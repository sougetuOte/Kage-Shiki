# 影式 (Kage-Shiki)

**"Not yet divine. Not yet free."**

人格を持ち、記憶を引き継ぐ Windows 常駐テキストデスクトップマスコット。

セッションをまたいで記憶が継続し、人格は初期生成後に凍結される。歴史（エピソード）の蓄積によって関係が深まる。ウィンドウのヘリをボディ代わりに、突っつくと反応する。

## 主な特徴

- **人格生成システム**: AI おまかせ / 既存イメージ / 白紙育成 の3方式。生成後は凍結し一貫性を保つ
- **3層記憶システム**: Hot（人格核・常時注入）/ Warm（直近サマリー）/ Cold（FTS5 検索）
- **永続記憶**: SQLite + FTS5 による会話断片の即時書込と日次サマリー蒸留
- **シャットダウン耐性**: atexit / signal の2層防御 + 起動時リカバリ
- **Windows 常駐**: pystray によるトレイ常駐 + tkinter 枠なしウィンドウ

## 技術スタック

| 要素 | 選定 |
|------|------|
| 言語 | Python 3.12+ |
| GUI | tkinter（標準ライブラリ） |
| トレイ常駐 | pystray |
| LLM API | anthropic（公式 SDK） |
| DB | SQLite + FTS5 |
| 設定 | TOML（tomllib） |

## Phase ロードマップ

| Phase | 内容 | 状況 |
|-------|------|------|
| **Phase 1: 基盤（MVP）** | tkinter GUI + pystray 常駐、API 接続、人格生成ウィザード、記憶システム、日次サマリー | **BUILDING 中** |
| **Phase 2: 自律性** | 欲求システム、自律発言、セマンティック検索（sqlite-vec）、忘却曲線 | 未着手 |
| **Phase 3: 知性** | 好奇心システム、Theory of Mind、傾向メモ層の承認制更新 | 未着手 |
| **Phase 4: 成熟** | 整合性チェック精度向上、月次記憶要約 | 未着手 |

### Phase 1 進捗

テスト: 546 passed / カバレッジ: 98%

実装済みモジュール:
- `core/config.py` — TOML 設定パーサー + バリデーション
- `core/env.py` — 環境変数管理 + API キー検証
- `core/errors.py` — エラーメッセージ定義（EM-001〜EM-011）
- `core/logging_setup.py` — ログ設定（RotatingFileHandler）
- `core/shutdown_handler.py` — シャットダウン2層防御（atexit + SetConsoleCtrlHandler）
- `agent/llm_client.py` — LLM クライアント（purpose ベースモデルスロット）
- `agent/agent_core.py` — AgentCore ReAct ループ + 整合性チェック + クリック処理
- `agent/trends_proposal.py` — personality_trends 承認フロー（トリガー + 承認判定）
- `agent/human_block_updater.py` — human_block 自己編集（ガードレール付き）
- `memory/db.py` — SQLite + FTS5 CRUD + リトライ
- `memory/memory_worker.py` — 日次サマリー生成 + 欠損日補完
- `persona/persona_system.py` — 3段階ペルソナロード + 凍結制御 + freeze_and_save
- `persona/wizard.py` — ウィザードモード A/B/C + プレビュー + 凍結 + 白紙育成
- `gui/tkinter_view.py` — MascotView Protocol + 枠なしウィンドウ
- `tray/system_tray.py` — pystray 統合 + メニュー + 通知

---

## 開発プロセス（LAM フレームワーク）

LAM（Living Architect Model）の概念を素早く理解するには、[概念説明スライド](docs/slides/index.html)をご覧ください。

### フェーズコマンド

| コマンド | 用途 | 禁止事項 |
|---------|------|---------|
| `/planning` | 要件定義・設計・タスク分解 | コード生成禁止 |
| `/building` | TDD 実装 | 仕様なし実装禁止 |
| `/auditing` | レビュー・監査・リファクタ | 修正の直接実施禁止 |
| `/project-status` | 進捗状況の表示 | - |

### 承認ゲート

```
requirements → [承認] → design → [承認] → tasks → [承認] → BUILDING → [承認] → AUDITING
```

各サブフェーズ完了時にユーザー承認が必要。未承認のまま次に進むことは禁止。

### サブエージェント

| エージェント | 用途 | 推奨フェーズ |
|-------------|------|-------------|
| `requirement-analyst` | 要件分析・ユーザーストーリー | PLANNING |
| `design-architect` | API 設計・アーキテクチャ | PLANNING |
| `task-decomposer` | タスク分割・依存関係整理 | PLANNING |
| `tdd-developer` | Red-Green-Refactor 実装 | BUILDING |
| `quality-auditor` | 品質監査・セキュリティ | AUDITING |
| `doc-writer` | ドキュメント作成・仕様策定・更新 | ALL |
| `test-runner` | テスト実行・分析 | BUILDING |
| `code-reviewer` | コードレビュー（LAM 品質基準） | AUDITING |

### セッション管理コマンド

| コマンド | 用途 |
|---------|------|
| `/quick-save` | 軽量セーブ（SESSION_STATE.md のみ） |
| `/quick-load` | 軽量ロード（日常の再開） |
| `/full-save` | フルセーブ（commit + push + daily） |
| `/full-load` | フルロード（数日ぶりの復帰） |

### 推奨モデル

| フェーズ | 推奨モデル |
|---------|----------|
| **PLANNING** | Claude Opus / Sonnet |
| **BUILDING** | Claude Sonnet（単純作業なら Haiku） |
| **AUDITING** | Claude Opus（Long Context） |

---

## 環境要件

| 要件 | 用途 | 必須/任意 |
|------|------|----------|
| [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) | AI アシスタント実行環境 | 必須 |
| Python 3.12+ | アプリケーション本体 | 必須 |
| Git | バージョン管理 | 必須 |

## ライセンス

MIT License
