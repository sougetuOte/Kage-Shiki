# Living Architect 行動規範

## Active Retrieval（能動的検索原則）

1. **Context Swapping**: タスク開始時、関連ファイルを検索・ロードする
2. **Freshness Verification**: 重要判断前には再読込を行う
3. **Assumption Elimination**: 「覚えているはずだ」を仮定しない

## Subagent 委任判断

| 条件 | 判断 |
|:-----|:-----|
| 単一ファイル・小規模変更 | メインで直接実施 |
| 複数ファイル・並列可能 | Subagent に委任（lam-orchestrate） |
| 深い分析・判断が必要 | メイン（Opus）で直接実施 |
| 定型的な検査・実行 | Subagent に委任 |

## コンテキスト節約原則

1. 大量のファイルを先回りして読み込まない（必要になった時点で読む）
2. Subagent の出力は要約して取り込む（全文をメインに展開しない）
3. 長大な出力が予想される場合は Subagent に委任してサマリーだけ受け取る

## Context Compression

セッションが長くなった場合:
1. 決定事項と未解決タスクを `docs/tasks/` または `docs/memos/` に書き出す
2. ユーザーに「コンテキストをリセットします」と宣言
