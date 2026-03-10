# ループログスキーマ定義（LAM v4.0.0）

## 概要

`/full-review` の自動ループ実行ログのスキーマ定義。
ループの実行履歴を記録し、KPI 計測の基礎データとする。

## lam-loop-state.json

実行中のループ状態を管理する一時ファイル。

```json
{
  "iteration": 1,
  "max_iterations": 5,
  "started_at": "2026-03-10T10:00:00Z",
  "green_state": {
    "G1_tests": false,
    "G2_lint": false,
    "G3_issues": false,
    "G4_spec_sync": false,
    "G5_security": false
  },
  "issues": {
    "total": 0,
    "fixed": 0,
    "remaining": 0,
    "pm_level": 0
  },
  "fullscan_pending": false
}
```

## ループログ（.claude/logs/loop-*.json）

各ループ完了時に記録する実行ログ。

```json
{
  "id": "loop-YYYYMMDD-HHMMSS",
  "command": "/full-review",
  "iterations": 2,
  "started_at": "ISO8601",
  "completed_at": "ISO8601",
  "result": "green_state_achieved",
  "green_state_history": [
    { "iteration": 1, "G1": true, "G2": true, "G3": false, "G4": true, "G5": true },
    { "iteration": 2, "G1": true, "G2": true, "G3": true, "G4": true, "G5": true }
  ],
  "issues_fixed": 3,
  "issues_remaining": 0,
  "issues_pm_level": 1
}
```

## 参照

- `evaluation-kpi.md` — K2（平均ループイテレーション）の計測元
- `.claude/skills/lam-orchestrate/SKILL.md` — ループ統合セクション
