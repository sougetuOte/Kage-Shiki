"""E6: config.toml 設定値反映の統合テスト (T-26).

対応 FR:
    FR-1.1: config.toml を読み込み、全設定値をアプリケーションに反映
    FR-1.2: config.toml が存在しない場合、デフォルト値で config.toml を生成
    FR-1.3: config.toml の値が不正な場合、デフォルト値にフォールバック

テスト方針:
    - config.toml → load_config → AppConfig → get_model/get_temperature/get_max_tokens
      の統合的なデータフローを検証
    - 実ファイル I/O を使用（tmp_path）
"""

from pathlib import Path

import pytest

from kage_shiki.core.config import (
    _MAX_TOKENS_MAP,
    _PURPOSE_MODEL_SLOTS,
    _PURPOSE_TEMPERATURES,
    VALID_PURPOSES,
    AppConfig,
    generate_default_config,
    get_max_tokens,
    get_model,
    get_temperature,
    load_config,
)

# ---------------------------------------------------------------------------
# E6-1: config.toml → load_config → AppConfig 変換
# ---------------------------------------------------------------------------


class TestConfigLoadReflection:
    """config.toml ファイルの読み書き統合テスト."""

    def test_generate_and_load_default_config(self, tmp_path: Path):
        """デフォルト config.toml 生成→再読込でデフォルト値が復元されること."""
        config_path = tmp_path / "config.toml"
        generate_default_config(config_path)

        assert config_path.exists()

        loaded = load_config(config_path)
        default = AppConfig()

        assert loaded.general.persona_frozen == default.general.persona_frozen
        assert loaded.models.conversation == default.models.conversation
        assert loaded.conversation.temperature == default.conversation.temperature
        assert loaded.conversation.max_tokens == default.conversation.max_tokens
        assert loaded.memory.warm_days == default.memory.warm_days
        assert loaded.memory.cold_top_k == default.memory.cold_top_k
        assert loaded.memory.consistency_interval == default.memory.consistency_interval
        assert loaded.api.max_retries == default.api.max_retries
        assert loaded.wizard.blank_freeze_threshold == default.wizard.blank_freeze_threshold

    def test_load_config_generates_file_when_missing(self, tmp_path: Path):
        """config.toml 不在時にデフォルトファイルが生成されること (FR-1.2)."""
        config_path = tmp_path / "config.toml"
        assert not config_path.exists()

        loaded = load_config(config_path)

        assert config_path.exists()
        assert loaded.conversation.temperature == AppConfig().conversation.temperature

    def test_custom_values_reflected(self, tmp_path: Path):
        """カスタム値が正しく反映されること (FR-1.1)."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(
            '[conversation]\n'
            'temperature = 0.5\n'
            'max_tokens = 2048\n'
            '\n'
            '[memory]\n'
            'warm_days = 10\n'
            'cold_top_k = 3\n'
            'consistency_interval = 5\n'
            '\n'
            '[models]\n'
            'conversation = "claude-sonnet-4-20250514"\n'
            'wizard = "claude-sonnet-4-20250514"\n',
            encoding="utf-8",
        )

        loaded = load_config(config_path)

        assert loaded.conversation.temperature == 0.5
        assert loaded.conversation.max_tokens == 2048
        assert loaded.memory.warm_days == 10
        assert loaded.memory.cold_top_k == 3
        assert loaded.memory.consistency_interval == 5
        assert loaded.models.conversation == "claude-sonnet-4-20250514"
        assert loaded.models.wizard == "claude-sonnet-4-20250514"

    def test_invalid_values_fallback_to_default(self, tmp_path: Path):
        """不正な値がデフォルト値にフォールバックすること (FR-1.3)."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(
            '[conversation]\n'
            'temperature = 5.0\n'  # 上限 2.0 を超過
            'max_tokens = -1\n'    # 下限 1 を下回る
            '\n'
            '[memory]\n'
            'warm_days = "not_a_number"\n'  # 型不正
            ,
            encoding="utf-8",
        )

        loaded = load_config(config_path)
        default = AppConfig()

        assert loaded.conversation.temperature == default.conversation.temperature
        assert loaded.conversation.max_tokens == default.conversation.max_tokens
        assert loaded.memory.warm_days == default.memory.warm_days

    def test_partial_config_fills_defaults(self, tmp_path: Path):
        """一部セクションのみの config でも他はデフォルト値になること."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(
            '[general]\npersona_frozen = true\n',
            encoding="utf-8",
        )

        loaded = load_config(config_path)
        default = AppConfig()

        assert loaded.general.persona_frozen is True
        assert loaded.conversation.temperature == default.conversation.temperature
        assert loaded.models.conversation == default.models.conversation


# ---------------------------------------------------------------------------
# E6-2: 用途別パラメータ解決（config → LLM パラメータ）
# ---------------------------------------------------------------------------


class TestPurposeParameterResolution:
    """config の設定値が用途別パラメータに正しく反映されるテスト (D-15)."""

    def test_conversation_max_tokens_from_config(self):
        """conversation の max_tokens が config.conversation.max_tokens を使うこと."""
        config = AppConfig()
        config.conversation.max_tokens = 512

        assert get_max_tokens(config, "conversation") == 512

    def test_non_conversation_max_tokens_fixed(self):
        """conversation 以外の max_tokens は config に依存しない固定値であること."""
        config = AppConfig()
        for purpose, expected in _MAX_TOKENS_MAP.items():
            assert get_max_tokens(config, purpose) == expected

    def test_temperature_override_purposes(self):
        """固定 temperature を持つ purpose はオーバーライド値を返すこと."""
        config = AppConfig()
        config.conversation.temperature = 0.5  # デフォルトと異なる値

        for purpose, override in _PURPOSE_TEMPERATURES.items():
            temp = get_temperature(config, purpose)
            if override is not None:
                assert temp == override, f"{purpose}: expected {override}, got {temp}"
            else:
                assert temp == 0.5, f"{purpose}: expected config value 0.5, got {temp}"

    def test_model_slot_mapping(self):
        """各 purpose が正しいモデルスロットに解決されること."""
        config = AppConfig()
        config.models.conversation = "model-conv"
        config.models.wizard = "model-wiz"
        config.models.memory_worker = "model-mem"
        config.models.utility = "model-util"

        expected_map = {
            "conversation": "model-conv",
            "poke": "model-conv",
            "wizard_preview": "model-conv",
            "wizard_generate": "model-wiz",
            "wizard_association": "model-wiz",
            "memory_worker": "model-mem",
            "memory_summary": "model-mem",
            "human_block_update": "model-util",
        }
        for purpose, expected_model in expected_map.items():
            assert get_model(config, purpose) == expected_model, \
                f"{purpose}: expected {expected_model}"

    def test_unknown_purpose_raises_value_error(self):
        """未知の purpose で ValueError が発生すること."""
        config = AppConfig()

        with pytest.raises(ValueError, match="Unknown purpose"):
            get_max_tokens(config, "unknown_purpose")

        with pytest.raises(ValueError, match="Unknown purpose"):
            get_temperature(config, "unknown_purpose")

        with pytest.raises(ValueError, match="Unknown purpose"):
            get_model(config, "unknown_purpose")

    def test_valid_purposes_complete(self):
        """VALID_PURPOSES が全ての用途マップキーと整合していること."""
        assert set(_PURPOSE_MODEL_SLOTS.keys()) == VALID_PURPOSES
        assert set(_PURPOSE_TEMPERATURES.keys()) == VALID_PURPOSES
        # conversation 以外は _MAX_TOKENS_MAP にある
        non_conv = VALID_PURPOSES - {"conversation"}
        assert non_conv == set(_MAX_TOKENS_MAP.keys())


# ---------------------------------------------------------------------------
# E6-3: config → AgentCore 統合
# ---------------------------------------------------------------------------


class TestConfigToAgentCoreIntegration:
    """config の設定値が AgentCore の動作に反映されるテスト."""

    def test_consistency_interval_from_config(
        self, db_conn, mock_llm_client, persona_data_dir,
    ):
        """config.memory.consistency_interval が AgentCore に反映されること."""
        from kage_shiki.agent.agent_core import AgentCore, PromptBuilder

        from .conftest import SAMPLE_PERSONA_CORE, SAMPLE_STYLE_SAMPLES

        config = AppConfig()
        config.memory.consistency_interval = 2
        config.general.data_dir = str(persona_data_dir)

        persona_system = __import__(
            "kage_shiki.persona.persona_system", fromlist=["PersonaSystem"],
        ).PersonaSystem()
        prompt_builder = PromptBuilder(
            persona_core=SAMPLE_PERSONA_CORE.to_markdown(),
            style_samples=SAMPLE_STYLE_SAMPLES,
            human_block="",
        )
        agent = AgentCore(
            config=config,
            db_conn=db_conn,
            llm_client=mock_llm_client,
            persona_system=persona_system,
            prompt_builder=prompt_builder,
            data_dir=persona_data_dir,
        )
        mock_llm_client.send_message_for_purpose.return_value = "応答"
        agent.generate_session_start_message()

        # consistency_check_active を監視
        build_calls = []
        original_build = prompt_builder.build_system_prompt

        def capture_build(**kwargs):
            build_calls.append(kwargs.get("consistency_check_active", False))
            return original_build(**kwargs)

        prompt_builder.build_system_prompt = capture_build

        for i in range(4):
            agent.process_turn(f"入力{i}")

        # interval=2 なので 2, 4 ターン目で active
        assert build_calls == [False, True, False, True]

    def test_cold_top_k_limits_search_results(self, db_conn, integration_config):
        """config.memory.cold_top_k が FTS5 検索結果の上限に反映されること."""
        import time

        from kage_shiki.memory.db import save_observation, search_observations_fts

        integration_config.memory.cold_top_k = 2

        for i in range(5):
            save_observation(
                db_conn, f"プログラミング言語の話題{i}", "user", time.time() + i,
            )

        results = search_observations_fts(
            db_conn, "プログラミング",
            top_k=integration_config.memory.cold_top_k,
        )
        assert len(results) <= 2
