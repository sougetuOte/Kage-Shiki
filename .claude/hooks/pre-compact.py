"""PreCompact hook — コンテキスト圧縮前の状態保存.

1. pre-compact-fired にタイムスタンプを記録
2. SESSION_STATE.md に PreCompact セクションを追記/更新（冪等）
3. lam-loop-state.json のバックアップ作成

LAM v4.4.1 準拠。
"""
from __future__ import annotations

import pathlib
import shutil
import sys

_HOOKS_DIR = str(pathlib.Path(__file__).resolve().parent)
if _HOOKS_DIR not in sys.path:
    sys.path.insert(0, _HOOKS_DIR)

from _hook_utils import get_project_root, now_utc_iso8601, safe_exit  # noqa: E402


def write_pre_compact_flag(project_root: pathlib.Path, timestamp: str) -> None:
    """PreCompact 発火フラグファイルにタイムスタンプを書き込む。"""
    flag_path = project_root / ".claude" / "pre-compact-fired"
    flag_path.write_text(timestamp + "\n", encoding="utf-8")


def update_session_state(session_state: pathlib.Path, timestamp: str) -> None:
    """SESSION_STATE.md に PreCompact 発火を記録する（冪等処理）。"""
    content = session_state.read_text(encoding="utf-8")
    section_header = "## PreCompact 発火"

    if section_header in content:
        lines = content.splitlines(keepends=True)
        updated_lines = []
        in_section = False
        for line in lines:
            if line.rstrip() == section_header:
                in_section = True
            elif line.startswith("## ") and line.strip() != section_header:
                in_section = False
            if in_section and line.startswith("- 時刻: "):
                updated_lines.append(f"- 時刻: {timestamp}\n")
            else:
                updated_lines.append(line)
        session_state.write_text("".join(updated_lines), encoding="utf-8")
    else:
        suffix = (
            f"\n{section_header}\n"
            f"- 時刻: {timestamp}\n"
        )
        with open(session_state, "a", encoding="utf-8", newline="\n") as f:
            f.write(suffix)


def fallback_log(project_root: pathlib.Path, timestamp: str) -> None:
    """SESSION_STATE.md が存在しない場合に loop.log へフォールバック記録する。"""
    log_path = project_root / ".claude" / "logs" / "loop.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8", newline="\n") as f:
        f.write(f"{timestamp} PreCompact fired (no SESSION_STATE.md)\n")


def backup_loop_state(project_root: pathlib.Path) -> None:
    """lam-loop-state.json が存在すれば .bak にコピーする。"""
    loop_state = project_root / ".claude" / "lam-loop-state.json"
    if loop_state.exists():
        shutil.copy2(loop_state, loop_state.with_suffix(".json.bak"))


def main() -> None:
    try:
        project_root = get_project_root()
        timestamp = now_utc_iso8601()

        write_pre_compact_flag(project_root, timestamp)

        session_state = project_root / "SESSION_STATE.md"
        if session_state.exists():
            update_session_state(session_state, timestamp)
        else:
            fallback_log(project_root, timestamp)

        backup_loop_state(project_root)

    except Exception:
        pass

    safe_exit(0)


if __name__ == "__main__":
    main()
