# Subagent Strategy

本ドキュメントは、Living Architect Model における Subagent の運用戦略を定義する。

## 1. エージェント一覧

### カスタムエージェント（`.claude/agents/`）

| エージェント | 役割 | 推奨モデル | 主な使用フェーズ |
|:------------|:-----|:----------|:---------------|
| `requirement-analyst` | 要件分析・仕様変換 | Sonnet | PLANNING |
| `design-architect` | 設計・アーキテクチャ | Sonnet | PLANNING |
| `task-decomposer` | タスク分解・依存整理 | Haiku | PLANNING |
| `tdd-developer` | TDD 実装（Red-Green-Refactor） | Sonnet | BUILDING |
| `test-runner` | テスト実行・分析 | Haiku | BUILDING / AUDITING |
| `code-reviewer` | コードレビュー | Sonnet | AUDITING |
| `quality-auditor` | 品質監査・改善提案 | Sonnet | AUDITING |
| `doc-writer` | ドキュメント作成・更新 | Sonnet | 全フェーズ |

### ビルトインエージェント

| エージェント | 用途 |
|:------------|:-----|
| `Explore` | コードベース探索（Glob/Grep/Read） |
| `Plan` | 実装計画の設計 |
| `general-purpose` | 汎用的な調査・マルチステップタスク |

## 2. 委任判断基準

### メインで直接実施するケース

- 単一ファイル・小規模変更
- 深い分析・判断が必要（Opus の推論力が必要）
- コンテキスト内の情報だけで完結する作業
- 3 回以内の検索で完了する調査

### Subagent に委任するケース

- 複数ファイルにまたがる並列可能な作業
- 定型的な検査・実行（テスト、リント、カバレッジ）
- 大量の出力が予想される作業（メインのコンテキスト保護）
- 独立した複数タスクの同時進行

### 判断フローチャート

```
作業が発生
  ├─ 単一ファイル・小規模? → メインで直接実施
  ├─ 深い判断が必要? → メインで直接実施
  ├─ 定型的な検査? → Subagent に委任
  ├─ 並列可能な複数作業? → 複数 Subagent を同時起動
  └─ 大量出力が予想? → Subagent に委任（サマリーのみ取り込み）
```

## 3. 並列実行パターン

### `/full-review`（4 並列監査）

```
メイン（Opus）
  ├─ #1 code-reviewer: ソースコード品質
  ├─ #2 code-reviewer: テスト品質
  ├─ #3 quality-auditor: アーキテクチャ・仕様ドリフト
  └─ #4 code-reviewer: セキュリティ（OWASP Top 10）
  │
  ▼ 結果統合
  メイン: Issue 一覧作成 → 修正実施 → Green State 検証
```

### `/ship`（論理コミット）

```
メイン（Opus）
  ├─ 変更の棚卸し（git diff 分析）
  ├─ 論理グループ分け
  └─ 順次コミット（依存順）
```

### BUILDING（大規模タスク）

```
メイン: 設計判断 + タスク分割
  ├─ tdd-developer: モジュール A 実装
  ├─ tdd-developer: モジュール B 実装（A と独立）
  └─ test-runner: 既存テストの回帰確認
```

## 4. モデル選択ガイド

| モデル | 強み | 推奨用途 |
|:------|:-----|:---------|
| **Opus** | 深い推論、複雑な判断、大局的分析 | 設計判断、要件分析、品質監査、意思決定 |
| **Sonnet** | 高速、コスト効率、十分な品質 | TDD 実装、テスト実行、ドキュメント作成、定型タスク |
| **Haiku** | 最速、最低コスト | テスト実行・分析（test-runner）、単純な検索、フォーマット変換 |

### 選択基準

- **判断の深さ**が必要 → Opus
- **速度とコスト**が重要 → Sonnet
- メインセッションは常に **Opus**（Living Architect としての判断品質を担保）

## 5. 出力統合フォーマット

Subagent からの結果をメインに取り込む際のルール:

### サマリー形式（推奨）

```markdown
## [エージェント名] 結果
- 結論: [1-2 行の要約]
- 発見事項: [Critical X件 / Warning X件 / Info X件]
- アクション: [必要な対応の一覧]
```

### 禁止事項

- Subagent の全出力をメインのコンテキストに展開しない
- 同じ検索をメインと Subagent で重複して行わない
- Subagent に委任した作業をメインで再実行しない

### コンテキスト節約の原則

1. Subagent の出力は要約して取り込む
2. 詳細が必要な場合のみ、該当部分を展開する
3. 長大な出力が予想される場合は Subagent に委任してサマリーだけ受け取る
