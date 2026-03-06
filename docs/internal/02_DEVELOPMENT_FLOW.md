# Development Flow & TDD Cycle

本ドキュメントは、**Phase 1 (設計)** および **Phase 2 (実装)** におけるプロトコルを定義する。
"Definition of Ready" を通過したタスクのみが、このフローに乗ることができる。

## Phase 1: The "Pre-Flight" Impact Analysis (着手前影響分析)

**[PLANNING]** モードにて、以下の分析を行う。

1.  **Dependency Traversal (依存関係の巡回)**:
    - `grep_search` 等を用いて、変更対象モジュールの依存元・依存先を物理的に特定する。
2.  **Static & Mental Simulation**:
    - コードを実行せず、静的解析と論理的思考実験により、DB スキーマや API への波及効果を予測する。
3.  **Git State Verification (Git 状態の検証)**:
    - `git status` および `git diff` を用いて、変更対象ファイルの現在の状態を確認する。
    - 未コミット変更がある場合、その差分を分析に含める。
4.  **Phase State Verification (フェーズ状態の検証)**:
    - `.claude/current-phase.md` を確認し、現在の開発フェーズ（PLANNING/BUILDING/AUDITING）を把握する。
    - フェーズとタスク内容が一致しない場合（例: BUILDING 中に仕様策定を要求された）、ユーザーに確認する。
5.  **Risk Assessment (Critical Agent)**:
    - `docs/internal/06_DECISION_MAKING.md` の **Critical Agent** として振る舞い、「手戻りリスク」と「破壊的変更の有無」を徹底的に洗い出す。
    - 楽観的な予測は排除し、最悪のケースを想定してユーザーに報告する。
6.  **Implementation Plan (Artifact)**:
    - 変更内容、検証計画をまとめた `implementation_plan.md` を作成し、ユーザーの承認を得ることを必須とする。

### AoT フレームワークとの連携

Phase 1 の各ステップにおいて、Atom of Thought フレームワークを活用できる:

| ステップ | AoT 適用 | 参照 |
|----------|----------|------|
| 要件定義 | 要件の Atom 分解 | `.claude/agents/requirement-analyst.md` |
| 設計 | 設計の Atom 分解 | `.claude/agents/design-architect.md` |
| タスク分割 | タスクの Atom 化 | `.claude/agents/task-decomposer.md` |

詳細は `docs/internal/06_DECISION_MAKING.md` Section 5: AoT を参照。

> **Note**: AoT は主に Phase 1 で使用するが、Phase 2 での実装中に新たな設計判断が発生した場合や、
> Phase 3 でのリファクタリング方針決定時にも適用可能である。

## Phase 2: The TDD & Implementation Cycle (実装サイクル)

**[BUILDING]** モードにて、以下の厳格なサイクル（t-wada style）を回す。

> **Kage-Shiki テスト環境**: `pytest` を使用する。テストは `tests/` 配下に配置し、
> `pytest tests/` で実行する。fixture は `conftest.py` で管理する。

### Step 1: Spec & Task Update (Dynamic Documentation)

- コードを書く前に、必ず `./docs/specs/` および `./docs/adr/` の更新案を提示する。
- ドキュメントとコードの同期は絶対である。
- 進捗管理には `task.md` を使用し、タスクの細分化と完了状況を可視化することを推奨する。

### Step 2: Red (Test First)

- 「仕様をコードで表現する」段階。
- 実装対象の機能要件を満たし、かつ**現在は失敗する**テストコードを作成する。
- テスト環境がない場合は、テストコード自体を「実行可能な仕様書」として提示する。

### Step 3: Green (Minimal Implementation)

- テストを通過させるための**最小限のコード**を実装する。
- 最速で Green にすることを優先し、設計の美しさは二の次とする。

### Step 4: Refactor (Clean Up)

- **Green になった後、初めて設計を改善する。**
- 重複排除、可読性向上、複雑度低減を行う。

### Step 5: Commit & Review

- 一つのサイクル（Red-Green-Refactor）が完了したら、直ちにユーザーに報告する。
- 検証結果は `walkthrough.md` にまとめ、スクリーンショットやログと共に報告することを必須とする。

## Phase 3: Periodic Auditing (定期監査)

**[AUDITING]** モードにて、以下の活動を行う。

1.  **Full Codebase Review**: "Broken Windows" の修復。
2.  **Massive Refactoring**: アーキテクチャレベルの改善。
3.  **Documentation Gardening**: ドキュメントの動的保守と整合性確認。
4.  **Context Compression**: セッションが長期化した際、決定事項をドキュメントに書き出し、コンテキストリセットを提案する。

---

## Wave-Based Development (Wave 開発サイクル)

Phase 2 (BUILDING) および Phase 3 (AUDITING) は、**Wave** と呼ぶ反復サイクルで進行する。

### Wave の定義

1〜3 個の関連タスクを選定し、以下のサイクルを 1 Wave として回す:

```
Wave 計画 (/wave-plan)
  → TDD 実装 (/building)
    → 監査・修正 (/full-review)
      → コミット (/ship)
        → 振り返り (/retro) [Phase/Wave 完了時]
```

### Wave 選定基準

| 基準 | 説明 |
|:-----|:-----|
| 依存関係 | 先行タスクが完了しているものを優先 |
| 統合リスク | 結合度の高いタスクは同一 Wave にまとめる |
| スコープ | 1 Wave = 1 セッションで完了可能な規模を目安とする |

### Wave 実績サマリー（Phase 1 MVP）

| Wave | タスク | 内容 |
|:-----|:------|:-----|
| 1 | T-01, T-02 | 設定管理、人格データモデル |
| 2 | T-03, T-04, T-05 | 記憶DB、感情エンジン、LLM統合 |
| 3 | T-06, T-07 | プロンプトビルダー、会話マネージャー |
| 4 | T-08, T-10 | 記憶検索、トレイ常駐 |
| 5 | T-11, T-12, T-13 | GUI表示、吹き出し、ユーザー入力 |
| 6 | T-14, T-15 | 自律発話、ドラッグ移動 |
| 7 | T-09, T-23, T-24 | 記憶要約、ウィザード、外観管理 |
| 8 | T-25 | 起動シーケンス統合 |

---

## Advanced Workflows (高度なワークフロー)

日常の開発で使用する主要コマンドとその連携を示す。

### `/ship` — 論理コミット

変更の棚卸しを行い、論理的なグループごとにコミットを作成する。

1. `git diff` で全変更を把握
2. 変更を論理グループに分類（機能/テスト/ドキュメント/設定）
3. グループごとに順次コミット（依存順）
4. CHANGELOG 更新、README 進捗同期

### `/full-review` — 3 並列監査 + 全修正

3 つの Subagent を並列起動し、網羅的な監査を実施する。

1. `code-reviewer`: コード品質レビュー
2. `quality-auditor`: アーキテクチャ・仕様整合性
3. `test-runner`: テスト実行 + カバレッジ
4. メインが結果を統合し、対応可能な Issue を全て修正（`audit-fix-policy.md`）

### `/wave-plan` — Wave 計画策定

次 Wave で実施するタスクを選定し、実行順序を決定する。

1. タスク一覧から未完了タスクを抽出
2. 依存関係・統合リスク・スコープを評価
3. 1〜3 タスクを選定し、実行順序を提案

### `/retro` — KPT 振り返り

Wave または Phase の完了時に学習サイクルを回す。

1. Keep（継続）/ Problem（問題）/ Try（改善）を整理
2. プロセス改善アクションを特定
3. 次 Wave/Phase への申し送り事項を記録

### コマンド連携図

```
/wave-plan → /building → /full-review → /ship → /retro
    ▲                                              │
    └──────────────── 次 Wave ◄────────────────────┘
```

---

## Quality Rules Integration (品質ルールの適用タイミング)

TDD サイクルの各ステップに、品質ルール（`.claude/rules/`）がどう対応するかを示す。

### TDD サイクルと品質ルールのマッピング

```
Red（テスト作成）
  ├─ R-4: FR チェックリスト駆動テスト
  └─ R-5: 異常系テストの義務
      │
Green（最小実装）
  ├─ R-2: 有限セットは dict ディスパッチ
  ├─ R-6: else のデフォルト値禁止
  └─ R-3: 定数定義 → 使用の即時接続
      │
Green 直後（検証）
  ├─ R-1: FR 突合チェック（文字単位照合）
  ├─ R-5: カバレッジ確認（目標 90%+）
  └─ S-1: 仕様同期チェック（docs/specs/ 更新）
      │
Refactor（設計改善）
  └─ S-4: Refactor 後の仕様再読
      │
AUDITING（監査フェーズ）
  ├─ A-1: 全重篤度への対応義務（Critical/Warning/Info）
  ├─ A-2: 対応不可 Issue の明示
  ├─ A-3: 修正後の再検証（テスト + ruff）
  └─ A-4: 仕様ズレの同時修正（Atomic Commit）
```

### ルール参照先

| ルール群 | ファイル | 適用フェーズ |
|:---------|:--------|:------------|
| R-1〜R-6 | `.claude/rules/building-checklist.md` | BUILDING |
| S-1〜S-4 | `.claude/rules/spec-sync.md` | BUILDING / AUDITING |
| A-1〜A-4 | `.claude/rules/audit-fix-policy.md` | AUDITING |
