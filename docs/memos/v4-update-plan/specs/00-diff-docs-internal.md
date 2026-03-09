# docs/internal/ + docs/specs/ 差分分析

**作成日**: 2026-03-10
**目的**: LAM 4.0.1 テンプレートと影式現行版の差分を把握し、移行計画の基礎資料とする

---

## 概要

LAM 4.0.1 テンプレートは v4.0.0「免疫系アーキテクチャ」を導入したメジャーアップデートである。影式現行版は LAM 3.9.x ベースに影式固有のカスタマイズ（Python/pytest 特化、Phase 1 Retro 由来のルール等）を加えたものである。

主要な変更軸:
1. **権限等級システム（PG/SE/PM）の導入** — 全ファイルに影響
2. **Hooks ベース自動化** — 07_SECURITY に新セクション、02_DEVELOPMENT_FLOW に TDD Introspection 追加
3. **SSOT 3層アーキテクチャの明文化** — 00_PROJECT_STRUCTURE に追加
4. **AUDITING フェーズの修正緩和** — PG/SE級の修正を許可（従来は修正禁止）
5. **TDD 内省パイプライン** — 自動ルール生成の仕組み

影式固有ファイル（08_SESSION_MANAGEMENT.md, 09_SUBAGENT_STRATEGY.md）は LAM テンプレートには存在しないが、4.0.1 の新概念を一部先取りした内容を含む。

---

## docs/internal/ 差分

### 00_PROJECT_STRUCTURE.md

#### セクション 1: Directory Structure

| 項目 | 影式現行 | LAM 4.0.1 | 差分種別 |
|------|---------|-----------|---------|
| src/ 配下構造 | `kage_shiki/` パッケージ（agent, core, gui, memory, persona, tray） | `backend/` + `frontend/`（汎用テンプレート） | 影式固有カスタマイズ（維持すべき） |
| .claude/ 配下 | 記載なし | `commands/`, `rules/`, `hooks/`, `skills/`, `agents/`, `states/`, `logs/`, `settings.json` を明示 | **LAM 4.0.1 で新規追加**。hooks/, logs/ が v4.0.0 の免疫系基盤 |

#### セクション 2: Asset Placement Rules

| 項目 | 影式現行 | LAM 4.0.1 | 差分種別 |
|------|---------|-----------|---------|
| A〜C | 同一 | 同一 | 差分なし |
| C. ADR Naming | `YYYY-MM-DD_{decision_title}.md` | `NNNN-kebab-case-title.md`（4桁連番） | **LAM 4.0.1 で変更**。連番方式に統一 |
| D. State Management | 同一 | 同一 | 差分なし |

#### セクション 3: SSOT 3層アーキテクチャ（LAM 4.0.1 で新規追加）

影式現行には存在しない。LAM 4.0.1 で以下が追加:

```
Layer 1: docs/internal/ — プロセス SSOT（What & Why）
Layer 2: .claude/rules/ + commands/ + hooks/ + agents/ + skills/
Layer 3: CHEATSHEET.md — クイックリファレンス
```

- Layer 1 が最高権限、Layer 2 は Layer 1 の「実装」
- Layer 2 に hooks/ が追加されている（v4.0.0 免疫系）

**影式への適用**: 必要。既に影式は暗黙的にこの3層構造を運用しているが、明文化されていない。hooks/ を含む形で追加すべき。

#### セクション 4: File Naming Conventions

| 項目 | 影式現行 | LAM 4.0.1 | 差分種別 |
|------|---------|-----------|---------|
| Files (Code) | Python 標準のみ | Python + JS/TS（PascalCase.tsx, camelCase.ts）も例示 | テンプレートの汎用化。影式は Python のみで OK |

---

### 01_REQUIREMENT_MANAGEMENT.md

**差分なし**。影式現行と LAM 4.0.1 は完全に同一。

---

### 02_DEVELOPMENT_FLOW.md

#### Phase 1: Pre-Flight Impact Analysis

| 項目 | 影式現行 | LAM 4.0.1 | 差分種別 |
|------|---------|-----------|---------|
| Dependency Traversal | `grep_search` を使用 | `Grep` / `Glob` を使用 | **LAM 4.0.1 で更新**。Claude Code のツール名に統一 |
| AoT フレームワークとの連携 | 同一 | 同一 | 差分なし |

#### Phase 2: TDD & Implementation Cycle

| 項目 | 影式現行 | LAM 4.0.1 | 差分種別 |
|------|---------|-----------|---------|
| テスト環境 Note | `pytest` を使用する旨の Note あり | なし（汎用テンプレートのため） | 影式固有カスタマイズ（維持すべき） |
| Step 5: Commit & Review | `walkthrough.md` にまとめ | `docs/memos/walkthrough-<feature>.md` にまとめ（推奨） | **LAM 4.0.1 で微修正**。パス指定がより具体的に |
| **Automated TDD Introspection (v4.0.0)** | なし | PostToolUse hook によるテスト実行結果の自動監視、`.claude/tdd-patterns.log` への蓄積、`.claude/doc-sync-flag` への記録 | **LAM 4.0.1 で新規追加**。免疫系の中核機能 |

#### Phase 3: Periodic Auditing

| 項目 | 影式現行 | LAM 4.0.1 | 差分種別 |
|------|---------|-----------|---------|
| 1〜4 の基本項目 | 同一 | 同一 | 差分なし |
| **権限等級に基づく修正制御 (v4.0.0)** | なし | PG級: 自動修正可、SE級: 修正後報告、PM級: 指摘のみ（承認ゲート） | **LAM 4.0.1 で新規追加** |

#### Wave-Based Development

| 項目 | 影式現行 | LAM 4.0.1 | 差分種別 |
|------|---------|-----------|---------|
| Wave の定義 | 同一 | 同一 | 差分なし |
| Wave 選定基準 | 同一 | 同一 | 差分なし |
| **Wave 実績サマリー** | Wave 1〜8 の影式 Phase 1 MVP 実績あり | なし | 影式固有（維持すべき） |

#### Advanced Workflows

| 項目 | 影式現行 | LAM 4.0.1 | 差分種別 |
|------|---------|-----------|---------|
| `/ship`, `/full-review`, `/wave-plan`, `/retro` | 同一 | 同一 | 差分なし |
| コマンド連携図 | 同一 | 同一 | 差分なし |

#### Quality Rules Integration

| 項目 | 影式現行 | LAM 4.0.1 | 差分種別 |
|------|---------|-----------|---------|
| TDD サイクルとルールのマッピング | R-1〜R-6, S-1〜S-4, A-1〜A-4 の詳細 | なし（LAM テンプレートではこのセクション自体が存在しない） | 影式固有カスタマイズ（Phase 1 Retro 由来。維持すべき） |
| ルール参照先テーブル | あり | なし | 影式固有 |

---

### 03_QUALITY_STANDARDS.md

#### セクション 1〜5: 設計原則〜コード明確性

**差分なし**。影式現行と LAM 4.0.1 は完全に同一。

#### セクション 6: Python Coding Conventions

| 項目 | 影式現行 | LAM 4.0.1 | 差分種別 |
|------|---------|-----------|---------|
| Python 3.12+, PEP 8, Type Hints, ruff, Docstrings | あり | **なし** | 影式固有カスタマイズ（維持すべき）。LAM テンプレートは言語非依存 |

#### セクション 7: Building Defect Prevention

| 項目 | 影式現行 | LAM 4.0.1 | 差分種別 |
|------|---------|-----------|---------|
| R-1〜R-6 の不具合防止ルール一覧 | あり | **なし** | 影式固有カスタマイズ（Phase 1 監査由来。維持すべき） |

#### セクション 8(影式)/6(LAM): Technology Trend Awareness

**差分なし**。同一内容。

---

### 04_RELEASE_OPS.md

**差分なし**。影式現行と LAM 4.0.1 は完全に同一。

ただし影式現行には `<!-- Phase 2b 以降でパッケージング方法（PyInstaller, Nuitka 等）を確定予定 -->` という HTML コメントがあり、LAM 4.0.1 にはない。これは影式固有のメモ。

---

### 05_MCP_INTEGRATION.md

#### セクション 1: MCP Servers

| 項目 | 影式現行 | LAM 4.0.1 | 差分種別 |
|------|---------|-----------|---------|
| Phase 1 MVP Note | 「MCP サーバーは未導入」の Note あり + 各サーバーに「Phase 2 以降で検討」 | 各サーバーに「Optional」とのみ記載 | 影式固有カスタマイズ（影式の現フェーズを反映）。LAM テンプレートはフェーズ非依存 |

#### セクション 2〜6

**差分なし**。影式現行と LAM 4.0.1 は完全に同一（Section 2: 運用注意、Section 3: ワークフロー統合、Section 4: MCP 探し方、Section 5: 設定例、Section 6: MEMORY.md Policy）。

---

### 06_DECISION_MAKING.md

**差分なし**。影式現行と LAM 4.0.1 は完全に同一（Section 1〜5 全て）。

---

### 07_SECURITY_AND_AUTOMATION.md

#### セクション 1: Core Principle

**差分なし**。

#### セクション 2: Command Lists

| 項目 | 影式現行 | LAM 4.0.1 | 差分種別 |
|------|---------|-----------|---------|
| A. Allow List — Testing | `pytest`, `pytest -v`, `pytest --tb=short` | `pytest`, `npm test`, `go test` | 影式は pytest 特化、LAM は汎用 |
| A. Allow List — Linting | `ruff check`, `ruff format --check` あり | なし | 影式固有追加（維持すべき） |
| A. Allow List — Package Info | `pip list`, `pip show` | `npm list`, `pip list`, `gem list` | 影式は pip 特化、LAM は汎用 |
| B. Deny List — Build/Run | `python main.py`, `python -m kage_shiki` | `npm start`, `npm run build`, `python main.py` | 影式固有カスタマイズ |
| B. Deny List — Linting (Write) | `ruff check --fix`, `ruff format` あり | なし | 影式固有追加 |
| B. Deny List — Package Install | `pip install`, `pip uninstall` あり | なし | 影式固有追加 |

#### セクション 3〜4: Automation Workflow, Emergency Stop

**差分なし**。

#### セクション 5: Hooks-Based Permission System (v4.0.0) — LAM 4.0.1 で新規追加

影式現行には存在しない。LAM 4.0.1 で以下の大規模セクションが追加:

- **多層権限モデル**: Layer 0（憲法的プロンプティング）→ Layer 1（settings.json）→ Layer 2（PreToolUse hook）
- **PG/SE/PM 権限等級**: ファイルパスベースの動的判定
- **PostToolUse による自動記録**: TDD パターン検出、ドキュメント同期フラグ、ループログ
- **Stop hook による自律ループ制御**: Green State 判定、反復上限、コンテキスト圧迫検出

#### セクション 6: Recommended Security Tools — LAM 4.0.1 で新規追加

影式現行には存在しない。LAM 4.0.1 で以下が追加:

- Anthropic 公式ツール（security-guidance plugin, claude-code-security-review, Claude Code Security）
- 依存脆弱性スキャン（npm audit, pip-audit, safety, govulncheck）
- CI/CD 統合例（GitHub Actions）

---

### 99_reference_generic.md

#### セクション B: Phase-by-Phase Generic Example

| 項目 | 影式現行 | LAM 4.0.1 | 差分種別 |
|------|---------|-----------|---------|
| 各 Phase の見出し | `Planning`, `TDD Cycle`, `Periodic Auditing`, `Release/Ops` | `[PLANNING]`, `[BUILDING]`, `[AUDITING]`, `[RELEASE]` のモードタグ付き | **LAM 4.0.1 で微修正**。フェーズモードの明示 |

#### セクション D: Tiny "Starter Kit"

| 項目 | 影式現行 | LAM 4.0.1 | 差分種別 |
|------|---------|-----------|---------|
| docs/internal/ のファイル番号 | `00..07` | `00_PROJECT_STRUCTURE .. 07_SECURITY_AND_AUTOMATION` | **LAM 4.0.1 で明確化**。ファイル名を明示 |

他のセクション（A, C）は差分なし。

---

### LAM 4.0.1 で新規追加されたファイル

LAM 4.0.1 の `docs/internal/` には影式現行と同じ 9 ファイル（00〜07 + 99）のみ存在し、新規ファイルの追加はない。

### 現行にのみ存在するファイル

| ファイル | 内容 | LAM 4.0.1 での対応 |
|---------|------|-------------------|
| `08_SESSION_MANAGEMENT.md` | セッション状態保存・復元、Save/Load コマンド体系、コンテキスト残量管理、Context Compression | LAM テンプレートには存在しない。CLAUDE.md の Context Management セクションに基本方針のみ記載。影式が独自に詳細化したもの |
| `09_SUBAGENT_STRATEGY.md` | Subagent 運用戦略、委任判断基準、並列実行パターン、モデル選択ガイド、出力統合フォーマット | LAM テンプレートには存在しない。`lam-orchestrate-design.md`（specs）に設計書として存在するが、internal ドキュメントとしての運用戦略は影式独自 |

**判断**: 両ファイルとも影式の運用で有用性が実証されているため維持すべき。ただし 09 は LAM 4.0.1 の `lam-orchestrate-design.md` v3.0.0 の内容と整合を取る必要がある。

---

## docs/specs/ LAM テンプレート側の新規仕様

### 影式に適用すべきもの

| ファイル | 内容 | 適用理由 |
|---------|------|---------|
| **v4.0.0-immune-system-requirements.md** | v4.0.0 免疫系の要件定義書。5つの柱（権限等級、ループ統合、TDD内省、ドキュメント自動追従、収束条件）の User Story、Problem Statement、FR、3 Agents 分析 | v4.0.0 移行の根拠文書。全柱の要件が網羅されている |
| **v4.0.0-immune-system-design.md** | v4.0.0 の設計書。Hook 設計（PreToolUse/PostToolUse/Stop/PreCompact）、モデルルーティング、Wave 0〜4 の詳細設計 | 実装の設計仕様として必須。影式への hooks 導入の具体的な実装方針 |
| **green-state-definition.md** | Green State 5条件（テスト全パス、lint全パス、Issue全解決、仕様差分ゼロ、セキュリティチェック）の詳細定義。MVP vs 完全実装 | Stop hook の収束条件。影式で自動ループを導入する際に必須 |
| **evaluation-kpi.md** | 運用 KPI 定義（K1: タスク完了率、K2: 平均ループイテレーション、K3: フック介入率、K4: コンテキスト枯渇率、K5: 同一Issue再発率）。Tier 1/2 の区分、`/daily` 集計テンプレート | 自動ループの運用品質を定量評価するための基盤。影式でも `/daily` に KPI セクションを追加すべき |
| **loop-log-schema.md** | ループログの JSON/テキストスキーマ。convergence_reason、iteration メタデータ、deferred_items の定義 | KPI 計測のデータソース。ループ統合導入時に必須 |
| **doc-writer-spec.md** | doc-writer エージェントの実装仕様。Doc Sync モード、仕様策定モード、`/ship` との連携フロー、PostToolUse hook との連携 | ドキュメント自動追従（柱4）の実装仕様。影式の `/ship` 強化に必要 |
| **v3.9.0-improvement-adoption.md** | v3.9.0 で採用した改善項目（V1〜V6）。`/ship`, `/full-review`, BUILDING チェックリスト、仕様同期ルール、SSOT 3層、AUDITING 整合性チェック | 影式は既にこれらの多くを独自に実装済みだが、テンプレート側の正式定義として参照すべき |

### 影式には不要なもの（LAM開発用）

| ファイル | 内容 | 不要判断の理由 |
|---------|------|--------------|
| **feat-v4.0.0-immune-system.md** | v4.0.0 の要件分析**中間成果物**（requirement-analyst サブエージェントの出力）。正式版は `v4.0.0-immune-system-requirements.md` | 中間成果物であり、正式要件定義書と内容が重複。requirements.md を使用すれば本ファイルは不要 |
| **lam-orchestrate-design.md** | lam-orchestrate Skill の設計書 v3.0.0。3層アーキテクチャ（Coordinator/Dispatcher/Workers）、Agent 定義テンプレート、Wave 実行フロー、Agent Teams 将来計画 | LAM フレームワーク自体の orchestration 設計書。影式は利用者であり、この設計を変更する必要はない。ただし 09_SUBAGENT_STRATEGY.md との整合確認に参照する |
| **ui-lam-slides.md** | LAM 概念説明スライド（reveal.js）の UI 仕様書。FR-001〜FR-006、デザイン仕様 | LAM のオンボーディング資料の仕様。影式プロジェクト固有の成果物ではない |
| **ultimate-think.md** | ultimate-think スキルの機能仕様書。AoT + Three Agents + Reflection を統合した思考スキル。Phase 0 Grounding、Level 1-3 の適応的深度制御、アンカーファイル管理 | スキルの仕様書であり、影式が利用する分には仕様を理解すれば十分。影式固有の specs には含めない |

---

## 移行時の注意事項

### 1. 影式固有カスタマイズの保護

以下は LAM テンプレートのマージ時に上書きしてはならない:

- **03_QUALITY_STANDARDS.md Section 6**: Python Coding Conventions（ruff 設定含む）
- **03_QUALITY_STANDARDS.md Section 7**: Building Defect Prevention（R-1〜R-6）
- **02_DEVELOPMENT_FLOW.md**: Wave 実績サマリー、Quality Rules Integration セクション
- **07_SECURITY_AND_AUTOMATION.md Section 2**: pytest/ruff 固有のコマンドリスト
- **00_PROJECT_STRUCTURE.md Section 1**: kage_shiki パッケージ構造
- **05_MCP_INTEGRATION.md Section 1**: Phase 1 MVP の状況記述
- **08_SESSION_MANAGEMENT.md**, **09_SUBAGENT_STRATEGY.md**: 影式独自ファイル

### 2. マージ戦略

推奨するマージ順序:

1. **00_PROJECT_STRUCTURE.md**: SSOT 3層アーキテクチャ（Section 3）を追加、.claude/ 配下構造を更新。ADR 命名規則の変更（日付→連番）は ADR で判断
2. **02_DEVELOPMENT_FLOW.md**: Automated TDD Introspection セクションと権限等級に基づく修正制御を追加。Dependency Traversal のツール名を更新
3. **07_SECURITY_AND_AUTOMATION.md**: Section 5（Hooks-Based Permission System）と Section 6（Recommended Security Tools）を追加
4. **03_QUALITY_STANDARDS.md**: 差分なし（影式固有セクションを維持）
5. **99_reference_generic.md**: フェーズモードタグの追加、Starter Kit のファイル名明示化

### 3. .claude/rules/ の同期

LAM 4.0.1 では以下のルールファイルが新規追加・変更されている:

| ファイル | 変更内容 |
|---------|---------|
| `permission-levels.md` | **新規**。PG/SE/PM 分類基準の詳細定義 |
| `upstream-first.md` | **新規**。Claude Code プラットフォーム機能の実装前仕様確認ルール |
| `core-identity.md` | Subagent 委任判断が削除され、権限等級（PG/SE/PM）セクションが追加 |
| `phase-rules.md` | BUILDING に TDD 品質チェック・仕様同期ルール・TDD 内省パイプライン追加。AUDITING を PG/SE/PM に基づく修正制御に変更 |
| `security-commands.md` | v4.0.0 ネイティブ権限モデルへの移行セクション追加 |
| `decision-making.md` | SSOT 参照の明記（`docs/internal/06_DECISION_MAKING.md` への参照） |

### 4. CLAUDE.md の差分

LAM 4.0.1 の CLAUDE.md と影式現行の差分:

| 項目 | 影式現行 | LAM 4.0.1 |
|------|---------|-----------|
| Identity | 「影式 (Kage-Shiki) プロジェクト」の記載あり | プロジェクト名なし（汎用） |
| Project Overview | 技術スタック表あり | なし |
| Project Scale | Medium | Medium to Large |
| 設計文書参照 | `docs/memos/middle-draft/` | なし |
| 概念説明スライド | `docs/slides/index.html` | `docs/slides/index.html` |

影式の CLAUDE.md は影式固有情報を含むため、LAM テンプレートとの差分は意図的なものが多い。

### 5. 段階的導入の推奨

v4.0.0 の全機能を一度に導入せず、以下の順序を推奨:

1. **Wave 0**: docs/internal/ の更新（本分析に基づくマージ）+ Green State 定義の策定
2. **Wave 1**: permission-levels.md の導入 + settings.json の更新 + phase-rules.md の AUDITING 修正制御変更
3. **Wave 2**: hooks の導入（PreToolUse, PostToolUse, Stop, PreCompact）+ `/full-review` のループ化
4. **Wave 3**: doc-writer エージェントの自律化 + `/ship` Doc Sync 強化
5. **Wave 4**: TDD 内省パイプライン（パターン記録 + 信頼度モデル）

各 Wave は独立してロールバック可能であること（設計原則 DP-10）。
