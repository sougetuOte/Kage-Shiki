"""LAM hooks 共通ユーティリティ.

全 hook スクリプトから共有される基盤関数群。
- read_stdin(): stdin から JSON 読み取り
- write_json(): stdout に JSON 出力
- utc_now(): UTC タイムスタンプ (ISO 8601)
- normalize_path(): 絶対パス → PROJECT_ROOT 相対パス (POSIX 形式)
- get_current_phase(): current-phase.md からフェーズ名を取得
"""

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


MAX_STDIN_BYTES = 1 * 1024 * 1024  # 1 MB


def read_stdin() -> dict:
    """stdin から JSON を読み取る。失敗時は空辞書を返す。"""
    try:
        return json.loads(sys.stdin.read(MAX_STDIN_BYTES))
    except Exception:
        return {}


def write_json(data: dict) -> None:
    """stdout に JSON を出力する。"""
    json.dump(data, sys.stdout, ensure_ascii=False)


def utc_now() -> str:
    """UTC タイムスタンプを ISO 8601 形式で返す。"""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_path(file_path: str) -> str:
    """絶対パスを PROJECT_ROOT からの相対パスに正規化する (POSIX 形式)。

    プロジェクト外のパスはそのまま返す。空文字列は空文字列を返す。
    """
    if not file_path:
        return ""
    try:
        rel = Path(file_path).resolve().relative_to(PROJECT_ROOT)
        return rel.as_posix()
    except (ValueError, OSError):
        return file_path


def get_current_phase() -> str:
    """current-phase.md からフェーズ名を取得する。

    Returns:
        "PLANNING", "BUILDING", "AUDITING" のいずれか。
        取得失敗時は空文字列。
    """
    phase_file = PROJECT_ROOT / ".claude" / "current-phase.md"
    phase_pattern = re.compile(r"\*\*(PLANNING|BUILDING|AUDITING)\*\*")
    try:
        content = phase_file.read_text(encoding="utf-8")
        match = phase_pattern.search(content)
        return match.group(1) if match else ""
    except Exception:
        return ""
