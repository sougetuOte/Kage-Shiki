# LAM v4.0.1 → v4.4.1 移行 — 統合差分サマリー

**作成日**: 2026-03-13
**対象**: 影式 (Kage-Shiki) v4.0.1 適用済み環境への LAM v4.4.1 差分適用
**前回移行参考**: `docs/memos/v4-update-plan/` (v3.x → v4.0.1)

---

## バージョン間の変更概要

v4.0.1 → v4.4.1 は以下の 6 リリースを含む:

| バージョン | リリース日 | 主要テーマ |
|-----------|-----------|-----------|
| v4.1.0 | 2026-03-10 | hooks Python 移行、/retro・/wave-plan 新設 |
| v4.2.0 | 2026-03-12 | 3層メモリアーキテクチャ、docs/artifacts/ 分離 |
| v4.3.0 | 2026-03-12 | PM級ループ制御、セキュリティ強化 |
| v4.3.1 | 2026-03-12 | find コマンド deny バイパス修正 |
| v4.4.0 | 2026-03-13 | TDD 内省 v2（JUnit XML）、廃止コマンド整理 |
| v4.4.1 | 2026-03-13 | hooks 品質改善、テスト強化、リリースオペ汎用化 |

---

## 変更規模サマリー

### 1. 新規ディレクトリ・構造の追加

| ディレクトリ | 導入バージョン | 概要 | 影式での状態 |
|-------------|--------------|------|-------------|
| `docs/artifacts/` | v4.2.0 | コマンド/スキル生成物の保存先 | **未作成** |
| `docs/artifacts/knowledge/` | v4.2.0 | `/retro` で蓄積する構造化知見 | **未作成** |
| `docs/artifacts/audit-reports/` | v4.2.0 | 監査レポート永続化 | **未作成** |
| `docs/artifacts/tdd-patterns/` | v4.2.0 | TDD パターン詳細記録 | **未作成** |
| `.claude/agent-memory/` | v4.2.0 | Subagent 永続記憶 | **未作成** |
| `.claude/hooks/tests/` | v4.1.0 | hook ユニットテスト | **未作成** |

### 2. 新規ファイルの追加

| ファイル | 導入バージョン | 概要 | 影式での状態 |
|---------|--------------|------|-------------|
| `.claude/rules/test-result-output.md` | v4.4.0 | JUnit XML 出力必須ルール | **未作成** |
| `.claude/skills/ui-design-guide/SKILL.md` | v4.0.0 | UI/UX 設計チェックリスト | **未作成** |
| `docs/specs/tdd-introspection-v2.md` | v4.4.0 | TDD 内省 v2 仕様書 | **未作成** |
| `docs/specs/release-ops-revision.md` | v4.4.1 | リリースオペ改訂仕様 | **未作成** |
| `QUICKSTART.md` / `QUICKSTART_en.md` | v4.0.0 | 初心者向け導入ガイド | **未作成**（影式に必要か要判断） |

### 3. 廃止されたコマンド/スキル（v4.4.0 で削除）

| ファイル | 廃止理由 | 影式での状態 |
|---------|---------|-------------|
| `.claude/commands/daily.md` | `/quick-save` の Daily 記録に統合 | **存在**（削除対象） |
| `.claude/commands/focus.md` | 使用頻度低 | **存在**（削除対象） |
| `.claude/commands/full-load.md` | `/quick-load` に統合 | **存在**（削除対象） |
| `.claude/commands/full-save.md` | `/ship` + `/quick-save` に統合 | **存在**（削除対象） |
| `.claude/commands/adr-create.md` | adr-template スキルに統合 | **存在**（削除対象） |
| `.claude/commands/impact-analysis.md` | 使用頻度低 | **存在**（削除対象） |
| `.claude/commands/security-review.md` | `/full-review` に統合 | **存在**（削除対象） |
| `.claude/skills/ultimate-think/` | 使用頻度低 | **存在**（削除対象） |

### 4. 更新が必要な既存ファイル

#### Rules（高影響）

| ファイル | 主な変更 | 影響度 |
|---------|---------|-------|
| `core-identity.md` | Subagent 委任判断セクション削除、Context Compression の出力先変更（`docs/artifacts/`） | 中 |
| `phase-rules.md` | TDD 内省パイプライン v2 への更新（JUnit XML ベース）、PLANNING 許可に `docs/artifacts/` 追加 | 大 |
| `permission-levels.md` | 影式固有パス (`pyproject.toml`, `src/kage_shiki/`, `config/`) の削除（汎用化）、`src/` パスの汎用化、`docs/internal/*.md` PM パス追加 | 中 |
| `security-commands.md` | `find` → ask 移動、Layer 数 3→2 に変更、`mv` deny 化、Allow List から `find` 削除、`rm`/`chmod`/`chown` deny エスカレーション | 中 |
| `upstream-first.md` | URL 変更（`docs.anthropic.com` → `code.claude.com`）、WebFetch 注意事項追加 | 小 |
| `auto-generated/README.md` | TDD 内省 v2 対応、閾値 3→2 に変更 | 小 |
| `auto-generated/trust-model.md` | JUnit XML ベースへの全面改訂、閾値 3→2、`/retro` 統合 | 大 |

#### Commands（高影響）

| ファイル | 主な変更 | 影響度 |
|---------|---------|-------|
| `quick-save.md` | full-save 機能を吸収（Daily 記録 + ループログ保存）、git 操作なし | 大 |
| `quick-load.md` | 関連ドキュメント特定 + 復帰サマリー機能追加 | 中 |
| `full-review.md` | jq → Python ワンライナー、PM級ループ制御 (pm_pending) | 中 |
| `ship.md` | Doc Sync 連携強化 | 小 |
| `retro.md` | Step 2.5 TDD パターン分析追加、Step 4 Knowledge Layer 蓄積 | 大 |
| `project-status.md` | Wave 進捗 + KPI 統合 | 小 |
| `auditing.md` | 微調整 | 小 |
| `building.md` | TDD 内省 v2 連携 | 小 |
| `planning.md` | 微調整 | 小 |
| `wave-plan.md` | 微調整 | 小 |
| `pattern-review.md` | 微調整 | 小 |

#### Agents

| ファイル | 主な変更 | 影響度 |
|---------|---------|-------|
| 全 8 エージェント | `memory: project` 削除（v4.3.0）、出力先 `docs/memos/` → `docs/artifacts/` | 中 |
| `quality-auditor.md` | model: opus → sonnet に変更 | 中 |
| `test-runner.md` | model: sonnet → haiku に変更 | 小 |
| `code-reviewer.md` | agent-memory 対応 | 小 |

#### Skills

| ファイル | 主な変更 | 影響度 |
|---------|---------|-------|
| `lam-orchestrate/SKILL.md` | pm_pending フロー、出力先変更 | 中 |
| `adr-template/SKILL.md` | 微調整 | 小 |
| `spec-template/SKILL.md` | 微調整 | 小 |
| `skill-creator/SKILL.md` | 微調整 | 小 |

#### CLAUDE.md / CHEATSHEET.md

| ファイル | 主な変更 | 影響度 |
|---------|---------|-------|
| `CLAUDE.md` | Memory Policy 3層化、セーブ/ロード体系変更（2コマンド化）、References 簡素化 | 大 |
| `CHEATSHEET.md` | Rules に test-result-output 追加、コマンド削減反映、Memory 列更新、docs/artifacts/ 追加 | 大 |

#### docs/internal/

| ファイル | 主な変更 | 影響度 |
|---------|---------|-------|
| `00_PROJECT_STRUCTURE.md` | `docs/artifacts/` + `.claude/agent-memory/` 構造追加 | 中 |
| `02_DEVELOPMENT_FLOW.md` | TDD 内省 v2、廃止コマンド反映 | 中 |
| `04_RELEASE_OPS.md` | P1/P2/P3 優先度体系導入（汎用化） | 中 |
| `05_MCP_INTEGRATION.md` | Memory Policy 3層化対応 | 中 |
| `07_SECURITY_AND_AUTOMATION.md` | find deny パターン追加、Allow List 更新 | 中 |

#### settings.json

| 変更項目 | 現状(影式) | v4.4.1 | 対応 |
|---------|-----------|--------|------|
| `find` コマンド | allow | ask（破壊パターンは deny） | **要更新** — セキュリティ修正 |
| `python` vs `python3` | `python` | `python3` | **影式維持**: Windows は `python` |
| `Bash(python *)` | なし | ask | **要追加** |
| `Bash(git status *)` | allow | なし | 影式で維持して問題なし |
| `Bash(pip show *)` | allow | なし | 影式で維持して問題なし |
| find 破壊パターン | なし | deny に 4 パターン | **要追加** — セキュリティ修正 |

#### Hooks

| ファイル | 主な変更 | 影響度 |
|---------|---------|-------|
| `hook_utils.py` → `_hook_utils.py` | 命名変更、`now_utc_iso8601()` 集約、例外キャッチ具体化、LAM_PROJECT_ROOT 検証 | 大 |
| `pre-tool-use.py` | TSV ログのエスケープ修正、応答形式変更（`hookSpecificOutput` + `permissionDecision`） | 中 |
| `post-tool-use.py` | JUnit XML 読取対応、`_handle_loop_log` バグ修正、go test 正規表現修正 | 大 |
| `lam-stop-hook.py` | convergence_reason 導入、pip-audit 誤検出修正、symlink スキップ、STEP 統一 | 大 |
| `pre-compact.py` | 変更なしまたは軽微 | 小 |
| `tests/` (6ファイル) | hook テストスイート（conftest + 5 テストファイル、計53テスト） | **新規** |

### 5. docs/specs/ の変更

| ファイル | 状態 | 概要 |
|---------|------|------|
| `tdd-introspection-v2.md` | v4.4.0 新規 | TDD 内省 v2 仕様書 |
| `release-ops-revision.md` | v4.4.1 新規 | リリースオペ改訂 |
| `hooks-python-migration/` | v4.1.0 新規 | hooks Python 移行 3ドキュメント |
| `v4.0.0-immune-system-*.md` | 既存（v4.0.1で導入済み） | 更新箇所あり（閾値 3→2 等） |
| `green-state-definition.md` | 既存（v4.0.1で導入済み） | 微調整 |
| `evaluation-kpi.md` | 既存（v4.0.1で導入済み） | 微調整 |
| `loop-log-schema.md` | 既存（v4.0.1で導入済み） | convergence_reason enum 追加 |
| `doc-writer-spec.md` | 既存（v4.0.1で導入済み） | 微調整 |
| `lam-orchestrate-design.md` | 既存 | quality-auditor 追加、memory コメント更新 |
| `ui-lam-slides.md` | 既存 | 現行実装に合わせて全面改訂 |

---

## 影式固有の考慮事項

### 保持すべきもの（前回移行で確立）

| 項目 | 理由 |
|------|------|
| `CLAUDE.md` Project Overview | 影式固有の技術スタック（Python, tkinter, pystray） |
| `.claude/rules/building-checklist.md` | Phase 1 Retro 由来 R-2〜R-11, S-2（LAM テンプレートに無い） |
| `phase-rules.md` Phase 完了判定 | L-4 スモークテスト（デスクトップアプリ固有） |
| `permission-levels.md` 影式パス | `pyproject.toml`, `src/kage_shiki/`, `config/` のパス分類 |
| `settings.json` `python` | Windows 環境では `python3` ではなく `python` |
| `docs/internal/08_SESSION_MANAGEMENT.md` | 影式独自 |
| `docs/internal/09_SUBAGENT_STRATEGY.md` | 影式独自 |
| `03_QUALITY_STANDARDS.md` Section 6,7 | Python 規約、不具合防止ルール |
| `.claude/hooks/notify-sound.py` | 影式固有フック |

### 保全検証ノート

移行作業の各 Phase 完了時に、上記 9 項目が意図せず変更・削除されていないことを確認する。
具体的には `/full-review` の Phase 1（#3 quality-auditor）で影式固有保全チェックを含めること。

### 設計済みの判断項目

| 項目 | 判断ポイント |
|------|------------|
| コマンド廃止（7件）+ スキル廃止（1件: ultimate-think） | コマンド7件は全削除確定（各機能は残存コマンドに吸収済み）。ultimate-think は lam-orchestrate に統合 |
| JUnit XML テスト出力 | 影式の pytest に `--junitxml` 追加が必要 |
| `QUICKSTART.md` | **スキップ**: 個人プロジェクトのため不要 |
| `docs/slides/` 更新 | **スキップ**: 必要になった時点で作成 |

---

## 衝突解決ポリシー（前回踏襲）

1. **影式の実運用経験が優先**: building-checklist.md の R-2〜R-11 等
2. **LAM の構造改善は受け入れ**: コマンド整理、3層メモリ、セキュリティ修正等
3. **矛盾は両立を試みる**: まず共存させ、問題が出たら調整

### 確定済みの衝突解決

| 衝突 | 解決方針 | 詳細 |
|------|---------|------|
| ADR 番号衝突（影式 0001 vs LAM 0001） | LAM ADR を 0002〜0005 に振り直し、影式 ADR-0001 を維持 | `designs/01-design-new-directories.md` 判断3 |
| `docs/memos/` vs `docs/artifacts/` | 新規のみ `docs/artifacts/`、既存 `docs/memos/` は維持 | `designs/01-design-new-directories.md` 判断1 |
| `.claude/agent-memory/` | ディレクトリ作成は延期、CLAUDE.md Memory Policy のみ更新 | `designs/01-design-new-directories.md` 判断2 |
| `ultimate-think` スキル廃止 | 削除。構造化思考は `lam-orchestrate` に統合 | `designs/01-design-commands-skills-agents.md` 判断6 |

---

## 推奨移行順序

```
Phase 0: 差分分析 + 設計 + タスク分解（完了）
  └─ 本ファイル + specs/ + designs/

Phase 1: セキュリティ修正 + settings.json（即時適用推奨）
  ├─ find コマンドの deny パターン追加
  ├─ python コマンドの ask 追加
  ├─ find を allow → ask に移動
  └─ .gitignore 更新（lam-loop-state.json, test-results.xml）

Phase 2: ルール + docs/internal/ + CLAUDE.md
  ├─ test-result-output.md 新規追加
  ├─ phase-rules.md TDD 内省 v2 更新
  ├─ auto-generated/ 更新
  ├─ security-commands.md 更新（rm/chmod/chown deny エスカレーション含む）
  ├─ core-identity.md 更新
  ├─ permission-levels.md 更新（docs/internal PM パス追加、影式固有パス保持）
  ├─ docs/internal/ 差分適用
  └─ CLAUDE.md / CHEATSHEET.md 更新（3層メモリ含む）

Phase 3: コマンド / スキル / エージェント
  ├─ 廃止コマンド 7件 + ultimate-think スキルの削除
  ├─ 残存コマンドの差分適用
  ├─ ui-design-guide スキル追加
  ├─ エージェント更新（memory: project 削除、出力先変更）
  └─ docs/specs/lam/ の新規取り込み（tdd-introspection-v2, release-ops-revision）

Phase 4: 新ディレクトリ + Hooks
  ├─ docs/artifacts/ ディレクトリ構造作成（knowledge/, audit-reports/, tdd-patterns/）
  ├─ ADR 0002〜0005 取り込み（LAM ADR を +1 シフト）
  ├─ hooks 差分適用（_hook_utils.py, post-tool-use.py, lam-stop-hook.py）
  ├─ hooks/tests/ 追加
  └─ pytest --junitxml 設定追加

Phase 5: 統合検証 + 完了
  ├─ 全テスト実行
  ├─ ruff check
  ├─ /full-review 実行
  └─ SESSION_STATE.md 更新 + Phase 2b 再開
```

### 移行 Phase ↔ 設計ファイル対応表

| 移行 Phase | 対応する設計ファイル |
|-----------|-------------------|
| Phase 1 | `designs/01-design-hooks-settings.md`（settings.json セクション）、`designs/01-design-new-directories.md`（.gitignore） |
| Phase 2 | `designs/01-design-rules-docs.md` |
| Phase 3 | `designs/01-design-commands-skills-agents.md`、`designs/01-design-new-directories.md`（specs 取り込み） |
| Phase 4 | `designs/01-design-new-directories.md`（dirs + ADR）、`designs/01-design-hooks-settings.md`（hooks） |
| Phase 5 | 全設計共通 |

> **注**: `designs/01-design-new-directories.md` 内部の P1〜P5 は当該設計内の依存関係順序であり、本サマリーの移行 Phase 1〜5 とは別の番号空間。

---

## 詳細差分ファイル一覧

| ファイル | 対象領域 | ステータス |
|---------|---------|----------|
| [00-diff-summary.md](00-diff-summary.md) | 統合サマリー（本ファイル） | 完了 |
| [00-diff-rules.md](00-diff-rules.md) | .claude/rules/ 詳細差分 | 完了 |
| [00-diff-commands-skills-agents.md](00-diff-commands-skills-agents.md) | commands/, skills/, agents/ 詳細差分 | 完了 |
| [00-diff-hooks-settings.md](00-diff-hooks-settings.md) | hooks/, settings.json 詳細差分 | 完了 |
| [00-diff-docs.md](00-diff-docs.md) | docs/internal/, docs/specs/, CLAUDE.md, CHEATSHEET.md | 完了 |
| [00-diff-new-directories.md](00-diff-new-directories.md) | docs/artifacts/, .claude/agent-memory/ | 完了 |
