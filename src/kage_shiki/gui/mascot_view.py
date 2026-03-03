"""MascotView Protocol 定義.

対応 FR:
    FR-2.6: MascotView Protocol の6メソッド定義
"""

from collections.abc import Callable
from typing import Protocol, runtime_checkable


@runtime_checkable
class MascotView(Protocol):
    """マスコット GUI の抽象インターフェース.

    任意の GUI バックエンド（tkinter、Qt 等）がこの Protocol を実装することで、
    AgentCore や SystemTray は具体的な実装に依存しない。

    Methods:
        show: ウィンドウを表示する。
        hide: ウィンドウを非表示にする。
        display_text: マスコットのセリフテキストを更新する。
        set_body_state: ボディ表示状態を設定する（Phase 2 以降で有効化）。
        schedule: GUI スレッド上で遅延コールバックを実行する。
        on_click: ウィンドウクリックイベントにハンドラーを登録する。
    """

    def show(self) -> None:
        """ウィンドウを表示する."""
        ...

    def hide(self) -> None:
        """ウィンドウを非表示にする."""
        ...

    def display_text(self, text: str) -> None:
        """マスコットのセリフテキストを更新する.

        Args:
            text: 表示するテキスト。空文字も許容する。
        """
        ...

    def set_body_state(self, state: str) -> None:
        """ボディ表示状態を設定する.

        Phase 1 では no-op。Phase 2 でボディアニメーションに使用する。

        Args:
            state: 状態識別子（例: "idle", "talking"）。
        """
        ...

    def schedule(self, delay_ms: int, callback: Callable) -> None:
        """GUI スレッド上で遅延コールバックを実行する.

        バックグラウンドスレッドから GUI を安全に更新するために使用する。
        tkinter 実装では root.after() に対応する。

        Args:
            delay_ms: 遅延時間（ミリ秒）。0 以上を指定する。
            callback: 遅延後に実行するコールバック。
        """
        ...

    def on_click(self, handler: Callable[[int, int], None]) -> None:
        """ウィンドウクリックイベントにハンドラーを登録する.

        Args:
            handler: クリック時に呼ばれるコールバック。
                引数は (x, y) のスクリーン座標。
        """
        ...
