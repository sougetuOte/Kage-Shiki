"""LLM クライアント — Anthropic SDK ラッパー (T-07, T-28).

対応 FR:
    FR-6.7: Anthropic API 経由で LLM を呼び出す
    FR-7.1: API 接続失敗時のリトライ（指数バックオフ）
    FR-7.2: 認証エラー（401/403）の検出と案内
    FR-8.6: LLMProtocol 抽出（抽象インターフェース定義）
対応設計: D-15（用途別 max_tokens）, D-17（LLMProtocol 抽出）

ログポリシー (D-2 Section 5.5):
    - LLM レスポンス本文はログに含めない
    - トークン数・処理時間のみ記録
"""

import logging
import time
from typing import Protocol, runtime_checkable

import anthropic

from kage_shiki.core.config import (
    VALID_PURPOSES,
    AppConfig,
    get_max_tokens,
    get_model,
    get_temperature,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 例外クラス
# ---------------------------------------------------------------------------


class LLMError(Exception):
    """LLM クライアントの一般例外."""


class AuthenticationError(LLMError):
    """API 認証エラー（401/403）."""


# ---------------------------------------------------------------------------
# LLMProtocol — 抽象インターフェース（D-17, FR-8.6）
# ---------------------------------------------------------------------------


@runtime_checkable
class LLMProtocol(Protocol):
    """LLM クライアントの抽象インターフェース.

    任意の LLM バックエンド（Anthropic API、LocalLLM 等）がこの Protocol を
    実装することで、AgentCore・MemoryWorker・WizardController は
    具体的な実装に依存しない。

    Phase 2a では LLMClient（既存の Anthropic 実装）のみが実装する。
    Phase 3 以降で LocalLLM 等の第2実装を追加する際に活用する。

    Methods:
        chat: LLM に対話リクエストを送信し、応答テキストを返す。
        send_message_for_purpose: 用途に応じたパラメータで LLM を呼び出す。
    """

    def chat(
        self,
        messages: list[dict],
        *,
        system: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """LLM に対話リクエストを送信し、応答テキストを返す.

        Args:
            messages: Anthropic Messages API 形式の会話配列。
                各要素は {"role": "user"|"assistant", "content": str} の形式。
            system: システムプロンプト。
            model: モデル ID（例: "claude-haiku-4-5-20251001"）。
            max_tokens: 最大出力トークン数。
            temperature: サンプリング温度（0.0〜2.0）。

        Returns:
            LLM の応答テキスト。

        Raises:
            実装依存のエラー。AuthenticationError、LLMError 等。
        """
        ...

    def send_message_for_purpose(
        self,
        system: str,
        messages: list[dict],
        purpose: str,
    ) -> str:
        """用途識別子から model/max_tokens/temperature を自動解決して API を呼び出す.

        Args:
            system: システムプロンプト。
            messages: 会話メッセージ配列。
            purpose: 用途識別子（"conversation", "wizard_generate" 等）。

        Returns:
            LLM の応答テキスト。
        """
        ...


# ---------------------------------------------------------------------------
# LLMClient
# ---------------------------------------------------------------------------


class LLMClient:
    """Anthropic Messages API のラッパー.

    リトライ（指数バックオフ）、認証エラー検出、用途別 max_tokens を提供する。

    Args:
        config: アプリケーション設定。api / models / conversation セクションを参照する。
    """

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._client = anthropic.Anthropic(
            timeout=config.api.timeout,
        )

    def send_message(
        self,
        system: str,
        messages: list[dict],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Anthropic Messages API を呼び出し、応答テキストを返す.

        Args:
            system: システムプロンプト。
            messages: 会話メッセージ配列。
            model: モデル ID。
            max_tokens: 最大出力トークン数。
            temperature: サンプリング温度。

        Returns:
            LLM の応答テキスト。

        Raises:
            AuthenticationError: 401/403 エラー。
            LLMError: リトライ上限超過。
        """
        api_config = self._config.api
        last_error: Exception | None = None

        for attempt in range(api_config.max_retries + 1):
            try:
                start = time.monotonic()
                response = self._client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system,
                    messages=messages,
                )
                elapsed = time.monotonic() - start

                # D-2 ログポリシー: 本文は含めない
                logger.debug(
                    "LLM応答: model=%s input_tokens=%d output_tokens=%d time=%.3fs",
                    model,
                    response.usage.input_tokens,
                    response.usage.output_tokens,
                    elapsed,
                )

                return response.content[0].text

            except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as e:
                # 認証エラーはリトライせず即座に通知
                raise AuthenticationError(str(e)) from e

            except (anthropic.APIStatusError, anthropic.APIConnectionError) as e:
                last_error = e
                if attempt < api_config.max_retries:
                    wait = api_config.retry_backoff_base * (2 ** attempt)
                    logger.warning(
                        "API エラー（リトライ %d/%d, %.1f秒後に再試行）: %s",
                        attempt + 1,
                        api_config.max_retries,
                        wait,
                        e,
                    )
                    time.sleep(wait)

        raise LLMError(
            f"リトライ上限 ({api_config.max_retries}回) に到達: {last_error}",
        ) from last_error

    def chat(
        self,
        messages: list[dict],
        *,
        system: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """LLMProtocol を満足するための chat() メソッド.

        内部で send_message() に委譲する。
        LLMProtocol の実装として機能する（Phase 3 での差し替え口）。

        Args:
            messages: Anthropic Messages API 形式の会話配列。
            system: システムプロンプト。
            model: モデル ID。
            max_tokens: 最大出力トークン数。
            temperature: サンプリング温度。

        Returns:
            LLM の応答テキスト。
        """
        return self.send_message(
            system=system,
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def send_message_for_purpose(
        self,
        system: str,
        messages: list[dict],
        purpose: str,
    ) -> str:
        """用途識別子から model/max_tokens/temperature を自動解決して API を呼び出す.

        Args:
            system: システムプロンプト。
            messages: 会話メッセージ配列。
            purpose: 用途識別子（"conversation", "wizard_generate" 等）。

        Returns:
            LLM の応答テキスト。

        Raises:
            LLMError: 未知の purpose が指定された場合。
        """
        if purpose not in VALID_PURPOSES:
            raise LLMError(f"未知の purpose: {purpose!r}")

        config = self._config
        max_tokens = get_max_tokens(config, purpose)
        model = get_model(config, purpose)
        temperature = get_temperature(config, purpose)

        return self.send_message(
            system=system,
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )
