"""AgenticSearch モジュール — Protocol 定義と SearchResult dataclass.

具象実装 (HaikuEngine) は Wave 3 (Task 3-1) で追加される。
本モジュールは Protocol と dataclass のみを定義し、外部依存を持たない。

対応要件: FR-9.10
"""

from __future__ import annotations

import typing
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Web 検索の 1 件分の結果を保持するデータクラス。

    Attributes:
        title: 検索結果のページタイトル。
        url: 検索結果の URL。
        snippet: ページの要約テキスト（スニペット）。
    """

    title: str
    url: str
    snippet: str


@typing.runtime_checkable
class AgenticSearchEngine(typing.Protocol):
    """AgenticSearch パイプラインのエンジン抽象インターフェース。

    HaikuEngine (Wave 3, Task 3-1) がこの Protocol を実装する。
    将来的な LocalLLMEngine (Phase 3) への差し替えも、この Protocol を実装することで
    上位ロジックを変更せずに行える（US-19 に対応）。

    メソッド概要:
        decompose_query: トピックを複数のサブクエリに分解する（LLM を使用）。
        search: 単一クエリに対して Web 検索を実行する。
        summarize: 検索結果をトピックに沿って要約する（LLM を使用）。
        extract_noise_topics: 検索結果から派生テーマを抽出する（LLM を使用）。
    """

    def decompose_query(self, topic: str) -> list[str]:
        """トピックをサブクエリのリストに分解する。

        Args:
            topic: 調査対象のトピック文字列。

        Returns:
            2〜max_subqueries 個のサブクエリ文字列リスト。
        """
        ...

    def search(self, query: str) -> list[SearchResult]:
        """単一クエリに対する検索を実行する。

        Args:
            query: 検索クエリ。

        Returns:
            SearchResult のリスト（最大 5 件程度）。
        """
        ...

    def summarize(self, topic: str, results: list[SearchResult]) -> str:
        """検索結果をトピックに沿って要約する。

        Args:
            topic: 調査対象トピック（要約の方向付け）。
            results: 検索結果のリスト。

        Returns:
            要約テキスト。
        """
        ...

    def extract_noise_topics(self, results: list[SearchResult]) -> list[str]:
        """検索結果から派生テーマを抽出する。

        Args:
            results: 検索結果のリスト。

        Returns:
            0〜3 個の派生テーマ文字列リスト（FR-9.8）。
        """
        ...
