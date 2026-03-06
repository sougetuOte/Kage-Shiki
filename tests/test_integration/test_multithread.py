"""マルチスレッド統合テスト (T-30).

対応 FR:
    FR-8.3: マルチスレッド環境でのスレッド安全性検証

対応教訓:
    L-1: SQLite の check_same_thread 制約の明示的検証

テスト方針:
    - 実 SQLite DB + モック LLM + queue.Queue によるスレッド間通信
    - time.sleep() 禁止。threading.Event.wait(timeout=N) / queue.Queue.get(timeout=N) を使用
    - バックグラウンドスレッドは daemon=True で起動（テスト終了時のリーク防止）

Building Checklist:
    [R-4] FR-8.3 を docstring に転記済み
    [R-5] 異常系テスト: test_thread_same_connection_raises（L-1 回帰）
    [R-7] スレッド安全性: スレッド間受け渡しパスを検証
"""

import queue
import sqlite3
import threading
from pathlib import Path
from unittest.mock import MagicMock

from kage_shiki.agent.agent_core import AgentCore, PromptBuilder
from kage_shiki.core.config import AppConfig
from kage_shiki.memory.db import Database, initialize_db
from kage_shiki.persona.persona_system import PersonaSystem

# ---------------------------------------------------------------------------
# テスト用ヘルパー: 最小限の AgentCore を組み立てる
# ---------------------------------------------------------------------------


def _make_minimal_agent_core(
    db_conn: sqlite3.Connection,
    llm_client: object,
    config: AppConfig,
) -> AgentCore:
    """テスト用に最小構成の AgentCore を生成する."""
    persona_system = PersonaSystem()
    prompt_builder = PromptBuilder(
        persona_core="テストキャラクター",
        style_samples="## S1\n1. 例文",
        human_block="",
    )
    return AgentCore(
        config=config,
        db_conn=db_conn,
        llm_client=llm_client,
        persona_system=persona_system,
        prompt_builder=prompt_builder,
    )


# ---------------------------------------------------------------------------
# FR-8.3: バックグラウンドスレッドでの queue 経由対話テスト
# ---------------------------------------------------------------------------


class TestBackgroundThreadWithQueue:
    """FR-8.3: キュー経由でバックグラウンドスレッドに入力を渡し、応答が取得できる."""

    def test_background_thread_with_queue(self, tmp_path: Path) -> None:
        """FR-8.3 受入条件:
        (1) メインスレッドで DB 接続を生成（check_same_thread=False）
        (2) バックグラウンドスレッドが同接続を使用
        (3) queue.Queue 経由で入力を渡す
        (4) 応答が取り出せることを検証
        """
        # Arrange
        db_path = tmp_path / "memory.db"
        db = Database(db_path)
        conn = db.connect()  # Database.connect() は check_same_thread=False
        initialize_db(conn)

        mock_llm = MagicMock()
        mock_llm.send_message_for_purpose.return_value = "テスト応答"

        config = AppConfig()
        agent = _make_minimal_agent_core(conn, mock_llm, config)

        input_q: queue.Queue[str] = queue.Queue()
        response_q: queue.Queue[str] = queue.Queue()
        completed = threading.Event()

        def _worker() -> None:
            try:
                user_input = input_q.get(timeout=5.0)
                response = agent.process_turn(user_input)
                response_q.put(response)
            finally:
                completed.set()

        # Act
        bg = threading.Thread(target=_worker, daemon=True)
        bg.start()
        input_q.put("こんにちは")

        # Assert: タイムアウト付きで完了を待機
        finished = completed.wait(timeout=10.0)
        assert finished, "バックグラウンドスレッドがタイムアウト内に完了しなかった"

        response = response_q.get_nowait()
        assert response == "テスト応答"

        db.close()

    def test_multiple_turns_via_queue(self, tmp_path: Path) -> None:
        """FR-8.3: 複数ターンを queue 経由で処理できること."""
        # Arrange
        db_path = tmp_path / "memory.db"
        db = Database(db_path)
        conn = db.connect()
        initialize_db(conn)

        mock_llm = MagicMock()
        mock_llm.send_message_for_purpose.side_effect = ["応答1", "応答2", "応答3"]

        config = AppConfig()
        agent = _make_minimal_agent_core(conn, mock_llm, config)

        input_q: queue.Queue[str] = queue.Queue()
        response_q: queue.Queue[str] = queue.Queue()
        completed = threading.Event()
        n_turns = 3

        def _worker() -> None:
            try:
                for _ in range(n_turns):
                    user_input = input_q.get(timeout=5.0)
                    response = agent.process_turn(user_input)
                    response_q.put(response)
            finally:
                completed.set()

        # Act
        bg = threading.Thread(target=_worker, daemon=True)
        bg.start()
        for i in range(n_turns):
            input_q.put(f"メッセージ{i}")

        finished = completed.wait(timeout=10.0)
        assert finished, "バックグラウンドスレッドがタイムアウト内に完了しなかった"

        responses = []
        for _ in range(n_turns):
            responses.append(response_q.get_nowait())

        assert responses == ["応答1", "応答2", "応答3"]
        db.close()


# ---------------------------------------------------------------------------
# FR-8.3 回帰テスト: L-1 教訓 — check_same_thread=True の挙動
# ---------------------------------------------------------------------------


class TestThreadConnectionConstraint:
    """L-1 回帰テスト: SQLite の check_same_thread 制約の明示的検証."""

    def test_thread_same_connection_raises(self, tmp_path: Path) -> None:
        """L-1 回帰テスト:
        check_same_thread=True（デフォルト）でバックグラウンドスレッドから
        同接続を使用すると sqlite3.ProgrammingError が発生する。
        """
        # Arrange: check_same_thread=True（デフォルト）で接続生成
        db_path = tmp_path / "constraint_test.db"
        conn = sqlite3.connect(str(db_path))  # check_same_thread=True がデフォルト
        conn.execute(
            "CREATE TABLE test (id INTEGER PRIMARY KEY, val TEXT)",
        )
        conn.commit()

        error_holder: list[Exception] = []
        completed = threading.Event()

        def _worker() -> None:
            try:
                conn.execute("INSERT INTO test (val) VALUES (?)", ("test",))
            except Exception as e:
                error_holder.append(e)
            finally:
                completed.set()

        # Act
        bg = threading.Thread(target=_worker, daemon=True)
        bg.start()

        finished = completed.wait(timeout=5.0)
        assert finished, "スレッドがタイムアウト内に完了しなかった"

        # Assert: ProgrammingError が発生していること
        assert len(error_holder) == 1
        assert isinstance(error_holder[0], sqlite3.ProgrammingError)

        conn.close()

    def test_thread_different_connection_ok(self, tmp_path: Path) -> None:
        """check_same_thread=False で別スレッドから使用してもエラーにならない."""
        # Arrange
        db_path = tmp_path / "ok_test.db"
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        conn.execute(
            "CREATE TABLE test (id INTEGER PRIMARY KEY, val TEXT)",
        )
        conn.commit()

        error_holder: list[Exception] = []
        completed = threading.Event()

        def _worker() -> None:
            try:
                conn.execute("INSERT INTO test (val) VALUES (?)", ("ok",))
                conn.commit()
            except Exception as e:
                error_holder.append(e)
            finally:
                completed.set()

        # Act
        bg = threading.Thread(target=_worker, daemon=True)
        bg.start()

        finished = completed.wait(timeout=5.0)
        assert finished, "スレッドがタイムアウト内に完了しなかった"

        # Assert: エラーなし
        assert len(error_holder) == 0

        conn.close()

    def test_database_class_uses_check_same_thread_false(
        self, tmp_path: Path,
    ) -> None:
        """Database.connect() が check_same_thread=False で接続することを確認する."""
        # Arrange
        db_path = tmp_path / "database_test.db"
        db = Database(db_path)
        conn = db.connect()
        initialize_db(conn)

        error_holder: list[Exception] = []
        completed = threading.Event()

        def _worker() -> None:
            try:
                # 別スレッドから SELECT を実行
                result = conn.execute(
                    "SELECT COUNT(*) FROM observations",
                ).fetchone()
                assert result[0] == 0  # 初期状態は空
            except Exception as e:
                error_holder.append(e)
            finally:
                completed.set()

        # Act
        bg = threading.Thread(target=_worker, daemon=True)
        bg.start()

        finished = completed.wait(timeout=5.0)
        assert finished, "スレッドがタイムアウト内に完了しなかった"

        # Assert
        assert len(error_holder) == 0, f"エラーが発生した: {error_holder}"

        db.close()
