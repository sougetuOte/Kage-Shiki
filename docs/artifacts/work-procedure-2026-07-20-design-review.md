# 作業手順書: 設計書レビュー → Wave 3 準備（2026-07-20）

**作成者**: Fable 5（メインモデル — ユーザー指示 2026-07-20 のモデル運用方針に基づく）
**目的**: 復帰パッケージ指定の設計書レビュー ①〜⑥ を完了し、Phase 2b Wave 3
（HaikuEngine → AgenticSearch 統合）着手可否を判定する。
**停止点**: `/building` 移行 = Opus 切替（ユーザー注意喚起必須）。ここでユーザー判断待ちで終了する。

## 並列レーン構成

```
[開始]
  ├─ Lane A（Fable 直・メイン）: ①②③ 精読レビュー ── crux 判断は Fable の本領のため直接実施
  │     ① docs/specs/phase2b-autonomy/design.md（Section 3.5/4.1/4.2 Wave 2 注記）
  │     ② docs/specs/phase2b-autonomy/requirements.md
  │     ③ docs/tasks/phase2b-autonomy-tasks.md
  │
  ├─ Lane B（並列 subagent・読取専用）: ④⑤⑥ の要約 + Wave 3 影響事項の抽出
  │     ④ docs/artifacts/audit-reports/2026-04-29-wave2-final.md
  │     ⑤ docs/artifacts/retro-phase2b-wave2.md
  │     ⑥ docs/tasks/phase2a-pending-fixes.md
  │
  └─ Lane C（並列 subagent・読取専用・先取り）: Wave 3 対象コードの現状調査
        src/kage_shiki/ の LLM エンジン / 検索まわりの現行構造・拡張点・テスト状況
        （Wave 3 実装の前提となる事実収集。実装は行わない）

[バリア] Lane A/B/C 完了
  ↓
[統合]（Fable 直）: レビュー統合 → docs/artifacts/design-review-2026-07-20.md 作成
  - 指摘の重要度分類（Critical/Warning/Info）+ 権限等級（PG/SE/PM）
  - SE 級以下の文書修正は実施、PM 級（specs/tasks の意味変更）は指摘のみ
  - Wave 3 着手可否の判定
  ↓
[報告 + 停止]: ユーザーへ結果報告 + **Opus 切替の注意喚起**（/building はユーザー判断）
```

## 委譲判断の可視化

- Lane A を L1（Fable）直としたのは、設計レビューの crux 判断が今回のモデル運用方針の目的そのものであるため
- Lane B/C は事実収集主体のため並列 subagent へ委譲（grounding bolt-on 適用・読取専用）
- Lane B と C は互いに独立、Lane A とも独立 → 3 レーン同時進行。統合のみバリア

## 逸脱・例外の扱い

- PM 級指摘（仕様の意味を変える修正）はレポートに記載のみ、承認ゲートへ
- gabriel timeout 再校正等の既存 follow-up は本手順のスコープ外（レポート末尾で再掲のみ）
