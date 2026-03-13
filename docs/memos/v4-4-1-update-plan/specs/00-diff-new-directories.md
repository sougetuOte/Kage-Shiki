# 新ディレクトリ構造 + docs/specs/ 差分分析

## 概要

LAM v4.4.1 テンプレートと影式現行を比較し、以下 5 カテゴリの差分を分析した。

1. `docs/artifacts/`（v4.2.0 新規）
2. `.claude/agent-memory/`（v4.2.0 新規）
3. `docs/specs/` の差分
4. `docs/adr/` の差分
5. `.gitignore` の差分

**結論**: `docs/artifacts/` は影式プロジェクトに導入する価値がある（特に `knowledge/` と `tdd-patterns/`）。`.claude/agent-memory/` は code-reviewer エージェント導入時に合わせて検討。`docs/specs/` は 4 ファイルが新規追加。`docs/adr/` は 3 件新規。`.gitignore` は LAM ランタイム状態ファイルの除外追加が必要。

---

## 1. docs/artifacts/（v4.2.0 新規）

### 概要

影式には存在しない新規ディレクトリ。LAM の「中間成果物・知見蓄積の専用場所」として v4.2.0 で導入された。影式では現在 `docs/memos/` がこの役割を兼ねている。

### LAM v4.4.1 のディレクトリ構造

```
docs/artifacts/
├── audit-reports/              # 監査レポート格納
│   ├── 2026-03-12-fullscan-comprehensive.md
│   ├── 2026-03-12-iter1.md
│   ├── 2026-03-12-iter2.md
│   ├── 2026-03-13-iter1.md
│   ├── 2026-03-13-iter2.md
│   ├── 2026-03-13-v441-iter1.md
│   ├── 2026-03-13-v441-iter2.md
│   ├── 2026-03-13-v441-iter3.md
│   └── 2026-03-13-v441-iter4.md
├── knowledge/                  # /retro 由来の知見蓄積
│   ├── README.md
│   ├── conventions.md
│   ├── patterns.md
│   └── pitfalls.md
├── tdd-patterns/               # TDD 内省パイプラインのパターン詳細記録（空）
├── feat-v4.0.0-immune-system.md  # 免疫系要件分析の中間成果物（specs/ から移動）
├── retro-v4.4.0.md             # v4.4.0 レトロスペクティブ
└── retro-v4.4.1.md             # v4.4.1 レトロスペクティブ
```

### サブディレクトリ詳細

#### knowledge/

`/retro` の Step 4「知見の蓄積」で記録される、プロジェクト固有のコンテキスト知識。

| ファイル | 内容 | 管理ルール |
|---------|------|-----------|
| `README.md` | Knowledge Layer の説明、管理ルール、権限等級、Subagent Memory との棲み分け | カテゴリファイル上限 5、各ファイル 200 行上限 |
| `conventions.md` | プロジェクト固有の慣例（テンプレートのみ、実データなし） | 定着したら `.claude/rules/` へ昇格（PM級） |
| `patterns.md` | うまくいったコーディング・設計パターン（テンプレートのみ） | 繰り返し参照されたら rules へ昇格 |
| `pitfalls.md` | 踏んだ地雷と回避策（テンプレートのみ） | 繰り返し記録されたら rules へ昇格 |

知見蓄積の権限等級:
- knowledge/ への記録: **SE級**
- knowledge/ から rules/ への昇格: **PM級**
- knowledge/ の棚卸し・削除: **PM級**
- 90 日未参照の知見は `/quick-save` の Daily 記録時に棚卸し通知

#### audit-reports/

`/full-review` の各イテレーション監査レポートを格納。日付ベースの命名規則（`YYYY-MM-DD-iterN.md`）。

#### tdd-patterns/

TDD 内省パイプライン v2 のパターン詳細記録先。LAM v4.4.1 時点では空ディレクトリ。
影式では現在 `docs/memos/tdd-patterns/` として `.claude/rules/auto-generated/README.md` から参照されている。

### 影式での導入判断ポイント

| サブディレクトリ | 導入判断 | 理由 |
|----------------|---------|------|
| `knowledge/` | **推奨** | 影式の retro 記録（`retro-phase-1.md`, `retro-wave-9.md` 等）は `docs/memos/` に散在しており、構造化された蓄積先がない。knowledge/ の 3 ファイル構造は知見整理に有効 |
| `audit-reports/` | **推奨** | 影式の監査レポート（`audit-report-full-source.md`, `audit-report-wave3.md`）も `docs/memos/` に散在。専用ディレクトリに移動すべき |
| `tdd-patterns/` | **推奨** | `.claude/rules/auto-generated/README.md` が既に `docs/memos/tdd-patterns/` を参照しているが、実ディレクトリが未作成。`docs/artifacts/tdd-patterns/` にパス変更して作成 |
| ルートの retro/feat ファイル | **適宜** | retro ファイルは `/retro` 実行時に自然に生成される |

**移行作業**: 既存の `docs/memos/` にある監査レポートや retro 記録を `docs/artifacts/` に移動する場合は PM級（ディレクトリ構造変更）。

---

## 2. .claude/agent-memory/（v4.2.0 新規）

### 概要

影式には存在しない新規ディレクトリ。カスタム Subagent（`.claude/agents/`）がレビュー中に学んだプロジェクト固有の知見を永続化する仕組み。Claude Code の公式フロントマター機能ではなく、CLAUDE.md の指示に従いサブエージェントが自発的に書き込む。

### LAM v4.4.1 のディレクトリ構造

```
.claude/agent-memory/
└── code-reviewer/
    ├── MEMORY.md                    # インデックス（3 ファイルへのリンク）
    ├── project_hook_structure.md    # hooks/ の実装構造と既知の品質課題
    ├── project_hooks_security.md    # hooks/ セキュリティ監査結果と要注意箇所
    └── project_test_structure.md    # テストスイート構成と重複問題
```

### 各ファイルの内容

| ファイル | フロントマター type | 内容 |
|---------|-------------------|------|
| `MEMORY.md` | - | 知見ファイルのインデックス表 |
| `project_hook_structure.md` | `project` | hooks/ 構成（5 ファイル）、残存課題 10 件、解消済み課題 6 件の詳細記録 |
| `project_hooks_security.md` | `project` | セキュリティ要注意箇所 5 件（優先度順）、良好な点 5 件の記録 |
| `project_test_structure.md` | `project` | テスト分散（hooks/tests/ + tests/）と重複定義 5 件の記録 |

各知見ファイルには `Why`（なぜ記録するか）と `How to apply`（次回レビュー時の使い方）が記載されている。

### knowledge/ との棲み分け

CLAUDE.md の Memory Policy セクションで明確に区別されている:

| 仕組み | 蓄積者 | タイミング | 内容 |
|--------|--------|-----------|------|
| `docs/artifacts/knowledge/` | 人間（/retro 経由） | Wave/Phase 完了時 | 意図的に整理された知見・教訓 |
| `.claude/agent-memory/` | Subagent（自動） | 実行中に自発的に | 実行中に学んだパターン・慣例 |
| Auto Memory (`MEMORY.md`) | Claude 本体（自動） | セッション中 | ビルドコマンド、デバッグ知見等 |

### 影式での導入判断ポイント

| 観点 | 判断 | 理由 |
|------|------|------|
| ディレクトリ作成 | **延期可** | 影式には現在 code-reviewer エージェントが存在しない。LAM テンプレートの `.claude/agents/code-reviewer.md` を導入する際に合わせて作成するのが自然 |
| CLAUDE.md の Memory Policy 更新 | **推奨** | 影式の現行 CLAUDE.md は「Subagent の役割ノウハウ蓄積のみに使用可」と記載。LAM v4.4.1 の三層構造（knowledge / agent-memory / auto-memory）に更新すべき |
| .gitignore への追加 | **不要** | agent-memory はプロジェクト固有知見のためリポジトリに含めるべき（LAM v4.4.1 でも gitignore 対象外） |

---

## 3. docs/specs/ の差分

### LAM v4.4.1 の仕様書一覧

| ファイル | 概要 | 影式の対応 |
|---------|------|-----------|
| `doc-writer-spec.md` | doc-writer エージェントのドキュメント自動追従仕様（Wave 3 対応） | **取り込み済み**（v4.0.1 移行時） |
| `evaluation-kpi.md` | 運用 KPI 定義（Tier 1: 5 指標） | **取り込み済み** |
| `green-state-definition.md` | Green State 5 条件の定義（P5-FR-1 対応） | **取り込み済み**（影式版にカスタマイズ済み） |
| `lam-orchestrate-design.md` | LAM Orchestrate エージェントの設計書（v3.0.0） | **取り込み済み** |
| `loop-log-schema.md` | `/full-review` ループログのスキーマ定義 | **取り込み済み** |
| `v3.9.0-improvement-adoption.md` | v3.9.0 運用実績ベースの改善採用記録 | **取り込み済み** |
| `v4.0.0-immune-system-design.md` | 免疫系アーキテクチャ設計書（歴史的文書注記あり） | **取り込み済み** |
| `v4.0.0-immune-system-requirements.md` | 免疫系アーキテクチャ要件定義（歴史的文書注記あり） | **取り込み済み** |
| `hooks-python-migration/requirements.md` | フックスクリプト Python 一本化の要件定義 | **v4.4.1 新規** |
| `hooks-python-migration/design.md` | フックスクリプト Python 一本化の設計書 | **v4.4.1 新規** |
| `hooks-python-migration/tasks.md` | フックスクリプト Python 一本化のタスク分解（全 32 タスク） | **v4.4.1 新規** |
| `release-ops-revision.md` | `04_RELEASE_OPS.md` 改訂仕様（approved） | **v4.4.1 新規** |
| `tdd-introspection-v2.md` | TDD 内省パイプライン v2 仕様（JUnit XML 方式、approved） | **v4.4.1 新規** |
| `ui-lam-slides.md` | LAM 概念説明スライド UI 仕様 | **取り込み済み** |

### 影式の docs/specs/ 一覧

| ディレクトリ | 内容 | LAM 対応 |
|-------------|------|---------|
| `lam/` | LAM 関連仕様 7 ファイル（上記の取り込み済み分） | v4.0.1 移行時に取り込み |
| `phase1-mvp/` | 影式 Phase 1 MVP 仕様（requirements, tasks, design-d01〜d16） | **影式固有** |
| `phase2a-foundation/` | 影式 Phase 2a 基盤仕様（requirements, tasks, design-d17〜d20） | **影式固有** |
| `phase2b-autonomy/` | 影式 Phase 2b 自律性仕様（requirements のみ） | **影式固有** |

### v4.4.1 新規ファイルの導入判断

| ファイル | 導入判断 | 理由 |
|---------|---------|------|
| `hooks-python-migration/*` | **要検討** | 影式は Python プロジェクトのため bash → Python 移行の恩恵あり。ただし hooks 自体の差分分析（`00-diff-hooks-settings.md`）と連動して判断すべき |
| `release-ops-revision.md` | **推奨** | `docs/internal/04_RELEASE_OPS.md` の改訂仕様。影式の SSOT 更新に必要 |
| `tdd-introspection-v2.md` | **推奨** | TDD 内省パイプラインの再設計仕様。影式の `.claude/rules/auto-generated/trust-model.md` が v1 のまま。v2 への更新に必要 |
| `ui-lam-slides.md` | **取り込み済み** | v4.0.1 移行時に取り込み済み |

### 取り込み済みファイルの v4.4.1 での変更点

| ファイル | v4.4.1 での変更 |
|---------|----------------|
| `v4.0.0-immune-system-design.md` | 「歴史的文書」注記が追加。TDD パターン記録先が `docs/memos/tdd-patterns/` → `docs/artifacts/tdd-patterns/` に変更。ループログ形式の注記追加 |
| `v4.0.0-immune-system-requirements.md` | 「歴史的文書」注記が追加。`ultimate-think` 統合、TDD パターン記録先変更、v2 再設計の注記追加 |
| その他 | 軽微な更新（未精査。必要に応じて個別差分確認） |

---

## 4. docs/adr/ の差分

### LAM v4.4.1 の ADR 一覧

| ADR | タイトル | ステータス | 影式の対応 |
|-----|---------|-----------|-----------|
| `0001-model-routing-strategy.md` | モデルルーティング戦略 | Proposed | **v4.4.1 新規** |
| `0002-stop-hook-implementation.md` | Stop hook 実装方式（Ralph Wiggum vs 独自実装） | Accepted | **v4.4.1 新規** |
| `0003-context7-vs-webfetch.md` | 公式仕様取得における context7 MCP vs WebFetch の使い分け | Accepted | **v4.4.1 新規** |
| `0004-bash-read-commands-allow-list.md` | settings.json の Bash(cat/grep *) 無制限許可を現行維持 | Accepted | **v4.4.1 新規** |

### 影式の ADR 一覧

| ADR | タイトル | ステータス |
|-----|---------|-----------|
| `0001-lam-v4-immune-system-architecture.md` | LAM v4.0.0 免疫系アーキテクチャの導入 | Accepted |

### 差分分析

| 観点 | 詳細 |
|------|------|
| 番号体系の衝突 | 影式の ADR-0001 は「免疫系アーキテクチャの導入」（影式固有の導入判断記録）。LAM v4.4.1 の ADR-0001 は「モデルルーティング戦略」（LAM 汎用の設計判断）。内容が異なるため番号の再割り当てが必要 |
| 取り込み対象 | LAM の ADR-0002〜0004 は LAM 汎用の設計判断であり、影式でも同じ基盤を使用するため取り込み推奨 |
| 番号割り当て案 | 影式 ADR-0001 は既存維持。LAM の ADR-0001〜0004 を影式 ADR-0002〜0005 として取り込み |

### 導入判断

| LAM ADR | 導入判断 | 理由 |
|---------|---------|------|
| ADR-0001 モデルルーティング | **推奨** | Opus/Sonnet の使い分け基準。影式でも同じモデルを使用 |
| ADR-0002 Stop hook | **推奨** | lam-stop-hook.py の設計根拠。影式でも hooks を導入するなら必要 |
| ADR-0003 context7 vs WebFetch | **推奨** | upstream-first.md から参照される設計判断。影式に既に upstream-first.md がある |
| ADR-0004 Bash read commands | **推奨** | settings.json の設計判断根拠。影式でも同じ設定を使用 |

---

## 5. .gitignore の差分

### 差分一覧

| セクション | 影式現行 | LAM v4.4.1 | 差分 |
|-----------|---------|------------|------|
| General | `.DS_Store`, `Thumbs.db`, `*.log` | 同一 | なし |
| Editors | `.vscode/`, `.idea/`, `*.swp` | 同一 | なし |
| Python | `__pycache__/`, `*.py[cod]` 等 | 同一 | なし |
| Node.js | なし | `node_modules/`, `dist/`, `build/`, `.env`, `.env.local`, `npm-debug.log*` 等 | **LAM にのみ存在**（影式は Python 専用） |
| Environment | `.env`, `.env.local` | なし（Node.js セクションに含む） | 影式は独自セクション |
| pytest | `.pytest_cache/`, `htmlcov/`, `.coverage` | なし | **影式にのみ存在** |
| Agent | 下記参照 | 下記参照 | 差分あり |
| LAM runtime | なし | 下記参照 | **LAM v4.4.1 新規** |
| Reference | `_reference/` | `_reference/`, `last-test-result` | LAM に `last-test-result` 追加 |
| User Config | `config.toml` | なし | **影式にのみ存在** |

### Agent セクション詳細差分

| エントリ | 影式 | LAM v4.4.1 | 備考 |
|---------|------|------------|------|
| `.agent/` | あり | あり | 同一 |
| `memos/` | あり | あり | 同一 |
| `!docs/memos/` | あり | なし | 影式固有（docs/memos/ を除外から除く） |
| `docs/memos/*` | あり | なし | 影式固有 |
| `!docs/memos/v4-update-plan/` | あり | なし | 影式固有（特定サブディレクトリを追跡） |
| `.serena/` | あり | あり | 同一 |
| `data/` | あり | あり | 同一 |
| `SESSION_STATE.md` | あり | あり | 同一 |
| `docs/daily/` | あり | あり | 同一 |
| `.claude/settings.local.json` | あり | あり | 同一 |
| `.claude/commands/release.md` | あり | あり | 同一（LAM にはコメント付き） |
| `.claude/doc-sync-flag` | あり | なし（LAM runtime セクションに移動） | 位置の違い |
| `.claude/last-test-result` | あり | なし（LAM runtime セクションに移動） | 位置の違い |
| `.claude/pre-compact-fired` | あり | なし（LAM runtime セクションに移動） | 位置の違い |

### LAM v4.4.1 新規: LAM runtime state files セクション

```gitignore
# LAM runtime state files
.claude/lam-loop-state.json
.claude/doc-sync-flag
.claude/pre-compact-fired
.claude/last-test-result
.claude/test-results.xml
```

影式に追加が必要なエントリ:

| エントリ | 理由 |
|---------|------|
| `.claude/lam-loop-state.json` | lam-stop-hook.py が生成するループ状態ファイル。影式に hooks を導入する場合に必要 |
| `.claude/test-results.xml` | TDD 内省パイプライン v2 が pytest の JUnit XML 出力を読み取るファイル。test-result-output.md ルールで定義 |

既存の `.claude/doc-sync-flag`, `.claude/last-test-result`, `.claude/pre-compact-fired` は影式にも存在するため、セクション整理のみで内容変更なし。

### 導入作業

1. `.claude/lam-loop-state.json` を `.gitignore` に追加
2. `.claude/test-results.xml` を `.gitignore` に追加
3. （任意）Agent セクションから LAM runtime エントリを分離してセクション整理

---

## 移行時の注意事項

### 1. 新規ディレクトリ作成が必要なもの

| ディレクトリ | 優先度 | 作業内容 |
|-------------|--------|---------|
| `docs/artifacts/knowledge/` | 高 | README.md + 3 テンプレートファイル作成 |
| `docs/artifacts/audit-reports/` | 中 | ディレクトリ作成。既存レポートの移動は任意 |
| `docs/artifacts/tdd-patterns/` | 中 | ディレクトリ作成。`.claude/rules/auto-generated/README.md` のパス参照更新 |
| `.claude/agent-memory/` | 低 | code-reviewer エージェント導入時に作成 |

### 2. 取り込みが必要な新規 specs

| ファイル | 優先度 | 理由 |
|---------|--------|------|
| `tdd-introspection-v2.md` | 高 | TDD 内省パイプラインの再設計。影式の trust-model.md 更新に必要 |
| `release-ops-revision.md` | 中 | SSOT（04_RELEASE_OPS.md）の改訂 |
| `hooks-python-migration/*` | 低 | hooks 差分分析と連動して判断 |

### 3. ADR の取り込み

影式 ADR-0002〜0005 として LAM ADR-0001〜0004 を取り込み。番号体系の衝突を回避。

### 4. .gitignore の更新

`.claude/lam-loop-state.json` と `.claude/test-results.xml` の追加が必須。
