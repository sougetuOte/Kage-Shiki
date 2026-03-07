"""Tests for memory/db.py — SQLite DB 初期化 + スキーマ定義 + FTS5 トリガー.

対応 FR:
    FR-3.1: SQLite DB を初期化し、observations / observations_fts /
            day_summary / curiosity_targets テーブルを作成
    FR-3.2: FTS5 INSERT トリガーにより observations 書込時に
            全文検索インデックスを自動同期

対応設計:
    D-4: INSERT トリガー方式（Phase 1 は INSERT のみ）
    D-7: WAL モード、VACUUM なし（Phase 1 では自動 VACUUM 不使用）
"""

import sqlite3
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from kage_shiki.memory.db import (
    Database,
    _retry_on_lock,
    get_day_observations,
    get_missing_summary_dates,
    get_recent_day_summaries,
    initialize_db,
    save_day_summary,
    save_observation,
    search_observations_fts,
)

# ---------------------------------------------------------------------------
# FR-3.1: DB 初期化 — テーブル作成
# ---------------------------------------------------------------------------


class TestDatabaseConnection:
    """Database クラスの接続管理テスト."""

    def test_connect_creates_db_file(self, tmp_path: Path) -> None:
        """DB ファイルが指定パスに作成されること."""
        db_path = tmp_path / "test.db"
        db = Database(db_path)
        conn = db.connect()
        try:
            assert db_path.exists()
        finally:
            conn.close()
            db.close()

    def test_context_manager_returns_connection(self, tmp_path: Path) -> None:
        """コンテキストマネージャが sqlite3.Connection を返すこと."""
        db_path = tmp_path / "test.db"
        with Database(db_path) as conn:
            assert isinstance(conn, sqlite3.Connection)

    def test_context_manager_closes_on_exit(self, tmp_path: Path) -> None:
        """コンテキストマネージャ終了時に接続が閉じられること."""
        db_path = tmp_path / "test.db"
        db = Database(db_path)
        with db as conn:
            conn.execute("SELECT 1")
        # close 後に操作するとエラーになることを確認
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")

    def test_row_factory_is_row(self, tmp_path: Path) -> None:
        """row_factory が sqlite3.Row に設定されること."""
        db_path = tmp_path / "test.db"
        with Database(db_path) as conn:
            assert conn.row_factory is sqlite3.Row


class TestPragmaSettings:
    """PRAGMA 設定のテスト（D-7）."""

    def test_journal_mode_is_wal(self, tmp_path: Path) -> None:
        """journal_mode が WAL に設定されること."""
        db_path = tmp_path / "test.db"
        with Database(db_path) as conn:
            result = conn.execute("PRAGMA journal_mode").fetchone()
            assert result[0] == "wal"

    def test_cache_size_is_2000(self, tmp_path: Path) -> None:
        """cache_size が -2000 に設定されること."""
        db_path = tmp_path / "test.db"
        with Database(db_path) as conn:
            result = conn.execute("PRAGMA cache_size").fetchone()
            assert result[0] == -2000


class TestInitializeDbTables:
    """initialize_db によるテーブル作成テスト（FR-3.1）."""

    def test_observations_table_exists(self, db_conn: sqlite3.Connection) -> None:
        """observations テーブルが存在すること."""
        tables = _get_table_names(db_conn)
        assert "observations" in tables

    def test_observations_fts_table_exists(self, db_conn: sqlite3.Connection) -> None:
        """observations_fts 仮想テーブルが存在すること."""
        # FTS5 仮想テーブルは sqlite_master で type='table' として登録される
        tables = _get_table_names(db_conn)
        assert "observations_fts" in tables

    def test_day_summary_table_exists(self, db_conn: sqlite3.Connection) -> None:
        """day_summary テーブルが存在すること."""
        tables = _get_table_names(db_conn)
        assert "day_summary" in tables

    def test_curiosity_targets_table_exists(self, db_conn: sqlite3.Connection) -> None:
        """curiosity_targets テーブルが存在すること（Phase 2 予約）."""
        tables = _get_table_names(db_conn)
        assert "curiosity_targets" in tables

    def test_curiosity_targets_index_exists(self, db_conn: sqlite3.Connection) -> None:
        """idx_curiosity_status インデックスが存在すること."""
        indexes = _get_index_names(db_conn)
        assert "idx_curiosity_status" in indexes

    def test_observations_columns(self, db_conn: sqlite3.Connection) -> None:
        """observations テーブルのカラムが仕様と一致すること."""
        columns = _get_column_info(db_conn, "observations")
        expected_names = {"id", "content", "speaker", "created_at", "session_id", "embedding"}
        assert {col["name"] for col in columns} == expected_names

    def test_observations_content_not_null(self, db_conn: sqlite3.Connection) -> None:
        """observations.content が NOT NULL であること."""
        columns = _get_column_info(db_conn, "observations")
        content_col = next(c for c in columns if c["name"] == "content")
        assert content_col["notnull"] == 1

    def test_observations_speaker_not_null(self, db_conn: sqlite3.Connection) -> None:
        """observations.speaker が NOT NULL であること."""
        columns = _get_column_info(db_conn, "observations")
        speaker_col = next(c for c in columns if c["name"] == "speaker")
        assert speaker_col["notnull"] == 1

    def test_observations_created_at_not_null(self, db_conn: sqlite3.Connection) -> None:
        """observations.created_at が NOT NULL であること."""
        columns = _get_column_info(db_conn, "observations")
        created_at_col = next(c for c in columns if c["name"] == "created_at")
        assert created_at_col["notnull"] == 1

    def test_day_summary_columns(self, db_conn: sqlite3.Connection) -> None:
        """day_summary テーブルのカラムが仕様と一致すること."""
        columns = _get_column_info(db_conn, "day_summary")
        expected_names = {"id", "date", "summary", "created_at"}
        assert {col["name"] for col in columns} == expected_names

    def test_day_summary_date_unique(self, db_conn: sqlite3.Connection) -> None:
        """day_summary.date が UNIQUE 制約を持つこと."""
        now = time.time()
        db_conn.execute(
            "INSERT INTO day_summary (date, summary, created_at) VALUES (?, ?, ?)",
            ("2026-03-01", "test summary", now),
        )
        with pytest.raises(sqlite3.IntegrityError):
            db_conn.execute(
                "INSERT INTO day_summary (date, summary, created_at) VALUES (?, ?, ?)",
                ("2026-03-01", "duplicate", now),
            )

    def test_curiosity_targets_columns(self, db_conn: sqlite3.Connection) -> None:
        """curiosity_targets テーブルのカラムが仕様と一致すること."""
        columns = _get_column_info(db_conn, "curiosity_targets")
        expected_names = {
            "id", "topic", "status", "priority",
            "parent_id", "created_at", "result_summary",
        }
        assert {col["name"] for col in columns} == expected_names


# ---------------------------------------------------------------------------
# FR-3.2: FTS5 INSERT トリガー
# ---------------------------------------------------------------------------


class TestFts5Trigger:
    """FTS5 INSERT トリガーのテスト（FR-3.2, D-4）."""

    def test_fts5_insert_trigger_exists(self, db_conn: sqlite3.Connection) -> None:
        """observations_fts_insert トリガーが存在すること."""
        triggers = _get_trigger_names(db_conn)
        assert "observations_fts_insert" in triggers

    def test_insert_syncs_to_fts5(self, db_conn: sqlite3.Connection) -> None:
        """observations への INSERT 後に FTS5 検索可能であること."""
        now = time.time()
        db_conn.execute(
            "INSERT INTO observations (content, speaker, created_at, session_id) "
            "VALUES (?, ?, ?, ?)",
            ("今日はとても良い天気ですね", "mascot", now, "test_session"),
        )
        db_conn.commit()

        # trigram トークナイザは最低3文字のクエリが必要
        results = db_conn.execute(
            "SELECT o.content FROM observations_fts "
            "JOIN observations o ON observations_fts.rowid = o.id "
            "WHERE observations_fts MATCH ?",
            ("良い天気",),
        ).fetchall()
        assert len(results) == 1
        assert results[0]["content"] == "今日はとても良い天気ですね"

    def test_multiple_inserts_all_searchable(self, db_conn: sqlite3.Connection) -> None:
        """複数 INSERT 後に全件が FTS5 検索可能であること."""
        now = time.time()
        entries = [
            ("猫が好きです", "user"),
            ("私も猫が大好きです", "mascot"),
            ("犬も可愛いですよね", "user"),
        ]
        for content, speaker in entries:
            db_conn.execute(
                "INSERT INTO observations (content, speaker, created_at, session_id) "
                "VALUES (?, ?, ?, ?)",
                (content, speaker, now, "test_session"),
            )
        db_conn.commit()

        # trigram: 3文字以上 「猫が好き」で検索 → 1件ヒット
        results = db_conn.execute(
            "SELECT o.content FROM observations_fts "
            "JOIN observations o ON observations_fts.rowid = o.id "
            "WHERE observations_fts MATCH ?",
            ("猫が好き",),
        ).fetchall()
        assert len(results) == 1

        # 「大好きです」で検索 → 1件ヒット
        results2 = db_conn.execute(
            "SELECT o.content FROM observations_fts "
            "JOIN observations o ON observations_fts.rowid = o.id "
            "WHERE observations_fts MATCH ?",
            ("大好きです",),
        ).fetchall()
        assert len(results2) == 1

    def test_bm25_ordering(self, db_conn: sqlite3.Connection) -> None:
        """BM25 スコアリングで関連度の高い結果が先頭に来ること."""
        now = time.time()
        # 「プログラミング」が1回だけ出現するエントリ
        db_conn.execute(
            "INSERT INTO observations (content, speaker, created_at, session_id) "
            "VALUES (?, ?, ?, ?)",
            ("今日はプログラミングをした", "user", now, "test_session"),
        )
        # 「プログラミング」が複数回出現するエントリ（より関連度が高い）
        db_conn.execute(
            "INSERT INTO observations (content, speaker, created_at, session_id) "
            "VALUES (?, ?, ?, ?)",
            (
                "プログラミングが好きです。プログラミングは楽しい。"
                "プログラミングを毎日やっています",
                "mascot",
                now,
                "test_session",
            ),
        )
        db_conn.commit()

        # trigram: 「プログラミング」で検索 → 2件ヒット、BM25 順
        results = db_conn.execute(
            "SELECT o.content FROM observations_fts "
            "JOIN observations o ON observations_fts.rowid = o.id "
            "WHERE observations_fts MATCH ? "
            "ORDER BY bm25(observations_fts)",
            ("プログラミング",),
        ).fetchall()
        assert len(results) == 2
        # BM25 はスコアが低い（負の値が小さい）ほど関連度が高い
        # より多く「プログラミング」を含むエントリが先頭に来る
        assert "プログラミングが好きです" in results[0]["content"]

    def test_trigram_min_3_chars(self, db_conn: sqlite3.Connection) -> None:
        """trigram トークナイザの最低3文字制約の確認."""
        now = time.time()
        db_conn.execute(
            "INSERT INTO observations (content, speaker, created_at) "
            "VALUES (?, ?, ?)",
            ("今日は良い天気です", "user", now),
        )
        db_conn.commit()

        # 2文字クエリ → 0件（trigram の仕様）
        results = db_conn.execute(
            "SELECT o.content FROM observations_fts "
            "JOIN observations o ON observations_fts.rowid = o.id "
            "WHERE observations_fts MATCH ?",
            ("天気",),
        ).fetchall()
        assert len(results) == 0

        # 3文字クエリ → 1件
        results3 = db_conn.execute(
            "SELECT o.content FROM observations_fts "
            "JOIN observations o ON observations_fts.rowid = o.id "
            "WHERE observations_fts MATCH ?",
            ("良い天",),
        ).fetchall()
        assert len(results3) == 1

    def test_fts5_no_match_returns_empty(self, db_conn: sqlite3.Connection) -> None:
        """FTS5 検索でヒットなしの場合、空リストを返すこと."""
        now = time.time()
        db_conn.execute(
            "INSERT INTO observations (content, speaker, created_at) "
            "VALUES (?, ?, ?)",
            ("今日は良い天気", "user", now),
        )
        db_conn.commit()

        results = db_conn.execute(
            "SELECT o.content FROM observations_fts "
            "JOIN observations o ON observations_fts.rowid = o.id "
            "WHERE observations_fts MATCH ?",
            ("プログラミング",),
        ).fetchall()
        assert len(results) == 0


# ---------------------------------------------------------------------------
# 異常系テスト [R-5]
# ---------------------------------------------------------------------------


class TestInitializeDbIdempotent:
    """initialize_db の冪等性テスト."""

    def test_double_initialize_is_safe(self, tmp_path: Path) -> None:
        """2回呼び出してもエラーにならないこと（IF NOT EXISTS）."""
        db_path = tmp_path / "memory.db"
        with Database(db_path) as conn:
            initialize_db(conn)
            initialize_db(conn)  # 2回目 — エラーなし
            tables = _get_table_names(conn)
            assert "observations" in tables

    def test_initialize_preserves_existing_data(self, tmp_path: Path) -> None:
        """再初期化で既存データが消えないこと."""
        db_path = tmp_path / "memory.db"
        with Database(db_path) as conn:
            initialize_db(conn)
            now = time.time()
            conn.execute(
                "INSERT INTO observations (content, speaker, created_at) "
                "VALUES (?, ?, ?)",
                ("test data", "user", now),
            )
            conn.commit()

            # 再初期化
            initialize_db(conn)

            count = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
            assert count == 1


class TestPragmaValidation:
    """PRAGMA バリデーションテスト（W-1: SQL インジェクション防止）."""

    def test_unsafe_pragma_name_raises(self) -> None:
        """不正な PRAGMA 名で ValueError が発生すること."""
        from kage_shiki.memory.db import _configure_pragmas

        conn = sqlite3.connect(":memory:")
        try:
            with patch(
                "kage_shiki.memory.db._PRAGMA_SETTINGS",
                {"journal_mode; DROP TABLE x": "WAL"},
            ), pytest.raises(ValueError, match="不正な PRAGMA 名"):
                _configure_pragmas(conn)
        finally:
            conn.close()

    def test_unsafe_pragma_value_raises(self) -> None:
        """不正な PRAGMA 値で ValueError が発生すること."""
        from kage_shiki.memory.db import _configure_pragmas

        conn = sqlite3.connect(":memory:")
        try:
            with patch(
                "kage_shiki.memory.db._PRAGMA_SETTINGS",
                {"journal_mode": "WAL; DROP TABLE x"},
            ), pytest.raises(ValueError, match="不正な PRAGMA 値"):
                _configure_pragmas(conn)
        finally:
            conn.close()


class TestDatabaseDoubleConnect:
    """Database の二重接続ガードテスト（INFO-002）."""

    def test_double_connect_closes_previous(self, tmp_path: Path) -> None:
        """connect() の再呼び出しで前の接続が閉じられること."""
        db_path = tmp_path / "test.db"
        db = Database(db_path)
        conn1 = db.connect()
        conn1.execute("SELECT 1")  # 接続が有効であること

        conn2 = db.connect()  # 再接続
        assert conn2 is not conn1

        # conn1 は閉じられているため操作不可
        with pytest.raises(sqlite3.ProgrammingError):
            conn1.execute("SELECT 1")

        db.close()


class TestDatabasePathHandling:
    """DB パスに関するエッジケーステスト."""

    def test_parent_directory_not_exist(self, tmp_path: Path) -> None:
        """親ディレクトリが存在しない場合に適切にエラーになること."""
        db_path = tmp_path / "nonexistent" / "subdir" / "memory.db"
        with pytest.raises(sqlite3.OperationalError), Database(db_path) as conn:
            initialize_db(conn)

    def test_memory_db_in_memory(self) -> None:
        """:memory: DB でも初期化が成功すること."""
        with Database(":memory:") as conn:
            initialize_db(conn)
            tables = _get_table_names(conn)
            assert "observations" in tables
            assert "observations_fts" in tables
            assert "day_summary" in tables
            assert "curiosity_targets" in tables


# ---------------------------------------------------------------------------
# ヘルパー関数
# ---------------------------------------------------------------------------


def _get_table_names(conn: sqlite3.Connection) -> set[str]:
    """DB 内の全テーブル名を取得する."""
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    return {row[0] for row in rows}


def _get_index_names(conn: sqlite3.Connection) -> set[str]:
    """DB 内の全インデックス名を取得する."""
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index'"
    ).fetchall()
    return {row[0] for row in rows}


def _get_trigger_names(conn: sqlite3.Connection) -> set[str]:
    """DB 内の全トリガー名を取得する."""
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='trigger'"
    ).fetchall()
    return {row[0] for row in rows}


_ALLOWED_TABLES = frozenset({"observations", "day_summary", "curiosity_targets"})


def _get_column_info(conn: sqlite3.Connection, table_name: str) -> list[dict]:
    """テーブルのカラム情報を取得する."""
    if table_name not in _ALLOWED_TABLES:
        msg = f"許可されていないテーブル名: {table_name}"
        raise ValueError(msg)
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()  # noqa: S608
    return [
        {
            "name": row[1],
            "type": row[2],
            "notnull": row[3],
            "default": row[4],
            "pk": row[5],
        }
        for row in rows
    ]


# ---------------------------------------------------------------------------
# FR-3.3: save_observation — observations 即時書込 (T-06)
# ---------------------------------------------------------------------------


class TestSaveObservation:
    """save_observation 関数のテスト (FR-3.3)."""

    def test_save_and_retrieve(self, db_conn: sqlite3.Connection) -> None:
        """INSERT 後に SELECT で取得できること."""
        now = time.time()
        rowid = save_observation(db_conn, "テスト内容", "user", now, "session_001")
        assert rowid > 0
        row = db_conn.execute(
            "SELECT content, speaker, created_at, session_id "
            "FROM observations WHERE id = ?",
            (rowid,),
        ).fetchone()
        assert row["content"] == "テスト内容"
        assert row["speaker"] == "user"
        assert row["created_at"] == now
        assert row["session_id"] == "session_001"

    def test_save_without_session_id(self, db_conn: sqlite3.Connection) -> None:
        """session_id なしで保存できること."""
        now = time.time()
        rowid = save_observation(db_conn, "内容", "mascot", now)
        row = db_conn.execute(
            "SELECT session_id FROM observations WHERE id = ?", (rowid,),
        ).fetchone()
        assert row["session_id"] is None

    def test_fts5_sync_after_save(self, db_conn: sqlite3.Connection) -> None:
        """save_observation 後に FTS5 検索可能であること."""
        now = time.time()
        save_observation(
            db_conn, "今日はプログラミングを楽しんだ", "user", now, "s1",
        )
        results = search_observations_fts(db_conn, "プログラミング")
        assert len(results) == 1
        assert results[0]["content"] == "今日はプログラミングを楽しんだ"

    def test_returns_incrementing_rowid(
        self, db_conn: sqlite3.Connection,
    ) -> None:
        """連続 INSERT で rowid が増加すること."""
        now = time.time()
        rowid1 = save_observation(db_conn, "one", "user", now)
        rowid2 = save_observation(db_conn, "two", "user", now)
        assert rowid2 > rowid1


# ---------------------------------------------------------------------------
# FR-3.4: search_observations_fts — FTS5 検索 (T-06)
# ---------------------------------------------------------------------------


class TestSearchObservationsFts:
    """search_observations_fts 関数のテスト (FR-3.4)."""

    def test_bm25_ordering(self, db_conn: sqlite3.Connection) -> None:
        """BM25 スコアリングで関連度順に並ぶこと."""
        now = time.time()
        # 低関連度: 「プログラミング」が1回 + 他の話題
        save_observation(
            db_conn,
            "今日はプログラミングをした。天気も良かった。散歩にも行った。",
            "user", now, "s1",
        )
        # 高関連度: 「プログラミング」が3回
        save_observation(
            db_conn,
            "プログラミングが好きです。プログラミングは楽しい。"
            "プログラミングを毎日やっています",
            "mascot", now, "s1",
        )
        results = search_observations_fts(db_conn, "プログラミング")
        assert len(results) == 2
        assert "プログラミングが好きです" in results[0]["content"]

    def test_top_k_limit(self, db_conn: sqlite3.Connection) -> None:
        """top_k でヒット数が制限されること."""
        now = time.time()
        for i in range(10):
            save_observation(
                db_conn, f"テスト用の文章番号{i:03d}です", "user", now, "s1",
            )
        results = search_observations_fts(db_conn, "テスト用の", top_k=3)
        assert len(results) == 3

    def test_empty_results(self, db_conn: sqlite3.Connection) -> None:
        """ヒットなしの場合空リストを返すこと."""
        now = time.time()
        save_observation(db_conn, "プログラミング最高", "user", now, "s1")
        results = search_observations_fts(db_conn, "存在しないキーワード")
        assert results == []

    def test_short_query_returns_empty(
        self, db_conn: sqlite3.Connection,
    ) -> None:
        """3文字未満のクエリで空リストを返すこと."""
        now = time.time()
        save_observation(db_conn, "テスト内容です", "user", now, "s1")
        assert search_observations_fts(db_conn, "テス") == []
        assert search_observations_fts(db_conn, "テ") == []
        assert search_observations_fts(db_conn, "") == []

    def test_result_dict_fields(self, db_conn: sqlite3.Connection) -> None:
        """結果の dict に必要なフィールドが含まれること."""
        now = time.time()
        save_observation(
            db_conn, "テスト用コンテンツです", "mascot", now, "sess_123",
        )
        results = search_observations_fts(db_conn, "テスト用コンテンツ")
        assert len(results) == 1
        r = results[0]
        assert r["content"] == "テスト用コンテンツです"
        assert r["speaker"] == "mascot"
        assert r["created_at"] == now
        assert r["session_id"] == "sess_123"


# ---------------------------------------------------------------------------
# get_day_observations — 日次サマリー生成用 (T-06)
# ---------------------------------------------------------------------------


class TestGetDayObservations:
    """get_day_observations 関数のテスト."""

    def test_returns_observations_for_date(
        self, db_conn: sqlite3.Connection,
    ) -> None:
        """指定日の observations を返すこと."""
        today = date.today()
        start_ts = datetime.combine(today, datetime.min.time()).timestamp()
        save_observation(db_conn, "朝の挨拶", "user", start_ts + 3600, "s1")
        save_observation(db_conn, "おはよう", "mascot", start_ts + 3660, "s1")
        results = get_day_observations(db_conn, today.isoformat())
        assert len(results) == 2
        assert results[0]["content"] == "朝の挨拶"
        assert results[1]["content"] == "おはよう"

    def test_excludes_other_dates(
        self, db_conn: sqlite3.Connection,
    ) -> None:
        """他の日の observations を含まないこと."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        today_ts = datetime.combine(today, datetime.min.time()).timestamp()
        yesterday_ts = datetime.combine(
            yesterday, datetime.min.time(),
        ).timestamp()
        save_observation(db_conn, "今日", "user", today_ts + 100, "s1")
        save_observation(db_conn, "昨日", "user", yesterday_ts + 100, "s1")

        results = get_day_observations(db_conn, today.isoformat())
        assert len(results) == 1
        assert results[0]["content"] == "今日"

    def test_no_observations(self, db_conn: sqlite3.Connection) -> None:
        """該当日に observations がない場合空リストを返すこと."""
        results = get_day_observations(db_conn, "2099-01-01")
        assert results == []

    def test_ordered_by_created_at(
        self, db_conn: sqlite3.Connection,
    ) -> None:
        """created_at の昇順で返すこと."""
        today = date.today()
        base_ts = datetime.combine(today, datetime.min.time()).timestamp()
        save_observation(db_conn, "後", "user", base_ts + 7200, "s1")
        save_observation(db_conn, "先", "user", base_ts + 3600, "s1")

        results = get_day_observations(db_conn, today.isoformat())
        assert results[0]["content"] == "先"
        assert results[1]["content"] == "後"


# ---------------------------------------------------------------------------
# get_missing_summary_dates — 欠損日検出 (T-06)
# ---------------------------------------------------------------------------


class TestGetMissingSummaryDates:
    """get_missing_summary_dates 関数のテスト."""

    def test_detects_missing_date(self, db_conn: sqlite3.Connection) -> None:
        """summary がない過去の日を検出すること."""
        yesterday = date.today() - timedelta(days=1)
        ts = datetime.combine(
            yesterday, datetime.min.time(),
        ).timestamp() + 3600
        save_observation(db_conn, "昨日の会話", "user", ts, "s1")

        missing = get_missing_summary_dates(db_conn)
        assert yesterday.isoformat() in missing

    def test_excludes_summarized_date(
        self, db_conn: sqlite3.Connection,
    ) -> None:
        """summary がある日は含まないこと."""
        yesterday = date.today() - timedelta(days=1)
        ts = datetime.combine(
            yesterday, datetime.min.time(),
        ).timestamp() + 3600
        save_observation(db_conn, "昨日", "user", ts, "s1")
        save_day_summary(db_conn, yesterday.isoformat(), "昨日のまとめ")

        missing = get_missing_summary_dates(db_conn)
        assert yesterday.isoformat() not in missing

    def test_excludes_today(self, db_conn: sqlite3.Connection) -> None:
        """今日の日付は含まないこと."""
        today = date.today()
        ts = datetime.combine(today, datetime.min.time()).timestamp() + 3600
        save_observation(db_conn, "今日の会話", "user", ts, "s1")

        missing = get_missing_summary_dates(db_conn)
        assert today.isoformat() not in missing

    def test_empty_when_no_observations(
        self, db_conn: sqlite3.Connection,
    ) -> None:
        """observations がない場合空リストを返すこと."""
        missing = get_missing_summary_dates(db_conn)
        assert missing == []

    def test_sorted_ascending(self, db_conn: sqlite3.Connection) -> None:
        """結果が昇順ソートされること."""
        base = date.today() - timedelta(days=5)
        for i in [3, 1, 2]:
            d = base + timedelta(days=i)
            ts = datetime.combine(d, datetime.min.time()).timestamp() + 3600
            save_observation(
                db_conn, f"day {i}", "user", ts, "s1",
            )

        missing = get_missing_summary_dates(db_conn)
        assert missing == sorted(missing)


# ---------------------------------------------------------------------------
# save_day_summary (T-06)
# ---------------------------------------------------------------------------


class TestSaveDaySummary:
    """save_day_summary 関数のテスト."""

    def test_save_and_retrieve(self, db_conn: sqlite3.Connection) -> None:
        """保存したサマリーが取得できること."""
        save_day_summary(db_conn, "2026-03-01", "今日は楽しい一日でした。")
        row = db_conn.execute(
            "SELECT date, summary FROM day_summary WHERE date = ?",
            ("2026-03-01",),
        ).fetchone()
        assert row["date"] == "2026-03-01"
        assert row["summary"] == "今日は楽しい一日でした。"

    def test_duplicate_date_raises(
        self, db_conn: sqlite3.Connection,
    ) -> None:
        """同一日のサマリーを重複 INSERT すると IntegrityError."""
        save_day_summary(db_conn, "2026-03-01", "初回")
        with pytest.raises(sqlite3.IntegrityError):
            save_day_summary(db_conn, "2026-03-01", "重複")


# ---------------------------------------------------------------------------
# get_recent_day_summaries — 直近 N 日分のサマリー取得 (T-25, FR-3.6)
# ---------------------------------------------------------------------------


class TestGetRecentDaySummaries:
    """get_recent_day_summaries 関数のテスト (FR-3.6)."""

    def test_empty_table_returns_empty_list(
        self, db_conn: sqlite3.Connection,
    ) -> None:
        """空の day_summary テーブルで空リストが返ること."""
        result = get_recent_day_summaries(db_conn, days=5)
        assert result == []

    def test_returns_latest_n_days(self, db_conn: sqlite3.Connection) -> None:
        """3件のサマリーを INSERT して days=2 で最新2件が返ること."""
        save_day_summary(db_conn, "2026-03-01", "3月1日のサマリー")
        save_day_summary(db_conn, "2026-03-02", "3月2日のサマリー")
        save_day_summary(db_conn, "2026-03-03", "3月3日のサマリー")

        result = get_recent_day_summaries(db_conn, days=2)
        assert len(result) == 2
        # 最新2件は 2026-03-02 と 2026-03-03
        dates = [r["date"] for r in result]
        assert "2026-03-02" in dates
        assert "2026-03-03" in dates
        assert "2026-03-01" not in dates

    def test_result_is_ascending_by_date(
        self, db_conn: sqlite3.Connection,
    ) -> None:
        """結果が日付昇順（古い日付が先）であること."""
        save_day_summary(db_conn, "2026-03-03", "3日")
        save_day_summary(db_conn, "2026-03-01", "1日")
        save_day_summary(db_conn, "2026-03-02", "2日")

        result = get_recent_day_summaries(db_conn, days=3)
        assert len(result) == 3
        assert result[0]["date"] == "2026-03-01"
        assert result[1]["date"] == "2026-03-02"
        assert result[2]["date"] == "2026-03-03"

    def test_days_zero_returns_empty_list(
        self, db_conn: sqlite3.Connection,
    ) -> None:
        """days=0 で空リストが返ること."""
        save_day_summary(db_conn, "2026-03-01", "サマリー")
        result = get_recent_day_summaries(db_conn, days=0)
        assert result == []

    def test_result_dict_structure(self, db_conn: sqlite3.Connection) -> None:
        """結果の各要素が date と summary キーを持つ dict であること."""
        save_day_summary(db_conn, "2026-03-01", "今日は晴れでした。")
        result = get_recent_day_summaries(db_conn, days=1)
        assert len(result) == 1
        assert result[0]["date"] == "2026-03-01"
        assert result[0]["summary"] == "今日は晴れでした。"


# ---------------------------------------------------------------------------
# _retry_on_lock — DB ロックリトライ (FR-7.3, T-06)
# ---------------------------------------------------------------------------


class TestRetryOnLock:
    """_retry_on_lock デコレータのテスト (FR-7.3, EM-008)."""

    @patch("kage_shiki.memory.db.time.sleep")
    def test_succeeds_after_retries(self, mock_sleep) -> None:
        """リトライ後に成功すること."""
        call_count = 0

        @_retry_on_lock
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise sqlite3.OperationalError("database is locked")
            return "success"

        result = flaky()
        assert result == "success"
        assert call_count == 3
        assert mock_sleep.call_count == 2

    @patch("kage_shiki.memory.db.time.sleep")
    def test_raises_after_max_retries(self, mock_sleep) -> None:
        """最大リトライ回数超過で例外が送出されること."""

        @_retry_on_lock
        def always_locked():
            raise sqlite3.OperationalError("database is locked")

        with pytest.raises(sqlite3.OperationalError, match="locked"):
            always_locked()

    def test_non_lock_error_not_retried(self) -> None:
        """locked 以外の OperationalError はリトライしないこと."""
        call_count = 0

        @_retry_on_lock
        def other_error():
            nonlocal call_count
            call_count += 1
            raise sqlite3.OperationalError("no such table")

        with pytest.raises(sqlite3.OperationalError, match="no such table"):
            other_error()
        assert call_count == 1
