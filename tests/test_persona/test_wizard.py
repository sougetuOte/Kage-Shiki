"""Tests for persona/wizard.py — WizardController (T-20).

対応 FR:
    FR-5.1: ウィザード方式によるキャラクター生成（方式 A のバックエンドロジック部分）
    FR-5.2: AI おまかせ方式（連想拡張 + 候補生成 + 選択）
    FR-5.7: 連想拡張パイプライン
    FR-5.8: 生成メタデータの記録

対応設計:
    D-5: ウィザードフロー設計
    D-12: ウィザード用モデルスロット
"""

import json
from unittest.mock import Mock

import pytest

from kage_shiki.agent.llm_client import LLMClient, LLMError
from kage_shiki.core.config import AppConfig
from kage_shiki.persona.persona_system import PersonaCore
from kage_shiki.persona.wizard import (
    WizardController,
    _dict_to_persona_core,
    _extract_json,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_llm() -> Mock:
    """LLMClient のモック."""
    return Mock(spec=LLMClient)


@pytest.fixture()
def config() -> AppConfig:
    """デフォルト AppConfig."""
    return AppConfig()


@pytest.fixture()
def controller(mock_llm: Mock, config: AppConfig) -> WizardController:
    """WizardController インスタンス."""
    return WizardController(mock_llm, config)


# ---------------------------------------------------------------------------
# _extract_json ヘルパー
# ---------------------------------------------------------------------------


class TestExtractJson:
    """_extract_json ヘルパーのテスト."""

    def test_plain_json_array(self) -> None:
        """プレーンな JSON 配列をパースできること."""
        result = _extract_json('["a", "b", "c"]')
        assert result == ["a", "b", "c"]

    def test_plain_json_object(self) -> None:
        """プレーンな JSON オブジェクトをパースできること."""
        result = _extract_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_markdown_code_block(self) -> None:
        """マークダウンコードブロック内の JSON をパースできること."""
        text = '```json\n["a", "b"]\n```'
        result = _extract_json(text)
        assert result == ["a", "b"]

    def test_markdown_code_block_no_lang(self) -> None:
        """言語指定なしのコードブロックをパースできること."""
        text = '```\n{"key": "val"}\n```'
        result = _extract_json(text)
        assert result == {"key": "val"}

    def test_invalid_json_raises_value_error(self) -> None:
        """不正な JSON で ValueError が発生すること."""
        with pytest.raises(ValueError, match="JSON パース失敗"):
            _extract_json("これはJSONではない")


# ---------------------------------------------------------------------------
# _dict_to_persona_core ヘルパー
# ---------------------------------------------------------------------------


class TestDictToPersonaCore:
    """_dict_to_persona_core ヘルパーのテスト."""

    def test_all_fields_mapped(self) -> None:
        """全 C1-C11 フィールドがマッピングされること."""
        d = {
            "c1_name": "テスト",
            "c2_first_person": "わたし",
            "c3_second_person": "あなた",
            "c4_personality_core": "好奇心旺盛",
            "c5_personality_axes": "明るい",
            "c6_speech_pattern": "丁寧語",
            "c7_catchphrase": "ふむふむ",
            "c8_age_impression": "高校生",
            "c9_values": "誠実",
            "c10_forbidden": "嘘",
            "c11_self_knowledge": "素直",
        }
        core = _dict_to_persona_core(d)
        assert core.c1_name == "テスト"
        assert core.c4_personality_core == "好奇心旺盛"
        assert core.c11_self_knowledge == "素直"

    def test_optional_fields_default_to_empty(self) -> None:
        """非必須フィールドが空文字列になること."""
        core = _dict_to_persona_core({
            "c1_name": "テスト",
            "c4_personality_core": "元気",
        })
        assert core.c1_name == "テスト"
        assert core.c2_first_person == ""
        assert core.c10_forbidden == ""

    def test_missing_c1_name_raises(self) -> None:
        """c1_name 欠損で ValueError が発生すること (FR-4.8(c))."""
        with pytest.raises(ValueError, match="c1_name"):
            _dict_to_persona_core({"c4_personality_core": "元気"})

    def test_missing_c4_personality_core_raises(self) -> None:
        """c4_personality_core 欠損で ValueError が発生すること (FR-4.8(c))."""
        with pytest.raises(ValueError, match="c4_personality_core"):
            _dict_to_persona_core({"c1_name": "テスト"})

    def test_empty_required_field_raises(self) -> None:
        """必須フィールドが空文字列で ValueError が発生すること."""
        with pytest.raises(ValueError, match="c1_name"):
            _dict_to_persona_core({"c1_name": "", "c4_personality_core": "元気"})


# ---------------------------------------------------------------------------
# W-1: 連想拡張 (FR-5.7)
# ---------------------------------------------------------------------------


class TestExpandAssociations:
    """expand_associations のテスト (W-1)."""

    def _mock_response(self, mock_llm: Mock, keywords: list[str]) -> None:
        mock_llm.send_message_for_purpose.return_value = json.dumps(
            keywords, ensure_ascii=False,
        )

    def test_returns_association_list(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """連想キーワードのリストが返ること."""
        self._mock_response(mock_llm, ["元気", "猫耳", "ツンデレ", "甘えん坊", "夜行性"])
        result = controller.expand_associations(["猫", "かわいい"])
        assert len(result) == 5
        assert "元気" in result

    def test_uses_wizard_association_purpose(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """purpose='wizard_association' で LLM を呼び出すこと (D-12)."""
        self._mock_response(mock_llm, ["a", "b", "c", "d", "e"])
        controller.expand_associations(["test"])
        call_kwargs = mock_llm.send_message_for_purpose.call_args.kwargs
        assert call_kwargs["purpose"] == "wizard_association"

    def test_keywords_in_user_message(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """ユーザーキーワードがプロンプトに含まれること."""
        self._mock_response(mock_llm, ["a", "b", "c", "d", "e"])
        controller.expand_associations(["猫", "優しい"])
        call_kwargs = mock_llm.send_message_for_purpose.call_args.kwargs
        user_msg = call_kwargs["messages"][0]["content"]
        assert "猫" in user_msg
        assert "優しい" in user_msg

    def test_association_count_in_prompt(
        self, controller: WizardController, mock_llm: Mock, config: AppConfig,
    ) -> None:
        """association_count がプロンプトに反映されること."""
        self._mock_response(mock_llm, ["a"] * config.wizard.association_count)
        controller.expand_associations(["test"])
        user_msg = mock_llm.send_message_for_purpose.call_args.kwargs[
            "messages"
        ][0]["content"]
        assert str(config.wizard.association_count) in user_msg

    def test_non_list_response_raises(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """リスト以外の応答で ValueError が発生すること."""
        mock_llm.send_message_for_purpose.return_value = '{"key": "value"}'
        with pytest.raises(ValueError, match="リストではありません"):
            controller.expand_associations(["test"])

    def test_llm_error_propagates(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """LLMError がそのまま伝播すること (EM-010)."""
        mock_llm.send_message_for_purpose.side_effect = LLMError("API失敗")
        with pytest.raises(LLMError):
            controller.expand_associations(["test"])


# ---------------------------------------------------------------------------
# W-2: 候補生成 (FR-5.2)
# ---------------------------------------------------------------------------


def _make_candidate_json(count: int, user_name: str = "") -> str:
    """テスト用の候補 JSON を生成する."""
    candidates = []
    for i in range(count):
        candidates.append({
            "c1_name": f"キャラ{i + 1}",
            "c2_first_person": "わたし",
            "c3_second_person": user_name or "あなた",
            "c4_personality_core": f"性格{i + 1}",
            "c5_personality_axes": "明るい",
            "c6_speech_pattern": "丁寧語",
            "c7_catchphrase": "ふむふむ",
            "c8_age_impression": "高校生",
            "c9_values": "誠実",
            "c10_forbidden": "嘘",
            "c11_self_knowledge": "素直",
        })
    return json.dumps({"candidates": candidates}, ensure_ascii=False)


class TestGenerateCandidates:
    """generate_candidates のテスト (W-2)."""

    def test_returns_persona_core_list(
        self, controller: WizardController, mock_llm: Mock, config: AppConfig,
    ) -> None:
        """PersonaCore のリストが返ること."""
        n = config.wizard.candidate_count
        mock_llm.send_message_for_purpose.return_value = _make_candidate_json(n)
        result = controller.generate_candidates(["元気", "猫耳"])
        assert len(result) == n
        assert all(isinstance(c, PersonaCore) for c in result)

    def test_all_c1_c11_fields_present(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """各候補が C1-C11 の全フィールドを持つこと."""
        mock_llm.send_message_for_purpose.return_value = _make_candidate_json(1)
        result = controller.generate_candidates(["test"])
        persona = result[0]
        assert persona.c1_name == "キャラ1"
        assert persona.c2_first_person == "わたし"
        assert persona.c4_personality_core == "性格1"
        assert persona.c11_self_knowledge == "素直"

    def test_uses_wizard_generate_purpose(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """purpose='wizard_generate' で LLM を呼び出すこと (D-12)."""
        mock_llm.send_message_for_purpose.return_value = _make_candidate_json(1)
        controller.generate_candidates(["test"])
        call_kwargs = mock_llm.send_message_for_purpose.call_args.kwargs
        assert call_kwargs["purpose"] == "wizard_generate"

    def test_user_name_in_prompt(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """ユーザー名がプロンプトに含まれること."""
        mock_llm.send_message_for_purpose.return_value = _make_candidate_json(
            1, "田中",
        )
        controller.generate_candidates(["test"], user_name="田中")
        user_msg = mock_llm.send_message_for_purpose.call_args.kwargs[
            "messages"
        ][0]["content"]
        assert "田中" in user_msg

    def test_handles_raw_list_response(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """candidates キーなしの直接リスト応答にも対応すること."""
        raw = [{"c1_name": "テスト", "c4_personality_core": "元気"}]
        mock_llm.send_message_for_purpose.return_value = json.dumps(
            raw, ensure_ascii=False,
        )
        result = controller.generate_candidates(["test"])
        assert len(result) == 1
        assert result[0].c1_name == "テスト"

    def test_llm_error_propagates(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """LLMError がそのまま伝播すること (EM-010)."""
        mock_llm.send_message_for_purpose.side_effect = LLMError("API失敗")
        with pytest.raises(LLMError):
            controller.generate_candidates(["test"])

    def test_invalid_data_format_raises(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """dict でも list でもないデータ形式で ValueError が発生すること."""
        mock_llm.send_message_for_purpose.return_value = '"just a string"'
        with pytest.raises(ValueError, match="候補データの形式が不正です"):
            controller.generate_candidates(["test"])

    def test_invalid_json_raises(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """不正な JSON で ValueError が伝播すること."""
        mock_llm.send_message_for_purpose.return_value = "これはJSONではない"
        with pytest.raises(ValueError, match="JSON パース失敗"):
            controller.generate_candidates(["test"])


# ---------------------------------------------------------------------------
# W-4: スタイルサンプル生成
# ---------------------------------------------------------------------------

_STYLE_SAMPLE_RESPONSE = """\
## S1: 日常会話
1. （雑談中）→「えっとね、さっき考えてたんだけど...」
2. （質問されて）→「ふむふむ...それって、こういうこと？」

## S2: 喜び
1. （褒められて）→「え、ほんと？ ...ありがとう」

## S3: 怒り・不快
1. （嫌なこと）→「...それはちょっと、嫌だったかな」

## S4: 悲しみ・寂しさ
1. （寂しい時）→「なんか...久しぶりに話せて、よかった」

## S5: 困惑・不知
1. （知らないこと）→「あのね、それはわたしも知らなくて」

## S6: ユーモア
1. （冗談）→「それってさぁ、もしかして...って、冗談だよ」

## S7: 沈黙破り
1. （長い沈黙後）→「...ねえ、さっきのこと、まだ考えてた」
"""


class TestGenerateStyleSamples:
    """generate_style_samples のテスト (W-4)."""

    def _make_persona(self) -> PersonaCore:
        return PersonaCore(
            c1_name="アキ",
            c2_first_person="わたし",
            c4_personality_core="好奇心旺盛だが慎重",
            c5_personality_axes="好奇心、繊細さ、几帳面さ",
            c6_speech_pattern="「〜だよ」「〜かな」が多め",
            c7_catchphrase="ふむふむ",
            c8_age_impression="高校生くらい",
        )

    def test_returns_style_text(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """スタイルサンプルテキストが返ること."""
        mock_llm.send_message_for_purpose.return_value = _STYLE_SAMPLE_RESPONSE
        result = controller.generate_style_samples(self._make_persona())
        assert "## S1" in result
        assert "## S7" in result

    def test_contains_s1_through_s7(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """S1-S7 の全セクションが含まれること."""
        mock_llm.send_message_for_purpose.return_value = _STYLE_SAMPLE_RESPONSE
        result = controller.generate_style_samples(self._make_persona())
        for i in range(1, 8):
            assert f"## S{i}" in result

    def test_uses_wizard_generate_purpose(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """purpose='wizard_generate' で LLM を呼び出すこと (D-12)."""
        mock_llm.send_message_for_purpose.return_value = _STYLE_SAMPLE_RESPONSE
        controller.generate_style_samples(self._make_persona())
        call_kwargs = mock_llm.send_message_for_purpose.call_args.kwargs
        assert call_kwargs["purpose"] == "wizard_generate"

    def test_persona_fields_in_prompt(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """PersonaCore のフィールドがプロンプトに含まれること."""
        mock_llm.send_message_for_purpose.return_value = _STYLE_SAMPLE_RESPONSE
        controller.generate_style_samples(self._make_persona())
        user_msg = mock_llm.send_message_for_purpose.call_args.kwargs[
            "messages"
        ][0]["content"]
        assert "アキ" in user_msg
        assert "わたし" in user_msg
        assert "好奇心旺盛だが慎重" in user_msg

    def test_llm_error_propagates(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """LLMError がそのまま伝播すること (EM-010)."""
        mock_llm.send_message_for_purpose.side_effect = LLMError("API失敗")
        with pytest.raises(LLMError):
            controller.generate_style_samples(self._make_persona())


# ---------------------------------------------------------------------------
# FR-5.8: 生成メタデータ
# ---------------------------------------------------------------------------


class TestGenerationMetadata:
    """生成メタデータの記録テスト (FR-5.8)."""

    def test_metadata_recorded_after_candidate_generation(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """候補生成後にメタデータが記録されること."""
        mock_llm.send_message_for_purpose.return_value = _make_candidate_json(1)
        associations = ["元気", "猫耳", "明るい"]
        controller.generate_candidates(associations)

        meta = controller.generation_metadata
        assert meta["method"] == "A"
        assert meta["associations"] == associations
        assert "generated_at" in meta

    def test_metadata_initially_empty(
        self, controller: WizardController,
    ) -> None:
        """初期状態ではメタデータが空であること."""
        assert controller.generation_metadata == {}
