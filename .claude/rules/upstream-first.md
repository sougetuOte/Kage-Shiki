# Upstream First — プラットフォーム仕様優先原則

## 原則

Claude Code のプラットフォーム機能（hooks, settings, permissions, skills, sub-agents, MCP）に関する
実装・修正・トラブルシューティングでは、**必ず公式ドキュメントを事前確認**する。

「以前の記憶」や「推測」で実装を進めない。Claude Code は頻繁に更新されるため、
過去のセッションで正しかった情報が現在は古くなっている可能性がある。

## 確認先

| 機能 | 公式ドキュメント |
|------|----------------|
| Hooks | https://docs.anthropic.com/en/docs/claude-code/hooks |
| Settings | https://docs.anthropic.com/en/docs/claude-code/settings |
| Permissions | https://docs.anthropic.com/en/docs/claude-code/permissions |
| Skills | https://docs.anthropic.com/en/docs/claude-code/skills |
| Sub-agents | https://docs.anthropic.com/en/docs/claude-code/sub-agents |
| MCP | https://docs.anthropic.com/en/docs/claude-code/mcp |

## 確認手順

1. **context7 MCP** で最新ドキュメントを取得（利用可能な場合）
2. context7 が利用不可の場合、**WebFetch** で公式 URL を直接取得
3. 取得した仕様と既存実装の**差分を特定**
4. 差分があればユーザーに報告し、対応方針を確認
5. 承認後に実装を開始

## 注意事項

- `/full-review` 等の自動フロー内では WebFetch を使用しない（コンテキスト消費を避ける）
- Wave 開始前に一括ですり合わせることを推奨
- 公式ドキュメントに記載がない挙動を発見した場合、`docs/memos/` に記録する
