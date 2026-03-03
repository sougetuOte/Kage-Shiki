"""GUI テスト用フィクスチャ.

Note:
    pyenv-win 環境では root.destroy() 後に tk.Tk() を再生成すると
    Tcl ライブラリの探索が失敗するケースがある。
    そのため tk_root はセッションスコープで1インスタンスを共有し、
    各テスト後は withdraw() で非表示に戻す設計とする。
"""

import queue
import tkinter as tk

import pytest

from kage_shiki.core.config import GuiConfig


@pytest.fixture(scope="session")
def tk_root():
    """非表示の tkinter ルートウィンドウをセッション全体で共有する.

    セッションスコープにより、同一プロセス内での tk.Tk() 複数回生成による
    TclError（pyenv-win 環境固有）を回避する。

    Yields:
        tk.Tk: mainloop を呼ばない状態の Tk インスタンス。
    """
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def input_queue():
    """ユーザー入力用キューを提供する.

    Returns:
        queue.Queue: 空のキューインスタンス。
    """
    return queue.Queue()


@pytest.fixture
def gui_config():
    """テスト用 GuiConfig を提供する.

    Returns:
        GuiConfig: デフォルト値の GuiConfig インスタンス。
    """
    return GuiConfig(
        window_width=400,
        window_height=300,
        opacity=0.95,
        topmost=False,  # テスト環境では最前面固定を無効化
        font_size=14,
        font_family="",
    )
