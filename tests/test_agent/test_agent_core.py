"""Tests for agent/agent_core.py — session_id + SessionContext + PromptBuilder + AgentCore.

対応 FR:
    FR-2.5: クリックイベント（突っつき）処理
    FR-3.5: SystemPrompt にペルソナ情報を展開
    FR-3.6: XML タグによる構造化
    FR-3.7: 応答後の observations 即時書込
    FR-3.11: プロンプトインジェクション対策
    FR-3.12: session_id のハイブリッド形式（YYYYMMDD_HHMM_xxxxxxxx）
    FR-6.1: ReAct ループ本体
    FR-6.2: コンテキスト注入優先順位
    FR-6.3: 簡易自己問答指示
    FR-6.4: 整合性チェック間隔
    FR-6.5: 括弧書き心情描写の禁止
    FR-6.6: 後処理（observations 書込、human_block/trends 判断）

対応設計:
    D-3: プロンプトテンプレート設計
    D-8: 整合性チェック3類型
    D-13: session_id 生成規則
    D-15: poke 用 max_tokens=256
"""

import re
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kage_shiki.agent.agent_core import (
    _SESSION_ID_LENGTH,
    _SESSION_ID_PATTERN,
    POKE_EVENT_PREFIX,
    AgentCore,
    PromptBuilder,
    SessionContext,
    check_consistency_rules,
    generate_session_id,
)
from kage_shiki.agent.llm_client import LLMProtocol
from kage_shiki.core.config import AppConfig
from kage_shiki.persona.persona_system import PersonaSystem

# ---------------------------------------------------------------------------
# FR-3.12: session_id 生成
# ---------------------------------------------------------------------------


class TestGenerateSessionId:
    """generate_session_id 関数のテスト (D-13)."""

    def test_format_matches_pattern(self) -> None:
        """YYYYMMDD_HHMM_xxxxxxxx 形式であること."""
        sid = generate_session_id()
        assert _SESSION_ID_PATTERN.fullmatch(sid)

    def test_fixed_length_22(self) -> None:
        """固定22文字であること."""
        sid = generate_session_id()
        assert len(sid) == _SESSION_ID_LENGTH

    def test_uniqueness(self) -> None:
        """2回呼び出しで異なる値が返ること."""
        sid1 = generate_session_id()
        sid2 = generate_session_id()
        assert sid1 != sid2

    def test_date_part_is_numeric(self) -> None:
        """日付部分が数字8桁であること."""
        sid = generate_session_id()
        date_part = sid[:8]
        assert date_part.isdigit()
        assert len(date_part) == 8

    def test_time_part_is_numeric(self) -> None:
        """時刻部分が数字4桁であること."""
        sid = generate_session_id()
        time_part = sid[9:13]
        assert time_part.isdigit()
        assert len(time_part) == 4

    def test_uuid_part_is_hex(self) -> None:
        """UUID 部分が16進数8桁であること."""
        sid = generate_session_id()
        uuid_part = sid[14:]
        assert re.fullmatch(r"[0-9a-f]{8}", uuid_part)


# ---------------------------------------------------------------------------
# SessionContext
# ---------------------------------------------------------------------------


class TestSessionContext:
    """SessionContext クラスのテスト (D-13)."""

    def test_default_session_id_format(self) -> None:
        """デフォルトの session_id が正しい形式であること."""
        ctx = SessionContext()
        assert _SESSION_ID_PATTERN.fullmatch(ctx.session_id)
        assert len(ctx.session_id) == _SESSION_ID_LENGTH

    def test_default_turns_is_empty(self) -> None:
        """デフォルトの turns が空リストであること."""
        ctx = SessionContext()
        assert ctx.turns == []

    def test_default_message_count_is_zero(self) -> None:
        """デフォルトの message_count が 0 であること."""
        ctx = SessionContext()
        assert ctx.message_count == 0

    def test_turns_are_independent(self) -> None:
        """各インスタンスの turns が独立していること."""
        ctx1 = SessionContext()
        ctx2 = SessionContext()
        ctx1.turns.append({"role": "user", "content": "hello"})
        assert ctx2.turns == []

    def test_custom_session_id(self) -> None:
        """カスタム session_id を指定できること."""
        ctx = SessionContext(session_id="20260303_1432_f47ac10b")
        assert ctx.session_id == "20260303_1432_f47ac10b"


# ---------------------------------------------------------------------------
# T-12: PromptBuilder — SystemPrompt 構築
# ---------------------------------------------------------------------------


class TestPromptBuilderSystemPrompt:
    """PromptBuilder.build_system_prompt のテスト (D-3).

    対応 FR:
        FR-3.5: SystemPrompt にペルソナ情報を展開
        FR-3.6: XML タグによる構造化
        FR-3.11: プロンプトインジェクション対策
        FR-6.3: 簡易自己問答指示
        FR-6.5: 括弧書き心情描写の禁止
    """

    def _make_builder(self, **kwargs) -> PromptBuilder:
        defaults = {
            "persona_core": "# テストキャラ\n好奇心旺盛な性格。",
            "style_samples": "## S1: 日常会話\n「えっとね」",
            "human_block": "## 基本情報\n名前: テストユーザー",
            "personality_trends": "## 会話傾向\nフレンドリーな距離感",
            "day_summaries": [
                {"date": "2026-03-01", "summary": "テストの話をした。"},
                {"date": "2026-03-02", "summary": "天気の話をした。"},
            ],
        }
        defaults.update(kwargs)
        return PromptBuilder(**defaults)

    def test_contains_behavior_block(self) -> None:
        """S1 行動規範ブロックが含まれること."""
        prompt = self._make_builder().build_system_prompt()
        assert "あなたはデスクトップマスコットです" in prompt

    def test_contains_persona_tag(self) -> None:
        """S2 <persona> タグでキャラクター定義が展開されること."""
        prompt = self._make_builder().build_system_prompt()
        assert "<persona>" in prompt
        assert "</persona>" in prompt
        assert "テストキャラ" in prompt

    def test_contains_style_samples_tag(self) -> None:
        """S3 <style_samples> タグで口調参照が展開されること."""
        prompt = self._make_builder().build_system_prompt()
        assert "<style_samples>" in prompt
        assert "</style_samples>" in prompt
        assert "発話スタイルの参照例" in prompt

    def test_contains_user_info_tag(self) -> None:
        """S4 <user_info> タグでユーザー情報が展開されること."""
        prompt = self._make_builder().build_system_prompt()
        assert "<user_info>" in prompt
        assert "</user_info>" in prompt
        assert "テストユーザー" in prompt

    def test_user_info_present_when_empty(self) -> None:
        """S4 human_block が空でも <user_info> タグが維持されること."""
        prompt = self._make_builder(human_block="").build_system_prompt()
        assert "<user_info>" in prompt
        assert "</user_info>" in prompt

    def test_contains_personality_trends_tag(self) -> None:
        """S5 非空の personality_trends が展開されること."""
        prompt = self._make_builder().build_system_prompt()
        assert "<personality_trends>" in prompt
        assert "</personality_trends>" in prompt
        assert "フレンドリーな距離感" in prompt

    def test_omits_personality_trends_when_empty(self) -> None:
        """S5 personality_trends が空なら省略されること."""
        prompt = self._make_builder(personality_trends="").build_system_prompt()
        assert "</personality_trends>" not in prompt

    def test_contains_recent_memories_tag(self) -> None:
        """S6 day_summary が存在する場合に <recent_memories> が含まれること."""
        prompt = self._make_builder().build_system_prompt()
        assert "<recent_memories>" in prompt
        assert "</recent_memories>" in prompt

    def test_omits_recent_memories_when_no_summaries(self) -> None:
        """S6 day_summary が空なら省略されること."""
        prompt = self._make_builder(day_summaries=[]).build_system_prompt()
        assert "</recent_memories>" not in prompt

    def test_contains_response_rules(self) -> None:
        """S7 応答規範ブロックが含まれること."""
        prompt = self._make_builder().build_system_prompt()
        assert "【応答規範】" in prompt

    def test_contains_emotion_prohibition(self) -> None:
        """S7 括弧書き心情描写の禁止が含まれること (FR-6.5)."""
        prompt = self._make_builder().build_system_prompt()
        assert "括弧書きの心情描写" in prompt

    def test_contains_info_protection(self) -> None:
        """S7 情報保護指示が含まれること (FR-3.11)."""
        prompt = self._make_builder().build_system_prompt()
        assert "情報保護" in prompt

    def test_consistency_check_when_active(self) -> None:
        """整合性チェック指示が active 時に含まれること (D-8)."""
        prompt = self._make_builder().build_system_prompt(
            consistency_check_active=True,
        )
        assert "【本ターンの自己確認】" in prompt

    def test_no_consistency_check_when_inactive(self) -> None:
        """整合性チェック指示が inactive 時に含まれないこと."""
        prompt = self._make_builder().build_system_prompt(
            consistency_check_active=False,
        )
        assert "【本ターンの自己確認】" not in prompt

    def test_consistency_check_three_types(self) -> None:
        """整合性チェックが3類型すべて含まれること (D-8)."""
        prompt = self._make_builder().build_system_prompt(
            consistency_check_active=True,
        )
        assert "アイデンティティの確認" in prompt
        assert "口調の確認" in prompt
        assert "知識応答の確認" in prompt

    def test_block_order_s1_to_s7(self) -> None:
        """S1 → S2 → S3 → S4 → S5 → S6 → S7 の順であること."""
        prompt = self._make_builder().build_system_prompt()
        positions = [
            prompt.index("あなたはデスクトップマスコットです"),
            prompt.index("<persona>"),
            prompt.index("<style_samples>"),
            prompt.index("<user_info>"),
            prompt.index("<personality_trends>"),
            prompt.index("<recent_memories>"),
            prompt.index("【応答規範】"),
        ]
        assert positions == sorted(positions)

    def test_day_summaries_chronological_order(self) -> None:
        """day_summary が古い日付から順に並ぶこと."""
        prompt = self._make_builder().build_system_prompt()
        assert prompt.index("2026-03-01") < prompt.index("2026-03-02")

    def test_day_summaries_separator(self) -> None:
        """day_summary が --- で区切られていること."""
        prompt = self._make_builder().build_system_prompt()
        section = prompt.split("<recent_memories>")[1].split("</recent_memories>")[0]
        assert "---" in section

    def test_self_reflection_instruction(self) -> None:
        """S7 簡易自己問答指示が含まれること (FR-6.3)."""
        prompt = self._make_builder().build_system_prompt()
        assert "C4: 人格核文" in prompt
        assert "C10: 禁忌" in prompt


# ---------------------------------------------------------------------------
# T-12: PromptBuilder — Messages 配列構築
# ---------------------------------------------------------------------------


class TestPromptBuilderMessages:
    """PromptBuilder.build_messages のテスト (D-3).

    対応 FR:
        FR-3.5: 会話履歴の管理
        FR-6.2: コンテキスト注入優先順位
    """

    def _make_builder(self) -> PromptBuilder:
        return PromptBuilder(
            persona_core="# テストキャラ",
            style_samples="## S1\nテスト",
            human_block="",
            personality_trends="",
            day_summaries=[],
        )

    def test_starts_with_session_start_message(self) -> None:
        """messages 配列が assistant ロールの開始メッセージで始まること."""
        msgs = self._make_builder().build_messages(
            session_start_message="やあ、久しぶり。",
            turns=[],
            latest_input="こんにちは",
        )
        assert msgs[0]["role"] == "assistant"
        assert msgs[0]["content"] == "やあ、久しぶり。"

    def test_ends_with_latest_input(self) -> None:
        """messages 配列が最新ユーザー入力で終わること."""
        msgs = self._make_builder().build_messages(
            session_start_message="やあ",
            turns=[],
            latest_input="最近どう？",
        )
        assert msgs[-1]["role"] == "user"
        assert msgs[-1]["content"] == "最近どう？"

    def test_includes_turns(self) -> None:
        """会話履歴が正しく配置されること."""
        turns = [
            {"role": "user", "content": "元気？"},
            {"role": "assistant", "content": "元気だよ"},
        ]
        msgs = self._make_builder().build_messages(
            session_start_message="やあ",
            turns=turns,
            latest_input="そっか",
        )
        # 4件 = session_start(assistant) + turn_user + turn_assistant + latest_input(user)
        assert len(msgs) == 4
        assert msgs[1]["content"] == "元気？"
        assert msgs[2]["content"] == "元気だよ"
        assert msgs[3]["content"] == "そっか"

    def test_cold_memory_injection(self) -> None:
        """Cold Memory が最新 user メッセージに結合されること (D-3 5.6)."""
        cold = [
            {"content": "テスト記憶", "speaker": "user", "created_at": 1709510400.0},
        ]
        msgs = self._make_builder().build_messages(
            session_start_message="やあ",
            turns=[],
            latest_input="昨日何した？",
            cold_memories=cold,
        )
        last = msgs[-1]
        assert last["role"] == "user"
        assert "<retrieved_memories>" in last["content"]
        assert "</retrieved_memories>" in last["content"]
        assert "昨日何した？" in last["content"]
        assert "テスト記憶" in last["content"]

    def test_no_cold_memory_when_empty_list(self) -> None:
        """Cold Memory が空リストなら注入されないこと."""
        msgs = self._make_builder().build_messages(
            session_start_message="やあ",
            turns=[],
            latest_input="こんにちは",
            cold_memories=[],
        )
        assert "<retrieved_memories>" not in msgs[-1]["content"]

    def test_no_cold_memory_when_none(self) -> None:
        """Cold Memory が None なら注入されないこと."""
        msgs = self._make_builder().build_messages(
            session_start_message="やあ",
            turns=[],
            latest_input="こんにちは",
            cold_memories=None,
        )
        assert "<retrieved_memories>" not in msgs[-1]["content"]

    def test_cold_memory_format(self) -> None:
        """Cold Memory のフォーマットが D-3 5.6 準拠であること."""
        ts1 = 1709510400.0
        ts2 = 1709596800.0
        cold = [
            {"content": "記憶1", "speaker": "user", "created_at": ts1},
            {"content": "記憶2", "speaker": "mascot", "created_at": ts2},
        ]
        msgs = self._make_builder().build_messages(
            session_start_message="やあ",
            turns=[],
            latest_input="テスト",
            cold_memories=cold,
        )
        content = msgs[-1]["content"]
        assert "[1]" in content
        assert "[2]" in content
        assert "発言者: user" in content
        assert "発言者: mascot" in content
        # タイムスタンプの日付フォーマットを検証
        expected_date1 = datetime.fromtimestamp(ts1).strftime("%Y-%m-%d")
        assert f"{expected_date1} の記録" in content

    def test_cold_memory_before_user_input(self) -> None:
        """Cold Memory がユーザー入力の前に配置されること."""
        cold = [
            {"content": "記憶", "speaker": "user", "created_at": 1709510400.0},
        ]
        msgs = self._make_builder().build_messages(
            session_start_message="やあ",
            turns=[],
            latest_input="質問です",
            cold_memories=cold,
        )
        content = msgs[-1]["content"]
        mem_pos = content.index("<retrieved_memories>")
        input_pos = content.index("質問です")
        assert mem_pos < input_pos


# ---------------------------------------------------------------------------
# T-13: ConsistencyHit + check_consistency_rules (D-8)
# ---------------------------------------------------------------------------


class TestCheckConsistencyRules:
    """ルールベース後処理のテスト (D-8).

    対応 FR:
        FR-6.4: 整合性チェック3類型
    """

    def test_detects_character_hallucination(self) -> None:
        """「私はAIです」でタイプ1ヒットが検出されること."""
        hits = check_consistency_rules("実は私はAIです。何でも聞いてね。")
        assert any(h.type_id == 1 for h in hits)
        assert any(h.type_name == "character_hallucination" for h in hits)

    def test_detects_action_ambiguity(self) -> None:
        """「承知しました」でタイプ2ヒットが検出されること."""
        hits = check_consistency_rules("承知しました。説明いたします。")
        assert any(h.type_id == 2 for h in hits)

    def test_detects_knowledge_degradation(self) -> None:
        """「答えられません」でタイプ3ヒットが検出されること."""
        hits = check_consistency_rules("その質問には答えられません。")
        assert any(h.type_id == 3 for h in hits)

    def test_no_hit_on_normal_response(self) -> None:
        """正常な応答でヒットが検出されないこと."""
        hits = check_consistency_rules("今日はいい天気だね。散歩でもしない？")
        assert hits == []

    def test_multiple_hits(self) -> None:
        """複数パターンが同時検出されること."""
        text = "私はAIです。承知しました。答えられません。"
        hits = check_consistency_rules(text)
        type_ids = {h.type_id for h in hits}
        assert type_ids == {1, 2, 3}

    def test_hit_contains_matched_pattern(self) -> None:
        """ヒットにマッチしたパターン文字列が含まれること."""
        hits = check_consistency_rules("ChatGPTみたいだね")
        assert len(hits) >= 1
        assert any("ChatGPT" in h.pattern for h in hits)


# ---------------------------------------------------------------------------
# T-13: AgentCore (FR-6.1, FR-3.7, FR-6.6)
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_llm() -> Mock:
    """LLMProtocol のモック（カスタム戻り値）."""
    m = Mock(spec=LLMProtocol)
    m.send_message_for_purpose.return_value = "テスト応答だよ。"
    return m


@pytest.fixture()
def mock_db_conn() -> Mock:
    """DB接続のモック."""
    return Mock()


@pytest.fixture()
def persona_system() -> PersonaSystem:
    """PersonaSystem インスタンス."""
    ps = PersonaSystem()
    ps._persona_core_text = "# テストキャラ\n## C1: テスト名\nテスト"
    ps._style_samples_text = "## S1\nテスト口調"
    ps._human_block_text = ""
    ps._personality_trends_text = ""
    return ps


@pytest.fixture()
def default_prompt_builder() -> PromptBuilder:
    """テスト用デフォルト PromptBuilder."""
    return PromptBuilder(
        persona_core="# テストキャラ\n## C1: テスト名\nテスト",
        style_samples="## S1\nテスト口調",
        human_block="",
        personality_trends="",
    )


@pytest.fixture()
def agent_core(
    mock_llm: Mock,
    mock_db_conn: Mock,
    persona_system: PersonaSystem,
    config: AppConfig,
    default_prompt_builder: PromptBuilder,
) -> AgentCore:
    """AgentCore インスタンス."""
    return AgentCore(
        config=config,
        db_conn=mock_db_conn,
        llm_client=mock_llm,
        persona_system=persona_system,
        prompt_builder=default_prompt_builder,
    )


class TestAgentCoreInit:
    """AgentCore 初期化テスト."""

    def test_session_context_created(self, agent_core: AgentCore) -> None:
        """初期化時に SessionContext が生成されること."""
        assert agent_core.session_context is not None
        assert agent_core.session_context.session_id != ""
        assert agent_core.session_context.message_count == 0

    def test_session_start_message_empty_initially(
        self, agent_core: AgentCore,
    ) -> None:
        """初期化時にセッション開始メッセージが空であること."""
        assert agent_core.session_start_message == ""


class TestGenerateSessionStartMessage:
    """セッション開始メッセージ生成テスト."""

    def test_generates_greeting(
        self, agent_core: AgentCore, mock_llm: Mock,
    ) -> None:
        """LLM を呼び出してセッション開始メッセージを生成すること."""
        mock_llm.send_message_for_purpose.return_value = "おはよう！今日もよろしくね。"
        result = agent_core.generate_session_start_message()
        assert result == "おはよう！今日もよろしくね。"
        assert agent_core.session_start_message == result

    def test_uses_conversation_purpose(
        self, agent_core: AgentCore, mock_llm: Mock,
    ) -> None:
        """purpose='conversation' で LLM を呼び出すこと."""
        agent_core.generate_session_start_message()
        call_kwargs = mock_llm.send_message_for_purpose.call_args.kwargs
        assert call_kwargs["purpose"] == "conversation"


class TestProcessTurn:
    """process_turn のテスト (ReAct ループ単一ターン)."""

    def test_returns_llm_response(
        self, agent_core: AgentCore, mock_llm: Mock,
    ) -> None:
        """ユーザー入力に対して LLM 応答が返ること."""
        agent_core.session_start_message = "やあ"
        mock_llm.send_message_for_purpose.return_value = "そうだね、元気だよ。"
        result = agent_core.process_turn("元気？")
        assert result == "そうだね、元気だよ。"

    def test_writes_user_input_to_observations(
        self, agent_core: AgentCore, mock_llm: Mock, mock_db_conn: Mock,
    ) -> None:
        """ユーザー入力が observations に書き込まれること (FR-3.7)."""
        agent_core.session_start_message = "やあ"
        with patch("kage_shiki.agent.agent_core.save_observation") as mock_save:
            agent_core.process_turn("テスト入力")
            calls = [
                c for c in mock_save.call_args_list
                if c.kwargs.get("speaker") == "user"
                or (len(c.args) > 2 and c.args[2] == "user")
            ]
            assert len(calls) >= 1

    def test_writes_mascot_response_to_observations(
        self, agent_core: AgentCore, mock_llm: Mock, mock_db_conn: Mock,
    ) -> None:
        """マスコット応答が observations に書き込まれること (FR-3.7)."""
        agent_core.session_start_message = "やあ"
        mock_llm.send_message_for_purpose.return_value = "応答テスト"
        with patch("kage_shiki.agent.agent_core.save_observation") as mock_save:
            agent_core.process_turn("入力")
            calls = [
                c for c in mock_save.call_args_list
                if c.kwargs.get("speaker") == "mascot"
                or (len(c.args) > 2 and c.args[2] == "mascot")
            ]
            assert len(calls) >= 1

    def test_increments_message_count(
        self, agent_core: AgentCore, mock_llm: Mock,
    ) -> None:
        """message_count が正しくインクリメントされること."""
        agent_core.session_start_message = "やあ"
        assert agent_core.session_context.message_count == 0
        agent_core.process_turn("1回目")
        assert agent_core.session_context.message_count == 1
        agent_core.process_turn("2回目")
        assert agent_core.session_context.message_count == 2

    def test_consistency_check_active_at_interval(
        self, agent_core: AgentCore, mock_llm: Mock,
    ) -> None:
        """consistency_interval 間隔で consistency_check_active が True になること."""
        agent_core.session_start_message = "やあ"
        interval = agent_core._config.memory.consistency_interval
        for i in range(interval - 1):
            agent_core.process_turn(f"入力{i}")
        # interval回目で active になること
        # Phase 2a 以降は build_with_truncation() 経由で build_system_prompt() が呼ばれる
        with patch.object(
            agent_core._prompt_builder, "build_with_truncation",
            wraps=agent_core._prompt_builder.build_with_truncation,
        ) as mock_build:
            agent_core.process_turn(f"入力{interval}")
            mock_build.assert_called_once()
            call_kwargs = mock_build.call_args.kwargs
            assert call_kwargs["consistency_check_active"] is True

    def test_fts5_results_injected_into_prompt(
        self, agent_core: AgentCore, mock_llm: Mock,
    ) -> None:
        """FTS5 検索結果がプロンプトに注入されること."""
        agent_core.session_start_message = "やあ"
        cold = [
            {"content": "昨日公園で遊んだ", "speaker": "user", "created_at": 1709510400.0},
        ]
        with patch("kage_shiki.agent.agent_core.search_observations_fts", return_value=cold):
            agent_core.process_turn("昨日のことだけど")
            call_kwargs = mock_llm.send_message_for_purpose.call_args.kwargs
            messages = call_kwargs["messages"]
            last_user = messages[-1]["content"]
            assert "<retrieved_memories>" in last_user

    def test_turns_appended_to_session_context(
        self, agent_core: AgentCore, mock_llm: Mock,
    ) -> None:
        """会話ターンが SessionContext に追加されること."""
        agent_core.session_start_message = "やあ"
        mock_llm.send_message_for_purpose.return_value = "応答1"
        agent_core.process_turn("入力1")
        assert len(agent_core.session_context.turns) == 2  # user + assistant
        assert agent_core.session_context.turns[0]["role"] == "user"
        assert agent_core.session_context.turns[1]["role"] == "assistant"

    def test_consistency_rules_logged_on_hit(
        self, agent_core: AgentCore, mock_llm: Mock,
    ) -> None:
        """ルールベース後処理でパターンマッチ時に WARNING ログが記録されること."""
        agent_core.session_start_message = "やあ"
        mock_llm.send_message_for_purpose.return_value = "私はAIです。何でも聞いてね。"
        with patch("kage_shiki.agent.agent_core.logger") as mock_logger:
            agent_core.process_turn("あなたは誰？")
            warning_calls = mock_logger.warning.call_args_list
            assert any("consistency_check" in str(c) for c in warning_calls)

    def test_consistency_interval_zero_disables_check(
        self, mock_llm: Mock, mock_db_conn: Mock,
        persona_system: PersonaSystem,
        default_prompt_builder: PromptBuilder,
    ) -> None:
        """consistency_interval=0 でチェックが無効化されること."""
        config = AppConfig()
        config.memory.consistency_interval = 0
        core = AgentCore(
            config=config, db_conn=mock_db_conn,
            llm_client=mock_llm, persona_system=persona_system,
            prompt_builder=default_prompt_builder,
        )
        core.session_start_message = "やあ"
        with patch.object(
            core._prompt_builder, "build_with_truncation",
            wraps=core._prompt_builder.build_with_truncation,
        ) as mock_build:
            for i in range(20):
                core.process_turn(f"入力{i}")
            # 20回全て consistency_check_active=False であること
            assert mock_build.call_count == 20
            for call in mock_build.call_args_list:
                assert call.kwargs.get("consistency_check_active") is False


# ---------------------------------------------------------------------------
# T-14: クリックイベント（突っつき）処理 (FR-2.5)
# ---------------------------------------------------------------------------


class TestPokeEvent:
    """クリックイベント（突っつき）処理のテスト (FR-2.5).

    対応 FR:
        FR-2.5: クリックイベント（突っつき）処理
    対応設計:
        D-15: poke 用 max_tokens=256
    """

    def test_poke_event_prefix_defined(self) -> None:
        """クリックイベントプレフィックス定数が定義されていること."""
        assert POKE_EVENT_PREFIX == "[クリックイベント]"

    def test_poke_event_uses_poke_purpose(
        self, agent_core: AgentCore, mock_llm: Mock,
    ) -> None:
        """クリックイベント入力時に purpose='poke' で LLM が呼ばれること."""
        agent_core.session_start_message = "やあ"
        poke_input = f"{POKE_EVENT_PREFIX} ユーザーがウィンドウをクリックして突っつきました"
        agent_core.process_turn(poke_input)
        call_kwargs = mock_llm.send_message_for_purpose.call_args.kwargs
        assert call_kwargs["purpose"] == "poke"

    def test_normal_input_uses_conversation_purpose(
        self, agent_core: AgentCore, mock_llm: Mock,
    ) -> None:
        """通常入力時は purpose='conversation' であること."""
        agent_core.session_start_message = "やあ"
        agent_core.process_turn("普通の会話です")
        call_kwargs = mock_llm.send_message_for_purpose.call_args.kwargs
        assert call_kwargs["purpose"] == "conversation"

    def test_poke_event_still_saves_observations(
        self, agent_core: AgentCore, mock_llm: Mock,
    ) -> None:
        """クリックイベントでも observations に保存されること."""
        agent_core.session_start_message = "やあ"
        poke_input = f"{POKE_EVENT_PREFIX} ユーザーがウィンドウをクリック"
        with patch("kage_shiki.agent.agent_core.save_observation") as mock_save:
            agent_core.process_turn(poke_input)
            assert mock_save.call_count == 2  # user + mascot


# ---------------------------------------------------------------------------
# T-15: 整合性チェック公開定数 + 累計カウンタ (FR-6.4)
# ---------------------------------------------------------------------------


class TestConsistencyPublicConstants:
    """整合性チェック公開定数のテスト (T-15)."""

    def test_character_hallucination_patterns_exported(self) -> None:
        """CHARACTER_HALLUCINATION_PATTERNS が公開されていること."""
        from kage_shiki.agent.agent_core import CHARACTER_HALLUCINATION_PATTERNS
        assert isinstance(CHARACTER_HALLUCINATION_PATTERNS, list)
        assert len(CHARACTER_HALLUCINATION_PATTERNS) > 0

    def test_action_ambiguity_patterns_exported(self) -> None:
        """ACTION_AMBIGUITY_PATTERNS が公開されていること."""
        from kage_shiki.agent.agent_core import ACTION_AMBIGUITY_PATTERNS
        assert isinstance(ACTION_AMBIGUITY_PATTERNS, list)
        assert len(ACTION_AMBIGUITY_PATTERNS) > 0

    def test_knowledge_degradation_patterns_exported(self) -> None:
        """KNOWLEDGE_DEGRADATION_PATTERNS が公開されていること."""
        from kage_shiki.agent.agent_core import KNOWLEDGE_DEGRADATION_PATTERNS
        assert isinstance(KNOWLEDGE_DEGRADATION_PATTERNS, list)
        assert len(KNOWLEDGE_DEGRADATION_PATTERNS) > 0

    def test_public_aliases_match_internal(self) -> None:
        """公開定数が内部定数と同一オブジェクトであること."""
        from kage_shiki.agent.agent_core import (
            _AMBIGUITY_PATTERNS,
            _DEGRADATION_PATTERNS,
            _HALLUCINATION_PATTERNS,
            ACTION_AMBIGUITY_PATTERNS,
            CHARACTER_HALLUCINATION_PATTERNS,
            KNOWLEDGE_DEGRADATION_PATTERNS,
        )
        assert CHARACTER_HALLUCINATION_PATTERNS is _HALLUCINATION_PATTERNS
        assert ACTION_AMBIGUITY_PATTERNS is _AMBIGUITY_PATTERNS
        assert KNOWLEDGE_DEGRADATION_PATTERNS is _DEGRADATION_PATTERNS


class TestConsistencyHitCount:
    """consistency_hit_count セッション累計テスト (T-15)."""

    def test_initial_hit_count_is_zero(self, agent_core: AgentCore) -> None:
        """初期状態で consistency_hit_count が 0 であること."""
        assert agent_core.consistency_hit_count == 0

    def test_hit_count_incremented_on_detection(
        self, agent_core: AgentCore, mock_llm: Mock,
    ) -> None:
        """パターン検出時に hit_count が加算されること."""
        agent_core.session_start_message = "やあ"
        mock_llm.send_message_for_purpose.return_value = "私はAIです。"
        agent_core.process_turn("テスト")
        assert agent_core.consistency_hit_count > 0

    def test_hit_count_not_incremented_on_clean_response(
        self, agent_core: AgentCore, mock_llm: Mock,
    ) -> None:
        """正常応答では hit_count が加算されないこと."""
        agent_core.session_start_message = "やあ"
        mock_llm.send_message_for_purpose.return_value = "いい天気だね。"
        agent_core.process_turn("テスト")
        assert agent_core.consistency_hit_count == 0

    def test_hit_count_accumulates_across_turns(
        self, agent_core: AgentCore, mock_llm: Mock,
    ) -> None:
        """複数ターンで累計が蓄積されること."""
        agent_core.session_start_message = "やあ"
        mock_llm.send_message_for_purpose.return_value = "私はAIです。"
        agent_core.process_turn("テスト1")
        first_count = agent_core.consistency_hit_count
        agent_core.process_turn("テスト2")
        assert agent_core.consistency_hit_count > first_count

    def test_hit_count_logged_in_warning(
        self, agent_core: AgentCore, mock_llm: Mock,
    ) -> None:
        """WARNING ログにセッション累計が含まれること."""
        agent_core.session_start_message = "やあ"
        mock_llm.send_message_for_purpose.return_value = "私はAIです。"
        with patch("kage_shiki.agent.agent_core.logger") as mock_logger:
            agent_core.process_turn("テスト")
            warning_calls = mock_logger.warning.call_args_list
            assert any("session_total" in str(c) for c in warning_calls)


# ---------------------------------------------------------------------------
# T-25: C-01 解決 — PromptBuilder 外部注入 + W-T25 後処理 (FR-6.6)
# ---------------------------------------------------------------------------


class TestAgentCorePromptBuilderInjection:
    """PromptBuilder 外部注入 (C-01) のテスト."""

    def test_prompt_builder_injected(
        self,
        mock_llm: Mock,
        mock_db_conn: Mock,
        persona_system: PersonaSystem,
        config: AppConfig,
    ) -> None:
        """外部注入した PromptBuilder が使われること."""
        custom_builder = PromptBuilder(
            persona_core="custom persona",
            style_samples="custom style",
            human_block="custom human",
        )
        core = AgentCore(
            config=config,
            db_conn=mock_db_conn,
            llm_client=mock_llm,
            persona_system=persona_system,
            prompt_builder=custom_builder,
        )
        assert core._prompt_builder is custom_builder

    def test_data_dir_none_by_default(
        self,
        mock_llm: Mock,
        mock_db_conn: Mock,
        persona_system: PersonaSystem,
        config: AppConfig,
        default_prompt_builder: PromptBuilder,
    ) -> None:
        """data_dir 未指定時は None になること."""
        core = AgentCore(
            config=config,
            db_conn=mock_db_conn,
            llm_client=mock_llm,
            persona_system=persona_system,
            prompt_builder=default_prompt_builder,
        )
        assert core._data_dir is None
        assert core._human_block_path is None
        assert core._trends_path is None

    def test_data_dir_sets_paths(
        self,
        mock_llm: Mock,
        mock_db_conn: Mock,
        persona_system: PersonaSystem,
        config: AppConfig,
        default_prompt_builder: PromptBuilder,
        tmp_path: Path,
    ) -> None:
        """data_dir 指定時にパスが設定されること."""
        core = AgentCore(
            config=config,
            db_conn=mock_db_conn,
            llm_client=mock_llm,
            persona_system=persona_system,
            prompt_builder=default_prompt_builder,
            data_dir=tmp_path,
        )
        assert core._data_dir == tmp_path
        assert core._human_block_path == tmp_path / "human_block.md"
        assert core._trends_path == tmp_path / "personality_trends.md"

    def test_trends_manager_none_by_default(
        self,
        mock_llm: Mock,
        mock_db_conn: Mock,
        persona_system: PersonaSystem,
        config: AppConfig,
        default_prompt_builder: PromptBuilder,
    ) -> None:
        """_trends_manager 初期値が None であること."""
        core = AgentCore(
            config=config,
            db_conn=mock_db_conn,
            llm_client=mock_llm,
            persona_system=persona_system,
            prompt_builder=default_prompt_builder,
        )
        assert core._trends_manager is None


class TestApplyHumanBlockUpdates:
    """_apply_human_block_updates のテスト (T-17, W-T25)."""

    def _make_core(
        self,
        mock_llm: Mock,
        mock_db_conn: Mock,
        persona_system: PersonaSystem,
        config: AppConfig,
        default_prompt_builder: PromptBuilder,
        tmp_path: Path | None = None,
    ) -> AgentCore:
        return AgentCore(
            config=config,
            db_conn=mock_db_conn,
            llm_client=mock_llm,
            persona_system=persona_system,
            prompt_builder=default_prompt_builder,
            data_dir=tmp_path,
        )

    def test_apply_human_block_updates_with_valid_marker(
        self,
        mock_llm: Mock,
        mock_db_conn: Mock,
        persona_system: PersonaSystem,
        config: AppConfig,
        default_prompt_builder: PromptBuilder,
        tmp_path: Path,
    ) -> None:
        """更新マーカー入り応答で update_human_block が呼ばれること."""
        core = self._make_core(
            mock_llm, mock_db_conn, persona_system, config,
            default_prompt_builder, tmp_path,
        )
        persona_system.update_human_block = Mock()

        valid_response = (
            "通常の会話テキスト。\n"
            "---human_block_update---\n"
            "セクション: 基本情報\n"
            "内容: 好きな食べ物はラーメン\n"
            "---update_end---"
        )
        core._apply_human_block_updates(valid_response)

        persona_system.update_human_block.assert_called_once()
        call_args = persona_system.update_human_block.call_args
        assert call_args.args[1] == "基本情報" or call_args.kwargs.get("section") == "基本情報"

    def test_apply_human_block_updates_skips_invalid(
        self,
        mock_llm: Mock,
        mock_db_conn: Mock,
        persona_system: PersonaSystem,
        config: AppConfig,
        default_prompt_builder: PromptBuilder,
        tmp_path: Path,
    ) -> None:
        """不正な更新がスキップされログに記録されること."""
        core = self._make_core(
            mock_llm, mock_db_conn, persona_system, config,
            default_prompt_builder, tmp_path,
        )
        persona_system.update_human_block = Mock()

        # 推測マーカー入り（ガードレール: 推測禁止）
        invalid_response = (
            "---human_block_update---\n"
            "セクション: 基本情報\n"
            "内容: おそらくラーメンが好きかもしれない\n"
            "---update_end---"
        )
        with patch("kage_shiki.agent.agent_core.logger") as mock_logger:
            core._apply_human_block_updates(invalid_response)
            mock_logger.info.assert_called_once()

        persona_system.update_human_block.assert_not_called()

    def test_apply_human_block_updates_no_data_dir(
        self,
        mock_llm: Mock,
        mock_db_conn: Mock,
        persona_system: PersonaSystem,
        config: AppConfig,
        default_prompt_builder: PromptBuilder,
    ) -> None:
        """data_dir=None の場合何もしないこと."""
        core = self._make_core(
            mock_llm, mock_db_conn, persona_system, config,
            default_prompt_builder, None,
        )
        persona_system.update_human_block = Mock()

        response_with_marker = (
            "---human_block_update---\n"
            "セクション: 基本情報\n"
            "内容: 何か情報\n"
            "---update_end---"
        )
        core._apply_human_block_updates(response_with_marker)

        persona_system.update_human_block.assert_not_called()


class TestHandleTrendsApproval:
    """_handle_trends_approval のテスト (T-16, W-T25)."""

    def _make_core_with_manager(
        self,
        mock_llm: Mock,
        mock_db_conn: Mock,
        persona_system: PersonaSystem,
        config: AppConfig,
        default_prompt_builder: PromptBuilder,
        tmp_path: Path,
    ) -> AgentCore:
        from kage_shiki.agent.trends_proposal import TrendsProposalManager
        core = AgentCore(
            config=config,
            db_conn=mock_db_conn,
            llm_client=mock_llm,
            persona_system=persona_system,
            prompt_builder=default_prompt_builder,
            data_dir=tmp_path,
        )
        core._trends_manager = TrendsProposalManager()
        return core

    def test_handle_trends_approval_approved(
        self,
        mock_llm: Mock,
        mock_db_conn: Mock,
        persona_system: PersonaSystem,
        config: AppConfig,
        default_prompt_builder: PromptBuilder,
        tmp_path: Path,
    ) -> None:
        """承認時に append_personality_trends が呼ばれること."""
        core = self._make_core_with_manager(
            mock_llm, mock_db_conn, persona_system, config,
            default_prompt_builder, tmp_path,
        )
        persona_system.append_personality_trends = Mock()

        mock_manager = Mock()
        mock_manager.parse_proposal_from_response.return_value = None
        mock_manager.judge_approval.return_value = "approved"
        from kage_shiki.agent.trends_proposal import TrendsProposal
        mock_proposal = TrendsProposal(
            trigger_type="T1",
            section="関係性の変化",
            content="最近仲良くなってきた",
            proposed_at_turn=1,
        )
        mock_manager.get_approved_proposal.return_value = mock_proposal
        mock_manager.format_entry_for_trends.return_value = (
            "### [2026-03-05] 関係性の変化\n\n最近仲良くなってきた"
        )
        core._trends_manager = mock_manager

        core._handle_trends_approval("承認", core.session_context.message_count)

        persona_system.append_personality_trends.assert_called_once()

    def test_handle_trends_approval_no_manager(
        self,
        mock_llm: Mock,
        mock_db_conn: Mock,
        persona_system: PersonaSystem,
        config: AppConfig,
        default_prompt_builder: PromptBuilder,
        tmp_path: Path,
    ) -> None:
        """_trends_manager=None の場合何もしないこと."""
        core = AgentCore(
            config=config,
            db_conn=mock_db_conn,
            llm_client=mock_llm,
            persona_system=persona_system,
            prompt_builder=default_prompt_builder,
            data_dir=tmp_path,
        )
        persona_system.append_personality_trends = Mock()

        # _trends_manager は None のまま
        core._handle_trends_approval("承認", 0)

        persona_system.append_personality_trends.assert_not_called()
