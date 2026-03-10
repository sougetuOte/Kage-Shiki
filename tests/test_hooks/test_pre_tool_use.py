"""pre-tool-use.py のテスト."""

import json
from io import StringIO
from unittest.mock import patch

import pytest
from tests.test_hooks.conftest import load_hook_module


@pytest.fixture
def mod(hook_project_root):
    """pre-tool-use モジュールをロードし、PROJECT_ROOT を差し替える。"""
    m = load_hook_module("pre-tool-use.py")
    m.PROJECT_ROOT = hook_project_root
    # hook_utils の PROJECT_ROOT も差し替え
    m.hook_utils.PROJECT_ROOT = hook_project_root
    return m


@pytest.fixture
def setup_phase(hook_project_root):
    """current-phase.md にフェーズを設定するヘルパー。"""

    def _set(phase: str):
        phase_file = hook_project_root / ".claude" / "current-phase.md"
        phase_file.write_text(
            f"# Current Phase\n\n**{phase}**\n", encoding="utf-8"
        )

    return _set


class TestClassifyPermission:
    """classify_permission 関数のテスト。"""

    def test_read_tool_is_pg(self, mod):
        level, reason = mod.classify_permission("Read", "", "", "BUILDING")
        assert level == "PG"

    def test_glob_tool_is_pg(self, mod):
        level, reason = mod.classify_permission("Glob", "", "", "BUILDING")
        assert level == "PG"

    def test_grep_tool_is_pg(self, mod):
        level, reason = mod.classify_permission("Grep", "", "", "BUILDING")
        assert level == "PG"

    def test_edit_specs_is_pm(self, mod):
        level, reason = mod.classify_permission(
            "Edit", "docs/specs/config.md", "", "BUILDING"
        )
        assert level == "PM"

    def test_edit_adr_is_pm(self, mod):
        level, reason = mod.classify_permission(
            "Edit", "docs/adr/ADR-0001.md", "", "BUILDING"
        )
        assert level == "PM"

    def test_edit_internal_is_pm(self, mod):
        level, reason = mod.classify_permission(
            "Edit", "docs/internal/00_PROJECT_STRUCTURE.md", "", "BUILDING"
        )
        assert level == "PM"

    def test_write_rules_is_pm(self, mod):
        level, reason = mod.classify_permission(
            "Write", ".claude/rules/new-rule.md", "", "BUILDING"
        )
        assert level == "PM"

    def test_write_rules_subdir_is_pm(self, mod):
        level, reason = mod.classify_permission(
            "Write",
            ".claude/rules/auto-generated/draft-001.md",
            "",
            "BUILDING",
        )
        assert level == "PM"

    def test_edit_settings_is_pm(self, mod):
        level, reason = mod.classify_permission(
            "Edit", ".claude/settings.json", "", "BUILDING"
        )
        assert level == "PM"

    def test_edit_pyproject_is_pm(self, mod):
        level, reason = mod.classify_permission(
            "Edit", "pyproject.toml", "", "BUILDING"
        )
        assert level == "PM"

    def test_edit_src_is_se(self, mod):
        level, reason = mod.classify_permission(
            "Edit", "src/kage_shiki/core/config.py", "", "BUILDING"
        )
        assert level == "SE"

    def test_edit_tests_is_se(self, mod):
        level, reason = mod.classify_permission(
            "Edit", "tests/test_core.py", "", "BUILDING"
        )
        assert level == "SE"

    def test_edit_docs_general_is_se(self, mod):
        level, reason = mod.classify_permission(
            "Edit", "docs/memos/note.md", "", "BUILDING"
        )
        assert level == "SE"

    def test_unknown_path_is_se(self, mod):
        level, reason = mod.classify_permission(
            "Edit", "random/file.txt", "", "BUILDING"
        )
        assert level == "SE"


class TestBashCommand:
    """Bash ツール内のコマンドからパスを抽出するテスト。"""

    def test_bash_without_file_path_is_se(self, mod):
        level, reason = mod.classify_permission(
            "Bash", "", "cat docs/specs/config.md", "BUILDING"
        )
        # Bash はファイルパスなし → SE 級（安全側に倒す）
        assert level == "SE"


class TestAuditingPhase:
    """AUDITING フェーズの特別処理テスト。"""

    def test_auditing_pg_tool_allowed(self, mod):
        level, reason = mod.classify_permission(
            "Read", "docs/specs/config.md", "", "AUDITING"
        )
        assert level == "PG"

    def test_auditing_pm_path_still_pm(self, mod):
        """AUDITING でも PM パスへの Edit は PM 級。"""
        level, reason = mod.classify_permission(
            "Edit", "docs/specs/config.md", "", "AUDITING"
        )
        assert level == "PM"


class TestMainFunction:
    """main() 関数の統合テスト。"""

    def test_pg_tool_exits_silently(self, mod, mock_stdin, capture_stdout):
        data = {"tool_name": "Read", "tool_input": {"file_path": "/tmp/test.py"}}
        with mock_stdin(data):
            patcher, buf = capture_stdout()
            with patcher:
                mod.main()
        # PG 級は何も出力しない
        assert buf.getvalue() == ""

    def test_pg_tool_writes_permission_log(
        self, mod, mock_stdin, capture_stdout, hook_project_root,
    ):
        data = {"tool_name": "Read", "tool_input": {"file_path": "/tmp/test.py"}}
        with mock_stdin(data):
            patcher, buf = capture_stdout()
            with patcher:
                mod.main()
        log_file = hook_project_root / ".claude" / "logs" / "permission.log"
        assert log_file.exists()
        log_content = log_file.read_text(encoding="utf-8")
        assert "[PG]" in log_content

    def test_pm_tool_outputs_json(self, mod, mock_stdin, capture_stdout, setup_phase):
        setup_phase("BUILDING")
        abs_path = str(mod.PROJECT_ROOT / "docs" / "specs" / "test.md")
        data = {"tool_name": "Edit", "tool_input": {"file_path": abs_path}}
        with mock_stdin(data):
            patcher, buf = capture_stdout()
            with patcher:
                mod.main()
        output = json.loads(buf.getvalue())
        assert output.get("decision") == "block"
        assert "PM" in output.get("reason", "")

    def test_invalid_json_exits_safely(self, mod, capture_stdout):
        with patch("sys.stdin", StringIO("not json")):
            patcher, buf = capture_stdout()
            with patcher:
                mod.main()
        assert buf.getvalue() == ""

    def test_empty_input_exits_safely(self, mod, capture_stdout):
        with patch("sys.stdin", StringIO("")):
            patcher, buf = capture_stdout()
            with patcher:
                mod.main()
        assert buf.getvalue() == ""
