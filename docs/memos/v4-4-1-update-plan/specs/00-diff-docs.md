# docs/internal/ + CLAUDE.md + CHEATSHEET.md 差分分析（v4.0.1 → v4.4.1）

**作成日**: 2026-03-13
**目的**: LAM v4.4.1 テンプレートと影式現行版（LAM v4.0.1 移行済み）の差分を把握し、v4.4.1 移行計画の基礎資料とする

---

## 概要

LAM v4.4.1 は v4.0.1 からの漸進的アップデートであり、以下の主要な変更軸を持つ:

1. **TDD 内省パイプライン v2**: JUnit XML ベースのテスト結果読み取り、`/retro` 経由の人間判断フロー（閾値 3→2 に引き下げ）
2. **docs/artifacts/ の新設**: 中間成果物・監査レポート・TDD パターン・知見の統合格納先
3. **セッション管理の簡素化**: `/full-save`・`/full-load` を廃止し、`/quick-save`・`/quick-load` に統合
4. **Memory Policy の拡張**: Auto Memory の用途明確化、Subagent Persistent Memory、Knowledge Layer の追加
5. **セキュリティコマンドの deny/ask 分離**: 従来の単一 Deny List を deny（実行禁止）と ask（承認必須）に二分
6. **test-result-output.md の新設**: テスト結果ファイル出力の義務化（JUnit XML）
7. **リリースフローの汎用化**: デプロイ基準に Quality Gate Passed と Retrospective Done を追加
8. **ui-design-guide スキル**: 新規スキルの追加
9. **Subagent Persistent Memory**: `.claude/agent-memory/` による知見の自発的蓄積

---

## 1. ファイル単位の存在差異

### LAM v4.4.1 にのみ存在するファイル

| ファイル（LAM v4.4.1 側） | 内容 |
|:--------------------------|:-----|
| `.claude/rules/test-result-output.md` | テスト結果ファイル出力ルール（JUnit XML 形式での `.claude/test-results.xml` 出力を義務化） |
| `.claude/rules/auto-generated/README.md`（更新） | v2 ライフサイクルに大幅変更あり |
| `.claude/rules/auto-generated/trust-model.md`（更新） | v2 対応で全面書き換え |

### 影式にのみ存在するファイル

| ファイル | 内容 | LAM v4.4.1 での対応 |
|:---------|:-----|:--------------------|
| `docs/internal/08_SESSION_MANAGEMENT.md` | セッション状態保存・復元、Save/Load コマンド体系 | LAM テンプレートには存在しない。CLAUDE.md に簡略版が記載 |
| `docs/internal/09_SUBAGENT_STRATEGY.md` | Subagent 運用戦略、委任判断基準 | LAM テンプレートには存在しない |

**判断**: 両ファイルとも影式の運用で有用性が実証されているため維持すべき。ただし 08 はセッション管理の簡素化（`/full-save`・`/full-load` 廃止）に追従する必要がある。

---

## 2. docs/internal/ ファイル別差分

### 00_PROJECT_STRUCTURE.md

#### Section 1: Directory Structure

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| src/ 配下構造 | `kage_shiki/` パッケージ | `backend/` + `frontend/`（汎用） | 影式固有（維持） |
| tests/ 説明 | `テストコード (pytest)` | `テストコード` | 影式固有（維持） |
| docs/ 配下 | `memos/` のみ | `artifacts/`（knowledge/, audit-reports/, tdd-patterns/）、`slides/`、`daily/`、`memos/` を新設 | **v4.4.1 新規** |
| .claude/ 配下 | `hooks/`, `logs/`, `states/` | 上記に加え `commands/`, `rules/`, `skills/`, `agents/`, `agent-memory/`, `settings.json` を明示 | **v4.4.1 拡充** |

#### Section 2: Asset Placement Rules

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| A. Intermediate Reports | `docs/memos/` に保存 | `docs/artifacts/` に保存 | **v4.4.1 変更** |
| A. Knowledge | なし | `docs/artifacts/knowledge/`（/retro Step 4） | **v4.4.1 新規** |
| A. Audit Reports | なし | `docs/artifacts/audit-reports/`（/full-review） | **v4.4.1 新規** |
| A. TDD Patterns | なし | `docs/artifacts/tdd-patterns/`（パターン詳細記録） | **v4.4.1 新規** |
| C. ADR Naming | `NNNN-kebab-case-title.md` | 同一 + `（NNNN: 4桁連番、0001から）` の補足追加 | **v4.4.1 微修正** |
| D. Subagent Persistent Memory | なし | `.claude/agent-memory/<agent-name>/` | **v4.4.1 新規** |
| D→E. State Management | Section D | Section E に移動（D に Subagent Memory 挿入のため） | **v4.4.1 構造変更** |
| E. SESSION_STATE.md | `/full-load` で復元 | `/quick-load` で復元 | **v4.4.1 変更**（セッション管理簡素化） |

#### Section 3: SSOT 3層アーキテクチャ

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| 用語注意 Note | なし | Permission Layer 0/1/2 との混同防止注記を追加 | **v4.4.1 新規** |
| 情報層 2 の詳細 | hooks のみ | `commands/`, `hooks/`, `agents/`, `skills/` を明示 | **v4.4.1 拡充** |
| セクション番号 | 番号なし（`## SSOT 3層アーキテクチャ`） | `## 3.`（番号付き） | **v4.4.1 微修正** |
| 層の名称 | 「上位層」「下位層」 | 「情報層 1」「情報層 2」「情報層 3」 | **v4.4.1 明確化** |

#### Section 4: File Naming Conventions

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| Files (Code) | `Python: snake_case.py` のみ | JS/TS も例示（`PascalCase.tsx`, `camelCase.ts`） | テンプレート汎用化 |

---

### 01_REQUIREMENT_MANAGEMENT.md

**差分なし。** 影式現行と LAM v4.4.1 は完全に同一。

---

### 02_DEVELOPMENT_FLOW.md

#### Phase 1: Pre-Flight Impact Analysis

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| 冒頭文 | `Phase 1 (設計) および Phase 2 (実装)` | `Phase 1 (設計)、Phase 2 (実装)、および Phase 3 (定期監査)` | **v4.4.1 微修正** |
| Step 6: Implementation Plan | `implementation_plan.md` を作成、承認必須 | `/planning` の承認ゲートフロー、`docs/tasks/{feature_name}-tasks.md` に保存 | **v4.4.1 変更** |

#### Phase 2: TDD & Implementation Cycle

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| テスト環境 Note | `pytest` を使用する旨の Note あり | なし | 影式固有（維持すべき） |
| Step 1: 進捗管理 | `task.md` を使用 | `docs/tasks/{feature_name}-tasks.md` を使用 | **v4.4.1 変更** |
| Step 5: 検証結果パス | `docs/memos/walkthrough-<feature>.md` | `docs/artifacts/walkthrough-<feature>.md` | **v4.4.1 変更**（artifacts 移行） |
| Step 5: 必須/推奨 | `必須とする` | `推奨する` | **v4.4.1 緩和** |
| **Automated TDD Introspection** | v4.0.0（tdd-patterns.log 記録、3回閾値、`/pattern-review` 承認） | **v2**（JUnit XML 読み取り、2回閾値、`/retro` 内で分析、FAIL→PASS 遷移検出時に `/retro` 推奨） | **v4.4.1 大幅変更** |

##### TDD Introspection v1 → v2 の主要変更点

| 観点 | v1（影式現行） | v2（LAM v4.4.1） |
|:-----|:--------------|:-----------------|
| データソース | `tool_response.exitCode`（実際は動作せず） | `.claude/test-results.xml`（JUnit XML） |
| 閾値 | 3回 | 2回 |
| 分析タイミング | 自動（PostToolUse 内） | `/retro` 実行時（人間判断） |
| ルール候補承認 | `/pattern-review` | `/retro` Step 2.5 |
| パターン詳細記録先 | `docs/memos/tdd-patterns/` | `docs/artifacts/tdd-patterns/` |
| FAIL→PASS 遷移通知 | なし | systemMessage で `/retro` 推奨 |

#### Phase 3: Periodic Auditing

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| 権限等級参照先 | `.claude/rules/permission-levels.md` を直接記載 | 同内容 + `詳細は〜を参照` 形式 | 差分なし（実質同一） |

#### Wave-Based Development

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| 全セクション | あり | **全削除** | **v4.4.1 で削除** |

影式現行に存在する Wave-Based Development セクション（Wave 定義、選定基準、実績サマリー）、Advanced Workflows セクション（`/ship`, `/full-review`, `/wave-plan`, `/retro`）、Quality Rules Integration セクションが LAM v4.4.1 では全て削除されている。

**判断**: Wave-Based Development と Quality Rules Integration は影式固有の運用実績と品質ルールマッピングであり、維持すべき。Advanced Workflows は CHEATSHEET.md やコマンド定義に委譲された可能性があるが、02 内での参照価値は高いため要検討。

---

### 03_QUALITY_STANDARDS.md

#### Section 1-5: 設計原則〜コード明確性

**差分なし。** 影式現行と LAM v4.4.1 は完全に同一。

#### Section 6 (影式) / 不在 (LAM)

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| Python Coding Conventions | Section 6 にあり（PEP 8, Type Hints, ruff, Docstrings） | **なし** | 影式固有（維持すべき） |

#### Section 7 (影式) / 不在 (LAM)

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| Building Defect Prevention | Section 7 にあり（R-1〜R-6 一覧） | **なし** | 影式固有（維持すべき） |

#### Section 8 (影式) / Section 6 (LAM)

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| Technology Trend Awareness | 同一内容 | 同一内容 | 差分なし |

---

### 04_RELEASE_OPS.md

#### Section 1: Deployment Criteria

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| Performance Check | 個別チェック項目として記載 | **Quality Gate Passed** に統合（汎用化） | **v4.4.1 変更** |
| Retrospective Done | なし | `/retro` 実施済みを追加 | **v4.4.1 新規** |
| HTML コメント | `<!-- Phase 2b 以降でパッケージング方法... -->` | なし | 影式固有メモ |

#### Section 2: Release Flow

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| ステップ名 | Staging Verification → Backup → Deploy → Smoke Test | Verification → Backup → Release → Post-Release Check | **v4.4.1 汎用化** |
| 各ステップ説明 | 具体的（Blue/Green, Canary 等） | 汎用的（「プロジェクトの性質に応じた検証」） | **v4.4.1 汎用化** |

#### Section 3: Emergency Protocols

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| Post-Mortem 記録先 | `docs/adr/` | `docs/artifacts/` + アーキテクチャ判断時は `docs/adr/` | **v4.4.1 変更** |

#### Section 4: Versioning

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| PATCH 説明 | `後方互換性のあるバグ修正` | `後方互換性のあるバグ修正、ドキュメント修正、内部改善` | **v4.4.1 拡張** |

---

### 05_MCP_INTEGRATION.md

#### Section 1: MCP Servers

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| Phase 1 MVP Note | `MCP サーバーは未導入` の Note あり | なし | 影式固有（維持 or 更新） |
| 各サーバー表記 | `Phase 2 以降で検討` | `Optional` | テンプレート汎用化 |
| File System (Read) Allow List 内 find | あり | v4.3.1 で ask に移動の注記 | **v4.4.1 変更** |
| Heimdall Integration Rule | `docs/memos/` への書き出し | `docs/artifacts/` への書き出し | **v4.4.1 変更** |

#### Section 2-5

**差分なし。**

#### Section 6: MEMORY.md Policy

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| 内容 | 同一 | 同一 | 差分なし |

---

### 06_DECISION_MAKING.md

**差分なし。** 影式現行と LAM v4.4.1 は完全に同一（Section 1〜5 全て）。

---

### 07_SECURITY_AND_AUTOMATION.md

#### Section 2: Command Lists

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| A. Allow List — File System | `find` を含む | `find` を除外（v4.3.1 で ask に移動） | **v4.4.1 変更** |
| A. Allow List — Testing | `pytest -v`, `pytest --tb=short` も列挙 | `pytest`, `npm test`, `go test` のみ | テンプレート汎用化 |
| A. Allow List — Linting | `ruff check`, `ruff format --check` | なし | 影式固有（維持すべき） |
| A. Allow List — Package Info | `pip list`, `pip show` | `npm list`, `pip list` | テンプレート汎用化 |
| A. Allow List — Process Info | `ps`, `top (batch mode)` | `ps` のみ | **v4.4.1 変更** |
| B. Deny List 構造 | 単一 Deny List（B） | **B-1: Deny List（実行禁止）+ B-2: Approval Required（承認必須）に分離** | **v4.4.1 大幅変更** |
| B-1. Deny List | なし（B に一括） | `rm`, `mv`, `chmod/chown`, `apt/brew/systemctl`, `find -delete/-exec rm/-exec chmod` | **v4.4.1 新規** |
| B-2. Approval Required | なし（B に一括） | `cp/touch/mkdir`, `find`, `git push/commit/merge`, `curl/wget`, `npm start/python main.py/make` | **v4.4.1 新規** |
| B. Linting (Write) | `ruff check --fix`, `ruff format` あり | なし | 影式固有（維持すべき） |
| B. Package Install | `pip install`, `pip uninstall` あり | なし | 影式固有（維持すべき） |
| B. Build/Run | `python -m kage_shiki` あり | `npm start`, `npm run build`, `python main.py`, `make` | テンプレート汎用化 |
| Permission Layer Note | なし | Layer 0/1 の関係説明 Note を追加 | **v4.4.1 新規** |

#### Section 3: Automation Workflow

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| v4.0.0 注記 | なし | Section 5 の多層権限モデルへの参照注記を追加 | **v4.4.1 新規** |
| Decide 項目 | `SafeToAutoRun: true/false` | `Allow List に含まれる / 含まれない` | **v4.4.1 簡素化** |

#### Section 5: Hooks-Based Permission System

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| 多層モデル表 | なし | Permission Layer 0/1/2 テーブルを新設 | **v4.4.1 新規** |
| 用語注意 Note | なし | 00_PROJECT_STRUCTURE.md の情報層との混同防止注記 | **v4.4.1 新規** |
| deny/ask 関係 Note | なし | Section 2 B-1/B-2 との関係説明 | **v4.4.1 新規** |
| PreToolUse 詳細 | 影式固有パス（`pyproject.toml`, `src/kage_shiki/`, `config/`）を含む | 汎用パスのみ（`docs/specs/`, `.claude/rules/` 等） | 影式固有（維持すべき） |
| PostToolUse 詳細 | 3項目（TDD パターン、doc-sync-flag、ループログ） | 同一 | 差分なし（実質同一） |
| Stop Hook 詳細 | Green State G1-G5 | 同一 | 差分なし |

#### Section 6: Recommended Security Tools

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| 影式固有ツール列 | `影式での利用` 列あり（ruff, pip-audit, safety, bandit） | Anthropic 公式ツール + 言語別スキャンツール + CI/CD 統合例 | **v4.4.1 大幅拡充** |

---

### 99_reference_generic.md

#### Section B: Phase-by-Phase Generic Example

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| フェーズモードタグ | 独立セクションとして記載 | 各 Phase 見出しに `[PLANNING]` 等を付与（inline 化） | **v4.4.1 変更** |
| フェーズモードタグセクション | あり（独立） | 削除（各 Phase に統合） | **v4.4.1 変更** |

#### Section D: Tiny "Starter Kit"

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| docs/internal/ ファイル | `00..07` | `00_PROJECT_STRUCTURE .. 07_SECURITY_AND_AUTOMATION` | **v4.4.1 明確化** |

他のセクション（A, C）は差分なし。

---

## 3. CLAUDE.md 差分

### 変更セクション

#### Identity

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| プロジェクト名 | `影式 (Kage-Shiki)` を明記 | `本プロジェクト`（汎用） | 影式固有（維持） |
| Project Scale | `Medium` | `Medium to Large` | テンプレート汎用化 |

#### Hierarchy of Truth

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| Architecture 参照範囲 | `docs/internal/`（SSOT: 00〜09, 参考: 99） | `docs/internal/00-07`（SSOT） | **v4.4.1 変更**（08, 09 は LAM テンプレートに存在しない）。**影式は 00〜09 を維持**（08, 09 は影式固有ファイル） |

#### Execution Modes

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| `/auditing` ガードレール | `PM級修正禁止（PG/SE級は許可）` | `PG/SE修正可、PM指摘のみ` | 同一内容、表現が微妙に異なる |

#### References

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| 設計文書行 | `docs/memos/middle-draft/` を含む | なし（行自体削除） | 影式固有（維持） |
| 概念説明スライド | `docs/slides/index.html`（将来作成予定） | `docs/slides/index.html` | 影式固有注記 |

#### Project Overview

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| セクション全体 | 技術スタックテーブルあり | **セクション自体なし** | 影式固有（維持） |

#### Context Management

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| セーブ/ロード | `/quick-save`, `/quick-load`, `/full-save`, `/full-load` の4種 | `/quick-save`, `/quick-load` の2種 + git commit は `/ship` | **v4.4.1 大幅変更** |
| `/quick-save` 内容 | SESSION_STATE.md のみ | SESSION_STATE.md + ループログ + Daily 記録 | **v4.4.1 拡充** |
| `/quick-load` 内容 | SESSION_STATE.md のみ読込 | SESSION_STATE.md 読込 + 関連ドキュメント特定 + 復帰サマリー | **v4.4.1 拡充** |

#### Memory Policy

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| セクション名 | `MEMORY.md Policy` | `Memory Policy` | **v4.4.1 変更** |
| Auto Memory | Subagent の役割ノウハウ蓄積のみ | ビルドコマンド、デバッグ知見、ワークフロー習慣など**作業効率に関する学習** | **v4.4.1 拡張**（用途が広がった） |
| Subagent Persistent Memory | なし | `.claude/agent-memory/<agent-name>/` での知見蓄積 | **v4.4.1 新規** |
| Knowledge Layer | なし | `docs/artifacts/knowledge/`（/retro Step 4） | **v4.4.1 新規** |
| 参照先 | `docs/internal/05_MCP_INTEGRATION.md` Section 6 | セクション内に自己完結 | **v4.4.1 変更** |

#### Initial Instruction

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| プロジェクト名 | `影式 (Kage-Shiki) プロジェクトの` を含む | なし（汎用） | 影式固有（維持） |

---

## 4. CHEATSHEET.md 差分

### タイトル・はじめに

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| タイトル | `影式 (Kage-Shiki) チートシート` | `Living Architect Model チートシート` | 影式固有（維持） |
| 概念説明スライド参照 | `docs/slides/index.html`（将来作成予定） | `docs/slides/index.html` + QUICKSTART.md リンク追加 | **v4.4.1 拡充** |

### プロジェクト技術スタック

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| セクション全体 | あり（Python 3.12+ 等） | **セクション自体なし** | 影式固有（維持） |

### ディレクトリ構造

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| logs/ 説明 | `permission.log, loop-*.json` | `permission.log, loop-*.txt` | **v4.4.1 変更**（.json → .txt） |
| agent-memory/ | なし | なし（ディレクトリ構造には未記載だが CLAUDE.md で言及） | — |
| CLAUDE.md 説明 | `憲法（コア原則 + 技術スタック）` | `憲法（コア原則のみ）` | **v4.4.1 変更** |
| docs/memos/middle-draft/ | あり | なし | 影式固有（維持） |

### Rules ファイル一覧

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| `core-identity.md` 説明 | `Living Architect 行動規範 + 権限等級サマリー` | `Living Architect 行動規範`（権限サマリー言及なし） | **v4.4.1 微修正** |
| `security-commands.md` 説明 | `コマンド安全基準（Layer 0/1/2）` | `コマンド安全基準（Allow/Deny List）` | **v4.4.1 微修正** |
| `building-checklist.md` | あり（影式固有） | **なし** | 影式固有（維持） |
| `test-result-output.md` | なし | **新規追加** | **v4.4.1 新規** |
| `upstream-first.md` 説明 | `プラットフォーム仕様優先原則` | `上流仕様優先原則（プラットフォーム機能の実装前確認）` | **v4.4.1 微修正** |

### 権限等級（PG/SE/PM）

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| PreToolUse hook 詳細 | あり（パスベース判定、permission.log 記録、誤判定率計測） | あり（同一構造だがパス例が汎用的） | 差分なし |

### セッション管理コマンド

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| コマンド数 | 4種（quick-save/load, full-save/load） | **2種**（quick-save/load のみ） | **v4.4.1 大幅変更** |
| `/quick-save` 内容 | `SESSION_STATE.md のみ` | `SESSION_STATE.md + ループログ + Daily` | **v4.4.1 拡充** |
| `/quick-load` 内容 | `SESSION_STATE.md のみ` | `SESSION_STATE.md + 関連ドキュメント特定` | **v4.4.1 拡充** |
| `/full-save` | あり（commit + push + daily、約10%） | **削除** | **v4.4.1 削除** |
| `/full-load` | あり（状態確認 + 詳細報告、2-3%） | **削除** | **v4.4.1 削除** |
| コミット方法 | `/full-save` に含む | `/ship` を使用 | **v4.4.1 変更** |
| StatusLine Python バージョン | `要 Python 3.x` | `要 Python 3.8+` | **v4.4.1 明確化** |

### サブエージェント

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| Memory 列 | なし | **Memory 列を追加**（`auto` = agent-memory に蓄積） | **v4.4.1 新規** |
| `code-reviewer` Memory | — | `auto` | **v4.4.1 新規** |

### スキル

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| `ultimate-think` | あり | **削除** | **v4.4.1 削除**（lam-orchestrate に統合の可能性） |
| `lam-orchestrate` 説明 | `タスク分解・並列実行の自動調整` | `タスク分解・並列実行 + 構造化思考（AoT + Three Agents）` | **v4.4.1 拡充** |
| `ui-design-guide` | なし | **新規追加** | **v4.4.1 新規** |

### ワークフローコマンド

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| `/full-review` | 引数なし | `<対象>` 引数追加 | **v4.4.1 変更** |
| `/release` | なし | **新規追加**（`<version>` 引数） | **v4.4.1 新規** |
| `/wave-plan` | 補助コマンドに記載 | **ワークフローコマンドに昇格** + `[N]` 引数 | **v4.4.1 変更** |
| `/retro` | 補助コマンドに記載 | **ワークフローコマンドに昇格** + `[wave|phase]` 引数 | **v4.4.1 変更** |

### 補助コマンド

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| `/focus` | あり | **削除** | **v4.4.1 削除** |
| `/daily` | あり | **削除** | **v4.4.1 削除**（`/quick-save` に統合の可能性） |
| `/adr-create` | あり | **削除** | **v4.4.1 削除** |
| `/security-review` | あり | **削除** | **v4.4.1 削除** |
| `/impact-analysis` | あり | **削除** | **v4.4.1 削除** |
| `/wave-plan` | あり（影式固有） | ワークフローに移動 | **v4.4.1 移動** |
| `/retro` | あり（影式固有） | ワークフローに移動 | **v4.4.1 移動** |
| `/pattern-review` | あり | あり | 差分なし |
| `/project-status` | フェーズコマンドに記載 | 補助コマンドに移動 | **v4.4.1 移動** |

### 状態管理

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| `docs/artifacts/knowledge/` | なし | **新規追加** | **v4.4.1 新規** |
| `.claude/agent-memory/` | なし | **新規追加** | **v4.4.1 新規** |

### 日常ワークフロー

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| セクション全体 | あり（一日の開始〜割り込み・中断まで7パターン） | **セクション自体なし** | 影式固有（維持検討）|

### AoT クイックガイド

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| Atom テーブル形式 | テーブル記法で記載 | コードブロック記法で記載 | **v4.4.1 微修正** |
| 並列可否列 | `並列可否` | `並列可否(任意)` | **v4.4.1 微修正** |

### 参照ドキュメント (SSOT)

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| 08_SESSION_MANAGEMENT.md | あり | **なし** | 影式固有 |
| 09_SUBAGENT_STRATEGY.md | あり | **なし** | 影式固有 |
| 99_reference_generic.md | なし | あり | **v4.4.1 追加** |

### クイックリファレンス

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| 次のセッション | `/quick-load` or `/full-load` | `/quick-load` のみ | **v4.4.1 変更** |
| 変更をコミット | `/ship` | なし | 影式固有（維持） |
| 設計中間文書 | `docs/memos/middle-draft/` | なし | 影式固有（維持） |

---

## 5. .claude/rules/ 差分

### core-identity.md

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| Subagent 委任判断 | テーブルあり | 削除 | v4.0.1 で既に削除済み（差分なし） |
| Context Compression | `docs/tasks/` または `docs/memos/` | `docs/tasks/` または `docs/artifacts/` | **v4.4.1 変更** |

### decision-making.md

**差分なし。** 影式現行と LAM v4.4.1 は完全に同一。

### permission-levels.md

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| 冒頭説明 | SSOT としての本ファイルの位置付けを詳述 | 簡潔な説明 | **v4.4.1 簡素化** |
| PG級例 | 同一 | `テスト失敗の自明な修正（型ミスマッチ等）` を追加 | **v4.4.1 拡充** |
| SE級例 | 同一 | `内部関数の名前変更`、`ログ出力の追加・修正`、`コメントの追加・修正` を追加 | **v4.4.1 拡充** |
| PM級例 | 同一 | `フェーズの巻き戻し` を追加 | **v4.4.1 追加** |
| ファイルパスベース分類 | `docs/internal/` → PM、`src/kage_shiki/` → SE、`pyproject.toml` → PM、`config/` → SE | `docs/internal/` → なし（削除）、影式固有パス（`src/kage_shiki/`, `pyproject.toml`, `config/`）→ なし | **v4.4.1 変更**（影式固有パスが削除） |
| SSOT 参照 | なし | `docs/specs/v4.0.0-immune-system-requirements.md` Section 5.1 等を追加 | **v4.4.1 追加** |
| 迷った場合の例 | 影式固有例を含む | テンプレート汎用例 | テンプレート汎用化 |

### phase-rules.md

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| PLANNING — 許可 | `docs/memos/` | `docs/artifacts/` を追加 | **v4.4.1 変更** |
| BUILDING — TDD 品質チェック | `building-checklist.md` 参照あり | `プロジェクト固有ルールを R-5 以降に追加可` の注記 | **v4.4.1 変更** |
| BUILDING — TDD 内省パイプライン | v4.0.0（PostToolUse 自動、3回閾値、`/pattern-review`） | **v2**（JUnit XML、2回閾値、`/retro` Step 2.5） | **v4.4.1 大幅変更** |
| BUILDING — Phase 完了判定 | L-4 由来のスモークテスト（影式固有） | なし | 影式固有（維持すべき） |
| AUDITING — Green State 5条件 | テーブルで対応を記載 | なし | 影式固有（維持すべき） |
| AUDITING — A-1〜A-4 | 明示的に記載 | なし | 影式固有（維持すべき） |
| AUDITING — `/full-review` 参照 | あり | なし | 影式固有 |

### security-commands.md

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| Allow List — Python カテゴリ | `python`, `python -m pytest`, `python -m ruff`, `python -c`, `pip`, `pyenv` | なし | 影式固有（維持すべき） |
| 高リスクコマンドの名称 | `高リスクコマンド（Layer 0: 承認必須）` | 2つに分離（`実行禁止コマンド（Layer 0: deny）` + `承認必須コマンド（Layer 0: ask）`） | **v4.4.1 大幅変更** |
| find の扱い | Allow List に含む | **ask**（通常検索）/ **deny**（破壊パターン）に分離 | **v4.4.1 変更** |
| ネイティブ権限モデル | `三層で管理` | `二層で管理`（Layer 0 を含めない表現） | **v4.4.1 微修正** |
| upstream-first.md | `docs.anthropic.com/en/docs/claude-code/` | `code.claude.com/docs/en/` | **v4.4.1 URL変更** |

### upstream-first.md

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| セクション名 | `Upstream First — プラットフォーム仕様優先原則` | `Upstream First（上流仕様優先）原則` | **v4.4.1 微修正** |
| 確認先 URL | `docs.anthropic.com/en/docs/claude-code/` | `code.claude.com/docs/en/` | **v4.4.1 URL 変更** |
| WebFetch フォールバック注意 | `コンテキスト消費を避ける` | `無応答リスクのため` | **v4.4.1 変更** |
| Wave 開始前の一括すり合わせ | 推奨のみ | 推奨 + **対象範囲の明示**（更新すべき/不要なものの判断基準） | **v4.4.1 拡充** |

### auto-generated/README.md

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| ライフサイクル | 4ステップ（PostToolUse → tdd-patterns.log → draft → /pattern-review 承認） | **全面書き換え**（JUnit XML → PostToolUse → FAIL→PASS 遷移 → /retro → 人間承認） | **v4.4.1 大幅変更** |
| 閾値 | 3回 | 2回 | **v4.4.1 変更** |
| ルール寿命管理 | `/daily` で棚卸し通知 | `/quick-save (Daily記録)` で棚卸し通知 | **v4.4.1 変更** |
| 参照セクション | なし | 仕様書（`docs/specs/tdd-introspection-v2.md`）、テスト結果ルール、パターンログ等の参照を追加 | **v4.4.1 追加** |

### auto-generated/trust-model.md

| 項目 | 影式現行 | LAM v4.4.1 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| 全体 | v1（手動照合ベース） | **v2 で全面書き換え**（JUnit XML ベース、FAIL→PASS 遷移、/retro 連携） | **v4.4.1 大幅変更** |
| データソース | 言及なし | PostToolUse hook が `.claude/test-results.xml`（JUnit XML）を読み取り | **v4.4.1 新規** |
| v1 非動作の記録 | なし | `exitCode が存在しないため動作していなかった（2026-03-13 判明）` | **v4.4.1 新規**（教訓記録） |
| 閾値テーブル | 4段階（1: 記録、2: 注意、3: 候補生成、3+: 承認待ち） | 2段階（FAIL→PASS: 記録、2回以上: /retro で提案） | **v4.4.1 簡素化** |
| パターン照合ロジック | MVP: 手動照合 / 完全実装: 将来 | /retro Step 2.5 での実施手順を具体的に記述 | **v4.4.1 具体化** |
| ルール候補フォーマット | テーブル形式（日時/テストファイル/失敗メッセージ） | テーブル形式（日付/テスト名/失敗内容）+ 推奨ルール文 + 適用範囲 | **v4.4.1 拡充** |
| 権限等級 | パターン記録: PG級、候補生成〜承認: PM級 | 同一 + 信頼度モデル自体の変更: PM級を明示 | **v4.4.1 追加** |

### test-result-output.md（LAM v4.4.1 新規）

影式現行には存在しない新規ルールファイル。

- テストフレームワーク導入時に JUnit XML 形式で `.claude/test-results.xml` を出力する設定を義務化
- Python (pytest)、JavaScript (Jest/Vitest)、Go、Rust の設定リファレンスを提供
- TDD 内省パイプライン v2 の基盤として必須

---

## 6. 影式固有の保持すべき内容

### docs/internal/ 内

1. **02_DEVELOPMENT_FLOW.md**: Wave 実績サマリー、Quality Rules Integration、テスト環境 Note（pytest）
2. **03_QUALITY_STANDARDS.md Section 6**: Python Coding Conventions（PEP 8, Type Hints, ruff, Docstrings）
3. **03_QUALITY_STANDARDS.md Section 7**: Building Defect Prevention（R-1〜R-6）
4. **07_SECURITY_AND_AUTOMATION.md Section 2**: pytest/ruff 固有コマンドリスト、`python -m kage_shiki` のビルド・ラン
5. **07_SECURITY_AND_AUTOMATION.md Section 5**: PreToolUse の影式固有パス（`pyproject.toml`, `src/kage_shiki/`, `config/`）
6. **07_SECURITY_AND_AUTOMATION.md Section 6**: 影式固有ツール列（ruff, pip-audit, safety, bandit）
7. **08_SESSION_MANAGEMENT.md**: セッション管理の詳細（ただしセッション管理簡素化に追従要）
8. **09_SUBAGENT_STRATEGY.md**: Subagent 運用戦略

### CLAUDE.md 内

9. **Identity**: `影式 (Kage-Shiki)` の名称と説明文
10. **Project Overview**: 技術スタックテーブル全体
11. **Hierarchy of Truth**: `SSOT: 00〜09` の範囲（08, 09 を含む）
12. **References**: `docs/memos/middle-draft/` の行
13. **Initial Instruction**: プロジェクト名修飾

### CHEATSHEET.md 内

14. **プロジェクト技術スタック**: テーブル全体
15. **building-checklist.md**: Rules 一覧への記載
16. **日常ワークフロー**: 7パターンの作業フロー
17. **クイックリファレンス**: `/ship`、設計中間文書

### .claude/rules/ 内

18. **building-checklist.md**: R-2〜R-11, S-2 の影式固有チェックリスト
19. **phase-rules.md**: Phase 完了判定（L-4 スモークテスト）、Green State 5条件対応表、A-1〜A-4
20. **permission-levels.md**: 影式固有パス分類（`src/kage_shiki/`, `pyproject.toml`, `config/`）

---

## 7. 移行時の注意点

### 1. TDD 内省パイプライン v1 → v2 の移行

最大の構造的変更。影響範囲:
- `.claude/rules/auto-generated/README.md`: ライフサイクル全面書き換え
- `.claude/rules/auto-generated/trust-model.md`: 全面書き換え
- `.claude/rules/phase-rules.md`: BUILDING セクションの TDD 内省パイプライン記述
- `docs/internal/02_DEVELOPMENT_FLOW.md`: Automated TDD Introspection セクション
- **新規**: `.claude/rules/test-result-output.md` の導入
- **新規**: `pyproject.toml` に `--junitxml=.claude/test-results.xml` 設定を追加
- **新規**: `.gitignore` に `.claude/test-results.xml` を追加

### 2. docs/artifacts/ ディレクトリの新設

複数ファイルに波及する変更:
- `docs/memos/tdd-patterns/` → `docs/artifacts/tdd-patterns/` に移動
- `docs/memos/walkthrough-*` → `docs/artifacts/walkthrough-*` に移動
- 監査レポートの保存先変更
- `/retro` Step 4 知見の保存先（`docs/artifacts/knowledge/`）
- 00_PROJECT_STRUCTURE.md、05_MCP_INTEGRATION.md、core-identity.md 等の参照先更新

### 3. セッション管理の簡素化

`/full-save` と `/full-load` を廃止し、`/quick-save`・`/quick-load` に統合する変更:
- CLAUDE.md の Context Management セクション更新
- CHEATSHEET.md のセッション管理コマンド更新
- 08_SESSION_MANAGEMENT.md の更新（影式固有ファイル）
- `/quick-save` の動作拡充（Daily 記録を含む）
- `/quick-load` の動作拡充（関連ドキュメント特定を含む）
- git commit 操作は `/ship` に完全委譲

### 4. セキュリティコマンドの deny/ask 分離

07_SECURITY_AND_AUTOMATION.md の Section 2 を大幅変更:
- 単一 Deny List → B-1 (deny) + B-2 (ask) に分離
- `find` の扱い変更（Allow → ask/deny に分離）
- Permission Layer 間の関係説明を追加
- 影式固有のコマンド（`ruff check --fix`, `pip install` 等）はどちらに配置するか要決定

### 5. Memory Policy の拡張

CLAUDE.md の Memory Policy セクションを大幅拡張:
- Auto Memory の用途を「Subagent ノウハウ限定」から「作業効率に関する学習」に拡張
- Subagent Persistent Memory（`.claude/agent-memory/`）の導入
- Knowledge Layer（`docs/artifacts/knowledge/`）の導入
- 三層の記憶メカニズム（Auto Memory / Persistent Memory / Knowledge Layer）の棲み分け

### 6. 影式固有パスの再設定

permission-levels.md から影式固有パスが削除されているため、マージ時に再追加が必要:
- `docs/internal/*.md` → PM（LAM v4.4.1 では削除されている）
- `src/kage_shiki/` → SE
- `pyproject.toml` → PM
- `config/` → SE

### 7. 公式 URL の変更

upstream-first.md、security-commands.md で Claude Code 公式ドキュメントの URL が変更:
- `docs.anthropic.com/en/docs/claude-code/` → `code.claude.com/docs/en/`

### 8. マージ戦略の推奨

前回（v4.0.1）と同様に **Template-First 戦略** を推奨:
1. LAM v4.4.1 テンプレートをベースとして採用
2. 影式固有カスタマイズ（Section 6 で列挙）を上乗せ
3. セッション管理簡素化と TDD 内省 v2 は構造的変更であり、影式側の 08_SESSION_MANAGEMENT.md も追従が必要
