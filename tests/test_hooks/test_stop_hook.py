"""lam-stop-hook.py のテスト（safety-net only 版）.

LAM v4.5.0: Green State 判定は /full-review Stage 5（Claude 側）に移行。
Stop hook はループ安全ネット（再帰防止、上限、コンテキスト圧、block）のみ。
"""

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


class TestSafetyNetBlock:
    """STEP 4: 安全ネット block（Green State 判定なし）。"""

    def test_active_loop_blocks(
        self, mod, mock_stdin, loop_state, capture_stdout,
    ):
        """アクティブなループでは常に block を出力する。"""
        loop_state(iteration=1)
        data = {}
        with mock_stdin(data):
            patcher, buf = capture_stdout()
            with patcher, pytest.raises(SystemExit):
                mod.main()
        output = buf.getvalue()
        assert output, "アクティブなループでは block 出力が必須"
        result = json.loads(output)
        assert result["decision"] == "block"

    def test_block_reason_contains_iteration(
        self, mod, mock_stdin, loop_state, capture_stdout,
    ):
        """block の reason にイテレーション番号が含まれる。"""
        loop_state(iteration=3)
        data = {}
        with mock_stdin(data):
            patcher, buf = capture_stdout()
            with patcher, pytest.raises(SystemExit):
                mod.main()
        output = buf.getvalue()
        result = json.loads(output)
        assert "3" in result["reason"]

    def test_first_iteration_blocks(
        self, mod, mock_stdin, loop_state, capture_stdout,
    ):
        """iteration=0 でも block する。"""
        loop_state(iteration=0)
        data = {}
        with mock_stdin(data):
            patcher, buf = capture_stdout()
            with patcher, pytest.raises(SystemExit):
                mod.main()
        output = buf.getvalue()
        assert output, "初回イテレーションでも block 出力が必須"
        result = json.loads(output)
        assert result["decision"] == "block"


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


class TestRemovedFunctions:
    """Green State 判定関数が削除されていることの確認。"""

    def test_no_run_tests(self, mod):
        assert not hasattr(mod, "_run_tests")

    def test_no_run_lint(self, mod):
        assert not hasattr(mod, "_run_lint")

    def test_no_run_security(self, mod):
        assert not hasattr(mod, "_run_security")

    def test_no_result_constants(self, mod):
        assert not hasattr(mod, "RESULT_PASS")
        assert not hasattr(mod, "RESULT_FAIL")

    def test_no_green_state_evaluator(self, mod):
        assert not hasattr(mod, "_evaluate_green_state")

    def test_no_escalation_checker(self, mod):
        assert not hasattr(mod, "_check_escalation")

    def test_no_issue_recurrence_checker(self, mod):
        assert not hasattr(mod, "_check_issue_recurrence")
