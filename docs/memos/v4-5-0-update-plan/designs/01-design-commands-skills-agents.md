# 設計: コマンド / スキル / エージェント + specs/design 取込（v4.4.1 → v4.5.0）

**作成日**: 2026-03-16
**ステータス**: Draft
**対象 Phase**: Phase 2（LAM v4.5.0 移行）
**関連**: [差分分析](../specs/00-diff-commands-skills-agents.md) | [差分サマリー](../specs/00-diff-summary.md) | [前回設計](../../v4-4-1-update-plan/designs/01-design-commands-skills-agents.md)

---

## 1. 概要

Phase 2 は LAM v4.5.0 移行のうち、**コマンド（11件）、スキル（既存4件 + 新規3件）、エージェント（8件）** の更新、および **新規 specs/design ファイルの取込** を行う。

Phase 1（ルール + docs/internal/ + CLAUDE.md）で MAGI System 命名変更、`code-quality-guideline.md`、`planning-quality-guideline.md` が導入済みであることを前提とする。

### Phase 2 の目的

1. 全コマンドに MAGI System 命名・新ルール参照を反映
2. `full-review.md` を Phase 体系から **6 Stage 体系** に全面再編
3. 新規スキル `/magi`、`/clarify`、`ui-design-guide` を導入
4. 全エージェントのモデル・権限等級を確定設計に更新
5. Scalable Code Review の specs/design を取込

### 確定済み判断（2026-03-16 承認）

| # | 判断 | 内容 |
|---|------|------|
| D1 | quality-auditor モデル | **Sonnet に変更**（Opus から）。`code-quality-guideline.md` による品質基準定量化でモデル依存度が低下 |
| D2 | task-decomposer モデル | **Haiku 維持**（現行通り） |
| D3 | requirement-analyst 権限 | **PM級に昇格**（現行 PM級。フロントマター明示を強化） |
| D4 | test-runner | **PG級・Haiku 維持**（現行通り） |
| D5 | MAGI System 命名 | 全ファイルで Three Agents → MAGI System に統一 |
| D6 | 新規スキル | `/magi`、`/clarify` を導入 |
| D7 | full-review | 6 Stage 体系に全面再編 |

### 判断の依存関係

```
D5 (MAGI命名) ─── 全コマンド・スキル・エージェントに横断的影響
D7 (full-review) ── D1 (quality-auditor Sonnet化) に関連
D6 (/magi) ─────── lam-orchestrate 更新に連鎖
D1 (quality-auditor) ── design-architect 権限判断に独立
```

---

## 2. 移行戦略

### 2.1 コマンド: ファイル別変更計画

#### 2.1.1 `full-review.md` ★最大変更

**方針**: v4.5.0 版をベースに 6 Stage 体系に全面再編。影式固有参照を上乗せ。

| 現行（影式 v4.4.1） | v4.5.0 | 影式 v4.5.0 |
|---------------------|--------|------------|
| Phase 0: ループ初期化 | Stage 0: 初期化 + Scale Detection | Stage 0: 初期化 + Scale Detection（Plan E: ~10K LOC 想定） |
| Phase 0.5: ツール検出 | Stage 0 に統合 | Stage 0 に統合 |
| Phase 1: 並列監査（4エージェント） | Stage 2: チャンク分割 + トポロジカル順レビュー | Stage 2: 並列監査（4エージェント構成維持） |
| Phase 2: レポート統合 | Stage 3: 階層的統合 + レポート生成 | Stage 3: レポート統合 + 契約カード永続化 |
| Phase 3: 全修正 | Stage 4: トポロジカル順修正 | Stage 4: 修正（PM級処理フロー詳細化） |
| Phase 4-5: 検証+完了 | Stage 5: 検証 + Green State 判定 + 完了 | Stage 5: 検証 + True Green State 判定 |
| — | Stage 1: 静的分析 + 依存グラフ（Plan A） | Stage 1: 静的分析（analyzers/ 導入後に有効化） |

**影式固有の保持・追加**:
- Stage 2 の quality-auditor #3 に `building-checklist.md` R-1〜R-13 参照を維持（R-12/R-13 は Phase 1 でリナンバ済み）
- Stage 5 の検証コマンドを影式固有に明示: `pytest tests/ -v --tb=short`、`ruff check src/ tests/`
- Stage 0 の Scale Detection: 影式は ~5K LOC のため Plan E（~10K）相当。Stage 1 の静的分析パイプラインは Phase 3（analyzers/ 導入）後に有効化
- A-1〜A-4 監査ルールを Stage 4 に記述（A-2 はスコープ外 Issue 5条件に拡充）

**実装手順**:
1. 現行 `full-review.md` をバックアップ（git 管理下のため不要だが念のため差分確認用）
2. v4.5.0 テンプレートの Stage 0〜5 構造をベースに記述
3. 各 Stage に影式固有参照を追加
4. Scalable Code Review の Plan A〜E 制御テーブルを記載（Phase 3 以降で有効化の旨注記）

---

#### 2.1.2 `planning.md`

**方針**: v4.5.0 版をベースに差分追加。

| 変更項目 | 内容 |
|---------|------|
| 構造化思考セクション | **新規追加**: `/magi` の使用条件（判断ポイント 2+、影響レイヤー 3+、選択肢 3+） |
| 権限等級セクション | **新規追加**: PLANNING フェーズの変更は原則 PM 級。`permission-levels.md` 参照 |
| 品質基準参照 | **新規追加**: `planning-quality-guideline.md` 準拠（`phase-rules.md` 経由） |
| MAGI 命名 | Phase 1 で `decision-making.md` が更新済みのため、planning.md 本体は `/magi` 参照のみ |

---

#### 2.1.3 `building.md`

**方針**: v4.5.0 版をベースに影式固有参照を維持。

| 変更項目 | 内容 |
|---------|------|
| Step 4 影響分析（Pre-Flight） | **新規追加**: 依存関係調査、直接/間接影響特定、PG/SE/PM 分類 |
| R-1〜R-6 インライン記述 | **削除**: `building-checklist.md` への参照に集約（影式では v4.4.1 で既に分離済み） |
| TDD 内省パイプライン | **独立セクション化**: `/pattern-review` コマンド連携を明記 |
| 状態ファイルフィールド | v4.5.0 形式に更新（`current_task`、`completed_tasks`） |

**影式固有の保持**:
- `building-checklist.md` への明示的参照を TDD サイクルセクションに記載

---

#### 2.1.4 `auditing.md`

**方針**: v4.5.0 版をベースに影式固有のテンプレートを維持。

| 変更項目 | 内容 |
|---------|------|
| コード明確性チェック | **新規追加**: `phase-rules.md` 参照 |
| ドキュメント整合性 | **3項目→5項目に拡充**: `.claude/` 変更の `docs/internal/` 反映チェック追加 |
| `/full-review` との使い分け | **新規追加**: 手動段階的監査 vs ワンショット自動修正のガイド |
| 成果物パス | `docs/artifacts/audit-reports/<feature>.md`（日付接頭辞削除） |

**影式固有の保持**:
- 権限等級サマリーテーブル（出力テンプレート内）

---

#### 2.1.5 `wave-plan.md`

| 変更項目 | 内容 |
|---------|------|
| 構造化思考 | **新規追加**: `/magi` の使用条件 |
| lint コマンド | 汎用化（`ruff check` → `lint チェック`）しつつ影式では `ruff` を明示 |

**影式固有の保持**: `<!-- permission-level: SE -->` 明示、5タスク分割必須の記述

---

#### 2.1.6 `ship.md`

| 変更項目 | 内容 |
|---------|------|
| Phase 2 Doc Sync | **doc-sync-flag ファーストフロー化**: flag参照 → PG/SE/PM分類 → doc-writer → フラグクリア |
| Phase 5 | push しない設計に変更（明示的分離）。`git log --oneline -N` 表示 |

**影式固有の保持**:
- Phase 1 の `*.key`, `api_key` パターン（v4.5.0 で欠落）
- Phase 2 の README_en.md / CHEATSHEET.md チェック（doc-sync-flag 未存在時フォールバック）

---

#### 2.1.7 `retro.md`

| 変更項目 | 内容 |
|---------|------|
| Step 4 反映先 | `docs/artifacts/knowledge/xxx.md`（Knowledge Layer）を追加 |
| Step 5 出力先 | `docs/artifacts/retro-<version>.md`（リリース単位）を追加 |

**影式固有の保持**: `<!-- permission-level: PM -->` 明示

---

#### 2.1.8 その他コマンド（変更小）

| コマンド | 変更内容 |
|---------|---------|
| `pattern-review.md` | 差分なし（permission-level コメント維持） |
| `project-status.md` | KPI ダッシュボード参照を `docs/specs/lam/evaluation-kpi.md` で維持。Wave 進捗を独立セクション化 |
| `quick-load.md` | description 更新。影式固有の git log フォールバック維持 |
| `quick-save.md` | description 更新、コンテキスト節約注記追加、KPI 集計サブセクション独立化 |

---

### 2.2 スキル: 新規追加 + 既存更新

#### 2.2.1 `/magi` ★新規導入

**配置先**: `.claude/skills/magi/SKILL.md` + `.claude/skills/magi/references/anchor-format.md`

| 項目 | 内容 |
|------|------|
| 目的 | MAGI System（旧 Three Agents Model）による構造化意思決定 |
| 実行フロー | Step 0: AoT Decomposition → Step 1: Divergence → Step 2: Debate → Step 3: Convergence → Step 4: Reflection → Step 5: AoT Synthesis |
| MAGI エージェント | MELCHIOR（科学者/推進者）、BALTHASAR（母/批判者）、CASPAR（女/調停者） |
| Reflection | 新規追加。全員で結論を検証（1回限り）。Bikeshedding 防止ルール適用 |
| アンカーファイル | `docs/artifacts/YYYY-MM-DD-magi-{用途}.md`（CASPAR のみ書き込み権限） |
| 参照先 | `docs/internal/06_DECISION_MAKING.md`、`docs/specs/lam/magi-skill-spec.md` |

**実装手順**:
1. `.claude/skills/magi/` ディレクトリ作成
2. `SKILL.md` を LAM v4.5.0 テンプレートから取込
3. `references/anchor-format.md` を LAM v4.5.0 テンプレートから取込
4. 影式固有のカスタマイズは不要（汎用スキル）

---

#### 2.2.2 `/clarify` ★新規導入

**配置先**: `.claude/skills/clarify/SKILL.md`

| 項目 | 内容 |
|------|------|
| 目的 | 文書の曖昧さ・矛盾・欠落をインタビュー形式で精緻化 |
| Phase 構成 | Phase 1: 文書分析 → Phase 2: 質問生成+インタビュー → Phase 3: 文書更新 → Phase 4: 完了判定 |
| 「わからない」回答時 | MAGI System を自動発動して仮決定 |
| 連携先 | `planning-quality-guideline.md` の Requirements Smells / Example Mapping |

**実装手順**:
1. `.claude/skills/clarify/` ディレクトリ作成
2. `SKILL.md` を LAM v4.5.0 テンプレートから取込
3. Three Agents 参照箇所を MAGI System に確認（テンプレート時点で対応済みのはず）

---

#### 2.2.3 `ui-design-guide` 導入（低優先度）

**配置先**: `.claude/skills/ui-design-guide/SKILL.md`

v4.4.1 で導入済みだが影式では未導入。v4.4.1 → v4.5.0 で内容変更なし。
影式は tkinter ベースのため Web 固有項目は直接適用しないが、状態設計・アクセシビリティの原則は有用。

**方針**: Phase 2 スコープに含めるが、カスタマイズ（tkinter 固有項目への置換）は将来対応とし、まず LAM テンプレートのまま導入する。

---

#### 2.2.4 `lam-orchestrate/SKILL.md` ★大幅更新

| 変更項目 | 内容 |
|---------|------|
| 構造化思考セクション | **`/magi` への委譲**: 詳細ロジックを `/magi` に移動、参照のみ記述 |
| MAGI 命名 | Three Agents → MAGI System（MELCHIOR/BALTHASAR/CASPAR） |
| アンカーファイル名 | `lam-think` → `magi`（`docs/artifacts/YYYY-MM-DD-magi-{用途}.md`） |
| references 追加 | `magi-skill.md`（magi スキルの SKILL.md コピー）を新規追加 |
| hooks 連携 | 3 hook の参照タイミング・動作を詳述、データフロー ASCII 図追加 |
| エスカレーション条件 | 3条件 → 6条件に拡充（再帰防止、コンテキスト枯渇、テスト数減少を追加） |
| `fullscan_pending` | 廃止済みとの注記追加 |

**anchor-format.md 配置方針**: LAM v4.5.0 に合わせてコピー配置とする。`magi/references/anchor-format.md` と `lam-orchestrate/references/anchor-format.md` の両方に同一内容を配置。Windows 環境ではシンボリックリンクに管理者権限が必要なため、コピーが実用的。更新時は両方を同時に更新すること。

**実装手順**:
1. v4.5.0 テンプレートをベースに SKILL.md を更新
2. `references/anchor-format.md` を MAGI 対応版に更新
3. `references/magi-skill.md` を新規追加（`/magi` の SKILL.md コピー）
4. Subagent 選択テーブル（9行）は現行維持（v4.4.1 で拡充済み）

---

#### 2.2.5 その他スキルの更新

| スキル | 変更内容 |
|--------|---------|
| `adr-template/SKILL.md` | フロントマター順序変更、`/ship` 自動起票フロー追加、参照ドキュメント更新 |
| `spec-template/SKILL.md` | Section 6「権限等級（v4.0.0）」挿入によるセクション番号 +1 ずれ対応（v4.4.1 で対応済み、差分確認のみ） |
| `skill-creator/SKILL.md` | 差分なし |

---

### 2.3 エージェント: ファイル別変更計画

#### 全エージェント共通

- MAGI System 命名への更新（description 内の `3 Agents Model` → `MAGI System`）
- フロントマター内の permission-level 記述は v4.4.1 で対応済み（確認のみ）

#### 個別変更計画

| エージェント | model 変更 | 権限変更 | その他変更 |
|------------|-----------|---------|-----------|
| **quality-auditor** | opus → **sonnet** | SE 維持 | 役割境界セクション削除、Step 3 統合（仕様ドリフト+構造整合性）、ドリフト種別 4種化、構造整合性 5観点化。**影式固有**: R-1〜R-13 品質ルール適合性チェックを Step 3b として維持 |
| **task-decomposer** | haiku 維持 | SE 維持 | AoT Step 3.5 + SPIDR タスク分割の参照追加 |
| **requirement-analyst** | sonnet 維持 | **PM級**（維持強化） | AoT Step 1.5 追加。description に MAGI 命名反映 |
| **test-runner** | haiku 維持 | **PG級**（維持） | 差分なし（確認のみ） |
| **code-reviewer** | 変更なし | SE 維持 | 役割境界セクション削除、PG/SE/PM 分類基準を独立セクション化、F 評価追加 |
| **tdd-developer** | 変更なし | SE 維持 | **Pre-flight セクション新設**: `code-quality-guideline.md` 必読、品質ゲート暗記項目追加 |
| **design-architect** | 変更なし | **PM 維持**（LAM は SE だが影式は PM を継続） | AoT Step 1.5 追加 |
| **doc-writer** | 変更なし | SE 維持 | ドキュメント自動追従モードを `/ship` Phase 2 連携版に更新 |

#### quality-auditor 変更の詳細

**Sonnet への変更根拠**（D1 承認済み）:
- `code-quality-guideline.md` が Critical/Warning/Info の判断基準を明文化したため、モデルの推論能力への依存度が低下
- 品質基準の定量化（関数50行以内、ネスト3階層以内等）により Sonnet でも十分な精度
- コスト最適化の優先（v4.4.1 移行時は Opus 維持だったが、品質ガイドライン導入で状況が変化）

**影式固有の R-1〜R-13 チェック維持方法**:
- v4.5.0 の構造整合性 5観点（スキーマ、参照、データフロー、設定、ドキュメント間）を採用
- これに加え Step 3b として「影式固有: `building-checklist.md` の R-1〜R-13 品質ルール適合性チェック」を維持
- R-12/R-13 は Phase 1 で R-5/R-6 からリナンバ済み

#### design-architect PM 維持の根拠

LAM v4.5.0 では SE に降格されているが、影式では PM を継続する。

理由:
1. 影式では設計判断（データモデル、API 設計、コンポーネント分割）がアーキテクチャ変更に直結
2. SE にすると設計変更が承認なしに実施されるリスク
3. LAM の降格理由（「PLANNING フェーズでの委任を推奨」）は等級降格の根拠として不十分

---

### 2.4 specs/design 取込

#### 新規取込ファイル

| ファイル | 取込先 | 内容 |
|---------|-------|------|
| `magi-skill-spec.md` | `docs/specs/lam/magi-skill-spec.md` | MAGI スキル仕様書 |
| `scalable-code-review-spec.md` | `docs/specs/lam/scalable-code-review-spec.md` | SCR 基本仕様 |
| `scalable-code-review-phase5-spec.md` | `docs/specs/lam/scalable-code-review-phase5-spec.md` | SCR Phase 5（Stage 再編）仕様 |
| `scalable-code-review.md` | `docs/specs/lam/scalable-code-review.md` | SCR 概要 |
| `scalable-code-review-design.md` | `docs/design/scalable-code-review-design.md` | SCR 設計書 |

**方針**: LAM v4.5.0 テンプレートからそのまま取込。影式固有のカスタマイズは不要（参照用ドキュメントのため）。`docs/design/` ディレクトリが存在しない場合は作成する。

**注意**: これらの specs/design は Phase 3（analyzers/ 導入）の前提知識として必要。Phase 2 で取込むことで、Phase 3 の作業開始時に参照可能な状態にする。

**配置先方針**: 新規 specs/design は影式の既存方針に従い `docs/specs/lam/` に配置する（LAM v4.5.0 テンプレートは `docs/specs/` 直下だが、影式では LAM 由来ファイルを `lam/` サブディレクトリで管理）。

---

## 3. 影式固有保持項目チェックリスト

Phase 2 完了時に以下の全項目が保持されていることを確認する。

### 3.1 コマンド関連

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

### 3.2 エージェント関連

- [ ] `quality-auditor.md` model: **sonnet**（D1 確定）
- [ ] `quality-auditor.md` に R-1〜R-13 品質ルール適合性チェック（Step 3b）あり
- [ ] `design-architect.md` permission-level: **PM**（影式固有維持）
- [ ] `requirement-analyst.md` permission-level: **PM**（D3 確定）
- [ ] `test-runner.md` model: **haiku**、permission-level: **PG**（D4 確定）
- [ ] `task-decomposer.md` model: **haiku**（D2 確定）

### 3.3 スキル関連

- [ ] `lam-orchestrate/references/anchor-format.md` が MAGI 対応版に更新されている
- [ ] `lam-orchestrate/references/magi-skill.md` が新規追加されている
- [ ] `magi/SKILL.md` と `magi/references/anchor-format.md` が配置されている
- [ ] `clarify/SKILL.md` が配置されている

### 3.4 プロジェクト全体

- [ ] 全ファイルで `Three Agents Model` → `MAGI System` に統一（一括検索で確認）
- [ ] 全ファイルで `Affirmative/Critical/Mediator` → `MELCHIOR/BALTHASAR/CASPAR` に統一
- [ ] アンカーファイルパスが `lam-think` → `magi` に統一

---

## 4. 検証チェックリスト（Phase 2 完了条件）

### 4.1 構造検証

- [ ] `.claude/commands/` に 11 ファイル存在（増減なし）
- [ ] `.claude/agents/` に 8 ファイル存在（増減なし）
- [ ] `.claude/skills/` に 7 スキル存在（adr-template, clarify, lam-orchestrate, magi, skill-creator, spec-template, ui-design-guide）
- [ ] `docs/specs/` に新規 4 ファイル取込済み
- [ ] `docs/design/` に新規 1 ファイル取込済み

### 4.2 内容検証

- [ ] `full-review.md` が Stage 0〜5 構成になっている
- [ ] `full-review.md` に Plan A〜E 制御テーブルがある
- [ ] 全エージェントのフロントマターに `model` と description が正しく設定されている
- [ ] `/magi` スキルの Reflection ステップ（Step 4）が記述されている
- [ ] `/clarify` スキルの Phase 1〜4 構成が記述されている
- [ ] `lam-orchestrate` の構造化思考が `/magi` への参照に変更されている
- [ ] `lam-orchestrate` のエスカレーション条件が 6 条件に拡充されている

### 4.3 MAGI 命名検証

- [ ] `grep -r "Three Agents Model" .claude/` が 0 件（後方互換の括弧書きを除く）
- [ ] `grep -r "Affirmative" .claude/commands/ .claude/agents/ .claude/skills/` が 0 件
- [ ] `grep -r "Critical" .claude/agents/` で quality-auditor の「Critical/Warning/Info」以外が 0 件
- [ ] `grep -r "Mediator" .claude/commands/ .claude/agents/ .claude/skills/` が 0 件

### 4.4 参照整合性検証

- [ ] 全コマンド・スキル・エージェントが参照する `.claude/rules/` ファイルが存在する
- [ ] `code-quality-guideline.md` を参照するファイル: `tdd-developer.md`, `quality-auditor.md`, `full-review.md`
- [ ] `planning-quality-guideline.md` を参照するファイル: `planning.md`（`phase-rules.md` 経由）
- [ ] `docs/specs/lam/magi-skill-spec.md` が存在し、`/magi` スキルから参照されている

### 4.5 既存テスト回帰

- [ ] `pytest tests/ -v --tb=short` 全件 PASSED（830 tests）
- [ ] `ruff check src/ tests/` All checks passed

---

## 5. リスクと対策

### R1: full-review.md の Stage 体系移行で既存の運用知識が失われる

**リスク**: Phase 0〜5 に慣れたユーザーが Stage 0〜5 との対応を見失う。

**対策**: full-review.md の冒頭に「v4.4.1 からの移行マッピング」テーブルを注記として記載（本設計書 Section 2.1.1 のテーブルを簡略化して転記）。安定後に削除。

### R2: quality-auditor の Sonnet 化で品質検出精度が低下する

**リスク**: Opus → Sonnet により、仕様ドリフトや構造整合性の深い分析が低下する可能性。

**対策**:
- `code-quality-guideline.md` の Critical/Warning/Info 基準が判断を補完
- 構造整合性チェック 5観点が明文化されており、モデル依存度が低い
- Phase 4（統合検証）で `/full-review` を実行し、品質低下がないか検証
- 問題がある場合は Opus に戻す（PM級判断）

### R3: 新規スキル（/magi, /clarify）の参照先ファイルが未存在

**リスク**: `/magi` が参照する `docs/specs/lam/magi-skill-spec.md` や `docs/internal/06_DECISION_MAKING.md` の MAGI 対応が不完全な場合、スキル実行時に不整合が生じる。

**対策**: Phase 1 で `06_DECISION_MAKING.md` の MAGI 対応は完了済み。`magi-skill-spec.md` は Phase 2 の specs 取込で配置する。Phase 2 の作業順序を「specs 取込 → スキル配置 → コマンド更新」とする。

### R4: lam-orchestrate のアンカーファイル名変更で既存ファイルとの不整合

**リスク**: `docs/artifacts/` に `YYYY-MM-DD-lam-think-*` 形式の既存アンカーファイルがある場合、新命名規則 `YYYY-MM-DD-magi-*` と混在する。

**対策**: 既存ファイルはリネームしない（履歴として保持）。新規作成分から `magi-` プレフィックスを使用。`lam-orchestrate` の説明に「旧 `lam-think-*` ファイルも参照可能」の注記を追加。

### R5: Phase 2 の作業規模が大きく、中断リスクがある

**リスク**: 11 コマンド + 7 スキル + 8 エージェント + 5 specs/design の更新は 1 セッションで完了しない可能性。

**対策**: 以下の作業順序で実施し、各ステップが独立して完結するようにする:
1. specs/design 取込（参照先の事前準備）
2. 新規スキル導入（/magi, /clarify, ui-design-guide）
3. lam-orchestrate 更新（/magi 依存）
4. 全エージェント更新（モデル・権限変更）
5. full-review.md 全面再編（最大変更、エージェント更新に依存）
6. その他コマンド更新（10件、並列可能）

各ステップ完了後に `/quick-save` を実行し、中断に備える。

### R6: Phase 2-3 間の /full-review 二重判定

**リスク**: Phase 2 で full-review を Stage 体系に更新後、Phase 3 で lam-stop-hook を安全ネットに縮小するまでの間に /full-review を実行すると、Stage 5 の Green State 判定と旧 stop-hook の Green State 判定が二重で動作する。

**影響度**: 高

**対策**: **Phase 2-3 間での /full-review 実行を禁止**。Phase 4（統合検証）で初めて新体制で実行する。

---

## 6. 作業順序まとめ

| 順序 | 作業 | 対象ファイル数 | 依存 |
|------|------|:------------:|------|
| 1 | specs/design 取込 | 5 | なし |
| 2 | 新規スキル導入 | 3 スキル（5ファイル） | なし |
| 3 | lam-orchestrate 更新 | 1 スキル（3ファイル） | 順序 2 |
| 4 | 既存スキル更新（adr-template, spec-template） | 2 | なし |
| 5 | 全エージェント更新 | 8 | なし |
| 6 | full-review.md 全面再編 | 1 | 順序 5（quality-auditor 仕様確定） |
| 7 | その他コマンド更新 | 10 | 順序 2（/magi 参照） |
| 8 | MAGI 命名の横断検証 | — | 順序 1〜7 全完了 |
| 9 | 影式固有保持項目チェック | — | 順序 8 |
| 10 | テスト回帰確認 | — | 順序 9 |
