"""parse_blame_hint() のテスト。

対応仕様: cross-module-blame-spec.md FR-2c
対応設計: cross-module-blame-design.md Section 2.4, 3.1
"""
from __future__ import annotations

from analyzers.card_generator import parse_blame_hint, parse_contract


class TestParseBlameHint:
    """parse_blame_hint() のテスト。"""

    def test_single_marker(self) -> None:
        """正常: 単一の BLAME-HINT マーカーからフィールドを抽出する (AC-3)。"""
        output = (
            "Some review text\n"
            "---BLAME-HINT---\n"
            "issue: Module Z calls A.validate() with unchecked args\n"
            "suspected_responsible: downstream\n"
            "module: module_z\n"
            "reason: A's precondition requires type check\n"
            "---END-BLAME-HINT---\n"
            "More review text"
        )
        result = parse_blame_hint(output)
        assert len(result) == 1
        assert result[0]["issue"] == "Module Z calls A.validate() with unchecked args"
        assert result[0]["suspected_responsible"] == "downstream"
        assert result[0]["module"] == "module_z"
        assert result[0]["reason"] == "A's precondition requires type check"

    def test_multiple_markers(self) -> None:
        """正常: 複数の BLAME-HINT マーカーを全て抽出する (AC-3)。"""
        output = (
            "---BLAME-HINT---\n"
            "issue: Issue one\n"
            "suspected_responsible: upstream\n"
            "module: mod_a\n"
            "reason: Reason one\n"
            "---END-BLAME-HINT---\n"
            "\n"
            "---BLAME-HINT---\n"
            "issue: Issue two\n"
            "suspected_responsible: spec_ambiguity\n"
            "module: mod_b\n"
            "reason: Reason two\n"
            "---END-BLAME-HINT---\n"
        )
        result = parse_blame_hint(output)
        assert len(result) == 2
        assert result[0]["suspected_responsible"] == "upstream"
        assert result[1]["suspected_responsible"] == "spec_ambiguity"

    def test_no_marker(self) -> None:
        """フォールバック: マーカーなしの場合は空リストを返す (AC-4)。"""
        output = "Normal agent output without any blame hints."
        result = parse_blame_hint(output)
        assert result == []

    def test_missing_end_marker(self) -> None:
        """堅牢性: 閉じマーカーがない場合は空リストを返す (AC-5)。"""
        output = (
            "---BLAME-HINT---\n"
            "issue: Something\n"
            "suspected_responsible: unknown\n"
        )
        result = parse_blame_hint(output)
        assert result == []

    def test_empty_content(self) -> None:
        """堅牢性: マーカーはあるが中身が空の場合は空リストを返す (AC-5)。"""
        output = "---BLAME-HINT---\n---END-BLAME-HINT---"
        result = parse_blame_hint(output)
        assert result == []

    def test_partial_fields(self) -> None:
        """正常（縮退動作）: 一部フィールドのみでも有効な BlameHint として返す。"""
        output = (
            "---BLAME-HINT---\n"
            "issue: Partial issue\n"
            "reason: Only two fields present\n"
            "---END-BLAME-HINT---\n"
        )
        result = parse_blame_hint(output)
        assert len(result) == 1
        assert result[0]["issue"] == "Partial issue"
        assert result[0]["reason"] == "Only two fields present"
        assert "suspected_responsible" not in result[0]
        assert "module" not in result[0]

    def test_coexistence_with_contract_card(self) -> None:
        """共存: CONTRACT-CARD と BLAME-HINT が混在しても互いに干渉しない。"""
        output = (
            "---CONTRACT-CARD---\n"
            "preconditions: [input must be non-null]\n"
            "postconditions: [returns valid result]\n"
            "side_effects: [none]\n"
            "invariants: [state unchanged]\n"
            "---END-CONTRACT-CARD---\n"
            "\n"
            "---BLAME-HINT---\n"
            "issue: Cross-module violation\n"
            "suspected_responsible: downstream\n"
            "module: mod_x\n"
            "reason: Contract precondition violated\n"
            "---END-BLAME-HINT---\n"
        )
        blame_result = parse_blame_hint(output)
        assert len(blame_result) == 1
        assert blame_result[0]["suspected_responsible"] == "downstream"

        contract_result = parse_contract(output)
        assert "preconditions" in contract_result

    def test_empty_content_whitespace_only(self) -> None:
        """堅牢性: 空白行のみのコンテンツでも空リストを返す (AC-5/NFR-3)。"""
        output = "---BLAME-HINT---\n   \n---END-BLAME-HINT---"
        result = parse_blame_hint(output)
        assert result == []

    def test_partial_fields_only_responsible(self) -> None:
        """正常（縮退動作）: suspected_responsible のみでも有効。"""
        output = (
            "---BLAME-HINT---\n"
            "suspected_responsible: upstream\n"
            "---END-BLAME-HINT---\n"
        )
        result = parse_blame_hint(output)
        assert len(result) == 1
        assert result[0]["suspected_responsible"] == "upstream"
        assert "issue" not in result[0]

    def test_broken_first_block_does_not_discard_second(self) -> None:
        """堅牢性: 最初のブロックが壊れていても後続ブロックを抽出する (NFR-3)。"""
        output = (
            "---BLAME-HINT---\n"
            "issue: Broken block without end marker\n"
            "\n"
            "---BLAME-HINT---\n"
            "issue: Valid block\n"
            "suspected_responsible: downstream\n"
            "reason: Valid reason\n"
            "---END-BLAME-HINT---\n"
        )
        result = parse_blame_hint(output)
        assert len(result) == 1
        assert result[0]["issue"] == "Valid block"
        assert result[0]["suspected_responsible"] == "downstream"
        assert "Broken block without end marker" not in str(result)

    def test_invalid_responsible_normalized_to_unknown(self) -> None:
        """堅牢性: 無効な suspected_responsible 値は unknown に正規化される。"""
        output = (
            "---BLAME-HINT---\n"
            "issue: Some issue\n"
            "suspected_responsible: everyone\n"
            "module: mod_x\n"
            "reason: Invalid value test\n"
            "---END-BLAME-HINT---\n"
        )
        result = parse_blame_hint(output)
        assert len(result) == 1
        assert result[0]["suspected_responsible"] == "unknown"
