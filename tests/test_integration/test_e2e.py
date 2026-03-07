"""E2E 統合テスト (T-26).

対応 FR:
    FR-3.3: observations 即時書込
    FR-3.4: FTS5 検索
    FR-3.7: Cold Memory 注入
    FR-3.8: シャットダウン時サマリー生成
    FR-3.10: 起動時欠損補完
    FR-3.12: SessionContext 管理
    FR-6.1: ReAct ループ（入力 → 検索 → 応答 → 書込）
    FR-6.4: 整合性チェック
    NFR-10: テストカバレッジ

テスト方針:
    - LLM 呼び出しは全てモック（実 API 不使用）
    - SQLite は :memory: ではなく tmp_path の実ファイル DB を使用
    - GUI は不使用（AgentCore のデータフローのみ検証）
"""

import time
from datetime import date, datetime, timedelta

from kage_shiki.agent.agent_core import (
    AgentCore,
    PromptBuilder,
    SessionContext,
    check_consistency_rules,
    generate_session_id,
)
from kage_shiki.memory.db import (
    get_day_observations,
    get_missing_summary_dates,
    get_recent_day_summaries,
    save_day_summary,
    save_observation,
    search_observations_fts,
)
from kage_shiki.memory.memory_worker import MemoryWorker
from kage_shiki.persona.persona_system import PersonaSystem

from .conftest import SAMPLE_PERSONA_CORE, SAMPLE_STYLE_SAMPLES, insert_test_observations

# ---------------------------------------------------------------------------
# E1: 起動→対話→終了の基本フロー
# ---------------------------------------------------------------------------


class TestBasicDialogueFlow:
    """起動→対話→終了のコア統合テスト (FR-6.1, FR-3.3)."""

    def test_process_turn_saves_observations_and_returns_response(
        self, db_conn, mock_llm_client, integration_config, persona_data_dir,
    ):
        """process_turn でユーザー入力と応答が observations に書き込まれること."""
        mock_llm_client.send_message_for_purpose.return_value = "こんにちは！元気だよ"

        persona_system = PersonaSystem()
        prompt_builder = PromptBuilder(
            persona_core=SAMPLE_PERSONA_CORE.to_markdown(),
            style_samples=SAMPLE_STYLE_SAMPLES,
            human_block="",
        )
        agent = AgentCore(
            config=integration_config,
            db_conn=db_conn,
            llm_client=mock_llm_client,
            persona_system=persona_system,
            prompt_builder=prompt_builder,
            data_dir=persona_data_dir,
        )

        # セッション開始メッセージ
        mock_llm_client.send_message_for_purpose.return_value = "やっほー！"
        greeting = agent.generate_session_start_message()
        assert greeting == "やっほー！"
        assert agent.session_start_message == "やっほー！"

        # 1ターン目
        mock_llm_client.send_message_for_purpose.return_value = "こんにちは！元気だよ"
        response = agent.process_turn("こんにちは")

        assert response == "こんにちは！元気だよ"

        # observations に user + mascot の2レコードが書き込まれたこと
        rows = db_conn.execute(
            "SELECT content, speaker FROM observations ORDER BY id",
        ).fetchall()
        assert len(rows) == 2
        assert rows[0]["content"] == "こんにちは"
        assert rows[0]["speaker"] == "user"
        assert rows[1]["content"] == "こんにちは！元気だよ"
        assert rows[1]["speaker"] == "mascot"

    def test_multi_turn_conversation_increments_message_count(
        self, db_conn, mock_llm_client, integration_config, persona_data_dir,
    ):
        """複数ターンの会話で message_count が正しくインクリメントされること."""
        persona_system = PersonaSystem()
        prompt_builder = PromptBuilder(
            persona_core=SAMPLE_PERSONA_CORE.to_markdown(),
            style_samples=SAMPLE_STYLE_SAMPLES,
            human_block="",
        )
        agent = AgentCore(
            config=integration_config,
            db_conn=db_conn,
            llm_client=mock_llm_client,
            persona_system=persona_system,
            prompt_builder=prompt_builder,
            data_dir=persona_data_dir,
        )

        mock_llm_client.send_message_for_purpose.return_value = "挨拶"
        agent.generate_session_start_message()

        responses = []
        for i in range(3):
            mock_llm_client.send_message_for_purpose.return_value = f"応答{i}"
            responses.append(agent.process_turn(f"入力{i}"))

        assert agent.session_context.message_count == 3
        assert len(agent.session_context.turns) == 6  # 3 * (user + assistant)
        assert responses == ["応答0", "応答1", "応答2"]

        # DB に 6 レコード書き込まれていること
        count = db_conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
        assert count == 6

    def test_session_id_is_consistent_across_turns(
        self, db_conn, mock_llm_client, integration_config, persona_data_dir,
    ):
        """同一セッション内の全 observations が同じ session_id を持つこと."""
        persona_system = PersonaSystem()
        prompt_builder = PromptBuilder(
            persona_core=SAMPLE_PERSONA_CORE.to_markdown(),
            style_samples=SAMPLE_STYLE_SAMPLES,
            human_block="",
        )
        agent = AgentCore(
            config=integration_config,
            db_conn=db_conn,
            llm_client=mock_llm_client,
            persona_system=persona_system,
            prompt_builder=prompt_builder,
            data_dir=persona_data_dir,
        )
        mock_llm_client.send_message_for_purpose.return_value = "応答"
        agent.generate_session_start_message()

        agent.process_turn("入力1")
        agent.process_turn("入力2")

        session_ids = db_conn.execute(
            "SELECT DISTINCT session_id FROM observations",
        ).fetchall()
        assert len(session_ids) == 1
        assert session_ids[0][0] == agent.session_context.session_id

    def test_consistency_check_activates_at_interval(
        self, db_conn, mock_llm_client, integration_config, persona_data_dir,
    ):
        """consistency_interval の倍数ターンで整合性チェックが有効になること."""
        integration_config.memory.consistency_interval = 3

        persona_system = PersonaSystem()
        prompt_builder = PromptBuilder(
            persona_core=SAMPLE_PERSONA_CORE.to_markdown(),
            style_samples=SAMPLE_STYLE_SAMPLES,
            human_block="",
        )
        agent = AgentCore(
            config=integration_config,
            db_conn=db_conn,
            llm_client=mock_llm_client,
            persona_system=persona_system,
            prompt_builder=prompt_builder,
            data_dir=persona_data_dir,
        )
        mock_llm_client.send_message_for_purpose.return_value = "応答"
        agent.generate_session_start_message()

        # 3ターン目で整合性チェックが有効になることを確認（T-29: build_with_truncation 経由）
        calls_with_consistency = []

        original_build_trunc = prompt_builder.build_with_truncation

        def capture_build_trunc(*args, **kwargs):
            calls_with_consistency.append(kwargs.get("consistency_check_active", False))
            return original_build_trunc(*args, **kwargs)

        prompt_builder.build_with_truncation = capture_build_trunc

        for i in range(6):
            agent.process_turn(f"入力{i}")

        # message_count 3, 6 で active になる
        assert calls_with_consistency == [False, False, True, False, False, True]


# ---------------------------------------------------------------------------
# E2: 記憶システム統合（即時書込 → FTS5 検索 → プロンプト注入）
# ---------------------------------------------------------------------------


class TestMemorySystemIntegration:
    """記憶システム統合テスト (FR-3.3, FR-3.4, FR-3.7)."""

    def test_observation_write_then_fts5_search(self, db_conn):
        """observations への書込後に FTS5 検索で見つかること."""
        save_observation(db_conn, "今日は晴れて気持ちいい天気だね", "mascot", time.time())
        save_observation(db_conn, "プログラミングの勉強をしているよ", "user", time.time())

        # trigram なので最低3文字
        results = search_observations_fts(db_conn, "プログラミング")
        assert len(results) >= 1
        assert any("プログラミング" in r["content"] for r in results)

    def test_cold_memory_injected_into_prompt(
        self, db_conn, mock_llm_client, integration_config, persona_data_dir,
    ):
        """過去の observations が Cold Memory としてプロンプトに注入されること."""
        # 事前に observations を挿入（trigram 検索でマッチするよう
        # クエリ「プログラミングの勉強」と共通部分文字列を持つ内容にする）
        insert_test_observations(db_conn, [
            ("あたしはプログラミングが好きだよ", "mascot"),
            ("プログラミングの勉強を始めたんだ", "user"),
            ("プログラミング楽しいよね！", "mascot"),
        ])

        persona_system = PersonaSystem()
        prompt_builder = PromptBuilder(
            persona_core=SAMPLE_PERSONA_CORE.to_markdown(),
            style_samples=SAMPLE_STYLE_SAMPLES,
            human_block="",
        )
        agent = AgentCore(
            config=integration_config,
            db_conn=db_conn,
            llm_client=mock_llm_client,
            persona_system=persona_system,
            prompt_builder=prompt_builder,
            data_dir=persona_data_dir,
        )
        mock_llm_client.send_message_for_purpose.return_value = "挨拶"
        agent.generate_session_start_message()

        mock_llm_client.send_message_for_purpose.return_value = "プログラミング楽しいよね！"
        agent.process_turn("プログラミングの勉強")

        # LLM に渡された messages を検証（keyword 引数で呼ばれる前提）
        call_args = mock_llm_client.send_message_for_purpose.call_args_list[-1]
        messages = call_args.kwargs["messages"]

        # 最新の user メッセージに retrieved_memories が含まれることを確認
        last_user_msg = [m for m in messages if m["role"] == "user"][-1]
        assert "retrieved_memories" in last_user_msg["content"]

    def test_fts5_search_returns_empty_for_short_query(self, db_conn):
        """3文字未満のクエリで空リストが返ること (trigram 制約)."""
        save_observation(db_conn, "テストデータ", "user", time.time())
        results = search_observations_fts(db_conn, "テス")
        assert results == []

    def test_day_observations_retrieval(self, db_conn):
        """特定日の observations が正しく取得できること."""
        today = date.today().isoformat()
        now = time.time()
        save_observation(db_conn, "朝の挨拶", "user", now)
        save_observation(db_conn, "おはよう！", "mascot", now + 1)

        obs = get_day_observations(db_conn, today)
        assert len(obs) == 2
        assert obs[0]["content"] == "朝の挨拶"
        assert obs[1]["content"] == "おはよう！"


# ---------------------------------------------------------------------------
# E4: シャットダウン時サマリー生成（MemoryWorker 統合）
# ---------------------------------------------------------------------------


class TestShutdownSummaryGeneration:
    """シャットダウン時の日次サマリー生成テスト (FR-3.8, FR-7.5)."""

    def test_generate_daily_summary_with_real_db(self, db_conn, mock_llm_client):
        """実 DB で observations → サマリー生成 → day_summary 保存が動作すること."""
        today = date.today().isoformat()
        now = time.time()
        save_observation(db_conn, "今日は天気がいいね", "user", now)
        save_observation(db_conn, "そうだね！お出かけ日和だよ", "mascot", now + 1)
        save_observation(db_conn, "何して遊ぶ？", "user", now + 2)
        save_observation(db_conn, "公園に行こうよ！", "mascot", now + 3)

        mock_llm_client.send_message_for_purpose.return_value = (
            "今日はいい天気で、ユーザーさんと公園に行く約束をした。"
            "お出かけ日和で気分が良かった。楽しい一日になりそう。"
        )

        worker = MemoryWorker(db_conn, mock_llm_client)
        result = worker.generate_daily_summary(today)

        assert result is not None
        assert "公園" in result

        # day_summary に保存されたことを確認
        summaries = get_recent_day_summaries(db_conn, 7)
        assert len(summaries) == 1
        assert summaries[0]["date"] == today

    def test_generate_daily_summary_sync_handles_error(
        self, db_conn, mock_llm_client,
    ):
        """generate_daily_summary_sync がエラーを吸収して None を返すこと."""
        today = date.today().isoformat()
        save_observation(db_conn, "テスト", "user", time.time())

        mock_llm_client.send_message_for_purpose.side_effect = RuntimeError("API down")

        worker = MemoryWorker(db_conn, mock_llm_client)
        result = worker.generate_daily_summary_sync(today)

        assert result is None

    def test_summary_not_generated_without_observations(
        self, db_conn, mock_llm_client,
    ):
        """observations がない日にはサマリーが生成されないこと."""
        worker = MemoryWorker(db_conn, mock_llm_client)
        result = worker.generate_daily_summary("2026-01-01")

        assert result is None
        mock_llm_client.send_message_for_purpose.assert_not_called()


# ---------------------------------------------------------------------------
# E5: 起動時欠損補完
# ---------------------------------------------------------------------------


class TestMissingSummaryBackfill:
    """起動時の欠損日補完テスト (FR-3.10)."""

    def test_fill_missing_summaries_with_real_db(self, db_conn, mock_llm_client):
        """欠損日が検出されサマリーが補完されること."""
        # 昨日の observations を挿入
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        yesterday_dt = datetime.combine(
            date.today() - timedelta(days=1), datetime.min.time(),
        )
        ts = yesterday_dt.timestamp() + 3600  # 昨日の AM 1:00

        save_observation(db_conn, "昨日の会話1", "user", ts)
        save_observation(db_conn, "昨日の応答1", "mascot", ts + 1)

        # 欠損日が検出されること
        missing = get_missing_summary_dates(db_conn)
        assert yesterday in missing

        # 補完実行
        mock_llm_client.send_message_for_purpose.return_value = "昨日は楽しい会話をした。"
        worker = MemoryWorker(db_conn, mock_llm_client)
        filled = worker.check_and_fill_missing_summaries()

        assert yesterday in filled

        # day_summary に保存されたことを確認
        summaries = get_recent_day_summaries(db_conn, 7)
        assert any(s["date"] == yesterday for s in summaries)

    def test_no_backfill_when_no_missing_dates(self, db_conn, mock_llm_client):
        """欠損日がない場合は何も生成されないこと."""
        worker = MemoryWorker(db_conn, mock_llm_client)
        filled = worker.check_and_fill_missing_summaries()

        assert filled == []
        mock_llm_client.send_message_for_purpose.assert_not_called()

    def test_today_excluded_from_missing(self, db_conn, mock_llm_client):
        """今日の observations は欠損日として検出されないこと."""
        save_observation(db_conn, "今日の会話", "user", time.time())

        missing = get_missing_summary_dates(db_conn)
        today = date.today().isoformat()
        assert today not in missing

    def test_partial_failure_does_not_block_other_dates(
        self, db_conn, mock_llm_client,
    ):
        """1日の補完が失敗しても他の日には影響しないこと."""
        # 2日分の欠損を作成
        two_days_ago = (date.today() - timedelta(days=2)).isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()

        for day_offset in [2, 1]:
            d = date.today() - timedelta(days=day_offset)
            ts = datetime.combine(d, datetime.min.time()).timestamp() + 3600
            save_observation(db_conn, f"{day_offset}日前の会話", "user", ts)

        # 1回目は失敗、2回目は成功
        mock_llm_client.send_message_for_purpose.side_effect = [
            RuntimeError("API error"),
            "昨日のサマリー",
        ]

        worker = MemoryWorker(db_conn, mock_llm_client)
        filled = worker.check_and_fill_missing_summaries()

        # 2日前は失敗、昨日は成功
        assert yesterday in filled
        assert two_days_ago not in filled


# ---------------------------------------------------------------------------
# Warm Memory 統合
# ---------------------------------------------------------------------------


class TestWarmMemoryIntegration:
    """Warm Memory ロードの統合テスト (FR-3.6)."""

    def test_recent_summaries_loaded_into_prompt_builder(self, db_conn):
        """day_summary がプロンプトに反映されること."""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        save_day_summary(db_conn, yesterday, "昨日は楽しい一日だった。")

        summaries = get_recent_day_summaries(db_conn, 5)
        assert len(summaries) == 1

        builder = PromptBuilder(
            persona_core=SAMPLE_PERSONA_CORE.to_markdown(),
            style_samples=SAMPLE_STYLE_SAMPLES,
            human_block="",
            day_summaries=summaries,
        )
        system_prompt = builder.build_system_prompt()
        assert "recent_memories" in system_prompt
        assert "昨日は楽しい一日だった" in system_prompt

    def test_empty_summaries_omitted_from_prompt(self, db_conn):
        """day_summary が空の場合、日記セクションが省略されること."""
        summaries = get_recent_day_summaries(db_conn, 5)
        assert summaries == []

        builder = PromptBuilder(
            persona_core=SAMPLE_PERSONA_CORE.to_markdown(),
            style_samples=SAMPLE_STYLE_SAMPLES,
            human_block="",
            day_summaries=summaries,
        )
        system_prompt = builder.build_system_prompt()
        # S6 セクション（日記）が生成されていないことを確認
        # 注: S7 情報保護ブロック内に <recent_memories> の言及があるため
        # 日記特有のフレーズで確認する
        assert "日分の日記" not in system_prompt


# ---------------------------------------------------------------------------
# SessionContext 統合
# ---------------------------------------------------------------------------


class TestSessionContextIntegration:
    """SessionContext の統合テスト (FR-3.12)."""

    def test_session_id_format(self):
        """session_id が YYYYMMDD_HHMM_xxxxxxxx 形式であること."""
        import re
        sid = generate_session_id()
        assert len(sid) == 22
        assert re.match(r"\d{8}_\d{4}_[0-9a-f]{8}", sid)

    def test_session_id_uniqueness(self):
        """2回生成で異なる値が返ること."""
        sid1 = generate_session_id()
        sid2 = generate_session_id()
        assert sid1 != sid2

    def test_session_context_initial_state(self):
        """SessionContext の初期状態が正しいこと."""
        ctx = SessionContext()
        assert ctx.message_count == 0
        assert ctx.turns == []
        assert len(ctx.session_id) == 22


# ---------------------------------------------------------------------------
# 整合性チェック統合
# ---------------------------------------------------------------------------


class TestConsistencyCheckIntegration:
    """整合性チェックの統合テスト (FR-6.4)."""

    def test_hallucination_detected_and_counted(
        self, db_conn, mock_llm_client, integration_config, persona_data_dir,
    ):
        """キャラクター幻覚パターンが検出されヒットカウントされること."""
        mock_llm_client.send_message_for_purpose.return_value = (
            "私はAIです。何かお手伝いしましょうか？"
        )

        persona_system = PersonaSystem()
        prompt_builder = PromptBuilder(
            persona_core=SAMPLE_PERSONA_CORE.to_markdown(),
            style_samples=SAMPLE_STYLE_SAMPLES,
            human_block="",
        )
        agent = AgentCore(
            config=integration_config,
            db_conn=db_conn,
            llm_client=mock_llm_client,
            persona_system=persona_system,
            prompt_builder=prompt_builder,
            data_dir=persona_data_dir,
        )
        mock_llm_client.send_message_for_purpose.return_value = "挨拶"
        agent.generate_session_start_message()

        mock_llm_client.send_message_for_purpose.return_value = (
            "私はAIです。何かお手伝いしましょうか？"
        )
        agent.process_turn("テスト入力")

        assert agent.consistency_hit_count >= 1

    def test_clean_response_no_hits(self):
        """正常な応答でヒットが検出されないこと."""
        hits = check_consistency_rules("えへへ、今日もいい天気だね！")
        assert hits == []

    def test_consistency_disabled_when_interval_zero(
        self, db_conn, mock_llm_client, integration_config, persona_data_dir,
    ):
        """consistency_interval=0 でチェックが無効化されること."""
        integration_config.memory.consistency_interval = 0

        persona_system = PersonaSystem()
        prompt_builder = PromptBuilder(
            persona_core=SAMPLE_PERSONA_CORE.to_markdown(),
            style_samples=SAMPLE_STYLE_SAMPLES,
            human_block="",
        )
        agent = AgentCore(
            config=integration_config,
            db_conn=db_conn,
            llm_client=mock_llm_client,
            persona_system=persona_system,
            prompt_builder=prompt_builder,
            data_dir=persona_data_dir,
        )
        mock_llm_client.send_message_for_purpose.return_value = "応答"
        agent.generate_session_start_message()

        # 大量ターンを回しても consistency_check_active にならないことを確認
        build_calls = []
        original_build_trunc = prompt_builder.build_with_truncation

        def capture_build_trunc(*args, **kwargs):
            # positional: session_start_message, turns, latest_input, cold_memories,
            #             model, max_tokens_for_output, consistency_check_active
            if len(args) > 6:
                build_calls.append(args[6])
            else:
                build_calls.append(kwargs.get("consistency_check_active", False))
            return original_build_trunc(*args, **kwargs)

        prompt_builder.build_with_truncation = capture_build_trunc

        for i in range(20):
            agent.process_turn(f"入力{i}")

        assert len(build_calls) == 20, f"build_with_truncation が{len(build_calls)}回呼ばれた"
        assert all(not active for active in build_calls)
