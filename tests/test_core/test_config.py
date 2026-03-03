"""T-02: AppConfig dataclass + config.toml 読み書きのテスト.

対応 FR:
    FR-1.1: config.toml を読み込み、全設定値をアプリケーションに反映
    FR-1.2: config.toml が存在しない場合、デフォルト値で config.toml を生成
    FR-1.3: config.toml の値が不正な場合、デフォルト値にフォールバックし警告表示
"""

import logging
import tomllib
from pathlib import Path

import pytest

from kage_shiki.core.config import (
    ApiConfig,
    AppConfig,
    ConversationConfig,
    GeneralConfig,
    GuiConfig,
    LoggingConfig,
    MemoryConfig,
    ModelsConfig,
    TrayConfig,
    WizardConfig,
    generate_default_config,
    get_max_tokens,
    load_config,
)

# ---------------------------------------------------------------------------
# フィクスチャ
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_config_dir(tmp_path: Path) -> Path:
    """一時ディレクトリを返す。"""
    return tmp_path


@pytest.fixture
def valid_config_toml(tmp_config_dir: Path) -> Path:
    """有効な config.toml を一時ディレクトリに作成して返す。"""
    config_path = tmp_config_dir / "config.toml"
    config_path.write_text(
        """
[general]
persona_frozen = true
data_dir = "./custom_data"

[models]
conversation = "claude-haiku-4-5-20251001"
memory_worker = "claude-haiku-4-5-20251001"
utility = "claude-haiku-4-5-20251001"
wizard = "claude-haiku-4-5-20251001"

[wizard]
association_count = 7
temperature = 0.8
candidate_count = 4
blank_freeze_threshold = 25

[conversation]
temperature = 0.6
max_tokens = 2048

[gui]
window_width = 500
window_height = 400
opacity = 0.85
topmost = false
font_size = 16
font_family = "Meiryo"

[memory]
warm_days = 7
cold_top_k = 10
consistency_interval = 30

[api]
max_retries = 5
retry_backoff_base = 1.5
timeout = 60

[tray]
minimize_to_tray = false

[logging]
level = "DEBUG"
file_level = "INFO"
max_bytes = 1048576
backup_count = 5
""",
        encoding="utf-8",
    )
    return config_path


# ---------------------------------------------------------------------------
# dataclass のデフォルト値テスト
# ---------------------------------------------------------------------------


class TestDataclassDefaults:
    """各 dataclass がデフォルト値を持つことを検証する。"""

    def test_general_config_defaults(self):
        """GeneralConfig のデフォルト値が仕様通りであること。"""
        cfg = GeneralConfig()
        assert cfg.persona_frozen is False
        assert cfg.data_dir == "./data"

    def test_models_config_defaults(self):
        """ModelsConfig のデフォルト値が仕様通りであること。"""
        cfg = ModelsConfig()
        assert cfg.conversation == "claude-haiku-4-5-20251001"
        assert cfg.memory_worker == "claude-haiku-4-5-20251001"
        assert cfg.utility == "claude-haiku-4-5-20251001"
        assert cfg.wizard == "claude-haiku-4-5-20251001"

    def test_wizard_config_defaults(self):
        """WizardConfig のデフォルト値が仕様通りであること。"""
        cfg = WizardConfig()
        assert cfg.association_count == 5
        assert cfg.temperature == pytest.approx(0.9)
        assert cfg.candidate_count == 3
        assert cfg.blank_freeze_threshold == 20

    def test_conversation_config_defaults(self):
        """ConversationConfig のデフォルト値が仕様通りであること。"""
        cfg = ConversationConfig()
        assert cfg.temperature == pytest.approx(0.7)
        assert cfg.max_tokens == 1024

    def test_gui_config_defaults(self):
        """GuiConfig のデフォルト値が仕様通りであること。"""
        cfg = GuiConfig()
        assert cfg.window_width == 400
        assert cfg.window_height == 300
        assert cfg.opacity == pytest.approx(0.95)
        assert cfg.topmost is True
        assert cfg.font_size == 14
        assert cfg.font_family == ""

    def test_memory_config_defaults(self):
        """MemoryConfig のデフォルト値が仕様通りであること。"""
        cfg = MemoryConfig()
        assert cfg.warm_days == 5
        assert cfg.cold_top_k == 5
        assert cfg.consistency_interval == 15

    def test_api_config_defaults(self):
        """ApiConfig のデフォルト値が仕様通りであること。"""
        cfg = ApiConfig()
        assert cfg.max_retries == 3
        assert cfg.retry_backoff_base == pytest.approx(2.0)
        assert cfg.timeout == 30

    def test_tray_config_defaults(self):
        """TrayConfig のデフォルト値が仕様通りであること。"""
        cfg = TrayConfig()
        assert cfg.minimize_to_tray is True

    def test_logging_config_defaults(self):
        """LoggingConfig のデフォルト値が仕様通りであること。"""
        cfg = LoggingConfig()
        assert cfg.level == "INFO"
        assert cfg.file_level == "DEBUG"
        assert cfg.max_bytes == 5242880
        assert cfg.backup_count == 3

    def test_app_config_defaults(self):
        """AppConfig がデフォルトで全サブ config を持つこと。"""
        cfg = AppConfig()
        assert isinstance(cfg.general, GeneralConfig)
        assert isinstance(cfg.models, ModelsConfig)
        assert isinstance(cfg.wizard, WizardConfig)
        assert isinstance(cfg.conversation, ConversationConfig)
        assert isinstance(cfg.gui, GuiConfig)
        assert isinstance(cfg.memory, MemoryConfig)
        assert isinstance(cfg.api, ApiConfig)
        assert isinstance(cfg.tray, TrayConfig)
        assert isinstance(cfg.logging, LoggingConfig)


# ---------------------------------------------------------------------------
# FR-1.1: 正常な config.toml の読み込み
# ---------------------------------------------------------------------------


class TestLoadConfigNormal:
    """FR-1.1: 正常な config.toml の読み込みを検証する。"""

    def test_load_config_returns_app_config(self, valid_config_toml: Path):
        """load_config が AppConfig インスタンスを返すこと。"""
        cfg = load_config(valid_config_toml)
        assert isinstance(cfg, AppConfig)

    def test_load_config_general_section(self, valid_config_toml: Path):
        """[general] セクションが正しく読み込まれること。"""
        cfg = load_config(valid_config_toml)
        assert cfg.general.persona_frozen is True
        assert cfg.general.data_dir == "./custom_data"

    def test_load_config_models_section(self, valid_config_toml: Path):
        """[models] セクションが正しく読み込まれること。"""
        cfg = load_config(valid_config_toml)
        assert cfg.models.conversation == "claude-haiku-4-5-20251001"

    def test_load_config_wizard_section(self, valid_config_toml: Path):
        """[wizard] セクションが正しく読み込まれること。"""
        cfg = load_config(valid_config_toml)
        assert cfg.wizard.association_count == 7
        assert cfg.wizard.temperature == pytest.approx(0.8)
        assert cfg.wizard.candidate_count == 4
        assert cfg.wizard.blank_freeze_threshold == 25

    def test_load_config_conversation_section(self, valid_config_toml: Path):
        """[conversation] セクションが正しく読み込まれること。"""
        cfg = load_config(valid_config_toml)
        assert cfg.conversation.temperature == pytest.approx(0.6)
        assert cfg.conversation.max_tokens == 2048

    def test_load_config_gui_section(self, valid_config_toml: Path):
        """[gui] セクションが正しく読み込まれること。"""
        cfg = load_config(valid_config_toml)
        assert cfg.gui.window_width == 500
        assert cfg.gui.window_height == 400
        assert cfg.gui.opacity == pytest.approx(0.85)
        assert cfg.gui.topmost is False
        assert cfg.gui.font_size == 16
        assert cfg.gui.font_family == "Meiryo"

    def test_load_config_memory_section(self, valid_config_toml: Path):
        """[memory] セクションが正しく読み込まれること。"""
        cfg = load_config(valid_config_toml)
        assert cfg.memory.warm_days == 7
        assert cfg.memory.cold_top_k == 10
        assert cfg.memory.consistency_interval == 30

    def test_load_config_api_section(self, valid_config_toml: Path):
        """[api] セクションが正しく読み込まれること。"""
        cfg = load_config(valid_config_toml)
        assert cfg.api.max_retries == 5
        assert cfg.api.retry_backoff_base == pytest.approx(1.5)
        assert cfg.api.timeout == 60

    def test_load_config_tray_section(self, valid_config_toml: Path):
        """[tray] セクションが正しく読み込まれること。"""
        cfg = load_config(valid_config_toml)
        assert cfg.tray.minimize_to_tray is False

    def test_load_config_logging_section(self, valid_config_toml: Path):
        """[logging] セクションが正しく読み込まれること。"""
        cfg = load_config(valid_config_toml)
        assert cfg.logging.level == "DEBUG"
        assert cfg.logging.file_level == "INFO"
        assert cfg.logging.max_bytes == 1048576
        assert cfg.logging.backup_count == 5

    def test_load_config_ignores_unknown_keys(self, tmp_config_dir: Path):
        """未知のキーが存在しても例外を起こさずに読み込まれること。"""
        config_path = tmp_config_dir / "config.toml"
        config_path.write_text(
            "[general]\nunknown_key = 'unexpected'\npersona_frozen = false\n",
            encoding="utf-8",
        )
        cfg = load_config(config_path)
        assert isinstance(cfg, AppConfig)


# ---------------------------------------------------------------------------
# FR-1.2: config.toml が存在しない場合のデフォルト生成
# ---------------------------------------------------------------------------


class TestLoadConfigMissing:
    """FR-1.2: config.toml 不在時のデフォルト生成を検証する。"""

    def test_load_config_creates_file_when_missing(self, tmp_config_dir: Path):
        """config.toml が存在しない場合、ファイルが生成されること。"""
        config_path = tmp_config_dir / "config.toml"
        assert not config_path.exists()

        load_config(config_path)

        assert config_path.exists()

    def test_load_config_returns_defaults_when_missing(self, tmp_config_dir: Path):
        """config.toml が存在しない場合、デフォルト値の AppConfig が返ること。"""
        config_path = tmp_config_dir / "config.toml"
        cfg = load_config(config_path)

        default = AppConfig()
        assert cfg.general.persona_frozen == default.general.persona_frozen
        assert cfg.general.data_dir == default.general.data_dir
        assert cfg.gui.window_width == default.gui.window_width
        assert cfg.conversation.max_tokens == default.conversation.max_tokens

    def test_generated_file_is_valid_toml(self, tmp_config_dir: Path):
        """生成された config.toml が有効な TOML であること。"""
        config_path = tmp_config_dir / "config.toml"
        load_config(config_path)

        with open(config_path, "rb") as f:
            parsed = tomllib.load(f)
        assert isinstance(parsed, dict)

    def test_generated_file_contains_all_sections(self, tmp_config_dir: Path):
        """生成された config.toml に全セクションが含まれること。"""
        config_path = tmp_config_dir / "config.toml"
        load_config(config_path)

        content = config_path.read_text(encoding="utf-8")
        expected_sections = [
            "[general]",
            "[models]",
            "[wizard]",
            "[conversation]",
            "[gui]",
            "[memory]",
            "[api]",
            "[tray]",
            "[logging]",
        ]
        for section in expected_sections:
            assert section in content, f"Section {section} not found in generated config"


# ---------------------------------------------------------------------------
# generate_default_config のテスト
# ---------------------------------------------------------------------------


class TestGenerateDefaultConfig:
    """generate_default_config の出力を検証する。"""

    def test_generates_file(self, tmp_config_dir: Path):
        """ファイルが生成されること。"""
        config_path = tmp_config_dir / "config.toml"
        generate_default_config(config_path)
        assert config_path.exists()

    def test_generated_file_is_valid_toml(self, tmp_config_dir: Path):
        """生成ファイルが有効な TOML であること。"""
        config_path = tmp_config_dir / "config.toml"
        generate_default_config(config_path)

        with open(config_path, "rb") as f:
            parsed = tomllib.load(f)
        assert isinstance(parsed, dict)

    def test_generated_file_contains_all_sections(self, tmp_config_dir: Path):
        """全セクションが含まれること。"""
        config_path = tmp_config_dir / "config.toml"
        generate_default_config(config_path)

        content = config_path.read_text(encoding="utf-8")
        for section in [
            "[general]", "[models]", "[wizard]", "[conversation]",
            "[gui]", "[memory]", "[api]", "[tray]", "[logging]",
        ]:
            assert section in content

    def test_generated_file_contains_comments(self, tmp_config_dir: Path):
        """コメント（# で始まる行）が含まれること。"""
        config_path = tmp_config_dir / "config.toml"
        generate_default_config(config_path)

        content = config_path.read_text(encoding="utf-8")
        comment_lines = [line for line in content.splitlines() if line.strip().startswith("#")]
        assert len(comment_lines) > 0, "Generated config should contain comments"

    def test_generated_values_match_defaults(self, tmp_config_dir: Path):
        """生成された値がデフォルト値と一致すること。"""
        config_path = tmp_config_dir / "config.toml"
        generate_default_config(config_path)

        with open(config_path, "rb") as f:
            parsed = tomllib.load(f)

        assert parsed["general"]["persona_frozen"] is False
        assert parsed["gui"]["window_width"] == 400
        assert parsed["conversation"]["max_tokens"] == 1024
        assert parsed["api"]["retry_backoff_base"] == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# FR-1.3: 不正な値のフォールバック
# ---------------------------------------------------------------------------


class TestLoadConfigInvalidValues:
    """FR-1.3: 不正な値のフォールバック動作を検証する。"""

    def test_invalid_int_field_falls_back_to_default(
        self, tmp_config_dir: Path, caplog: pytest.LogCaptureFixture
    ):
        """int フィールドに文字列が入っている場合、デフォルト値にフォールバックすること。"""
        config_path = tmp_config_dir / "config.toml"
        config_path.write_text(
            '[gui]\nwindow_width = "not_an_int"\n',
            encoding="utf-8",
        )
        with caplog.at_level(logging.WARNING):
            cfg = load_config(config_path)

        assert cfg.gui.window_width == GuiConfig().window_width
        assert len(caplog.records) > 0

    def test_opacity_out_of_range_falls_back_to_default(
        self, tmp_config_dir: Path, caplog: pytest.LogCaptureFixture
    ):
        """opacity が範囲外（1.5）の場合、デフォルト値にフォールバックすること。"""
        config_path = tmp_config_dir / "config.toml"
        config_path.write_text(
            "[gui]\nopacity = 1.5\n",
            encoding="utf-8",
        )
        with caplog.at_level(logging.WARNING):
            cfg = load_config(config_path)

        assert cfg.gui.opacity == pytest.approx(GuiConfig().opacity)
        assert len(caplog.records) > 0

    def test_opacity_negative_falls_back_to_default(
        self, tmp_config_dir: Path, caplog: pytest.LogCaptureFixture
    ):
        """opacity が負の値の場合、デフォルト値にフォールバックすること。"""
        config_path = tmp_config_dir / "config.toml"
        config_path.write_text(
            "[gui]\nopacity = -0.1\n",
            encoding="utf-8",
        )
        with caplog.at_level(logging.WARNING):
            cfg = load_config(config_path)

        assert cfg.gui.opacity == pytest.approx(GuiConfig().opacity)

    def test_invalid_bool_field_falls_back_to_default(
        self, tmp_config_dir: Path, caplog: pytest.LogCaptureFixture
    ):
        """bool フィールドに数値が入っている場合、デフォルト値にフォールバックすること。"""
        config_path = tmp_config_dir / "config.toml"
        config_path.write_text(
            '[general]\npersona_frozen = "yes"\n',
            encoding="utf-8",
        )
        with caplog.at_level(logging.WARNING):
            cfg = load_config(config_path)

        assert cfg.general.persona_frozen == GeneralConfig().persona_frozen

    def test_warning_is_logged_for_invalid_value(
        self, tmp_config_dir: Path, caplog: pytest.LogCaptureFixture
    ):
        """不正な値に対して logging.warning が呼ばれること。"""
        config_path = tmp_config_dir / "config.toml"
        config_path.write_text(
            '[gui]\nwindow_width = "bad"\n',
            encoding="utf-8",
        )
        with caplog.at_level(logging.WARNING):
            load_config(config_path)

        warning_records = [r for r in caplog.records if r.levelno >= logging.WARNING]
        assert len(warning_records) > 0

    def test_valid_fields_are_not_affected_by_one_invalid(
        self, tmp_config_dir: Path, caplog: pytest.LogCaptureFixture
    ):
        """一部フィールドが不正でも、他のフィールドは正常に読み込まれること。"""
        config_path = tmp_config_dir / "config.toml"
        config_path.write_text(
            '[gui]\nwindow_width = "bad"\nwindow_height = 999\n',
            encoding="utf-8",
        )
        with caplog.at_level(logging.WARNING):
            cfg = load_config(config_path)

        assert cfg.gui.window_width == GuiConfig().window_width  # フォールバック
        assert cfg.gui.window_height == 999  # 正常値はそのまま

    def test_temperature_out_of_range_falls_back(
        self, tmp_config_dir: Path, caplog: pytest.LogCaptureFixture
    ):
        """conversation.temperature が範囲外の場合、デフォルト値にフォールバックすること。"""
        config_path = tmp_config_dir / "config.toml"
        config_path.write_text(
            "[conversation]\ntemperature = 2.5\n",
            encoding="utf-8",
        )
        with caplog.at_level(logging.WARNING):
            cfg = load_config(config_path)

        assert cfg.conversation.temperature == pytest.approx(ConversationConfig().temperature)

    def test_max_tokens_negative_falls_back(
        self, tmp_config_dir: Path, caplog: pytest.LogCaptureFixture
    ):
        """max_tokens が負の値の場合、デフォルト値にフォールバックすること。"""
        config_path = tmp_config_dir / "config.toml"
        config_path.write_text(
            "[conversation]\nmax_tokens = -100\n",
            encoding="utf-8",
        )
        with caplog.at_level(logging.WARNING):
            cfg = load_config(config_path)

        assert cfg.conversation.max_tokens == ConversationConfig().max_tokens


# ---------------------------------------------------------------------------
# get_max_tokens のテスト
# ---------------------------------------------------------------------------


class TestGetMaxTokens:
    """get_max_tokens の全 purpose を検証する。"""

    def test_conversation_purpose(self):
        """purpose='conversation' が config.conversation.max_tokens を返すこと。"""
        cfg = AppConfig()
        assert get_max_tokens(cfg, "conversation") == cfg.conversation.max_tokens

    def test_wizard_generate_purpose(self):
        """purpose='wizard_generate' が 2048 を返すこと。"""
        cfg = AppConfig()
        assert get_max_tokens(cfg, "wizard_generate") == 2048

    def test_wizard_preview_purpose(self):
        """purpose='wizard_preview' が 1024 を返すこと。"""
        cfg = AppConfig()
        assert get_max_tokens(cfg, "wizard_preview") == 1024

    def test_memory_worker_purpose(self):
        """purpose='memory_worker' が 800 を返すこと。"""
        cfg = AppConfig()
        assert get_max_tokens(cfg, "memory_worker") == 800

    def test_poke_purpose(self):
        """purpose='poke' が 256 を返すこと。"""
        cfg = AppConfig()
        assert get_max_tokens(cfg, "poke") == 256

    def test_conversation_reflects_custom_max_tokens(self, tmp_config_dir: Path):
        """conversation.max_tokens をカスタム値に設定した場合、それが返ること。"""
        config_path = tmp_config_dir / "config.toml"
        config_path.write_text(
            "[conversation]\nmax_tokens = 512\n",
            encoding="utf-8",
        )
        cfg = load_config(config_path)
        assert get_max_tokens(cfg, "conversation") == 512

    def test_unknown_purpose_raises_value_error(self):
        """未知の purpose に対して ValueError が発生すること。"""
        cfg = AppConfig()
        with pytest.raises(ValueError, match="Unknown purpose"):
            get_max_tokens(cfg, "unknown_purpose")
