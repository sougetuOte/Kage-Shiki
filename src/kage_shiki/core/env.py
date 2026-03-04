"""環境変数 + API キー確認 (T-04).

対応 FR: FR-1.6 — 起動時に ANTHROPIC_API_KEY 環境変数の存在を確認
対応設計: D-10 — python-dotenv 採用

Note:
    load_dotenv_file() は main.py の起動シーケンス最初期に呼び出す。
    ensure_api_key() は load_dotenv_file() の後に呼び出す。
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_API_KEY_ENV = "ANTHROPIC_API_KEY"
_DEFAULT_ENV_PATH = Path(__file__).resolve().parent.parent.parent.parent / ".env"


def load_dotenv_file(env_path: Path | None = None) -> None:
    """python-dotenv で .env ファイルを読み込む (D-10 Section 5.2).

    既に設定されている環境変数は上書きしない（override=False）。

    Args:
        env_path: .env ファイルのパス。None の場合はプロジェクトルートを推定する。
    """
    if env_path is None:
        env_path = _DEFAULT_ENV_PATH

    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)
        logger.debug(".env ファイルを読み込みました: %s", env_path)
    else:
        logger.debug(".env ファイルが見つかりません: %s", env_path)


def ensure_api_key(env_path: Path | None = None) -> str:
    """ANTHROPIC_API_KEY 環境変数を検証し、API キーを返す.

    環境変数が未設定または空の場合、エラーメッセージを stderr に出力して
    sys.exit(1) で終了する。.env ファイルの有無に応じて段階的に案内する。

    Args:
        env_path: .env ファイルのパス（エラーメッセージ分岐用）。
            None の場合はプロジェクトルートを推定する。

    Returns:
        検証済みの API キー文字列。

    Raises:
        SystemExit: API キーが未設定または空の場合。
    """
    key = os.environ.get(_API_KEY_ENV, "").strip()
    if key:
        return key

    # エラーメッセージの構築 (D-10 Section 5.4)
    if env_path is None:
        env_path = _DEFAULT_ENV_PATH

    if env_path.exists():
        msg = (
            f"エラー: .env ファイルは見つかりましたが "
            f"{_API_KEY_ENV} が見つかりません。\n"
            f".env ファイルに以下の行を追加してください:\n"
            f"  {_API_KEY_ENV}=sk-ant-ここにキーを貼り付ける\n"
        )
    else:
        msg = (
            f"エラー: {_API_KEY_ENV} が設定されていません。\n\n"
            f"設定方法:\n"
            f"  方法1（推奨）: .env.example を .env にコピーして\n"
            f"    {_API_KEY_ENV} に API キーを貼り付けてください。\n\n"
            f"  方法2: Windows の環境変数として設定してください。\n"
            f"    [スタートメニュー] → 「環境変数」で検索 → [環境変数を編集]\n"
            f"    変数名: {_API_KEY_ENV}\n"
            f"    変数値: [API キー]\n\n"
            f"  API キーの取得: https://console.anthropic.com/\n"
        )

    print(msg, file=sys.stderr)
    sys.exit(1)
