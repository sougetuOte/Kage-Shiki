"""SystemTray のテスト (T-11).

対応 FR: FR-2.7〜2.10 — システムトレイ常駐
対応設計: D-9 — pystray 通知 + 遅延通知フォールバック
"""

from collections.abc import Callable
from unittest.mock import MagicMock, patch

from kage_shiki.gui.mascot_view import MascotView
from kage_shiki.tray.system_tray import SystemTray


class FakeMascotView:
    """テスト用の MascotView Protocol 実装."""

    def __init__(self) -> None:
        self.shown = False
        self.hidden = False
        self._display_text_calls: list[str] = []

    def show(self) -> None:
        self.shown = True
        self.hidden = False

    def hide(self) -> None:
        self.hidden = True
        self.shown = False

    def display_text(self, text: str) -> None:
        self._display_text_calls.append(text)

    def set_body_state(self, state: str) -> None:
        pass

    def schedule(self, delay_ms: int, callback: Callable) -> None:
        pass

    def on_click(self, handler: Callable[[int, int], None]) -> None:
        pass


class TestSystemTrayMenu:
    """メニュー構造の検証."""

    def test_has_menu_items(self) -> None:
        """SystemTray がメニュー項目を持つこと."""
        view = FakeMascotView()
        shutdown_cb = MagicMock()
        tray = SystemTray(view, shutdown_callback=shutdown_cb)

        menu_items = tray.get_menu_items()
        labels = [item.text for item in menu_items]
        assert "表示" in labels
        assert "最小化" in labels
        assert "終了" in labels

    def test_menu_includes_wizard_when_callback_set(self) -> None:
        """wizard_callback 設定時にウィザードメニューが含まれること."""
        view = FakeMascotView()
        tray = SystemTray(
            view, shutdown_callback=MagicMock(),
            wizard_callback=MagicMock(),
        )
        labels = [item.text for item in tray.get_menu_items()]
        assert "ウィザード起動" in labels

    def test_menu_excludes_wizard_when_no_callback(self) -> None:
        """wizard_callback 未設定時にウィザードメニューが含まれないこと."""
        view = FakeMascotView()
        tray = SystemTray(view, shutdown_callback=MagicMock())
        labels = [item.text for item in tray.get_menu_items()]
        assert "ウィザード起動" not in labels


class TestSystemTrayActions:
    """メニューアクションの動作検証."""

    def test_show_action_calls_view_show(self) -> None:
        """「表示」メニュー選択時に MascotView.show() が呼ばれること."""
        view = FakeMascotView()
        shutdown_cb = MagicMock()
        tray = SystemTray(view, shutdown_callback=shutdown_cb)

        tray.action_show()
        assert view.shown is True

    def test_hide_action_calls_view_hide(self) -> None:
        """action_hide() で MascotView.hide() が呼ばれること (FR-2.8)."""
        view = FakeMascotView()
        shutdown_cb = MagicMock()
        tray = SystemTray(view, shutdown_callback=shutdown_cb)

        tray.action_hide()
        assert view.hidden is True

    def test_toggle_hides_when_visible(self) -> None:
        """action_toggle() で表示中→非表示になること."""
        view = FakeMascotView()
        tray = SystemTray(view, shutdown_callback=MagicMock())

        assert tray._visible is True
        tray.action_toggle()
        assert view.hidden is True
        assert tray._visible is False

    def test_toggle_shows_when_hidden(self) -> None:
        """action_toggle() で非表示→表示になること."""
        view = FakeMascotView()
        tray = SystemTray(view, shutdown_callback=MagicMock())

        tray.action_hide()
        assert tray._visible is False

        tray.action_toggle()
        assert view.shown is True
        assert tray._visible is True

    def test_show_sets_visible_flag(self) -> None:
        """action_show() で _visible が True になること."""
        view = FakeMascotView()
        tray = SystemTray(view, shutdown_callback=MagicMock())
        tray._visible = False

        tray.action_show()
        assert tray._visible is True

    def test_hide_sets_visible_flag(self) -> None:
        """action_hide() で _visible が False になること."""
        view = FakeMascotView()
        tray = SystemTray(view, shutdown_callback=MagicMock())

        tray.action_hide()
        assert tray._visible is False

    def test_wizard_action_calls_callback(self) -> None:
        """「ウィザード起動」で wizard_callback が呼ばれること."""
        view = FakeMascotView()
        wizard_cb = MagicMock()
        tray = SystemTray(
            view, shutdown_callback=MagicMock(),
            wizard_callback=wizard_cb,
        )
        tray.action_wizard()
        wizard_cb.assert_called_once()

    def test_wizard_action_noop_without_callback(self) -> None:
        """wizard_callback 未設定時に action_wizard がエラーにならないこと."""
        view = FakeMascotView()
        tray = SystemTray(view, shutdown_callback=MagicMock())
        tray.action_wizard()  # should not raise

    def test_quit_action_calls_shutdown(self) -> None:
        """「終了」メニュー選択時にシャットダウンコールバックが呼ばれること."""
        view = FakeMascotView()
        shutdown_cb = MagicMock()
        tray = SystemTray(view, shutdown_callback=shutdown_cb)

        tray.action_quit()
        shutdown_cb.assert_called_once()


class TestSystemTrayNotify:
    """通知の動作検証."""

    def test_notify_does_not_crash_without_icon(self) -> None:
        """_icon 未設定時に notify() が例外でクラッシュしないこと."""
        view = FakeMascotView()
        shutdown_cb = MagicMock()
        tray = SystemTray(view, shutdown_callback=shutdown_cb)

        tray.notify("テスト通知", "影式")

    def test_notify_with_icon_exception(self) -> None:
        """_icon 設定済みで notify() が例外を投げてもクラッシュしないこと."""
        view = FakeMascotView()
        shutdown_cb = MagicMock()
        tray = SystemTray(view, shutdown_callback=shutdown_cb)

        mock_icon = MagicMock()
        mock_icon.notify.side_effect = RuntimeError("notify failed")
        tray._icon = mock_icon

        # 例外が握りつぶされることを確認
        tray.notify("テスト通知")

    def test_notify_with_fallback_sets_flag_and_notifies(self) -> None:
        """notify_with_fallback() がトレイ通知と遅延フラグの両方を設定すること."""
        view = FakeMascotView()
        shutdown_cb = MagicMock()
        tray = SystemTray(view, shutdown_callback=shutdown_cb)

        tray.notify_with_fallback("APIキーエラー")

        assert tray.error_notification_pending is True
        assert tray.error_notification_message == "APIキーエラー"

    def test_notify_with_fallback_clears_on_show(self) -> None:
        """notify_with_fallback() 後に show() で遅延通知が表示されクリアされること."""
        view = FakeMascotView()
        shutdown_cb = MagicMock()
        tray = SystemTray(view, shutdown_callback=shutdown_cb)

        tray.notify_with_fallback("APIキーエラー")
        tray.action_show()

        assert tray.error_notification_pending is False
        assert "APIキーエラー" in view._display_text_calls


class TestSystemTrayPendingNotification:
    """遅延通知の動作検証."""

    def test_pending_notification_flag(self) -> None:
        """遅延通知フラグが正しく管理されること."""
        view = FakeMascotView()
        shutdown_cb = MagicMock()
        tray = SystemTray(view, shutdown_callback=shutdown_cb)

        assert tray.error_notification_pending is False
        assert tray.error_notification_message == ""

        tray.set_error_notification("テストエラー")
        assert tray.error_notification_pending is True
        assert tray.error_notification_message == "テストエラー"

    def test_check_pending_clears_flag(self) -> None:
        """show 時の遅延通知チェックでフラグがクリアされること."""
        view = FakeMascotView()
        shutdown_cb = MagicMock()
        tray = SystemTray(view, shutdown_callback=shutdown_cb)

        tray.set_error_notification("テストエラー")
        tray.check_pending_notification()

        assert tray.error_notification_pending is False
        assert tray.error_notification_message == ""
        assert "テストエラー" in view._display_text_calls

    def test_check_pending_noop_when_no_notification(self) -> None:
        """通知がない場合は check_pending_notification が何もしないこと."""
        view = FakeMascotView()
        shutdown_cb = MagicMock()
        tray = SystemTray(view, shutdown_callback=shutdown_cb)

        tray.check_pending_notification()
        assert view._display_text_calls == []


class TestSystemTrayIcon:
    """アイコン生成の検証."""

    def test_create_icon_image(self) -> None:
        """アイコン画像が生成できること."""
        view = FakeMascotView()
        shutdown_cb = MagicMock()
        tray = SystemTray(view, shutdown_callback=shutdown_cb)

        image = tray.create_icon_image()
        assert image is not None
        assert image.size == (64, 64)

    def test_run_detached_noop_without_icon(self) -> None:
        """_icon 未設定時に run_detached() が何もしないこと."""
        view = FakeMascotView()
        shutdown_cb = MagicMock()
        tray = SystemTray(view, shutdown_callback=shutdown_cb)

        # 例外が発生しないことを確認
        tray.run_detached()

    def test_stop_noop_without_icon(self) -> None:
        """_icon 未設定時に stop() が何もしないこと."""
        view = FakeMascotView()
        shutdown_cb = MagicMock()
        tray = SystemTray(view, shutdown_callback=shutdown_cb)

        tray.stop()

    def test_stop_with_icon_exception(self) -> None:
        """_icon 設定済みで stop() が例外を投げてもクラッシュしないこと."""
        view = FakeMascotView()
        shutdown_cb = MagicMock()
        tray = SystemTray(view, shutdown_callback=shutdown_cb)

        mock_icon = MagicMock()
        mock_icon.stop.side_effect = RuntimeError("stop failed")
        tray._icon = mock_icon

        tray.stop()

    def test_run_detached_with_icon_exception(self) -> None:
        """_icon 設定済みで run_detached() が例外を投げてもクラッシュしないこと."""
        view = FakeMascotView()
        shutdown_cb = MagicMock()
        tray = SystemTray(view, shutdown_callback=shutdown_cb)

        mock_icon = MagicMock()
        mock_icon.run_detached.side_effect = RuntimeError("run_detached failed")
        tray._icon = mock_icon

        tray.run_detached()

    def test_setup_icon_creates_pystray_icon(self) -> None:
        """setup_icon() が pystray.Icon を正しく初期化すること (WARN-002)."""
        view = FakeMascotView()
        shutdown_cb = MagicMock()
        tray = SystemTray(view, shutdown_callback=shutdown_cb)

        mock_pystray = MagicMock()
        mock_icon_instance = MagicMock()
        mock_pystray.Icon.return_value = mock_icon_instance

        with patch.dict("sys.modules", {"pystray": mock_pystray}):
            tray.setup_icon()

        mock_pystray.Icon.assert_called_once()
        assert tray._icon is mock_icon_instance

    def test_setup_icon_handles_import_error(self) -> None:
        """setup_icon() で pystray が import できない場合もクラッシュしないこと."""
        view = FakeMascotView()
        shutdown_cb = MagicMock()
        tray = SystemTray(view, shutdown_callback=shutdown_cb)

        with patch.dict("sys.modules", {"pystray": None}):
            tray.setup_icon()

        assert tray._icon is None


class TestFakeMascotViewProtocol:
    """FakeMascotView の Protocol 準拠検証 (WARN-006)."""

    def test_isinstance_check(self) -> None:
        """FakeMascotView が MascotView Protocol の isinstance チェックを通ること."""
        view = FakeMascotView()
        assert isinstance(view, MascotView)
