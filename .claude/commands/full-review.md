---
description: "全ソース網羅レビュー + 全Issue修正を一括実行"
---

# Full Review: 網羅的レビュー + 全修正

対象ファイル/ディレクトリの品質レビューを並列実行し、発見された Issue をすべて修正する。
権限等級（PG/SE/PM）に基づく修正制御を適用する。

## 引数（必須）

```
/full-review <target>

target: 監査対象（必須）
  - ファイル: src/kage_shiki/core.py
  - ディレクトリ: src/kage_shiki/
  - "." でプロジェクト全体
```

引数なしの場合は対象の指定を求める。

## 実行フロー

### Phase 0: ループ初期化

初回実行時:
1. イテレーション番号を 1 に設定
2. スキャン範囲: **常に指定範囲の全ファイルを対象とする（フルスキャン）**

> **差分チェックモードは廃止。** 修正による周辺への波及影響、修正で蓋をされていた
> 潜在的問題の露出、予期しない場所での影響発生を捕捉するため、
> 毎イテレーションで指定範囲のすべてのファイルを探索する。
> 変更ファイルのみの差分チェックでは、これらの間接的影響を見落とす。

### Phase 0.5: ツール検出

context7 MCP が利用可能か検出する:
- 利用可能 → Phase 1 のエージェントに最新ドキュメント参照を指示可能
- 利用不可 → ローカルドキュメントのみで監査

### Phase 1: 並列監査（4エージェント）

以下の4つのエージェントを **並列起動** する:

#### #1 code-reviewer（ソースコード品質）
- **対象**: `src/` 配下の全 `.py` ファイル
- **観点**: コード品質、エラーハンドリング、命名規則
- **仕様書との突合**: `docs/specs/` 参照
- **出力**: 各 Issue に PG/SE/PM 分類を付与

#### #2 code-reviewer（テスト品質）
- **対象**: `tests/` 配下の全 `.py` ファイル
- **観点**: テストカバレッジ、テスト品質、fixture の共通化、FR との対応
- **出力**: 各 Issue に PG/SE/PM 分類を付与

#### #3 quality-auditor（アーキテクチャ + 仕様ドリフト）
- **対象**: プロジェクト全体
- **観点**:
  - アーキテクチャ健全性、依存関係、構造整合性
  - 仕様ドリフトチェック（`docs/specs/` と実装の乖離検出）
  - `.claude/rules/building-checklist.md` の R-1〜R-11 適合性
- **出力**: 各 Issue に PG/SE/PM 分類を付与

#### #4 code-reviewer（セキュリティ）
- **対象**: プロジェクト全体
- **観点**: OWASP Top 10（インジェクション、認証、シークレット、依存脆弱性、データ露出、デシリアライゼーション）
- **出力**: 各 Issue に PG/SE/PM 分類を付与

### Phase 2: レポート統合

4エージェントの結果を統合し、以下の形式でレポートを作成:

```
# 統合監査レポート（イテレーション N）

## サマリー
- Critical: X件 / Warning: X件 / Info: X件
- 総合評価: [A/B/C/D]

## 権限等級別サマリー
| 等級 | 件数 | 対応 |
|------|------|------|
| PG | X件 | 自動修正 |
| SE | X件 | 修正 + 報告 |
| PM | X件 | 指摘のみ（承認ゲート） |

## 対応可能な Issue 一覧（PG/SE級）
[Issue ごとに: 重篤度、等級、場所、内容、修正方針]

## PM級 Issue 一覧（指摘のみ）
[Issue ごとに: 重篤度、場所、内容、推奨対応]

## 対応不可な Issue 一覧
[理由と追跡先]
```

### Phase 3: 全修正

Phase 1 の監査エージェントは **指摘のみ** を行う。修正はメイン（Orchestrator）が本 Phase で実施する。
権限等級に基づき修正を実施（`.claude/rules/permission-levels.md` 参照）:

- **PG級**: 自動修正（フォーマット、typo、lint 違反等）
- **SE級**: 修正後にレポートで報告（テスト追加、内部リファクタリング等）
- **PM級**: 修正しない（レポートで指摘のみ、承認ゲート）

修正順序:
1. Critical Issue（最優先）
2. Warning Issue
3. Info Issue
4. 仕様書の同期更新（S-1〜S-4 準拠）

### Phase 3b: PM 級 Issue への対応

PM 級の Issue を検出した場合:
1. 対応不可エントリリストを出力
2. `pm_pending` フラグを `lam-loop-state.json` に設定
3. ループが自動停止（lam-stop-hook.py で収束条件に達する）

ユーザー承認後:
- `pm_pending` フラグを clear する: `python -c "import json; d=json.load(open('.claude/lam-loop-state.json')); d.pop('pm_pending',None); json.dump(d,open('.claude/lam-loop-state.json','w'))"`
- ループを再開

### Phase 4: Green State 検証

以下の5条件すべてを満たすか検証する:

| ID | 条件 | 検証方法 |
|----|------|---------|
| G1 | テスト全パス | `pytest tests/ -v --tb=short` |
| G2 | lint エラーゼロ | `ruff check src/ tests/` |
| G3 | 対応可能 Issue ゼロ | Phase 3 修正後の残 Issue 確認 |
| G4 | 仕様差分ゼロ | `docs/specs/` と実装の突合 |
| G5 | セキュリティチェック通過 | エージェント #4 の結果 |

### 自動ループ制御

#### hooks 導入済みの場合
lam-stop-hook による自動ループ（最大 5 イテレーション）:
- Green State 未達 → 自動的に Phase 1 に戻る（**全ファイル再スキャン**）
- Green State 達成 → Phase 5 へ
- 5 イテレーション超過 → 残 Issue を報告して停止

> **重要: 各イテレーションは常にフルスキャン。**
> 前回修正したファイルだけでなく、指定範囲の全ファイルを対象とする。

#### hooks 未導入の場合（現在）
- Green State 未達の場合、修正内容を報告しユーザーに再実行を提案
- ユーザーが `/full-review` を再実行することで手動ループ

### Phase 5: 完了報告

```
[Full Review] 完了（イテレーション N）

修正前: Critical X / Warning X / Info X
修正後: Critical 0 / Warning 0 / Info 0
PM級（指摘のみ）: X件
テスト: XXX passed / 0 failed
カバレッジ: XX%

Green State: G1 ✅ G2 ✅ G3 ✅ G4 ✅ G5 ✅
```

## 注意事項

- Phase 1 の4エージェントは必ず **並列** で起動すること（逐次実行は禁止）
- 修正後は必ずテスト + ruff で検証すること
- 仕様ズレが見つかった場合は S-1〜S-4（仕様同期ルール）に従い同時修正すること
- `.claude/rules/building-checklist.md` への参照を維持すること

## 監査レポート出力

成果物: `docs/artifacts/audit-reports/YYYY-MM-DD-iter{N}.md`

形式:
- 対象: `<target-file-or-dir>`
- フェーズ: Phase 1 ~ Phase 4
- Issue: Critical X件 / Warning X件 / Info X件
- Summary: [A/B/C/D評価]
