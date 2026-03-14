"""Stop hook — 自律ループの収束判定 (Green State チェック).

STEP 1: 再帰防止 + 状態ファイル確認 + pm_pending チェック
STEP 2: 反復上限チェック
STEP 3: コンテキスト残量チェック（PreCompact 直近 10 分以内 → 停止）
STEP 4: Green State 判定 (G1: テスト, G2: lint, G5: セキュリティ)
STEP 5: Green State 総合判定
STEP 6: エスカレーション条件（テスト数減少、Issue 再発）
STEP 7: 継続（iteration インクリメント + block 出力）

停止 → exit 0（何も出力しない）
継続 → stdout に {"decision": "block", "reason": "..."}

LAM v4.4.1 準拠 + 影式固有調整（ツール自動検出不採用、sys.executable 使用）。
"""
from __future__ import annotations

import contextlib
import datetime
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

# sys.path に hooks ディレクトリを追加（_hook_utils を import するため）
_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from _hook_utils import (  # noqa: E402
    atomic_write_json,
    get_project_root,
    log_entry,
    now_utc_iso8601,
    read_stdin_json,
    run_command,
)

# 結果定数
RESULT_PASS = 1
RESULT_FAIL = 2

# PreCompact 発火から何秒以内を「直近」とみなすか（10分）
PRE_COMPACT_THRESHOLD_SECONDS = 600

# シークレットスキャン用の正規表現パターン
_SECRET_PATTERN = re.compile(
    r'(password|secret|api_key|apikey|token|private_key)\s*=\s*["\']([^"\']{8,})',
    re.IGNORECASE,
)
_SAFE_PATTERN = re.compile(
    r"(\btest\b|\bspec\b|\bmock\b|\bexample\b|\bplaceholder\b|\bxxx\b|\bchangeme\b)",
    re.IGNORECASE,
)

# シークレットスキャン時に除外するディレクトリ
_SCAN_EXCLUDE_DIRS = frozenset({
    ".git", "node_modules", "__pycache__", ".venv", ".pytest_cache",
    "logs",  # .claude/logs/ 内のログファイルがスキャン対象に含まれることを防止
})


def _get_log_file(project_root: Path) -> Path:
    return project_root / ".claude" / "logs" / "loop.log"


def _log(log_file: Path, level: str, message: str) -> None:
    with contextlib.suppress(Exception):
        log_entry(log_file, level, "stop-hook", message)


def _stop(log_file: Path, message: str) -> None:
    """停止許可: 何も出力せず exit 0。"""
    _log(log_file, "INFO", message)
    sys.exit(0)


def _block(log_file: Path, reason: str) -> None:
    """継続指示: block JSON を stdout に出力して exit 0。"""
    _log(log_file, "INFO", f"block: {reason}")
    print(json.dumps({"decision": "block", "reason": reason}), flush=True)
    sys.exit(0)


def _save_loop_log(
    project_root: Path, state: dict, log_file: Path,
    convergence_reason: str = "green_state",
) -> None:
    """ループ終了ログを .claude/logs/ に保存する。"""
    try:
        logs_dir = project_root / ".claude" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        now = now_utc_iso8601()
        now_dt = datetime.datetime.fromisoformat(now.replace("Z", "+00:00"))
        loop_log_file = logs_dir / f"loop-{now_dt.strftime('%Y%m%d-%H%M%S')}.txt"
        lines = [
            "=== LAM Loop Log ===",
            f"Command: {state.get('command', '')}",
            f"Target: {state.get('target', '')}",
            f"Started: {state.get('started_at', '')}",
            f"Completed: {now}",
            f"Total Iterations: {state.get('iteration', 0)}",
            f"Convergence: {convergence_reason}",
            "",
            "--- Iteration Log ---",
        ]
        for entry in state.get("log", []):
            lines.append(
                f"iter {entry.get('iteration', '?')}: "
                f"found={entry.get('issues_found', 0)} "
                f"fixed={entry.get('issues_fixed', 0)} "
                f"pg={entry.get('pg', 0)} "
                f"se={entry.get('se', 0)} "
                f"pm={entry.get('pm', 0)} "
                f"tests={entry.get('test_count', 0)}"
            )
        loop_log_file.write_text("\n".join(lines), encoding="utf-8")
        _log(log_file, "INFO", f"Loop log saved to {loop_log_file}")
    except Exception:
        pass


def _validate_check_dir(cwd: str, project_root: Path) -> Path:
    """CWD の安全性を検証してチェック対象ディレクトリを返す。

    パストラバーサル防止: PROJECT_ROOT 配下のみ許可。
    """
    if not cwd:
        return project_root
    check_dir = Path(cwd).resolve()
    if not check_dir.is_absolute():
        return project_root
    try:
        check_dir.relative_to(project_root.resolve())
        return check_dir
    except ValueError:
        return project_root


def _cleanup_state_file(state_file: Path) -> None:
    """状態ファイルを安全に削除する。"""
    with contextlib.suppress(Exception):
        state_file.unlink()


# ================================================================
# Green State チェック（影式固有: ツール固定、自動検出不採用）
# ================================================================


def _run_tests(check_dir: Path, log_file: Path) -> tuple[int, int]:
    """テストを実行して (result, test_count) を返す。

    影式固有: sys.executable で pytest を直接実行（自動検出不使用）。
    注: --junitxml は付与しない（TDD パターン記録は PostToolUse hook の責務）。
    """
    cmd_args = [sys.executable, "-m", "pytest", "--tb=short", "-q"]
    _log(log_file, "INFO", f"G1: running pytest: {' '.join(cmd_args)}")

    exit_code, stdout, stderr = run_command(cmd_args, str(check_dir), timeout=120)

    if exit_code == 0:
        _log(log_file, "INFO", "G1: tests PASSED")
        test_count = 0
        m = re.search(r"(\d+) passed", stdout)
        if m:
            test_count = int(m.group(1))
        return (RESULT_PASS, test_count)

    if "timed out" in stderr:
        _log(log_file, "WARN", "G1: test timeout (120s) → FAIL")
    elif "command not found" in stderr:
        _log(log_file, "WARN", f"G1: pytest not found → FAIL ({stderr})")
    else:
        _log(log_file, "INFO", f"G1: tests FAILED (exit {exit_code})")
    return (RESULT_FAIL, 0)


def _run_lint(check_dir: Path, log_file: Path) -> int:
    """lint を実行して result を返す。

    影式固有: sys.executable で ruff を直接実行（自動検出不使用）。
    """
    cmd_args = [sys.executable, "-m", "ruff", "check", "."]
    _log(log_file, "INFO", f"G2: running ruff: {' '.join(cmd_args)}")

    exit_code, _, stderr = run_command(cmd_args, str(check_dir), timeout=60)

    if exit_code == 0:
        _log(log_file, "INFO", "G2: lint PASSED")
        return RESULT_PASS

    if "timed out" in stderr:
        _log(log_file, "WARN", "G2: lint timeout (60s) → FAIL")
    else:
        _log(log_file, "INFO", f"G2: lint FAILED (exit {exit_code})")
    return RESULT_FAIL


def _run_security(check_dir: Path, log_file: Path) -> int:
    """セキュリティチェックを実行して result を返す。

    影式固有: pip-audit を固定使用（自動検出不使用）。
    シークレットスキャンは v4.4.1 準拠で実施。
    """
    sec_fail = False

    # pip-audit（存在する場合のみ）
    if shutil.which("pip-audit"):
        _log(log_file, "INFO", "G5: running pip-audit")
        exit_code, _, stderr = run_command(
            ["pip-audit", "--desc"], str(check_dir), timeout=120
        )
        if exit_code != 0 and "timed out" not in stderr:
            _log(log_file, "INFO", "G5: pip-audit found issues")
            sec_fail = True
        elif "timed out" in stderr:
            _log(log_file, "WARN", "G5: pip-audit timeout (120s) → treating as FAIL")
            sec_fail = True
    else:
        _log(log_file, "INFO", "G5: pip-audit not found, skipping")

    # シークレットスキャン（check_dir 全体を再帰走査）
    secret_count = 0
    for scan_file in check_dir.rglob("*"):
        if scan_file.is_symlink():
            continue
        if not scan_file.is_file():
            continue
        try:
            rel = scan_file.relative_to(check_dir)
        except ValueError:
            continue
        if any(part in _SCAN_EXCLUDE_DIRS for part in rel.parts):
            continue
        try:
            if scan_file.stat().st_size > 1_000_000:
                continue
        except OSError:
            continue
        if scan_file.suffix not in {
            ".py", ".js", ".ts", ".json", ".yaml", ".yml",
            ".toml", ".cfg", ".ini", ".sh", ".env",
        }:
            continue
        try:
            content = scan_file.read_text(encoding="utf-8", errors="replace")
            for line_no, line in enumerate(content.splitlines(), 1):
                m = _SECRET_PATTERN.search(line)
                if m and not _SAFE_PATTERN.search(m.group(2)):
                    secret_count += 1
                    _log(log_file, "WARN",
                         f"G5: potential secret in {rel}:{line_no} (key={m.group(1)})")
        except Exception:
            pass

    if secret_count > 0:
        _log(log_file, "WARN",
             f"G5: potential secret leak detected ({secret_count} matches)")
        sec_fail = True

    if sec_fail:
        _log(log_file, "INFO", "G5: security checks FAILED")
        return RESULT_FAIL

    _log(log_file, "INFO", "G5: security checks PASSED")
    return RESULT_PASS


# ================================================================
# エスカレーション・TDD パターン通知
# ================================================================


def _check_issue_recurrence(state: dict) -> bool:
    """同一 Issue 再発チェック。2サイクル連続 issues_fixed=0 で True。"""
    log = state.get("log", [])
    if len(log) < 2:
        return False
    last = log[-1]
    prev = log[-2]
    return (
        last.get("issues_found", 0) > 0
        and last.get("issues_fixed", 0) == 0
        and prev.get("issues_found", 0) > 0
        and prev.get("issues_fixed", 0) == 0
    )


def _check_unanalyzed_tdd_patterns(project_root: Path, log_file: Path) -> None:
    """通知B: tdd-patterns.log の未分析パターンをチェックしてログに記録する。"""
    tdd_log = project_root / ".claude" / "tdd-patterns.log"
    if not tdd_log.exists():
        return
    try:
        lines = tdd_log.read_text(encoding="utf-8").splitlines()
        last_analyzed_idx = -1
        for i, line in enumerate(lines):
            if "\tANALYZED\t" in line:
                last_analyzed_idx = i
        unanalyzed = [
            line for line in lines[last_analyzed_idx + 1:]
            if "\tPASS\t" in line
        ]
        if unanalyzed:
            _log(
                log_file, "INFO",
                f"TDD patterns: {len(unanalyzed)}件の未分析パターンあり。/retro を推奨。",
            )
    except Exception:
        pass


# ================================================================
# STEP 分解された判定ロジック
# ================================================================


def _check_recursion_and_state(
    input_data: dict, state_file: Path, log_file: Path,
) -> dict:
    """STEP 1: 再帰防止・状態ファイル確認・pm_pending チェック。"""
    if input_data.get("stop_hook_active") is True:
        _stop(log_file, "stop_hook_active=true → recursion guard exit")

    if not state_file.exists():
        _stop(log_file, "no state file → normal stop")

    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception as e:
        _log(log_file, "ERROR", f"state file read/parse error: {type(e).__name__}: {e}")
        _stop(log_file, "failed to read state file → normal stop")

    if not state.get("active"):
        _stop(log_file, "active=false → loop disabled, normal stop")

    if state.get("pm_pending"):
        _stop(log_file, "pm_pending=true → waiting for human decision")

    return state


def _check_max_iterations(
    state: dict, state_file: Path, project_root: Path, log_file: Path,
) -> tuple[int, int]:
    """STEP 2: 反復上限チェック。"""
    iteration = int(state.get("iteration", 0))
    max_iterations = int(state.get("max_iterations", 5))

    if iteration >= max_iterations:
        _log(log_file, "WARN",
             f"max_iterations reached ({iteration}/{max_iterations}) → stop loop")
        _save_loop_log(project_root, state, log_file, "max_iterations")
        _cleanup_state_file(state_file)
        _stop(log_file, "max_iterations reached → stopped")

    return iteration, max_iterations


def _check_context_pressure(
    pre_compact_flag: Path, state: dict, state_file: Path,
    project_root: Path, log_file: Path,
) -> None:
    """STEP 3: コンテキスト残量チェック（PreCompact 発火検出）。"""
    if not pre_compact_flag.exists():
        return
    try:
        flag_content = pre_compact_flag.read_text(encoding="utf-8").strip()
        flag_dt = datetime.datetime.fromisoformat(flag_content.replace("Z", "+00:00"))
        now_dt = datetime.datetime.now(datetime.UTC)
        elapsed = (now_dt - flag_dt).total_seconds()
        if elapsed <= PRE_COMPACT_THRESHOLD_SECONDS:
            _save_loop_log(project_root, state, log_file, "context_exhaustion")
            _cleanup_state_file(state_file)
            _stop(log_file,
                  f"PreCompact fired {elapsed:.0f}s ago → context pressure, stop loop")
    except Exception:
        try:
            flag_mtime = os.path.getmtime(str(pre_compact_flag))
            elapsed = time.time() - flag_mtime
            if elapsed <= PRE_COMPACT_THRESHOLD_SECONDS:
                _save_loop_log(project_root, state, log_file, "context_exhaustion")
                _cleanup_state_file(state_file)
                _stop(log_file,
                      f"PreCompact fired {elapsed:.0f}s ago (mtime) → context pressure")
        except Exception:
            pass


def _check_escalation(
    state: dict, test_count: int, state_file: Path,
    project_root: Path, log_file: Path,
) -> None:
    """STEP 6: エスカレーション条件チェック。"""
    log_entries = state.get("log", [])
    prev_test_count = 0
    if log_entries:
        prev_test_count = int(log_entries[-1].get("test_count", 0))

    # test_count=0 は「テスト未実行」を意味し、エスカレーション対象外。
    # pytest はコレクション失敗時に exit!=0 を返すため G1 で FAIL 判定される。
    if prev_test_count > 0 and test_count > 0 and test_count < prev_test_count:
        _log(log_file, "WARN",
             f"ESC: test count decreased ({prev_test_count} → {test_count})")
        _save_loop_log(project_root, state, log_file, "escalation")
        _cleanup_state_file(state_file)
        _stop(log_file,
              f"ESC: test count decreased ({prev_test_count} → {test_count}) → escalate")

    if _check_issue_recurrence(state):
        _save_loop_log(project_root, state, log_file, "escalation")
        _cleanup_state_file(state_file)
        _stop(log_file,
              "ESC: same issues recurring (no fix for 2 cycles) → escalate")


def _evaluate_green_state(
    state: dict,
    test_result: int,
    lint_result: int,
    security_result: int,
    state_file: Path,
    project_root: Path,
    log_file: Path,
) -> tuple[bool, list[str]]:
    """STEP 5: Green State 条件の総合判定。"""
    fail_parts = []
    if test_result == RESULT_FAIL:
        fail_parts.append("テスト失敗")
    if lint_result == RESULT_FAIL:
        fail_parts.append("lint 失敗")
    if security_result == RESULT_FAIL:
        fail_parts.append("セキュリティチェック失敗")

    green_state = len(fail_parts) == 0

    if green_state:
        # convergence_reason を state に記録
        state["convergence_reason"] = "green_state"

        # 常にフルスキャンのため fullscan_pending 分岐は不要
        # （full-review は毎イテレーション全ファイルを探索する）
        _log(log_file, "INFO",
             "Green State achieved → stop loop (normal convergence)")
        _check_unanalyzed_tdd_patterns(project_root, log_file)
        _save_loop_log(project_root, state, log_file)
        _cleanup_state_file(state_file)
        _stop(log_file, "Green State achieved → loop converged")

    # green_state=True の場合は _stop() で到達しない
    return False, fail_parts


def _continue_loop(
    state: dict,
    iteration: int,
    test_count: int,
    fail_parts: list[str],
    state_file: Path,
    log_file: Path,
) -> None:
    """STEP 7: 状態更新と継続（block）。"""
    new_iteration = iteration + 1
    state["iteration"] = new_iteration

    log_entries = state.get("log", [])
    if test_count > 0 and log_entries:
        log_entries[-1]["test_count"] = test_count
    with contextlib.suppress(Exception):
        atomic_write_json(state_file, state)

    _log(log_file, "INFO", f"continuing: iteration {iteration} → {new_iteration}")

    remaining_msg = " + ".join(fail_parts) if fail_parts else "Green State 未達"
    reason = (
        f"Green State 未達。サイクル {new_iteration} を開始。残Issue: {remaining_msg}"
    )

    _block(log_file, reason)


def main() -> None:
    project_root = get_project_root()
    state_file = project_root / ".claude" / "lam-loop-state.json"
    pre_compact_flag = project_root / ".claude" / "pre-compact-fired"
    log_file = _get_log_file(project_root)

    input_data = read_stdin_json()

    # STEP 1: 再帰防止・状態ファイル確認・pm_pending
    state = _check_recursion_and_state(input_data, state_file, log_file)

    # STEP 2: 反復上限チェック
    iteration, max_iterations = _check_max_iterations(
        state, state_file, project_root, log_file
    )
    command = state.get("command", "")
    _log(log_file, "INFO",
         f"loop active: command={command}, iteration={iteration}/{max_iterations}")

    # STEP 3: コンテキスト残量チェック
    _check_context_pressure(
        pre_compact_flag, state, state_file, project_root, log_file
    )

    # STEP 4: Green State 判定（テスト + lint + セキュリティ）
    cwd = input_data.get("cwd", "")
    check_dir = _validate_check_dir(cwd, project_root)
    test_result, test_count = _run_tests(check_dir, log_file)
    lint_result = _run_lint(check_dir, log_file)
    security_result = _run_security(check_dir, log_file)

    # STEP 5: Green State 総合判定
    _, fail_parts = _evaluate_green_state(  # green_state=True なら内部で _stop()
        state, test_result, lint_result, security_result,
        state_file, project_root, log_file,
    )

    # STEP 6: エスカレーション条件チェック
    _check_escalation(state, test_count, state_file, project_root, log_file)

    # STEP 7: 継続（block）
    _continue_loop(
        state, iteration, test_count,
        fail_parts,
        state_file, log_file,
    )


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)
