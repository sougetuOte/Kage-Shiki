"""personality_trends 承認フロー テスト (T-16, FR-4.6, D-14).

FR チェックリスト:
  FR-4.6: personality_trends.md を読み込み、AI は変更提案のみ行う（直接書き込み禁止）
          AI の提案がテキストで表示され、ユーザー承認後に追記される

対応設計: D-14（ルールベーストリガー + 通常対話内提案 + キーワード承認判定）

テストカバレッジ対象:
  - T1 トリガー: 同一テーマが 3日以上登場
  - T2 トリガー: 感情キーワードが過半数の日に登場
  - セッション内最大2件制限
  - 承認判定: 肯定・否定・否定修飾・タイムアウト
  - 提案パース: デリミタあり/なし、種別パース
  - フォーマット: T1/T2/T3 の追記フォーマット
  - 履歴フォーマット: 承認/却下
"""
from kage_shiki.agent.trends_proposal import (
    TrendsProposal,
    TrendsProposalManager,
)

# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------

def make_day_summaries(texts: list[str]) -> list[dict[str, str]]:
    """テスト用 day_summaries を生成する."""
    return [
        {"date": f"2026-03-{i+1:02d}", "summary": text}
        for i, text in enumerate(texts)
    ]


def make_proposal(
    trigger_type: str = "T1",
    section: str = "関係性の変化",
    content: str = "最近Pythonの話で盛り上がることが多い",
    proposed_at_turn: int = 0,
) -> TrendsProposal:
    """テスト用 TrendsProposal を生成する."""
    return TrendsProposal(
        trigger_type=trigger_type,
        section=section,
        content=content,
        proposed_at_turn=proposed_at_turn,
    )


# ---------------------------------------------------------------------------
# TestTrendsProposalManagerEvaluateTriggers
# ---------------------------------------------------------------------------

class TestTrendsProposalManagerEvaluateTriggers:
    """evaluate_triggers のテスト."""

    def test_t1_triggers_on_3_day_theme(self) -> None:
        """同一テーマが 3日以上登場すると T1 が発火し、プロンプト追加指示を返す."""
        manager = TrendsProposalManager()
        # 「料理」という日本語テーマが 3日連続で登場
        summaries = make_day_summaries([
            "今日は料理の話で盛り上がった",
            "また料理について語り合った",
            "料理のレシピを教えてもらった",
        ])
        result = manager.evaluate_triggers(
            day_summaries=summaries,
            warm_days=7,
            trends_content="",
        )
        assert result is not None
        assert "今ターンの追加指示" in result
        assert "personality_trends_proposal" in result

    def test_t1_no_trigger_under_3_days(self) -> None:
        """同一テーマが 2日以下の場合 T1 は発火しない."""
        manager = TrendsProposalManager()
        summaries = make_day_summaries([
            "今日は料理の話で盛り上がった",
            "また料理について語り合った",
            "全く別の話をした",
        ])
        result = manager.evaluate_triggers(
            day_summaries=summaries,
            warm_days=7,
            trends_content="",
        )
        # T2 も発火しなければ None
        assert result is None

    def test_t1_no_trigger_if_already_in_trends(self) -> None:
        """検出テーマが既に trends_content に含まれている場合 T1 は発火しない."""
        manager = TrendsProposalManager()
        summaries = make_day_summaries([
            "今日はPythonの勉強をした",
            "Pythonのコードを書いた",
            "Pythonについて話し合った",
        ])
        # trends_content に "Python" が記載済み
        result = manager.evaluate_triggers(
            day_summaries=summaries,
            warm_days=7,
            trends_content="### 関係性の変化\n最近Pythonの話をよくする",
        )
        assert result is None

    def test_t2_triggers_on_positive_emotion(self) -> None:
        """ポジティブ感情が warm_days // 2 以上の日に登場すると T2 が発火する."""
        manager = TrendsProposalManager()
        # 4日中 2日（warm_days=4, threshold=2）にポジティブキーワード
        summaries = make_day_summaries([
            "今日は嬉しいことがあった",
            "楽しかった一日",
            "普通の日",
            "普通の日",
        ])
        result = manager.evaluate_triggers(
            day_summaries=summaries,
            warm_days=4,
            trends_content="",
        )
        assert result is not None
        assert "感情" in result or "personality_trends_proposal" in result

    def test_t2_no_trigger_under_threshold(self) -> None:
        """ポジティブ感情が閾値未満の場合 T2 は発火しない."""
        manager = TrendsProposalManager()
        # 4日中 1日（threshold=2）のみポジティブキーワード
        # T1 が誤発火しないよう、各日異なる1語サマリーを使用
        summaries = make_day_summaries([
            "今日は嬉しいことがあった",
            "作業した",
            "散歩した",
            "読書した",
        ])
        result = manager.evaluate_triggers(
            day_summaries=summaries,
            warm_days=4,
            trends_content="",
        )
        assert result is None

    def test_max_proposals_limit(self) -> None:
        """セッション内 max_proposals_per_session（2件）に達したら発火しない."""
        manager = TrendsProposalManager()
        manager.proposal_count = 2  # 上限到達済み
        summaries = make_day_summaries([
            "今日はPythonの勉強をした",
            "Pythonのコードを書いた",
            "Pythonについて話し合った",
        ])
        result = manager.evaluate_triggers(
            day_summaries=summaries,
            warm_days=7,
            trends_content="",
        )
        assert result is None


# ---------------------------------------------------------------------------
# TestJudgeApproval
# ---------------------------------------------------------------------------

class TestJudgeApproval:
    """judge_approval のテスト."""

    def _manager_with_proposal(self, proposed_at_turn: int = 0) -> TrendsProposalManager:
        manager = TrendsProposalManager()
        manager.pending_proposal = make_proposal(proposed_at_turn=proposed_at_turn)
        return manager

    def test_approval_on_yes(self) -> None:
        """「はい」で承認が返る."""
        manager = self._manager_with_proposal()
        assert manager.judge_approval("はい", message_count=1) == "approved"

    def test_approval_on_ok(self) -> None:
        """「OK」で承認が返る."""
        manager = self._manager_with_proposal()
        assert manager.judge_approval("OK", message_count=1) == "approved"

    def test_approval_on_shounin(self) -> None:
        """「承認」で承認が返る."""
        manager = self._manager_with_proposal()
        assert manager.judge_approval("承認", message_count=1) == "approved"

    def test_rejection_on_kyakka(self) -> None:
        """「却下」で却下が返る."""
        manager = self._manager_with_proposal()
        assert manager.judge_approval("却下", message_count=1) == "rejected"

    def test_rejection_on_iranai(self) -> None:
        """「いらない」で却下が返る."""
        manager = self._manager_with_proposal()
        assert manager.judge_approval("いらない", message_count=1) == "rejected"

    def test_negative_modifier_blocks_approval(self) -> None:
        """「承認できない」では承認しない（否定修飾による誤マッチ防止）."""
        manager = self._manager_with_proposal()
        result = manager.judge_approval("承認できない", message_count=1)
        assert result != "approved"

    def test_expired_after_timeout(self) -> None:
        """提案から 3ターン超過後に expired が返る."""
        manager = self._manager_with_proposal(proposed_at_turn=0)
        # timeout_turns=3 なので message_count=4 で expired
        assert manager.judge_approval("はい", message_count=4) == "expired"

    def test_pending_on_unrelated_input(self) -> None:
        """承認・却下どちらでもない入力で pending が返る."""
        manager = self._manager_with_proposal()
        assert manager.judge_approval("今日は天気がいいね", message_count=1) == "pending"

    def test_none_when_no_proposal(self) -> None:
        """提案がない状態では none が返る."""
        manager = TrendsProposalManager()
        assert manager.judge_approval("はい", message_count=1) == "none"


# ---------------------------------------------------------------------------
# TestParseProposalFromResponse
# ---------------------------------------------------------------------------

class TestParseProposalFromResponse:
    """parse_proposal_from_response のテスト."""

    _VALID_RESPONSE = (
        "最近の会話を振り返ってみると、\n"
        "---personality_trends_proposal---\n"
        "種別: 関係性の変化\n"
        "内容: 最近Pythonの話で盛り上がることが多い\n"
        "---proposal_end---\n"
        "記録に残してもいいですか？"
    )

    def test_parses_valid_proposal(self) -> None:
        """正常なデリミタ付き応答から提案をパースできる."""
        manager = TrendsProposalManager()
        proposal = manager.parse_proposal_from_response(self._VALID_RESPONSE, message_count=0)
        assert proposal is not None
        assert proposal.content == "最近Pythonの話で盛り上がることが多い"
        assert proposal.proposed_at_turn == 0

    def test_returns_none_on_missing_delimiter(self) -> None:
        """デリミタがない応答では None を返す."""
        manager = TrendsProposalManager()
        proposal = manager.parse_proposal_from_response("ただの返答です", message_count=0)
        assert proposal is None

    def test_parses_section_type(self) -> None:
        """種別 '感情の傾向' が正しくパースされ trigger_type が T2 になる."""
        response = (
            "---personality_trends_proposal---\n"
            "種別: 感情の傾向\n"
            "内容: 最近ポジティブな会話が続いている\n"
            "---proposal_end---"
        )
        manager = TrendsProposalManager()
        proposal = manager.parse_proposal_from_response(response, message_count=2)
        assert proposal is not None
        assert proposal.trigger_type == "T2"
        assert proposal.section == "感情の傾向"
        assert proposal.proposed_at_turn == 2


# ---------------------------------------------------------------------------
# TestFormatEntryForTrends
# ---------------------------------------------------------------------------

class TestFormatEntryForTrends:
    """format_entry_for_trends のテスト."""

    def test_t1_format(self) -> None:
        """T1（関係性の変化）は ### ヘッダー + 本文で追記される."""
        manager = TrendsProposalManager()
        proposal = make_proposal(
            trigger_type="T1",
            section="関係性の変化",
            content="最近Pythonの話で盛り上がることが多い",
        )
        entry = manager.format_entry_for_trends(proposal)
        assert "### [" in entry
        assert "関係性の変化" in entry
        assert "最近Pythonの話で盛り上がることが多い" in entry

    def test_t3_format_with_bullet(self) -> None:
        """T3（口癖候補）は箇条書き（- ）付きでフォーマットされる."""
        manager = TrendsProposalManager()
        proposal = make_proposal(
            trigger_type="T3",
            section="新しい口癖候補（supplementary_styles）",
            content="「ふむふむ」をよく使うようになった",
        )
        entry = manager.format_entry_for_trends(proposal)
        assert "- " in entry
        assert "「ふむふむ」" in entry


# ---------------------------------------------------------------------------
# TestFormatHistoryEntry
# ---------------------------------------------------------------------------

class TestFormatHistoryEntry:
    """format_history_entry のテスト."""

    def test_approved_history(self) -> None:
        """承認履歴は '承認' を含む文字列になる."""
        manager = TrendsProposalManager()
        proposal = make_proposal(content="最近Pythonの話で盛り上がることが多い")
        entry = manager.format_history_entry(proposal, "approved")
        assert "承認" in entry
        assert "最近Pythonの話で盛り上がることが多い" in entry

    def test_rejected_history(self) -> None:
        """却下履歴は '却下' を含む文字列になる."""
        manager = TrendsProposalManager()
        proposal = make_proposal(content="最近Pythonの話で盛り上がることが多い")
        entry = manager.format_history_entry(proposal, "rejected")
        assert "却下" in entry


# ---------------------------------------------------------------------------
# カバレッジ補完テスト (R-5: エラーパス・境界値)
# ---------------------------------------------------------------------------

class TestCoverageComplement:
    """未カバーパスの補完テスト."""

    def test_t1_no_trigger_on_empty_summaries(self) -> None:
        """day_summaries が 2件以下では T1 は発火しない（< 3 チェック）."""
        manager = TrendsProposalManager()
        summaries = make_day_summaries(["料理の話をした", "料理について語った"])
        result = manager.evaluate_triggers(
            day_summaries=summaries,
            warm_days=7,
            trends_content="",
        )
        assert result is None

    def test_t2_no_trigger_on_empty_summaries(self) -> None:
        """day_summaries が空の場合 T2 は発火しない."""
        manager = TrendsProposalManager()
        result = manager.evaluate_triggers(
            day_summaries=[],
            warm_days=7,
            trends_content="",
        )
        assert result is None

    def test_t2_triggers_on_negative_emotion(self) -> None:
        """ネガティブ感情が閾値以上の日に登場すると T2（ネガティブ方向）が発火する."""
        manager = TrendsProposalManager()
        summaries = make_day_summaries([
            "今日は悲しいことがあった",
            "寂しかった一日",
            "読書した",
            "散歩した",
        ])
        result = manager.evaluate_triggers(
            day_summaries=summaries,
            warm_days=4,
            trends_content="",
        )
        assert result is not None
        assert "ネガティブ" in result or "personality_trends_proposal" in result

    def test_get_approved_proposal_clears_pending(self) -> None:
        """get_approved_proposal が pending_proposal をクリアして返す."""
        manager = TrendsProposalManager()
        proposal = make_proposal()
        manager.pending_proposal = proposal
        retrieved = manager.get_approved_proposal()
        assert retrieved is proposal
        assert manager.pending_proposal is None

    def test_get_approved_proposal_returns_none_when_no_pending(self) -> None:
        """提案がない状態では get_approved_proposal は None を返す."""
        manager = TrendsProposalManager()
        assert manager.get_approved_proposal() is None
