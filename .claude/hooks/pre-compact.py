"""PreCompact hook — コンテキスト圧縮前の状態保存.

1. pre-compact-fired にタイムスタンプを記録
2. SESSION_STATE.md に PreCompact セクションを追記/更新（冪等）
3. lam-loop-state.json のバックアップ作成
"""

import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hook_utils  # noqa: E402

PROJECT_ROOT = hook_utils.PROJECT_ROOT

PRECOMPACT_SECTION = "## PreCompact 発火記録"


def main() -> None:
    """hook のメインエントリポイント。"""
    hook_utils.read_stdin()  # 消費するが内容は使わない

    claude_dir = PROJECT_ROOT / ".claude"
    timestamp = hook_utils.utc_now()

    # 1. タイムスタンプ記録
    fired_file = claude_dir / "pre-compact-fired"
    fired_file.write_text(timestamp + "\n", encoding="utf-8")

    # 2. SESSION_STATE.md に PreCompact セクション追記（冪等）
    session_file = PROJECT_ROOT / "SESSION_STATE.md"
    if session_file.exists():
        content = session_file.read_text(encoding="utf-8")
        if PRECOMPACT_SECTION not in content:
            new_content = (
                content + f"\n{PRECOMPACT_SECTION}\n\n最終発火: {timestamp}\n"
            )
        else:
            new_content = re.sub(
                r"最終発火: .+",
                f"最終発火: {timestamp}",
                content,
            )
        # アトミック書き込み
        try:
            fd, tmp_path = tempfile.mkstemp(
                dir=str(session_file.parent), suffix=".tmp"
            )
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(new_content)
            os.replace(tmp_path, str(session_file))
        except OSError:
            session_file.write_text(new_content, encoding="utf-8")

    # 3. lam-loop-state.json のバックアップ
    state_file = claude_dir / "lam-loop-state.json"
    if state_file.exists():
        backup_file = claude_dir / "lam-loop-state.json.bak"
        shutil.copy2(state_file, backup_file)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
