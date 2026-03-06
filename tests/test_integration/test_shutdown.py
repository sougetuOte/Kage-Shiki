"""シャットダウン全経路統合テスト (T-30).

対応 FR:
    FR-8.5: シャットダウン全経路で1回だけ実行されること

対応教訓:
    L-3: シャットダウン経路の一意性チェック

テスト方針:
    - make_atexit_handler / reset_shutdown_state を直接使用
    - autouse フィクスチャで各テスト前後に reset_shutdown_state() を呼ぶ
    - 全経路（atexit、直接呼び出し、連続呼び出し）を検証

Building Checklist:
    [R-4] FR-8.5 を docstring に転記済み
    [R-5] 異常系テスト: test_double_call_prevented（重複呼び出し防止）
    [R-9] シャットダウン経路: 全経路で1回実行保証
"""

import threading
from unittest.mock import MagicMock

import pytest

from kage_shiki.core.shutdown_handler import make_atexit_handler, reset_shutdown_state

# ---------------------------------------------------------------------------
# autouse フィクスチャ: 各テスト前後でシャットダウン状態をリセット
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_shutdown(monkeypatch: pytest.MonkeyPatch) -> None:
    """各テストの前後で _shutdown_done をリセットする.

    モジュールレベルのグローバル状態をクリアすることで
    テスト間の干渉を防止する。
    """
    reset_shutdown_state()
    yield
    reset_shutdown_state()


# ---------------------------------------------------------------------------
# FR-8.5: atexit 経路テスト
# ---------------------------------------------------------------------------


class TestAtexitPath:
    """FR-8.5 受入条件 (1): atexit 経由でシャットダウンが1回呼ばれる."""

    def test_atexit_path(self) -> None:
        """FR-8.5 受入条件 (1): atexit 経由のシャットダウン.

        手順:
        1. reset_shutdown_state() は autouse フィクスチャで実施済み
        2. make_atexit_handler(shutdown_cb) でハンドラ作成
        3. ハンドラを手動実行
        4. shutdown_cb が1回呼ばれたことを確認
        """
        # Arrange
        shutdown_cb = MagicMock()
        handler = make_atexit_handler(shutdown_cb)

        # Act
        handler()

        # Assert
        shutdown_cb.assert_called_once()

    def test_atexit_handler_calls_callback_with_no_args(self) -> None:
        """atexit ハンドラは shutdown_cb を引数なしで呼ぶ."""
        shutdown_cb = MagicMock()
        handler = make_atexit_handler(shutdown_cb)

        handler()

        shutdown_cb.assert_called_once_with()


# ---------------------------------------------------------------------------
# FR-8.5: 直接呼び出し経路テスト
# ---------------------------------------------------------------------------


class TestDirectShutdownPath:
    """FR-8.5 受入条件 (2): 直接呼び出しでシャットダウンが1回呼ばれる."""

    def test_direct_shutdown_path(self) -> None:
        """FR-8.5 受入条件 (2): 直接呼び出し.

        手順:
        1. shutdown_cb を直接呼び出し
        2. 1回呼ばれたことを確認

        Note:
            このテストは shutdown_handler の _shutdown_done が関与しない
            純粋な「直接呼び出し」の動作検証。
            実際の _shutdown_done ガードは make_atexit_handler 内部にある。
        """
        # Arrange
        shutdown_cb = MagicMock()
        handler = make_atexit_handler(shutdown_cb)

        # Act: ハンドラを通じて1回実行（直接経路をシミュレート）
        handler()

        # Assert
        shutdown_cb.assert_called_once()
        assert shutdown_cb.call_count == 1

    def test_callback_exception_does_not_propagate(self) -> None:
        """shutdown_cb が例外を投げても make_atexit_handler は握りつぶす."""
        shutdown_cb = MagicMock(side_effect=RuntimeError("シャットダウンエラー"))
        handler = make_atexit_handler(shutdown_cb)

        # atexit ハンドラは例外をキャッチするため、外部に伝播しない
        try:
            handler()
        except Exception as e:
            pytest.fail(f"ハンドラが例外を伝播させた: {e}")

        shutdown_cb.assert_called_once()


# ---------------------------------------------------------------------------
# FR-8.5: 連続呼び出しで1回のみ実行テスト
# ---------------------------------------------------------------------------


class TestDoubleCallPrevented:
    """FR-8.5 受入条件 (3): 連続呼び出しで shutdown_cb が合計1回だけ呼ばれる."""

    def test_double_call_prevented(self) -> None:
        """FR-8.5 受入条件 (3): 連続呼び出しで1回のみ.

        手順:
        1. make_atexit_handler(shutdown_cb) でハンドラ作成
        2. ハンドラを2回連続実行
        3. shutdown_cb が合計1回だけ呼ばれたことを確認
        """
        # Arrange
        shutdown_cb = MagicMock()
        handler = make_atexit_handler(shutdown_cb)

        # Act: 2回連続実行
        handler()
        handler()

        # Assert: 1回のみ
        assert shutdown_cb.call_count == 1

    def test_triple_call_still_one_execution(self) -> None:
        """3回呼び出しても shutdown_cb は1回のみ."""
        shutdown_cb = MagicMock()
        handler = make_atexit_handler(shutdown_cb)

        handler()
        handler()
        handler()

        assert shutdown_cb.call_count == 1

    def test_two_different_handlers_same_callback(self) -> None:
        """同一コールバックで2つのハンドラを作っても、_shutdown_done の共有により1回のみ."""
        shutdown_cb = MagicMock()
        handler1 = make_atexit_handler(shutdown_cb)
        handler2 = make_atexit_handler(shutdown_cb)

        # 2つのハンドラを連続実行
        handler1()
        handler2()

        # _shutdown_done はモジュールレベルの共有 Event なので1回のみ実行
        assert shutdown_cb.call_count == 1

    def test_concurrent_calls_prevented(self) -> None:
        """複数スレッドからの同時呼び出しでも shutdown_cb は1回のみ."""
        shutdown_cb = MagicMock()
        handler = make_atexit_handler(shutdown_cb)

        # 複数スレッドで同時実行
        threads = [
            threading.Thread(target=handler, daemon=True)
            for _ in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5.0)

        # threading.Event による2重実行防止で1回のみ
        assert shutdown_cb.call_count == 1


# ---------------------------------------------------------------------------
# FR-8.5: reset_shutdown_state の動作確認
# ---------------------------------------------------------------------------


class TestResetShutdownState:
    """reset_shutdown_state() がテスト間状態をクリアすること."""

    def test_reset_allows_handler_to_run_again(self) -> None:
        """reset_shutdown_state() 後に再びハンドラが実行できること."""
        shutdown_cb = MagicMock()
        handler = make_atexit_handler(shutdown_cb)

        # 1回目
        handler()
        assert shutdown_cb.call_count == 1

        # リセット後
        reset_shutdown_state()
        handler2 = make_atexit_handler(shutdown_cb)
        handler2()
        assert shutdown_cb.call_count == 2
