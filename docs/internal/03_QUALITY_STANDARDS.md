# Architectural Standards & Quality Gates

本ドキュメントは、"Living Architect" がコードを生成・レビューする際の基準値（Quality Gates）である。

## 1. Design Principles (設計原則)

### Single Source of Truth (SSOT)

- 設定値、定数、型定義は一箇所で定義する。重複定義はバグの温床とみなす。
- ドキュメントとコードが乖離した場合、ドキュメントを正とする。

### Cognitive Load Management (認知負荷の管理)

- **Magic Numbers/Strings**: 禁止。定数化すること。
- **Function Length**: 1 関数は 1 画面（約 30-50 行）を目安とする。
- **Naming**: 「何が入っているか」だけでなく「何のためにあるか」がわかる名前をつける。

## 2. Documentation Standards (ドキュメント基準)

### ADR (Architectural Decision Records)

重要な技術的決定（ライブラリ選定、DB 設計、アーキテクチャ変更）を行う際は、必ず ADR を作成すること。

- Status, Context, Decision, Consequences を記述する。

### Docstrings & Comments

- **What**: コードで語る。
- **Why**: コメントで語る。
- **Workaround**: `FIXME` または `HACK` タグと理由を記述する。

## 3. Spec Maturity (仕様の成熟度)

- **Unambiguous**: 自然言語の曖昧さが排除されている。
- **Testable**: テストケースとして記述可能である。
- **Atomic**: 独立して実装・検証可能である。

## 4. Refactoring Triggers (リファクタリングのトリガー)

以下の兆候が見られた場合、機能追加を停止し、リファクタリングを優先する。

- **Deep Nesting**: ネスト > 3 階層
- **Long Function**: 行数 > 50 行
- **Duplication**: 重複 > 3 回 (Rule of Three)
- **Parameter Explosion**: 引数 > 4 個
- **Nested Ternary**: ネストした三項演算子
- **Dense One-liner**: 理解に時間がかかるワンライナー

## 5. Code Clarity Principle（コード明確性原則）

**Clarity over Brevity（明確さ > 簡潔さ）** を原則とする。

### 推奨
- 読みやすさを最優先する
- 明示的なコードを書く（暗黙の挙動に頼らない）
- 適切な抽象化を維持する（1箇所でしか使わなくても意味のある抽象化は残す）
- 条件分岐は switch/if-else で明確に書く

### 禁止
- ネストした三項演算子
- 読みやすさを犠牲にした行数削減
- 複数の関心事を1つの関数に統合
- デバッグ・拡張を困難にする「賢い」コード
- 3行程度の類似コードを無理に共通化

### 判断基準
「このコードを3ヶ月後の自分が読んで、すぐに理解できるか？」

## 6. Python Coding Conventions (Python コーディング規約)

本プロジェクトは **Python 3.12+** を使用する。以下の規約に従うこと。

- **PEP 8**: Python 標準コーディングスタイルに準拠する。
- **Type Hints**: 全ての関数シグネチャに型アノテーションを付与する（`def func(x: int) -> str:`）。
  複雑な型は `from __future__ import annotations` または `typing` モジュールを活用する。
- **Linter/Formatter**: `ruff` を使用する（linting + formatting）。
  pyproject.toml の `[tool.ruff]` で `line-length = 100`、`select = ["E", "W", "F", "I", "UP", "B", "SIM"]` を設定済み。
- **Docstrings**: モジュール・クラス・関数レベルで Google スタイルの docstring を記述する。

## 7. Building Defect Prevention (実装不具合防止)

Phase 1 監査で発見された不具合パターン分析に基づく防止ルール。
ルール本体は `.claude/rules/building-checklist.md` に定義（自動ロード対象）。

| ルール | 防止する不具合パターン | 適用タイミング |
|--------|----------------------|---------------|
| R-1: FR 突合チェック | 仕様-実装ドリフト | Green 直後 |
| R-2: dict ディスパッチ | 列挙の網羅漏れ | Green（実装時） |
| R-3: 定数→使用の即時接続 | SSOT 違反 | Red-Green サイクル内 |
| R-4: FR チェックリスト駆動テスト | FR 実装漏れ | Red（テスト作成時） |
| R-5: カバレッジ確認 | テストの構造的盲点 | Green 直後 |
| R-6: else の正当性確認 | 暗黙のフォールバック | Green（実装時） |

根拠分析: `docs/memos/audit-report-wave3.md`, `docs/memos/audit-report-full-source.md`

## 8. Technology Trend Awareness (トレンド適応)

- ライブラリの Deprecated 状況を定期的に確認する。
- 長期保守性を最優先し、枯れた技術と最新技術のバランスをとる。
