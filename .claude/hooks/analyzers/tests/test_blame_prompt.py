"""build_review_prompt_with_contracts() の帰責ガイド注入テスト。

対応仕様: cross-module-blame-spec.md FR-2a
対応設計: cross-module-blame-design.md Section 2.2
"""
from __future__ import annotations

from analyzers.card_generator import ContractCard
from analyzers.chunker import Chunk
from analyzers.orchestrator import build_review_prompt_with_contracts


def _make_chunk(name: str, start: int = 0) -> Chunk:
    """テスト用の最小 Chunk を生成する。"""
    return Chunk(
        file_path=f"src/{name}.py",
        start_line=start,
        end_line=start + 10,
        content=f"def {name}(): pass\n",
        overlap_header="",
        overlap_footer="",
        token_count=20,
        level="L2",
        node_name=name,
    )


def _make_contract_card(module_name: str) -> ContractCard:
    """テスト用の最小 ContractCard を生成する。"""
    return ContractCard(
        module_name=module_name,
        public_api=["func_a"],
        signatures=["def func_a(x: int) -> str"],
        preconditions=["x must be positive"],
        postconditions=["returns non-empty string"],
        side_effects=["none"],
        invariants=["state unchanged"],
    )


class TestBlameGuideInjection:
    """帰責判断ガイドの注入テスト。"""

    def test_blame_guide_included_when_contracts_present(self) -> None:
        """契約カードがある場合、帰責判断ガイドがプロンプトに含まれる (AC-2)。"""
        chunk = _make_chunk("handler", 0)
        contract = _make_contract_card("src.upstream")

        prompt = build_review_prompt_with_contracts(chunk, [contract])

        assert "帰責判断ガイド" in prompt
        assert "---BLAME-HINT---" in prompt
        assert "suspected_responsible" in prompt

    def test_no_blame_guide_when_contracts_empty(self) -> None:
        """契約カードがない場合、帰責指示は含まれない (AC-10)。"""
        chunk = _make_chunk("simple", 0)

        prompt = build_review_prompt_with_contracts(chunk, [])

        assert "帰責判断ガイド" not in prompt
        assert "---BLAME-HINT---" not in prompt

    def test_blame_guide_token_count(self) -> None:
        """帰責ガイド追加分のトークン数が 200 以下 (AC-9)。"""
        chunk = _make_chunk("check", 0)
        contract = _make_contract_card("src.upstream")

        prompt_with = build_review_prompt_with_contracts(chunk, [contract])

        guide_start = prompt_with.find("帰責判断ガイド")
        guide_end = prompt_with.find("---END-BLAME-HINT---") + len("---END-BLAME-HINT---")
        assert guide_start != -1
        guide_text = prompt_with[guide_start:guide_end]

        approx_tokens = len(guide_text) / 4
        assert approx_tokens <= 200, f"Blame guide is ~{approx_tokens:.0f} tokens (max 200)"
