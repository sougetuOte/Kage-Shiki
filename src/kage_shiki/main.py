"""影式 (Kage-Shiki) エントリポイント — 起動シーケンス統合 (T-25, D-16).

requirements.md Section 5.5 の起動シーケンスに D-10 規定の .env 読み込みを
Step 0 として追加した 13 ステップ構成。

Step 0:  .env ファイル読み込み
Step 1:  config.toml 読み込み
Step 2:  ANTHROPIC_API_KEY 存在確認
Step 3:  data_dir 初期化 + logging + SQLite DB 作成
Step 4:  persona_core.md 存在チェック → 不在ならウィザード起動
Step 5:  凍結状態チェック: 手動編集検出
Step 6:  Hot Memory ロード
Step 7:  日次サマリー欠損チェック → 補完生成
Step 8:  Warm Memory ロード
Step 9:  プロンプト構築（PromptBuilder 生成）
Step 10: SessionContext 初期化（AgentCore 生成）
Step 11: シャットダウンコールバック + GUI + トレイ
Step 12: バックグラウンドスレッド起動 + シャットダウンハンドラ登録 + メインループ
"""

import atexit
import logging
import queue
import sys
import threading
import tkinter as tk
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from kage_shiki.agent.agent_core import AgentCore, PromptBuilder
from kage_shiki.agent.llm_client import LLMClient
from kage_shiki.agent.trends_proposal import TrendsProposalManager
from kage_shiki.core.config import load_config
from kage_shiki.core.env import ensure_api_key, load_dotenv_file
from kage_shiki.core.errors import format_error_message
from kage_shiki.core.logging_setup import setup_logging
from kage_shiki.core.shutdown_handler import (
    make_atexit_handler,
    register_windows_ctrl_handler,
)
from kage_shiki.gui.tkinter_view import TkinterMascotView
from kage_shiki.gui.wizard_gui import WizardGUI
from kage_shiki.memory.db import (
    Database,
    get_recent_day_summaries,
    initialize_db,
)
from kage_shiki.memory.memory_worker import MemoryWorker
from kage_shiki.persona.persona_system import PersonaLoadError, PersonaSystem
from kage_shiki.persona.wizard import WizardController
from kage_shiki.tray.system_tray import SystemTray

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

_POLL_INTERVAL_MS = 100


# ---------------------------------------------------------------------------
# バックグラウンドループ (D-16 Section 4.3)
# ---------------------------------------------------------------------------


def _run_background_loop(
    agent_core: AgentCore,
    input_queue: queue.Queue[str],
    response_queue: queue.Queue[str],
    shutdown_event: threading.Event,
    *,
    persona_name: str = "",
) -> None:
    """バックグラウンドスレッドのメインループ.

    セッション開始メッセージを生成した後、input_queue を 0.1 秒間隔で
    ポーリングし、process_turn() で応答を生成して response_queue に返す。

    Args:
        agent_core: 対話エンジン。
        input_queue: ユーザー入力キュー（メイン → バックグラウンド）。
        response_queue: 応答キュー（バックグラウンド → メイン）。
        shutdown_event: graceful shutdown 通知。
        persona_name: ペルソナ名（EM-006 メッセージ用）。
    """
    name_prefix = f"{persona_name}「" if persona_name else ""

    # セッション開始メッセージ生成
    try:
        greeting = agent_core.generate_session_start_message()
        response_queue.put(greeting)
    except Exception:
        logger.error("セッション開始メッセージの生成に失敗", exc_info=True)
        response_queue.put(
            format_error_message("EM-006", name_prefix=name_prefix),
        )

    # 対話ループ
    while not shutdown_event.is_set():
        try:
            user_input = input_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        try:
            response = agent_core.process_turn(user_input)
            response_queue.put(response)
        except Exception:
            logger.error("process_turn 失敗", exc_info=True)
            response_queue.put(
                format_error_message("EM-006", name_prefix=name_prefix),
            )


# ---------------------------------------------------------------------------
# 応答ポーリング + シャットダウン監視 (D-16 Section 4.4)
# ---------------------------------------------------------------------------


def _start_response_polling(
    root: tk.Tk,
    mascot_view: TkinterMascotView,
    response_queue: queue.Queue[str],
    shutdown_event: threading.Event,
) -> None:
    """response_queue を定期ポーリングし、GUI に応答を表示する.

    shutdown_event が set された場合、メインスレッドから root.quit() を
    安全に呼び出す（D-11 Section 5.4 のスレッドセーフ要件に準拠）。

    Args:
        root: tkinter ルートウィンドウ。
        mascot_view: GUI ビュー。
        response_queue: 応答キュー。
        shutdown_event: シャットダウン通知イベント。
    """

    def _poll() -> None:
        if shutdown_event.is_set():
            logger.debug("shutdown_event 検出 — root.quit() 呼び出し")
            root.quit()
            return

        try:
            while True:
                text = response_queue.get_nowait()
                mascot_view.display_text(text)
        except queue.Empty:
            pass
        root.after(_POLL_INTERVAL_MS, _poll)

    root.after(_POLL_INTERVAL_MS, _poll)


# ---------------------------------------------------------------------------
# シャットダウンコールバック (D-16 Section 6)
# ---------------------------------------------------------------------------


def _make_shutdown_callback(
    memory_worker: MemoryWorker,
    db: "Database",
    shutdown_event: threading.Event,
) -> Callable[[], None]:
    """シャットダウンコールバックを生成する.

    SetConsoleCtrlHandler や atexit からシステムスレッド経由で
    呼ばれる可能性があるため、tkinter API を直接呼ばない。
    GUI 終了は shutdown_event 経由でメインスレッドに通知する。

    Args:
        memory_worker: 日次サマリー生成用。
        db: Database インスタンス（クローズ用）。
        shutdown_event: メインスレッドへの GUI 終了通知。

    Returns:
        シャットダウンコールバック関数。
    """

    # _done: コールバック自体の2重実行を防止する。
    # shutdown_handler.py の _shutdown_done はハンドラ（atexit/Ctrl）レベルの
    # 2重ディスパッチを防止する。2つの Event は責務が異なるため意図的に分離。
    # _done はすべての呼び出し経路（SystemTray 直接呼び出し含む）をガードする。
    _done = threading.Event()

    def _shutdown() -> None:
        if _done.is_set():
            return
        _done.set()

        logger.info("シャットダウンシーケンス開始")

        # 1. まず GUI を閉じる（ユーザーを待たせない）
        shutdown_event.set()

        # 2. 当日の日次サマリー生成
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            memory_worker.generate_daily_summary_sync(today)
        except Exception:
            logger.error("日次サマリー生成失敗（シャットダウン続行）", exc_info=True)

        # 3. DB コネクションのクローズ
        try:
            db.close()
        except Exception:
            logger.error("DB クローズ失敗", exc_info=True)

        logger.info("シャットダウン完了")

    return _shutdown


# ---------------------------------------------------------------------------
# ウィザードモード起動 (D-16 Section 3)
# ---------------------------------------------------------------------------


def _run_wizard(
    config: "AppConfig",  # noqa: F821
    data_dir: Path,
    db: "Database",
    persona_system: PersonaSystem,
    *,
    config_path: Path = Path("config.toml"),
) -> None:
    """ウィザードモードで起動する (T-31, D-19).

    persona_core.md が不在の場合に呼ばれる。WizardGUI が
    WizardController のビジネスロジックと tkinter GUI を統合する。
    ウィザード完了後はプロセスを終了し、次回起動で通常モードになる。
    """
    llm_client = LLMClient(config)
    wizard_ctrl = WizardController(llm_client, config)

    root = tk.Tk()
    wizard_gui = WizardGUI(
        root, wizard_ctrl, persona_system, data_dir, config,
        config_path=config_path,
    )
    wizard_gui.show()
    root.mainloop()


# ---------------------------------------------------------------------------
# メインエントリポイント (D-16 Section 2)
# ---------------------------------------------------------------------------


def main() -> None:
    """影式の起動シーケンスを実行する (requirements.md Section 5.5)."""
    # ------------------------------------------------------------------
    # Step 0: .env ファイル読み込み (D-10)
    # ------------------------------------------------------------------
    load_dotenv_file()

    # ------------------------------------------------------------------
    # Step 1: config.toml 読み込み (FR-1.1, FR-1.2, FR-1.3)
    # ------------------------------------------------------------------
    config_path = Path("config.toml")
    config = load_config(config_path)

    # ------------------------------------------------------------------
    # Step 2: ANTHROPIC_API_KEY 存在確認 (FR-1.6)
    # ------------------------------------------------------------------
    ensure_api_key()

    # ------------------------------------------------------------------
    # Step 3: data_dir 初期化 + logging + SQLite DB (FR-1.4, FR-1.5)
    # ------------------------------------------------------------------
    data_dir = Path(config.general.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    setup_logging(config, data_dir / "logs")

    try:
        db = Database(data_dir / "memory.db")
        db_conn = db.connect()
        initialize_db(db_conn)
    except Exception as e:
        logger.critical("DB 初期化失敗: %s", e, exc_info=True)
        print(
            format_error_message(
                "EM-003",
                persona_path=str(data_dir / "memory.db"),
                error_detail=str(e),
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    logger.info("影式を起動しています...")

    # ------------------------------------------------------------------
    # Step 4: persona_core.md 存在チェック (FR-4.7)
    # ------------------------------------------------------------------
    persona_system = PersonaSystem()
    try:
        persona_core = persona_system.load_persona_core(
            data_dir / "persona_core.md",
        )
    except PersonaLoadError as e:
        logger.error("persona_core.md の読み込みに失敗: %s", e)
        print(
            format_error_message("EM-004", detail=str(e)),
            file=sys.stderr,
        )
        sys.exit(1)

    if persona_core is None:
        logger.info("persona_core.md が見つかりません。ウィザードを起動します。")
        _run_wizard(
            config, data_dir, db, persona_system,
            config_path=config_path,
        )
        return

    # ------------------------------------------------------------------
    # Step 5: 凍結状態チェック (FR-4.4)
    # ------------------------------------------------------------------
    if persona_system.detect_manual_edit(data_dir / "persona_core.md"):
        logger.warning("persona_core.md の手動編集を検出しました")

    # ------------------------------------------------------------------
    # Step 6: Hot Memory ロード (FR-3.5)
    # ------------------------------------------------------------------
    style_samples = persona_system.load_style_samples(
        data_dir / "style_samples.md",
    )
    human_block = persona_system.load_human_block(
        data_dir / "human_block.md",
    )
    personality_trends_raw = persona_system.load_personality_trends(
        data_dir / "personality_trends.md",
    )
    personality_trends = (
        ""
        if persona_system.is_trends_empty(personality_trends_raw)
        else personality_trends_raw
    )

    # ------------------------------------------------------------------
    # Step 7: 日次サマリー欠損チェック → 補完生成 (FR-3.10)
    # ------------------------------------------------------------------
    llm_client = LLMClient(config)
    memory_worker = MemoryWorker(db_conn, llm_client)
    try:
        memory_worker.check_and_fill_missing_summaries()
    except Exception:
        logger.error("日次サマリー補完に失敗（続行）", exc_info=True)

    # ------------------------------------------------------------------
    # Step 8: Warm Memory ロード (FR-3.6)
    # ------------------------------------------------------------------
    try:
        day_summaries = get_recent_day_summaries(
            db_conn, config.memory.warm_days,
        )
    except Exception:
        logger.warning("Warm Memory ロード失敗（空リストで続行）", exc_info=True)
        day_summaries = []

    # ------------------------------------------------------------------
    # Step 9: プロンプト構築 (FR-3.11, C-01 解決)
    # ------------------------------------------------------------------
    prompt_builder = PromptBuilder(
        persona_core=persona_core.to_markdown(),
        style_samples=style_samples,
        human_block=human_block,
        personality_trends=personality_trends,
        day_summaries=day_summaries,
    )

    # ------------------------------------------------------------------
    # Step 10: SessionContext 初期化 (FR-3.12)
    # ------------------------------------------------------------------
    # Step 10.5: TrendsProposalManager 初期化 + トリガー評価 (D-14)
    trends_manager = TrendsProposalManager()
    trigger_addition = trends_manager.evaluate_triggers(
        day_summaries, config.memory.warm_days, personality_trends,
    )
    if trigger_addition:
        trends_manager.prompt_addition = trigger_addition

    agent_core = AgentCore(
        config=config,
        db_conn=db_conn,
        llm_client=llm_client,
        persona_system=persona_system,
        prompt_builder=prompt_builder,
        data_dir=data_dir,
        trends_manager=trends_manager,
    )

    # ------------------------------------------------------------------
    # Step 11: シャットダウンCB + GUI + トレイ (FR-2.1, FR-2.7)
    # ------------------------------------------------------------------
    shutdown_event = threading.Event()

    root = tk.Tk()
    input_queue: queue.Queue[str] = queue.Queue()
    response_queue: queue.Queue[str] = queue.Queue()

    mascot_view = TkinterMascotView(root, input_queue, config.gui)

    shutdown_cb = _make_shutdown_callback(memory_worker, db, shutdown_event)
    system_tray = SystemTray(mascot_view, shutdown_cb)
    system_tray.setup_icon()

    # ------------------------------------------------------------------
    # Step 12: バックグラウンドスレッド + ハンドラ登録 + メインループ
    # ------------------------------------------------------------------
    bg_thread = threading.Thread(
        target=_run_background_loop,
        args=(agent_core, input_queue, response_queue, shutdown_event),
        kwargs={"persona_name": persona_core.c1_name},
        daemon=True,
    )
    bg_thread.start()

    _start_response_polling(root, mascot_view, response_queue, shutdown_event)

    register_windows_ctrl_handler(shutdown_cb)
    atexit.register(make_atexit_handler(shutdown_cb))

    system_tray.run_detached()

    mascot_view.show()
    logger.info("影式の起動が完了しました")
    root.mainloop()
    root.destroy()


if __name__ == "__main__":
    main()
