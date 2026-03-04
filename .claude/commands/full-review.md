---
description: "全ソース網羅レビュー + 全Issue修正を一括実行"
---

# Full Review: 網羅的レビュー + 全修正

全ソースコードの品質レビューを並列実行し、発見された Issue をすべて修正する。

## 実行フロー

### Phase 1: 並列監査（3エージェント）

以下の3つの `code-reviewer` エージェントを **Opus モデル** で **並列起動** する:

1. **ソースコードレビュー**
   - 対象: `src/` 配下の全 `.py` ファイル
   - 観点: コード品質、セキュリティ、エラーハンドリング、命名規則
   - 仕様書との突合（`docs/specs/` 参照）

2. **テストコードレビュー**
   - 対象: `tests/` 配下の全 `.py` ファイル
   - 観点: テストカバレッジ、テスト品質、fixture の共通化、FR との対応

3. **品質監査**
   - 対象: プロジェクト全体
   - 観点: アーキテクチャ健全性、依存関係、ドキュメント整合性
   - `.claude/rules/building-checklist.md` の R-1〜R-6 適合性

### Phase 2: レポート統合

3エージェントの結果を統合し、以下の形式でレポートを作成:

```
# 統合監査レポート

## サマリー
- Critical: X件 / Warning: X件 / Info: X件
- 総合評価: [A/B/C/D]

## 対応可能な Issue 一覧
[Issue ごとに: 重篤度、場所、内容、修正方針]

## 対応不可な Issue 一覧
[理由と追跡先]
```

### Phase 3: 全修正

`.claude/rules/audit-fix-policy.md` に従い、**対応可能な Issue をすべて修正する**。

修正順序:
1. Critical Issue（最優先）
2. Warning Issue
3. Info Issue
4. 仕様書の同期更新

### Phase 4: 検証

1. `pytest tests/ -v --tb=short` — 全テスト PASSED 確認
2. `ruff check src/ tests/` — リントクリーン確認
3. カバレッジ確認 — 各モジュール 90% 以上

### Phase 5: 完了報告

```
[Full Review] 完了

修正前: Critical X / Warning X / Info X
修正後: Critical 0 / Warning 0 / Info 0（対応不可 X件を除く）
テスト: XXX passed / 0 failed
カバレッジ: XX%
```

## モデル選択ガイド

| エージェント | 推奨モデル | 理由 |
|-----------|----------|------|
| code-reviewer (ソース) | **Opus** | 深い分析が必要 |
| code-reviewer (テスト) | **Opus** | テスト品質の判断が必要 |
| quality-auditor | **Opus** | アーキテクチャ判断が必要 |
| 修正実装 | **Sonnet** | 定型的な修正作業 |

## 注意事項

- Phase 1 の3エージェントは必ず **並列** で起動すること（逐次実行は禁止）
- 修正後は必ずテスト + ruff で検証すること
- 仕様ズレが見つかった場合は `.claude/rules/spec-sync.md` に従い同時修正すること
