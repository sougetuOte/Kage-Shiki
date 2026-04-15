"""tests/test_agent/test_agentic_search.py

AgenticSearchEngine Protocol と SearchResult dataclass のテスト (FR-9.10)。
"""

from __future__ import annotations

import inspect
import typing

import pytest

# --------------------------------------------------------------------------- #
# SearchResult dataclass
# --------------------------------------------------------------------------- #


class TestSearchResult:
    """SearchResult dataclass の構造と動作を検証する。"""

    def test_has_three_fields(self) -> None:
        """SearchResult が title / url / snippet の 3 フィールドを持つこと。"""
        from kage_shiki.agent.agentic_search import SearchResult

        fields = {f.name for f in SearchResult.__dataclass_fields__.values()}
        assert fields == {"title", "url", "snippet"}

    def test_instantiation_and_field_access(self) -> None:
        """SearchResult インスタンスを生成してフィールドにアクセスできること。"""
        from kage_shiki.agent.agentic_search import SearchResult

        result = SearchResult(
            title="テストタイトル",
            url="https://example.com",
            snippet="テストの要約テキスト。",
        )
        assert result.title == "テストタイトル"
        assert result.url == "https://example.com"
        assert result.snippet == "テストの要約テキスト。"

    def test_fields_are_required(self) -> None:
        """SearchResult は引数なしで生成できないこと（全フィールド必須）。"""
        from kage_shiki.agent.agentic_search import SearchResult

        with pytest.raises(TypeError):
            SearchResult()  # type: ignore[call-arg]

    def test_equality(self) -> None:
        """同じフィールド値を持つ SearchResult インスタンスが等値であること。"""
        from kage_shiki.agent.agentic_search import SearchResult

        a = SearchResult(title="T", url="U", snippet="S")
        b = SearchResult(title="T", url="U", snippet="S")
        assert a == b


# --------------------------------------------------------------------------- #
# AgenticSearchEngine Protocol 構造
# --------------------------------------------------------------------------- #


class TestAgenticSearchEngineProtocol:
    """AgenticSearchEngine が typing.Protocol として正しく定義されていることを検証する。"""

    def test_is_protocol(self) -> None:
        """AgenticSearchEngine が typing.Protocol のサブクラスであること。"""
        from kage_shiki.agent.agentic_search import AgenticSearchEngine

        assert issubclass(AgenticSearchEngine, typing.Protocol)

    def test_is_runtime_checkable(self) -> None:
        """AgenticSearchEngine が @runtime_checkable であること。"""
        from kage_shiki.agent.agentic_search import AgenticSearchEngine

        # runtime_checkable でなければ isinstance() が TypeError を送出する
        try:
            result = isinstance(object(), AgenticSearchEngine)
        except TypeError as exc:
            pytest.fail(f"@runtime_checkable が付与されていない: {exc}")
        # object() は Protocol のメソッドを実装していないので False が返る
        assert result is False, (
            "素の object() が AgenticSearchEngine Protocol に isinstance=True を"
            "返した: Protocol 制約が検出されていない"
        )

    def test_has_required_four_methods(self) -> None:
        """必須 4 メソッドが Protocol に callable として定義されていること (W-12).

        `dir()` ではなく `hasattr` + `callable` で検証する（`object` 継承属性との
        誤検知を防ぐ）。
        """
        from kage_shiki.agent.agentic_search import AgenticSearchEngine

        required = ("decompose_query", "search", "summarize", "extract_noise_topics")
        for method_name in required:
            assert hasattr(AgenticSearchEngine, method_name), (
                f"Protocol に {method_name} が定義されていない"
            )
            attr = getattr(AgenticSearchEngine, method_name)
            assert callable(attr), f"{method_name} が callable でない"


# --------------------------------------------------------------------------- #
# シグネチャ検証
# --------------------------------------------------------------------------- #


class TestAgenticSearchEngineSignatures:
    """各メソッドのシグネチャが設計書・要件書に準拠していることを検証する。"""

    def test_decompose_query_signature(self) -> None:
        """decompose_query(self, topic: str) -> list[str] であること。"""
        from kage_shiki.agent.agentic_search import AgenticSearchEngine

        sig = inspect.signature(AgenticSearchEngine.decompose_query)
        params = list(sig.parameters.keys())
        assert params == ["self", "topic"], f"引数が異なる: {params}"

        hints = typing.get_type_hints(AgenticSearchEngine.decompose_query)
        assert hints.get("topic") is str
        # 戻り値は list[str]
        return_hint = hints.get("return")
        assert return_hint is not None, "戻り値アノテーションがない"
        assert return_hint == list[str]

    def test_search_signature(self) -> None:
        """search(self, query: str) -> list[SearchResult] であること。"""
        from kage_shiki.agent.agentic_search import AgenticSearchEngine, SearchResult

        sig = inspect.signature(AgenticSearchEngine.search)
        params = list(sig.parameters.keys())
        assert params == ["self", "query"], f"引数が異なる: {params}"

        hints = typing.get_type_hints(AgenticSearchEngine.search)
        assert hints.get("query") is str
        assert hints.get("return") == list[SearchResult]

    def test_summarize_signature(self) -> None:
        """summarize(self, topic: str, results: list[SearchResult]) -> str であること。

        要件書 Rev.1 で確定したシグネチャ (topic, results) -> str を検証する。
        """
        from kage_shiki.agent.agentic_search import AgenticSearchEngine, SearchResult

        sig = inspect.signature(AgenticSearchEngine.summarize)
        params = list(sig.parameters.keys())
        assert params == ["self", "topic", "results"], f"引数順が異なる: {params}"

        hints = typing.get_type_hints(AgenticSearchEngine.summarize)
        assert hints.get("topic") is str
        assert hints.get("results") == list[SearchResult]
        assert hints.get("return") is str

    def test_extract_noise_topics_signature(self) -> None:
        """extract_noise_topics(self, results: list[SearchResult]) -> list[str] であること。"""
        from kage_shiki.agent.agentic_search import AgenticSearchEngine, SearchResult

        sig = inspect.signature(AgenticSearchEngine.extract_noise_topics)
        params = list(sig.parameters.keys())
        assert params == ["self", "results"], f"引数が異なる: {params}"

        hints = typing.get_type_hints(AgenticSearchEngine.extract_noise_topics)
        assert hints.get("results") == list[SearchResult]
        assert hints.get("return") == list[str]


# --------------------------------------------------------------------------- #
# isinstance チェック（runtime_checkable 動作確認）
# --------------------------------------------------------------------------- #


class TestAgenticSearchEngineInstanceCheck:
    """isinstance() による Protocol 準拠チェックを検証する。"""

    def test_complete_implementation_passes_isinstance(self) -> None:
        """4 メソッドをすべて実装したダミークラスが isinstance で True を返すこと。"""
        from kage_shiki.agent.agentic_search import AgenticSearchEngine, SearchResult

        class _DummyEngine:
            def decompose_query(self, topic: str) -> list[str]:
                return []

            def search(self, query: str) -> list[SearchResult]:
                return []

            def summarize(self, topic: str, results: list[SearchResult]) -> str:
                return ""

            def extract_noise_topics(self, results: list[SearchResult]) -> list[str]:
                return []

        assert isinstance(_DummyEngine(), AgenticSearchEngine)

    def test_incomplete_implementation_fails_isinstance(self) -> None:
        """必須メソッドが欠けた実装が isinstance で False を返すこと。"""
        from kage_shiki.agent.agentic_search import AgenticSearchEngine

        class _IncompleteEngine:
            """search のみを実装（残り 3 メソッドが欠ける）。"""

            def search(self, query: str) -> list:
                return []

        assert not isinstance(_IncompleteEngine(), AgenticSearchEngine)

    def test_empty_class_fails_isinstance(self) -> None:
        """何もメソッドを持たないクラスが isinstance で False を返すこと。"""
        from kage_shiki.agent.agentic_search import AgenticSearchEngine

        class _EmptyEngine:
            pass

        assert not isinstance(_EmptyEngine(), AgenticSearchEngine)
