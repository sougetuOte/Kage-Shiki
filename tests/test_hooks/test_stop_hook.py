"""lam-stop-hook.py のテスト."""

import json
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from tests.test_hooks.conftest import load_hook_module


@pytest.fixture
def mod(hook_project_root):
    m = load_hook_module("lam-stop-hook.py")
    m.PROJECT_ROOT = hook_project_root
    m.hook_utils.PROJECT_ROOT = hook_project_root
    return m


@pytest.fixture
def loop_state(hook_project_root):
    """lam-loop-state.json を作成するヘルパー。"""

    def _create(**overrides):
        state = {
            "active": True,
            "iteration": 0,
            "max_iterations": 5,
            "tool_events": [],
            "issues": [],
        }
        state.update(overrides)
        state_file = hook_project_root / ".claude" / "lam-loop-state.json"
        state_file.write_text(
            json.dumps(state, ensure_ascii=False), encoding="utf-8"
        )
        return state_file

    return _create


def _mock_all_green():
    """全 Green State チェックが成功する mock side_effect。"""
    def side_effect(cmd, **kwargs):
        result = MagicMock()
        result.returncode = 0
        result.stdout = "5 passed"
        return result
    return side_effect


def _mock_test_fail():
    """G1(test) のみ失敗する mock side_effect。"""
    def side_effect(cmd, **kwargs):
        result = MagicMock()
        if "pytest" in str(cmd):
            result.returncode = 1
            result.stdout = "1 failed, 4 passed"
        else:
            result.returncode = 0
            result.stdout = ""
        return result
    return side_effect


class TestReentryGuard:
    """STEP 0: 再帰防止。"""

    def test_stop_hook_active_exits(self, mod, mock_stdin, capture_stdout):
        data = {"stop_hook_active": True}
        with mock_stdin(data):
            patcher, buf = capture_stdout()
            with patcher:
                mod.main()
        assert buf.getvalue() == ""

    def test_no_stop_hook_active_continues(
        self, mod, mock_stdin, loop_state, capture_stdout,
    ):
        loop_state(active=False)
        data = {}
        with mock_stdin(data):
            patcher, buf = capture_stdout()
            with patcher:
                mod.main()
        assert buf.getvalue() == ""


class TestLoopStateCheck:
    """STEP 1: lam-loop-state.json の確認。"""

    def test_no_loop_state_exits(self, mod, mock_stdin, capture_stdout):
        data = {}
        with mock_stdin(data):
            patcher, buf = capture_stdout()
            with patcher:
                mod.main()
        assert buf.getvalue() == ""

    def test_inactive_loop_exits(
        self, mod, mock_stdin, loop_state, capture_stdout,
    ):
        loop_state(active=False)
        data = {}
        with mock_stdin(data):
            patcher, buf = capture_stdout()
            with patcher:
                mod.main()
        assert buf.getvalue() == ""


class TestIterationLimit:
    """STEP 2: 反復上限チェック。"""

    def test_max_iterations_reached_stops(
        self, mod, mock_stdin, loop_state, capture_stdout,
        hook_project_root,
    ):
        state_file = loop_state(iteration=5, max_iterations=5)
        data = {}
        with mock_stdin(data):
            patcher, buf = capture_stdout()
            with patcher:
                mod.main()
        assert buf.getvalue() == ""
        # iteration が変更されていないこと（上限で停止）
        state = json.loads(state_file.read_text(encoding="utf-8"))
        assert state["iteration"] == 5


class TestContextCheck:
    """STEP 3: コンテキスト残量チェック。"""

    def test_recent_precompact_stops(
        self, mod, mock_stdin, loop_state, capture_stdout,
        hook_project_root,
    ):
        loop_state(iteration=1)
        fired_file = hook_project_root / ".claude" / "pre-compact-fired"
        fired_file.write_text(
            mod.hook_utils.utc_now() + "\n", encoding="utf-8"
        )

        data = {}
        with mock_stdin(data):
            patcher, buf = capture_stdout()
            with patcher:
                mod.main()
        assert buf.getvalue() == ""


class TestGreenState:
    """STEP 4: Green State 判定。"""

    def test_all_green_stops(
        self, mod, mock_stdin, loop_state, capture_stdout,
        hook_project_root,
    ):
        state_file = loop_state(iteration=1)

        with (
            patch("subprocess.run", side_effect=_mock_all_green()),
            patch.object(mod, "_resolve_security_cmd", return_value=None),
        ):
            data = {}
            with mock_stdin(data):
                patcher, buf = capture_stdout()
                with patcher:
                    mod.main()
        assert buf.getvalue() == ""  # Green State 達成で停止
        # iteration が変更されていないこと
        state = json.loads(state_file.read_text(encoding="utf-8"))
        assert state["iteration"] == 1

    def test_test_fail_continues(
        self, mod, mock_stdin, loop_state, capture_stdout,
    ):
        loop_state(iteration=1)

        with (
            patch("subprocess.run", side_effect=_mock_test_fail()),
            patch.object(mod, "_resolve_security_cmd", return_value=None),
        ):
            data = {}
            with mock_stdin(data):
                patcher, buf = capture_stdout()
                with patcher:
                    mod.main()
        output = buf.getvalue()
        assert output, "テスト失敗時は継続（block 出力）が必須"
        result = json.loads(output)
        assert result["decision"] == "block"

    def test_tool_not_found_stops(
        self, mod, mock_stdin, loop_state, capture_stdout,
    ):
        """コマンドが見つからない場合はループ即停止（環境整備を促す）。"""
        loop_state(iteration=1)

        with (
            patch(
                "subprocess.run", side_effect=FileNotFoundError("pytest not found"),
            ),
            patch.object(mod, "_resolve_security_cmd", return_value=None),
        ):
            data = {}
            with mock_stdin(data):
                patcher, buf = capture_stdout()
                with patcher:
                    mod.main()
        assert buf.getvalue() == "", "ツール不在時は停止（出力なし）が必須"

    def test_lint_fail_continues(
        self, mod, mock_stdin, loop_state, capture_stdout,
    ):
        loop_state(iteration=1)

        def side_effect(cmd, **kwargs):
            result = MagicMock()
            if "ruff" in str(cmd):
                result.returncode = 1
                result.stdout = "error"
            else:
                result.returncode = 0
                result.stdout = "5 passed"
            return result

        with (
            patch("subprocess.run", side_effect=side_effect),
            patch.object(mod, "_resolve_security_cmd", return_value=None),
        ):
            data = {}
            with mock_stdin(data):
                patcher, buf = capture_stdout()
                with patcher:
                    mod.main()
        output = buf.getvalue()
        assert output, "lint 失敗時は継続（block 出力）が必須"
        result = json.loads(output)
        assert result["decision"] == "block"


class TestEscalation:
    """STEP 5: エスカレーション条件。"""

    def test_test_count_decrease_stops(
        self, mod, mock_stdin, loop_state, capture_stdout,
        hook_project_root,
    ):
        state_file = loop_state(iteration=1, prev_test_count=10)

        with (
            patch("subprocess.run", side_effect=_mock_all_green()),
            patch.object(mod, "_parse_test_count", return_value=5),
            patch.object(mod, "_resolve_security_cmd", return_value=None),
        ):
            data = {}
            with mock_stdin(data):
                patcher, buf = capture_stdout()
                with patcher:
                    mod.main()
        # テスト数減少でエスカレーション → 停止
        assert buf.getvalue() == ""
        # iteration が変更されていないこと
        state = json.loads(state_file.read_text(encoding="utf-8"))
        assert state["iteration"] == 1


class TestIterationIncrement:
    """STEP 6: iteration インクリメント。"""

    def test_iteration_incremented_on_continue(
        self, mod, mock_stdin, loop_state, capture_stdout,
        hook_project_root,
    ):
        state_file = loop_state(iteration=1)

        with (
            patch("subprocess.run", side_effect=_mock_test_fail()),
            patch.object(mod, "_resolve_security_cmd", return_value=None),
        ):
            data = {}
            with mock_stdin(data):
                patcher, buf = capture_stdout()
                with patcher:
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
            with patcher:
                mod.main()
        assert buf.getvalue() == ""

    def test_empty_input_exits_safely(self, mod, capture_stdout):
        with patch("sys.stdin", StringIO("")):
            patcher, buf = capture_stdout()
            with patcher:
                mod.main()
        assert buf.getvalue() == ""
