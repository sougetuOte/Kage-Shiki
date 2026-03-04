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
    VALID_PURPOSES,
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
    _is_valid_type,
    generate_default_config,
    get_max_tokens,
    get_model,
    get_temperature,
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

    def test_general_config_defaults(self) -> None:
        """GeneralConfig のデフォルト値が仕様通りであること。"""
        cfg = GeneralConfig()
        assert cfg.persona_frozen is False
        assert cfg.data_dir == "./data"

    def test_models_config_defaults(self) -> None:
        """ModelsConfig のデフォルト値が仕様通りであること。"""
        cfg = ModelsConfig()
        assert cfg.conversation == "claude-haiku-4-5-20251001"
        assert cfg.memory_worker == "claude-haiku-4-5-20251001"
        assert cfg.utility == "claude-haiku-4-5-20251001"
        assert cfg.wizard == "claude-haiku-4-5-20251001"

    def test_wizard_config_defaults(self) -> None:
        """WizardConfig のデフォルト値が仕様通りであること。"""
        cfg = WizardConfig()
        assert cfg.association_count == 5
        assert cfg.temperature == pytest.approx(0.9)
        assert cfg.candidate_count == 3
        assert cfg.blank_freeze_threshold == 20

    def test_conversation_config_defaults(self) -> None:
        """ConversationConfig のデフォルト値が仕様通りであること。"""
        cfg = ConversationConfig()
        assert cfg.temperature == pytest.approx(0.7)
        assert cfg.max_tokens == 1024

    def test_gui_config_defaults(self) -> None:
        """GuiConfig のデフォルト値が仕様通りであること。"""
        cfg = GuiConfig()
        assert cfg.window_width == 400
        assert cfg.window_height == 300
        assert cfg.opacity == pytest.approx(0.95)
        assert cfg.topmost is True
        assert cfg.font_size == 14
        assert cfg.font_family == ""

    def test_memory_config_defaults(self) -> None:
        """MemoryConfig のデフォルト値が仕様通りであること。"""
        cfg = MemoryConfig()
        assert cfg.warm_days == 5
        assert cfg.cold_top_k == 5
        assert cfg.consistency_interval == 15

    def test_api_config_defaults(self) -> None:
        """ApiConfig のデフォルト値が仕様通りであること。"""
        cfg = ApiConfig()
        assert cfg.max_retries == 3
        assert cfg.retry_backoff_base == pytest.approx(2.0)
        assert cfg.timeout == 30

    def test_tray_config_defaults(self) -> None:
        """TrayConfig のデフォルト値が仕様通りであること。"""
        cfg = TrayConfig()
        assert cfg.minimize_to_tray is True

    def test_logging_config_defaults(self) -> None:
        """LoggingConfig のデフォルト値が仕様通りであること。"""
        cfg = LoggingConfig()
        assert cfg.level == "INFO"
        assert cfg.file_level == "DEBUG"
        assert cfg.max_bytes == 5242880
        assert cfg.backup_count == 3

    def test_app_config_defaults(self) -> None:
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

    def test_load_config_returns_app_config(self, valid_config_toml: Path) -> None:
        """load_config が AppConfig インスタンスを返すこと。"""
        cfg = load_config(valid_config_toml)
        assert isinstance(cfg, AppConfig)

    def test_load_config_general_section(self, valid_config_toml: Path) -> None:
        """[general] セクションが正しく読み込まれること。"""
        cfg = load_config(valid_config_toml)
        assert cfg.general.persona_frozen is True
        assert cfg.general.data_dir == "./custom_data"

    def test_load_config_models_section(self, valid_config_toml: Path) -> None:
        """[models] セクションが正しく読み込まれること。"""
        cfg = load_config(valid_config_toml)
        assert cfg.models.conversation == "claude-haiku-4-5-20251001"

    def test_load_config_wizard_section(self, valid_config_toml: Path) -> None:
        """[wizard] セクションが正しく読み込まれること。"""
        cfg = load_config(valid_config_toml)
        assert cfg.wizard.association_count == 7
        assert cfg.wizard.temperature == pytest.approx(0.8)
        assert cfg.wizard.candidate_count == 4
        assert cfg.wizard.blank_freeze_threshold == 25

    def test_load_config_conversation_section(self, valid_config_toml: Path) -> None:
        """[conversation] セクションが正しく読み込まれること。"""
        cfg = load_config(valid_config_toml)
        assert cfg.conversation.temperature == pytest.approx(0.6)
        assert cfg.conversation.max_tokens == 2048

    def test_load_config_gui_section(self, valid_config_toml: Path) -> None:
        """[gui] セクションが正しく読み込まれること。"""
        cfg = load_config(valid_config_toml)
        assert cfg.gui.window_width == 500
        assert cfg.gui.window_height == 400
        assert cfg.gui.opacity == pytest.approx(0.85)
        assert cfg.gui.topmost is False
        assert cfg.gui.font_size == 16
        assert cfg.gui.font_family == "Meiryo"

    def test_load_config_memory_section(self, valid_config_toml: Path) -> None:
        """[memory] セクションが正しく読み込まれること。"""
        cfg = load_config(valid_config_toml)
        assert cfg.memory.warm_days == 7
        assert cfg.memory.cold_top_k == 10
        assert cfg.memory.consistency_interval == 30

    def test_load_config_api_section(self, valid_config_toml: Path) -> None:
        """[api] セクションが正しく読み込まれること。"""
        cfg = load_config(valid_config_toml)
        assert cfg.api.max_retries == 5
        assert cfg.api.retry_backoff_base == pytest.approx(1.5)
        assert cfg.api.timeout == 60

    def test_load_config_tray_section(self, valid_config_toml: Path) -> None:
        """[tray] セクションが正しく読み込まれること。"""
        cfg = load_config(valid_config_toml)
        assert cfg.tray.minimize_to_tray is False

    def test_load_config_logging_section(self, valid_config_toml: Path) -> None:
        """[logging] セクションが正しく読み込まれること。"""
        cfg = load_config(valid_config_toml)
        assert cfg.logging.level == "DEBUG"
        assert cfg.logging.file_level == "INFO"
        assert cfg.logging.max_bytes == 1048576
        assert cfg.logging.backup_count == 5

    def test_load_config_ignores_unknown_keys(self, tmp_config_dir: Path) -> None:
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

    def test_load_config_creates_file_when_missing(self, tmp_config_dir: Path) -> None:
        """config.toml が存在しない場合、ファイルが生成されること。"""
        config_path = tmp_config_dir / "config.toml"
        assert not config_path.exists()

        load_config(config_path)

        assert config_path.exists()

    def test_load_config_returns_defaults_when_missing(self, tmp_config_dir: Path) -> None:
        """config.toml が存在しない場合、デフォルト値の AppConfig が返ること。"""
        config_path = tmp_config_dir / "config.toml"
        cfg = load_config(config_path)

        default = AppConfig()
        assert cfg.general.persona_frozen == default.general.persona_frozen
        assert cfg.general.data_dir == default.general.data_dir
        assert cfg.gui.window_width == default.gui.window_width
        assert cfg.conversation.max_tokens == default.conversation.max_tokens

    def test_generated_file_is_valid_toml(self, tmp_config_dir: Path) -> None:
        """生成された config.toml が有効な TOML であること。"""
        config_path = tmp_config_dir / "config.toml"
        load_config(config_path)

        with open(config_path, "rb") as f:
            parsed = tomllib.load(f)
        assert isinstance(parsed, dict)

    def test_generated_file_contains_all_sections(self, tmp_config_dir: Path) -> None:
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

    def test_generates_file(self, tmp_config_dir: Path) -> None:
        """ファイルが生成されること。"""
        config_path = tmp_config_dir / "config.toml"
        generate_default_config(config_path)
        assert config_path.exists()

    def test_generated_file_is_valid_toml(self, tmp_config_dir: Path) -> None:
        """生成ファイルが有効な TOML であること。"""
        config_path = tmp_config_dir / "config.toml"
        generate_default_config(config_path)

        with open(config_path, "rb") as f:
            parsed = tomllib.load(f)
        assert isinstance(parsed, dict)

    def test_generated_file_contains_all_sections(self, tmp_config_dir: Path) -> None:
        """全セクションが含まれること。"""
        config_path = tmp_config_dir / "config.toml"
        generate_default_config(config_path)

        content = config_path.read_text(encoding="utf-8")
        for section in [
            "[general]", "[models]", "[wizard]", "[conversation]",
            "[gui]", "[memory]", "[api]", "[tray]", "[logging]",
        ]:
            assert section in content

    def test_generated_file_contains_comments(self, tmp_config_dir: Path) -> None:
        """コメント（# で始まる行）が含まれること。"""
        config_path = tmp_config_dir / "config.toml"
        generate_default_config(config_path)

        content = config_path.read_text(encoding="utf-8")
        comment_lines = [line for line in content.splitlines() if line.strip().startswith("#")]
        assert len(comment_lines) > 0, "Generated config should contain comments"

    def test_generated_values_match_defaults(self, tmp_config_dir: Path) -> None:
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
    ) -> None:
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
    ) -> None:
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
    ) -> None:
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
    ) -> None:
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
    ) -> None:
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
    ) -> None:
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
    ) -> None:
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
    ) -> None:
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

    def test_conversation_purpose(self) -> None:
        """purpose='conversation' が config.conversation.max_tokens を返すこと。"""
        cfg = AppConfig()
        assert get_max_tokens(cfg, "conversation") == cfg.conversation.max_tokens

    def test_wizard_generate_purpose(self) -> None:
        """purpose='wizard_generate' が 2048 を返すこと。"""
        cfg = AppConfig()
        assert get_max_tokens(cfg, "wizard_generate") == 2048

    def test_wizard_preview_purpose(self) -> None:
        """purpose='wizard_preview' が 1024 を返すこと。"""
        cfg = AppConfig()
        assert get_max_tokens(cfg, "wizard_preview") == 1024

    def test_memory_worker_purpose(self) -> None:
        """purpose='memory_worker' が 800 を返すこと。"""
        cfg = AppConfig()
        assert get_max_tokens(cfg, "memory_worker") == 800

    def test_poke_purpose(self) -> None:
        """purpose='poke' が 256 を返すこと。"""
        cfg = AppConfig()
        assert get_max_tokens(cfg, "poke") == 256

    def test_conversation_reflects_custom_max_tokens(self, tmp_config_dir: Path) -> None:
        """conversation.max_tokens をカスタム値に設定した場合、それが返ること。"""
        config_path = tmp_config_dir / "config.toml"
        config_path.write_text(
            "[conversation]\nmax_tokens = 512\n",
            encoding="utf-8",
        )
        cfg = load_config(config_path)
        assert get_max_tokens(cfg, "conversation") == 512

    def test_wizard_association_purpose(self) -> None:
        """purpose='wizard_association' が 512 を返すこと。"""
        cfg = AppConfig()
        assert get_max_tokens(cfg, "wizard_association") == 512

    def test_memory_summary_purpose(self) -> None:
        """purpose='memory_summary' が 800 を返すこと。"""
        cfg = AppConfig()
        assert get_max_tokens(cfg, "memory_summary") == 800

    def test_human_block_update_purpose(self) -> None:
        """purpose='human_block_update' が 256 を返すこと。"""
        cfg = AppConfig()
        assert get_max_tokens(cfg, "human_block_update") == 256

    def test_unknown_purpose_raises_value_error(self) -> None:
        """未知の purpose に対して ValueError が発生すること。"""
        cfg = AppConfig()
        with pytest.raises(ValueError, match="Unknown purpose"):
            get_max_tokens(cfg, "unknown_purpose")


# ---------------------------------------------------------------------------
# get_temperature のテスト
# ---------------------------------------------------------------------------


class TestGetTemperature:
    """get_temperature の全 purpose を検証する。"""

    def test_conversation_uses_config_temperature(self) -> None:
        """purpose='conversation' が config.conversation.temperature を返すこと。"""
        cfg = AppConfig(conversation=ConversationConfig(temperature=0.5))
        assert get_temperature(cfg, "conversation") == pytest.approx(0.5)

    def test_wizard_generate_returns_fixed_temperature(self) -> None:
        """purpose='wizard_generate' が 0.9 を返すこと。"""
        cfg = AppConfig()
        assert get_temperature(cfg, "wizard_generate") == pytest.approx(0.9)

    def test_wizard_preview_uses_config_temperature(self) -> None:
        """purpose='wizard_preview' が config.conversation.temperature を返すこと。"""
        cfg = AppConfig(conversation=ConversationConfig(temperature=0.6))
        assert get_temperature(cfg, "wizard_preview") == pytest.approx(0.6)

    def test_wizard_association_returns_fixed_temperature(self) -> None:
        """purpose='wizard_association' が 0.9 を返すこと。"""
        cfg = AppConfig()
        assert get_temperature(cfg, "wizard_association") == pytest.approx(0.9)

    def test_memory_worker_returns_fixed_temperature(self) -> None:
        """purpose='memory_worker' が 0.3 を返すこと。"""
        cfg = AppConfig()
        assert get_temperature(cfg, "memory_worker") == pytest.approx(0.3)

    def test_memory_summary_returns_fixed_temperature(self) -> None:
        """purpose='memory_summary' が 0.3 を返すこと。"""
        cfg = AppConfig()
        assert get_temperature(cfg, "memory_summary") == pytest.approx(0.3)

    def test_human_block_update_returns_fixed_temperature(self) -> None:
        """purpose='human_block_update' が 0.3 を返すこと。"""
        cfg = AppConfig()
        assert get_temperature(cfg, "human_block_update") == pytest.approx(0.3)

    def test_poke_uses_config_temperature(self) -> None:
        """purpose='poke' が config.conversation.temperature を返すこと。"""
        cfg = AppConfig(conversation=ConversationConfig(temperature=0.8))
        assert get_temperature(cfg, "poke") == pytest.approx(0.8)

    def test_unknown_purpose_raises_value_error(self) -> None:
        """未知の purpose に対して ValueError が発生すること。"""
        cfg = AppConfig()
        with pytest.raises(ValueError, match="Unknown purpose"):
            get_temperature(cfg, "unknown_purpose")


# ---------------------------------------------------------------------------
# get_model のテスト
# ---------------------------------------------------------------------------


class TestGetModel:
    """get_model の全 purpose を検証する。"""

    def test_conversation_returns_conversation_model(self) -> None:
        """purpose='conversation' が models.conversation を返すこと。"""
        cfg = AppConfig()
        assert get_model(cfg, "conversation") == cfg.models.conversation

    def test_poke_returns_conversation_model(self) -> None:
        """purpose='poke' が models.conversation を返すこと。"""
        cfg = AppConfig()
        assert get_model(cfg, "poke") == cfg.models.conversation

    def test_wizard_preview_returns_conversation_model(self) -> None:
        """purpose='wizard_preview' が models.conversation を返すこと。"""
        cfg = AppConfig()
        assert get_model(cfg, "wizard_preview") == cfg.models.conversation

    def test_wizard_generate_returns_wizard_model(self) -> None:
        """purpose='wizard_generate' が models.wizard を返すこと。"""
        cfg = AppConfig()
        assert get_model(cfg, "wizard_generate") == cfg.models.wizard

    def test_wizard_association_returns_wizard_model(self) -> None:
        """purpose='wizard_association' が models.wizard を返すこと。"""
        cfg = AppConfig()
        assert get_model(cfg, "wizard_association") == cfg.models.wizard

    def test_memory_worker_returns_memory_worker_model(self) -> None:
        """purpose='memory_worker' が models.memory_worker を返すこと。"""
        cfg = AppConfig()
        assert get_model(cfg, "memory_worker") == cfg.models.memory_worker

    def test_memory_summary_returns_memory_worker_model(self) -> None:
        """purpose='memory_summary' が models.memory_worker を返すこと。"""
        cfg = AppConfig()
        assert get_model(cfg, "memory_summary") == cfg.models.memory_worker

    def test_human_block_update_returns_utility_model(self) -> None:
        """purpose='human_block_update' が models.utility を返すこと。"""
        cfg = AppConfig()
        assert get_model(cfg, "human_block_update") == cfg.models.utility

    def test_unknown_purpose_raises_value_error(self) -> None:
        """未知の purpose に対して ValueError が発生すること。"""
        cfg = AppConfig()
        with pytest.raises(ValueError, match="Unknown purpose"):
            get_model(cfg, "unknown_purpose")


# ---------------------------------------------------------------------------
# VALID_PURPOSES のテスト
# ---------------------------------------------------------------------------


class TestValidPurposes:
    """VALID_PURPOSES 定数の整合性を検証する。"""

    def test_contains_all_expected_purposes(self) -> None:
        """8つの purpose が全て含まれること。"""
        expected = {
            "conversation", "wizard_generate", "wizard_preview",
            "wizard_association", "memory_worker", "memory_summary",
            "human_block_update", "poke",
        }
        assert expected == VALID_PURPOSES


# ---------------------------------------------------------------------------
# _is_valid_type のテスト
# ---------------------------------------------------------------------------


class TestIsValidType:
    """_is_valid_type の型チェック動作を検証する。"""

    def test_int_value_matches_int_type(self) -> None:
        """int 値が int 型にマッチすること。"""
        assert _is_valid_type(42, int) is True

    def test_bool_value_does_not_match_int_type(self) -> None:
        """bool 値が int 型にマッチしないこと（サブクラス問題の防止）。"""
        assert _is_valid_type(True, int) is False

    def test_bool_value_matches_bool_type(self) -> None:
        """bool 値が bool 型にマッチすること。"""
        assert _is_valid_type(True, bool) is True

    def test_str_value_matches_str_type(self) -> None:
        """str 値が str 型にマッチすること。"""
        assert _is_valid_type("hello", str) is True

    def test_float_value_matches_float_type(self) -> None:
        """float 値が float 型にマッチすること。"""
        assert _is_valid_type(0.5, float) is True

    def test_str_value_does_not_match_int_type(self) -> None:
        """str 値が int 型にマッチしないこと。"""
        assert _is_valid_type("hello", int) is False
