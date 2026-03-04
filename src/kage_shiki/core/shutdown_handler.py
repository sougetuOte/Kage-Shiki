"""シャットダウン2層防御 (T-19, FR-3.9, D-11).

Layer 1: atexit フック（正常終了時）
Layer 2: ctypes SetConsoleCtrlHandler（コンソールクローズ / Windows シャットダウン時）

2重実行防止は threading.Event で管理する。
"""

import ctypes
import ctypes.wintypes
import logging
import sys
import threading

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Windows コントロールイベント定数 (D-11 Section 5.1)
# ---------------------------------------------------------------------------

CTRL_C_EVENT = 0
CTRL_BREAK_EVENT = 1
CTRL_CLOSE_EVENT = 2
CTRL_LOGOFF_EVENT = 5
CTRL_SHUTDOWN_EVENT = 6

_SHUTDOWN_EVENTS = frozenset({CTRL_CLOSE_EVENT, CTRL_LOGOFF_EVENT, CTRL_SHUTDOWN_EVENT})

# Windows API 型定義
_HandlerRoutine = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.DWORD)

# 2重実行防止フラグ
_shutdown_done = threading.Event()

# コールバック参照保持（GC 対策）
_ctrl_handler_ref: _HandlerRoutine | None = None


def _make_ctrl_handler(shutdown_callback):
    """SetConsoleCtrlHandler 用コールバックを生成する."""

    def handler(ctrl_type: int) -> bool:
        if ctrl_type in _SHUTDOWN_EVENTS:  # noqa: SIM102
            if not _shutdown_done.is_set():
                _shutdown_done.set()
                logger.info(
                    "Windows コントロールイベント受信: ctrl_type=%d", ctrl_type,
                )
                try:
                    shutdown_callback()
                except Exception:
                    logger.error(
                        "シャットダウン処理でエラー", exc_info=True,
                    )
        return False

    return handler


def register_windows_ctrl_handler(shutdown_callback) -> bool:
    """SetConsoleCtrlHandler を登録する (D-11 Section 5.2).

    Args:
        shutdown_callback: 引数なし・戻り値なしの同期関数。

    Returns:
        登録成功なら True。失敗（コンソールなし環境等）なら False。
    """
    global _ctrl_handler_ref

    if sys.platform != "win32":
        logger.info("Windows 以外の環境: SetConsoleCtrlHandler をスキップ")
        return False

    raw_handler = _make_ctrl_handler(shutdown_callback)
    _ctrl_handler_ref = _HandlerRoutine(raw_handler)

    try:
        kernel32 = ctypes.windll.kernel32
        result = kernel32.SetConsoleCtrlHandler(_ctrl_handler_ref, True)
    except (OSError, AttributeError):
        logger.warning(
            "SetConsoleCtrlHandler の登録に失敗しました。"
            "atexit（Layer 1）が保護します。",
        )
        return False

    if result:
        logger.info("Windows SetConsoleCtrlHandler 登録完了")
        return True

    logger.warning(
        "SetConsoleCtrlHandler の登録に失敗しました。"
        "コンソールなし環境の可能性があります。"
        "atexit（Layer 1）が保護します。",
    )
    return False


def make_atexit_handler(shutdown_callback):
    """atexit 用のラッパーを生成する (D-11 Section 5.2).

    _shutdown_done フラグで2重実行を防止する。

    Args:
        shutdown_callback: 引数なし・戻り値なしの同期関数。

    Returns:
        atexit.register に渡すコールバック関数。

    Note:
        返り値を atexit.register() に渡して使用すること:
            handler = make_atexit_handler(callback)
            atexit.register(handler)
    """

    def atexit_handler():
        if not _shutdown_done.is_set():
            _shutdown_done.set()
            logger.info("atexit ハンドラ実行")
            try:
                shutdown_callback()
            except Exception:
                logger.error(
                    "atexit シャットダウン処理でエラー", exc_info=True,
                )

    return atexit_handler


def reset_shutdown_state() -> None:
    """テスト用: シャットダウン状態をリセットする."""
    global _ctrl_handler_ref
    _shutdown_done.clear()
    _ctrl_handler_ref = None
