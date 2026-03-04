"""ログシステム初期化 (T-03).

対応 FR: FR-1.5 — INFO 以上のログをコンソール+ファイル出力
対応設計: D-2 — コンソール/ファイル分離 + RotatingFileHandler

プライバシーポリシー (D-2 Section 5.5):
    - LLM レスポンス本文はログに含めない（トークン数・処理時間のみ記録）
    - ユーザー入力テキスト本文はログに含めない（文字数・タイムスタンプのみ）
    - persona_core.md の内容はログに含めない（パス・ハッシュ・成否のみ）
"""

import logging
import logging.handlers
import sys
from pathlib import Path

from kage_shiki.core.config import AppConfig

_LOG_FILENAME = "kage_shiki.log"

_CONSOLE_FORMAT = "[%(asctime)s] %(levelname)-8s %(name)s  %(message)s"
_CONSOLE_DATE_FORMAT = "%H:%M:%S"

_FILE_FORMAT = "%(asctime)s %(levelname)-10s %(name)s  %(message)s"
_FILE_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# setup_logging が追加したハンドラーを追跡し、再呼び出し時に重複を防ぐ
_HANDLER_ATTR = "_kage_shiki_handler"

# 有効なログレベル名のホワイトリスト
_VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def setup_logging(config: AppConfig, log_dir: Path) -> None:
    """アプリケーションのログシステムを初期化する.

    ルートロガーに ConsoleHandler（stderr, INFO）と
    RotatingFileHandler（DEBUG, 5MB×3世代）を登録する。
    2回以上呼び出しても重複ハンドラーは追加されない。

    Args:
        config: アプリケーション設定。logging セクションを参照する。
        log_dir: ログファイルの出力先ディレクトリ。存在しない場合は作成する。
    """
    log_dir.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()

    # 既にセットアップ済みの場合はハンドラーを除去してから再設定
    root.handlers = [
        h for h in root.handlers
        if not getattr(h, _HANDLER_ATTR, False)
    ]

    # ルートロガーのレベルは最も低い DEBUG に設定（全レベルを捕捉）
    root.setLevel(logging.DEBUG)

    log_cfg = config.logging

    # --- ConsoleHandler (StreamHandler to stderr) ---
    console_handler = logging.StreamHandler(sys.stderr)
    console_level = _resolve_log_level(log_cfg.level, logging.INFO)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(
        logging.Formatter(_CONSOLE_FORMAT, datefmt=_CONSOLE_DATE_FORMAT),
    )
    setattr(console_handler, _HANDLER_ATTR, True)
    root.addHandler(console_handler)

    # --- RotatingFileHandler ---
    log_file = log_dir / _LOG_FILENAME
    file_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_file),
        maxBytes=log_cfg.max_bytes,
        backupCount=log_cfg.backup_count,
        encoding="utf-8",
        delay=True,
    )
    file_level = _resolve_log_level(log_cfg.file_level, logging.DEBUG)
    file_handler.setLevel(file_level)
    file_handler.setFormatter(
        logging.Formatter(_FILE_FORMAT, datefmt=_FILE_DATE_FORMAT),
    )
    setattr(file_handler, _HANDLER_ATTR, True)
    root.addHandler(file_handler)

    # --- anthropic ライブラリのロガーを WARNING 以上に抑制 ---
    logging.getLogger("anthropic").setLevel(logging.WARNING)


def _resolve_log_level(level_name: str, default: int) -> int:
    """ログレベル名を検証し、有効であれば対応する整数値を返す.

    Args:
        level_name: ログレベル名（"DEBUG", "INFO" 等）。
        default: 無効な場合のフォールバック値。

    Returns:
        ログレベルの整数値。
    """
    if level_name not in _VALID_LOG_LEVELS:
        logging.warning(
            "無効なログレベル %r — デフォルト (%s) にフォールバック",
            level_name,
            logging.getLevelName(default),
        )
        return default
    return getattr(logging, level_name)
