# 一時停止中の開発計画

**作成日**: 2026-03-18
**理由**: LAM v4.6.0 適用作業を優先するため一時停止
**復帰条件**: v4.6.0 移行完了（Phase 4 統合検証 GREEN STATE 達成後）

---

## 1. src/tests full-review（AUDITING）

**状態**: イテレーション 0 完了、未修正

### 残作業

- Critical 6件 + Warning 25件の修正
- Before=0 確認まで自動ループ
- PM 級 1件（trends_proposal Shotgun Surgery）→ Phase 2b で対応

### 復帰手順

1. v4.6.0 適用完了後に `/full-review src/kage_shiki/ tests/` を実行
2. 前回レポート参照: `docs/artifacts/audit-reports/2026-03-16-src-tests-iter0.md`
3. v4.6.0 で gitleaks が統合されるため、G5 チェックが強化された状態で再監査される

### 関連ファイル

- `docs/artifacts/audit-reports/2026-03-16-src-tests-iter0.md`（イテレーション 0 レポート）

---

## 2. Phase 2b — 影式自律性機能（PLANNING）

**状態**: 要件書承認済み、設計・タスク未着手

### 残作業

- 設計書作成（`docs/specs/phase2b-autonomy/` 配下）
- タスク分解
- 承認 → BUILDING 開始

### 復帰手順

1. `/planning` でフェーズ切替
2. `docs/specs/phase2b-autonomy/requirements.md` を再読
3. 設計書作成から再開

### 関連ファイル

- `docs/specs/phase2b-autonomy/requirements.md`（承認済み要件書）
- `.claude/states/phase-2-autonomy.json`（Phase 2b PLANNING 状態）
- `docs/memos/middle-draft/02-personality-system.md`（欲求設計）
- `docs/memos/middle-draft/05-agentic-search.md`（AgenticSearch）
- `docs/memos/middle-draft/04-unified-design.md`（統合設計）

---

## 3. PM 級据え置き事項

| 事項 | 対応時期 | 参照 |
|------|---------|------|
| trends_proposal.py Shotgun Surgery → TriggerType Enum 化 | Phase 2b | audit-reports/2026-03-16-src-tests-iter0.md |
| StatusLine vs PreCompact のコンテキスト残量不一致 | 調査未了 | SESSION_STATE.md |
