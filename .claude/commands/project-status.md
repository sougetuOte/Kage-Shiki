---
description: "プロジェクトの進捗状況を表示"
---

# 進捗状況表示

## 実行ステップ

1. `.claude/states/` 内の状態ファイルを検索
2. 各機能の状態を読み込み
3. タスク定義ファイル（`docs/specs/*/tasks.md` 等）があれば Wave 進捗を集計
4. 以下の形式で表示

## 出力形式

```
# プロジェクト状態

## 現在: [subPhase]

## 機能: [feature-name]

| サブフェーズ | 状態 | 承認 |
|-------------|------|------|
| 要件定義 | [アイコン] | [日時 or -] |
| 設計 | [アイコン] | [日時 or -] |
| タスク分解 | [アイコン] | [日時 or -] |
| 実装 | [アイコン] | [日時 or -] |

次のアクション: [推奨アクション]

## Wave 進捗（タスク定義ファイルがある場合）

| Wave | タスク | 状態 | ステータス |
|:----:|:-------|:-----|:----------|
| 1 | T-01, T-02 | 完了 | approved |
| 2 | T-03, T-04 | 完了 | approved |
| N | T-XX | 進行中 | warning |

全体: XX/YY タスク完了
```

## アイコン凡例

| 状態 | アイコン |
|------|---------|
| approved | ✅ |
| in_progress | 🔄 |
| pending | ⏳ |

## 状態ファイルがない場合

```
# プロジェクト状態

状態ファイルがありません。

/planning で機能の検討を開始してください。
```

## KPI ダッシュボード（v4.0.0）

KPI 定義: `docs/specs/lam/evaluation-kpi.md`

```
## KPI ダッシュボード

| KPI | 現在値 | 目標 | 状態 |
|-----|--------|------|------|
| K1: タスク完了率 | [値]% | 100% | [approved/warning/blocked] |
| K2: 平均ループイテレーション | — | ≤3 | [approved/warning/blocked] |
| K3: フック介入率 | — | ≤5% | [approved/warning/blocked] |
| K4: コンテキスト枯渇率 | [値]% | ≤10% | [approved/warning/blocked] |
| K5: 同一Issue再発率 | [値]% | 0% | [approved/warning/blocked] |
```

KPI の計算:
- **K1**: 完了タスク数 / 全タスク数
- **K2**: hooks 導入後に `/full-review` の平均ループ回数を計測
- **K3**: hooks 導入後に PreToolUse hook の介入回数 / 全ツール呼び出し回数を計測
- **K4**: auto-compact 発動回数 / 全セッション数
- **K5**: `/full-review` で同一ファイル・同一種別の Issue が再発した割合

## 複数機能がある場合

各機能ごとに表を表示する。
