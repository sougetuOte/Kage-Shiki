# 設計: Hooks + Settings v4.4.1 移行戦略

**作成日**: 2026-03-13
**ステータス**: Draft
**対象 Phase**: Phase 2b (LAM v4.4.1 移行 — Hooks + Settings)

---

## 概要

影式は LAM v4.0.1 移行（2026-03）において hooks を Python で実装した。LAM v4.4.1 では hooks に大幅な機能追加と品質改善が行われており、影式の現行実装との間に複数の差異が存在する。

本文書では、差分分析 (`docs/memos/v4-4-1-update-plan/specs/00-diff-hooks-settings.md`) で特定された 6 つの主要な判断ポイントについて設計を記述する。

### 移行の目的

1. **バグ修正**: TDD パターン記録が実質的に動作していない問題（exitCode 方式の欠陥）を解消する
2. **セキュリティ強化**: `find` コマンドの権限昇格リスクを修正する
3. **品質向上**: `_hook_utils.py` の API 統一・テスト容易性の向上
4. **機能拡充**: `lam-stop-hook.py` の収束判定精度を高める
5. **テスト基盤整備**: hook に対するテストがゼロである現状を解消する

### 方針の概観

影式固有の制約（Windows, Python 単一言語, `python` コマンド名）を維持しながら、v4.4.1 の改善を取り込む。全ての変更は影式の `Hierarchy of Truth`（仕様書 > 既存コード）に従い、仕様書との整合を確保する。

---

## 判断1: _hook_utils.py リネームと API 移行戦略

### 現状

影式は `hook_utils.py` として共通ユーティリティを実装している。v4.4.1 では `_hook_utils.py`（アンダースコア接頭辞）に変更されており、さらに複数の新関数が追加されている。

現行 API との差異:

| 関数 | 影式現行 | v4.4.1 | 差異 |
|------|---------|--------|------|
| プロジェクトルート | `PROJECT_ROOT`（モジュール定数） | `get_project_root()`（関数） | テスト可能性の差 |
| stdin 読み取り | `read_stdin()` | `read_stdin_json()` | 名前変更 + 空入力ガード |
| タイムスタンプ | `utc_now()` | `now_utc_iso8601()` | 名前変更 |
| ログ記録 | 各 hook で独自実装 | `log_entry(log_file, level, source, message)` | **新規 — 統一フォーマット** |
| アトミック書き込み | 各 hook で独自実装（retry なし） | `atomic_write_json(path, data)` | **新規 — Windows retry 付き** |
| subprocess 実行 | `lam-stop-hook.py` で直接 `subprocess.run` | `run_command(args, cwd, timeout)` | **新規 — shutil.which 解決** |
| tool_name 取得 | `data.get("tool_name", "")` | `get_tool_name(data)` | **新規 — 型安全抽出** |
| tool_input 取得 | 直接アクセス | `get_tool_input(data, key)` | **新規 — 型安全抽出** |
| tool_response 取得 | 直接アクセス | `get_tool_response(data, key, default)` | **新規 — 型安全抽出** |
| 終了 | `sys.exit(0)` | `safe_exit(code)` | **新規 — ラッパー** |

### 選択肢

| 選択肢 | 概要 | メリット | デメリット |
|--------|------|---------|-----------|
| A. 完全移行 | リネーム + 全 API 移行 + 新関数追加 | v4.4.1 との整合性最大、テスト容易性向上 | 全 hook の変更が必要 |
| B. リネームのみ | `_hook_utils.py` にリネームし、API は現行維持 | 変更範囲が最小 | 新関数のメリットを受けられない。v4.5 移行時に再度作業 |
| C. 変更なし | `hook_utils.py` のままで API も維持 | 作業不要 | テストスイート（判断6）が `_hook_utils.py` 前提のため導入不可 |

### 比較

| 評価軸 | A. 完全移行 | B. リネームのみ | C. 変更なし |
|--------|-----------|--------------|-----------|
| テスト容易性 | ◎ `LAM_PROJECT_ROOT` 環境変数で tmp_path に差し替え可能 | ○ リネームは満たすが PROJECT_ROOT は固定のまま | × テストスイート導入の前提条件を満たさない |
| Windows 互換性 | ◎ `atomic_write_json` の Windows retry が有効 | △ retry なしのまま | △ retry なしのまま |
| 移行コスト | 中（全 hook import 変更 + 各 hook の実装更新） | 低（import 変更のみ） | なし |
| v4.4.x 追従性 | ◎ | △（都度 API 追加が必要） | × |
| ログ統一性 | ◎ TSV フォーマットで全 hook のログが統一される | × 各 hook で独自フォーマット継続 | × |

### 決定: **A. 完全移行（リネーム + API 移行 + 新関数追加）**

**根拠**:

1. **テストスイート（判断6）の前提条件**: `get_project_root()` の `LAM_PROJECT_ROOT` 環境変数サポートがなければ、hook テストで `tmp_path` への差し替えができない。B/C を選択するとテストスイート導入が実質的に不可能になる
2. **`atomic_write_json` の Windows 安全性**: 現行実装は `os.replace()` による一時ファイル置換だが、retry ロジックがない。Windows では他プロセスによるファイルロックで `PermissionError` が発生する可能性があり、retry 付きの実装が堅牢
3. **ログ統一**: TSV フォーマットへの統一により、`permission.log` や `tdd-patterns.log` の可読性・解析性が向上する
4. **一括作業の効率**: 選択肢 B を選んでも、次の移行時に改めて全 hook を変更することになる。今回まとめて行う方が総コストは低い

**影式固有の考慮事項**:

- `read_stdin_json()` の `MAX_STDIN_BYTES` 制限（現行 1MB）は v4.4.1 では削除されているが、セキュリティ観点から影式版では制限を維持する（v4.4.1 には空入力ガード `if not raw.strip(): return {}` があり、これは採用する）
- 例外キャッチを `except Exception` から `except (json.JSONDecodeError, ValueError, OSError)` に具体化する（v4.4.1 の方針を採用）

**影響する全 hook の import 変更**:

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

**リスク**: v4.0.1 の `notify-sound.py` は `hook_utils` を import していない（単独スクリプト）ため影響なし。

---

## 判断2: TDD 内省パイプライン v1 → v2 移行（JUnit XML 方式）

### 現状と問題

差分分析で判明した **重大なバグ**: 影式の `post-tool-use.py` は `tool_response.get("exitCode")` でテスト結果を判定しているが、**Claude Code の PostToolUse イベントの stdin JSON に `exitCode` フィールドは存在しない**。結果として、TDD パターン記録は常に `exit_code = None`（失敗なし）として動作しており、実質的に機能していない。

v4.4.1 では JUnit XML ファイルのパースに移行してこの問題を解決している。

### 方式の比較

| 評価軸 | 現行: exitCode 方式（v1） | v4.4.1: JUnit XML 方式（v2） |
|--------|--------------------------|------------------------------|
| 動作状態 | **機能不全**（exitCode が存在しない） | 正常動作 |
| pytest との親和性 | × | ◎ `--junitxml` オプションは pytest 標準機能 |
| 失敗テスト名の取得 | 不可 | ◎ XML の `<testcase>` + `<failure>` から取得可能 |
| FAIL→PASS 通知 | ログ記録のみ（実質なし） | `systemMessage` で `/retro` 推奨を出力 |
| 追加設定 | なし | `pyproject.toml` に `--junitxml` 追加が必要 |
| `.gitignore` | 変更なし | `.claude/test-results.xml` 追加が必要 |
| 新規ルールファイル | なし | `.claude/rules/test-result-output.md` 作成が必要 |

### v2 移行に必要な変更一覧

**pyproject.toml の変更**:

現行の `addopts`:
```toml
addopts = "--cov=kage_shiki --cov-report=term-missing"
```

変更後:
```toml
addopts = "--cov=kage_shiki --cov-report=term-missing --junitxml=.claude/test-results.xml"
```

**`.gitignore` への追加**:
```
.claude/test-results.xml
```

**`.claude/rules/test-result-output.md` の新規作成**:

TDD パターン記録の運用ルールを記述するルールファイル。hook が `/retro` 推奨を出したときの対応フローを定義する。

**`post-tool-use.py` の変更点**:

| 項目 | 現行 | v2 |
|------|------|-----|
| テスト結果判定 | `tool_response.exitCode` | `.claude/test-results.xml` をパース |
| XML パース関数 | なし | `_parse_junit_xml(xml_path)` を追加 |
| 失敗検出 | `exitCode != 0` | XML の `failures > 0 or errors > 0` |
| ログ内容 | exit_code のみ | `tests=N failures=N` + 失敗テスト名 |
| FAIL→PASS 時の出力 | なし | `systemMessage` で `/retro` 推奨 |
| 検出閾値 | 3回 | **2回**（v4.4.1 の変更を採用） |

**閾値変更（3→2）の根拠**: v4.4.1 の改訂判断。3回は「確認が遅すぎる」という運用上の知見。

**`_parse_junit_xml` の設計**:

```
入力: xml_path (Path)
出力: {"tests": int, "failures": int, "errors": int, "failed_names": list[str]}
      ファイル不存在 or パース失敗時: None を返す

処理:
  1. xml_path が存在するか確認
  2. xml.etree.ElementTree でパース
  3. testsuite 要素から tests/failures/errors 属性を取得
  4. failure 要素を持つ testcase の classname+name を収集
  5. failed_names として返す
```

### 決定: **v2 完全移行（JUnit XML 方式）**

**根拠**:

1. **現行実装はバグ**: exitCode 方式は Claude Code の仕様上動作しない。維持する理由がない
2. **pytest 標準機能**: `--junitxml` は pytest の標準オプションであり、追加依存なし
3. **失敗テスト名の可視化**: ログに失敗テスト名が記録されることで、TDD パターンの分析精度が大幅に向上する
4. **`/retro` 推奨の自動化**: FAIL→PASS 遷移時に `systemMessage` でレトロスペクティブを促す機能は、チームの学習サイクルを支援する

**影式固有の考慮事項**:

- `python -m pytest` を使用する影式では `python -m pytest --junitxml=...` が正しいコマンド形式。pyproject.toml の `addopts` に追加することで自動的に有効になる
- `.claude/test-results.xml` はセッションごとに上書きされる揮発性ファイル。`.gitignore` への追加が必須
- テストコマンド判定パターンの更新: 現行パターンは `python -m pytest` にマッチするが、v4.4.1 では `pytest` のみにマッチするよう変更されている。影式では `python -m pytest` も頻繁に使用するため、**両方にマッチするパターンを維持する**（v4.4.1 の変更を採用しない）

---

## 判断3: lam-stop-hook.py 大幅拡張の採用範囲

### 現状

影式現行の `lam-stop-hook.py` は 225 行、関数数 8。v4.4.1 は 678 行、関数数 20+。約 3 倍の規模差があり、機能追加と品質改善が含まれている。

### 採用候補の機能一覧

| 機能 | v4.4.1 の実装 | 影式での価値 | 採用判断 |
|------|--------------|------------|---------|
| ツール自動検出 | `_detect_test_framework()` | 低（影式は pytest 固定） | **不採用**（後述） |
| lint 自動検出 | `_detect_lint_tool()` | 低（影式は ruff 固定） | **不採用** |
| セキュリティツール自動検出 | `_detect_security_tools()` | 低（影式は pip-audit 固定） | **不採用** |
| pip-audit 誤検出修正 | `[project]` セクション確認 | 高（影式は pyproject.toml に `[project]` あり） | **採用** |
| `convergence_reason` 記録 | 停止理由を state に記録 | 中（ループログの可読性向上） | **採用** |
| `pm_pending` フラグ | PM 級 Issue 検出時の即停止 | 高（pre-tool-use との連携） | **採用** |
| `fullscan_pending` フラグ | Green State 後の追加スキャン | 中（品質向上） | **採用** |
| Issue 再発チェック | 2サイクル連続 issues_fixed=0 でエスカレーション | 高（無限ループ防止） | **採用** |
| TDD パターン通知 | 未分析パターンがあれば通知 | 中（判断2と連携） | **採用** |
| ループログ保存 | 停止時に `.claude/logs/loop-{timestamp}.txt` | 高（デバッグ性向上） | **採用** |
| 状態ファイルクリーンアップ | ループ終了時に `lam-loop-state.json` 削除 | 高（状態の確実なリセット） | **採用** |
| シークレットスキャン | ファイル内のシークレットパターン検出 | 高（セキュリティ） | **採用**（後述で詳細検討） |
| CWD 検証 | パストラバーサル防止 | 中（セキュリティ） | **採用** |
| symlink スキップ | シークレットスキャン時に symlink を除外 | 中（安全性） | **採用** |
| STEP 番号体系 | 1-7 に統一 | 低（コードコメントのみ） | **採用**（コスト低） |

### ツール自動検出の採用判断

**不採用の根拠**:

影式は Python 単一言語プロジェクト。`_detect_test_framework()` が `pyproject.toml` / `package.json` / `go.mod` / `Makefile` を検索しても、pytest 以外が検出される可能性は実質ゼロ。

| 評価軸 | 自動検出（v4.4.1） | ハードコード（影式維持） |
|--------|-------------------|----------------------|
| 複数言語プロジェクトへの対応 | ◎ | × （影式の要件外） |
| 実行速度 | △（ファイル検索のオーバーヘッド） | ◎ |
| コードの単純さ | △（複雑なフォールバックロジック） | ◎ |
| 誤検出リスク | 中（Makefile の `test:` 誤検出） | なし |
| 将来の言語追加時 | 自動対応 | 手動変更が必要 |

影式の YAGNI 原則（`CLAUDE.md` 参照）に従い、不要な抽象化は避ける。

**ハードコードの設計**:

```python
# 影式固有: ツールをハードコード
TEST_CMD = [sys.executable, "-m", "pytest"]
LINT_CMD = [sys.executable, "-m", "ruff", "check", "."]
SECURITY_CMD = ["pip-audit"]  # shutil.which で存在確認
```

### シークレットスキャンの採用詳細

v4.4.1 のシークレットスキャンを採用する。影式への適用における考慮点:

**対象拡張子（影式向け調整）**:

| 拡張子 | v4.4.1 | 影式 | 理由 |
|--------|--------|------|------|
| `.py .json .yaml .yml .toml .cfg .ini .env` | 採用 | 採用 | 影式で使用 |
| `.js .ts .sh` | 採用 | 採用（スキャンのみ、実ファイルは少ない） | 汎用性 |

**除外ディレクトリ**:

v4.4.1 の `.git node_modules __pycache__ .venv .pytest_cache` を採用する。影式固有の除外として `.mypy_cache` を追加する。

**安全パターン除外**: `\btest\b \bspec\b \bmock\b \bexample\b` 等の v4.4.1 パターンをそのまま採用する。

### 決定: **主要機能を採用、ツール検出はハードコードを維持**

採用する機能の優先度と依存関係:

```
pip-audit 誤検出修正（独立）
    ↕ 並列可
convergence_reason 追加（lam-loop-state.json のスキーマ変更）
    ↕ 並列可
pm_pending / fullscan_pending フラグ（state 読み取りロジック追加）
    ↓
Issue 再発チェック（convergence_reason に依存）
    ↓
ループログ保存 + 状態クリーンアップ（停止フローに追加）
    ↕ 並列可（独立）
CWD 検証（_validate_check_dir 関数追加）
    ↕ 並列可（独立）
シークレットスキャン（G5 の拡張）
    ↕ 並列可（独立）
TDD パターン通知（判断2の JUnit XML 移行と連携）
```

**影式固有の調整事項**:

- STEP 番号: 影式現行は STEP 0-6、v4.4.1 は STEP 1-7。v4.4.1 に合わせて STEP 1-7 に統一する
- `sys.executable` を使用することで `python` / `python3` の差異を吸収する（Windows 安全）

---

## 判断4: pre-tool-use.py の応答形式更新

### 現状と問題

影式現行の PM 級応答:
```json
{"decision": "block", "reason": "..."}
```

v4.4.1 の PM 級応答:
```json
{
  "hookSpecificOutput": {
    "permissionDecision": "ask",
    "permissionDecisionReason": "..."
  }
}
```

差分分析では「**要確認**: upstream-first ルールに従い、Claude Code 公式ドキュメントで正しい形式を確認すべき」と明記されている。

### upstream-first 原則の適用

`.claude/rules/upstream-first.md` の定義に従い、Claude Code 公式ドキュメントで `hookSpecificOutput` の仕様を確認した上で決定する。

**確認の観点**:

| 確認ポイント | 確認内容 |
|------------|---------|
| `permissionDecision` の有効値 | `ask`, `allow`, `block` のいずれか |
| `hookSpecificOutput` の正式なインターフェース | PreToolUse hook の出力スキーマ |
| `decision: block` の後方互換性 | 旧形式が引き続き動作するか |

**現時点での設計判断**:

差分分析で v4.4.1 が `hookSpecificOutput` 形式を採用していること、および v4.4.1 が最新の Claude Code 公式仕様に追従していることから、`hookSpecificOutput` 形式を採用する。ただし、実装 Phase 開始前に公式ドキュメントで最終確認を行うことを **必須条件** とする。

`permissionDecision: "ask"` は「ユーザーに確認を求める」意味であり、`"block"` よりもユーザーフレンドリーな動作（理由が表示されてユーザーが判断できる）が期待できる。

### その他の変更点

**out-of-root 検出の追加**:

現行実装はプロジェクトルート外のパスをそのまま返すため、PM 判定が漏れる可能性がある。v4.4.1 は `__out_of_root__/` マーカーを付与して PM 級として捕捉する。

```python
# v4.4.1 の out-of-root 検出
try:
    rel = str(Path(file_path).resolve().relative_to(project_root))
except ValueError:
    rel = f"__out_of_root__/{Path(file_path).name}"
```

**AUDITING PG 特別処理の追加**:

v4.4.1 は AUDITING フェーズ中に lint/format コマンドを PG 級として自動許可する `_AUDITING_PG_COMMANDS` を定義している。

```python
_AUDITING_PG_COMMANDS = frozenset([
    "ruff check --fix",
    "ruff format",
    "npx prettier",
    "npx eslint --fix",
])
```

影式では `ruff check --fix` と `ruff format` のみが対象（Node.js ツールは不使用だが、将来の拡張性のためパターン定義として保持する）。

**PM パターンの厳密化**:

| パターン | 現行 | v4.4.1 | 影式での対応 |
|---------|------|--------|-------------|
| `docs/specs/` | prefix match | `^docs/specs/.*\.md$` | v4.4.1 を採用（.md 以外は PM 不要） |
| `docs/adr/` | prefix match | `^docs/adr/.*\.md$` | v4.4.1 を採用 |
| `.claude/rules/` | prefix match | `^\.claude/rules/.*\.md$` | v4.4.1 を採用 |
| `.claude/settings*.json` | `\.claude/settings.*\.json$` | `^\.claude/settings.*\.json$` | `^` 追加のみ |
| `docs/internal/` | あり | **なし** | **影式固有として保持** |
| `pyproject.toml` | あり | **なし** | **影式固有として保持** |

### 選択肢

| 選択肢 | 概要 |
|--------|------|
| A. `hookSpecificOutput` 形式に移行 | v4.4.1 と公式仕様に準拠。`permissionDecision: "ask"` を使用 |
| B. `decision: block` を維持 | 現行形式。動作確認済みだが、公式仕様との乖離が不明 |
| C. 両形式をフォールバック付きで実装 | `hookSpecificOutput` が未サポートの場合に `decision: block` へフォールバック |

### 比較

| 評価軸 | A. hookSpecificOutput | B. decision: block 維持 | C. 両形式フォールバック |
|--------|----------------------|------------------------|----------------------|
| 公式仕様準拠 | ◎（v4.4.1 採用形式） | 不明（公式確認必要） | △ |
| ユーザー体験 | ◎（ask でユーザーが判断可能） | △（block は強制的） | ○ |
| 実装複雑度 | 低 | 最低 | 高 |
| 後方互換性 | 不明（要確認） | ◎ | ◎ |

### 決定: **A. `hookSpecificOutput` 形式に移行（公式確認を前提条件として）**

**根拠**:

1. **upstream-first 原則**: v4.4.1 が採用している形式は公式 Claude Code の最新仕様を反映している可能性が高い
2. **ユーザー体験**: `permissionDecision: "ask"` はユーザーが理由を確認して判断できるため、`"block"` より優れた UX
3. **将来性**: 旧形式 (`decision: block`) が将来非推奨になるリスクを回避

**前提条件**: 実装 Phase 開始前に Claude Code 公式ドキュメント（https://docs.anthropic.com/en/docs/claude-code/hooks）で `hookSpecificOutput` スキーマを確認すること。公式仕様が `decision: block` を推奨している場合は B を採用する。

---

## 判断5: settings.json セキュリティ修正

### 現状

差分分析で特定されたセキュリティ上の問題:

1. `Bash(find *)` が `allow` に分類されており、`find . -delete` 等の破壊的操作が許可される
2. `find` を利用した権限昇格コマンドの deny パターンが存在しない
3. `Bash(python *)` が未分類（ask にも deny にも allow にも存在しない）

### 変更の詳細

**allow → ask 移動**:

| コマンド | 現行 | 変更後 | 理由 |
|---------|------|--------|------|
| `Bash(find *)` | allow | **ask** | 破壊的オプション（`-delete`, `-exec rm`）が allow される安全上の問題 |

**deny リストへの追加**:

| コマンドパターン | 追加理由 |
|---------------|---------|
| `Bash(find * -delete *)` | `find . -delete` でファイルを直接削除可能 |
| `Bash(find * -exec rm *)` | `find` + `exec rm` でファイル削除 |
| `Bash(find * -exec chmod *)` | `find` + `chmod` での権限変更 |
| `Bash(find * -exec chown *)` | `find` + `chown` での所有者変更 |

**ask リストへの追加**:

| コマンドパターン | 追加理由 |
|---------------|---------|
| `Bash(find *)` | allow から移動 |
| `Bash(python *)` | Python スクリプト実行の制御（settings.local.json で allow にオーバーライド済みだが、明示的に ask として定義する） |

### 影式固有の維持事項

v4.4.1 テンプレートには存在しないが、影式固有として維持するエントリ:

| コマンド | 維持理由 |
|---------|---------|
| `Bash(git status *)` | `git status ./path` 等の引数付き git status を allow で使用 |
| `Bash(pip show *)` | 依存パッケージの確認コマンド |

### hooks セクションの変更

v4.4.1 では hooks コマンドで `python3` を使用しているが、**影式は `python` を維持する**。

**理由**: Windows 環境では `python3` コマンドが存在しない場合がある。影式の全 hooks は `python .claude/hooks/xxx.py` 形式で動作確認済みであり、変更するメリットがない。

### 変更後の settings.json 構造（変更点のみ）

```json
{
  "permissions": {
    "allow": [
      "Bash(ls *)",
      "Bash(cat *)",
      "Bash(grep *)",
      // "Bash(find *)" を削除
      "Bash(pwd)",
      "Bash(du *)",
      "Bash(file *)",
      "Bash(git status)",
      "Bash(git status *)",   // 影式固有: 維持
      "Bash(git log *)",
      "Bash(git diff *)",
      "Bash(git show *)",
      "Bash(git branch *)",
      "Bash(pytest *)",
      "Bash(npm test *)",
      "Bash(go test *)",
      "Bash(npm list *)",
      "Bash(pip list *)",
      "Bash(pip show *)",     // 影式固有: 維持
      "Bash(ps *)",
      "Bash(npx prettier *)",
      "Bash(npx eslint --fix *)",
      "Bash(ruff check --fix *)",
      "Bash(ruff format *)"
    ],
    "deny": [
      "Bash(rm *)",
      "Bash(rm -rf *)",
      "Bash(mv *)",
      "Bash(chmod *)",
      "Bash(chown *)",
      "Bash(systemctl *)",
      "Bash(service *)",
      "Bash(reboot)",
      "Bash(shutdown *)",
      "Bash(apt *)",
      "Bash(yum *)",
      "Bash(brew *)",
      // v4.4.1 追加: find の破壊的パターン
      "Bash(find * -delete *)",
      "Bash(find * -exec rm *)",
      "Bash(find * -exec chmod *)",
      "Bash(find * -exec chown *)"
    ],
    "ask": [
      "Bash(git push *)",
      "Bash(git pull *)",
      "Bash(git fetch *)",
      "Bash(git clone *)",
      "Bash(git commit *)",
      "Bash(git merge *)",
      "Bash(curl *)",
      "Bash(wget *)",
      "Bash(ssh *)",
      "Bash(npm start *)",
      "Bash(npm run *)",
      "Bash(make *)",
      "Bash(mkdir *)",
      "Bash(touch *)",
      "Bash(cp *)",
      // v4.4.1 追加: allow から移動 + 新規
      "Bash(find *)",
      "Bash(python *)"
    ]
  }
}
```

**注意**: `Bash(python *)` を ask に追加しても、`settings.local.json` で `Bash(python *)` が allow になっているため、実際の影響はない。明示的な定義として記録する意味がある。

### 決定: **全セキュリティ修正を適用、影式固有エントリを維持**

**根拠**:

1. **セキュリティリスクの排除**: `find * -delete` は不可逆的な操作であり、allow から除外することはリスクゼロのセキュリティ向上
2. **deny パターンの明示化**: 破壊的 find コマンドを deny リストに追加することで、設定の意図が明確になる
3. **影式固有維持**: `git status *` と `pip show *` は影式の日常的なワークフローで使用されており、ask に移動すると作業効率が低下する。v4.4.1 テンプレートとの乖離は最小限にとどめつつ、運用性を優先する

---

## 判断6: Hook テストスイートの導入

### 現状

影式は hooks を実装しているが、**hook に対するテストが存在しない**。v4.4.1 は 53 テストのテストスイートを持ち、`_hook_utils.py`、各 hook、統合テストをカバーしている。

### テスト配置の選択肢

| 選択肢 | 配置場所 | メリット | デメリット |
|--------|---------|---------|-----------|
| A. `.claude/hooks/tests/` | hooks と同じ `.claude/` 以下 | hooks と同じ場所に存在、LAM v4.4.1 の配置と同一 | `testpaths = ["tests"]` の設定外で自動収集されない |
| B. `tests/test_hooks/` | 既存 tests/ ディレクトリ以下 | 既存テストインフラと統合、`pytest` 一発で全テスト実行 | 影式アプリのテストと hooks テストが混在 |
| C. 両方（リンク or 参照） | A + B の参照関係 | 柔軟 | 複雑、メンテナンス負担 |

### 比較

| 評価軸 | A. .claude/hooks/tests/ | B. tests/test_hooks/ |
|--------|------------------------|---------------------|
| LAM v4.4.1 との整合性 | ◎（同一配置） | △ |
| 既存 pytest インフラの活用 | △（設定変更が必要） | ◎（testpaths 追加のみ） |
| `pytest` 単発実行 | △（`--testpaths` 指定 or 設定変更） | ◎（testpaths に追加すれば自動） |
| カバレッジ集計 | △（`--cov` の対象外になる可能性） | ◎（既存 `--cov=kage_shiki` の外だが hooks は別モジュール） |
| 関心の分離 | ◎（インフラコードのテストを分離） | △（アプリテストと混在） |
| conftest.py の衝突 | なし | 既存 `tests/conftest.py` との調整必要 |

### pyproject.toml の設定変更（選択肢 A の場合）

```toml
[tool.pytest.ini_options]
testpaths = ["tests", ".claude/hooks/tests"]
```

### conftest.py の設計

v4.4.1 の `conftest.py` 設計を参考に、影式向けに調整:

```python
# .claude/hooks/tests/conftest.py (選択肢A) または
# tests/test_hooks/conftest.py (選択肢B)

import os
import sys
from pathlib import Path
import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent  # .claude/hooks/
PROJECT_ROOT = HOOKS_DIR.parent.parent              # プロジェクトルート

@pytest.fixture(autouse=True)
def _set_project_root(tmp_path, monkeypatch):
    """全テストで LAM_PROJECT_ROOT を tmp_path に設定する。"""
    # 必要なディレクトリを作成
    (tmp_path / ".claude" / "logs").mkdir(parents=True)
    (tmp_path / ".claude" / "hooks").mkdir(parents=True)
    monkeypatch.setenv("LAM_PROJECT_ROOT", str(tmp_path))
    return tmp_path

@pytest.fixture
def project_root(tmp_path):
    """tmp_path ベースのプロジェクトルートを返す。"""
    (tmp_path / ".claude" / "logs").mkdir(parents=True)
    return tmp_path

@pytest.fixture
def hooks_on_syspath():
    """hooks ディレクトリを sys.path に追加する。"""
    if str(HOOKS_DIR) not in sys.path:
        sys.path.insert(0, str(HOOKS_DIR))
    yield
    if str(HOOKS_DIR) in sys.path:
        sys.path.remove(str(HOOKS_DIR))
```

### テストファイル構成

| ファイル | テスト数（目標） | 対象 |
|---------|---------------|------|
| `conftest.py` | — | 共通 fixtures |
| `test_hook_utils.py` | 15+ | `_hook_utils.py` の全関数 |
| `test_pre_tool_use.py` | 8+ | 権限等級判定、out-of-root、AUDITING PG |
| `test_post_tool_use.py` | 10+ | JUnit XML パース、TDD ログ、doc-sync-flag |
| `test_stop_hook.py` | 8+ | 収束判定、pm_pending、Issue 再発 |
| `test_pre_compact.py` | 4+ | セクション更新、フォールバックログ |
| `test_loop_integration.py` | 7+ | ループ全体の統合シナリオ |
| **合計** | **52+** | — |

### 決定: **A. `.claude/hooks/tests/` に配置し、`testpaths` に追加**

**根拠**:

1. **関心の分離**: hooks は影式アプリ（`kage_shiki`）とは独立した CI/CD インフラ。テストも分離すると役割が明確になる
2. **LAM テンプレートとの整合性**: v4.4.1 の配置を踏襲することで、将来の移行差分が最小化される
3. **pytest への統合**: `testpaths` に `.claude/hooks/tests` を追加することで `pytest` 単発で全テストが実行される。コストは `pyproject.toml` の 1 行変更のみ
4. **conftest.py 衝突回避**: 既存の `tests/conftest.py`（影式アプリのフィクスチャ）との干渉がない

**pyproject.toml の変更**:

```toml
[tool.pytest.ini_options]
testpaths = ["tests", ".claude/hooks/tests"]
addopts = "--cov=kage_shiki --cov-report=term-missing --junitxml=.claude/test-results.xml"
```

**カバレッジの扱い**: `--cov=kage_shiki` は `kage_shiki` モジュールのみを対象とする。hooks のカバレッジは別途 `pytest .claude/hooks/tests/ --cov=.claude/hooks` で取得する（日常的には不要）。

---

## リスクと対策

| # | リスク | 影響度 | 発生確率 | 対策 |
|---|--------|--------|---------|------|
| R1 | `hookSpecificOutput` の形式が公式仕様と異なる | 高（PM 判定が機能しない） | 中 | 実装前に公式ドキュメント確認を必須条件化。旧形式 (`decision: block`) へのフォールバックを準備する |
| R2 | JUnit XML ファイルが生成されない環境での post-tool-use.py の挙動 | 中（TDD ログが記録されない） | 低（`pytest` 実行時は常に生成） | XML ファイル不存在時は早期 return（ログスキップ）で安全に処理する |
| R3 | `_hook_utils.py` リネームで既存 hook が import エラーになる | 高（全 hook が停止） | 高（リネームと import 変更を同時に行わないと発生） | リネームと全 hook の import 変更を **1 コミット** でアトミックに実施する |
| R4 | `.claude/hooks/tests/` を `testpaths` に追加した際に hook テストが kage_shiki のカバレッジを下げる | 低 | 低 | hook テストは `kage_shiki` モジュールを import しないため、カバレッジに影響しない |
| R5 | lam-stop-hook.py の大幅変更による Green State 判定の誤動作 | 高（自律ループの誤停止 or 無限ループ） | 中 | 変更前後の動作を `test_stop_hook.py` で検証する。段階的に機能を追加し、各段階でテストを実行する |
| R6 | シークレットスキャンがソースコードの正規のパターン（test データ等）を誤検出する | 中（不要なエスカレーション） | 中 | 安全パターン除外（`\btest\b \bmock\b \bexample\b` 等）を確実に実装する。初回実行時に誤検出数を確認して調整する |
| R7 | pyproject.toml の `addopts` 変更で CI/CD 環境が壊れる | 高 | 低（影式は CI なし） | 影式はローカル開発のみのため影響は限定的。変更後に `pytest` を実行して確認する |
| R8 | `pm_pending` フラグが pre-tool-use.py から lam-stop-hook.py に伝わらない | 中（ループが止まらない） | 中 | フラグの書き込み（pre-tool-use.py 側）と読み取り（lam-stop-hook.py 側）の両方をテストする |

### ロールバック計画

段階的な移行を行うため、各段階でロールバック可能とする:

1. **settings.json 変更（判断5）**: git revert で即時ロールバック可能。hooks の動作に影響なし
2. **`_hook_utils.py` リネーム（判断1）**: リネーム + import 変更を1コミット。`git revert` で一括復元
3. **JUnit XML 移行（判断2）**: `pyproject.toml` の `addopts` から `--junitxml` を削除。`post-tool-use.py` の XML パースロジックを除去
4. **lam-stop-hook.py 拡張（判断3）**: 機能ごとに独立したコミット。問題のある機能のみ revert 可能
5. **テストスイート（判断6）**: テストの追加は影式アプリの動作に影響しない。削除は容易

---

## 影式固有の考慮事項まとめ

移行全体を通じて保持する影式固有の設定:

| 項目 | 値 | 理由 |
|------|-----|------|
| hooks コマンド | `python`（`python3` ではなく） | Windows では `python3` が存在しない場合がある |
| テストコマンド | `python -m pytest`（`pytest` のみではなく） | 影式での標準実行形式 |
| lint ツール | `ruff`（ハードコード） | 影式は Python 単一言語 |
| PM パターン: `docs/internal/` | 維持 | 影式固有の SSOT ディレクトリ |
| PM パターン: `pyproject.toml` | 維持 | 影式固有の設定ファイル |
| allow: `git status *` | 維持 | 引数付き git status の日常使用 |
| allow: `pip show *` | 維持 | 依存パッケージ確認の日常使用 |
| stdin 制限: 1MB | 維持 | セキュリティ観点（v4.4.1 では削除されたが影式では保持） |
| `notify-sound.py` | 維持（変更不要） | 影式固有フック。`_hook_utils` を import しない単独スクリプトのため hooks 移行の影響なし。Phase 4 の hooks 差分適用時に誤削除しないこと |

---

## 実装順序の推奨

設計の判断を踏まえた実装の推奨順序:

### Wave A: セキュリティ修正（即時適用、リスク低）
1. `settings.json`: find コマンドの deny パターン追加 + allow→ask 移動 + `python *` を ask に追加

### Wave B: 基盤整備（高優先度）
2. `_hook_utils.py` リネーム + 新 API 追加（`get_project_root`, `read_stdin_json`, `log_entry`, `atomic_write_json`, `run_command` 等）
3. 全 hook の import 文を `_hook_utils` に変更

### Wave C: バグ修正（高優先度）
4. `pyproject.toml`: `--junitxml` オプション追加
5. `.gitignore`: `.claude/test-results.xml` 追加
6. `.claude/rules/test-result-output.md` 新規作成
7. `post-tool-use.py`: JUnit XML 方式に移行（`_parse_junit_xml` 追加、FAIL→PASS 通知追加）

### Wave D: 品質改善（中優先度）
8. `pre-tool-use.py`: out-of-root 検出、AUDITING PG 特別処理、PM パターン厳密化、応答形式更新（要公式確認）
9. `lam-stop-hook.py`: `convergence_reason`、`pm_pending`、`fullscan_pending`、Issue 再発チェック、ループログ保存、状態クリーンアップ、CWD 検証、シークレットスキャン
10. `pre-compact.py`: セクション内チェック修正、フォールバックログ追加

### Wave E: テスト基盤（低優先度）
11. `.claude/hooks/tests/` ディレクトリ作成
12. `conftest.py` + テストスイート（52+ テスト）作成
13. `pyproject.toml`: `testpaths` に `.claude/hooks/tests` 追加

---

## ADR 候補

以下の決定事項は正式な ADR として記録を推奨:

1. **`hookSpecificOutput` 形式の採用**
   - 選択肢: `decision: block` / `hookSpecificOutput: permissionDecision: ask`
   - 推奨: `hookSpecificOutput` 形式
   - 条件: 公式ドキュメント確認後に確定

2. **JUnit XML によるテスト結果検出**
   - 選択肢: exitCode 方式（継続）/ JUnit XML 方式（移行）
   - 推奨: JUnit XML 方式
   - 理由: exitCode 方式の構造的欠陥（PostToolUse stdin に exitCode が存在しない）

3. **ツール検出のハードコード維持**
   - 選択肢: 自動検出（v4.4.1）/ ハードコード（維持）
   - 推奨: ハードコード
   - 理由: 影式は Python 単一言語プロジェクト（YAGNI 原則）
