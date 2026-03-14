"""lam-stop-hook.py のテスト."""

import json
from io import StringIO
from unittest.mock import patch

import pytest
from tests.test_hooks.conftest import load_hook_module


@pytest.fixture
def mod(hook_project_root):
    return load_hook_module("lam-stop-hook.py")


@pytest.fixture
def loop_state(hook_project_root):
    """lam-loop-state.json を作成するヘルパー。"""

    def _create(**overrides):
        state = {
            "active": True,
            "iteration": 0,
            "max_iterations": 5,
            "tool_events": [],
            "log": [],
        }
        state.update(overrides)
        state_file = hook_project_root / ".claude" / "lam-loop-state.json"
        state_file.write_text(
            json.dumps(state, ensure_ascii=False), encoding="utf-8"
        )
        return state_file

    return _create


class TestReentryGuard:
    """STEP 1: 再帰防止。"""

    def test_stop_hook_active_exits(self, mod, mock_stdin, capture_stdout):
        data = {"stop_hook_active": True}
        with mock_stdin(data):
            patcher, buf = capture_stdout()
            with patcher, pytest.raises(SystemExit):
                mod.main()
        assert buf.getvalue() == ""

    def test_no_stop_hook_active_continues(
        self, mod, mock_stdin, loop_state, capture_stdout,
    ):
        loop_state(active=False)
        data = {}
        with mock_stdin(data):
            patcher, buf = capture_stdout()
            with patcher, pytest.raises(SystemExit):
                mod.main()
        assert buf.getvalue() == ""


class TestLoopStateCheck:
    """STEP 1: lam-loop-state.json の確認。"""

    def test_no_loop_state_exits(self, mod, mock_stdin, capture_stdout):
        data = {}
        with mock_stdin(data):
            patcher, buf = capture_stdout()
            with patcher, pytest.raises(SystemExit):
                mod.main()
        assert buf.getvalue() == ""

    def test_inactive_loop_exits(
        self, mod, mock_stdin, loop_state, capture_stdout,
    ):
        loop_state(active=False)
        data = {}
        with mock_stdin(data):
            patcher, buf = capture_stdout()
            with patcher, pytest.raises(SystemExit):
                mod.main()
        assert buf.getvalue() == ""

    def test_pm_pending_exits(
        self, mod, mock_stdin, loop_state, capture_stdout,
    ):
        loop_state(pm_pending=True)
        data = {}
        with mock_stdin(data):
            patcher, buf = capture_stdout()
            with patcher, pytest.raises(SystemExit):
                mod.main()
        assert buf.getvalue() == ""


class TestIterationLimit:
    """STEP 2: 反復上限チェック。"""

    def test_max_iterations_reached_stops(
        self, mod, mock_stdin, loop_state, capture_stdout,
    ):
        loop_state(iteration=5, max_iterations=5)
        data = {}
        with mock_stdin(data):
            patcher, buf = capture_stdout()
            with patcher, pytest.raises(SystemExit):
                mod.main()
        assert buf.getvalue() == ""


class TestContextCheck:
    """STEP 3: コンテキスト残量チェック。"""

    def test_recent_precompact_stops(
        self, mod, mock_stdin, loop_state, capture_stdout,
        hook_project_root,
    ):
        loop_state(iteration=1)
        utils = load_hook_module("_hook_utils.py")
        fired_file = hook_project_root / ".claude" / "pre-compact-fired"
        fired_file.write_text(utils.now_utc_iso8601() + "\n", encoding="utf-8")

        data = {}
        with mock_stdin(data):
            patcher, buf = capture_stdout()
            with patcher, pytest.raises(SystemExit):
                mod.main()
        assert buf.getvalue() == ""


class TestGreenState:
    """STEP 4-5: Green State 判定。"""

    def test_all_green_stops(
        self, mod, mock_stdin, loop_state, capture_stdout,
    ):
        loop_state(iteration=1)

        with patch.object(mod, "_run_tests", return_value=(mod.RESULT_PASS, 5)), \
             patch.object(mod, "_run_lint", return_value=mod.RESULT_PASS), \
             patch.object(mod, "_run_security", return_value=mod.RESULT_PASS):
            data = {}
            with mock_stdin(data):
                patcher, buf = capture_stdout()
                with patcher, pytest.raises(SystemExit):
                    mod.main()
        assert buf.getvalue() == ""

    def test_test_fail_continues(
        self, mod, mock_stdin, loop_state, capture_stdout,
    ):
        loop_state(iteration=1)

        with patch.object(mod, "_run_tests", return_value=(mod.RESULT_FAIL, 0)), \
             patch.object(mod, "_run_lint", return_value=mod.RESULT_PASS), \
             patch.object(mod, "_run_security", return_value=mod.RESULT_PASS):
            data = {}
            with mock_stdin(data):
                patcher, buf = capture_stdout()
                with patcher, pytest.raises(SystemExit):
                    mod.main()
        output = buf.getvalue()
        assert output, "テスト失敗時は継続（block 出力）が必須"
        result = json.loads(output)
        assert result["decision"] == "block"

    def test_lint_fail_continues(
        self, mod, mock_stdin, loop_state, capture_stdout,
    ):
        loop_state(iteration=1)

        with patch.object(mod, "_run_tests", return_value=(mod.RESULT_PASS, 5)), \
             patch.object(mod, "_run_lint", return_value=mod.RESULT_FAIL), \
             patch.object(mod, "_run_security", return_value=mod.RESULT_PASS):
            data = {}
            with mock_stdin(data):
                patcher, buf = capture_stdout()
                with patcher, pytest.raises(SystemExit):
                    mod.main()
        output = buf.getvalue()
        assert output
        result = json.loads(output)
        assert result["decision"] == "block"


class TestEscalation:
    """STEP 6: エスカレーション条件。"""

    def test_test_count_decrease_stops(
        self, mod, mock_stdin, loop_state, capture_stdout,
    ):
        loop_state(
            iteration=1,
            log=[{"iteration": 0, "test_count": 10, "issues_found": 0, "issues_fixed": 0}],
        )

        with patch.object(mod, "_run_tests", return_value=(mod.RESULT_PASS, 5)), \
             patch.object(mod, "_run_lint", return_value=mod.RESULT_PASS), \
             patch.object(mod, "_run_security", return_value=mod.RESULT_PASS):
            data = {}
            with mock_stdin(data):
                patcher, buf = capture_stdout()
                with patcher, pytest.raises(SystemExit):
                    mod.main()
        assert buf.getvalue() == ""

    def test_issue_recurrence_stops(
        self, mod, mock_stdin, loop_state, capture_stdout,
    ):
        loop_state(
            iteration=2,
            log=[
                {"iteration": 0, "issues_found": 3, "issues_fixed": 0, "test_count": 5},
                {"iteration": 1, "issues_found": 3, "issues_fixed": 0, "test_count": 5},
            ],
        )

        with patch.object(mod, "_run_tests", return_value=(mod.RESULT_FAIL, 5)), \
             patch.object(mod, "_run_lint", return_value=mod.RESULT_PASS), \
             patch.object(mod, "_run_security", return_value=mod.RESULT_PASS):
            data = {}
            with mock_stdin(data):
                patcher, buf = capture_stdout()
                with patcher, pytest.raises(SystemExit):
                    mod.main()
        assert buf.getvalue() == ""


class TestIterationIncrement:
    """STEP 7: iteration インクリメント。"""

    def test_iteration_incremented_on_continue(
        self, mod, mock_stdin, loop_state, capture_stdout,
        hook_project_root,
    ):
        state_file = loop_state(iteration=1)

        with patch.object(mod, "_run_tests", return_value=(mod.RESULT_FAIL, 0)), \
             patch.object(mod, "_run_lint", return_value=mod.RESULT_PASS), \
             patch.object(mod, "_run_security", return_value=mod.RESULT_PASS):
            data = {}
            with mock_stdin(data):
                patcher, buf = capture_stdout()
                with patcher, pytest.raises(SystemExit):
                    mod.main()

        output = buf.getvalue()
        assert output, "テスト失敗時は継続が必須"
        state = json.loads(state_file.read_text(encoding="utf-8"))
        assert state["iteration"] >= 2


class TestMainSafety:
    """main() の安全性。"""

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
