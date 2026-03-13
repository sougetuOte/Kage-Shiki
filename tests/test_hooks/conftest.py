"""hooks テスト共通フィクスチャ."""

import importlib.util
import json
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent.parent / ".claude" / "hooks"


def load_hook_module(name: str):
    """hook スクリプトをモジュールとしてロードする。

    Args:
        name: ファイル名（例: "pre-tool-use.py", "_hook_utils.py"）

    Returns:
        ロードされたモジュール
    """
    file_path = HOOKS_DIR / name
    module_name = name.replace("-", "_").replace(".py", "")
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def hook_project_root(tmp_path, monkeypatch):
    """テスト用の擬似プロジェクトルートを作成する。

    LAM_PROJECT_ROOT 環境変数を設定し、_hook_utils.get_project_root() が
    テスト用ディレクトリを返すようにする。
    """
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    hooks_dir = claude_dir / "hooks"
    hooks_dir.mkdir()
    logs_dir = claude_dir / "logs"
    logs_dir.mkdir()

    phase_file = claude_dir / "current-phase.md"
    phase_file.write_text("# Current Phase\n\n**BUILDING**\n", encoding="utf-8")

    monkeypatch.setenv("LAM_PROJECT_ROOT", str(tmp_path))
    return tmp_path


@pytest.fixture
def mock_stdin():
    """stdin を JSON データで差し替えるコンテキストマネージャを返す。"""

    def _mock(data: dict):
        return patch("sys.stdin", StringIO(json.dumps(data)))

    return _mock


@pytest.fixture
def capture_stdout():
    """stdout をキャプチャする StringIO を返す。"""

    def _capture():
        buf = StringIO()
        return patch("sys.stdout", buf), buf

    return _capture
