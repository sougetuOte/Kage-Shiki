"""autonomous_prompt — 自律発言プロンプトテンプレートのテスト (Phase 2b Wave 2 / D-23).

対応 FR:
    FR-9.3: 自律発言時に既存 ReAct ループを再利用する
    FR-9.4: autonomous_turn=True 時のシステムプロンプトに独り言指示を含める
    FR-9.9: reflect 欲求発現時に day_summary を参照した内省テキスト

対応設計:
    design.md Section 4.2: 自律発言プロンプトテンプレート
"""

from __future__ import annotations

import re

import pytest

from kage_shiki.agent.autonomous_prompt import AUTONOMOUS_PROMPTS
from kage_shiki.agent.desire_worker import DesireWorker
from kage_shiki.core.config import DesireConfig

# ---------------------------------------------------------------------------
# AUTONOMOUS_PROMPTS — 構造テスト
# ---------------------------------------------------------------------------


class TestAutonomousPromptsStructure:
    """AUTONOMOUS_PROMPTS の構造を検証する."""

    def test_contains_all_four_desire_types(self) -> None:
        """4 つの desire_type すべてが定義されていること (talk/curiosity/reflect/rest)."""
        assert set(AUTONOMOUS_PROMPTS.keys()) == {
            "talk",
            "curiosity",
            "reflect",
            "rest",
        }

    def test_all_values_are_non_empty_strings(self) -> None:
        """各プロンプトが非空文字列であること."""
        for desire_type, prompt in AUTONOMOUS_PROMPTS.items():
            assert isinstance(prompt, str), f"{desire_type} is not a str"
            assert prompt.strip(), f"{desire_type} is empty"

    @pytest.mark.parametrize("desire_type", ["talk", "curiosity", "reflect", "rest"])
    def test_each_prompt_mentions_50_char_limit(self, desire_type: str) -> None:
        """各プロンプトが 50 文字以内推奨を明示すること (US-15)."""
        assert "50" in AUTONOMOUS_PROMPTS[desire_type]

    @pytest.mark.parametrize("desire_type", ["talk", "curiosity", "rest"])
    def test_non_reflect_prompts_have_no_placeholder(self, desire_type: str) -> None:
        """reflect 以外のプロンプトには未置換プレースホルダ ({xxx}) がないこと."""
        prompt = AUTONOMOUS_PROMPTS[desire_type]
        assert "{day_summary}" not in prompt
        # {anything} 形式のプレースホルダが残っていないこと
        assert re.search(r"\{[^}]+\}", prompt) is None


class TestReflectPromptPlaceholder:
    """reflect プロンプトの {day_summary} プレースホルダを検証する (FR-9.9)."""

    def test_reflect_contains_day_summary_placeholder(self) -> None:
        """reflect プロンプトに {day_summary} プレースホルダが含まれること."""
        assert "{day_summary}" in AUTONOMOUS_PROMPTS["reflect"]

    def test_reflect_placeholder_substitution(self) -> None:
        """{day_summary} が str.format で正しく置換されること."""
        formatted = AUTONOMOUS_PROMPTS["reflect"].format(
            day_summary="今日はテストの話をした。",
        )
        assert "{day_summary}" not in formatted
        assert "今日はテストの話をした。" in formatted

    def test_reflect_mentions_introspection(self) -> None:
        """reflect プロンプトが内省を示唆する語彙を含むこと."""
        prompt = AUTONOMOUS_PROMPTS["reflect"]
        assert "振り返" in prompt or "内省" in prompt


class TestPromptToneByDesireType:
    """各 desire_type のプロンプトが期待される語彙を含むことを検証する."""

    def test_talk_prompt_mentions_idle_state(self) -> None:
        """talk プロンプトが「話していない」状態を示唆すること."""
        assert "話していない" in AUTONOMOUS_PROMPTS["talk"]

    def test_curiosity_prompt_mentions_research(self) -> None:
        """curiosity プロンプトが「調べる」「気になる」を含むこと."""
        prompt = AUTONOMOUS_PROMPTS["curiosity"]
        assert "調べ" in prompt
        assert "気になっ" in prompt

    def test_rest_prompt_mentions_fatigue(self) -> None:
        """rest プロンプトが「疲れ」「休息」「眠い」を示唆すること."""
        prompt = AUTONOMOUS_PROMPTS["rest"]
        assert "疲れ" in prompt or "休息" in prompt or "眠い" in prompt


# ---------------------------------------------------------------------------
# AUTONOMOUS_PROMPTS と DesireWorker のキー同期検証 (W-E iter 1 監査対応)
# ---------------------------------------------------------------------------


class TestAutonomousPromptsDesireWorkerSync:
    """AUTONOMOUS_PROMPTS のキーと DesireWorker.desires のキーが同期していることを検証する.

    `agent_core.handle_autonomous_turn` は `state.desires[desire_type].active` を
    KeyError ガードなしで参照しているため、両者のキー集合が一致していなければ
    KeyError が発生する。本テストはその不変条件を担保する。
    """

    def test_keys_match_desire_worker_initialization(self) -> None:
        """AUTONOMOUS_PROMPTS のキー集合と DesireWorker 初期化後の desires キー集合が一致する."""
        worker = DesireWorker(
            config=DesireConfig(),
            get_pending_curiosity_count=lambda: 0,
            get_observation_count=lambda: 0,
            on_threshold_exceeded=lambda _: None,
        )
        state = worker.get_state()
        assert set(AUTONOMOUS_PROMPTS.keys()) == set(state.desires.keys()), (
            "AUTONOMOUS_PROMPTS のキーと DesireWorker.desires のキーが一致していません。"
            "両者を同時に更新してください (R-3 定数定義 → 使用の即時接続)。"
        )
