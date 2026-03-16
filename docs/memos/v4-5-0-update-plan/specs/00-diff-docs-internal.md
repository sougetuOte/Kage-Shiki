# docs/internal/ + CLAUDE.md + CHEATSHEET.md 差分分析（v4.4.1 → v4.5.0）

**作成日**: 2026-03-16
**目的**: LAM v4.5.0 テンプレートと影式現行版（LAM v4.4.1 移行済み）の差分を把握し、v4.5.0 移行計画の基礎資料とする

---

## 概要

LAM v4.5.0 は v4.4.1 からの漸進的アップデートであり、以下の主要な変更軸を持つ:

1. **MAGI System の導入**: Three Agents Model のエージェント名を MELCHIOR / BALTHASAR / CASPAR に変更し、エヴァンゲリオン由来の命名体系を採用
2. **Reflection ステップの追加**: MAGI Debate（Step 1-3）完了後に全員で結論を検証する Step 4 を新設（1回限り）
3. **`/magi` スキルの導入**: AoT + MAGI Debate + Reflection を統合した構造化意思決定スキル
4. **`/clarify` スキルの導入**: 仕様書・設計書の曖昧さ・矛盾・欠落を検出する文書精緻化スキル
5. **planning-quality-guideline.md の新設**: Requirements Smells、RFC 2119、Design Doc チェックリスト、SPIDR 分割、WBS 100% Rule、Example Mapping
6. **code-quality-guideline.md の新設**: 重要度分類（Critical/Warning/Info）の定量的判断基準
7. **SSOT 3層アーキテクチャの再構成**: 情報層の方向を逆転（docs/internal/ を情報層 1 → CHEATSHEET.md を情報層 3）
8. **02_DEVELOPMENT_FLOW.md の汎用化**: 影式固有セクション（Wave, Advanced Workflows, Quality Rules Integration）が全削除
9. **03_QUALITY_STANDARDS.md の簡素化**: Python 固有セクション（Section 6, 7）と Technology Trend セクション番号変更

---

## 1. docs/internal/ ファイル別差分

### 00_PROJECT_STRUCTURE.md

#### Section 1: Directory Structure

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| src/ 配下構造 | `kage_shiki/` パッケージ（6サブモジュール記載） | `backend/` + `frontend/`（汎用） | 影式固有（維持） |
| tests/ 説明 | `テストコード (pytest)` | `テストコード` | 影式固有（維持） |
| docs/ 配下 | `artifacts/`（knowledge/, audit-reports/, tdd-patterns/）、`memos/` | 上記に加え `slides/`、`daily/` を明示 | **v4.5.0 新規** |
| .claude/ 配下 | `hooks/`, `logs/`, `states/`, `agent-memory/` | 上記に加え `commands/`, `rules/`, `skills/`, `agents/`, `settings.json` を明示 | **v4.5.0 拡充** |

#### Section 2: Asset Placement Rules

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| A. Knowledge | `docs/artifacts/knowledge/`（/retro Step 4） | 同一（v4.4.1 で導入済み） | 差分なし |
| A. Audit Reports | `docs/artifacts/audit-reports/`（/full-review） | 同一 | 差分なし |
| A. TDD Patterns | `docs/artifacts/tdd-patterns/` | 同一 + v2 ログ `.claude/tdd-patterns.log` 注記追加 | **v4.5.0 微修正** |
| A. Reference Materials | あり | 同一 | 差分なし |
| C. ADR Naming | `NNNN-kebab-case-title.md`（4桁連番、0001から） | 同一 | 差分なし |
| D. Subagent Persistent Memory | あり | 説明文拡充（「CLAUDE.md の指示に従いサブエージェントが自発的に書き込む」追加） | **v4.5.0 微修正** |

#### Section 3: SSOT 3層アーキテクチャ（大幅変更）

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| セクション番号 | `## SSOT 情報層アーキテクチャ` | `## 3. SSOT 3層アーキテクチャ` | **v4.5.0 変更** |
| 層の順序 | 情報層 1: CLAUDE.md → 情報層 2: .claude/ → 情報層 3: docs/internal/ | **情報層 1: docs/internal/ → 情報層 2: .claude/ → 情報層 3: CHEATSHEET.md** | **v4.5.0 大幅変更** |
| 情報層 1 の位置 | CLAUDE.md | docs/internal/（プロセス SSOT = What & Why） | **v4.5.0 大幅変更** |
| 情報層 2 の内容 | .claude/rules/, hooks/ | .claude/rules/, commands/, hooks/, agents/, skills/ を列挙 | **v4.5.0 拡充** |
| 情報層 3 | docs/internal/ | CHEATSHEET.md（クイックリファレンス）。情報層 3 は独自情報を持たない | **v4.5.0 大幅変更** |
| 図表形式 | テーブル形式 | **ASCII 矢印図**（参照・実装・要約の方向を視覚化） | **v4.5.0 変更** |
| 用語注意 Note | Permission Layer との混同防止注記あり | 同一趣旨で独立セクション化 | 差分なし（表現変更のみ） |

**重要**: v4.4.1 では CLAUDE.md が情報層 1（最高権限）だったが、v4.5.0 では docs/internal/ が情報層 1（最高権限）に昇格した。CHEATSHEET.md は情報層 3（要約専用、独自情報なし）に降格。影式現行の CLAUDE.md には Hierarchy of Truth で `docs/internal/` が User Intent に次ぐ第2位と定義されており、v4.5.0 の方向性と整合する。

#### Section 4: File Naming Conventions

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| Files (Code) | `Python: snake_case.py` のみ | JS/TS も例示（`PascalCase.tsx`, `camelCase.ts`） | テンプレート汎用化 |

---

### 01_REQUIREMENT_MANAGEMENT.md

#### Section E: Perspective Check

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| エージェント名 | `Affirmative / Critical / Mediator` （3 Agents） | **MELCHIOR / BALTHASAR / CASPAR**（MAGI System） | **v4.5.0 変更** |
| 批判者の表記 | `「Critical Agent」によるリスク指摘` | `BALTHASAR（批判者）によるリスク指摘` | **v4.5.0 変更** |
| /magi スキル | なし | `複雑な判断には /magi スキルの活用を推奨` | **v4.5.0 新規** |

#### Section F: Clarification（新規セクション）

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| `/clarify` スキル | なし | 仕様書ドラフト完成後に曖昧さ・矛盾・欠落を検出 | **v4.5.0 新規** |
| 曖昧修飾語排除 | なし | 「適切に」「必要に応じて」等を数値・条件に置換 | **v4.5.0 新規** |
| planning-quality-guideline 参照 | なし | `.claude/rules/planning-quality-guideline.md` を参照 | **v4.5.0 新規** |

#### Section 2: Definition of Ready

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| Unambiguous 条件 | `解釈の揺れがない` | `解釈の揺れがない。/clarify で精緻化済みであること` | **v4.5.0 変更** |

---

### 02_DEVELOPMENT_FLOW.md

#### Phase 1: Pre-Flight Impact Analysis

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| 冒頭文 | `Phase 1 (設計) および Phase 2 (実装)` | `Phase 1 (設計)、Phase 2 (実装)、および Phase 3 (定期監査)` | **v4.5.0 微修正** |
| Step 6 名称 | `Implementation Plan (Artifact)` | `Implementation Plan` | **v4.5.0 微修正** |
| Step 6 内容 | `docs/tasks/` に作成、承認必須 | `/planning` の承認ゲートフロー、`docs/tasks/` に保存 | **v4.5.0 変更** |

#### Phase 1: AoT フレームワーク → MAGI System 連携

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| セクション名 | `AoT フレームワークとの連携` | `MAGI System（構造化意思決定）との連携` | **v4.5.0 変更** |
| 参照先 | `.claude/agents/*` のみ | `/magi` スキル + `.claude/agents/*` | **v4.5.0 変更** |
| 表の内容 | `AoT 適用` 列 | `適用` 列（AoT + MAGI 合議を統合表記） | **v4.5.0 変更** |
| 参照先ドキュメント | `06_DECISION_MAKING.md` Section 5: AoT | `06_DECISION_MAKING.md`（セクション指定なし） | **v4.5.0 変更** |

#### Phase 1: 文書精緻化（/clarify）（新規サブセクション）

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| セクション全体 | なし | `/clarify` による仕様書・設計書の精緻化手順を新設 | **v4.5.0 新規** |
| 使用例 | — | `仕様書ドラフト完成後`、`設計書完成後`、`文書間横断チェック` | **v4.5.0 新規** |

#### Phase 2: TDD & Implementation Cycle

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| テスト環境 Note | `pytest` を使用する旨の Kage-Shiki Note あり | なし | 影式固有（維持すべき） |
| Step 5: 検証結果パス | `docs/artifacts/walkthrough-<feature>.md` | 同一 | 差分なし |
| Automated TDD Introspection v2 | v2 記述あり | v2 記述あり（微修正: `src/` 配下のファイル変更検知とドキュメント同期フラグ設定の記述追加） | **v4.5.0 微修正** |

#### Phase 3: Periodic Auditing

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| 権限等級詳細参照先 | 直接記載 | `詳細は .claude/rules/permission-levels.md を参照` を追加 | **v4.5.0 微修正** |

#### 影式固有セクション（Wave, Advanced Workflows, Quality Rules Integration）

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| Wave-Based Development | あり（Wave 定義、選定基準、実績サマリー） | **全削除** | v4.4.1 で既に削除済み |
| Advanced Workflows | あり（/ship, /full-review, /wave-plan, /retro） | **全削除** | v4.4.1 で既に削除済み |
| Quality Rules Integration | あり（TDD サイクルとルールのマッピング） | **全削除** | v4.4.1 で既に削除済み |

**判断**: v4.4.1 移行時点で「影式固有として維持」と判断済み。v4.5.0 でも変更なし。引き続き維持。

---

### 03_QUALITY_STANDARDS.md

#### Section 1-5: 設計原則〜コード明確性

**差分なし。** 影式現行と LAM v4.5.0 は完全に同一。

#### Section 6 (影式) / 不在 (LAM)

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| Python Coding Conventions | Section 6 にあり（PEP 8, Type Hints, ruff, Docstrings） | **なし** | 影式固有（維持すべき） |

#### Section 7 (影式) / 不在 (LAM)

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| Building Defect Prevention | Section 7 にあり（R-1〜R-6 一覧） | **なし** | 影式固有（維持すべき） |

#### Section 8 (影式) / Section 6 (LAM)

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| Technology Trend Awareness | Section 8 | Section 6（番号のみ変更） | 差分なし（内容同一） |

---

### 04_RELEASE_OPS.md

#### Section 1: Deployment Criteria

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| チェック項目構成 | Quality Gate Passed, No Critical Bugs, Retrospective Done, Documentation Updated | **All Tests Green（独立項目化）** + Quality Gate Passed（汎用化: 「プロジェクトが定めるリリース品質基準」）+ No Critical Bugs + Documentation Updated + Retrospective Done | **v4.5.0 変更** |
| All Tests Green | Quality Gate Passed に統合 | **独立チェック項目として分離** | **v4.5.0 変更** |
| HTML コメント | `<!-- Phase 2b 以降でパッケージング方法... -->` | なし | 影式固有メモ（維持 or 削除） |

#### Section 3: Emergency Protocols

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| Post-Mortem 記録先 | `docs/adr/` + `docs/artifacts/` | `docs/artifacts/` + アーキテクチャ判断時は `docs/adr/` | 表現変更のみ（実質同一） |

#### Section 2, 4

**差分なし。**

---

### 05_MCP_INTEGRATION.md

#### Section 1: MCP Servers

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| Phase 1 MVP Note | `MCP サーバーは未導入` の Note あり | なし（各サーバーに `Optional` 表記） | 影式固有（維持 or 更新） |
| 各サーバー表記 | `Phase 2 以降で検討` | `Optional` | テンプレート汎用化 |

#### Section 2-6

**差分なし。** 影式現行と LAM v4.5.0 は完全に同一。

---

### 06_DECISION_MAKING.md（大幅変更）

#### Section 1: Core Concept

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| ドキュメントタイトル | `Multi-Perspective Decision Making Protocol (The "Three Agents" Model)` | `Multi-Perspective Decision Making Protocol (The MAGI System / "Three Agents" Model)` | **v4.5.0 変更** |
| Agent 名: 推進者 | **Affirmative** / The Proponent | **MELCHIOR** / 科学者 (Affirmative / 推進者) | **v4.5.0 変更** |
| Agent 名: 批判者 | **Critical** / The Skeptic | **BALTHASAR** / 母 (Critical / 批判者) | **v4.5.0 変更** |
| Agent 名: 調停者 | **Mediator** / The Architect | **CASPAR** / 女 (Mediator / 調停者) | **v4.5.0 変更** |

#### Section 2: Execution Flow

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| Step 1 | Mediator が議題を提示 | CASPAR が議題を提示 | **v4.5.0 変更**（名称変更） |
| Step 2 例 | `Critical「セキュリティが不安だ」 -> Affirmative「では認証層を強化しよう」` | `BALTHASAR「〜」 -> MELCHIOR「〜」` | **v4.5.0 変更**（名称変更） |
| Step 3 | Mediator が最終決定 | CASPAR が最終決定 | **v4.5.0 変更**（名称変更） |

#### Section 3: Output Format

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| ラベル | `[Affirmative]`, `[Critical]`, `[Mediator]` | `[MELCHIOR]`, `[BALTHASAR]`, `[CASPAR]` | **v4.5.0 変更** |

#### Section 5: AoT

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| 5.4 ワークフロー名 | `AoT + Three Agents ワークフロー` | `AoT + MAGI ワークフロー` | **v4.5.0 変更** |
| Step 1-3 説明 | `Three Agents Debate（各 Atom について）` | `MAGI Debate（各 Atom について）` | **v4.5.0 変更** |
| Step 1-3 詳細 | `Affirmative / Critical / Mediator が議論` | `MELCHIOR / BALTHASAR が発散 → 議論 → CASPAR が収束` | **v4.5.0 変更** |
| **Step 4: Reflection** | **なし** | **新設**（全員で結論を検証。致命的な見落としがあれば修正。なければ確定。） | **v4.5.0 新規** |
| 旧 Step 4 → 新 Step 5 | Step 4: AoT Synthesis | **Step 5: AoT Synthesis**（番号ズレ） | **v4.5.0 変更** |
| 5.5 出力フォーマット | Affirmative/Critical/Mediator ラベル | MELCHIOR/BALTHASAR/CASPAR ラベル + **Reflection セクション追加** | **v4.5.0 変更** |

#### Section 6: Reflection（新規セクション）

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| セクション全体 | なし | **新設**: MAGI Debate 後の振り返りステップ | **v4.5.0 新規** |
| 6.1 目的 | — | 結論に致命的な見落としがないかの最終確認。Multi-Agent Reflexion (MAR) 研究に基づく | **v4.5.0 新規** |
| 6.2 ルール | — | 修正条件: 致命的な見落とし（セキュリティ、データ損失、仕様違反）のみ / Bikeshedding 防止 / 回数制限: 最大1回 | **v4.5.0 新規** |
| 6.3 出力フォーマット | — | 見落としなし: `致命的な見落とし: なし → 結論確定` / あり: `致命的な見落とし: [内容] → 結論修正: [内容]` | **v4.5.0 新規** |
| 6.4 参照 | — | Multi-Agent Reflexion (MAR) 論文リンク | **v4.5.0 新規** |

---

### 07_SECURITY_AND_AUTOMATION.md

#### Section 2: Command Lists

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| A. Allow List — File System | `find` 含まない（v4.3.1 で ask 移動済み） | `find` の v4.3.1 移動注記を追加 | **v4.5.0 微修正** |
| A. Allow List — Testing | `pytest` 等（影式固有） | `pytest`, `npm test`, `go test` | テンプレート汎用化 |
| A. Allow List — Linting | `ruff check`, `ruff format --check` | なし | 影式固有（維持すべき） |
| B-1 Deny List — find | `find -delete`, `find -exec rm`, `find -exec chmod`, `find -exec chown` | `find -delete`, `find -exec rm`, `find -exec chmod/chown`（表記簡素化） | **v4.5.0 微修正** |
| B-2 Approval Required — Network | `curl, wget, ssh, ping, nc` | `curl, wget, ssh` | **v4.5.0 簡素化** |
| B-2 Approval Required — Linting (Write) | `ruff check --fix`, `ruff format` | なし | 影式固有（維持すべき） |
| B-2 Approval Required — Package Install | `pip install`, `pip uninstall` | なし | 影式固有（維持すべき） |
| B-2 Note (Permission Layer) | あり | 同一 | 差分なし |

#### Section 3: Automation Workflow

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| v4.0.0 注記 | あり | 同一 | 差分なし |
| Decide 判定文 | `SafeToAutoRun: true/false` 使用 | `Allow List に含まれる / 含まれない` | **v4.5.0 変更**（v4.4.1 と同様の簡素化、未反映） |

#### Section 5: Hooks-Based Permission System

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| 多層モデル表 | あり | 同一 | 差分なし |
| PreToolUse パス | 影式固有パス（`pyproject.toml`, `src/kage_shiki/`, `config/`）含む | 汎用パスのみ | 影式固有（維持すべき） |
| PostToolUse | 3項目（TDD パターン、doc-sync-flag、ループログ） | 同一 | 差分なし |
| Stop Hook | Green State G1-G5 | `docs/specs/green-state-definition.md` 参照を追加 | **v4.5.0 微修正** |

#### Section 6: Recommended Security Tools

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| 構成 | `影式での利用` 列付きテーブル（ruff, pip-audit, safety, bandit） | **Anthropic 公式ツール** + **言語別脆弱性スキャン** + **CI/CD 統合例** の3カテゴリに大幅拡充 | **v4.5.0 大幅変更** |
| Anthropic 公式 | なし | security-guidance plugin, claude-code-security-review, Claude Code Security | **v4.5.0 新規** |
| 言語別スキャン | なし | npm audit, pip-audit, safety, govulncheck | **v4.5.0 新規** |
| CI/CD 統合 | なし | GitHub Actions `claude-code-security-review` 設定例 | **v4.5.0 新規** |

---

### 99_reference_generic.md

#### Section B: Phase 4

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| Phase 4 タグ | なし | `[RELEASE]` タグ追加 | **v4.5.0 微修正** |

**他のセクション（A, C, D）は差分なし。**

---

## 2. CLAUDE.md 差分

### Identity

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| プロジェクト名 | `影式 (Kage-Shiki)` を明記 | `本プロジェクト`（汎用） | 影式固有（維持） |
| Project Scale | `Medium` | `Medium to Large` | テンプレート汎用化 |

### Project Overview

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| セクション全体 | 技術スタックテーブルあり | **セクション自体なし** | 影式固有（維持） |

### Hierarchy of Truth

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| Architecture 参照範囲 | `docs/internal/`（SSOT: 00〜09, 参考: 99） | `docs/internal/00-07`（SSOT） | **v4.5.0 変更**。影式は 00〜09 を維持（08, 09 は影式固有ファイル） |

### Execution Modes

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| `/auditing` ガードレール | `PM級修正禁止（PG/SE級は許可）` | `PG/SE修正可、PM指摘のみ` | 同一内容、表現微修正 |

### References

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| 設計文書行 | `docs/memos/middle-draft/` を含む | なし（行自体削除） | 影式固有（維持） |
| 概念説明スライド | `docs/slides/index.html`（将来作成予定） | `docs/slides/index.html`（注記なし） | 影式固有注記 |

### Context Management

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| 閾値 | **20%** | **10%** | **v4.5.0 変更**（閾値引き下げ） |
| `/quick-save` 内容 | `SESSION_STATE.md + Daily 記録 + ループログ` | `SESSION_STATE.md + ループログ + Daily 記録（git操作なし）` | 同一内容（語順変更 + git 注記追加） |
| 残量 25% 条件 | `残量 25% 以下では /quick-save を使うこと` | なし | 影式固有（維持検討） |
| git commit | `/ship` を使用 | `git commit が必要なら /ship を使用` | 同一内容（表現微修正） |

### Memory Policy（v4.4.1 での変更の確認）

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| セクション名 | `MEMORY.md Policy` | `Memory Policy` | **v4.5.0 変更**（v4.4.1 で既に指摘済み） |
| Layer 名称 | `Layer 1: Auto Memory`, `Layer 2: Subagent Persistent Memory`, `Layer 3: Knowledge Layer` | `Auto Memory（MEMORY.md）`, `Subagent Persistent Memory`, `Knowledge Layer`（Layer 番号なし） | **v4.5.0 変更** |
| Auto Memory 詳細 | `作業効率に関する学習（ビルドコマンド、デバッグ知見、Subagent 役割ノウハウ等）` | `ビルドコマンド、デバッグ知見、ワークフロー習慣など作業効率に関する学習` + MEMORY.md パス明示 | **v4.5.0 拡充** |
| Subagent Memory 詳細 | `.claude/agent-memory/<agent-name>/` のみ | `.claude/agents/` からの指示、「Claude Code の公式フロントマター機能ではない」と明記 | **v4.5.0 拡充** |
| Knowledge Layer 参照 | `docs/internal/05_MCP_INTEGRATION.md` Section 6 | `docs/artifacts/knowledge/README.md` | **v4.5.0 変更** |

### Initial Instruction

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| プロジェクト名 | `影式 (Kage-Shiki) プロジェクトの` を含む | なし（汎用） | 影式固有（維持） |

---

## 3. CHEATSHEET.md 差分

### タイトル・はじめに

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| タイトル | `影式 (Kage-Shiki) チートシート` | `Living Architect Model チートシート` | 影式固有（維持） |
| スライド参照 | `docs/slides/index.html`（将来作成予定） | `docs/slides/index.html` + `QUICKSTART.md` リンク追加 | **v4.5.0 拡充** |

### プロジェクト技術スタック

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| セクション全体 | あり（Python 3.12+ 等） | **セクション自体なし** | 影式固有（維持） |

### ディレクトリ構造

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| logs/ 説明 | `permission.log, loop-*.txt` | `permission.log, loop-*.txt（実行時生成）` | **v4.5.0 微修正** |
| agent-memory/ | `.claude/agent-memory/` | なし（ディレクトリ構造には未記載） | 影式固有（維持） |
| CLAUDE.md 説明 | `憲法（コア原則 + 技術スタック）` | `憲法（コア原則のみ）` | **v4.5.0 変更** |
| docs/memos/middle-draft/ | あり | なし | 影式固有（維持） |

### Rules ファイル一覧

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| `core-identity.md` 説明 | `Living Architect 行動規範 + 権限等級サマリー` | `Living Architect 行動規範` | **v4.5.0 微修正** |
| `decision-making.md` 説明 | `意思決定プロトコル` | `意思決定プロトコル（MAGI System）` | **v4.5.0 変更** |
| `permission-levels.md` 説明 | `権限等級分類基準（PG/SE/PM）` | `権限等級分類基準（PG/SE/PM）**v4.0.0 新規**` | **v4.5.0 微修正** |
| `building-checklist.md` | あり（影式固有） | **なし** | 影式固有（維持） |
| `auto-generated/` | あり | なし（一覧に不記載） | **v4.5.0 変更**（ただし存在はする） |
| **`code-quality-guideline.md`** | なし | **新規追加予定**（LAM v4.5.0 の .claude/rules/ に存在） | **v4.5.0 新規** |
| **`planning-quality-guideline.md`** | なし | **新規追加予定**（LAM v4.5.0 の .claude/rules/ に存在） | **v4.5.0 新規** |

### 権限等級（PG/SE/PM）

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| PreToolUse hook 詳細 | パスベース判定 + permission.log 記録 + 誤判定率計測 | 同一構造（パス例のみ汎用） | 差分なし |
| フック分類の誤判定率計測 | なし（影式独自で存在） | あり | 差分なし |

### セッション管理コマンド

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| `/quick-save` 内容 | `SESSION_STATE.md + Daily 記録 + ループログ` | `SESSION_STATE.md + ループログ + Daily` | 同一内容（語順変更） |
| `/quick-save` コスト | `3-4%` | `3-5%` | **v4.5.0 微修正** |
| `/quick-load` コスト | `2-3%` | `1-2%` | **v4.5.0 微修正** |
| セーブ/ロード使い分け | なし（コマンド表のみ） | **サブセクション追加**（セーブ/ロード/コミットの使い分けを明示） | **v4.5.0 新規** |

### サブエージェント

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| Memory 列 | なし | **Memory 列を追加**（`auto` / `-`） | **v4.5.0 新規**（v4.4.1 で既に指摘済み、未反映） |
| `code-reviewer` Memory | — | `auto` | **v4.5.0 新規** |

### スキル

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| `lam-orchestrate` 説明 | `タスク分解・並列実行 + 構造化思考（AoT + Three Agents）` | `タスク分解・並列実行 + /magi 統合` | **v4.5.0 変更** |
| **`/magi`** | なし | **新規追加**: 構造化意思決定（AoT + MAGI System + Reflection） | **v4.5.0 新規** |
| **`/clarify`** | なし | **新規追加**: 文書精緻化（曖昧さ・矛盾・欠落検出） | **v4.5.0 新規** |
| **`ui-design-guide`** | なし | **新規追加**: UI/UX設計チェックリスト | **v4.5.0 新規** |

### ワークフローコマンド

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| `/full-review` | `並列監査 + 全修正 + 検証（4エージェント、一気通貫）` | `並列監査 + 全修正 + 検証（一気通貫）` + `<対象>` 引数 | **v4.5.0 変更** |
| **`/release`** | なし | **新規追加**: `<version>` 引数（CHANGELOG -> commit -> push -> tag） | **v4.5.0 新規** |
| `/wave-plan` | ワークフローコマンドに記載 | `[N]` 引数追加 | **v4.5.0 微修正** |
| `/retro` | ワークフローコマンドに記載 | `[wave|phase]` 引数明示 | **v4.5.0 微修正** |

### 補助コマンド

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| `/pattern-review` | あり | あり | 差分なし |
| `/project-status` | あり | あり | 差分なし |

### 状態管理

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| `docs/artifacts/knowledge/` | `retro Step 4 の知見保存先` | `プロジェクト知見の構造化蓄積（/retro 経由）` | **v4.5.0 微修正** |
| `.claude/agent-memory/` | `Subagent Persistent Memory` | `Subagent の自動学習記録` | **v4.5.0 微修正** |

### AoT クイックガイド → /magi クイックガイド

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| セクション名 | `AoT（Atom of Thought）クイックガイド` | `/magi（構造化意思決定）クイックガイド` | **v4.5.0 変更** |
| MAGI System 説明 | なし | **MELCHIOR/BALTHASAR/CASPAR の役割説明を追加** | **v4.5.0 新規** |
| ワークフロー | `1. Decomposition → 2. Debate → 3. Synthesis` | `0. Decomposition → 1-3. MAGI Debate → 4. Reflection → 5. Synthesis` | **v4.5.0 変更** |
| Debate 説明 | `各 Atom で 3 Agents 議論` | `各 Atom で MELCHIOR/BALTHASAR/CASPAR 合議` | **v4.5.0 変更** |
| **Reflection** | なし | **Step 4: 結論の致命的見落としを検証（1回限り）** | **v4.5.0 新規** |

### /clarify クイックガイド（新規セクション）

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| セクション全体 | なし | **新設**: いつ使う？ / 使い方（1文書精緻化 / 横断チェック） | **v4.5.0 新規** |

### 参照ドキュメント (SSOT)

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| 06_DECISION_MAKING.md 説明 | `意思決定（3 Agents + AoT）` | `意思決定（MAGI System + AoT + Reflection）` | **v4.5.0 変更** |
| 08_SESSION_MANAGEMENT.md | あり | **なし** | 影式固有 |
| 09_SUBAGENT_STRATEGY.md | あり | **なし** | 影式固有 |
| 99_reference_generic.md | なし | **あり** | **v4.5.0 追加**（v4.4.1 で既に指摘済み、未反映） |

### 日常ワークフロー

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| セクション全体 | あり（一日の開始〜割り込み・中断まで7パターン） | **セクション自体なし** | 影式固有（維持） |

### クイックリファレンス

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| 「次のセッション」 | `/quick-load` | `/quick-load で前回の続きから（日常）` + `/quick-load でセッション復帰` | **v4.5.0 微修正** |
| 「変更をコミット」 | `/ship` | なし | 影式固有（維持） |
| 「設計中間文書」 | `docs/memos/middle-draft/` | なし | 影式固有（維持） |

---

## 4. 影式固有保持項目

### docs/internal/ 内

1. **02_DEVELOPMENT_FLOW.md**: Wave 実績サマリー、Quality Rules Integration、テスト環境 Note（pytest）、Advanced Workflows
2. **03_QUALITY_STANDARDS.md Section 6**: Python Coding Conventions（PEP 8, Type Hints, ruff, Docstrings）
3. **03_QUALITY_STANDARDS.md Section 7**: Building Defect Prevention（R-1〜R-6）
4. **05_MCP_INTEGRATION.md**: Phase 1 MVP Note（MCP 未導入）
5. **07_SECURITY_AND_AUTOMATION.md Section 2**: pytest/ruff 固有コマンドリスト、`python -m kage_shiki` のビルド・ラン、`pip install/uninstall`
6. **07_SECURITY_AND_AUTOMATION.md Section 5**: PreToolUse の影式固有パス（`pyproject.toml`, `src/kage_shiki/`, `config/`）
7. **07_SECURITY_AND_AUTOMATION.md Section 6**: 影式固有ツール列（ruff, pip-audit, safety, bandit）
8. **08_SESSION_MANAGEMENT.md**: セッション管理の詳細（LAM テンプレートには不在）
9. **09_SUBAGENT_STRATEGY.md**: Subagent 運用戦略（LAM テンプレートには不在）

### CLAUDE.md 内

10. **Identity**: `影式 (Kage-Shiki)` の名称と説明文
11. **Project Overview**: 技術スタックテーブル全体
12. **Hierarchy of Truth**: `SSOT: 00〜09` の範囲（08, 09 を含む）
13. **References**: `docs/memos/middle-draft/` の行
14. **Context Management**: 残量 25% 条件、閾値 20%（LAM は 10%）
15. **MEMORY.md Policy**: Layer 1/2/3 の番号付き記法
16. **Initial Instruction**: プロジェクト名修飾

### CHEATSHEET.md 内

17. **プロジェクト技術スタック**: テーブル全体
18. **building-checklist.md**: Rules 一覧への記載
19. **日常ワークフロー**: 7パターンの作業フロー
20. **クイックリファレンス**: `/ship`、設計中間文書
21. **ディレクトリ構造**: `docs/memos/middle-draft/`、`.claude/agent-memory/`

### .claude/rules/ 内

22. **building-checklist.md**: R-2〜R-11, S-2 の影式固有チェックリスト
23. **phase-rules.md**: Phase 完了判定（L-4 スモークテスト）、Green State 5条件対応表、A-1〜A-4、修正後の再検証義務（A-3）
24. **permission-levels.md**: 影式固有パス分類（`src/kage_shiki/`, `pyproject.toml`, `config/`, `docs/internal/`）

---

## 5. Migration Action Items

### 1. MAGI System への移行（最大の変更軸）

影響範囲:
- `docs/internal/06_DECISION_MAKING.md`: Affirmative/Critical/Mediator → MELCHIOR/BALTHASAR/CASPAR + Reflection セクション新設
- `docs/internal/01_REQUIREMENT_MANAGEMENT.md`: Perspective Check の MAGI 化 + Section F (Clarification) 新設
- `docs/internal/02_DEVELOPMENT_FLOW.md`: AoT フレームワーク → MAGI System 連携 + /clarify サブセクション新設
- `.claude/rules/decision-making.md`: 全面書き換え（MAGI + Reflection）
- `.claude/rules/phase-rules.md`: AUDITING セクションの「3 Agents Model」→「MAGI System」
- `CHEATSHEET.md`: AoT クイックガイド → /magi クイックガイド + /clarify クイックガイド新設

### 2. 新規 Rules ファイルの導入

- **`.claude/rules/code-quality-guideline.md`**: 重要度分類（Critical/Warning/Info）の定量的基準。Error Swallowing、Cognitive Complexity > 15、SRP 違反等の具体的判定ルール。Green State G3 の判定基準を定義
- **`.claude/rules/planning-quality-guideline.md`**: Requirements Smells（危険な単語リスト）、RFC 2119 キーワード、Design Doc チェックリスト（Non-Goals/Alternatives/Success Criteria）、SPIDR 分割、WBS 100% Rule、Example Mapping

### 3. phase-rules.md の更新

- PLANNING セクション: **品質基準サブセクション新設**（planning-quality-guideline.md 参照）
- BUILDING セクション: **R-5, R-6 の新規追加**（テスト名と入力値の一致、設計書出力ファイルからのアサーション生成）
- AUDITING セクション: **重要度分類の判断基準を code-quality-guideline.md に委譲**（`判断基準は .claude/rules/code-quality-guideline.md に準拠` 注記追加）。Green State 条件の簡素化（`Critical = 0 かつ Warning = 0`）

### 4. SSOT 3層アーキテクチャの再構成

`00_PROJECT_STRUCTURE.md` Section 3 の大幅変更:
- 情報層の方向を逆転（docs/internal/ を情報層 1、CHEATSHEET.md を情報層 3）
- テーブル形式 → ASCII 矢印図
- CLAUDE.md は情報層に含まれなくなった（「プロジェクト憲法」として独立的位置付けに）

**注意**: 影式現行の CLAUDE.md Hierarchy of Truth（User Intent > docs/internal/ > docs/specs/ > Code）は v4.5.0 の SSOT 3層と整合しているため、構造変更は自然に受け入れ可能。

### 5. Context Management 閾値変更

- CLAUDE.md のコンテキスト残量閾値: 20% → **10%** に引き下げ
- 影式現行は 20%（+ 25% で `/quick-save` 推奨）。v4.5.0 は 10% のみ
- **判断**: 影式の 20% 閾値は運用実績があるため維持を検討。10% は auto-compact がより発達した環境を想定している可能性あり

### 6. 07_SECURITY_AND_AUTOMATION.md Section 6 の拡充

影式固有ツール列に加え、Anthropic 公式ツール（security-guidance plugin, claude-code-security-review）と CI/CD 統合例を追加。影式の既存セクションを LAM v4.5.0 形式に再構成する必要あり。

### 7. core-identity.md の簡素化

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| Subagent 委任判断 | テーブルあり | 削除 | **v4.5.0 変更**（影式は維持中） |
| コンテキスト節約原則 | あり | 削除 | **v4.5.0 変更**（影式は維持中） |
| Context Compression | `docs/tasks/` または `docs/artifacts/` | 同一 | 差分なし |

**判断**: 影式では Subagent 委任判断とコンテキスト節約原則が実運用で参照されているため維持を推奨。

### 8. permission-levels.md の微更新

| 項目 | 影式現行 | LAM v4.5.0 | 差分種別 |
|:-----|:---------|:-----------|:---------|
| 冒頭説明 | SSOT 位置付けの詳述 | 簡潔な説明 | 影式固有（維持） |
| PM級 | 既存 | `フェーズの巻き戻し` 追加 | **v4.5.0 追加** |
| SSOT 参照 | なし | `docs/specs/v4.0.0-immune-system-requirements.md` 参照を追加 | テンプレート汎用化（影式には該当ファイル不在のため不要） |
| 迷った場合の例 | 影式固有例を含む | テンプレート汎用例（`package.json`） | 影式固有（維持） |

### 9. 新規スキル・コマンドの導入

以下のスキル/コマンドが LAM v4.5.0 で新設されている:
- **`/magi`**: 構造化意思決定（AoT + MAGI System + Reflection）
- **`/clarify`**: 文書精緻化（曖昧さ・矛盾・欠落検出）
- **`/release`**: リリースコマンド（CHANGELOG → commit → push → tag）
- **`ui-design-guide`**: UI/UX 設計チェックリスト

### 10. マージ戦略の推奨

前回（v4.4.1）と同様に **Template-First 戦略** を推奨:
1. LAM v4.5.0 テンプレートをベースとして採用
2. 影式固有カスタマイズ（Section 4 で列挙）を上乗せ
3. MAGI System 移行は 06_DECISION_MAKING.md を中心に波及範囲が広いため、一括で実施
4. 新規 Rules ファイル（code-quality-guideline.md, planning-quality-guideline.md）は影式固有の building-checklist.md と共存可能。そのまま導入
5. SSOT 3層の再構成は 00_PROJECT_STRUCTURE.md の該当セクションのみ変更。CLAUDE.md の Hierarchy of Truth は現行維持で整合

### 11. v4.4.1 移行時に未反映だった項目の確認

前回の差分分析（`00-diff-docs.md`）で指摘されたが未反映の可能性がある項目:
- CHEATSHEET.md: サブエージェントの Memory 列追加
- CHEATSHEET.md: 参照ドキュメントに 99_reference_generic.md 追加
- CLAUDE.md: Memory Policy のセクション名変更（MEMORY.md Policy → Memory Policy）
- 07_SECURITY_AND_AUTOMATION.md Section 3: Automation Workflow の簡素化（SafeToAutoRun → Allow List 判定）

これらは v4.5.0 移行と合わせて対応すること。
