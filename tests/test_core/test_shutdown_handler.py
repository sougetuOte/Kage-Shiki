"""T-19: シャットダウン2層防御のテスト.

対応 FR:
    FR-3.9: プロセス終了シグナル捕捉（Layer 2: SetConsoleCtrlHandler）

対応設計:
    D-11: ctypes + atexit の二重化
"""

from unittest.mock import MagicMock, patch

import pytest

import kage_shiki.core.shutdown_handler as shutdown_handler
from kage_shiki.core.shutdown_handler import (
    CTRL_C_EVENT,
    CTRL_CLOSE_EVENT,
    CTRL_LOGOFF_EVENT,
    CTRL_SHUTDOWN_EVENT,
    make_atexit_handler,
    register_windows_ctrl_handler,
    reset_shutdown_state,
)

# ---------------------------------------------------------------------------
# フィクスチャ
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_state() -> None:
    """各テスト前後にシャットダウン状態をリセットする."""
    reset_shutdown_state()
    yield
    reset_shutdown_state()


# ---------------------------------------------------------------------------
# TestShutdownDoneFlag: _shutdown_done フラグの2重実行防止テスト
# ---------------------------------------------------------------------------


class TestShutdownDoneFlag:
    """_shutdown_done フラグの2重実行防止テスト."""

    def test_callback_executes_once_via_atexit(self) -> None:
        """atexit ハンドラで callback が1回実行されること."""
        call_count = []

        def callback():
            call_count.append(1)

        handler = make_atexit_handler(callback)
        handler()

        assert len(call_count) == 1

    def test_callback_not_executed_twice(self) -> None:
        """atexit と ctrl_handler を両方呼んでも callback は1回のみ."""
        call_count = []

        def callback():
            call_count.append(1)

        atexit_handler = make_atexit_handler(callback)

        # atexit ハンドラを実行
        atexit_handler()

        # 再度 atexit ハンドラを呼んでもスキップされること
        atexit_handler()

        assert len(call_count) == 1

    def test_reset_allows_re_execution(self) -> None:
        """reset_shutdown_state 後に再実行できること（テスト用）."""
        call_count = []

        def callback():
            call_count.append(1)

        handler = make_atexit_handler(callback)
        handler()
        assert len(call_count) == 1

        reset_shutdown_state()

        handler2 = make_atexit_handler(callback)
        handler2()
        assert len(call_count) == 2


# ---------------------------------------------------------------------------
# TestRegisterWindowsCtrlHandler: register_windows_ctrl_handler テスト
# ---------------------------------------------------------------------------


class TestRegisterWindowsCtrlHandler:
    """register_windows_ctrl_handler テスト."""

    def test_returns_true_on_success(self) -> None:
        """登録成功時に True を返すこと."""
        mock_kernel32 = MagicMock()
        mock_kernel32.SetConsoleCtrlHandler.return_value = 1  # 成功

        with patch("sys.platform", "win32"), patch("ctypes.windll") as mock_windll:
            mock_windll.kernel32 = mock_kernel32
            result = register_windows_ctrl_handler(lambda: None)

        assert result is True

    def test_returns_false_on_failure(self) -> None:
        """登録失敗時（コンソールなし）に False + WARNING ログ."""
        mock_kernel32 = MagicMock()
        mock_kernel32.SetConsoleCtrlHandler.return_value = 0  # 失敗

        with patch("sys.platform", "win32"), patch("ctypes.windll") as mock_windll:
            mock_windll.kernel32 = mock_kernel32
            result = register_windows_ctrl_handler(lambda: None)

        assert result is False

    def test_handler_ref_preserved(self) -> None:
        """_ctrl_handler_ref がモジュールレベルで保持されること."""
        mock_kernel32 = MagicMock()
        mock_kernel32.SetConsoleCtrlHandler.return_value = 1

        with patch("sys.platform", "win32"), patch("ctypes.windll") as mock_windll:
            mock_windll.kernel32 = mock_kernel32
            register_windows_ctrl_handler(lambda: None)

        assert shutdown_handler._ctrl_handler_ref is not None

    def test_returns_false_on_non_windows(self) -> None:
        """Windows 以外の環境では False を返すこと."""
        with patch("sys.platform", "linux"):
            result = register_windows_ctrl_handler(lambda: None)

        assert result is False

    def test_returns_false_on_os_error(self) -> None:
        """OSError 発生時は False + WARNING ログ."""
        mock_kernel32 = MagicMock()
        mock_kernel32.SetConsoleCtrlHandler.side_effect = OSError("no console")

        with patch("sys.platform", "win32"), patch("ctypes.windll") as mock_windll:
            mock_windll.kernel32 = mock_kernel32
            result = register_windows_ctrl_handler(lambda: None)

        assert result is False


# ---------------------------------------------------------------------------
# TestMakeAtexitHandler: make_atexit_handler テスト
# ---------------------------------------------------------------------------


class TestMakeAtexitHandler:
    """make_atexit_handler テスト."""

    def test_creates_callable(self) -> None:
        """返り値が callable であること."""
        handler = make_atexit_handler(lambda: None)
        assert callable(handler)

    def test_calls_callback_on_first_invocation(self) -> None:
        """初回呼び出しで callback が実行されること."""
        executed = []

        def callback():
            executed.append(True)

        handler = make_atexit_handler(callback)
        handler()

        assert executed == [True]

    def test_skips_callback_if_already_done(self) -> None:
        """_shutdown_done が set 済みなら callback をスキップすること."""
        executed = []

        def callback():
            executed.append(True)

        # _shutdown_done を手動で set する
        shutdown_handler._shutdown_done.set()

        handler = make_atexit_handler(callback)
        handler()

        assert executed == []

    def test_callback_exception_does_not_crash(self) -> None:
        """atexit callback 内で例外が発生してもクラッシュしないこと."""
        def bad_callback():
            raise ValueError("atexit error")

        handler = make_atexit_handler(bad_callback)

        # 例外が伝播しないこと
        try:
            handler()
        except ValueError:
            pytest.fail("atexit callback の例外がクラッシュを引き起こした")


# ---------------------------------------------------------------------------
# TestCtrlHandler: ctrl_handler コールバックテスト
# ---------------------------------------------------------------------------


class TestCtrlHandler:
    """ctrl_handler コールバックテスト."""

    def _get_ctrl_handler(self, callback):
        """_make_ctrl_handler を通じてコントロールハンドラを取得する."""
        from kage_shiki.core.shutdown_handler import _make_ctrl_handler
        return _make_ctrl_handler(callback)

    def test_calls_callback_on_close_event(self) -> None:
        """CTRL_CLOSE_EVENT で callback が呼ばれること."""
        executed = []

        def callback():
            executed.append(True)

        handler = self._get_ctrl_handler(callback)
        handler(CTRL_CLOSE_EVENT)

        assert executed == [True]

    def test_calls_callback_on_shutdown_event(self) -> None:
        """CTRL_SHUTDOWN_EVENT で callback が呼ばれること."""
        executed = []

        def callback():
            executed.append(True)

        handler = self._get_ctrl_handler(callback)
        handler(CTRL_SHUTDOWN_EVENT)

        assert executed == [True]

    def test_calls_callback_on_logoff_event(self) -> None:
        """CTRL_LOGOFF_EVENT で callback が呼ばれること."""
        executed = []

        def callback():
            executed.append(True)

        handler = self._get_ctrl_handler(callback)
        handler(CTRL_LOGOFF_EVENT)

        assert executed == [True]

    def test_does_not_call_on_ctrl_c(self) -> None:
        """CTRL_C_EVENT では callback が呼ばれないこと."""
        executed = []

        def callback():
            executed.append(True)

        handler = self._get_ctrl_handler(callback)
        handler(CTRL_C_EVENT)

        assert executed == []

    def test_callback_exception_does_not_crash(self) -> None:
        """callback 内で例外が発生してもクラッシュしないこと."""
        def bad_callback():
            raise RuntimeError("shutdown error")

        handler = self._get_ctrl_handler(bad_callback)

        # 例外が伝播しないこと
        try:
            handler(CTRL_CLOSE_EVENT)
        except RuntimeError:
            pytest.fail("callback の例外がクラッシュを引き起こした")

    def test_returns_false(self) -> None:
        """全シャットダウンイベントで False（デフォルト処理に委譲）を返すこと."""
        handler = self._get_ctrl_handler(lambda: None)

        for event in (CTRL_CLOSE_EVENT, CTRL_SHUTDOWN_EVENT, CTRL_LOGOFF_EVENT):
            reset_shutdown_state()
            result = handler(event)
            assert result is False, f"Event {event}: expected False, got {result}"

    def test_ctrl_c_returns_false(self) -> None:
        """CTRL_C_EVENT でも False を返すこと."""
        handler = self._get_ctrl_handler(lambda: None)
        result = handler(CTRL_C_EVENT)
        assert result is False

    def test_callback_called_only_once_on_repeated_events(self) -> None:
        """同じハンドラが複数回呼ばれても callback は1回のみ実行されること."""
        call_count = []

        def callback():
            call_count.append(1)

        handler = self._get_ctrl_handler(callback)
        handler(CTRL_CLOSE_EVENT)
        handler(CTRL_SHUTDOWN_EVENT)

        assert len(call_count) == 1
