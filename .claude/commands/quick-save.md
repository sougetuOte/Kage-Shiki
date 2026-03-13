# クイックセーブ

プロジェクトルートの `SESSION_STATE.md` への記録 + ループログ保存 + Daily 記録。
git commit は行わない（コミットは `/ship` を使用）。

配置先: `<project>/.claude/commands/quick-save.md`
呼び出し: Claude Code 内で `/quick-save`

## Step 1: SESSION_STATE.md を書き出す

以下の内容を **簡潔に** 記録（各項目は箇条書き数行で十分）:

### 完了タスク
- 今回のセッションで完了した作業を箇条書き

### 進行中タスク
- 作業途中のものとその現在の状態
- 次に何をすべきか

### 次のステップ
- 次セッションで最初にやるべきこと（優先順位付き）

### 変更ファイル一覧
- 今回変更したファイルのパス一覧

### 未解決の問題
- 残っている課題、確認事項（なければ「なし」）

### コンテキスト情報
- 現在のフェーズ (PLANNING / BUILDING / AUDITING)
- 現在のgitブランチ
- テスト結果（passed 数 / カバレッジ）
- 関連するSPEC/ADR/設計書ファイル名

## Step 2: ループログ保存

`.claude/logs/loop-*.txt` が存在する場合:
1. ログ内容を確認し、今回のセッションのループ実行概要を記録
2. SESSION_STATE.md の「コンテキスト情報」にループ実行回数を追記

存在しない場合はスキップ。

## Step 3: Daily 記録

`docs/daily/YYYY-MM-DD.md` に日次記録を追記（同日に複数回実行した場合は追記）:

```markdown
## YYYY-MM-DD

### セッション概要
- フェーズ: [PLANNING/BUILDING/AUDITING]
- 完了タスク: [箇条書き]

### KPI（参考）
- テスト数: N passed
- カバレッジ: N%
- lint: clean / N warnings
- Issue 修正数: N

### メモ
- [特記事項があれば]
```

## 完了報告

以下を表示:

```
--- quick-save 完了 ---
SESSION_STATE.md: 更新済み
Daily: docs/daily/YYYY-MM-DD.md

コミットが必要な場合は /ship を実行してください。

再開方法:
  claude -c  （直前セッション続行）
  claude     （新規セッション → /quick-load）
---
```
