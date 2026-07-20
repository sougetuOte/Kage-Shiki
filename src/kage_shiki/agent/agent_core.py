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

from kage_shiki.agent.agentic_search import AgenticSearchEngine
from kage_shiki.agent.autonomous_prompt import (
    AUTONOMOUS_PROMPTS,
    CURIOSITY_COMPLETION_PROMPT,
)
from kage_shiki.agent.desire_worker import DesireWorker
from kage_shiki.agent.human_block_updater import parse_human_block_updates, validate_update
from kage_shiki.agent.llm_client import LLMProtocol
from kage_shiki.agent.prompt_builder import PromptBuilder  # re-export for backward compat
from kage_shiki.agent.trends_proposal import TrendsProposalManager
from kage_shiki.core.config import AppConfig, get_max_tokens, get_model
from kage_shiki.memory.db import (
    count_pending_curiosity_targets,
    create_curiosity_target,
    curiosity_topic_exists,
    get_pending_targets,
    get_recent_day_summaries,
    recover_stale_searching_targets,
    save_observation_safe,
    search_observations_fts,
    update_target_status,
)
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
        desire_worker: DesireWorker | None = None,
        search_engine: AgenticSearchEngine | None = None,
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

        # Phase 2b Wave 2: 自律発言用 DesireWorker 参照（前後アクティブフラグチェックに使用）。
        # main.py 統合は Wave 5 (Task 5-1) で行い、それまで handle_autonomous_turn は
        # 呼び出し元未接続。
        self._desire_worker = desire_worker

        # Phase 2b Wave 3 (Task 3-2): curiosity 分岐で使用する AgenticSearch エンジン。
        # main.py 統合は Wave 5 で HaikuEngine が注入される。Wave 3 では None のとき
        # curiosity 分岐は None 返却で短絡する (テストは Mock を注入)。
        self._search_engine = search_engine

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
            save_observation_safe(
                self._db_conn, user_input, "user", now_user,
                session_id=self.session_context.session_id,
            )
            now_mascot = time.time()
            save_observation_safe(
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

    # ---------------------------------------------------------------------------
    # Phase 2b Wave 2: handle_autonomous_turn (FR-9.3, FR-9.4, FR-9.5, FR-9.9)
    #
    # 呼び出し元: 現状なし。Wave 5 (Task 5-1, main.py の _run_background_loop 拡張)
    # で autonomous_queue 経由で呼び出される。それまでは単体テストでのみ実行される
    # (デッドコードに見えるが Wave 5 で接続される予定)。
    # ---------------------------------------------------------------------------

    _AUTONOMOUS_TRIGGER_INPUT = "(独り言)"
    _AUTONOMOUS_PURPOSE = "autonomous_talk"
    _REFLECT_DAY_SUMMARY_LOOKBACK = 1  # reflect 用に取得する day_summary 日数

    def handle_autonomous_turn(self, desire_type: str) -> str | None:
        """欲求閾値超過時に自律発言テキストを生成する (FR-9.3, FR-9.4).

        既存の ReAct ループ (`PromptBuilder.build_with_truncation`) を
        `autonomous_prompt` 引数経由で再利用する (C-4)。仕様書の
        `autonomous_turn=True` 表現は、本実装では `autonomous_prompt` を
        SystemPrompt 末尾 (S8) に注入することで等価機能を提供する。

        active フラグの LLM 前後二重チェックにより、ユーザー入力 (reset_all) で
        進行中の自律行動が破棄される (FR-9.5 / design.md L466-479)。

        LLM 呼び出し例外は呼び出し元 (`_run_background_loop`) に伝播させる
        (集約エラーハンドリング前提)。

        Wave 3 Task 3-2 追加 (HGA A-3):
            終端 (成功・破棄・失敗の全経路) で `_desire_worker.reset(desire_type)` を
            呼び active フラグを False に戻す (要件書 Section 4.2「実行後 False」)。
            try/finally で保証する。curiosity 分岐は `_handle_curiosity_pipeline()`
            に委譲する (design.md §5.4)。

        Args:
            desire_type: "talk" | "curiosity" | "reflect" | "rest"

        Returns:
            生成した自律発言テキスト。以下の場合は None:
                - desire_worker が未注入
                - desire_type が AUTONOMOUS_PROMPTS に存在しない
                - LLM 前または後で active=False (破棄)
                - curiosity で pending なし / search_engine 未注入 / パイプライン失敗

        Raises:
            Exception: LLM 呼び出し例外は呼び出し元に伝播。
        """
        # ガード 1: desire_worker 未注入 (finally での reset 呼び出しを回避)
        if self._desire_worker is None:
            return None

        # ガード 2: 無効な desire_type (finally での reset 前に KeyError を避ける)
        prompt_template = AUTONOMOUS_PROMPTS.get(desire_type)
        if prompt_template is None:
            return None

        try:
            # curiosity 分岐: AgenticSearch パイプライン本実装 (Task 3-2 / design.md §5.4)
            if desire_type == "curiosity":
                return self._handle_curiosity_pipeline()

            # talk / reflect / rest 分岐: 単一 LLM 呼び出しの自律発言
            # 前チェック: active フラグ
            # AUTONOMOUS_PROMPTS のキー集合と DesireWorker.desires のキー集合は同期
            # している (TestAutonomousPromptsDesireWorkerSync で不変条件を検証)。
            # 同期が破綻した場合は KeyError で早期失敗させる (R-13: silent skip 禁止)。
            state = self._desire_worker.get_state()
            if not state.desires[desire_type].active:
                return None

            # reflect: day_summary を DB から取得して {day_summary} を置換 (FR-9.9)
            autonomous_prompt = self._build_autonomous_prompt(
                desire_type, prompt_template,
            )

            response = self._generate_autonomous_tweet(autonomous_prompt)

            # 後チェック: LLM 実行中に reset_all() が呼ばれていれば結果を破棄
            post_state = self._desire_worker.get_state()
            if not post_state.desires[desire_type].active:
                return None

            return response
        finally:
            # HGA A-3: 成功・破棄・失敗の全経路で active を False に戻す。
            # 未知の desire_type は KeyError で即時失敗する (R-13 準拠)。
            self._desire_worker.reset(desire_type)

    def _generate_autonomous_tweet(self, autonomous_prompt: str) -> str:
        """autonomous_prompt を SystemPrompt に注入して LLM でつぶやきを生成する.

        curiosity パイプラインの starting/completion tweet および talk/reflect/rest
        の自律発言で共用するヘルパ (build_with_truncation 経由・purpose=autonomous_talk)。

        Args:
            autonomous_prompt: SystemPrompt 末尾に注入する独り言指示テンプレート。

        Returns:
            LLM が生成したつぶやきテキスト。
        """
        purpose = self._AUTONOMOUS_PURPOSE
        system_prompt, messages = self._prompt_builder.build_with_truncation(
            session_start_message=self.session_start_message,
            turns=self.session_context.turns,
            latest_input=self._AUTONOMOUS_TRIGGER_INPUT,
            cold_memories=None,
            model=get_model(self._config, purpose),
            max_tokens_for_output=get_max_tokens(self._config, purpose),
            autonomous_prompt=autonomous_prompt,
        )
        return self._llm_client.send_message_for_purpose(
            system=system_prompt,
            messages=messages,
            purpose=purpose,
        )

    def _should_abort_autonomous(self, desire_type: str) -> bool:
        """パイプラインの各ステージ境界で active フラグを確認する (HGA A-4 helper).

        ユーザー入力が発生して reset_all() が呼ばれていれば True を返す。
        パイプライン多段化時の active チェック挿入漏れを防ぐため共通化する。

        Args:
            desire_type: 確認する欲求タイプ。

        Returns:
            active=False (中断すべき) なら True。desire_worker が None なら True (中断)。
        """
        if self._desire_worker is None:
            return True
        state = self._desire_worker.get_state()
        return not state.desires[desire_type].active

    def _handle_curiosity_pipeline(self) -> str | None:
        """curiosity 欲求の AgenticSearch パイプラインを実行する (Task 3-2 / design.md §5.4).

        HGA A-1〜A-7 対応:
            A-1: 起動時に searching 残骸を pending に復旧
            A-2: 派生テーマ登録前に重複チェック + pending 上限チェック (2 段ガード)
            A-3: 呼び出し元 (handle_autonomous_turn) の finally で reset("curiosity")
            A-4: 各ステージ境界で _should_abort_autonomous → 中断時 status を pending に戻す
            A-5: HaikuEngine 側でインジェクション防御 (実装済み)
            A-6: HaikuEngine 側で decompose 0 件時に topic に fallback (実装済み)
            A-7: 成功時の完了つぶやきを必須生成

        Returns:
            完了つぶやきテキスト。以下の場合は None:
                - search_engine 未注入
                - 前チェック時点で active=False
                - pending トピックなし
                - パイプライン中断 (abort)
                - パイプライン例外 (failed)

        Raises:
            例外: パイプライン内例外は catch して failed に遷移し None を返すため
                呼び出し元には伝播しない (呼び出し元 finally での reset 保証のため)。
        """
        # ガード: search_engine 未注入 (Wave 5 で main.py が HaikuEngine を注入する)
        if self._search_engine is None:
            logger.debug(
                "curiosity: search_engine 未注入のため pipeline をスキップ "
                "(Wave 5 で main.py 統合)",
            )
            return None

        # 前チェック: active
        if self._should_abort_autonomous("curiosity"):
            return None

        # HGA A-1: パイプライン起動時に searching 残骸を復旧
        recover_stale_searching_targets(self._db_conn)

        # priority 昇順で pending 1 件取得
        pending = get_pending_targets(self._db_conn, limit=1)
        if not pending:
            # FR-9.6 (2): pending なしなら何もしない (つぶやきなし)
            return None

        target = pending[0]
        tid = int(target["id"])
        topic = str(target["topic"])

        # 「調べ始める」つぶやき生成 (design.md §5.4: status 変更より先)
        # Wave 3 は main.py 未接続のため戻り値には含めない。Wave 5 で
        # main.py が LLM 呼び出しを傍観して response_queue に put する経路を追加する。
        _starting_tweet = self._generate_autonomous_tweet(
            AUTONOMOUS_PROMPTS["curiosity"],
        )

        # status → searching (以降の abort では pending に戻す — HGA A-4)
        update_target_status(self._db_conn, tid, "searching")

        try:
            # ステージ境界 abort チェック #1: decompose 前
            if self._should_abort_autonomous("curiosity"):
                update_target_status(self._db_conn, tid, "pending")
                return None

            queries = self._search_engine.decompose_query(topic)

            # ステージ境界 abort チェック #2: search_parallel 前
            if self._should_abort_autonomous("curiosity"):
                update_target_status(self._db_conn, tid, "pending")
                return None

            results_lists = self._search_engine.search_parallel(queries)
            all_results = [r for sub in results_lists for r in sub]

            # ステージ境界 abort チェック #3: summarize 前
            if self._should_abort_autonomous("curiosity"):
                update_target_status(self._db_conn, tid, "pending")
                return None

            summary = self._search_engine.summarize(topic, all_results)

            # ステージ境界 abort チェック #4: extract_noise 前
            if self._should_abort_autonomous("curiosity"):
                update_target_status(self._db_conn, tid, "pending")
                return None

            noise_topics = self._search_engine.extract_noise_topics(all_results)
        except Exception:
            logger.warning(
                "curiosity パイプライン例外, topic=%r → failed",
                topic,
                exc_info=True,
            )
            update_target_status(self._db_conn, tid, "failed")
            return None

        # 成功: done + result_summary 保存
        update_target_status(self._db_conn, tid, "done", result_summary=summary)

        # HGA A-2: 派生テーマ登録 (2 段ガード: 重複チェック + pending 上限チェック)
        max_pending = self._config.agentic_search.max_pending_targets
        for topic_candidate in noise_topics:
            current_pending = count_pending_curiosity_targets(self._db_conn)
            if current_pending >= max_pending:
                logger.warning(
                    "curiosity: pending 件数 %d >= max %d、以降の派生テーマ登録をスキップ",
                    current_pending,
                    max_pending,
                )
                break
            if curiosity_topic_exists(self._db_conn, topic_candidate):
                logger.info(
                    "curiosity: 派生テーマ重複スキップ topic=%r",
                    topic_candidate,
                )
                continue
            create_curiosity_target(
                self._db_conn, topic_candidate, parent_id=tid,
            )

        # HGA A-7: 完了つぶやき必須生成
        completion_prompt = CURIOSITY_COMPLETION_PROMPT.format(summary=summary)
        return self._generate_autonomous_tweet(completion_prompt)

    def _build_autonomous_prompt(
        self,
        desire_type: str,
        prompt_template: str,
    ) -> str:
        """desire_type に応じた autonomous_prompt を構築する.

        reflect の場合は直近の day_summary を取得し {day_summary} を置換する (FR-9.9)。
        day_summary が存在しない場合は空文字列で置換する (LLM 呼び出しは継続)。

        Args:
            desire_type: 欲求タイプ。
            prompt_template: AUTONOMOUS_PROMPTS から取得したテンプレート文字列。

        Returns:
            placeholder 置換済みの autonomous_prompt 文字列。
        """
        if desire_type != "reflect":
            return prompt_template

        try:
            summaries = get_recent_day_summaries(
                self._db_conn, self._REFLECT_DAY_SUMMARY_LOOKBACK,
            )
        except sqlite3.Error:
            # DB エラー (ロック / スキーマ不整合等) のみ握り、AttributeError 等の
            # プログラミングミスは伝播させる (Silent Failure 防止)。
            logger.warning(
                "reflect day_summary 取得失敗、空文字列でフォールバック",
                exc_info=True,
            )
            summaries = []

        if summaries:
            day_summary_text = "\n".join(
                f"{s['date']}: {s['summary']}" for s in summaries
            )
        else:
            day_summary_text = ""

        return prompt_template.format(day_summary=day_summary_text)

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
