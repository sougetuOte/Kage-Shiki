# 影式 (Kage-Shiki) 作業状況保全ファイル

**作成日**: 2026-03-10
**目的**: LAM 4.0.1 移行作業中に影式本来の作業状況を失わないための記録

---

## 現在のフェーズ

**Phase 2a BUILDING — スモークテスト再検証待ち**

## 直近の完了作業 (2026-03-08)

- スモークテスト修正12件のコミット + push（3コミット、HEAD: fd28418）
- 再検証チェックリスト作成（`docs/testing/retest-smoketest-2026-03-08.md`、20項目）
- CHANGELOG 更新

## 再開時のタスク

1. **スモークテスト再検証**: `docs/testing/retest-smoketest-2026-03-08.md` に従い実施
   - 推奨順序: Part A(ウィザード) → B(メインウィンドウ) → C(トレイ) → E(FTS5) → D(シャットダウン+再起動)
2. **Phase 2a 完了判定**: 全20項目パス後に宣言
3. **再検証チェックリストのコミット**

## テスト状況

- テスト数: 722 passed
- カバレッジ: 92%
- ruff: clean

## 据置Issue（Phase 2b 対応）

| Issue ID | 内容 |
|----------|------|
| SRC-CRIT-001 | Phase 2b |
| SRC-CRIT-002 | Phase 2b |
| SRC-WARN-002 | Phase 2b |
| SRC-WARN-003 | Phase 2b |
| SRC-WARN-005 | Phase 2b |
| SRC-WARN-006 | Phase 2b |
| TEST-WARN-4 | Phase 2b |
| TEST-WARN-5 | Phase 2b |

## Phase 2b 候補機能

- F-1: 呼び名動的変化
- F-2: ウィザード安全性
- F-3: キーワード数
- F-4: 候補選択UI

## 未コミットファイル (移行前時点)

- `docs/testing/retest-smoketest-2026-03-08.md`: 再検証チェックリスト（新規）

## ブランチ

- master

## 参照ファイル

- `SESSION_STATE.md`: セッション状態（次回 `/quick-load` で読み込まれる）
- `docs/testing/retest-smoketest-2026-03-08.md`: 再検証チェックリスト
- `docs/memos/v4-update-plan/`: LAM 4.0.1 移行計画ディレクトリ

---

## LAM 4.0.1 移行完了後の手順

1. `SESSION_STATE.md` を最新状態に更新（LAM移行完了を記載）
2. 本ファイルの「再開時のタスク」に従い影式作業を再開
3. スモークテスト再検証を実施
