# Hooks + Settings 詳細差分分析

**作成日**: 2026-03-13
**対象**: 影式 hooks (v4.0.1 移行時に作成) vs LAM v4.4.1 hooks

---

## 1. アーキテクチャレベルの差異

### 1.1 ファイル命名

| 項目 | 影式（現行） | v4.4.1 | 影響 |
|------|------------|--------|------|
| 共通ユーティリティ | `hook_utils.py` | `_hook_utils.py` | **全 hook の import 文変更が必要** |

影式は v4.0.1 移行時に `hook_utils.py` として作成。v4.4.1 では `_hook_utils.py`（アンダースコア接頭辞）に命名変更されている。
Python の慣例では `_` 接頭辞は「内部モジュール」を意味し、外部からの import を意図しないことを示す。

### 1.2 プロジェクトルート取得方式

| 項目 | 影式（現行） | v4.4.1 |
|------|------------|--------|
| 変数名 | `PROJECT_ROOT`（モジュール定数） | `get_project_root()`（関数） |
| テスト対応 | なし（固定パス） | `LAM_PROJECT_ROOT` 環境変数でオーバーライド可能 |
| 検証 | なし | `resolve()` + `is_dir()` 検証あり |

影式の `PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent` は固定値であり、テスト時に tmp_path に差し替えできない。
v4.4.1 の `get_project_root()` は環境変数 `LAM_PROJECT_ROOT` によるオーバーライドに対応し、hook テストスイートの基盤になっている。

### 1.3 stdin 読み取り

| 項目 | 影式（現行） | v4.4.1 |
|------|------------|--------|
| 関数名 | `read_stdin()` | `read_stdin_json()` |
| サイズ制限 | `MAX_STDIN_BYTES = 1MB` で `sys.stdin.read(1MB)` | 制限なし `sys.stdin.read()` |
| 空入力ガード | なし（json.loads が例外を投げる） | `if not raw.strip(): return {}` で明示ガード |
| 例外キャッチ | `except Exception` | `except (json.JSONDecodeError, ValueError, OSError)` — 具体型に限定 |

### 1.4 新規関数（v4.4.1 で追加、影式に存在しない）

| 関数 | 用途 | 影式での対応 |
|------|------|-------------|
| `get_tool_name(data)` | `data["tool_name"]` 抽出 | 各 hook で直接 `data.get("tool_name", "")` |
| `get_tool_input(data, key)` | `data["tool_input"][key]` 抽出（型安全） | 各 hook で直接アクセス |
| `get_tool_response(data, key, default)` | `data["tool_response"][key]` 抽出 | 各 hook で直接アクセス |
| `log_entry(log_file, level, source, message)` | TSV ログ追記（統一フォーマット） | 各 hook で独自実装 |
| `atomic_write_json(path, data)` | アトミック書き込み（Windows retry 付き） | 各 hook で独自実装（retry なし） |
| `run_command(args, cwd, timeout)` | subprocess ラッパー（shutil.which 解決） | lam-stop-hook.py で直接 `subprocess.run` |
| `now_utc_iso8601()` | タイムスタンプ統一 | `utc_now()` という名前で存在 |
| `safe_exit(code)` | sys.exit ラッパー | なし |

---

## 2. pre-tool-use.py 差分

### 2.1 構造的差異

| 項目 | 影式（現行） | v4.4.1 |
|------|------------|--------|
| 行数 | 128行 | 181行 |
| import 方式 | `import hook_utils` | `from _hook_utils import (get_project_root, ...)` |
| PM パターン定義 | `re.compile(r"docs/specs/")` | `re.compile(r"^docs/specs/.*\.md$")` — より厳密 |
| out-of-root 検出 | なし（プロジェクト外パスをそのまま返す） | `__out_of_root__/` マーカー付きで返し PM 級として捕捉 |
| AUDITING PG 特別処理 | なし | `_AUDITING_PG_COMMANDS` で lint/format コマンドを PG 許可 |
| docs/internal/ PM 判定 | `re.compile(r"docs/internal/")` あり | **なし**（v4.4.1 では汎用テンプレートなので不要） |
| pyproject.toml PM 判定 | `re.compile(r"pyproject\.toml$")` あり | **なし**（影式固有） |
| SE パターン | 定義なし（PM 以外は全て SE） | `_SE_PATTERNS` で `docs/`, `src/` を明示的に SE |
| ログフォーマット | `{utc_now()} [{level}] {tool_name} {path} -- {reason}` | TSV: `log_entry(level, tool_name, f"{target}\t\"{reason}\"")` |
| ログのエスケープ | なし | `target.replace("\t", " ").replace("\n", " ")` — タブ改行エスケープ |

### 2.2 PM パターン比較（正規表現）

| パス | 影式 | v4.4.1 | 差異 |
|------|------|--------|------|
| `docs/specs/*.md` | `r"docs/specs/"` (prefix match) | `r"^docs/specs/.*\.md$"` (.md のみ) | v4.4.1 は .md 以外を除外 |
| `docs/adr/*.md` | `r"docs/adr/"` | `r"^docs/adr/.*\.md$"` | 同上 |
| `docs/internal/` | `r"docs/internal/"` | **なし** | 影式固有（保持すべき） |
| `.claude/rules/` | `r"\.claude/rules/"` | `r"^\.claude/rules/.*\.md$"` | v4.4.1 は .md のみ |
| `.claude/settings*.json` | `r"\.claude/settings.*\.json$"` | `r"^\.claude/settings.*\.json$"` | ほぼ同じ（^追加） |
| `pyproject.toml` | `r"pyproject\.toml$"` | **なし** | 影式固有（保持すべき） |
| out-of-root | **なし** | `r"^__out_of_root__/"` | v4.4.1 新規セキュリティ |

### 2.3 応答形式の差異

| 項目 | 影式（現行） | v4.4.1 |
|------|------------|--------|
| PM 応答 | `{"decision": "block", "reason": "..."}` | `{"hookSpecificOutput": {"permissionDecision": "ask", "permissionDecisionReason": "..."}}` |

**重要**: v4.4.1 は Claude Code の公式 `hookSpecificOutput` → `permissionDecision` インターフェースを使用。
影式の `decision: block` は LAM v4.0.1 時点の実装だが、公式仕様は `permissionDecision: ask` の可能性がある。
**要確認**: upstream-first ルールに従い、Claude Code 公式ドキュメントで正しい形式を確認すべき。

---

## 3. post-tool-use.py 差分

### 3.1 TDD パターン検出方式（最大の差異）

| 項目 | 影式（現行） | v4.4.1 |
|------|------------|--------|
| **方式** | `exit_code` ベース（v1） | **JUnit XML** ベース（v2） |
| テスト結果判定 | `tool_response.exitCode` を使用 | `.claude/test-results.xml` をパース |
| 既知の問題 | **exitCode が Claude Code PostToolUse 入力に存在しない** | JUnit XML で解決済み |
| 失敗テスト名取得 | 不可（exit_code のみ） | XML の `<testcase>` + `<failure>` から取得 |
| ログフォーマット | `{utc_now()} \| FAIL \| {cmd} \| {stdout}` | TSV: `{timestamp}\tFAIL\t{test_cmd}\ttests=N failures=N\t"{summary}"` |
| FAIL→PASS 通知 | ログ記録のみ | `systemMessage` で `/retro` 推奨を出力 |

**重大な発見**: 影式の `exit_code = tool_response.get("exitCode")` は **Claude Code の PostToolUse 入力に exitCode フィールドが存在しない**ため、実質的に動作していない（常に `exit_code = 0` になる）。v4.4.1 では JUnit XML 方式に移行してこの問題を解決している。

### 3.2 テストコマンド判定パターン

| 項目 | 影式（現行） | v4.4.1 |
|------|------------|--------|
| パターン | `r"(?:^|\s)(?:pytest\|python\s+-m\s+pytest\|npm\s+test\|go\s+test)"` | `r"(^\|[\s])(pytest\|npm[\s]+test\|go[\s]+test)(?:[\s]\|$)"` |
| `python -m pytest` | マッチする | **マッチしない**（`pytest` だけで十分と判断） |
| go test 修正 | — | v4.3.0 で正規表現修正（`go test` が `google` にマッチしない等） |

### 3.3 新規関数（v4.4.1 のみ）

| 関数 | 用途 |
|------|------|
| `_parse_junit_xml(xml_path)` | JUnit XML パース → `{tests, failures, failed_names}` |
| `_is_test_command(command)` | テストコマンド判定 |
| `_get_test_cmd_label(command)` | 短縮ラベル取得 |
| `_append_to_tdd_log(tdd_log, line)` | TDD ログ追記 |
| `_handle_test_result(...)` | テスト結果処理メイン（JUnit XML 方式） |

### 3.4 ループログ（_handle_loop_log）

| 項目 | 影式（現行） | v4.4.1 |
|------|------------|--------|
| JSON パース失敗時 | `except: return`（空 dict で state を上書きするバグあり）| `except Exception: return` — 早期 return でループ状態を破壊しない |
| MAX_TOOL_EVENTS | 200 | 500 |
| exit_code 引数 | `exit_code: int`（整数） | `exit_code: str`（文字列、呼び出し元で `""` を渡す） |
| アトミック書き込み | 独自実装（try/except フォールバック） | `atomic_write_json()` 共通関数使用 |

### 3.5 doc-sync-flag

| 項目 | 影式（現行） | v4.4.1 |
|------|------------|--------|
| パス正規化 | `hook_utils.normalize_path(file_path)` | `normalize_path(file_path, project_root)` — project_root 引数追加 |
| アトミック書き込み | 独自 tempfile 実装 | ファイル append モード（`open("a")`） — 簡素化 |

---

## 4. lam-stop-hook.py 差分

### 4.1 規模の差異

| 項目 | 影式（現行） | v4.4.1 |
|------|------------|--------|
| 行数 | 225行 | 678行 |
| 関数数 | 8 | 20+ |

v4.4.1 は v4.0.1 の約 3 倍のサイズ。大幅な機能追加がある。

### 4.2 Green State チェック方式

| 項目 | 影式（現行） | v4.4.1 |
|------|------------|--------|
| テスト検出 | ハードコード（`sys.executable -m pytest`） | **自動検出** `_detect_test_framework()` — pyproject.toml/package.json/go.mod/Makefile |
| lint 検出 | ハードコード（`sys.executable -m ruff check .`） | **自動検出** `_detect_lint_tool()` — ruff/npm lint/eslint/Makefile |
| セキュリティ | `shutil.which("pip-audit")` → fallback `safety` | **自動検出** `_detect_security_tools()` — npm-audit + pip-audit/safety、pyproject.toml `[project]` チェック（誤検出防止） |
| pip-audit 誤検出 | あり（`[project]` セクションのない pyproject.toml でグローバル環境を監査） | **修正済み** — `[project]` or `[tool.poetry` or `requirements.txt` がある場合のみ |
| symlink | スキャンする（潜在的問題） | `scan_file.is_symlink()` でスキップ |
| timeout 扱い | 失敗扱い（`except subprocess.TimeoutExpired`） | 明示的に FAIL 扱い + WARN ログ |

### 4.3 ループ状態管理

| 項目 | 影式（現行） | v4.4.1 |
|------|------------|--------|
| 状態読み込みエラー | `except (json.JSONDecodeError, OSError): return None` | `except Exception as e: _log(ERROR, ...) → _stop()` — エラー詳細ログ |
| convergence_reason | なし（ループログに理由未記録） | `"green_state"`, `"max_iterations"`, `"context_exhaustion"`, `"escalation"` |
| pm_pending | なし | `state.get("pm_pending")` → 即座に停止 |
| fullscan_pending | なし | `state.get("fullscan_pending")` → Green State 達成後に fullscan サイクルを追加 |
| Issue 再発チェック | なし | `_check_issue_recurrence()` — 2サイクル連続 issues_fixed=0 でエスカレーション |
| TDD パターン通知 | なし | `_check_unanalyzed_tdd_patterns()` — 未分析パターンがあれば通知B |
| ループログ保存 | なし | `_save_loop_log()` — 停止時に `.claude/logs/loop-{timestamp}.txt` を生成 |
| 状態ファイルクリーンアップ | なし | `_cleanup_state_file()` — ループ終了時に `lam-loop-state.json` を削除 |

### 4.4 シークレットスキャン

| 項目 | 影式（現行） | v4.4.1 |
|------|------------|--------|
| スキャン範囲 | なし | `check_dir` 全体を再帰走査 |
| 対象拡張子 | — | `.py .js .ts .json .yaml .yml .toml .cfg .ini .sh .env` |
| 除外ディレクトリ | — | `.git node_modules __pycache__ .venv .pytest_cache` |
| パターン | — | `(password\|secret\|api_key\|...) = "値"` で 8文字以上 |
| 安全パターン除外 | — | `\btest\b \bspec\b \bmock\b \bexample\b ...` |
| 報告 | — | WARN ログに `file:line` (key=xxx) を記録 |
| サイズ制限 | — | 1MB 超のファイルをスキップ |

### 4.5 STEP 番号体系

| 影式（現行） | v4.4.1 |
|------------|--------|
| STEP 0-6 (docstring) | STEP 1-7 (docstring, main コメント, 関数名 全箇所統一) |

### 4.6 CWD 検証

| 項目 | 影式（現行） | v4.4.1 |
|------|------------|--------|
| CWD 検証 | なし（常に `PROJECT_ROOT` 使用） | `_validate_check_dir()` — パストラバーサル防止、PROJECT_ROOT 外はフォールバック |

---

## 5. pre-compact.py 差分

### 5.1 差異

| 項目 | 影式（現行） | v4.4.1 |
|------|------------|--------|
| 行数 | 71行 | 105行 |
| セクションヘッダ | `## PreCompact 発火記録` | `## PreCompact 発火` |
| 時刻行フォーマット | `最終発火: {timestamp}` | `- 時刻: {timestamp}` |
| 更新ロジック | `re.sub(r"最終発火: .+", ...)` — セクション外の同パターンも誤置換する可能性 | 行ごとにセクション内かチェックしてから更新（安全） |
| SESSION_STATE.md 非存在時 | 何もしない | `fallback_log()` でループログにフォールバック記録 |
| 終了方式 | `sys.exit(0)` | `safe_exit(0)` |

---

## 6. Hook テストスイート（v4.4.1 新規、影式に存在しない）

### 6.1 テストファイル一覧

| ファイル | テスト数 | 対象 |
|---------|---------|------|
| `conftest.py` | — | 共通 fixtures（project_root, hook_runner, hooks_on_syspath） |
| `test_hook_utils.py` | 21 | _hook_utils.py の全関数 |
| `test_pre_tool_use.py` | 8 | pre-tool-use.py の権限判定 |
| `test_post_tool_use.py` | 11 | post-tool-use.py の TDD/doc-sync/loop |
| `test_stop_hook.py` | 6 | lam-stop-hook.py の収束判定 |
| `test_loop_integration.py` | 7 | S-1〜S-5 統合シナリオ |
| **合計** | **53** | — |

### 6.2 テスト基盤の設計

- **`project_root` fixture**: `tmp_path` に `.claude/logs/` を作成。実プロジェクトへの汚染防止
- **`_set_project_root` autouse fixture**: `LAM_PROJECT_ROOT` 環境変数を自動設定
- **`hook_runner` fixture**: subprocess でフックを実行。環境変数の allowlist 制御あり
- **`hooks_on_syspath` fixture**: sys.path に hooks ディレクトリを追加（monkeypatch で自動復元）

### 6.3 影式での導入判断

影式は既に hook を使用しているが、**hook のテストは存在しない**。
v4.4.1 のテストスイートを取り込む場合:
- `conftest.py` の `project_root` fixture は影式のプロジェクト構造と整合する
- `_hook_utils.py` への命名変更が前提
- テストは `.claude/hooks/tests/` に配置（影式の `tests/` とは分離）
- pytest 実行時に自動的に収集される（`testpaths` 設定次第）

---

## 7. settings.json 差分

### 7.1 permissions 差分

| カテゴリ | 項目 | 影式（現行） | v4.4.1 | 対応 |
|---------|------|------------|--------|------|
| allow | `Bash(find *)` | **allow** | なし（ask へ移動） | **修正**: allow から削除 |
| allow | `Bash(git status *)` | allow | なし | 影式独自。維持可 |
| allow | `Bash(pip show *)` | allow | なし | 影式独自。維持可 |
| deny | `find * -delete *` | なし | **deny** | **追加**: セキュリティ修正 |
| deny | `find * -exec rm *` | なし | **deny** | **追加**: セキュリティ修正 |
| deny | `find * -exec chmod *` | なし | **deny** | **追加**: セキュリティ修正 |
| deny | `find * -exec chown *` | なし | **deny** | **追加**: セキュリティ修正 |
| ask | `Bash(find *)` | なし（allow にある） | **ask** | **追加**: allow から移動 |
| ask | `Bash(python *)` | なし | **ask** | **追加**: 実行制御 |

### 7.2 hooks 差分

| 項目 | 影式（現行） | v4.4.1 |
|------|------------|--------|
| Python コマンド | `python` | `python3` |
| 注意 | Windows では `python3` が存在しない場合がある | **影式は `python` を維持すべき** |

---

## 8. 移行作業の優先度と依存関係

### 即時適用（セキュリティ修正）

1. **settings.json**: find コマンドの deny パターン追加 + allow→ask 移動
2. **settings.json**: `Bash(python *)` を ask に追加

### 高優先度（機能バグ修正）

3. **post-tool-use.py**: exitCode ベース → JUnit XML ベースに移行（TDD パターン記録が動作していない）
4. **_hook_utils.py**: `hook_utils.py` → `_hook_utils.py` リネーム + 新関数追加
5. **全 hook**: import 文を `_hook_utils` に変更

### 中優先度（品質改善）

6. **pre-tool-use.py**: out-of-root 検出、AUDITING PG 特別処理、PM 応答形式の更新
7. **lam-stop-hook.py**: 自動検出、convergence_reason、pm_pending、fullscan_pending、シークレットスキャン
8. **pre-compact.py**: セクション内チェック、フォールバックログ

### 低優先度（テスト基盤）

9. **hooks/tests/**: テストスイート追加（53テスト）

### 依存関係

```
settings.json（独立、即時適用可）
    ↓ なし
_hook_utils.py リネーム + 新関数追加
    ↓ 全 hook が依存
pre-tool-use.py 更新
post-tool-use.py 更新（JUnit XML 方式）
    ↓ pytest --junitxml 設定が前提
lam-stop-hook.py 更新
pre-compact.py 更新
    ↓ 全 hook 更新完了後
hooks/tests/ 追加
```

---

## 9. 影式固有の考慮事項

### 保持すべきもの

- `docs/internal/` の PM 判定パターン
- `pyproject.toml` の PM 判定パターン
- `python`（`python3` ではなく）の hooks コマンド
- `Bash(git status *)`, `Bash(pip show *)` の allow
- `notify-sound.py` との共存

### JUnit XML 移行に必要な追加作業

- `pyproject.toml` に `addopts = "--junitxml=.claude/test-results.xml"` 追加
- `.gitignore` に `.claude/test-results.xml` 追加
- `.claude/rules/test-result-output.md` 新規作成

### hook テスト配置の判断

影式の `tests/` と `.claude/hooks/tests/` は別ディレクトリ。
影式の `pyproject.toml` の `testpaths` に `.claude/hooks/tests` を追加するか、
あるいは hook テストは別途 `pytest .claude/hooks/tests/` で実行する運用とするか要判断。
