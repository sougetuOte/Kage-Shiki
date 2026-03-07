"""Tests for memory/memory_worker.py — 日次サマリー生成 + 欠損補完.

対応 FR:
    FR-3.8: シャットダウン時の日次サマリー生成
    FR-3.10: 起動時の欠損日補完
    FR-7.5: サマリー生成失敗時のログ記録（EM-009）
"""

import sqlite3
from unittest.mock import Mock, patch

import pytest

from kage_shiki.agent.llm_client import LLMProtocol
from kage_shiki.memory.memory_worker import MemoryWorker

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_llm() -> Mock:
    """LLMProtocol のモック."""
    m = Mock(spec=LLMProtocol)
    m.send_message_for_purpose.return_value = (
        "今日はユーザーと天気の話をした。"
        "最近寒くなってきたねと言われた。"
        "温かいものが食べたいという話になった。"
    )
    return m


@pytest.fixture()
def mock_db_conn() -> Mock:
    """DB 接続のモック."""
    conn = Mock(spec=sqlite3.Connection)
    # 既存サマリーチェック: デフォルトは「未生成」（None）
    conn.execute.return_value.fetchone.return_value = None
    return conn


@pytest.fixture()
def worker(mock_db_conn: Mock, mock_llm: Mock) -> MemoryWorker:
    """MemoryWorker インスタンス."""
    return MemoryWorker(db_conn=mock_db_conn, llm_client=mock_llm)


# ---------------------------------------------------------------------------
# generate_daily_summary
# ---------------------------------------------------------------------------


class TestGenerateDailySummary:
    """日次サマリー生成テスト (FR-3.8)."""

    def test_generates_summary_from_observations(
        self, worker: MemoryWorker, mock_llm: Mock,
    ) -> None:
        """observations がある日にサマリーが生成されること."""
        observations = [
            {"content": "今日は寒いね", "speaker": "user", "created_at": 1709510400.0},
            {
                "content": "そうだね、温かいものが食べたいな",
                "speaker": "mascot",
                "created_at": 1709510460.0,
            },
        ]
        with patch(
            "kage_shiki.memory.memory_worker.get_day_observations",
            return_value=observations,
        ), patch(
            "kage_shiki.memory.memory_worker.save_day_summary",
        ):
            result = worker.generate_daily_summary("2026-03-03")
            assert result != ""
            mock_llm.send_message_for_purpose.assert_called_once()

    def test_returns_none_when_no_observations(
        self, worker: MemoryWorker, mock_llm: Mock,
    ) -> None:
        """observations がない日には None を返すこと."""
        with patch(
            "kage_shiki.memory.memory_worker.get_day_observations",
            return_value=[],
        ):
            result = worker.generate_daily_summary("2026-03-03")
            assert result is None
            mock_llm.send_message_for_purpose.assert_not_called()

    def test_saves_summary_to_db(
        self, worker: MemoryWorker,
    ) -> None:
        """生成されたサマリーが day_summary テーブルに保存されること."""
        observations = [
            {"content": "テスト", "speaker": "user", "created_at": 1709510400.0},
        ]
        with patch(
            "kage_shiki.memory.memory_worker.get_day_observations",
            return_value=observations,
        ), patch(
            "kage_shiki.memory.memory_worker.save_day_summary",
        ) as mock_save:
            worker.generate_daily_summary("2026-03-03")
            mock_save.assert_called_once()
            call_args = mock_save.call_args
            assert call_args.args[1] == "2026-03-03"

    def test_uses_memory_worker_purpose(
        self, worker: MemoryWorker, mock_llm: Mock,
    ) -> None:
        """purpose='memory_worker' で LLM を呼び出すこと."""
        observations = [
            {"content": "テスト", "speaker": "user", "created_at": 1709510400.0},
        ]
        with patch(
            "kage_shiki.memory.memory_worker.get_day_observations",
            return_value=observations,
        ), patch(
            "kage_shiki.memory.memory_worker.save_day_summary",
        ):
            worker.generate_daily_summary("2026-03-03")
            call_kwargs = mock_llm.send_message_for_purpose.call_args.kwargs
            assert call_kwargs["purpose"] == "memory_worker"

    def test_prompt_contains_observations(
        self, worker: MemoryWorker, mock_llm: Mock,
    ) -> None:
        """プロンプトに observations の内容が含まれること."""
        observations = [
            {"content": "今日は寒いね", "speaker": "user", "created_at": 1709510400.0},
            {"content": "温かいもの食べたい", "speaker": "mascot", "created_at": 1709510460.0},
        ]
        with patch(
            "kage_shiki.memory.memory_worker.get_day_observations",
            return_value=observations,
        ), patch(
            "kage_shiki.memory.memory_worker.save_day_summary",
        ):
            worker.generate_daily_summary("2026-03-03")
            call_kwargs = mock_llm.send_message_for_purpose.call_args.kwargs
            user_msg = call_kwargs["messages"][0]["content"]
            assert "今日は寒いね" in user_msg
            assert "温かいもの食べたい" in user_msg


# ---------------------------------------------------------------------------
# generate_daily_summary_sync
# ---------------------------------------------------------------------------


class TestGenerateDailySummarySync:
    """同期版サマリー生成テスト (FR-3.8, FR-7.5)."""

    def test_sync_success(
        self, worker: MemoryWorker,
    ) -> None:
        """同期版が正常に動作すること."""
        observations = [
            {"content": "テスト", "speaker": "user", "created_at": 1709510400.0},
        ]
        with patch(
            "kage_shiki.memory.memory_worker.get_day_observations",
            return_value=observations,
        ), patch(
            "kage_shiki.memory.memory_worker.save_day_summary",
        ):
            result = worker.generate_daily_summary_sync("2026-03-03")
            assert result is not None

    def test_sync_logs_on_failure(
        self, worker: MemoryWorker,
    ) -> None:
        """失敗時に EM-009 ログが記録されること (FR-7.5)."""
        with patch(
            "kage_shiki.memory.memory_worker.get_day_observations",
            side_effect=Exception("DB error"),
        ), patch(
            "kage_shiki.memory.memory_worker.logger",
        ) as mock_logger:
            result = worker.generate_daily_summary_sync("2026-03-03")
            assert result is None
            assert any(
                "EM-009" in str(c) for c in mock_logger.warning.call_args_list
            )

    def test_sync_does_not_raise(
        self, worker: MemoryWorker,
    ) -> None:
        """失敗時でも例外を送出しないこと."""
        with patch(
            "kage_shiki.memory.memory_worker.get_day_observations",
            side_effect=RuntimeError("unexpected"),
        ):
            result = worker.generate_daily_summary_sync("2026-03-03")
            assert result is None


# ---------------------------------------------------------------------------
# check_and_fill_missing_summaries
# ---------------------------------------------------------------------------


class TestCheckAndFillMissingSummaries:
    """起動時欠損補完テスト (FR-3.10)."""

    def test_fills_missing_dates(
        self, worker: MemoryWorker,
    ) -> None:
        """欠損日に対してサマリーが生成されること."""
        missing = ["2026-03-01", "2026-03-02"]
        observations = [
            {"content": "テスト", "speaker": "user", "created_at": 1709510400.0},
        ]
        with patch(
            "kage_shiki.memory.memory_worker.get_missing_summary_dates",
            return_value=missing,
        ), patch(
            "kage_shiki.memory.memory_worker.get_day_observations",
            return_value=observations,
        ), patch(
            "kage_shiki.memory.memory_worker.save_day_summary",
        ):
            filled = worker.check_and_fill_missing_summaries()
            assert filled == ["2026-03-01", "2026-03-02"]

    def test_no_missing_dates(
        self, worker: MemoryWorker,
    ) -> None:
        """欠損日がなければ空リストを返すこと."""
        with patch(
            "kage_shiki.memory.memory_worker.get_missing_summary_dates",
            return_value=[],
        ):
            filled = worker.check_and_fill_missing_summaries()
            assert filled == []

    def test_skips_dates_without_observations(
        self, worker: MemoryWorker,
    ) -> None:
        """observations がない欠損日はスキップされること."""
        missing = ["2026-03-01", "2026-03-02"]
        with patch(
            "kage_shiki.memory.memory_worker.get_missing_summary_dates",
            return_value=missing,
        ), patch(
            "kage_shiki.memory.memory_worker.get_day_observations",
            return_value=[],
        ):
            filled = worker.check_and_fill_missing_summaries()
            assert filled == []

    def test_continues_on_individual_failure(
        self, worker: MemoryWorker, mock_llm: Mock,
    ) -> None:
        """個別の日付で失敗しても他の日付は処理されること."""
        missing = ["2026-03-01", "2026-03-02"]
        observations = [
            {"content": "テスト", "speaker": "user", "created_at": 1709510400.0},
        ]
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("API error")
            return "サマリーテキスト"

        mock_llm.send_message_for_purpose.side_effect = side_effect
        with patch(
            "kage_shiki.memory.memory_worker.get_missing_summary_dates",
            return_value=missing,
        ), patch(
            "kage_shiki.memory.memory_worker.get_day_observations",
            return_value=observations,
        ), patch(
            "kage_shiki.memory.memory_worker.save_day_summary",
        ):
            filled = worker.check_and_fill_missing_summaries()
            assert "2026-03-02" in filled
