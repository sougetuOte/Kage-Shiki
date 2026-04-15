# Phase 2b 自律性コア 設計書

**機能名**: phase-2b-autonomy
**文書種別**: Design（設計）
**根拠**: `docs/specs/phase2b-autonomy/requirements.md`（Rev.1 承認済み）
**作成日**: 2026-03-31
**状態**: 初版

---

## 0. Problem Statement

Phase 1 / Phase 2a の影式は「ユーザーが話しかけたときだけ応答する」受動的なモデルである。
この設計では常駐アプリとしての「そばにいる」実感が薄く、ユーザーとの関係深化が生まれにくい。

Phase 2b では以下の 3 要素を追加し、マスコットが「内的動機に基づいて自発的に行動できる」状態を実現する。

1. **DesireWorker**: 4 種類の欲求（talk / curiosity / reflect / rest）を純粋計算で更新するエンジン
2. **自律発言**: 欲求閾値超過時に既存 ReAct ループを再利用してテキストを生成し GUI に表示する
3. **AgenticSearch**: curiosity 欲求に基づき Web 調査を行い、`curiosity_targets` テーブルを更新する

**最大の設計制約**: 既存のアーキテクチャは `threading + queue.Queue` モデル（asyncio 未使用）であり、
DesireWorker の「asyncio ループ内で定期実行」という要件書 Section 5.1 の記述との不整合がある。
本設計書ではこの不整合を **DesireWorker は専用デーモンスレッドで実装** することで解決する。
AgenticSearch の並列検索部分のみ、当該スレッド内で asyncio を使用する。

---

## 1. 設計方針と全体構造

### 1.1 基本方針

| 方針 | 根拠 |
|------|------|
| 既存 threading モデルを踏襲し、新スレッドを 1 本追加する | asyncio 全体導入の複雑性・テスト困難性を回避（D-26 参照） |
| DesireWorker は LLM 不要の純粋計算 | NFR-14（CPU 負荷）、C-1 を満たす |
| AgentCore の自律発言は既存 ReAct ループを再利用 | 人格一貫性の自動維持、C-4 を満たす |
| AgenticSearchEngine を Protocol で抽象化 | Phase 3 の LocalLLMEngine 移行を上位ロジック無変更で実現（US-19） |
| curiosity_targets の priority 管理はシンプルな整数降順 | Phase 2b の MVP として過剰設計を避ける |

### 1.2 全体スレッドモデル（Phase 2b 後）

```
メインスレッド: tkinter GUI (TkinterMascotView)
    root.after() でポーリング
    |
    | queue.Queue（input_queue, response_queue）
    |
バックグラウンドスレッド: 対話ループ (_run_background_loop)
    AgentCore.process_turn() — ユーザー入力を処理
    AgentCore.handle_autonomous_turn() — 自律発言を処理
    |
    | コールバック（スレッドセーフ）
    |
DesireWorker スレッド (daemon=True)
    threading.Timer による定期実行（update_desires → 閾値判定 → コールバック）
    AgenticSearch の並列検索部分のみ asyncio.run() で実行
```

**通信パス（追加分）:**

```
DesireWorker → [callback] → バックグラウンドスレッド（AgentCore.handle_autonomous_turn）
                                → [response_queue] → GUI
ユーザー入力 → [input_queue] → バックグラウンドスレッド
                                → desire_worker.reset_all() 呼び出し
```

---

## 2. モジュール構成（D-29）

### 2.1 新規ファイル

| ファイル | 主な責務 |
|---------|---------|
| `src/kage_shiki/agent/desire_worker.py` | DesireState / DesireLevel データクラス、DesireWorker クラス |
| `src/kage_shiki/agent/agentic_search.py` | AgenticSearchEngine Protocol、HaikuEngine、SearchResult |
| `src/kage_shiki/agent/autonomous_prompt.py` | 自律発言用プロンプトテンプレート（D-23） |

### 2.2 変更ファイル

| ファイル | 変更内容 |
|---------|---------|
| `src/kage_shiki/agent/agent_core.py` | `handle_autonomous_turn()` 追加、DesireWorker / AgenticSearchEngine 参照追加 |
| `src/kage_shiki/agent/prompt_builder.py` | `build_system_prompt()` に `autonomous_prompt: str \| None = None` 引数追加。autonomous_turn=True 時に独り言プロンプトを SystemPrompt 末尾に注入する |
| `src/kage_shiki/memory/db.py` | `curiosity_targets` CRUD 操作追加（FR-9.11） |
| `src/kage_shiki/core/config.py` | `DesireConfig` / `AgenticSearchConfig` dataclass 追加、`AppConfig` に組み込み。`_PURPOSE_MODEL_SLOTS`, `_MAX_TOKENS_MAP`, `_PURPOSE_TEMPERATURES` に新 purpose 4件を同時追加（R-3 準拠） |
| `src/kage_shiki/main.py` | DesireWorker の起動・停止、コールバック登録、`autonomous_queue`（`maxsize=1`）、`_run_background_loop` 拡張（`desire_worker`, `autonomous_queue` 引数追加）、シャットダウン連携 |

### 2.3 モジュール依存関係

```
main.py
  └─ desire_worker.py        ← threading ベース（asyncio 不要）
  └─ agent_core.py           ← handle_autonomous_turn() 追加
       └─ agentic_search.py  ← Protocol + HaikuEngine（LLM 呼び出し）
       └─ autonomous_prompt.py ← テンプレート定義
  └─ db.py                   ← curiosity_targets CRUD
  └─ config.py               ← DesireConfig / AgenticSearchConfig
```

---

## 3. DesireWorker 設計（D-21, D-22, D-26）

### 3.1 データクラス

```python
# desire_worker.py

@dataclass
class DesireLevel:
    """単一欲求の状態。

    要件書 Section 4.1 の ActionSchedule データクラスは、
    本 DesireLevel の active フラグで代替する。
    ActionSchedule を独立データクラスとして定義しない設計判断。
    """
    level: float        # 0.0 〜 1.0
    threshold: float    # config から読み込み
    last_updated: float # Unix timestamp（time.time()）
    active: bool = False  # 閾値超過中は True、リセット後 False

@dataclass
class DesireState:
    desires: dict[str, DesireLevel]
    # key: "talk" | "curiosity" | "reflect" | "rest"
```

### 3.2 欲求計算式（D-21）

#### 設計方針

**線形増加** を採用する。対数曲線との比較検討は Section 10 を参照。

欲求レベルの基本更新モデルは「時間比率によるランプ関数」とする。
各欲求のレベルは、所定の「飽和時間」に到達したとき 1.0 になる線形増加で計算する。

#### 各欲求の計算式

**talk 欲求:**

```
level = min(1.0, elapsed_idle_minutes / idle_minutes_for_talk)
```

- `elapsed_idle_minutes`: 最後のユーザー入力からの経過時間（分）
- `idle_minutes_for_talk`: config `[desire].idle_minutes_for_talk`（デフォルト 30 分）
- ユーザー入力時に経過時間をリセット（reset_all() ではなく最終入力時刻を更新）

**curiosity 欲求:**

```
pending_weight = min(1.0, pending_count / 5)   # 5 件で飽和
time_weight    = min(1.0, elapsed_idle_minutes / idle_minutes_for_curiosity)
level          = pending_weight * time_weight
```

- `pending_count`: `curiosity_targets` の status=pending レコード数
- `idle_minutes_for_curiosity`: config `[desire].idle_minutes_for_curiosity`（デフォルト 15 分）
- ユーザーがアクティブな間（idle < 2 分）は time_weight = 0 として curiosity を抑制
- pending が 0 件のときは level = 0（FR-9.6「pending が存在しない場合は何もしない」に準拠）

**reflect 欲求:**

```
level = min(1.0, unprocessed_episodes / reflect_episode_threshold)
```

- `unprocessed_episodes`: 前回の reflect 発現以降に蓄積された observations 件数
- `reflect_episode_threshold`: config `[desire].reflect_episode_threshold`（デフォルト 20 件）
- 実行後は内部カウンタをリセット

**rest 欲求:**

```
uptime_hours = (time.time() - session_start_time) / 3600
level = min(1.0, uptime_hours / rest_hours_threshold)
```

- `rest_hours_threshold`: config `[desire].rest_hours_threshold`（デフォルト 4 時間）
- rest 欲求は閾値を超えても active=True になるだけで、AgentCore への通知頻度は
  他の欲求より低い（一度発現したら 60 分間は再通知しない抑制ロジックを実装）

#### 初期値

DesireWorker 起動時、全欲求を level=0.0 / active=False で初期化する。
欲求レベルは永続化しない（要件書 Section 4.2、再起動時はリセット）。

### 3.3 DesireWorker クラス設計

```python
# desire_worker.py（シグネチャのみ）

class DesireWorker:
    def __init__(
        self,
        config: DesireConfig,
        db_conn: sqlite3.Connection,
        on_threshold_exceeded: Callable[[str], None],
    ) -> None:
        # db_conn は check_same_thread=False で生成されたものを受け取る（R-7）。
        # DesireWorker スレッドから observations 件数を COUNT するため。
        self._lock = threading.Lock()  # update_desires / reset_all の排他制御

    def start(self) -> None:
        """threading.Timer による定期更新ループを開始する.

        Timer は一回限りのため、update_desires() 末尾で次の Timer を
        再帰的にスケジュールする。stop() は次回 Timer をキャンセルするが、
        実行中の update_desires() は完了を待つ。
        """

    def stop(self) -> None:
        """更新ループを停止し、次回タイマーをキャンセルする."""

    def update_desires(self) -> None:
        """全欲求レベルを再計算し、閾値超過があれば on_threshold_exceeded を呼ぶ.

        self._lock を取得して実行する。LLM 呼び出しなし（NFR-14 準拠）。
        reflect 欲求の unprocessed_episodes は DB クエリで取得する:
            SELECT COUNT(*) FROM observations
            WHERE created_at > :last_reflect_time
        last_reflect_time は内部で管理し、reflect 発現後にリセットする。
        """

    def reset_all(self) -> None:
        """全欲求の active を False にリセットし、最終入力時刻を更新する.

        self._lock を取得して実行する。ユーザー入力時に呼び出す（FR-9.5）。
        """

    def get_state(self) -> DesireState:
        """現在の DesireState を返す（テスト・デバッグ用）."""

    def notify_user_input(self) -> None:
        """ユーザー入力を通知し、idle タイマーをリセットする.

        reset_all() と組み合わせて使用。
        注: 本メソッドは要件書 Section 5.1 の Protocol 定義外メソッドであり、
        building-checklist.md S-2 に準拠して明示する。
        """
```

#### 通知の重複抑制

同一欲求が閾値超過した場合、`DesireLevel.active == True` の間は追加通知しない。
`reset_all()` 呼び出し後に active が False に戻り、再び通知可能になる。

これにより「1 回の閾値超過 → 1 回の自律発言」が保証される（FR-9.2 受入条件 (2)）。

### 3.4 DesireWorker と既存 threading モデルの接続（D-26）

**接続方式: コールバック経由（スレッドセーフ）**

DesireWorker スレッドから AgentCore のメソッドを直接呼び出すのではなく、
`on_threshold_exceeded` コールバック経由で `response_queue` に処理要求を投入する。

```python
# main.py での接続イメージ

def _on_desire_exceeded(desire_type: str) -> None:
    """DesireWorker のコールバック。バックグラウンドスレッドに処理を委譲する."""
    # autonomous_queue は maxsize=1。古いイベントを drain して最新のみ保持する。
    # これにより閾値超過の連続通知時に古い自律行動要求が蓄積しない。
    while not autonomous_queue.empty():
        try:
            autonomous_queue.get_nowait()
        except queue.Empty:
            break
    autonomous_queue.put(desire_type)

desire_worker = DesireWorker(
    config=config.desire,
    db_conn=db_conn,
    on_threshold_exceeded=_on_desire_exceeded,
)
```

バックグラウンドスレッドのループを以下のように拡張する:

```python
# _run_background_loop の拡張イメージ

while not shutdown_event.is_set():
    # ユーザー入力を優先チェック
    try:
        user_input = input_queue.get_nowait()
        desire_worker.reset_all()
        desire_worker.notify_user_input()
        response = agent_core.process_turn(user_input)
        response_queue.put(response)
        continue
    except queue.Empty:
        pass

    # 自律行動チェック（ユーザー入力がない場合のみ）
    try:
        desire_type = autonomous_queue.get_nowait()
        response = agent_core.handle_autonomous_turn(desire_type)
        if response:
            response_queue.put(response)
    except queue.Empty:
        pass

    time.sleep(0.1)
```

**コールバックのスレッドセーフ性**: `queue.Queue` は スレッドセーフであり、
DesireWorker スレッドから `autonomous_queue.put()` を呼ぶのは安全。

### 3.5 rest 欲求の発現形式（D-22）

rest 欲求が発現した場合、AgentCore は以下のプロンプトで短いつぶやきを生成する。

```
「今日はちょっと眠いな...」「長い時間働いた気がする」
のような、疲労・休息を示唆する短い独り言（50文字以内推奨）
```

Phase 2b では応答テンポ低下や短文化といった動的な変更は行わない（実装複雑性 vs 効果のトレードオフ）。
テキストのみで休息状態を表現する。

---

## 4. 自律発言設計（D-23, D-27）

### 4.1 AgentCore への追加メソッド

```python
# agent_core.py への追加（シグネチャのみ）

def handle_autonomous_turn(self, desire_type: str) -> str | None:
    """欲求閾値超過時に自律発言テキストを生成する.

    既存の ReAct ループを autonomous_turn=True で実行する（C-4）。
    curiosity 欲求の場合は AgenticSearch パイプラインを起動する。
    reflect 欲求の場合は直近の day_summary を DB から取得し、
    AUTONOMOUS_PROMPTS["reflect"] の {day_summary} に注入する（FR-9.9）。

    Args:
        desire_type: "talk" | "curiosity" | "reflect" | "rest"

    Returns:
        生成した自律発言テキスト。生成スキップ時は None。
    """
```

### 4.2 自律発言プロンプトテンプレート（D-23）

`autonomous_prompt.py` に欲求タイプ別のシステムプロンプト補足文を定義する。

**共通制約（全 desire_type）:**
- 既存の persona_core.md + style_samples.md は通常通り注入する（人格維持、FR-9.3 (3)）
- 独り言・つぶやきとして生成する（ユーザーへの返答ではない）
- 長さ: 50 文字以内を推奨（長文は邪魔になる、US-15）
- 「。」「...」で終わる短い文を推奨

**desire_type 別補足プロンプト:**

```python
# autonomous_prompt.py（定数として定義）

AUTONOMOUS_PROMPTS: dict[str, str] = {
    "talk": """\
あなたは今、しばらくユーザーと話していない状態です。
ふと思いついたこと、最近気になっていること、
または単純に「ねえ、聞いてる？」のような軽い呼びかけを
独り言として一言だけ言ってください。
50文字以内の短い独り言を1文だけ出力してください。""",

    "curiosity": """\
あなたは今、気になっていることについて調べ始めたところです。
「そういえば〜について調べてみようかな」
「〜が気になってた」のような、
好奇心を示す独り言を一言だけ言ってください。
50文字以内の短い独り言を1文だけ出力してください。
調査結果の報告は別途行います。ここでは「調べ始める」つぶやきのみ。""",

    "reflect": """\
あなたは今、最近のことを振り返っています。
以下は直近の日次サマリーです:
{day_summary}

上記の内容を踏まえた内省的な一言を言ってください。
「ちょっと考え事してた」「さっきのこと、気になってる」のような
内省を示す独り言を1文だけ出力してください。
50文字以内を推奨します。""",

    "rest": """\
あなたは今、少し疲れを感じています。
「今日はちょっと眠いな...」「長い時間動いてた気がする」のような
軽い疲労・休息を示す独り言を一言だけ言ってください。
50文字以内の短い独り言を1文だけ出力してください。""",
}
```

### 4.3 ユーザー入力と自律行動の排他制御（D-27）

**採用方式: 結果破棄方式（MVP）**

要件書 10.4（Mediator）の判断を踏まえ、Phase 2b では「結果破棄方式」を採用する。

動作仕様:
1. DesireWorker が `autonomous_queue` に desire_type を投入する
2. バックグラウンドスレッドが `autonomous_queue` を処理し、`handle_autonomous_turn()` を開始する
3. 処理中にユーザー入力が `input_queue` に到着した場合:
   - ユーザー入力ループで `input_queue` を先にチェックする（優先度制御）
   - 現在実行中の `handle_autonomous_turn()` は完了まで待つ（即座キャンセルなし）
   - 完了後の結果は `response_queue` に投入せず **破棄する**（`active` フラグで制御）
   - 即座にユーザー入力処理を行う

**active フラグによる破棄制御:**

```python
# handle_autonomous_turn の概念実装

def handle_autonomous_turn(self, desire_type: str) -> str | None:
    desire_level = self._desire_worker.get_state().desires.get(desire_type)
    if desire_level is None or not desire_level.active:
        # reset_all() が呼ばれていれば active=False になっているので破棄
        return None
    # ... LLM 呼び出し ...
    # 生成後も active を再チェック（LLM 実行中に reset_all() が呼ばれた場合）
    if not self._desire_worker.get_state().desires[desire_type].active:
        return None  # 破棄
    return generated_text
```

---

## 5. AgenticSearch 設計（D-24, D-25）

### 5.1 AgenticSearchEngine Protocol

```python
# agentic_search.py

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str

class AgenticSearchEngine(typing.Protocol):
    def decompose_query(self, topic: str) -> list[str]:
        """トピックをサブクエリに分解する（LLM）.

        Returns:
            2 〜 max_subqueries 個のサブクエリリスト。
        """

    def search(self, query: str) -> list[SearchResult]:
        """単一クエリの検索を実行する.

        Returns:
            検索結果リスト（最大 5 件程度）。
        """

    def summarize(
        self,
        topic: str,
        results: list[SearchResult],
    ) -> str:
        """検索結果を要約する（LLM）."""

    def extract_noise_topics(
        self,
        results: list[SearchResult],
    ) -> list[str]:
        """派生テーマ候補を抽出する（LLM）.

        Returns:
            0 〜 3 個の派生テーマリスト（FR-9.8）。
        """
```

### 5.2 HaikuEngine 実装設計（D-24）

#### decompose_query プロンプト

```python
DECOMPOSE_QUERY_PROMPT = """\
以下のトピックについて、Web 検索で調べるための具体的なサブクエリを
{max_subqueries} 個以内で提案してください。

トピック: {topic}

各サブクエリは以下の形式で出力してください:
- [サブクエリ1]
- [サブクエリ2]
...

サブクエリは互いに異なる観点をカバーするようにしてください。
JSON ではなく、上記の箇条書き形式で出力してください。"""
```

#### 並列検索の実装（asyncio.run() 方式）

> **FR-9.7 受入条件 (2) との対応**: 要件書の「search() が asyncio で並列実行される」は、
> Protocol の `search()` メソッド自体ではなく、HaikuEngine の `search_parallel()` 実装メソッドにより実現する。
> Protocol は単一クエリの `search()` のみを定義し、並列実行は実装の責務とする。

HaikuEngine の `search_parallel()` メソッドは DesireWorker スレッド内から呼び出される。
DesireWorker スレッドには asyncio イベントループが存在しないため、
`asyncio.run()` を使用して新しいイベントループを生成・実行・破棄する。

```python
# HaikuEngine のシグネチャ

class HaikuEngine:
    def __init__(
        self,
        config: AgenticSearchConfig,
        llm_client: LLMProtocol,
    ) -> None: ...

    def decompose_query(self, topic: str) -> list[str]: ...

    def search(self, query: str) -> list[SearchResult]:
        """duckduckgo-search の DDGS().text() を呼び出す（同期）."""

    def search_parallel(self, queries: list[str]) -> list[list[SearchResult]]:
        """複数クエリを asyncio で並列実行する.

        内部で asyncio.run(_search_all_async(queries)) を呼ぶ。
        DesireWorker スレッドから安全に呼び出し可能。
        """

    def summarize(
        self,
        topic: str,
        results: list[SearchResult],
    ) -> str: ...

    def extract_noise_topics(
        self,
        results: list[SearchResult],
    ) -> list[str]: ...
```

#### タイムアウト設計

| フェーズ | タイムアウト | 設定先 |
|---------|-----------|--------|
| decompose_query（LLM） | `config.api.timeout`（デフォルト 30 秒） | 既存 LLMClient のタイムアウト流用 |
| search（duckduckgo） | 10 秒（固定） | DDGS のデフォルト timeout 引数 |
| search_parallel（全体） | 30 秒（固定） | asyncio.wait_for でラップ |
| summarize（LLM） | `config.api.timeout` | 既存 LLMClient のタイムアウト流用 |
| extract_noise_topics（LLM） | `config.api.timeout` | 既存 LLMClient のタイムアウト流用 |

#### エラーハンドリング

- 検索失敗（ネットワーク、レート制限）: `status=failed` に更新し処理を終了（致命的にしない）
- LLM 呼び出し失敗（decompose / summarize）: 同様に `status=failed`
- AgenticSearch の失敗は curiosity レベルをリセット（次サイクルで再試行させない）

### 5.3 duckduckgo-search の利用方式（D-25）

#### 基本呼び出し方式

```python
# 同期 API を使用（search() メソッド内）
from duckduckgo_search import DDGS

with DDGS() as ddgs:
    results = list(ddgs.text(query, max_results=5))
```

#### レート制限対策

- 連続検索間に 1 秒のスリープを挿入する（並列実行のサブクエリ間は asyncio.gather + セマフォで制御）
- `max_concurrent_searches` をセマフォの上限として使用（config `[agentic_search].max_concurrent_searches`、デフォルト 3）
- 検索失敗時は `status=failed` に更新し、次回起動で再試行（Phase 2b は即座リトライなし）

#### フォールバック

Phase 2b では duckduckgo-search のみ。検索失敗時は以下の動作とする:
1. `curiosity_targets` の該当レコードを `status=failed` に更新
2. ログに WARNING を記録
3. 欲求の `active` を False にリセット
4. つぶやきのみ生成して代替（「〜について調べようとしたけど、うまくいかなかった」等）

将来の Brave Search アップグレードは `AgenticSearchEngine` Protocol を差し替えることで対応する。

### 5.4 AgenticSearch パイプライン全体フロー

```
curiosity 欲求閾値超過
    ↓
AgentCore.handle_autonomous_turn("curiosity") 呼び出し
    ↓
「調べ始める」つぶやき生成 → response_queue → GUI 表示
    ↓
db.get_pending_targets(limit=1) — priority 昇順の上位 1 件を取得
    ↓ （pending なし → 終了）
db.update_target_status(id, "searching") — status を searching に更新
    ↓
search_engine.decompose_query(topic) — LLM でサブクエリ生成（2〜3 個）
    ↓
search_engine.search_parallel(queries) — asyncio で並列検索
    ↓
search_engine.summarize(topic, all_results) — LLM で統合要約
    ↓
search_engine.extract_noise_topics(all_results) — LLM で派生テーマ抽出（0〜3 個）
    ↓
db.update_target_status(id, "done", result_summary=summary)
    ↓ （noise_topics があれば）
db.create_curiosity_target(noise_topic, parent_id=id) — 各派生テーマを登録
    ↓
(オプション) 調査完了つぶやき生成 → response_queue → GUI 表示
```

---

## 6. curiosity_targets 運用設計（D-28）

### 6.1 CRUD 操作（FR-9.11）

`db.py` に以下を追加する:

```python
# db.py への追加（シグネチャのみ）

def create_curiosity_target(
    conn: sqlite3.Connection,
    topic: str,
    priority: int = 5,
    parent_id: int | None = None,
) -> int:
    """pending トピックを登録し、生成した id を返す.

    派生テーマ登録時も priority=5（デフォルト）で統一する。
    """

def get_pending_targets(
    conn: sqlite3.Connection,
    limit: int = 1,
) -> list[dict]:
    """priority 昇順（高優先）の pending レコードを取得する."""

def update_target_status(
    conn: sqlite3.Connection,
    target_id: int,
    status: str,
    result_summary: str | None = None,
) -> None:
    """status を更新する。status=done 時に result_summary も書き込む."""

def update_target_priority(
    conn: sqlite3.Connection,
    target_id: int,
    delta: int,
) -> None:
    """priority を delta だけ増減する（最低値 1 を保証）."""
```

有効な status 値は `frozenset{"pending", "searching", "done", "failed"}` で管理し、
範囲外の値は `ValueError` を送出する（building-checklist.md R-2 準拠）。

### 6.2 トピック照合方式（D-28）

**採用方式: 単純キーワード一致**

ユーザー入力のキーワードと `curiosity_targets.topic` の照合に、FTS5 や LLM は使用しない。

理由:
- Phase 2b では priority 更新の精度よりも実装シンプルさを優先する
- FTS5 は `observations` 全文検索用に既存利用しており、curiosity_targets への適用は
  スキーマ変更を伴いテスト範囲が広がる
- LLM 照合はコスト・レイテンシの両面でオーバースペック

実装:

```python
# agent_core.py の process_turn 内に以下のロジックを追加

def _update_curiosity_priority_on_user_input(
    self,
    user_input: str,
    pending_targets: list[dict],
) -> None:
    """ユーザー入力にキーワード一致した pending トピックの priority を 1 下げる.

    大文字・小文字を無視した部分文字列一致。
    """
    user_lower = user_input.lower()
    for target in pending_targets:
        if target["topic"].lower() in user_lower:
            update_target_priority(self._db_conn, target["id"], delta=-1)
```

照合は `str.lower()` による大文字・小文字無視の部分文字列一致とする。
照合コストは O(pending_count × topic_length) であり、pending が数十件程度では無視できる。

---

## 7. config.toml 拡張

### 7.1 新規 dataclass

```python
# config.py への追加

@dataclass
class DesireConfig:
    update_interval_sec: float = 7.5      # 欲求更新間隔（秒）
    talk_threshold: float = 0.7           # talk 欲求の発現閾値
    curiosity_threshold: float = 0.6      # curiosity 欲求の発現閾値
    reflect_threshold: float = 0.8        # reflect 欲求の発現閾値
    rest_threshold: float = 0.9           # rest 欲求の発現閾値
    idle_minutes_for_talk: float = 30.0   # talk 閾値到達までの無入力時間（分）
    idle_minutes_for_curiosity: float = 15.0  # curiosity が上昇し始める無入力時間（分）
    reflect_episode_threshold: int = 20   # reflect 発現までの observations 蓄積件数
    rest_hours_threshold: float = 4.0     # rest 発現までの稼働時間（時間）
    rest_suppress_minutes: float = 60.0   # rest 再通知抑制時間（分）

@dataclass
class AgenticSearchConfig:
    engine: str = "haiku"             # "haiku" | "local"（Phase 3）
    search_api: str = "duckduckgo"    # "duckduckgo" | "brave"（将来）
    max_subqueries: int = 3           # サブクエリ最大数
    max_concurrent_searches: int = 3  # 並列検索数上限
```

### 7.2 AppConfig への組み込み

```python
@dataclass
class AppConfig:
    # ... 既存フィールド ...
    desire: DesireConfig = field(default_factory=DesireConfig)
    agentic_search: AgenticSearchConfig = field(default_factory=AgenticSearchConfig)
```

### 7.3 Purpose 管理への追加

`VALID_PURPOSES` に以下を追加する:

| purpose | 用途 | モデルスロット | max_tokens | temperature |
|---------|------|--------------|-----------|-------------|
| `autonomous_talk` | 自律発言（talk/curiosity/reflect/rest 全4欲求） | `conversation` | 256 | 0.9 |
| `agentic_decompose` | クエリ分解 | `utility` | 256 | 0.3 |
| `agentic_summarize` | 検索結果要約 | `utility` | 512 | 0.3 |
| `agentic_noise` | 派生テーマ抽出 | `utility` | 256 | 0.5 |

---

## 8. データフロー全体図

```
[ユーザー入力]
    │
    ▼
input_queue
    │
    ▼
_run_background_loop (バックグラウンドスレッド)
    │  1. desire_worker.reset_all() — 全欲求リセット
    │  2. desire_worker.notify_user_input() — idle タイマーリセット
    │  3. _update_curiosity_priority_on_user_input() — トピック照合
    │  4. agent_core.process_turn() — 通常対話処理
    │
    ▼
response_queue → GUI 表示

─────────────────────────────────────────────────────────

[DesireWorker スレッド (daemon=True)]
    │
    │  threading.Timer（update_interval_sec 間隔）
    │
    ▼
update_desires()
    │  各欲求レベルを再計算
    │
    ├── level >= threshold かつ active=False → on_threshold_exceeded(desire_type) 呼び出し
    │       │
    │       ▼
    │  autonomous_queue.put(desire_type)
    │
    └── それ以外 → 何もしない（CPU 消費 < 1ms）

─────────────────────────────────────────────────────────

autonomous_queue
    │
    ▼
_run_background_loop — 自律行動処理
    │  1. active フラグ確認（ユーザー入力で reset されていれば破棄）
    │  2. agent_core.handle_autonomous_turn(desire_type)
    │
    │  desire_type = "talk" / "reflect" / "rest":
    │      → 自律発言プロンプトで LLM 呼び出し → response_queue → GUI
    │
    │  desire_type = "curiosity":
    │      → 「調べ始める」つぶやき → response_queue → GUI
    │      → AgenticSearch パイプライン実行
    │           → db 更新
    │           → (オプション) 完了つぶやき → response_queue → GUI
    │
    ▼
response_queue → GUI 表示
```

---

## 9. テスト方針

### 9.1 DesireWorker のテスト

**タイマー依存を排除する設計**: `update_desires()` を直接呼び出してテストする。

```python
# テストパターン例

def test_talk_desire_increases_with_idle_time():
    """アイドル時間に応じて talk 欲求が増加することを検証."""
    worker = DesireWorker(config=..., db_conn=..., on_threshold_exceeded=callback)
    worker.notify_user_input()  # 最終入力時刻を設定
    # 時刻をモックして経過時間を操作
    with freeze_time(now + timedelta(minutes=15)):
        worker.update_desires()
    state = worker.get_state()
    assert 0.4 < state.desires["talk"].level < 0.6  # 30分で1.0なので15分で0.5付近

def test_threshold_exceeded_callback():
    """閾値超過時にコールバックが呼ばれることを検証."""
    received = []
    worker = DesireWorker(config=..., on_threshold_exceeded=received.append)
    # talk レベルを閾値超過状態に設定してから update_desires を呼ぶ
    ...
    assert "talk" in received

def test_reset_all_suppresses_callback():
    """reset_all() 後は同一欲求のコールバックが再通知されないことを検証."""
    ...
```

`freeze_time` には `pytest-freezegun` または `freezegun` を使用する。

### 9.2 AgenticSearch のテスト

**外部 API は全てモックで代替する。**

- `DDGS().text()` をモック → 固定の `SearchResult` リストを返す
- `LLMClient.create()` をモック → 固定のプロンプト応答を返す

```python
def test_haiku_engine_decompose_query(mock_llm):
    """decompose_query が 2〜3 個のサブクエリを返すことを検証."""
    engine = HaikuEngine(config=..., llm_client=mock_llm)
    queries = engine.decompose_query("ゴールデンドーンの起源")
    assert 2 <= len(queries) <= 3

def test_search_parallel_executes_concurrently(mock_ddgs):
    """search_parallel が複数クエリを並列実行することを検証."""
    engine = HaikuEngine(...)
    results = engine.search_parallel(["query1", "query2"])
    assert len(results) == 2
    assert mock_ddgs.call_count == 2
```

### 9.3 curiosity_targets CRUD のテスト

`:memory:` DB で全 CRUD 操作を網羅する。
`get_pending_targets()` の priority 昇順ソートと `status` フィルタリングを重点検証する。

### 9.4 AgentCore 統合テスト

```python
def test_handle_autonomous_turn_talk():
    """handle_autonomous_turn("talk") が response_queue に投入されることを検証."""

def test_handle_autonomous_turn_aborts_on_reset():
    """handle_autonomous_turn 実行中に reset_all() が呼ばれると結果が破棄されることを検証."""

def test_user_input_resets_desire():
    """ユーザー入力処理時に desire_worker.reset_all() が呼ばれることを検証."""

def test_handle_autonomous_turn_reflect():
    """handle_autonomous_turn("reflect") が day_summary を参照した内省テキストを生成することを検証（FR-9.9）."""

def test_reflect_prompt_contains_day_summary():
    """reflect 時のシステムプロンプトに直近の day_summary が含まれることを検証."""
```

### 9.5 カバレッジ目標

| モジュール | 目標 |
|-----------|------|
| `desire_worker.py` | 95% 以上 |
| `agentic_search.py` | 90% 以上 |
| `agent_core.py`（追加部分） | 90% 以上 |
| `db.py`（追加部分） | 95% 以上 |
| Phase 2b 全体 | 90% 以上（NFR-15） |

---

## 10. Alternatives Considered（却下した選択肢）

### D-21: 欲求計算式

| 選択肢 | 評価 | 採否 |
|--------|------|------|
| **線形増加**（採用） | シンプルで理解しやすい。閾値到達時間を直感的にパラメータで制御できる | 採用 |
| 対数曲線 | 現実の欲求に近い（急速な初期上昇 + 鈍化）。パラメータが増える | 却下（MVP 段階では過剰） |
| 指数関数 | 閾値手前で急激に上昇。過剰発火リスクがある | 却下 |

### D-26: DesireWorker と AgentCore の接続方式

| 選択肢 | 評価 | 採否 |
|--------|------|------|
| **threading.Timer + コールバック**（採用） | 既存の threading モデルと完全に整合。テストが書きやすい | 採用 |
| asyncio イベントループをバックグラウンドスレッドで常時実行 | AgenticSearch の並列検索には有利。既存ループとの接続が複雑（スレッド間の asyncio 共有は避けるべき）| 却下 |
| asyncio 全体導入（main.py を asyncio ベースに移行） | 根本的な解決だが、Phase 1 の全テスト・実装に影響が及ぶ大規模変更。Phase 3 以降での検討が適切 | 却下（PM 級判断） |
| DesireWorker を MemoryWorker 内のサブタスクとして実装 | モジュール分離が不明確になる。MemoryWorker のスコープ拡大 | 却下 |

### D-28: トピック照合方式

| 選択肢 | 評価 | 採否 |
|--------|------|------|
| **単純キーワード一致**（採用） | 実装が最小。Phase 2b では十分な精度 | 採用 |
| FTS5 | 既存 FTS5 インデックスの活用が可能だが、curiosity_targets への FTS5 仮想テーブル追加が必要（C-3 のスキーマ無変更前提に反する可能性） | 却下 |
| LLM 分類 | 精度は最高だが、毎入力ごとの LLM 呼び出しは C-1 と矛盾しないものの、コスト・レイテンシのオーバーヘッドがある | 却下（Phase 3 以降で検討） |

### D-24 並列検索実装方式

| 選択肢 | 評価 | 採否 |
|--------|------|------|
| **asyncio.run() でスレッド内に独立ループ生成**（採用） | DesireWorker スレッド内で完結。既存ループを汚染しない | 採用 |
| threading.Thread で各検索を並列化 | asyncio 不使用で一貫性あり。GIL の影響でネットワーク IO 待ちに弱い（実害は小さいが） | 次善策として許容（初期実装はこちらでも可） |
| LLM ツールコール | 05-agentic-search.md で Qwen3.5-9B バグのため明示的に避けるべきと記載 | 却下 |

---

## 11. Success Criteria

本設計が正しく実装されたとき、以下の条件を全て満たす:

### 機能的成功条件

| 条件 | 対応 FR | 検証方法 |
|------|---------|---------|
| DesireWorker が指定間隔で update_desires() を呼び出す | FR-9.1 | `threading.Timer` の呼び出し回数をモックで検証 |
| 各欲求レベルが 0.0〜1.0 の範囲を維持する | FR-9.1 | DesireWorker ユニットテスト |
| LLM 呼び出しが update_desires() 内で発生しない | FR-9.1 (3) | 欲求更新中の LLMClient モックの呼び出し回数 = 0 |
| 閾値超過時にコールバックが desire_type と共に呼ばれる | FR-9.2 | コールバックモックで検証 |
| 同一欲求の連続通知が active=True の間は抑制される | FR-9.2 (2) | reset_all() なしで 2 回超過しても通知は 1 回のみ |
| handle_autonomous_turn("talk") 実行時に ReAct ループが起動する | FR-9.3 (1) | LLMClient モックの呼び出しを検証 |
| 自律発言テキストが response_queue 経由で GUI に届く | FR-9.3 (2) | 統合テストで response_queue の内容を検証 |
| autonomous_turn=True 時のプロンプトに persona_core + style_samples が含まれる | FR-9.3 (3) | PromptBuilder のプロンプト内容をアサート |
| autonomous_turn=True 時のシステムプロンプトに独り言指示が含まれる | FR-9.4 | PromptBuilder のプロンプト内容をアサート |
| ユーザー入力時に reset_all() が呼ばれる | FR-9.5 | input_queue に投入後の DesireWorker 状態を検証 |
| curiosity 閾値超過時に AgenticSearch が起動する | FR-9.6 | AgenticSearchEngine モックの呼び出しを検証 |
| pending なし時は AgenticSearch が起動しない | FR-9.6 (2) | DB に pending なし状態での動作確認 |
| AgenticSearch が分解→検索→要約→更新の順序で実行される | FR-9.7 | モックの呼び出し順序を検証 |
| 派生テーマが parent_id 付きで登録される | FR-9.8 | DB レコードの parent_id を検証 |
| curiosity_targets CRUD が仕様通りに動作する | FR-9.11 | DB ユニットテスト |
| reflect 欲求発現時に day_summary を参照した内省テキストが生成される | FR-9.9 | reflect プロンプトに day_summary が含まれることを検証 |
| AgenticSearchEngine が typing.Protocol として定義され、HaikuEngine が静的型チェックで満足する | FR-9.10 | mypy / pyright で静的検証 |
| 照合一致時に priority が 1 下がる | FR-9.12 | process_turn 呼び出し後の DB レコードを検証 |

### 非機能的成功条件

| 条件 | 対応 NFR | 検証方法 |
|------|---------|---------|
| 追加依存は `duckduckgo-search` のみ | NFR-13 | `pyproject.toml` の dependencies 確認 |
| update_desires() 1 回の実行時間 < 1ms（LLM なし時） | NFR-14 | ユニットテストで timeit 計測 |
| Phase 2b 追加モジュールのカバレッジ 90% 以上 | NFR-15 | `pytest --cov` |
| 全体カバレッジが Phase 2a 完了時点（92%）を下回らない | NFR-15 | `pytest --cov` |

---

## 付録: AoT 設計分解と並列実装計画

要件書 Section 10.1 の AoT Atom に基づく実装順序:

| Atom | 設計書での対応 | 並列可否 |
|------|--------------|---------|
| A1: DesireWorker 基盤 | Section 3, Section 7 | A3/A4 と並列可 |
| A2: 自律発言統合 | Section 4 | A1 完了後 |
| A3: AgenticSearchEngine Protocol + HaikuEngine | Section 5 | A1/A4 と並列可 |
| A4: curiosity_targets CRUD | Section 6 | A1/A3 と並列可 |
| A5: AgenticSearch と curiosity 統合 | Section 5.4, Section 8 | A1/A3/A4 完了後 |
| A6: reflect 欲求 + トピック照合 | Section 3.2（reflect）, Section 6.2 | A1/A2/A4 完了後 |

**インターフェース契約（先行確定が必要な項目）:**
- `DesireConfig` / `AgenticSearchConfig` dataclass（A1, A3 の起点）
- `AgenticSearchEngine` Protocol（A3 の契約）
- `curiosity_targets` CRUD シグネチャ（A4 の契約）
- `handle_autonomous_turn()` シグネチャ（A2 の契約）

これら 4 項目のシグネチャを確定した後、A1 / A3 / A4 は並列実装可能。
