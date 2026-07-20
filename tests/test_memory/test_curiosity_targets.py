"""Tests for curiosity_targets CRUD 操作 (FR-9.11).

対応 FR:
    FR-9.11: curiosity_targets テーブル CRUD 操作

対応設計:
    D-28: curiosity_targets 運用設計 (docs/specs/phase2b-autonomy/design.md Section 6)
"""

import sqlite3
import time
from pathlib import Path

import pytest

from kage_shiki.memory.db import (
    Database,
    count_pending_curiosity_targets,
    create_curiosity_target,
    curiosity_topic_exists,  # noqa: F401 — HGA A-2 追加 (Task 3-2 実装対象)
    get_pending_targets,
    initialize_db,
    recover_stale_searching_targets,  # noqa: F401 — HGA A-1 追加 (Task 3-2 実装対象)
    update_target_priority,
    update_target_status,
)

# ---------------------------------------------------------------------------
# フィクスチャ
# ---------------------------------------------------------------------------


@pytest.fixture()
def mem_conn() -> sqlite3.Connection:
    """インメモリ DB を初期化して接続を返す."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    initialize_db(conn)
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# テーブル存在確認（スキーマ）
# ---------------------------------------------------------------------------


class TestCuriosityTargetsSchema:
    """curiosity_targets テーブルのスキーマ検証."""

    def test_table_exists_after_init(self, mem_conn: sqlite3.Connection) -> None:
        """initialize_db 後に curiosity_targets テーブルが存在すること."""
        rows = mem_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='curiosity_targets'"
        ).fetchall()
        assert len(rows) == 1

    def test_updated_at_column_exists(self, mem_conn: sqlite3.Connection) -> None:
        """updated_at カラムが存在すること（Phase 2b 追加）."""
        columns = {
            row[1]
            for row in mem_conn.execute(
                "PRAGMA table_info(curiosity_targets)"
            ).fetchall()
        }
        assert "updated_at" in columns

    def test_index_on_status_priority_exists(self, mem_conn: sqlite3.Connection) -> None:
        """status, priority 複合インデックスが存在すること."""
        # PRAGMA index_list の列: seq, name, unique, origin, partial
        indexes = {
            row[1]
            for row in mem_conn.execute(
                "PRAGMA index_list(curiosity_targets)"
            ).fetchall()
        }
        assert "idx_curiosity_targets_status_priority" in indexes


# ---------------------------------------------------------------------------
# create_curiosity_target
# ---------------------------------------------------------------------------


class TestCreateCuriosityTarget:
    """create_curiosity_target のテスト."""

    def test_returns_integer_id(self, mem_conn: sqlite3.Connection) -> None:
        """create_curiosity_target が整数 ID を返すこと."""
        row_id = create_curiosity_target(mem_conn, topic="Python の非同期処理")
        assert isinstance(row_id, int)
        assert row_id >= 1

    def test_creates_pending_status(self, mem_conn: sqlite3.Connection) -> None:
        """作成直後の status が 'pending' であること."""
        row_id = create_curiosity_target(mem_conn, topic="機械学習入門")
        row = mem_conn.execute(
            "SELECT status FROM curiosity_targets WHERE id=?", (row_id,)
        ).fetchone()
        assert row["status"] == "pending"

    def test_default_priority_is_5(self, mem_conn: sqlite3.Connection) -> None:
        """priority のデフォルト値が 5 であること."""
        row_id = create_curiosity_target(mem_conn, topic="デフォルト優先度テスト")
        row = mem_conn.execute(
            "SELECT priority FROM curiosity_targets WHERE id=?", (row_id,)
        ).fetchone()
        assert row["priority"] == 5

    def test_custom_priority_is_saved(self, mem_conn: sqlite3.Connection) -> None:
        """priority=1 を指定した場合、値が保存されること."""
        row_id = create_curiosity_target(mem_conn, topic="高優先トピック", priority=1)
        row = mem_conn.execute(
            "SELECT priority FROM curiosity_targets WHERE id=?", (row_id,)
        ).fetchone()
        assert row["priority"] == 1

    def test_parent_id_is_saved(self, mem_conn: sqlite3.Connection) -> None:
        """parent_id が指定された場合、値が保存されること."""
        parent_id = create_curiosity_target(mem_conn, topic="親トピック")
        child_id = create_curiosity_target(
            mem_conn, topic="派生トピック", parent_id=parent_id
        )
        row = mem_conn.execute(
            "SELECT parent_id FROM curiosity_targets WHERE id=?", (child_id,)
        ).fetchone()
        assert row["parent_id"] == parent_id

    def test_parent_id_none_by_default(self, mem_conn: sqlite3.Connection) -> None:
        """parent_id のデフォルトが NULL であること."""
        row_id = create_curiosity_target(mem_conn, topic="ルートトピック")
        row = mem_conn.execute(
            "SELECT parent_id FROM curiosity_targets WHERE id=?", (row_id,)
        ).fetchone()
        assert row["parent_id"] is None

    def test_created_at_is_set(self, mem_conn: sqlite3.Connection) -> None:
        """created_at が現在時刻付近で設定されること."""
        before = time.time()
        row_id = create_curiosity_target(mem_conn, topic="タイムスタンプテスト")
        after = time.time()
        row = mem_conn.execute(
            "SELECT created_at FROM curiosity_targets WHERE id=?", (row_id,)
        ).fetchone()
        assert before <= row["created_at"] <= after

    def test_updated_at_equals_created_at_on_create(
        self, mem_conn: sqlite3.Connection
    ) -> None:
        """作成時点では updated_at が created_at と同じ（または近い）値であること."""
        row_id = create_curiosity_target(mem_conn, topic="updated_at 初期値テスト")
        row = mem_conn.execute(
            "SELECT created_at, updated_at FROM curiosity_targets WHERE id=?", (row_id,)
        ).fetchone()
        # 作成時は updated_at と created_at が同一 time.time() 呼び出しではないため
        # 誤差 1 秒以内で検証
        assert abs(row["updated_at"] - row["created_at"]) < 1.0

    def test_sequential_ids_are_incremented(self, mem_conn: sqlite3.Connection) -> None:
        """複数レコードの ID が AUTOINCREMENT で増加すること."""
        id1 = create_curiosity_target(mem_conn, topic="トピック A")
        id2 = create_curiosity_target(mem_conn, topic="トピック B")
        assert id2 > id1


# ---------------------------------------------------------------------------
# get_pending_targets
# ---------------------------------------------------------------------------


class TestGetPendingTargets:
    """get_pending_targets のテスト."""

    def test_returns_pending_only(self, mem_conn: sqlite3.Connection) -> None:
        """status='pending' のレコードのみ返すこと（searching/done/failed は除外）."""
        pending_id = create_curiosity_target(mem_conn, topic="pending トピック")
        searching_id = create_curiosity_target(mem_conn, topic="searching トピック")
        done_id = create_curiosity_target(mem_conn, topic="done トピック")
        failed_id = create_curiosity_target(mem_conn, topic="failed トピック")

        update_target_status(mem_conn, searching_id, "searching")
        update_target_status(mem_conn, done_id, "done")
        update_target_status(mem_conn, failed_id, "failed")

        results = get_pending_targets(mem_conn, limit=10)
        result_ids = {r["id"] for r in results}
        assert pending_id in result_ids
        assert searching_id not in result_ids
        assert done_id not in result_ids
        assert failed_id not in result_ids

    def test_sorted_by_priority_ascending(self, mem_conn: sqlite3.Connection) -> None:
        """priority 昇順（1 → 10）で返されること."""
        create_curiosity_target(mem_conn, topic="優先度10", priority=10)
        create_curiosity_target(mem_conn, topic="優先度1", priority=1)
        create_curiosity_target(mem_conn, topic="優先度5", priority=5)

        results = get_pending_targets(mem_conn, limit=10)
        priorities = [r["priority"] for r in results]
        assert priorities == sorted(priorities)

    def test_limit_parameter(self, mem_conn: sqlite3.Connection) -> None:
        """limit パラメータが結果件数を制限すること."""
        for i in range(5):
            create_curiosity_target(mem_conn, topic=f"トピック {i}")

        results = get_pending_targets(mem_conn, limit=2)
        assert len(results) == 2

    def test_default_limit_is_1(self, mem_conn: sqlite3.Connection) -> None:
        """limit のデフォルト値が 1 であること."""
        for i in range(3):
            create_curiosity_target(mem_conn, topic=f"デフォルト {i}")

        results = get_pending_targets(mem_conn)
        assert len(results) == 1

    def test_returns_empty_list_when_no_pending(
        self, mem_conn: sqlite3.Connection
    ) -> None:
        """pending レコードが 0 件なら空リストを返すこと."""
        results = get_pending_targets(mem_conn)
        assert results == []

    def test_returns_list_of_dicts(self, mem_conn: sqlite3.Connection) -> None:
        """結果が list[dict] 形式であること（sqlite3.Row ではない）."""
        create_curiosity_target(mem_conn, topic="dict 確認")
        results = get_pending_targets(mem_conn)
        assert isinstance(results, list)
        assert isinstance(results[0], dict)

    def test_result_contains_expected_keys(self, mem_conn: sqlite3.Connection) -> None:
        """結果 dict に必要なキーが含まれること."""
        create_curiosity_target(mem_conn, topic="キー確認")
        results = get_pending_targets(mem_conn)
        assert len(results) == 1
        keys = set(results[0].keys())
        # 最低限必要なキー
        assert {"id", "topic", "status", "priority"}.issubset(keys)


# ---------------------------------------------------------------------------
# update_target_status
# ---------------------------------------------------------------------------


class TestUpdateTargetStatus:
    """update_target_status のテスト."""

    def test_pending_to_searching(self, mem_conn: sqlite3.Connection) -> None:
        """pending → searching への status 更新が成功すること."""
        target_id = create_curiosity_target(mem_conn, topic="調査中テスト")
        update_target_status(mem_conn, target_id, "searching")
        row = mem_conn.execute(
            "SELECT status FROM curiosity_targets WHERE id=?", (target_id,)
        ).fetchone()
        assert row["status"] == "searching"

    def test_searching_to_done(self, mem_conn: sqlite3.Connection) -> None:
        """searching → done への status 更新が成功すること."""
        target_id = create_curiosity_target(mem_conn, topic="完了テスト")
        update_target_status(mem_conn, target_id, "searching")
        update_target_status(
            mem_conn, target_id, "done", result_summary="調査完了しました"
        )
        row = mem_conn.execute(
            "SELECT status FROM curiosity_targets WHERE id=?", (target_id,)
        ).fetchone()
        assert row["status"] == "done"

    def test_done_saves_result_summary(self, mem_conn: sqlite3.Connection) -> None:
        """status='done' 時に result_summary が保存されること."""
        target_id = create_curiosity_target(mem_conn, topic="要約保存テスト")
        summary = "Python の非同期処理についての調査結果です。"
        update_target_status(mem_conn, target_id, "done", result_summary=summary)
        row = mem_conn.execute(
            "SELECT result_summary FROM curiosity_targets WHERE id=?", (target_id,)
        ).fetchone()
        assert row["result_summary"] == summary

    def test_searching_without_result_summary(
        self, mem_conn: sqlite3.Connection
    ) -> None:
        """status='searching' で result_summary を省略できること."""
        target_id = create_curiosity_target(mem_conn, topic="中間状態テスト")
        # 例外が出なければ OK
        update_target_status(mem_conn, target_id, "searching")
        row = mem_conn.execute(
            "SELECT status FROM curiosity_targets WHERE id=?", (target_id,)
        ).fetchone()
        assert row["status"] == "searching"

    def test_invalid_status_raises_value_error(
        self, mem_conn: sqlite3.Connection
    ) -> None:
        """無効な status 値は ValueError を送出すること（R-13）."""
        target_id = create_curiosity_target(mem_conn, topic="無効ステータステスト")
        with pytest.raises(ValueError, match="Unknown status"):
            update_target_status(mem_conn, target_id, "invalid")

    def test_nonexistent_target_id_raises_lookup_error(
        self, mem_conn: sqlite3.Connection
    ) -> None:
        """存在しない target_id への更新で LookupError が送出されること (W-8)."""
        with pytest.raises(LookupError, match="id=99999"):
            update_target_status(mem_conn, 99999, "searching")

    def test_updated_at_changes_on_status_update(
        self, mem_conn: sqlite3.Connection,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """status 更新時に updated_at が更新されること (W-11: time mock で決定論化)."""
        # create_curiosity_target と update_target_status で異なる時刻を返すよう mock
        times = iter([1000.0, 2000.0])
        monkeypatch.setattr("kage_shiki.memory.db.time.time", lambda: next(times))
        target_id = create_curiosity_target(mem_conn, topic="updated_at 変更テスト")
        update_target_status(mem_conn, target_id, "searching")
        row = mem_conn.execute(
            "SELECT updated_at FROM curiosity_targets WHERE id=?", (target_id,)
        ).fetchone()
        assert row["updated_at"] == 2000.0

    def test_searching_status_does_not_overwrite_result_summary(
        self, mem_conn: sqlite3.Connection
    ) -> None:
        """status='searching' + result_summary=None が既存 result_summary を保持すること (W-6)."""
        target_id = create_curiosity_target(mem_conn, topic="result_summary 保持テスト")
        update_target_status(mem_conn, target_id, "done", result_summary="調査完了")
        # status を searching に戻す際、result_summary=None を渡しても既存値は保持される
        update_target_status(mem_conn, target_id, "searching")
        row = mem_conn.execute(
            "SELECT status, result_summary FROM curiosity_targets WHERE id=?", (target_id,)
        ).fetchone()
        assert row["status"] == "searching"
        assert row["result_summary"] == "調査完了"

    def test_failed_status_update(self, mem_conn: sqlite3.Connection) -> None:
        """pending → failed への status 更新が成功すること."""
        target_id = create_curiosity_target(mem_conn, topic="失敗テスト")
        update_target_status(mem_conn, target_id, "failed")
        row = mem_conn.execute(
            "SELECT status FROM curiosity_targets WHERE id=?", (target_id,)
        ).fetchone()
        assert row["status"] == "failed"


# ---------------------------------------------------------------------------
# update_target_priority
# ---------------------------------------------------------------------------


class TestUpdateTargetPriority:
    """update_target_priority のテスト."""

    def test_increase_priority(self, mem_conn: sqlite3.Connection) -> None:
        """priority が delta 分増加すること."""
        target_id = create_curiosity_target(mem_conn, topic="優先度増加テスト", priority=5)
        update_target_priority(mem_conn, target_id, delta=3)
        row = mem_conn.execute(
            "SELECT priority FROM curiosity_targets WHERE id=?", (target_id,)
        ).fetchone()
        assert row["priority"] == 8

    def test_decrease_priority(self, mem_conn: sqlite3.Connection) -> None:
        """priority が delta 分減少すること."""
        target_id = create_curiosity_target(mem_conn, topic="優先度減少テスト", priority=5)
        update_target_priority(mem_conn, target_id, delta=-2)
        row = mem_conn.execute(
            "SELECT priority FROM curiosity_targets WHERE id=?", (target_id,)
        ).fetchone()
        assert row["priority"] == 3

    def test_priority_floor_at_1(self, mem_conn: sqlite3.Connection) -> None:
        """delta=-10 で priority が 1 に床止めされること."""
        target_id = create_curiosity_target(mem_conn, topic="床止めテスト", priority=3)
        update_target_priority(mem_conn, target_id, delta=-10)
        row = mem_conn.execute(
            "SELECT priority FROM curiosity_targets WHERE id=?", (target_id,)
        ).fetchone()
        assert row["priority"] == 1

    def test_priority_floor_exact_boundary(self, mem_conn: sqlite3.Connection) -> None:
        """priority が 1 のときに delta=-1 しても 1 のままであること."""
        target_id = create_curiosity_target(mem_conn, topic="境界値テスト", priority=1)
        update_target_priority(mem_conn, target_id, delta=-1)
        row = mem_conn.execute(
            "SELECT priority FROM curiosity_targets WHERE id=?", (target_id,)
        ).fetchone()
        assert row["priority"] == 1

    def test_nonexistent_target_id_raises_lookup_error(
        self, mem_conn: sqlite3.Connection
    ) -> None:
        """存在しない target_id への priority 更新で LookupError が送出されること (W-8)."""
        with pytest.raises(LookupError, match="id=99999"):
            update_target_priority(mem_conn, 99999, delta=1)

    def test_updated_at_changes_on_priority_update(
        self, mem_conn: sqlite3.Connection,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """priority 更新時に updated_at が更新されること (W-11: time mock で決定論化)."""
        times = iter([1000.0, 2000.0])
        monkeypatch.setattr("kage_shiki.memory.db.time.time", lambda: next(times))
        target_id = create_curiosity_target(mem_conn, topic="priority updated_at テスト")
        update_target_priority(mem_conn, target_id, delta=1)
        row = mem_conn.execute(
            "SELECT updated_at FROM curiosity_targets WHERE id=?", (target_id,)
        ).fetchone()
        assert row["updated_at"] == 2000.0


# ---------------------------------------------------------------------------
# count_pending_curiosity_targets
# ---------------------------------------------------------------------------


class TestCountPendingCuriosityTargets:
    """count_pending_curiosity_targets のテスト (FR-9.11, iter 1 W-4)."""

    def test_empty_returns_zero(self, mem_conn: sqlite3.Connection) -> None:
        """テーブルが空のとき 0 を返す."""
        assert count_pending_curiosity_targets(mem_conn) == 0

    def test_counts_only_pending_records(self, mem_conn: sqlite3.Connection) -> None:
        """pending 以外（searching/done/failed）は件数に含めない."""
        # pending レコード 2 件を作成（id は検証対象外のため捨てる）
        create_curiosity_target(mem_conn, topic="pending-1")
        create_curiosity_target(mem_conn, topic="pending-2")
        searching_id = create_curiosity_target(mem_conn, topic="searching")
        done_id = create_curiosity_target(mem_conn, topic="done")
        failed_id = create_curiosity_target(mem_conn, topic="failed")

        update_target_status(mem_conn, searching_id, "searching")
        update_target_status(mem_conn, done_id, "done", result_summary="完了")
        update_target_status(mem_conn, failed_id, "failed")

        count = count_pending_curiosity_targets(mem_conn)
        assert count == 2

    def test_count_ignores_priority(self, mem_conn: sqlite3.Connection) -> None:
        """priority の値に関わらず pending を全件カウントする."""
        create_curiosity_target(mem_conn, topic="high", priority=1)
        create_curiosity_target(mem_conn, topic="mid", priority=5)
        create_curiosity_target(mem_conn, topic="low", priority=10)
        assert count_pending_curiosity_targets(mem_conn) == 3


# ---------------------------------------------------------------------------
# R-8: 永続状態 2 回目テスト（ファイル DB を閉じて再接続）
# ---------------------------------------------------------------------------


class TestPersistenceAcrossConnections:
    """R-8: 永続状態 — 接続を閉じて再接続後もデータが残ること."""

    def test_data_persists_after_reconnect(self, tmp_path: Path) -> None:
        """ファイル DB に書き込み後、接続を閉じて再接続してもレコードが残ること."""
        db_path = tmp_path / "curiosity_test.db"

        # 1 回目の接続：レコードを作成
        db1 = Database(db_path)
        conn1 = db1.connect()
        initialize_db(conn1)
        target_id = create_curiosity_target(conn1, topic="永続化テスト")
        update_target_status(conn1, target_id, "searching")
        db1.close()

        # 2 回目の接続：レコードが残っていることを確認
        db2 = Database(db_path)
        conn2 = db2.connect()
        initialize_db(conn2)  # IF NOT EXISTS なのでデータは保持される
        # searching に変更したので pending にはない（空であることを確認済み）
        assert get_pending_targets(conn2, limit=10) == []
        all_rows = conn2.execute(
            "SELECT id, topic, status FROM curiosity_targets WHERE id=?", (target_id,)
        ).fetchall()
        db2.close()

        assert len(all_rows) == 1
        row = dict(all_rows[0])
        assert row["topic"] == "永続化テスト"
        assert row["status"] == "searching"

    def test_multiple_records_persist(self, tmp_path: Path) -> None:
        """複数レコードが再接続後も全て残っていること."""
        db_path = tmp_path / "multi_persist.db"

        # 1 回目の接続：複数レコードを作成
        db1 = Database(db_path)
        conn1 = db1.connect()
        initialize_db(conn1)
        ids = [
            create_curiosity_target(conn1, topic=f"トピック {i}", priority=i + 1)
            for i in range(3)
        ]
        db1.close()

        # 2 回目の接続：全レコードの確認
        db2 = Database(db_path)
        conn2 = db2.connect()
        initialize_db(conn2)
        results = get_pending_targets(conn2, limit=10)
        db2.close()

        assert len(results) == 3
        result_ids = {r["id"] for r in results}
        assert set(ids) == result_ids


# ---------------------------------------------------------------------------
# recover_stale_searching_targets (HGA A-1, Task 3-2)
# ---------------------------------------------------------------------------


class TestRecoverStaleSearchingTargets:
    """パイプライン中断で取り残された searching レコードの復旧を検証."""

    def test_no_searching_returns_zero(self, mem_conn: sqlite3.Connection) -> None:
        """searching が 0 件なら 0 を返し、他 status に影響しない."""
        create_curiosity_target(mem_conn, "topic-pending")
        done_id = create_curiosity_target(mem_conn, "topic-done")
        update_target_status(mem_conn, done_id, "done", result_summary="x")

        count = recover_stale_searching_targets(mem_conn)

        assert count == 0
        # pending / done の件数不変
        assert count_pending_curiosity_targets(mem_conn) == 1
        row = mem_conn.execute(
            "SELECT status FROM curiosity_targets WHERE id=?", (done_id,)
        ).fetchone()
        assert row["status"] == "done"

    def test_recovers_all_searching_records(
        self, mem_conn: sqlite3.Connection,
    ) -> None:
        """searching 3 件を全て pending に復旧し件数 3 を返す."""
        ids = []
        for i in range(3):
            tid = create_curiosity_target(mem_conn, f"topic-{i}")
            update_target_status(mem_conn, tid, "searching")
            ids.append(tid)

        count = recover_stale_searching_targets(mem_conn)

        assert count == 3
        for tid in ids:
            row = mem_conn.execute(
                "SELECT status FROM curiosity_targets WHERE id=?", (tid,)
            ).fetchone()
            assert row["status"] == "pending"
        # pending 総数 = 3
        assert count_pending_curiosity_targets(mem_conn) == 3

    def test_does_not_touch_done_or_failed(
        self, mem_conn: sqlite3.Connection,
    ) -> None:
        """done / failed レコードは影響を受けない."""
        stale_id = create_curiosity_target(mem_conn, "topic-stale")
        update_target_status(mem_conn, stale_id, "searching")
        done_id = create_curiosity_target(mem_conn, "topic-done")
        update_target_status(mem_conn, done_id, "done", result_summary="x")
        failed_id = create_curiosity_target(mem_conn, "topic-failed")
        update_target_status(mem_conn, failed_id, "failed")

        count = recover_stale_searching_targets(mem_conn)

        assert count == 1
        for tid, expected in [(done_id, "done"), (failed_id, "failed")]:
            row = mem_conn.execute(
                "SELECT status FROM curiosity_targets WHERE id=?", (tid,)
            ).fetchone()
            assert row["status"] == expected

    def test_updates_updated_at_timestamp(
        self, mem_conn: sqlite3.Connection,
    ) -> None:
        """復旧時に updated_at タイムスタンプが更新される."""
        tid = create_curiosity_target(mem_conn, "topic")
        update_target_status(mem_conn, tid, "searching")
        row = mem_conn.execute(
            "SELECT updated_at FROM curiosity_targets WHERE id=?", (tid,)
        ).fetchone()
        old_updated_at = row["updated_at"]
        time.sleep(0.01)

        recover_stale_searching_targets(mem_conn)

        row = mem_conn.execute(
            "SELECT updated_at FROM curiosity_targets WHERE id=?", (tid,)
        ).fetchone()
        assert row["updated_at"] > old_updated_at


# ---------------------------------------------------------------------------
# curiosity_topic_exists (HGA A-2, Task 3-2)
# ---------------------------------------------------------------------------


class TestCuriosityTopicExists:
    """派生テーマ登録前の重複ガード検証."""

    def test_returns_true_for_exact_match(
        self, mem_conn: sqlite3.Connection,
    ) -> None:
        """完全一致で True を返す."""
        create_curiosity_target(mem_conn, "Python asyncio")

        assert curiosity_topic_exists(mem_conn, "Python asyncio") is True

    def test_returns_true_for_case_mismatch(
        self, mem_conn: sqlite3.Connection,
    ) -> None:
        """大文字小文字の違いを無視して True を返す."""
        create_curiosity_target(mem_conn, "Python Asyncio")

        assert curiosity_topic_exists(mem_conn, "python asyncio") is True
        assert curiosity_topic_exists(mem_conn, "PYTHON ASYNCIO") is True

    def test_returns_false_for_no_match(
        self, mem_conn: sqlite3.Connection,
    ) -> None:
        """一致するレコードがなければ False を返す."""
        create_curiosity_target(mem_conn, "Python asyncio")

        assert curiosity_topic_exists(mem_conn, "Rust tokio") is False

    def test_returns_false_for_partial_match(
        self, mem_conn: sqlite3.Connection,
    ) -> None:
        """部分一致は False を返す（完全一致のみ）."""
        create_curiosity_target(mem_conn, "Python asyncio programming")

        assert curiosity_topic_exists(mem_conn, "Python") is False
        assert curiosity_topic_exists(mem_conn, "asyncio") is False

    def test_status_agnostic(self, mem_conn: sqlite3.Connection) -> None:
        """status を問わず一致（done / failed の topic とも重複判定される）."""
        tid = create_curiosity_target(mem_conn, "Topic X")
        update_target_status(mem_conn, tid, "done", result_summary="x")

        # done レコードとも重複判定される
        assert curiosity_topic_exists(mem_conn, "topic x") is True

    def test_empty_table_returns_false(
        self, mem_conn: sqlite3.Connection,
    ) -> None:
        """空テーブルでは常に False."""
        assert curiosity_topic_exists(mem_conn, "any topic") is False

    def test_japanese_topic(self, mem_conn: sqlite3.Connection) -> None:
        """日本語トピックの完全一致で True."""
        create_curiosity_target(mem_conn, "Pythonの非同期処理")

        assert curiosity_topic_exists(mem_conn, "Pythonの非同期処理") is True
        assert curiosity_topic_exists(mem_conn, "Pythonの同期処理") is False
