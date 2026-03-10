"""Stop hook — 自律ループの収束判定 (Green State チェック).

STEP 0: 再帰防止
STEP 1: lam-loop-state.json 確認
STEP 2: 反復上限チェック
STEP 3: コンテキスト残量チェック（PreCompact 直近 10 分以内 → 停止）
STEP 4: Green State 判定 (G1: テスト, G2: lint, G5: セキュリティ)
STEP 5: エスカレーション条件
STEP 5b: Green State 総合判定
STEP 6: 継続（iteration インクリメント + block 出力）

停止 → exit 0（何も出力しない）
継続 → stdout に {"decision": "block", "reason": "..."}
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hook_utils  # noqa: E402

PROJECT_ROOT = hook_utils.PROJECT_ROOT

# Green State 判定用コマンド（辞書駆動, R-2 準拠）
# G3(対応可能 Issue ゼロ), G4(仕様差分ゼロ) は自動化困難なため本フックでは未実装（手動判断）
GREEN_STATE_COMMANDS = {
    "G1": {
        "name": "test",
        "cmd": [sys.executable, "-m", "pytest", "--tb=short", "-q"],
        "timeout": 120,
    },
    "G2": {
        "name": "lint",
        "cmd": [sys.executable, "-m", "ruff", "check", "."],
        "timeout": 60,
    },
    "G5": {
        "name": "security",
        "cmd": None,  # 動的に解決（pip-audit or safety）
        "timeout": 120,
    },
}

PRECOMPACT_THRESHOLD_MINUTES = 10


def _load_loop_state() -> dict | None:
    """lam-loop-state.json を読み込む。存在しない/不正な場合は None。"""
    state_file = PROJECT_ROOT / ".claude" / "lam-loop-state.json"
    if not state_file.exists():
        return None
    try:
        return json.loads(state_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _save_loop_state(state: dict) -> None:
    """lam-loop-state.json をアトミックに書き込む。"""
    state_file = PROJECT_ROOT / ".claude" / "lam-loop-state.json"
    dir_path = state_file.parent
    try:
        fd, tmp_path = tempfile.mkstemp(dir=str(dir_path), suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, str(state_file))
    except OSError:
        state_file.write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def _check_precompact_recent() -> bool:
    """PreCompact が直近 10 分以内に発火したか確認する。"""
    fired_file = PROJECT_ROOT / ".claude" / "pre-compact-fired"
    if not fired_file.exists():
        return False
    try:
        content = fired_file.read_text(encoding="utf-8").strip()
        fired_time = datetime.fromisoformat(content.replace("Z", "+00:00"))
        now = datetime.now(UTC)
        diff_minutes = (now - fired_time).total_seconds() / 60
        return diff_minutes < PRECOMPACT_THRESHOLD_MINUTES
    except (ValueError, OSError):
        return False


def _run_green_check(check_id: str) -> tuple[bool | None, str]:
    """Green State の個別チェックを実行する。

    Returns:
        (passed, output) のタプル。
        - True: チェック通過
        - False: チェック失敗（ループ継続）
        - None: ツール不在（ループ即停止 — 環境整備を促す）
    """
    check = GREEN_STATE_COMMANDS.get(check_id)
    if not check:
        return True, ""  # 未定義チェックはスキップ

    cmd = check["cmd"]

    # G5: セキュリティツールを動的に解決
    if cmd is None:
        cmd = _resolve_security_cmd()
        if cmd is None:
            return True, f"{check['name']} tool not found, skipping"

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=check["timeout"],
            cwd=str(PROJECT_ROOT),
        )
        return result.returncode == 0, result.stdout[:500]
    except FileNotFoundError:
        # コマンドが見つからない → 環境未整備、即停止してツール整備を促す
        return None, f"{check['name']} not found — install required"
    except subprocess.TimeoutExpired:
        return False, f"{check['name']} timed out"
    except Exception as e:
        # 予期しないエラーは失敗扱い（誤って Green と判定しない）
        return False, f"{check['name']} unexpected error: {e}"


def _resolve_security_cmd() -> list[str] | None:
    """利用可能なセキュリティチェックツールのコマンドを返す。"""
    if shutil.which("pip-audit"):
        return ["pip-audit"]
    if shutil.which("safety"):
        return ["safety", "check"]
    return None


def _parse_test_count(stdout: str) -> int:
    """pytest 出力からテスト総数を抽出する。"""
    # "5 passed", "3 passed, 2 failed" 等のパターン（warning は除外）
    numbers = re.findall(r"(\d+)\s+(?:passed|failed|error)", stdout)
    return sum(int(n) for n in numbers)


def main() -> None:
    """hook のメインエントリポイント。"""
    input_data = hook_utils.read_stdin()

    # STEP 0: 再帰防止
    if input_data.get("stop_hook_active"):
        return

    # STEP 1: loop state 確認
    state = _load_loop_state()
    if state is None:
        return
    if not state.get("active", False):
        return

    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 5)

    # STEP 2: 反復上限
    if iteration >= max_iterations:
        return

    # STEP 3: コンテキスト残量
    if _check_precompact_recent():
        return

    # STEP 4: Green State 判定
    g1_passed, g1_output = _run_green_check("G1")
    g2_passed, g2_output = _run_green_check("G2")
    g5_passed, g5_output = _run_green_check("G5")

    # STEP 4b: ツール不在チェック — 環境未整備なら即停止
    if any(p is None for p in (g1_passed, g2_passed, g5_passed)):
        return

    # STEP 5: エスカレーション
    prev_test_count = state.get("prev_test_count", 0)
    if prev_test_count > 0 and g1_output:
        current_test_count = _parse_test_count(g1_output)
        if current_test_count > 0 and current_test_count < prev_test_count:
            # テスト数が減少 → エスカレーション停止
            return

    # STEP 5b: Green State 総合判定
    if g1_passed and g2_passed and g5_passed:
        # Green State 達成 → 停止
        return

    # STEP 6: 継続
    state["iteration"] = iteration + 1
    if g1_passed and g1_output:
        state["prev_test_count"] = _parse_test_count(g1_output)

    reasons = []
    if not g1_passed:
        reasons.append("G1(test): FAIL")
    if not g2_passed:
        reasons.append("G2(lint): FAIL")
    if not g5_passed:
        reasons.append("G5(security): FAIL")

    _save_loop_state(state)

    hook_utils.write_json({
        "decision": "block",
        "reason": f"Iteration {iteration + 1}/{max_iterations}: {', '.join(reasons)}",
    })


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
