"""テスト共通フィクスチャ.

全テストモジュールから参照される共通フィクスチャを定義する。
各テストモジュールで同名のローカルフィクスチャが定義されている場合、
ローカルが優先される（pytest のフィクスチャ解決規則）。
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from kage_shiki.agent.llm_client import LLMProtocol
from kage_shiki.core.config import AppConfig


@pytest.fixture()
def mock_llm() -> Mock:
    """LLMProtocol のモック（共通）.

    send_message_for_purpose / chat にデフォルト戻り値を設定。
    テストケースごとに return_value や side_effect でカスタマイズ可能。
    """
    m = Mock(spec=LLMProtocol)
    m.send_message_for_purpose.return_value = "テスト応答"
    m.chat.return_value = "テスト応答"
    return m


@pytest.fixture()
def config() -> AppConfig:
    """デフォルト AppConfig."""
    return AppConfig()


@pytest.fixture()
def project_root() -> Path:
    """プロジェクトルートディレクトリを返す.

    tests/conftest.py は tests/ 直下にあるため、
    その親がプロジェクトルートになる。

    Returns:
        Path: プロジェクトルートの絶対パス。
    """
    return Path(__file__).parent.parent
