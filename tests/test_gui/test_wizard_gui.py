"""WizardGUI テスト (T-31, FR-8.8/8.9/8.10).

FR-8.8: 方式選択画面（3方式ボタン + 状態遷移）
FR-8.9: プレビュー会話 UI（送信・やり直し・確定）
FR-8.10: 凍結確認ダイアログ（persona_core.md 生成 + config.toml 更新）

テスト方針:
- root.update_idletasks() を使用（ウィンドウ表示を伴わない）
- WizardController はモックを使用
- messagebox はモックで差し替え
"""

import contextlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from kage_shiki.core.config import AppConfig, GuiConfig, WizardConfig
from kage_shiki.gui.wizard_gui import WizardGUI, WizardStep, _set_persona_frozen
from kage_shiki.persona.persona_system import PersonaCore, PersonaSystem

# ---------------------------------------------------------------------------
# テスト用ヘルパー
# ---------------------------------------------------------------------------


def _make_persona_core(name: str = "テスト太郎") -> PersonaCore:
    """テスト用 PersonaCore を生成する."""
    return PersonaCore(
        c1_name=name,
        c2_first_person="ぼく",
        c3_second_person="あなた",
        c4_personality_core=f"{name}です。よろしくね。",
        c5_personality_axes="",
        c6_speech_pattern="",
        c7_catchphrase="",
        c8_age_impression="",
        c9_values="",
        c10_forbidden="",
        c11_self_knowledge="",
    )


def _make_mock_wizard_ctrl() -> MagicMock:
    """モック WizardController を生成する."""
    ctrl = MagicMock()
    ctrl.expand_associations.return_value = ["元気", "猫耳", "ツンデレ"]
    ctrl.generate_candidates.return_value = [
        _make_persona_core("候補A"),
        _make_persona_core("候補B"),
        _make_persona_core("候補C"),
    ]
    ctrl.generate_style_samples.return_value = "## S1: 日常会話\n1. テスト"
    ctrl.reshape_free_description.return_value = (
        _make_persona_core("自由記述キャラ"),
        "## S1: 日常会話\n1. テスト",
        ["c5_personality_axes"],
    )
    ctrl.create_blank_persona.return_value = (
        _make_persona_core("白紙キャラ"),
        "## S1: 日常会話\n（まだ定義されていません）",
    )
    ctrl.preview_conversation_turn.return_value = "こんにちは！テスト太郎だよ！"
    ctrl.freeze_persona.return_value = None
    return ctrl


def _make_config() -> AppConfig:
    """テスト用 AppConfig を生成する."""
    return AppConfig(
        gui=GuiConfig(
            window_width=480,
            window_height=360,
            opacity=0.95,
            topmost=False,
            font_size=14,
            font_family="",
        ),
        wizard=WizardConfig(),
    )


def _go_to_preview(tk_root, gui):
    """方式 C 経由でプレビュー画面に到達するヘルパー (I-2 統合)."""
    gui.show()
    tk_root.update_idletasks()

    gui._btn_method_c.invoke()
    tk_root.update_idletasks()

    gui._entry_name.delete(0, "end")
    gui._entry_name.insert(0, "テストちゃん")
    gui._entry_first_person.delete(0, "end")
    gui._entry_first_person.insert(0, "わたし")
    tk_root.update_idletasks()

    gui._btn_submit.invoke()
    tk_root.update_idletasks()


# ---------------------------------------------------------------------------
# テスト後クリーンアップ (WARN-005 対応)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _cleanup_wizard_frame(tk_root):
    """各テスト終了後に WizardGUI の Frame を破棄する."""
    yield
    for child in tk_root.winfo_children():
        with contextlib.suppress(Exception):
            child.destroy()


# ---------------------------------------------------------------------------
# FR-8.8: 方式選択画面テスト
# ---------------------------------------------------------------------------


class TestWizardStepMethodSelect:
    """FR-8.8: 方式選択画面（初期状態 + 遷移）."""

    def test_initial_step_is_method_select(self, tk_root):
        """WizardGUI 生成後に current_step == METHOD_SELECT."""
        ctrl = _make_mock_wizard_ctrl()
        gui = WizardGUI(
            tk_root, ctrl, PersonaSystem(), Path("/tmp/test"), _make_config(),
        )
        gui.show()
        tk_root.update_idletasks()

        assert gui.current_step == WizardStep.METHOD_SELECT

    def test_method_a_button_transitions_to_input_a(self, tk_root):
        """AI おまかせボタンで INPUT_A に遷移."""
        ctrl = _make_mock_wizard_ctrl()
        gui = WizardGUI(
            tk_root, ctrl, PersonaSystem(), Path("/tmp/test"), _make_config(),
        )
        gui.show()
        tk_root.update_idletasks()

        gui._btn_method_a.invoke()
        tk_root.update_idletasks()

        assert gui.current_step == WizardStep.INPUT_A

    def test_method_b_button_transitions_to_input_b(self, tk_root):
        """既存イメージボタンで INPUT_B に遷移."""
        ctrl = _make_mock_wizard_ctrl()
        gui = WizardGUI(
            tk_root, ctrl, PersonaSystem(), Path("/tmp/test"), _make_config(),
        )
        gui.show()
        tk_root.update_idletasks()

        gui._btn_method_b.invoke()
        tk_root.update_idletasks()

        assert gui.current_step == WizardStep.INPUT_B

    def test_method_c_button_transitions_to_input_c(self, tk_root):
        """白紙育成ボタンで INPUT_C に遷移."""
        ctrl = _make_mock_wizard_ctrl()
        gui = WizardGUI(
            tk_root, ctrl, PersonaSystem(), Path("/tmp/test"), _make_config(),
        )
        gui.show()
        tk_root.update_idletasks()

        gui._btn_method_c.invoke()
        tk_root.update_idletasks()

        assert gui.current_step == WizardStep.INPUT_C


# ---------------------------------------------------------------------------
# FR-8.8: 各入力画面からの遷移テスト
# ---------------------------------------------------------------------------


class TestWizardInputScreens:
    """各入力画面から生成中 or プレビューへの遷移."""

    def test_input_a_back_returns_to_method_select(self, tk_root):
        """方式 A 入力画面の「戻る」で METHOD_SELECT に戻る."""
        ctrl = _make_mock_wizard_ctrl()
        gui = WizardGUI(
            tk_root, ctrl, PersonaSystem(), Path("/tmp/test"), _make_config(),
        )
        gui.show()
        tk_root.update_idletasks()

        gui._btn_method_a.invoke()
        tk_root.update_idletasks()
        assert gui.current_step == WizardStep.INPUT_A

        gui._btn_back.invoke()
        tk_root.update_idletasks()
        assert gui.current_step == WizardStep.METHOD_SELECT

    def test_input_b_back_returns_to_method_select(self, tk_root):
        """方式 B 入力画面の「戻る」で METHOD_SELECT に戻る."""
        ctrl = _make_mock_wizard_ctrl()
        gui = WizardGUI(
            tk_root, ctrl, PersonaSystem(), Path("/tmp/test"), _make_config(),
        )
        gui.show()
        tk_root.update_idletasks()

        gui._btn_method_b.invoke()
        tk_root.update_idletasks()

        gui._btn_back.invoke()
        tk_root.update_idletasks()
        assert gui.current_step == WizardStep.METHOD_SELECT

    def test_input_c_back_returns_to_method_select(self, tk_root):
        """方式 C 入力画面の「戻る」で METHOD_SELECT に戻る."""
        ctrl = _make_mock_wizard_ctrl()
        gui = WizardGUI(
            tk_root, ctrl, PersonaSystem(), Path("/tmp/test"), _make_config(),
        )
        gui.show()
        tk_root.update_idletasks()

        gui._btn_method_c.invoke()
        tk_root.update_idletasks()

        gui._btn_back.invoke()
        tk_root.update_idletasks()
        assert gui.current_step == WizardStep.METHOD_SELECT

    def test_method_c_submit_goes_to_preview(self, tk_root):
        """方式 C は生成なしで直接 PREVIEW に遷移."""
        ctrl = _make_mock_wizard_ctrl()
        gui = WizardGUI(
            tk_root, ctrl, PersonaSystem(), Path("/tmp/test"), _make_config(),
        )
        gui.show()
        tk_root.update_idletasks()

        gui._btn_method_c.invoke()
        tk_root.update_idletasks()

        gui._entry_name.delete(0, "end")
        gui._entry_name.insert(0, "テストちゃん")
        gui._entry_first_person.delete(0, "end")
        gui._entry_first_person.insert(0, "わたし")
        tk_root.update_idletasks()

        gui._btn_submit.invoke()
        tk_root.update_idletasks()

        assert gui.current_step == WizardStep.PREVIEW
        ctrl.create_blank_persona.assert_called_once()


# ---------------------------------------------------------------------------
# FR-8.9: プレビュー会話 UI テスト
# ---------------------------------------------------------------------------


class TestWizardPreview:
    """FR-8.9: プレビュー会話 UI."""

    def test_preview_shows_persona_name(self, tk_root):
        """プレビュー画面にキャラクター名が表示される."""
        ctrl = _make_mock_wizard_ctrl()
        gui = WizardGUI(
            tk_root, ctrl, PersonaSystem(), Path("/tmp/test"), _make_config(),
        )
        _go_to_preview(tk_root, gui)

        assert gui.current_step == WizardStep.PREVIEW
        assert "白紙キャラ" in gui._preview_name_label.cget("text")

    def test_preview_retry_returns_to_method_select(self, tk_root):
        """「やり直す」で METHOD_SELECT に戻る."""
        ctrl = _make_mock_wizard_ctrl()
        gui = WizardGUI(
            tk_root, ctrl, PersonaSystem(), Path("/tmp/test"), _make_config(),
        )
        _go_to_preview(tk_root, gui)

        gui._btn_retry.invoke()
        tk_root.update_idletasks()

        assert gui.current_step == WizardStep.METHOD_SELECT

    def test_preview_send_displays_response(self, tk_root):
        """送信後にセリフが表示エリアに反映される."""
        ctrl = _make_mock_wizard_ctrl()
        gui = WizardGUI(
            tk_root, ctrl, PersonaSystem(), Path("/tmp/test"), _make_config(),
        )
        _go_to_preview(tk_root, gui)

        gui._preview_entry.delete(0, "end")
        gui._preview_entry.insert(0, "こんにちは")
        tk_root.update_idletasks()

        gui._send_preview_sync()
        tk_root.update_idletasks()

        text_content = gui._preview_text.get("1.0", "end").strip()
        assert "こんにちは" in text_content
        assert ctrl.preview_conversation_turn.return_value in text_content

    def test_preview_confirm_transitions_to_freeze(self, tk_root):
        """「確定する」で FREEZE_CONFIRM を経由する (C-3 対応)."""
        ctrl = _make_mock_wizard_ctrl()
        gui = WizardGUI(
            tk_root, ctrl, PersonaSystem(), Path("/tmp/test"), _make_config(),
        )
        _go_to_preview(tk_root, gui)

        steps_seen: list[WizardStep] = []

        def _capture_step(*args, **kwargs):
            steps_seen.append(gui.current_step)
            return False  # キャンセル

        with patch("kage_shiki.gui.wizard_gui.messagebox") as mock_msgbox:
            mock_msgbox.askyesno.side_effect = _capture_step
            gui._btn_confirm.invoke()
            tk_root.update_idletasks()

            mock_msgbox.askyesno.assert_called_once()
            assert WizardStep.FREEZE_CONFIRM in steps_seen
            assert gui.current_step == WizardStep.METHOD_SELECT


# ---------------------------------------------------------------------------
# FR-8.10: 凍結確認テスト
# ---------------------------------------------------------------------------


class TestWizardFreeze:
    """FR-8.10: 凍結確認ダイアログ + ペルソナ生成."""

    def test_freeze_creates_persona_files(self, tk_root, tmp_path):
        """凍結確認「はい」で persona_core.md + style_samples.md が生成."""
        ctrl = _make_mock_wizard_ctrl()
        persona_system = PersonaSystem()
        config = _make_config()

        config_path = tmp_path / "config.toml"
        config_path.write_text(
            "[general]\npersona_frozen = false\n", encoding="utf-8",
        )

        gui = WizardGUI(
            tk_root, ctrl, persona_system, tmp_path, config,
            config_path=config_path,
        )
        _go_to_preview(tk_root, gui)

        with patch("kage_shiki.gui.wizard_gui.messagebox") as mock_msgbox:
            mock_msgbox.askyesno.return_value = True
            with patch.object(tk_root, "quit"):
                gui._btn_confirm.invoke()
                tk_root.update_idletasks()

        ctrl.freeze_persona.assert_called_once()

        updated = config_path.read_text(encoding="utf-8")
        assert "persona_frozen = true" in updated

    def test_freeze_cancel_returns_to_method_select(self, tk_root):
        """凍結確認「キャンセル」で METHOD_SELECT に戻る."""
        ctrl = _make_mock_wizard_ctrl()
        gui = WizardGUI(
            tk_root, ctrl, PersonaSystem(), Path("/tmp/test"), _make_config(),
        )
        _go_to_preview(tk_root, gui)

        with patch("kage_shiki.gui.wizard_gui.messagebox") as mock_msgbox:
            mock_msgbox.askyesno.return_value = False
            gui._btn_confirm.invoke()
            tk_root.update_idletasks()

        assert gui.current_step == WizardStep.METHOD_SELECT

    def test_freeze_done_calls_root_quit(self, tk_root, tmp_path):
        """凍結完了後に root.quit() が呼ばれる."""
        ctrl = _make_mock_wizard_ctrl()
        config_path = tmp_path / "config.toml"
        config_path.write_text(
            "[general]\npersona_frozen = false\n", encoding="utf-8",
        )

        gui = WizardGUI(
            tk_root, ctrl, PersonaSystem(), tmp_path, _make_config(),
            config_path=config_path,
        )
        _go_to_preview(tk_root, gui)

        with patch("kage_shiki.gui.wizard_gui.messagebox") as mock_msgbox:
            mock_msgbox.askyesno.return_value = True
            with patch.object(tk_root, "quit") as mock_quit:
                gui._btn_confirm.invoke()
                tk_root.update_idletasks()

                mock_quit.assert_called_once()

    def test_freeze_done_step_is_done(self, tk_root, tmp_path):
        """凍結完了後に current_step == DONE."""
        ctrl = _make_mock_wizard_ctrl()
        config_path = tmp_path / "config.toml"
        config_path.write_text(
            "[general]\npersona_frozen = false\n", encoding="utf-8",
        )

        gui = WizardGUI(
            tk_root, ctrl, PersonaSystem(), tmp_path, _make_config(),
            config_path=config_path,
        )
        _go_to_preview(tk_root, gui)

        with patch("kage_shiki.gui.wizard_gui.messagebox") as mock_msgbox:
            mock_msgbox.askyesno.return_value = True
            with patch.object(tk_root, "quit"):
                gui._btn_confirm.invoke()
                tk_root.update_idletasks()

        assert gui.current_step == WizardStep.DONE

    def test_freeze_error_returns_to_method_select(self, tk_root, tmp_path):
        """凍結処理失敗時に METHOD_SELECT に戻る (WARN-001 対応)."""
        ctrl = _make_mock_wizard_ctrl()
        ctrl.freeze_persona.side_effect = RuntimeError("freeze failed")

        config_path = tmp_path / "config.toml"
        config_path.write_text(
            "[general]\npersona_frozen = false\n", encoding="utf-8",
        )

        gui = WizardGUI(
            tk_root, ctrl, PersonaSystem(), tmp_path, _make_config(),
            config_path=config_path,
        )
        _go_to_preview(tk_root, gui)

        with patch("kage_shiki.gui.wizard_gui.messagebox") as mock_msgbox:
            mock_msgbox.askyesno.return_value = True
            gui._btn_confirm.invoke()
            tk_root.update_idletasks()

            mock_msgbox.showerror.assert_called_once()
        assert gui.current_step == WizardStep.METHOD_SELECT


# ---------------------------------------------------------------------------
# _set_persona_frozen テスト
# ---------------------------------------------------------------------------


class TestSetPersonaFrozen:
    """config.toml の persona_frozen 書き換え."""

    def test_false_to_true(self, tmp_path):
        """persona_frozen = false → true."""
        p = tmp_path / "config.toml"
        p.write_text(
            "[general]\ndata_dir = \"data\"\npersona_frozen = false\n",
            encoding="utf-8",
        )
        _set_persona_frozen(p)
        assert "persona_frozen = true" in p.read_text(encoding="utf-8")

    def test_already_true(self, tmp_path):
        """既に true の場合もエラーなし."""
        p = tmp_path / "config.toml"
        p.write_text(
            "[general]\npersona_frozen = true\n", encoding="utf-8",
        )
        _set_persona_frozen(p)
        assert "persona_frozen = true" in p.read_text(encoding="utf-8")

    def test_missing_field_raises(self, tmp_path):
        """persona_frozen がない場合 ValueError."""
        p = tmp_path / "config.toml"
        p.write_text("[general]\ndata_dir = \"data\"\n", encoding="utf-8")
        with pytest.raises(ValueError, match="persona_frozen"):
            _set_persona_frozen(p)

    def test_preserves_other_fields(self, tmp_path):
        """他のフィールドが変更されない."""
        original = (
            "[general]\ndata_dir = \"my_data\"\n"
            "persona_frozen = false\n\n"
            "[llm]\nmodel = \"claude-3-haiku\"\n"
        )
        p = tmp_path / "config.toml"
        p.write_text(original, encoding="utf-8")
        _set_persona_frozen(p)
        result = p.read_text(encoding="utf-8")
        assert 'data_dir = "my_data"' in result
        assert 'model = "claude-3-haiku"' in result
        assert "persona_frozen = true" in result


# ---------------------------------------------------------------------------
# WizardStep Enum テスト
# ---------------------------------------------------------------------------


class TestWizardStepEnum:
    """WizardStep Enum の値テスト."""

    def test_all_steps_defined(self):
        """全ステップが定義されている."""
        expected = {
            "METHOD_SELECT", "INPUT_A", "INPUT_B", "INPUT_C",
            "GENERATING", "PREVIEW", "FREEZE_CONFIRM", "DONE",
        }
        actual = {s.name for s in WizardStep}
        assert actual == expected


# ---------------------------------------------------------------------------
# 連打防止ガードテスト (CRIT-001 対応)
# ---------------------------------------------------------------------------


class TestProcessingGuard:
    """連打防止ガードのテスト."""

    def test_is_processing_blocks_preview_send(self, tk_root):
        """_is_processing が True のとき送信がブロックされる."""
        ctrl = _make_mock_wizard_ctrl()
        gui = WizardGUI(
            tk_root, ctrl, PersonaSystem(), Path("/tmp/test"), _make_config(),
        )
        _go_to_preview(tk_root, gui)

        gui._is_processing = True
        gui._preview_entry.delete(0, "end")
        gui._preview_entry.insert(0, "テスト")
        tk_root.update_idletasks()

        gui._on_preview_send()
        tk_root.update_idletasks()

        # 送信がブロックされ、preview_conversation_turn は呼ばれない
        ctrl.preview_conversation_turn.assert_not_called()
