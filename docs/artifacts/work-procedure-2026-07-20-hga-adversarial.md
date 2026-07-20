# 作業手順書: Wave 3 HGA 敵対的レビュー（2026-07-20）

**作成者**: Fable 5（メインモデル常駐 = HGA 召喚をメインセッションで充足。ユーザー指示 2026-07-20）
**目的**: Wave 3（HaikuEngine → AgenticSearch 統合）の設計を敵対的に攻撃し、
「壊れるケース・最悪ケース」を網羅列挙する。結果に基づき修正を実施する。
**召喚ゲート根拠**: 新規ドメイン統合（既定で召喚）。`hga-summoning.md` §loose brief の唯一例外
（敵対 coverage-first レビュー）に該当 — 重要度・確信度でフィルタせず全指摘を挙げる。

## 並列レーン構成

```
[開始]
  ├─ Lane A（Fable 直・敵対分析）: Wave 3 設計（design.md Rev.2 §5/§6/§8、Task 3-1/3-2）への攻撃
  │     攻撃面: 状態機械の障害復旧 / スレッド・ブロッキング / 無限増殖・コスト暴走 /
  │             Web 由来プロンプトインジェクション / LLM 出力パース / UX 価値未達 / テスト脆弱性
  │
  └─ Lane B（並列 subagent・読取専用）: Wave 2 実装コードの事実検証
        desire_worker.py / agent_core.py / db.py / main.py に対する grounding
        （W-4 の実態確認を含む。攻撃仮説を file:line で確定/棄却する材料収集）

[バリア] Lane A/B 完了
  ↓
[統合]（Fable 直）: 検証済み findings を重要度分類 → docs/artifacts/hga-adversarial-wave3-2026-07-20.md
  ↓
[修正]: 推奨案で design.md / tasks.md へ反映（PM 級 Auto 進行 — ユーザー包括指示 2026-07-20・事後確認前提）
  ↓
[記録 + 報告]: hga-summon-log.md に #K2 追記 + SESSION_STATE 同期 + ユーザー報告
```

## 委譲判断の可視化

- 敵対分析の本体は Fable 直（HGA の本領・loose brief 例外適用）
- コード事実検証は subagent へ委譲（grounding bolt-on 適用・読取専用）

## 修正の権限等級

- specs/tasks への修正 = PM 級 → ユーザー包括指示に基づき推奨案で Auto 進行し、明示通知 + 事後確認
- 仕様の意味を変えない artifacts への記録 = SE 級
