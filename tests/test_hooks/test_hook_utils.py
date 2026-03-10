"""hook_utils.py のテスト."""

import json
from datetime import datetime
from io import StringIO
from unittest.mock import patch

from tests.test_hooks.conftest import load_hook_module

# hook_utils をモジュールとしてロード
utils = load_hook_module("hook_utils.py")


class TestReadStdin:
    def test_valid_json(self):
        data = {"tool_name": "Read", "tool_input": {"file_path": "/tmp/test.py"}}
        with patch("sys.stdin", StringIO(json.dumps(data))):
            result = utils.read_stdin()
        assert result == data

    def test_empty_input(self):
        with patch("sys.stdin", StringIO("")):
            result = utils.read_stdin()
        assert result == {}

    def test_invalid_json(self):
        with patch("sys.stdin", StringIO("not json")):
            result = utils.read_stdin()
        assert result == {}


class TestWriteJson:
    def test_output(self):
        buf = StringIO()
        with patch("sys.stdout", buf):
            utils.write_json({"decision": "block", "reason": "PM level"})
        output = json.loads(buf.getvalue())
        assert output["decision"] == "block"
        assert output["reason"] == "PM level"

    def test_non_ascii(self):
        buf = StringIO()
        with patch("sys.stdout", buf):
            utils.write_json({"msg": "日本語テスト"})
        output = json.loads(buf.getvalue())
        assert output["msg"] == "日本語テスト"


class TestUtcNow:
    def test_format(self):
        ts = utils.utc_now()
        assert ts.endswith("Z")
        assert "T" in ts
        assert len(ts) == 20  # YYYY-MM-DDTHH:MM:SSZ

    def test_parseable(self):
        ts = utils.utc_now()
        parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        assert parsed.year >= 2024


class TestNormalizePath:
    def test_project_relative(self):
        abs_path = str(utils.PROJECT_ROOT / "src" / "kage_shiki" / "main.py")
        result = utils.normalize_path(abs_path)
        assert result == "src/kage_shiki/main.py"

    def test_posix_format(self):
        abs_path = str(utils.PROJECT_ROOT / "docs" / "specs" / "test.md")
        result = utils.normalize_path(abs_path)
        assert "/" in result
        assert "\\" not in result

    def test_outside_project(self):
        path = "/tmp/outside/file.py"
        result = utils.normalize_path(path)
        # プロジェクト外パスはそのまま返す
        assert result == path

    def test_empty_path_returns_empty(self):
        result = utils.normalize_path("")
        assert result == ""


class TestGetCurrentPhase:
    def test_building_phase(self, tmp_path):
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        phase_file = claude_dir / "current-phase.md"
        phase_file.write_text(
            "# Current Phase\n\n**BUILDING**\n", encoding="utf-8"
        )

        with patch.object(utils, "PROJECT_ROOT", tmp_path):
            result = utils.get_current_phase()
        assert result == "BUILDING"

    def test_auditing_phase(self, tmp_path):
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        phase_file = claude_dir / "current-phase.md"
        phase_file.write_text(
            "# Current Phase\n\n**AUDITING**\n", encoding="utf-8"
        )

        with patch.object(utils, "PROJECT_ROOT", tmp_path):
            result = utils.get_current_phase()
        assert result == "AUDITING"

    def test_missing_file(self, tmp_path):
        with patch.object(utils, "PROJECT_ROOT", tmp_path):
            result = utils.get_current_phase()
        assert result == ""

    def test_with_extra_text(self, tmp_path):
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        phase_file = claude_dir / "current-phase.md"
        phase_file.write_text(
            "# Current Phase\n\n**BUILDING** (LAM 4.0.1 移行作業中)\n",
            encoding="utf-8",
        )

        with patch.object(utils, "PROJECT_ROOT", tmp_path):
            result = utils.get_current_phase()
        assert result == "BUILDING"
