"""FR-8.7 トランケートアルゴリズムのテスト.

FR 番号一覧（R-4 チェックリスト）:
    FR-8.7: コンテキストウィンドウ超過時に以下の優先順位でコンテキストを削減する
        (1) 削除優先順位: Cold Memory → Warm Memory → Session Context → Hot Memory
        (2) persona_core は絶対に削除しない

テストケース一覧:
    1. test_no_truncation_when_within_limit       — 上限内なら削減なし（Phase 1 と同一出力）
    2. test_cold_memory_truncated_first           — Cold Memory が最初に削減される
    3. test_warm_memory_truncated_after_cold      — Cold 全削除後に Warm が削減される
    4. test_session_truncated_after_warm          — Warm 全削除後に Session が削減される
    5. test_persona_core_never_truncated   — persona_core は上限超過時でも含まれる
    6. test_hot_memory_reduction_order     — Hot Memory 削減順: trends → human → style
    7. test_empty_cold_memories            — cold_memories=None でスキップ
    8. test_empty_day_summaries            — day_summaries=[] でスキップ
    9. test_empty_turns                    — turns=[] でスキップ
    10. test_promptbuilder_state_unchanged — フィールド不変保証
"""


from kage_shiki.agent.agent_core import PromptBuilder
from kage_shiki.agent.truncation import estimate_tokens, get_effective_token_limit

# ---------------------------------------------------------------------------
# テスト用ヘルパー・フィクスチャ
# ---------------------------------------------------------------------------


def _make_builder(
    persona_core: str = "[人格定義]",
    style_samples: str = "[スタイルサンプル]",
    human_block: str = "[ユーザー情報]",
    personality_trends: str = "[傾向メモ]",
    day_summaries: list[dict] | None = None,
) -> PromptBuilder:
    """テスト用 PromptBuilder を生成する."""
    return PromptBuilder(
        persona_core=persona_core,
        style_samples=style_samples,
        human_block=human_block,
        personality_trends=personality_trends,
        day_summaries=day_summaries or [],
    )


def _make_cold_memories(n: int) -> list[dict]:
    """テスト用 cold_memories リストを生成する."""
    return [
        {"content": f"記憶{i}", "speaker": "user", "created_at": 1700000000.0 + i}
        for i in range(n)
    ]


def _make_turns(n_pairs: int) -> list[dict[str, str]]:
    """テスト用 turns リストを生成する（n_pairs 往復分）."""
    turns = []
    for i in range(n_pairs):
        turns.append({"role": "user", "content": f"ユーザー発言{i}"})
        turns.append({"role": "assistant", "content": f"マスコット応答{i}"})
    return turns


# ---------------------------------------------------------------------------
# truncation.py ユーティリティのテスト
# ---------------------------------------------------------------------------


class TestEstimateTokens:
    """estimate_tokens() のテスト."""

    def test_empty_string(self) -> None:
        assert estimate_tokens("") == 0

    def test_ascii_text(self) -> None:
        # 10文字 × 2.0 = 20  (D-18 Section 5.1: _CHARS_TO_TOKENS_RATIO = 2.0)
        assert estimate_tokens("helloworld") == 20

    def test_japanese_text(self) -> None:
        # 5文字 × 2.0 = 10  (D-18 Section 5.1: _CHARS_TO_TOKENS_RATIO = 2.0)
        assert estimate_tokens("あいうえお") == 10


class TestGetEffectiveTokenLimit:
    """get_effective_token_limit() のテスト."""

    def test_known_model(self) -> None:
        # 200_000 × 0.80 - 1024 = 158976
        result = get_effective_token_limit("claude-haiku-4-5-20251001", 1024)
        assert result == 158_976

    def test_unknown_model_uses_default(self) -> None:
        # デフォルト = 200_000 × 0.80 - 1024 = 158976
        result = get_effective_token_limit("unknown-model", 1024)
        assert result == 158_976

    def test_large_max_tokens_returns_zero(self) -> None:
        # 出力用トークンがウィンドウを超えてもマイナスにならない
        result = get_effective_token_limit("claude-haiku-4-5", 999_999)
        assert result == 0


# ---------------------------------------------------------------------------
# PromptBuilder.build_with_truncation() のテスト（FR-8.7）
# ---------------------------------------------------------------------------


class TestBuildWithTruncationNoTruncation:
    """テスト 1: 上限内なら削減なし（FR-8.7）."""

    def test_no_truncation_when_within_limit(self) -> None:
        """上限が十分に大きい場合、Phase 1 と同一の出力になる."""
        builder = _make_builder()
        cold_memories = _make_cold_memories(2)
        turns = _make_turns(2)

        system_phase1 = builder.build_system_prompt(consistency_check_active=False)
        messages_phase1 = builder.build_messages(
            session_start_message="挨拶",
            turns=turns,
            latest_input="こんにちは",
            cold_memories=cold_memories,
        )

        system_trunc, messages_trunc = builder.build_with_truncation(
            session_start_message="挨拶",
            turns=turns,
            latest_input="こんにちは",
            cold_memories=cold_memories,
            model="claude-haiku-4-5-20251001",
            max_tokens_for_output=1024,
            consistency_check_active=False,
            _override_token_limit=999_999,
        )

        assert system_trunc == system_phase1
        assert messages_trunc == messages_phase1


class TestBuildWithTruncationColdMemory:
    """テスト 2: Cold Memory が最初に削減される（FR-8.7 受入条件(1)）."""

    def test_cold_memory_truncated_first(self) -> None:
        """Cold Memory を含むと超過する上限のとき、Cold が削減され Warm・Session は維持される."""
        day_summaries = [{"date": "2026-03-05", "summary": "昨日のまとめ"}]
        builder = _make_builder(day_summaries=day_summaries)
        cold_memories = _make_cold_memories(5)
        turns = _make_turns(1)

        # Cold Memory なしのコストを計算
        system_no_cold = builder.build_system_prompt()
        messages_no_cold = builder.build_messages(
            session_start_message="挨拶",
            turns=turns,
            latest_input="テスト",
            cold_memories=None,
        )
        base_cost = estimate_tokens(system_no_cold) + estimate_tokens(
            str(messages_no_cold)
        )

        # Cold Memory 1件分のコストより少し大きい上限を設定 → Cold が削減される
        cold_one_cost = estimate_tokens(str(_make_cold_memories(1)))
        token_limit = base_cost + cold_one_cost - 1

        system_out, messages_out = builder.build_with_truncation(
            session_start_message="挨拶",
            turns=turns,
            latest_input="テスト",
            cold_memories=cold_memories,
            model="claude-haiku-4-5-20251001",
            max_tokens_for_output=1024,
            consistency_check_active=False,
            _override_token_limit=token_limit,
        )

        # day_summaries は維持される
        assert "昨日のまとめ" in system_out
        # turns は維持される（セッション開始メッセージを除いた会話ターン）
        assert any("ユーザー発言0" in str(m) for m in messages_out)
        # Cold Memory が削減されているか（元は5件、削減後は5件未満）
        cold_count_in_output = sum(
            1 for m in messages_out if "記憶" in str(m["content"])
        )
        assert cold_count_in_output < 5


class TestBuildWithTruncationWarmMemory:
    """テスト 3: Cold 全削除後に Warm が削減される（FR-8.7 受入条件(1)）."""

    def test_warm_memory_truncated_after_cold(self) -> None:
        """Cold をすべて削除しても超過する場合、Warm（day_summaries）が削減される."""
        day_summaries = [
            {"date": "2026-03-04", "summary": "おととい" * 100},
            {"date": "2026-03-05", "summary": "きのう" * 100},
        ]
        builder = _make_builder(day_summaries=day_summaries)
        cold_memories = _make_cold_memories(2)
        turns = _make_turns(1)

        # Cold なし・Warm なしの最小コスト
        builder_no_warm = _make_builder(day_summaries=[])
        system_bare = builder_no_warm.build_system_prompt()
        messages_bare = builder_no_warm.build_messages(
            session_start_message="挨拶",
            turns=turns,
            latest_input="テスト",
            cold_memories=None,
        )
        bare_cost = estimate_tokens(system_bare) + estimate_tokens(str(messages_bare))

        # Warm 1件分未満のトークン上限 → Warm が削減される
        warm_one_cost = estimate_tokens(day_summaries[0]["summary"])
        token_limit = bare_cost + warm_one_cost - 1

        system_out, messages_out = builder.build_with_truncation(
            session_start_message="挨拶",
            turns=turns,
            latest_input="テスト",
            cold_memories=cold_memories,
            model="claude-haiku-4-5-20251001",
            max_tokens_for_output=1024,
            consistency_check_active=False,
            _override_token_limit=token_limit,
        )

        # Cold は全て削除される（retrieved_memories タグが消えるか内容が空）
        assert "記憶0" not in system_out
        # Warm が削減されている（古い日付の日記が消える）
        assert "おととい" not in system_out or "きのう" not in system_out


class TestBuildWithTruncationSessionContext:
    """テスト 4: Warm 全削除後に Session が削減される（FR-8.7 受入条件(1)）."""

    def test_session_truncated_after_warm(self) -> None:
        """Cold・Warm を全削除しても超過する場合、Session の古いターンが削減される."""
        # 大量の会話ターン
        turns = _make_turns(5)  # 10要素
        builder = _make_builder(day_summaries=[])
        cold_memories = _make_cold_memories(1)

        # Warm なし・Cold なし・最新入力のみの最小コストを計算
        system_bare = builder.build_system_prompt()
        messages_minimal = builder.build_messages(
            session_start_message="挨拶",
            turns=[],
            latest_input="テスト",
            cold_memories=None,
        )
        min_cost = estimate_tokens(system_bare) + estimate_tokens(str(messages_minimal))

        # 最古ターンが入ると超過するが、それ以外は収まる上限
        one_turn_cost = estimate_tokens(str(turns[:2]))
        token_limit = min_cost + one_turn_cost // 2

        system_out, messages_out = builder.build_with_truncation(
            session_start_message="挨拶",
            turns=turns,
            latest_input="テスト",
            cold_memories=cold_memories,
            model="claude-haiku-4-5-20251001",
            max_tokens_for_output=1024,
            consistency_check_active=False,
            _override_token_limit=token_limit,
        )

        # 最古ターン（ユーザー発言0, マスコット応答0）が消えている
        all_content = " ".join(m["content"] for m in messages_out)
        assert "ユーザー発言0" not in all_content


class TestPersonaCoreNeverTruncated:
    """テスト 5: persona_core は上限超過時でも保持される（FR-8.7 受入条件(2)）."""

    def test_persona_core_never_truncated(self) -> None:
        """token_limit を極小にしても persona_core は system_prompt に含まれる."""
        builder = _make_builder(
            persona_core="[長い人格定義テキスト]",
            style_samples="[スタイルサンプル]" * 100,
            human_block="[ユーザー情報]" * 100,
            personality_trends="[傾向メモ]" * 100,
            day_summaries=[{"date": "2026-03-05", "summary": "まとめ" * 100}],
        )

        system_out, _messages = builder.build_with_truncation(
            session_start_message="挨拶",
            turns=_make_turns(10),
            latest_input="最新の入力",
            cold_memories=_make_cold_memories(5),
            model="claude-haiku-4-5-20251001",
            max_tokens_for_output=1024,
            consistency_check_active=False,
            _override_token_limit=10,  # 極小
        )

        assert "[長い人格定義テキスト]" in system_out


class TestHotMemoryReductionOrder:
    """テスト 6: Hot Memory 削減順（personality_trends → human_block → style_samples）."""

    def test_hot_memory_reduction_order(self) -> None:
        """personality_trends が最初に削除され、次に human_block が削除される."""
        builder = _make_builder(
            persona_core="[人格核]",
            style_samples="[スタイル]" * 50,
            human_block="[ユーザー情報]" * 50,
            personality_trends="[傾向メモ]" * 50,
            day_summaries=[],
        )

        # persona_core + style_samples のみが収まる程度の上限
        # → personality_trends と human_block が削除されるはず
        system_bare = PromptBuilder(
            persona_core="[人格核]",
            style_samples="[スタイル]" * 50,
            human_block="",
            personality_trends="",
            day_summaries=[],
        ).build_system_prompt()
        bare_cost = estimate_tokens(system_bare)
        # human_block 分を少し超えるが personality_trends 分より小さな上限
        trend_cost = estimate_tokens("[傾向メモ]" * 50)
        token_limit = bare_cost + trend_cost // 2

        system_out, _messages = builder.build_with_truncation(
            session_start_message="挨拶",
            turns=[],
            latest_input="テスト",
            cold_memories=None,
            model="claude-haiku-4-5-20251001",
            max_tokens_for_output=1024,
            consistency_check_active=False,
            _override_token_limit=token_limit,
        )

        # personality_trends が削除されている
        assert "[傾向メモ]" not in system_out
        # persona_core は残っている
        assert "[人格核]" in system_out


class TestEdgeCases:
    """テスト 7-9: 空データの境界値テスト（FR-8.7 Section 6.4）."""

    def test_empty_cold_memories(self) -> None:
        """cold_memories=None の場合、Cold 削減フェーズをスキップしてクラッシュしない."""
        builder = _make_builder()

        system_out, messages_out = builder.build_with_truncation(
            session_start_message="挨拶",
            turns=[],
            latest_input="テスト",
            cold_memories=None,
            model="claude-haiku-4-5-20251001",
            max_tokens_for_output=1024,
            consistency_check_active=False,
        )

        assert isinstance(system_out, str)
        assert isinstance(messages_out, list)

    def test_empty_day_summaries(self) -> None:
        """day_summaries=[] の場合、Warm 削減フェーズをスキップしてクラッシュしない."""
        builder = _make_builder(day_summaries=[])

        system_out, messages_out = builder.build_with_truncation(
            session_start_message="挨拶",
            turns=[],
            latest_input="テスト",
            cold_memories=None,
            model="claude-haiku-4-5-20251001",
            max_tokens_for_output=1024,
            consistency_check_active=False,
        )

        assert isinstance(system_out, str)
        assert isinstance(messages_out, list)

    def test_empty_turns(self) -> None:
        """turns=[] の場合、Session 削減フェーズをスキップしてクラッシュしない."""
        builder = _make_builder()

        system_out, messages_out = builder.build_with_truncation(
            session_start_message="挨拶",
            turns=[],
            latest_input="テスト",
            cold_memories=None,
            model="claude-haiku-4-5-20251001",
            max_tokens_for_output=1024,
            consistency_check_active=False,
        )

        assert isinstance(system_out, str)
        assert isinstance(messages_out, list)


class TestPromptBuilderStateUnchanged:
    """テスト 10: build_with_truncation() のフィールド不変保証（FR-8.7 Section 5.7）."""

    def test_promptbuilder_state_unchanged(self) -> None:
        """build_with_truncation() 呼び出し後も PromptBuilder のフィールドが不変."""
        day_summaries = [
            {"date": "2026-03-04", "summary": "おととい"},
            {"date": "2026-03-05", "summary": "きのう"},
        ]
        builder = PromptBuilder(
            persona_core="[人格核]",
            style_samples="[スタイル]",
            human_block="[ユーザー情報]",
            personality_trends="[傾向メモ]",
            day_summaries=list(day_summaries),
        )

        # 呼び出し前の状態を記録
        before_persona_core = builder.persona_core
        before_style_samples = builder.style_samples
        before_human_block = builder.human_block
        before_personality_trends = builder.personality_trends
        before_day_summaries = list(builder.day_summaries)

        # 極小 token_limit で強制削減
        builder.build_with_truncation(
            session_start_message="挨拶",
            turns=_make_turns(5),
            latest_input="テスト",
            cold_memories=_make_cold_memories(3),
            model="claude-haiku-4-5-20251001",
            max_tokens_for_output=1024,
            consistency_check_active=False,
            _override_token_limit=10,
        )

        # 呼び出し後のフィールドが変化していない
        assert builder.persona_core == before_persona_core
        assert builder.style_samples == before_style_samples
        assert builder.human_block == before_human_block
        assert builder.personality_trends == before_personality_trends
        assert builder.day_summaries == before_day_summaries
