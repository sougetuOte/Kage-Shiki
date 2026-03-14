"""pre-tool-use.py のテスト."""

import json
from io import StringIO
from unittest.mock import patch

import pytest
from tests.test_hooks.conftest import load_hook_module


@pytest.fixture
def mod(hook_project_root):
    """pre-tool-use モジュールをロードする。"""
    return load_hook_module("pre-tool-use.py")


@pytest.fixture
def setup_phase(hook_project_root):
    """current-phase.md にフェーズを設定するヘルパー。"""

    def _set(phase: str):
        phase_file = hook_project_root / ".claude" / "current-phase.md"
        phase_file.write_text(
            f"# Current Phase\n\n**{phase}**\n", encoding="utf-8"
        )

    return _set


class TestDetermineLevel:
    """_determine_level_and_reason 関数のテスト。"""

    def test_edit_specs_is_pm(self, mod, hook_project_root):
        level, reason = mod._determine_level_and_reason(
            "Edit", "docs/specs/config.md", "",
            hook_project_root,
            hook_project_root / ".claude" / "current-phase.md",
        )
        assert level == "PM"

    def test_edit_adr_is_pm(self, mod, hook_project_root):
        level, reason = mod._determine_level_and_reason(
            "Edit", "docs/adr/ADR-0001.md", "",
            hook_project_root,
            hook_project_root / ".claude" / "current-phase.md",
        )
        assert level == "PM"

    def test_edit_internal_is_pm(self, mod, hook_project_root):
        level, reason = mod._determine_level_and_reason(
            "Edit", "docs/internal/00_PROJECT_STRUCTURE.md", "",
            hook_project_root,
            hook_project_root / ".claude" / "current-phase.md",
        )
        assert level == "PM"

    def test_write_rules_is_pm(self, mod, hook_project_root):
        level, reason = mod._determine_level_and_reason(
            "Write", ".claude/rules/new-rule.md", "",
            hook_project_root,
            hook_project_root / ".claude" / "current-phase.md",
        )
        assert level == "PM"

    def test_write_rules_subdir_is_pm(self, mod, hook_project_root):
        level, reason = mod._determine_level_and_reason(
            "Write",
            ".claude/rules/auto-generated/draft-001.md",
            "",
            hook_project_root,
            hook_project_root / ".claude" / "current-phase.md",
        )
        assert level == "PM"

    def test_edit_settings_is_pm(self, mod, hook_project_root):
        level, reason = mod._determine_level_and_reason(
            "Edit", ".claude/settings.json", "",
            hook_project_root,
            hook_project_root / ".claude" / "current-phase.md",
        )
        assert level == "PM"

    def test_edit_pyproject_is_pm(self, mod, hook_project_root):
        level, reason = mod._determine_level_and_reason(
            "Edit", "pyproject.toml", "",
            hook_project_root,
            hook_project_root / ".claude" / "current-phase.md",
        )
        assert level == "PM"

    def test_edit_src_is_se(self, mod, hook_project_root):
        level, reason = mod._determine_level_and_reason(
            "Edit", "src/kage_shiki/core/config.py", "",
            hook_project_root,
            hook_project_root / ".claude" / "current-phase.md",
        )
        assert level == "SE"

    def test_edit_tests_is_se(self, mod, hook_project_root):
        level, reason = mod._determine_level_and_reason(
            "Edit", "tests/test_core.py", "",
            hook_project_root,
            hook_project_root / ".claude" / "current-phase.md",
        )
        assert level == "SE"

    def test_edit_docs_general_is_se(self, mod, hook_project_root):
        level, reason = mod._determine_level_and_reason(
            "Edit", "docs/memos/note.md", "",
            hook_project_root,
            hook_project_root / ".claude" / "current-phase.md",
        )
        assert level == "SE"

    def test_unknown_path_is_se(self, mod, hook_project_root):
        level, reason = mod._determine_level_and_reason(
            "Edit", "random/file.txt", "",
            hook_project_root,
            hook_project_root / ".claude" / "current-phase.md",
        )
        assert level == "SE"

    def test_out_of_root_is_pm(self, mod, hook_project_root):
        """プロジェクト外の絶対パスは __out_of_root__ マーカーで PM 級になる。"""
        # Windows で確実にプロジェクト外の絶対パスを使う
        abs_path = str(hook_project_root.parent / "other_project" / "secret.py")
        level, reason = mod._determine_level_and_reason(
            "Edit", abs_path, "",
            hook_project_root,
            hook_project_root / ".claude" / "current-phase.md",
        )
        assert level == "PM"

    def test_edit_settings_local_is_pm(self, mod, hook_project_root):
        level, reason = mod._determine_level_and_reason(
            "Edit", ".claude/settings.local.json", "",
            hook_project_root,
            hook_project_root / ".claude" / "current-phase.md",
        )
        assert level == "PM"

    def test_auditing_pg_command(self, mod, hook_project_root, setup_phase):
        setup_phase("AUDITING")
        level, reason = mod._determine_level_and_reason(
            "Bash", "", "ruff format .",
            hook_project_root,
            hook_project_root / ".claude" / "current-phase.md",
        )
        assert level == "PG"

    def test_building_same_command_is_se(self, mod, hook_project_root, setup_phase):
        setup_phase("BUILDING")
        level, reason = mod._determine_level_and_reason(
            "Bash", "", "ruff format .",
            hook_project_root,
            hook_project_root / ".claude" / "current-phase.md",
        )
        assert level == "SE"


class TestBashCommand:
    """Bash ツール内のコマンドからパスを抽出するテスト。"""

    def test_bash_without_file_path_is_se(self, mod, hook_project_root):
        level, reason = mod._determine_level_and_reason(
            "Bash", "", "cat docs/specs/config.md",
            hook_project_root,
            hook_project_root / ".claude" / "current-phase.md",
        )
        assert level == "SE"


class TestMainFunction:
    """main() 関数の統合テスト。"""

    def test_pg_tool_exits_silently(self, mod, mock_stdin, capture_stdout):
        data = {"tool_name": "Read", "tool_input": {"file_path": "/tmp/test.py"}}
        with mock_stdin(data):
            patcher, buf = capture_stdout()
            with patcher, pytest.raises(SystemExit):
                mod.main()
        assert buf.getvalue() == ""

    def test_pm_tool_outputs_hookspecificoutput(
        self, mod, mock_stdin, capture_stdout, hook_project_root, setup_phase,
    ):
        setup_phase("BUILDING")
        abs_path = str(hook_project_root / "docs" / "specs" / "test.md")
        data = {"tool_name": "Edit", "tool_input": {"file_path": abs_path}}
        with mock_stdin(data):
            patcher, buf = capture_stdout()
            with patcher, pytest.raises(SystemExit):
                mod.main()
        output = json.loads(buf.getvalue())
        assert "hookSpecificOutput" in output
        hso = output["hookSpecificOutput"]
        assert hso["permissionDecision"] == "ask"
        assert "PM" in hso["permissionDecisionReason"]

    def test_invalid_json_exits_safely(self, mod, capture_stdout):
        with patch("sys.stdin", StringIO("not json")):
            patcher, buf = capture_stdout()
            with patcher, pytest.raises(SystemExit):
                mod.main()
        assert buf.getvalue() == ""

    def test_empty_input_exits_safely(self, mod, capture_stdout):
        with patch("sys.stdin", StringIO("")):
            patcher, buf = capture_stdout()
            with patcher, pytest.raises(SystemExit):
                mod.main()
        assert buf.getvalue() == ""
