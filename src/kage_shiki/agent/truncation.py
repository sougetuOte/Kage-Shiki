"""トランケートアルゴリズム — コンテキストウィンドウ超過時のコンテキスト削減.

FR-8.7: コンテキストウィンドウ超過時に以下の優先順位でコンテキストを削減する。
    削除優先順位: Cold Memory → Warm Memory → Session Context → Hot Memory
    persona_core は絶対に削除しない。

Phase 4 への引き継ぎ:
    - トークン数精密化: Anthropic SDK の client.messages.count_tokens() API を使用
    - 換算係数の動的調整: 実際のトークン数をログに記録し実績ベースで調整
    - コンテキストウィンドウの設定外部化: config.toml に [models].context_window を追加
"""

# ---------------------------------------------------------------------------
# 定数（D-18 Section 5.1）
# ---------------------------------------------------------------------------

# モデル別コンテキストウィンドウ（トークン数）
_CONTEXT_WINDOWS: dict[str, int] = {
    "claude-haiku-4-5-20251001": 200_000,
    "claude-haiku-4-5": 200_000,
    "claude-sonnet-4-5": 200_000,
    "claude-opus-4-5": 200_000,
}

_DEFAULT_CONTEXT_WINDOW = 200_000  # 未知モデルのフォールバック

# 安全マージン（実運用しきい値 = コンテキストウィンドウの 80%）
_CONTEXT_WINDOW_SAFETY_RATIO = 0.80

# 文字数→トークン数換算係数（過大評価側に倒す: 日本語 1文字 ≒ 1.5〜2トークン）
_CHARS_TO_TOKENS_RATIO = 2.0

# Hot Memory 削減時の style_samples 保持最大文字数
_STYLE_SAMPLES_TRUNCATION_CHARS = 500


# ---------------------------------------------------------------------------
# ユーティリティ関数（D-18 Section 5.1）
# ---------------------------------------------------------------------------


def get_effective_token_limit(model: str, max_tokens_for_output: int) -> int:
    """入力に使用可能なトークン数の実運用上限を返す.

    コンテキストウィンドウ × 安全マージン - 出力用 max_tokens

    Args:
        model: モデル ID。
        max_tokens_for_output: 出力に割り当てる max_tokens。

    Returns:
        入力トークン数の実運用上限。0 未満にはならない。
    """
    window = _CONTEXT_WINDOWS.get(model, _DEFAULT_CONTEXT_WINDOW)
    effective_window = int(window * _CONTEXT_WINDOW_SAFETY_RATIO)
    return max(0, effective_window - max_tokens_for_output)


def estimate_tokens(text: str) -> int:
    """テキストのトークン数を文字数から近似する.

    換算係数 2.0 を使用（日本語テキストを過大評価側に倒す）。
    Phase 4 で Anthropic count_tokens() API に置き換え予定。

    Args:
        text: トークン数を推定するテキスト。

    Returns:
        推定トークン数（過大評価側）。
    """
    return int(len(text) * _CHARS_TO_TOKENS_RATIO)
