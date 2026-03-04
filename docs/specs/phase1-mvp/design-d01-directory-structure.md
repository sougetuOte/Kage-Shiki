# D-1: src/ ディレクトリ構成

**決定対象**: requirements.md Section 8 D-1「src/ ディレクトリ構成 — レイヤード or フラット — モジュール分割方針」
**関連 FR**: 全 FR（基盤）
**ステータス**: 提案（承認待ち）

---

## 1. コンテキスト

影式は Python 3.12+ で実装する Windows 常駐デスクトップマスコットである。
Phase 1 MVP では以下の主要コンポーネントが存在する。

| コンポーネント | 役割 |
|-------------|------|
| AgentCore | ReAct ループ、LLM 呼び出し、記憶検索 |
| MemoryWorker | observations 保存、日次サマリー生成 |
| TkinterMascotView | MascotView Protocol の tkinter 実装 |
| SystemTray | pystray によるトレイアイコン管理 |
| Config | config.toml の読み書き、バリデーション |
| PersonaSystem | persona_core.md / style_samples.md の読み込み・凍結管理 |
| Wizard | 人格生成ウィザード（3方式 + プレビュー） |

Phase 2-4 では以下が追加される。

| コンポーネント | 役割 |
|-------------|------|
| DesireWorker | 欲求システム（talk / curiosity / reflect / rest） |
| AgenticSearch | Web 検索パイプライン（HaikuEngine → LocalLLMEngine） |
| Theory of Mind | トーン分析（ルールベース → LLM 昇格） |

src/ 内パッケージ構成を決定することで、以降の全 D-item の実装場所・import 経路・依存方向が確定する。

---

## 2. 選択肢分析

### 選択肢 A: フラット構成

全モジュールを `kage_shiki/` 直下に配置する。

```
src/
└── kage_shiki/
    ├── __init__.py
    ├── main.py           # エントリポイント
    ├── config.py         # Config
    ├── agent_core.py     # AgentCore
    ├── memory_worker.py  # MemoryWorker
    ├── mascot_view.py    # MascotView Protocol 定義
    ├── tkinter_view.py   # TkinterMascotView
    ├── system_tray.py    # SystemTray
    ├── persona.py        # PersonaSystem
    ├── wizard.py         # Wizard
    └── db.py             # SQLite 操作
```

- **概要**: Python スクリプト的な、最もシンプルな配置
- **メリット**: import が単純（`from kage_shiki import agent_core`）。小規模プロジェクトの Python 慣例に沿う。ファイル間の関係がリスト形式で一目瞭然
- **デメリット**: Phase 2-4 でコンポーネントが増えると（DesireWorker, AgenticSearch 等）ファイルが乱立する。DB 操作・LLM 呼び出し等の横断関心事がどこに属するか曖昧になる。依存方向の制約がコードで表現できない

### 選択肢 B: レイヤードアーキテクチャ（domain / infra / presentation）

責務を「何を行うか（domain）」「どこと通信するか（infra）」「何を表示するか（presentation）」で分割する。

```
src/
└── kage_shiki/
    ├── __init__.py
    ├── main.py
    ├── domain/           # ビジネスロジック（外部依存なし）
    │   ├── __init__.py
    │   ├── agent_core.py
    │   ├── memory_worker.py
    │   ├── persona_system.py
    │   └── wizard.py
    ├── infra/            # 外部システムとの境界
    │   ├── __init__.py
    │   ├── db.py         # SQLite + FTS5
    │   ├── llm_client.py # Anthropic SDK ラッパー
    │   └── file_io.py    # persona_core.md 等のファイル操作
    ├── presentation/     # GUI・トレイ
    │   ├── __init__.py
    │   ├── mascot_view.py
    │   ├── tkinter_view.py
    │   └── system_tray.py
    └── config.py         # 設定（全レイヤーから参照可）
```

- **概要**: 古典的なレイヤードアーキテクチャ。依存は presentation → domain → infra の一方向
- **メリット**: 依存方向が明確で循環依存を防げる。infra 差し替え（SQLite → PostgreSQL 等）が容易。クリーンアーキテクチャの概念を学習済みチームには馴染みやすい
- **デメリット**: 影式の実際の設計（AgentCore が DB も LLM も呼ぶ）では「domain が infra を呼ぶ」が自然であり、依存逆転の原則（DIP）を厳守しようとするとインターフェースが増殖する。Python プロジェクトの標準的慣例とは言えず、過剰な抽象化になりやすい。Phase 1 の規模では恩恵より複雑性のほうが大きい

### 選択肢 C: フィーチャーベース（機能ドメインごとにディレクトリ）

アプリの関心事（feature）ごとにまとめる。

```
src/
└── kage_shiki/
    ├── __init__.py
    ├── main.py              # エントリポイント
    ├── core/                # アプリケーション基盤（全体から参照）
    │   ├── __init__.py
    │   ├── config.py        # Config（AppConfig dataclass）
    │   └── logging_setup.py # ログ設定（D-2 参照）
    ├── agent/               # 対話エンジン
    │   ├── __init__.py
    │   ├── agent_core.py    # ReAct ループ本体
    │   └── llm_client.py    # Anthropic SDK ラッパー
    ├── memory/              # 記憶システム
    │   ├── __init__.py
    │   ├── db.py            # SQLite + FTS5 操作
    │   └── memory_worker.py # 日次サマリー生成
    ├── persona/             # 人格システム
    │   ├── __init__.py
    │   ├── persona_system.py # persona_core.md / style_samples.md 管理
    │   └── wizard.py        # 人格生成ウィザード
    ├── gui/                 # GUI・表示
    │   ├── __init__.py
    │   ├── mascot_view.py   # MascotView Protocol（Interface）
    │   └── tkinter_view.py  # TkinterMascotView（実装）
    └── tray/                # システムトレイ
        ├── __init__.py
        └── system_tray.py   # pystray ラッパー
```

- **概要**: 機能ドメイン単位でディレクトリを切る。各ディレクトリが「一つのテーマ」を持つ
- **メリット**: 機能追加（Phase 2 の DesireWorker → `desire/`、AgenticSearch → `search/`）がディレクトリの追加で完結し、既存コードへの影響が最小。関連ファイルが地理的に近い。テストのディレクトリ構造と1対1に対応しやすい（`tests/test_agent/` 等）。Python パッケージングの慣例（setuptools, hatch 等の src layout）に適合
- **デメリット**: フラット構成よりは import パスが長い（`from kage_shiki.agent.agent_core import AgentCore`）。機能が cross-cutting（例：ログ）の場合の配置に迷う余地がある

### 選択肢 D: フラット + サブモジュール折衷案

コア部分はフラットに、肥大化するモジュールだけサブディレクトリを切る。

```
src/
└── kage_shiki/
    ├── __init__.py
    ├── main.py
    ├── config.py
    ├── agent_core.py
    ├── llm_client.py
    ├── db.py
    ├── memory_worker.py
    ├── persona_system.py
    ├── wizard/              # ウィザードのみサブモジュール化
    │   ├── __init__.py
    │   └── ...
    └── gui/
        ├── __init__.py
        └── ...
```

- **概要**: フラットを基本とし、必要に応じてサブモジュール化する漸進的アプローチ
- **メリット**: 今必要な分だけ構造化できる
- **デメリット**: 構造化の基準が曖昧で、チームやセッションによってばらつく。Phase 2 でリファクタリングが必要になる可能性が高い

---

## 3. Three Agents Perspective

**[Affirmative]**（推進者の視点）

フィーチャーベース（選択肢 C）を強く推奨する。影式は Phase 1 から Phase 4 にわたって拡張されることが確定しており、Phase 2 で DesireWorker・AgenticSearch、Phase 3 で Theory of Mind が追加される。これらはそれぞれ独立した「機能ドメイン」であり、ディレクトリを追加するだけで既存コードを一切変更せずに統合できる。

また、`tests/` ディレクトリとの対称性が生まれる（`tests/test_agent/`、`tests/test_memory/` 等）。pytest の収集パスも自然に分離される。

Phase 1 の段階でこの構造を確立することで、チーム間の「このファイルはどこ？」という認知負荷を排除できる。

**[Critical]**（批判者の視点）

懸念点は2つある。

第一に、`core/` の性質が曖昧になるリスクがある。`config.py` と `logging_setup.py` を `core/` に入れているが、他の全モジュールが `core/` に依存する構造は「フラット外のフラット」を作るだけで、かえって `core/` がゴミ箱になりかねない。

第二に、`agent/` と `memory/` の間で `db.py` がどちらに属するか曖昧である。AgentCore が FTS5 検索を行うため、`agent/` が `memory/db.py` を import する構造になるが、これは機能ドメイン間の依存を生む。依存方向のルールを明示しないと、実装時に混乱する。

**[Mediator]**（調停者の結論）

フィーチャーベース（選択肢 C）を採用するが、Critical の懸念に対処するために以下の補足ルールを加える。

1. `core/` は config と logging のみに限定し、「ゴミ箱化」を防ぐ。他の横断関心事（エラー定義等）が増える場合は D-6（エラーメッセージ）設計時に再評価する
2. 依存方向のルールを明示する（Section 5 に記述）
3. `tray/` は Phase 1 において `system_tray.py` 1ファイルのみのため、小さすぎるディレクトリとなる懸念がある。しかし MascotView Protocol との関心事分離（GUI ウィンドウ vs トレイ）を明確にするため、独立させる価値がある

---

## 4. 決定

**採用**: 選択肢 C — フィーチャーベース構成

**理由**:
1. **拡張性**: Phase 2-4 のコンポーネント追加がディレクトリ追加で完結し、既存コードへの影響が最小化される
2. **可読性**: 機能ドメインと物理構造が一致し、「このコードはどこ？」の認知負荷が低い
3. **テスト対称性**: `tests/` が `src/kage_shiki/` と同じ構造を持てる
4. **Python 慣例**: src layout + パッケージ分割は Python プロジェクトの標準的なアプローチ
5. **YAGNI 遵守**: レイヤードアーキテクチャ（選択肢 B）のような過剰なインターフェース定義が不要

---

## 5. 詳細仕様

### 5.1 確定ディレクトリ構成

```
src/
└── kage_shiki/
    ├── __init__.py          # バージョン定義のみ
    ├── main.py              # エントリポイント（起動シーケンス）
    ├── core/                # アプリケーション基盤
    │   ├── __init__.py
    │   ├── config.py        # AppConfig dataclass + TOML 読み書き
    │   └── logging_setup.py # ログ初期化（D-2 で仕様確定）
    ├── agent/               # 対話エンジン（AgentCore）
    │   ├── __init__.py
    │   ├── agent_core.py    # ReAct ループ本体
    │   └── llm_client.py    # Anthropic SDK ラッパー（リトライ・タイムアウト）
    ├── memory/              # 記憶システム
    │   ├── __init__.py
    │   ├── db.py            # SQLite + FTS5 操作（スキーマ定義・CRUD）
    │   └── memory_worker.py # 日次サマリー生成・欠損補完
    ├── persona/             # 人格システム
    │   ├── __init__.py
    │   ├── persona_system.py # persona_core.md / style_samples.md の読み込み・凍結管理
    │   └── wizard.py        # 人格生成ウィザード（3方式 + プレビュー + 凍結）
    ├── gui/                 # GUI・表示
    │   ├── __init__.py
    │   ├── mascot_view.py   # MascotView Protocol 定義（typing.Protocol）
    │   └── tkinter_view.py  # TkinterMascotView 実装
    └── tray/                # システムトレイ
        ├── __init__.py
        └── system_tray.py   # pystray ラッパー（メニュー定義・表示/非表示コールバック）
```

### 5.2 対応テストディレクトリ構成

```
tests/
├── conftest.py              # pytest フィクスチャ共通定義
├── test_core/
│   ├── __init__.py
│   └── test_config.py
├── test_agent/
│   ├── __init__.py
│   ├── test_agent_core.py
│   └── test_llm_client.py
├── test_memory/
│   ├── __init__.py
│   ├── test_db.py
│   └── test_memory_worker.py
├── test_persona/
│   ├── __init__.py
│   ├── test_persona_system.py
│   └── test_wizard.py
├── test_gui/
│   ├── __init__.py
│   └── test_mascot_view.py
└── test_tray/
    ├── __init__.py
    └── test_system_tray.py
```

### 5.3 依存方向ルール

以下のルールを遵守する。違反はコードレビューで検出する。

```
依存の許可方向:
  main.py
    ├── core/
    ├── agent/   ──→ core/, memory/, persona/
    ├── memory/  ──→ core/
    ├── persona/ ──→ core/
    ├── gui/     ──→ core/
    └── tray/    ──→ core/, gui/

禁止:
  core/ → core 外のいかなるパッケージも import 禁止（core 内部の相互参照は許可）
  memory/ → agent/ の import 禁止（逆方向）
  gui/ → agent/, memory/, persona/ の直接 import 禁止
         （GUI はキューのみで通信。AgentCore の参照を持たない）
```

### 5.4 モジュール責務一覧

| ファイル | 主な責務 | 外部ライブラリ依存 |
|---------|---------|-----------------|
| `main.py` | 起動シーケンス（FR-1.1〜1.6 の順序制御）、スレッド起動 | tkinter, threading, asyncio |
| `core/config.py` | AppConfig dataclass、TOML 読み書き、バリデーション | tomllib（標準） |
| `core/logging_setup.py` | ロガー初期化、ハンドラー設定（D-2 参照） | logging（標準） |
| `agent/agent_core.py` | ReAct ループ、コンテキスト構築、FTS5 呼び出し判断 | asyncio |
| `agent/llm_client.py` | Anthropic SDK 呼び出し、リトライ、タイムアウト | anthropic |
| `memory/db.py` | SQLite 接続管理、スキーマ初期化、observations CRUD、FTS5 検索 | sqlite3（標準） |
| `memory/memory_worker.py` | サマリー生成、欠損補完、atexit フック登録 | asyncio |
| `persona/persona_system.py` | persona_core.md・style_samples.md 読み込み・ハッシュ検証・凍結ガード | hashlib（標準） |
| `persona/wizard.py` | ウィザード3方式、LLM パイプライン、プレビュー会話 | asyncio |
| `gui/mascot_view.py` | MascotView Protocol（typing.Protocol）定義のみ | なし |
| `gui/tkinter_view.py` | Protocol 実装、枠なしウィンドウ、ドラッグ、queue ポーリング | tkinter（標準） |
| `tray/system_tray.py` | pystray アイコン、メニュー定義、表示/非表示コールバック | pystray |

### 5.5 data/ ディレクトリ（実行時生成）

```
data/                        # config.toml の data_dir で指定（デフォルト: ./data）
├── memory.db                # SQLite DB（起動時に自動生成）
├── persona_core.md          # 人格核（ウィザード完了後に生成）
├── style_samples.md         # 口調参照例（ウィザード完了後に生成）
├── human_block.md           # ユーザー情報（起動時に空ファイル生成）
├── personality_trends.md    # 傾向メモ（起動時に空ファイル生成）
└── kage_shiki.log           # ログファイル（D-2 参照）
```

`data/` は `.gitignore` に追加し、個人データをリポジトリに含めない。

### 5.6 Phase 2-4 拡張パス

Phase 2 以降のコンポーネント追加は以下のディレクトリ追加で対応する。既存ディレクトリへの変更は最小限。

```
Phase 2 追加:
  src/kage_shiki/
    ├── desire/             # DesireWorker（欲求システム）
    │   ├── __init__.py
    │   └── desire_worker.py
    └── search/             # AgenticSearch パイプライン
        ├── __init__.py
        ├── search_engine.py  # 抽象インターフェース
        └── haiku_engine.py   # HaikuEngine 実装

Phase 3 追加:
  src/kage_shiki/
    └── mind/               # Theory of Mind
        ├── __init__.py
        └── tone_analyzer.py  # ルールベース → LLM 昇格
```

---

## 6. 影響範囲

| 影響先 | 内容 |
|--------|------|
| D-2（ログ設計） | `core/logging_setup.py` への配置が確定。ログファイルは `data/kage_shiki.log` |
| D-3（プロンプトテンプレート） | `agent/agent_core.py` 内に実装 |
| D-4（FTS5 同期） | `memory/db.py` 内に実装 |
| D-5（ウィザードフロー） | `persona/wizard.py` に実装。GUI 部分は `gui/tkinter_view.py` との連携 |
| D-6（エラーメッセージ） | `core/` への追加（例: `core/errors.py`）または各モジュールに分散。D-6 で決定 |
| D-7（SQLite VACUUM） | `memory/db.py` または `memory/memory_worker.py` に実装 |
| D-8（整合性チェック） | `agent/agent_core.py` 内のプロンプト構築ロジック |
| D-9（トレイ通知） | `tray/system_tray.py` に実装 |
| D-10（.env ファイル） | `main.py` または `core/config.py` の起動直後に処理 |
| D-11（Windows 終了シグナル） | `main.py` でのシグナル登録、`memory/memory_worker.py` でのサマリー生成 |
| D-12（ウィザードモデル） | `core/config.py` の AppConfig + `persona/wizard.py` での参照 |
| D-13（session_id 生成） | `memory/db.py` または `agent/agent_core.py` |
| D-14（personality_trends 承認） | `agent/agent_core.py` での検出 + `persona/persona_system.py` での書き込み |
| D-15（max_tokens） | `agent/llm_client.py` での API 呼び出し + `core/config.py` の AppConfig |
| tests/ | `src/kage_shiki/` の構造と1対1で対応 |
