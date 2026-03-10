"""PreToolUse hook — ファイルパスベースの PG/SE/PM 権限等級判定.

stdin JSON から tool_name と file_path/command を取得し、
権限等級を判定する。PM 級の場合は hookSpecificOutput を stdout に出力して
ユーザーに確認を求める。
"""

import re
import sys
from pathlib import Path

# hook_utils を同ディレクトリからインポート
sys.path.insert(0, str(Path(__file__).resolve().parent))
import hook_utils  # noqa: E402

PROJECT_ROOT = hook_utils.PROJECT_ROOT

# 読み取り専用ツール（常に PG 級）
READONLY_TOOLS = frozenset({
    "Read", "Glob", "Grep", "WebSearch", "WebFetch",
    "Agent", "LSP", "TaskGet", "TaskList", "TaskOutput",
})

# PM 級パスパターン（POSIX 形式の相対パスに対して match() で先頭一致）
# - match() は暗黙の ^ アンカー付き（文字列先頭から照合）
# - ディレクトリパターン（末尾 /）: 配下全ファイルに一致
# - ファイルパターン（末尾 $）: プロジェクトルート直下の特定ファイルのみ
PM_PATTERNS = [
    re.compile(r"docs/specs/"),       # 仕様書（配下全体）
    re.compile(r"docs/adr/"),         # ADR（配下全体）
    re.compile(r"docs/internal/"),    # プロセス SSOT（配下全体）
    re.compile(r"\.claude/rules/"),   # ルールファイル（配下全体）
    re.compile(r"\.claude/settings.*\.json$"),  # 設定ファイル（ルート直下）
    re.compile(r"pyproject\.toml$"),  # プロジェクト設定（ルート直下）
]


def classify_permission(
    tool_name: str, file_path: str, command: str, phase: str
) -> tuple[str, str]:
    """権限等級を判定する。

    Args:
        tool_name: ツール名 (Read, Edit, Write, Bash, etc.)
        file_path: 正規化済み相対パス (POSIX 形式)
        command: Bash コマンド文字列
        phase: 現在のフェーズ (PLANNING, BUILDING, AUDITING)

    Returns:
        (level, reason) のタプル。level は "PG", "SE", "PM" のいずれか。
    """
    # 読み取り専用ツールは常に PG
    if tool_name in READONLY_TOOLS:
        return "PG", f"read-only tool: {tool_name}"

    # ファイルパスがない場合は SE（安全側に倒す）
    if not file_path:
        return "SE", "no file path"

    # PM パターンチェック（match() で先頭一致）
    for pattern in PM_PATTERNS:
        if pattern.match(file_path):
            return "PM", f"protected path: {file_path}"

    # それ以外は SE
    return "SE", f"general path: {file_path}"


def _extract_path(tool_input: dict) -> str:
    """tool_input からファイルパスを抽出し、正規化する。"""
    raw = tool_input.get("file_path", "") or tool_input.get("path", "")
    if not raw:
        return ""
    return hook_utils.normalize_path(raw)


def _extract_command(tool_input: dict) -> str:
    """tool_input から Bash コマンドを抽出する。"""
    return tool_input.get("command", "")


def _log_decision(level: str, tool_name: str, path: str, reason: str) -> None:
    """権限判定をログファイルに記録する。"""
    log_dir = PROJECT_ROOT / ".claude" / "logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "permission.log"
        # パス表示を 100 文字にトランケート
        display_path = path[:100] if len(path) > 100 else path
        entry = f"{hook_utils.utc_now()} [{level}] {tool_name} {display_path} -- {reason}\n"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass


def main() -> None:
    """hook のメインエントリポイント。"""
    input_data = hook_utils.read_stdin()
    if not input_data:
        return

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    if isinstance(tool_input, str):
        tool_input = {}

    file_path = _extract_path(tool_input)
    command = _extract_command(tool_input)
    phase = hook_utils.get_current_phase()

    level, reason = classify_permission(tool_name, file_path, command, phase)

    _log_decision(level, tool_name, file_path, reason)

    # PM 級の場合、hookSpecificOutput を出力
    if level == "PM":
        hook_utils.write_json({
            "decision": "block",
            "reason": f"[{level}] {reason} — 承認が必要です",
        })


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
