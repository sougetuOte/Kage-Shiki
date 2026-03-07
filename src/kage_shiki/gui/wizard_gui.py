"""ウィザード GUI (T-31, D-19).

対応 FR:
    FR-8.8: 方式選択画面（AI おまかせ / 既存イメージ / 白紙育成）
    FR-8.9: プレビュー会話 UI（入力・送信・やり直し・確定）
    FR-8.10: 凍結確認ダイアログ + persona_core.md 生成

設計:
    - 同一 root 内での Frame 切り替え方式（D-19 Atom A1）
    - WizardStep Enum による状態管理（D-19 Atom A2）
    - バックグラウンドスレッド + root.after() で LLM 非同期化（D-19 Atom A3）
    - MascotView Protocol は拡張しない（D-19 Atom A4）
    - ウィザード完了後はプロセス終了（D-19 Atom A5）

Note:
    ウィザードモードでは TkinterMascotView を生成しないため、
    root に overrideredirect(True) は設定されない。
    messagebox は通常のウィンドウとして表示される（D-19 Section 4.3 注意書き対処不要）。
"""

from __future__ import annotations

import contextlib
import logging
import os
import re
import tempfile
import threading
import tkinter as tk
from enum import Enum, auto
from pathlib import Path
from tkinter import messagebox
from typing import TYPE_CHECKING

from kage_shiki.persona.persona_system import PersonaCore, PersonaSystem

if TYPE_CHECKING:
    from kage_shiki.core.config import AppConfig
    from kage_shiki.persona.wizard import WizardController

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# WizardStep Enum (D-19 Atom A2)
# ---------------------------------------------------------------------------


class WizardStep(Enum):
    """ウィザードの現在の画面ステップ."""

    METHOD_SELECT = auto()
    INPUT_A = auto()
    INPUT_B = auto()
    INPUT_C = auto()
    GENERATING = auto()
    PREVIEW = auto()
    FREEZE_CONFIRM = auto()
    DONE = auto()


# ---------------------------------------------------------------------------
# config.toml の persona_frozen 更新 (D-19 Section 4.4)
# ---------------------------------------------------------------------------


def _set_persona_frozen(config_path: Path) -> None:
    """config.toml の persona_frozen を true にアトミックに書き換える."""
    text = config_path.read_text(encoding="utf-8")
    new_text, count = re.subn(
        r"^(\s*persona_frozen\s*=\s*)(?:false|true)\s*$",
        r"\1true",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if count == 0:
        raise ValueError("config.toml に persona_frozen の設定行が見つかりません")

    # アトミック書き込み: 一時ファイル → os.replace (CRIT-002 対応)
    fd, tmp_path = tempfile.mkstemp(
        dir=str(config_path.parent), suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(new_text)
        os.replace(tmp_path, str(config_path))
    except BaseException:
        # KeyboardInterrupt/SystemExit を含む全例外で一時ファイルを確実に削除
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)
        raise


# ---------------------------------------------------------------------------
# WizardGUI (D-19 Section 4.1)
# ---------------------------------------------------------------------------


class WizardGUI:
    """ウィザード GUI クラス.

    同一 root 内で Frame を切り替えて画面遷移を実現する。
    WizardController のビジネスロジックは変更しない（C-4）。

    Args:
        root: tkinter の Tk インスタンス。
        wizard_ctrl: WizardController インスタンス。
        persona_system: PersonaSystem インスタンス。
        data_dir: データディレクトリパス。
        config: AppConfig インスタンス。
        config_path: config.toml のパス（凍結時に persona_frozen を更新）。
    """

    def __init__(
        self,
        root: tk.Tk,
        wizard_ctrl: WizardController,
        persona_system: PersonaSystem,
        data_dir: Path,
        config: AppConfig,
        *,
        config_path: Path | None = None,
    ) -> None:
        self._root = root
        self._wizard_ctrl = wizard_ctrl
        self._persona_system = persona_system
        self._data_dir = data_dir
        self._config = config
        self._config_path = config_path or Path("config.toml")

        self._current_step = WizardStep.METHOD_SELECT
        self._current_frame: tk.Frame | None = None
        self._is_processing = False  # 連打防止ガード (CRIT-001)

        # プレビュー用の状態
        self._current_persona: PersonaCore | None = None
        self._current_style: str = ""
        self._preview_turns: list[dict[str, str]] = []

        # ウィジェット参照（テストからアクセス可能、show() 前は None）
        self._btn_method_a: tk.Button | None = None
        self._btn_method_b: tk.Button | None = None
        self._btn_method_c: tk.Button | None = None
        self._btn_back: tk.Button | None = None
        self._btn_submit: tk.Button | None = None
        self._btn_retry: tk.Button | None = None
        self._btn_confirm: tk.Button | None = None

        # 入力画面ウィジェット
        self._entry_keywords: tk.Entry | None = None
        self._text_description: tk.Text | None = None
        self._entry_name: tk.Entry | None = None
        self._entry_first_person: tk.Entry | None = None
        self._entry_user_name: tk.Entry | None = None

        # プレビュー画面ウィジェット
        self._preview_name_label: tk.Label | None = None
        self._preview_text: tk.Text | None = None
        self._preview_entry: tk.Entry | None = None
        self._preview_send_btn: tk.Button | None = None

        # 生成中画面ウィジェット (C-1 対応)
        self._generating_label: tk.Label | None = None
        self._dot_count: int = 0

    @property
    def current_step(self) -> WizardStep:
        """現在の画面ステップを返す."""
        return self._current_step

    def show(self) -> None:
        """ウィザードのメインウィジェットを表示する."""
        self._root.geometry("480x360")
        self._show_method_select()

    # ------------------------------------------------------------------
    # Frame 切り替えヘルパー
    # ------------------------------------------------------------------

    def _clear_frame(self) -> None:
        """現在の Frame を破棄する."""
        if self._current_frame is not None:
            self._current_frame.destroy()
            self._current_frame = None

    def _make_frame(self) -> tk.Frame:
        """新しい Frame を生成して表示する."""
        self._clear_frame()
        frame = tk.Frame(self._root)
        frame.pack(fill="both", expand=True)
        self._current_frame = frame
        return frame

    # ------------------------------------------------------------------
    # 方式選択画面 (FR-8.8)
    # ------------------------------------------------------------------

    def _show_method_select(self) -> None:
        """方式選択画面を表示する."""
        self._current_step = WizardStep.METHOD_SELECT
        self._is_processing = False
        self._root.geometry("480x360")
        frame = self._make_frame()

        tk.Label(
            frame, text="影式 セットアップウィザード",
            font=("", 16, "bold"),
        ).pack(pady=(20, 10))

        tk.Label(
            frame, text="まずはキャラクターを作成しましょう。",
        ).pack(pady=(0, 20))

        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill="x", padx=40)

        self._btn_method_a = tk.Button(
            btn_frame, text="AI おまかせ\nキーワードから AI がキャラを生成",
            command=self._show_input_a, height=2,
        )
        self._btn_method_a.pack(fill="x", pady=4)

        self._btn_method_b = tk.Button(
            btn_frame, text="既存イメージ\nあなたのイメージを自由に記述",
            command=self._show_input_b, height=2,
        )
        self._btn_method_b.pack(fill="x", pady=4)

        self._btn_method_c = tk.Button(
            btn_frame, text="白紙育成\n名前と一人称だけ決めて育てていく",
            command=self._show_input_c, height=2,
        )
        self._btn_method_c.pack(fill="x", pady=4)

    # ------------------------------------------------------------------
    # 方式 A 入力画面
    # ------------------------------------------------------------------

    def _show_input_a(self) -> None:
        """方式 A: キーワード入力画面を表示する."""
        self._current_step = WizardStep.INPUT_A
        frame = self._make_frame()

        tk.Label(
            frame, text="AI おまかせ: キーワード入力",
            font=("", 14, "bold"),
        ).pack(pady=(20, 10))

        tk.Label(frame, text="イメージするキーワードを入力:").pack(
            anchor="w", padx=40,
        )
        self._entry_keywords = tk.Entry(frame)
        self._entry_keywords.pack(fill="x", padx=40, pady=(0, 4))
        tk.Label(frame, text="（カンマ区切りで複数入力可能）").pack(
            anchor="w", padx=40,
        )

        tk.Label(frame, text="ユーザー名（任意）:").pack(
            anchor="w", padx=40, pady=(10, 0),
        )
        self._entry_user_name = tk.Entry(frame)
        self._entry_user_name.pack(fill="x", padx=40)

        btn_row = tk.Frame(frame)
        btn_row.pack(pady=20)
        self._btn_back = tk.Button(
            btn_row, text="戻る", command=self._show_method_select,
        )
        self._btn_back.pack(side="left", padx=8)
        self._btn_submit = tk.Button(
            btn_row, text="生成する", command=self._on_generate_a,
        )
        self._btn_submit.pack(side="left", padx=8)

    def _on_generate_a(self) -> None:
        """方式 A の生成処理を開始する."""
        if self._is_processing:
            return
        keywords_raw = self._entry_keywords.get().strip()
        if not keywords_raw:
            return
        keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
        user_name = self._entry_user_name.get().strip()

        self._is_processing = True
        self._show_generating()

        def _bg() -> None:
            try:
                associations = self._wizard_ctrl.expand_associations(keywords)
                candidates = self._wizard_ctrl.generate_candidates(
                    associations, user_name=user_name,
                )
                if not candidates:
                    self._root.after(0, self._on_generation_error, "候補が生成されませんでした")
                    return
                selected = candidates[0]
                style = self._wizard_ctrl.generate_style_samples(selected)
                self._root.after(
                    0, self._on_generation_done, selected, style,
                )
            except Exception:
                logger.error("方式 A 生成失敗", exc_info=True)
                self._root.after(0, self._on_generation_error, "キャラクター生成に失敗しました")

        threading.Thread(target=_bg, daemon=True).start()

    # ------------------------------------------------------------------
    # 方式 B 入力画面
    # ------------------------------------------------------------------

    def _show_input_b(self) -> None:
        """方式 B: 自由記述入力画面を表示する."""
        self._current_step = WizardStep.INPUT_B
        frame = self._make_frame()

        tk.Label(
            frame, text="既存イメージ: 自由記述",
            font=("", 14, "bold"),
        ).pack(pady=(20, 10))

        tk.Label(frame, text="キャラクターのイメージを自由に記述:").pack(
            anchor="w", padx=40,
        )
        self._text_description = tk.Text(frame, height=5, wrap="word")
        self._text_description.pack(fill="x", padx=40, pady=(0, 4))

        tk.Label(frame, text="ユーザー名（任意）:").pack(
            anchor="w", padx=40, pady=(10, 0),
        )
        self._entry_user_name = tk.Entry(frame)
        self._entry_user_name.pack(fill="x", padx=40)

        btn_row = tk.Frame(frame)
        btn_row.pack(pady=20)
        self._btn_back = tk.Button(
            btn_row, text="戻る", command=self._show_method_select,
        )
        self._btn_back.pack(side="left", padx=8)
        self._btn_submit = tk.Button(
            btn_row, text="生成する", command=self._on_generate_b,
        )
        self._btn_submit.pack(side="left", padx=8)

    def _on_generate_b(self) -> None:
        """方式 B の生成処理を開始する."""
        if self._is_processing:
            return
        description = self._text_description.get("1.0", "end").strip()
        if not description:
            return
        user_name = self._entry_user_name.get().strip()

        self._is_processing = True
        self._show_generating()

        def _bg() -> None:
            try:
                persona, style, _ = self._wizard_ctrl.reshape_free_description(
                    description, user_name=user_name,
                )
                self._root.after(0, self._on_generation_done, persona, style)
            except Exception:
                logger.error("方式 B 生成失敗", exc_info=True)
                self._root.after(0, self._on_generation_error, "キャラクター生成に失敗しました")

        threading.Thread(target=_bg, daemon=True).start()

    # ------------------------------------------------------------------
    # 方式 C 入力画面
    # ------------------------------------------------------------------

    def _show_input_c(self) -> None:
        """方式 C: 名前 + 一人称入力画面を表示する."""
        self._current_step = WizardStep.INPUT_C
        frame = self._make_frame()

        tk.Label(
            frame, text="白紙育成: 基本情報の設定",
            font=("", 14, "bold"),
        ).pack(pady=(20, 10))

        tk.Label(frame, text="キャラクター名:").pack(
            anchor="w", padx=40,
        )
        self._entry_name = tk.Entry(frame)
        self._entry_name.pack(fill="x", padx=40, pady=(0, 10))

        tk.Label(frame, text="一人称:").pack(anchor="w", padx=40)
        self._entry_first_person = tk.Entry(frame)
        self._entry_first_person.pack(fill="x", padx=40, pady=(0, 10))

        tk.Label(frame, text="ユーザー名（任意）:").pack(
            anchor="w", padx=40,
        )
        self._entry_user_name = tk.Entry(frame)
        self._entry_user_name.pack(fill="x", padx=40)

        btn_row = tk.Frame(frame)
        btn_row.pack(pady=20)
        self._btn_back = tk.Button(
            btn_row, text="戻る", command=self._show_method_select,
        )
        self._btn_back.pack(side="left", padx=8)
        self._btn_submit = tk.Button(
            btn_row, text="始める（プレビューへ）",
            command=self._on_submit_c,
        )
        self._btn_submit.pack(side="left", padx=8)

    def _on_submit_c(self) -> None:
        """方式 C のプレビュー遷移処理."""
        name = self._entry_name.get().strip()
        first_person = self._entry_first_person.get().strip()
        if not name or not first_person:
            return
        user_name = self._entry_user_name.get().strip()

        persona, style = self._wizard_ctrl.create_blank_persona(
            name, first_person, user_name=user_name,
        )
        self._on_generation_done(persona, style)

    # ------------------------------------------------------------------
    # 生成中画面 (GENERATING)
    # ------------------------------------------------------------------

    def _show_generating(self) -> None:
        """生成中表示を表示する."""
        self._current_step = WizardStep.GENERATING
        frame = self._make_frame()

        tk.Label(
            frame, text="キャラクターを生成中...",
            font=("", 14, "bold"),
        ).pack(pady=(80, 20))

        self._generating_label = tk.Label(frame, text="しばらくお待ちください。")
        self._generating_label.pack()

        self._dot_count = 0
        self._animate_dots()

    def _animate_dots(self) -> None:
        """ドットアニメーションを更新する."""
        if self._current_step != WizardStep.GENERATING:
            return
        self._dot_count = (self._dot_count + 1) % 4
        dots = "." * self._dot_count
        try:
            self._generating_label.configure(
                text=f"しばらくお待ちください{dots}",
            )
        except tk.TclError:
            return
        self._root.after(500, self._animate_dots)

    # ------------------------------------------------------------------
    # 生成完了 / エラー
    # ------------------------------------------------------------------

    def _on_generation_done(
        self, persona: PersonaCore, style: str,
    ) -> None:
        """生成完了後にプレビュー画面に遷移する."""
        self._is_processing = False
        self._current_persona = persona
        self._current_style = style
        self._preview_turns = []
        self._show_preview()

    def _on_generation_error(self, msg: str) -> None:
        """生成エラー時にメッセージを表示して方式選択に戻る (W-2 対応)."""
        self._is_processing = False
        messagebox.showerror("エラー", msg)
        self._show_method_select()

    # ------------------------------------------------------------------
    # プレビュー会話画面 (FR-8.9)
    # ------------------------------------------------------------------

    def _show_preview(self) -> None:
        """プレビュー会話画面を表示する."""
        self._current_step = WizardStep.PREVIEW
        self._root.geometry("480x400")
        frame = self._make_frame()

        if self._current_persona is None:
            raise RuntimeError("_current_persona が未設定の状態で呼ばれました")
        name = self._current_persona.c1_name

        self._preview_name_label = tk.Label(
            frame, text=f"{name}（プレビュー中）",
            font=("", 14, "bold"),
        )
        self._preview_name_label.pack(anchor="w", padx=10, pady=(10, 4))

        self._build_preview_text_area(frame)
        self._build_preview_input_area(frame)
        self._build_preview_buttons(frame)

    def _build_preview_text_area(self, parent: tk.Frame) -> None:
        """プレビュー画面の会話表示エリアを構築する."""
        text_frame = tk.Frame(parent)
        text_frame.pack(fill="both", expand=True, padx=10, pady=4)

        self._preview_text = tk.Text(
            text_frame, wrap="word", state="disabled", height=10,
        )
        scrollbar = tk.Scrollbar(
            text_frame, command=self._preview_text.yview,
        )
        self._preview_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._preview_text.pack(side="left", fill="both", expand=True)

    def _build_preview_input_area(self, parent: tk.Frame) -> None:
        """プレビュー画面の入力エリアを構築する."""
        input_frame = tk.Frame(parent)
        input_frame.pack(fill="x", padx=10, pady=4)

        self._preview_entry = tk.Entry(input_frame)
        self._preview_entry.pack(side="left", fill="x", expand=True)
        self._preview_entry.bind(
            "<Return>", lambda _: self._on_preview_send(),
        )

        self._preview_send_btn = tk.Button(
            input_frame, text="送信", command=self._on_preview_send,
        )
        self._preview_send_btn.pack(side="right", padx=(4, 0))

    def _build_preview_buttons(self, parent: tk.Frame) -> None:
        """プレビュー画面のボタンエリアを構築する."""
        btn_frame = tk.Frame(parent)
        btn_frame.pack(fill="x", padx=10, pady=(4, 10))

        self._btn_retry = tk.Button(
            btn_frame, text="やり直す", command=self._show_method_select,
        )
        self._btn_retry.pack(side="left")

        self._btn_confirm = tk.Button(
            btn_frame, text="確定する", command=self._on_confirm,
        )
        self._btn_confirm.pack(side="right")

    def _on_preview_send(self) -> None:
        """プレビュー会話の送信をバックグラウンドスレッドで実行する."""
        if self._is_processing:
            return
        user_input = self._preview_entry.get().strip()
        if not user_input:
            return

        self._is_processing = True
        self._preview_send_btn.configure(state="disabled")
        self._preview_entry.delete(0, "end")

        self._append_preview_text(f"あなた: {user_input}\n")
        self._preview_turns.append({"role": "user", "content": user_input})

        def _bg() -> None:
            try:
                if self._current_persona is None:
                    raise RuntimeError("_current_persona が未設定")
                response = self._wizard_ctrl.preview_conversation_turn(
                    self._current_persona,
                    self._current_style,
                    self._preview_turns[:-1],
                    user_input,
                )
                self._root.after(0, self._on_preview_response, response)
            except Exception:
                logger.error("プレビュー会話失敗", exc_info=True)
                self._root.after(
                    0, self._append_preview_text,
                    "(エラー: 応答を取得できませんでした)\n\n",
                )
            finally:
                self._root.after(0, self._unlock_preview_send)

        threading.Thread(target=_bg, daemon=True).start()

    def _unlock_preview_send(self) -> None:
        """プレビュー送信の処理中ロックを解除する."""
        self._is_processing = False
        with contextlib.suppress(tk.TclError):
            self._preview_send_btn.configure(state="normal")

    def _send_preview_sync(self) -> None:
        """テスト用: プレビュー会話を同期的に実行する (Protocol 外メソッド)."""
        user_input = self._preview_entry.get().strip()
        if not user_input:
            return
        self._preview_entry.delete(0, "end")

        self._append_preview_text(f"あなた: {user_input}\n")
        self._preview_turns.append({"role": "user", "content": user_input})

        if self._current_persona is None:
            raise RuntimeError("_current_persona が未設定")
        response = self._wizard_ctrl.preview_conversation_turn(
            self._current_persona,
            self._current_style,
            self._preview_turns[:-1],
            user_input,
        )
        self._on_preview_response(response)

    def _on_preview_response(self, response: str) -> None:
        """プレビュー会話の応答を表示する."""
        if self._current_persona is None:
            raise RuntimeError("_current_persona が未設定")
        name = self._current_persona.c1_name
        self._append_preview_text(f"{name}: {response}\n\n")
        self._preview_turns.append({"role": "assistant", "content": response})

    def _append_preview_text(self, text: str) -> None:
        """プレビュー会話テキストを追加する."""
        self._preview_text.configure(state="normal")
        self._preview_text.insert("end", text)
        self._preview_text.configure(state="disabled")
        self._preview_text.see("end")

    # ------------------------------------------------------------------
    # 凍結確認 (FR-8.10)
    # ------------------------------------------------------------------

    def _on_confirm(self) -> None:
        """確定ボタン押下 — 凍結確認ダイアログを表示する."""
        self._current_step = WizardStep.FREEZE_CONFIRM

        result = messagebox.askyesno(
            title="凍結確認",
            message=(
                "このキャラクターで始めますか？\n\n"
                "※ 凍結後、人格の変更は手動（ファイル直接編集）のみとなります。"
            ),
        )

        if result:
            self._on_freeze_confirmed()
        else:
            self._show_method_select()

    def _on_freeze_confirmed(self) -> None:
        """凍結を実行し、完了後に root.quit() でメインループを終了する."""
        if self._current_persona is None:
            raise RuntimeError("_current_persona が未設定")

        try:
            self._wizard_ctrl.freeze_persona(
                self._persona_system,
                self._current_persona,
                self._current_style,
                self._data_dir,
            )
            _set_persona_frozen(self._config_path)
        except ValueError:
            logger.error(
                "config.toml に persona_frozen 設定行が見つかりません",
                exc_info=True,
            )
            messagebox.showerror("エラー", "設定ファイルの形式が不正です。やり直してください。")
            self._show_method_select()
            return
        except Exception:
            logger.error("凍結処理に失敗しました", exc_info=True)
            messagebox.showerror("エラー", "凍結処理に失敗しました。やり直してください。")
            self._show_method_select()
            return

        self._current_step = WizardStep.DONE
        logger.info("ウィザード完了: %s", self._current_persona.c1_name)
        self._root.quit()
