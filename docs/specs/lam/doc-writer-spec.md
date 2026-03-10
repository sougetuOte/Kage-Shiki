# doc-writer エージェント詳細仕様（LAM v4.0.0）

## 概要

doc-writer エージェントのドキュメント自動追従モードの詳細仕様。
PostToolUse hook が生成する `doc-sync-flag` と連携し、
コード変更に伴うドキュメント更新を自動化する。

## doc-sync-flag 連携フロー

### 1. フラグ生成（PostToolUse hook）
コード変更を検出した PostToolUse hook が `.claude/doc-sync-flag` ファイルを生成する。

```json
{
  "changed_files": ["src/kage_shiki/core/engine.py", "src/kage_shiki/agent/client.py"],
  "change_type": "edit",
  "timestamp": "ISO8601"
}
```

### 2. フラグ読取（doc-writer）
`/ship` の Phase 2（Doc Sync）で doc-writer が `doc-sync-flag` を読み取り、
変更ファイルに対応するドキュメントを特定する。

### 3. ドキュメント更新
特定されたドキュメントを更新し、変更サマリーを報告する。

### 4. フラグ消費
処理完了後、`doc-sync-flag` を削除する。

## フォールバック（hooks 未導入時）

`doc-sync-flag` が存在しない場合は従来フロー:
- CHANGELOG.md, README.md, README_en.md, CHEATSHEET.md の固定チェック

## 参照

- `.claude/agents/doc-writer.md` — エージェント定義
- `.claude/commands/ship.md` — Phase 2: Doc Sync
