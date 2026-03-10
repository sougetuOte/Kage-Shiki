# LAM 4.0.1 移行 — 統合差分サマリー

**作成日**: 2026-03-10
**対象**: LAM 4.0.1 (v4.0.0 "免疫系アーキテクチャ") → 影式 (Kage-Shiki) への適用

---

## 詳細差分ファイル一覧

| ファイル | 対象領域 |
|---------|---------|
| [00-diff-claude-md.md](00-diff-claude-md.md) | CLAUDE.md / CHEATSHEET.md |
| [00-diff-rules.md](00-diff-rules.md) | .claude/rules/ |
| [00-diff-commands-skills-agents.md](00-diff-commands-skills-agents.md) | .claude/commands/, skills/, agents/ |
| [00-diff-docs-internal.md](00-diff-docs-internal.md) | docs/internal/, docs/specs/ (LAM側) |
| [00-diff-claude-misc.md](00-diff-claude-misc.md) | settings.json, hooks/, states/, current-phase.md |
| [00-diff-root-files.md](00-diff-root-files.md) | CHANGELOG, README, LICENSE, 新規ルートファイル |

---

## v4.0.0 の 5 つの柱

| # | 柱 | 概要 | 影式への影響度 |
|---|---|------|-------------|
| 1 | **権限等級 (PG/SE/PM)** | 全変更を3段階にリスク分類。AUDITING での修正を部分許可 | **大** — 全ファイルに横断的影響 |
| 2 | **自動ループ統合** | Stop hook による `/full-review` の自動イテレーション | **大** — full-review.md の大幅拡張 |
| 3 | **TDD 内省パイプライン** | テスト失敗パターンの自動記録 → ルール候補生成 | **中** — 影式は手動ルール(R-1〜R-11)で運用中 |
| 4 | **ドキュメント自動追従** | PostToolUse hook + doc-sync-flag → `/ship` 連携 | **中** — ship.md の Doc Sync 変更 |
| 5 | **Green State 収束条件** | 5条件(テスト/lint/Issue/仕様差分/セキュリティ)の定義 | **中** — `/full-review` の完了判定基準 |

---

## 変更規模サマリー

### 新規追加が必要なファイル

| ファイル | 種別 | 優先度 |
|---------|------|-------|
| `.claude/rules/permission-levels.md` | ルール | **必須** — 柱1の基盤 |
| `.claude/rules/upstream-first.md` | ルール | 必須 |
| `.claude/rules/auto-generated/README.md` | ルール | 柱3導入時 |
| `.claude/rules/auto-generated/trust-model.md` | ルール | 柱3導入時 |
| `.claude/hooks/pre-tool-use.sh` | Hook | 柱1実装時 |
| `.claude/hooks/post-tool-use.sh` | Hook | 柱2,3,4実装時 |
| `.claude/hooks/lam-stop-hook.sh` | Hook | 柱2実装時 |
| `.claude/hooks/pre-compact.sh` | Hook | 推奨 |
| `.claude/settings.json` | 設定 | 柱1実装時 |
| `.claude/commands/pattern-review.md` | コマンド | 柱3導入時 |
| `.claude/skills/ui-design-guide/SKILL.md` | スキル | 任意（GUI設計時に有用） |
| `docs/specs/green-state-definition.md` | 仕様 | 柱5の定義 |
| `docs/specs/evaluation-kpi.md` | 仕様 | KPI計測用 |
| `docs/specs/loop-log-schema.md` | 仕様 | ループログ定義 |
| `docs/specs/doc-writer-spec.md` | 仕様 | 柱4の実装仕様 |
| `docs/specs/v4.0.0-immune-system-requirements.md` | 仕様 | 移行根拠文書 |
| `docs/specs/v4.0.0-immune-system-design.md` | 仕様 | Hook実装設計 |

### 更新が必要な既存ファイル

| ファイル | 主な変更内容 |
|---------|------------|
| `CLAUDE.md` | テンプレート汎用化部分の取り込み（影式固有は維持） |
| `CHEATSHEET.md` | 権限等級セクション追加、コマンド分類再編、AoT テーブル形式 |
| `.claude/rules/core-identity.md` | 権限等級セクション追加、Subagent委任判断の移動 |
| `.claude/rules/decision-making.md` | SSOT参照注記追加（軽微） |
| `.claude/rules/phase-rules.md` | **最大の変更** — TDD品質チェック統合、AUDITING修正ルール変更、TDD内省パイプライン |
| `.claude/rules/security-commands.md` | Layer 0/1/2 三層モデル追加 |
| `.claude/commands/full-review.md` | **最大の拡張** — 4エージェント、Green State、自動ループ、セキュリティ・仕様ドリフトチェック |
| `.claude/commands/auditing.md` | 権限等級修正ルール、コード明確性チェック |
| `.claude/commands/building.md` | TDD内省パイプライン連携（影式固有R-1〜R-6参照は維持） |
| `.claude/commands/ship.md` | doc-sync-flag 連携、Phase構成簡素化 |
| `.claude/commands/daily.md` | KPI集計セクション追加 |
| `.claude/commands/project-status.md` | KPIダッシュボード追加（Wave進捗は維持） |
| `.claude/commands/impact-analysis.md` | PG/SE/PM分類ステップ追加 |
| `.claude/commands/security-review.md` | 権限等級対応表、自動化ツール連携 |
| `docs/internal/00_PROJECT_STRUCTURE.md` | SSOT 3層アーキテクチャ、.claude/ 配下構造 |
| `docs/internal/02_DEVELOPMENT_FLOW.md` | TDD Introspection、権限等級修正制御 |
| `docs/internal/07_SECURITY_AND_AUTOMATION.md` | **大幅追加** — Section 5(Hooks), Section 6(Security Tools) |
| `docs/internal/99_reference_generic.md` | フェーズモードタグ（軽微） |
| 全agents/*.md | `# permission-level` コメント追加 |
| 全skills/SKILL.md | `version: 1.0.0` 追加 |

### 影式固有（保持すべきもの）

| ファイル/セクション | 内容 |
|-------------------|------|
| `CLAUDE.md` Project Overview | 技術スタック表（Python, tkinter, pystray, etc.） |
| `.claude/rules/building-checklist.md` | R-2〜R-11（Phase 1 Retro由来の教訓） |
| `.claude/rules/spec-sync.md` S-2 | Protocol外メソッドの明示 |
| `.claude/rules/audit-fix-policy.md` A-3 | 修正後の再検証手順 |
| `phase-rules.md` Phase完了判定 | L-4由来スモークテスト（デスクトップアプリ固有） |
| `security-commands.md` Python Allow | python, pytest, ruff, pip, pyenv |
| `.claude/commands/retro.md` | Wave/Phase振り返り（LAMテンプレートに無い） |
| `.claude/commands/wave-plan.md` | Wave計画策定（LAMテンプレートに無い） |
| `docs/internal/08_SESSION_MANAGEMENT.md` | セッション管理（影式独自） |
| `docs/internal/09_SUBAGENT_STRATEGY.md` | Subagent戦略（影式独自） |
| `03_QUALITY_STANDARDS.md` Section 6,7 | Python規約、不具合防止ルール |
| `02_DEVELOPMENT_FLOW.md` Wave実績 | Phase 1 Wave 1-8 実績 |
| `07_SECURITY_AND_AUTOMATION.md` Section 2 | pytest/ruff固有コマンド |

### 廃止候補

| ファイル | 理由 | 代替 |
|---------|------|------|
| `.claude/rules/audit-fix-policy.md` | PG/SE/PM で大部分カバー。A-3 のみ phase-rules.md に統合 | permission-levels.md + phase-rules.md |
| `.claude/rules/spec-sync.md` | S-1/S-3/S-4 は phase-rules.md に統合済み | phase-rules.md + S-2 を building-checklist.md へ |

---

## エージェントモデル変更

| エージェント | 現行 | LAM 4.0.1 | 判断 |
|-------------|------|-----------|------|
| quality-auditor | opus | sonnet | 要検討（影式はアーキテクチャ判断にOpus使用中） |
| test-runner | sonnet | haiku | 採用推奨（コスト削減、品質影響小） |

---

## 推奨移行順序

```
Phase 0: 準備
  ├─ 移行計画（design/tasks文書作成）
  └─ 影式作業状況の保全

Phase 1: 基盤（docs/internal/ + rules + CLAUDE.md）
  ├─ docs/internal/ のマージ（00, 02, 07, 99）
  ├─ permission-levels.md 導入 + ファイルパス分類を影式用にカスタマイズ
  ├─ core-identity.md, decision-making.md, security-commands.md 更新
  ├─ phase-rules.md 更新（影式固有ルール保持）
  ├─ upstream-first.md 導入
  ├─ CLAUDE.md, CHEATSHEET.md 更新
  └─ 影式固有ルールの再配置（building-checklist.md, spec-sync.md → 統合/移動）

Phase 2: コマンド / スキル / エージェント
  ├─ 全 agents に permission-level コメント追加
  ├─ 全 skills に version: 1.0.0 追加
  ├─ commands の差分適用（full-review, auditing, building, ship, daily 等）
  ├─ pattern-review.md 新規追加
  ├─ ui-design-guide スキル導入検討
  └─ docs/specs/ LAM仕様書の取り込み

Phase 3: Hooks + 自動化
  ├─ .claude/settings.json 導入
  ├─ hooks スクリプト作成（Windows対応要確認）
  ├─ auto-generated/ ディレクトリ準備
  ├─ Green State 定義の影式版策定
  └─ 統合テスト（/full-review 自動ループ動作確認）

Phase 4: 検証 + ドキュメント最終整備
  ├─ 全テスト実行 + ruff check
  ├─ 移行後の /full-review 実行
  └─ SESSION_STATE.md 更新
```

---

## Windows 環境での注意事項

LAM 4.0.1 の hooks は `.sh` (bash) スクリプトで提供されている。影式は Windows 11 環境で動作しているため:

- Git Bash / WSL2 経由での実行を前提とする
- Claude Code の hooks 機能が Windows でどのように動作するか upstream-first で確認が必要
- 代替として `.cmd` / `.ps1` スクリプトが必要になる可能性がある

---

## 次のステップ

1. 本サマリーに基づき `01-design-*.md` を作成（設計判断）
2. `02-tasks-*.md` を作成（タスク分解）
3. 移行作業の実施
4. 影式本来の作業（Phase 2a スモークテスト再検証）を再開
