"""post-tool-use.py のテスト."""

import json
from io import StringIO
from unittest.mock import patch

import pytest
from tests.test_hooks.conftest import load_hook_module


@pytest.fixture
def mod(hook_project_root):
    """post-tool-use モジュールをロードし、PROJECT_ROOT を差し替える。"""
    m = load_hook_module("post-tool-use.py")
    m.PROJECT_ROOT = hook_project_root
    m.hook_utils.PROJECT_ROOT = hook_project_root
    return m


class TestTddPatternRecord:
    """責務1: TDD パターン記録。"""

    def test_pytest_fail_records_entry(self, mod, hook_project_root):
        mod.record_tdd_pattern("Bash", "pytest tests/", 1, "FAILED test_foo")
        log = (hook_project_root / ".claude" / "tdd-patterns.log").read_text(
            encoding="utf-8"
        )
        assert "FAIL" in log
        assert "pytest" in log

    def test_pytest_pass_after_fail_records(self, mod, hook_project_root):
        # 前回失敗を記録
        last_result = hook_project_root / ".claude" / "last-test-result"
        last_result.write_text("FAIL", encoding="utf-8")

        mod.record_tdd_pattern("Bash", "pytest tests/", 0, "5 passed")
        log = (hook_project_root / ".claude" / "tdd-patterns.log").read_text(
            encoding="utf-8"
        )
        assert "PASS (previously failed)" in log

    def test_pytest_pass_no_previous_fail_skips(self, mod, hook_project_root):
        mod.record_tdd_pattern("Bash", "pytest tests/", 0, "5 passed")
        log_file = hook_project_root / ".claude" / "tdd-patterns.log"
        assert not log_file.exists()

    def test_non_test_command_skips(self, mod, hook_project_root):
        mod.record_tdd_pattern("Bash", "ls -la", 0, "")
        log_file = hook_project_root / ".claude" / "tdd-patterns.log"
        assert not log_file.exists()

    def test_non_bash_tool_skips(self, mod, hook_project_root):
        mod.record_tdd_pattern("Edit", "", 0, "")
        log_file = hook_project_root / ".claude" / "tdd-patterns.log"
        assert not log_file.exists()

    def test_last_test_result_updated_on_fail(self, mod, hook_project_root):
        mod.record_tdd_pattern("Bash", "pytest", 1, "FAILED")
        result = (hook_project_root / ".claude" / "last-test-result").read_text(
            encoding="utf-8"
        )
        assert result == "FAIL"

    def test_last_test_result_updated_on_pass(self, mod, hook_project_root):
        mod.record_tdd_pattern("Bash", "pytest", 0, "passed")
        result = (hook_project_root / ".claude" / "last-test-result").read_text(
            encoding="utf-8"
        )
        assert result == "PASS"


class TestDocSyncFlag:
    """責務2: doc-sync-flag 記録。"""

    def test_src_edit_records(self, mod, hook_project_root):
        mod.record_doc_sync("Edit", "src/kage_shiki/core/config.py")
        flag_file = hook_project_root / ".claude" / "doc-sync-flag"
        content = flag_file.read_text(encoding="utf-8")
        assert "src/kage_shiki/core/config.py" in content

    def test_docs_edit_not_recorded(self, mod, hook_project_root):
        mod.record_doc_sync("Edit", "docs/specs/config.md")
        flag_file = hook_project_root / ".claude" / "doc-sync-flag"
        assert not flag_file.exists()

    def test_tests_edit_not_recorded(self, mod, hook_project_root):
        mod.record_doc_sync("Edit", "tests/test_core.py")
        flag_file = hook_project_root / ".claude" / "doc-sync-flag"
        assert not flag_file.exists()

    def test_duplicate_path_not_repeated(self, mod, hook_project_root):
        mod.record_doc_sync("Edit", "src/kage_shiki/main.py")
        mod.record_doc_sync("Edit", "src/kage_shiki/main.py")
        flag_file = hook_project_root / ".claude" / "doc-sync-flag"
        content = flag_file.read_text(encoding="utf-8")
        assert content.count("src/kage_shiki/main.py") == 1

    def test_read_tool_not_recorded(self, mod, hook_project_root):
        mod.record_doc_sync("Read", "src/kage_shiki/main.py")
        flag_file = hook_project_root / ".claude" / "doc-sync-flag"
        assert not flag_file.exists()


class TestLoopLog:
    """責務3: ループログ記録。"""

    def test_appends_to_loop_state(self, mod, hook_project_root):
        state_file = hook_project_root / ".claude" / "lam-loop-state.json"
        state_file.write_text(
            json.dumps({"active": True, "iteration": 1, "tool_events": []}),
            encoding="utf-8",
        )

        mod.record_loop_event("Edit", "src/main.py", 0)
        state = json.loads(state_file.read_text(encoding="utf-8"))
        assert len(state["tool_events"]) == 1
        assert state["tool_events"][0]["tool"] == "Edit"

    def test_tool_events_capped_at_200(self, mod, hook_project_root):
        state_file = hook_project_root / ".claude" / "lam-loop-state.json"
        state_file.write_text(
            json.dumps({"active": True, "iteration": 1, "tool_events": [
                {"tool": "Edit", "path": f"file{i}.py", "exit_code": 0}
                for i in range(200)
            ]}),
            encoding="utf-8",
        )

        mod.record_loop_event("Edit", "src/new.py", 0)
        state = json.loads(state_file.read_text(encoding="utf-8"))
        assert len(state["tool_events"]) == 200
        assert state["tool_events"][-1]["path"] == "src/new.py"

    def test_no_loop_state_does_nothing(self, mod, hook_project_root):
        # lam-loop-state.json が存在しない
        mod.record_loop_event("Edit", "src/main.py", 0)

    def test_inactive_loop_does_nothing(self, mod, hook_project_root):
        state_file = hook_project_root / ".claude" / "lam-loop-state.json"
        state_file.write_text(
            json.dumps({"active": False, "iteration": 0, "tool_events": []}),
            encoding="utf-8",
        )

        mod.record_loop_event("Edit", "src/main.py", 0)
        state = json.loads(state_file.read_text(encoding="utf-8"))
        assert len(state["tool_events"]) == 0


class TestMainFunction:
    """main() 関数の統合テスト。"""

    def test_invalid_json_exits_safely(self, mod, hook_project_root):
        with patch("sys.stdin", StringIO("not json")):
            mod.main()
        # 副作用なし（ログファイル等が作られない）
        log_file = hook_project_root / ".claude" / "tdd-patterns.log"
        assert not log_file.exists()

    def test_empty_input_exits_safely(self, mod, hook_project_root):
        with patch("sys.stdin", StringIO("")):
            mod.main()
        log_file = hook_project_root / ".claude" / "tdd-patterns.log"
        assert not log_file.exists()
