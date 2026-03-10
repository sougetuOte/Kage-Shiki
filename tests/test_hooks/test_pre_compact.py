"""pre-compact.py のテスト."""

import json
import re

import pytest
from tests.test_hooks.conftest import load_hook_module


@pytest.fixture
def mod(hook_project_root):
    m = load_hook_module("pre-compact.py")
    m.PROJECT_ROOT = hook_project_root
    m.hook_utils.PROJECT_ROOT = hook_project_root
    return m


class TestPreCompact:
    def test_records_timestamp(self, mod, hook_project_root):
        mod.main()
        fired_file = hook_project_root / ".claude" / "pre-compact-fired"
        assert fired_file.exists()
        content = fired_file.read_text(encoding="utf-8").strip()
        assert "T" in content  # ISO 8601 format

    def test_appends_to_session_state(self, mod, hook_project_root):
        session_file = hook_project_root / "SESSION_STATE.md"
        session_file.write_text("# SESSION_STATE\n\nsome content\n", encoding="utf-8")

        mod.main()
        content = session_file.read_text(encoding="utf-8")
        assert "PreCompact" in content

    def test_session_state_idempotent(self, mod, hook_project_root):
        session_file = hook_project_root / "SESSION_STATE.md"
        session_file.write_text("# SESSION_STATE\n\nsome content\n", encoding="utf-8")

        mod.main()
        content_after_first = session_file.read_text(encoding="utf-8")
        ts1 = re.search(r"最終発火: (.+)", content_after_first)

        mod.main()  # 2回実行
        content = session_file.read_text(encoding="utf-8")
        assert content.count("PreCompact") == 1  # セクションは1つだけ
        # タイムスタンプが更新されていること
        ts2 = re.search(r"最終発火: (.+)", content)
        assert ts1 and ts2
        assert ts2.group(1) >= ts1.group(1)  # 同一秒以降

    def test_backs_up_loop_state(self, mod, hook_project_root):
        state_file = hook_project_root / ".claude" / "lam-loop-state.json"
        state_file.write_text(
            json.dumps({"active": True, "iteration": 3}), encoding="utf-8"
        )

        mod.main()
        backup = hook_project_root / ".claude" / "lam-loop-state.json.bak"
        assert backup.exists()
        data = json.loads(backup.read_text(encoding="utf-8"))
        assert data["iteration"] == 3

    def test_no_loop_state_no_backup(self, mod, hook_project_root):
        mod.main()
        backup = hook_project_root / ".claude" / "lam-loop-state.json.bak"
        assert not backup.exists()

    def test_no_session_state_does_not_crash(self, mod, hook_project_root):
        # SESSION_STATE.md が存在しない場合でもクラッシュしない
        mod.main()
        # タイムスタンプは記録される（SESSION_STATE.md がなくても）
        fired_file = hook_project_root / ".claude" / "pre-compact-fired"
        assert fired_file.exists()
        # SESSION_STATE.md は作成されない
        session_file = hook_project_root / "SESSION_STATE.md"
        assert not session_file.exists()
