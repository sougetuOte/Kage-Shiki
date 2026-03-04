"""memory テスト用共通フィクスチャ."""

import sqlite3
from pathlib import Path

import pytest

from kage_shiki.memory.db import Database, initialize_db


@pytest.fixture()
def db_conn(tmp_path: Path) -> sqlite3.Connection:
    """初期化済み DB 接続を返す fixture."""
    db_path = tmp_path / "memory.db"
    db = Database(db_path)
    conn = db.connect()
    initialize_db(conn)
    yield conn
    db.close()
