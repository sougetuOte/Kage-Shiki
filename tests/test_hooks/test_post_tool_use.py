"""post-tool-use.py のテスト."""

import json
from io import StringIO
from unittest.mock import patch

import pytest
from tests.test_hooks.conftest import load_hook_module


@pytest.fixture
def mod(hook_project_root):
    """post-tool-use モジュールをロードする。"""
    return load_hook_module("post-tool-use.py")


class TestTddPatternRecord:
    """責務1: TDD パターン記録（JUnit XML 方式）。"""

    def _write_junit_xml(self, hook_project_root, tests=5, failures=0, failed_names=None):
        """テスト用の JUnit XML を作成する。"""
        xml_file = hook_project_root / ".claude" / "test-results.xml"
        testcases = []
        for i in range(tests):
            name = f"test_{i}"
            if failed_names and name in failed_names:
                testcases.append(f'  <testcase name="{name}"><failure message="fail"/></testcase>')
            elif i < failures and not failed_names:
                name = f"test_fail_{i}"
                testcases.append(f'  <testcase name="{name}"><failure message="fail"/></testcase>')
            else:
                testcases.append(f'  <testcase name="{name}"/>')
        xml_content = (
            '<?xml version="1.0" ?>\n'
            f'<testsuite tests="{tests}" failures="{failures}">\n'
            + "\n".join(testcases)
            + "\n</testsuite>\n"
        )
        xml_file.write_text(xml_content, encoding="utf-8")

    def test_pytest_fail_records_entry(self, mod, hook_project_root):
        self._write_junit_xml(hook_project_root, tests=5, failures=2)
        tdd_log = hook_project_root / ".claude" / "tdd-patterns.log"
        xml_path = hook_project_root / ".claude" / "test-results.xml"
        last_result = hook_project_root / ".claude" / "last-test-result"
        log_file = hook_project_root / ".claude" / "logs" / "post-tool-use.log"

        mod._handle_test_result(
            "pytest tests/", tdd_log, xml_path, last_result, log_file, "2026-03-14T00:00:00Z"
        )
        log = tdd_log.read_text(encoding="utf-8")
        assert "FAIL" in log
        assert "pytest" in log

    def test_pytest_pass_after_fail_records(self, mod, hook_project_root):
        last_result = hook_project_root / ".claude" / "last-test-result"
        last_result.write_text("fail pytest\n", encoding="utf-8")
        self._write_junit_xml(hook_project_root, tests=5, failures=0)

        tdd_log = hook_project_root / ".claude" / "tdd-patterns.log"
        xml_path = hook_project_root / ".claude" / "test-results.xml"
        log_file = hook_project_root / ".claude" / "logs" / "post-tool-use.log"

        msg = mod._handle_test_result(
            "pytest tests/", tdd_log, xml_path, last_result, log_file, "2026-03-14T00:00:00Z"
        )
        log = tdd_log.read_text(encoding="utf-8")
        assert "PASS" in log
        assert msg is not None
        assert "/retro" in msg

    def test_pytest_pass_no_previous_fail_skips(self, mod, hook_project_root):
        self._write_junit_xml(hook_project_root, tests=5, failures=0)
        tdd_log = hook_project_root / ".claude" / "tdd-patterns.log"
        xml_path = hook_project_root / ".claude" / "test-results.xml"
        last_result = hook_project_root / ".claude" / "last-test-result"
        log_file = hook_project_root / ".claude" / "logs" / "post-tool-use.log"

        msg = mod._handle_test_result(
            "pytest tests/", tdd_log, xml_path, last_result, log_file, "2026-03-14T00:00:00Z"
        )
        assert not tdd_log.exists()
        assert msg is None

    def test_non_test_command_skips(self, mod, hook_project_root):
        tdd_log = hook_project_root / ".claude" / "tdd-patterns.log"
        xml_path = hook_project_root / ".claude" / "test-results.xml"
        last_result = hook_project_root / ".claude" / "last-test-result"
        log_file = hook_project_root / ".claude" / "logs" / "post-tool-use.log"

        msg = mod._handle_test_result(
            "ls -la", tdd_log, xml_path, last_result, log_file, "2026-03-14T00:00:00Z"
        )
        assert not tdd_log.exists()
        assert msg is None

    def test_xml_with_error_elements(self, mod, hook_project_root):
        """JUnit XML の <error> 要素も failures としてカウントされる。"""
        xml_file = hook_project_root / ".claude" / "test-results.xml"
        xml_file.write_text(
            '<?xml version="1.0" ?>\n'
            '<testsuite tests="3" failures="0" errors="1">\n'
            '  <testcase name="test_ok1"/>\n'
            '  <testcase name="test_ok2"/>\n'
            '  <testcase name="test_broken"><error message="setup error"/></testcase>\n'
            '</testsuite>\n',
            encoding="utf-8",
        )
        tdd_log = hook_project_root / ".claude" / "tdd-patterns.log"
        last_result = hook_project_root / ".claude" / "last-test-result"
        log_file = hook_project_root / ".claude" / "logs" / "post-tool-use.log"

        mod._handle_test_result(
            "pytest tests/", tdd_log, xml_file, last_result, log_file, "2026-03-14T00:00:00Z"
        )
        log = tdd_log.read_text(encoding="utf-8")
        assert "FAIL" in log
        assert "test_broken" in log

    def test_no_xml_file_warns(self, mod, hook_project_root):
        tdd_log = hook_project_root / ".claude" / "tdd-patterns.log"
        xml_path = hook_project_root / ".claude" / "test-results.xml"  # 存在しない
        last_result = hook_project_root / ".claude" / "last-test-result"
        log_file = hook_project_root / ".claude" / "logs" / "post-tool-use.log"

        msg = mod._handle_test_result(
            "pytest tests/", tdd_log, xml_path, last_result, log_file, "2026-03-14T00:00:00Z"
        )
        assert not tdd_log.exists()
        assert msg is None
        # WARN がログに記録されているはず
        assert log_file.exists()


class TestDocSyncFlag:
    """責務2: doc-sync-flag 記録。"""

    def test_src_edit_records(self, mod, hook_project_root):
        doc_sync_flag = hook_project_root / ".claude" / "doc-sync-flag"
        mod._handle_doc_sync_flag("Edit", "src/kage_shiki/core/config.py",
                                  hook_project_root, doc_sync_flag)
        content = doc_sync_flag.read_text(encoding="utf-8")
        assert "src/kage_shiki/core/config.py" in content

    def test_src_edit_absolute_path_records(self, mod, hook_project_root):
        """絶対パスでも src/ 配下なら正しく記録される。"""
        doc_sync_flag = hook_project_root / ".claude" / "doc-sync-flag"
        abs_path = str(hook_project_root / "src" / "kage_shiki" / "main.py")
        mod._handle_doc_sync_flag("Edit", abs_path,
                                  hook_project_root, doc_sync_flag)
        content = doc_sync_flag.read_text(encoding="utf-8")
        assert "src" in content
        assert "main.py" in content

    def test_docs_edit_not_recorded(self, mod, hook_project_root):
        doc_sync_flag = hook_project_root / ".claude" / "doc-sync-flag"
        mod._handle_doc_sync_flag("Edit", "docs/specs/config.md",
                                  hook_project_root, doc_sync_flag)
        assert not doc_sync_flag.exists()

    def test_tests_edit_not_recorded(self, mod, hook_project_root):
        doc_sync_flag = hook_project_root / ".claude" / "doc-sync-flag"
        mod._handle_doc_sync_flag("Edit", "tests/test_core.py",
                                  hook_project_root, doc_sync_flag)
        assert not doc_sync_flag.exists()

    def test_duplicate_path_not_repeated(self, mod, hook_project_root):
        doc_sync_flag = hook_project_root / ".claude" / "doc-sync-flag"
        mod._handle_doc_sync_flag("Edit", "src/kage_shiki/main.py",
                                  hook_project_root, doc_sync_flag)
        mod._handle_doc_sync_flag("Edit", "src/kage_shiki/main.py",
                                  hook_project_root, doc_sync_flag)
        content = doc_sync_flag.read_text(encoding="utf-8")
        assert content.count("src/kage_shiki/main.py") == 1

    def test_read_tool_not_recorded(self, mod, hook_project_root):
        doc_sync_flag = hook_project_root / ".claude" / "doc-sync-flag"
        mod._handle_doc_sync_flag("Read", "src/kage_shiki/main.py",
                                  hook_project_root, doc_sync_flag)
        assert not doc_sync_flag.exists()


class TestLoopLog:
    """責務3: ループログ記録。"""

    def test_appends_to_loop_state(self, mod, hook_project_root):
        state_file = hook_project_root / ".claude" / "lam-loop-state.json"
        state_file.write_text(
            json.dumps({"active": True, "iteration": 1, "tool_events": []}),
            encoding="utf-8",
        )

        mod._handle_loop_log("Edit", "", "src/main.py", state_file, "2026-03-14T00:00:00Z")
        state = json.loads(state_file.read_text(encoding="utf-8"))
        assert len(state["tool_events"]) == 1
        assert state["tool_events"][0]["tool_name"] == "Edit"

    def test_tool_events_capped_at_500(self, mod, hook_project_root):
        state_file = hook_project_root / ".claude" / "lam-loop-state.json"
        state_file.write_text(
            json.dumps({"active": True, "iteration": 1, "tool_events": [
                {"tool_name": "Edit", "file_path": f"file{i}.py"}
                for i in range(500)
            ]}),
            encoding="utf-8",
        )

        mod._handle_loop_log("Edit", "", "src/new.py", state_file, "2026-03-14T00:00:00Z")
        state = json.loads(state_file.read_text(encoding="utf-8"))
        assert len(state["tool_events"]) == 500
        assert state["tool_events"][-1]["file_path"] == "src/new.py"

    def test_no_loop_state_does_nothing(self, mod, hook_project_root):
        state_file = hook_project_root / ".claude" / "lam-loop-state.json"
        mod._handle_loop_log("Edit", "", "src/main.py", state_file, "2026-03-14T00:00:00Z")


class TestMainFunction:
    """main() 関数の統合テスト。"""

    def test_invalid_json_exits_safely(self, mod, hook_project_root):
        with patch("sys.stdin", StringIO("not json")):
            mod.main()
        log_file = hook_project_root / ".claude" / "tdd-patterns.log"
        assert not log_file.exists()

    def test_empty_input_exits_safely(self, mod, hook_project_root):
        with patch("sys.stdin", StringIO("")):
            mod.main()
        log_file = hook_project_root / ".claude" / "tdd-patterns.log"
        assert not log_file.exists()
