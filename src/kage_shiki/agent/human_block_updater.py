"""human_block 自己編集ロジック (T-17, FR-4.5, FR-6.6).

LLM応答から更新マーカーをパースし、human_block.md のセクション追記を行う。
ガードレール: 推測禁止、削除禁止、一時情報フィルタ。
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime

from kage_shiki.persona.persona_system import HUMAN_BLOCK_SECTIONS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 更新マーカー定数
# ---------------------------------------------------------------------------

_UPDATE_START = "---human_block_update---"
_UPDATE_END = "---update_end---"

# human_block.md の有効セクション名（PersonaSystem.HUMAN_BLOCK_SECTIONS と同期）
VALID_SECTIONS: frozenset[str] = HUMAN_BLOCK_SECTIONS

# ---------------------------------------------------------------------------
# ガードレール: 一時情報フィルタキーワード
# ---------------------------------------------------------------------------

_TEMPORAL_KEYWORDS: list[str] = [
    "今日", "昨日", "さっき", "今", "現在",
    "たった今", "先ほど", "今から",
]

# ガードレール: 推測マーカー
_SPECULATIVE_KEYWORDS: list[str] = [
    "おそらく", "たぶん", "きっと", "〜だろう", "かもしれない",
    "推測", "思われる", "可能性がある", "〜そう",
]


# ---------------------------------------------------------------------------
# データモデル
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HumanBlockUpdate:
    """human_block 更新エントリ.

    Attributes:
        section: 追記先セクション名。
        content: 追記するテキスト。
        raw_text: パース前の元テキスト。
    """

    section: str
    content: str
    raw_text: str


# ---------------------------------------------------------------------------
# パース + バリデーション
# ---------------------------------------------------------------------------

def parse_human_block_updates(response: str) -> list[HumanBlockUpdate]:
    """LLM応答から human_block 更新マーカーをパースする.

    Args:
        response: LLM応答テキスト。

    Returns:
        パースされた更新エントリのリスト。マーカーなし/パース失敗時は空リスト。
    """
    updates: list[HumanBlockUpdate] = []

    pattern = re.compile(
        re.escape(_UPDATE_START) + r"(.*?)" + re.escape(_UPDATE_END),
        re.DOTALL,
    )
    for match in pattern.finditer(response):
        raw = match.group(1).strip()
        if not raw:
            continue

        section: str | None = None
        content_lines: list[str] = []
        for line in raw.split("\n"):
            line = line.strip()
            if line.startswith("セクション:") or line.startswith("セクション："):
                section = line.split(":", 1)[-1].split("：", 1)[-1].strip()
            elif line.startswith("内容:") or line.startswith("内容："):
                content_lines.append(line.split(":", 1)[-1].split("：", 1)[-1].strip())
            elif content_lines:
                # 内容の続き行
                content_lines.append(line)
            else:
                # セクション名：コンテンツ 形式（全角コロン区切り）
                for sec in VALID_SECTIONS:
                    if line.startswith(sec + "：") or line.startswith(sec + ":"):
                        section = sec
                        sep_idx = len(sec)
                        content_lines.append(line[sep_idx + 1:].strip())
                        break

        if section and content_lines:
            content = "\n".join(content_lines).strip()
            updates.append(HumanBlockUpdate(
                section=section,
                content=content,
                raw_text=raw,
            ))

    return updates


def validate_update(update: HumanBlockUpdate) -> tuple[bool, str]:
    """更新エントリのガードレール検証.

    Args:
        update: 検証する更新エントリ。

    Returns:
        (valid, reason) のタプル。valid=False の場合 reason に拒否理由を格納。
    """
    # 1. 有効セクション名チェック
    if update.section not in VALID_SECTIONS:
        return False, f"無効なセクション名: {update.section}"

    # 2. 更新履歴セクションへの直接書き込み禁止（自動管理）
    if update.section == "更新履歴":
        return False, "更新履歴セクションへの直接書き込みは禁止です"

    # 3. 推測による書き込み禁止（FR-6.6: 明示的情報のみ）
    for kw in _SPECULATIVE_KEYWORDS:
        if kw in update.content:
            return False, f"推測的な情報が含まれています: {kw}"

    # 4. 一時情報フィルタ（2つ以上の一時キーワードで拒否）
    temporal_count = sum(1 for kw in _TEMPORAL_KEYWORDS if kw in update.content)
    if temporal_count >= 2:
        return False, "一時的な情報と判断されました"

    # 5. 空コンテンツチェック
    if not update.content.strip():
        return False, "コンテンツが空です"

    return True, ""


def format_history_entry(update: HumanBlockUpdate) -> str:
    """更新履歴エントリをフォーマットする.

    Args:
        update: 記録する更新エントリ。

    Returns:
        更新履歴に追記するテキスト（日付・セクション・コンテンツ先頭50文字）。
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    truncated_content = update.content[:50]
    return f"- [{date_str}] {update.section}: {truncated_content}"
