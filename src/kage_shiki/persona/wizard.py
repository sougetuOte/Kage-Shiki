"""ウィザードコントローラ (T-20, T-21, T-22).

対応 FR:
    FR-5.1: ウィザード方式によるキャラクター生成
    FR-5.2: AI おまかせ方式（連想拡張 + 候補生成 + 選択）
    FR-5.3: 既存イメージ方式（自由記述 + AI 整形補完）
    FR-5.5: プレビュー会話（3-5往復）
    FR-5.6: 凍結処理
    FR-5.7: 連想拡張パイプライン
    FR-5.8: 生成メタデータの記録

対応設計:
    D-5: ウィザードフロー設計
    D-12: ウィザード用モデルスロット
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from kage_shiki.agent.llm_client import LLMClient
from kage_shiki.core.config import AppConfig
from kage_shiki.persona.persona_system import PersonaCore, PersonaSystem

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PersonaCore フィールド定義
# ---------------------------------------------------------------------------

_PERSONA_CORE_FIELDS: list[str] = [
    "c1_name",
    "c2_first_person",
    "c3_second_person",
    "c4_personality_core",
    "c5_personality_axes",
    "c6_speech_pattern",
    "c7_catchphrase",
    "c8_age_impression",
    "c9_values",
    "c10_forbidden",
    "c11_self_knowledge",
]

# ---------------------------------------------------------------------------
# W-1: 連想拡張プロンプト (FR-5.7)
# ---------------------------------------------------------------------------

_W1_SYSTEM = (
    "あなたはキャラクター設計の補助AIです。"
    "ユーザーが提供したキーワードから連想を広げ、"
    "デスクトップマスコットのキャラクター設計に使える"
    "多様な連想キーワードを生成してください。\n\n"
    "応答はJSON配列のみを出力してください。説明文は不要です。\n"
    '例: ["元気", "猫耳", "ツンデレ", "甘えん坊", "夜行性"]'
)

# ---------------------------------------------------------------------------
# W-2: 候補生成プロンプト (FR-5.2)
# ---------------------------------------------------------------------------

_W2_SYSTEM = (
    "あなたはキャラクター設計の専門家です。"
    "連想キーワードに基づき、個性的なデスクトップマスコットキャラクターを"
    "提案してください。\n\n"
    "各キャラクターは以下のJSON構造で出力してください:\n"
    '{"candidates": [\n'
    "  {\n"
    '    "c1_name": "名前",\n'
    '    "c2_first_person": "一人称",\n'
    '    "c3_second_person": "ユーザーの呼び方",\n'
    '    "c4_personality_core": "人格核文（2-3文）",\n'
    '    "c5_personality_axes": "性格軸（箇条書き3-5項目）",\n'
    '    "c6_speech_pattern": "口調パターンの説明",\n'
    '    "c7_catchphrase": "口癖（2-3個）",\n'
    '    "c8_age_impression": "年齢感の説明",\n'
    '    "c9_values": "価値観の説明",\n'
    '    "c10_forbidden": "禁忌事項（2-3個）",\n'
    '    "c11_self_knowledge": "知識の自己認識"\n'
    "  }\n"
    "]}\n\n"
    "応答はJSONのみを出力してください。説明文は不要です。"
)

# ---------------------------------------------------------------------------
# W-3: 自由記述整形プロンプト (FR-5.3)
# ---------------------------------------------------------------------------

_W3_SYSTEM = (
    "あなたはキャラクター設計の専門家です。"
    "ユーザーの自由記述からデスクトップマスコットのキャラクター設定を"
    "整形・補完してください。\n\n"
    "ユーザーが明示しなかったフィールドは、"
    "記述の雰囲気に合わせてAIが補完してください。\n\n"
    "応答は以下のJSON構造のみを出力してください:\n"
    "{\n"
    '  "persona": {\n'
    '    "c1_name": "名前",\n'
    '    "c2_first_person": "一人称",\n'
    '    "c3_second_person": "ユーザーの呼び方",\n'
    '    "c4_personality_core": "人格核文（2-3文）",\n'
    '    "c5_personality_axes": "性格軸（箇条書き3-5項目）",\n'
    '    "c6_speech_pattern": "口調パターンの説明",\n'
    '    "c7_catchphrase": "口癖（2-3個）",\n'
    '    "c8_age_impression": "年齢感の説明",\n'
    '    "c9_values": "価値観の説明",\n'
    '    "c10_forbidden": "禁忌事項（2-3個）",\n'
    '    "c11_self_knowledge": "知識の自己認識"\n'
    "  },\n"
    '  "style_samples": "## S1: 日常会話\\n1. ...（S1-S7 の口調サンプル）",\n'
    '  "ai_filled": ["AIが補完したフィールド名のリスト"]\n'
    "}\n\n"
    "応答はJSONのみを出力してください。説明文は不要です。"
)

# ---------------------------------------------------------------------------
# W-4: スタイルサンプル生成プロンプト
# ---------------------------------------------------------------------------

_W4_SYSTEM = (
    "あなたはキャラクターの口調デザイナーです。"
    "以下のキャラクター設定に基づき、"
    "7種類の場面での口調サンプルを生成してください。\n\n"
    "各場面について2-3例の発話サンプルを作成してください。\n\n"
    "出力形式:\n"
    "## S1: 日常会話\n"
    "1. （場面説明）→「セリフ」\n"
    "2. （場面説明）→「セリフ」\n\n"
    "## S2: 喜び\n...\n\n"
    "## S3: 怒り・不快\n...\n\n"
    "## S4: 悲しみ・寂しさ\n...\n\n"
    "## S5: 困惑・不知\n...\n\n"
    "## S6: ユーモア\n...\n\n"
    "## S7: 沈黙破り\n..."
)


# ---------------------------------------------------------------------------
# JSON 抽出ヘルパー
# ---------------------------------------------------------------------------


def _extract_json(text: str) -> Any:
    """LLM 応答から JSON を抽出する.

    マークダウンコードブロックで囲まれた JSON にも対応する。

    Args:
        text: LLM 応答テキスト。

    Returns:
        パース済みの JSON オブジェクト。

    Raises:
        ValueError: JSON のパースに失敗した場合。
    """
    text = text.strip()

    # マークダウンコードブロックを除去
    code_block = re.search(r"```(?:json)?\s*\n(.*?)```", text, re.DOTALL)
    if code_block:
        text = code_block.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON パース失敗: {e}") from e


_REQUIRED_PERSONA_FIELDS = frozenset({"c1_name", "c4_personality_core"})


def _dict_to_persona_core(d: dict[str, str]) -> PersonaCore:
    """辞書から PersonaCore を構築する.

    c1_name と c4_personality_core は必須フィールド（FR-4.8(c)）。
    欠損または空文字列の場合は ValueError を送出する。
    その他のフィールドは空文字列でフォールバックする。

    Args:
        d: C1-C11 フィールドを含む辞書。

    Returns:
        PersonaCore インスタンス。

    Raises:
        ValueError: 必須フィールドが欠損または空の場合。
    """
    for f in _REQUIRED_PERSONA_FIELDS:
        if not d.get(f):
            raise ValueError(f"必須フィールド '{f}' が欠損または空です")
    return PersonaCore(**{f: d.get(f, "") for f in _PERSONA_CORE_FIELDS})


# ---------------------------------------------------------------------------
# WizardController
# ---------------------------------------------------------------------------


class WizardController:
    """ウィザードコントローラ (D-5, T-20/T-21/T-22).

    方式 A: 連想拡張 → 候補生成 → スタイルサンプル生成 (T-20)
    方式 B: 自由記述 → AI 整形・補完 (T-21)
    共通: プレビュー会話 + 凍結処理 (T-22)
    方式 C (W-6: 凍結提案) は T-23 で実装予定。

    Attributes:
        generation_metadata: 生成メタデータ（FR-5.8）。
    """

    def __init__(self, llm: LLMClient, config: AppConfig) -> None:
        self._llm = llm
        self._config = config
        self.generation_metadata: dict[str, Any] = {}

    def expand_associations(self, keywords: list[str]) -> list[str]:
        """連想拡張パイプライン (W-1, FR-5.7).

        ユーザー入力キーワードを LLM で意味拡張し、
        association_count 個の連想キーワードを生成する。

        Args:
            keywords: ユーザー入力キーワード（1-3個）。

        Returns:
            連想キーワードのリスト（association_count 個）。

        Raises:
            LLMError: API 呼び出し失敗。
            ValueError: 応答の JSON パース失敗。
        """
        n = self._config.wizard.association_count
        user_msg = (
            f"以下のキーワードから{n}個の連想キーワードを生成してください:\n"
            f"{', '.join(keywords)}"
        )

        response = self._llm.send_message_for_purpose(
            system=_W1_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
            purpose="wizard_association",
        )

        result = _extract_json(response)
        if not isinstance(result, list):
            raise ValueError(f"連想結果がリストではありません: {type(result)}")

        logger.info("連想拡張完了: %d個のキーワード生成", len(result))
        return [str(item) for item in result]

    def generate_candidates(
        self,
        associations: list[str],
        user_name: str = "",
    ) -> list[PersonaCore]:
        """候補生成パイプライン (W-2, FR-5.2).

        連想キーワードに基づき、candidate_count 体のキャラクター候補を生成する。

        Args:
            associations: 連想キーワードリスト。
            user_name: ユーザー名（任意）。指定時は C3 に反映。

        Returns:
            PersonaCore のリスト（candidate_count 個）。

        Raises:
            LLMError: API 呼び出し失敗。
            ValueError: 応答の JSON パース失敗。
        """
        n = self._config.wizard.candidate_count
        user_parts = [
            f"以下の連想キーワードに基づき、"
            f"{n}体のキャラクターを提案してください:\n"
            f"{', '.join(associations)}",
        ]
        if user_name:
            user_parts.append(
                f"\nユーザーの名前は「{user_name}」です。"
                "c3_second_person にはこの名前を適切な呼び方で設定してください。",
            )

        response = self._llm.send_message_for_purpose(
            system=_W2_SYSTEM,
            messages=[{"role": "user", "content": "\n".join(user_parts)}],
            purpose="wizard_generate",
        )

        self.generation_metadata = {}

        data = _extract_json(response)
        if isinstance(data, dict) and "candidates" in data:
            raw_candidates = data["candidates"]
        elif isinstance(data, list):
            raw_candidates = data
        else:
            raise ValueError(f"候補データの形式が不正です: {type(data)}")

        candidates = [_dict_to_persona_core(c) for c in raw_candidates]
        logger.info("候補生成完了: %d体のキャラクター", len(candidates))

        # FR-5.8: メタデータ記録（成功時のみ更新）
        self.generation_metadata = {
            "generated_at": datetime.now().isoformat(),
            "method": "A",
            "associations": associations,
        }

        return candidates

    def generate_style_samples(self, persona: PersonaCore) -> str:
        """スタイルサンプル生成パイプライン (W-4).

        選択された PersonaCore の C1-C11 から S1-S7 の口調サンプルを生成する。

        Args:
            persona: 選択されたキャラクター候補。

        Returns:
            S1-S7 のスタイルサンプルテキスト（Markdown 形式）。

        Raises:
            LLMError: API 呼び出し失敗。
        """
        user_msg = (
            "以下のキャラクター設定に基づいて口調サンプルを生成してください:\n\n"
            f"名前: {persona.c1_name}\n"
            f"一人称: {persona.c2_first_person}\n"
            f"人格核文: {persona.c4_personality_core}\n"
            f"性格軸: {persona.c5_personality_axes}\n"
            f"口調パターン: {persona.c6_speech_pattern}\n"
            f"口癖: {persona.c7_catchphrase}\n"
            f"年齢感: {persona.c8_age_impression}"
        )

        response = self._llm.send_message_for_purpose(
            system=_W4_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
            purpose="wizard_generate",
        )

        logger.info("スタイルサンプル生成完了")
        return response.strip()

    def reshape_free_description(
        self,
        text: str,
        user_name: str = "",
    ) -> tuple[PersonaCore, str, list[str]]:
        """自由記述の整形・補完パイプライン (W-3, FR-5.3).

        ユーザーの自由記述テキストを AI が C1-C11 + S1-S7 に整形し、
        不足フィールドを補完する。

        Args:
            text: ユーザーの自由記述テキスト。
            user_name: ユーザー名（任意）。指定時は C3 に反映。

        Returns:
            (PersonaCore, style_samples テキスト, AI 補完フィールド名リスト)。

        Raises:
            LLMError: API 呼び出し失敗。
            ValueError: 応答の JSON パース失敗。
        """
        user_parts = [
            "以下の自由記述からキャラクター設定を整形・補完してください:\n\n"
            f"{text}",
        ]
        if user_name:
            user_parts.append(
                f"\nユーザーの名前は「{user_name}」です。"
                "c3_second_person にはこの名前を適切な呼び方で設定してください。",
            )

        response = self._llm.send_message_for_purpose(
            system=_W3_SYSTEM,
            messages=[{"role": "user", "content": "\n".join(user_parts)}],
            purpose="wizard_generate",
        )

        data = _extract_json(response)
        if not isinstance(data, dict) or "persona" not in data:
            raise ValueError("LLM 応答に 'persona' キーが含まれていません")
        if "style_samples" not in data:
            raise ValueError("LLM 応答に 'style_samples' キーが含まれていません")
        persona = _dict_to_persona_core(data["persona"])
        style_samples = data["style_samples"]
        ai_filled: list[str] = data.get("ai_filled", [])

        # FR-5.8: メタデータ記録
        self.generation_metadata = {
            "generated_at": datetime.now().isoformat(),
            "method": "B",
            "free_description": text,
        }

        logger.info("自由記述整形完了: %s", persona.c1_name)
        return persona, style_samples, ai_filled

    def preview_conversation_turn(
        self,
        persona: PersonaCore,
        style_text: str,
        turns: list[dict],
        user_input: str,
    ) -> str:
        """プレビュー会話の1ターン生成 (FR-5.5).

        生成した人格で会話プレビューを行う。

        Args:
            persona: プレビュー対象の PersonaCore。
            style_text: S1-S7 スタイルサンプルテキスト。
            turns: これまでの会話ターン。
            user_input: ユーザーの最新入力。

        Returns:
            キャラクターの応答テキスト。

        Raises:
            LLMError: API 呼び出し失敗。
        """
        system_prompt = (
            f"あなたは「{persona.c1_name}」というキャラクターです。\n"
            f"一人称: {persona.c2_first_person}\n"
            f"人格核文: {persona.c4_personality_core}\n"
            f"性格軸: {persona.c5_personality_axes}\n"
            f"口調パターン: {persona.c6_speech_pattern}\n"
            f"口癖: {persona.c7_catchphrase}\n\n"
            f"口調サンプル:\n{style_text}\n\n"
            "上記の人格設定に従って、ユーザーとの会話に応答してください。"
        )

        messages = list(turns) + [{"role": "user", "content": user_input}]

        return self._llm.send_message_for_purpose(
            system=system_prompt,
            messages=messages,
            purpose="wizard_preview",
        )

    def freeze_persona(
        self,
        persona_system: PersonaSystem,
        persona: PersonaCore,
        style_text: str,
        persona_dir: Path,
    ) -> None:
        """ペルソナ凍結処理 (FR-5.6).

        PersonaCore と style_samples を保存し、凍結状態に設定する。

        Args:
            persona_system: PersonaSystem インスタンス。
            persona: 凍結対象の PersonaCore。
            style_text: S1-S7 スタイルサンプルテキスト。
            persona_dir: ペルソナファイルの保存先ディレクトリ。
        """
        # persona_core.md を凍結メタデータ付きで保存
        persona_path = persona_dir / "persona_core.md"
        persona_system.freeze_and_save(persona_path, persona)

        # style_samples.md 保存
        style_path = persona_dir / "style_samples.md"
        style_path.write_text(style_text, encoding="utf-8")

        logger.info("ペルソナ凍結完了: %s", persona.c1_name)
