"""PostToolUse hook — TDD パターン記録 + doc-sync-flag + ループログ.

責務1: テスト実行結果を tdd-patterns.log に記録
責務2: src/ 配下の変更を doc-sync-flag に記録
責務3: ループ実行中の tool_events を lam-loop-state.json に追記
"""

import json
import os
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hook_utils  # noqa: E402

PROJECT_ROOT = hook_utils.PROJECT_ROOT

# テストコマンド判定パターン
TEST_CMD_PATTERN = re.compile(
    r"(?:^|\s)(?:pytest|python\s+-m\s+pytest|npm\s+test|go\s+test)"
)

# doc-sync 対象ツール
DOC_SYNC_TOOLS = frozenset({"Edit", "Write"})

# doc-sync 対象パスプレフィックス（ソースコードのみ）
DOC_SYNC_PREFIXES = ("src/",)


def record_tdd_pattern(
    tool_name: str, command: str, exit_code: int, stdout_text: str
) -> None:
    """テスト実行結果を TDD パターンログに記録する。"""
    if tool_name != "Bash":
        return
    if not TEST_CMD_PATTERN.search(command):
        return

    claude_dir = PROJECT_ROOT / ".claude"
    last_result_file = claude_dir / "last-test-result"
    log_file = claude_dir / "tdd-patterns.log"

    # 前回結果を読み取り
    prev_result = ""
    if last_result_file.exists():
        prev_result = last_result_file.read_text(encoding="utf-8").strip()

    if exit_code != 0:
        # テスト失敗
        safe_stdout = stdout_text.replace("|", "/").replace("\n", " ")[:200]
        _append_log(log_file, f"FAIL | {command[:100]} | {safe_stdout}")
        last_result_file.write_text("FAIL", encoding="utf-8")
    else:
        # テスト成功
        if prev_result == "FAIL":
            safe_stdout = stdout_text.replace("|", "/").replace("\n", " ")[:200]
            _append_log(
                log_file,
                f"PASS (previously failed) | {command[:100]} | {safe_stdout}",
            )
        last_result_file.write_text("PASS", encoding="utf-8")


def record_doc_sync(tool_name: str, file_path: str) -> None:
    """src/ 配下のファイル変更を doc-sync-flag に記録する。"""
    if tool_name not in DOC_SYNC_TOOLS:
        return
    if not file_path:
        return
    if not any(file_path.startswith(prefix) for prefix in DOC_SYNC_PREFIXES):
        return

    flag_file = PROJECT_ROOT / ".claude" / "doc-sync-flag"

    # 重複チェック + アトミック書き込み
    existing_lines = []
    if flag_file.exists():
        existing_lines = flag_file.read_text(encoding="utf-8").splitlines()

    if file_path not in set(existing_lines):
        existing_lines.append(file_path)
        new_content = "\n".join(existing_lines) + "\n"
        try:
            fd, tmp_path = tempfile.mkstemp(
                dir=str(flag_file.parent), suffix=".tmp"
            )
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(new_content)
            os.replace(tmp_path, str(flag_file))
        except OSError:
            flag_file.write_text(new_content, encoding="utf-8")


def record_loop_event(tool_name: str, file_path: str, exit_code: int) -> None:
    """ループ実行中のツールイベントを lam-loop-state.json に追記する。"""
    state_file = PROJECT_ROOT / ".claude" / "lam-loop-state.json"
    if not state_file.exists():
        return

    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return

    if not state.get("active", False):
        return

    event = {
        "timestamp": hook_utils.utc_now(),
        "tool": tool_name,
        "path": file_path,
        "exit_code": exit_code,
    }
    MAX_TOOL_EVENTS = 200
    events = state.setdefault("tool_events", [])
    events.append(event)
    if len(events) > MAX_TOOL_EVENTS:
        state["tool_events"] = events[-MAX_TOOL_EVENTS:]

    # アトミック書き込み
    dir_path = state_file.parent
    try:
        fd, tmp_path = tempfile.mkstemp(dir=str(dir_path), suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, str(state_file))
    except OSError:
        # フォールバック: 直接書き込み
        state_file.write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def _append_log(log_file: Path, entry: str) -> None:
    """ログファイルにエントリを追記する。"""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{hook_utils.utc_now()} | {entry}\n")


def main() -> None:
    """hook のメインエントリポイント。"""
    input_data = hook_utils.read_stdin()
    if not input_data:
        return

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    if isinstance(tool_input, str):
        tool_input = {}
    tool_response = input_data.get("tool_response", {})
    if isinstance(tool_response, str):
        tool_response = {}

    command = tool_input.get("command", "")
    file_path = tool_input.get("file_path", "") or tool_input.get("path", "")
    exit_code = tool_response.get("exitCode")
    if exit_code is None:
        exit_code = 0
    stdout_text = tool_response.get("stdout", "") or ""

    # パス正規化
    normalized_path = hook_utils.normalize_path(file_path) if file_path else ""

    # 責務1: TDD パターン記録
    record_tdd_pattern(tool_name, command, exit_code, stdout_text)

    # 責務2: doc-sync-flag
    record_doc_sync(tool_name, normalized_path)

    # 責務3: ループログ
    record_loop_event(tool_name, normalized_path, exit_code)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
