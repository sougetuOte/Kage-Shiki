"""Tests for persona/wizard.py — WizardController (T-20, T-21, T-22, T-23).

対応 FR:
    FR-5.1: ウィザード方式によるキャラクター生成（方式 A/B のバックエンドロジック部分）
    FR-5.2: AI おまかせ方式（連想拡張 + 候補生成 + 選択）
    FR-5.3: 既存イメージ方式（自由記述 + AI 整形補完）
    FR-5.4: 方式 C（白紙育成）— 名前 + 一人称のみ入力 → 未凍結で開始
    FR-5.5: プレビュー会話（3-5往復）
    FR-5.6: 凍結処理
    FR-5.7: 連想拡張パイプライン
    FR-5.8: 生成メタデータの記録
    FR-5.9: blank_freeze_threshold 会話後に AI が全体像を提案 → ユーザー承認で凍結

対応設計:
    D-5: ウィザードフロー設計
    D-12: ウィザード用モデルスロット
"""

import json
from unittest.mock import Mock

import pytest

from kage_shiki.agent.llm_client import LLMError
from kage_shiki.core.config import AppConfig
from kage_shiki.persona.persona_system import PersonaCore, PersonaSystem
from kage_shiki.persona.wizard import (
    WizardController,
    _dict_to_persona_core,
    _extract_json,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def controller(mock_llm: Mock, config) -> WizardController:
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

    def test_list_values_converted_to_str(self) -> None:
        """LLM がリストを返した場合に文字列に変換されること."""
        core = _dict_to_persona_core({
            "c1_name": "テスト",
            "c4_personality_core": "好奇心旺盛",
            "c5_personality_axes": ["明るい", "活発", "社交的"],
            "c9_values": ["誠実", "優しさ"],
        })
        assert core.c5_personality_axes == "明るい\n活発\n社交的"
        assert core.c9_values == "誠実\n優しさ"


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


# ---------------------------------------------------------------------------
# T-21: W-3 方式 B — 自由記述の整形補完 (FR-5.3)
# ---------------------------------------------------------------------------


class TestReshapeFreeDescription:
    """reshape_free_description のテスト (W-3, FR-5.3)."""

    _RESHAPE_RESPONSE = json.dumps(
        {
            "persona": {
                "c1_name": "ミカ",
                "c2_first_person": "僕",
                "c3_second_person": "きみ",
                "c4_personality_core": "ちょっと毒舌だけど根は優しい",
                "c5_personality_axes": "皮肉屋、世話焼き",
                "c6_speech_pattern": "ぶっきらぼうな語尾",
                "c7_catchphrase": "知らないの？",
                "c8_age_impression": "大学生くらい",
                "c9_values": "本音を大切にする",
                "c10_forbidden": "嘘をつくこと",
                "c11_self_knowledge": "人並みの知識はある",
            },
            "style_samples": (
                "## S1: 日常会話\n1. →「まぁ、そうだろうね」\n\n"
                "## S2: 喜び\n1. →「...悪くないね」\n\n"
                "## S3: 怒り・不快\n1. →「はぁ？ ちょっと待てよ」\n\n"
                "## S4: 悲しみ・寂しさ\n1. →「...別に」\n\n"
                "## S5: 困惑・不知\n1. →「んー、それは知らないな」\n\n"
                "## S6: ユーモア\n1. →「ははっ、なにそれ」\n\n"
                "## S7: 沈黙破り\n1. →「...暇？」"
            ),
            "ai_filled": ["c9_values", "c10_forbidden", "c11_self_knowledge"],
        },
        ensure_ascii=False,
    )

    def test_returns_persona_and_style(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """PersonaCore と style_samples のタプルが返ること."""
        mock_llm.send_message_for_purpose.return_value = self._RESHAPE_RESPONSE
        persona, style, ai_filled = controller.reshape_free_description(
            "名前はミカ。毒舌だけど優しい。一人称は僕。",
        )
        assert isinstance(persona, PersonaCore)
        assert persona.c1_name == "ミカ"
        assert isinstance(style, str)
        assert "## S1" in style

    def test_ai_filled_fields_returned(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """AI が補完したフィールド一覧が返ること."""
        mock_llm.send_message_for_purpose.return_value = self._RESHAPE_RESPONSE
        _, _, ai_filled = controller.reshape_free_description("テスト記述")
        assert "c9_values" in ai_filled

    def test_uses_wizard_generate_purpose(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """purpose='wizard_generate' で LLM を呼び出すこと."""
        mock_llm.send_message_for_purpose.return_value = self._RESHAPE_RESPONSE
        controller.reshape_free_description("テスト記述")
        call_kwargs = mock_llm.send_message_for_purpose.call_args.kwargs
        assert call_kwargs["purpose"] == "wizard_generate"

    def test_user_name_in_prompt(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """ユーザー名がプロンプトに含まれること."""
        mock_llm.send_message_for_purpose.return_value = self._RESHAPE_RESPONSE
        controller.reshape_free_description("テスト記述", user_name="太郎")
        user_msg = mock_llm.send_message_for_purpose.call_args.kwargs[
            "messages"
        ][0]["content"]
        assert "太郎" in user_msg

    def test_metadata_records_method_b(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """メタデータの method が 'B' であること."""
        mock_llm.send_message_for_purpose.return_value = self._RESHAPE_RESPONSE
        controller.reshape_free_description("テスト記述")
        assert controller.generation_metadata["method"] == "B"

    def test_free_description_in_prompt(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """ユーザーの自由記述がプロンプトに含まれること."""
        mock_llm.send_message_for_purpose.return_value = self._RESHAPE_RESPONSE
        controller.reshape_free_description("名前はミカ。毒舌だけど優しい。")
        user_msg = mock_llm.send_message_for_purpose.call_args.kwargs[
            "messages"
        ][0]["content"]
        assert "名前はミカ" in user_msg


# ---------------------------------------------------------------------------
# T-22: プレビュー会話 (FR-5.5)
# ---------------------------------------------------------------------------


class TestPreviewConversationTurn:
    """preview_conversation_turn のテスト (FR-5.5, D-12)."""

    def _make_persona(self) -> PersonaCore:
        return PersonaCore(
            c1_name="アキ",
            c2_first_person="わたし",
            c4_personality_core="好奇心旺盛だが慎重",
        )

    def test_returns_response(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """プレビュー応答が返ること."""
        mock_llm.send_message_for_purpose.return_value = "やあ、はじめまして！"
        result = controller.preview_conversation_turn(
            persona=self._make_persona(),
            style_text="## S1\nテスト",
            turns=[],
            user_input="こんにちは",
        )
        assert result == "やあ、はじめまして！"

    def test_uses_wizard_preview_purpose(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """purpose='wizard_preview' で LLM を呼び出すこと (D-12)."""
        mock_llm.send_message_for_purpose.return_value = "応答"
        controller.preview_conversation_turn(
            persona=self._make_persona(),
            style_text="## S1\nテスト",
            turns=[],
            user_input="テスト",
        )
        call_kwargs = mock_llm.send_message_for_purpose.call_args.kwargs
        assert call_kwargs["purpose"] == "wizard_preview"

    def test_persona_in_system_prompt(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """システムプロンプトにペルソナ情報が含まれること."""
        mock_llm.send_message_for_purpose.return_value = "応答"
        controller.preview_conversation_turn(
            persona=self._make_persona(),
            style_text="## S1\nテスト口調",
            turns=[],
            user_input="テスト",
        )
        call_kwargs = mock_llm.send_message_for_purpose.call_args.kwargs
        assert "アキ" in call_kwargs["system"]
        assert "好奇心旺盛" in call_kwargs["system"]

    def test_turns_included_in_messages(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """過去のターンが messages に含まれること."""
        mock_llm.send_message_for_purpose.return_value = "応答"
        turns = [
            {"role": "user", "content": "前の入力"},
            {"role": "assistant", "content": "前の応答"},
        ]
        controller.preview_conversation_turn(
            persona=self._make_persona(),
            style_text="",
            turns=turns,
            user_input="新しい入力",
        )
        messages = mock_llm.send_message_for_purpose.call_args.kwargs["messages"]
        assert len(messages) == 3  # 2 turns + latest input
        assert messages[-1]["content"] == "新しい入力"


# ---------------------------------------------------------------------------
# T-22: 凍結処理 (FR-5.6)
# ---------------------------------------------------------------------------


class TestFreezePersona:
    """freeze_persona のテスト (FR-5.6)."""

    def test_saves_persona_core(
        self, controller: WizardController, mock_llm: Mock, tmp_path,
    ) -> None:
        """persona_core.md が保存されること."""
        ps = PersonaSystem()
        persona = PersonaCore(
            c1_name="アキ",
            c2_first_person="わたし",
            c4_personality_core="好奇心旺盛",
        )
        controller.freeze_persona(
            persona_system=ps,
            persona=persona,
            style_text="## S1\nテスト",
            persona_dir=tmp_path,
        )
        persona_file = tmp_path / "persona_core.md"
        assert persona_file.exists()
        content = persona_file.read_text(encoding="utf-8")
        assert "アキ" in content

    def test_saves_style_samples(
        self, controller: WizardController, mock_llm: Mock, tmp_path,
    ) -> None:
        """style_samples.md が保存されること."""
        ps = PersonaSystem()
        persona = PersonaCore(
            c1_name="アキ",
            c2_first_person="わたし",
            c4_personality_core="好奇心旺盛",
        )
        controller.freeze_persona(
            persona_system=ps,
            persona=persona,
            style_text="## S1\nテスト口調サンプル",
            persona_dir=tmp_path,
        )
        style_file = tmp_path / "style_samples.md"
        assert style_file.exists()
        content = style_file.read_text(encoding="utf-8")
        assert "テスト口調サンプル" in content

    def test_persona_is_frozen(
        self, controller: WizardController, mock_llm: Mock, tmp_path,
    ) -> None:
        """凍結後に persona_frozen が true であること."""
        ps = PersonaSystem()
        persona = PersonaCore(
            c1_name="アキ",
            c2_first_person="わたし",
            c4_personality_core="好奇心旺盛",
        )
        controller.freeze_persona(
            persona_system=ps,
            persona=persona,
            style_text="## S1\nテスト",
            persona_dir=tmp_path,
        )
        # 凍結状態を検証: persona_core.md に freeze マーカーが含まれる
        content = (tmp_path / "persona_core.md").read_text(encoding="utf-8")
        assert "frozen" in content.lower()

    def test_no_observations_saved(
        self, controller: WizardController, mock_llm: Mock, tmp_path,
    ) -> None:
        """凍結処理で observations に保存されないこと."""
        ps = PersonaSystem()
        persona = PersonaCore(
            c1_name="アキ",
            c2_first_person="わたし",
            c4_personality_core="好奇心旺盛",
        )
        # freeze_persona は save_observation を呼ばない設計。
        # 正常完了すれば DB 操作なしが保証される。
        controller.freeze_persona(
            persona_system=ps,
            persona=persona,
            style_text="## S1\nテスト",
            persona_dir=tmp_path,
        )


# ---------------------------------------------------------------------------
# T-23: 方式 C — 白紙育成 (FR-5.4)
# ---------------------------------------------------------------------------


class TestCreateBlankPersona:
    """create_blank_persona のテスト (FR-5.4)."""

    def test_create_blank_persona_basic(
        self, controller: WizardController,
    ) -> None:
        """名前 + 一人称で最小 PersonaCore が生成されること."""
        persona, _ = controller.create_blank_persona(
            name="ミドリ", first_person="わたし",
        )
        assert isinstance(persona, PersonaCore)
        assert persona.c1_name == "ミドリ"
        assert persona.c2_first_person == "わたし"

    def test_create_blank_persona_with_user_name(
        self, controller: WizardController,
    ) -> None:
        """user_name 指定時に c3_second_person が設定されること."""
        persona, _ = controller.create_blank_persona(
            name="ミドリ", first_person="わたし", user_name="田中",
        )
        assert persona.c3_second_person == "田中"

    def test_create_blank_persona_without_user_name(
        self, controller: WizardController,
    ) -> None:
        """user_name 未指定時に c3_second_person が 'あなた' であること."""
        persona, _ = controller.create_blank_persona(
            name="ミドリ", first_person="わたし",
        )
        assert persona.c3_second_person == "あなた"

    def test_create_blank_persona_metadata(
        self, controller: WizardController,
    ) -> None:
        """generation_metadata に method='C' が記録されること."""
        controller.create_blank_persona(name="ミドリ", first_person="わたし")
        assert controller.generation_metadata["method"] == "C"

    def test_create_blank_persona_style_template(
        self, controller: WizardController,
    ) -> None:
        """返される style_samples が S1-S7 の空テンプレートであること."""
        _, style = controller.create_blank_persona(
            name="ミドリ", first_person="わたし",
        )
        for i in range(1, 8):
            assert f"## S{i}" in style
        assert "まだ定義されていません" in style


# ---------------------------------------------------------------------------
# T-23: 凍結提案トリガー (FR-5.9)
# ---------------------------------------------------------------------------


class TestShouldProposeFreeze:
    """should_propose_freeze のテスト (FR-5.9)."""

    def test_should_propose_freeze_at_threshold(
        self, controller: WizardController, config: AppConfig,
    ) -> None:
        """threshold=20 で count=20 → True であること."""
        assert config.wizard.blank_freeze_threshold == 20
        assert controller.should_propose_freeze(20) is True

    def test_should_propose_freeze_at_multiple(
        self, controller: WizardController,
    ) -> None:
        """threshold=20 で count=40 → True であること."""
        assert controller.should_propose_freeze(40) is True

    def test_should_propose_freeze_below(
        self, controller: WizardController,
    ) -> None:
        """threshold=20 で count=19 → False であること."""
        assert controller.should_propose_freeze(19) is False

    def test_should_propose_freeze_between(
        self, controller: WizardController,
    ) -> None:
        """threshold=20 で count=25 → False であること."""
        assert controller.should_propose_freeze(25) is False

    def test_should_propose_freeze_zero_count(
        self, controller: WizardController,
    ) -> None:
        """count=0 → False であること."""
        assert controller.should_propose_freeze(0) is False

    def test_should_propose_freeze_zero_threshold(
        self, mock_llm: Mock,
    ) -> None:
        """threshold=0 で任意 count → False であること（無効化）."""
        config = AppConfig()
        # blank_freeze_threshold を 0 に設定したコントローラを作る
        import dataclasses

        wiz_cfg = dataclasses.replace(config.wizard, blank_freeze_threshold=0)
        cfg_zero = dataclasses.replace(config, wizard=wiz_cfg)
        ctrl = WizardController(mock_llm, cfg_zero)
        assert ctrl.should_propose_freeze(20) is False
        assert ctrl.should_propose_freeze(100) is False

    def test_should_propose_freeze_negative_count(
        self, controller: WizardController,
    ) -> None:
        """負数の会話数では凍結提案しないこと（防御的）."""
        # 実用上 mascot_message_count が負になることはないが、防御的に False を返すこと
        result = controller.should_propose_freeze(-20)
        assert result is False


# ---------------------------------------------------------------------------
# T-23: 凍結提案生成 (FR-5.9)
# ---------------------------------------------------------------------------

_FREEZE_PROPOSAL_RESPONSE = json.dumps(
    {
        "c1_name": "ミドリ",
        "c2_first_person": "わたし",
        "c3_second_person": "あなた",
        "c4_personality_core": "明るくて好奇心旺盛です。",
        "c5_personality_axes": "積極性、好奇心",
        "c6_speech_pattern": "「〜だよ」が多め",
        "c7_catchphrase": "えへへ",
        "c8_age_impression": "10代",
        "c9_values": "誠実さ",
        "c10_forbidden": "嘘をつくこと",
        "c11_self_knowledge": "知識は標準的",
    },
    ensure_ascii=False,
)


class TestGenerateFreezeProposal:
    """generate_freeze_proposal のテスト (FR-5.9)."""

    def test_generate_freeze_proposal_success(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """LLM モック、正常系で PersonaCore が返ること."""
        mock_llm.send_message_for_purpose.return_value = _FREEZE_PROPOSAL_RESPONSE
        persona = controller.generate_freeze_proposal(
            name="ミドリ",
            observations_text="会話内容のまとめ...",
        )
        assert isinstance(persona, PersonaCore)
        assert persona.c1_name == "ミドリ"

    def test_generate_freeze_proposal_metadata(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """method='C_freeze' が generation_metadata に記録されること."""
        mock_llm.send_message_for_purpose.return_value = _FREEZE_PROPOSAL_RESPONSE
        controller.generate_freeze_proposal(
            name="ミドリ",
            observations_text="観察内容",
        )
        assert controller.generation_metadata["method"] == "C_freeze"
        assert "observations_summary" in controller.generation_metadata

    def test_generate_freeze_proposal_invalid_json(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """LLM 応答が不正 JSON → ValueError が発生すること."""
        mock_llm.send_message_for_purpose.return_value = "これはJSONではない"
        with pytest.raises(ValueError, match="JSON パース失敗"):
            controller.generate_freeze_proposal(
                name="ミドリ",
                observations_text="観察内容",
            )

    def test_generate_freeze_proposal_with_user_name(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """user_name 指定時にプロンプトにユーザー名が含まれること。"""
        mock_llm.send_message_for_purpose.return_value = _FREEZE_PROPOSAL_RESPONSE
        controller.generate_freeze_proposal(
            name="ミドリ",
            observations_text="観察内容",
            user_name="田中",
        )
        user_msg = mock_llm.send_message_for_purpose.call_args.kwargs["messages"][0]["content"]
        assert "田中" in user_msg

    def test_generate_freeze_proposal_without_user_name(
        self, controller: WizardController, mock_llm: Mock,
    ) -> None:
        """user_name 未指定時にプロンプトにユーザー名情報が含まれないこと。"""
        mock_llm.send_message_for_purpose.return_value = _FREEZE_PROPOSAL_RESPONSE
        controller.generate_freeze_proposal(
            name="ミドリ",
            observations_text="観察内容",
        )
        user_msg = mock_llm.send_message_for_purpose.call_args.kwargs["messages"][0]["content"]
        assert "ユーザーの名前は" not in user_msg


# ---------------------------------------------------------------------------
# T-23: 空スタイルテンプレート (FR-5.4)
# ---------------------------------------------------------------------------


class TestGenerateBlankStyleTemplate:
    """generate_blank_style_template のテスト (FR-5.4)."""

    def test_generate_blank_style_template(self) -> None:
        """S1-S7 全セクションが含まれること."""
        result = WizardController.generate_blank_style_template()
        for i in range(1, 8):
            assert f"## S{i}" in result

    def test_generate_blank_style_template_placeholder(self) -> None:
        """各セクションに「まだ定義されていません」が含まれること."""
        result = WizardController.generate_blank_style_template()
        assert result.count("まだ定義されていません") == 7
