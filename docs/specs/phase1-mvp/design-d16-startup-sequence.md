# D-16: 起動シーケンス統合 + スレッド間通信

**タスク**: T-25
**対応 FR**: 全 FR（requirements.md Section 5.5 起動シーケンス）
**依存設計**: D-1〜D-15 の全設計
**ステータス**: Approved

---

## 1. 概要

全コンポーネントを統合し、requirements.md Section 5.5 の起動シーケンスを
`src/kage_shiki/main.py` に実装する。メインスレッド（tkinter mainloop）と
バックグラウンドスレッド（AgentCore ループ）間のスレッド間通信を構築する。

加えて、Wave 1〜7 で積み残した以下の課題を T-25 スコープ内で解決する。

| ID | 課題 | 解決方針 |
|----|------|----------|
| C-01 | AgentCore が PersonaSystem のプライベート属性に getattr で依存 | main.py で load 結果を保持し PromptBuilder に直接渡す |
| W-T25 | process_turn への trends/human_block 統合 | process_turn に後処理メソッド呼び出しを追加 |
| — | Warm Memory ロード関数の不在 | memory/db.py に `get_recent_day_summaries()` を追加 |

---

## 2. 起動シーケンス

requirements.md Section 5.5 の 12 ステップに `.env` 読み込み（D-10 規定）を
Step 0 として先頭に追加した 13 ステップ構成。

> Note: requirements.md は Step 1 から始まるが、本設計では D-10 で規定された
> `.env` 読み込みを Step 0 として明示的に追加する。

```
Step 0:  .env ファイル読み込み — load_dotenv_file() [D-10]
Step 1:  config.toml 読み込み — load_config()
Step 2:  ANTHROPIC_API_KEY 存在確認 — ensure_api_key()
Step 3:  data_dir 初期化 + logging + SQLite DB 作成
Step 4:  persona_core.md 存在チェック → 不在ならウィザード起動
Step 5:  凍結状態チェック: 手動編集検出
Step 6:  Hot Memory ロード
Step 7:  日次サマリー欠損チェック → 補完生成
Step 8:  Warm Memory ロード
Step 9:  プロンプト構築（PromptBuilder 生成）
Step 10: SessionContext 初期化（AgentCore 生成）
Step 11: シャットダウンコールバック生成 + GUI ウィンドウ表示 + トレイアイコン登録
Step 12: バックグラウンドスレッド起動 + シャットダウンハンドラ登録 + メインループ
```

### 2.1 ステップ詳細

#### Step 0: .env ファイル読み込み
```python
from kage_shiki.core.env import load_dotenv_file
load_dotenv_file()
```

#### Step 1: config.toml 読み込み
```python
from kage_shiki.core.config import load_config
config = load_config(Path("config.toml"))
```

#### Step 2: ANTHROPIC_API_KEY 存在確認
```python
from kage_shiki.core.env import ensure_api_key
api_key = ensure_api_key()
```
未設定の場合は `sys.exit(1)` で終了（D-10 Section 5.4）。

#### Step 3: data_dir 初期化 + logging + SQLite DB 作成
```python
from kage_shiki.core.logging_setup import setup_logging
from kage_shiki.memory.db import Database, initialize_db

data_dir = Path(config.general.data_dir)
data_dir.mkdir(parents=True, exist_ok=True)

setup_logging(config, data_dir / "logs")

db = Database(data_dir / "memory.db")
db_conn = db.connect()
initialize_db(db_conn)
```

logging は data_dir 作成後・DB 初期化前に行う。
これ以降のステップでは logger が使用可能。

#### Step 4: persona_core.md 存在チェック
```python
persona_system = PersonaSystem()
persona_core = persona_system.load_persona_core(data_dir / "persona_core.md")

if persona_core is None:
    # ウィザード起動 → Section 3 参照
    run_wizard(config, api_key, data_dir, db, persona_system)
    return
```

#### Step 5: 凍結状態チェック
```python
if persona_system.detect_manual_edit(data_dir / "persona_core.md"):
    logger.warning("persona_core.md の手動編集を検出しました")
```
Phase 1 では WARNING ログのみ。凍結状態の再確認ダイアログは Phase 2 スコープ。

#### Step 6: Hot Memory ロード
```python
style_samples = persona_system.load_style_samples(data_dir / "style_samples.md")
human_block = persona_system.load_human_block(data_dir / "human_block.md")
personality_trends_raw = persona_system.load_personality_trends(
    data_dir / "personality_trends.md",
)

# テンプレートのプレースホルダのみの場合は空文字列として扱う
personality_trends = (
    "" if persona_system.is_trends_empty(personality_trends_raw)
    else personality_trends_raw
)
```
各 load メソッドの戻り値（str）を変数に保持。これを PromptBuilder に渡す。
`is_trends_empty()` でテンプレートのみのケースを除外し、無駄なトークン消費を防ぐ。

#### Step 7: 日次サマリー欠損チェック → 補完生成
```python
llm_client = LLMClient(config)
memory_worker = MemoryWorker(db_conn, llm_client)
memory_worker.check_and_fill_missing_summaries()
```

#### Step 8: Warm Memory ロード
```python
from kage_shiki.memory.db import get_recent_day_summaries
day_summaries = get_recent_day_summaries(db_conn, config.memory.warm_days)
```
新規関数。Section 5 で詳述。

#### Step 9: プロンプト構築

> **Note**: `PromptBuilder` は Phase 2a で `agent/prompt_builder.py` に分離された。
> `agent_core.py` からも re-export されているため、既存の import パスは引き続き有効。

```python
prompt_builder = PromptBuilder(
    persona_core=persona_core.to_markdown(),
    style_samples=style_samples,
    human_block=human_block,
    personality_trends=personality_trends,
    day_summaries=day_summaries,
)
```
PersonaCore dataclass の `to_markdown()` メソッドで C1-C11 の Markdown テキストを再構成。
C-01 解決: PersonaSystem のプライベート属性への getattr を廃止し、
load 結果を main.py 経由で PromptBuilder に直接渡す。

#### Step 10: SessionContext 初期化
```python
agent_core = AgentCore(
    config=config,
    db_conn=db_conn,
    llm_client=llm_client,
    persona_system=persona_system,
    prompt_builder=prompt_builder,
    data_dir=data_dir,
)
```
AgentCore.__init__ の変更: `prompt_builder` を外部注入パラメータに変更。

#### Step 11: シャットダウンコールバック + GUI + トレイ

シャットダウンコールバックを先に生成し、SystemTray に渡す。

```python
# シャットダウン通知用イベント（スレッドセーフな GUI 終了に使用）
shutdown_event = threading.Event()

root = tk.Tk()
input_queue: queue.Queue[str] = queue.Queue()
response_queue: queue.Queue[str] = queue.Queue()

mascot_view = TkinterMascotView(root, input_queue, config.gui)

# シャットダウンコールバック生成（SystemTray に渡す前に定義）
shutdown_cb = _make_shutdown_callback(
    memory_worker, db_conn, shutdown_event,
)
system_tray = SystemTray(mascot_view, shutdown_cb)
system_tray.setup_icon()
```

#### Step 12: バックグラウンドスレッド起動 + シャットダウンハンドラ登録 + メインループ
```python
bg_thread = threading.Thread(
    target=_run_background_loop,
    args=(agent_core, input_queue, response_queue, shutdown_event),
    daemon=True,
)
bg_thread.start()

# メインスレッドの応答ポーリング + シャットダウン監視開始
_start_response_polling(root, mascot_view, response_queue, shutdown_event)

# シャットダウンハンドラ登録（D-11 2層防御）
register_windows_ctrl_handler(shutdown_cb)
atexit.register(make_atexit_handler(shutdown_cb))

# pystray を run_detached で起動（内部でバックグラウンドスレッドを生成）
system_tray.run_detached()

# tkinter メインループ（メインスレッド）
root.mainloop()
```

---

## 3. ウィザードモード起動

persona_core.md が不在の場合（Step 4）。

WizardController は T-20〜T-23 で実装済みの個別メソッドを持つが、
GUI のフレーム遷移を管理する高レベルの `start()` メソッドは存在しない。
T-25 では main.py の `run_wizard()` がオーケストレーションを担当する。

```python
def run_wizard(
    config: AppConfig,
    api_key: str,
    data_dir: Path,
    db: Database,
    persona_system: PersonaSystem,
) -> None:
    """ウィザードモードで起動する.

    WizardController の個別メソッド（expand_associations,
    generate_candidates, freeze_persona 等）を TkinterMascotView の
    ウィザードフレームと連携させる。

    ウィザード完了後は「アプリを再起動してください」と案内し、
    プロセスを終了する。
    """
    llm_client = LLMClient(config)
    wizard = WizardController(llm_client, config)

    root = tk.Tk()
    input_queue: queue.Queue[str] = queue.Queue()
    mascot_view = TkinterMascotView(root, input_queue, config.gui)

    # Phase 1 MVP: ウィザード GUI 統合は最小限とする。
    # WizardController と TkinterMascotView のフレーム遷移連携は
    # Phase 2 で本格実装を検討する。

    root.mainloop()

    # ウィザード完了後、プロセス終了
    # 次回起動時に通常モードで起動される
```

---

## 4. スレッド間通信

### 4.1 アーキテクチャ

```
┌── メインスレッド（tkinter mainloop）────────────────┐
│                                                       │
│  TkinterMascotView                                    │
│    ├─ ユーザー入力 → input_queue.put(text)            │
│    └─ display_text(text) ← poll で response_queue 取得│
│                                                       │
│  _poll_response_queue()                               │
│    root.after(100ms) で定期ポーリング                 │
│    + shutdown_event 監視 → root.quit() 呼び出し       │
│                                                       │
│  SystemTray（pystray run_detached で内部スレッド起動）│
│    └─ action_quit() → shutdown_callback               │
└───────────────────────────────────────────────────────┘
        ↕ queue.Queue × 2 + threading.Event
┌── バックグラウンドスレッド（daemon=True）─────────────┐
│                                                       │
│  _run_background_loop()                               │
│    1. セッション開始メッセージ生成 → response_queue   │
│    2. shutdown_event を監視しつつ input_queue を       │
│       0.1 秒間隔でポーリング                          │
│    3. process_turn(user_input) → response_queue       │
│    4. ループ                                          │
│                                                       │
└───────────────────────────────────────────────────────┘
```

### 4.2 キュー設計

| キュー/イベント | 方向 | 型 | 用途 |
|----------------|------|----|------|
| `input_queue` | メイン → バックグラウンド | `queue.Queue[str]` | ユーザー入力テキスト |
| `response_queue` | バックグラウンド → メイン | `queue.Queue[str]` | マスコット応答テキスト |
| `shutdown_event` | シャットダウンCB → 全スレッド | `threading.Event` | graceful shutdown 通知 |

### 4.3 バックグラウンドループ

```python
def _run_background_loop(
    agent_core: AgentCore,
    input_queue: queue.Queue[str],
    response_queue: queue.Queue[str],
    shutdown_event: threading.Event,
) -> None:
    """バックグラウンドスレッドのメインループ."""
    # セッション開始メッセージ生成
    try:
        greeting = agent_core.generate_session_start_message()
        response_queue.put(greeting)
    except Exception:
        logger.error("セッション開始メッセージの生成に失敗", exc_info=True)
        response_queue.put(format_error_message("EM-006"))

    # 対話ループ（shutdown_event で停止可能）
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
            response_queue.put(format_error_message("EM-006"))
```

`input_queue.get(timeout=0.1)` でブロッキングポーリング。
asyncio は使用しない（全 I/O が同期 API のため不要）。

### 4.4 応答ポーリング + シャットダウン監視

```python
_POLL_INTERVAL_MS = 100

def _start_response_polling(
    root: tk.Tk,
    mascot_view: TkinterMascotView,
    response_queue: queue.Queue[str],
    shutdown_event: threading.Event,
) -> None:
    """response_queue を定期ポーリングし、GUI に応答を表示する.

    shutdown_event が set された場合、メインスレッドから root.quit() を
    安全に呼び出す（D-11 Section 5.4 のスレッドセーフ要件に準拠）。
    """

    def _poll() -> None:
        # シャットダウン通知の確認
        if shutdown_event.is_set():
            root.quit()
            return

        # 応答キューの処理
        try:
            while True:
                text = response_queue.get_nowait()
                mascot_view.display_text(text)
        except queue.Empty:
            pass
        root.after(_POLL_INTERVAL_MS, _poll)

    root.after(_POLL_INTERVAL_MS, _poll)
```

100ms 間隔でポーリング。キュー内の全メッセージを一括処理。
`shutdown_event` の監視もメインスレッドのポーリングで行うことで、
`root.quit()` が常にメインスレッドから呼ばれることを保証する。

---

## 5. 既存モジュール変更

### 5.1 memory/db.py — get_recent_day_summaries 追加

```python
def get_recent_day_summaries(
    conn: sqlite3.Connection,
    days: int,
) -> list[dict[str, str]]:
    """直近 N 日分の day_summary を取得する (FR-3.6).

    Args:
        conn: DB コネクション。
        days: 取得する日数。

    Returns:
        [{"date": "YYYY-MM-DD", "summary": "..."}] 形式のリスト。
        古い日付が先。
    """
    rows = conn.execute(
        "SELECT date, summary FROM day_summary "
        "ORDER BY date DESC LIMIT ?",
        (days,),
    ).fetchall()
    return [{"date": r[0], "summary": r[1]} for r in reversed(rows)]
```

### 5.2 AgentCore.__init__ 変更（C-01 解決）

**Before**:
```python
def __init__(
    self,
    config: AppConfig,
    db_conn: sqlite3.Connection,
    llm_client: LLMClient,
    persona_system: PersonaSystem,
) -> None:
    # ...
    self._prompt_builder = PromptBuilder(
        persona_core=getattr(persona_system, "_persona_core_text", ""),
        style_samples=getattr(persona_system, "_style_samples_text", ""),
        human_block=getattr(persona_system, "_human_block_text", ""),
        # ...
    )
```

**After**:
```python
def __init__(
    self,
    config: AppConfig,
    db_conn: sqlite3.Connection,
    llm_client: LLMClient,
    persona_system: PersonaSystem,
    prompt_builder: PromptBuilder,
    *,
    data_dir: Path | None = None,
) -> None:
    self._config = config
    self._db_conn = db_conn
    self._llm_client = llm_client
    self._persona_system = persona_system

    self.session_context = SessionContext()
    self.session_start_message = ""
    self.consistency_hit_count = 0

    self._prompt_builder = prompt_builder

    # W-T25: ファイルパス（human_block / trends 更新用）
    self._data_dir = data_dir
    self._human_block_path = data_dir / "human_block.md" if data_dir else None
    self._trends_path = (
        data_dir / "personality_trends.md" if data_dir else None
    )

    # W-T25: TrendsProposalManager（セッション開始時にトリガー評価）
    self._trends_manager: TrendsProposalManager | None = None
```

`prompt_builder` を外部注入パラメータに変更。
getattr によるプライベート属性アクセスを完全に排除する。
`data_dir` はオプショナル（テスト時は None で渡せる）。

### 5.3 PersonaCore.to_markdown() 追加

PersonaCore dataclass に `to_markdown()` メソッドを追加し、
C1-C11 フィールドから Markdown テキストを再構成する。
PromptBuilder に渡す persona_core テキストとして使用。

`_SECTION_LABELS` 辞書を参照して正式な日本語ラベルを使用する。

```python
@dataclass
class PersonaCore:
    # ... 既存フィールド ...

    def to_markdown(self) -> str:
        """C1-C11 フィールドを Markdown テキストとして再構成する.

        _SECTION_LABELS を参照し、requirements.md Section 4.3.1 準拠の
        日本語ラベルを使用する。
        """
        lines: list[str] = []
        for num, attr_name in _FIELD_MAP.items():
            value = getattr(self, attr_name, "")
            if value:
                label = _SECTION_LABELS[num]
                lines.append(f"## C{num}: {label}\n\n{value}")
        return "\n\n".join(lines)
```

### 5.4 process_turn への後処理追加（W-T25 解決）

process_turn のステップ 8（ターン記録）の後に、
human_block 更新マーカーパースと trends 承認判定を追加する。

```python
def process_turn(self, user_input: str) -> str:
    # ... 既存のステップ 1〜8 ...

    # 9. human_block 更新マーカーのパースと適用 (T-17)
    self._apply_human_block_updates(response)

    # 10. personality_trends 承認フロー (T-16)
    self._handle_trends_approval(response, user_input)

    return response
```

#### 5.4.1 _apply_human_block_updates

```python
def _apply_human_block_updates(self, response: str) -> None:
    """LLM 応答から human_block 更新マーカーを抽出し適用する (T-17).

    parse_human_block_updates() でマーカーをパースし、
    validate_update() で各更新を検証後、PersonaSystem に委譲する。
    """
    if self._human_block_path is None:
        return
    updates = parse_human_block_updates(response)
    for update in updates:
        valid, reason = validate_update(update)
        if not valid:
            logger.info("human_block 更新をスキップ: %s", reason)
            continue
        try:
            self._persona_system.update_human_block(
                self._human_block_path,
                update.section,
                update.content,
            )
            logger.info(
                "human_block 更新: section=%s", update.section,
            )
        except Exception:
            logger.error("human_block 更新失敗", exc_info=True)
```

#### 5.4.2 _handle_trends_approval

TrendsProposalManager の実際の API に準拠:
- `parse_proposal_from_response(response, message_count)` で LLM 応答からパース
- `judge_approval(user_input, message_count)` で承認判定（戻り値: 文字列）
- `get_approved_proposal()` で承認済み提案を取得
- `format_entry_for_trends(proposal)` で追記用テキストを生成

```python
def _handle_trends_approval(self, response: str, user_input: str) -> None:
    """personality_trends 承認フローを処理する (T-16).

    1. LLM 応答から提案マーカーをパース
    2. ユーザー入力で承認/却下/保留を判定
    3. 承認時は personality_trends.md に追記
    """
    if self._trends_manager is None or self._trends_path is None:
        return

    # 1. LLM 応答から提案をパース（提案マーカーがあればpending_proposalに格納）
    self._trends_manager.parse_proposal_from_response(
        response, self.session_context.message_count,
    )

    # 2. ユーザー入力で承認判定
    result = self._trends_manager.judge_approval(
        user_input, self.session_context.message_count,
    )

    if result == "approved":
        proposal = self._trends_manager.get_approved_proposal()
        if proposal is not None:
            entry = self._trends_manager.format_entry_for_trends(proposal)
            try:
                self._persona_system.append_personality_trends(
                    self._trends_path,
                    proposal.section,
                    entry,
                )
                logger.info(
                    "personality_trends 追記: section=%s",
                    proposal.section,
                )
            except Exception:
                logger.error("personality_trends 追記失敗", exc_info=True)
```

---

## 6. シャットダウンシーケンス

シャットダウンコールバックは `threading.Event` を使用して
メインスレッドに GUI 終了を通知する。
`root.quit()` をコールバック内で直接呼ばない（D-11 Section 5.4 準拠）。

```python
def _make_shutdown_callback(
    memory_worker: MemoryWorker,
    db: Database,
    shutdown_event: threading.Event,
) -> Callable[[], None]:
    """シャットダウンコールバックを生成する.

    SetConsoleCtrlHandler や atexit からシステムスレッド経由で
    呼ばれる可能性があるため、tkinter API を直接呼ばない。
    GUI 終了は shutdown_event 経由でメインスレッドに通知する。
    """

    def _shutdown() -> None:
        logger.info("シャットダウンシーケンス開始")

        # 1. 当日の日次サマリー生成
        today = datetime.now().strftime("%Y-%m-%d")
        memory_worker.generate_daily_summary_sync(today)

        # 2. DB コネクションのクローズ
        try:
            db_conn.close()
        except Exception:
            logger.error("DB クローズ失敗", exc_info=True)

        # 3. メインスレッドに GUI 終了を通知
        shutdown_event.set()

        logger.info("シャットダウン完了")

    return _shutdown
```

D-11 の2層防御（ctypes + atexit）により、
正常終了・強制終了のどちらでもこのコールバックが1回だけ実行される。
`_shutdown_done` フラグは `shutdown_handler.py` 内で管理済み。
`shutdown_event.set()` はスレッドセーフであり、メインスレッドの
`_poll_response_queue()` が次のポーリングで `root.quit()` を呼ぶ。

---

## 7. エラーハンドリング

| ステップ | エラー | 対応 |
|----------|--------|------|
| Step 1 | config.toml パースエラー | デフォルト値でフォールバック（T-02 実装済み） |
| Step 2 | API キー未設定 | EM-001 表示 + sys.exit(1)（T-04 実装済み） |
| Step 3 | DB 初期化失敗 | EM-003 表示 + sys.exit(1) |
| Step 4 | persona_core.md 読取不能 | PersonaLoadError → EM-004 表示 + sys.exit(1) |
| Step 6 | Hot Memory ロード失敗 | 空文字列フォールバック（各 load メソッド実装済み） |
| Step 7 | サマリー生成失敗 | EM-009 ログ + 続行（T-18 実装済み） |
| Step 8 | day_summary 取得失敗 | 空リストフォールバック + WARNING ログ |
| Step 9 | PromptBuilder 生成エラー | EM-003 表示 + sys.exit(1) |
| Step 10 | AgentCore 初期化エラー | EM-003 表示 + sys.exit(1) |
| Step 11 | tkinter ウィンドウ表示失敗 | EM-003 表示 + sys.exit(1) |
| Step 12 | セッション開始メッセージ生成失敗 | EM-006 フォールバック表示 |
| ループ | process_turn 失敗 | EM-006 フォールバック表示 + ループ継続 |

---

## 8. テスト方針

### 8.1 新規テスト

| テスト | ファイル | 内容 |
|--------|---------|------|
| 起動シーケンス順序 | `test_integration/test_startup.py` | 各ステップが正しい順序で実行されること |
| config.toml 不在時デフォルト生成 | 同上 | デフォルト config.toml が作成されること |
| persona_core.md 不在時ウィザード起動 | 同上 | ウィザードモードに分岐すること |
| スレッド間通信 | 同上 | input_queue → process_turn → response_queue の一連の流れ |
| 応答ポーリング | 同上 | response_queue のメッセージが display_text に渡ること |
| シャットダウン通知 | 同上 | shutdown_event.set() で root.quit() が呼ばれること |
| get_recent_day_summaries | `test_memory/test_db.py` | 直近 N 日分が日付昇順で返ること |
| PersonaCore.to_markdown | `test_persona/test_persona_system.py` | C1-C11 が `_SECTION_LABELS` の日本語ラベル付きで再構成されること |
| _apply_human_block_updates | `test_agent/test_agent_core.py` | 更新マーカーがパースされ PersonaSystem に委譲されること |
| _handle_trends_approval | `test_agent/test_agent_core.py` | judge_approval → append_personality_trends の流れが動作すること |

### 8.2 既存テスト修正

AgentCore.__init__ のシグネチャ変更（`prompt_builder` + `data_dir` 追加）に伴い、
既存テストの AgentCore インスタンス生成を更新する。
全テストで PromptBuilder を明示的に生成して渡すようにする。

---

## 9. 成果物一覧

| ファイル | 変更種別 | 内容 |
|---------|---------|------|
| `src/kage_shiki/main.py` | 新規 | エントリポイント + 起動シーケンス |
| `src/kage_shiki/memory/db.py` | 追加 | `get_recent_day_summaries()` |
| `src/kage_shiki/agent/agent_core.py` | 変更 | C-01 解決 + W-T25 後処理追加 |
| `src/kage_shiki/persona/persona_system.py` | 追加 | `PersonaCore.to_markdown()` |
| `tests/test_integration/test_startup.py` | 新規 | 起動シーケンステスト |
| `tests/test_memory/test_db.py` | 追加 | get_recent_day_summaries テスト |
| `tests/test_persona/test_persona_system.py` | 追加 | to_markdown テスト |
| `tests/test_agent/test_agent_core.py` | 変更 | AgentCore シグネチャ更新 + 後処理テスト |
