"""T-10: MascotView Protocol + TkinterMascotView テスト.

対応 FR:
    - FR-2.1: 枠なし透過ウィンドウ（overrideredirect）
    - FR-2.2: ドラッグで任意位置に移動
    - FR-2.3: テキスト入力欄と送信ボタン
    - FR-2.4: マスコットのセリフをテキスト表示
    - FR-2.6: MascotView Protocol の6メソッドを実装
"""

from collections.abc import Callable
from unittest.mock import MagicMock, patch


class TestMascotViewProtocol:
    """MascotView Protocol 定義のテスト."""

    def test_protocol_importable(self) -> None:
        """MascotView Protocol がインポート可能であること."""
        from kage_shiki.gui.mascot_view import MascotView

        assert MascotView is not None

    def test_protocol_has_required_methods(self) -> None:
        """MascotView Protocol が6つの必須メソッドを持つこと."""
        from kage_shiki.gui.mascot_view import MascotView

        # typing.Protocol はアノテーションで各メソッドを持つ
        # __protocol_attrs__ で確認（Python 3.12+）
        assert hasattr(MascotView, "show")
        assert hasattr(MascotView, "hide")
        assert hasattr(MascotView, "display_text")
        assert hasattr(MascotView, "set_body_state")
        assert hasattr(MascotView, "schedule")
        assert hasattr(MascotView, "on_click")

    def test_protocol_is_runtime_checkable(self) -> None:
        """MascotView Protocol が runtime_checkable であること."""
        from kage_shiki.gui.mascot_view import MascotView

        # runtime_checkable なら isinstance チェックが可能
        # ダックタイピングの確認: 6メソッドを持つオブジェクトは Protocol に準拠する
        class FakeView:
            def show(self) -> None:
                pass

            def hide(self) -> None:
                pass

            def display_text(self, text: str) -> None:
                pass

            def set_body_state(self, state: str) -> None:
                pass

            def schedule(self, delay_ms: int, callback: Callable) -> None:
                pass

            def on_click(self, handler: Callable[[int, int], None]) -> None:
                pass

        fake = FakeView()
        assert isinstance(fake, MascotView)


class TestTkinterMascotViewInit:
    """TkinterMascotView 初期化テスト."""

    def test_importable(self) -> None:
        """TkinterMascotView がインポート可能であること."""
        from kage_shiki.gui.tkinter_view import TkinterMascotView

        assert TkinterMascotView is not None

    def test_instantiation(self, tk_root, input_queue, gui_config) -> None:
        """TkinterMascotView が正常にインスタンス化できること."""
        from kage_shiki.gui.tkinter_view import TkinterMascotView

        view = TkinterMascotView(root=tk_root, input_queue=input_queue, config=gui_config)
        assert view is not None

    def test_implements_mascot_view_protocol(self, tk_root, input_queue, gui_config) -> None:
        """TkinterMascotView が MascotView Protocol に準拠すること (FR-2.6)."""
        from kage_shiki.gui.mascot_view import MascotView
        from kage_shiki.gui.tkinter_view import TkinterMascotView

        view = TkinterMascotView(root=tk_root, input_queue=input_queue, config=gui_config)
        assert isinstance(view, MascotView)

    def test_overrideredirect_applied(self, tk_root, input_queue, gui_config) -> None:
        """overrideredirect(True) が適用されてタイトルバーなしになること (FR-2.1)."""
        from kage_shiki.gui.tkinter_view import TkinterMascotView

        TkinterMascotView(root=tk_root, input_queue=input_queue, config=gui_config)
        # overrideredirect の設定値を確認
        assert tk_root.overrideredirect() is True


class TestTkinterMascotViewDisplay:
    """TkinterMascotView の表示機能テスト."""

    def test_display_text_updates_label(self, tk_root, input_queue, gui_config) -> None:
        """display_text() でラベルのテキストが更新されること (FR-2.4)."""
        from kage_shiki.gui.tkinter_view import TkinterMascotView

        view = TkinterMascotView(root=tk_root, input_queue=input_queue, config=gui_config)
        view.display_text("こんにちは")

        assert view.text_var.get() == "こんにちは"

    def test_display_text_with_empty_string(self, tk_root, input_queue, gui_config) -> None:
        """display_text() に空文字を渡してもエラーにならないこと."""
        from kage_shiki.gui.tkinter_view import TkinterMascotView

        view = TkinterMascotView(root=tk_root, input_queue=input_queue, config=gui_config)
        view.display_text("")

        assert view.text_var.get() == ""

    def test_display_text_overwrites_previous(self, tk_root, input_queue, gui_config) -> None:
        """display_text() の連続呼び出しで最新テキストに上書きされること."""
        from kage_shiki.gui.tkinter_view import TkinterMascotView

        view = TkinterMascotView(root=tk_root, input_queue=input_queue, config=gui_config)
        view.display_text("最初のテキスト")
        view.display_text("更新後のテキスト")

        assert view.text_var.get() == "更新後のテキスト"


class TestTkinterMascotViewShowHide:
    """TkinterMascotView の表示/非表示テスト."""

    def test_show_makes_window_visible(self, tk_root, input_queue, gui_config) -> None:
        """show() でウィンドウが表示状態になること (FR-2.1)."""
        from kage_shiki.gui.tkinter_view import TkinterMascotView

        view = TkinterMascotView(root=tk_root, input_queue=input_queue, config=gui_config)
        # withdraw() で非表示にしてから show() を呼ぶ
        tk_root.withdraw()
        view.show()

        # winfo_viewable() は実際の表示状態、state() は管理状態を返す
        assert tk_root.state() != "withdrawn"

    def test_hide_makes_window_invisible(self, tk_root, input_queue, gui_config) -> None:
        """hide() でウィンドウが非表示状態になること."""
        from kage_shiki.gui.tkinter_view import TkinterMascotView

        view = TkinterMascotView(root=tk_root, input_queue=input_queue, config=gui_config)
        view.hide()

        assert tk_root.state() == "withdrawn"


class TestTkinterMascotViewSchedule:
    """TkinterMascotView の schedule() テスト."""

    def test_schedule_calls_root_after(self, tk_root, input_queue, gui_config) -> None:
        """schedule() が root.after() を呼び出すこと."""
        from kage_shiki.gui.tkinter_view import TkinterMascotView

        view = TkinterMascotView(root=tk_root, input_queue=input_queue, config=gui_config)

        callback = MagicMock()
        with patch.object(tk_root, "after") as mock_after:
            view.schedule(100, callback)
            mock_after.assert_called_once_with(100, callback)

    def test_schedule_with_zero_delay(self, tk_root, input_queue, gui_config) -> None:
        """schedule() にディレイ0を渡しても正常動作すること."""
        from kage_shiki.gui.tkinter_view import TkinterMascotView

        view = TkinterMascotView(root=tk_root, input_queue=input_queue, config=gui_config)

        callback = MagicMock()
        with patch.object(tk_root, "after") as mock_after:
            view.schedule(0, callback)
            mock_after.assert_called_once_with(0, callback)


class TestTkinterMascotViewOnClick:
    """TkinterMascotView の on_click() テスト."""

    def test_on_click_registers_handler(self, tk_root, input_queue, gui_config) -> None:
        """on_click() でクリックハンドラーが登録されること."""
        from kage_shiki.gui.tkinter_view import TkinterMascotView

        view = TkinterMascotView(root=tk_root, input_queue=input_queue, config=gui_config)

        handler = MagicMock()
        view.on_click(handler)

        # ハンドラーが内部に保存されていること
        assert view._click_handler is handler

    def test_on_click_replaces_previous_handler(self, tk_root, input_queue, gui_config) -> None:
        """on_click() の再呼び出しで前のハンドラーが置き換わること."""
        from kage_shiki.gui.tkinter_view import TkinterMascotView

        view = TkinterMascotView(root=tk_root, input_queue=input_queue, config=gui_config)

        handler1 = MagicMock()
        handler2 = MagicMock()
        view.on_click(handler1)
        view.on_click(handler2)

        assert view._click_handler is handler2


class TestTkinterMascotViewInput:
    """TkinterMascotView の入力送信テスト."""

    def test_submit_enqueues_text(self, tk_root, input_queue, gui_config) -> None:
        """送信ボタン押下でテキストが input_queue に enqueue されること (FR-2.3)."""
        from kage_shiki.gui.tkinter_view import TkinterMascotView

        view = TkinterMascotView(root=tk_root, input_queue=input_queue, config=gui_config)

        # 入力欄にテキストをセット
        view.entry_var.set("テストメッセージ")
        # 送信メソッドを直接呼び出す（ボタン押下と同等）
        view._submit()

        assert not input_queue.empty()
        assert input_queue.get_nowait() == "テストメッセージ"

    def test_submit_clears_entry(self, tk_root, input_queue, gui_config) -> None:
        """送信後に入力欄がクリアされること."""
        from kage_shiki.gui.tkinter_view import TkinterMascotView

        view = TkinterMascotView(root=tk_root, input_queue=input_queue, config=gui_config)

        view.entry_var.set("クリアされるテキスト")
        view._submit()

        assert view.entry_var.get() == ""

    def test_submit_with_empty_text_does_not_enqueue(
        self, tk_root, input_queue, gui_config,
    ) -> None:
        """空文字の送信では enqueue しないこと."""
        from kage_shiki.gui.tkinter_view import TkinterMascotView

        view = TkinterMascotView(root=tk_root, input_queue=input_queue, config=gui_config)

        view.entry_var.set("")
        view._submit()

        assert input_queue.empty()


class TestTkinterMascotViewSetBodyState:
    """TkinterMascotView の set_body_state() テスト."""

    def test_set_body_state_does_not_raise(self, tk_root, input_queue, gui_config) -> None:
        """set_body_state() が例外を出さないこと（Phase 1 は no-op）."""
        from kage_shiki.gui.tkinter_view import TkinterMascotView

        view = TkinterMascotView(root=tk_root, input_queue=input_queue, config=gui_config)

        # 例外が発生しなければ OK
        view.set_body_state("idle")
        view.set_body_state("talking")
        view.set_body_state("unknown_state")
