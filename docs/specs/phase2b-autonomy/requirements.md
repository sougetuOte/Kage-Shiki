# Phase 2b 自律性コア 要件定義書

**機能名**: phase-2b-autonomy
**文書種別**: Requirements（要件定義）
**根拠**:
- `docs/memos/middle-draft/04-unified-design.md`（Phase 2 ロードマップ）
- `docs/memos/middle-draft/02-personality-system.md`（欲求システム設計・自律行動制御）
- `docs/memos/middle-draft/05-agentic-search.md`（AgenticSearch パイプライン詳細）
- `docs/memos/middle-draft/01-memory-system.md`（記憶システム Phase 2 拡張）
- `docs/memos/middle-draft/03-architecture.md`（アーキテクチャ全体図）

**作成日**: 2026-03-11
**状態**: 承認済み Rev.1

---

## 1. 概要

影式 Phase 2b（自律性コア）は、Phase 2a で強化された基盤の上に **DesireWorker（欲求システム）、自律発言（つぶやき）、AgenticSearch パイプライン** を構築し、マスコットが「ユーザーの入力を待たずに自ら行動する」能力を獲得するフェーズである。

Phase 1 MVP と Phase 2a は「ユーザーが話しかけたときだけ反応する」受動的な対話モデルだった。Phase 2b ではマスコットに **内的動機（欲求）** を持たせ、欲求が閾値を超えたときに自律的にアクション（つぶやき、Web 調査）を起こす **因果連鎖** を実装する。

Phase 2a との差分:

| 領域 | Phase 2a | Phase 2b 追加・変更 |
|------|----------|-------------------|
| 行動モデル | 受動的（ユーザー入力に応答） | 自律的（欲求に基づく自発的行動） |
| DesireWorker | 未実装 | 4欲求（talk/curiosity/reflect/rest）の計算エンジン |
| 自律発言 | 未実装 | 欲求閾値超過時のつぶやきテキスト生成 |
| AgenticSearch | 未実装 | curiosity 欲求駆動の Web 調査パイプライン |
| curiosity_targets | スキーマ予約のみ | CRUD 操作 + priority 更新ロジック |
| 可変層 | 未運用 | L1（興味の広がり）を curiosity_targets と連動 |
| config.toml | Phase 2a 項目まで | DesireWorker・AgenticSearch 関連パラメータ追加 |

---

## 2. スコープ

### 2.1 Phase 2b に含むもの

| # | 機能領域 | 概要 |
|---|---------|------|
| 1 | DesireWorker | 4欲求（talk/curiosity/reflect/rest）のレベル計算エンジン（LLM 不要） |
| 2 | 自律発言（つぶやき） | DesireWorker の閾値超過通知を受けて AgentCore が自律発言テキストを生成 |
| 3 | AgenticSearch パイプライン | HaikuEngine Protocol + duckduckgo-search による Web 調査 |
| 4 | curiosity_targets CRUD | pending/searching/done/failed の状態管理 + priority 更新 |
| 5 | 可変層 L1 運用 | curiosity_targets の蓄積に連動した「興味の広がり」管理 |
| 6 | config.toml 拡張 | DesireWorker 閾値・AgenticSearch 設定の追加 |
| 7 | 自律行動制御 | ユーザー入力時の即座リセット、行動間の競合解決 |

### 2.2 Phase 2b に含まないもの（Phase 2c 以降）

- セマンティック検索（sqlite-vec + e5-small）
- 忘却曲線による検索重み付け
- ボディ表現（透過 PNG 差し替え、`set_body_state()` の実装）
- 可変層 L2〜L6 の本格運用
- 記憶閲覧 GUI、承認制 UI
- Theory of Mind（トーン分析）
- AgenticSearch エンジンの LocalLLM 移行（Qwen3.5-9B）
- curiosity_targets の「興味の系譜」グラフ化（parent_id の本格運用は Phase 3）
- personality_trends.md の自動提案ロジック

---

## 3. ユーザーストーリー

| ID | ストーリー | 優先度 |
|----|-----------|--------|
| US-14 | ユーザーとして、マスコットが自ら話しかけてくることを期待したい。**なぜなら**、「相手から話しかけてくれる」ことが「そばにいる」実感の核心であり、入力待ちの受動的な存在では愛着が生まれにくいから | Must |
| US-15 | ユーザーとして、マスコットの自律発言がうるさくないことを期待したい。**なぜなら**、1対1のデスクトップマスコットでは「作業の邪魔にならない」ことが常駐の前提だから | Must |
| US-16 | ユーザーとして、マスコットが会話中の話題に興味を持ち、自分で調べてくることを期待したい。**なぜなら**、「自ら学ぶ」行動がキャラクターの知性と好奇心を感じさせ、関係の深化につながるから | Should |
| US-17 | ユーザーとして、話しかけたときに自律行動が即座に中断されることを期待したい。**なぜなら**、ユーザーの入力は常に最高優先であり、自律行動が応答を遅延させることは許容できないから | Must |
| US-18 | ユーザーとして、マスコットが時折「ちょっと考え事してた」と内省する姿を見たい。**なぜなら**、内面の思考を感じさせることがキャラクターの「深み」につながるから | Could |
| US-19 | 開発者として、AgenticSearch のエンジンを差し替え可能にしたい。**なぜなら**、Phase 3 でローカル LLM（Qwen3.5-9B）に移行する計画があり、上位ロジックの変更を避けたいから | Should |

### 3.1 ユーザーストーリー → 機能要件 トレーサビリティ

| US | 対応 FR |
|----|---------|
| US-14 | FR-9.1, FR-9.2, FR-9.3 |
| US-15 | FR-9.4, FR-9.5 |
| US-16 | FR-9.6, FR-9.7, FR-9.8 |
| US-17 | FR-9.5 |
| US-18 | FR-9.1, FR-9.9 |
| US-19 | FR-9.10 |

---

## 4. データモデル

### 4.1 Phase 2b で追加・変更するエンティティ

Phase 2a のデータモデルを引き継ぐ。追加・変更要素のみ記載する。

| エンティティ | 変更種別 | 内容 |
|------------|---------|------|
| `DesireState` | 新規 | 4欲求の現在レベル・閾値・最終更新時刻を保持するデータクラス |
| `ActionSchedule` | 新規 | 欲求に対応する行動予定（active/inactive）を保持 |
| `curiosity_targets` | 運用開始 | Phase 1 で予約済みのスキーマを本格運用。CRUD 操作を追加 |
| `AgenticSearchEngine` Protocol | 新規 | HaikuEngine / 将来の LocalLLMEngine の抽象インターフェース |
| `config.toml` | 拡張 | `[desire]`, `[agentic_search]` セクション追加 |

### 4.2 DesireState データモデル（要件レベル）

DesireState:
    desires: dict[str, DesireLevel]    # "talk", "curiosity", "reflect", "rest"

DesireLevel:
    level: float       # 0.0 - 1.0
    threshold: float   # config.toml で設定
    last_updated: float # Unix timestamp
    active: bool       # 閾値超過で True、実行後 or ユーザー入力時に False

欲求レベルは **永続化しない**（再起動時は初期値にリセット）。curiosity の未調査トピック残量は `curiosity_targets` テーブルに永続化されるため、再起動後も curiosity 欲求は適切に再計算される。

### 4.3 config.toml 拡張（要件レベル）

    [desire]
    update_interval_sec = 7.5       # 欲求更新間隔（5-10秒の中間値）
    talk_threshold = 0.7            # talk 欲求の発現閾値
    curiosity_threshold = 0.6       # curiosity 欲求の発現閾値
    reflect_threshold = 0.8         # reflect 欲求の発現閾値
    rest_threshold = 0.9            # rest 欲求の発現閾値
    idle_minutes_for_talk = 30      # talk 欲求が閾値に達するまでの無入力時間（分）
    idle_minutes_for_curiosity = 15 # curiosity が上昇し始めるまでの無入力時間（分）
    reflect_episode_threshold = 20  # reflect 発現までの observations 蓄積件数
    rest_hours_threshold = 4.0      # rest 発現までの稼働時間（時間）
    rest_suppress_minutes = 60.0    # rest 再通知抑制時間（分）

    [agentic_search]
    engine = "haiku"                # "haiku" | "local"（Phase 3）
    search_api = "duckduckgo"       # "duckduckgo" | "brave"（将来）
    max_subqueries = 3              # サブクエリ最大数
    max_concurrent_searches = 3     # 並列検索数上限

具体的な閾値・間隔の数値は設計フェーズで確定する（D-21）。

### 4.4 curiosity_targets CRUD 操作（要件レベル）

| 操作 | 説明 |
|------|------|
| Create | 新規トピック登録（status=pending, priority=5） |
| Read | pending トピックを priority 昇順で取得 |
| Update (status) | pending -> searching -> done/failed |
| Update (priority) | ユーザー言及時に priority を 1 下げる（最低 1） |
| Delete | Phase 2b では削除しない（Phase 3 で棚卸しロジックを検討） |

---

## 5. インターフェース定義

### 5.1 DesireWorker（新規）

DesireWorker は専用デーモンスレッド上で `threading.Timer` により定期実行されるワーカーで、欲求レベルの更新と閾値超過通知を担当する。

    DesireWorker
    +-- start()               # 定期更新ループを開始
    +-- stop()                # ループを停止
    +-- update_desires()      # 全欲求レベルを再計算（LLM 不要、純粋な計算）
    +-- reset_all()           # 全欲求を active=False にリセット（ユーザー入力時）
    +-- on_threshold_exceeded # コールバック: 閾値超過時に AgentCore に通知
    +-- get_state()           # 現在の DesireState を返す（テスト・デバッグ用）

DesireWorker -> AgentCore の通知は、AgentCore が登録するコールバック関数経由で行う。AgentCore は通知を受けて ReAct ループを `autonomous_turn=True` で起動する。

### 5.2 AgenticSearchEngine Protocol（新規）

    AgenticSearchEngine (typing.Protocol)
    +-- decompose_query(topic: str) -> list[str]     # トピックをサブクエリに分解（LLM）
    +-- search(query: str) -> list[SearchResult]      # 単一クエリの検索実行
    +-- summarize(topic: str, results: list[SearchResult]) -> str  # 検索結果の要約（LLM）
    +-- extract_noise_topics(results) -> list[str]    # 派生テーマ候補の抽出（LLM）

    HaikuEngine
    +-- AgenticSearchEngine を実装（anthropic SDK + duckduckgo-search）

    SearchResult:
        title: str
        url: str
        snippet: str

### 5.3 AgentCore 拡張（変更）

Phase 1/2a の AgentCore に以下を追加する:

    AgentCore（追加メソッド/属性）
    +-- handle_autonomous_turn(desire_type: str)  # 自律発言の ReAct ループ実行
    +-- _desire_worker: DesireWorker              # 欲求ワーカーへの参照
    +-- _search_engine: AgenticSearchEngine       # 検索エンジンへの参照

自律発言は既存の ReAct ループを再利用する。`autonomous_turn=True` フラグにより、プロンプトに「つぶやき文脈」を注入し、GUI への出力は `MascotView.schedule()` 経由で行う。

### 5.4 スレッド間通信（Phase 2b 追加パス）

Phase 1 の通信モデルに以下の経路を追加する:

    DesireWorker（専用デーモンスレッド、threading.Timer）
        -> コールバック -> autonomous_queue -> バックグラウンドスレッド
            -> AgentCore.handle_autonomous_turn()
            -> response_queue -> GUI 表示

    DesireWorker.reset_all()
        <- GUI スレッド -> queue.Queue -> AgentCore（ユーザー入力処理時に呼び出し）

---

## 6. 機能要件

### FR-9: Phase 2b 自律性コア

番号体系は FR-9.x（Phase 1: FR-1〜FR-7、Phase 2a: FR-8.x）。

#### FR-9.1〜9.2: DesireWorker

| ID | 要件 | 優先度 | 受入条件 |
|----|------|--------|---------|
| FR-9.1 | DesireWorker が 4 欲求（talk/curiosity/reflect/rest）のレベルを config.toml の `update_interval_sec` 間隔で更新する | Must | (1) DesireWorker.start() 後、指定間隔で update_desires() が呼び出されることをテストで検証できる、(2) 各欲求レベルは 0.0〜1.0 の範囲内に収まる、(3) LLM 呼び出しが発生しない（純粋な計算処理） |
| FR-9.2 | 欲求レベルが閾値を超過した場合、on_threshold_exceeded コールバックで AgentCore に通知する | Must | (1) talk 欲求が threshold を超えたとき、コールバックが desire_type="talk" で呼び出されることをテストで検証できる、(2) 同一欲求の連続通知は active=True の間は抑制される（1 回のみ通知） |

#### FR-9.3〜9.4: 自律発言（つぶやき）

| ID | 要件 | 優先度 | 受入条件 |
|----|------|--------|---------|
| FR-9.3 | AgentCore が DesireWorker からの通知を受けて自律発言テキストを生成する | Must | (1) handle_autonomous_turn("talk") が呼び出されたとき、ReAct ループが autonomous_turn=True で実行されることをテストで検証できる、(2) 生成されたテキストが MascotView.schedule() 経由で GUI に表示される、(3) persona_core.md と style_samples.md がコンテキストに含まれる（人格維持） |
| FR-9.4 | 自律発言は通常対話と異なるプロンプト文脈（「つぶやき」モード）で生成される | Should | (1) autonomous_turn=True 時のシステムプロンプトに「独り言として」等の文脈指示が含まれる、(2) 生成テキストの長さが通常応答より短い傾向にあることを促す指示が含まれる |

#### FR-9.5: 自律行動制御

| ID | 要件 | 優先度 | 受入条件 |
|----|------|--------|---------|
| FR-9.5 | ユーザー入力を検知した時点で DesireWorker.reset_all() を呼び出し、全欲求の active フラグを False にリセットする | Must | (1) ユーザーがテキスト入力を送信した時点で、実行中の自律行動が中断される（進行中の LLM 呼び出しは完了を待つが、結果は破棄可能）、(2) reset_all() 後、欲求タイマーが再スタートすることをテストで検証できる、(3) ユーザー入力の処理が自律行動より常に優先される |

#### FR-9.6〜9.8: AgenticSearch パイプライン

| ID | 要件 | 優先度 | 受入条件 |
|----|------|--------|---------|
| FR-9.6 | curiosity 欲求が閾値を超過したとき、AgenticSearch パイプラインが起動し、curiosity_targets から pending トピックを取得して調査を実行する | Should | (1) curiosity 閾値超過時に AgenticSearch が起動することをテストで検証できる、(2) pending トピックが存在しない場合は何もしない、(3) 調査対象は priority が最も高い（数値が最も低い）pending トピック |
| FR-9.7 | AgenticSearch パイプラインが (1) クエリ分解 -> (2) 並列検索 -> (3) 結果要約 -> (4) curiosity_targets 更新 の順序で実行される | Should | (1) decompose_query() がサブクエリ（2〜max_subqueries 個）を返すことをテストで検証できる、(2) search() が asyncio で並列実行されること、(3) 要約結果が curiosity_targets.result_summary に書き込まれること、(4) status が done に更新されること |
| FR-9.8 | AgenticSearch が派生テーマ（noise_topics）を検出し、新規の curiosity_targets として登録する | Could | (1) extract_noise_topics() が 0〜3 個の派生テーマを返すこと、(2) 各派生テーマが parent_id を設定した状態で curiosity_targets に INSERT されること（Phase 2b では parent_id は記録のみ、グラフ化は Phase 3） |

#### FR-9.9: reflect 欲求の発現

| ID | 要件 | 優先度 | 受入条件 |
|----|------|--------|---------|
| FR-9.9 | reflect 欲求が閾値を超過したとき、AgentCore が内省テキストを生成する | Could | (1) handle_autonomous_turn("reflect") が呼び出されたとき、直近の day_summary を参照した内省テキストが生成されることをテストで検証できる、(2) 内省結果は通常のつぶやきとして GUI に表示される |

#### FR-9.10: AgenticSearchEngine Protocol

| ID | 要件 | 優先度 | 受入条件 |
|----|------|--------|---------|
| FR-9.10 | AgenticSearchEngine を typing.Protocol として定義し、HaikuEngine がこれを実装する | Should | (1) AgenticSearchEngine が typing.Protocol として定義されている、(2) HaikuEngine が AgenticSearchEngine を静的型チェックで満足する、(3) decompose_query(), search(), summarize(), extract_noise_topics() の 4 メソッドが定義されている |

#### FR-9.11〜9.12: curiosity_targets 運用

| ID | 要件 | 優先度 | 受入条件 |
|----|------|--------|---------|
| FR-9.11 | curiosity_targets テーブルの CRUD 操作を `db.py` に追加する | Must | (1) create_curiosity_target(topic) で pending レコードが作成される、(2) get_pending_targets(limit) で priority 昇順の pending レコードが取得できる、(3) update_target_status(id, status) で status が更新される、(4) update_target_priority(id, delta) で priority が増減する（1 以上を維持） |
| FR-9.12 | ユーザーが会話中に curiosity_targets の既存トピックに関連する話題に言及した場合、該当トピックの priority を 1 下げる | Could | (1) AgentCore の対話処理中に、ユーザー入力のキーワードと pending の curiosity_targets.topic を照合するロジックが存在する、(2) 一致した場合に priority が 1 下がることをテストで検証できる |

---

## 7. 非機能要件

Phase 2a の NFR-1〜NFR-12 を引き継ぐ。Phase 2b で追加・変更する項目のみ記載する。

| ID | カテゴリ | 要件 | 基準 |
|----|---------|------|------|
| NFR-13 | 依存追加 | Phase 2b での追加依存は `duckduckgo-search` のみ | pip install で追加。pyproject.toml に記載 |
| NFR-14 | CPU 負荷 | DesireWorker の定期更新が CPU を過度に消費しない | 更新間隔 5-10 秒、1回の更新は < 1ms（純粋な算術計算）。常駐時の CPU 使用率が Phase 2a 比で有意に増加しないこと |
| NFR-15 | テスト | Phase 2b のカバレッジ | Phase 2b 追加モジュールのカバレッジ 90% 以上。全体カバレッジが Phase 2a 完了時点（92%）を下回らない |

---

## 8. 制約・前提条件

### 8.1 前提条件

| # | 前提 |
|---|------|
| P-1 | Phase 2a が完了していること（822テスト、92%カバレッジ） |
| P-2 | `ANTHROPIC_API_KEY` が環境変数に設定されていること（AgenticSearch の HaikuEngine が使用） |
| P-3 | インターネット接続があること（duckduckgo-search API が外部通信を行う） |

### 8.2 技術制約

| # | 制約 |
|---|------|
| C-1 | DesireWorker の欲求更新は LLM 呼び出しを行わない（純粋な計算処理） |
| C-2 | 検索の並列実行は LLM のツールコールに依存せず、コード側（asyncio）で実装する |
| C-3 | curiosity_targets のスキーマは Phase 1 で予約済みのものを使用する（ALTER TABLE なし） |
| C-4 | 自律発言は既存の ReAct ループを再利用する（新たな応答生成パイプラインを追加しない） |
| C-5 | GUI ライブラリは引き続き tkinter を使用する |

### 8.3 スコープ境界

| # | 境界 |
|---|------|
| S-1 | AgenticSearchEngine の第2実装（LocalLLMEngine / Qwen3.5-9B）は Phase 3 スコープ |
| S-2 | curiosity_targets の parent_id を活用したグラフ構造は Phase 3 スコープ（Phase 2b では記録のみ） |
| S-3 | 忘却曲線による検索重み付けは Phase 2c スコープ |
| S-4 | セマンティック検索（sqlite-vec + e5-small）は Phase 2c スコープ |
| S-5 | 可変層 L2〜L6 の本格運用は Phase 2c スコープ |
| S-6 | rest 欲求の発現形式（応答テンポ低下等）の具体的実装は設計フェーズで決定する（D-22） |

---

## 9. 設計フェーズで決定する項目

| # | 項目 | 候補・方針 | 備考 |
|---|------|-----------|------|
| D-21 | DesireWorker の欲求計算式 | 線形増加 vs 対数曲線。各欲求の増加関数・減衰関数・初期値を設計する | FR-9.1 の実装詳細 |
| D-22 | rest 欲求の発現形式 | 応答テンポの低下 / 短文化 / 「眠い」つぶやき。テキストベースでどう「休息状態」を表現するか | FR-9.1 の UI 詳細 |
| D-23 | 自律発言のプロンプトテンプレート | autonomous_turn=True 時のシステムプロンプト。つぶやきの長さ・トーンの制御方法 | FR-9.3, FR-9.4 の実装詳細 |
| D-24 | AgenticSearch の HaikuEngine 実装設計 | decompose_query のプロンプト、並列度制御、タイムアウト設計 | FR-9.7, FR-9.10 の実装詳細 |
| D-25 | duckduckgo-search の利用方式 | DDGS().text() の呼び出し方式、レート制限対策、フォールバック | FR-9.7 の実装詳細 |
| D-26 | DesireWorker と AgentCore の接続設計 | コールバック方式の具体的実装、asyncio イベントループ内の配置 | FR-9.2 の実装詳細 |
| D-27 | ユーザー入力と自律行動の排他制御 | 進行中の LLM 呼び出しのキャンセル方式（結果破棄 vs 即座中断） | FR-9.5 の実装詳細 |
| D-28 | curiosity_targets のトピック照合方式 | 単純なキーワード一致 vs FTS5 利用 vs LLM 分類 | FR-9.12 の実装詳細 |
| D-29 | 新規モジュール構成 | `src/kage_shiki/agent/desire_worker.py`, `src/kage_shiki/agent/agentic_search.py` 等の配置 | 全 FR の実装基盤 |

---

## 10. Three Agents Perspective Check

### 10.1 AoT Decomposition

| Atom | 内容 | 依存 | 並列可否 |
|------|------|------|---------|
| A1 | DesireWorker 基盤（FR-9.1, FR-9.2） | なし | 可（A3 と並列） |
| A2 | 自律発言統合（FR-9.3, FR-9.4, FR-9.5） | A1（通知元） | A1 完了後 |
| A3 | AgenticSearchEngine Protocol + HaikuEngine（FR-9.10, FR-9.7） | なし | 可（A1 と並列） |
| A4 | curiosity_targets CRUD（FR-9.11） | なし | 可（A1, A3 と並列） |
| A5 | AgenticSearch と curiosity 統合（FR-9.6, FR-9.8） | A1, A3, A4 | A1, A3, A4 完了後 |
| A6 | reflect 欲求 + 残タスク（FR-9.9, FR-9.12） | A1, A2, A4 | A1, A2, A4 完了後 |

### 10.2 [Affirmative]（推進者）

- Phase 2b はプロジェクトの **核心的差別化要因** を実装するフェーズ。「自ら行動するマスコット」は競合（静的チャットボット）との根本的な差異
- DesireWorker の「LLM 不要」設計は、コスト・レイテンシの両面で優れている。欲求更新が純粋な計算処理であるため、常時起動のデスクトップアプリとしての要件を満たす
- 既存 ReAct ループの再利用（C-4）により、自律発言でも人格維持（persona_core + style_samples 注入）が自動的に保証される
- AgenticSearchEngine Protocol の導入により、Phase 3 の LocalLLM 移行が上位ロジック無変更で実現可能
- curiosity_targets スキーマが Phase 1 で予約済み（C-3）のため、マイグレーション不要で運用を開始できる

### 10.3 [Critical]（批判者）

1. **自律発言の頻度制御**: 設計メモ（02-personality-system.md）で「1対1では'うるさい'が致命的」と指摘されている。talk_threshold の初期値設定を誤ると UX が大幅に悪化するリスクがある。D-21 での慎重な設計が不可欠
2. **duckduckgo-search の信頼性**: 非公式 API であり、レート制限や仕様変更のリスクがある。フォールバック設計（D-25）が不十分だと AgenticSearch が恒常的に失敗する可能性
3. **asyncio と tkinter の共存**: 現在のアーキテクチャは threading + queue.Queue で GUI とバックグラウンドを接続している。asyncio ループの追加はスレッドモデルの複雑化を招く。既存の threading モデルとの整合性を D-26 で慎重に設計する必要がある
4. **ユーザー入力時の排他制御**: FR-9.5 の「進行中の LLM 呼び出しは完了を待つが、結果は破棄可能」は、API コストの無駄が発生する。即座中断の実現可能性を D-27 で検討すべき
5. **テスト可能性**: 非同期の定期実行（DesireWorker）と外部 API（duckduckgo-search）を組み合わせたテストはフレイキーになりやすい。モック戦略を設計段階で確立する必要がある

### 10.4 [Mediator]（調停者）

1. **自律発言の頻度制御（対応）**: D-21 で欲求計算式を設計する際、talk_threshold を「控えめ」に設定する方針を明記。初回リリースでは 30 分無入力で初めて発言する程度の保守的な閾値から開始し、ユーザーフィードバックで調整する
2. **duckduckgo-search の信頼性（対応）**: D-25 で (1) タイムアウト設計、(2) 失敗時の status=failed 遷移、(3) 将来の Brave Search アップグレードパスを設計する。Phase 2b では「検索が失敗しても致命的ではない」設計とする（つぶやきのみで代替可能）
3. **asyncio と tkinter の共存（対応）**: D-26 で既存の threading + queue.Queue モデルとの整合性を確保する。※設計フェーズで threading.Timer + デーモンスレッド方式を採用（設計書 Section 0, D-26）。当初案の「asyncio ループ統合・スレッド追加なし」は却下済み
4. **排他制御とコスト（対応）**: D-27 で「結果破棄」方式を Phase 2b の MVP とする。API コストは自律発言の頻度が低い（30分に1回程度）ため影響は限定的。即座中断は Phase 3 以降でストリーミングキャンセルとして検討
5. **テスト可能性（対応）**: AgenticSearchEngine Protocol のモック実装を用意し、HaikuEngine のユニットテストは外部 API モックで実施する。DesireWorker のテストは update_desires() を直接呼び出す方式で、タイマー依存を排除する

---

## 11. Definition of Ready チェックリスト

- [x] **Doc Exists**: `docs/specs/phase2b-autonomy/requirements.md` が存在する
- [x] **Unambiguous**: A（Core Value）〜 D（Constraints）の要素が明記され、解釈の揺れがない
- [ ] **Atomic**: タスクが 1 PR サイズに分割されている -> tasks サブフェーズで実施
- [x] **Testable**: 全 FR の受入条件が観察可能・測定可能な形式で記述されている
- [x] **Phase Boundary**: Phase 2c/3 のスコープ（セマンティック検索、忘却曲線、L2-L6、グラフ化）が含まれていないことを確認済み
- [x] **Perspective Check**: Three Agents による多角的レビューが完了している（Section 10）
- [x] **Traceability**: US -> FR の対応表が存在する（Section 3.1）
- [x] **NFR Continuity**: Phase 2a の NFR-1〜12 を引き継ぎ、追加項目（NFR-13〜15）を明記している
- [x] **Numbering Continuity**: FR-9.x（Phase 1: FR-1〜7, Phase 2a: FR-8.x）、US-14〜19（Phase 2a: US-8〜13）、D-21〜29（Phase 2a: D-17〜20）の連番が正しい
