# Phase 2 タスク: コマンド / スキル / エージェント + specs/design 取込

**ステータス**: Draft
**対象設計**: `designs/01-design-commands-skills-agents.md`
**優先度**: 高（コマンド体系の大規模再編）
**依存**: Phase 1 完了（MAGI 命名、code-quality-guideline.md、planning-quality-guideline.md が導入済み）
**承認日**: 2026-03-16

---

## 1. 概要

### 1.1 Phase 2 の目的

LAM v4.5.0 の変更のうち、コマンド（11 件）、スキル（既存 4 件 + 新規 3 件）、エージェント（8 件）の更新、および新規 specs/design ファイルの取込を行う。

### 1.2 前提条件

- Phase 1 完了: MAGI System 命名、R-12/R-13 リナンバ、code-quality-guideline.md、planning-quality-guideline.md が全て適用済み
- 以下の判断が承認済み:
  - D1: quality-auditor → Sonnet に変更
  - D2: task-decomposer → Haiku 維持
  - D3: requirement-analyst → PM 級維持強化
  - D4: test-runner → PG 級・Haiku 維持
  - D5: design-architect → PM 級を維持（LAM は SE だが影式は PM を継続）
  - D6: /magi、/clarify を導入
  - D7: full-review を 6 Stage 体系に全面再編

### 1.3 完了条件

1. 全コマンド（11 件）が v4.5.0 版に更新されている
2. 新規スキル 3 件（/magi、/clarify、ui-design-guide）が配置されている
3. 既存スキル 4 件が更新されている
4. 全エージェント（8 件）のモデル・権限等級が確定設計に合致している
5. 新規 specs 4 件 + design 1 件が `docs/specs/lam/` および `docs/design/` に取込済み
6. MAGI System 命名が全ファイルで統一されている
7. 影式固有保持項目が全て保全されている（Section 6 チェックリスト全項目パス）
8. 既存テスト（830 tests）が全件 PASSED、ruff check がクリーン

### 1.4 重要な制約

**Phase 2 と Phase 3 の完了までの間、`/full-review` の実行は禁止**。理由: Phase 2 で full-review を Stage 体系に更新後、Phase 3 で lam-stop-hook を安全ネットに縮小するまでの間に /full-review を実行すると、Stage 5 の Green State 判定と旧 stop-hook の Green State 判定が二重で動作する。

---

## 2. AoT Decomposition

### 2.1 Atom 分解

| Atom | 判断内容 | 対象ファイル数 | 依存 | サイズ |
|------|----------|:------------:|------|:-----:|
| B0 | specs/design 取込（参照先の事前準備） | 5 | なし | M |
| B1 | 新規スキル導入（/magi、/clarify、ui-design-guide） | 3 スキル（5 ファイル） | なし | M |
| B2 | lam-orchestrate 更新（/magi 依存） | 1 スキル（3 ファイル） | B1 | L |
| B3 | 既存スキル更新（adr-template、spec-template） | 2 | なし | S |
| B4 | 全エージェント更新（モデル・権限変更 + MAGI 命名） | 8 | なし | L |
| B5 | full-review.md 全面再編（Stage 体系） | 1 | B4 | L |
| B6 | その他コマンド更新（10 件） | 10 | B1 | M |
| B7 | anchor-format.md コピー配置 | 2 | B1, B2 | S |
| B8 | 横断検証（MAGI 残存、参照整合性、影式固有保全、テスト回帰） | 0（検証のみ） | B0-B7 | M |

### 2.2 依存 DAG

```
B0（specs/design 取込）
 │
 ├── B1（新規スキル）──── B2（lam-orchestrate）──┐
 │                                               ├── B7（anchor-format コピー）
 ├── B3（既存スキル）                             │
 │                                               │
 ├── B4（全エージェント）── B5（full-review）     │
 │                                               │
 ├── B6（その他コマンド）──────────────────────────┘
 │                                                │
 └────────────────────────────────────────────── B8（横断検証）
```

並列可能: B0、B1、B3、B4 は全て独立して並列実行可能。B6 は B1 に依存（/magi 参照）するが、/magi を参照しないコマンドは先行着手可能。

---

## 3. タスク一覧

### Atom B0: specs/design 取込

#### T-200: 新規 specs の取込（4 件）

| 項目 | 内容 |
|------|------|
| **Task ID** | T-200 |
| **説明** | LAM v4.5.0 から以下の仕様書を `docs/specs/lam/` に取込む: (1) magi-skill-spec.md（MAGI スキル仕様書）、(2) scalable-code-review-spec.md（SCR 基本仕様）、(3) scalable-code-review-phase5-spec.md（SCR Phase 5 仕様）、(4) scalable-code-review.md（SCR 概要）。影式の規約に従い `docs/specs/lam/` サブディレクトリに配置する（LAM テンプレートの `docs/specs/` 直下ではない） |
| **対象ファイル** | `docs/specs/lam/magi-skill-spec.md`, `docs/specs/lam/scalable-code-review-spec.md`, `docs/specs/lam/scalable-code-review-phase5-spec.md`, `docs/specs/lam/scalable-code-review.md` |
| **変更種別** | 新規 |
| **影式固有考慮** | 配置先は `docs/specs/lam/`（影式の LAM 由来ファイル管理規約） |
| **依存** | なし |
| **サイズ** | M |

#### T-201: 新規 design の取込（1 件）

| 項目 | 内容 |
|------|------|
| **Task ID** | T-201 |
| **説明** | LAM v4.5.0 から scalable-code-review-design.md を `docs/design/` に取込む。`docs/design/` ディレクトリが存在しない場合は作成する |
| **対象ファイル** | `docs/design/scalable-code-review-design.md` |
| **変更種別** | 新規 |
| **影式固有考慮** | なし |
| **依存** | なし |
| **サイズ** | S |

---

### Atom B1: 新規スキル導入

#### T-210: /magi スキルの導入

| 項目 | 内容 |
|------|------|
| **Task ID** | T-210 |
| **説明** | `.claude/skills/magi/` ディレクトリを作成し、LAM v4.5.0 から以下を配置: (1) SKILL.md（MAGI System 構造化意思決定フレームワーク: Step 0 AoT Decomposition → Step 1 Divergence → Step 2 Debate → Step 3 Convergence → Step 4 Reflection → Step 5 AoT Synthesis）、(2) references/anchor-format.md（構造化思考アンカーテンプレート）。影式固有のカスタマイズは不要 |
| **対象ファイル** | `.claude/skills/magi/SKILL.md`, `.claude/skills/magi/references/anchor-format.md` |
| **変更種別** | 新規 |
| **影式固有考慮** | なし（汎用スキル） |
| **依存** | なし |
| **サイズ** | M |

#### T-211: /clarify スキルの導入

| 項目 | 内容 |
|------|------|
| **Task ID** | T-211 |
| **説明** | `.claude/skills/clarify/` ディレクトリを作成し、LAM v4.5.0 から SKILL.md を配置する。Phase 構成: Phase 1 文書分析 → Phase 2 質問生成+インタビュー → Phase 3 文書更新 → Phase 4 完了判定。Three Agents 参照箇所が MAGI System になっていることを確認 |
| **対象ファイル** | `.claude/skills/clarify/SKILL.md` |
| **変更種別** | 新規 |
| **影式固有考慮** | なし（汎用スキル）。planning-quality-guideline.md の Requirements Smells/Example Mapping と連携 |
| **依存** | なし |
| **サイズ** | S |

#### T-212: ui-design-guide スキルの導入

| 項目 | 内容 |
|------|------|
| **Task ID** | T-212 |
| **説明** | `.claude/skills/ui-design-guide/` ディレクトリを作成し、LAM v4.5.0 から SKILL.md を配置する。v4.4.1 で LAM に導入済みだが影式では未導入。tkinter 固有項目への置換は将来対応とし、まずテンプレートのまま導入 |
| **対象ファイル** | `.claude/skills/ui-design-guide/SKILL.md` |
| **変更種別** | 新規 |
| **影式固有考慮** | 影式は tkinter ベースのため Web 固有項目（レスポンシブ、LCP/CLS）は直接適用しないが、状態設計やアクセシビリティの原則は有用 |
| **依存** | なし |
| **サイズ** | S |

---

### Atom B2: lam-orchestrate 更新

#### T-220: lam-orchestrate/SKILL.md の大幅更新

| 項目 | 内容 |
|------|------|
| **Task ID** | T-220 |
| **説明** | lam-orchestrate/SKILL.md を v4.5.0 版に大幅更新する。変更点: (1) 構造化思考セクションを `/magi` への参照に変更（詳細ロジックは /magi に委譲）、(2) MAGI 命名（Three Agents → MAGI System）、(3) アンカーファイル名を `lam-think` → `magi`（`docs/artifacts/YYYY-MM-DD-magi-{用途}.md`）、(4) CASPAR のみ書き込み権限、(5) hooks 連携テーブルの拡充（3 hook の参照タイミング・動作の詳述、データフロー ASCII 図追加）、(6) エスカレーション条件を 3→6 条件に拡充（再帰防止、コンテキスト枯渇、テスト数減少を追加）、(7) `fullscan_pending` 廃止注記追加、(8) Subagent 選択テーブル（9 行）は現行維持 |
| **対象ファイル** | `.claude/skills/lam-orchestrate/SKILL.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | Subagent 選択テーブルは v4.4.1 で拡充済みのものを維持 |
| **依存** | T-210 |
| **サイズ** | L |

#### T-221: lam-orchestrate/references/ の更新

| 項目 | 内容 |
|------|------|
| **Task ID** | T-221 |
| **説明** | lam-orchestrate の references ディレクトリを更新する: (1) anchor-format.md を MAGI 対応版に更新（タイトル変更、WebSearch 条件注記追加）、(2) magi-skill.md を新規追加（/magi の SKILL.md のコピー。lam-orchestrate から magi スキルの詳細を参照するための reference ファイル） |
| **対象ファイル** | `.claude/skills/lam-orchestrate/references/anchor-format.md`, `.claude/skills/lam-orchestrate/references/magi-skill.md` |
| **変更種別** | 更新 + 新規 |
| **影式固有考慮** | なし |
| **依存** | T-210 |
| **サイズ** | M |

---

### Atom B3: 既存スキル更新

#### T-230: adr-template/SKILL.md の更新

| 項目 | 内容 |
|------|------|
| **Task ID** | T-230 |
| **説明** | adr-template/SKILL.md を v4.5.0 版に更新する: (1) フロントマターフィールド順序変更（name, description, version）、(2) 適用条件の表現変更、(3) /ship 自動起票フローの追加（/ship Phase 2 で PM 級設計判断検出時に ADR 起票を提案）、(4) 参照ドキュメントに permission-levels.md と /ship コマンドを追加 |
| **対象ファイル** | `.claude/skills/adr-template/SKILL.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | なし |
| **依存** | なし |
| **サイズ** | S |

#### T-231: spec-template/SKILL.md の差分確認

| 項目 | 内容 |
|------|------|
| **Task ID** | T-231 |
| **説明** | spec-template/SKILL.md の v4.4.1→v4.5.0 差分を確認する。v4.4.1 移行時に Section 6「権限等級」挿入によるセクション番号ずれは対応済みのため、追加差分がないことを確認するのみ |
| **対象ファイル** | `.claude/skills/spec-template/SKILL.md` |
| **変更種別** | 検証（差分なしの場合は変更不要） |
| **影式固有考慮** | なし |
| **依存** | なし |
| **サイズ** | S |

---

### Atom B4: 全エージェント更新

#### T-240: quality-auditor.md の更新（Sonnet 化 + 構造整合性 5 観点化）

| 項目 | 内容 |
|------|------|
| **Task ID** | T-240 |
| **説明** | quality-auditor.md を v4.5.0 版に更新する: (1) model を opus → **sonnet** に変更（D1 承認済み）、(2) 役割境界セクション削除、(3) Step 3 を「ドキュメント整合性監査 + 仕様ドリフトチェック」に統合、(4) 仕様ドリフト種別を 4 種に拡充（Phase/Wave 未到達を追加）、(5) 構造整合性チェックを 5 観点化（スキーマ、参照、データフロー、設定、ドキュメント間）、(6) Step 番号を 7→6 に再編、(7) 禁止事項の文言精緻化 |
| **対象ファイル** | `.claude/agents/quality-auditor.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | **Step 3b として「影式固有: building-checklist.md の R-1〜R-13 品質ルール適合性チェック」を維持**。v4.5.0 の 5 観点に加えて影式固有のチェック項目を追加配置する |
| **依存** | なし |
| **サイズ** | L |

#### T-241: tdd-developer.md の更新（Pre-flight セクション新設）

| 項目 | 内容 |
|------|------|
| **Task ID** | T-241 |
| **説明** | tdd-developer.md を v4.5.0 版に更新する: (1) description 変更、(2) Pre-flight セクション新設（4 ステップ: code-quality-guideline.md の Read 必須、タスク指定仕様書の Read 必須、変更対象ファイルの Read 必須、既存テスト構造の確認必須）、(3) 品質ゲート暗記項目追加（関数 50 行以内、ネスト 3 階層以内、エラー握りつぶし禁止、Silent Failure 禁止）、(4) 参照ドキュメントに code-quality-guideline.md 追加、(5) 旧「実装前チェック」チェックリストを Pre-flight に統合し削除 |
| **対象ファイル** | `.claude/agents/tdd-developer.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | なし |
| **依存** | なし |
| **サイズ** | M |

#### T-242: code-reviewer.md の更新（PG/SE/PM 分類基準独立化 + F 評価追加）

| 項目 | 内容 |
|------|------|
| **Task ID** | T-242 |
| **説明** | code-reviewer.md を v4.5.0 版に更新する: (1) 役割境界セクション削除、(2) PG/SE/PM 分類基準を独立セクション化（permission-levels.md 準拠を明記）、(3) 出力形式で各 Issue 先頭に権限等級ラベル配置、(4) 総合評価に F 評価を追加（A/B/C/D/F） |
| **対象ファイル** | `.claude/agents/code-reviewer.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | なし |
| **依存** | なし |
| **サイズ** | M |

#### T-243: doc-writer.md の更新（Doc Sync モード精緻化）

| 項目 | 内容 |
|------|------|
| **Task ID** | T-243 |
| **説明** | doc-writer.md を v4.5.0 版に更新する: (1) permission-level 注記を簡素化、(2) ドキュメント自動追従モードを /ship Phase 2 連携版に更新（入力仕様、処理フロー、diff 形式の Doc Sync 更新案出力） |
| **対象ファイル** | `.claude/agents/doc-writer.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | なし |
| **依存** | なし |
| **サイズ** | M |

#### T-244: requirement-analyst.md の更新（PM 級フロントマター強化）

| 項目 | 内容 |
|------|------|
| **Task ID** | T-244 |
| **説明** | requirement-analyst.md の permission-level がフロントマターで PM 級として明示されていることを確認する。description に MAGI 命名を反映。AoT Step 1.5 の参照を追加（該当する場合） |
| **対象ファイル** | `.claude/agents/requirement-analyst.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | なし |
| **依存** | なし |
| **サイズ** | S |

#### T-245: task-decomposer.md の更新（SPIDR 参照追加）

| 項目 | 内容 |
|------|------|
| **Task ID** | T-245 |
| **説明** | task-decomposer.md に AoT Step 3.5 + SPIDR タスク分割の参照を追加する。model: haiku を維持 |
| **対象ファイル** | `.claude/agents/task-decomposer.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | なし |
| **依存** | なし |
| **サイズ** | S |

#### T-246: design-architect.md の更新（PM 級維持 + AoT Step 1.5）

| 項目 | 内容 |
|------|------|
| **Task ID** | T-246 |
| **説明** | design-architect.md に AoT Step 1.5 を追加する。**permission-level は PM を維持**（LAM v4.5.0 は SE だが、影式では設計判断の重要性から PM を継続。D5 承認済み） |
| **対象ファイル** | `.claude/agents/design-architect.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | **PM 級を維持**。LAM の SE への降格は採用しない |
| **依存** | なし |
| **サイズ** | S |

#### T-247: test-runner.md の確認

| 項目 | 内容 |
|------|------|
| **Task ID** | T-247 |
| **説明** | test-runner.md の model: haiku、permission-level: PG が正しく設定されていることを確認する。v4.4.1→v4.5.0 間で本文差分なし |
| **対象ファイル** | `.claude/agents/test-runner.md` |
| **変更種別** | 検証 |
| **影式固有考慮** | なし |
| **依存** | なし |
| **サイズ** | S |

---

### Atom B5: full-review.md 全面再編

#### T-250: full-review.md の 6 Stage 体系への全面再編

| 項目 | 内容 |
|------|------|
| **Task ID** | T-250 |
| **説明** | full-review.md を Phase 0-5 体系から Stage 0-5 体系に全面再編する。最大の変更タスク。具体的な Stage 対応: Stage 0（初期化 + Scale Detection、Plan E: ~10K LOC）、Stage 1（静的分析、Phase 3 analyzers/ 導入後に有効化）、Stage 2（並列監査 4 エージェント構成維持、チャンク分割はPhase 3 以降）、Stage 3（階層的統合 + レポート生成、契約カード永続化）、Stage 4（トポロジカル順修正、PM 級処理フロー詳細化、A-1〜A-4 監査ルール記述、A-2 スコープ外 Issue 5 条件に拡充）、Stage 5（検証 + Green State 判定 + 完了、影響範囲分析、再レビューループ）。冒頭に v4.4.1 からの移行マッピングテーブルを注記として記載 |
| **対象ファイル** | `.claude/commands/full-review.md` |
| **変更種別** | 更新（全面再編） |
| **影式固有考慮** | (1) Stage 2 の quality-auditor #3 に building-checklist.md R-1〜R-13 参照を維持、(2) Stage 5 の検証コマンドを影式固有に明示: `pytest tests/ -v --tb=short`、`ruff check src/ tests/`、(3) Stage 0 の Scale Detection で影式は Plan E（~10K）相当。Stage 1 は Phase 3 後に有効化の旨を注記、(4) A-1〜A-4 を Stage 4 に記述 |
| **依存** | T-240（quality-auditor の仕様確定） |
| **サイズ** | L |

---

### Atom B6: その他コマンド更新

#### T-260: planning.md の更新（構造化思考 + 権限等級セクション追加）

| 項目 | 内容 |
|------|------|
| **Task ID** | T-260 |
| **説明** | planning.md に以下を追加: (1) 構造化思考セクション新設（/magi の使用条件: 判断ポイント 2+、影響レイヤー 3+、選択肢 3+）、(2) 権限等級セクション新設（PLANNING フェーズの変更は原則 PM 級、permission-levels.md 参照）、(3) 品質基準参照の追加（planning-quality-guideline.md 準拠、phase-rules.md 経由） |
| **対象ファイル** | `.claude/commands/planning.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | なし |
| **依存** | T-210 |
| **サイズ** | S |

#### T-261: building.md の更新（Pre-Flight 追加 + TDD 内省独立化）

| 項目 | 内容 |
|------|------|
| **Task ID** | T-261 |
| **説明** | building.md を v4.5.0 版に更新する: (1) Step 4 影響分析（Pre-Flight）新設（依存関係調査、直接/間接影響特定、PG/SE/PM 分類）、(2) R-1〜R-6 のインライン記述を削除し building-checklist.md への参照に集約（影式では既に分離済みだが、参照の明示を強化）、(3) TDD 内省パイプラインを独立セクション化（/pattern-review 連携明記）、(4) 状態ファイルフィールドを v4.5.0 形式に更新 |
| **対象ファイル** | `.claude/commands/building.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | building-checklist.md への明示的参照を TDD サイクルセクションに記載。R-1〜R-13 の参照を維持 |
| **依存** | なし |
| **サイズ** | M |

#### T-262: auditing.md の更新（明確性チェック + /full-review 使い分け）

| 項目 | 内容 |
|------|------|
| **Task ID** | T-262 |
| **説明** | auditing.md を v4.5.0 版に更新する: (1) コード明確性チェック新設（phase-rules.md 参照）、(2) ドキュメント整合性を 3→5 項目に拡充（.claude/ 変更の docs/internal/ 反映チェック等）、(3) /full-review との使い分けガイド新設（手動段階的監査 vs ワンショット自動修正）、(4) 成果物パスから日付接頭辞を削除 |
| **対象ファイル** | `.claude/commands/auditing.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | 権限等級サマリーテーブル（出力テンプレート内）を維持 |
| **依存** | なし |
| **サイズ** | M |

#### T-263: ship.md の更新（doc-sync-flag ファーストフロー + push 分離）

| 項目 | 内容 |
|------|------|
| **Task ID** | T-263 |
| **説明** | ship.md を v4.5.0 版に更新する: (1) Phase 2 を doc-sync-flag ファーストフローに変更（flag 参照→PG/SE/PM 分類→doc-writer 呼び出し→フラグクリア）、(2) Phase 5 で push しない設計に変更（git log --oneline -N 表示のみ）、(3) ADR 起票提案フローを Phase 2 に追加 |
| **対象ファイル** | `.claude/commands/ship.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | (1) Phase 1 の `*.key`, `api_key` パターンを維持（v4.5.0 で欠落）、(2) Phase 2 の README_en.md / CHEATSHEET.md チェックを doc-sync-flag 未存在時のフォールバックとして維持 |
| **依存** | なし |
| **サイズ** | M |

#### T-264: wave-plan.md の更新（構造化思考 + lint 汎用化）

| 項目 | 内容 |
|------|------|
| **Task ID** | T-264 |
| **説明** | wave-plan.md に以下を追加/変更: (1) 構造化思考セクション新設（/magi の使用条件）、(2) lint コマンドを汎用化（「lint チェッククリーン」）しつつ影式では ruff を明示 |
| **対象ファイル** | `.claude/commands/wave-plan.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | `<!-- permission-level: SE -->` 明示を維持。5 タスク分割必須の記述を維持 |
| **依存** | T-210 |
| **サイズ** | S |

#### T-265: retro.md の更新（Knowledge Layer + リリース単位出力）

| 項目 | 内容 |
|------|------|
| **Task ID** | T-265 |
| **説明** | retro.md に以下を追加: (1) Step 4 アクション抽出の反映先に `docs/artifacts/knowledge/xxx.md` を追加、(2) Step 5 出力先に `docs/artifacts/retro-<version>.md`（リリース単位）を追加 |
| **対象ファイル** | `.claude/commands/retro.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | `<!-- permission-level: PM -->` 明示を維持 |
| **依存** | なし |
| **サイズ** | S |

#### T-266: project-status.md の更新（KPI ダッシュボード + Wave 進捗独立化）

| 項目 | 内容 |
|------|------|
| **Task ID** | T-266 |
| **説明** | project-status.md に以下を適用: (1) Wave 進捗を独立セクションとして分離、(2) KPI ダッシュボード参照パスを `docs/specs/lam/evaluation-kpi.md` で維持（影式固有パス）、(3) ステータス列に approved/warning/blocked を追加 |
| **対象ファイル** | `.claude/commands/project-status.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | KPI 計算ロジック（K1〜K5）のインライン記述を維持。`docs/specs/lam/` パスを維持 |
| **依存** | なし |
| **サイズ** | S |

#### T-267: quick-load.md の更新（description + コンテキスト節約）

| 項目 | 内容 |
|------|------|
| **Task ID** | T-267 |
| **説明** | quick-load.md の description を「セッション状態のロード（SESSION_STATE.md + 関連ドキュメント特定）」に更新する |
| **対象ファイル** | `.claude/commands/quick-load.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | フォールバック時の git log 推定機能を維持（v4.5.0 では簡略化されているが影式では有用） |
| **依存** | なし |
| **サイズ** | S |

#### T-268: quick-save.md の更新（description + KPI 集計独立化）

| 項目 | 内容 |
|------|------|
| **Task ID** | T-268 |
| **説明** | quick-save.md に以下を適用: (1) description を「セッション状態のセーブ（SESSION_STATE.md + ループログ + Daily 記録）」に更新、(2) コンテキスト節約注記追加、(3) Daily 記録のセクション構成を簡略化、(4) KPI 集計を独立サブセクション化 |
| **対象ファイル** | `.claude/commands/quick-save.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | なし |
| **依存** | なし |
| **サイズ** | S |

#### T-269: pattern-review.md の確認

| 項目 | 内容 |
|------|------|
| **Task ID** | T-269 |
| **説明** | pattern-review.md の差分がないことを確認する。`<!-- permission-level: PM -->` の HTML コメントが維持されていることを確認 |
| **対象ファイル** | `.claude/commands/pattern-review.md` |
| **変更種別** | 検証 |
| **影式固有考慮** | permission-level コメントを維持 |
| **依存** | なし |
| **サイズ** | S |

---

### Atom B7: anchor-format.md コピー配置

#### T-270: anchor-format.md の両スキルへのコピー配置確認

| 項目 | 内容 |
|------|------|
| **Task ID** | T-270 |
| **説明** | anchor-format.md が以下の 2 箇所に同一内容で配置されていることを確認する: (1) `.claude/skills/magi/references/anchor-format.md`、(2) `.claude/skills/lam-orchestrate/references/anchor-format.md`。Windows 環境ではシンボリックリンクに管理者権限が必要なため、コピー配置とする。更新時は両方を同時に更新する旨の注記を lam-orchestrate の SKILL.md 内に記載 |
| **対象ファイル** | 2 ファイル（上記） |
| **変更種別** | 検証 |
| **影式固有考慮** | Windows 環境ではシンボリックリンクではなくコピー配置 |
| **依存** | T-210, T-221 |
| **サイズ** | S |

---

### Atom B8: 横断検証

#### T-280: MAGI 命名の横断検証

| 項目 | 内容 |
|------|------|
| **Task ID** | T-280 |
| **説明** | Phase 2 対象の全ファイル（commands/、agents/、skills/）で旧名称の残存チェックを実施する: (1) `grep -r "Three Agents Model" .claude/` で 0 件（後方互換の括弧書きを除く）、(2) `grep -r "Affirmative" .claude/commands/ .claude/agents/ .claude/skills/` で 0 件、(3) `grep -r "Mediator" .claude/commands/ .claude/agents/ .claude/skills/` で 0 件、(4) `grep -r "lam-think" .claude/` で 0 件（アンカーファイル名の移行確認） |
| **対象ファイル** | `.claude/commands/`, `.claude/agents/`, `.claude/skills/` |
| **変更種別** | 検証 |
| **影式固有考慮** | なし |
| **依存** | T-220, T-240〜T-247, T-250〜T-269 |
| **サイズ** | S |

#### T-281: 参照整合性の検証

| 項目 | 内容 |
|------|------|
| **Task ID** | T-281 |
| **説明** | Phase 2 で追加・変更した参照の整合性を確認する: (1) 全コマンド・スキル・エージェントが参照する .claude/rules/ ファイルが存在する、(2) code-quality-guideline.md を参照するファイル: tdd-developer.md、quality-auditor.md、full-review.md、(3) planning-quality-guideline.md を参照するファイル: planning.md（phase-rules.md 経由）、(4) docs/specs/lam/magi-skill-spec.md が存在し /magi スキルから参照されている、(5) lam-orchestrate から /magi への参照が正しい |
| **対象ファイル** | Phase 2 対象全ファイル |
| **変更種別** | 検証 |
| **影式固有考慮** | docs/specs/lam/ パスの統一確認 |
| **依存** | T-200, T-210, T-220, T-250 |
| **サイズ** | S |

#### T-282: 構造検証

| 項目 | 内容 |
|------|------|
| **Task ID** | T-282 |
| **説明** | Phase 2 完了時のファイル構成を確認する: (1) .claude/commands/ に 11 ファイル（増減なし）、(2) .claude/agents/ に 8 ファイル（増減なし）、(3) .claude/skills/ に 7 スキル（adr-template, clarify, lam-orchestrate, magi, skill-creator, spec-template, ui-design-guide）、(4) docs/specs/lam/ に新規 4 ファイル、(5) docs/design/ に新規 1 ファイル |
| **対象ファイル** | ディレクトリ構造 |
| **変更種別** | 検証 |
| **影式固有考慮** | なし |
| **依存** | B0〜B7 全て |
| **サイズ** | S |

#### T-283: 影式固有保持項目の全数検証

| 項目 | 内容 |
|------|------|
| **Task ID** | T-283 |
| **説明** | Section 6 の影式固有保持チェックリスト全項目（コマンド 11 項目、エージェント 6 項目、スキル 4 項目、プロジェクト全体 3 項目、計 24 項目）が保全されていることを確認する |
| **対象ファイル** | Phase 2 対象全ファイル |
| **変更種別** | 検証 |
| **影式固有考慮** | 本タスクの核心 |
| **依存** | B0〜B7 全て |
| **サイズ** | M |

#### T-284: テスト回帰確認

| 項目 | 内容 |
|------|------|
| **Task ID** | T-284 |
| **説明** | 既存テストの回帰がないことを確認する: (1) `pytest tests/ -v --tb=short` で全件 PASSED（830 tests）、(2) `ruff check src/ tests/` で All checks passed。Phase 2 はドキュメント・設定変更のみだがコマンド構造の変更が hooks の動作に影響する可能性を排除するための確認 |
| **対象ファイル** | テストスイート |
| **変更種別** | 検証 |
| **影式固有考慮** | なし |
| **依存** | B0〜B7 全て |
| **サイズ** | S |

---

## 4. MAGI Review of Task Decomposition

### [MELCHIOR]

タスク分解の粒度は適切。特に以下の設計判断を評価する:

1. **B0 を先行実行**: specs/design の取込を最初に行うことで、後続タスクで参照される仕様書が事前に配置される。これにより参照先の不在エラーを回避できる。

2. **B4 と B5 の分離**: エージェント更新（B4）と full-review（B5）を分離し、B5 が B4 に依存する構造は正しい。full-review は quality-auditor の仕様（Sonnet 化、5 観点化）が確定していないと Stage 2 の記述ができない。

3. **B6 の並列可能性**: 10 コマンド中、/magi を参照する planning.md と wave-plan.md のみが B1 に依存。残り 8 コマンドは独立して先行着手可能。

### [BALTHASAR]

**懸念 1: T-250 の規模リスク**。full-review.md の全面再編は L サイズだが、実際には Stage 0〜5 の 6 セクション全てを書き換える必要がある。1 タスクとして完了するには 1 セッション以上かかる可能性がある。ただし、分割するとファイル内の整合性維持が困難になるため、単一タスクとしつつ中断ポイントを Stage 単位で設けるべき。

**懸念 2: /full-review 実行禁止制約の運用リスク**。Phase 2 完了後、Phase 3 完了までの間に /full-review が実行される事故のリスクがある。SESSION_STATE.md に制約を明記し、/quick-load 時に警告が表示されるようにすべき。

**懸念 3: T-220 の lam-orchestrate 更新と T-221 の references 更新の依存関係**。T-221 で magi-skill.md を配置するためには T-210（/magi 導入）が完了している必要があるが、T-220 の SKILL.md 更新自体は T-210 と独立して進められる部分もある。ただし依存を明示している現在の構造で問題はない。

**懸念 4: quality-auditor の Sonnet 化による品質低下の検証方法が不十分**。T-284 のテスト回帰確認は src/tests レベルの回帰であり、quality-auditor の品質検出精度は /full-review でしか検証できない。しかし Phase 2-3 間で /full-review は禁止されている。Phase 4 統合検証での確認に委ねる構造は正しいが、リスクとして明示すべき。

### [CASPAR]

MELCHIOR の効率性評価と BALTHASAR の懸念を統合する。

**結論 1**: T-250 は L サイズ単一タスクとして維持。ただし Stage 0/1 → Stage 2/3 → Stage 4/5 の 3 段階で中間セーブを推奨する注記を追加する。

**結論 2**: /full-review 実行禁止制約は Phase 2 完了時の /quick-save で SESSION_STATE.md に「注意: Phase 3 完了まで /full-review 実行禁止」と明記する運用とする。タスク一覧には追加しない（Phase 2 の /quick-save 実行時に自然に記録される）。

**結論 3**: 依存関係は現状で正しい。T-220 と T-221 を同一 Atom（B2）にまとめているため、実行順序は自然に保証される。

**結論 4**: quality-auditor の品質検証は Phase 4 統合検証（本タスクスコープ外）に委ねる。Phase 2 の完了条件にはテスト回帰のみを含め、/full-review による品質検証は Phase 4 で実施する。この制約はリスクセクションに明記済み（設計書 Section 5 R2）。

### Reflection

致命的な見落とし: なし。BALTHASAR の懸念 4 は Phase 4 で対処可能であり、Phase 2 のタスク分解への影響はない。結論確定。

---

## 5. 実行順序

### Step 1: 参照先の事前準備（B0）

```
T-200 specs 取込（4 件）
T-201 design 取込（1 件）
```

### Step 2: 並列実行可能グループ（B1 + B3 + B4）

```
並列ストリーム 1: T-210 → T-211 → T-212    （新規スキル）
並列ストリーム 2: T-230, T-231              （既存スキル）
並列ストリーム 3: T-240 → T-241 → T-242 → T-243 → T-244 → T-245 → T-246 → T-247
                                              （全エージェント。T-240 quality-auditor を最優先）
```

注: シングルセッション実行では、ストリーム 1 を最優先（B2、B5、B6 のブロッカー）。ストリーム 3 の T-240 を次に実行（B5 のブロッカー）。

### Step 3: lam-orchestrate 更新（B2）

```
T-220 lam-orchestrate SKILL.md
T-221 lam-orchestrate references/
```
前提: Step 2 のストリーム 1（T-210）が完了していること。

### Step 4: full-review.md 全面再編（B5）

```
T-250 full-review.md（Stage 0/1 → Stage 2/3 → Stage 4/5 の 3 段階で中間セーブ推奨）
```
前提: Step 2 のストリーム 3（T-240 quality-auditor の仕様確定）が完了していること。

### Step 5: その他コマンド更新（B6）

```
/magi 非依存（先行可能）: T-261, T-262, T-263, T-265, T-266, T-267, T-268, T-269
/magi 依存: T-260, T-264
```
前提: /magi 依存タスクは Step 2 のストリーム 1（T-210）が完了していること。

### Step 6: anchor-format コピー確認（B7）

```
T-270 anchor-format.md 両スキル配置確認
```
前提: Step 2 ストリーム 1 + Step 3 が完了していること。

### Step 7: 横断検証（B8）

```
T-280 MAGI 命名横断検証
T-281 参照整合性検証
T-282 構造検証
T-283 影式固有保持全数検証
T-284 テスト回帰確認
```
前提: Step 1〜Step 6 が全て完了していること。

---

## 6. 影式固有保持チェックリスト

Phase 2 完了時に以下が破壊されていないことを確認する。

### コマンド関連（11 項目）

- [ ] `full-review.md` Stage 2 に `building-checklist.md` R-1〜R-13 参照あり
- [ ] `full-review.md` Stage 5 に `pytest tests/ -v --tb=short` / `ruff check src/ tests/` あり
- [ ] `full-review.md` Stage 4 に A-1〜A-4 監査ルールあり
- [ ] `ship.md` Phase 1 に `*.key` / `api_key` パターンあり
- [ ] `ship.md` Phase 2 に README_en.md / CHEATSHEET.md フォールバックあり
- [ ] `retro.md` に `<!-- permission-level: PM -->` あり
- [ ] `pattern-review.md` に `<!-- permission-level: PM -->` あり
- [ ] `wave-plan.md` に `<!-- permission-level: SE -->` あり
- [ ] `quick-load.md` に git log フォールバック推定機能あり
- [ ] `auditing.md` 出力テンプレートに権限等級サマリーテーブルあり
- [ ] `project-status.md` に KPI 計算ロジック（K1〜K5）インライン記述あり

### エージェント関連（6 項目）

- [ ] `quality-auditor.md` model: **sonnet**（D1 確定）
- [ ] `quality-auditor.md` に R-1〜R-13 品質ルール適合性チェック（Step 3b）あり
- [ ] `design-architect.md` permission-level: **PM**（影式固有維持）
- [ ] `requirement-analyst.md` permission-level: **PM**（D3 確定）
- [ ] `test-runner.md` model: **haiku**、permission-level: **PG**（D4 確定）
- [ ] `task-decomposer.md` model: **haiku**（D2 確定）

### スキル関連（4 項目）

- [ ] `lam-orchestrate/references/anchor-format.md` が MAGI 対応版に更新されている
- [ ] `lam-orchestrate/references/magi-skill.md` が新規追加されている
- [ ] `magi/SKILL.md` と `magi/references/anchor-format.md` が配置されている
- [ ] `clarify/SKILL.md` が配置されている

### プロジェクト全体（3 項目）

- [ ] 全ファイルで `Three Agents Model` → `MAGI System` に統一（括弧書き併記を除く）
- [ ] 全ファイルで `Affirmative/Critical/Mediator` → `MELCHIOR/BALTHASAR/CASPAR` に統一
- [ ] アンカーファイルパスが `lam-think` → `magi` に統一

---

## 7. タスクサイズ評価

| Task ID | タスク名 | サイズ |
|---------|---------|:-----:|
| T-200 | specs 取込（4 件） | M |
| T-201 | design 取込（1 件） | S |
| T-210 | /magi スキル導入 | M |
| T-211 | /clarify スキル導入 | S |
| T-212 | ui-design-guide スキル導入 | S |
| T-220 | lam-orchestrate SKILL.md 更新 | L |
| T-221 | lam-orchestrate references 更新 | M |
| T-230 | adr-template 更新 | S |
| T-231 | spec-template 差分確認 | S |
| T-240 | quality-auditor 更新 | L |
| T-241 | tdd-developer 更新 | M |
| T-242 | code-reviewer 更新 | M |
| T-243 | doc-writer 更新 | M |
| T-244 | requirement-analyst 更新 | S |
| T-245 | task-decomposer 更新 | S |
| T-246 | design-architect 更新 | S |
| T-247 | test-runner 確認 | S |
| T-250 | full-review.md 全面再編 | L |
| T-260 | planning.md 更新 | S |
| T-261 | building.md 更新 | M |
| T-262 | auditing.md 更新 | M |
| T-263 | ship.md 更新 | M |
| T-264 | wave-plan.md 更新 | S |
| T-265 | retro.md 更新 | S |
| T-266 | project-status.md 更新 | S |
| T-267 | quick-load.md 更新 | S |
| T-268 | quick-save.md 更新 | S |
| T-269 | pattern-review.md 確認 | S |
| T-270 | anchor-format コピー確認 | S |
| T-280 | MAGI 命名横断検証 | S |
| T-281 | 参照整合性検証 | S |
| T-282 | 構造検証 | S |
| T-283 | 影式固有保持全数検証 | M |
| T-284 | テスト回帰確認 | S |

**合計**: 34 タスク（S: 19、M: 11、L: 4）
