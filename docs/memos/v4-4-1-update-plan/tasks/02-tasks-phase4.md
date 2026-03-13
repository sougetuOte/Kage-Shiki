# Phase 4 タスク: 新規ディレクトリ + Hooks

**ステータス**: Draft
**対象設計**:
- `01-design-new-directories.md` — 全判断（ディレクトリ構造、ADR、specs、gitignore）
- `01-design-hooks-settings.md` — 判断 1-4（Hooks 実装の大規模化）
**優先度**: 中（インフラストラクチャ準備）
**依存**: Phase 2, Phase 3 完了

---

## タスク一覧（グループ別概要）

| グループ | 対象 | タスク数 | 権限等級 | 規模 |
|---------|------|---------|---------|------|
| P4A: ディレクトリ構造準備 | docs/artifacts, .claude/agent-memory, .gitignore | 4 | SE/PM 級 | M |
| P4B: ADR 番号衝突解決 | docs/adr/ 0002〜0005 新規作成 | 4 | PM 級 | S |
| P4C: docs/specs/lam/ スペック取り込み | tdd-introspection-v2, release-ops-revision | 2 | PM 級 | M |
| P4D: Hooks の大規模化 | _hook_utils.py, 全 hook ファイル更新 | 5 | SE 級 | L |
| **合計** | — | **15** | 混在 | **L** |

---

## Phase 4A: ディレクトリ構造準備

### P4A-1: docs/artifacts/ ディレクトリ群の作成

**概要**: `docs/artifacts/` およびサブディレクトリ（knowledge/, audit-reports/, tdd-patterns/）を作成。CLAUDE.md の出力先統一の基盤。

**対応設計**: `01-design-new-directories.md` 判断1「docs/artifacts/ 導入」→ 決定 B「新規のみ、既存は docs/memos/ 維持」

**作成対象**:
```
docs/artifacts/
├── knowledge/                    （高優先度）
│   ├── .gitkeep
│   ├── README.md                 （テンプレート）
│   ├── conventions.md            （テンプレート）
│   ├── patterns.md               （テンプレート）
│   └── pitfalls.md               （テンプレート）
├── audit-reports/                （中優先度）
│   ├── .gitkeep
│   └── INDEX.md                  （既存レポートへのリンク集）
└── tdd-patterns/                 （中優先度）
    └── .gitkeep
```

**contents**:

**knowledge/README.md**:
```markdown
# Knowledge Layer — 知見蓄積

このディレクトリには、/retro Step 4 で人間が整理した知見を保存する。

- conventions.md: プロジェクト固有の慣例・パターン
- patterns.md: テスト失敗パターン、デバッグ手法の蓄積
- pitfalls.md: 陥りやすい誤り、注意点の記録
```

**audit-reports/INDEX.md**:
```markdown
# 監査レポート インデックス

## docs/artifacts/audit-reports/ （新規、v4.4.1 以降）
[今後のレポートがここに作成される]

## docs/memos/audit-report-*.md （既存、v4.0.1 までのレポート）
- audit-report-wave3.md
- audit-report-full-source.md
[その他既存レポートへのリンク]
```

**完了条件**:
- [ ] `docs/artifacts/` ディレクトリが作成されている
- [ ] 3 つのサブディレクトリが存在
- [ ] knowledge/, audit-reports/, tdd-patterns/ に `.gitkeep` がある
- [ ] knowledge/README.md, conventions.md, patterns.md, pitfalls.md がテンプレートとして配置
- [ ] audit-reports/INDEX.md が既存レポートへのリンクを記載

---

### P4A-2: .gitignore の更新（LAM 新規エントリ追加 + セクション整理）

**概要**: `.claude/lam-loop-state.json`, `.claude/test-results.xml` を `.gitignore` に追加。同時に LAM runtime state files セクションを整理。

**対応設計**: `01-design-new-directories.md` 判断4「.gitignore の更新」→ 決定「2 エントリ追加 + セクション整理」

**対象ファイル**: `.gitignore`

**変更内容**:
```gitignore
# Agent
.agent/
memos/
!docs/memos/
docs/memos/*
!docs/memos/v4-update-plan/
!docs/memos/v4-4-1-update-plan/          ← 追加（現在計画書を Git 追跡対象に）
.serena/
data/
SESSION_STATE.md
docs/daily/
.claude/settings.local.json
.claude/commands/release.md

# LAM runtime state files                 ← 新規セクション
.claude/lam-loop-state.json               ← 追加（LAM stop-hook が実行時に生成）
.claude/doc-sync-flag
.claude/pre-compact-fired
.claude/last-test-result
.claude/test-results.xml                  ← 追加（TDD 内省 v2 が pytest 出力を読み込む）

# ... その他既存セクション ...
```

**影式固有の注意**:
- `docs/memos/v4-4-1-update-plan/` を除外ルール対象に追加（移行計画を Git 追跡）
- LAM runtime state files セクションを新設して整理

**完了条件**:
- [ ] `.claude/lam-loop-state.json` が `.gitignore` に追加
- [ ] `.claude/test-results.xml` が `.gitignore` に追加
- [ ] LAM runtime state files セクションが整理されている

---

### P4A-3: CLAUDE.md の Memory Policy 三層構造 — 確認タスク

**概要**: P2C-2 で CLAUDE.md の Memory Policy 三層化は実施済み。本タスクでは、Phase 4A-1 で作成した `docs/artifacts/knowledge/` との整合性を確認する。

**注意**: 実装は P2C-2 で完了。本タスクは確認のみ（重複実装しないこと）。

**確認項目**:
- [ ] P2C-2 で Memory Policy セクションが三層構造に更新済みであること
- [ ] Layer 3 の保存先（`docs/artifacts/knowledge/`）が P4A-1 で作成済みであること
- [ ] Layer 2 のディレクトリ作成延期が注記されていること

---

### P4A-4: docs/internal/00_PROJECT_STRUCTURE.md に docs/artifacts/ セクション追記

**概要**: Phase 2 で既に docs/artifacts/ 説明は追加されているが、新規ディレクトリ作成（P4A-1）に合わせて確認。

**対応設計**: `01-design-new-directories.md` 判断1「docs/artifacts/ 導入」

**確認項目**:
- [ ] `docs/artifacts/` セクションが `docs/internal/00_PROJECT_STRUCTURE.md` に記載されている
- [ ] knowledge/, audit-reports/, tdd-patterns/ が列挙されている
- [ ] 「既存 docs/memos/ との役割分離」が説明されている

---

## Phase 4B: ADR 番号衝突解決（影式固有 ADR-0001 を尊重）

### P4B-1: LAM v4.4.1 ADR-0001 を影式 ADR-0002 として取り込み

**概要**: LAM テンプレートの ADR を +1 シフトして取り込み。影式の既存 ADR-0001（免疫系アーキテクチャ）を保護。

**対応設計**: `01-design-new-directories.md` 判断3「ADR 番号衝突解決」→ 決定 A「LAM ADR を 0002〜0005 として取り込み」

**成果物**: `docs/adr/0002-model-routing-strategy.md`

**内容**: LAM v4.4.1 の ADR-0001（モデルルーティング戦略）をそのまま配置し、冒頭に「LAM v4.4.1 ADR-0001 より移植」の注記を追加。

**完了条件**:
- [ ] `docs/adr/0002-model-routing-strategy.md` が作成されている
- [ ] 冒頭に「LAM v4.4.1 ADR-0001 より移植」の注記がある

---

### P4B-2 〜 P4B-4: LAM v4.4.1 ADR-0002〜0004 を影式 ADR-0003〜0005 として取り込み

**概要**: 以下の 3 つの LAM ADR を影式 ADR-0003〜0005 として取り込み。

**成果物**:
- `docs/adr/0003-stop-hook-implementation.md` （LAM ADR-0002 より）
- `docs/adr/0004-context7-vs-webfetch.md` （LAM ADR-0003 より）
- `docs/adr/0005-bash-read-commands-allow-list.md` （LAM ADR-0004 より）

**各ファイル冒頭の注記テンプレート**:
```markdown
# ADR-000X: [タイトル]

> LAM v4.4.1 ADR-000N より移植

## Status
Accepted

## Context
[LAM テンプレートのコンテキスト]
```

**完了条件**:
- [ ] ADR 0003, 0004, 0005 が作成されている
- [ ] 各ファイルに「LAM v4.4.1 ADR-000N より移植」の注記がある
- [ ] Status が Accepted になっている

---

## Phase 4C: docs/specs/lam/ スペック取り込み

### P4C-1: tdd-introspection-v2.md の取り込み

**概要**: LAM v4.4.1 の TDD 内省 v2 仕様を `docs/specs/lam/` に取り込み。後続の trust-model.md v2 化の根拠となる。

**対応設計**: `01-design-new-directories.md` 判断5「docs/specs/lam/ スペック取り込み」

**成果物**: `docs/specs/lam/tdd-introspection-v2.md`

**内容**: LAM v4.4.1 の `tdd-introspection-v2.md` をそのまま配置。

**影式固有の注意**:
- Phase 4C 完了後、Phase 5 で `.claude/rules/auto-generated/trust-model.md` の v2 化を実施（PM 級承認待ち）

**完了条件**:
- [ ] `docs/specs/lam/tdd-introspection-v2.md` が配置されている
- [ ] ファイル内容が LAM v4.4.1 版と同一

---

### P4C-2: release-ops-revision.md の取り込み

**概要**: LAM v4.4.1 の Release Ops 改訂仕様を `docs/specs/lam/` に取り込み。後続の `04_RELEASE_OPS.md` 改訂の根拠となる。

**対応設計**: `01-design-new-directories.md` 判断5「docs/specs/lam/ スペック取り込み」

**成果物**: `docs/specs/lam/release-ops-revision.md`

**内容**: LAM v4.4.1 の `release-ops-revision.md` をそのまま配置。

**影式固有の注意**:
- Phase 4C 完了後、Phase 5 で `docs/internal/04_RELEASE_OPS.md` の改訂を検討（別 PM 承認）

**完了条件**:
- [ ] `docs/specs/lam/release-ops-revision.md` が配置されている

---

## Phase 4D: Hooks の大規模化（_hook_utils.py + 全 hook ファイル）

### P4D-1: _hook_utils.py のリネームと新 API 追加

**概要**: `hook_utils.py` を `_hook_utils.py` にリネーム。新API（`get_project_root()`, `log_entry()`, `atomic_write_json()` 等）を追加。すべて LAM v4.4.1 仕様に従う。

**対応設計**: `01-design-hooks-settings.md` 判断1「_hook_utils.py リネームと API 移行」→ 決定 A「完全移行」

**対象ファイル**: `.claude/hooks/_hook_utils.py`

**変更内容**:

| 関数 | 影式現行 | v4.4.1 | 対応 |
|------|--------|--------|------|
| `PROJECT_ROOT` | モジュール定数 | `get_project_root()` | 関数化（LAM_PROJECT_ROOT 環境変数対応） |
| `read_stdin()` | あり | `read_stdin_json()` | リネーム + 空入力ガード追加 |
| `utc_now()` | あり | `now_utc_iso8601()` | リネーム |
| `log_entry()` | なし | **新規** | TSV フォーマット統一ログ |
| `atomic_write_json()` | なし | **新規** | Windows retry 付きアトミック書き込み |
| `run_command()` | なし | **新規** | subprocess.run ラッパー（shutil.which 対応） |
| `get_tool_name()` | なし | **新規** | 型安全な tool_name 抽出 |
| `get_tool_input()` | なし | **新規** | 型安全な tool_input 抽出 |
| `get_tool_response()` | なし | **新規** | 型安全な tool_response 抽出 |
| `safe_exit()` | なし | **新規** | sys.exit ラッパー |

**影式固有の考慮事項**:
- `read_stdin_json()` の 1MB 制限（現行）は v4.4.1 では削除されているが、セキュリティ観点から影式では保持
- `run_command()` の実装は `sys.executable` を使用して Windows 互換性を確保

**完了条件**:
- [ ] `hook_utils.py` が `_hook_utils.py` にリネームされている
- [ ] 全新 API 関数が実装されている
- [ ] LAM_PROJECT_ROOT 環境変数対応が含まれている
- [ ] Windows retry ロジックが atomic_write_json に含まれている
- [ ] テストが可能な形式になっている

---

### P4D-2 〜 P4D-5: 全 hook ファイルの import 更新（4 hook ファイル）

**概要**: 全 hook ファイルの import 文を `hook_utils` → `_hook_utils` に変更。同時に新 API 呼び出しを適用（段階的）。

**対応設計**: `01-design-hooks-settings.md` 判断1「全 hook の import 変更」

**対象ファイル**（影式に存在する hook のみ）:
```
.claude/hooks/
├── pre-tool-use.py
├── post-tool-use.py
├── lam-stop-hook.py
├── pre-compact.py
└── notify-sound.py    ← 影式固有（hook_utils を import しないため変更不要）
```

**変更パターン**:

```python
# 変更前
import hook_utils

# 変更後
from _hook_utils import (
    get_project_root,
    read_stdin_json,
    log_entry,
    atomic_write_json,
    run_command,
    get_tool_name,
    get_tool_input,
    get_tool_response,
    now_utc_iso8601,
    safe_exit,
)
```

**段階的対応方針**（リスク回避）:

1. **P4D-2**: `pre-tool-use.py` — 権限等級判定メインロジック + out-of-root 検出
2. **P4D-3**: `post-tool-use.py` — JUnit XML パース + TDD ログ記録
3. **P4D-4**: `lam-stop-hook.py` — 収束判定メインロジック + pm_pending フラグ読取
4. **P4D-5**: `pre-compact.py` — 簡易ロジック（リスク低）

> **除外**: P4D-6〜P4D-8（pre-flight-check.py, doc-sync-trigger.py, check-circular-deps.py）は影式に存在しないため対象外。

**各 Hook の詳細**:

#### P4D-2: pre-tool-use.py の更新

**概要**: PreToolUse hook を v4.4.1 仕様に更新。hookSpecificOutput 形式、out-of-root 検出、AUDITING PG 特別処理、PM パターン厳密化を実装。

**対応設計**: `01-design-hooks-settings.md` 判断4「pre-tool-use.py の応答形式更新」

**主要変更**:
- 応答形式: `{"decision": "block"}` → `{"hookSpecificOutput": {"permissionDecision": "ask"}}`
- out-of-root マーカー追加（プロジェクトルート外のパスを検出）
- AUDITING PG 特別処理（ruff, prettier 等の lint コマンドを自動許可）
- PM パターン厳密化（prefix match → 正規表現）

**検証注記**: 実装前に Claude Code 公式ドキュメント（`https://code.claude.com/docs/en/hooks`）で `hookSpecificOutput` スキーマを最終確認する（upstream-first 原則）。

**完了条件**:
- [ ] import が `_hook_utils` に変更されている
- [ ] 応答形式が `hookSpecificOutput` 形式に更新されている
- [ ] out-of-root 検出が実装されている
- [ ] PM パターンが厳密化されている

---

#### P4D-3: post-tool-use.py の更新

**概要**: PostToolUse hook を TDD 内省 v2（JUnit XML）対応に更新。exitCode 方式から JUnit XML パースへ移行。

**対応設計**: `01-design-hooks-settings.md` 判断2「TDD 内省 v2 移行」

**主要変更**:
- テスト結果判定: `tool_response.exitCode` → `.claude/test-results.xml` をパース
- XML パース関数 `_parse_junit_xml()` を実装
- ログ内容: exit_code のみ → `tests=N failures=N` + 失敗テスト名
- FAIL→PASS 時の systemMessage 出力（`/retro` 推奨）を実装
- 検出閾値: 3 回 → 2 回に引き下げ

**`_parse_junit_xml()` の仕様**:
```python
def _parse_junit_xml(xml_path: Path) -> Optional[Dict]:
    """
    JUnit XML ファイルをパース。

    入力: xml_path (Path)
    出力: {
        "tests": int,
        "failures": int,
        "errors": int,
        "failed_names": list[str]
    }
    ファイル不存在またはパース失敗時: None を返す
    """
```

**完了条件**:
- [ ] import が `_hook_utils` に変更されている
- [ ] `_parse_junit_xml()` 関数が実装されている
- [ ] 実行時に `.claude/test-results.xml` を読取している
- [ ] ログに失敗テスト名が記載されている
- [ ] FAIL→PASS 時に systemMessage が出力される

---

#### P4D-4: lam-stop-hook.py の大幅拡張

**概要**: LAM v4.4.1 の拡張機能を採用。収束判定精度向上、pm_pending フラグ対応、シークレットスキャン、Issue 再発チェック等を実装。

**対応設計**: `01-design-hooks-settings.md` 判断3「lam-stop-hook.py 大幅拡張」

**採用機能**:
```
[ ] convergence_reason を state に記録（停止理由の可視化）
[ ] pm_pending フラグの読取（pre-tool-use との連携）
[ ] fullscan_pending フラグ（Green State 後の追加スキャン）
[ ] Issue 再発チェック（2 サイクル連続 issues_fixed=0 でエスカレーション）
[ ] TDD パターン通知（未分析パターンがあれば通知）
[ ] ループログ保存（停止時に .claude/logs/loop-{timestamp}.txt）
[ ] 状態ファイルクリーンアップ（ループ終了時に lam-loop-state.json 削除）
[ ] シークレットスキャン（ファイル内のシークレットパターン検出）
[ ] CWD 検証（パストラバーサル防止）
[ ] symlink スキップ（シークレットスキャン時に symlink を除外）
[ ] STEP 番号体系（0-6 → 1-7 に統一）
```

**不採用機能**:
```
[ ✗ ] ツール自動検出（pytest, ruff を固定）
[ ✗ ] lint 自動検出（ruff を固定）
[ ✗ ] セキュリティツール自動検出（pip-audit を固定）
```

**影式固有の調整**:
- STEP 番号: 1-7 に統一（影式は現在 0-6）
- `sys.executable` を使用して Windows 互換性確保
- ハードコードされたツール（pytest, ruff, pip-audit）を保持

**完了条件**:
- [ ] `_hook_utils` import が更新されている
- [ ] convergence_reason が記録されている
- [ ] pm_pending / fullscan_pending フラグが読取られている
- [ ] Issue 再発チェックが実装されている
- [ ] ループログ保存 + 状態クリーンアップが実装されている
- [ ] シークレットスキャン機能が追加されている
- [ ] STEP 番号が 1-7 に統一されている

---

#### P4D-5: pre-compact.py の import 更新

**概要**: `pre-compact.py` の import を `hook_utils` → `_hook_utils` に変更。

**対象ファイル**: `.claude/hooks/pre-compact.py`

**最小変更**:
- import 文のみ変更
- 新 API（log_entry, atomic_write_json 等）の活用は後続 Phase で検討

**完了条件**:
- [ ] import が `_hook_utils` に変更されている
- [ ] 構文エラーがないこと

---

> **注**: P4D-6〜P4D-8（pre-flight-check.py, doc-sync-trigger.py, check-circular-deps.py）は
> LAM テンプレートにのみ存在するファイルであり、影式には未導入。
> 影式の hooks は以下の 6 ファイル構成:
> `hook_utils.py`（→ `_hook_utils.py`）, `pre-tool-use.py`, `post-tool-use.py`,
> `lam-stop-hook.py`, `pre-compact.py`, `notify-sound.py`（影式固有、変更不要）

---

## 作業順序と依存関係

```
Phase 4A: ディレクトリ準備
  ├─ P4A-1 (docs/artifacts/ 作成): 1時間
  ├─ P4A-2 (.gitignore 更新): 30分
  ├─ P4A-3 (CLAUDE.md Memory Policy): 30分
  └─ P4A-4 (PROJECT_STRUCTURE 確認): 15分
  並列可: P4A-1/2/3/4

Phase 4B: ADR 番号衝突解決
  ├─ P4B-1 (ADR-0002): 15分
  ├─ P4B-2 (ADR-0003): 15分
  ├─ P4B-3 (ADR-0004): 15分
  └─ P4B-4 (ADR-0005): 15分
  並列可: P4B-1/2/3/4

Phase 4C: docs/specs/lam/ スペック取り込み
  ├─ P4C-1 (tdd-introspection-v2.md): 15分
  └─ P4C-2 (release-ops-revision.md): 15分
  並列可: P4C-1/2

Phase 4D: Hooks 大規模化
  ├─ P4D-1 (_hook_utils.py リネーム + API 追加): 2時間
  ├─ P4D-2 (pre-tool-use.py): 1.5時間
  ├─ P4D-3 (post-tool-use.py): 1.5時間
  ├─ P4D-4 (lam-stop-hook.py): 2時間
  └─ P4D-5 (pre-compact.py): 30分
  （P4D-6〜P4D-8 は影式に存在しないため対象外）

  依存順序:
    P4D-1 → P4D-2, P4D-3, P4D-4, P4D-5
    （P4D-1 完了後、P4D-2〜5 は並列可）
    notify-sound.py は変更不要（hook_utils を import しないため）

総作業量: ~8-9時間
権限等級: PM 級（仕様変更）+ SE 級（実装変更）
```

---

## リスク と対策

| # | リスク | 影響度 | 対策 |
|---|--------|--------|------|
| R1 | `_hook_utils.py` リネーム時に既存 hook が import エラーになる | 高 | P4D-1 と P4D-2〜5 を同一コミットでアトミック実施 |
| R2 | JUnit XML ファイルが生成されない環境で post-tool-use.py がエラー | 中 | XML ファイル不存在時は早期 return（ログスキップ）で安全処理 |
| R3 | out-of-root 検出の正規表現が不適切で PM 判定漏れ | 中 | Path.resolve().relative_to() 実装で確実に検出 |
| R4 | hookSpecificOutput 形式が公式仕様と異なる | 高 | 実装前に公式ドキュメント確認を必須条件化 |
| R5 | シークレットスキャンが安全パターン(test, mock 等)を誤検出 | 中 | 安全パターン除外（\btest\b, \bmock\b, \bexample\b）を実装 |

---

## 検証チェックリスト

### ディレクトリ構造
- [ ] `docs/artifacts/knowledge/`, `audit-reports/`, `tdd-patterns/` が作成
- [ ] knowledge/ にテンプレート 4 ファイルがある
- [ ] audit-reports/INDEX.md が既存レポートへのリンク記載
- [ ] .gitkeep が配置

### .gitignore
- [ ] `.claude/lam-loop-state.json` が追加
- [ ] `.claude/test-results.xml` が追加
- [ ] LAM runtime state files セクションが新規

### ADR
- [ ] ADR 0002〜0005 が作成
- [ ] 各ファイルに「LAM v4.4.1 ADR-000N より移植」注記

### specs/lam/
- [ ] `tdd-introspection-v2.md` が配置
- [ ] `release-ops-revision.md` が配置

### Hooks
- [ ] `_hook_utils.py` が配置（リネーム完了）
- [ ] 全新 API 関数が実装
- [ ] 全 4 hook ファイル（pre-tool-use, post-tool-use, lam-stop-hook, pre-compact）の import が `_hook_utils` に更新
- [ ] pre-tool-use.py が hookSpecificOutput 形式
- [ ] post-tool-use.py が JUnit XML パース実装
- [ ] lam-stop-hook.py が拡張機能採用
- [ ] notify-sound.py が変更されていない（影式固有、保護対象）
