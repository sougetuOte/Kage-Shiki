# Phase 1 タスク: Rules + docs/internal/ + CLAUDE.md + CHEATSHEET.md

**ステータス**: Draft
**対象設計**: `designs/01-design-rules-docs.md`
**優先度**: 高（プロセス定義の基盤更新）
**依存**: なし（Phase 0 完了済み）
**承認日**: 2026-03-16

---

## 1. 概要

### 1.1 Phase 1 の目的

LAM v4.5.0 のドキュメント層（.claude/rules/、docs/internal/、CLAUDE.md、CHEATSHEET.md）を影式に適用する。既存テストやソースコードへの影響がなく、リスクが最も低い Phase として先行実施する。

### 1.2 前提条件

- Phase 0（差分分析 + 設計）が完了していること
- 以下の判断が承認済みであること:
  - R-5/R-6 衝突 → 影式を R-12/R-13 にリナンバ
  - SSOT 3層 → LAM に追従
  - Context 閾値 → 影式 20% を維持
  - 03_QS Python セクション → 影式保持

### 1.3 完了条件

1. MAGI System 命名が全対象ファイルに適用されている
2. 新規ルール 2 件（code-quality-guideline.md、planning-quality-guideline.md）が配置されている
3. R-5/R-6 リナンバリングが整合している
4. SSOT 3 層再構成が 00_PROJECT_STRUCTURE.md に反映されている
5. v4.4.1 未反映項目が対応済みである
6. 影式固有保持項目が全て保全されている（Section 6 チェックリスト全項目パス）

---

## 2. AoT Decomposition

### 2.1 Atom 分解

| Atom | 判断内容 | 対象ファイル数 | 依存 | サイズ |
|------|----------|:------------:|------|:-----:|
| A0 | 事前確認（Green State 定義、R-5/R-6 参照箇所、コンテキスト消費） | 0（検証のみ） | なし | S |
| A1 | R-5/R-6 リナンバリング（building-checklist.md + 参照元更新） | 2-3 | なし | S |
| A2 | MAGI System 命名変更（rules + docs/internal 横断） | 4 | なし | M |
| A3 | 新規ルール追加（code-quality-guideline.md、planning-quality-guideline.md） | 2 | なし | M |
| A4 | phase-rules.md 更新（品質基準、R-5/R-6 追加、Green State 再定義） | 1 | A1, A3 | L |
| A5 | その他 rules 更新（security-commands、permission-levels、upstream-first、test-result-output、auto-generated） | 6 | なし | M |
| A6 | docs/internal/ 更新（06_DM が最大、01、02、00、07、04、05、99） | 9 | A2 | L |
| A7 | CLAUDE.md + CHEATSHEET.md 更新 | 2 | A2, A3, A6 | M |
| A8 | 横断検証（MAGI 残存チェック、参照整合性、影式固有保全） | 0（検証のみ） | A1-A7 | S |

### 2.2 依存 DAG

```
A0（事前確認）
 ├── A1（R-5/R-6 リナンバ）
 ├── A2（MAGI 命名）──┐
 ├── A3（新規ルール）──┼── A4（phase-rules.md）
 └── A5（その他 rules） │
                        ├── A6（docs/internal/）
                        │    │
                        └────┴── A7（CLAUDE.md + CHEATSHEET.md）
                                  │
                                  └── A8（横断検証）
```

並列可能: A1, A2, A3, A5 は全て独立して並列実行可能（A0 完了後）。

---

## 3. タスク一覧

### Atom A0: 事前確認

#### T-100: 事前確認の実施

| 項目 | 内容 |
|------|------|
| **Task ID** | T-100 |
| **説明** | Phase 1 開始前に 3 点の事前確認を実施する: (1) `docs/specs/green-state-definition.md` の存在確認、(2) `.claude/rules/` の合計行数と新規追加による増加率の計測、(3) `03_QUALITY_STANDARDS.md` Section 7 および全ファイルでの R-5/R-6 参照箇所の特定 |
| **対象ファイル** | なし（検証のみ） |
| **変更種別** | 検証 |
| **影式固有考慮** | green-state-definition.md が存在しない場合、phase-rules.md の G1-G5 テーブルが Green State SSOT となる。R-5/R-6 の grep 結果がリナンバリング対象の網羅性を保証する |
| **依存** | なし |
| **サイズ** | S |

---

### Atom A1: R-5/R-6 リナンバリング

#### T-101: building-checklist.md の R-5→R-12, R-6→R-13 リナンバリング

| 項目 | 内容 |
|------|------|
| **Task ID** | T-101 |
| **説明** | building-checklist.md 内の R-5（異常系テストの義務）を R-12 に、R-6（else のデフォルト値禁止）を R-13 にリナンバリングする。対象: (1) Red セクション見出し内 R-5→R-12、(2) Green セクション見出し内 R-6→R-13、(3) Green 直後セクション内 R-6 再確認→R-13 再確認、(4) R-5 続: カバレッジ確認→R-12 続: カバレッジ確認 |
| **対象ファイル** | `.claude/rules/building-checklist.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | building-checklist.md は影式固有ファイルであり、R-2, R-3, R-7〜R-11, S-2 は一切変更しない |
| **依存** | T-100 |
| **サイズ** | S |

#### T-102: R-5/R-6 参照元の更新

| 項目 | 内容 |
|------|------|
| **Task ID** | T-102 |
| **説明** | T-100 の grep 結果に基づき、building-checklist.md 以外のファイルで R-5/R-6 への参照を R-12/R-13 に更新する。主要対象: (1) phase-rules.md の参照コメント `(プロジェクト固有ルールは building-checklist.md を参照: R-2, R-3, R-5〜R-11, S-2)` → `R-2, R-3, R-12, R-13, R-7〜R-11, S-2`、(2) 03_QUALITY_STANDARDS.md Section 7 内の R-5/R-6 言及（該当する場合） |
| **対象ファイル** | `.claude/rules/phase-rules.md`, `docs/internal/03_QUALITY_STANDARDS.md`（該当する場合） |
| **変更種別** | 更新 |
| **影式固有考慮** | phase-rules.md の参照コメントは影式固有の追記。LAM 本体の R-5/R-6 と混同しないよう注意 |
| **依存** | T-100, T-101 |
| **サイズ** | S |

---

### Atom A2: MAGI System 命名変更

#### T-110: decision-making.md の MAGI System 導入 + Reflection 追加

| 項目 | 内容 |
|------|------|
| **Task ID** | T-110 |
| **説明** | decision-making.md を MAGI System 版に更新する。変更点: (1) タイトル→「意思決定プロトコル（MAGI System）」、(2) セクション名→「MAGI System」、(3) Agent テーブルの MAGI 名称付与（旧名カッコ内併記）、(4) Execution Flow の MAGI 名称 + Step 4 Reflection 新設、(5) AoT ワークフロー更新、(6) Output Format のラベル変更 + Reflection セクション追加 |
| **対象ファイル** | `.claude/rules/decision-making.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | なし（影式固有の追記は存在しない） |
| **依存** | T-100 |
| **サイズ** | M |

#### T-111: 06_DECISION_MAKING.md の MAGI 全面導入 + Reflection 新設

| 項目 | 内容 |
|------|------|
| **Task ID** | T-111 |
| **説明** | docs/internal/06_DECISION_MAKING.md を MAGI System 版に全面更新する。最大規模の変更。変更点: (1) タイトル変更、(2) Section 1 Agent 名を MAGI に変更（旧名カッコ内併記）、(3) Section 2 Execution Flow の全ステップで MAGI 名称、(4) Section 3 Output Format のラベル変更、(5) Section 5 AoT の 5.4 ワークフロー名・Step 詳細・Step 4 Reflection 新設・旧 Step 4→新 Step 5 へ番号変更・5.5 出力フォーマット更新、(6) Section 6 Reflection 新設（6.1 目的、6.2 ルール、6.3 出力フォーマット、6.4 参照） |
| **対象ファイル** | `docs/internal/06_DECISION_MAKING.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | なし |
| **依存** | T-100 |
| **サイズ** | L |

#### T-112: 01_REQUIREMENT_MANAGEMENT.md の MAGI + /clarify 統合

| 項目 | 内容 |
|------|------|
| **Task ID** | T-112 |
| **説明** | 01_REQUIREMENT_MANAGEMENT.md に MAGI 命名と /clarify 参照を統合する。変更点: (1) Section E Perspective Check で Affirmative/Critical/Mediator → MELCHIOR/BALTHASAR/CASPAR、(2) /magi スキル参照追加、(3) Section F Clarification 新設（/clarify による文書精緻化手順）、(4) Section 2 Definition of Ready に「/clarify で精緻化済みであること」を追加 |
| **対象ファイル** | `docs/internal/01_REQUIREMENT_MANAGEMENT.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | なし |
| **依存** | T-100 |
| **サイズ** | M |

#### T-113: 02_DEVELOPMENT_FLOW.md の MAGI + /clarify + R-5/R-6 参照

| 項目 | 内容 |
|------|------|
| **Task ID** | T-113 |
| **説明** | 02_DEVELOPMENT_FLOW.md に MAGI 命名、/clarify 参照、R-5/R-6 参照を追加する。変更点: (1) Phase 1 冒頭文に Phase 3 を追加、(2) AoT セクション名→「MAGI System（構造化意思決定）との連携」、(3) /magi スキル参照追加、(4) Three Agents Debate→MAGI Debate、(5) 文書精緻化（/clarify）サブセクション新設、(6) Phase 2 TDD 内省の src/ 変更検知記述追加、(7) Phase 3 に permission-levels.md 参照追加 |
| **対象ファイル** | `docs/internal/02_DEVELOPMENT_FLOW.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | テスト環境 Note（pytest）、Wave-Based Development、Quality Rules Integration、Advanced Workflows の各影式固有セクションを全て保持 |
| **依存** | T-100 |
| **サイズ** | M |

---

### Atom A3: 新規ルール追加

#### T-120: code-quality-guideline.md の新規追加

| 項目 | 内容 |
|------|------|
| **Task ID** | T-120 |
| **説明** | LAM v4.5.0 の code-quality-guideline.md をそのまま `.claude/rules/` に配置する。主要セクション: 三層モデル、Critical/Warning/Info 定義、Green State Issue 条件、判断フローチャート、アンチパターン、BUILDING/AUDITING での適用 |
| **対象ファイル** | `.claude/rules/code-quality-guideline.md` |
| **変更種別** | 新規 |
| **影式固有考慮** | building-checklist.md R-12（異常系テストの義務）と Critical「Error Swallowing」は補完関係（責務が異なるため衝突なし）。03_QUALITY_STANDARDS.md の閾値とも矛盾なし |
| **依存** | T-100 |
| **サイズ** | M |

#### T-121: planning-quality-guideline.md の新規追加

| 項目 | 内容 |
|------|------|
| **Task ID** | T-121 |
| **説明** | LAM v4.5.0 の planning-quality-guideline.md をそのまま `.claude/rules/` に配置する。主要セクション: Requirements Smells、RFC 2119 キーワード、Design Doc チェックリスト、SPIDR タスク分割、WBS 100% Rule、Example Mapping |
| **対象ファイル** | `.claude/rules/planning-quality-guideline.md` |
| **変更種別** | 新規 |
| **影式固有考慮** | Phase 2 で導入される /clarify スキルとの連携が想定されるが、Phase 1 時点ではスキル未導入。参照が見つからないだけでドキュメントとしては正しい。RFC 2119 の既存仕様書への遡及適用は PM 級判断として別途扱う |
| **依存** | T-100 |
| **サイズ** | M |

---

### Atom A4: phase-rules.md 更新

#### T-130: phase-rules.md の PLANNING 品質基準 + BUILDING R-5/R-6 + AUDITING Green State 再定義

| 項目 | 内容 |
|------|------|
| **Task ID** | T-130 |
| **説明** | phase-rules.md に 4 つの主要変更を適用する。(A) PLANNING セクションに品質基準サブセクション新設（planning-quality-guideline.md 参照）。(B) BUILDING セクションに LAM R-5、R-6 を追加 + 参照コメントを R-12/R-13 に更新。(C) AUDITING 必須セクションの更新: code-quality-guideline.md 参照追加、`3 Agents Model`→`MAGI System`、項目順序微調整。(D) AUDITING Green State 条件の追加: `Critical = 0 かつ Warning = 0` を既存 G1-G5 テーブルの前に新設 |
| **対象ファイル** | `.claude/rules/phase-rules.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | 以下を全て保持: (1) 影式固有: Phase 完了判定（L-4 由来）、(2) 影式固有: 修正後の再検証義務（A-3 由来）、(3) 影式固有: 監査レポート完了条件、(4) AUDITING ルール識別子（A-1〜A-4）、(5) Green State 5条件テーブル（G1-G5）。v4.5.0 Issue ベース条件は G3 に相当し、G1/G2/G4/G5 は影式追加要件として位置付ける |
| **依存** | T-101, T-102, T-120, T-121 |
| **サイズ** | L |

---

### Atom A5: その他 rules 更新

#### T-140: security-commands.md の find deny 昇格 + 説明文追加

| 項目 | 内容 |
|------|------|
| **Task ID** | T-140 |
| **説明** | security-commands.md に以下を適用: (1) deny テーブルに find 破壊パターンを独立行として追加、(2) ask テーブルに find 通常検索を独立行として追加、(3) deny/ask セクションに説明文追加、(4) v4.0.0 セクション PG級コマンド例示の微修正（ruff format を追記） |
| **対象ファイル** | `.claude/rules/security-commands.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | Python カテゴリ（Allow List）、`pip show`（パッケージ情報）、※1 注記（二段構成: settings.json と settings.local.json）を全て保持 |
| **依存** | T-100 |
| **サイズ** | S |

#### T-141: permission-levels.md の SE/PM 説明文改善 + 注記更新

| 項目 | 内容 |
|------|------|
| **Task ID** | T-141 |
| **説明** | permission-levels.md に以下を適用: (1) SE級説明文の更新（LAM 定義型表現＋影式の行動指示を併記）、(2) PM級の導入説明文を追加、(3) ファイルパスベース分類の `.claude/rules/` 注記に「（サブディレクトリ含む）」を追加。参照セクションへの `docs/specs/v4.0.0-immune-system-requirements.md` 追加は影式に該当ファイルが不在のため実施しない |
| **対象ファイル** | `.claude/rules/permission-levels.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | SSOT 宣言（冒頭 4 行）、影式固有パス（docs/internal/, pyproject.toml, src/kage_shiki/, tests/, config/）、影式固有例（config.toml テンプレート等）、相互参照を全て保持 |
| **依存** | T-100 |
| **サイズ** | S |

#### T-142: upstream-first.md の確認対象明示 + WebFetch 注意事項

| 項目 | 内容 |
|------|------|
| **Task ID** | T-142 |
| **説明** | upstream-first.md に以下を適用: (1) 「必須: 実装前の仕様確認」に確認対象リスト（settings.json、hooks/、フロントマター、MCP）を追加、(2) 確認手順の後に WebFetch 注意事項の注記ブロックを追加（/full-review 内での WebFetch 禁止） |
| **対象ファイル** | `.claude/rules/upstream-first.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | なし |
| **依存** | T-100 |
| **サイズ** | S |

#### T-143: test-result-output.md の構造改善 + 言語別リファレンス拡充

| 項目 | 内容 |
|------|------|
| **Task ID** | T-143 |
| **説明** | test-result-output.md に以下を適用: (1) 概要の一般化（「構造化ファイルに出力」）、(2) ルールセクションの番号付きリスト統合、(3) 理由セクション新設、(4) Go リファレンス更新（gotestsum）、(5) Rust リファレンス拡充、(6) 「その他の言語」セクション追加、(7) 適用タイミングセクション新設、(8) PostToolUse 連携→「結果ファイルが存在しない場合」にセクション名変更、(9) 参照セクション新設（影式パス `docs/specs/lam/tdd-introspection-v2.md` を使用） |
| **対象ファイル** | `.claude/rules/test-result-output.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | 影式は Python (pytest) のみ使用。Go/Rust の更新は直接影響ないがテンプレート整合のため取り込む |
| **依存** | T-100 |
| **サイズ** | M |

#### T-144: auto-generated/README.md の冒頭説明文追加

| 項目 | 内容 |
|------|------|
| **Task ID** | T-144 |
| **説明** | auto-generated/README.md の「# 自動生成ルール」直下にディレクトリ目的の説明文を追加: 「このディレクトリには、TDD 内省パイプライン v2 によって自動生成されたルールが配置される。」 |
| **対象ファイル** | `.claude/rules/auto-generated/README.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | 仕様書パスの `lam/` プレフィックス（`docs/specs/lam/tdd-introspection-v2.md`）を保持 |
| **依存** | T-100 |
| **サイズ** | S |

#### T-145: auto-generated/trust-model.md のフロー図微修正

| 項目 | 内容 |
|------|------|
| **Task ID** | T-145 |
| **説明** | auto-generated/trust-model.md のフロー図で「JUnit XML 出力 (.claude/test-results.xml)」→「JUnit XML 出力」にパス注記を削除 |
| **対象ファイル** | `.claude/rules/auto-generated/trust-model.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | tdd-patterns.log の形式セクション（TSV 形式定義）、仕様書パスの `lam/` プレフィックス、パターン詳細記録先（`docs/artifacts/tdd-patterns/`）を全て保持 |
| **依存** | T-100 |
| **サイズ** | S |

---

### Atom A6: docs/internal/ 更新

#### T-150: 00_PROJECT_STRUCTURE.md の SSOT 3層再構成

| 項目 | 内容 |
|------|------|
| **Task ID** | T-150 |
| **説明** | 00_PROJECT_STRUCTURE.md に以下を適用: (A) Section 1 の .claude/ 配下に commands/, rules/, skills/, agents/, settings.json を明示 + docs/ 配下に slides/, daily/ 追加。(B) Section 2 の TDD Patterns に .claude/tdd-patterns.log 注記追加 + Subagent Memory 説明拡充。(C) Section 3 を SSOT 3層構成に全面変更（情報層 1: docs/internal/ → 情報層 2: .claude/ → 情報層 3: CHEATSHEET.md、CLAUDE.md はブートストラップ。テーブル形式→ASCII 矢印図） |
| **対象ファイル** | `docs/internal/00_PROJECT_STRUCTURE.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | src/kage_shiki/ パッケージ構造、docs/memos/middle-draft/ 記載、tests/ の pytest 明示を保持 |
| **依存** | T-100 |
| **サイズ** | L |

#### T-151: 04_RELEASE_OPS.md のデプロイ基準更新

| 項目 | 内容 |
|------|------|
| **Task ID** | T-151 |
| **説明** | 04_RELEASE_OPS.md に以下を適用: (1) Section 1 で All Tests Green を独立チェック項目として分離、(2) Quality Gate Passed を汎用化、(3) Section 3 Post-Mortem 記録先の表現整理 |
| **対象ファイル** | `docs/internal/04_RELEASE_OPS.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | HTML コメント（`<!-- Phase 2b 以降で... -->`）を保持 |
| **依存** | T-100 |
| **サイズ** | S |

#### T-152: 05_MCP_INTEGRATION.md の微修正

| 項目 | 内容 |
|------|------|
| **Task ID** | T-152 |
| **説明** | 05_MCP_INTEGRATION.md の MCP サーバー表記を「Phase 2 以降で検討」→「Optional」に更新 |
| **対象ファイル** | `docs/internal/05_MCP_INTEGRATION.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | Phase 1 MVP Note（MCP 未導入）を保持 |
| **依存** | T-100 |
| **サイズ** | S |

#### T-153: 07_SECURITY_AND_AUTOMATION.md の Permission Layer 整理

| 項目 | 内容 |
|------|------|
| **Task ID** | T-153 |
| **説明** | 07_SECURITY_AND_AUTOMATION.md に以下を適用: (1) Section 2 Allow List に find v4.3.1 移動注記、(2) Section 2 Deny List に find 破壊パターン、(3) Section 2 Approval Required の Network 簡素化（ping, nc 削除）、(4) Section 3 Automation Workflow で SafeToAutoRun→Allow List 判定（v4.4.1 未反映対応）、(5) Section 5 Stop Hook に green-state-definition.md 参照追加、(6) Section 6 Recommended Security Tools を 3 カテゴリに大幅拡充（Anthropic 公式ツール + 言語別脆弱性スキャン + CI/CD 統合例） |
| **対象ファイル** | `docs/internal/07_SECURITY_AND_AUTOMATION.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | Section 2 の pytest/ruff コマンドリスト、pip install/uninstall。Section 5 の影式固有パス（pyproject.toml, src/kage_shiki/, config/）。Section 6 の影式固有ツール列（ruff, pip-audit, safety, bandit）。全て保持 |
| **依存** | T-100 |
| **サイズ** | M |

#### T-154: 03_QUALITY_STANDARDS.md の R-5/R-6 リナンバ確認

| 項目 | 内容 |
|------|------|
| **Task ID** | T-154 |
| **説明** | 03_QUALITY_STANDARDS.md Section 7（Building Defect Prevention）内に R-5/R-6 への言及がある場合、R-12/R-13 に更新する。Section 6/7 全体は影式固有として保持 |
| **対象ファイル** | `docs/internal/03_QUALITY_STANDARDS.md` |
| **変更種別** | 更新（該当箇所がある場合のみ） |
| **影式固有考慮** | Section 6（Python Coding Conventions）と Section 7（Building Defect Prevention）全体を保持。変更は R-5/R-6 参照のリナンバのみ |
| **依存** | T-100, T-101 |
| **サイズ** | S |

#### T-155: 99_reference_generic.md の Phase 4 タグ追加

| 項目 | 内容 |
|------|------|
| **Task ID** | T-155 |
| **説明** | 99_reference_generic.md の Phase 4 に `[RELEASE]` タグを追加 |
| **対象ファイル** | `docs/internal/99_reference_generic.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | なし |
| **依存** | T-100 |
| **サイズ** | S |

---

### Atom A7: CLAUDE.md + CHEATSHEET.md 更新

#### T-160: CLAUDE.md の更新

| 項目 | 内容 |
|------|------|
| **Task ID** | T-160 |
| **説明** | CLAUDE.md に以下を適用: (A) Memory Policy セクション名を「MEMORY.md Policy」→「Memory Policy」に変更（v4.4.1 未反映対応）、Auto Memory 説明拡充、Subagent Memory 説明拡充、Knowledge Layer 参照先を `docs/artifacts/knowledge/` に変更。(B) Context Management で git 注記を「git commit が必要なら /ship を使用」に微修正。(C) Execution Modes の /auditing を「PG/SE修正可、PM指摘のみ」に微修正。影式固有: Identity、Project Overview、Project Scale（Medium）、Hierarchy of Truth（00〜09）、References、Context 閾値（20%）、残量 25% 条件、Initial Instruction は全て保持 |
| **対象ファイル** | `CLAUDE.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | Context 閾値 20% を維持（LAM の 10% は採用しない）。Layer 番号付き記法を可読性のため保持。Project Scale は Medium を維持 |
| **依存** | T-111, T-120, T-121, T-150 |
| **サイズ** | M |

#### T-161: CHEATSHEET.md の更新

| 項目 | 内容 |
|------|------|
| **Task ID** | T-161 |
| **説明** | CHEATSHEET.md に以下を適用: (A) ディレクトリ構造: CLAUDE.md 説明の「技術スタック」削除、logs/ に「（実行時生成）」追記。(B) Rules 一覧: decision-making.md 説明に「（MAGI System）」追加、code-quality-guideline.md/planning-quality-guideline.md 行を追加。(C) セッション管理: quick-save コスト 3-5%、quick-load コスト 1-2% に更新。(D) サブエージェント: Memory 列追加（v4.4.1 未反映対応）。(E) スキル: lam-orchestrate 説明を「/magi 統合」に変更、/magi/clarify/ui-design-guide を新規追加。(F) ワークフローコマンド: /full-review 説明簡素化、/wave-plan に [N] 引数、/retro に [wave|phase] 引数。(G) 状態管理: knowledge/ 説明、agent-memory/ 説明の更新。(H) 参照ドキュメント: 06_DM 説明を MAGI + AoT + Reflection に変更、99_reference_generic.md 追加（v4.4.1 未反映対応）。(I) AoT クイックガイド→/magi クイックガイドに全面変更 + MAGI System 役割説明 + Reflection 追加。(J) /clarify クイックガイド新設 |
| **対象ファイル** | `CHEATSHEET.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | プロジェクト技術スタックセクション、building-checklist.md のRules 一覧記載、日常ワークフロー 7 パターン、クイックリファレンスの /ship と設計中間文書、docs/memos/middle-draft/、08_SESSION_MANAGEMENT.md/09_SUBAGENT_STRATEGY.md の参照を全て保持 |
| **依存** | T-110, T-120, T-121, T-150 |
| **サイズ** | L |

---

### Atom A8: 横断検証

#### T-170: MAGI 命名の残存チェック

| 項目 | 内容 |
|------|------|
| **Task ID** | T-170 |
| **説明** | Phase 1 対象の全ファイルで旧名称の単独出現がないことを確認する。grep 対象: (1) `Three Agents Model`（MAGI 名称のカッコ内併記は許可）、(2) `Affirmative`（Agent 名として単独出現するもの）、(3) `Mediator`（同上）。`Critical` は品質用語として使用されるため、Agent 名としての出現のみ検出 |
| **対象ファイル** | Phase 1 対象全ファイル |
| **変更種別** | 検証 |
| **影式固有考慮** | なし |
| **依存** | T-110, T-111, T-112, T-113, T-130, T-160, T-161 |
| **サイズ** | S |

#### T-171: R-5/R-6 リナンバリングの残存チェック

| 項目 | 内容 |
|------|------|
| **Task ID** | T-171 |
| **説明** | Phase 1 対象の全ファイルで旧 R-5/R-6（影式固有の異常系テスト/else デフォルト値禁止を指すもの）が R-12/R-13 に更新されていることを確認する。LAM の R-5/R-6（テスト名一致/設計書アサーション）は phase-rules.md に正しく追加されていることを確認 |
| **対象ファイル** | `.claude/rules/`, `docs/internal/` |
| **変更種別** | 検証 |
| **影式固有考慮** | building-checklist.md 内に旧 R-5/R-6 が残っていないことを確認 |
| **依存** | T-101, T-102, T-130, T-154 |
| **サイズ** | S |

#### T-172: 参照整合性の検証

| 項目 | 内容 |
|------|------|
| **Task ID** | T-172 |
| **説明** | Phase 1 で追加・変更した参照の整合性を確認する: (1) code-quality-guideline.md が phase-rules.md AUDITING から参照されている、(2) planning-quality-guideline.md が phase-rules.md PLANNING から参照されている、(3) docs/specs/lam/ パスが全ファイルで統一されている、(4) Green State 条件が phase-rules.md と code-quality-guideline.md で矛盾しない |
| **対象ファイル** | Phase 1 対象全ファイル |
| **変更種別** | 検証 |
| **影式固有考慮** | なし |
| **依存** | T-130, T-120, T-121 |
| **サイズ** | S |

#### T-173: 影式固有保持項目の全数検証

| 項目 | 内容 |
|------|------|
| **Task ID** | T-173 |
| **説明** | Section 6 の影式固有保持チェックリスト全項目（.claude/rules/ 20 項目、docs/internal/ 12 項目、CLAUDE.md 8 項目、CHEATSHEET.md 8 項目、計 48 項目）が保全されていることを確認する |
| **対象ファイル** | Phase 1 対象全ファイル |
| **変更種別** | 検証 |
| **影式固有考慮** | 本タスクの核心。全項目の存在を確認する |
| **依存** | T-100 〜 T-161 全て |
| **サイズ** | M |

---

## 4. MAGI Review of Task Decomposition

### [MELCHIOR]

タスクの並列化設計は効率的である。A1, A2, A3, A5 が全て独立しているため、4 ストリームでの並列実行が可能。A0 を先行させることで、リナンバリング対象の網羅性が事前に保証される。全 23 タスクの粒度は適切で、各タスクが独立して完結する。

特に T-130（phase-rules.md）の依存関係設計が良い。A1 のリナンバと A3 の新規ルール追加が完了してからでないと、phase-rules.md の参照コメントと新規 R-5/R-6 追加を正しく行えない。

### [BALTHASAR]

**懸念 1: T-153 の規模リスク**。07_SECURITY_AND_AUTOMATION.md Section 6 の「3 カテゴリに大幅拡充」は M サイズとしているが、Anthropic 公式ツールや CI/CD 統合例の記述量次第で L サイズに膨らむ可能性がある。LAM テンプレートの Section 6 全文を事前確認すべき。

**懸念 2: T-161 の複雑性**。CHEATSHEET.md は 10 個の変更項目 (A)〜(J) を含む L サイズタスクである。単一タスクとして扱うと、部分的な適用漏れのリスクがある。ただし、CHEATSHEET.md は単一ファイルであり分割するとコンフリクトリスクが高まるため、チェックリスト方式での対応が現実的。

**懸念 3: A6 の T-111 と A2 の重複**。06_DECISION_MAKING.md は A2（MAGI 命名）と A6（docs/internal/ 更新）の両方に属する。T-111 が A2 に含まれているが、A6 の依存に A2 があるため論理的には問題ない。ただし実行時に混乱しないよう、T-111 は明確に「A2 完了の一部」として位置付けるべき。

### [CASPAR]

MELCHIOR の並列化評価と BALTHASAR の懸念を統合する。

**結論 1**: T-153 は M サイズを維持するが、作業開始時に LAM v4.5.0 の Section 6 全文を確認し、想定以上の規模であれば T-153a/T-153b に分割する判断ポイントを設ける。

**結論 2**: T-161 は L サイズの単一タスクとして維持。ただし、(A)〜(J) の各項目にチェックマークを付ける形式で進捗管理する。実行順序は (I)(J) の /magi + /clarify クイックガイドを先に着手し、最も重要な変更を確実に反映する。

**結論 3**: T-111 は Atom A2 に帰属させる。DAG 上の依存関係は正しいため、実行順序の問題はない。

### Reflection

致命的な見落とし: なし。懸念はいずれも運用レベルの対処で解決可能。結論確定。

---

## 5. 実行順序

### Step 1: 事前確認（A0）

```
T-100 事前確認
```

### Step 2: 並列実行可能グループ（A1 + A2 + A3 + A5）

```
並列ストリーム 1: T-101 → T-102     （R-5/R-6 リナンバ）
並列ストリーム 2: T-110 → T-111 → T-112 → T-113   （MAGI 命名）
並列ストリーム 3: T-120, T-121       （新規ルール）
並列ストリーム 4: T-140, T-141, T-142, T-143, T-144, T-145  （その他 rules）
```

注: 実際のシングルセッション実行では、ストリーム 1 → ストリーム 3 → ストリーム 4 → ストリーム 2 の順が推奨。理由: ストリーム 1 と 3 は A4 のブロッカーであり早期完了が望ましい。ストリーム 2 の MAGI 命名は最も規模が大きく、集中して取り組むべき。

### Step 3: phase-rules.md（A4）

```
T-130 phase-rules.md 更新
```
前提: Step 2 のストリーム 1（T-101, T-102）とストリーム 3（T-120, T-121）が完了していること。

### Step 4: 残りの docs/internal/（A6 の残り）

```
T-150, T-151, T-152, T-153, T-154, T-155
```
前提: Step 2 のストリーム 2（MAGI 命名）が完了していること（06_DM は Step 2 で完了済み）。

### Step 5: CLAUDE.md + CHEATSHEET.md（A7）

```
T-160 → T-161
```
前提: Step 2 〜 Step 4 が全て完了していること。

### Step 6: 横断検証（A8）

```
T-170, T-171, T-172, T-173
```
前提: Step 1 〜 Step 5 が全て完了していること。

---

## 6. 影式固有保持チェックリスト

Phase 1 完了時に以下が破壊されていないことを確認する。

### .claude/rules/（20 項目）

- [ ] `core-identity.md`: Subagent 委任判断テーブルが存在する
- [ ] `core-identity.md`: コンテキスト節約原則（3 項目）が存在する
- [ ] `phase-rules.md`: `影式固有: Phase 完了判定（L-4 由来）`が存在する
- [ ] `phase-rules.md`: `影式固有: 修正後の再検証義務（A-3 由来）`が存在する
- [ ] `phase-rules.md`: `影式固有: 監査レポート完了条件`が存在する
- [ ] `phase-rules.md`: `AUDITING ルール識別子（A-1〜A-4）`が存在する
- [ ] `phase-rules.md`: Green State 5 条件テーブル（G1-G5）が存在する
- [ ] `building-checklist.md`: R-2, R-3, R-7〜R-11, S-2 が存在する（R-12, R-13 にリナンバ済み）
- [ ] `building-checklist.md`: 旧 R-5, R-6 が存在しない（R-12, R-13 に変更済み）
- [ ] `security-commands.md`: Python カテゴリ（Allow List）が存在する
- [ ] `security-commands.md`: `pip show` が存在する
- [ ] `security-commands.md`: ※1 注記（二段構成）が存在する
- [ ] `permission-levels.md`: SSOT 宣言（冒頭）が存在する
- [ ] `permission-levels.md`: 影式固有パス（docs/internal/, pyproject.toml, src/kage_shiki/, tests/, config/）が存在する
- [ ] `permission-levels.md`: 影式固有例（config.toml テンプレート, docs/internal/, tests/）が存在する
- [ ] `permission-levels.md`: 相互参照（phase-rules.md, core-identity.md, security-commands.md）が存在する
- [ ] `auto-generated/README.md`: 仕様書パスが `docs/specs/lam/` プレフィックス付きである
- [ ] `auto-generated/trust-model.md`: tdd-patterns.log の形式セクションが存在する
- [ ] `auto-generated/trust-model.md`: 仕様書パスが `docs/specs/lam/` プレフィックス付きである
- [ ] `auto-generated/trust-model.md`: パターン詳細記録先（`docs/artifacts/tdd-patterns/`）が存在する

### docs/internal/（12 項目）

- [ ] `00_PROJECT_STRUCTURE.md`: `src/kage_shiki/` パッケージ構造が存在する
- [ ] `00_PROJECT_STRUCTURE.md`: `docs/memos/middle-draft/` が記載されている
- [ ] `02_DEVELOPMENT_FLOW.md`: テスト環境 Note（pytest）が存在する
- [ ] `02_DEVELOPMENT_FLOW.md`: Wave-Based Development セクションが存在する
- [ ] `02_DEVELOPMENT_FLOW.md`: Quality Rules Integration セクションが存在する
- [ ] `02_DEVELOPMENT_FLOW.md`: Advanced Workflows セクションが存在する
- [ ] `03_QUALITY_STANDARDS.md`: Section 6（Python Coding Conventions）が存在する
- [ ] `03_QUALITY_STANDARDS.md`: Section 7（Building Defect Prevention）が存在する
- [ ] `05_MCP_INTEGRATION.md`: Phase 1 MVP Note が存在する
- [ ] `07_SECURITY_AND_AUTOMATION.md`: pytest/ruff 固有コマンドリストが存在する
- [ ] `07_SECURITY_AND_AUTOMATION.md`: 影式固有パス（PreToolUse）が存在する
- [ ] `07_SECURITY_AND_AUTOMATION.md`: 影式固有ツール列（Section 6）が存在する

### CLAUDE.md（8 項目）

- [ ] Identity に `影式 (Kage-Shiki)` が明記されている
- [ ] Project Overview（技術スタックテーブル）が存在する
- [ ] Project Scale が `Medium` である
- [ ] Hierarchy of Truth の Architecture 参照範囲が `00〜09` である
- [ ] References に `docs/memos/middle-draft/` が存在する
- [ ] Context Management の閾値が 20% である
- [ ] Context Management に残量 25% 条件が存在する
- [ ] Initial Instruction にプロジェクト名が含まれている

### CHEATSHEET.md（8 項目）

- [ ] プロジェクト技術スタックセクションが存在する
- [ ] `building-checklist.md` が Rules 一覧に記載されている
- [ ] 日常ワークフロー 7 パターンが存在する
- [ ] クイックリファレンスに `/ship` が存在する
- [ ] クイックリファレンスに `docs/memos/middle-draft/` が存在する
- [ ] ディレクトリ構造に `docs/memos/middle-draft/` が存在する
- [ ] 参照ドキュメントに `08_SESSION_MANAGEMENT.md` が存在する
- [ ] 参照ドキュメントに `09_SUBAGENT_STRATEGY.md` が存在する

---

## 7. タスクサイズ評価

| Task ID | タスク名 | サイズ |
|---------|---------|:-----:|
| T-100 | 事前確認 | S |
| T-101 | building-checklist.md リナンバ | S |
| T-102 | R-5/R-6 参照元更新 | S |
| T-110 | decision-making.md MAGI 導入 | M |
| T-111 | 06_DECISION_MAKING.md MAGI 全面導入 | L |
| T-112 | 01_REQUIREMENT_MANAGEMENT.md MAGI + /clarify | M |
| T-113 | 02_DEVELOPMENT_FLOW.md MAGI + /clarify | M |
| T-120 | code-quality-guideline.md 新規 | M |
| T-121 | planning-quality-guideline.md 新規 | M |
| T-130 | phase-rules.md 総合更新 | L |
| T-140 | security-commands.md 更新 | S |
| T-141 | permission-levels.md 更新 | S |
| T-142 | upstream-first.md 更新 | S |
| T-143 | test-result-output.md 更新 | M |
| T-144 | auto-generated/README.md 更新 | S |
| T-145 | auto-generated/trust-model.md 更新 | S |
| T-150 | 00_PROJECT_STRUCTURE.md SSOT 再構成 | L |
| T-151 | 04_RELEASE_OPS.md 更新 | S |
| T-152 | 05_MCP_INTEGRATION.md 微修正 | S |
| T-153 | 07_SECURITY_AND_AUTOMATION.md 更新 | M |
| T-154 | 03_QUALITY_STANDARDS.md リナンバ確認 | S |
| T-155 | 99_reference_generic.md タグ追加 | S |
| T-160 | CLAUDE.md 更新 | M |
| T-161 | CHEATSHEET.md 更新 | L |
| T-170 | MAGI 残存チェック | S |
| T-171 | R-5/R-6 残存チェック | S |
| T-172 | 参照整合性検証 | S |
| T-173 | 影式固有保持全数検証 | M |

**合計**: 28 タスク（S: 15、M: 9、L: 4）
