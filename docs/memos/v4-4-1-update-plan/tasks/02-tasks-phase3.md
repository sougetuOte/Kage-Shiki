# Phase 3 タスク: コマンド / スキル / エージェント

**ステータス**: Draft
**対象設計**:
- `01-design-commands-skills-agents.md` — 全判断（コマンド廃止、quick-save/load拡張、full-review拡張、retro/ship更新、ultimate-think廃止、エージェント更新）
**優先度**: 高（メインワークフローの大幅変更）
**依存**: Phase 2 完了

---

## タスク一覧（グループ別概要）

| グループ | 対象 | タスク数 | 権限等級 | 規模 |
|---------|------|---------|---------|------|
| P3A: コマンド廃止 | 7コマンド削除 | 1 | PM 級 | S |
| P3B: quick-save/load拡張 | 2コマンド置き換え | 4 | PM 級 | M |
| P3C: full-review拡張 | 引数必須化、pm_pending、レポート永続化 | 3 | PM 級 | L |
| P3D: retro/ship/auditing/building/planning更新 | 5コマンド更新 | 5 | PM 級 | M |
| P3E: ultimate-think廃止 | スキル削除、lam-orchestrate統合 | 2 | PM 級 | M |
| P3F: エージェント更新 | 全8エージェント | 3 | PM 級 | M |
| **合計** | — | **18** | PM 級 | **L** |

---

## Phase 3A: 7コマンド廃止

### P3A-1: 廃止コマンド 7 件の削除

**概要**: LAM v4.4.1 で廃止された以下の 7 コマンドを削除。

**対応設計**: `01-design-commands-skills-agents.md` 判断1「7コマンド廃止戦略」→ 決定 A「全廃止」

**削除対象**:
```
.claude/commands/
├── daily.md        ← 削除
├── focus.md        ← 削除
├── full-load.md    ← 削除
├── full-save.md    ← 削除
├── adr-create.md   ← 削除
├── impact-analysis.md ← 削除
└── security-review.md ← 削除
```

**削除手順**:
```bash
git rm .claude/commands/daily.md
git rm .claude/commands/focus.md
git rm .claude/commands/full-load.md
git rm .claude/commands/full-save.md
git rm .claude/commands/adr-create.md
git rm .claude/commands/impact-analysis.md
git rm .claude/commands/security-review.md
```

**影式固有の注意**:
- `daily.md` は実運用で頻繁に使用されていたが、`quick-save.md` の拡張（Step 3）で機能が吸収される
- `full-load.md` の詳細な復帰情報は `quick-load.md` の 4 ステップ化で提供される
- `full-save.md` の git commit/push 機能は `/ship` に委譲される
- 削除後、`.claude/commands/` に以下ファイルが残る: `quick-save.md`, `quick-load.md`, `building.md`, `planning.md`, `auditing.md`, `wave-plan.md`, `retro.md`, `ship.md`, `pattern-review.md`, `release.md`（計 10 個）

**完了条件**:
- [ ] 7つのコマンドファイルが削除されている
- [ ] git rm で確認されている

---

## Phase 3B: quick-save / quick-load の拡張（新規依存ファイル作成含む）

### P3B-1: 新規依存ディレクトリの作成

**概要**: `quick-save.md` と `quick-load.md` が参照する新規ディレクトリを先行作成。

**対応設計**: `01-design-commands-skills-agents.md` 判断2「quick-save/load拡張」

**対象ファイル**:
```
docs/
├── daily/             ← 新規ディレクトリ（日次記録格納）
│   └── .gitkeep
├── specs/
│   ├── loop-log-schema.md      ← 新規（ループログスキーマ）
│   ├── evaluation-kpi.md       ← 新規（KPI定義）
│   └── lam/
│       ├── （既存ファイル群）
│       └── evaluation-kpi.md    ← 新規（LAM仕様版のリンク先）
```

**内容**:
- `docs/daily/`: 月別サブディレクトリは不要。`.gitkeep` のみで初期化
- `docs/specs/lam/evaluation-kpi.md`: LAM v4.4.1 の KPI スペック（参考資料）
- `docs/specs/evaluation-kpi.md`: 影式カスタマイズ版（v4.4.1 版への参照も記載）

**完了条件**:
- [ ] `docs/daily/` ディレクトリが作成され、`.gitkeep` がある
- [ ] `docs/specs/loop-log-schema.md` が作成されている
- [ ] `docs/specs/lam/evaluation-kpi.md` が配置されている

---

### P3B-2: quick-save.md の v4.4.1 版置き換え

**概要**: `quick-save.md` を v4.4.1 版で置き換え。3 ステップ化: SESSION_STATE 記録 + ループログ保存 + Daily 記録。

**対応設計**: `01-design-commands-skills-agents.md` 判断2「quick-save/load拡張」→ 決定 A「v4.4.1 版で完全置き換え」

**成果物**: `.claude/commands/quick-save.md`

**変更内容**:

| ステップ | 現行 | v4.4.1 |
|---------|------|--------|
| Step 1 | SESSION_STATE.md 記録 | SESSION_STATE.md 記録（同一） |
| Step 2 | なし | **新規**: ループログ保存（`.claude/logs/loop-*.txt` が存在する場合） |
| Step 3 | なし | **新規**: Daily 記録（`docs/daily/YYYY-MM-DD.md`）+ KPI 集計 |
| 完了報告 | 簡易 | `/ship` 案内 + Daily ファイルパス表示 |

**影式固有の注意**:
- Step 3 の KPI 集計は `docs/specs/lam/evaluation-kpi.md` の K1〜K5 指標を参照
- ループログ保存により `lam-stop-hook.py` との統合が強化される

**完了条件**:
- [ ] `quick-save.md` が 3 ステップに拡張されている
- [ ] Step 2（ループログ保存）が実装されている
- [ ] Step 3（Daily 記録 + KPI）が実装されている
- [ ] `/ship` 案内が記述されている

---

### P3B-3: quick-load.md の v4.4.1 版置き換え

**概要**: `quick-load.md` を v4.4.1 版で置き換え。4 ステップ化: 読み込み + ドキュメント特定 + 構造化サマリー表示。

**対応設計**: `01-design-commands-skills-agents.md` 判断2「quick-save/load拡張」→ 決定 A「v4.4.1 版で完全置き換え」

**成果物**: `.claude/commands/quick-load.md`

**変更内容**:

| ステップ | 現行 | v4.4.1 |
|---------|------|--------|
| Step 1 | SESSION_STATE.md を読んで 1 行報告 | SESSION_STATE.md 読み込み + フォールバック追加 |
| Step 2 | なし | **新規**: 次ステップに必要なドキュメントを特定（読み込みはまだ） |
| Step 3 | 1 行報告 | 構造化復帰サマリー（前回日付/Phase/完了要約/未完了/次ステップ/参照予定ファイル） |
| Step 4 | ユーザー指示待ち | ユーザー指示待ち（同一） |

**影式固有の注意**:
- Step 2 の「ドキュメント特定」により、ユーザーが「どのファイルを読むべきか」を事前に把握できる
- Step 3 の「参照予定ファイル」セクションは先読み読み込みを防ぐ設計

**完了条件**:
- [ ] `quick-load.md` が 4 ステップに拡張されている
- [ ] Step 2（ドキュメント特定）が実装されている
- [ ] Step 3（構造化サマリー）に参照予定ファイルが列挙される

---

### P3B-4: wave-plan.md への /ship 案内追加

**概要**: `wave-plan.md` 完了時に `/ship` を案内するテンプレートを追加（コマンド廃止対応）。

**対応設計**: `01-design-commands-skills-agents.md` 判断1「廃止コマンドの吸収」

**変更内容**:
- Wave 完了後に `/ship` を実行してレポート作成・コミットする旨を案内

**完了条件**:
- [ ] wave-plan.md 終了時に `/ship` への言及がある

---

## Phase 3C: full-review の大幅拡張

### P3C-1: 引数必須化と使用フロー整備

**概要**: `full-review <target>` で対象ファイル/ディレクトリを明示必須に変更。意図せぬ全体スキャンを防止。

**対応設計**: `01-design-commands-skills-agents.md` 判断3「full-review大幅拡張」→ 決定 A「v4.4.1ベース + 影式固有参照追加」

**成果物**: `.claude/commands/full-review.md`

**変更内容**:
```
/full-review <target>

target: 監査対象（必須）
  - ファイル: src/kage_shiki/core.py
  - ディレクトリ: src/kage_shiki/
  - "." でプロジェクト全体
```

**影式固有の注意**:
- Phase 1 の quality-auditor 呼び出しに `building-checklist.md` R-1〜R-11 参照を追加
- Phase 4 の G1/G2 検証コマンドを影式固有コマンド（pytest/ruff）に明示

**完了条件**:
- [ ] 引数が必須化されている
- [ ] building-checklist.md の R-1〜R-11 が質適合チェック項目として追加されている
- [ ] pytest/ruff コマンドが Phase 4 G1/G2 に明示されている

---

### P3C-2: pm_pending フラグのフロー実装

**概要**: PM 級 Issue 検出時に `lam-loop-state.json` に `pm_pending: true` フラグを設定。lam-stop-hook が即停止することで承認ゲートを機能させる。

**対応設計**: `01-design-commands-skills-agents.md` 判断3「full-review大幅拡張」

**成果物**: `.claude/commands/full-review.md` Phase 3 セクション

**変更内容**:
```
## Phase 3: PM 級 Issue への対応

PM 級の Issue を検出した場合:
1. 対応不可エントリリストを出力
2. pm_pending フラグを lam-loop-state.json に設定
3. ループが自動停止（lam-stop-hook.py で収束条件に達する）

ユーザー承認後:
- pm_pending フラグを clear する bash スクリプトを実行
- ループを再開
```

**完了条件**:
- [ ] PM 級 Issue 検出時の pm_pending フラグ設定が記述されている
- [ ] フラグ clear スクリプトが示されている

---

### P3C-3: レポート永続化と `/artifacts/audit-reports/` への出力

**概要**: 監査レポートを `docs/artifacts/audit-reports/YYYY-MM-DD-iter{N}.md` に永続化。監査履歴の追跡可能性向上。

**対応設計**: `01-design-commands-skills-agents.md` 判断3「full-review大幅拡張」

**成果物**: `.claude/commands/full-review.md` 完了報告セクション

**変更内容**:
```markdown
## 監査レポート出力

成果物: docs/artifacts/audit-reports/YYYY-MM-DD-iter{N}.md

形式:
- 対象: <target-file-or-dir>
- フェーズ: Phase 1, Phase 2, Phase 3, Phase 4
- Issue: Critical X件 / Warning X件 / Info X件
- Summary: [A/B/C/D評価]
```

**完了条件**:
- [ ] レポート出力先が `docs/artifacts/audit-reports/` に変更されている
- [ ] ファイル名形式が `YYYY-MM-DD-iter{N}.md` に統一されている

---

## Phase 3D: retro / ship / auditing / building / planning の更新（5コマンド）

### P3D-1: retro.md の Step 2.5 TDD パターン分析追加

**概要**: `retro.md` に Step 2.5「TDD パターン分析」を追加。`.claude/tdd-patterns.log` をレビューして、同一パターン 2 回以上の候補を検出。

**対応設計**: `01-design-commands-skills-agents.md` 判断4「retro の Step 2.5 追加」→ 決定 A「v4.4.1 版採用」

**成果物**: `.claude/commands/retro.md`

**変更内容**:
```markdown
## Step 2.5: TDD パターン分析（新規）

.claude/tdd-patterns.log を確認し、以下のパターンを検査:
- 同一テスト失敗パターンが 2 回以上観測
- ルール化の可能性がある

見つかった場合:
1. パターン詳細を `docs/artifacts/tdd-patterns/<pattern-name>.md` に記録
2. ルール候補を `.claude/rules/auto-generated/draft-NNN.md` として提案
3. 次の `/pattern-review` で PM 級承認を求める
```

**影式固有の注意**:
- `permission-level: PM` をボディ内に記述（v4.4.1 では削除）
- TDD 内省 v2 の JUnit XML データソースに基づく分析

**完了条件**:
- [ ] Step 2.5 が新規追加されている
- [ ] `.claude/tdd-patterns.log` の確認手順が記述されている
- [ ] 出力先が `docs/artifacts/tdd-patterns/` に統一されている
- [ ] `permission-level: PM` が記述されている

---

### P3D-2: ship.md の Phase 構成変更（7 → 5 Phase）と doc-sync-flag フロー

**概要**: `ship.md` を 7 Phase から 5 Phase に簡略化。Phase 2 で doc-sync-flag ファーストフロー採用。

**対応設計**: `01-design-commands-skills-agents.md` 判断5「ship の Phase 構成変更」→ 決定 A「v4.4.1 ベース + 影式固有ドキュメントチェック維持」

**成果物**: `.claude/commands/ship.md`

**変更内容**:
```markdown
## Phase 1: シークレットスキャン
  秘密パターン検出: secret, token, password, api_key 等

## Phase 2: ドキュメント同期
  doc-sync-flag が存在 → doc-writer エージェント呼び出し
  存在しない → README_en.md / CHEATSHEET.md / CHANGELOG の固定チェック（影式従来）

## Phase 3: コミット計画（旧 Phase 3 + 4 統合）
  変更内容グループ分け + コミット計画

## Phase 4: コミット実行
  git commit + 作成メッセージ確認

## Phase 5: Git push / 完了報告
  git push + 手動作業通知
  （旧 Phase 6/7 統合）
```

**影式固有の保護**:
- Phase 2 のフォールバック（README_en.md / CHEATSHEET.md）を維持
- 秘密情報パターン拡充（secret, token, password 追加）を採用

**完了条件**:
- [ ] Phase 構成が 5 に簡略化されている
- [ ] Phase 2 で doc-sync-flag フローが実装されている
- [ ] フォールバック（README_en.md 等）が記述されている

---

### P3D-3: auditing.md の レポート出力先変更

**概要**: auditing コマンドの出力先を `docs/memos/audit-report-*.md` → `docs/artifacts/audit-reports/YYYY-MM-DD-*.md` に変更。

**対応設計**: `01-design-new-directories.md` 判断6「docs/memos/ → docs/artifacts/ パス変更」

**成果物**: `.claude/commands/auditing.md`

**変更内容**:
```markdown
## 成果物

出力先: docs/artifacts/audit-reports/YYYY-MM-DD-<feature>.md

形式: 既存の監査レポート形式を継続
```

**完了条件**:
- [ ] 出力先が `docs/artifacts/audit-reports/` に変更されている

---

### P3D-4: building.md / planning.md の軽微更新

**概要**: 参照先パスの変更（`docs/memos/` → `docs/artifacts/`）が必要な部分を更新。

**対応設計**: `01-design-new-directories.md` 判断6「パス変更影響」

**変更内容**:
- `docs/memos/tdd-patterns/` → `docs/artifacts/tdd-patterns/` （該当なし）
- `docs/memos/walkthrough/` → `docs/artifacts/walkthrough/` （参照箇所確認）

**完了条件**:
- [ ] パス参照が最新化されている

---

### P3D-5: pattern-review.md の閾値 3 → 2 への変更

**概要**: TDD 内省 v2 の閾値変更（3 回 → 2 回）に対応。パターン検出が早まる。

**対応設計**: `01-design-rules-docs.md` 判断1-7「auto-generated の TDD 内省 v2 更新」（閾値 3→2 変更の根拠）

**変更内容**:
```markdown
## /pattern-review フロー

同一パターンの観測回数が 2 回以上（旧: 3 回）に到達時に候補生成。
```

**完了条件**:
- [ ] 閾値が 2 に変更されている

---

## Phase 3E: ultimate-think 廃止と lam-orchestrate 統合

### P3E-1: anchor-format.md を lam-orchestrate/references/ に移動

> **実行順序注意**: 本タスクを P3E-2（削除）より**先に**実行すること。
> 先に削除すると anchor-format.md が失われる。

**概要**: `anchor-format.md` をコピー（移動）して、`lam-orchestrate` の参照ドキュメントとして配置。

**対応設計**: `01-design-commands-skills-agents.md` 判断6「ultimate-think廃止」

**成果物**: `.claude/skills/lam-orchestrate/references/anchor-format.md`

**手順**:
```bash
mkdir -p .claude/skills/lam-orchestrate/references
cp .claude/skills/ultimate-think/references/anchor-format.md .claude/skills/lam-orchestrate/references/
git add .claude/skills/lam-orchestrate/references/anchor-format.md
git rm -r .claude/skills/ultimate-think
```

**完了条件**:
- [ ] `lam-orchestrate/references/anchor-format.md` が配置されている
- [ ] ultimate-think/ ディレクトリが削除されている

---

### P3E-2: ultimate-think スキル削除

**概要**: `ultimate-think/` ディレクトリ全体を削除。機能は `lam-orchestrate` に統合済み。

**依存**: P3E-1（anchor-format.md のコピー）が完了していること。

**対応設計**: `01-design-commands-skills-agents.md` 判断6「ultimate-think廃止」→ 決定 A「廃止 + lam-orchestrate に統合」

**完了条件**:
- [ ] `.claude/skills/ultimate-think/` ディレクトリが削除されている
- [ ] P3E-1 で `anchor-format.md` が `lam-orchestrate/references/` にコピー済み

> **注**: P3E-1 の手順に `git rm -r .claude/skills/ultimate-think` が含まれているため、
> P3E-1 完了時点で本タスクも完了となる場合がある。確認のみ実施。

---

## Phase 3F: エージェント更新（全 8 エージェント）

### P3F-1: 全エージェントへのフロントマター化

**概要**: 全 8 エージェント（code-reviewer, quality-auditor, doc-writer, design-architect, requirement-analyst, task-decomposer, tdd-developer, test-runner）の permission-level をフロントマターに移動。

**対応設計**: `01-design-commands-skills-agents.md` 判断7「エージェント更新」→ 決定 A「フロントマター化は全採用、model/permission は影式判断優先」

**成果物**: `.claude/agents/*.md`（全 8 ファイル）

**変更内容**:
```markdown
# permission-level: SE または PM

## Agent: <name>
（既存本文）
```

**影式固有の注意**:
- code-reviewer: 見出しに `# permission-level: SE` を追加
- quality-auditor: 見出しに `# permission-level: SE` を追加（model は opus 維持）
- design-architect: 見出しに `# permission-level: PM` を追加（v4.4.1 は SE だが影式では PM 維持）
- その他エージェント: 権限等級を明示

**完了条件**:
- [ ] 全 8 エージェントの冒頭に `# permission-level: XX` が追加されている
- [ ] 形式が統一されている（フロントマター）

---

### P3F-2: quality-auditor の model:opus 維持確認

**概要**: LAM v4.4.1 では quality-auditor を sonnet に変更しているが、影式では opus を維持。Step 3b（R-1〜R-11 適合チェック）も維持。

**対応設計**: `01-design-commands-skills-agents.md` 判断7「quality-auditor の model:opus 維持」

**成果物**: `.claude/agents/quality-auditor.md`

**変更内容**:
```markdown
# permission-level: SE

## Quality Auditor

Model: claude-opus（影式固有：コスト最適化よりも品質優先）

### Step 3b: R-1〜R-11 品質ルール適合性チェック（影式固有）
building-checklist.md の R-1〜R-11 ルールへの適合を確認。
```

**影式固有の注意**:
- v4.0.1 移行時の判断を継続
- 影式特有ルール（R-2, R-3, R-5〜R-11）の検証は opus 級の推論能力を必要とする

**完了条件**:
- [ ] model が opus に明示されている
- [ ] Step 3b（R-1〜R-11）が記述されている

---

### P3F-3: design-architect の permission-level:PM 維持確認

**概要**: LAM v4.4.1 では design-architect を SE に変更しているが、影式では PM を維持。設計判断の承認ゲート機能が必要。

**対応設計**: `01-design-commands-skills-agents.md` 判断7「design-architect の PM 維持」

**成果物**: `.claude/agents/design-architect.md`

**変更内容**:
```markdown
# permission-level: PM

## Design Architect

設計判断（データモデル、API設計、コンポーネント分割）はアーキテクチャ変更に相当。
承認ゲート（PM級）が必要。
```

**影式固有の注意**:
- v4.0.1 移行時の判断を継続
- LAM は「PLANNING フェーズでの委任」を理由に SE 化を提案したが、相当根拠が弱い

**完了条件**:
- [ ] permission-level が PM に明示されている

---

## 作業順序と並列化

```
Phase 3A: 7コマンド廃止
  └─ P3A-1 (削除): 15分

Phase 3B: quick-save/load 拡張（新規ファイル含む）
  ├─ P3B-1 (新規ディレクトリ): 30分
  ├─ P3B-2 (quick-save): 1時間
  ├─ P3B-3 (quick-load): 1時間
  └─ P3B-4 (wave-plan案内): 15分
  並列: P3B-1 と P3B-2/3/4 は並列可

Phase 3C: full-review 大幅拡張
  ├─ P3C-1 (引数必須化): 30分
  ├─ P3C-2 (pm_pending フラグ): 30分
  └─ P3C-3 (レポート永続化): 30分
  並列: P3C-1/2/3 は並列可

Phase 3D: retro/ship/auditing/building/planning 更新
  ├─ P3D-1 (retro.md): 1時間
  ├─ P3D-2 (ship.md): 1時間
  ├─ P3D-3 (auditing.md): 15分
  ├─ P3D-4 (building/planning): 15分
  └─ P3D-5 (pattern-review): 15分
  並列: P3D-1/2/3/4/5 は並列可

Phase 3E: ultimate-think 廃止 + lam-orchestrate 統合
  ├─ P3E-1 (anchor-format 移動): 10分  ← 先に実行
  └─ P3E-2 (ultimate-think 削除): 5分  ← P3E-1 完了後

Phase 3F: エージェント更新
  ├─ P3F-1 (フロントマター化): 1時間
  ├─ P3F-2 (quality-auditor opus 維持): 15分
  └─ P3F-3 (design-architect PM 維持): 15分
  並列: P3F-2/3 は P3F-1 完了後

総作業量: ~8-9時間
権限等級: PM 級（ワークフロー定義変更）
```

---

## Dependencies

```
Phase 3A (コマンド廃止) → Phase 3B (新規ディレクトリ作成) → Phase 3C/3D (コマンド更新)
                                                            → Phase 3E (スキル廃止)
                                                            → Phase 3F (エージェント更新)
```

---

## 検証チェックリスト

### コマンド
- [ ] 7つの廃止コマンドが削除されている
- [ ] `quick-save.md` が 3 ステップ化されている
- [ ] `quick-load.md` が 4 ステップ化されている
- [ ] `full-review.md` が引数必須化されている
- [ ] `retro.md` に Step 2.5 TDD パターン分析が追加されている
- [ ] `ship.md` が 5 Phase 構成になっている
- [ ] `auditing.md` の出力先が `docs/artifacts/audit-reports/` に変更されている
- [ ] `pattern-review.md` の閾値が 2 に変更されている

### スキル
- [ ] `ultimate-think/` ディレクトリが削除されている
- [ ] `lam-orchestrate/references/anchor-format.md` が配置されている

### エージェント
- [ ] 全 8 エージェントに permission-level フロントマターが追加されている
- [ ] quality-auditor の model が opus に明示されている
- [ ] design-architect の permission-level が PM に明示されている

---

## Notes

- **影式固有の継続**: ultimate-think 廃止に対応しても、lam-orchestrate の 9 行 Subagent テーブルは Phase 2 で既に更新済み
- **新規依存ファイル**: `docs/daily/`, `docs/specs/loop-log-schema.md` などの作成リスク対策として Phase 3B-1 を最初に実行
- **TDD 内省 v2**: Phase 3D-1（retro.md 更新）は Phase 2 の trust-model.md v2 化に依存しない（独立）
