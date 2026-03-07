"""AgentCore — セッション管理 + プロンプト構築 + 対話エンジン.

T-06 スコープ:
    generate_session_id(): ハイブリッド session_id 生成（D-13）
    SessionContext: セッション状態管理

T-12 スコープ:
    PromptBuilder: SystemPrompt + Messages 配列構築（D-3, D-8）

T-13 スコープ:
    AgentCore: ReAct ループ本体（FR-6.1）
    ConsistencyHit: 整合性チェックヒット記録（D-8）
    check_consistency_rules: ルールベース後処理（D-8）
"""

import logging
import re
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from kage_shiki.agent.human_block_updater import parse_human_block_updates, validate_update
from kage_shiki.agent.llm_client import LLMProtocol
from kage_shiki.agent.prompt_builder import PromptBuilder  # re-export for backward compat
from kage_shiki.agent.trends_proposal import TrendsProposalManager
from kage_shiki.core.config import AppConfig, get_max_tokens, get_model
from kage_shiki.memory.db import save_observation, search_observations_fts
from kage_shiki.persona.persona_system import PersonaSystem

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# session_id 定数（D-13）
# ---------------------------------------------------------------------------

_SESSION_ID_LENGTH = 22
_SESSION_ID_PATTERN = re.compile(r"\d{8}_\d{4}_[0-9a-f]{8}")


# ---------------------------------------------------------------------------
# session_id 生成（D-13）
# ---------------------------------------------------------------------------


def generate_session_id() -> str:
    """ハイブリッド session_id を生成する (D-13).

    フォーマット: YYYYMMDD_HHMM_xxxxxxxx（固定22文字）
    - 日時部分: ローカルタイムで分精度（人間可読）
    - UUID 部分: uuid4 の先頭8文字（~42億の組み合わせ）

    Returns:
        22文字の session_id 文字列。

    Example:
        >>> sid = generate_session_id()
        >>> len(sid)
        22
    """
    now = datetime.now()
    date_part = now.strftime("%Y%m%d_%H%M")
    uuid_part = uuid.uuid4().hex[:8]
    return f"{date_part}_{uuid_part}"


# ---------------------------------------------------------------------------
# SessionContext（D-13）
# ---------------------------------------------------------------------------


@dataclass
class SessionContext:
    """セッションコンテキスト (D-13).

    AppCore 起動時に一度生成し、セッション全体で共有する。
    セッション終了まで同じ session_id を使い続ける。

    Attributes:
        session_id: ハイブリッド session_id（YYYYMMDD_HHMM_xxxxxxxx）。
        turns: 会話ターンのバッファ（user/assistant の dict リスト）。
        message_count: ユーザー発話のカウント（整合性チェック間隔の計算に使用）。
    """

    session_id: str = field(default_factory=generate_session_id)
    turns: list[dict[str, str]] = field(default_factory=list)
    message_count: int = 0


# ---------------------------------------------------------------------------
# T-13: 整合性チェック（D-8）
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConsistencyHit:
    """整合性チェックのヒット記録 (D-8).

    Attributes:
        type_id: 類型 ID（1: キャラクター幻覚、2: 行動曖昧性、3: 知識忘却）。
        type_name: 類型名。
        pattern: マッチしたパターン文字列。
    """

    type_id: int
    type_name: str
    pattern: str


_HALLUCINATION_PATTERNS: list[str] = [
    r"私はAIです",
    r"私はアシスタントです",
    r"私は言語モデルです",
    r"ChatGPT",
    r"Claude",
    r"Gemini",
    r"anthropic",
    r"OpenAI",
    r"私はプログラムされた",
    r"AIとして",
    r"言語モデルとして",
]

_AMBIGUITY_PATTERNS: list[str] = [
    r"了解しました",
    r"承知しました",
    r"ご質問にお答えします",
    r"について説明します",
    r"以下にまとめます",
    r"ご要望に応じて",
    r"お役に立てれば",
]

_DEGRADATION_PATTERNS: list[str] = [
    r"答えられません",
    r"回答できません",
    r"その情報は持っていません",
    r"私の能力を超えています",
    r"対応できかねます",
]

_CONSISTENCY_RULES: dict[int, tuple[str, list[str]]] = {
    1: ("character_hallucination", _HALLUCINATION_PATTERNS),
    2: ("action_ambiguity", _AMBIGUITY_PATTERNS),
    3: ("knowledge_degradation", _DEGRADATION_PATTERNS),
}

# 公開エイリアス（tasks.md 仕様名準拠、T-15）
CHARACTER_HALLUCINATION_PATTERNS = _HALLUCINATION_PATTERNS
ACTION_AMBIGUITY_PATTERNS = _AMBIGUITY_PATTERNS
KNOWLEDGE_DEGRADATION_PATTERNS = _DEGRADATION_PATTERNS


def check_consistency_rules(response: str) -> list[ConsistencyHit]:
    """ルールベース後処理パターンマッチング (D-8 Section 5.4).

    LLM 応答テキストに整合性チェックパターンが含まれているか検査する。
    マッチしたパターンごとに ConsistencyHit を生成する。
    Phase 1 では再生成は行わず、ログ記録のみに使用する。

    Args:
        response: LLM の応答テキスト。

    Returns:
        マッチしたパターンの ConsistencyHit リスト（マッチなしなら空リスト）。
    """
    hits: list[ConsistencyHit] = []
    for type_id, (type_name, patterns) in _CONSISTENCY_RULES.items():
        for pattern in patterns:
            if re.search(pattern, response):
                hits.append(
                    ConsistencyHit(
                        type_id=type_id,
                        type_name=type_name,
                        pattern=pattern,
                    ),
                )
    return hits


# ---------------------------------------------------------------------------
# T-14: クリックイベント（突っつき）定数 (FR-2.5)
# ---------------------------------------------------------------------------

POKE_EVENT_PREFIX = "[クリックイベント]"

# ---------------------------------------------------------------------------
# T-13: AgentCore（FR-6.1）
# ---------------------------------------------------------------------------

# datetime.weekday() の返り値（0=月曜〜6=日曜）に対応する日本語曜日名
_WEEKDAY_NAMES = ("月", "火", "水", "木", "金", "土", "日")


def _make_session_start_instruction() -> str:
    """現在時刻を含むセッション開始指示を生成する."""
    now = datetime.now()
    time_str = now.strftime("%Y年%m月%d日 %H時%M分")
    weekday = _WEEKDAY_NAMES[now.weekday()]
    return (
        f"セッションが開始されました。現在は{time_str}（{weekday}曜日）です。"
        "キャラクターとして、時間帯や曜日に合った自然な挨拶をしてください。"
        "短く、キャラクターらしい一言で構いません。"
    )


class AgentCore:
    """ReAct ループ本体 + セッション管理 (FR-6.1).

    process_turn() が1ターンの処理を行う:
        1. FTS5 検索（Cold Memory 取得）
        2. message_count インクリメント + consistency_check_active 判定
        3. SystemPrompt + Messages 構築
        4. LLM 呼び出し
        5. 後処理（observations 書込、整合性チェック、ターン記録）

    Attributes:
        session_context: セッション状態。
        session_start_message: セッション開始時の挨拶テキスト。
        consistency_hit_count: セッション開始からの整合性チェックヒット累計数（T-15）。
    """

    def __init__(
        self,
        config: AppConfig,
        db_conn: sqlite3.Connection,
        llm_client: LLMProtocol,
        persona_system: PersonaSystem,
        prompt_builder: PromptBuilder,
        *,
        data_dir: Path | None = None,
        trends_manager: TrendsProposalManager | None = None,
    ) -> None:
        self._config = config
        self._db_conn = db_conn
        self._llm_client: LLMProtocol = llm_client
        self._persona_system = persona_system

        self.session_context = SessionContext()
        self.session_start_message = ""
        self.consistency_hit_count = 0

        self._prompt_builder = prompt_builder

        # W-T25: ファイルパス（human_block / trends 更新用）
        self._data_dir = data_dir
        self._human_block_path = data_dir / "human_block.md" if data_dir else None
        self._trends_path = (
            data_dir / "personality_trends.md" if data_dir else None
        )

        # W-T25: TrendsProposalManager（セッション開始時にトリガー評価）
        self._trends_manager = trends_manager

    def generate_session_start_message(self) -> str:
        """セッション開始メッセージを LLM で生成する.

        Returns:
            生成された挨拶テキスト。
        """
        system_prompt = self._prompt_builder.build_system_prompt()
        messages = [{"role": "user", "content": _make_session_start_instruction()}]
        response = self._llm_client.send_message_for_purpose(
            system=system_prompt,
            messages=messages,
            purpose="conversation",
        )
        self.session_start_message = response
        return response

    def process_turn(self, user_input: str) -> str:
        """ReAct ループの1ターンを処理する (FR-6.1).

        Args:
            user_input: ユーザーの入力テキスト。

        Returns:
            マスコットの応答テキスト。
        """
        # 1. message_count インクリメント
        self.session_context.message_count += 1

        # 2. consistency_check_active 判定 (D-8 Section 5.1)
        interval = self._config.memory.consistency_interval
        if interval > 0:
            consistency_check_active = (
                self.session_context.message_count % interval == 0
            )
        else:
            consistency_check_active = False

        # 3. FTS5 検索（Cold Memory 取得）
        try:
            cold_memories = search_observations_fts(
                self._db_conn, user_input,
                top_k=self._config.memory.cold_top_k,
            )
        except Exception:
            logger.warning("FTS5 検索失敗（Cold Memory スキップ）", exc_info=True)
            cold_memories = None

        # 4. SystemPrompt + Messages 構築（トランケートあり、D-18 FR-8.7）
        purpose = "poke" if user_input.startswith(POKE_EVENT_PREFIX) else "conversation"
        system_prompt, messages = self._prompt_builder.build_with_truncation(
            session_start_message=self.session_start_message,
            turns=self.session_context.turns,
            latest_input=user_input,
            cold_memories=cold_memories,
            model=get_model(self._config, purpose),
            max_tokens_for_output=get_max_tokens(self._config, purpose),
            consistency_check_active=consistency_check_active,
        )

        # 5. LLM 呼び出し — クリックイベントなら purpose="poke" (FR-2.5)
        response = self._llm_client.send_message_for_purpose(
            system=system_prompt,
            messages=messages,
            purpose=purpose,
        )

        # 6. observations 即時書込 (FR-3.7)
        try:
            now_user = time.time()
            save_observation(
                self._db_conn, user_input, "user", now_user,
                session_id=self.session_context.session_id,
            )
            now_mascot = time.time()
            save_observation(
                self._db_conn, response, "mascot", now_mascot,
                session_id=self.session_context.session_id,
            )
        except Exception:
            logger.error(
                "observations 書込失敗（応答は返却を継続）",
                exc_info=True,
            )

        # 7. 整合性チェック（D-8 ルールベース後処理）
        hits = check_consistency_rules(response)
        self.consistency_hit_count += len(hits)
        for hit in hits:
            logger.warning(
                "consistency_check: type=%d (%s), session_id=%s, "
                "message_count=%d, session_total=%d, pattern=%r",
                hit.type_id,
                hit.type_name,
                self.session_context.session_id,
                self.session_context.message_count,
                self.consistency_hit_count,
                hit.pattern,
            )

        # 8. ターン記録
        self.session_context.turns.append(
            {"role": "user", "content": user_input},
        )
        self.session_context.turns.append(
            {"role": "assistant", "content": response},
        )

        # 9. human_block 更新マーカーのパースと適用 (T-17)
        self._apply_human_block_updates(response)

        # 10. personality_trends 承認フロー (T-16)
        self._handle_trends_approval(response, user_input)

        return response

    def _apply_human_block_updates(self, response: str) -> None:
        """LLM 応答から human_block 更新マーカーを抽出し適用する (T-17)."""
        if self._human_block_path is None:
            return
        updates = parse_human_block_updates(response)
        for update in updates:
            valid, reason = validate_update(update)
            if not valid:
                logger.info("human_block 更新をスキップ: %s", reason)
                continue
            try:
                self._persona_system.update_human_block(
                    self._human_block_path,
                    update.section,
                    update.content,
                )
                logger.info(
                    "human_block 更新: section=%s", update.section,
                )
            except Exception:
                logger.error(
                    "human_block 更新失敗: path=%s, section=%s",
                    self._human_block_path, update.section,
                    exc_info=True,
                )

    def _handle_trends_approval(self, response: str, user_input: str) -> None:
        """personality_trends 承認フローを処理する (T-16)."""
        if self._trends_manager is None or self._trends_path is None:
            return

        self._trends_manager.parse_proposal_from_response(
            response, self.session_context.message_count,
        )

        result = self._trends_manager.judge_approval(
            user_input, self.session_context.message_count,
        )

        if result == "approved":
            proposal = self._trends_manager.get_approved_proposal()
            if proposal is not None:
                entry = self._trends_manager.format_entry_for_trends(proposal)
                try:
                    self._persona_system.append_personality_trends(
                        self._trends_path,
                        proposal.section,
                        entry,
                    )
                    logger.info(
                        "personality_trends 追記: section=%s",
                        proposal.section,
                    )
                except Exception:
                    logger.error("personality_trends 追記失敗", exc_info=True)
