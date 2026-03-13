---
description: "TDD内省パターンの審査・承認"
---

# permission-level: PM
# ルール候補の承認・却下は PM 級の判断

# Pattern Review（TDD 内省パターン審査）

TDD 内省パイプラインが生成したルール候補を審査し、承認・却下・統合を行う。

## 実行ステップ

### Step 1: パターンログ確認

`.claude/tdd-patterns.log` を読み込み、記録されたパターンを一覧表示する。

```
--- Pattern Review: ログ確認 ---
記録パターン: X件
候補（2回以上）: X件
```

### Step 2: ルール候補の確認

`.claude/rules/auto-generated/draft-*.md` を読み込み、候補を一覧表示する。

```
| # | ファイル | 観測回数 | ステータス | 概要 |
|---|---------|---------|-----------|------|
| 1 | draft-001.md | 3 | draft | [概要] |
```

### Step 3: 審査（PM級判断）

各候補について以下を判断し、ユーザーに提示する:

1. **承認**: `draft-NNN.md` → `rule-NNN.md` にリネーム、ステータスを `approved` に変更
2. **却下**: ステータスを `retired` に変更、理由を記録
3. **統合**: 他の候補とマージし、新しい `draft-NNN.md` を生成
4. **保留**: 観測回数が不足、追加データ待ち

### Step 4: ユーザー確認

```
--- Pattern Review 結果 ---
承認: X件
却下: X件
統合: X件
保留: X件

この判断で進めますか？
```

## 参照

- `.claude/rules/auto-generated/README.md`: ライフサイクル定義
- `.claude/rules/auto-generated/trust-model.md`: 信頼度モデル
- `.claude/rules/phase-rules.md`: TDD 内省パイプライン v2
