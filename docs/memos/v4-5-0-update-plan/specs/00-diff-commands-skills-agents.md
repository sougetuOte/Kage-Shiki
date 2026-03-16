# commands / skills / agents 差分分析（v4.4.1 → v4.5.0）

## 概要

本文書は、影式（Kage-Shiki）プロジェクトの現行 `.claude/` 構成（LAM v4.4.1 移行済み）と LAM v4.5.0 テンプレートの差分を網羅的に分析したものである。

### ファイル数サマリー

| カテゴリ | 現行 | LAM 4.5.0 | 共通 | 現行のみ | 4.5.0のみ |
|---------|:----:|:---------:|:----:|:-------:|:---------:|
| commands | 11 | 11 | 11 | 0 | 0 |
| skills | 4 (4スキル) | 7 (7スキル) | 4 (4スキル) | 0 | 3 |
| agents | 8 | 8 | 8 | 0 | 0 |

### v4.5.0 の主要な変更概念

LAM v4.5.0 で全体的に導入された横断的な変更:

1. **MAGI System 導入**: Three Agents Model の名前を MELCHIOR/BALTHASAR/CASPAR に刷新。Reflection ステップ追加
2. **`/magi` スキル新設**: 構造化思考が独立スキル化（`lam-orchestrate` 内の構造化思考セクションから `/magi` への参照に変更）
3. **`/clarify` スキル新設**: 文書精緻化インタビュースキル。Requirements Smells 検出・Example Mapping を構造化
4. **`planning-quality-guideline.md` 新設**: PLANNING フェーズの成果物品質基準（Requirements Smells、RFC 2119、Design Doc チェックリスト、SPIDR、WBS 100% Rule）
5. **`code-quality-guideline.md` 新設**: AUDITING/BUILDING の重要度分類基準（Critical/Warning/Info の判断フローチャート、Green State の Issue 条件を明文化）
6. **`core-identity.md` 簡素化**: Subagent 委任判断テーブルとコンテキスト節約原則が削除
7. **`decision-making.md` リネーム**: Three Agents → MAGI System。Reflection ステップ追加
8. **`phase-rules.md` 変更**: PLANNING に品質基準参照追加、BUILDING に R-5/R-6 追加、AUDITING に Green State 条件・`code-quality-guideline.md` 参照追加、影式固有ルール（A-1〜A-4, R-7〜R-11 等）が汎用版で削除
9. **`permission-levels.md` 簡素化**: 影式固有パスパターン（`docs/internal/`, `pyproject.toml`, `src/kage_shiki/`, `config/`）が削除
10. **`full-review.md` 大幅拡張**: Stage 0〜5 の 5 段階構成に変更。Scalable Code Review（Plan A〜E）統合
11. **`tdd-developer.md` 大幅強化**: Pre-flight 必読ルール + `code-quality-guideline.md` 参照追加
12. **アンカーファイル名変更**: `docs/artifacts/YYYY-MM-DD-lam-think-*` → `docs/artifacts/YYYY-MM-DD-magi-*`

---

## 1. commands/ 差分

### コマンド構成

11 コマンド全て両方に存在。新規/削除なし。

---

#### 1.1 `auditing.md`

| 項目 | 現行（影式） | LAM 4.5.0 |
|------|-------------|-----------|
| 状態ファイル確認 | `implementation が approved か確認`、`subPhase を review に更新` | `phase が BUILDING で current_task が null`、`phase を AUDITING に更新` |
| 権限等級セクション | Step 5 に番号付きステップとして記述 | **独立セクション（v4.0.0）**: 見出し付きで明示、`permission-levels.md` 参照あり |
| コード明確性チェック | なし | **新規**: `phase-rules.md` 参照。ネスト三項演算子、密なワンライナー、デバッグ容易性 |
| ドキュメント整合性 | 3項目 | **5項目**: `.claude/` の変更が `docs/internal/` に反映されているか、`docs/internal/` と実運用の乖離チェックを追加 |
| `/full-review` との使い分け | なし | **新規**: 手動段階的監査 vs ワンショット自動修正の使い分けガイド |
| 成果物パス | `docs/artifacts/audit-reports/YYYY-MM-DD-<feature>.md` | `docs/artifacts/audit-reports/<feature>.md`（日付接頭辞なし） |
| 監査レポートの権限等級サマリー | あり（出力テンプレート内に権限等級別テーブル） | **削除**（v4.5.0 では出力形式が簡略化） |

**影式固有の保護対象**: 権限等級サマリーテーブル（現行の出力テンプレートにあるが v4.5.0 にはない）

---

#### 1.2 `building.md`

| 項目 | 現行（影式） | LAM 4.5.0 |
|------|-------------|-----------|
| Step 4 影響分析 | なし（状態ファイル更新が Step 4） | **新規 Step 4: 影響分析（Pre-Flight）**: 依存関係調査、直接/間接影響特定、PG/SE/PM 分類 |
| 状態ファイル更新 | `subPhase を implementation に更新`、`status.implementation を in_progress に更新` | `phase を BUILDING に更新`、`current_task を実装対象タスクIDに更新` |
| TDD サイクル内 R-1〜R-6 | **インライン記述**: Step 2 に R-4/R-5、Step 3 に R-2/R-3/R-6、Step 3.5 に R-1/R-5 | **削除**: 汎用 Step 1-5 のみ。R-1〜R-6 は `building-checklist.md` に分離済み |
| TDD 内省パイプライン | Step 5.5 として TDD サイクル内に記述 | **独立セクション（v2）**: `/pattern-review` コマンド連携を明記 |
| walkthrough.md | `walkthrough.md で検証完了` | `docs/artifacts/walkthrough-<feature>.md で検証完了（任意）` |
| フェーズ終了条件 | `implementation を approved に更新` | `current_task を null に、completed_tasks にタスクIDを追加` |
| 確認メッセージ | 適用ルール3項目 | 適用ルール4項目（「影響分析: 実装前に必須」追加） |

**影式固有の保護対象**:
- TDD サイクル内の R-1〜R-6 インライン参照（v4.5.0 では削除。`building-checklist.md` 経由で維持）
- Step 3.5 Post-Green Verification（v4.5.0 では削除。`building-checklist.md` R-11 で維持）

**移行方針**: v4.5.0 版をベースに、`building-checklist.md` への参照を TDD サイクルセクションに維持。R-1〜R-6 のインライン記述は不要（`building-checklist.md` に集約済み）。

---

#### 1.3 `full-review.md` ★重大変更

| 項目 | 現行（影式） | LAM 4.5.0 |
|------|-------------|-----------|
| 全体構成 | Phase 0〜5 の 6 段階 | **Stage 0〜5 の 6 段階に名称変更**（Phase → Stage）。内容は大幅拡張 |
| Stage 0 | ループ初期化 + context7 検出 | **Stage 0: 初期化** — ループ状態ファイル生成 + context7 検出 + **Scale Detection 判定（Plan E: FR-E2）新設** |
| Scale Detection | なし | **新規**: `scale_detector.py` による規模判定。Plan A〜E に応じた後続 Stage の制御テーブル |
| Stage 1 | （Phase 1 = 並列監査） | **Stage 1: 静的分析 + 依存グラフ構築（Plan A）新設** — ruff/bandit 等の静的解析パイプライン、AST マップ生成、import マップ生成、依存グラフ構築（FR-7a） |
| Stage 2 | （Phase 1 の並列監査に相当） | **Stage 2: チャンク分割 + トポロジカル順レビュー** — tree-sitter チャンキング（Plan B）、チャンクモード並列監査、トポロジカル順レビュー（Plan D）、概要カード・契約カード生成 |
| 並列監査エージェント構成 | 4エージェント（code-reviewer x2 + quality-auditor + code-reviewer セキュリティ） | 同構成（Stage 2 Step 3）。ただし Agent 出力に概要カード責務フィールド + 契約カードの追加出力を要求 |
| Stage 3 | （Phase 2 のレポート統合に相当） | **Stage 3: 階層的統合 + レポート生成** — Layer 2（モジュール統合、Plan C）、Layer 3（システムレビュー: 循環依存検出・命名規則チェック・LLM 仕様ドリフト検出）、契約カード永続化（FR-7c）、レポート統合 |
| Stage 4 | （Phase 3 の全修正に相当） | **Stage 4: トポロジカル順修正** — Plan D 有効時はトポロジカル順で修正。PM 級処理フロー詳細化 |
| Stage 5 | （Phase 4-5 の検証+完了に相当） | **Stage 5: 検証 + Green State 判定 + 完了** — 影響範囲分析（FR-7d）、再レビューループでの Stage 3 再実行（C-3b）、ループ継続/停止判定 |
| Scalable Review 参照 | なし | **新規**: Plan A〜E の実装状況一覧、要件仕様・設計書・タスク・構想メモへのリンク |
| 影式固有参照 | `building-checklist.md` R-1〜R-11、`pytest tests/ -v --tb=short`、`ruff check src/ tests/` | `building-checklist.md` 参照は Phase 1 #3 に残存。テストコマンドは汎用化 |
| A-1〜A-4 ルール | Phase 3 に記述 | Stage 4 に記述（内容同一だが A-2 が大幅拡充: スコープ外 Issue の5条件を明文化） |

**影式固有の保護対象**:
- Stage 2 Step 3 の `building-checklist.md` R-1〜R-11 参照（quality-auditor #3 への指示）
- Stage 5 の影式固有検証コマンド（`pytest tests/ -v --tb=short`、`ruff check src/ tests/`）

**移行方針**: v4.5.0 版は Scalable Code Review を全面統合した大幅拡張。影式では現時点で Plan A〜E の静的解析ツール群（`scale_detector.py`, `chunker.py` 等）が未実装のため、段階的に導入する。Stage 0 の Scale Detection で「なし（~10K）」に判定される場合は従来とほぼ同等の動作になる設計。

---

#### 1.4 `pattern-review.md`

| 項目 | 現行（影式） | LAM 4.5.0 |
|------|-------------|-----------|
| permission-level 記述 | HTML コメント `<!-- permission-level: PM -->` | なし（削除） |
| 内容 | 影式が v4.4.1 移行時にほぼ同一化済み | **同一**（差分なし） |

**影式固有の保護対象**: `<!-- permission-level: PM -->` の HTML コメント（v4.5.0 では削除されているが影式では維持推奨）

---

#### 1.5 `planning.md`

| 項目 | 現行（影式） | LAM 4.5.0 |
|------|-------------|-----------|
| 構造化思考の活用 | なし | **新規**: `/magi` の使用を検討する条件（判断ポイント 2+、影響レイヤー 3+、選択肢 3+） |
| 権限等級セクション | なし | **新規**: PLANNING フェーズでの変更は原則 PM 級。`permission-levels.md` 参照 |
| 品質基準 | なし（`phase-rules.md` 参照のみ） | **新規**: `planning-quality-guideline.md` 準拠の記述（Requirements Smells、RFC 2119 等。ただし planning.md 本体には直接記述なし、`phase-rules.md` 経由） |
| 3 Agents Model 記述 | `Affirmative/Critical/Mediator` | 同一（planning.md 本体は未変更。ルール側で MAGI に変更） |

**移行方針**: 構造化思考セクションと権限等級セクションを追加。影式固有の変更は不要。

---

#### 1.6 `project-status.md`

| 項目 | 現行（影式） | LAM 4.5.0 |
|------|-------------|-----------|
| Wave 進捗セクション | Step 3 にインライン記述 + 後半に独立セクション | **独立セクション**として分離（メイン出力形式から除外） |
| KPI ダッシュボード | `docs/specs/lam/evaluation-kpi.md` 参照、K1〜K5 計算式をインライン記述 | `docs/specs/evaluation-kpi.md` 参照、計算式は仕様書に委譲、ステータス列に `approved/warning/blocked` 追加 |
| KPI 参照パス | `docs/specs/lam/evaluation-kpi.md` | `docs/specs/evaluation-kpi.md` |

**影式固有の保護対象**: KPI 計算ロジック（K1〜K5）のインライン記述。`docs/specs/lam/` パスの維持判断が必要。

---

#### 1.7 `quick-load.md`

| 項目 | 現行（影式） | LAM 4.5.0 |
|------|-------------|-----------|
| description | `クイックロード` | `セッション状態のロード（SESSION_STATE.md + 関連ドキュメント特定）` |
| フォールバック | git log + current-phase.md からの推定（3ステップ） | 「SESSION_STATE.md が見つかりません。新規セッションとして開始します。」で終了 |
| 復帰サマリー形式 | 構造化（前回日付、Phase、完了、未完了、参照予定ファイル） | 簡略化（`前回: YYYY-MM-DD | Phase:` の1行形式 + 箇条書き） |

**影式固有の保護対象**: フォールバック時の git log 推定機能（v4.5.0 では簡略化されている）

---

#### 1.8 `quick-save.md`

| 項目 | 現行（影式） | LAM 4.5.0 |
|------|-------------|-----------|
| description | `クイックセーブ` | `セッション状態のセーブ（SESSION_STATE.md + ループログ + Daily記録）` |
| 配置先の記載 | あり（冒頭に記載） | なし（削除） |
| コンテキスト節約の注記 | なし | **新規**: 「コンテキスト消費を抑えるため、簡潔に実行すること」 |
| コンテキスト情報 | テスト結果（passed 数/カバレッジ）を含む | テスト結果を含まない（簡略化） |
| Daily 記録のセクション構成 | セッション概要 + KPI + メモ | **簡略化**: 本日完了 + 明日の最優先 + 課題・気づき + KPI 集計 |
| KPI 集計の位置 | Daily 記録の KPI セクション（参考レベル） | **独立サブセクション**: ベースライン確立後に集計。集計手順を具体的に記述（`loop-*.txt` 走査、`permission.log` 走査、テンプレート参照） |

**影式固有の保護対象**: なし（汎用的な内容のみ）

---

#### 1.9 `retro.md`

| 項目 | 現行（影式） | LAM 4.5.0 |
|------|-------------|-----------|
| description | `振り返り - Wave/Phase完了時の学習サイクル（KPT）を実施` | `振り返り - Wave/Phase完了時の学習サイクル` |
| permission-level | HTML コメント `<!-- permission-level: PM -->` | なし（削除） |
| Step 2.5 TDD パターン分析 | あり（v4.4.1 移行済み） | **同一** |
| Step 4 アクション抽出の反映先 | `docs/xxx`, `.claude/rules/xxx.md` 等 | **追加**: `docs/artifacts/knowledge/xxx.md`（Knowledge Layer） |
| Step 5 出力先 | `docs/artifacts/retro-wave-{N}.md`、`docs/artifacts/retro-phase-{N}.md` | 同一 + `docs/artifacts/retro-<version>.md`（リリース単位追加） |

**影式固有の保護対象**: `<!-- permission-level: PM -->` の明示（v4.5.0 では削除されているが維持推奨）

---

#### 1.10 `ship.md`

| 項目 | 現行（影式） | LAM 4.5.0 |
|------|-------------|-----------|
| description | `Ship — 変更の棚卸し・論理コミット・後処理` | `論理グループ分けコミット - 変更を棚卸し・分類・コミット` |
| 配置先/呼び出しの記載 | あり（冒頭に記載） | なし（削除） |
| Phase 構成 | 5 Phase（1→2→3→4→5） | 5 Phase（1→2→3→4→5）+ 手動作業通知（同一構成） |
| Phase 1 秘密情報チェック | 8パターン（`.env`, `credentials`, `*.key`, `settings.local.json`, `secret`, `token`, `password`, `api_key`） | 6パターン（`*.key` と `api_key` が欠落） |
| Phase 2 Doc Sync | 影式従来フロー（CHANGELOG/README/README_en/CHEATSHEET の4ファイルチェック）+ doc-sync-flag 分岐 | **doc-sync-flag ファーストフロー**: 2-1 flag参照 → 2-2 PG/SE/PM分類 → 2-3 doc-writer 呼び出し → 2-4 フラグクリア。ADR 起票提案追加 |
| Phase 2 の影式固有 | README_en.md / CHEATSHEET.md チェック | なし |
| Phase 5 | コミット + push + 完了報告 | コミット + `git log --oneline -N` 表示。**push しない**（明示的分離）。手動作業通知が Phase 5 後セクションに統合 |

**影式固有の保護対象**:
- Phase 2 の README_en.md / CHEATSHEET.md チェック（doc-sync-flag 未存在時のフォールバック）
- Phase 1 の `*.key`, `api_key` パターン（v4.5.0 で欠落）

---

#### 1.11 `wave-plan.md`

| 項目 | 現行（影式） | LAM 4.5.0 |
|------|-------------|-----------|
| permission-level | HTML コメント `<!-- permission-level: SE -->` | なし（削除） |
| Step 1 タスク定義読み込み | `SESSION_STATE.md および docs/tasks/（または docs/specs/*/tasks.md）` | `docs/specs/ および docs/tasks/` |
| 構造化思考の活用 | なし | **新規**: `/magi` の使用を検討する条件を記述 |
| Wave 完了条件の lint | `ruff check クリーン` | `lint チェッククリーン`（ツール非依存に汎用化） |
| 注意事項 | `Phase 1 Retro Try-3: 大規模タスク（L）は単独 Wave を推奨。5タスク以上は分割を必須とする。` | `大規模タスク（L）は単独 Wave を推奨`（5タスク分割必須の記述なし） |
| Wave 完了後 | `/ship` でコミット・push | `/ship` でコミット（push 記述なし） |

**影式固有の保護対象**: `<!-- permission-level: SE -->` の明示

---

## 2. skills/ 差分

### スキル構成

| スキル | 現行 | LAM 4.5.0 | 状態 |
|--------|:----:|:---------:|:----:|
| adr-template | あり | あり | 共通 |
| lam-orchestrate | あり | あり | 共通 |
| skill-creator | あり | あり | 共通 |
| spec-template | あり | あり | 共通 |
| ui-design-guide | なし | あり | 4.5.0のみ（v4.4.1 で導入済みだが影式未導入） |
| magi | なし | あり | **4.5.0新規** |
| clarify | なし | あり | **4.5.0新規** |

### 共通スキルの差分（4件）

---

#### 2.1 `adr-template/SKILL.md`

| 項目 | 現行（影式） | LAM 4.5.0 |
|------|-------------|-----------|
| frontmatter | `name`, `version`, `description` | `name`, `description`, `version`（フィールド順序変更） |
| 適用条件 | `adr-template スキルの明示的な呼び出し時` | `ADR の作成を求められた時` |
| `/ship` 自動起票フロー | なし | **新規**: `/ship` Phase 2 で PM級設計判断検出時に ADR 起票を提案するフロー |
| 参照ドキュメント | `06_DECISION_MAKING.md`、`adr-template スキル` | `06_DECISION_MAKING.md`、`.claude/rules/permission-levels.md`、`/ship コマンド (Phase 2)` |

---

#### 2.2 `lam-orchestrate/SKILL.md` ★重大変更

| 項目 | 現行（影式） | LAM 4.5.0 |
|------|-------------|-----------|
| frontmatter | `name`, `version`, `description` | `name`, `description`, `version`（フィールド順序変更） |
| 構造化思考セクション | AoT + Three Agents + Reflection を内蔵（lam-orchestrate 内に全ロジック記述） | **`/magi` スキルへの委譲**: 発動条件と実行フローの概要のみ記述し、詳細は `.claude/skills/magi/SKILL.md` を参照。レベル別モデル選択テーブルは維持 |
| MAGI System | Three Agents Model（Affirmative/Critical/Mediator） | **MAGI System**（MELCHIOR/BALTHASAR/CASPAR）。名称変更 + Reflection ステップ追加 |
| アンカーファイル名 | `docs/artifacts/YYYY-MM-DD-lam-think-{用途}.md` | `docs/artifacts/YYYY-MM-DD-magi-{用途}.md` |
| アンカーファイルの Single-Writer | Mediator のみ | **CASPAR** のみ |
| `anchor-format.md` 参照先 | `.claude/skills/lam-orchestrate/references/anchor-format.md` | `.claude/skills/magi/references/anchor-format.md`（magi スキル配下に移動） |
| Subagent 選択テーブル | 9行（v4.4.1 で拡充済み） | 同一（9行） |
| ループ統合 | lam-loop-state.json スキーマの詳細定義 | **SSOT 委譲強化**: `fullscan_pending` フィールドは廃止済みとの注記、G3/G4 の設定タイミング明記 |
| hooks 連携 | 3 hook の簡易テーブル | **拡充**: 3 hook（Stop/PostToolUse/PreToolUse）の参照タイミング・動作を詳述、データフローの ASCII 図。`stop_hook_active=true` の再帰防止説明、ループ主制御は Claude 側の責務と明記 |
| エスカレーション条件 | 3条件（PM級検出、2イテレーション連続未修正、max_iterations） | **6条件に拡充**: 再帰防止（`stop_hook_active=true`）、コンテキスト枯渇（PreCompact）、テスト数減少を追加 |
| `lam-orchestrate/references/` | `anchor-format.md` のみ | `anchor-format.md`（MAGI System 対応に更新）+ **`magi-skill.md` 新規**（magi スキルの SKILL.md コピー） |

**移行方針**: 構造化思考の詳細ロジックを `/magi` スキルに移動し、lam-orchestrate は参照のみとする。アンカーファイル名を `lam-think` → `magi` に変更。

---

#### 2.3 `skill-creator/SKILL.md`

完全同一。差分なし。

---

#### 2.4 `spec-template/SKILL.md`

| 項目 | 現行（影式） | LAM 4.5.0 |
|------|-------------|-----------|
| Section 6 | `制約事項` | **新規挿入 Section 6**: `権限等級（v4.0.0）` — 各変更項目の PG/SE/PM 分類テーブル + `permission-levels.md` 参照 |
| Section 9 権限等級 | `権限等級（v4.0.0）` — 1行参照文のみ | 旧 Section 6 の位置に移動し、テーブル形式で詳細化 |
| 以降のセクション番号 | 6-11（制約→変更履歴） | 7-11（制約→変更履歴）。Section 6 挿入により +1 ずれ |

**備考**: v4.4.1 → v4.5.0 で変化なし（v4.4.1 移行時の差分がそのまま残存）。

---

### v4.5.0 のみのスキル（3件）

---

#### 2.5 `magi/SKILL.md` ★新規

| 項目 | 内容 |
|------|------|
| 目的 | MAGI System による構造化意思決定フレームワーク。旧 Three Agents Model の進化版 |
| 由来 | lam-orchestrate 内の構造化思考セクションを独立スキル化 |
| MAGI System | MELCHIOR（科学者/推進者）、BALTHASAR（母/批判者）、CASPAR（女/調停者） |
| 実行フロー | Step 0: AoT Decomposition → Step 1: Divergence → Step 2: Debate → Step 3: Convergence → Step 4: Reflection → Step 5: AoT Synthesis |
| Reflection | **新規追加**: 全員で結論を検証（1回限り）。致命的な見落とし時のみ修正。Bikeshedding 防止ルール |
| アンカーファイル | `docs/artifacts/YYYY-MM-DD-magi-{用途}.md`。CASPAR のみ書き込み権限 |
| references | `anchor-format.md`（アンカーテンプレート） |
| 参照先 | `docs/internal/06_DECISION_MAKING.md`（SSOT）、`docs/specs/magi-skill-spec.md` |

**影式への影響**: `decision-making.md` ルールの Three Agents → MAGI 名称変更が必要。既存のアンカーファイルパスの変更が必要。

---

#### 2.6 `clarify/SKILL.md` ★新規

| 項目 | 内容 |
|------|------|
| 目的 | 文書の曖昧さ・矛盾・欠落をインタビュー形式で特定し精緻化 |
| 対象 | spec、design、ADR、tasks 等の技術文書 |
| Phase 構成 | Phase 1: 文書分析（曖昧さ/矛盾/欠落検出）→ Phase 2: 質問生成+インタビュー → Phase 3: 文書更新 → Phase 4: 完了判定 |
| 曖昧さ検出パターン | 曖昧な修飾語、未定義用語、主語欠落、数値欠落、条件欠落、スコープの曖昧さ |
| Three Agents 提案 | ユーザーが「わからない」と回答時に自動発動 |
| 回答パターン | 具体的回答→直接反映、skip→TBD マーク、任せる→仮決定マーク |
| 複数文書横断チェック | spec → design → tasks 間の整合性チェック |
| 設計原則 | 1回3-5問制限、質問に必ず提案を添える、TBD/仮決定で止まらない設計 |

**影式への影響**: `planning-quality-guideline.md` の Requirements Smells/Example Mapping と連携。PLANNING フェーズでの文書品質向上に有用。

---

#### 2.7 `ui-design-guide/SKILL.md`（v4.4.1 で導入済み、影式未導入）

| 項目 | 内容 |
|------|------|
| 目的 | UI/UX 設計時のチェックリスト。PLANNING フェーズで `docs/specs/ui-*.md` 作成時に自動適用 |
| 5つの観点 | アクセシビリティ（WCAG 2.1 AA）、状態設計（5 UI States）、レスポンシブ設計、フォーム UX、パフォーマンス意識 |
| 影式への適用 | tkinter ベースのため Web 固有項目（レスポンシブ、LCP/CLS）は直接適用しないが、状態設計やアクセシビリティの原則は有用 |

**備考**: v4.4.1 差分分析で既に記述済み。内容は v4.4.1 → v4.5.0 で変更なし。

---

### references/ の差分

#### `lam-orchestrate/references/anchor-format.md`

| 項目 | 現行（影式） | LAM 4.5.0 |
|------|-------------|-----------|
| タイトル | `# lam-orchestrate Anchor: {用途}` | `# Structured Thinking Anchor: {用途}` |
| Web サーチ結果 | `**Web サーチ結果**:` | `**Web サーチ結果**（WebSearch 利用可能な場合のみ。不可時はスキップ）:` |
| Three Agents 表記 | `Three Agents Debate` | 同一（anchor-format.md 内では名称変更なし） |

**備考**: v4.5.0 では `magi/references/anchor-format.md` にも同一内容のコピーが存在。lam-orchestrate 側と magi 側の両方に配置。

#### `lam-orchestrate/references/magi-skill.md` ★新規

magi スキルの SKILL.md と同一内容のコピー。lam-orchestrate から magi スキルの詳細を参照するための reference ファイル。

---

## 3. agents/ 差分

### エージェント構成

8 エージェント全て両方に存在。新規/削除なし。

---

#### 3.1 `code-reviewer.md`

| 項目 | 現行（影式） | LAM 4.5.0 |
|------|-------------|-----------|
| permission-level 位置 | ボディ内（`# permission-level: SE`） | **フロントマター内**: `# permission-level: SE` |
| 役割境界セクション | あり（code-reviewer vs quality-auditor の使い分け） | **削除** |
| 出力形式のPG/SE/PM | 各 Issue 末尾に `**[PG/SE/PM]**` + 権限等級サマリーテーブル | 各 Issue 先頭に `**[PG/SE/PM]**` + 権限等級テーブルが出力形式内に統合 |
| PG/SE/PM 分類基準セクション | 権限等級サマリーテーブルで記述 | **独立セクション（v4.0.0）**: 分類基準の説明 + `permission-levels.md` 準拠の明記 |
| 総合評価 | `A/B/C/D` | `A / B / C / D / F`（F 評価追加） |

---

#### 3.2 `design-architect.md`

| 項目 | 現行（影式） | LAM 4.5.0 |
|------|-------------|-----------|
| permission-level 位置 | ボディ内（`# permission-level: PM`） | **フロントマター内**: `# permission-level: SE` |
| permission-level 等級 | **PM** | **SE** |
| description | `大規模設計や並列設計時に委任可能。単一機能の設計はメインで直接実施する方が効率的。` | `PLANNINGフェーズでの設計作業で使用推奨。` |

**影式固有の保護対象**: permission-level の PM→SE 変更は慎重に検討。影式では design-architect を PM 級としている理由（設計判断の重要性）がある。

---

#### 3.3 `doc-writer.md`

| 項目 | 現行（影式） | LAM 4.5.0 |
|------|-------------|-----------|
| permission-level 位置 | ボディ内（`# permission-level: SE` + 注記） | **フロントマター内**: `# permission-level: SE` |
| permission-level 注記 | ボディ内に `docs/specs/` 書き込みが PM 級だが lam-orchestrate 経由の場合に限定する旨の説明 | なし（削除） |
| ドキュメント自動追従モード | doc-sync-flag 連携（4ステップ: 読み取り→特定→更新→報告） | **v4.0.0 / Wave 3 版**: `/ship` Phase 2 からの呼び出しフロー。入力仕様、処理フロー、diff 形式の Doc Sync 更新案出力、完全実装への言及 |

---

#### 3.4 `quality-auditor.md` ★重要変更

| 項目 | 現行（影式） | LAM 4.5.0 |
|------|-------------|-----------|
| permission-level 位置 | ボディ内（`# permission-level: SE`） | **フロントマター内**: `# permission-level: SE` |
| model | **opus** | **sonnet** |
| 役割境界セクション | あり（quality-auditor vs code-reviewer の使い分け） | **削除** |
| Step 3 タイトル | `仕様ドリフトチェック`（Step 3 と Step 3b が独立） | `ドキュメント整合性監査 + 仕様ドリフトチェック`（Step 3 に統合） |
| 仕様ドリフトチェック | 影式固有の詳細版（検出方法3ステップ、ドリフト種別3種） | **v4.0.0 強化版**: ドリフト種別 **4種**（Phase/Wave 未到達を追加）、PG/SE/PM 分類付き出力形式 |
| 構造整合性チェック | 影式固有版（R-1〜R-11 品質ルール適合性、ADR 決定事項反映） | **v4.0.0 版**: スキーマ整合性、参照整合性、データフロー整合性、設定整合性、ドキュメント間整合性の5観点。具体的チェックテーブル付き |
| Step 番号 | Step 1-7（7ステップ） | Step 1-6（6ステップ。仕様ドリフト+構造整合性が Step 3 に統合） |
| 禁止事項 | `PM級の修正の実施（PG/SE級は permission-level に従い実施可）` | `PM級の修正の実施（指摘のみ、承認ゲート。PG/SE級の修正は許可。permission-levels.md 参照）` |

**影式固有の保護対象**:
- model: `opus` の維持判断（品質 vs コスト）
- Step 3b の R-1〜R-11 品質ルール適合性チェック（v4.5.0 では5観点の構造整合性に置換。影式の `building-checklist.md` 内容だが AUDITING 時の検証としても有用）

---

#### 3.5 `requirement-analyst.md`

| 項目 | 現行（影式） | LAM 4.5.0 |
|------|-------------|-----------|
| permission-level 位置 | ボディ内（`# permission-level: PM`） | **フロントマター内**: `# permission-level: PM` |

本文は同一。

---

#### 3.6 `task-decomposer.md`

| 項目 | 現行（影式） | LAM 4.5.0 |
|------|-------------|-----------|
| permission-level 位置 | ボディ内（`# permission-level: SE` + 注記） | **フロントマター内**: `# permission-level: SE` |
| model コメント | なし（model: haiku は既にフロントマターに記載） | 同一（変更なし） |

本文は同一。

---

#### 3.7 `tdd-developer.md` ★重大変更

| 項目 | 現行（影式） | LAM 4.5.0 |
|------|-------------|-----------|
| permission-level 位置 | ボディ内（`# permission-level: SE`） | **フロントマター内**: `# permission-level: SE` |
| description | `大規模タスクや並列実装時に委任可能。小規模タスクはメインで直接実装する方が効率的。` | `BUILDINGフェーズでの実装作業で使用推奨。` |
| Pre-flight セクション | なし（`実装前チェック` のチェックリストのみ） | **新規 Pre-flight セクション**: 4ステップの必読ルール。`code-quality-guideline.md` の Read 必須、タスク指定仕様書の Read 必須、変更対象ファイルの Read 必須、既存テスト構造の確認必須 |
| 品質ゲート暗記項目 | なし | **新規**: 関数50行以内、ネスト3階層以内、エラー握りつぶし禁止、Silent Failure 禁止 |
| 参照ドキュメント | `02_DEVELOPMENT_FLOW.md`、`03_QUALITY_STANDARDS.md` | `code-quality-guideline.md`（**Pre-flight で必読**）、`02_DEVELOPMENT_FLOW.md`、`03_QUALITY_STANDARDS.md` |
| 事前確認チェック | 5項目のチェックリスト | **削除**（Pre-flight に統合） |

---

#### 3.8 `test-runner.md`

| 項目 | 現行（影式） | LAM 4.5.0 |
|------|-------------|-----------|
| permission-level 位置 | ボディ内（`# permission-level: PG`） | **フロントマター内**: `# permission-level: PG` |
| model | **haiku** | **haiku**（同一。v4.4.1 で sonnet → haiku に変更済み） |

本文は同一。

---

## 4. 影式固有保持項目

以下は影式固有であり、LAM 4.5.0 テンプレートへの移行時に失われないよう注意:

### 4.1 コマンド関連

| 項目 | 保護理由 |
|------|---------|
| `building.md` の R-1〜R-6 インライン参照 | `building-checklist.md` 経由で維持（影式では既に分離済み） |
| `ship.md` Phase 2 の README_en.md / CHEATSHEET.md チェック | 影式固有のドキュメント。doc-sync-flag 未存在時のフォールバックとして維持 |
| `ship.md` Phase 1 の `*.key`, `api_key` パターン | v4.5.0 で欠落。影式で追加維持 |
| `retro.md` / `pattern-review.md` / `wave-plan.md` の permission-level 記述 | v4.5.0 では削除されているが、影式では PM/SE 級であることの明示を維持 |
| `quick-load.md` のフォールバック git log 推定 | v4.5.0 では簡略化。影式では有用な機能として維持 |
| `auditing.md` の権限等級サマリーテーブル | v4.5.0 の出力テンプレートにはないが、影式の運用で有用 |
| `project-status.md` の KPI 計算ロジック（K1〜K5） | v4.5.0 では仕様書に委譲。影式ではインラインで維持可能 |
| `full-review.md` の `building-checklist.md` R-1〜R-11 参照 | quality-auditor #3 への指示として維持 |

### 4.2 エージェント関連

| 項目 | 保護理由 |
|------|---------|
| `quality-auditor.md` の model: opus | v4.5.0 では sonnet に変更。影式での品質要件に応じて判断 |
| `design-architect.md` の permission-level: PM | v4.5.0 では SE に降格。影式での設計判断の重要性に応じて判断 |
| `quality-auditor.md` の R-1〜R-11 適合性チェック | v4.5.0 では5観点の構造整合性に置換。影式の `building-checklist.md` との連携として維持推奨 |

### 4.3 スキル関連

| 項目 | 保護理由 |
|------|---------|
| `lam-orchestrate/references/anchor-format.md` の現行内容 | v4.5.0 で `magi/references/` にも配置。影式では両方に配置するか、magi 側のみにするか判断が必要 |

---

## 5. Migration Action Items

### Phase 1: 新規 rules の導入

1. [ ] `.claude/rules/code-quality-guideline.md` を LAM 4.5.0 から導入
2. [ ] `.claude/rules/planning-quality-guideline.md` を LAM 4.5.0 から導入
3. [ ] `.claude/rules/decision-making.md` を MAGI System 版に更新（Three Agents → MAGI）
4. [ ] `.claude/rules/phase-rules.md` を v4.5.0 版に更新（影式固有ルール R-7〜R-11, A-1〜A-4 を `building-checklist.md` 経由で維持）

### Phase 2: 新規スキルの導入

5. [ ] `.claude/skills/magi/` ディレクトリを作成し SKILL.md + references/anchor-format.md を配置
6. [ ] `.claude/skills/clarify/` ディレクトリを作成し SKILL.md を配置
7. [ ] `.claude/skills/ui-design-guide/` ディレクトリを作成し SKILL.md を配置（影式の tkinter ベースに適用する場合）
8. [ ] `.claude/skills/lam-orchestrate/references/magi-skill.md` を追加

### Phase 3: エージェントの更新

9. [ ] 全8エージェントの permission-level をフロントマターに移動
10. [ ] `code-reviewer.md`: 役割境界セクション削除、PG/SE/PM 分類基準セクション追加、F 評価追加
11. [ ] `quality-auditor.md`: model opus→sonnet の判断（影式では opus 維持を推奨）、構造整合性チェックを v4.5.0 版に更新しつつ R-1〜R-11 参照を維持
12. [ ] `doc-writer.md`: ドキュメント自動追従モードを `/ship` Phase 2 連携版に更新
13. [ ] `tdd-developer.md`: Pre-flight セクション追加、`code-quality-guideline.md` 参照追加
14. [ ] `design-architect.md`: permission-level PM→SE の判断（影式では PM 維持を推奨）

### Phase 4: コマンドの差分適用

15. [ ] `planning.md`: 構造化思考セクション + 権限等級セクション追加
16. [ ] `building.md`: Step 4 影響分析追加、TDD サイクルの R-1〜R-6 をインラインから `building-checklist.md` 参照に変更
17. [ ] `auditing.md`: コード明確性チェック追加、ドキュメント整合性5項目に拡充、`/full-review` 使い分けガイド追加
18. [ ] `full-review.md`: Stage 0〜5 構成に更新（Scalable Code Review 統合）。影式では Plan なし（~10K）の従来モードから段階的に拡張
19. [ ] `ship.md`: Phase 2 を doc-sync-flag ファーストフローに更新しつつ影式固有フォールバック維持
20. [ ] `retro.md`: Step 4 に Knowledge Layer 反映先追加
21. [ ] `wave-plan.md`: 構造化思考セクション追加
22. [ ] `quick-save.md` / `quick-load.md`: description 更新、マイナー差分適用

### Phase 5: lam-orchestrate の更新

23. [ ] 構造化思考セクションを `/magi` 参照に変更
24. [ ] アンカーファイル名を `lam-think` → `magi` に変更
25. [ ] hooks 連携テーブルの拡充、データフロー図の追加
26. [ ] エスカレーション条件を6条件に拡充
27. [ ] `anchor-format.md` を MAGI 版に更新

### Phase 6: 新規依存ファイルの確認

| 参照元 | 参照先 | 影式での状態 |
|--------|--------|------------|
| `planning.md` / `phase-rules.md` | `.claude/rules/planning-quality-guideline.md` | 未作成（Phase 1 で導入） |
| `tdd-developer.md` / `phase-rules.md` | `.claude/rules/code-quality-guideline.md` | 未作成（Phase 1 で導入） |
| `magi/SKILL.md` | `docs/specs/magi-skill-spec.md` | 未作成（必要に応じて作成） |
| `magi/SKILL.md` | `docs/internal/06_DECISION_MAKING.md` のMMAGI対応 | 更新が必要 |
| `full-review.md` Stage 0 | `.claude/hooks/analyzers/scale_detector.py` | 未実装（Scalable Review 段階導入時に対応） |
| `full-review.md` Stage 1-3 | `.claude/hooks/analyzers/` 配下のモジュール群 | 未実装（同上） |

### Phase 7: MAGI System への名称変更

28. [ ] `docs/internal/06_DECISION_MAKING.md` の Three Agents Model → MAGI System 更新
29. [ ] `.claude/rules/decision-making.md` の名称変更
30. [ ] 既存のアンカーファイル（`docs/artifacts/YYYY-MM-DD-lam-think-*`）がある場合のリネーム判断
31. [ ] `adr-template/SKILL.md` の 3 Agents Analysis セクションの MAGI 対応（テンプレート内の `[Affirmative]`/`[Critical]`/`[Mediator]` を `[MELCHIOR]`/`[BALTHASAR]`/`[CASPAR]` に変更するか判断）
