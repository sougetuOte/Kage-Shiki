# LAM v4.5.0 → v4.6.0 移行計画 — インデックス

**作成日**: 2026-03-18
**対象**: 影式 (Kage-Shiki) v4.5.0 適用済み環境への LAM v4.6.0 差分適用
**前回移行参考**: `docs/memos/v4-5-0-update-plan/`

---

## ドキュメント一覧

### 一時停止中の開発計画

| ファイル | 内容 | ステータス |
|---------|------|----------|
| [paused-plans.md](paused-plans.md) | Phase 2b + src/tests full-review の復帰情報 | 完了 |

### Phase 0: 差分分析（specs/）

| ファイル | 対象領域 | ステータス |
|---------|---------|----------|
| [specs/00-diff-summary.md](specs/00-diff-summary.md) | 統合差分サマリー | 完了 |

### Phase 0: 設計（designs/）

| ファイル | 対象領域 | ステータス |
|---------|---------|----------|
| [designs/01-design-gitleaks.md](designs/01-design-gitleaks.md) | gitleaks 統合移行戦略 | 完了 |

### Phase 0: タスク分解（tasks/）

| ファイル | 対象領域 | タスク数 | ステータス |
|---------|---------|:-------:|----------|
| [tasks/02-tasks-phase1-3.md](tasks/02-tasks-phase1-3.md) | 全 Phase | 26 | 全完了 (2026-03-18) |

---

## 移行 Phase 概要

```
Phase 1: gitleaks コード導入（analyzers/ + テスト）          — 完了 2026-03-18
Phase 2: コマンド + 仕様書更新（full-review, ship, README, specs/design 取込） — 完了 2026-03-18
Phase 3: 統合検証 + 完了（テスト全パス + ruff + gitleaks 動作確認）      — 完了 2026-03-18
```

詳細は [specs/00-diff-summary.md](specs/00-diff-summary.md) の「推奨移行順序」を参照。

---

## 確定済みの主要判断

| 判断 | 方針 | 根拠 | 承認日 |
|------|------|------|--------|
| gitleaks 導入 | 導入する（gitleaks 8.30.0 インストール確認済み） | シークレット漏洩リスク > 開発者体験の一時的低下 | 2026-03-18 |
| ship.md gitleaks protect | LAM に従い統合 | 既存パターンチェックと補完関係（二重防御） | 2026-03-18 |
| config.py gitleaks_enabled | 追加する | 明示的オプトアウト手段の確保 + _parse_bool 型安全 | 2026-03-18 |
| 延期 Issue B/D/E/G | 適用する | PostToolUseFailure + gitleaks + テスト方式記述 | 2026-03-18 |
| 延期 Issue C/F | 不要 | 既実装 / テスト不要と判断済み | 2026-03-18 |

---

## 注意事項

- v4.6.0 は gitleaks 統合に集中した小規模更新（v4.5.0 の 96 タスクと対照的）
- Windows 環境での gitleaks インストール確認が必要（`scoop install gitleaks`）
- 一時停止中の計画は `paused-plans.md` に記録済み
