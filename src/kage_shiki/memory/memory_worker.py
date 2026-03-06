"""MemoryWorker — 日次サマリー生成 + 欠損補完 (T-18).

対応 FR:
    FR-3.8: シャットダウン時の日次サマリー生成
    FR-3.10: 起動時の欠損日補完
    FR-7.5: サマリー生成失敗時のログ記録（EM-009）
"""

import logging
import sqlite3

from kage_shiki.agent.llm_client import LLMClient
from kage_shiki.memory.db import (
    get_day_observations,
    get_missing_summary_dates,
    save_day_summary,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# サマリー生成プロンプト
# ---------------------------------------------------------------------------

_SUMMARY_SYSTEM = (
    "あなたはキャラクターの日記係です。"
    "以下の会話ログから、5-8文の日記形式で要約を作成してください。"
    "キャラクターの視点で、その日あった出来事や印象的な会話を記録してください。\n\n"
    "応答は日記テキストのみを出力してください。"
)


def _format_observations_for_prompt(observations: list[dict]) -> str:
    """observations をプロンプト用テキストにフォーマットする."""
    lines: list[str] = []
    for obs in observations:
        speaker = obs["speaker"]
        content = obs["content"]
        lines.append(f"[{speaker}] {content}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MemoryWorker
# ---------------------------------------------------------------------------


class MemoryWorker:
    """日次サマリー生成 + 欠損補完 (FR-3.8, FR-3.10).

    Attributes:
        _db_conn: DB 接続。
        _llm: LLM クライアント。
    """

    def __init__(
        self,
        db_conn: sqlite3.Connection,
        llm_client: LLMClient,
    ) -> None:
        self._db_conn = db_conn
        self._llm = llm_client

    def generate_daily_summary(self, date_str: str) -> str | None:
        """指定日の日次サマリーを生成する (FR-3.8).

        Args:
            date_str: 日付文字列（YYYY-MM-DD 形式）。

        Returns:
            生成されたサマリーテキスト。observations がない場合は None。

        Raises:
            LLMError: API 呼び出し失敗。
            sqlite3.IntegrityError: 同一日のサマリーが既に存在する場合。
        """
        # 既にサマリーが存在する場合はスキップ（UNIQUE 制約違反防止）
        existing = self._db_conn.execute(
            "SELECT 1 FROM day_summary WHERE date = ?", (date_str,),
        ).fetchone()
        if existing:
            logger.info("サマリー既存: %s（生成スキップ）", date_str)
            return None

        observations = get_day_observations(self._db_conn, date_str)
        if not observations:
            logger.info("observations なし: %s（サマリー生成スキップ）", date_str)
            return None

        log_text = _format_observations_for_prompt(observations)
        user_msg = (
            f"以下は {date_str} の会話ログです。"
            f"日記形式で要約してください。\n\n{log_text}"
        )

        summary = self._llm.send_message_for_purpose(
            system=_SUMMARY_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
            purpose="memory_worker",
        )

        save_day_summary(self._db_conn, date_str, summary)
        logger.info("日次サマリー生成完了: %s", date_str)
        return summary

    def generate_daily_summary_sync(self, date_str: str) -> str | None:
        """シャットダウン用の同期版サマリー生成 (FR-3.8, FR-7.5).

        失敗時は例外を送出せず、EM-009 ログを記録して None を返す。
        次回起動時に check_and_fill_missing_summaries で再試行される。

        Args:
            date_str: 日付文字列（YYYY-MM-DD 形式）。

        Returns:
            生成されたサマリーテキスト。失敗時は None。
        """
        try:
            return self.generate_daily_summary(date_str)
        except Exception:
            logger.warning(
                "EM-009: サマリー生成失敗 date=%s（次回起動時に再試行）",
                date_str,
                exc_info=True,
            )
            return None

    def check_and_fill_missing_summaries(self) -> list[str]:
        """起動時の欠損日補完 (FR-3.10).

        observations に存在するが day_summary に存在しない日を検出し、
        各欠損日のサマリーを生成する。個別の失敗は他の日に影響しない。

        Returns:
            サマリーを生成した日付のリスト。
        """
        missing = get_missing_summary_dates(self._db_conn)
        if not missing:
            logger.info("欠損日なし")
            return []

        logger.info("欠損日検出: %d日分", len(missing))
        filled: list[str] = []

        for date_str in missing:
            try:
                result = self.generate_daily_summary(date_str)
                if result is not None:
                    filled.append(date_str)
            except Exception:
                logger.warning(
                    "EM-009: 欠損補完失敗 date=%s（スキップ）",
                    date_str,
                    exc_info=True,
                )

        logger.info("欠損補完完了: %d/%d日分", len(filled), len(missing))
        return filled
