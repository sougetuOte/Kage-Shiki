"""Tests for agent/agent_core.py — session_id + SessionContext + PromptBuilder.

対応 FR:
    FR-3.5: SystemPrompt にペルソナ情報を展開
    FR-3.6: XML タグによる構造化
    FR-3.11: プロンプトインジェクション対策
    FR-3.12: session_id のハイブリッド形式（YYYYMMDD_HHMM_xxxxxxxx）
    FR-6.2: コンテキスト注入優先順位
    FR-6.3: 簡易自己問答指示
    FR-6.5: 括弧書き心情描写の禁止

対応設計:
    D-3: プロンプトテンプレート設計
    D-8: 整合性チェック3類型
    D-13: session_id 生成規則
"""

import re
from datetime import datetime

from kage_shiki.agent.agent_core import (
    _SESSION_ID_LENGTH,
    _SESSION_ID_PATTERN,
    PromptBuilder,
    SessionContext,
    generate_session_id,
)

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
