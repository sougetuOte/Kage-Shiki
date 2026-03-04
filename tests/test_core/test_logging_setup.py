"""logging_setup のテスト (T-03).

対応 FR: FR-1.5 — INFO 以上をコンソール+ファイル出力
対応設計: D-2 — コンソール/ファイル分離 + RotatingFileHandler
"""

import logging
import logging.handlers
import sys
from pathlib import Path

import pytest

from kage_shiki.core.config import AppConfig, LoggingConfig
from kage_shiki.core.logging_setup import (
    _CONSOLE_DATE_FORMAT,
    _CONSOLE_FORMAT,
    _FILE_DATE_FORMAT,
    _FILE_FORMAT,
    _HANDLER_ATTR,
    setup_logging,
)


def _get_kage_handlers(root: logging.Logger) -> list[logging.Handler]:
    """setup_logging が追加したハンドラーのみを返す."""
    return [h for h in root.handlers if getattr(h, _HANDLER_ATTR, False)]


def _get_kage_console(root: logging.Logger) -> list[logging.StreamHandler]:
    """setup_logging が追加したコンソールハンドラーを返す."""
    return [
        h for h in _get_kage_handlers(root)
        if isinstance(h, logging.StreamHandler)
        and not isinstance(h, logging.handlers.RotatingFileHandler)
    ]


def _get_kage_file(root: logging.Logger) -> list[logging.handlers.RotatingFileHandler]:
    """setup_logging が追加したファイルハンドラーを返す."""
    return [
        h for h in _get_kage_handlers(root)
        if isinstance(h, logging.handlers.RotatingFileHandler)
    ]


@pytest.fixture(autouse=True)
def _reset_root_logger():
    """テストごとにルートロガーのハンドラーをリセットする."""
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    original_level = root.level
    yield
    root.handlers = original_handlers
    root.level = original_level


@pytest.fixture()
def log_dir(tmp_path: Path) -> Path:
    """一時ログディレクトリを返す（存在しない状態で返す）."""
    return tmp_path / "logs"


class TestSetupLogging:
    """setup_logging() の動作検証."""

    def test_adds_two_handlers_to_root_logger(self, log_dir: Path) -> None:
        """呼び出し後、ルートロガーにハンドラーが2つ登録されること."""
        config = AppConfig()
        setup_logging(config, log_dir)

        root = logging.getLogger()
        kage_handlers = _get_kage_handlers(root)
        assert len(kage_handlers) == 2

    def test_root_logger_level_is_debug(self, log_dir: Path) -> None:
        """ルートロガーのレベルが DEBUG に設定されること."""
        config = AppConfig()
        setup_logging(config, log_dir)

        root = logging.getLogger()
        assert root.level == logging.DEBUG

    def test_console_handler_level_default_info(self, log_dir: Path) -> None:
        """コンソールハンドラーのデフォルトレベルが INFO であること."""
        config = AppConfig()
        setup_logging(config, log_dir)

        root = logging.getLogger()
        console_handlers = _get_kage_console(root)
        assert len(console_handlers) == 1
        assert console_handlers[0].level == logging.INFO

    def test_file_handler_level_default_debug(self, log_dir: Path) -> None:
        """ファイルハンドラーのデフォルトレベルが DEBUG であること."""
        config = AppConfig()
        setup_logging(config, log_dir)

        root = logging.getLogger()
        file_handlers = _get_kage_file(root)
        assert len(file_handlers) == 1
        assert file_handlers[0].level == logging.DEBUG

    def test_file_handler_parameters(self, log_dir: Path) -> None:
        """RotatingFileHandler のパラメータが設定どおりであること."""
        config = AppConfig()
        setup_logging(config, log_dir)

        root = logging.getLogger()
        file_handlers = _get_kage_file(root)
        assert len(file_handlers) == 1
        handler = file_handlers[0]
        assert handler.maxBytes == 5242880  # 5MB
        assert handler.backupCount == 3
        assert handler.encoding == "utf-8"
        assert handler.delay is True

    def test_info_message_reaches_both_handlers(self, log_dir: Path) -> None:
        """INFO メッセージがコンソールとファイルの両方に出力されること."""
        config = AppConfig()
        setup_logging(config, log_dir)

        test_logger = logging.getLogger("kage_shiki.test")
        test_logger.info("テスト INFO メッセージ")

        # ファイルハンドラーをフラッシュ
        root = logging.getLogger()
        for h in root.handlers:
            h.flush()

        log_file = log_dir / "kage_shiki.log"
        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert "テスト INFO メッセージ" in content

    def test_debug_message_only_in_file(self, log_dir: Path) -> None:
        """DEBUG メッセージがファイルハンドラーにのみ出力されること."""
        config = AppConfig()
        setup_logging(config, log_dir)

        test_logger = logging.getLogger("kage_shiki.test_debug")
        test_logger.debug("テスト DEBUG メッセージ")

        root = logging.getLogger()
        for h in root.handlers:
            h.flush()

        log_file = log_dir / "kage_shiki.log"
        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert "テスト DEBUG メッセージ" in content

    def test_custom_logging_config(self, log_dir: Path) -> None:
        """カスタム LoggingConfig が反映されること."""
        config = AppConfig(
            logging=LoggingConfig(
                level="WARNING",
                file_level="INFO",
                max_bytes=1048576,
                backup_count=5,
            ),
        )
        setup_logging(config, log_dir)

        root = logging.getLogger()
        console_handlers = _get_kage_console(root)
        file_handlers = _get_kage_file(root)
        assert console_handlers[0].level == logging.WARNING
        assert file_handlers[0].level == logging.INFO
        assert file_handlers[0].maxBytes == 1048576
        assert file_handlers[0].backupCount == 5

    def test_anthropic_logger_level_warning(self, log_dir: Path) -> None:
        """anthropic ライブラリのロガーが WARNING 以上に設定されること."""
        config = AppConfig()
        setup_logging(config, log_dir)

        anthropic_logger = logging.getLogger("anthropic")
        assert anthropic_logger.level == logging.WARNING

    def test_log_file_path(self, log_dir: Path) -> None:
        """ログファイルが log_dir/kage_shiki.log に作成されること."""
        config = AppConfig()
        setup_logging(config, log_dir)

        root = logging.getLogger()
        file_handlers = _get_kage_file(root)
        expected_path = str(log_dir / "kage_shiki.log")
        assert file_handlers[0].baseFilename == expected_path

    def test_idempotent_setup(self, log_dir: Path) -> None:
        """2回呼び出しても重複ハンドラーが追加されないこと."""
        config = AppConfig()
        setup_logging(config, log_dir)
        setup_logging(config, log_dir)

        root = logging.getLogger()
        assert len(_get_kage_console(root)) == 1
        assert len(_get_kage_file(root)) == 1

    def test_log_dir_auto_created(self, tmp_path: Path) -> None:
        """log_dir が存在しない場合に自動作成されること."""
        nested_dir = tmp_path / "a" / "b" / "logs"
        assert not nested_dir.exists()

        config = AppConfig()
        setup_logging(config, nested_dir)
        assert nested_dir.exists()

    def test_console_handler_outputs_to_stderr(self, log_dir: Path) -> None:
        """コンソールハンドラーの出力先が sys.stderr であること."""
        config = AppConfig()
        setup_logging(config, log_dir)

        root = logging.getLogger()
        console_handlers = _get_kage_console(root)
        assert len(console_handlers) == 1
        assert console_handlers[0].stream is sys.stderr

    def test_console_handler_format(self, log_dir: Path) -> None:
        """コンソールハンドラーのフォーマットが仕様どおりであること."""
        config = AppConfig()
        setup_logging(config, log_dir)

        root = logging.getLogger()
        console_handlers = _get_kage_console(root)
        formatter = console_handlers[0].formatter
        assert formatter._fmt == _CONSOLE_FORMAT
        assert formatter.datefmt == _CONSOLE_DATE_FORMAT

    def test_file_handler_format(self, log_dir: Path) -> None:
        """ファイルハンドラーのフォーマットが仕様どおりであること."""
        config = AppConfig()
        setup_logging(config, log_dir)

        root = logging.getLogger()
        file_handlers = _get_kage_file(root)
        formatter = file_handlers[0].formatter
        assert formatter._fmt == _FILE_FORMAT
        assert formatter.datefmt == _FILE_DATE_FORMAT

    def test_invalid_log_level_falls_back_with_warning(
        self, log_dir: Path, caplog: pytest.LogCaptureFixture,
    ) -> None:
        """無効なログレベル名でフォールバックと WARNING ログが出ること."""
        config = AppConfig(
            logging=LoggingConfig(level="VERBOSE"),
        )
        with caplog.at_level(logging.WARNING):
            setup_logging(config, log_dir)

        root = logging.getLogger()
        console_handlers = _get_kage_console(root)
        # フォールバックでデフォルト INFO になる
        assert console_handlers[0].level == logging.INFO
        assert "VERBOSE" in caplog.text
