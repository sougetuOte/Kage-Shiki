# LAM v4.4.1 → v4.5.0 移行計画 — インデックス

**作成日**: 2026-03-16
**対象**: 影式 (Kage-Shiki) v4.4.1 適用済み環境への LAM v4.5.0 差分適用
**前回移行参考**: `docs/memos/v4-4-1-update-plan/`

---

## ドキュメント一覧

### Phase 0: 差分分析（specs/）

| ファイル | 対象領域 | ステータス |
|---------|---------|----------|
| [specs/00-diff-summary.md](specs/00-diff-summary.md) | 統合差分サマリー | 完了 |
| [specs/00-diff-rules.md](specs/00-diff-rules.md) | .claude/rules/ 詳細差分 | 完了 |
| [specs/00-diff-commands-skills-agents.md](specs/00-diff-commands-skills-agents.md) | commands/, skills/, agents/ 詳細差分 | 完了 |
| [specs/00-diff-docs-internal.md](specs/00-diff-docs-internal.md) | docs/internal/, CLAUDE.md, CHEATSHEET.md 差分 | 完了 |
| [specs/00-diff-hooks-analyzers.md](specs/00-diff-hooks-analyzers.md) | hooks/, analyzers/, settings.json 差分 | 完了 |

### Phase 0: 設計（designs/）

| ファイル | 対象領域 | ステータス |
|---------|---------|----------|
| [designs/01-design-rules-docs.md](designs/01-design-rules-docs.md) | ルール + docs/internal/ + CLAUDE.md 移行戦略 | 完了 |
| [designs/01-design-commands-skills-agents.md](designs/01-design-commands-skills-agents.md) | コマンド/スキル/エージェント移行 | 完了 |
| [designs/01-design-hooks-analyzers.md](designs/01-design-hooks-analyzers.md) | Hooks + analyzers/ 導入戦略 | 完了 |

### Phase 0: タスク分解（tasks/）

| ファイル | 対象領域 | タスク数 | ステータス |
|---------|---------|:-------:|----------|
| [tasks/02-tasks-phase1.md](tasks/02-tasks-phase1.md) | ルール + docs/internal/ + CLAUDE.md | 28 | 完了 |
| [tasks/02-tasks-phase2.md](tasks/02-tasks-phase2.md) | コマンド / スキル / エージェント | 34 | 完了 |
| [tasks/02-tasks-phase3.md](tasks/02-tasks-phase3.md) | Hooks + analyzers/ | 21 | 完了 |
| [tasks/02-tasks-phase4.md](tasks/02-tasks-phase4.md) | 統合検証 + 完了 | 13 | 完了 |

---

## 移行 Phase 概要

```
Phase 0: 差分分析 + 設計 + タスク分解（本ディレクトリ）
Phase 1: ルール + docs/internal/ + CLAUDE.md + CHEATSHEET.md
Phase 2: コマンド / スキル / エージェント + specs/design 取込
Phase 3: Hooks + analyzers/ + settings.json + .gitignore
Phase 4: 統合検証 + 完了
```

詳細は [specs/00-diff-summary.md](specs/00-diff-summary.md) の「推奨移行順序」を参照。

---

## 確定済みの主要判断

| 判断 | 方針 | 根拠 | 承認日 |
|------|------|------|--------|
| analyzers/ 導入 | 導入する | Stage 体系は規模に関わらず有用 | 2026-03-16 |
| task-decomposer Haiku | LAM に従い変更 | 定型的タスク分解はコスト最適化で十分 | 2026-03-16 |
| requirement-analyst PM級 | LAM に従い変更 | 要件定義は仕様変更に直結 | 2026-03-16 |
| Context 閾値 | 影式 20% を維持 | 安全側運用の継続 | 2026-03-16 |
| 03_QS Python セクション | 影式保持 | Python プロジェクト固有のため | 2026-03-16 |
| docs/slides/ | スキップ | 影式に既存なし。将来作成予定 | 2026-03-16 |
| QUICKSTART/英語版 | スキップ | 個人プロジェクトのため不要 | 2026-03-16 |
| **R-5/R-6 衝突** | **影式を R-12/R-13 にリナンバ** | LAM 識別子と一致させる | 2026-03-16 |
| **quality-auditor** | **Sonnet に変更** | code-quality-guideline で品質担保 | 2026-03-16 |
| **lam-stop-hook** | **LAM 設計に移行（安全ネット）** | Stage 5 との二重判定解消 | 2026-03-16 |
| **design-architect** | **PM級を維持** | 設計判断の重要性。LAM v4.5.0 は SE だが影式は PM を継続 | 2026-03-16 |
| **SSOT 3層** | **LAM に追従** | CLAUDE.md はブートストラップ | 2026-03-16 |

## 注意事項

- 影式固有の保持項目は 10 件が差分分析で識別済み（specs/00-diff-summary.md Section 5）
- 各移行 Phase 完了時に影式固有保全チェックを実施すること
- analyzers/ のテストは影式既存テスト（830件）と共存する形で追加
