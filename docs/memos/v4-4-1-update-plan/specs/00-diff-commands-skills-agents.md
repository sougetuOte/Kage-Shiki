# commands / skills / agents 差分分析（v4.0.1 → v4.4.1）

## 概要

本文書は、影式（Kage-Shiki）プロジェクトの現行 `.claude/` 構成（LAM v4.0.1 移行済み）と LAM v4.4.1 テンプレートの差分を網羅的に分析したものである。

### ファイル数サマリー

| カテゴリ | 現行 | LAM 4.4.1 | 共通 | 現行のみ | 4.4.1のみ |
|---------|:----:|:---------:|:----:|:-------:|:---------:|
| commands | 18 | 11 | 11 | 7 | 0 |
| skills | 5 (5スキル) | 5 (5スキル) | 4 (4スキル) | 1 | 1 |
| agents | 8 | 8 | 8 | 0 | 0 |

### v4.4.1 の主要な変更概念

LAM v4.4.1 で全体的に導入された横断的な変更:

1. **コマンド統合（7→0 削減）**: `daily`, `focus`, `full-load`, `full-save`, `adr-create`, `impact-analysis`, `security-review` が削除。各機能は残存コマンドに吸収
2. **TDD 内省パイプライン v2**: 閾値 3→2 に引き下げ、JUnit XML ベースに変更、分析を `/retro` Step 2.5 に移動
3. **出力パス変更**: `docs/memos/` → `docs/artifacts/` へ（監査レポート、Retro 記録等）
4. **ultimate-think 廃止**: 構造化思考が lam-orchestrate に統合
5. **ui-design-guide 新設**: WCAG 2.1 AA 準拠の UI 設計チェックリスト
6. **permission-level のフロントマター化**: エージェントの `# permission-level` がボディからフロントマターコメントに移動
7. **Subagent 選択テーブル拡充**: lam-orchestrate に全カスタムエージェントの対応表を追加
8. **Agent Memory**: `.claude/agent-memory/<agent-name>/` による永続記憶（v4.4.1 テンプレートに `code-reviewer` 用が存在）
9. **Knowledge Layer**: `docs/artifacts/knowledge/` による知見蓄積
10. **anchor-format.md の移動**: `ultimate-think/references/` → `lam-orchestrate/references/`

---

## commands/ 差分

### v4.4.1 で削除されたコマンド（現行のみ、7件）

| コマンド | 吸収先 | 備考 |
|---------|--------|------|
| `daily.md` | `quick-save.md` Step 3 | Daily 記録 + KPI 集計が quick-save に統合 |
| `focus.md` | 廃止 | ポモドーロ機能は外部ツールに委譲 |
| `full-load.md` | `quick-load.md` | quick-load が多段ステップ化し full-load 相当を吸収 |
| `full-save.md` | `quick-save.md` + `/ship` | セーブは quick-save、コミットは /ship に分離 |
| `adr-create.md` | `adr-template` スキル | ADR 作成はスキル経由に統一 |
| `impact-analysis.md` | `building.md` Step 4 | 影響分析が building の Pre-Flight として統合 |
| `security-review.md` | `full-review.md` Phase 1 #4 | セキュリティレビューが full-review の監査エージェントに統合 |

**影式への影響**: これらのコマンドは影式で個別に使用されている。移行時は吸収先の機能が十分にカバーしているか確認すること。特に `daily.md` の KPI 集計は `quick-save.md` に移動しているが、影式の daily 運用フローとの整合を確認する必要がある。

### 共通コマンドの差分（11件）

---

#### 1. `quick-save.md` ★重点比較

| 項目 | 現行（影式） | LAM 4.4.1 |
|------|-------------|-----------|
| frontmatter description | なし | `セッション状態のセーブ（SESSION_STATE.md + ループログ + Daily記録）` |
| 概要文 | `SESSION_STATE.md への記録のみ。git commit は行わない。` | `SESSION_STATE.md への記録 + ループログ保存 + Daily 記録。git commit は行わない（コミットは /ship を使用）。` |
| 配置先の記載 | あり（冒頭に記載） | なし（削除） |
| Step 2 | （なし） | **新規**: ループログ保存 — `.claude/logs/loop-*.txt` が存在する場合に未コミットのループログを記録に含める。`docs/specs/loop-log-schema.md` 参照 |
| Step 3 | （なし） | **新規**: Daily 記録 — `docs/daily/YYYY-MM-DD.md` に本日完了・明日の最優先・課題を記録。KPI 集計（ベースライン確立後）を含む。`.claude/logs/loop-*.txt` と `.claude/logs/permission.log` から K1〜K5 を計算 |
| 完了報告 | 簡易（再開方法のみ） | 拡張（SESSION_STATE.md 更新済み、Daily ファイルパス表示、`/ship` 案内） |

**影式固有の保護対象**: なし（現行の quick-save は汎用的な内容のみ）

**移行方針**: v4.4.1 版で置き換え可能。ただし daily 統合により `docs/daily/` ディレクトリの作成、`docs/specs/evaluation-kpi.md` と `docs/specs/loop-log-schema.md` の存在が前提となる。

---

#### 2. `quick-load.md` ★重点比較

| 項目 | 現行（影式） | LAM 4.4.1 |
|------|-------------|-----------|
| frontmatter description | なし | `セッション状態のロード（SESSION_STATE.md + 関連ドキュメント特定）` |
| 構成 | 1行フォーマット指定 + 待機指示（3行） | 4ステップの構造化フロー（36行） |
| Step 1 | SESSION_STATE.md を読み、1行で報告 | SESSION_STATE.md を読む。存在しない場合のフォールバックメッセージ追加 |
| Step 2 | （なし） | **新規**: 関連ドキュメントの特定 — SESSION_STATE.md の「コンテキスト情報」から次のステップに必要なドキュメントを特定（**読み込みはまだ行わない**） |
| Step 3 | 1行報告形式: `Phase: [X] \| 次: [Y] \| 未解決: [Z]` | 構造化復帰サマリー: 前回日付、Phase、完了要約、未完了、次ステップ、参照予定ファイルパス |
| Step 4 | 報告後ユーザー指示待ち（同一） | 同一（先回りしてファイルを読み込まない） |

**影式固有の保護対象**: なし

**移行方針**: v4.4.1 版で置き換え可能。現行の1行報告形式は簡潔だが、v4.4.1 の構造化サマリーの方が復帰時の情報量が多く実用的。

---

#### 3. `full-review.md` ★重点比較

| 項目 | 現行（影式） | LAM 4.4.1 |
|------|-------------|-----------|
| description | `全ソース網羅レビュー + 全Issue修正を一括実行` | `並列監査 + 全修正 + 検証の一気通貫レビュー` |
| 引数 | なし（暗黙的に全体対象） | **必須**: 対象ファイルまたはディレクトリ |
| `/auditing` との使い分けガイド | なし | **新規**: フェーズ切替 vs ワンショット実行の使い分け説明 |
| Phase 0 ループ初期化 | 簡易（イテレーション番号設定、フルスキャン判定） | **詳細化**: `lam-loop-state.json` の bash スクリプト生成例、状態ファイルスキーマ全フィールド定義、追加フィールド（`pm_pending`, `tool_events`）、log エントリスキーマ |
| Phase 0.5 context7 | 簡易（利用可/不可の検出のみ） | **詳細化**: 利用不可時の警告テンプレート追加、WebFetch 不使用の理由説明 |
| Phase 1 並列監査 | 影式固有: `building-checklist.md` R-1〜R-11 への参照あり | **汎用版**: R-1〜R-11 参照なし。セキュリティチェックリスト統合、リスクレベルと権限等級の対応表、小規模プロジェクト向けエージェント構成の緩和、**イテレーション2回目以降のゼロベース全ファイル監査**の明文化 |
| 仕様ドリフトチェック | 影式版に記述あり | 同内容 |
| 構造整合性チェック | 影式版に記述あり | 同内容 |
| Phase 2 レポート統合 | 簡易（PG/SE/PM 分類 + 一覧表示） | **拡張**: `docs/artifacts/audit-reports/` への永続化（ファイル名: `YYYY-MM-DD-iterN.md`）、PM級 Issue の承認ゲートフロー、レポート永続化の理由説明 |
| Phase 3 全修正 | 簡易（PG/SE/PM 分類 + A-1〜A-4） | **拡張**: PM級の処理フロー詳細（`pm_pending` フラグセット/クリアの bash スクリプト）、A-1〜A-4 は同一 |
| Phase 4 Green State | 5条件（G1〜G5）は同一 | **拡張**: 真の Green State の定義（「スキャンして0件」）、G5 セキュリティチェック詳細（ツール例、判定基準）、監査範囲と検証範囲の分離表、フルスキャン発動の bash スクリプト、状態ファイル更新手順、ループ継続/停止の判定ロジック |
| 自動ループ | hooks 導入済み/未導入の分岐あり | **詳細化**: Stop hook の挙動記述が full-review 本体に詳述 |
| Phase 5 完了報告 | 簡易 | **拡張**: 「Before=0 で Green State 確定」の表現、対応不可 Issue の追跡先記載 |
| Scalable Review | なし | **新規**: 将来拡張セクション — モジュール分割レビューの構想、`/batch` スキル参照、構想メモ・計画メモのリンク |

**影式固有の保護対象**:
- Phase 1 の `building-checklist.md` R-1〜R-11 参照
- Phase 4 の影式固有検証コマンド（`pytest tests/ -v --tb=short`、`ruff check src/ tests/`）

**移行方針**: v4.4.1 版をベースに影式固有参照を追加。特に `building-checklist.md` への参照は quality-auditor エージェント経由で維持可能。

---

#### 4. `retro.md` ★重点比較

| 項目 | 現行（影式） | LAM 4.4.1 |
|------|-------------|-----------|
| description | `振り返り - Wave/Phase完了時の学習サイクル（KPT）を実施` | `振り返り - Wave/Phase完了時の学習サイクル` |
| permission-level 記述位置 | ボディ内（`# permission-level: PM`） | なし（ボディにもフロントマターにもない） |
| Step 2.5 TDD パターン分析 | なし | **新規**: `.claude/tdd-patterns.log` 読み込み、FAIL→PASS ペア抽出、頻出パターン（2回以上）でルール候補提案、`ANALYZED` マーカー追記。`docs/specs/tdd-introspection-v2.md` Section 6 参照 |
| Step 4 アクション抽出の反映先 | `docs/xxx` | **追加**: `docs/artifacts/knowledge/xxx.md`（Knowledge Layer） |
| Step 5 出力先 | `docs/memos/retro-wave-{N}.md`、`docs/memos/retro-phase-{N}.md` | `docs/artifacts/retro-wave-{N}.md`、`docs/artifacts/retro-phase-{N}.md`、`docs/artifacts/retro-<version>.md`（リリース単位追加） |
| Phase 横断分析の出力 | `docs/memos/retro-phase-{N}.md` | `docs/artifacts/retro-phase-{N}.md` |

**影式固有の保護対象**:
- permission-level: PM の明示（v4.4.1 では削除されているが、影式では維持すべき）

**移行方針**: v4.4.1 版をベースに、permission-level 記述を維持。出力パスは `docs/memos/` → `docs/artifacts/` への一括変更として扱う。Step 2.5 は TDD 内省パイプライン v2 の導入に伴い追加。

---

#### 5. `ship.md` ★重点比較

| 項目 | 現行（影式） | LAM 4.4.1 |
|------|-------------|-----------|
| frontmatter description | なし | `論理グループ分けコミット - 変更を棚卸し・分類・コミット` |
| 配置先/呼び出しの記載 | あり（冒頭に記載） | なし（削除） |
| 引数 | `/ship dry-run` | `dry-run`（任意） |
| Phase 構成 | 7 Phase（1→2→3→4→5→6→7） | 5 Phase（1→2→3→4→5） + 手動作業通知 |
| Phase 1 棚卸し | 5ステップ（ファイル一覧→変更量→要約→秘密情報チェック→表示） | 3ステップ（一覧化→秘密情報検出→表示）。秘密情報パターンが拡充（`secret`, `token`, `password` 追加） |
| Phase 2 Doc Sync | **影式従来フロー**: CHANGELOG, README, README_en, CHEATSHEET の固定4ファイルチェック + doc-sync-flag 分岐 | **doc-sync-flag ファーストフロー**: 2-1 flag参照 → 2-2 PG/SE/PM分類 → 2-3 doc-writer エージェント呼び出し → 2-4 フラグクリア（`rm -f`）。CHANGELOG/README/CHEATSHEET の具体的チェックは doc-writer に委譲 |
| Phase 2 の影式固有 | README_en.md のチェック | なし（汎用テンプレートに統合） |
| Phase 3（旧 Phase 3） | 論理グループ分け（分類基準: 目的/レイヤー/依存関係、最大5グループ、迷うファイルの扱い） | グループ分け + コミット計画を統合（Phase 3 = 旧 Phase 3 + 旧 Phase 4） |
| Phase 4（旧 Phase 4） | コミット計画 + ユーザー確認（停止判断基準あり） | 確認（コミット計画表示、dry-run 時はここで終了） |
| Phase 5（旧 Phase 5） | コミット実行（push しない） | 実行（コミット + `git log --oneline -N` で結果表示、push しない） |
| Phase 6 手動作業通知 | **独立 Phase**: 手動削除候補 + ユーザーに委ねる作業 | **Phase 5 の後セクション**: 手動削除候補 + ユーザー作業（`/release` 案内追加） |
| Phase 7 完了報告 | あり（コミット数、スキップ数、手動削除候補数、ユーザー作業数、次ステップ） | なし（Phase 5 の手動作業通知で終了） |

**影式固有の保護対象**:
- Phase 2 の README_en.md チェック
- Phase 2 の CHEATSHEET.md チェック
- Phase 6 の手動削除候補セクション（v4.4.1 にも存在するが簡略化）
- Phase 7 完了報告（v4.4.1 では削除）

**移行方針**: v4.4.1 版をベースに、影式固有ドキュメント（README_en.md, CHEATSHEET.md）のチェックロジックを doc-sync-flag 未存在時のフォールバックとして維持。完了報告は簡略化して良い。

---

#### 6. `auditing.md`

| 項目 | 現行（影式） | LAM 4.4.1 |
|------|-------------|-----------|
| 状態ファイル確認 | `implementation が approved か確認`、`subPhase を review に更新` | `phase が BUILDING で current_task が null（BUILDING 完了確認）`、`phase を AUDITING に更新` |
| 権限等級セクション | Step 5 に記述あり | **独立セクション（v4.0.0 強化）**: 見出し付きで権限等級に基づく修正ルールを明示 |
| コード明確性チェック | なし | **新規**: `phase-rules.md` 参照。ネスト三項演算子、密なワンライナー、デバッグ容易性 |
| ドキュメント整合性 | 3項目 | **5項目**: `.claude/` の変更が `docs/internal/` に反映されているか、`docs/internal/` と実運用の乖離チェックを追加 |
| `/full-review` との使い分け | なし | **新規**: 手動段階的監査 vs ワンショット自動修正の使い分けガイド |
| 成果物パス | `docs/memos/audit-report-<feature>.md` | `docs/artifacts/audit-reports/<feature>.md` |
| 監査レポートの権限等級サマリー | あり（Step 5 で定義済み） | なし（v4.4.1 ではレポート形式を簡略化） |

**影式固有の保護対象**: 権限等級サマリーテーブル（現行にはあるが v4.4.1 にはない）

---

#### 7. `building.md`

| 項目 | 現行（影式） | LAM 4.4.1 |
|------|-------------|-----------|
| Step 4（現行なし） | 状態ファイル更新がStep 4 | **新規 Step 4: 影響分析（Pre-Flight）**: 変更対象の依存関係調査、直接/間接影響の特定、公開 API 変更確認、影響テスト特定、PG/SE/PM 分類 |
| 状態ファイル更新 | `subPhase を implementation に更新`、`status.implementation を in_progress に更新` | `phase を BUILDING に更新`、`current_task を実装対象タスクIDに更新` |
| TDD サイクル内 R-1〜R-6 | **埋め込み**: Step 2 に R-4/R-5、Step 3 に R-2/R-3/R-6、Step 3.5 に R-1/R-5 | **削除**: 汎用 Step 1-5 のみ。R-1〜R-6 は `building-checklist.md` に分離済み |
| TDD 内省パイプライン | `Step 5.5`: PostToolUse hook 自動記録、閾値 **3回**、`draft-*.md` 自動生成、`trust-model.md` 参照 | **独立セクション（v2）**: PostToolUse hook + JUnit XML、閾値 **2回**、`/pattern-review` コマンド連携、`trust-model.md` 参照 |
| walkthrough.md | `walkthrough.md で検証完了` | `docs/artifacts/walkthrough-<feature>.md で検証完了（任意）` |
| フェーズ終了条件 | `implementation を approved に更新` | `current_task を null に、completed_tasks にタスクIDを追加` |
| 確認メッセージ | 適用ルール3項目 | 適用ルール4項目（「影響分析: 実装前に必須」追加） |

**影式固有の保護対象**:
- TDD サイクル内の R-1〜R-6 インライン参照（v4.4.1 では削除。`building-checklist.md` 経由で維持）
- Step 3.5 Post-Green Verification（v4.4.1 では削除。`building-checklist.md` R-11 で維持）

**移行方針**: v4.4.1 版をベースに、`building-checklist.md` への参照を TDD サイクルセクションに追加。R-1〜R-6 のインライン記述は不要（`building-checklist.md` に集約済み）。

---

#### 8. `planning.md`

| 項目 | 現行（影式） | LAM 4.4.1 |
|------|-------------|-----------|
| 権限等級セクション | なし | **新規**: PLANNING フェーズでの変更は原則 PM 級。`permission-levels.md` 参照 |

その他は同一。差分は権限等級セクションの追加のみ。

---

#### 9. `project-status.md`

| 項目 | 現行（影式） | LAM 4.4.1 |
|------|-------------|-----------|
| Wave 進捗セクション | Step 3 で `docs/specs/*/tasks.md` からの集計を記述 | Step 3 に Wave 進捗なし（後半の独立セクションで記述） |
| Wave 進捗の位置 | メイン出力形式に統合 | **独立セクション**として分離 |
| KPI ダッシュボード | `docs/specs/lam/evaluation-kpi.md` 参照、値と目標のテーブル | `docs/specs/evaluation-kpi.md` 参照、ステータス列に `approved/warning/blocked` を追加 |
| KPI 計算式 | 5項目の計算ロジックを記述 | なし（仕様書に委譲） |

**影式固有の保護対象**: KPI 計算ロジック（K1〜K5）のインライン記述

---

#### 10. `pattern-review.md`

| 項目 | 現行（影式） | LAM 4.4.1 |
|------|-------------|-----------|
| permission-level 記述位置 | ボディ内（`# permission-level: PM`） | なし |
| MVP 制限の注記 | なし | **新規**: 冒頭に MVP 制限の注記（パターンログ閲覧と手動審査のみ、`draft-*.md` 自動生成は完全実装で対応予定） |
| 閾値 | 3回 | **2回** |
| パターン詳細参照先 | なし | `docs/artifacts/tdd-patterns/` 配下のパターンファイル参照 |
| Phase 1 出力形式 | `候補（3回以上）: X件` | テーブル形式（パターン名、観測回数、最終観測、ステータス）に拡充 |
| Phase 2 ルール候補表示 | 簡易テーブル | **詳細化**: 根拠の日付・ファイル・失敗内容を表示、承認/却下/保留の選択肢 |
| Phase 3 却下処理 | `ステータスを retired に変更` | `draft-NNN.md を削除。ステータスを rejected として記録` |
| Phase 4 寿命チェック | なし | **新規**: 承認済みルールの 90 日未使用通知 |
| 参照 | `.claude/rules/auto-generated/` 3ファイル | なし（ドキュメント内で完結） |

---

#### 11. `wave-plan.md`

| 項目 | 現行（影式） | LAM 4.4.1 |
|------|-------------|-----------|
| permission-level 記述位置 | ボディ内（`# permission-level: SE`） | なし |
| Step 1 タスク定義読み込み | `SESSION_STATE.md および docs/tasks/（または docs/specs/*/tasks.md）` | `docs/specs/ および docs/tasks/` |
| Step 2 タスク選定の注記 | Phase 1 Retro Try-3 由来の注記（大規模タスク単独 Wave 推奨、5タスク以上は分割必須） | 同等内容（注意事項セクションに簡略記載） |
| 除外基準 | `Phase 2 以降に明示的に据え置かれたもの` | `後続 Phase に明示的に据え置かれたもの` |
| Wave 完了条件の lint | `ruff check クリーン` | `lint チェッククリーン`（ツール非依存に汎用化） |
| 注意事項 | `3 タスクを超える場合は分割を検討` | `4 タスクを超える場合は分割を検討` + `大規模タスク（L）は単独 Wave を推奨` |

---

## skills/ 差分

### 共通スキルの差分（4件）

#### 1. `adr-template/SKILL.md`

| 項目 | 現行（影式） | LAM 4.4.1 |
|------|-------------|-----------|
| 適用条件 | `docs/adr/` 作成 + 決定記録 + `/adr-create` コマンド | `docs/adr/` 作成 + 決定記録 + `ADR の作成を求められた時`（`/adr-create` 参照削除、コマンド自体が v4.4.1 で廃止） |
| `/ship` 自動起票フロー | なし | **新規**: `/ship` Phase 2 で PM級設計判断検出時に ADR 起票を提案するフロー |
| 参照ドキュメント | `06_DECISION_MAKING.md`、`/adr-create` コマンド | `06_DECISION_MAKING.md`、`.claude/rules/permission-levels.md`、`/ship` コマンド (Phase 2) |

#### 2. `lam-orchestrate/SKILL.md`

| 項目 | 現行（影式） | LAM 4.4.1 |
|------|-------------|-----------|
| frontmatter | `name`, `version`, `description` | `name`, `description`, `version`（フィールド順序変更のみ） |
| 構造化思考セクション | なし | **新規**: AoT + Three Agents + Reflection を統合した構造化思考。発動条件（4条件）、実行フロー（Phase 0 → Level 1-3）、レベル別モデル選択（Sonnet/Opus）、アンカーファイル（`docs/artifacts/` に書き出し、Single-Writer/Multi-Reader）、`anchor-format.md` 参照 |
| Subagent 選択テーブル | 5行（test-runner, doc-writer, code-reviewer, Explore, general-purpose） | **9行に拡充**: quality-auditor（アーキテクチャ・仕様ドリフト検証）、requirement-analyst（3 Agents Model 内蔵）、design-architect（データモデル・API設計）、task-decomposer（1PR単位分割）を追加 |
| ループ統合 lam-loop-state.json スキーマ | green_state フィールド構造 | **SSOT 委譲**: `/full-review` コマンドを参照。スキーマ定義を full-review に一本化 |
| hooks 連携テーブル | 簡易（PostToolUse, lam-stop-hook） | **拡充**: 3 hook（Stop/PostToolUse/PreToolUse）の参照タイミング・動作を詳述、データフローの ASCII 図 |
| `/full-review` との統合 | なし | **新規**: 単独実行 vs lam-orchestrate 経由の状態ファイル生成責任分担を明記 |
| fullscan_pending フラグ管理 | なし | **新規**: Phase 4 での差分チェック Green State 達成時のフラグセット bash スクリプト |
| エスカレーション条件 | 3条件（PM級検出、2イテレーション連続未修正、max_iterations） | **6条件に拡充**: 再帰防止（`stop_hook_active=true`）、コンテキスト枯渇（PreCompact 発火）、テスト数減少を追加 |

**影式固有の保護対象**: なし

#### 3. `skill-creator/SKILL.md`

完全同一。差分なし。

#### 4. `spec-template/SKILL.md`

| 項目 | 現行（影式） | LAM 4.4.1 |
|------|-------------|-----------|
| Section 6 | `制約事項` | **新規挿入 Section 6**: `権限等級（v4.0.0）` — 各変更項目の PG/SE/PM 分類テーブル + `permission-levels.md` 参照 |
| Section 9 権限等級 | `権限等級（v4.0.0）` — 1行参照文のみ | 旧 Section 6 の位置に移動し、テーブル形式で詳細化 |
| 以降のセクション番号 | 6-11（制約→変更履歴） | 7-11（制約→変更履歴）。Section 6 挿入により +1 ずれ |

### 現行のみのスキル（1件）

#### `ultimate-think/SKILL.md`

| 項目 | 内容 |
|------|------|
| 機能 | AoT + Three Agents + Reflection を統合した構造化思考 |
| 吸収先 | `lam-orchestrate/SKILL.md` の「構造化思考」セクション |
| references | `anchor-format.md` → `lam-orchestrate/references/anchor-format.md` に移動 |

**移行方針**: ultimate-think を削除し、lam-orchestrate の構造化思考セクションで機能を維持。`anchor-format.md` の移動も必要。

### v4.4.1 のみのスキル（1件）

#### `ui-design-guide/SKILL.md`

| 項目 | 内容 |
|------|------|
| 目的 | UI/UX 設計時のチェックリスト。PLANNING フェーズで `docs/specs/ui-*.md` 作成時に自動適用 |
| 5つの観点 | アクセシビリティ（WCAG 2.1 AA）、状態設計（5 UI States）、レスポンシブ設計、フォーム UX、パフォーマンス意識 |
| 影式への適用 | tkinter ベースのため Web 固有項目（レスポンシブ、LCP/CLS）は直接適用しないが、状態設計やアクセシビリティの原則は有用 |

---

## agents/ 差分

### エージェント構成

8 エージェント全て両方に存在。新規/削除なし。

### 各エージェントの差分

#### 1. `code-reviewer.md`

| 項目 | 現行（影式） | LAM 4.4.1 |
|------|-------------|-----------|
| permission-level 位置 | ボディ内（`# permission-level: SE`） | **フロントマター内**: `# permission-level: SE` |
| 役割境界セクション | あり（code-reviewer vs quality-auditor の使い分け） | **削除** |
| 出力形式のPG/SE/PM | 各 Issue 末尾に `**[PG/SE/PM]**` | 各 Issue 先頭に `**[PG/SE/PM]**`、権限等級テーブルが出力形式内に統合 |
| PG/SE/PM 分類基準セクション | 権限等級サマリーテーブルで記述 | **独立セクション（v4.0.0）**: 分類基準の説明 + `permission-levels.md` 準拠の明記 |
| 総合評価 | `A/B/C/D` | `A / B / C / D / F`（F 評価追加） |

#### 2. `quality-auditor.md`

| 項目 | 現行（影式） | LAM 4.4.1 |
|------|-------------|-----------|
| permission-level 位置 | ボディ内（`# permission-level: SE`） | **フロントマター内**: `# permission-level: SE` |
| model | `opus` | `sonnet` |
| 役割境界セクション | あり（quality-auditor vs code-reviewer の使い分け） | **削除** |
| Step 3 タイトル | `仕様ドリフトチェック`（Step 3 と Step 3b が独立） | `ドキュメント整合性監査 + 仕様ドリフトチェック`（Step 3 に統合） |
| 仕様ドリフトチェック | 影式固有の詳細版（検出方法3ステップ、ドリフト種別3種、テーブル形式） | **v4.0.0 強化版**: ドリフト種別 **4種**（Phase/Wave 未到達を追加）、PG/SE/PM 分類付き出力形式 |
| 構造整合性チェック | 影式固有版（R-1〜R-11 品質ルール適合性、ADR 決定事項反映） | **v4.0.0 版**: スキーマ整合性（`lam-loop-state.json` 等）、参照整合性、データフロー整合性、設定整合性、ドキュメント間整合性の5観点。具体的チェックテーブル例付き |
| Step 番号 | Step 1-7（7ステップ） | Step 1-6（6ステップ。仕様ドリフト+構造整合性が Step 3 に統合） |
| 禁止事項 | `PM級の修正の実施（PG/SE級は permission-level に従い実施可）` | `PM級の修正の実施（指摘のみ、承認ゲート。PG/SE級の修正は許可。permission-levels.md 参照）` |

**影式固有の保護対象**:
- model: `opus` の維持判断（品質 vs コスト）
- Step 3b の R-1〜R-11 品質ルール適合性チェック（v4.4.1 では削除。`building-checklist.md` の内容だが、AUDITING 時の検証としても有用）

#### 3. `doc-writer.md`

| 項目 | 現行（影式） | LAM 4.4.1 |
|------|-------------|-----------|
| permission-level 位置 | ボディ内（`# permission-level: SE` + 注記） | **フロントマター内**: `# permission-level: SE` |
| permission-level 注記 | ボディ内に `docs/specs/` 書き込みが PM 級だが lam-orchestrate 経由の場合に限定する旨の説明 | なし（削除） |
| ドキュメント自動追従モード | doc-sync-flag 連携（4ステップ: 読み取り→特定→更新→報告） | **v4.0.0 / Wave 3 版**: `/ship` Phase 2 からの呼び出しフロー。入力仕様（変更ファイル一覧の提供元、PROJECT_ROOT 相対パス）、処理フロー（仕様書特定→変更分析→更新案差分生成→ユーザー提示）、出力形式（diff 形式の Doc Sync 更新案）、完全実装への言及（PostToolUse 非同期呼び出し） |

#### 4. `design-architect.md`

| 項目 | 現行（影式） | LAM 4.4.1 |
|------|-------------|-----------|
| permission-level 位置 | ボディ内（`# permission-level: PM`） | **フロントマター内**: `# permission-level: SE` |
| permission-level 等級 | **PM** | **SE** |
| description | `大規模設計や並列設計時に委任可能。単一機能の設計はメインで直接実施する方が効率的。` | `PLANNINGフェーズでの設計作業で使用推奨。` |

**影式固有の保護対象**: permission-level の PM→SE 変更は慎重に検討。影式では design-architect を PM 級としている理由（設計判断の重要性）がある。

#### 5. `requirement-analyst.md`

| 項目 | 現行（影式） | LAM 4.4.1 |
|------|-------------|-----------|
| permission-level 位置 | なし | **フロントマター内**: `# permission-level: PM` |

本文は同一。

#### 6. `task-decomposer.md`

| 項目 | 現行（影式） | LAM 4.4.1 |
|------|-------------|-----------|
| permission-level 位置 | なし | **フロントマター内**: `# permission-level: SE` |
| model コメント | なし | `# コスト最適化のため意図的に Haiku を採用（タスク分解は出力品質より速度重視）` |

本文は同一。

#### 7. `tdd-developer.md`

| 項目 | 現行（影式） | LAM 4.4.1 |
|------|-------------|-----------|
| permission-level 位置 | なし | **フロントマター内**: `# permission-level: SE` |
| description | `大規模タスクや並列実装時に委任可能。小規模タスクはメインで直接実装する方が効率的。` | `BUILDINGフェーズでの実装作業で使用推奨。` |

本文は同一。

#### 8. `test-runner.md`

| 項目 | 現行（影式） | LAM 4.4.1 |
|------|-------------|-----------|
| permission-level 位置 | なし | **フロントマター内**: `# permission-level: PG` |
| model | `sonnet` | `haiku` |

本文は同一。

---

## 移行時の注意事項

### 1. 影式固有の資産を保護すること

以下は影式固有であり、LAM 4.4.1 テンプレートへの移行時に失われないよう注意:

- **`building.md` の R-1〜R-6 インライン参照**: v4.4.1 では削除。`building-checklist.md` 経由で維持（影式では既に対応済み）
- **`ship.md` Phase 2 の README_en.md / CHEATSHEET.md チェック**: v4.4.1 には影式固有のドキュメントチェックがない。doc-sync-flag 未存在時のフォールバックとして維持
- **`quality-auditor.md` の model: opus**: v4.4.1 では sonnet に変更。影式での品質要件に応じて判断
- **`design-architect.md` の permission-level: PM**: v4.4.1 では SE に降格。影式での設計判断の重要性に応じて判断
- **`retro.md` / `pattern-review.md` の permission-level 記述**: v4.4.1 では削除されているが、影式では PM 級であることの明示を維持すべき

### 2. 削除されるコマンドの吸収確認

7件のコマンドが削除される。各コマンドの機能が吸収先で十分にカバーされているか確認:

| 削除コマンド | 確認事項 |
|-------------|---------|
| `daily.md` | `quick-save.md` の Step 3 で KPI 集計が実行されるか |
| `focus.md` | 影式で実際に使用されているか（使用頻度が低ければ削除可） |
| `full-load.md` | `quick-load.md` の 4 ステップで十分か |
| `full-save.md` | `quick-save.md` + `/ship` の組み合わせで十分か |
| `adr-create.md` | `adr-template` スキルで代替可能か |
| `impact-analysis.md` | `building.md` Step 4 で影響分析がカバーされるか |
| `security-review.md` | `full-review.md` Phase 1 #4 でセキュリティレビューがカバーされるか |

### 3. 出力パスの変更

以下のパスが `docs/memos/` → `docs/artifacts/` に変更:

| 対象 | 現行パス | v4.4.1 パス |
|------|---------|------------|
| 監査レポート | `docs/memos/audit-report-*.md` | `docs/artifacts/audit-reports/*.md` |
| Retro 記録 | `docs/memos/retro-wave-*.md` | `docs/artifacts/retro-wave-*.md` |
| TDD パターン詳細 | `docs/memos/tdd-patterns/` | `docs/artifacts/tdd-patterns/` |
| 思考アンカー | （lam-orchestrate に新設） | `docs/artifacts/YYYY-MM-DD-lam-think-*.md` |
| Knowledge Layer | なし | `docs/artifacts/knowledge/` |

### 4. TDD 内省パイプライン v2 への移行

| 項目 | v4.0.1（現行） | v4.4.1 |
|------|---------------|--------|
| 閾値 | 3回 | 2回 |
| データソース | `tool_response.exitCode`（実際には動作していなかった可能性） | JUnit XML（`.claude/test-results.xml`） |
| 分析実行者 | PostToolUse hook（自動） | `/retro` Step 2.5（人間が判断） |
| ルール候補生成 | `draft-*.md` 自動生成（閾値到達時） | `/retro` 内で提案（人間が承認） |
| 新規ルール | なし | `.claude/rules/test-result-output.md`（JUnit XML 出力義務） |

### 5. model 変更の影響

| エージェント | 現行 | v4.4.1 | 影響 |
|-------------|------|--------|------|
| quality-auditor | opus | sonnet | 深い分析品質の低下リスク |
| test-runner | sonnet | haiku | コスト削減、軽微な品質低下 |

### 6. 新規依存ファイルの確認

v4.4.1 のコマンド/スキル/エージェントが参照する新規ファイルで、影式に未作成のもの:

| 参照元 | 参照先 | 状態 |
|--------|--------|------|
| `quick-save.md` Step 3 | `docs/specs/loop-log-schema.md` | 未作成 |
| `quick-save.md` Step 3 | `docs/specs/evaluation-kpi.md` | 要確認（`docs/specs/lam/evaluation-kpi.md` として存在する可能性） |
| `quick-save.md` Step 3 | `docs/daily/` ディレクトリ | 未作成 |
| `retro.md` Step 2.5 | `docs/specs/tdd-introspection-v2.md` | 未作成 |
| `retro.md` Step 4 | `docs/artifacts/knowledge/` ディレクトリ | 未作成 |
| `full-review.md` Phase 2 | `docs/artifacts/audit-reports/` ディレクトリ | 未作成 |
| `full-review.md` 参照 | `docs/memos/2026-03-10-scalable-review-and-eval-ideas.md` | 要確認 |
| `lam-orchestrate/SKILL.md` | `.claude/skills/lam-orchestrate/references/anchor-format.md` | 未作成（現在は `ultimate-think/references/` に存在） |
| rules | `.claude/rules/test-result-output.md` | 未作成 |

### 7. permission-level フロントマター化

v4.4.1 ではエージェントの `# permission-level` がボディからフロントマターコメントに移動:

```yaml
# 現行（ボディ内）
---
name: code-reviewer
model: sonnet
---
# permission-level: SE

# 本文...
```

```yaml
# v4.4.1（フロントマター内）
---
name: code-reviewer
# permission-level: SE
model: sonnet
---

# 本文...
```

全8エージェントに適用。commands の `retro.md`, `pattern-review.md`, `wave-plan.md` のボディ内記述も確認が必要。

### 8. 推奨移行順序

> **注**: 以下の Phase 番号は本ファイル内の作業順序であり、`specs/00-diff-summary.md` の移行 Phase 1〜5 とは別の番号空間。

1. **Phase 1**: 新規 rules の導入（`test-result-output.md`）
2. **Phase 2**: 出力パスの変更（`docs/memos/` → `docs/artifacts/`）+ 新規ディレクトリ作成
3. **Phase 3**: エージェントの更新（フロントマター化 + 差分適用）
4. **Phase 4**: コマンドの差分適用（影式固有部分を保護しつつマージ）
5. **Phase 5**: スキルの差分適用（ultimate-think → lam-orchestrate 統合、anchor-format.md 移動）
6. **Phase 6**: 削除コマンドの整理（7件の削除、吸収先の動作確認）
7. **Phase 7**: TDD 内省パイプライン v2 への移行（閾値変更、JUnit XML 設定）
