"""エラーメッセージ定義 + テンプレート変数解決 (T-24).

対応 FR:
    FR-7.1: API 呼び出し失敗時のリトライ後エラーメッセージ (EM-006)
    FR-7.2: 認証エラー（401/403）時の通知メッセージ (EM-007)
    FR-7.3: SQLite DB ロック時のログメッセージ (EM-008)
    FR-7.4: persona_core.md 読み込み失敗時のエラーメッセージ (EM-003, EM-004)
    FR-7.5: シャットダウン中サマリー生成失敗時のログメッセージ (EM-009)
    FR-1.6: ANTHROPIC_API_KEY 未設定エラー (EM-001)
    FR-4.8: ペルソナ読み込み3段階エラーハンドリング (EM-003, EM-004, EM-005)

対応設計:
    D-6: エラーメッセージ一覧（EM-001〜EM-011）
    D-6 Section 5.2.2: テンプレート変数フォールバック（defaultdict(str)）
"""

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum

# ---------------------------------------------------------------------------
# 重篤度定義
# ---------------------------------------------------------------------------


class ErrorSeverity(Enum):
    """エラーの重篤度レベル."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


# ---------------------------------------------------------------------------
# エラーメッセージデータモデル
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _ErrorDef:
    """エラーメッセージ定義（内部用）.

    Attributes:
        severity: 重篤度。
        template: ユーザー向けメッセージテンプレート。
        log_template: ログ出力テンプレート。
    """

    severity: ErrorSeverity
    template: str
    log_template: str


# ---------------------------------------------------------------------------
# EM-001〜EM-011 メッセージ定義（D-6 Section 5.1 準拠、文字単位一致）
# ---------------------------------------------------------------------------

ERROR_MESSAGES: dict[str, _ErrorDef] = {
    # ------------------------------------------------------------------
    # EM-001: ANTHROPIC_API_KEY 未設定（FR-1.6）
    # ------------------------------------------------------------------
    "EM-001": _ErrorDef(
        severity=ErrorSeverity.CRITICAL,
        template=(
            "影式を起動できませんでした。\n"
            "\n"
            "ANTHROPIC_API_KEY が設定されていません。\n"
            "\n"
            "設定方法:\n"
            "  Windowsの「システム環境変数」に\n"
            "  ANTHROPIC_API_KEY=sk-... を追加し、\n"
            "  アプリを再起動してください。\n"
            "\n"
            "詳しくは README.md を参照してください。"
        ),
        log_template=(
            "ANTHROPIC_API_KEY not found in environment variables"
        ),
    ),
    # ------------------------------------------------------------------
    # EM-002: config.toml 値不正（FR-1.3）
    # ------------------------------------------------------------------
    "EM-002": _ErrorDef(
        severity=ErrorSeverity.WARNING,
        template=(
            "設定ファイルの一部の値が不正なため、デフォルト値を使用しています。\n"
            "不正な項目: {invalid_keys}\n"
            "詳細はログファイルを確認してください。"
        ),
        log_template=(
            "Invalid config value for {key}: {value}, "
            "fallback to {default}"
        ),
    ),
    # ------------------------------------------------------------------
    # EM-003: persona_core.md 不在または読取不能（FR-4.8(a), FR-7.4）
    # ------------------------------------------------------------------
    "EM-003": _ErrorDef(
        severity=ErrorSeverity.CRITICAL,
        template=(
            "人格ファイルの読み込みに失敗しました。\n"
            "\n"
            "ファイルパス: {persona_path}\n"
            "エラー: {error_detail}\n"
            "\n"
            "対処法:\n"
            "  1. ファイルが存在するか確認してください\n"
            "  2. ファイルのアクセス権限を確認してください\n"
            "  3. 初回起動の場合、ウィザードから人格を作成してください\n"
            "\n"
            "ウィザードを起動しますか？"
        ),
        log_template=(
            "Failed to load persona_core.md: {error}"
        ),
    ),
    # ------------------------------------------------------------------
    # EM-004: persona_core.md 必須フィールド欠損（FR-4.8(c)）
    # ------------------------------------------------------------------
    "EM-004": _ErrorDef(
        severity=ErrorSeverity.CRITICAL,
        template=(
            "人格ファイルに必須の情報が不足しています。\n"
            "\n"
            "不足している項目: {missing_fields}\n"
            "\n"
            "対処法:\n"
            "  persona_core.md を直接編集するか、\n"
            "  ウィザードで人格を作り直してください。\n"
            "\n"
            "ウィザードを起動しますか？"
        ),
        log_template=(
            "Missing required fields in persona_core.md: {missing_fields}"
        ),
    ),
    # ------------------------------------------------------------------
    # EM-005: persona_core.md メタデータパース失敗（FR-4.8(b)）
    # ------------------------------------------------------------------
    "EM-005": _ErrorDef(
        severity=ErrorSeverity.WARNING,
        template=(
            "人格ファイルのメタデータの一部が読み取れなかったため、\n"
            "デフォルト値を使用しています。\n"
            "手動編集した場合は形式を確認してください。"
        ),
        log_template=(
            "Failed to parse metadata section in persona_core.md, "
            "using defaults"
        ),
    ),
    # ------------------------------------------------------------------
    # EM-006: API 呼び出し失敗・リトライ後最終失敗（FR-7.1）
    # ------------------------------------------------------------------
    "EM-006": _ErrorDef(
        severity=ErrorSeverity.WARNING,
        template=(
            "{name_prefix}ごめん、うまく考えられなかった...。\n"
            "もう少ししたら、また話しかけてみてね。"
        ),
        log_template=(
            "API call failed after {max_retries} retries: {error}"
        ),
    ),
    # ------------------------------------------------------------------
    # EM-007: API 認証エラー 401/403（FR-7.2）
    # ------------------------------------------------------------------
    "EM-007": _ErrorDef(
        severity=ErrorSeverity.CRITICAL,
        template=(
            "あれ...なんか、繋がれない。\n"
            "API キーを確認してみてくれる？\n"
            "(ANTHROPIC_API_KEY の設定を確認してください)"
        ),
        log_template=(
            "API authentication error (HTTP {status_code}): {error}"
        ),
    ),
    # ------------------------------------------------------------------
    # EM-008: SQLite DB ロック（FR-7.3）
    # ------------------------------------------------------------------
    "EM-008": _ErrorDef(
        severity=ErrorSeverity.WARNING,
        template="",  # ログのみ（ユーザー向けメッセージなし）
        log_template=(
            "SQLite DB locked after 5 retries, "
            "buffering {N} observations in memory"
        ),
    ),
    # ------------------------------------------------------------------
    # EM-009: シャットダウン中サマリー生成失敗（FR-7.5）
    # ------------------------------------------------------------------
    "EM-009": _ErrorDef(
        severity=ErrorSeverity.WARNING,
        template="",  # ログのみ
        log_template=(
            "Failed to generate day_summary on shutdown: {error}. "
            "Will retry on next startup."
        ),
    ),
    # ------------------------------------------------------------------
    # EM-010: ウィザード中 API 失敗（FR-5.2, FR-5.3, FR-5.7）
    # ------------------------------------------------------------------
    "EM-010": _ErrorDef(
        severity=ErrorSeverity.WARNING,
        template=(
            "接続に失敗しました。インターネット接続と\n"
            "ANTHROPIC_API_KEY の設定を確認してください。\n"
            "\n"
            "もう一度試しますか？"
        ),
        log_template=(
            "API call failed during wizard ({step}): {error}"
        ),
    ),
    # ------------------------------------------------------------------
    # EM-011: 手動編集検出（FR-4.4）
    # ------------------------------------------------------------------
    "EM-011": _ErrorDef(
        severity=ErrorSeverity.INFO,
        template=(
            "persona_core.md が前回の凍結後に変更されています。\n"
            "\n"
            "変更を有効にするため、再凍結しますか？\n"
            "（再凍結しない場合、変更された状態のまま起動します）"
        ),
        log_template=(
            "persona_core.md hash mismatch, manual edit detected"
        ),
    ),
}


# ---------------------------------------------------------------------------
# 公開 API
# ---------------------------------------------------------------------------


def format_error_message(error_id: str, **kwargs: str) -> str:
    """エラーメッセージをフォーマットする.

    テンプレート変数は ``str.format_map(defaultdict(str, **kwargs))`` で
    解決する。未定義変数は空文字にフォールバックする（D-6 Section 5.2.2）。

    Args:
        error_id: エラーコード（EM-001〜EM-011）。
        **kwargs: テンプレート変数。

    Returns:
        フォーマット済みメッセージ文字列。

    Raises:
        KeyError: 未定義のエラーコードが指定された場合。
    """
    msg = ERROR_MESSAGES[error_id]
    return msg.template.format_map(defaultdict(str, **kwargs))


def format_log_message(error_id: str, **kwargs: str) -> str:
    """ログ出力用メッセージをフォーマットする.

    テンプレート変数のフォールバックは ``format_error_message`` と同様。

    Args:
        error_id: エラーコード（EM-001〜EM-011）。
        **kwargs: テンプレート変数。

    Returns:
        フォーマット済みログメッセージ文字列。

    Raises:
        KeyError: 未定義のエラーコードが指定された場合。
    """
    msg = ERROR_MESSAGES[error_id]
    return msg.log_template.format_map(defaultdict(str, **kwargs))


def get_severity(error_id: str) -> ErrorSeverity:
    """エラーコードの重篤度を返す.

    Args:
        error_id: エラーコード（EM-001〜EM-011）。

    Returns:
        重篤度（ErrorSeverity）。

    Raises:
        KeyError: 未定義のエラーコードが指定された場合。
    """
    return ERROR_MESSAGES[error_id].severity
