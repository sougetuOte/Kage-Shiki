"""永続状態ありの起動統合テスト (T-30).

対応 FR:
    FR-8.4: 2回目起動時に UNIQUE 制約エラーなしで起動できる

対応教訓:
    L-2: 永続状態の「2回目起動」テスト

テスト方針:
    - 実 SQLite ファイルDB（tmp_path）を使用
    - モック LLM で日次サマリー生成をシミュレート
    - 1回目: 会話 → サマリー生成 → DB クローズ
    - 2回目: 同 DB ファイルで再接続 → 欠損補完 → サマリー生成 → エラーなし確認

Building Checklist:
    [R-4] FR-8.4 を docstring に転記済み
    [R-5] 異常系テスト: test_second_startup_with_existing_summary_skipped
          （既存サマリー再生成スキップ）
    [R-8] 永続状態: 「2回目起動」テスト
"""

import sqlite3
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from kage_shiki.memory.db import Database, initialize_db, save_observation
from kage_shiki.memory.memory_worker import MemoryWorker

# テスト用固定日付（実行日に依存しないよう十分な過去日を使用）
_YESTERDAY = (date.today() - timedelta(days=1)).isoformat()
_TWO_DAYS_AGO = (date.today() - timedelta(days=2)).isoformat()
_THREE_DAYS_AGO = (date.today() - timedelta(days=3)).isoformat()

# ---------------------------------------------------------------------------
# FR-8.4: 2回目起動での UNIQUE 制約エラーなしテスト
# ---------------------------------------------------------------------------


class TestSecondStartup:
    """FR-8.4: 永続状態がある状態での2回目起動."""

    def test_second_startup_no_unique_constraint_error(
        self, tmp_path: Path,
    ) -> None:
        """FR-8.4 受入条件:
        (1) 1回目でサマリー生成確認
        (2) 2回目で UNIQUE 制約エラーなし

        手順:
        1. tmp_path に DB 作成
        2. モック LLM（send_message_for_purpose 実装）
        3. 1回目: AgentCore 起動相当 → observations 挿入 → サマリー生成 → DB クローズ
        4. 2回目: 同 DB ファイルで再接続 → check_and_fill_missing_summaries() → サマリー生成
        5. UNIQUE 制約エラーが発生しないことをアサート
        """
        db_path = tmp_path / "memory.db"
        # 過去日付（今日ではない）のタイムスタンプを使用（get_missing_summary_dates は今日を除外）
        yesterday_date = _YESTERDAY
        yesterday_ts = _date_to_timestamp(yesterday_date)

        mock_llm = MagicMock()
        mock_llm.send_message_for_purpose.return_value = "テスト日記エントリ"

        # === 1回目起動 ===
        db1 = Database(db_path)
        conn1 = db1.connect()
        initialize_db(conn1)

        # observations を昨日の日付で挿入
        save_observation(conn1, "こんにちは", "user", yesterday_ts, session_id="sess1")
        save_observation(conn1, "こんにちは", "mascot", yesterday_ts + 1, session_id="sess1")

        worker1 = MemoryWorker(conn1, mock_llm)
        summary1 = worker1.generate_daily_summary_sync(yesterday_date)
        assert summary1 == "テスト日記エントリ"

        # DB に1件のサマリーが存在することを確認
        row = conn1.execute(
            "SELECT summary FROM day_summary WHERE date = ?", (yesterday_date,),
        ).fetchone()
        assert row is not None
        assert row[0] == "テスト日記エントリ"

        db1.close()

        # === 2回目起動 ===
        db2 = Database(db_path)
        conn2 = db2.connect()
        initialize_db(conn2)  # IF NOT EXISTS なのでデータは保持される

        worker2 = MemoryWorker(conn2, mock_llm)

        # check_and_fill_missing_summaries() は UNIQUE 制約エラーを起こさないこと
        try:
            filled = worker2.check_and_fill_missing_summaries()
        except sqlite3.IntegrityError as e:
            pytest.fail(f"2回目起動で UNIQUE 制約エラーが発生した: {e}")

        # 昨日のサマリーは既存なのでスキップされる（filled に含まれない）
        assert yesterday_date not in filled

        # サマリーはまだ1件のみ（重複挿入されていない）
        count = conn2.execute("SELECT COUNT(*) FROM day_summary").fetchone()[0]
        assert count == 1

        # 2回目でも当日サマリー生成を呼んでエラーなし
        today_date = date.today().isoformat()
        # 今日はget_missing_summary_datesで除外されるので直接generate_daily_summary_syncをテスト
        # 今日の observations がない場合は None が返るだけ
        result = worker2.generate_daily_summary_sync(today_date)
        assert result is None  # observations がないので None

        db2.close()

    def test_second_startup_with_new_days_fills_missing(
        self, tmp_path: Path,
    ) -> None:
        """2回目起動時に未サマリー日がある場合、補完生成されること."""
        db_path = tmp_path / "memory.db"

        # 2日分の過去データ（異なる日付）
        day1 = _THREE_DAYS_AGO
        day2 = _TWO_DAYS_AGO
        day1_ts = _date_to_timestamp(day1)
        day2_ts = _date_to_timestamp(day2)

        mock_llm = MagicMock()
        mock_llm.send_message_for_purpose.side_effect = [
            "1日目の日記",
            "2日目の日記",
        ]

        # === 1回目: observations のみ挿入（サマリーなし）===
        db1 = Database(db_path)
        conn1 = db1.connect()
        initialize_db(conn1)
        save_observation(conn1, "1日目の会話", "user", day1_ts)
        save_observation(conn1, "1日目の応答", "mascot", day1_ts + 1)
        save_observation(conn1, "2日目の会話", "user", day2_ts)
        save_observation(conn1, "2日目の応答", "mascot", day2_ts + 1)
        db1.close()

        # === 2回目: 欠損補完 ===
        db2 = Database(db_path)
        conn2 = db2.connect()
        initialize_db(conn2)

        worker2 = MemoryWorker(conn2, mock_llm)
        filled = worker2.check_and_fill_missing_summaries()

        assert day1 in filled
        assert day2 in filled
        assert len(filled) == 2

        # サマリーが2件保存されていること
        count = conn2.execute("SELECT COUNT(*) FROM day_summary").fetchone()[0]
        assert count == 2

        db2.close()

    def test_existing_summary_not_duplicated(self, tmp_path: Path) -> None:
        """既存サマリーがある日に generate_daily_summary を呼んでも重複しない."""
        db_path = tmp_path / "memory.db"
        date_str = _YESTERDAY
        ts = _date_to_timestamp(date_str)

        mock_llm = MagicMock()
        mock_llm.send_message_for_purpose.return_value = "既存サマリー"

        db = Database(db_path)
        conn = db.connect()
        initialize_db(conn)

        # observations と1回目のサマリーを作成
        save_observation(conn, "テスト会話", "user", ts)
        worker = MemoryWorker(conn, mock_llm)
        first = worker.generate_daily_summary(date_str)
        assert first == "既存サマリー"

        # 2回目の呼び出し: 既存サマリーがあるので None が返る（スキップ）
        second = worker.generate_daily_summary(date_str)
        assert second is None

        # DBに重複がないこと
        count = conn.execute(
            "SELECT COUNT(*) FROM day_summary WHERE date = ?", (date_str,),
        ).fetchone()[0]
        assert count == 1

        db.close()


# ---------------------------------------------------------------------------
# ヘルパー関数
# ---------------------------------------------------------------------------


def _date_to_timestamp(date_str: str) -> float:
    """YYYY-MM-DD 文字列をローカルタイム正午のタイムスタンプに変換する.

    get_day_observations はローカルタイム（'localtime'）で日付境界を判定するため、
    ローカルタイムの正午を使用する。正午を選ぶことで、どのタイムゾーンでも
    同じ日付として判定される。
    """
    import datetime
    d = datetime.date.fromisoformat(date_str)
    dt = datetime.datetime(d.year, d.month, d.day, 12, 0, 0)
    return dt.timestamp()
