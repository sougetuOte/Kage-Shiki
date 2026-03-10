# LAM 4.0.1 移行 — マスターインデックス

**作成日**: 2026-03-10
**ステータス**: Phase 3 完了（コミット済み、push待ち）

---

## 目次

- [1. 移行の目的と方針](#1-移行の目的と方針)
- [2. 差分分析ファイル一覧](#2-差分分析ファイル一覧)
- [3. Git 戦略](#3-git-戦略)
- [4. 衝突解決ポリシー](#4-衝突解決ポリシー)
- [5. Phase 別計画とチェックリスト](#5-phase-別計画とチェックリスト)
- [6. 成功基準](#6-成功基準)
- [7. ロールバック計画](#7-ロールバック計画)
- [8. Windows 固有リスク](#8-windows-固有リスク)
- [9. 影式作業の保全と再開](#9-影式作業の保全と再開)

---

## 1. 移行の目的と方針

### 目的

LAM (Living Architect Model) のハーネステンプレートを v3.x → v4.0.1 へアップデートし、
v4.0.0「免疫系アーキテクチャ」の 5 つの柱を影式プロジェクトに導入する。

### 5 つの柱

| # | 柱 | 概要 |
|---|---|------|
| 1 | 権限等級 (PG/SE/PM) | 全変更を 3 段階にリスク分類 |
| 2 | 自動ループ統合 | Stop hook による `/full-review` の自動イテレーション |
| 3 | TDD 内省パイプライン | テスト失敗パターンの自動記録 → ルール候補生成 |
| 4 | ドキュメント自動追従 | PostToolUse hook + doc-sync-flag → `/ship` 連携 |
| 5 | Green State 収束条件 | 5 条件 (テスト/lint/Issue/仕様差分/セキュリティ) の定義 |

### 基本方針

- **Template-First**: LAM 4.0.1 をベースに影式固有カスタマイズを上乗せする
- **段階的導入**: 4 Phase に分けて移行し、各 Phase でロールバック可能にする
- **影式資産の保護**: Phase 1 Retro 由来のルール (R-2〜R-11) 等は必ず保持する
- **検証駆動**: 各 Phase 完了時に検証チェックリストを実施してから次へ進む

---

## 2. 差分分析ファイル一覧

| ファイル | 対象領域 | サイズ |
|---------|---------|-------|
| [specs/00-diff-summary.md](specs/00-diff-summary.md) | 統合サマリー | 9KB |
| [specs/00-diff-claude-md.md](specs/00-diff-claude-md.md) | CLAUDE.md / CHEATSHEET.md | 21KB |
| [specs/00-diff-rules.md](specs/00-diff-rules.md) | .claude/rules/ | 22KB |
| [specs/00-diff-commands-skills-agents.md](specs/00-diff-commands-skills-agents.md) | commands/, skills/, agents/ | 29KB |
| [specs/00-diff-docs-internal.md](specs/00-diff-docs-internal.md) | docs/internal/, docs/specs/ | 20KB |
| [specs/00-diff-claude-misc.md](specs/00-diff-claude-misc.md) | settings.json, hooks/, states/ | 22KB |
| [specs/00-diff-root-files.md](specs/00-diff-root-files.md) | CHANGELOG, README, LICENSE, 新規ルートファイル | — |
| [00-kageshiki-state-preservation.md](00-kageshiki-state-preservation.md) | 影式作業状況の保全記録 | 2KB |

---

## 3. Git 戦略

### ブランチ構成

```
master (現状)
  ├─ git tag pre-lam-4.0.1    ← 移行前スナップショット
  └─ lam-4.0.1-migration      ← 移行作業ブランチ
       ├─ Phase 1 commits
       ├─ Phase 2 commits
       ├─ Phase 3 commits
       └─ Phase 4 commit (検証完了)
            └─ master へマージ
                 └─ git tag post-lam-4.0.1
```

### コミット粒度

- 論理的な変更単位でコミットする（1ファイル1コミットではない）
- 例: 「rules/ の更新 + phase-rules.md の影式固有ルール統合」は 1 コミット
- コミットメッセージに `[LAM-4.0.1]` プレフィックスを付ける

### ロールバックポイント

| タイミング | 方法 |
|-----------|------|
| Phase 0 完了時 | `git tag pre-lam-4.0.1` |
| Phase 1 完了時 | コミットハッシュを記録 |
| Phase 2 完了時 | コミットハッシュを記録 |
| Phase 3 完了時 | コミットハッシュを記録 |
| 全Phase 完了後 | `git tag post-lam-4.0.1` |

---

## 4. 衝突解決ポリシー

影式固有のカスタマイズと LAM 4.0.1 の変更が衝突する場合の解決ルール:

### 原則

1. **影式の実運用経験が優先**: Phase 1 Retro で実証されたルール (R-2〜R-11, L-1〜L-5) は LAM テンプレートより優先
2. **LAM の構造改善は受け入れ**: セクション再編、フォーマット変更、新概念の追加は受け入れる
3. **矛盾は両立を試みる**: まず共存させ、実運用で問題が出たら調整する

### 具体的な衝突と解決策

| 衝突 | 解決策 |
|------|--------|
| audit-fix-policy (全修正義務) vs PG/SE/PM (PM級は指摘のみ) | **両立**: PG/SE は即修正、PM は指摘→承認→修正のフローに。A-3 (再検証) は維持 |
| AUDITING「修正禁止」vs「PG/SE級は許可」 | **LAM 4.0.1 採用**: PG/SE 級の修正を許可に緩和。影式でも効率改善になる |
| building-checklist.md (独立ファイル) vs phase-rules.md (統合) | **並存**: phase-rules.md に LAM コアルール (R-1, R-4, S-1, S-3, S-4) を統合し、影式固有 (R-2〜R-11, S-2) は building-checklist.md に維持。phase-rules.md から参照リンク |
| quality-auditor model (opus→sonnet) | **影式判断を保持**: opus を継続使用。コスト増だがアーキテクチャ判断の品質を優先 |
| test-runner model (sonnet→haiku) | **LAM 4.0.1 採用**: haiku に変更。テスト実行は速度重視で品質影響小 |
| Phase 完了判定スモークテスト (影式固有) | **影式を保持**: phase-rules.md に影式固有セクションとして追記 |

---

## 5. Phase 別計画とチェックリスト

### Phase 0: 準備

**目的**: 安全に移行を開始できる状態を作る

- [x] 差分分析 (00-diff-*.md) — 7 ファイル完成
- [x] 影式作業状況の保全 (00-kageshiki-state-preservation.md)
- [x] CLAUDE.md に Active Migration Notice 追加
- [x] SESSION_STATE.md 更新
- [x] current-phase.md 更新
- [x] ギャップ分析（ベストプラクティス照合）
- [x] 本インデックス作成 (000-index.md)
- [x] design 文書作成 (01-design-*.md) — 4 ファイル完成、承認済み
- [x] tasks 文書作成 (02-tasks-*.md) — 4 ファイル完成
- [x] `git tag pre-lam-4.0.1` で現状を固定
- [x] `git checkout -b lam-4.0.1-migration` でブランチ作成

**Phase 0 完了条件**: design/tasks 文書が承認され、タグとブランチが作成されている

---

### Phase 1: 基盤移行

**目的**: ルール・プロセス文書・CLAUDE.md の更新（コード変更なし）
**リスク**: 低（ドキュメント変更のみ）

#### 作業項目

- [x] docs/internal/ のマージ
  - [x] 00_PROJECT_STRUCTURE.md: SSOT 3 層アーキテクチャ追加、.claude/ 配下構造更新
  - [x] 02_DEVELOPMENT_FLOW.md: TDD Introspection + 権限等級修正制御追加
  - [x] 07_SECURITY_AND_AUTOMATION.md: Section 5 (Hooks) + Section 6 (Security Tools) 追加
  - [x] 99_reference_generic.md: フェーズモードタグ追加（軽微）
  - [x] 03_QUALITY_STANDARDS.md: 影式固有セクション (6, 7) の保護を確認
- [x] .claude/rules/ の更新
  - [x] permission-levels.md: 新規追加（影式パス分類をカスタマイズ）
  - [x] upstream-first.md: 新規追加
  - [x] auto-generated/README.md: 新規追加
  - [x] auto-generated/trust-model.md: 新規追加
  - [x] core-identity.md: 権限等級セクション追加
  - [x] decision-making.md: SSOT 参照注記追加
  - [x] phase-rules.md: TDD 品質チェック統合 + AUDITING 修正ルール変更 + 影式固有保持
  - [x] security-commands.md: Layer 0/1/2 三層モデル追加 + Python コマンド保持
  - [x] building-checklist.md: R-5〜R-11, S-2 を維持、S-1/S-3/S-4 統合に合わせて再編
  - [x] audit-fix-policy.md → A-3 を phase-rules.md に統合、ファイル自体は廃止
  - [x] spec-sync.md → S-2 を building-checklist.md に移動、ファイル自体は廃止
- [x] CLAUDE.md 更新（影式固有 Project Overview は保持）
- [x] CHEATSHEET.md 更新（権限等級セクション追加、コマンド分類再編、影式固有は保持）

#### Phase 1 検証チェックリスト

- [x] 全 rules ファイルが構文エラーなく読み込めること（Claude Code 起動で確認）
- [x] `/quick-load` が正常動作すること
- [x] `/planning`、`/building`、`/auditing` の切替が正常動作すること
- [x] 影式固有ルール (R-2〜R-11) が参照可能であること
- [x] Phase 完了判定スモークテスト要件が phase-rules.md に残っていること
- [x] コミット: `[LAM-4.0.1] Phase 1: 基盤移行 — rules/docs/CLAUDE.md` (79c24db)

---

### Phase 2: コマンド / スキル / エージェント

**目的**: 操作インターフェースの更新
**リスク**: 中（コマンド動作が変わる可能性）

#### 作業項目

- [x] agents/ の更新
  - [x] 全 8 エージェントに `# permission-level` コメント追加
  - [x] quality-auditor: 仕様ドリフト + 構造整合性チェック追加（model は opus 維持）
  - [x] test-runner: model を haiku に変更
  - [x] code-reviewer: PG/SE/PM 分類出力追加
  - [x] doc-writer: ドキュメント自動追従モード追加
  - [x] 他 4 エージェント: 軽微な差分適用
- [x] skills/ の更新
  - [x] 全スキルに `version: 1.0.0` 追加
  - [x] lam-orchestrate: ループ統合セクション追加
  - [x] adr-template: `/ship` 連携フロー追加
  - [x] spec-template: 権限等級セクション追加
  - [x] ultimate-think: frontmatter 更新
  - [x] ui-design-guide: 新規追加（任意、GUI 設計時に有用）
- [x] commands/ の更新
  - [x] full-review.md: 4 エージェント構成、Green State、自動ループ（最大の変更）
  - [x] auditing.md: 権限等級修正ルール追加
  - [x] building.md: TDD 内省パイプライン連携（影式 R-1〜R-6 参照は維持）
  - [x] ship.md: doc-sync-flag 連携
  - [x] daily.md: KPI 集計セクション追加
  - [x] project-status.md: KPI ダッシュボード追加（Wave 進捗は維持）
  - [x] impact-analysis.md: PG/SE/PM 分類ステップ追加
  - [x] security-review.md: 権限等級対応表 + 自動化ツール連携
  - [x] pattern-review.md: 新規追加
  - [x] その他 (adr-create, focus, full-load/save, quick-load/save, planning): 軽微な差分
  - [x] retro.md, wave-plan.md: frontmatter 追加（description, 権限等級注記）
- [x] docs/specs/ LAM 仕様書の取り込み
  - [x] v4.0.0-immune-system-requirements.md
  - [x] v4.0.0-immune-system-design.md
  - [x] green-state-definition.md
  - [x] evaluation-kpi.md
  - [x] loop-log-schema.md
  - [x] doc-writer-spec.md
  - [x] v3.9.0-improvement-adoption.md

#### Phase 2 検証チェックリスト

- [x] `/auditing` で権限等級 (PG/SE/PM) の分類が出力されること
- [x] `/building` で TDD サイクルの R-1〜R-6 参照が有効であること
- [x] `/impact-analysis` で PG/SE/PM 分類ステップが表示されること
- [x] `/daily` で KPI セクションの骨格が表示されること
- [x] `/project-status` で Wave 進捗 + KPI の両方が出力されること
- [x] `/ship` が doc-sync-flag の存在を確認するステップを含むこと
- [x] 影式固有コマンド (`/retro`, `/wave-plan`) が変更なく動作すること
- [x] コミット: 5件 (208e85d〜5c21ed5) で完了、push済み

---

### Phase 3: Hooks + 自動化

**目的**: v4.0.0 免疫系の実行基盤を構築
**リスク**: 高（Windows 環境での hooks 動作が未検証）

#### 事前確認（Phase 3 開始前に必須）

- [x] Claude Code の hooks 機能が Windows でどう動作するか公式ドキュメントを確認
  - [x] `.sh` スクリプトが直接実行できるか → Python で実装（Windows 互換）
  - [x] `.py` / `.cmd` / `.ps1` が代替として使えるか → `.py` を採用
  - [x] settings.json の hooks 定義フォーマットを確認
- [x] 影式既存の hooks (`notify-sound.py`) との共存方法を確認

#### 作業項目

- [x] settings.json マージ
  - [x] LAM 4.0.1 の permissions 設定を導入
  - [x] 影式固有の Python 権限を維持 (settings.local.json)
  - [x] hooks 定義を追加（Windows 対応版: Python スクリプト）
- [x] hooks スクリプト作成
  - [x] hook_utils.py: 共通ユーティリティ（stdin/JSON/パス正規化/フェーズ取得）
  - [x] pre-tool-use: ファイルパスベース PG/SE/PM 判定（Windows パス対応）
  - [x] post-tool-use: TDD パターン記録 + doc-sync-flag + ループログ
  - [x] lam-stop-hook: 自動ループ制御（Green State G1/G2/G5 + ツール不在即停止）
  - [x] pre-compact: コンパクト前自動セーブ（アトミック書き込み）
  - [x] 既存 notify-sound.py との共存（sampwidth修正 + 一時ファイル改善）
- [x] auto-generated/ ディレクトリの実運用準備（README.md + trust-model.md は Phase 1 で完了）
- [x] Green State 定義の影式版策定
  - [x] G1: pytest 全パス
  - [x] G2: ruff エラーゼロ
  - [x] G3: 対応可能 Issue ゼロ（手動判断、コメントで明記）
  - [x] G4: 仕様差分ゼロ（手動判断、コメントで明記）
  - [x] G5: セキュリティチェック通過（pip-audit/safety 動的解決）

#### Phase 3 検証チェックリスト

- [x] hooks が Windows 環境で実行されること（エラーなし）
- [x] pre-tool-use hook がファイルパスから PG/SE/PM を正しく判定すること
- [x] post-tool-use hook がテスト実行結果を `.claude/tdd-patterns.log` に記録すること
- [x] notify-sound.py が引き続き動作すること（共存確認）
- [x] `/full-review` の自動ループが 3 イテレーション正常に回ること（Green State 達成）
- [x] pre-compact hook が auto-compact 前に状態を保存すること
- [x] テスト: 822 passed (hook テスト 100件)、カバレッジ 92%、ruff clean
- [x] コミット: `[LAM-4.0.1] Phase 3: Hooks + Automation — 免疫システム基盤` (b6e0200)

---

### Phase 4: 統合検証 + 完了

**目的**: 移行全体の品質を確認し、master にマージする

#### 作業項目

- [ ] 全テスト実行: `pytest` — 722 件が全パス
- [ ] ruff check クリーン
- [ ] `/full-review` を新フォーマットで実行（移行後初の完全レビュー）
- [ ] 移行結果レポート作成
- [ ] master へマージ
- [ ] `git tag post-lam-4.0.1`
- [ ] CLAUDE.md の Active Migration Notice セクション削除
- [ ] SESSION_STATE.md を最新化（移行完了を記載）
- [ ] current-phase.md を元に戻す（移行注記を削除）

#### Phase 4 検証チェックリスト（成功基準と同一）

→ [6. 成功基準](#6-成功基準) を参照

---

## 6. 成功基準

移行完了を宣言するために**全て**を満たす必要がある:

### 機能的基準

- [ ] 全テスト PASSED（回帰なし）
- [ ] ruff check クリーン
- [ ] `/planning` → `/building` → `/auditing` のフェーズ切替が正常
- [ ] `/quick-save` → `/quick-load` のセッション管理が正常
- [ ] `/full-review` が新フォーマット（4 エージェント + PG/SE/PM 分類）で実行可能
- [ ] `/ship` が doc-sync-flag チェックを含む新フローで動作
- [ ] 影式固有コマンド (`/retro`, `/wave-plan`) が変更なく動作

### 構造的基準

- [ ] 影式固有ルール (R-2〜R-11, S-2, L-4 スモークテスト) が参照可能
- [ ] docs/internal/ の全ファイルが v4.0.1 の内容を反映
- [ ] permission-levels.md が影式のパス構造に合わせてカスタマイズ済み
- [ ] docs/specs/ に LAM v4.0.0 仕様書が取り込まれている

### 安全性基準

- [ ] hooks が Windows 環境でエラーなく動作（または明示的にスキップ + 理由記録）
- [ ] settings.json の permissions が影式の運用と整合
- [ ] 既存の notify-sound.py が引き続き動作

### 運用基準

- [ ] 移行後に影式 Phase 2a の作業を再開できること
- [ ] SESSION_STATE.md が最新化されていること
- [ ] CLAUDE.md から Active Migration Notice が削除されていること

---

## 7. ロールバック計画

### 原則

- 各 Phase は独立してロールバック可能
- ロールバック後も影式の作業状況は保全される（00-kageshiki-state-preservation.md）

### Phase 別ロールバック手順

| Phase | トリガー | 手順 | 影響範囲 |
|-------|---------|------|---------|
| Phase 1 | rules/docs のマージで Claude Code 起動不可 | `git revert` で Phase 1 コミットを取消 | ドキュメントのみ |
| Phase 2 | コマンド動作不良 | Phase 2 コミットのみ revert。Phase 1 は維持可 | コマンド/スキル/エージェント |
| Phase 3 | hooks が Windows で動作しない | hooks ファイル削除 + settings.json から hooks 定義を除去。Phase 1-2 は維持可 | hooks のみ。最も独立性が高い |
| 全体 | 想定外の問題 | `git reset --hard pre-lam-4.0.1` + ブランチ削除 | 完全復旧 |

### ロールバック後の対応

1. 問題の原因を特定し、`docs/memos/v4-update-plan/` に記録
2. 修正方針を策定してから再度移行を試行
3. Phase 3 (hooks) が失敗した場合は、Phase 1-2 の成果は維持して hooks のみ後日対応とする選択肢あり

---

## 8. Windows 固有リスク

### hooks スクリプト

| リスク | 影響 | 対策 |
|-------|------|------|
| `.sh` が直接実行できない | Phase 3 全体が停止 | Claude Code の hooks が `.py` をサポートするか事前確認。Python版で代替実装 |
| パスセパレータ (`\` vs `/`) | PG/SE/PM のパス判定が誤動作 | 正規表現を Windows パスに対応させる |
| CRLF 改行コード | シェルスクリプトの実行エラー | `.gitattributes` で LF を強制、または Python 版に統一 |
| `timeout` コマンドの差異 | hooks のタイムアウト処理が失敗 | Python の `subprocess.run(timeout=...)` で代替 |

### 推奨対応

**hooks は Python で実装する**ことを推奨。理由:
- 影式は Python プロジェクトであり、ランタイムが確実に存在する
- 既存の `notify-sound.py` が Python hooks の実績
- Windows/Linux 両対応が容易

---

## 9. 影式作業の保全と再開

### 保全ファイル

| ファイル | 自動読み込み | 内容 |
|---------|:-----------:|------|
| `CLAUDE.md` Active Migration Notice | 毎セッション | 移行中であること、保全ファイルへのパス |
| `SESSION_STATE.md` | `/quick-load` 時 | 中断前タスクセクション |
| `.claude/current-phase.md` | ルールとして | フェーズ注記 + 保全ファイルパス |
| `docs/memos/v4-update-plan/00-kageshiki-state-preservation.md` | 上記から参照 | 影式作業の完全な状態記録 |

### 再開手順（移行完了後）

1. CLAUDE.md から `Active Migration Notice` セクションを削除
2. current-phase.md から移行注記を削除
3. SESSION_STATE.md を最新化（移行完了 + Phase 2a 再開を記載）
4. `docs/testing/retest-smoketest-2026-03-08.md` に従いスモークテスト再検証
5. Phase 2a 完了判定 → Phase 2b へ

### 慣らし運転

移行完了後、影式の通常作業（Phase 2a スモークテスト再検証）を**新しい LAM 4.0.1 ルール下で実施**する。
これにより以下を確認する:

- 新しい PG/SE/PM 分類が実作業で適切に機能するか
- `/full-review` の新フォーマットが影式のコードベースで正常動作するか
- hooks（導入した場合）が作業フローを阻害しないか
- 問題があれば `docs/memos/v4-update-plan/` に記録し、ルールを微調整

---

## 次のステップ

| 順序 | 作業 | 出力 |
|------|------|------|
| 完了 | design 文書作成 | `designs/01-design-*.md` (4ファイル) |
| 完了 | tasks 文書作成 | `tasks/02-tasks-*.md` (4ファイル) |
| 完了 | tasks 文書の承認 | ユーザー承認 |
| 完了 | git tag + branch 作成 | `pre-lam-4.0.1` タグ |
| 完了 | Phase 1 実施 | 79c24db |
| 完了 | Phase 2 実施 | 208e85d〜5c21ed5 (5コミット) |
| 完了 | Phase 3 実施 | b6e0200 |
| **次** | Phase 4 実施 | 統合検証 + master マージ |
