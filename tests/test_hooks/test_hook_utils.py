"""_hook_utils.py のテスト."""

import json
from datetime import datetime
from io import StringIO
from unittest.mock import patch

from tests.test_hooks.conftest import load_hook_module

# _hook_utils をモジュールとしてロード
utils = load_hook_module("_hook_utils.py")


class TestReadStdinJson:
    def test_valid_json(self):
        data = {"tool_name": "Read", "tool_input": {"file_path": "/tmp/test.py"}}
        with patch("sys.stdin", StringIO(json.dumps(data))):
            result = utils.read_stdin_json()
        assert result == data

    def test_empty_input(self):
        with patch("sys.stdin", StringIO("")):
            result = utils.read_stdin_json()
        assert result == {}

    def test_invalid_json(self):
        with patch("sys.stdin", StringIO("not json")):
            result = utils.read_stdin_json()
        assert result == {}


class TestNowUtcIso8601:
    def test_format(self):
        ts = utils.now_utc_iso8601()
        assert ts.endswith("Z")
        assert "T" in ts
        assert len(ts) == 20  # YYYY-MM-DDTHH:MM:SSZ

    def test_parseable(self):
        ts = utils.now_utc_iso8601()
        parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        assert parsed.year >= 2024


class TestGetProjectRoot:
    def test_returns_path(self):
        root = utils.get_project_root()
        assert root.is_dir()

    def test_env_override(self, tmp_path, monkeypatch):
        monkeypatch.setenv("LAM_PROJECT_ROOT", str(tmp_path))
        root = utils.get_project_root()
        assert root == tmp_path


class TestGetToolName:
    def test_present(self):
        assert utils.get_tool_name({"tool_name": "Edit"}) == "Edit"

    def test_missing(self):
        assert utils.get_tool_name({}) == ""


class TestGetToolInput:
    def test_present(self):
        data = {"tool_input": {"file_path": "/tmp/test.py"}}
        assert utils.get_tool_input(data, "file_path") == "/tmp/test.py"

    def test_missing_key(self):
        data = {"tool_input": {"command": "ls"}}
        assert utils.get_tool_input(data, "file_path") == ""

    def test_no_tool_input(self):
        assert utils.get_tool_input({}, "file_path") == ""

    def test_tool_input_not_dict(self):
        assert utils.get_tool_input({"tool_input": "string"}, "file_path") == ""


class TestGetToolResponse:
    def test_present(self):
        data = {"tool_response": {"stdout": "output"}}
        assert utils.get_tool_response(data, "stdout", "") == "output"

    def test_missing(self):
        assert utils.get_tool_response({}, "stdout", "default") == "default"

    def test_not_dict(self):
        assert utils.get_tool_response({"tool_response": "str"}, "stdout", "d") == "d"


class TestNormalizePath:
    def test_relative_path_unchanged(self):
        result = utils.normalize_path("src/main.py", utils.get_project_root())
        assert result == "src/main.py"

    def test_absolute_inside_project(self, tmp_path, monkeypatch):
        monkeypatch.setenv("LAM_PROJECT_ROOT", str(tmp_path))
        abs_path = str(tmp_path / "src" / "main.py")
        result = utils.normalize_path(abs_path, tmp_path)
        assert "src" in result
        assert "main.py" in result

    def test_absolute_outside_project(self, tmp_path, monkeypatch):
        monkeypatch.setenv("LAM_PROJECT_ROOT", str(tmp_path))
        other = tmp_path.parent / "other_project" / "file.py"
        result = utils.normalize_path(str(other), tmp_path)
        assert result.startswith("__out_of_root__/")

    def test_empty_path(self):
        result = utils.normalize_path("", utils.get_project_root())
        assert result == ""


class TestLogEntry:
    def test_creates_log(self, tmp_path):
        log_file = tmp_path / "logs" / "test.log"
        utils.log_entry(log_file, "INFO", "test", "hello")
        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert "INFO" in content
        assert "test" in content
        assert "hello" in content


class TestAtomicWriteJson:
    def test_writes_json(self, tmp_path):
        path = tmp_path / "test.json"
        utils.atomic_write_json(path, {"key": "value"})
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["key"] == "value"

    def test_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "sub" / "dir" / "test.json"
        utils.atomic_write_json(path, {"ok": True})
        assert path.exists()


class TestRunCommand:
    def test_echo(self):
        code, stdout, stderr = utils.run_command(
            ["python", "-c", "print('hello')"], ".", timeout=10
        )
        assert code == 0
        assert "hello" in stdout

    def test_not_found(self):
        code, stdout, stderr = utils.run_command(
            ["nonexistent_command_xyz"], ".", timeout=5
        )
        assert code == 1
        assert "not found" in stderr
