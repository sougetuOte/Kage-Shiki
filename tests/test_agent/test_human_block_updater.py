"""human_block_updater のテスト (T-17, FR-4.5, FR-6.6).

対応 FR:
    FR-4.5: human_block.md を読み込み、会話中に検出したユーザー属性情報を自己編集する
    FR-6.6: 会話中の human_block 更新判断: 明示的なユーザー属性情報の検出時のみ

テストクラス:
    TestParseHumanBlockUpdates  — パーステスト
    TestValidateUpdate          — ガードレールテスト
    TestFormatHistoryEntry      — 履歴フォーマットテスト
"""

from datetime import datetime

from kage_shiki.agent.human_block_updater import (
    HumanBlockUpdate,
    format_history_entry,
    parse_human_block_updates,
    validate_update,
)


class TestParseHumanBlockUpdates:
    """parse_human_block_updates のテスト."""

    def test_parses_single_update(self) -> None:
        """単一マーカーが正しくパースされる."""
        response = (
            "会話テキスト\n"
            "---human_block_update---\n"
            "セクション: 基本情報\n"
            "内容: ユーザーは東京在住\n"
            "---update_end---\n"
        )
        updates = parse_human_block_updates(response)

        assert len(updates) == 1
        assert updates[0].section == "基本情報"
        assert updates[0].content == "ユーザーは東京在住"

    def test_parses_multiple_updates(self) -> None:
        """複数マーカーが全てパースされる."""
        response = (
            "---human_block_update---\n"
            "セクション: 基本情報\n"
            "内容: 東京在住\n"
            "---update_end---\n"
            "中間テキスト\n"
            "---human_block_update---\n"
            "セクション: 好み・興味\n"
            "内容: 読書が好き\n"
            "---update_end---\n"
        )
        updates = parse_human_block_updates(response)

        assert len(updates) == 2
        assert updates[0].section == "基本情報"
        assert updates[1].section == "好み・興味"

    def test_returns_empty_on_no_markers(self) -> None:
        """マーカーがなければ空リストを返す."""
        response = "普通の応答テキストで、マーカーなし"
        updates = parse_human_block_updates(response)

        assert updates == []

    def test_returns_empty_on_malformed_markers(self) -> None:
        """セクションも内容もないマーカーでは空リストを返す."""
        response = (
            "---human_block_update---\n"
            "\n"
            "---update_end---\n"
        )
        updates = parse_human_block_updates(response)

        assert updates == []

    def test_returns_empty_on_missing_end_marker(self) -> None:
        """終了マーカーがなければ空リストを返す."""
        response = (
            "---human_block_update---\n"
            "セクション: 基本情報\n"
            "内容: 東京在住\n"
        )
        updates = parse_human_block_updates(response)

        assert updates == []

    def test_extracts_section_and_content(self) -> None:
        """セクション名とコンテンツが正確に抽出される."""
        response = (
            "---human_block_update---\n"
            "セクション: 習慣・パターン\n"
            "内容: 毎朝コーヒーを飲む\n"
            "---update_end---\n"
        )
        updates = parse_human_block_updates(response)

        assert len(updates) == 1
        assert updates[0].section == "習慣・パターン"
        assert updates[0].content == "毎朝コーヒーを飲む"

    def test_multiline_content(self) -> None:
        """複数行コンテンツが結合される."""
        response = (
            "---human_block_update---\n"
            "セクション: 好み・興味\n"
            "内容: SF小説が好き\n"
            "特にハードSFを好む\n"
            "---update_end---\n"
        )
        updates = parse_human_block_updates(response)

        assert len(updates) == 1
        assert "SF小説が好き" in updates[0].content
        assert "特にハードSFを好む" in updates[0].content

    def test_parse_with_fullwidth_colon(self) -> None:
        """全角コロンでもセクション名がパースできること。"""
        response = (
            "---human_block_update---\n"
            "基本情報：テストの内容\n"
            "---update_end---"
        )
        updates = parse_human_block_updates(response)
        assert len(updates) == 1
        assert updates[0].section == "基本情報"


class TestValidateUpdate:
    """validate_update のガードレールテスト."""

    def _make_update(self, section: str, content: str) -> HumanBlockUpdate:
        return HumanBlockUpdate(section=section, content=content, raw_text="")

    def test_valid_update_passes(self) -> None:
        """有効な更新エントリがバリデーションを通過する (FR-6.6)."""
        update = self._make_update("基本情報", "ユーザーは東京在住のエンジニア")
        valid, reason = validate_update(update)

        assert valid is True
        assert reason == ""

    def test_rejects_invalid_section(self) -> None:
        """無効なセクション名を拒否する."""
        update = self._make_update("プロフィール", "無効なセクション")
        valid, reason = validate_update(update)

        assert valid is False
        assert "無効なセクション名" in reason

    def test_rejects_update_history_section(self) -> None:
        """更新履歴セクションへの直接書き込みを拒否する."""
        update = self._make_update("更新履歴", "直接書き込み試行")
        valid, reason = validate_update(update)

        assert valid is False
        assert "更新履歴" in reason

    def test_rejects_speculative_content(self) -> None:
        """推測的情報を含むエントリを拒否する (FR-6.6: 明示的情報のみ)."""
        update = self._make_update("基本情報", "おそらく東京在住だろう")
        valid, reason = validate_update(update)

        assert valid is False
        assert "推測的な情報" in reason

    def test_rejects_speculative_content_tabun(self) -> None:
        """「たぶん」を含む推測情報を拒否する."""
        update = self._make_update("基本情報", "たぶんエンジニアだ")
        valid, reason = validate_update(update)

        assert valid is False
        assert "推測的な情報" in reason

    def test_rejects_temporal_content(self) -> None:
        """複数の一時キーワードを含むエントリを拒否する (FR-6.6: 一時情報フィルタ)."""
        update = self._make_update("基本情報", "今日さっき言ったことを記録する")
        valid, reason = validate_update(update)

        assert valid is False
        assert "一時的な情報" in reason

    def test_allows_single_temporal_keyword(self) -> None:
        """一時キーワード1つのみではバリデーション通過する."""
        update = self._make_update("好み・興味", "今はコーヒーが好みとのこと")
        valid, reason = validate_update(update)

        assert valid is True

    def test_rejects_empty_content(self) -> None:
        """空コンテンツを拒否する."""
        update = self._make_update("基本情報", "   ")
        valid, reason = validate_update(update)

        assert valid is False
        assert "空" in reason


class TestFormatHistoryEntry:
    """format_history_entry のテスト."""

    def test_format_includes_date_and_section(self) -> None:
        """フォーマット結果に今日の日付とセクション名が含まれる."""
        update = HumanBlockUpdate(
            section="基本情報",
            content="東京在住のエンジニア",
            raw_text="",
        )
        result = format_history_entry(update)

        today = datetime.now().strftime("%Y-%m-%d")
        assert today in result
        assert "基本情報" in result
        assert result.startswith("- [")

    def test_truncates_long_content(self) -> None:
        """50文字超のコンテンツが切り詰められる."""
        long_content = "あ" * 60
        update = HumanBlockUpdate(
            section="好み・興味",
            content=long_content,
            raw_text="",
        )
        result = format_history_entry(update)

        # 50文字までしか含まない
        assert "あ" * 51 not in result
        assert "あ" * 50 in result
