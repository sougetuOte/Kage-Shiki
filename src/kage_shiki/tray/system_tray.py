"""システムトレイ管理 (T-11).

対応 FR:
    FR-2.7: トレイアイコンに「表示」「終了」メニュー
    FR-2.8: 閉じるボタンでトレイ格納（action_hide 提供）
    FR-2.9: トレイメニューから「表示」「終了」を選択
    FR-2.10: 常時最前面表示（TkinterMascotView が管理）
対応設計: D-9 — pystray 通知 + 遅延通知フォールバック
"""

import logging
from collections.abc import Callable
from typing import Any

from PIL import Image, ImageDraw

from kage_shiki.gui.mascot_view import MascotView

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# アイコン描画定数
# ---------------------------------------------------------------------------

_ICON_SIZE = 64
_ICON_PADDING = 4
_ICON_FILL_COLOR = (100, 100, 200, 255)
_ICON_OUTLINE_COLOR = (50, 50, 150, 255)
_ICON_OUTLINE_WIDTH = 2
_ICON_TEXT_COLOR = (255, 255, 255, 255)
_ICON_TEXT = "K"
_ICON_TEXT_OFFSET_X = 6
_ICON_TEXT_OFFSET_Y = 8

_APP_TITLE = "影式"


class _MenuItem:
    """pystray.MenuItem と同じインターフェースを持つ軽量データクラス.

    テスト時に pystray を import せずにメニュー構造を検証できる。
    """

    def __init__(self, text: str, action: Callable) -> None:
        self.text = text
        self.action = action


class SystemTray:
    """システムトレイアイコンとメニューを管理する.

    pystray.Icon のラッパーとして機能し、MascotView の表示/非表示切り替え
    およびシャットダウンシーケンスの起動を提供する。

    Args:
        mascot_view: MascotView Protocol を実装するインスタンス。
        shutdown_callback: 「終了」選択時に呼び出すコールバック。
    """

    def __init__(
        self,
        mascot_view: MascotView,
        shutdown_callback: Callable[[], None],
    ) -> None:
        self._view = mascot_view
        self._shutdown_callback = shutdown_callback
        self._icon: Any | None = None

        # 遅延通知フラグ (D-9 Section 5.3)
        self.error_notification_pending: bool = False
        self.error_notification_message: str = ""

    def get_menu_items(self) -> list[_MenuItem]:
        """メニュー項目のリストを返す.

        Returns:
            「表示」「終了」の2項目。
        """
        return [
            _MenuItem("表示", self.action_show),
            _MenuItem("終了", self.action_quit),
        ]

    def action_show(self) -> None:
        """マスコットウィンドウを表示し、遅延通知があれば表示する."""
        self._view.show()
        self.check_pending_notification()

    def action_hide(self) -> None:
        """マスコットウィンドウをトレイに格納する (FR-2.8)."""
        self._view.hide()

    def action_quit(self) -> None:
        """シャットダウンシーケンスを開始し、トレイアイコンを停止する."""
        self._shutdown_callback()
        self.stop()

    def create_icon_image(self) -> Image.Image:
        """簡易なトレイアイコン画像を PIL で生成する.

        Returns:
            64x64 の RGBA Image。
        """
        image = Image.new("RGBA", (_ICON_SIZE, _ICON_SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse(
            [
                _ICON_PADDING,
                _ICON_PADDING,
                _ICON_SIZE - _ICON_PADDING,
                _ICON_SIZE - _ICON_PADDING,
            ],
            fill=_ICON_FILL_COLOR,
            outline=_ICON_OUTLINE_COLOR,
            width=_ICON_OUTLINE_WIDTH,
        )
        draw.text(
            (
                _ICON_SIZE // 2 - _ICON_TEXT_OFFSET_X,
                _ICON_SIZE // 2 - _ICON_TEXT_OFFSET_Y,
            ),
            _ICON_TEXT,
            fill=_ICON_TEXT_COLOR,
        )
        return image

    def setup_icon(self) -> None:
        """pystray.Icon を初期化する.

        実際のトレイアイコンの表示は run_detached() で開始する。
        """
        try:
            # pystray 未インストール環境でも起動可能にするための遅延インポート
            import pystray

            menu = pystray.Menu(
                pystray.MenuItem("表示", lambda _icon, _item: self.action_show()),
                pystray.MenuItem("終了", lambda _icon, _item: self.action_quit()),
            )
            self._icon = pystray.Icon(
                name="kage_shiki",
                icon=self.create_icon_image(),
                title=_APP_TITLE,
                menu=menu,
            )
        except Exception:
            logger.warning("pystray Icon の初期化に失敗しました", exc_info=True)

    def run_detached(self) -> None:
        """トレイアイコンをバックグラウンドスレッドで起動する."""
        if self._icon is not None:
            try:
                self._icon.run_detached()
            except Exception:
                logger.warning("トレイアイコンの起動に失敗しました", exc_info=True)

    def stop(self) -> None:
        """トレイアイコンを停止する."""
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception:
                logger.warning("トレイアイコンの停止に失敗しました", exc_info=True)

    def notify(self, message: str, title: str = _APP_TITLE) -> None:
        """トレイ通知を試みる (D-9 Section 5.2).

        pystray.Icon.notify() を呼び出す。Windows 11 では Silent failure の
        可能性があるため、遅延通知フラグも併用すること。

        Args:
            message: 通知本文。
            title: 通知タイトル。
        """
        if self._icon is not None:
            try:
                self._icon.notify(message, title)
            except Exception:
                logger.debug(
                    "トレイ通知の送信に失敗（遅延通知にフォールバック）",
                    exc_info=True,
                )

    def notify_with_fallback(self, message: str) -> None:
        """D-9 統合フロー: トレイ通知 + 遅延通知の二段構え.

        1. pystray.Icon.notify() を試みる
        2. 遅延通知フラグを設定する（次回 show() 時に display_text）

        Args:
            message: 通知するメッセージ。
        """
        self.notify(message)
        self.set_error_notification(message)

    def set_error_notification(self, message: str) -> None:
        """遅延通知フラグを設定する (D-9 Section 5.3).

        Args:
            message: 次回 show() 時に表示するメッセージ。
        """
        self.error_notification_pending = True
        self.error_notification_message = message

    def check_pending_notification(self) -> None:
        """遅延通知があれば MascotView に表示してフラグをクリアする."""
        if self.error_notification_pending:
            self._view.display_text(self.error_notification_message)
            self.error_notification_pending = False
            self.error_notification_message = ""
