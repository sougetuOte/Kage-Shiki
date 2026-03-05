"""起動シーケンス統合テスト (T-25, D-16).

対応 FR:
    FR-1.1〜FR-1.6: アプリケーション基盤
    FR-2.1, FR-2.7: GUI + トレイ
    FR-3.5, FR-3.6, FR-3.10, FR-3.11, FR-3.12: 記憶システム
    FR-4.4, FR-4.7: ペルソナ管理

テスト方針:
    - tkinter/pystray はモックで置き換え（CI 環境でも実行可能に）
    - LLM 呼び出しは全てモック
    - SQLite は :memory: DB を使用
    - 各ステップが正しい順序で実行されることを検証
"""

import queue
import sqlite3
import threading
from unittest.mock import MagicMock, patch

import pytest

from kage_shiki.agent.agent_core import AgentCore
from kage_shiki.core.errors import format_error_message
from kage_shiki.main import (
    _make_shutdown_callback,
    _run_background_loop,
    _start_response_polling,
)
from kage_shiki.memory.db import initialize_db
from kage_shiki.persona.persona_system import PersonaSystem

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def memory_db():
    """インメモリ DB を初期化して返す."""
    conn = sqlite3.connect(":memory:")
    initialize_db(conn)
    yield conn
    conn.close()


@pytest.fixture()
def mock_agent_core():
    """AgentCore のモック."""
    core = MagicMock(spec=AgentCore)
    core.generate_session_start_message.return_value = "こんにちは！"
    core.process_turn.return_value = "応答テキスト"
    return core


@pytest.fixture()
def mock_memory_worker():
    """MemoryWorker のモック."""
    worker = MagicMock()
    worker.generate_daily_summary_sync.return_value = None
    return worker


@pytest.fixture()
def mock_db():
    """Database のモック."""
    db = MagicMock()
    return db


# ---------------------------------------------------------------------------
# _run_background_loop テスト
# ---------------------------------------------------------------------------


class TestRunBackgroundLoop:
    """バックグラウンドループのテスト (D-16 Section 4.3)."""

    def test_greeting_sent_to_response_queue(self, mock_agent_core):
        """セッション開始メッセージが response_queue に送信されること."""
        input_q: queue.Queue[str] = queue.Queue()
        response_q: queue.Queue[str] = queue.Queue()
        shutdown_event = threading.Event()

        # すぐに停止
        shutdown_event.set()

        _run_background_loop(
            mock_agent_core, input_q, response_q, shutdown_event,
        )

        assert response_q.get_nowait() == "こんにちは！"
        mock_agent_core.generate_session_start_message.assert_called_once()

    def test_greeting_failure_sends_error_message(self):
        """セッション開始メッセージ生成失敗時に EM-006 が送信されること."""
        agent = MagicMock(spec=AgentCore)
        agent.generate_session_start_message.side_effect = RuntimeError("API error")

        input_q: queue.Queue[str] = queue.Queue()
        response_q: queue.Queue[str] = queue.Queue()
        shutdown_event = threading.Event()
        shutdown_event.set()

        _run_background_loop(agent, input_q, response_q, shutdown_event)

        result = response_q.get_nowait()
        assert result == format_error_message("EM-006")

    def test_process_turn_sends_response(self, mock_agent_core):
        """ユーザー入力に対して process_turn の結果が返ること."""
        input_q: queue.Queue[str] = queue.Queue()
        response_q: queue.Queue[str] = queue.Queue()
        shutdown_event = threading.Event()

        input_q.put("こんにちは")

        def stop_after_one_turn(*args, **kwargs):
            shutdown_event.set()
            return "応答テキスト"

        mock_agent_core.process_turn.side_effect = stop_after_one_turn

        _run_background_loop(
            mock_agent_core, input_q, response_q, shutdown_event,
        )

        # greeting + response
        greeting = response_q.get_nowait()
        assert greeting == "こんにちは！"
        response = response_q.get_nowait()
        assert response == "応答テキスト"

    def test_process_turn_failure_sends_error(self, mock_agent_core):
        """process_turn 失敗時に EM-006 が送信されてループ継続すること."""
        input_q: queue.Queue[str] = queue.Queue()
        response_q: queue.Queue[str] = queue.Queue()
        shutdown_event = threading.Event()

        input_q.put("テスト入力")

        call_count = 0

        def fail_then_stop(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            shutdown_event.set()
            raise RuntimeError("LLM failure")

        mock_agent_core.process_turn.side_effect = fail_then_stop

        _run_background_loop(
            mock_agent_core, input_q, response_q, shutdown_event,
        )

        # greeting + error
        response_q.get_nowait()  # greeting
        error_msg = response_q.get_nowait()
        assert error_msg == format_error_message("EM-006")

    def test_shutdown_event_stops_loop(self, mock_agent_core):
        """shutdown_event が set されるとループが終了すること."""
        input_q: queue.Queue[str] = queue.Queue()
        response_q: queue.Queue[str] = queue.Queue()
        shutdown_event = threading.Event()

        # バックグラウンドスレッドで起動
        thread = threading.Thread(
            target=_run_background_loop,
            args=(mock_agent_core, input_q, response_q, shutdown_event),
            daemon=True,
        )
        thread.start()

        # 少し待ってから停止通知
        shutdown_event.set()
        thread.join(timeout=2.0)

        assert not thread.is_alive()


# ---------------------------------------------------------------------------
# _make_shutdown_callback テスト
# ---------------------------------------------------------------------------


class TestMakeShutdownCallback:
    """シャットダウンコールバックのテスト (D-16 Section 6)."""

    def test_generates_daily_summary(self, mock_memory_worker, mock_db):
        """当日の日次サマリー生成が呼ばれること."""
        shutdown_event = threading.Event()
        cb = _make_shutdown_callback(mock_memory_worker, mock_db, shutdown_event)

        cb()

        mock_memory_worker.generate_daily_summary_sync.assert_called_once()
        # 日付文字列が渡されていること
        args = mock_memory_worker.generate_daily_summary_sync.call_args
        date_str = args[0][0]
        assert len(date_str) == 10  # YYYY-MM-DD

    def test_closes_db(self, mock_memory_worker, mock_db):
        """DB クローズが呼ばれること."""
        shutdown_event = threading.Event()
        cb = _make_shutdown_callback(mock_memory_worker, mock_db, shutdown_event)

        cb()

        mock_db.close.assert_called_once()

    def test_sets_shutdown_event(self, mock_memory_worker, mock_db):
        """shutdown_event が set されること."""
        shutdown_event = threading.Event()
        cb = _make_shutdown_callback(mock_memory_worker, mock_db, shutdown_event)

        assert not shutdown_event.is_set()
        cb()
        assert shutdown_event.is_set()

    def test_db_close_failure_does_not_crash(self, mock_memory_worker, mock_db):
        """DB クローズ失敗時にクラッシュしないこと."""
        shutdown_event = threading.Event()
        mock_db.close.side_effect = RuntimeError("close failed")

        cb = _make_shutdown_callback(mock_memory_worker, mock_db, shutdown_event)
        cb()  # should not raise

        assert shutdown_event.is_set()

    def test_summary_failure_still_closes_db_and_sets_event(
        self, mock_memory_worker, mock_db,
    ):
        """日次サマリー生成失敗時も DB クローズと shutdown_event.set() が実行されること."""
        shutdown_event = threading.Event()
        mock_memory_worker.generate_daily_summary_sync.side_effect = RuntimeError(
            "LLM timeout",
        )

        cb = _make_shutdown_callback(mock_memory_worker, mock_db, shutdown_event)
        cb()  # should not raise

        mock_db.close.assert_called_once()
        assert shutdown_event.is_set()


# ---------------------------------------------------------------------------
# _start_response_polling テスト
# ---------------------------------------------------------------------------


class TestStartResponsePolling:
    """応答ポーリングのテスト (D-16 Section 4.4)."""

    def test_polls_response_queue(self):
        """response_queue のメッセージが display_text に渡ること."""
        root = MagicMock()
        mascot_view = MagicMock()
        response_q: queue.Queue[str] = queue.Queue()
        shutdown_event = threading.Event()

        # root.after を呼ばれた時にコールバックを即座に実行
        callbacks = []

        def capture_after(ms, cb):
            callbacks.append(cb)

        root.after.side_effect = capture_after

        _start_response_polling(root, mascot_view, response_q, shutdown_event)

        # 最初の after 登録を確認
        assert len(callbacks) == 1

        # キューにメッセージを入れてからコールバック実行
        response_q.put("テスト応答")
        callbacks[0]()

        mascot_view.display_text.assert_called_with("テスト応答")

    def test_shutdown_event_calls_root_quit(self):
        """shutdown_event が set の場合、root.quit() が呼ばれること."""
        root = MagicMock()
        mascot_view = MagicMock()
        response_q: queue.Queue[str] = queue.Queue()
        shutdown_event = threading.Event()
        shutdown_event.set()

        callbacks = []
        root.after.side_effect = lambda ms, cb: callbacks.append(cb)

        _start_response_polling(root, mascot_view, response_q, shutdown_event)

        # コールバック実行
        callbacks[0]()

        root.quit.assert_called_once()
        # display_text は呼ばれないこと
        mascot_view.display_text.assert_not_called()


# ---------------------------------------------------------------------------
# main() 起動シーケンステスト
# ---------------------------------------------------------------------------


class TestMainStartupSequence:
    """main() の起動シーケンステスト (D-16 Section 2)."""

    @patch("kage_shiki.main.tk.Tk")
    @patch("kage_shiki.main.TkinterMascotView")
    @patch("kage_shiki.main.SystemTray")
    @patch("kage_shiki.main.register_windows_ctrl_handler")
    @patch("kage_shiki.main.make_atexit_handler")
    @patch("kage_shiki.main.LLMClient")
    @patch("kage_shiki.main.MemoryWorker")
    @patch("kage_shiki.main.Database")
    @patch("kage_shiki.main.initialize_db")
    @patch("kage_shiki.main.setup_logging")
    @patch("kage_shiki.main.ensure_api_key")
    @patch("kage_shiki.main.load_config")
    @patch("kage_shiki.main.load_dotenv_file")
    @patch("kage_shiki.main.PersonaSystem")
    def test_persona_not_found_runs_wizard(
        self,
        mock_persona_system_cls,
        mock_load_dotenv,
        mock_load_config,
        mock_ensure_api,
        mock_setup_logging,
        mock_init_db,
        mock_database,
        mock_memory_worker_cls,
        mock_llm_client_cls,
        mock_register_ctrl,
        mock_make_atexit,
        mock_system_tray_cls,
        mock_mascot_view_cls,
        mock_tk,
        tmp_path,
    ):
        """persona_core.md 不在時にウィザードモードで起動すること."""
        # config mock
        config = MagicMock()
        config.general.data_dir = str(tmp_path)
        config.gui = MagicMock()
        mock_load_config.return_value = config
        mock_ensure_api.return_value = "sk-test-key"

        # DB mock
        mock_db_instance = MagicMock()
        mock_db_instance.connect.return_value = sqlite3.connect(":memory:")
        mock_database.return_value = mock_db_instance

        # PersonaSystem: load_persona_core returns None (not found)
        mock_ps = MagicMock(spec=PersonaSystem)
        mock_ps.load_persona_core.return_value = None
        mock_persona_system_cls.return_value = mock_ps

        # tkinter mock - mainloop を即座に返す
        mock_root = MagicMock()
        mock_tk.return_value = mock_root

        with patch("kage_shiki.main._run_wizard") as mock_wizard:
            from kage_shiki.main import main

            main()

            mock_wizard.assert_called_once()

    @patch("kage_shiki.main.tk.Tk")
    @patch("kage_shiki.main.TkinterMascotView")
    @patch("kage_shiki.main.SystemTray")
    @patch("kage_shiki.main.register_windows_ctrl_handler")
    @patch("kage_shiki.main.make_atexit_handler")
    @patch("kage_shiki.main.LLMClient")
    @patch("kage_shiki.main.MemoryWorker")
    @patch("kage_shiki.main.Database")
    @patch("kage_shiki.main.initialize_db")
    @patch("kage_shiki.main.setup_logging")
    @patch("kage_shiki.main.ensure_api_key")
    @patch("kage_shiki.main.load_config")
    @patch("kage_shiki.main.load_dotenv_file")
    @patch("kage_shiki.main.PersonaSystem")
    @patch("kage_shiki.main.get_recent_day_summaries")
    def test_normal_startup_sequence(
        self,
        mock_get_summaries,
        mock_persona_system_cls,
        mock_load_dotenv,
        mock_load_config,
        mock_ensure_api,
        mock_setup_logging,
        mock_init_db,
        mock_database,
        mock_memory_worker_cls,
        mock_llm_client_cls,
        mock_register_ctrl,
        mock_make_atexit,
        mock_system_tray_cls,
        mock_mascot_view_cls,
        mock_tk,
        tmp_path,
    ):
        """正常起動時に全ステップが実行されること."""
        # config mock
        config = MagicMock()
        config.general.data_dir = str(tmp_path)
        config.gui = MagicMock()
        config.memory.warm_days = 5
        mock_load_config.return_value = config
        mock_ensure_api.return_value = "sk-test-key"

        # DB mock
        mock_db_instance = MagicMock()
        mock_db_instance.connect.return_value = sqlite3.connect(":memory:")
        mock_database.return_value = mock_db_instance

        # PersonaSystem mock
        mock_ps = MagicMock(spec=PersonaSystem)
        mock_persona_core = MagicMock()
        mock_persona_core.to_markdown.return_value = "## C1: 名前\n\nテスト"
        mock_ps.load_persona_core.return_value = mock_persona_core
        mock_ps.detect_manual_edit.return_value = False
        mock_ps.load_style_samples.return_value = "style"
        mock_ps.load_human_block.return_value = "human"
        mock_ps.load_personality_trends.return_value = ""
        mock_ps.is_trends_empty.return_value = True
        mock_persona_system_cls.return_value = mock_ps

        # Warm Memory
        mock_get_summaries.return_value = []

        # tkinter mock - mainloop で即停止
        mock_root = MagicMock()
        mock_tk.return_value = mock_root

        # SystemTray mock
        mock_tray = MagicMock()
        mock_system_tray_cls.return_value = mock_tray

        from kage_shiki.main import main

        main()

        # 各ステップの実行を確認
        mock_load_dotenv.assert_called_once()         # Step 0
        mock_load_config.assert_called_once()          # Step 1
        mock_ensure_api.assert_called_once()           # Step 2
        mock_setup_logging.assert_called_once()        # Step 3
        mock_init_db.assert_called_once()              # Step 3
        mock_ps.load_persona_core.assert_called_once() # Step 4
        mock_ps.detect_manual_edit.assert_called_once()  # Step 5
        mock_ps.load_style_samples.assert_called_once()  # Step 6
        mock_ps.load_human_block.assert_called_once()    # Step 6
        mock_ps.load_personality_trends.assert_called_once()  # Step 6
        mock_get_summaries.assert_called_once()          # Step 8
        mock_tray.setup_icon.assert_called_once()        # Step 11
        mock_tray.run_detached.assert_called_once()      # Step 12
        mock_register_ctrl.assert_called_once()          # Step 12

    @patch("kage_shiki.main.tk.Tk")
    @patch("kage_shiki.main.TkinterMascotView")
    @patch("kage_shiki.main.SystemTray")
    @patch("kage_shiki.main.register_windows_ctrl_handler")
    @patch("kage_shiki.main.make_atexit_handler")
    @patch("kage_shiki.main.LLMClient")
    @patch("kage_shiki.main.MemoryWorker")
    @patch("kage_shiki.main.Database")
    @patch("kage_shiki.main.initialize_db")
    @patch("kage_shiki.main.setup_logging")
    @patch("kage_shiki.main.ensure_api_key")
    @patch("kage_shiki.main.load_config")
    @patch("kage_shiki.main.load_dotenv_file")
    @patch("kage_shiki.main.PersonaSystem")
    def test_persona_load_error_exits(
        self,
        mock_persona_system_cls,
        mock_load_dotenv,
        mock_load_config,
        mock_ensure_api,
        mock_setup_logging,
        mock_init_db,
        mock_database,
        mock_memory_worker_cls,
        mock_llm_client_cls,
        mock_register_ctrl,
        mock_make_atexit,
        mock_system_tray_cls,
        mock_mascot_view_cls,
        mock_tk,
        tmp_path,
    ):
        """persona_core.md の読み込みエラー時に sys.exit(1) すること."""
        from kage_shiki.persona.persona_system import PersonaLoadError

        config = MagicMock()
        config.general.data_dir = str(tmp_path)
        mock_load_config.return_value = config
        mock_ensure_api.return_value = "sk-test-key"

        mock_db_instance = MagicMock()
        mock_db_instance.connect.return_value = sqlite3.connect(":memory:")
        mock_database.return_value = mock_db_instance

        mock_ps = MagicMock(spec=PersonaSystem)
        mock_ps.load_persona_core.side_effect = PersonaLoadError("bad format")
        mock_persona_system_cls.return_value = mock_ps

        from kage_shiki.main import main

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
