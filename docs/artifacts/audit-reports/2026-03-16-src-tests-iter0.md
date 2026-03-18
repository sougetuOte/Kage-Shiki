# 監査レポート: src/kage_shiki/ + tests/

**日付**: 2026-03-16
**イテレーション**: 0（初回スキャン）
**方針**: Critical + 重要 Warning のみ修正（次セッションで /full-review 再実行）

## サマリー

Critical: 6件 / Warning: 25件 / Info: 25件
PG: 9件 / SE: 42件 / PM: 1件
総合評価: B

## Critical（6件、全て SE）

1. `db.py:200` — `_retry_on_lock` ループ後の暗黙 None 返却リスク
2. `persona_system.py:417,473` — ファイル読み込み失敗時エラーハンドリング欠如
3. `shutdown_handler.py:34` — モジュールレベル `_shutdown_done` がテスト間共有
4. `test_agent_core.py:582` — ポジショナル引数検証が位置依存
5. `test_truncation.py:182` — EdgeCases が isinstance のみで内容未検証
6. `test_e2e.py:129` — テスト重複（単体と統合で同一検証）

## PM 級（1件、Phase 2b で対応）

- `trends_proposal.py:81` — 3辞書の Shotgun Surgery → TriggerType Enum 統合提案

## セキュリティ High（2件、SE）

- `main.py:440` — subprocess.Popen noqa コメント不足
- `db.py:133` — check_same_thread=False 設計意図ドキュメント不足

## Warning 主要（抜粋）

- `main.py:256` — main() 220行超過（Long Function）
- `prompt_builder.py:262` — build_with_truncation() 130行超過
- `human_block_updater.py:80` — Deep Nesting 4階層
- `wizard_gui.py:308` — バックグラウンドスレッドエラー処理不十分
- `db.py:298` — FTS5 クエリ特殊文字エスケープ不完全
- `llm_client.py:183` — AuthenticationError 内部情報伝播リスク
- tests/ — main.py テスト不在、wizard_gui /tmp/test ハードコード、テストファイル肥大化

## 次セッションでの対応

1. /full-review src/kage_shiki/ tests/ を再実行
2. Critical 6件 + 重要 Warning を修正
3. Before=0 まで自動ループ
4. PM 級（trends_proposal Enum 化）は Phase 2b で対応
