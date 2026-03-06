"""E7: エラーハンドリング統合テスト (T-26).

対応 FR:
    FR-1.6: ANTHROPIC_API_KEY 未設定エラー (EM-001)
    FR-7.1: API 呼び出し失敗時のリトライ後エラーメッセージ (EM-006)
    FR-7.2: 認証エラー（401/403）の通知 (EM-007)
    FR-7.4: persona_core.md 読み込み失敗時のエラー (EM-003, EM-004)
    FR-7.5: シャットダウン中サマリー生成失敗時のログ (EM-009)
    FR-4.8: ペルソナ読み込み3段階エラーハンドリング

テスト方針:
    - エラー系の統合テスト（コンポーネント間のエラー伝播を検証）
    - LLM モック、実ファイル I/O + 実 DB
"""

import time
from pathlib import Path
from unittest.mock import patch

import pytest

from kage_shiki.core.errors import (
    ERROR_MESSAGES,
    ErrorSeverity,
    format_error_message,
    format_log_message,
    get_severity,
)
from kage_shiki.memory.db import save_observation
from kage_shiki.memory.memory_worker import MemoryWorker
from kage_shiki.persona.persona_system import (
    PersonaFrozenError,
    PersonaLoadError,
    PersonaSystem,
)

# ---------------------------------------------------------------------------
# E7-1: エラーメッセージ定義の整合性
# ---------------------------------------------------------------------------


class TestErrorMessageDefinitions:
    """EM-001〜EM-011 の定義と API の統合テスト."""

    def test_all_error_ids_defined(self):
        """EM-001〜EM-011 が全て定義されていること."""
        expected_ids = [f"EM-{i:03d}" for i in range(1, 12)]
        for eid in expected_ids:
            assert eid in ERROR_MESSAGES, f"{eid} が未定義"

    def test_format_error_message_with_variables(self):
        """テンプレート変数が正しく解決されること."""
        msg = format_error_message(
            "EM-003",
            persona_path="/data/persona_core.md",
            error_detail="FileNotFoundError",
        )
        assert "/data/persona_core.md" in msg
        assert "FileNotFoundError" in msg

    def test_format_error_message_missing_variable_fallback(self):
        """未定義のテンプレート変数が空文字にフォールバックすること (D-6 Section 5.2.2)."""
        # EM-003 は persona_path, error_detail を期待するが、渡さない
        msg = format_error_message("EM-003")
        # 変数部分が空文字列に置換され、例外は発生しない
        assert "人格ファイルの読み込みに失敗しました" in msg

    def test_format_log_message_with_variables(self):
        """ログテンプレートの変数が解決されること."""
        log = format_log_message(
            "EM-006",
            max_retries="3",
            error="APIStatusError",
        )
        assert "3" in log
        assert "APIStatusError" in log

    def test_severity_mapping(self):
        """各 EM の重篤度が仕様通りであること."""
        critical_ids = {"EM-001", "EM-003", "EM-004", "EM-007"}
        warning_ids = {"EM-002", "EM-005", "EM-006", "EM-008", "EM-009", "EM-010"}
        info_ids = {"EM-011"}

        for eid in critical_ids:
            assert get_severity(eid) == ErrorSeverity.CRITICAL, f"{eid}"
        for eid in warning_ids:
            assert get_severity(eid) == ErrorSeverity.WARNING, f"{eid}"
        for eid in info_ids:
            assert get_severity(eid) == ErrorSeverity.INFO, f"{eid}"

    def test_unknown_error_id_raises_key_error(self):
        """未定義のエラー ID で KeyError が発生すること."""
        with pytest.raises(KeyError):
            format_error_message("EM-999")

        with pytest.raises(KeyError):
            get_severity("EM-999")


# ---------------------------------------------------------------------------
# E7-2: ペルソナ読み込みエラーハンドリング
# ---------------------------------------------------------------------------


class TestPersonaLoadErrorHandling:
    """ペルソナファイル読み込みの3段階エラーハンドリング (FR-4.8)."""

    def test_persona_file_not_found_returns_none(self, tmp_path: Path):
        """persona_core.md が存在しない場合に None が返ること (ウィザード起動フラグ)."""
        system = PersonaSystem()
        nonexistent = tmp_path / "nonexistent.md"

        result = system.load_persona_core(nonexistent)
        assert result is None

    def test_persona_file_missing_required_fields(self, tmp_path: Path):
        """必須フィールドが欠損した persona_core.md で PersonaLoadError が発生すること."""
        system = PersonaSystem()
        broken_md = tmp_path / "persona_core.md"
        # C1（名前）のみの不完全ファイル
        broken_md.write_text(
            "# テスト\n\n## C1: 名前\n\nテスト太郎\n",
            encoding="utf-8",
        )

        with pytest.raises(PersonaLoadError):
            system.load_persona_core(broken_md)

    def test_persona_frozen_prevents_modification(self, persona_data_dir: Path):
        """凍結済みペルソナへの変更が PersonaFrozenError を発生すること."""
        system = PersonaSystem()
        persona_path = persona_data_dir / "persona_core.md"
        persona_core = system.load_persona_core(persona_path)

        # freeze_and_save で凍結
        system.freeze_and_save(persona_path, persona_core)
        frozen_core = system.load_persona_core(persona_path)

        # 凍結済み PersonaCore への save_persona_core は拒否される
        with pytest.raises(PersonaFrozenError):
            system.save_persona_core(persona_path, frozen_core)

    def test_persona_load_and_reload_consistency(self, persona_data_dir: Path):
        """保存→再読込でフィールド値が一致すること."""
        from dataclasses import replace

        system = PersonaSystem()
        persona_path = persona_data_dir / "persona_core.md"

        original = system.load_persona_core(persona_path)
        # 凍結解除した状態で保存テスト
        unfrozen = replace(
            original,
            metadata={**original.metadata, "凍結状態": "unfrozen"},
        )
        system.save_persona_core(persona_path, unfrozen)
        reloaded = system.load_persona_core(persona_path)

        assert reloaded.c1_name == original.c1_name
        assert reloaded.c4_personality_core == original.c4_personality_core
        assert reloaded.c6_speech_pattern == original.c6_speech_pattern


# ---------------------------------------------------------------------------
# E7-3: シャットダウン時サマリーエラー
# ---------------------------------------------------------------------------


class TestShutdownSummaryErrorHandling:
    """シャットダウン時サマリー生成のエラーハンドリング (FR-7.5, EM-009)."""

    def test_sync_summary_api_error_returns_none(
        self, db_conn, mock_llm_client,
    ):
        """API エラー時に generate_daily_summary_sync が None を返すこと."""
        from datetime import date
        today = date.today().isoformat()
        save_observation(db_conn, "テスト会話", "user", time.time())

        mock_llm_client.send_message_for_purpose.side_effect = RuntimeError(
            "Connection timeout",
        )

        worker = MemoryWorker(db_conn, mock_llm_client)
        result = worker.generate_daily_summary_sync(today)

        assert result is None

    def test_sync_summary_db_error_returns_none(
        self, db_conn, mock_llm_client,
    ):
        """DB エラー時に generate_daily_summary_sync が None を返すこと."""
        from datetime import date
        today = date.today().isoformat()
        save_observation(db_conn, "テスト会話", "user", time.time())

        mock_llm_client.send_message_for_purpose.return_value = "サマリー"

        # save_day_summary をモックして DB エラーを発生させる
        with patch(
            "kage_shiki.memory.memory_worker.save_day_summary",
            side_effect=Exception("DB write error"),
        ):
            worker = MemoryWorker(db_conn, mock_llm_client)
            result = worker.generate_daily_summary_sync(today)

        assert result is None


# ---------------------------------------------------------------------------
# E7-4: AgentCore のエラー耐性
# ---------------------------------------------------------------------------


class TestAgentCoreErrorResilience:
    """AgentCore がエラー発生時も応答を返し続けるテスト."""

    def test_fts5_error_does_not_block_response(
        self, db_conn, mock_llm_client, integration_config, persona_data_dir,
    ):
        """FTS5 検索失敗時も LLM 呼び出しと応答返却が継続すること."""
        from kage_shiki.agent.agent_core import AgentCore, PromptBuilder
        from kage_shiki.persona.persona_system import PersonaSystem

        from .conftest import SAMPLE_PERSONA_CORE, SAMPLE_STYLE_SAMPLES

        persona_system = PersonaSystem()
        prompt_builder = PromptBuilder(
            persona_core=SAMPLE_PERSONA_CORE.to_markdown(),
            style_samples=SAMPLE_STYLE_SAMPLES,
            human_block="",
        )
        agent = AgentCore(
            config=integration_config,
            db_conn=db_conn,
            llm_client=mock_llm_client,
            persona_system=persona_system,
            prompt_builder=prompt_builder,
            data_dir=persona_data_dir,
        )
        mock_llm_client.send_message_for_purpose.return_value = "挨拶"
        agent.generate_session_start_message()

        # FTS5 検索をモックしてエラーを発生させる
        mock_llm_client.send_message_for_purpose.return_value = "元気だよ！"
        with patch(
            "kage_shiki.agent.agent_core.search_observations_fts",
            side_effect=Exception("FTS5 error"),
        ):
            response = agent.process_turn("こんにちは")

        # エラーが起きても応答は返る
        assert response == "元気だよ！"

    def test_observation_write_error_does_not_block_response(
        self, db_conn, mock_llm_client, integration_config, persona_data_dir,
    ):
        """observations 書込失敗時も応答が返却されること."""
        from kage_shiki.agent.agent_core import AgentCore, PromptBuilder
        from kage_shiki.persona.persona_system import PersonaSystem

        from .conftest import SAMPLE_PERSONA_CORE, SAMPLE_STYLE_SAMPLES

        persona_system = PersonaSystem()
        prompt_builder = PromptBuilder(
            persona_core=SAMPLE_PERSONA_CORE.to_markdown(),
            style_samples=SAMPLE_STYLE_SAMPLES,
            human_block="",
        )
        agent = AgentCore(
            config=integration_config,
            db_conn=db_conn,
            llm_client=mock_llm_client,
            persona_system=persona_system,
            prompt_builder=prompt_builder,
            data_dir=persona_data_dir,
        )
        mock_llm_client.send_message_for_purpose.return_value = "挨拶"
        agent.generate_session_start_message()

        # save_observation をモックしてエラーを発生させる
        mock_llm_client.send_message_for_purpose.return_value = "大丈夫だよ！"
        with patch(
            "kage_shiki.agent.agent_core.save_observation",
            side_effect=Exception("DB locked"),
        ):
            response = agent.process_turn("テスト")

        assert response == "大丈夫だよ！"
        # ターンは記録されていること
        assert agent.session_context.message_count == 1


# ---------------------------------------------------------------------------
# E7-5: エラーメッセージとコンポーネントの統合
# ---------------------------------------------------------------------------


class TestErrorMessageIntegration:
    """エラーメッセージがコンポーネントのエラーシナリオと整合するテスト."""

    def test_em001_api_key_message_structure(self):
        """EM-001 のメッセージに設定方法の案内が含まれること."""
        msg = format_error_message("EM-001")
        assert "ANTHROPIC_API_KEY" in msg
        assert "設定方法" in msg
        assert "README.md" in msg

    def test_em003_persona_path_reflected(self):
        """EM-003 のメッセージにパスが反映されること."""
        msg = format_error_message(
            "EM-003",
            persona_path="C:/data/persona_core.md",
            error_detail="File not found",
        )
        assert "C:/data/persona_core.md" in msg
        assert "File not found" in msg
        assert "ウィザードを起動しますか" in msg

    def test_em006_name_prefix_reflected(self):
        """EM-006 のメッセージに名前プレフィクスが反映されること."""
        msg = format_error_message("EM-006", name_prefix="テスト花子")
        assert "テスト花子" in msg
        assert "うまく考えられなかった" in msg

    def test_em007_authentication_error_message(self):
        """EM-007 のメッセージに API キー確認の案内があること."""
        msg = format_error_message("EM-007")
        assert "API キー" in msg
        assert "ANTHROPIC_API_KEY" in msg

    def test_em009_log_message_structure(self):
        """EM-009 のログメッセージにリトライ情報が含まれること."""
        log = format_log_message("EM-009", error="TimeoutError")
        assert "TimeoutError" in log
        assert "retry" in log.lower() or "Will retry" in log

    def test_em010_wizard_error_message(self):
        """EM-010 のメッセージに再試行の案内があること."""
        msg = format_error_message("EM-010")
        assert "もう一度試しますか" in msg
        assert "ANTHROPIC_API_KEY" in msg

    def test_em011_manual_edit_detection_message(self):
        """EM-011 のメッセージに再凍結の案内があること."""
        msg = format_error_message("EM-011")
        assert "再凍結" in msg
        assert "変更されています" in msg
