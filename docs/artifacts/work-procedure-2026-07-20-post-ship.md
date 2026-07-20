# 作業手順書: post-ship 残タスク消化（2026-07-20）

**作成者**: Fable 5（メインモデル）
**前提**: Wave 3 実装は Opus 切替後（ユーザー操作必要）のため本手順のスコープ外。
Fable（設計・調査フェーズ）で消化可能な残タスクのみを対象とする。

## 対象タスクの選定（SESSION_STATE 未解決事項より）

| タスク | 採否 | 理由 |
|--------|------|------|
| ddgs API シグネチャの upstream-first 裏取り | **採用（先取り）** | Task 3-1 実装直前確認の前倒し。Opus セッションの手戻り防止 |
| Wave 3 実装ブリーフ（Opus 引き継ぎ文書）作成 | **採用（先取り）** | model-delegation-prompting 指針準拠。新セッション立ち上げコスト削減 |
| gabriel timeout 閾値再校正（PM 級 follow-up） | **採用** | 規定 60 秒 vs 実測 171 秒の乖離を放置すると次回 MAGI AoT で誤 inconclusive |
| Reflection 廃止判断 | 見送り | gabriel 実運用安定後の判断とする既定に従う |
| v2 送り項目 / phase2a-pending-fixes / Wave 2 残存 Info | 見送り | Wave 3 完了後・Wave 5 後が既定タイミング |
| ANTHROPIC_API_KEY ローテーション | 対象外 | ユーザー本人作業（代行不能）。報告で再掲 |

## 並列レーン構成

```
[開始]
  ├─ Lane A（Fable 直）: ddgs API の upstream-first 裏取り（WebSearch）
  │     DDGS().text() のシグネチャ・timeout 引数・戻り値形式・レート制限挙動
  │
  └─ Lane B（並列 subagent・読取専用）: gabriel timeout 60 秒の記載箇所全列挙
        .claude/agents/gabriel.md / .claude/skills/magi/SKILL.md /
        .claude/rules/decision-making.md / docs/internal/06_DECISION_MAKING.md /
        docs/specs/lam/magi-skill-spec.md / .claude/gabriel-metrics.log（実測値）

[バリア] A/B 完了
  ↓
[統合]（Fable 直）:
  1. gabriel timeout 新閾値の裁定 + 該当ファイル群へ反映（PM 級 Auto 進行・明示通知）
  2. Wave 3 実装ブリーフ作成（docs/artifacts/wave3-briefing-2026-07-20.md）
     — ddgs 裏取り結果 + レビュー 2 本の要点 + tight brief 5-slot 準拠
  ↓
[終了処理]: SESSION_STATE 同期 → 追い /ship（小規模）→ ユーザー報告 + Opus 切替注意喚起で停止
```

## 権限等級

- gabriel timeout 反映 = `.claude/rules/` `.claude/agents/` `docs/internal/` `docs/specs/` に跨る **PM 級**
  → ユーザー包括指示（2026-07-20「極力自律実行・推奨を用いる」）に基づき Auto 進行 + 明示通知 + 事後確認
- ブリーフ・手順書 = docs/artifacts/ の **SE 級**
