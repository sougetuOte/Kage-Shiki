"""SQLite DB 初期化 + スキーマ定義 + FTS5 トリガー + CRUD 操作.

対応 FR:
    FR-3.1: SQLite DB を初期化し、テーブルを作成
    FR-3.2: FTS5 INSERT トリガーにより全文検索インデックスを自動同期
    FR-3.3: observations テーブルへの即時書込
    FR-3.4: FTS5 全文検索（Cold Memory 取得）

対応設計:
    D-4: INSERT トリガー方式（Phase 1 は INSERT のみ）
    D-7: WAL モード、VACUUM なし
"""

import functools
import logging
import re
import sqlite3
import time
from datetime import date, datetime, timedelta
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
# DB ロックリトライ設定（FR-7.3, EM-008）
# ---------------------------------------------------------------------------

_DB_RETRY_MAX = 5
_DB_RETRY_INTERVAL_SEC = 0.1  # 100ms

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


# ハイフンは負の数値（例: "-2000"）を許容するためリテラルとして含める
_PRAGMA_SAFE_PATTERN = re.compile(r"^[A-Za-z0-9_\-]+$")


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


def _retry_on_lock(func):
    """DB ロック時のリトライデコレータ (FR-7.3, EM-008).

    最大 _DB_RETRY_MAX 回リトライし、各試行間で _DB_RETRY_INTERVAL_SEC 秒待機する。
    「database is locked」以外の OperationalError はリトライせずそのまま送出する。

    Args:
        func: ラップする DB 操作関数。

    Returns:
        リトライロジックを追加したラッパー関数。
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        for attempt in range(_DB_RETRY_MAX):
            try:
                return func(*args, **kwargs)
            except sqlite3.OperationalError as e:
                if "locked" not in str(e).lower():
                    raise
                if attempt == _DB_RETRY_MAX - 1:
                    logger.error(
                        "DB locked after %d retries", _DB_RETRY_MAX,
                    )
                    raise
                time.sleep(_DB_RETRY_INTERVAL_SEC)
                logger.warning(
                    "DB locked, retry %d/%d",
                    attempt + 1, _DB_RETRY_MAX,
                )
        raise RuntimeError("Unreachable")  # pragma: no cover

    return wrapper


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


# ---------------------------------------------------------------------------
# CRUD 操作（FR-3.3, FR-3.4, FR-3.12）
# ---------------------------------------------------------------------------


@_retry_on_lock
def save_observation(
    conn: sqlite3.Connection,
    content: str,
    speaker: str,
    created_at: float,
    session_id: str | None = None,
) -> int:
    """observations テーブルに即時書込する (FR-3.3).

    FTS5 INSERT トリガーにより、全文検索インデックスが自動同期される。

    Args:
        conn: DB 接続。
        content: 会話内容テキスト。
        speaker: 発言者識別子（"user" or "mascot"）。
        created_at: Unix タイムスタンプ（time.time() の戻り値）。
        session_id: セッション ID（省略時は NULL）。

    Returns:
        挿入されたレコードの rowid。
    """
    cursor = conn.execute(
        "INSERT INTO observations (content, speaker, created_at, session_id) "
        "VALUES (?, ?, ?, ?)",
        (content, speaker, created_at, session_id),
    )
    conn.commit()
    return cursor.lastrowid


@_retry_on_lock
def search_observations_fts(
    conn: sqlite3.Connection,
    query: str,
    top_k: int = 5,
) -> list[dict]:
    """FTS5 全文検索を実行し BM25 スコアリングで上位 top_k 件を返す (FR-3.4).

    trigram トークナイザを使用しているため、最低3文字のクエリが必要。
    3文字未満の場合は空リストを返す。

    Args:
        conn: DB 接続。
        query: 検索クエリ文字列（3文字以上推奨）。
        top_k: 取得する上位件数（デフォルト 5）。

    Returns:
        検索結果のリスト。各要素は dict (content, speaker, created_at, session_id)。
        BM25 スコアの降順（関連度が高い順）。
    """
    if len(query) < 3:
        return []
    rows = conn.execute(
        "SELECT o.content, o.speaker, o.created_at, o.session_id "
        "FROM observations_fts "
        "JOIN observations o ON observations_fts.rowid = o.id "
        "WHERE observations_fts MATCH ? "
        "ORDER BY bm25(observations_fts) "
        "LIMIT ?",
        (query, top_k),
    ).fetchall()
    return [dict(row) for row in rows]


@_retry_on_lock
def get_day_observations(
    conn: sqlite3.Connection,
    date_str: str,
) -> list[dict]:
    """指定日の observations を取得する（日次サマリー生成用）.

    日の境界はローカルタイムゾーンで判定する。

    Args:
        conn: DB 接続。
        date_str: 日付文字列（YYYY-MM-DD 形式）。

    Returns:
        observations のリスト。各要素は dict (content, speaker, created_at, session_id)。
        created_at の昇順。
    """
    d = date.fromisoformat(date_str)
    start_dt = datetime.combine(d, datetime.min.time())
    end_dt = start_dt + timedelta(days=1)
    rows = conn.execute(
        "SELECT content, speaker, created_at, session_id "
        "FROM observations "
        "WHERE created_at >= ? AND created_at < ? "
        "ORDER BY created_at",
        (start_dt.timestamp(), end_dt.timestamp()),
    ).fetchall()
    return [dict(row) for row in rows]


@_retry_on_lock
def get_missing_summary_dates(conn: sqlite3.Connection) -> list[str]:
    """observations に存在するが day_summary に存在しない日を検出する.

    日の判定はローカルタイムゾーン基準。今日の日付は除外する
    （1日が終了していないため、サマリー生成対象外）。

    Args:
        conn: DB 接続。

    Returns:
        YYYY-MM-DD 形式の日付文字列リスト（昇順）。
    """
    today = date.today().isoformat()
    rows = conn.execute(
        "SELECT DISTINCT date(created_at, 'unixepoch', 'localtime') AS d "
        "FROM observations "
        "ORDER BY d",
    ).fetchall()
    obs_dates = {row[0] for row in rows if row[0] != today}

    rows = conn.execute("SELECT date FROM day_summary").fetchall()
    summary_dates = {row[0] for row in rows}

    return sorted(obs_dates - summary_dates)


@_retry_on_lock
def save_day_summary(
    conn: sqlite3.Connection,
    date_str: str,
    summary: str,
) -> None:
    """日次サマリーを day_summary テーブルに保存する.

    Args:
        conn: DB 接続。
        date_str: 日付文字列（YYYY-MM-DD 形式）。
        summary: サマリーテキスト。

    Raises:
        sqlite3.IntegrityError: 同一日のサマリーが既に存在する場合（UNIQUE 制約）。
    """
    now = time.time()
    conn.execute(
        "INSERT INTO day_summary (date, summary, created_at) VALUES (?, ?, ?)",
        (date_str, summary, now),
    )
    conn.commit()
