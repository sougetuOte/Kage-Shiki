"""応答タイミング統合テスト (T-32, FR-8.11).

FR-8.11: GUI 統合後の応答時間（5 秒以内）をテストで検証する。
    受入条件:
    (1) TkinterMascotView と AgentCore を接続した統合テストで、
        input_queue enqueue から display_text() 呼び出しまで 5 秒以内
    (2) LLM は LLMProtocol 実装モックを使用（ネットワーク不要）
    (3) タイムアウトしても他のテストをブロックしない

設計: D-20 Section 4.4

Note:
    main.py の _run_background_loop / _start_response_polling は _ プレフィックス付きだが、
    D-20 Section 4.4 の設計で統合テストからの直接利用が意図されている（test_startup.py と同様）。
    tkinter ポーリングループ内の time.sleep(0.01) は D-20 設計例準拠
    （root.update() でイベント処理するために必要、Event.wait() では代替不可）。
"""

import contextlib
import queue
import threading
import time
import tkinter as tk

import pytest

from kage_shiki.agent.agent_core import AgentCore
from kage_shiki.agent.llm_client import LLMProtocol
from kage_shiki.agent.prompt_builder import PromptBuilder
from kage_shiki.core.config import AppConfig
from kage_shiki.gui.tkinter_view import TkinterMascotView
from kage_shiki.main import _run_background_loop, _start_response_polling
from kage_shiki.memory.db import Database, initialize_db
from kage_shiki.persona.persona_system import PersonaSystem

from .conftest import SAMPLE_PERSONA_CORE, SAMPLE_STYLE_SAMPLES

# ---------------------------------------------------------------------------
# MockLLMClientForTiming (D-20 Section 4.4)
# ---------------------------------------------------------------------------


class MockLLMClientForTiming:
    """タイミングテスト用 LLMProtocol 実装.

    chat() への委譲パターンは検証対象外とした簡略実装。
    AgentCore は send_message_for_purpose() を直接呼び出すため両メソッドを実装する。
    この設計上の張力は D-17 に記録済み（Phase 3 での解消予定）。
    """

    def __init__(
        self,
        response: str = "テスト応答",
        delay_seconds: float = 0.0,
    ) -> None:
        self._response = response
        self._delay = delay_seconds

    def chat(self, messages, *, system, model, max_tokens, temperature) -> str:
        if self._delay > 0:
            time.sleep(self._delay)
        return self._response

    def send_message_for_purpose(self, system, messages, purpose) -> str:
        """AgentCore が直接呼び出す便利メソッド."""
        if self._delay > 0:
            time.sleep(self._delay)
        return self._response


# ---------------------------------------------------------------------------
# テスト
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestResponseTiming:
    """FR-8.11: 応答タイミング統合テスト."""

    def test_response_within_5_seconds(self, tmp_path, persona_data_dir) -> None:
        """input_queue enqueue から display_text() 呼び出しまで 5 秒以内."""
        # --- Arrange ---
        # DB
        db = Database(tmp_path / "memory.db")
        conn = db.connect()
        initialize_db(conn)

        # LLM モック（即時応答・LLMProtocol 準拠を検証）
        mock_llm = MockLLMClientForTiming(response="テスト応答", delay_seconds=0.0)
        assert isinstance(mock_llm, LLMProtocol)

        # Config（persona_data_dir fixture からペルソナファイルを利用）
        config = AppConfig()
        config.general.data_dir = str(persona_data_dir)

        # PersonaSystem + PromptBuilder
        persona_system = PersonaSystem()
        prompt_builder = PromptBuilder(
            persona_core=SAMPLE_PERSONA_CORE.to_markdown(),
            style_samples=SAMPLE_STYLE_SAMPLES,
            human_block="",
        )

        # AgentCore
        agent_core = AgentCore(
            config=config,
            db_conn=conn,
            llm_client=mock_llm,
            persona_system=persona_system,
            prompt_builder=prompt_builder,
            data_dir=persona_data_dir,
        )

        # キュー + シャットダウンイベント
        input_queue: queue.Queue[str] = queue.Queue()
        response_queue: queue.Queue[str] = queue.Queue()
        shutdown_event = threading.Event()

        # tkinter GUI
        root = tk.Tk()
        root.withdraw()
        mascot_view = TkinterMascotView(root, input_queue, config.gui)

        # display_text() 呼び出しを捕捉（テキスト内容でフィルタリング可能）
        displayed_texts: list[tuple[float, str]] = []
        original_display_text = mascot_view.display_text

        def _capture_display_text(text: str) -> None:
            displayed_texts.append((time.monotonic(), text))
            original_display_text(text)

        mascot_view.display_text = _capture_display_text

        # --- Act ---
        bg_thread = None
        try:
            # バックグラウンドスレッド起動
            bg_thread = threading.Thread(
                target=_run_background_loop,
                args=(agent_core, input_queue, response_queue, shutdown_event),
                daemon=True,
            )
            bg_thread.start()

            # 応答ポーリング開始
            _start_response_polling(root, mascot_view, response_queue, shutdown_event)

            # セッション開始メッセージの完了を待機（root.update() で処理）
            greeting_deadline = time.monotonic() + 5.0
            while time.monotonic() < greeting_deadline and len(displayed_texts) == 0:
                root.update()
                time.sleep(0.01)

            assert len(displayed_texts) > 0, (
                "セッション開始メッセージが 5 秒以内に display_text() されませんでした"
            )

            # 開始メッセージをクリアして計測準備
            displayed_texts.clear()

            # 計測開始: put の直前に start_time を記録
            start_time = time.monotonic()
            input_queue.put("テスト入力")

            # display_text() が呼ばれるまでポーリング（最大 5 秒）
            deadline = start_time + 5.0
            while time.monotonic() < deadline and len(displayed_texts) == 0:
                root.update()
                time.sleep(0.01)

            # --- Assert ---
            assert len(displayed_texts) > 0, (
                "5 秒以内に display_text() が呼ばれませんでした"
            )
            elapsed = displayed_texts[0][0] - start_time
            assert elapsed < 5.0, f"応答タイムアウト: {elapsed:.2f}s"

        finally:
            # クリーンアップ: shutdown → スレッド join → GUI → DB の順
            shutdown_event.set()
            if bg_thread is not None:
                bg_thread.join(timeout=2.0)
            with contextlib.suppress(tk.TclError):
                root.update()
            root.destroy()
            db.close()
