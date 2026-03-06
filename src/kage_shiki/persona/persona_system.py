"""PersonaSystem — ペルソナファイル群の読み書き + 凍結ガード (T-08, T-09).

対応 FR:
    FR-4.1: persona_core.md の読み込み（C1-C11）
    FR-4.2: style_samples.md の読み込み（S1-S7 口調参照例）
    FR-4.3: ペルソナの凍結状態管理
    FR-4.4: 手動編集検出
    FR-4.5: human_block.md の読み込み・セクション更新（AI 自己編集）
    FR-4.6: personality_trends.md の読み込み・セクション追記（AI 提案 → 承認）
    FR-4.8: 3段階エラーハンドリング
"""

import hashlib
import logging
import re
from dataclasses import dataclass, field, replace
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

_SECTION_PATTERN = re.compile(r"^##\s+C(\d+):\s*(.+)$", re.MULTILINE)
_METADATA_TABLE_ROW = re.compile(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|$")
_REQUIRED_FIELDS = ("c1_name", "c4_personality_core")

# メタデータの凍結キー名（requirements.md Section 4.3.1 準拠）
_FREEZE_KEY = "凍結状態"
_FREEZE_VALUE_FROZEN = "frozen"
_FREEZE_VALUE_UNFROZEN = "unfrozen"

# メタデータパース失敗時のデフォルト値
_DEFAULT_METADATA: dict[str, str] = {
    _FREEZE_KEY: _FREEZE_VALUE_UNFROZEN,
}

# フィールド名のマッピング: C番号 → dataclass 属性名
# requirements.md Section 4.3.1 準拠
_FIELD_MAP: dict[int, str] = {
    1: "c1_name",
    2: "c2_first_person",
    3: "c3_second_person",
    4: "c4_personality_core",
    5: "c5_personality_axes",
    6: "c6_speech_pattern",
    7: "c7_catchphrase",
    8: "c8_age_impression",
    9: "c9_values",
    10: "c10_forbidden",
    11: "c11_self_knowledge",
}

# ---------------------------------------------------------------------------
# human_block.md テンプレート（requirements.md Section 4.3.3 準拠）
# ---------------------------------------------------------------------------

_HUMAN_BLOCK_TEMPLATE = """\
# ユーザー情報

## 基本情報

（AI が会話中に検出した情報を追記）

## 好み・興味

## 習慣・パターン

## 更新履歴

"""

_HUMAN_BLOCK_SECTIONS: frozenset[str] = frozenset({
    "基本情報",
    "好み・興味",
    "習慣・パターン",
    "更新履歴",
})

# human_block.md の有効セクション名（公開エイリアス: human_block_updater から参照）
HUMAN_BLOCK_SECTIONS: frozenset[str] = _HUMAN_BLOCK_SECTIONS

# ---------------------------------------------------------------------------
# personality_trends.md テンプレート（requirements.md Section 4.3.4 準拠）
# ---------------------------------------------------------------------------

_TRENDS_TEMPLATE = """\
# 傾向メモ

## 関係性の変化

（AI が提案 → ユーザー承認後に追記）

## 感情の傾向

## 新しい口癖候補（supplementary_styles）

## 提案履歴

"""

_TRENDS_SECTIONS: frozenset[str] = frozenset({
    "関係性の変化",
    "感情の傾向",
    "新しい口癖候補（supplementary_styles）",
    "提案履歴",
})

# D-3: 省略判定で除外するセクション（このセクションのみの場合は「空」とみなす）
_TRENDS_METADATA_ONLY_SECTION = "提案履歴"

# テンプレートのプレースホルダテキスト（空判定時に除外）
_TRENDS_PLACEHOLDER_TEXTS: frozenset[str] = frozenset({
    "（AI が提案 → ユーザー承認後に追記）",
})

# C番号 → セクション見出しラベル（requirements.md Section 4.3.1 準拠）
_SECTION_LABELS: dict[int, str] = {
    1: "名前",
    2: "一人称",
    3: "二人称（ユーザーの呼び方）",
    4: "人格核文",
    5: "性格軸",
    6: "口調パターン",
    7: "口癖",
    8: "年齢感",
    9: "価値観",
    10: "禁忌",
    11: "知識の自己認識",
}


# ---------------------------------------------------------------------------
# 例外クラス
# ---------------------------------------------------------------------------


class PersonaLoadError(Exception):
    """ペルソナ読み込みエラー（起動中断レベル）."""


class PersonaFrozenError(Exception):
    """凍結状態でのペルソナ書き込みエラー."""


# ---------------------------------------------------------------------------
# データモデル
# ---------------------------------------------------------------------------


@dataclass
class PersonaCore:
    """persona_core.md の構造化データ.

    Attributes:
        c1_name: C1 — キャラクター名（必須）。
        c2_first_person: C2 — 一人称。
        c3_second_person: C3 — 二人称（ユーザーの呼び方）。
        c4_personality_core: C4 — 人格核文（必須）。
        c5_personality_axes: C5 — 性格軸。
        c6_speech_pattern: C6 — 口調パターン。
        c7_catchphrase: C7 — 口癖。
        c8_age_impression: C8 — 年齢感。
        c9_values: C9 — 価値観。
        c10_forbidden: C10 — 禁忌。
        c11_self_knowledge: C11 — 知識の自己認識。
        metadata: メタデータ辞書。
    """

    c1_name: str = ""
    c2_first_person: str = ""
    c3_second_person: str = ""
    c4_personality_core: str = ""
    c5_personality_axes: str = ""
    c6_speech_pattern: str = ""
    c7_catchphrase: str = ""
    c8_age_impression: str = ""
    c9_values: str = ""
    c10_forbidden: str = ""
    c11_self_knowledge: str = ""
    metadata: dict[str, str] = field(default_factory=dict)

    def to_markdown(self) -> str:
        """C1-C11 フィールドを Markdown テキストとして再構成する.

        _SECTION_LABELS を参照し、requirements.md Section 4.3.1 準拠の
        日本語ラベルを使用する。空フィールドのセクションは出力しない。

        Returns:
            Markdown 形式のテキスト。各セクションは空行で区切られる。
        """
        lines: list[str] = []
        for num, attr_name in _FIELD_MAP.items():
            value = getattr(self, attr_name, "")
            if value:
                label = _SECTION_LABELS[num]
                lines.append(f"## C{num}: {label}\n\n{value}")
        return "\n\n".join(lines)


# ---------------------------------------------------------------------------
# PersonaSystem
# ---------------------------------------------------------------------------


class PersonaSystem:
    """ペルソナファイルの読み書き・凍結ガード・手動編集検出を管理する.

    load_persona_core() は3段階のエラーハンドリングを実装する (FR-4.8):
        (a-1) ファイル不在 → None を返す（ウィザード起動フラグ）
        (a-2) ファイル読取不能 → PersonaLoadError
        (b)   メタデータパース失敗 → デフォルトフォールバック + WARNING
        (c)   必須フィールド（C1, C4）欠損 → PersonaLoadError
    """

    def __init__(self) -> None:
        self._file_hash: str | None = None
        self._persona_frozen: bool = False

    def load_persona_core(self, path: Path) -> PersonaCore | None:
        """persona_core.md を読み込んで PersonaCore を返す.

        Args:
            path: persona_core.md のファイルパス。

        Returns:
            PersonaCore インスタンス。ファイル不在時は None（ウィザード起動フラグ）。

        Raises:
            PersonaLoadError: ファイル読取不能、または必須フィールド欠損。
        """
        # (a-1) ファイル不在
        if not path.exists():
            logger.info("persona_core.md が見つかりません: %s", path)
            return None

        # (a-2) ファイル読取
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as e:
            raise PersonaLoadError(f"persona_core.md の読み込みに失敗: {e}") from e

        # ハッシュ記録（手動編集検出用）
        self._file_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        # メタデータパース
        metadata = self._parse_metadata(content)

        # C1-C11 パース
        fields = self._parse_sections(content)

        core = PersonaCore(metadata=metadata, **fields)

        # (c) 必須フィールドチェック（_REQUIRED_FIELDS 駆動）
        for req_field in _REQUIRED_FIELDS:
            value = getattr(core, req_field, "")
            if not value.strip():
                # フィールド名から C番号を抽出してラベルを取得
                c_num = int(req_field.split("_")[0][1:])
                label = _SECTION_LABELS[c_num]
                raise PersonaLoadError(
                    f"必須フィールド C{c_num}（{label}）が欠損しています",
                )

        # 凍結状態を記録（T-09: style_samples 凍結ガードで参照）
        self._persona_frozen = (
            metadata.get(_FREEZE_KEY) == _FREEZE_VALUE_FROZEN
        )

        logger.info("persona_core.md を読み込みました: %s (C1=%s)", path, core.c1_name)
        return core

    def save_persona_core(self, path: Path, core: PersonaCore) -> None:
        """PersonaCore を persona_core.md として保存する.

        凍結ガード: メタデータの凍結状態が frozen の場合は書き込みを拒否する。

        Args:
            path: 保存先ファイルパス。
            core: 保存する PersonaCore データ。

        Raises:
            PersonaFrozenError: 凍結状態で書き込みが試みられた場合。
        """
        if core.metadata.get(_FREEZE_KEY) == _FREEZE_VALUE_FROZEN:
            raise PersonaFrozenError(
                "ペルソナは凍結されています。書き込みできません。",
            )

        content = self._render_persona_core(core)
        path.write_text(content, encoding="utf-8")
        self._file_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        logger.info("persona_core.md を保存しました: %s", path)

    def freeze_and_save(self, path: Path, core: PersonaCore) -> None:
        """凍結メタデータを付与して persona_core.md を保存する (FR-5.6).

        ウィザード完了時の初期凍結用。既存メタデータを保持しつつ
        凍結状態を frozen に設定して保存する。

        Args:
            path: 保存先ファイルパス。
            core: 凍結する PersonaCore データ。
        """
        frozen_core = replace(
            core,
            metadata={**core.metadata, _FREEZE_KEY: _FREEZE_VALUE_FROZEN},
        )
        content = self._render_persona_core(frozen_core)
        path.write_text(content, encoding="utf-8")
        self._file_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        self._persona_frozen = True
        logger.info("persona_core.md を凍結保存しました: %s", path)

    def detect_manual_edit(self, path: Path) -> bool:
        """ファイルのハッシュを比較して手動編集を検出する (FR-4.4).

        Args:
            path: 検査対象のファイルパス。

        Returns:
            手動編集が検出された場合 True。
        """
        if self._file_hash is None or not path.exists():
            return False

        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return False

        current_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        return current_hash != self._file_hash

    # ------------------------------------------------------------------
    # FR-4.2: style_samples.md
    # ------------------------------------------------------------------

    def load_style_samples(self, path: Path) -> str:
        """style_samples.md を全文読み込みする (FR-4.2).

        Args:
            path: style_samples.md のファイルパス。

        Returns:
            ファイル全文。ファイル不在時または読取不能時は空文字列。
        """
        if not path.exists():
            return ""
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            logger.warning("style_samples.md の読み込みに失敗: %s", path)
            return ""

    def save_style_samples(self, path: Path, content: str) -> None:
        """style_samples.md を保存する (FR-4.2).

        凍結ガード: ペルソナが凍結状態の場合は書き込みを拒否する。

        Args:
            path: 保存先ファイルパス。
            content: 保存するテキスト。

        Raises:
            PersonaFrozenError: 凍結状態で書き込みが試みられた場合。
        """
        if self._persona_frozen:
            raise PersonaFrozenError(
                "ペルソナは凍結されています。style_samples の書き込みはできません。",
            )
        path.write_text(content, encoding="utf-8")
        logger.info("style_samples.md を保存しました: %s", path)

    # ------------------------------------------------------------------
    # FR-4.5: human_block.md
    # ------------------------------------------------------------------

    def load_human_block(self, path: Path) -> str:
        """human_block.md を読み込む (FR-4.5).

        ファイルが存在しない場合はテンプレートを自動生成して保存する。

        Args:
            path: human_block.md のファイルパス。

        Returns:
            ファイル全文。
        """
        if not path.exists():
            path.write_text(_HUMAN_BLOCK_TEMPLATE, encoding="utf-8")
            logger.info("human_block.md テンプレートを生成しました: %s", path)
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            logger.warning("human_block.md の読み込みに失敗: %s", path, exc_info=True)
            return _HUMAN_BLOCK_TEMPLATE

    def update_human_block(
        self, path: Path, section: str, content: str,
    ) -> None:
        """human_block.md の指定セクションにコンテンツを追記する (FR-4.5).

        Args:
            path: human_block.md のファイルパス。
            section: 追記先セクション名（## の後の文字列）。
            content: 追記するテキスト。

        Raises:
            ValueError: 無効なセクション名が指定された場合。
        """
        file_content = path.read_text(encoding="utf-8")
        new_content = self._append_to_section(
            file_content, section, content, _HUMAN_BLOCK_SECTIONS,
        )
        path.write_text(new_content, encoding="utf-8")
        logger.info("human_block.md セクション '%s' を更新しました", section)

    # ------------------------------------------------------------------
    # FR-4.6: personality_trends.md
    # ------------------------------------------------------------------

    def load_personality_trends(self, path: Path) -> str:
        """personality_trends.md を読み込む (FR-4.6).

        ファイルが存在しない場合はテンプレートを自動生成して保存する。

        Args:
            path: personality_trends.md のファイルパス。

        Returns:
            ファイル全文。
        """
        if not path.exists():
            path.write_text(_TRENDS_TEMPLATE, encoding="utf-8")
            logger.info(
                "personality_trends.md テンプレートを生成しました: %s", path,
            )
        return path.read_text(encoding="utf-8")

    def append_personality_trends(
        self, path: Path, section: str, entry: str,
    ) -> None:
        """personality_trends.md の指定セクションにエントリを追記する (FR-4.6).

        Args:
            path: personality_trends.md のファイルパス。
            section: 追記先セクション名（## の後の文字列）。
            entry: 追記するテキスト。

        Raises:
            ValueError: 無効なセクション名が指定された場合。
        """
        file_content = path.read_text(encoding="utf-8")
        new_content = self._append_to_section(
            file_content, section, entry, _TRENDS_SECTIONS,
        )
        path.write_text(new_content, encoding="utf-8")
        logger.info(
            "personality_trends.md セクション '%s' にエントリを追記しました",
            section,
        )

    def is_trends_empty(self, content: str) -> bool:
        """personality_trends の省略判定 (D-3 Section 5.4).

        「提案履歴」以外のセクションにコンテンツが存在するか否かで判定する。
        テンプレートのプレースホルダテキストはコンテンツとして扱わない。

        Args:
            content: personality_trends.md の全文。

        Returns:
            実質的にコンテンツがない場合 True。
        """
        if not content.strip():
            return True

        section_pattern = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
        matches = list(section_pattern.finditer(content))

        for i, match in enumerate(matches):
            section_name = match.group(1)

            # D-3: 提案履歴セクションは省略判定から除外
            if section_name == _TRENDS_METADATA_ONLY_SECTION:
                continue

            # セクション本文の範囲を特定
            body_start = match.end()
            body_end = (
                matches[i + 1].start() if i + 1 < len(matches) else len(content)
            )
            body = content[body_start:body_end].strip()

            # プレースホルダを除いた実質コンテンツが存在すれば非空
            if body and body not in _TRENDS_PLACEHOLDER_TEXTS:
                return False

        return True

    # ------------------------------------------------------------------
    # 内部ヘルパー（パース・描画）
    # ------------------------------------------------------------------

    def _parse_metadata(self, content: str) -> dict[str, str]:
        """メタデータセクションをパースする.

        Args:
            content: persona_core.md の全文。

        Returns:
            メタデータ辞書。パース失敗時はデフォルトメタデータ。
        """
        # "## メタデータ" セクションを探す
        meta_match = re.search(r"^##\s+メタデータ\s*$", content, re.MULTILINE)
        if meta_match is None:
            return dict(_DEFAULT_METADATA)

        # メタデータセクションの範囲を特定
        start = meta_match.end()
        next_section = re.search(r"^##\s+", content[start:], re.MULTILINE)
        end = start + next_section.start() if next_section else len(content)
        meta_text = content[start:end]

        # テーブル行をパース
        metadata: dict[str, str] = {}
        rows_found = False
        for raw_line in meta_text.split("\n"):
            stripped = raw_line.strip()
            match = _METADATA_TABLE_ROW.match(stripped)
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                # ヘッダー行やセパレータ行をスキップ
                if key == "項目" or set(key) <= {"-", " "}:
                    continue
                metadata[key] = value
                rows_found = True

        if not rows_found:
            logger.warning(
                "メタデータテーブルのパースに失敗。"
                "デフォルト（凍結状態=%s）にフォールバックします。",
                _FREEZE_VALUE_UNFROZEN,
            )
            return dict(_DEFAULT_METADATA)

        return metadata

    def _parse_sections(self, content: str) -> dict[str, str]:
        """C1-C11 セクションをパースする.

        Args:
            content: persona_core.md の全文。

        Returns:
            フィールド名→値の辞書。
        """
        fields: dict[str, str] = {}

        # 全 ## の位置を収集（C セクション + その他の ## を含む）
        all_h2_positions = [
            m.start() for m in re.finditer(r"^##\s+", content, re.MULTILINE)
        ]

        # C セクションのみ抽出
        matches = list(_SECTION_PATTERN.finditer(content))

        for match in matches:
            c_num = int(match.group(1))
            if c_num not in _FIELD_MAP:
                logger.debug("未知の C%d セクションをスキップ", c_num)
                continue

            body_start = match.end()

            # 次の ## セクション（C 以外も含む）の開始位置を探す
            body_end = len(content)
            for pos in all_h2_positions:
                if pos > match.start():
                    body_end = pos
                    break

            body = content[body_start:body_end].strip()
            fields[_FIELD_MAP[c_num]] = body

        return fields

    def _render_persona_core(self, core: PersonaCore) -> str:
        """PersonaCore を Markdown 形式で描画する.

        空のセクションもヘッダーのみ出力する（手動編集テンプレート用）。

        Args:
            core: 描画する PersonaCore データ。

        Returns:
            Markdown テキスト。
        """
        lines = [f"# {core.c1_name or 'persona_core.md'}", ""]

        # メタデータ
        if core.metadata:
            lines.append("## メタデータ")
            lines.append("")
            lines.append("| 項目 | 値 |")
            lines.append("|------|-----|")
            for key, value in core.metadata.items():
                lines.append(f"| {key} | {value} |")
            lines.append("")

        # C1-C11（requirements.md Section 4.3.1 準拠のラベルを使用）
        field_values = [
            (1, core.c1_name),
            (2, core.c2_first_person),
            (3, core.c3_second_person),
            (4, core.c4_personality_core),
            (5, core.c5_personality_axes),
            (6, core.c6_speech_pattern),
            (7, core.c7_catchphrase),
            (8, core.c8_age_impression),
            (9, core.c9_values),
            (10, core.c10_forbidden),
            (11, core.c11_self_knowledge),
        ]

        for c_num, value in field_values:
            label = _SECTION_LABELS[c_num]
            lines.append(f"## C{c_num}: {label}")
            if value:
                lines.append(value)
            lines.append("")

        return "\n".join(lines)

    def _append_to_section(
        self,
        content: str,
        section: str,
        entry: str,
        valid_sections: frozenset[str],
    ) -> str:
        """指定セクションの末尾にエントリを追加する.

        Args:
            content: ファイル全文。
            section: 対象セクション名。
            entry: 追記するテキスト。
            valid_sections: 有効なセクション名の集合。

        Returns:
            更新後のファイル全文。

        Raises:
            ValueError: 無効なセクション名が指定された場合。
        """
        if section not in valid_sections:
            raise ValueError(
                f"セクション '{section}' は有効なセクション名ではありません",
            )

        header_pattern = re.compile(
            rf"^##\s+{re.escape(section)}\s*$", re.MULTILINE,
        )
        header_match = header_pattern.search(content)
        if header_match is None:
            raise ValueError(f"セクション '{section}' が見つかりません")

        after_header = header_match.end()

        # 次の ## セクションを探す
        next_match = re.search(r"^##\s+", content[after_header:], re.MULTILINE)
        insert_pos = (
            after_header + next_match.start() if next_match else len(content)
        )

        # セクション本文を取得して末尾に追記
        existing_body = content[after_header:insert_pos].rstrip()
        remaining = content[insert_pos:]
        before = content[:after_header]

        if existing_body:
            new_body = existing_body + "\n\n" + entry + "\n\n"
        else:
            new_body = "\n\n" + entry + "\n\n"

        return before + new_body + remaining
