"""SQLite DB 初期化 + スキーマ定義 + FTS5 トリガー (T-05).

対応 FR:
    FR-3.1: SQLite DB を初期化し、observations / observations_fts /
            day_summary / curiosity_targets テーブルを作成
    FR-3.2: FTS5 INSERT トリガーにより observations 書込時に
            全文検索インデックスを自動同期

対応設計:
    D-4: INSERT トリガー方式（Phase 1 は INSERT のみ）
    D-7: WAL モード、VACUUM なし
"""

import logging
import re
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PRAGMA 設定（D-7）
# ---------------------------------------------------------------------------

_PRAGMA_SETTINGS: dict[str, str] = {
    "journal_mode": "WAL",
    "cache_size": "-2000",
}

# ---------------------------------------------------------------------------
# スキーマ定義（requirements.md Section 4.2 + D-4 Section 5.2）
# ---------------------------------------------------------------------------

_SCHEMA_SQL = """\
-- 1. observations テーブル（会話断片 — 即時書込）
CREATE TABLE IF NOT EXISTS observations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    content     TEXT NOT NULL,
    speaker     TEXT NOT NULL,
    created_at  REAL NOT NULL,
    session_id  TEXT,
    embedding   BLOB
);

-- 2. FTS5 仮想テーブル（外部コンテンツテーブル方式 + trigram トークナイザ）
-- trigram: CJK テキストの部分一致検索に対応（最低3文字のクエリが必要）
CREATE VIRTUAL TABLE IF NOT EXISTS observations_fts USING fts5(
    content,
    content='observations',
    content_rowid='id',
    tokenize='trigram'
);

-- 3. FTS5 同期トリガー（INSERT のみ — D-4 Phase 1 スコープ）
CREATE TRIGGER IF NOT EXISTS observations_fts_insert
AFTER INSERT ON observations BEGIN
    INSERT INTO observations_fts(rowid, content)
    VALUES (new.id, new.content);
END;

-- 4. day_summary テーブル（日次要約 — memory_worker が生成）
CREATE TABLE IF NOT EXISTS day_summary (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT NOT NULL UNIQUE,
    summary     TEXT NOT NULL,
    created_at  REAL NOT NULL
);

-- 5. curiosity_targets テーブル（Phase 2 用予約）
CREATE TABLE IF NOT EXISTS curiosity_targets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    topic           TEXT NOT NULL,
    status          TEXT DEFAULT 'pending',
    priority        INTEGER DEFAULT 5,
    parent_id       INTEGER REFERENCES curiosity_targets(id),
    created_at      REAL NOT NULL,
    result_summary  TEXT
);

CREATE INDEX IF NOT EXISTS idx_curiosity_status
    ON curiosity_targets (status, priority);
"""


# ---------------------------------------------------------------------------
# Database クラス
# ---------------------------------------------------------------------------


class Database:
    """SQLite DB 接続管理（コンテキストマネージャ対応）.

    Usage::

        with Database(Path("data/memory.db")) as conn:
            initialize_db(conn)
            # conn を使って CRUD 操作

    Attributes:
        db_path: DB ファイルのパス。":memory:" も受け付ける。
    """

    def __init__(self, db_path: Path | str) -> None:
        self._db_path = str(db_path)
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        """DB に接続し PRAGMA を設定する.

        既に接続済みの場合は前の接続を閉じてから再接続する。

        Returns:
            設定済み sqlite3.Connection。

        Raises:
            sqlite3.OperationalError: DB ファイルの作成・接続に失敗した場合。
        """
        if self._conn is not None:
            self.close()
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        _configure_pragmas(conn)
        self._conn = conn
        logger.debug("DB connected: %s", self._db_path)
        return conn

    def close(self) -> None:
        """接続を閉じる."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
            logger.debug("DB closed: %s", self._db_path)

    def __enter__(self) -> sqlite3.Connection:
        return self.connect()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        self.close()


# ---------------------------------------------------------------------------
# 内部ヘルパー
# ---------------------------------------------------------------------------


_PRAGMA_SAFE_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def _configure_pragmas(conn: sqlite3.Connection) -> None:
    """PRAGMA 設定を適用する（D-7）.

    Args:
        conn: 対象の DB 接続。

    Raises:
        ValueError: PRAGMA のキーまたは値が安全でないパターンの場合。
    """
    for pragma, value in _PRAGMA_SETTINGS.items():
        if not _PRAGMA_SAFE_PATTERN.match(pragma):
            raise ValueError(f"不正な PRAGMA 名: {pragma}")
        if not _PRAGMA_SAFE_PATTERN.match(value):
            raise ValueError(f"不正な PRAGMA 値: {pragma}={value}")
        conn.execute(f"PRAGMA {pragma} = {value}")
    logger.debug("PRAGMA configured: %s", _PRAGMA_SETTINGS)


# ---------------------------------------------------------------------------
# 公開 API
# ---------------------------------------------------------------------------


def initialize_db(conn: sqlite3.Connection) -> None:
    """全テーブル・仮想テーブル・トリガーを冪等に作成する.

    IF NOT EXISTS を使用しているため、既にテーブルが存在する場合は
    何もしない（データは保持される）。

    Args:
        conn: 初期化対象の DB 接続。
    """
    conn.executescript(_SCHEMA_SQL)
    logger.info("DB schema initialized")
