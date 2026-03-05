"""personality_trends 承認フロー (T-16, FR-4.6, D-14).

トリガー評価 → プロンプト追加指示生成 → 承認判定 → 追記処理。

設計: D-14（ルールベーストリガー + 通常対話内提案 + キーワード承認判定）
仕様: docs/specs/phase1-mvp/design-d14-personality-trends-approval.md
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# トリガー用キーワード (D-14 Section 5.1)
# ---------------------------------------------------------------------------

POSITIVE_EMOTION_KEYWORDS: list[str] = [
    "嬉しい", "嬉しかった", "楽しい", "楽しかった", "よかった",
    "打ち解け", "仲良く", "ほっとした", "安心", "嬉しそう",
]

NEGATIVE_EMOTION_KEYWORDS: list[str] = [
    "悲しい", "悲しかった", "寂しい", "寂しかった", "落ち込んだ",
    "辛かった", "怒った", "不安", "心配", "つらかった",
]

# ---------------------------------------------------------------------------
# 承認判定パターン (D-14 Section 5.3)
# ---------------------------------------------------------------------------

APPROVAL_PATTERNS: list[str] = [
    r"^承認$", r"^承認します$", r"^承認する$",
    r"^はい$", r"^うん$", r"^いいよ$", r"^いいね$",
    r"^OK$", r"^ok$", r"^そうして$",
    r"^記録して$", r"^記録しといて$", r"^残して$",
    r"承認.*します", r"それ.*いいよ", r"それ.*記録",
]

APPROVAL_NEGATIVE_MODIFIERS: list[str] = [
    r"できない", r"しない", r"いらない", r"要らない",
    r"やめ", r"却下", r"ちがう", r"違う",
]

REJECTION_PATTERNS: list[str] = [
    r"^いや$", r"^いいや$", r"^いやだ$", r"^却下$",
    r"^やめて$", r"^いらない$", r"^要らない$", r"^やめ$",
    r"それはいい",
    r"記録.*しないで",
    r"覚えなくて.*いい",
]

# ---------------------------------------------------------------------------
# T1 トリガー用ストップワード
# 汎用的すぎる語を除外し、具体的なトピックのみを検出する
# ---------------------------------------------------------------------------

_T1_STOP_WORDS: frozenset[str] = frozenset([
    "今日は", "普通の", "普通に", "普通の日", "いつも", "何となく", "なんとなく",
    "ちょっと", "ところで", "とにかく", "とにかくも", "そんな",
    "全体的", "一日中", "その日", "この日", "その後",
    "嬉しいことがあった", "楽しかった一日",
])

# ---------------------------------------------------------------------------
# 提案デリミタ (D-14 Section 5.2)
# ---------------------------------------------------------------------------

_PROPOSAL_START = "---personality_trends_proposal---"
_PROPOSAL_END = "---proposal_end---"

# ---------------------------------------------------------------------------
# 種別マッピング (D-14 Section 5.4)
# ---------------------------------------------------------------------------

_SECTION_MAP: dict[str, str] = {
    "関係性の変化": "関係性の変化",
    "感情の傾向": "感情の傾向",
    "口癖候補": "新しい口癖候補（supplementary_styles）",
}

_TRIGGER_TYPE_MAP: dict[str, str] = {
    "関係性の変化": "T1",
    "感情の傾向": "T2",
    "新しい口癖候補（supplementary_styles）": "T3",
}

_SECTION_LABEL_MAP: dict[str, str] = {
    "T1": "関係性の変化",
    "T2": "感情の傾向",
    "T3": "口癖候補",
}

_RESULT_LABEL_MAP: dict[str, str] = {
    "approved": "承認",
    "rejected": "却下",
    "expired": "保留（タイムアウト）",
}


# ---------------------------------------------------------------------------
# 提案状態
# ---------------------------------------------------------------------------

@dataclass
class TrendsProposal:
    """承認待ち提案の状態."""

    trigger_type: str          # "T1", "T2", "T3"
    section: str               # 追記先セクション名
    content: str               # 提案テキスト（パース済み）
    proposed_at_turn: int      # 提案時の message_count
    timeout_turns: int = 3     # 保留タイムアウト（3ターン）


@dataclass
class TrendsProposalManager:
    """personality_trends 承認フローの管理 (D-14).

    Attributes:
        pending_proposal: 現在の承認待ち提案（None=提案なし）。
        proposal_count: 同一セッション内の提案件数。
        max_proposals_per_session: セッション内最大提案数。
        prompt_addition: 次ターンの SystemPrompt に追加する指示（空=なし）。
    """

    pending_proposal: TrendsProposal | None = None
    proposal_count: int = 0
    max_proposals_per_session: int = 2
    prompt_addition: str = ""
    _proposal_history: list[dict] = field(default_factory=list)

    # ------------------------------------------------------------------
    # トリガー評価
    # ------------------------------------------------------------------

    def evaluate_triggers(
        self,
        day_summaries: list[dict[str, str]],
        warm_days: int,
        trends_content: str,
    ) -> str | None:
        """セッション開始時のトリガー評価 (D-14 Section 5.1).

        Args:
            day_summaries: Warm Memory の day_summary リスト。
            warm_days: config.memory.warm_days 値。
            trends_content: personality_trends.md の現在の内容。

        Returns:
            トリガーされた追加指示テキスト。トリガーなしの場合 None。
        """
        if self.proposal_count >= self.max_proposals_per_session:
            return None

        t1_result = self._check_t1_relationship(day_summaries, trends_content)
        if t1_result:
            self.prompt_addition = t1_result
            return t1_result

        t2_result = self._check_t2_emotion(day_summaries, warm_days, trends_content)
        if t2_result:
            self.prompt_addition = t2_result
            return t2_result

        return None

    def _check_t1_relationship(
        self,
        day_summaries: list[dict[str, str]],
        trends_content: str,
    ) -> str | None:
        """T1 トリガー: 関係性の変化 (D-14 Section 5.1)."""
        if len(day_summaries) < 3:
            return None

        word_days: dict[str, set[str]] = {}
        for ds in day_summaries:
            date = ds["date"]
            words = self._extract_topic_words(ds["summary"])
            for w in words:
                if w not in word_days:
                    word_days[w] = set()
                word_days[w].add(date)

        for word, dates in word_days.items():
            if len(dates) >= 3 and word not in trends_content and word not in _T1_STOP_WORDS:
                return self._build_t1_prompt(word)

        return None

    def _check_t2_emotion(
        self,
        day_summaries: list[dict[str, str]],
        warm_days: int,
        trends_content: str,
    ) -> str | None:
        """T2 トリガー: 感情の傾向変化 (D-14 Section 5.1)."""
        if not day_summaries:
            return None

        threshold = max(1, warm_days // 2)
        positive_days = 0
        negative_days = 0

        for ds in day_summaries:
            summary = ds["summary"]
            if any(kw in summary for kw in POSITIVE_EMOTION_KEYWORDS):
                positive_days += 1
            if any(kw in summary for kw in NEGATIVE_EMOTION_KEYWORDS):
                negative_days += 1

        positive_not_recorded = (
            "ポジティブ" not in trends_content and "打ち解け" not in trends_content
        )
        if positive_days >= threshold and positive_not_recorded:
            return self._build_t2_prompt("ポジティブ")
        if negative_days >= threshold and "ネガティブ" not in trends_content:
            return self._build_t2_prompt("ネガティブ")

        return None

    def _extract_topic_words(self, text: str) -> list[str]:
        """サマリーからトピックワードを抽出する（簡易版、形態素解析なし）.

        助詞・記号で分割後、漢字またはカタカナを含む 2文字以上の語を抽出する。
        形態素解析は使用しない（D-14 Section 5.1 の「Python の Counter を使用」方針）。
        """
        parts = re.split(r"[はがをにのでともへかまよりだったちも、。！？\s\u3000]", text)
        kanji_or_kata = re.compile(r"[\u4E00-\u9FFF\u30A0-\u30FF]")
        result = []
        for part in parts:
            stripped = part.strip()
            if len(stripped) >= 2 and kanji_or_kata.search(stripped):
                result.append(stripped)
        return result

    # ------------------------------------------------------------------
    # プロンプト追加指示生成
    # ------------------------------------------------------------------

    def _build_t1_prompt(self, detected_theme: str) -> str:
        """T1 提案用プロンプト追加指示を生成する (D-14 Section 5.2)."""
        return (
            "【今ターンの追加指示】\n"
            "あなたとユーザーの最近の会話から、関係性に関する傾向が読み取れます。\n"
            "今回の応答の最後（または会話の自然な流れの中）で、以下のフォーマットに従い\n"
            "personality_trends への記録提案を1件行うこと:\n\n"
            f"{_PROPOSAL_START}\n"
            "種別: 関係性の変化\n"
            f"内容: 最近{detected_theme}の話題で盛り上がることが多い\n"
            f"{_PROPOSAL_END}\n\n"
            "提案は自然な会話の流れの中で行い、「記録に残してもいいですか？」等の"
            "キャラクターらしい言葉を添えること。"
        )

    def _build_t2_prompt(self, direction: str) -> str:
        """T2 提案用プロンプト追加指示を生成する (D-14 Section 5.2)."""
        return (
            "【今ターンの追加指示】\n"
            "あなたとユーザーの最近の会話から、感情的な傾向が読み取れます。\n"
            "今回の応答の最後（または会話の自然な流れの中）で、以下のフォーマットに従い\n"
            "personality_trends への記録提案を1件行うこと:\n\n"
            f"{_PROPOSAL_START}\n"
            "種別: 感情の傾向\n"
            f"内容: 最近{direction}な感じの会話が続いている\n"
            f"{_PROPOSAL_END}\n\n"
            "提案はキャラクターの口調に合わせた自然な言葉で行うこと。"
        )

    # ------------------------------------------------------------------
    # 提案パース
    # ------------------------------------------------------------------

    def parse_proposal_from_response(
        self,
        response: str,
        message_count: int,
    ) -> TrendsProposal | None:
        """LLM 応答から提案テキストをパースする (D-14 Section 5.4).

        Args:
            response: LLM 応答テキスト。
            message_count: 現在の message_count（タイムアウト計算用）。

        Returns:
            パースされた提案。デリミタが見つからない場合 None。
        """
        start_idx = response.find(_PROPOSAL_START)
        end_idx = response.find(_PROPOSAL_END)

        if start_idx == -1 or end_idx == -1 or start_idx >= end_idx:
            logger.debug("proposal delimiter not found in response")
            return None

        inner = response[start_idx + len(_PROPOSAL_START):end_idx].strip()

        section = "関係性の変化"
        content = inner

        for line in inner.split("\n"):
            stripped = line.strip()
            if stripped.startswith("種別:") or stripped.startswith("種別："):
                kind = re.split(r"[:：]", stripped, maxsplit=1)[-1].strip()
                if kind in _SECTION_MAP:
                    section = _SECTION_MAP[kind]
                else:
                    logger.warning(
                        "未知の提案種別 '%s' — デフォルト '関係性の変化' にフォールバック", kind,
                    )
                    section = "関係性の変化"
            elif stripped.startswith("内容:") or stripped.startswith("内容："):
                content = re.split(r"[:：]", stripped, maxsplit=1)[-1].strip()

        if section not in _TRIGGER_TYPE_MAP:
            logger.error(
                "未知のセクション '%s' — 提案を破棄", section,
            )
            return
        trigger_type = _TRIGGER_TYPE_MAP[section]

        proposal = TrendsProposal(
            trigger_type=trigger_type,
            section=section,
            content=content,
            proposed_at_turn=message_count,
        )
        self.pending_proposal = proposal
        return proposal

    # ------------------------------------------------------------------
    # 承認判定
    # ------------------------------------------------------------------

    def judge_approval(self, user_input: str, message_count: int) -> str:
        """承認判定 (D-14 Section 5.3).

        Args:
            user_input: ユーザーの入力テキスト。
            message_count: 現在の message_count。

        Returns:
            "approved", "rejected", "pending", "expired", or "none"。
        """
        if self.pending_proposal is None:
            return "none"

        turns_since = message_count - self.pending_proposal.proposed_at_turn
        if turns_since > self.pending_proposal.timeout_turns:
            self._record_history(self.pending_proposal, "expired")
            self.pending_proposal = None
            return "expired"

        text = user_input.strip()

        has_negative = any(
            re.search(p, text) for p in APPROVAL_NEGATIVE_MODIFIERS
        )

        if any(re.search(p, text) for p in REJECTION_PATTERNS):
            self._record_history(self.pending_proposal, "rejected")
            self.pending_proposal = None
            return "rejected"

        if not has_negative and any(re.search(p, text) for p in APPROVAL_PATTERNS):
            self._record_history(self.pending_proposal, "approved")
            self.proposal_count += 1
            # pending_proposal はクリアしない（get_approved_proposal で取り出す）
            return "approved"

        return "pending"

    def get_approved_proposal(self) -> TrendsProposal | None:
        """承認された提案を取得してクリアする."""
        proposal = self.pending_proposal
        self.pending_proposal = None
        return proposal

    # ------------------------------------------------------------------
    # フォーマット
    # ------------------------------------------------------------------

    def format_entry_for_trends(self, proposal: TrendsProposal) -> str:
        """提案を personality_trends.md 追記用にフォーマットする (D-14 Section 5.4).

        Args:
            proposal: 承認された提案。

        Returns:
            追記する Markdown テキスト。
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        if proposal.trigger_type in _SECTION_LABEL_MAP:
            label = _SECTION_LABEL_MAP[proposal.trigger_type]
        else:
            logger.warning(
                "未知のトリガータイプ '%s' — ラベルを '関係性の変化' にフォールバック",
                proposal.trigger_type,
            )
            label = "関係性の変化"

        if proposal.trigger_type == "T3":
            return f"### [{date_str}] {label}\n\n- {proposal.content}"
        return f"### [{date_str}] {label}\n\n{proposal.content}"

    def format_history_entry(self, proposal: TrendsProposal, result: str) -> str:
        """提案履歴エントリをフォーマットする (D-14 Section 5.5).

        Args:
            proposal: 提案オブジェクト。
            result: "approved", "rejected", or "expired"。

        Returns:
            履歴行テキスト。
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        if result in _RESULT_LABEL_MAP:
            result_label = _RESULT_LABEL_MAP[result]
        else:
            logger.warning(
                "未知の結果種別 '%s' — そのままフォールバック", result,
            )
            result_label = result
        label = _SECTION_LABEL_MAP.get(proposal.trigger_type, "不明")
        return f"- [{date_str}] {label}: 「{proposal.content}」→ {result_label}"

    # ------------------------------------------------------------------
    # 内部ユーティリティ
    # ------------------------------------------------------------------

    def _record_history(self, proposal: TrendsProposal, result: str) -> None:
        """提案履歴を内部に記録する."""
        self._proposal_history.append({
            "trigger_type": proposal.trigger_type,
            "content": proposal.content,
            "result": result,
            "timestamp": datetime.now().isoformat(),
        })
