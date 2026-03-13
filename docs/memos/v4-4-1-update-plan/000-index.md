# LAM v4.0.1 → v4.4.1 移行計画 — インデックス

**作成日**: 2026-03-13
**対象**: 影式 (Kage-Shiki) v4.0.1 適用済み環境への LAM v4.4.1 差分適用
**前回移行参考**: `docs/memos/v4-update-plan/` (v3.x → v4.0.1)

---

## ドキュメント一覧

### Phase 0: 差分分析（specs/）

| ファイル | 対象領域 | ステータス |
|---------|---------|----------|
| [specs/00-diff-summary.md](specs/00-diff-summary.md) | 統合差分サマリー | 完了 |
| [specs/00-diff-hooks-settings.md](specs/00-diff-hooks-settings.md) | hooks/, settings.json 詳細差分 | 完了 |
| [specs/00-diff-rules.md](specs/00-diff-rules.md) | .claude/rules/ 詳細差分 | 完了 |
| [specs/00-diff-commands-skills-agents.md](specs/00-diff-commands-skills-agents.md) | commands/, skills/, agents/ 詳細差分 | 完了 |
| [specs/00-diff-docs.md](specs/00-diff-docs.md) | docs/internal/, CLAUDE.md, CHEATSHEET.md 差分 | 完了 |
| [specs/00-diff-new-directories.md](specs/00-diff-new-directories.md) | 新規ディレクトリ, ADR, .gitignore | 完了 |

### Phase 0: 設計（designs/）

| ファイル | 対象領域 | ステータス |
|---------|---------|----------|
| [designs/01-design-hooks-settings.md](designs/01-design-hooks-settings.md) | Hooks + Settings 移行戦略 | Draft |
| [designs/01-design-commands-skills-agents.md](designs/01-design-commands-skills-agents.md) | コマンド/スキル/エージェント移行 | Draft |
| [designs/01-design-rules-docs.md](designs/01-design-rules-docs.md) | Rules + docs/internal/ + CLAUDE.md 移行 | Draft |
| [designs/01-design-new-directories.md](designs/01-design-new-directories.md) | 新規ディレクトリ構造・構成変更 | Draft |

### Phase 0: タスク分解（tasks/）

| ファイル | 対象領域 | タスク数 | ステータス |
|---------|---------|:-------:|----------|
| [tasks/02-tasks-phase1.md](tasks/02-tasks-phase1.md) | セキュリティ修正 + settings.json | 4 | Draft |
| [tasks/02-tasks-phase2.md](tasks/02-tasks-phase2.md) | ルール + docs/internal/ + CLAUDE.md | 20 | Draft |
| [tasks/02-tasks-phase3.md](tasks/02-tasks-phase3.md) | コマンド / スキル / エージェント | 18 | Draft |
| [tasks/02-tasks-phase4.md](tasks/02-tasks-phase4.md) | 新ディレクトリ + Hooks | 15 | Draft |
| [tasks/02-tasks-phase5.md](tasks/02-tasks-phase5.md) | 統合検証 + 完了 | 5 | Draft |

---

## 移行 Phase 概要

```
Phase 0: 差分分析 + 設計 + タスク分解（本ディレクトリ）
Phase 1: セキュリティ修正 + settings.json
Phase 2: ルール + docs/internal/ + CLAUDE.md
Phase 3: コマンド / スキル / エージェント
Phase 4: 新ディレクトリ + Hooks
Phase 5: 統合検証 + 完了
```

詳細は [specs/00-diff-summary.md](specs/00-diff-summary.md) の「推奨移行順序」を参照。

---

## 確定済みの主要判断

| 判断 | 方針 | 設計ファイル |
|------|------|------------|
| ADR 番号衝突 | LAM ADR を 0002〜0005 に振り直し | designs/01-design-new-directories.md |
| docs/artifacts/ 導入 | 新規のみ、既存 docs/memos/ は維持 | designs/01-design-new-directories.md |
| agent-memory/ | ディレクトリ延期、Memory Policy のみ更新 | designs/01-design-new-directories.md |
| QUICKSTART.md | スキップ（個人プロジェクトのため不要） | specs/00-diff-summary.md |
| docs/slides/ | スキップ（必要時に作成） | specs/00-diff-summary.md |
| ultimate-think 廃止 | 削除、lam-orchestrate に統合 | designs/01-design-commands-skills-agents.md |

## 注意事項

- ルート直下の `00-diff-summary.md`, `00-diff-hooks-settings.md` は正本へのリダイレクトスタブ（正本は `specs/`）
- 影式固有の保持項目は全 25 件が差分分析・設計で識別済み（100% カバレッジ）
- 各移行 Phase 完了時に影式固有保全チェックを `/full-review` で実施すること
