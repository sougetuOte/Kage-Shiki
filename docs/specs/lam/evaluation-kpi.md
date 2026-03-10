# KPI 定義（LAM v4.0.0）

プロジェクトの健全性を定量的に評価するための 5 つの KPI。
`/daily` と `/project-status` で参照される。

## KPI 一覧

| ID | 名称 | 定義 | 目標値 | 計測方法 |
|----|------|------|--------|---------|
| K1 | タスク完了率 | 完了タスク数 / 全タスク数 | 100% | `/project-status` で自動集計 |
| K2 | 平均ループイテレーション | `/full-review` の平均イテレーション回数 | ≤ 3 | `.claude/logs/loop-*.json` から集計（hooks 導入後） |
| K3 | フック介入率 | PreToolUse hook の介入回数 / 全ツール呼び出し回数 | ≤ 5% | hooks ログから集計（hooks 導入後） |
| K4 | コンテキスト枯渇率 | auto-compact 発動回数 / 全セッション数 | ≤ 10% | セッションログから手動集計 |
| K5 | 同一Issue再発率 | `/full-review` で同一ファイル・同一種別の Issue が再発した割合 | 0% | 監査レポートの差分比較 |

## 計測開始条件

| KPI | 計測開始 | 備考 |
|-----|---------|------|
| K1 | 即時 | Phase 0 から計測可能 |
| K2 | Phase 3（hooks 導入後） | lam-loop-state.json が必要 |
| K3 | Phase 3（hooks 導入後） | PreToolUse hook が必要 |
| K4 | 即時 | セッション単位で手動記録 |
| K5 | 即時 | `/full-review` 実行ごとに比較 |

## 影式での現状（Phase 2 時点）

- **K1**: 計測可能（SESSION_STATE.md のタスク進捗から算出）
- **K2**: 計測不可（hooks 未導入）。「—」と表示
- **K3**: 計測不可（hooks 未導入）。「—」と表示
- **K4**: 手動記録（auto-compact 発動時に daily に記録）
- **K5**: 手動比較（前回の監査レポートと比較）
