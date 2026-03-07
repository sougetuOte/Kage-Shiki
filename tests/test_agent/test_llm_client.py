"""LLMClient のテスト (T-07).

対応 FR: FR-6.7, FR-7.1, FR-7.2, FR-8.6
対応設計: D-15（用途別 max_tokens）, D-17（LLMProtocol 抽出）
"""

from unittest.mock import MagicMock, patch

import anthropic
import pytest

from kage_shiki.agent.llm_client import AuthenticationError, LLMClient, LLMError, LLMProtocol
from kage_shiki.core.config import ApiConfig, AppConfig, ConversationConfig


@pytest.fixture()
def config() -> AppConfig:
    """テスト用 AppConfig を返す."""
    return AppConfig(
        api=ApiConfig(max_retries=3, retry_backoff_base=0.01, timeout=5),
        conversation=ConversationConfig(max_tokens=1024, temperature=0.7),
    )


@pytest.fixture()
def client(config: AppConfig) -> LLMClient:
    """テスト用 LLMClient を返す."""
    return LLMClient(config)


def _make_mock_response(text: str = "こんにちは") -> MagicMock:
    """テスト用の LLM レスポンス mock を生成する."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=text)]
    mock_response.usage.input_tokens = 100
    mock_response.usage.output_tokens = 50
    return mock_response


class TestLLMClientSendMessage:
    """send_message() の動作検証."""

    def test_returns_response_text(self, client: LLMClient) -> None:
        """正常時に LLM レスポンステキストが返ること."""
        with patch.object(
            client._client.messages, "create",
            return_value=_make_mock_response(),
        ):
            result = client.send_message(
                system="あなたはマスコットです",
                messages=[{"role": "user", "content": "やあ"}],
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                temperature=0.7,
            )
        assert result == "こんにちは"

    def test_retries_on_transient_error(self, client: LLMClient) -> None:
        """一時的エラー時にリトライが行われること."""
        error = anthropic.APIStatusError(
            message="overloaded",
            response=MagicMock(status_code=529, headers={}),
            body=None,
        )

        call_count = 0

        def side_effect(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise error
            return _make_mock_response("成功")

        with patch.object(client._client.messages, "create", side_effect=side_effect):
            result = client.send_message(
                system="test",
                messages=[{"role": "user", "content": "test"}],
                model="claude-haiku-4-5-20251001",
                max_tokens=512,
                temperature=0.7,
            )
        assert result == "成功"
        assert call_count == 3

    def test_raises_after_max_retries(self, client: LLMClient) -> None:
        """リトライ上限に達した場合に例外が発生すること."""
        error = anthropic.APIStatusError(
            message="overloaded",
            response=MagicMock(status_code=529, headers={}),
            body=None,
        )

        with (
            patch.object(client._client.messages, "create", side_effect=error),
            pytest.raises(LLMError, match="リトライ上限"),
        ):
            client.send_message(
                system="test",
                messages=[{"role": "user", "content": "test"}],
                model="claude-haiku-4-5-20251001",
                max_tokens=512,
                temperature=0.7,
            )

    def test_authentication_error_on_401(self, client: LLMClient) -> None:
        """401 エラーで AuthenticationError が発生すること."""
        error = anthropic.AuthenticationError(
            message="invalid api key",
            response=MagicMock(status_code=401, headers={}),
            body=None,
        )

        with (
            patch.object(client._client.messages, "create", side_effect=error),
            pytest.raises(AuthenticationError),
        ):
            client.send_message(
                system="test",
                messages=[{"role": "user", "content": "test"}],
                model="claude-haiku-4-5-20251001",
                max_tokens=512,
                temperature=0.7,
            )

    def test_authentication_error_on_403(self, client: LLMClient) -> None:
        """403 エラーで AuthenticationError が発生すること."""
        error = anthropic.PermissionDeniedError(
            message="permission denied",
            response=MagicMock(status_code=403, headers={}),
            body=None,
        )

        with (
            patch.object(client._client.messages, "create", side_effect=error),
            pytest.raises(AuthenticationError),
        ):
            client.send_message(
                system="test",
                messages=[{"role": "user", "content": "test"}],
                model="claude-haiku-4-5-20251001",
                max_tokens=512,
                temperature=0.7,
            )

    def test_retries_on_connection_error(self, client: LLMClient) -> None:
        """APIConnectionError 時にリトライが行われること (WARN-003)."""
        error = anthropic.APIConnectionError(request=MagicMock())

        call_count = 0

        def side_effect(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise error
            return _make_mock_response("接続回復")

        with patch.object(client._client.messages, "create", side_effect=side_effect):
            result = client.send_message(
                system="test",
                messages=[{"role": "user", "content": "test"}],
                model="claude-haiku-4-5-20251001",
                max_tokens=512,
                temperature=0.7,
            )
        assert result == "接続回復"
        assert call_count == 2

    def test_exponential_backoff_timing(self) -> None:
        """指数バックオフの待機時間が正しいこと（time.sleep mock）."""
        config_fast = AppConfig(
            api=ApiConfig(max_retries=2, retry_backoff_base=0.5, timeout=5),
        )
        fast_client = LLMClient(config_fast)

        error = anthropic.APIStatusError(
            message="overloaded",
            response=MagicMock(status_code=529, headers={}),
            body=None,
        )

        with (
            patch.object(fast_client._client.messages, "create", side_effect=error),
            patch("kage_shiki.agent.llm_client.time.sleep") as mock_sleep,
            pytest.raises(LLMError),
        ):
            fast_client.send_message(
                system="test",
                messages=[{"role": "user", "content": "test"}],
                model="claude-haiku-4-5-20251001",
                max_tokens=512,
                temperature=0.7,
            )

        # backoff_base=0.5: 1回目 0.5*2^0=0.5, 2回目 0.5*2^1=1.0
        assert mock_sleep.call_count == 2
        assert mock_sleep.call_args_list[0].args[0] == pytest.approx(0.5)
        assert mock_sleep.call_args_list[1].args[0] == pytest.approx(1.0)


class TestLLMClientSendForPurpose:
    """send_message_for_purpose() の動作検証."""

    def test_conversation_purpose(self, client: LLMClient) -> None:
        """purpose='conversation' で正しい max_tokens と temperature が使われること."""
        with patch.object(
            client._client.messages, "create",
            return_value=_make_mock_response("応答"),
        ) as mock_create:
            client.send_message_for_purpose(
                system="test",
                messages=[{"role": "user", "content": "test"}],
                purpose="conversation",
            )
            kwargs = mock_create.call_args.kwargs
            assert kwargs["max_tokens"] == 1024
            assert kwargs["temperature"] == 0.7

    def test_wizard_generate_purpose(self, client: LLMClient) -> None:
        """purpose='wizard_generate' で max_tokens=2048, temperature=0.9 が使われること."""
        with patch.object(
            client._client.messages, "create",
            return_value=_make_mock_response("応答"),
        ) as mock_create:
            client.send_message_for_purpose(
                system="test",
                messages=[{"role": "user", "content": "test"}],
                purpose="wizard_generate",
            )
            kwargs = mock_create.call_args.kwargs
            assert kwargs["max_tokens"] == 2048
            assert kwargs["temperature"] == 0.9

    def test_wizard_association_purpose(self, client: LLMClient) -> None:
        """purpose='wizard_association' で max_tokens=512 が使われること."""
        with patch.object(
            client._client.messages, "create",
            return_value=_make_mock_response("応答"),
        ) as mock_create:
            client.send_message_for_purpose(
                system="test",
                messages=[{"role": "user", "content": "test"}],
                purpose="wizard_association",
            )
            kwargs = mock_create.call_args.kwargs
            assert kwargs["max_tokens"] == 512
            assert kwargs["temperature"] == 0.9

    def test_human_block_update_purpose(self, client: LLMClient) -> None:
        """purpose='human_block_update' で max_tokens=256, temperature=0.3 が使われること."""
        with patch.object(
            client._client.messages, "create",
            return_value=_make_mock_response("応答"),
        ) as mock_create:
            client.send_message_for_purpose(
                system="test",
                messages=[{"role": "user", "content": "test"}],
                purpose="human_block_update",
            )
            kwargs = mock_create.call_args.kwargs
            assert kwargs["max_tokens"] == 256
            assert kwargs["temperature"] == 0.3

    def test_memory_summary_purpose(self, client: LLMClient) -> None:
        """purpose='memory_summary' で max_tokens=800 が使われること."""
        with patch.object(
            client._client.messages, "create",
            return_value=_make_mock_response("応答"),
        ) as mock_create:
            client.send_message_for_purpose(
                system="test",
                messages=[{"role": "user", "content": "test"}],
                purpose="memory_summary",
            )
            kwargs = mock_create.call_args.kwargs
            assert kwargs["max_tokens"] == 800
            assert kwargs["temperature"] == 0.3

    def test_poke_purpose(self, client: LLMClient) -> None:
        """purpose='poke' で max_tokens=256 が使われること."""
        with patch.object(
            client._client.messages, "create",
            return_value=_make_mock_response("応答"),
        ) as mock_create:
            client.send_message_for_purpose(
                system="test",
                messages=[{"role": "user", "content": "test"}],
                purpose="poke",
            )
            kwargs = mock_create.call_args.kwargs
            assert kwargs["max_tokens"] == 256
            assert kwargs["temperature"] == 0.7

    def test_wizard_preview_purpose(self, client: LLMClient) -> None:
        """purpose='wizard_preview' で max_tokens=1024 が使われること."""
        with patch.object(
            client._client.messages, "create",
            return_value=_make_mock_response("応答"),
        ) as mock_create:
            client.send_message_for_purpose(
                system="test",
                messages=[{"role": "user", "content": "test"}],
                purpose="wizard_preview",
            )
            kwargs = mock_create.call_args.kwargs
            assert kwargs["max_tokens"] == 1024
            assert kwargs["temperature"] == 0.7

    def test_memory_worker_purpose(self, client: LLMClient) -> None:
        """purpose='memory_worker' で max_tokens=800, temperature=0.3 が使われること."""
        with patch.object(
            client._client.messages, "create",
            return_value=_make_mock_response("応答"),
        ) as mock_create:
            client.send_message_for_purpose(
                system="test",
                messages=[{"role": "user", "content": "test"}],
                purpose="memory_worker",
            )
            kwargs = mock_create.call_args.kwargs
            assert kwargs["max_tokens"] == 800
            assert kwargs["temperature"] == 0.3

    def test_unknown_purpose_raises_error(self, client: LLMClient) -> None:
        """未知の purpose で LLMError が発生すること."""
        with pytest.raises(LLMError, match="未知の purpose"):
            client.send_message_for_purpose(
                system="test",
                messages=[{"role": "user", "content": "test"}],
                purpose="nonexistent",
            )


class TestLLMProtocol:
    """FR-8.6: LLMProtocol の Protocol 互換性テスト (D-17).

    対応 FR: FR-8.6
    対応設計: D-17（LLMProtocol 抽出）

    テストケース:
        FR-8.6-1: LLMProtocol が typing.Protocol として定義されている
        FR-8.6-2: isinstance(LLMClient(config), LLMProtocol) が True
        FR-8.6-3: LLMProtocol を実装したモッククラスが isinstance で True
        FR-8.6-4: LLMClient.chat() が send_message() に正しく委譲する
        FR-8.6-5: Protocol を満たさないクラスの isinstance が False になる（異常系）
    """

    def test_llm_protocol_is_protocol(self) -> None:
        """FR-8.6-1: LLMProtocol が typing.Protocol として定義されていること."""
        from typing import Protocol
        assert issubclass(LLMProtocol, Protocol)

    def test_llm_client_satisfies_protocol(self, client: LLMClient) -> None:
        """FR-8.6-2: LLMClient インスタンスが LLMProtocol を満足すること."""
        assert isinstance(client, LLMProtocol)

    def test_mock_client_satisfies_protocol(self) -> None:
        """FR-8.6-3: chat() + send_message_for_purpose() を実装した
        モッククラスが LLMProtocol を満足すること."""
        class MockLLMClient:
            """テスト用 LLMProtocol 実装（D-17 Section 6.2 のモック設計に準拠）."""

            def __init__(self, response: str = "テスト応答") -> None:
                self._response = response
                self.calls: list[dict] = []

            def chat(
                self,
                messages: list[dict],
                *,
                system: str,
                model: str,
                max_tokens: int,
                temperature: float,
            ) -> str:
                self.calls.append({
                    "messages": messages,
                    "system": system,
                    "model": model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                })
                return self._response

            def send_message_for_purpose(
                self,
                system: str,
                messages: list[dict],
                purpose: str,
            ) -> str:
                return self._response

        mock_client = MockLLMClient()
        assert isinstance(mock_client, LLMProtocol)

    def test_chat_delegates_to_send_message(self, client: LLMClient) -> None:
        """FR-8.6-4: LLMClient.chat() が send_message() に正しく委譲すること."""
        with patch.object(
            client._client.messages, "create",
            return_value=_make_mock_response("chat委譲テスト"),
        ) as mock_create:
            result = client.chat(
                messages=[{"role": "user", "content": "テスト"}],
                system="システムプロンプト",
                model="claude-haiku-4-5-20251001",
                max_tokens=512,
                temperature=0.7,
            )
        assert result == "chat委譲テスト"
        kwargs = mock_create.call_args.kwargs
        assert kwargs["system"] == "システムプロンプト"
        assert kwargs["model"] == "claude-haiku-4-5-20251001"
        assert kwargs["max_tokens"] == 512
        assert kwargs["temperature"] == 0.7

    def test_class_without_chat_does_not_satisfy_protocol(self) -> None:
        """FR-8.6-5: chat() を実装していないクラスは LLMProtocol を満足しないこと（異常系）."""
        class NoChatClass:
            """chat() メソッドを持たないクラス."""
            def send_message(
                self, messages: list[dict], *,
                system: str, model: str, max_tokens: int, temperature: float,
            ) -> str:
                return "no chat"

        instance = NoChatClass()
        assert not isinstance(instance, LLMProtocol)
