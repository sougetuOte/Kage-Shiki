"""Tests for PersonaSystem 補助パーサー (T-09).

対応 FR:
    FR-4.2: style_samples.md の読み込み（S1-S7 口調参照例）
    FR-4.5: human_block.md の読み込み・セクション更新（AI 自己編集）
    FR-4.6: personality_trends.md の読み込み・セクション追記（AI 提案 → 承認）

対応設計:
    requirements.md Section 4.3.2〜4.3.4（ファイル形式）
    D-3 Section 5.4（personality_trends 省略判定）
"""

from pathlib import Path

import pytest

from kage_shiki.persona.persona_system import (
    PersonaFrozenError,
    PersonaSystem,
)

# ---------------------------------------------------------------------------
# テスト用データ（requirements.md Section 4.3.2 準拠）
# ---------------------------------------------------------------------------

VALID_STYLE_SAMPLES = """\
# テストキャラ - 口調参照例

## S1: 日常会話

1. （雑談中）→「今日はいい天気だねー」
2. （質問されて）→「えっとね、それはね……」
3. （相槌）→「うんうん、それでそれで？」

## S2: 喜び

1. （褒められて）→「えへへ、ありがとう！」
2. （小さな喜び）→「わーい！」

## S3: 怒り・不快

1. （嫌なことを言われて）→「むぅ……」
2. （理不尽に対して）→「それはちょっと違うと思う！」

## S4: 悲しみ・寂しさ

1. （寂しい時）→「……寂しいな」
2. （悲しい話を聞いて）→「そっか……大変だったね」

## S5: 困惑・不知

1. （知らないことを聞かれて）→「えーっと……わかんない」
2. （困った時）→「うーん、どうしよう」

## S6: ユーモア

1. （冗談を言う）→「なーんてね！」
2. （ツッコミ）→「それはさすがに無理でしょ！」

## S7: 沈黙破り

1. （長い沈黙の後）→「……ねぇねぇ」
2. （何気ないつぶやき）→「あ、そういえばさ」
"""


# ---------------------------------------------------------------------------
# テスト用テンプレート（requirements.md Section 4.3.3-4.3.4 準拠）
# ---------------------------------------------------------------------------

HUMAN_BLOCK_TEMPLATE = """\
# ユーザー情報

## 基本情報

（AI が会話中に検出した情報を追記）

## 好み・興味

## 習慣・パターン

## 更新履歴

"""

TRENDS_TEMPLATE = """\
# 傾向メモ

## 関係性の変化

（AI が提案 → ユーザー承認後に追記）

## 感情の傾向

## 新しい口癖候補（supplementary_styles）

## 提案履歴

"""


# ---------------------------------------------------------------------------
# FR-4.2: style_samples.md
# ---------------------------------------------------------------------------


class TestLoadStyleSamples:
    """style_samples.md の読み込みテスト."""

    def test_load_valid_file(self, tmp_path: Path) -> None:
        """正常な style_samples.md を全文読み込みできること."""
        path = tmp_path / "style_samples.md"
        path.write_text(VALID_STYLE_SAMPLES, encoding="utf-8")
        ps = PersonaSystem()
        result = ps.load_style_samples(path)
        assert "S1: 日常会話" in result
        assert "S7: 沈黙破り" in result

    def test_load_returns_full_text(self, tmp_path: Path) -> None:
        """全文がそのまま返ること."""
        path = tmp_path / "style_samples.md"
        path.write_text(VALID_STYLE_SAMPLES, encoding="utf-8")
        ps = PersonaSystem()
        result = ps.load_style_samples(path)
        assert result == VALID_STYLE_SAMPLES

    def test_load_nonexistent_returns_empty(self, tmp_path: Path) -> None:
        """ファイル不在時は空文字列を返すこと."""
        path = tmp_path / "nonexistent.md"
        ps = PersonaSystem()
        result = ps.load_style_samples(path)
        assert result == ""

    def test_load_os_error_returns_empty(self, tmp_path: Path) -> None:
        """OSError 発生時は空文字列を返すこと."""
        from unittest.mock import patch

        path = tmp_path / "style_samples.md"
        path.write_text("content", encoding="utf-8")
        ps = PersonaSystem()
        with patch.object(Path, "read_text", side_effect=OSError("read fail")):
            result = ps.load_style_samples(path)
        assert result == ""

    def test_save_frozen_raises(self, tmp_path: Path) -> None:
        """凍結状態で style_samples 書き込みが拒否されること."""
        path = tmp_path / "style_samples.md"
        ps = PersonaSystem()
        ps._persona_frozen = True
        with pytest.raises(PersonaFrozenError):
            ps.save_style_samples(path, "new content")

    def test_save_unfrozen_succeeds(self, tmp_path: Path) -> None:
        """非凍結状態で style_samples 書き込みが成功すること."""
        path = tmp_path / "style_samples.md"
        ps = PersonaSystem()
        ps._persona_frozen = False
        ps.save_style_samples(path, VALID_STYLE_SAMPLES)
        assert path.read_text(encoding="utf-8") == VALID_STYLE_SAMPLES


# ---------------------------------------------------------------------------
# FR-4.5: human_block.md
# ---------------------------------------------------------------------------


class TestLoadHumanBlock:
    """human_block.md の読み込みテスト."""

    def test_load_existing_file(self, tmp_path: Path) -> None:
        """既存ファイルの読み込みが成功すること."""
        path = tmp_path / "human_block.md"
        content = "# ユーザー情報\n\n## 基本情報\n\n名前: 田中\n"
        path.write_text(content, encoding="utf-8")
        ps = PersonaSystem()
        result = ps.load_human_block(path)
        assert "田中" in result

    def test_load_nonexistent_generates_template(self, tmp_path: Path) -> None:
        """ファイル不在時にテンプレートが自動生成されること."""
        path = tmp_path / "human_block.md"
        ps = PersonaSystem()
        result = ps.load_human_block(path)
        assert path.exists()
        assert "# ユーザー情報" in result
        assert "## 基本情報" in result
        assert "## 好み・興味" in result
        assert "## 習慣・パターン" in result
        assert "## 更新履歴" in result

    def test_template_matches_spec(self, tmp_path: Path) -> None:
        """生成されたテンプレートが requirements.md 4.3.3 と一致すること."""
        path = tmp_path / "human_block.md"
        ps = PersonaSystem()
        ps.load_human_block(path)
        saved = path.read_text(encoding="utf-8")
        # 仕様で定義されたセクションが全て含まれる
        assert "# ユーザー情報" in saved
        assert "## 基本情報" in saved
        assert "## 好み・興味" in saved
        assert "## 習慣・パターン" in saved
        assert "## 更新履歴" in saved


class TestUpdateHumanBlock:
    """human_block.md のセクション更新テスト."""

    def test_append_to_section(self, tmp_path: Path) -> None:
        """セクションへのコンテンツ追記が成功すること."""
        path = tmp_path / "human_block.md"
        ps = PersonaSystem()
        ps.load_human_block(path)

        ps.update_human_block(path, "基本情報", "名前: 田中太郎")
        content = path.read_text(encoding="utf-8")
        assert "名前: 田中太郎" in content

    def test_append_preserves_existing(self, tmp_path: Path) -> None:
        """追記時に既存情報が保持されること（削除禁止）."""
        path = tmp_path / "human_block.md"
        ps = PersonaSystem()
        ps.load_human_block(path)

        ps.update_human_block(path, "基本情報", "名前: 田中太郎")
        ps.update_human_block(path, "基本情報", "年齢: 30歳")
        content = path.read_text(encoding="utf-8")
        assert "名前: 田中太郎" in content
        assert "年齢: 30歳" in content

    def test_update_different_sections(self, tmp_path: Path) -> None:
        """異なるセクションへの追記が独立して動作すること."""
        path = tmp_path / "human_block.md"
        ps = PersonaSystem()
        ps.load_human_block(path)

        ps.update_human_block(path, "基本情報", "名前: 田中")
        ps.update_human_block(path, "好み・興味", "プログラミングが好き")
        content = path.read_text(encoding="utf-8")
        assert "名前: 田中" in content
        assert "プログラミングが好き" in content

    def test_unknown_section_raises(self, tmp_path: Path) -> None:
        """存在しないセクション名で ValueError が発生すること."""
        path = tmp_path / "human_block.md"
        ps = PersonaSystem()
        ps.load_human_block(path)

        with pytest.raises(ValueError, match="セクション"):
            ps.update_human_block(path, "存在しないセクション", "test")

    def test_valid_section_missing_header_raises(self, tmp_path: Path) -> None:
        """有効なセクション名だがファイル内にヘッダがない場合に ValueError が発生すること (I-4).

        ファイルが手動編集でセクションヘッダが削除された場合の防御テスト。
        """
        path = tmp_path / "human_block.md"
        # テンプレートから「## 基本情報」ヘッダを削除した壊れたファイル
        broken = "# ユーザー情報\n\n## 好み・興味\n\n## 習慣・パターン\n\n## 更新履歴\n"
        path.write_text(broken, encoding="utf-8")
        ps = PersonaSystem()

        with pytest.raises(ValueError, match="見つかりません"):
            ps.update_human_block(path, "基本情報", "test")


# ---------------------------------------------------------------------------
# FR-4.6: personality_trends.md
# ---------------------------------------------------------------------------


class TestLoadPersonalityTrends:
    """personality_trends.md の読み込みテスト."""

    def test_load_existing_file(self, tmp_path: Path) -> None:
        """既存ファイルの読み込みが成功すること."""
        path = tmp_path / "personality_trends.md"
        content = "# 傾向メモ\n\n## 関係性の変化\n\nユーザーとの距離感が縮まった\n"
        path.write_text(content, encoding="utf-8")
        ps = PersonaSystem()
        result = ps.load_personality_trends(path)
        assert "距離感が縮まった" in result

    def test_load_nonexistent_generates_template(self, tmp_path: Path) -> None:
        """ファイル不在時にテンプレートが自動生成されること."""
        path = tmp_path / "personality_trends.md"
        ps = PersonaSystem()
        result = ps.load_personality_trends(path)
        assert path.exists()
        assert "# 傾向メモ" in result
        assert "## 関係性の変化" in result
        assert "## 感情の傾向" in result
        assert "## 新しい口癖候補（supplementary_styles）" in result
        assert "## 提案履歴" in result

    def test_template_matches_spec(self, tmp_path: Path) -> None:
        """テンプレートが requirements.md 4.3.4 と一致すること."""
        path = tmp_path / "personality_trends.md"
        ps = PersonaSystem()
        ps.load_personality_trends(path)
        saved = path.read_text(encoding="utf-8")
        assert "# 傾向メモ" in saved
        assert "## 関係性の変化" in saved
        assert "## 感情の傾向" in saved
        assert "## 新しい口癖候補（supplementary_styles）" in saved
        assert "## 提案履歴" in saved


class TestAppendPersonalityTrends:
    """personality_trends.md のセクション追記テスト."""

    def test_append_to_section(self, tmp_path: Path) -> None:
        """セクションへのエントリ追記が成功すること."""
        path = tmp_path / "personality_trends.md"
        ps = PersonaSystem()
        ps.load_personality_trends(path)

        ps.append_personality_trends(path, "関係性の変化", "ユーザーとの距離感が縮まった")
        content = path.read_text(encoding="utf-8")
        assert "ユーザーとの距離感が縮まった" in content

    def test_append_at_section_end(self, tmp_path: Path) -> None:
        """追記がセクション末尾に挿入されること."""
        path = tmp_path / "personality_trends.md"
        ps = PersonaSystem()
        ps.load_personality_trends(path)

        ps.append_personality_trends(path, "関係性の変化", "エントリ1")
        ps.append_personality_trends(path, "関係性の変化", "エントリ2")
        content = path.read_text(encoding="utf-8")
        # エントリ1 が エントリ2 より前にあること
        assert content.index("エントリ1") < content.index("エントリ2")

    def test_append_to_proposal_history(self, tmp_path: Path) -> None:
        """提案履歴セクションへの追記が成功すること."""
        path = tmp_path / "personality_trends.md"
        ps = PersonaSystem()
        ps.load_personality_trends(path)

        ps.append_personality_trends(
            path, "提案履歴", "- 2026-03-04 口癖「えへへ」追加 → 承認",
        )
        content = path.read_text(encoding="utf-8")
        assert "口癖「えへへ」追加 → 承認" in content

    def test_unknown_section_raises(self, tmp_path: Path) -> None:
        """存在しないセクション名で ValueError が発生すること."""
        path = tmp_path / "personality_trends.md"
        ps = PersonaSystem()
        ps.load_personality_trends(path)

        with pytest.raises(ValueError, match="セクション"):
            ps.append_personality_trends(path, "不明なセクション", "test")


# ---------------------------------------------------------------------------
# D-3: personality_trends 省略判定
# ---------------------------------------------------------------------------


class TestIsTrendsEmpty:
    """is_trends_empty の省略判定テスト（D-3 Section 5.4）."""

    def test_template_only_is_empty(self) -> None:
        """テンプレートのみの場合は空と判定されること."""
        ps = PersonaSystem()
        assert ps.is_trends_empty(TRENDS_TEMPLATE) is True

    def test_with_content_is_not_empty(self) -> None:
        """コンテンツがある場合は空でないと判定されること."""
        ps = PersonaSystem()
        content = TRENDS_TEMPLATE.replace(
            "## 関係性の変化\n\n（AI が提案 → ユーザー承認後に追記）",
            "## 関係性の変化\n\nユーザーとの距離感が縮まった",
        )
        assert ps.is_trends_empty(content) is False

    def test_proposal_history_only_is_empty(self) -> None:
        """提案履歴のみにエントリがある場合は空と判定されること.

        D-3: 「## 提案履歴」以外のセクションにコンテンツが存在するか否かで判定。
        """
        ps = PersonaSystem()
        content = TRENDS_TEMPLATE + "- 2026-03-04 テスト → 却下\n"
        assert ps.is_trends_empty(content) is True

    def test_empty_string_is_empty(self) -> None:
        """空文字列は空と判定されること."""
        ps = PersonaSystem()
        assert ps.is_trends_empty("") is True

    def test_content_in_emotion_section(self) -> None:
        """感情の傾向セクションにコンテンツがある場合は空でないこと."""
        ps = PersonaSystem()
        content = TRENDS_TEMPLATE.replace(
            "## 感情の傾向\n",
            "## 感情の傾向\n\nポジティブな傾向が見られる\n",
        )
        assert ps.is_trends_empty(content) is False


# ---------------------------------------------------------------------------
# 凍結ガード連携
# ---------------------------------------------------------------------------


class TestFreezeGuardIntegration:
    """凍結ガードが PersonaCore 読み込みと連動すること."""

    def test_frozen_persona_sets_flag(self, tmp_path: Path) -> None:
        """凍結状態の persona_core 読み込みで _persona_frozen が True になること."""
        core_path = tmp_path / "persona_core.md"
        core_path.write_text(
            "# Test\n\n"
            "## メタデータ\n\n"
            "| 項目 | 値 |\n|------|-----|\n| 凍結状態 | frozen |\n\n"
            "## C1: 名前\n\nテスト\n\n"
            "## C4: 人格核文\n\nテスト人格\n",
            encoding="utf-8",
        )
        ps = PersonaSystem()
        ps.load_persona_core(core_path)
        assert ps._persona_frozen is True

    def test_unfrozen_persona_sets_flag(self, tmp_path: Path) -> None:
        """非凍結状態の persona_core 読み込みで _persona_frozen が False のままであること."""
        core_path = tmp_path / "persona_core.md"
        core_path.write_text(
            "# Test\n\n"
            "## メタデータ\n\n"
            "| 項目 | 値 |\n|------|-----|\n| 凍結状態 | unfrozen |\n\n"
            "## C1: 名前\n\nテスト\n\n"
            "## C4: 人格核文\n\nテスト人格\n",
            encoding="utf-8",
        )
        ps = PersonaSystem()
        ps.load_persona_core(core_path)
        assert ps._persona_frozen is False
