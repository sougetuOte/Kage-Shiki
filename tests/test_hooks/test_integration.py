"""hooks 統合テスト."""

import json
import subprocess
import sys

import pytest
from tests.test_hooks.conftest import HOOKS_DIR, load_hook_module

SETTINGS_FILE = HOOKS_DIR.parent / "settings.json"
SETTINGS_LOCAL_FILE = HOOKS_DIR.parent / "settings.local.json"


class TestSettingsJson:
    """settings.json の構造検証。"""

    @pytest.fixture(autouse=True)
    def load_settings(self):
        self.settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))

    def test_has_hooks_section(self):
        assert "hooks" in self.settings

    def test_has_four_hook_events(self):
        hooks = self.settings["hooks"]
        expected = {"PreToolUse", "PostToolUse", "Stop", "PreCompact"}
        assert set(hooks.keys()) == expected

    def test_hook_commands_use_python(self):
        for _event, entries in self.settings["hooks"].items():
            for entry in entries:
                for hook in entry["hooks"]:
                    assert hook["type"] == "command"
                    assert "python" in hook["command"]
                    assert ".py" in hook["command"]

    def test_post_tool_use_has_matcher(self):
        post = self.settings["hooks"]["PostToolUse"]
        assert post[0].get("matcher") == "Edit|Write|Bash"

    def test_permissions_has_ruff_allow(self):
        allow = self.settings["permissions"]["allow"]
        assert "Bash(ruff check --fix *)" in allow
        assert "Bash(ruff format *)" in allow

    def test_python_not_in_settings_allow(self):
        """python コマンドは settings.local.json に移動済み。"""
        allow = self.settings["permissions"]["allow"]
        assert "Bash(python *)" not in allow
        assert "Bash(python3 *)" not in allow


class TestSettingsLocalJson:
    """settings.local.json が変更されていないことを確認。"""

    def test_exists(self):
        assert SETTINGS_LOCAL_FILE.exists()

    def test_has_notify_sound(self):
        settings = json.loads(SETTINGS_LOCAL_FILE.read_text(encoding="utf-8"))
        stop_hooks = settings.get("hooks", {}).get("Stop", [])
        assert len(stop_hooks) > 0
        commands = [
            h["command"]
            for entry in stop_hooks
            for h in entry.get("hooks", [])
        ]
        assert any("notify-sound.py" in cmd for cmd in commands)

    def test_has_python_permissions(self):
        settings = json.loads(SETTINGS_LOCAL_FILE.read_text(encoding="utf-8"))
        allow = settings.get("permissions", {}).get("allow", [])
        assert "Bash(python *)" in allow


class TestHookScriptsDryRun:
    """全 hook スクリプトが python で起動可能であることを確認。"""

    HOOK_SCRIPTS = [
        "hook_utils.py",
        "pre-tool-use.py",
        "post-tool-use.py",
        "lam-stop-hook.py",
        "pre-compact.py",
        "notify-sound.py",
    ]

    @pytest.mark.parametrize("script", HOOK_SCRIPTS)
    def test_script_exists(self, script):
        assert (HOOKS_DIR / script).exists()

    @pytest.mark.parametrize(
        "script",
        [
            "hook_utils.py",
            "pre-tool-use.py",
            "post-tool-use.py",
            "pre-compact.py",
            "lam-stop-hook.py",
        ],
    )
    def test_script_importable(self, script):
        """hook スクリプトがモジュールとしてロード可能。"""
        mod = load_hook_module(script)
        assert mod is not None

    @pytest.mark.parametrize(
        "script",
        ["pre-tool-use.py", "post-tool-use.py", "lam-stop-hook.py", "pre-compact.py"],
    )
    def test_script_syntax_valid(self, script):
        """Python 構文エラーがないことを確認。"""
        result = subprocess.run(
            [
                sys.executable, "-c",
                f"import py_compile; py_compile.compile(r'{HOOKS_DIR / script}', doraise=True)",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"{script}: {result.stderr}"


class TestCoexistence:
    """notify-sound.py との共存確認。"""

    def test_notify_sound_not_modified(self):
        """notify-sound.py が LAM hooks 導入で変更されていないこと。"""
        content = (HOOKS_DIR / "notify-sound.py").read_text(encoding="utf-8")
        assert "winsound" in content
        assert "SOUNDS" in content
        assert "tada.wav" in content
