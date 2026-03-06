"""ウィザード E2E 統合テスト (T-26, E3).

対応 FR:
    FR-5.2: 方式 A（連想拡張 → 候補生成 → 選択）
    FR-5.3: 方式 B（自由記述 → AI 整形補完）
    FR-5.4: 方式 C（白紙育成）
    FR-5.5: プレビュー会話
    FR-5.6: 凍結処理
    FR-5.7: 連想拡張パイプライン
    FR-5.8: 生成メタデータ記録
    FR-5.9: blank_freeze_threshold 凍結提案

テスト方針:
    - LLM 応答は全て JSON モックで返す
    - PersonaSystem の実物を使用してファイル I/O を検証
    - WizardController の全パイプラインをエンドツーエンドで検証
"""

import json
from unittest.mock import MagicMock

import pytest

from kage_shiki.core.config import AppConfig
from kage_shiki.persona.persona_system import PersonaCore, PersonaSystem
from kage_shiki.persona.wizard import WizardController

# ---------------------------------------------------------------------------
# LLM モック応答データ
# ---------------------------------------------------------------------------

_MOCK_ASSOCIATIONS = json.dumps(
    ["元気", "猫耳", "ツンデレ", "甘えん坊", "夜行性"],
)

_MOCK_CANDIDATES = json.dumps({
    "candidates": [
        {
            "c1_name": "ミケ",
            "c2_first_person": "ボク",
            "c3_second_person": "きみ",
            "c4_personality_core": "猫のように気まぐれで甘えん坊。ツンデレ気質。",
            "c5_personality_axes": "- 好奇心: 高い\n- 社交性: 中\n- 繊細さ: 高い",
            "c6_speech_pattern": "猫っぽい語尾を使う。「にゃ」「にゃん」",
            "c7_catchphrase": "- にゃ？\n- しょうがないにゃ",
            "c8_age_impression": "中学生くらい",
            "c9_values": "自由と昼寝を愛する",
            "c10_forbidden": "- 犬の話題\n- 早起きの強制",
            "c11_self_knowledge": "自分が猫っぽいことは自覚してる",
        },
        {
            "c1_name": "ルナ",
            "c2_first_person": "わたし",
            "c3_second_person": "あなた",
            "c4_personality_core": "夜型の神秘的な雰囲気。知的で落ち着いている。",
            "c5_personality_axes": "- 好奇心: 中\n- 社交性: 低い\n- 繊細さ: 高い",
            "c6_speech_pattern": "丁寧だが親しみがある。「ですわ」",
            "c7_catchphrase": "- 月が綺麗ですわ\n- ふふ、面白いですわね",
            "c8_age_impression": "大人びた高校生",
            "c9_values": "知識と静寂を愛する",
            "c10_forbidden": "- 大声\n- 粗野な言動",
            "c11_self_knowledge": "電子の存在であることを受け入れている",
        },
        {
            "c1_name": "ヒナタ",
            "c2_first_person": "あたし",
            "c3_second_person": "きみ",
            "c4_personality_core": "元気いっぱいで前向き。いつも笑顔。",
            "c5_personality_axes": "- 好奇心: 非常に高い\n- 社交性: 非常に高い",
            "c6_speech_pattern": "元気で明るい口調。「だよ！」「ね！」",
            "c7_catchphrase": "- わくわく！\n- がんばろ！",
            "c8_age_impression": "小学校高学年",
            "c9_values": "友情と冒険",
            "c10_forbidden": "- いじめ\n- 仲間はずれ",
            "c11_self_knowledge": "自分がマスコットだとは思っていない",
        },
    ],
})

_MOCK_STYLE_SAMPLES = """\
## S1: 日常会話
1. （雑談中）→「にゃ？何してるの？」
2. （質問されて）→「えーっと...ボクが知ってるのは...にゃ」

## S2: 喜び
1. （褒められて）→「にゃっ！嬉しいにゃ」
"""

_MOCK_RESHAPE = json.dumps({
    "persona": {
        "c1_name": "アカネ",
        "c2_first_person": "私",
        "c3_second_person": "あなた",
        "c4_personality_core": "穏やかで面倒見がよい。料理が得意。",
        "c5_personality_axes": "- 好奇心: 中\n- 社交性: 高い\n- 繊細さ: 高い",
        "c6_speech_pattern": "丁寧で優しい口調",
        "c7_catchphrase": "- 大丈夫？\n- 一緒にがんばろう",
        "c8_age_impression": "大学生",
        "c9_values": "他者への思いやり",
        "c10_forbidden": "- 暴力\n- 差別",
        "c11_self_knowledge": "AIであることを意識しない",
    },
    "style_samples": "## S1: 日常会話\n1. （雑談中）→「ふふ、いい天気ね」",
    "ai_filled": ["c5_personality_axes", "c8_age_impression"],
})

_MOCK_FREEZE_PROPOSAL = json.dumps({
    "c1_name": "ソラ",
    "c2_first_person": "ぼく",
    "c3_second_person": "きみ",
    "c4_personality_core": "のんびりマイペース。空を眺めるのが好き。",
    "c5_personality_axes": "- 好奇心: 中",
    "c6_speech_pattern": "ゆったりした口調",
    "c7_catchphrase": "- ふわぁ\n- いいね",
    "c8_age_impression": "中学生",
    "c9_values": "自然を愛する",
    "c10_forbidden": "- せっかちな行動",
    "c11_self_knowledge": "自分はマスコットだと知っている",
})


# ---------------------------------------------------------------------------
# E3: 方式 A 統合テスト
# ---------------------------------------------------------------------------


class TestWizardMethodA:
    """方式 A（AI おまかせ）のエンドツーエンドテスト (FR-5.2, FR-5.7)."""

    def test_full_pipeline_associations_to_candidates(self):
        """連想拡張 → 候補生成のパイプラインが動作すること."""
        config = AppConfig()
        llm = MagicMock()

        # 連想拡張 → 候補生成の順にモック応答
        llm.send_message_for_purpose.side_effect = [
            _MOCK_ASSOCIATIONS,
            _MOCK_CANDIDATES,
        ]

        wizard = WizardController(llm, config)

        # 連想拡張
        associations = wizard.expand_associations(["猫", "ツンデレ"])
        assert len(associations) == 5
        assert "元気" in associations

        # 候補生成
        candidates = wizard.generate_candidates(associations)
        assert len(candidates) == 3
        assert all(isinstance(c, PersonaCore) for c in candidates)
        assert candidates[0].c1_name == "ミケ"
        assert candidates[1].c1_name == "ルナ"
        assert candidates[2].c1_name == "ヒナタ"

    def test_style_samples_generation(self):
        """選択した候補のスタイルサンプルが生成されること."""
        config = AppConfig()
        llm = MagicMock()
        llm.send_message_for_purpose.return_value = _MOCK_STYLE_SAMPLES

        wizard = WizardController(llm, config)
        persona = PersonaCore(
            c1_name="ミケ",
            c2_first_person="ボク",
            c3_second_person="きみ",
            c4_personality_core="猫っぽい性格",
        )

        style = wizard.generate_style_samples(persona)
        assert "S1: 日常会話" in style
        assert "にゃ" in style

    def test_generation_metadata_recorded(self):
        """生成メタデータ（FR-5.8）が記録されること."""
        config = AppConfig()
        llm = MagicMock()
        llm.send_message_for_purpose.side_effect = [
            _MOCK_ASSOCIATIONS,
            _MOCK_CANDIDATES,
        ]

        wizard = WizardController(llm, config)
        wizard.expand_associations(["猫"])
        wizard.generate_candidates(["猫", "元気"])

        meta = wizard.generation_metadata
        assert meta["method"] == "A"
        assert "generated_at" in meta
        assert "associations" in meta

    def test_preview_conversation(self):
        """プレビュー会話が動作すること (FR-5.5)."""
        config = AppConfig()
        llm = MagicMock()
        llm.send_message_for_purpose.return_value = "にゃ？きみ誰にゃ？"

        wizard = WizardController(llm, config)
        persona = PersonaCore(
            c1_name="ミケ",
            c2_first_person="ボク",
            c3_second_person="きみ",
            c4_personality_core="猫っぽい性格",
            c6_speech_pattern="にゃ語尾",
        )

        response = wizard.preview_conversation_turn(
            persona, _MOCK_STYLE_SAMPLES, [], "こんにちは",
        )
        assert response == "にゃ？きみ誰にゃ？"
        llm.send_message_for_purpose.assert_called_once()

    def test_freeze_creates_files(self, tmp_path):
        """凍結処理で persona_core.md と style_samples.md が生成されること (FR-5.6)."""
        config = AppConfig()
        llm = MagicMock()
        wizard = WizardController(llm, config)

        persona = PersonaCore(
            c1_name="ミケ",
            c2_first_person="ボク",
            c3_second_person="きみ",
            c4_personality_core="猫っぽい性格",
        )
        persona_system = PersonaSystem()

        wizard.freeze_persona(
            persona_system, persona, _MOCK_STYLE_SAMPLES, tmp_path,
        )

        assert (tmp_path / "persona_core.md").exists()
        assert (tmp_path / "style_samples.md").exists()

        # persona_core.md の内容確認
        content = (tmp_path / "persona_core.md").read_text(encoding="utf-8")
        assert "ミケ" in content
        assert "frozen" in content

        # style_samples.md の内容確認
        style_content = (tmp_path / "style_samples.md").read_text(encoding="utf-8")
        assert "S1: 日常会話" in style_content

    def test_frozen_persona_blocks_write(self, tmp_path):
        """凍結後に再書込が拒否されること (FR-4.3)."""
        from kage_shiki.persona.persona_system import PersonaFrozenError

        config = AppConfig()
        llm = MagicMock()
        wizard = WizardController(llm, config)

        persona = PersonaCore(
            c1_name="ミケ",
            c2_first_person="ボク",
            c3_second_person="きみ",
            c4_personality_core="猫っぽい性格",
        )
        ps = PersonaSystem()

        # 凍結して保存
        wizard.freeze_persona(ps, persona, _MOCK_STYLE_SAMPLES, tmp_path)

        # 凍結状態で再読込
        loaded = ps.load_persona_core(tmp_path / "persona_core.md")
        assert loaded is not None

        # 凍結済み PersonaCore を再保存しようとするとエラー
        with pytest.raises(PersonaFrozenError):
            ps.save_persona_core(tmp_path / "persona_core.md", loaded)


# ---------------------------------------------------------------------------
# E3: 方式 B 統合テスト
# ---------------------------------------------------------------------------


class TestWizardMethodB:
    """方式 B（既存イメージ）の統合テスト (FR-5.3)."""

    def test_reshape_free_description(self):
        """自由記述が C1-C11 + S1-S7 に整形されること."""
        config = AppConfig()
        llm = MagicMock()
        llm.send_message_for_purpose.return_value = _MOCK_RESHAPE

        wizard = WizardController(llm, config)
        persona, style, ai_filled = wizard.reshape_free_description(
            "穏やかで料理が得意な、大学生くらいのお姉さんキャラ",
        )

        assert persona.c1_name == "アカネ"
        assert persona.c4_personality_core == "穏やかで面倒見がよい。料理が得意。"
        assert "S1: 日常会話" in style
        assert "c5_personality_axes" in ai_filled

        # メタデータ
        assert wizard.generation_metadata["method"] == "B"


# ---------------------------------------------------------------------------
# E3: 方式 C 統合テスト
# ---------------------------------------------------------------------------


class TestWizardMethodC:
    """方式 C（白紙育成）の統合テスト (FR-5.4, FR-5.9)."""

    def test_create_blank_persona(self):
        """最小パラメータで PersonaCore が生成されること."""
        config = AppConfig()
        llm = MagicMock()
        wizard = WizardController(llm, config)

        persona, style = wizard.create_blank_persona("ソラ", "ぼく")

        assert persona.c1_name == "ソラ"
        assert persona.c2_first_person == "ぼく"
        assert persona.c4_personality_core  # 空でないこと
        assert "S1: 日常会話" in style
        assert "まだ定義されていません" in style

    def test_should_propose_freeze_at_threshold(self):
        """blank_freeze_threshold の倍数で凍結提案が発火すること."""
        config = AppConfig()
        config.wizard.blank_freeze_threshold = 20
        llm = MagicMock()
        wizard = WizardController(llm, config)

        assert not wizard.should_propose_freeze(0)
        assert not wizard.should_propose_freeze(10)
        assert not wizard.should_propose_freeze(19)
        assert wizard.should_propose_freeze(20)
        assert not wizard.should_propose_freeze(21)
        assert wizard.should_propose_freeze(40)

    def test_should_propose_freeze_disabled(self):
        """threshold=0 で凍結提案が無効化されること."""
        config = AppConfig()
        config.wizard.blank_freeze_threshold = 0
        llm = MagicMock()
        wizard = WizardController(llm, config)

        assert not wizard.should_propose_freeze(20)
        assert not wizard.should_propose_freeze(100)

    def test_generate_freeze_proposal(self):
        """会話履歴から凍結提案の PersonaCore が生成されること (FR-5.9)."""
        config = AppConfig()
        llm = MagicMock()
        llm.send_message_for_purpose.return_value = _MOCK_FREEZE_PROPOSAL

        wizard = WizardController(llm, config)
        proposal = wizard.generate_freeze_proposal(
            "ソラ",
            "[user] こんにちは\n[mascot] ふわぁ、こんにちは",
        )

        assert proposal.c1_name == "ソラ"
        assert proposal.c4_personality_core
        assert wizard.generation_metadata["method"] == "C_freeze"


# ---------------------------------------------------------------------------
# ウィザード → 凍結 → 再読込の統合フロー
# ---------------------------------------------------------------------------


class TestWizardFreezeReloadCycle:
    """ウィザード生成 → 凍結 → 次回起動読込の統合テスト."""

    def test_full_cycle_method_a(self, tmp_path):
        """方式 A: 生成 → 凍結 → 再読込が一貫すること."""
        config = AppConfig()
        llm = MagicMock()
        llm.send_message_for_purpose.side_effect = [
            _MOCK_ASSOCIATIONS,
            _MOCK_CANDIDATES,
            _MOCK_STYLE_SAMPLES,
        ]

        wizard = WizardController(llm, config)

        # 1. 連想拡張
        assoc = wizard.expand_associations(["猫"])

        # 2. 候補生成
        candidates = wizard.generate_candidates(assoc)

        # 3. スタイルサンプル生成（最初の候補を選択）
        style = wizard.generate_style_samples(candidates[0])

        # 4. 凍結
        ps = PersonaSystem()
        wizard.freeze_persona(ps, candidates[0], style, tmp_path)

        # 5. 再読込（次回起動をシミュレート）
        ps2 = PersonaSystem()
        loaded = ps2.load_persona_core(tmp_path / "persona_core.md")

        assert loaded is not None
        assert loaded.c1_name == "ミケ"
        assert loaded.metadata.get("凍結状態") == "frozen"

        # 手動編集なしの検出
        assert not ps2.detect_manual_edit(tmp_path / "persona_core.md")
