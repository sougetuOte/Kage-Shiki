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
from pathlib import Path

import pytest

from kage_shiki.memory.db import Database, initialize_db

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
            "INSERT INTO observations (content, speaker, created_at) "
            "VALUES (?, ?, ?)",
            ("今日はプログラミングをした", "user", now),
        )
        # 「プログラミング」が複数回出現するエントリ（より関連度が高い）
        db_conn.execute(
            "INSERT INTO observations (content, speaker, created_at) "
            "VALUES (?, ?, ?)",
            (
                "プログラミングが好きです。プログラミングは楽しい。"
                "プログラミングを毎日やっています",
                "mascot",
                now,
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

    def test_unsafe_pragma_name_raises(self, tmp_path: Path) -> None:
        """不正な PRAGMA 名で ValueError が発生すること."""
        from unittest.mock import patch

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

    def test_unsafe_pragma_value_raises(self, tmp_path: Path) -> None:
        """不正な PRAGMA 値で ValueError が発生すること."""
        from unittest.mock import patch

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


def _get_column_info(conn: sqlite3.Connection, table_name: str) -> list[dict]:
    """テーブルのカラム情報を取得する."""
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
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
