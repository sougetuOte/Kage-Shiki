"""Tests for core/errors.py — エラーメッセージ定義 + テンプレート変数解決 (T-24).

対応 FR:
    FR-7.1: API 呼び出し失敗時のリトライ後エラーメッセージ
    FR-7.2: 認証エラー（401/403）時の通知メッセージ
    FR-7.3: SQLite DB ロック時のログメッセージ
    FR-7.4: persona_core.md 読み込み失敗時のエラーメッセージ
    FR-7.5: シャットダウン中サマリー生成失敗時のログメッセージ
    FR-1.6: ANTHROPIC_API_KEY 未設定エラー
    FR-4.8: ペルソナ読み込み3段階エラーハンドリング

対応設計:
    D-6: エラーメッセージ一覧（EM-001〜EM-011）+ テンプレート変数化

テスト方針:
    - 全 EM-XXX メッセージがテンプレート変数なしでもフォーマット可能 [R-5]
    - テンプレート変数が提供された場合に正しく埋め込まれること
    - 未定義キーが空文字にフォールバックすること
    - 未定義エラーコードで KeyError が発生すること [R-2]
    - 重篤度マッピングが D-6 Section 5.2.3 と一致すること
"""

import pytest

from kage_shiki.core.errors import (
    ERROR_MESSAGES,
    ErrorSeverity,
    format_error_message,
    format_log_message,
    get_severity,
)

# ---------------------------------------------------------------------------
# EM-001〜EM-011 の全コード定義確認
# ---------------------------------------------------------------------------

ALL_EM_CODES = [
    "EM-001",
    "EM-002",
    "EM-003",
    "EM-004",
    "EM-005",
    "EM-006",
    "EM-007",
    "EM-008",
    "EM-009",
    "EM-010",
    "EM-011",
]


class TestErrorMessageDefinitions:
    """EM-001〜EM-011 の定義存在テスト."""

    @pytest.mark.parametrize("code", ALL_EM_CODES)
    def test_all_codes_defined(self, code: str) -> None:
        """全 EM コードが ERROR_MESSAGES に定義されていること."""
        assert code in ERROR_MESSAGES

    def test_no_extra_codes(self) -> None:
        """未定義のコードが混入していないこと."""
        assert set(ERROR_MESSAGES.keys()) == set(ALL_EM_CODES)


# ---------------------------------------------------------------------------
# テンプレート変数解決（format_error_message）
# ---------------------------------------------------------------------------


class TestFormatErrorMessage:
    """format_error_message のテンプレート変数解決テスト."""

    # EM-008, EM-009 はログのみ（ユーザー向けメッセージなし）
    _CODES_WITH_USER_MESSAGE = [
        c for c in ALL_EM_CODES if c not in {"EM-008", "EM-009"}
    ]

    @pytest.mark.parametrize("code", _CODES_WITH_USER_MESSAGE)
    def test_format_without_variables(self, code: str) -> None:
        """テンプレート変数なしでもフォーマットが成功すること（空文字フォールバック）."""
        result = format_error_message(code)
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.parametrize("code", ["EM-008", "EM-009"])
    def test_log_only_messages_return_empty(self, code: str) -> None:
        """ログのみメッセージのユーザー向けテンプレートが空であること."""
        result = format_error_message(code)
        assert result == ""

    def test_em001_message_content(self) -> None:
        """EM-001 メッセージが仕様通りの内容を含むこと."""
        result = format_error_message("EM-001")
        assert "ANTHROPIC_API_KEY" in result
        assert "設定方法" in result
        assert "README.md" in result

    def test_em002_with_invalid_keys(self) -> None:
        """EM-002 でテンプレート変数 {invalid_keys} が正しく埋め込まれること."""
        result = format_error_message("EM-002", invalid_keys="max_retries, timeout")
        assert "max_retries, timeout" in result

    def test_em003_with_variables(self) -> None:
        """EM-003 で {persona_path} と {error_detail} が正しく埋め込まれること."""
        result = format_error_message(
            "EM-003",
            persona_path="data/persona_core.md",
            error_detail="FileNotFoundError",
        )
        assert "data/persona_core.md" in result
        assert "FileNotFoundError" in result

    def test_em004_with_missing_fields(self) -> None:
        """EM-004 で {missing_fields} が正しく埋め込まれること."""
        result = format_error_message(
            "EM-004", missing_fields="C1（名前）",
        )
        assert "C1（名前）" in result

    def test_em006_character_tone(self) -> None:
        """EM-006 がキャラクター口調のメッセージであること."""
        result = format_error_message("EM-006")
        assert "ごめん" in result
        assert "また話しかけてみてね" in result

    def test_em007_window_message(self) -> None:
        """EM-007 ウィンドウ表示版がキャラクター口調を含むこと."""
        result = format_error_message("EM-007")
        assert "API キー" in result

    def test_em010_wizard_message(self) -> None:
        """EM-010 のウィザード中エラーメッセージが仕様通りであること."""
        result = format_error_message("EM-010")
        assert "接続に失敗しました" in result
        assert "もう一度試しますか" in result

    def test_em011_manual_edit_detection(self) -> None:
        """EM-011 の手動編集検出メッセージが仕様通りであること."""
        result = format_error_message("EM-011")
        assert "persona_core.md" in result
        assert "再凍結" in result

    def test_unknown_code_raises_keyerror(self) -> None:
        """未定義のエラーコードで KeyError が発生すること [R-2]."""
        with pytest.raises(KeyError):
            format_error_message("EM-999")

    def test_missing_variable_fallback_to_empty(self) -> None:
        """テンプレート変数が未提供の場合、空文字にフォールバックすること."""
        # EM-003 は {persona_path} と {error_detail} を期待
        result = format_error_message("EM-003")
        # フォールバック後も文章として成立する（例外にならない）
        assert "人格ファイルの読み込みに失敗しました" in result

    def test_extra_variables_ignored(self) -> None:
        """テンプレートにない変数を渡してもエラーにならないこと."""
        result = format_error_message("EM-001", extra_var="ignored")
        assert "ANTHROPIC_API_KEY" in result


# ---------------------------------------------------------------------------
# ログ出力フォーマット（format_log_message）
# ---------------------------------------------------------------------------


class TestFormatLogMessage:
    """format_log_message のログ出力テスト."""

    @pytest.mark.parametrize("code", ALL_EM_CODES)
    def test_format_log_without_variables(self, code: str) -> None:
        """全 EM コードのログメッセージがフォーマット可能であること."""
        result = format_log_message(code)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_em001_log_contains_key_info(self) -> None:
        """EM-001 のログに ANTHROPIC_API_KEY 情報が含まれること."""
        result = format_log_message("EM-001")
        assert "ANTHROPIC_API_KEY" in result

    def test_em006_log_with_variables(self) -> None:
        """EM-006 のログに max_retries と error が埋め込まれること."""
        result = format_log_message(
            "EM-006", max_retries="3", error="ConnectionError",
        )
        assert "3" in result
        assert "ConnectionError" in result

    def test_em008_log_with_count(self) -> None:
        """EM-008 のログに observations 数が埋め込まれること."""
        result = format_log_message("EM-008", N="5")
        assert "5" in result

    def test_unknown_code_raises_keyerror(self) -> None:
        """未定義のエラーコードで KeyError が発生すること [R-2]."""
        with pytest.raises(KeyError):
            format_log_message("EM-999")


# ---------------------------------------------------------------------------
# 重篤度マッピング（D-6 Section 5.2.3）
# ---------------------------------------------------------------------------


class TestGetSeverity:
    """get_severity の重篤度マッピングテスト."""

    @pytest.mark.parametrize(
        ("code", "expected"),
        [
            ("EM-001", ErrorSeverity.CRITICAL),
            ("EM-002", ErrorSeverity.WARNING),
            ("EM-003", ErrorSeverity.CRITICAL),
            ("EM-004", ErrorSeverity.CRITICAL),
            ("EM-005", ErrorSeverity.WARNING),
            ("EM-006", ErrorSeverity.WARNING),
            ("EM-007", ErrorSeverity.CRITICAL),
            ("EM-008", ErrorSeverity.WARNING),
            ("EM-009", ErrorSeverity.WARNING),
            ("EM-010", ErrorSeverity.WARNING),
            ("EM-011", ErrorSeverity.INFO),
        ],
    )
    def test_severity_mapping(
        self, code: str, expected: ErrorSeverity,
    ) -> None:
        """各 EM コードの重篤度が D-6 Section 5.2.3 と一致すること."""
        assert get_severity(code) == expected

    def test_unknown_code_raises_keyerror(self) -> None:
        """未定義のエラーコードで KeyError が発生すること [R-2]."""
        with pytest.raises(KeyError):
            get_severity("EM-999")


# ---------------------------------------------------------------------------
# 異常系テスト [R-5]
# ---------------------------------------------------------------------------


class TestErrorEdgeCases:
    """エラーメッセージのエッジケーステスト."""

    def test_empty_string_variable(self) -> None:
        """空文字列の変数が正しく処理されること."""
        result = format_error_message("EM-002", invalid_keys="")
        assert isinstance(result, str)

    def test_unicode_variable(self) -> None:
        """日本語テンプレート変数が正しく処理されること."""
        result = format_error_message(
            "EM-004", missing_fields="C1（名前）、C4（人格核文）",
        )
        assert "C1（名前）、C4（人格核文）" in result

    def test_severity_enum_values(self) -> None:
        """ErrorSeverity の値が仕様通りであること."""
        assert ErrorSeverity.CRITICAL.value == "critical"
        assert ErrorSeverity.WARNING.value == "warning"
        assert ErrorSeverity.INFO.value == "info"
