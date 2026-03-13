"""pre-compact.py のテスト."""

import json
import re

import pytest
from tests.test_hooks.conftest import load_hook_module


@pytest.fixture
def mod(hook_project_root):
    return load_hook_module("pre-compact.py")


class TestPreCompact:
    def test_records_timestamp(self, mod, hook_project_root):
        with pytest.raises(SystemExit):
            mod.main()
        fired_file = hook_project_root / ".claude" / "pre-compact-fired"
        assert fired_file.exists()
        content = fired_file.read_text(encoding="utf-8").strip()
        assert "T" in content  # ISO 8601 format

    def test_appends_to_session_state(self, mod, hook_project_root):
        session_file = hook_project_root / "SESSION_STATE.md"
        session_file.write_text("# SESSION_STATE\n\nsome content\n", encoding="utf-8")

        with pytest.raises(SystemExit):
            mod.main()
        content = session_file.read_text(encoding="utf-8")
        assert "PreCompact" in content

    def test_session_state_idempotent(self, mod, hook_project_root):
        session_file = hook_project_root / "SESSION_STATE.md"
        session_file.write_text("# SESSION_STATE\n\nsome content\n", encoding="utf-8")

        with pytest.raises(SystemExit):
            mod.main()
        content_after_first = session_file.read_text(encoding="utf-8")
        ts1 = re.search(r"時刻: (.+)", content_after_first)

        with pytest.raises(SystemExit):
            mod.main()
        content = session_file.read_text(encoding="utf-8")
        assert content.count("PreCompact") == 1
        ts2 = re.search(r"時刻: (.+)", content)
        assert ts1 and ts2
        assert ts2.group(1) >= ts1.group(1)

    def test_backs_up_loop_state(self, mod, hook_project_root):
        state_file = hook_project_root / ".claude" / "lam-loop-state.json"
        state_file.write_text(
            json.dumps({"active": True, "iteration": 3}), encoding="utf-8"
        )

        with pytest.raises(SystemExit):
            mod.main()
        backup = hook_project_root / ".claude" / "lam-loop-state.json.bak"
        assert backup.exists()
        data = json.loads(backup.read_text(encoding="utf-8"))
        assert data["iteration"] == 3

    def test_no_loop_state_no_backup(self, mod, hook_project_root):
        with pytest.raises(SystemExit):
            mod.main()
        backup = hook_project_root / ".claude" / "lam-loop-state.json.bak"
        assert not backup.exists()

    def test_no_session_state_does_not_crash(self, mod, hook_project_root):
        with pytest.raises(SystemExit):
            mod.main()
        fired_file = hook_project_root / ".claude" / "pre-compact-fired"
        assert fired_file.exists()
        session_file = hook_project_root / "SESSION_STATE.md"
        assert not session_file.exists()
