"""TkinterMascotView: tkinter による MascotView Protocol 実装.

対応 FR:
    FR-2.1: 枠なし透過ウィンドウ（overrideredirect）
    FR-2.2: ドラッグで任意位置に移動
    FR-2.3: テキスト入力欄と送信ボタン
    FR-2.4: マスコットのセリフをテキスト表示
    FR-2.6: MascotView Protocol の6メソッドを実装
    FR-7.1〜7.5: エラー表示 UI（専用エラー画面 + 警告バー）
"""

import queue
import tkinter as tk
from collections.abc import Callable

from kage_shiki.core.config import GuiConfig


class TkinterMascotView:
    """tkinter を使った MascotView Protocol 実装.

    枠なし透過ウィンドウとして描画し、ドラッグ移動・テキスト表示・
    入力送信の各機能を提供する。

    Attributes:
        text_var: セリフ表示用の StringVar。
        entry_var: 入力欄用の StringVar。

    Args:
        root: tkinter の Tk インスタンス（外部から注入）。
        input_queue: ユーザー入力テキストを enqueue するキュー。
        config: GUI 設定パラメータ。
    """

    def __init__(
        self,
        root: tk.Tk,
        input_queue: queue.Queue,
        config: GuiConfig,
    ) -> None:
        """TkinterMascotView を初期化する.

        Args:
            root: tkinter の Tk インスタンス。mainloop() は呼ばない。
            input_queue: バックグラウンドスレッドへの入力キュー。
            config: GUI 設定パラメータ（ウィンドウサイズ・フォント等）。
        """
        self._root = root
        self._input_queue = input_queue
        self._config = config
        self._click_handler: Callable[[int, int], None] | None = None

        # ドラッグ移動用の座標記録
        self._drag_start_x: int = 0
        self._drag_start_y: int = 0

        # エラー表示 UI（show_error_screen / show_warning_bar で生成）
        self._error_window: tk.Toplevel | None = None
        self._warning_bar: tk.Frame | None = None

        # StringVar は root が生きている間のみ有効
        self.text_var = tk.StringVar(master=root)
        self.entry_var = tk.StringVar(master=root)

        self._build_window()
        self._build_widgets(config)
        self._bind_events()

    def _build_window(self) -> None:
        """ウィンドウ基本設定を適用する."""
        config = self._config
        self._root.overrideredirect(True)
        self._root.geometry(f"{config.window_width}x{config.window_height}")
        self._root.attributes("-alpha", config.opacity)
        self._root.attributes("-topmost", config.topmost)

    def _build_widgets(self, config: GuiConfig) -> None:
        """ウィジェットを構築してレイアウトする.

        レイアウト:
            - name_label: キャラクター名ラベル（上部）
            - text_label: セリフ表示エリア（中央）
            - 入力エリア: Entry + 送信ボタン（下部）

        Args:
            config: フォント設定を含む GuiConfig。
        """
        font_spec = (
            (config.font_family, config.font_size)
            if config.font_family
            else ("", config.font_size)
        )

        # キャラクター名ラベル（上部）
        self._name_var = tk.StringVar(master=self._root, value="影式")
        self._name_label = tk.Label(
            self._root,
            textvariable=self._name_var,
            font=font_spec,
        )
        self._name_label.pack(anchor="nw", padx=8, pady=(8, 0))

        # セリフ表示エリア（中央）
        self._text_label = tk.Label(
            self._root,
            textvariable=self.text_var,
            font=font_spec,
            wraplength=config.window_width - 20,
            justify="left",
        )
        self._text_label.pack(fill="both", expand=True, padx=8, pady=8)

        # 入力エリアのフレーム（下部）
        input_frame = tk.Frame(self._root)
        input_frame.pack(fill="x", padx=8, pady=(0, 8))

        self._entry = tk.Entry(input_frame, textvariable=self.entry_var)
        self._entry.pack(side="left", fill="x", expand=True)

        self._submit_button = tk.Button(
            input_frame,
            text="送信",
            command=self._submit,
        )
        self._submit_button.pack(side="right", padx=(4, 0))

    def _bind_events(self) -> None:
        """イベントバインドを設定する."""
        # Enter キーで送信
        self._entry.bind("<Return>", lambda _event: self._submit())

        # ドラッグ移動
        self._root.bind("<Button-1>", self._on_drag_start)
        self._root.bind("<B1-Motion>", self._on_drag_motion)

    def _on_drag_start(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        """ドラッグ開始時にマウス座標を記録する.

        Args:
            event: tkinter のマウスイベント。
        """
        self._drag_start_x = event.x
        self._drag_start_y = event.y

        # 登録されたクリックハンドラーがあれば呼び出す
        if self._click_handler is not None:
            screen_x = self._root.winfo_x() + event.x
            screen_y = self._root.winfo_y() + event.y
            self._click_handler(screen_x, screen_y)

    def _on_drag_motion(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        """ドラッグ中にウィンドウ位置を更新する.

        Args:
            event: tkinter のマウスイベント。
        """
        new_x = self._root.winfo_x() + (event.x - self._drag_start_x)
        new_y = self._root.winfo_y() + (event.y - self._drag_start_y)
        self._root.geometry(f"+{new_x}+{new_y}")

    def _submit(self) -> None:
        """入力欄のテキストを input_queue に enqueue して入力欄をクリアする.

        空文字の場合は enqueue しない。
        """
        text = self.entry_var.get()
        if not text:
            return
        self._input_queue.put(text)
        self.entry_var.set("")

    # ------------------------------------------------------------------
    # MascotView Protocol の実装
    # ------------------------------------------------------------------

    def show(self) -> None:
        """ウィンドウを表示する."""
        self._root.deiconify()

    def hide(self) -> None:
        """ウィンドウを非表示にする."""
        self._root.withdraw()

    def display_text(self, text: str) -> None:
        """マスコットのセリフテキストを更新する.

        Args:
            text: 表示するテキスト。空文字も許容する。
        """
        self.text_var.set(text)

    def set_body_state(self, state: str) -> None:
        """ボディ表示状態を設定する（Phase 1 は no-op）.

        Args:
            state: 状態識別子（例: "idle", "talking"）。Phase 2 で実装予定。
        """

    def schedule(self, delay_ms: int, callback: Callable) -> None:
        """GUI スレッド上で遅延コールバックを実行する.

        Args:
            delay_ms: 遅延時間（ミリ秒）。
            callback: 遅延後に実行するコールバック。
        """
        self._root.after(delay_ms, callback)

    def on_click(self, handler: Callable[[int, int], None]) -> None:
        """ウィンドウクリックイベントにハンドラーを登録する.

        既存のハンドラーがある場合は置き換える。

        Args:
            handler: クリック時に呼ばれるコールバック。引数は (x, y) のスクリーン座標。
        """
        self._click_handler = handler

    # ------------------------------------------------------------------
    # エラー表示 UI（D-6 Section 5.4）
    # ------------------------------------------------------------------

    def set_character_name(self, name: str) -> None:
        """キャラクター名ラベルを更新する.

        Args:
            name: 表示するキャラクター名。
        """
        self._name_var.set(name)

    def show_error_screen(
        self,
        message: str,
        on_open_log: Callable[[], None] | None = None,
    ) -> None:
        """専用エラー画面を表示する（Critical エラー用）.

        D-6 Section 5.4.1: 400x300 の Toplevel ウィンドウにメッセージと
        「ログを開く」「閉じる」ボタンを表示する。

        Args:
            message: 表示するエラーメッセージ。
            on_open_log: 「ログを開く」ボタン押下時のコールバック。
                None の場合はボタンを非表示にする。
        """
        error_win = tk.Toplevel(self._root)
        error_win.title("影式 — エラー")
        error_win.geometry("400x300")
        error_win.resizable(False, False)

        msg_label = tk.Label(
            error_win,
            text=message,
            wraplength=360,
            justify="left",
            padx=20,
            pady=20,
        )
        msg_label.pack(fill="both", expand=True)

        btn_frame = tk.Frame(error_win)
        btn_frame.pack(pady=(0, 16))

        if on_open_log is not None:
            log_btn = tk.Button(
                btn_frame,
                text="ログを開く",
                command=on_open_log,
            )
            log_btn.pack(side="left", padx=(0, 8))

        close_btn = tk.Button(
            btn_frame,
            text="閉じる",
            command=error_win.destroy,
        )
        close_btn.pack(side="left")

        self._error_window = error_win

    def show_warning_bar(self, message: str) -> None:
        """警告バーをメインウィンドウ上部に表示する（Warning エラー用）.

        D-6 Section 5.4.2: 折りたたみ可能なバーをメインウィンドウ最上部に
        表示する。クリックで詳細を展開/折りたたみ、×ボタンで閉じる。

        Args:
            message: 表示する警告メッセージ。
        """
        bar = tk.Frame(self._root, bg="#FFF3CD")

        # 折りたたみ時は先頭行のみ表示
        first_line = message.split("\n")[0]

        label = tk.Label(
            bar,
            text=f"[!] {first_line}",
            bg="#FFF3CD",
            fg="#856404",
            anchor="w",
            padx=8,
            cursor="hand2",
        )
        label.pack(side="left", fill="x", expand=True)

        # クリックで展開/折りたたみをトグル
        def _toggle_expand(_event: tk.Event | None = None) -> None:  # type: ignore[type-arg]
            current = label.cget("text")
            if current == f"[!] {first_line}":
                label.configure(text=f"[!] {message}")
            else:
                label.configure(text=f"[!] {first_line}")

        label.bind("<Button-1>", _toggle_expand)
        bar._toggle_expand = _toggle_expand  # type: ignore[attr-defined]

        close_btn = tk.Button(
            bar,
            text="×",
            bg="#FFF3CD",
            fg="#856404",
            relief="flat",
            command=bar.destroy,
        )
        close_btn.pack(side="right", padx=4)

        # 最上部に配置（既存ウィジェットの上に）
        bar.pack(fill="x", before=self._name_label)

        self._warning_bar = bar
