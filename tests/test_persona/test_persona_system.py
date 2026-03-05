"""PersonaSystem のテスト (T-08).

対応 FR: FR-4.1, FR-4.3, FR-4.4, FR-4.8
対応設計: requirements.md Section 4.3.1（Markdown テーブル形式）
"""

from pathlib import Path

import pytest

from kage_shiki.persona.persona_system import (
    _SECTION_LABELS,
    PersonaCore,
    PersonaFrozenError,
    PersonaLoadError,
    PersonaSystem,
)

# ---------------------------------------------------------------------------
# テスト用データ（requirements.md Section 4.3.1 準拠）
# ---------------------------------------------------------------------------

VALID_PERSONA_CORE = """\
# persona_core.md

## メタデータ

| 項目 | 値 |
|------|-----|
| 凍結状態 | frozen |
| 生成日時 | 2026-03-01 |
| 生成方式 | ai_generate |
| hash | abc123 |

## C1: 名前
アリス

## C2: 一人称
わたし

## C3: 二人称（ユーザーの呼び方）
あなた

## C4: 人格核文
好奇心旺盛で、誰にでも優しく接する。ただし嘘が大嫌い。

## C5: 性格軸
- **好奇心**: とにかく新しいものが好き
- **社交性**: 人と話すのが大好き
- **繊細さ**: 少し打たれ弱い
- **几帳面さ**: まあまあ整理好き
- **思いやり**: 他人の気持ちに敏感

## C6: 口調パターン
語尾に「〜だよ」を付けることが多い

## C7: 口癖
- 「えへへ」
- 「なるほどね〜」
- 「それって面白いね！」

## C8: 年齢感
高校生くらい

## C9: 価値観
正直であることを最も大切にする。嘘や偽りを許さない。

## C10: 禁忌
- 暴力的な発言
- 差別的な表現

## C11: 知識の自己認識
自分がAIであることを知っているが、人間のように振る舞う
"""

MINIMAL_PERSONA_CORE = """\
# persona_core.md

## メタデータ

| 項目 | 値 |
|------|-----|
| 凍結状態 | unfrozen |

## C1: 名前
テスト太郎

## C4: 人格核文
テスト用の最小人格定義
"""

MISSING_NAME = """\
# persona_core.md

## C4: 人格核文
人格は定義されている
"""

MISSING_C4 = """\
# persona_core.md

## C1: 名前
名前だけある
"""

BAD_METADATA = """\
# persona_core.md

## メタデータ

テーブルじゃないテキスト

## C1: 名前
テストくん

## C4: 人格核文
テスト人格
"""


@pytest.fixture()
def persona_dir(tmp_path: Path) -> Path:
    """テスト用ペルソナディレクトリを返す."""
    return tmp_path


class TestPersonaSystemLoad:
    """PersonaSystem.load_persona_core() の動作検証."""

    def test_loads_all_fields(self, persona_dir: Path) -> None:
        """正常な persona_core.md を読み込み、全 C1-C11 フィールドが取得できること."""
        path = persona_dir / "persona_core.md"
        path.write_text(VALID_PERSONA_CORE, encoding="utf-8")

        system = PersonaSystem()
        core = system.load_persona_core(path)

        assert core.c1_name == "アリス"
        assert core.c2_first_person == "わたし"
        assert core.c3_second_person == "あなた"
        assert "好奇心旺盛" in core.c4_personality_core
        assert core.c5_personality_axes != ""
        assert core.c6_speech_pattern != ""
        assert core.c7_catchphrase != ""
        assert core.c8_age_impression != ""
        assert core.c9_values != ""
        assert core.c10_forbidden != ""
        assert core.c11_self_knowledge != ""

    def test_metadata_parsed(self, persona_dir: Path) -> None:
        """メタデータテーブルが正しくパースされること."""
        path = persona_dir / "persona_core.md"
        path.write_text(VALID_PERSONA_CORE, encoding="utf-8")

        system = PersonaSystem()
        core = system.load_persona_core(path)

        assert core.metadata["凍結状態"] == "frozen"
        assert core.metadata["生成日時"] == "2026-03-01"
        assert core.metadata["生成方式"] == "ai_generate"

    def test_file_not_found_returns_wizard_flag(self, persona_dir: Path) -> None:
        """ファイル不在時にウィザード起動フラグが返ること."""
        path = persona_dir / "persona_core.md"

        system = PersonaSystem()
        result = system.load_persona_core(path)

        assert result is None  # None はウィザード起動フラグ

    def test_file_read_error_raises(self, persona_dir: Path) -> None:
        """ファイル読取不能時に PersonaLoadError が発生すること (a-2)."""
        path = persona_dir / "persona_core.md"
        # ディレクトリを作成してファイルとして読もうとする
        path.mkdir()

        system = PersonaSystem()
        with pytest.raises(PersonaLoadError, match="読み込みに失敗"):
            system.load_persona_core(path)

    def test_missing_c1_raises_error(self, persona_dir: Path) -> None:
        """C1（名前）欠損時に例外が発生すること."""
        path = persona_dir / "persona_core.md"
        path.write_text(MISSING_NAME, encoding="utf-8")

        system = PersonaSystem()
        with pytest.raises(PersonaLoadError, match="C1"):
            system.load_persona_core(path)

    def test_missing_c4_raises_error(self, persona_dir: Path) -> None:
        """C4（人格核文）欠損時に例外が発生すること."""
        path = persona_dir / "persona_core.md"
        path.write_text(MISSING_C4, encoding="utf-8")

        system = PersonaSystem()
        with pytest.raises(PersonaLoadError, match="C4"):
            system.load_persona_core(path)

    def test_bad_metadata_uses_default(self, persona_dir: Path) -> None:
        """メタデータパース失敗時にデフォルト（unfrozen）でフォールバックすること."""
        path = persona_dir / "persona_core.md"
        path.write_text(BAD_METADATA, encoding="utf-8")

        system = PersonaSystem()
        core = system.load_persona_core(path)

        assert core is not None
        assert core.c1_name == "テストくん"
        assert core.metadata["凍結状態"] == "unfrozen"

    def test_minimal_persona_loads(self, persona_dir: Path) -> None:
        """最小限の persona_core.md が読み込めること."""
        path = persona_dir / "persona_core.md"
        path.write_text(MINIMAL_PERSONA_CORE, encoding="utf-8")

        system = PersonaSystem()
        core = system.load_persona_core(path)

        assert core is not None
        assert core.c1_name == "テスト太郎"
        assert core.c4_personality_core == "テスト用の最小人格定義"


class TestPersonaSystemFreezeGuard:
    """凍結ガードの動作検証."""

    def test_frozen_prevents_save(self, persona_dir: Path) -> None:
        """凍結状態で書き込みが拒否されること."""
        path = persona_dir / "persona_core.md"
        path.write_text(VALID_PERSONA_CORE, encoding="utf-8")

        system = PersonaSystem()
        core = system.load_persona_core(path)

        assert core is not None
        assert core.metadata.get("凍結状態") == "frozen"

        with pytest.raises(PersonaFrozenError, match="凍結"):
            system.save_persona_core(path, core)

    def test_unfrozen_allows_save(self, persona_dir: Path) -> None:
        """未凍結状態で書き込みが許可されること."""
        path = persona_dir / "persona_core.md"
        path.write_text(MINIMAL_PERSONA_CORE, encoding="utf-8")

        system = PersonaSystem()
        core = system.load_persona_core(path)

        assert core is not None
        system.save_persona_core(path, core)
        assert path.exists()

    def test_save_load_roundtrip(self, persona_dir: Path) -> None:
        """save → load のラウンドトリップで全フィールドが一致すること."""
        path = persona_dir / "persona_core.md"
        path.write_text(MINIMAL_PERSONA_CORE, encoding="utf-8")

        system = PersonaSystem()
        original = system.load_persona_core(path)
        assert original is not None

        # 全フィールドにデータを設定
        original.c2_first_person = "ぼく"
        original.c3_second_person = "きみ"
        original.c5_personality_axes = "好奇心旺盛"
        original.c6_speech_pattern = "です・ます調"
        original.c7_catchphrase = "やれやれ"
        original.c8_age_impression = "大学生"
        original.c9_values = "自由を重んじる"
        original.c10_forbidden = "暴言"
        original.c11_self_knowledge = "自分はAIだと理解"

        save_path = persona_dir / "roundtrip.md"
        system.save_persona_core(save_path, original)

        # 再読み込みして比較
        system2 = PersonaSystem()
        loaded = system2.load_persona_core(save_path)
        assert loaded is not None

        assert loaded.c1_name == original.c1_name
        assert loaded.c2_first_person == original.c2_first_person
        assert loaded.c3_second_person == original.c3_second_person
        assert loaded.c4_personality_core == original.c4_personality_core
        assert loaded.c5_personality_axes == original.c5_personality_axes
        assert loaded.c6_speech_pattern == original.c6_speech_pattern
        assert loaded.c7_catchphrase == original.c7_catchphrase
        assert loaded.c8_age_impression == original.c8_age_impression
        assert loaded.c9_values == original.c9_values
        assert loaded.c10_forbidden == original.c10_forbidden
        assert loaded.c11_self_knowledge == original.c11_self_knowledge


class TestPersonaSystemManualEditDetection:
    """手動編集検出の動作検証."""

    def test_hash_change_detected(self, persona_dir: Path) -> None:
        """ハッシュ変更時に手動編集が検出されること."""
        path = persona_dir / "persona_core.md"
        path.write_text(VALID_PERSONA_CORE, encoding="utf-8")

        system = PersonaSystem()
        core = system.load_persona_core(path)
        assert core is not None

        # ファイルを外部から変更
        original = path.read_text(encoding="utf-8")
        path.write_text(original + "\n# 手動追記", encoding="utf-8")

        assert system.detect_manual_edit(path) is True

    def test_no_change_no_detection(self, persona_dir: Path) -> None:
        """変更がない場合は手動編集が検出されないこと."""
        path = persona_dir / "persona_core.md"
        path.write_text(VALID_PERSONA_CORE, encoding="utf-8")

        system = PersonaSystem()
        system.load_persona_core(path)

        assert system.detect_manual_edit(path) is False

    def test_detect_before_load_returns_false(self, persona_dir: Path) -> None:
        """ロード前の detect_manual_edit は False を返すこと."""
        path = persona_dir / "persona_core.md"
        path.write_text(VALID_PERSONA_CORE, encoding="utf-8")

        system = PersonaSystem()
        assert system.detect_manual_edit(path) is False

    def test_detect_on_nonexistent_file_returns_false(self, persona_dir: Path) -> None:
        """存在しないファイルに対する detect_manual_edit は False を返すこと."""
        path = persona_dir / "nonexistent.md"

        system = PersonaSystem()
        assert system.detect_manual_edit(path) is False

    def test_detect_manual_edit_oserror_returns_false(
        self, persona_dir: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """detect_manual_edit で OSError が発生した場合 False を返すこと (WARN-005)."""
        path = persona_dir / "persona_core.md"
        path.write_text(VALID_PERSONA_CORE, encoding="utf-8")

        system = PersonaSystem()
        system.load_persona_core(path)

        # read_text が OSError を投げるようにモンキーパッチ
        def raise_oserror(*args, **kwargs):
            raise OSError("permission denied")

        monkeypatch.setattr(Path, "read_text", raise_oserror)
        assert system.detect_manual_edit(path) is False


class TestPersonaCoreToMarkdown:
    """PersonaCore.to_markdown() の動作検証 (T-25, D-16 Section 5.3)."""

    def test_all_fields_produce_labeled_sections(self) -> None:
        """全フィールド PersonaCore で to_markdown() が日本語ラベル付き Markdown を返すこと."""
        core = PersonaCore(
            c1_name="アリス",
            c2_first_person="わたし",
            c3_second_person="あなた",
            c4_personality_core="好奇心旺盛で誰にでも優しい",
            c5_personality_axes="好奇心: 高い",
            c6_speech_pattern="です・ます調",
            c7_catchphrase="なるほど〜",
            c8_age_impression="高校生くらい",
            c9_values="誠実であること",
            c10_forbidden="暴言禁止",
            c11_self_knowledge="自分がAIと知っている",
        )
        result = core.to_markdown()

        assert "## C1: 名前" in result
        assert "アリス" in result
        assert "## C4: 人格核文" in result
        assert "好奇心旺盛で誰にでも優しい" in result
        assert "## C11: 知識の自己認識" in result
        assert "自分がAIと知っている" in result

    def test_only_c1_populated_returns_c1_only(self) -> None:
        """c1_name のみの PersonaCore で C1 セクションだけが含まれること."""
        core = PersonaCore(c1_name="テストくん")
        result = core.to_markdown()

        assert "## C1: 名前" in result
        assert "テストくん" in result
        # 他のセクションは含まれない
        assert "## C2:" not in result
        assert "## C4:" not in result

    def test_empty_fields_excluded(self) -> None:
        """空フィールドのセクションが出力に含まれないこと."""
        core = PersonaCore(
            c1_name="名前あり",
            c4_personality_core="人格あり",
            # c2, c3, c5-c11 は空（デフォルト ""）
        )
        result = core.to_markdown()

        assert "## C1:" in result
        assert "## C4:" in result
        assert "## C2:" not in result
        assert "## C3:" not in result
        assert "## C5:" not in result

    def test_section_labels_are_japanese(self) -> None:
        """_SECTION_LABELS の日本語ラベルが使われていること."""
        core = PersonaCore(
            c1_name="テスト",
            c9_values="価値観テキスト",
        )
        result = core.to_markdown()

        # _SECTION_LABELS の値が使われている
        assert f"## C1: {_SECTION_LABELS[1]}" in result
        assert f"## C9: {_SECTION_LABELS[9]}" in result

    def test_sections_separated_by_blank_lines(self) -> None:
        """複数セクションが空行で区切られていること."""
        core = PersonaCore(
            c1_name="名前",
            c4_personality_core="人格",
        )
        result = core.to_markdown()

        # "\n\n" で join されているため2つのセクション間に空行がある
        assert "\n\n" in result


class TestPersonaSystemParseSections:
    """_parse_sections の境界ケース検証."""

    def test_unknown_c_number_is_skipped(self, persona_dir: Path) -> None:
        """未知の C 番号（C99 等）がスキップされること (INFO-006)."""
        content = """\
# persona_core.md

## C1: 名前
テストくん

## C4: 人格核文
テスト人格

## C99: 未知のフィールド
この内容はスキップされるべき
"""
        path = persona_dir / "persona_core.md"
        path.write_text(content, encoding="utf-8")

        system = PersonaSystem()
        core = system.load_persona_core(path)

        assert core is not None
        assert core.c1_name == "テストくん"
        assert core.c4_personality_core == "テスト人格"
