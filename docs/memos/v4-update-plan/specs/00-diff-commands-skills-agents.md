# commands / skills / agents 差分分析

## 概要

本文書は、影式（Kage-Shiki）プロジェクトの現行 `.claude/` 構成と LAM 4.0.1 テンプレートの差分を網羅的に分析したものである。

### ファイル数サマリー

| カテゴリ | 現行 | LAM 4.0.1 | 共通 | 現行のみ | 4.0.1のみ |
|---------|:----:|:---------:|:----:|:-------:|:---------:|
| commands | 17 | 16 | 14 | 3 | 2 |
| skills | 6 (5スキル) | 7 (6スキル) | 5 (5スキル) | 0 | 1 (1スキル) |
| agents | 8 | 8 | 8 | 0 | 0 |

### v4.0.0 の主要な新概念

LAM 4.0.1 で全体的に導入された横断的な変更:

1. **権限等級（PG/SE/PM）**: 全変更を3段階にリスク分類し、等級に応じた承認フローを適用
2. **自動ループ機構**: `/full-review` の Stop hook による自動イテレーション
3. **TDD 内省パイプライン**: テスト失敗パターンの自動記録とルール昇格
4. **doc-sync-flag**: PostToolUse hook による自動ドキュメント同期トリガー
5. **KPI ダッシュボード**: `/daily` と `/project-status` での定量メトリクス表示
6. **upstream-first ルール**: プラットフォーム仕様確認の義務化
7. **version フィールド**: スキルの frontmatter に `version: 1.0.0` を追加

---

## commands/ 差分

### 共通コマンドの差分

#### 1. `adr-create.md`

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| ファイル命名規則 | `YYYY-MM-DD_{title-in-kebab-case}.md` | `NNNN-kebab-case-title.md`（4桁連番、`adr-template` スキルの命名規則に準拠） |
| テンプレート参照 | なし | 「詳細版は `adr-template` スキルを参照」と明記 |

差分は軽微。命名規則の統一が主な変更点。

#### 2. `auditing.md`

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| description | 同一 | 同一 |
| 状態ファイル確認 | `implementation が approved か確認` | `phase が BUILDING で current_task が null（BUILDING 完了確認）`。`phase を AUDITING に更新` |
| 権限等級に基づく修正ルール | なし | **新規追加**: PG級（自動修正可）、SE級（修正後報告）、PM級（指摘のみ） |
| コード明確性チェック | なし | **新規追加**: ネスト三項演算子、密なワンライナー、デバッグ容易性のチェックリスト |
| ドキュメント整合性 | 3項目 | **5項目に拡張**: `.claude/` の変更が `docs/internal/` に反映されているか、`docs/internal/` と実運用の乖離チェックを追加 |
| `/full-review` との使い分け | なし | **新規追加**: 手動段階的監査 vs ワンショット自動修正の使い分けガイド |

**影響**: 現行の auditing.md には影式固有のカスタマイズがないため、LAM 4.0.1 版への置き換えで問題なし。

#### 3. `building.md`

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| 状態ファイル更新 | `subPhase を implementation に更新`、`status.implementation を in_progress に更新` | `phase を BUILDING に更新`、`current_task を実装対象タスクIDに更新`（状態管理スキーマの変更） |
| TDD サイクル詳細 | **影式固有の R-1〜R-6 ルール参照を含む詳細版**: R-4（FR チェックリスト駆動）、R-5（異常系テスト義務）、R-2（dict ディスパッチ）、R-3（定数即時使用）、R-6（else デフォルト値禁止）、Step 3.5 Post-Green Verification | **汎用版**: Step 1-5 のみの簡潔な記述。`building-checklist.md` の参照なし |
| TDD 内省パイプライン | なし | **新規追加**: PostToolUse hook による自動パターン記録、`/pattern-review` コマンドとの連携 |
| フェーズ終了条件 | `walkthrough.md で検証完了`、`implementation を approved に更新` | `walkthrough は任意`、`current_task を null に、completed_tasks にタスクIDを追加` |

**注意**: 現行版の方が TDD ステップ内に影式固有のビルディングチェックリスト（R-1〜R-6）を直接埋め込んでおり、より詳細。LAM 4.0.1 はこれらを `building-checklist.md`（影式独自ルール）に分離し、`building.md` 自体は汎用化している。移行時は R-1〜R-6 の参照関係を維持すること。

#### 4. `daily.md`

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| KPI 集計セクション | なし | **新規追加**: `.claude/logs/loop.log` からの K1〜K5 計算、`.claude/logs/permission.log` からの等級分布集計、`docs/specs/evaluation-kpi.md` 参照 |

その他の内容は同一。

#### 5. `focus.md`

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| ポモドーロ記述 | `25分のポモドーロタイマーを推奨` | `25分の集中作業を推奨（ポモドーロタイマーアプリの併用を案内）` |

差分は軽微（文言の微調整のみ）。

#### 6. `full-load.md`

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| frontmatter | なし（description なし） | **追加**: `description: "詳細な状態確認 + セッション復帰（数日ぶりの復帰向け）"` |

本文は同一。

#### 7. `full-review.md`

**最も差分が大きいコマンド。LAM 4.0.1 で大幅に拡張されている。**

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| description | `全ソース網羅レビュー + 全Issue修正を一括実行` | `並列監査 + 全修正 + 検証の一気通貫レビュー` |
| Phase 0 | なし | **新規**: ループ初期化（`lam-loop-state.json` 生成）。状態ファイルスキーマの詳細定義（active, command, target, iteration, max_iterations, started_at, log, fullscan_pending, tool_events） |
| Phase 0.5 | なし | **新規**: context7 MCP 検出。利用可否に応じた仕様確認の実行/スキップ判定 |
| Phase 1 並列監査 | 3エージェント: ソースレビュー、テストレビュー、品質監査 | **4エージェント構成に拡張**: ソース品質、テスト品質、アーキテクチャ・仕様整合性（仕様ドリフト+構造整合性）、セキュリティ（OWASP Top 10）。各 Issue に PG/SE/PM 分類を付与 |
| セキュリティチェック | 言及なし | **詳細定義**: インジェクション、認証・認可、シークレット漏洩、依存脆弱性、データ露出、安全でないデシリアライゼーションの6観点 |
| 仕様ドリフトチェック | なし | **新規**: `docs/specs/` と実装コードの整合性検証 |
| 構造整合性チェック | なし | **新規**: コンポーネント間のスキーマ整合性、参照整合性、データフロー整合性、設定整合性、ドキュメント間整合性の5観点 |
| Phase 2 | 重複排除 + 重要度分類のみ | **拡張**: PG/SE/PM 分類、レポートの `docs/memos/audit-reports/` への永続化、ユーザー承認ゲート |
| Phase 3 修正ポリシー | `audit-fix-policy.md` 参照 | **詳細化**: A-1（全重篤度対応、defer禁止）、A-2（スコープ外 Issue の免除条件を5条件で厳格化）、A-3（仕様ズレ同時修正）、A-4（1件ずつテスト確認） |
| Phase 4 検証 | テスト全パス + ruff クリーン + カバレッジ | **Green State 5条件**: G1（テスト全パス）、G2（lint エラーゼロ）、G3（対応可能 Issue ゼロ）、G4（仕様差分ゼロ）、G5（セキュリティチェック通過） |
| 真の Green State | なし | **新規定義**: 「修正後にゼロ」ではなく「スキャンして Issue がゼロ」。修正サイクル後の再スキャンで 0件が条件 |
| 差分チェック/フルスキャン | なし | **新規**: 毎サイクルは変更ファイルのみ、Green State 達成後にフルスキャン。`fullscan_pending` フラグ管理 |
| 自動ループ | なし | **新規**: Stop hook (`lam-stop-hook.sh`) による自動ループ。Phase 4 未達時に Phase 1 に自動復帰。最大 5 イテレーション |
| Phase 5 | 簡易な完了報告 | **拡張**: イテレーション数・累計修正数・Green State 達成状況を含む詳細レポート。`lam-loop-state.json` 削除 + ループログ保存 |
| モデル選択ガイド | エージェントごとの推奨モデル表 | 削除（エージェント定義側に委任） |

#### 8. `full-save.md`

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| frontmatter | description なし | **追加**: `description: "フルセーブ（SESSION_STATE.md + git commit + push + daily）"` |
| コンテキストガード閾値 | 15% 未満 | **25% 未満**（CLAUDE.md の閾値基準に統一） |
| ループログ保存 | なし | **新規**: Step 3 として `.claude/logs/loop.log` の保存手順を追加 |
| ステップ番号 | 1-6 | 1-7（ループログ保存の挿入によりずれ） |
| git commit の例 | `ドキュメント更新」「設定変更` | `ドキュメント更新」「設定変更」「ループログ` を追加 |
| 配置先の記載 | あり | 削除（frontmatter で十分と判断） |

#### 9. `impact-analysis.md`

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| 権限等級分類 | なし | **新規追加**: Step 5 として PG/SE/PM 分類を追加。等級に応じた対応方針（PG=自動修正可、SE=影響範囲確認、PM=詳細分析必須） |
| ステップ番号 | 報告形式が Step 5 | 報告形式が Step 6 に |

#### 10. `planning.md`

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| 権限等級セクション | なし | **新規追加**: PLANNING フェーズでの変更は原則 PM 級。`permission-levels.md` 参照 |

その他は同一。

#### 11. `project-status.md`

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| タスク定義ファイル参照 | `docs/specs/*/tasks.md` 等からの Wave 進捗集計あり | Wave 進捗セクションなし |
| KPI ダッシュボード | なし | **新規追加**: K1（タスク完了率）、K2（平均ループイテレーション）、K3（フック介入率）、K4（コンテキスト枯渇率）、K5（同一Issue再発率） |

**注意**: 現行版の Wave 進捗セクションは影式固有のタスク管理に有用。LAM 4.0.1 版に移行する場合、Wave 進捗セクションを維持しつつ KPI ダッシュボードを追加するのが推奨。

#### 12. `quick-load.md`

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| frontmatter | description なし | **追加**: `description: "SESSION_STATE.md を読んで簡潔に報告"` |

本文は同一。

#### 13. `quick-save.md`

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| frontmatter | description なし | **追加**: `description: "SESSION_STATE.md への軽量セーブ（git commitなし）"` |
| 配置先の記載 | あり | 削除 |

本文は同一。

#### 14. `security-review.md`

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| Critical Agent 記述 | `Critical Agent（批判者）の視点で評価する` | `セキュリティチェック完了後、改善提案フェーズで Critical Agent（批判者）の視点も適用する` |
| 権限等級対応表 | なし | **新規追加**: Critical/High=PM（即時報告）、Medium=SE（修正後報告）、Low=PG（自動修正可） |
| 自動化ツール連携 | なし | **新規追加**: npm audit、pip-audit/safety、grep パターンマッチの具体的コマンド例 |
| 公式セキュリティツール参照 | なし | **新規追加**: security-guidance plugin、claude-code-security-review、OWASP Top 10 (2025) への参照 |

#### 15. `ship.md`

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| description | なし（本文冒頭で説明） | **追加**: `description: "論理グループ分けコミット - 変更を棚卸し・分類・コミット"` |
| Phase 1.5 → Phase 2 | **Phase 1.5 Doc Sync**: 手動でのドキュメント照合（CHANGELOG.md, README.md, README_en.md, CHEATSHEET.md を固定チェック） | **Phase 2 Doc Sync チェック**: `doc-sync-flag` ファイル参照 → PG/SE/PM 分類 → SE/PM 級のみ doc-writer エージェント呼び出し → PM 級は ADR 起票提案（`/adr-create` 連携）→ フラグクリア |
| Phase 構成 | Phase 1→1.5→2→3→4→5→6→7 の 7 段階 | Phase 1→2→3→4→5 の 5 段階（簡素化） |
| 手動削除候補セクション | あり（Phase 6） | なし（簡素化） |
| ユーザー作業通知 | あり（Phase 6.2） | 簡易版（push 案内のみ） |

**注意**: 現行の ship.md には影式固有の README_en.md チェック等が含まれている。LAM 4.0.1 版は doc-sync-flag による自動化に移行しているが、影式固有のドキュメント（README_en.md、CHEATSHEET.md）のチェックロジックは別途維持する必要がある。

### LAM 4.0.1 で新規追加されたコマンド

#### 1. `pattern-review.md` (新規)

TDD 内省パイプラインの審査コマンド。PostToolUse hook が記録したテスト失敗パターンを確認し、閾値到達のルール候補を承認/却下する。

- **Phase 1**: パターン棚卸し（`.claude/tdd-patterns.log` 読み込み、観測回数集計）
- **Phase 2**: ルール候補の確認（`draft-*.md` の審査、承認/却下/保留）
- **Phase 3**: 承認処理（draft → rule リネーム or 削除）
- **Phase 4**: 寿命チェック（90日以上未使用ルールの棚卸し）
- 権限等級: 閲覧=PG、承認/却下/削除=PM

**影式への適用**: TDD 内省パイプラインを導入する場合に必要。現行の影式では building-checklist.md に手動ルール（R-1〜R-10）を蓄積しているが、pattern-review による自動化で補完可能。

### 現行にのみ存在するコマンド（影式固有）

#### 1. `retro.md` (影式固有)

Wave/Phase 完了時の振り返り（KPT）コマンド。

- `/retro wave` で直近 Wave、`/retro phase` で Phase 全体を振り返り
- 定量分析（メトリクス収集）+ 定性分析（KPT）+ アクション抽出
- 反映先の分類（rules/commands/agents/docs）
- Phase 横断分析（複数 Wave の Retro からパターン特定）

**LAM 4.0.1 への統合案**: LAM テンプレートにも有用なコマンド。影式固有として維持推奨。

#### 2. `wave-plan.md` (影式固有)

次 Wave のタスク選定と実行順序の策定コマンド。

- タスク選定基準（依存関係、統合リスク、サイズバランス、クリティカルパス）
- 1 Wave = 1-4 タスク推奨（Phase 1 Retro Try-3 由来）
- 並列可能性の分析
- Wave 完了条件（テスト PASSED + ruff クリーン + 仕様書同期 + `/full-review` + `/ship`）

**LAM 4.0.1 への統合案**: 影式固有として維持推奨。LAM テンプレートには Wave 計画の概念自体がないため。

#### 3. `project-status.md` の Wave 進捗セクション (影式固有拡張)

現行版にはタスク定義ファイルからの Wave 進捗集計セクションがある。LAM 4.0.1 版にはこれがなく、代わりに KPI ダッシュボードがある。両方を統合するのが最善。

---

## skills/ 差分

### 共通スキルの差分

#### 1. `adr-template/SKILL.md`

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| frontmatter | version なし | `version: 1.0.0` 追加 |
| `/ship` からの自動起票フロー | なし | **新規追加**: `/ship` Phase 2 で PM級の設計判断検出時に ADR 起票を提案するフロー |
| 参照ドキュメント | `06_DECISION_MAKING.md`、`/adr-create` コマンド | **追加**: `permission-levels.md`、`/ship` コマンド (Phase 2) |

#### 2. `lam-orchestrate/SKILL.md`

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| frontmatter | `disable-model-invocation: true`, `allowed-tools: Task, Read, Glob, Grep`, `argument-hint` あり | `version: 1.0.0` 追加。`disable-model-invocation`、`allowed-tools`、`argument-hint` は削除 |
| Subagent 選択ルール | `quality-auditor` の記載なし | **追加**: `品質監査・整合性` → `quality-auditor`（カスタム定義、アーキテクチャ・仕様ドリフト検証） |
| ループ統合セクション | なし | **新規追加**: v4.0.0 の自動ループ機構全体の記述。`lam-loop-state.json` のスキーマ定義（状態ファイルフィールド、log エントリスキーマ）、ループライフサイクル（初期化→状態更新→終了処理）、hooks との連携（Stop/PostToolUse/PreToolUse）、データフロー図、`/full-review` との統合責任分担、fullscan_pending フラグ管理、エスカレーション条件（6条件） |

**注意**: 現行版の frontmatter フィールド（`disable-model-invocation`、`allowed-tools`、`argument-hint`）は Claude Code の skills 仕様に基づくもの。LAM 4.0.1 でこれらが削除されている理由は要確認（upstream の仕様変更の可能性）。

#### 3. `skill-creator/SKILL.md`

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| frontmatter | version なし | `version: 1.0.0` 追加 |

本文・references は完全に同一。

#### 4. `spec-template/SKILL.md`

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| frontmatter | version なし | `version: 1.0.0` 追加 |
| 機能仕様書テンプレート Section 6 | `6. 制約事項` | **新規挿入**: `6. 権限等級（v4.0.0）` — 各変更項目の PG/SE/PM 分類テーブル。以降のセクション番号が +1 ずれる |
| セクション番号 | 6-10（制約〜変更履歴） | 7-11（制約〜変更履歴） |

#### 5. `ultimate-think/SKILL.md`

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| frontmatter | `disable-model-invocation: true`, version なし | `version: 1.0.0` 追加。`disable-model-invocation` は削除 |
| Phase 0 の `--no-web` | `--no-web 指定時またはオフライン環境では WebSearch をスキップする` の記載あり | **削除**: この条件分岐の記述なし |

`references/anchor-format.md` は完全に同一。

### LAM 4.0.1 で新規追加されたスキル

#### 1. `ui-design-guide/SKILL.md` (新規)

UI/UX 設計チェックリストスキル。PLANNING フェーズでの UI 仕様策定時に自動適用。

- **フレームワーク非依存**: 設計原則レベルの注意喚起に限定
- **適用条件**: `docs/specs/ui-*.md` 作成時、UI/UX 設計の議論時
- **5つのチェック観点**:
  1. アクセシビリティ（WCAG 2.1 AA）: 色コントラスト、タッチターゲット、キーボード操作、フォーカス表示、代替テキスト、見出し階層、フォームラベル、モーション
  2. 状態設計（UI States）: Empty, Loading, Error, Success, Partial の 5 状態
  3. レスポンシブ設計: ブレークポイント、レイアウト、画像、タイポグラフィ、ナビゲーション
  4. フォーム UX: バリデーション、エラー表示、入力補助、自動保存、確認画面、進捗表示
  5. パフォーマンス意識: LCP, CLS, バンドルサイズ
- **公式ツール参照**: frontend-design plugin、ui-ux-pro-max-skill、Web Interface Guidelines

**影式への適用**: 影式は tkinter ベースの GUI を持つため、一部の Web 固有項目（レスポンシブ設計、LCP/CLS）は直接適用しないが、状態設計やアクセシビリティの設計原則は有用。

### 現行にのみ存在するスキル（影式固有）

なし。現行の全スキルは LAM 4.0.1 にも存在する。

---

## agents/ 差分

### LAM 4.0.1 で新規追加されたエージェント

なし。エージェント構成は 8 ファイルで同一。

### 現行のエージェント構成

8 エージェント全て両方に存在。以下は各エージェントの差分。

#### 1. `code-reviewer.md`

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| frontmatter | なし | `# permission-level: SE` 追加 |
| 役割境界セクション | あり（code-reviewer vs quality-auditor の使い分け） | **削除** |
| PG/SE/PM 分類 | なし | **新規追加**: 出力形式に権限等級テーブルを追加。各 Issue に `**[PG/SE/PM]**` タグ付与。分類基準の説明セクション追加 |

#### 2. `design-architect.md`

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| frontmatter | なし | `# permission-level: SE` 追加 |
| description | `大規模設計や並列設計時に委任可能。単一機能の設計はメインで直接実施する方が効率的。` | `PLANNINGフェーズでの設計作業で使用推奨。`（簡素化） |

本文は同一。

#### 3. `doc-writer.md`

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| frontmatter | なし | `# permission-level: SE` 追加 |
| ドキュメント自動追従モード | なし | **新規追加**: `/ship` Phase 2 からの呼び出しフロー。`doc-sync-flag` からの変更ファイル読み取り、対応 `docs/specs/` 特定、公開 API 変更分析、更新案の差分形式生成、承認/修正/スキップ選択。完全実装（PostToolUse 非同期呼び出し）の言及 |

#### 4. `quality-auditor.md`

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| frontmatter | なし | `# permission-level: SE` 追加 |
| model | `opus` | `sonnet`（コスト最適化） |
| 役割境界セクション | あり | **削除** |
| Step 3 タイトル | `ドキュメント整合性監査` | `ドキュメント整合性監査 + 仕様ドリフトチェック` |
| 仕様ドリフトチェック | なし | **新規追加**: v4.0.0 の詳細な仕様ドリフトチェック。4種類のドリフト（未実装仕様、未文書化実装、仕様不一致、Phase/Wave 未到達）を定義。出力形式テンプレート付き |
| Step 3b 構造整合性チェック | なし | **新規追加**: v4.0.0 の詳細な構造整合性チェック。スキーマ整合性、参照整合性、データフロー整合性、設定整合性、ドキュメント間整合性の 5 観点。具体的なチェックテーブル例（lam-loop-state.json, doc-sync-flag 等のファイル間一致確認） |
| 禁止事項 | `修正の実施（指摘のみ、修正は別エージェント）` | `PM級の修正の実施（指摘のみ、承認ゲート）` + v4.0.0 注記（PG/SE級の修正は許可） |

**注意**: model が `opus` → `sonnet` に変更されている。影式では quality-auditor を Opus で実行していたため、移行時にコスト vs 品質のトレードオフを検討すること。

#### 5. `requirement-analyst.md`

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| frontmatter | なし | `# permission-level: PM` 追加 |

本文は同一。

#### 6. `task-decomposer.md`

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| frontmatter | なし | `# permission-level: SE` 追加 |
| model コメント | なし | `# コスト最適化のため意図的に Haiku を採用（タスク分解は出力品質より速度重視）` |

本文は同一。

#### 7. `tdd-developer.md`

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| frontmatter | なし | `# permission-level: SE` 追加 |
| description | `大規模タスクや並列実装時に委任可能。小規模タスクはメインで直接実装する方が効率的。` | `BUILDINGフェーズでの実装作業で使用推奨。`（簡素化） |

本文は同一。

#### 8. `test-runner.md`

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| frontmatter | なし | `# permission-level: PG` 追加 |
| model | `sonnet` | `haiku`（コスト最適化） |

本文は同一。

---

## 移行時の注意事項

### 1. 影式固有の資産を保護すること

以下のファイルは影式固有であり、LAM 4.0.1 テンプレートへの移行時に失われないよう注意:

- **`retro.md`**: LAM 4.0.1 に相当するコマンドなし。維持必須
- **`wave-plan.md`**: LAM 4.0.1 に相当するコマンドなし。維持必須
- **`project-status.md` の Wave 進捗セクション**: LAM 4.0.1 版の KPI ダッシュボードと統合する
- **`building.md` の R-1〜R-6 詳細参照**: LAM 4.0.1 版は汎用化されているため、影式固有のビルディングチェックリスト参照は `building-checklist.md` 経由で維持する

### 2. 状態管理スキーマの変更

LAM 4.0.1 では状態ファイルのスキーマが変更されている:

- 現行: `subPhase`, `status.implementation`, `status.requirements` 等
- LAM 4.0.1: `phase`, `current_task`, `completed_tasks` 等

既存の `.claude/states/*.json` ファイルのマイグレーションが必要。

### 3. model 変更の影響

以下のエージェントで model が変更されている:

| エージェント | 現行 | LAM 4.0.1 | 影響 |
|-------------|------|-----------|------|
| quality-auditor | opus | sonnet | 深い分析品質の低下リスク |
| test-runner | sonnet | haiku | コスト削減、軽微な品質低下 |

影式では quality-auditor を Opus で使用していた理由がある（アーキテクチャ判断の深さ）。移行時にこの判断を再評価すること。

### 4. 新規依存ファイルの確認

LAM 4.0.1 のコマンド/スキル/エージェントが参照する新規ファイルで、影式に未作成のもの:

| 参照元 | 参照先 | 内容 |
|--------|--------|------|
| 複数コマンド | `.claude/rules/permission-levels.md` | PG/SE/PM 分類基準 |
| `full-review.md` | `.claude/lam-loop-state.json` | 自動ループ状態ファイル（実行時生成） |
| `full-review.md` | `.claude/hooks/lam-stop-hook.sh` | Stop hook スクリプト |
| `full-review.md` | `.claude/hooks/post-tool-use.sh` | PostToolUse hook |
| `full-review.md` | `.claude/hooks/pre-tool-use.sh` | PreToolUse hook |
| `building.md` | `.claude/tdd-patterns.log` | TDD パターンログ（実行時生成） |
| `building.md` | `.claude/rules/auto-generated/trust-model.md` | 信頼度モデル定義 |
| `daily.md` | `docs/specs/evaluation-kpi.md` | KPI 定義仕様書 |
| `daily.md` | `.claude/logs/loop.log` | ループログ（実行時生成） |
| `daily.md` | `.claude/logs/permission.log` | 権限ログ（実行時生成） |
| `ship.md` | `.claude/doc-sync-flag` | ドキュメント同期フラグ（hook が生成） |
| `full-review.md` | `docs/memos/audit-reports/` | 監査レポート永続化ディレクトリ |
| core-identity.md | `.claude/rules/permission-levels.md` | 権限等級の詳細 |
| security-commands.md | `.claude/settings.json` | Layer 1 ネイティブ権限 |
| upstream-first.md | （新規ルール） | プラットフォーム仕様確認義務 |

### 5. frontmatter フィールドの変更

LAM 4.0.1 のスキルでは以下の frontmatter 変更あり:

- **`version: 1.0.0`** が全スキルに追加
- **`disable-model-invocation: true`** が lam-orchestrate と ultimate-think から削除
- **`allowed-tools`** と **`argument-hint`** が lam-orchestrate から削除
- エージェントに **`# permission-level: PG/SE/PM`** コメントが追加

これらは Claude Code の skills/agents 仕様の進化に対応した変更である可能性がある。upstream-first ルールに従い、移行前に最新の Claude Code ドキュメントを確認すること。

### 6. rules/ の新規ファイル

LAM 4.0.1 には以下の rules ファイルが新規追加されている（本分析のスコープ外だが参考）:

- `permission-levels.md`: 権限等級の定義（全コマンド/エージェントが参照）
- `upstream-first.md`: プラットフォーム仕様確認ルール
- `auto-generated/README.md`: 自動生成ルールディレクトリの説明
- `auto-generated/trust-model.md`: TDD 内省パイプラインの信頼度モデル

### 7. 推奨移行順序

1. **Phase 1**: `permission-levels.md` と関連 rules の導入（全体の基盤）
2. **Phase 2**: エージェントの frontmatter 更新（`# permission-level` 追加）
3. **Phase 3**: コマンドの差分適用（影式固有部分を保護しつつマージ）
4. **Phase 4**: スキルの差分適用（version 追加、新規スキル ui-design-guide 導入検討）
5. **Phase 5**: hooks の実装（自動ループ、doc-sync-flag、TDD パターン記録）
6. **Phase 6**: 統合テスト（`/full-review` の自動ループ動作確認）
