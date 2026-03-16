# LAM v4.4.1 → v4.5.0 Diff 分析: hooks/, analyzers/, settings.json

> 生成日: 2026-03-16
> 対象: `.claude/hooks/`, `.claude/hooks/analyzers/`, `.claude/settings.json`, `.gitignore`

---

## 1. 既存 hooks ファイル別差分

### 1.1 `_hook_utils.py`

| 関数/要素 | 影式 (v4.4.1) | LAM v4.5.0 | 差分 |
|-----------|--------------|------------|------|
| docstring | `LAM v4.4.1 準拠 + 影式固有調整（1MB stdin 制限）` | `対応仕様: design.md Section 2` | 記述のみ |
| import | `contextlib` を追加 import | `contextlib` なし | **影式固有追加** |
| `_MAX_STDIN_BYTES` | 定義あり (`1 * 1024 * 1024`) | **なし** | **影式固有** |
| `now_utc_iso8601()` | `datetime.UTC` 使用 | `datetime.timezone.utc` 使用 | 影式は Python 3.12+ 前提で短縮形を採用。**互換性あり** |
| `get_project_root()` | 同一 | 同一（コメント量が LAM 版は多い） | 差分なし |
| `read_stdin_json()` | `sys.stdin.buffer.read(_MAX_STDIN_BYTES)` でバイト制限あり | `sys.stdin.read()` 制限なし | **影式固有セキュリティ対策（保持必須）** |
| `get_tool_name()` | 同一 | 同一 | 差分なし |
| `get_tool_input()` | 同一 | 同一 | 差分なし |
| `get_tool_response()` | 同一 | 同一 | 差分なし |
| `normalize_path()` | `p.resolve().relative_to(project_root.resolve())` + `replace("\\", "/")` | `p.relative_to(project_root)` (resolve なし、\\ 変換なし) | **影式版が Windows 対応で改善済み。保持必須** |
| `log_entry()` | 同一 | 同一 | 差分なし |
| `atomic_write_json()` | `contextlib.suppress(OSError)` 使用、`dir=str(path.parent)` (str 変換)、`os.replace(tmp_path, str(path))` (str 変換) | `try/except OSError: pass`、`dir=path.parent` (Path直接)、`os.replace(tmp_path, path)` (Path直接) | 影式版は明示的 str 変換 + contextlib。**機能同一、スタイル差** |
| `run_command()` | 同一 | 同一 | 差分なし |
| `safe_exit()` | 同一 | 同一 | 差分なし |

**結論**: 影式版の `read_stdin_json()` のバイト制限、`normalize_path()` の Windows 対応（resolve + backslash 変換）は保持必須。LAM 4.5.0 との差分は影式固有改善のみで、LAM 側に新規追加関数はない。

---

### 1.2 `pre-tool-use.py`

| 関数/要素 | 影式 (v4.4.1) | LAM v4.5.0 | 差分 |
|-----------|--------------|------------|------|
| `_READ_ONLY_TOOLS` | 同一 | 同一 | 差分なし |
| `_AUDITING_PG_COMMANDS` | 同一（ただし LAM 版はコメントが長い） | 同一 + ブラックリスト補足コメント | 差分なし |
| **`_PG_BLACKLISTED_ARGS`** | **なし** | **定義あり**（`--config`, `--settings` 等 10 項目） | **LAM 4.5.0 新規追加**。PG コマンドの引数に悪意あるオプションが含まれないかチェック |
| `_PM_PATTERNS` | 5 パターン + 影式固有 2 項目 (`docs/internal/`, `pyproject.toml`) = **7 項目** | 5 パターン（影式固有なし） | **影式固有 PM パターン保持必須** |
| `_SE_PATTERNS` | 同一 | 同一 | 差分なし |
| `_determine_level_and_reason()` | PM パターン: `return "PM", f"protected path: {normalized}"` | PM パターン: `return "PM", reason` | 影式版は `normalized` を理由に含める（デバッグ容易）。**保持推奨** |
| `_determine_level_and_reason()` AUDITING PG | 単純なプレフィックスマッチ | プレフィックスマッチ + **`_PG_BLACKLISTED_ARGS` チェック追加** | **LAM 4.5.0 新機能。採用必須** |
| `_read_current_phase()` | 同一 | 同一 | 差分なし |
| `main()` read-only | ログ記録なし（即 exit） | `log_entry(... "PG", ... "read-only tool")` | LAM 版は read-only もログ出力。**トレードオフ: ログ量 vs 可視性** |
| `main()` PM 出力 | `"[PM] {reason} — 承認が必要です"` | `"PM級変更です。承認してください: {target}"` | 表現差のみ |

**結論**: LAM 4.5.0 の `_PG_BLACKLISTED_ARGS` チェックは**セキュリティ強化として採用必須**。影式固有の PM パターン 2 項目（`docs/internal/`, `pyproject.toml`）、`normalize_path` のパス含み理由文字列は保持。

---

### 1.3 `post-tool-use.py`

| 関数/要素 | 影式 (v4.4.1) | LAM v4.5.0 | 差分 |
|-----------|--------------|------------|------|
| `_TEST_CMD_PATTERN` | `pytest\|python\s+-m\s+pytest\|npm test\|go test` | `pytest\|npm test\|go test\|make test` | 影式は `python -m pytest` を含む、LAM は `make test` を含む。**両方マージ推奨** |
| `_get_test_cmd_label()` | `pytest`/`npm test`/`go test` | + `make test` | LAM 追加分を採用 |
| `_parse_junit_xml()` | `except Exception` で広く catch | `except ET.ParseError` + `except OSError` で個別 catch | LAM 版が厳密。**LAM 版を採用推奨** |
| **`_read_prev_result()`** | **なし**（`_handle_test_result` 内にインライン） | **関数として抽出** | LAM 版のリファクタリング。可読性向上 |
| **`_record_fail()`** | **なし**（`_handle_test_result` 内にインライン） | **関数として抽出** | LAM 版のリファクタリング。可読性向上 |
| **`_record_pass()`** | **なし**（`_handle_test_result` 内にインライン） | **関数として抽出** | LAM 版のリファクタリング。可読性向上 |
| `_handle_test_result()` | `is_failure_event` パラメータなし | **`is_failure_event` パラメータあり**（PostToolUseFailure 対応） | **LAM 4.5.0 新機能** |
| `_handle_test_result()` XML パース | 前回結果を直接 `prev_result.startswith("fail")` で判定 | `_read_prev_result()` 関数に分離 | リファクタリング |
| `_handle_doc_sync_flag()` | 同一 | `contextlib.suppress` を `try/except` に | スタイル差のみ |
| `_handle_loop_log()` | 引数に `exit_code` **なし** | 引数に `exit_code` **あり**（event dict に含める） | **LAM 4.5.0 追加フィールド** |
| `main()` | `hook_event_name` 取得なし | `hook_event_name = data.get("hook_event_name", "")` 取得 | **PostToolUseFailure 対応** |
| `main()` FAIL 判定 | なし | `is_failure = hook_event_name == "PostToolUseFailure"` | **LAM 4.5.0 新機能** |
| `main()` loop log | `_handle_loop_log(tool_name, command, file_path, ...)` | `_handle_loop_log(tool_name, command, file_path, "", ...)` | exit_code 引数追加（空文字） |

**結論**: LAM 4.5.0 の主要変更は (1) `PostToolUseFailure` イベント対応、(2) `_record_fail`/`_record_pass` の関数分離、(3) `_handle_loop_log` への `exit_code` 追加。いずれも採用推奨。影式固有の `python -m pytest` パターンは保持。

---

### 1.4 `lam-stop-hook.py`

| 関数/要素 | 影式 (v4.4.1) | LAM v4.5.0 | 差分 |
|-----------|--------------|------------|------|
| **全体設計** | **Green State 判定あり**（G1:テスト, G2:lint, G5:セキュリティを stop-hook 内で実行） | **安全ネットのみ**（Green State 判定なし、block して引き戻すだけ） | **根本的な設計差異** |
| import | `contextlib`, `re`, `shutil` 等多数 | `datetime`, `json`, `os`, `time` 等最小限 | 影式の追加 import は Green State 判定用 |
| `_SCAN_EXCLUDE_DIRS` | 定義あり（シークレットスキャン用） | **なし** | 影式固有 |
| `_SECRET_PATTERN`, `_SAFE_PATTERN` | 定義あり | **なし** | 影式固有 |
| `_log()` | `contextlib.suppress(Exception)` | `try/except + sys.stderr.write` | スタイル差 |
| `_save_loop_log()` | 同一構造 | 同一構造 | 差分なし |
| `_cleanup_state_file()` | `contextlib.suppress` | `try/except` | スタイル差 |
| `_validate_check_dir()` | **あり**（パストラバーサル防止） | **なし** | 影式固有セキュリティ対策 |
| `_run_tests()` | **あり**（`sys.executable -m pytest`） | **なし** | 影式固有（Green State G1） |
| `_run_lint()` | **あり**（`sys.executable -m ruff`） | **なし** | 影式固有（Green State G2） |
| `_run_security()` | **あり**（pip-audit + シークレットスキャン） | **なし** | 影式固有（Green State G5） |
| `_check_issue_recurrence()` | **あり** | **なし** | 影式固有エスカレーション |
| `_check_unanalyzed_tdd_patterns()` | **あり** | **なし** | 影式固有通知B |
| STEP 構成 | 7 STEP（再帰防止→上限→コンテキスト→Green State→総合判定→エスカレーション→継続） | 5 STEP（再帰防止→状態確認→上限→コンテキスト→block） | 影式が大幅に拡張 |
| `_check_recursion_and_state()` | `pm_pending` チェックあり | `pm_pending` チェックあり | 同一 |
| `_check_max_iterations()` | 同一 | 同一 | 差分なし |
| `_check_context_pressure()` | `datetime.UTC` 使用 | `datetime.timezone.utc` 使用 | Python 3.12+ 短縮形（影式固有） |
| `main()` STEP 4-7 | Green State 判定 + エスカレーション + 条件付き block/stop | 無条件 block（安全ネット） | **影式が独自に Green State 判定を実装** |

**結論**: 影式の `lam-stop-hook.py` は LAM 4.5.0 の安全ネット設計を大幅に拡張し、Green State 判定・エスカレーション・セキュリティチェックを stop-hook 内で実行する独自設計。LAM 4.5.0 は「ループ制御は /full-review（Claude 側）が行い、Stop hook は安全ネット」という設計。

**移行判断**: 影式の独自拡張（Green State 判定）を保持するか、LAM 4.5.0 の設計思想（安全ネット限定）に戻すかは PM 級判断。LAM 4.5.0 の STEP 1-4（再帰防止・状態確認・上限・コンテキスト）は影式と同一のため、共通部分の更新は不要。

---

### 1.5 `pre-compact.py`

| 関数/要素 | 影式 (v4.4.1) | LAM v4.5.0 | 差分 |
|-----------|--------------|------------|------|
| `write_pre_compact_flag()` | 同一 | 同一 | 差分なし |
| `update_session_state()` | 同一 | 同一 | 差分なし |
| `fallback_log()` | 同一 | 同一 | 差分なし |
| `backup_loop_state()` | 同一 | 同一 | 差分なし |
| `main()` | 同一 | 同一 | 差分なし |

**結論**: 差分なし。移行作業不要。

---

## 2. 新規 analyzers/ モジュール概要

### 2.1 ディレクトリ構成

```
.claude/hooks/analyzers/
├── __init__.py          (空ファイル)
├── base.py              (ABC + データモデル + Registry)
├── config.py            (ReviewConfig)
├── orchestrator.py      (バッチ並列 + プロンプト生成)
├── scale_detector.py    (スケール判定)
├── run_pipeline.py      (Phase 0 統合)
├── card_generator.py    (概要カード + 依存グラフ + 契約カード)
├── chunker.py           (AST チャンキング)
├── reducer.py           (重複排除 + 命名規則チェック)
├── state_manager.py     (永続化管理)
├── python_analyzer.py   (Python: ruff + bandit + ast)
├── javascript_analyzer.py (JS/TS: eslint + npm audit)
└── rust_analyzer.py     (Rust: cargo clippy + cargo audit)
```

### 2.2 モジュール別概要

| モジュール | 主要クラス/関数 | 責務 | 外部依存 |
|-----------|----------------|------|---------|
| `base.py` | `Issue`, `ASTNode`, `LanguageAnalyzer`(ABC), `AnalyzerRegistry`, `ToolRequirement`, `ToolNotFoundError` | データモデル定義 + Analyzer プラグイン基盤 | なし（標準ライブラリのみ） |
| `config.py` | `ReviewConfig` | `.claude/review-config.json` からの設定読み込み | なし |
| `orchestrator.py` | `ReviewResult`, `BatchResult`, `batch_chunks()`, `build_review_prompt()`, `parse_llm_issues()`, `order_chunks_by_topo()`, `build_review_prompt_with_contracts()`, `order_files_by_topo()`, `collect_results()` | チャンクのバッチ分割、Agent プロンプト生成、LLM 出力パース、トポロジカル順序付け | `analyzers.base`, `analyzers.chunker`, `analyzers.card_generator` |
| `scale_detector.py` | `PlanStatus`, `ScaleDetectionResult`, `detect_scale()`, `format_scale_detection()` | プロジェクト規模に基づく Plan A-D の有効化判定 | `analyzers.config`, `analyzers.run_pipeline` |
| `run_pipeline.py` | `Phase0Result`, `count_lines()`, `should_enable_static_analysis()`, `run_phase0()` | Phase 0 静的解析パイプライン統合 | `analyzers.base`, `analyzers.config`, 各 Analyzer |
| `card_generator.py` | `FileCard`, `ModuleCard`, `ContractCard`, `generate_file_cards()`, `generate_module_cards()`, `detect_circular_dependencies()`, `build_topo_order()`, `analyze_impact()`, `classify_impact_for_cards()`, `detect_module_naming_violations()`, `collect_spec_drift_context()` | 概要カード生成（Layer 1-3）、依存グラフ構築、契約カード、影響範囲分析 | `analyzers.base`, `analyzers.reducer`, `graphlib`(標準) |
| `chunker.py` | `Chunk`, `chunk_file()`, `count_tokens()` | tree-sitter ベースの AST チャンキング | `tree_sitter`, `tree_sitter_python`（**外部依存**） |
| `reducer.py` | `deduplicate_issues()`, `classify_name()`, `check_naming_consistency()` | Issue 重複排除、命名規則一貫性チェック | `analyzers.base` |
| `state_manager.py` | `save_issues()`, `load_issues()`, `save_ast_map()`, `load_ast_map()`, `generate_summary()`, `compute_file_hash()`, `save_chunks_index()`, `load_chunks_index()`, `save_dependency_graph()`, `load_dependency_graph()` | `.claude/review-state/` 配下の永続化管理 | `analyzers.base`, `analyzers.chunker` |
| `python_analyzer.py` | `PythonAnalyzer` | Python 言語: ruff(lint) + bandit(security) + ast(parse) | `ruff`, `bandit`（**外部 CLI ツール**） |
| `javascript_analyzer.py` | `JavaScriptAnalyzer` | JS/TS 言語: eslint(lint) + npm audit(security) | `npx`, `npm`（**外部 CLI ツール**） |
| `rust_analyzer.py` | `RustAnalyzer` | Rust 言語: clippy(lint) + cargo audit(security) | `cargo`（**外部 CLI ツール**） |

### 2.3 影式プロジェクトでの必要性判断

影式は **Python 単一言語プロジェクト**（Medium 規模）であるため:

- **必須**: `base.py`, `config.py`, `run_pipeline.py`, `python_analyzer.py`, `state_manager.py`, `reducer.py`
- **将来有用**: `orchestrator.py`, `chunker.py`, `card_generator.py`, `scale_detector.py`（規模拡大時）
- **不要**: `javascript_analyzer.py`, `rust_analyzer.py`（ただし LAM テンプレートとして配置しても害なし）

---

## 3. テスト比較

### 3.1 現行テスト（影式 `tests/test_hooks/`）

| ファイル | 対象 |
|---------|------|
| `conftest.py` | テスト共通フィクスチャ |
| `test_hook_utils.py` | `_hook_utils.py` |
| `test_pre_tool_use.py` | `pre-tool-use.py` |
| `test_post_tool_use.py` | `post-tool-use.py` |
| `test_stop_hook.py` | `lam-stop-hook.py` |
| `test_pre_compact.py` | `pre-compact.py` |
| `test_integration.py` | hook 間統合テスト |

### 3.2 LAM 4.5.0 hooks テスト（`.claude/hooks/tests/`）

| ファイル | 対象 | 影式との差分 |
|---------|------|------------|
| `conftest.py` | テスト共通フィクスチャ | 比較必要 |
| `test_hook_utils.py` | `_hook_utils.py` | 比較必要 |
| `test_pre_tool_use.py` | `pre-tool-use.py` | `_PG_BLACKLISTED_ARGS` テスト追加あり |
| `test_post_tool_use.py` | `post-tool-use.py` | `PostToolUseFailure` テスト追加あり |
| `test_stop_hook.py` | `lam-stop-hook.py` | 安全ネット設計のテスト（Green State なし） |
| `test_loop_integration.py` | ループ統合テスト | 影式の `test_integration.py` と比較必要 |

**注意**: 影式の `test_pre_compact.py` に対応するテストが LAM 4.5.0 にはない。

**テスト配置差異**: LAM 4.5.0 は `.claude/hooks/tests/` に配置（hooks と同階層）。影式は `tests/test_hooks/` に配置（プロジェクトルートの tests/ 配下）。影式の配置方式を保持する。

### 3.3 LAM 4.5.0 analyzer テスト（`.claude/hooks/analyzers/tests/`）

| ファイル | 対象 |
|---------|------|
| `conftest.py` | Analyzer テスト共通フィクスチャ |
| `test_base.py` | `base.py`（Issue, ASTNode, LanguageAnalyzer） |
| `test_registry.py` | `AnalyzerRegistry` |
| `test_config.py` | `ReviewConfig` |
| `test_python_analyzer.py` | `PythonAnalyzer` |
| `test_javascript_analyzer.py` | `JavaScriptAnalyzer` |
| `test_rust_analyzer.py` | `RustAnalyzer` |
| `test_run_pipeline.py` | `run_pipeline.py` |
| `test_orchestrator.py` | `orchestrator.py` |
| `test_chunker.py` | `chunker.py` |
| `test_reducer.py` | `reducer.py` |
| `test_state_manager.py` | `state_manager.py` |
| `test_card_generator.py` | `card_generator.py` |
| `test_integration_pipeline.py` | Phase 0 統合テスト |
| `test_e2e_review.py` | E2E レビューテスト |
| `fixtures/e2e/` | E2E テスト用サンプルコード |

**移行判断**: analyzer テストを導入する場合は `tests/test_analyzers/` 配下に配置（影式テスト構成に準拠）。

---

## 4. settings.json 差分

### 4.1 permissions.allow

| 項目 | 影式 | LAM v4.5.0 | 差分 |
|------|------|------------|------|
| `Bash(git status *)` | あり | **なし** | 影式固有追加 |
| `Bash(pip show *)` | あり | **なし** | 影式固有追加 |
| `Bash(python -m pytest *)` | なし | **あり** | LAM 4.5.0 新規 |
| `Bash(python3 -m pytest *)` | なし | **あり** | LAM 4.5.0 新規 |
| `Bash(python3 -c *)` | なし | **あり** | LAM 4.5.0 新規 |
| `Bash(python -c *)` | なし | **あり** | LAM 4.5.0 新規 |

### 4.2 permissions.deny

差分なし（同一）。

### 4.3 permissions.ask

| 項目 | 影式 | LAM v4.5.0 | 差分 |
|------|------|------------|------|
| `Bash(git pull *)` | あり | あり | 同一 |
| `Bash(git fetch *)` | あり | あり | 同一 |
| `Bash(git clone *)` | あり | あり | 同一 |
| `Bash(python *)` | なし | **あり** | LAM 4.5.0 新規（影式は settings.local.json に委任） |
| `Bash(find *)` | 順序が ask 末尾 | **順序が ask 先頭** | LAM 版は先頭配置 |

### 4.4 hooks 設定

| フック | 影式 | LAM v4.5.0 | 差分 |
|-------|------|------------|------|
| コマンドプレフィックス | `python` | `python3` | **影式は Windows 環境のため `python` を使用**（保持必須） |
| **PostToolUseFailure** | **なし** | **あり**（matcher: Bash、post-tool-use.py を実行） | **LAM 4.5.0 新規イベント** |
| PreToolUse | あり | あり | 同一（コマンドプレフィックス差異のみ） |
| PostToolUse | あり (matcher: `Edit\|Write\|Bash`) | あり (matcher: `Edit\|Write\|Bash`) | 同一 |
| Stop | あり | あり | 同一 |
| PreCompact | あり | あり | 同一 |

**結論**: LAM 4.5.0 の `PostToolUseFailure` イベント登録が最重要変更。`python3` → `python` の差異は影式固有として保持。

---

## 5. .gitignore 差分

| 項目 | 影式 | LAM v4.5.0 | 差分 |
|------|------|------------|------|
| Node.js セクション | なし | `node_modules/`, `npm-debug.log*` 等あり | LAM はマルチ言語対応 |
| `.env` | `# Environment` セクションに `.env` + `.env.local` | `# Node.js` セクションに `.env` + `.env.local` | 配置位置が異なるのみ |
| `!docs/memos/` | あり（docs/memos 選択的除外） | なし | **影式固有**（保持必須） |
| `!docs/memos/v4-update-plan/` | あり | なし | **影式固有** |
| `!docs/memos/v4-4-1-update-plan/` | あり | なし | **影式固有** |
| `docs/daily/` | あり | あり | 同一 |
| `.claude/test-results.xml` | あり | なし（`**/test-results.xml` で代替） | LAM 版はグロブパターン |
| `**/test-results.xml` | なし | あり | LAM 4.5.0 新規（より包括的） |
| `.claude/review-state/` | なし | **あり** | **LAM 4.5.0 新規**（analyzers の永続化ディレクトリ） |
| `last-test-result` | なし（`.claude/last-test-result` で記載） | **あり**（ルート直下にも） | LAM 追加 |
| `config.toml` | あり | なし | **影式固有** |
| `_reference/` | あり | あり | 同一 |
| `data/` | あり | あり | 同一 |

**結論**: `.claude/review-state/` の追加が必須。`**/test-results.xml` への変更は任意（現行でも機能する）。影式固有の `docs/memos` 除外、`config.toml` は保持。

---

## 6. 影式固有保持項目

以下の項目は LAM 4.5.0 に存在しないが、影式プロジェクトの要件として保持が必要:

### 6.1 hooks 固有

| 項目 | ファイル | 理由 |
|------|---------|------|
| `notify-sound.py` | `.claude/hooks/notify-sound.py` | 影式固有の通知音フック。LAM に存在しない |
| `_MAX_STDIN_BYTES` | `_hook_utils.py` | stdin バイト制限（セキュリティ対策） |
| `normalize_path()` の resolve + backslash 変換 | `_hook_utils.py` | Windows 対応 |
| `datetime.UTC`（Python 3.12+ 短縮形） | 複数ファイル | Python 3.12+ 前提 |
| PM パターン: `docs/internal/`, `pyproject.toml` | `pre-tool-use.py` | 影式固有の保護パス |
| Green State 判定（G1/G2/G5） | `lam-stop-hook.py` | 影式独自拡張（PM 級判断必要） |
| `_validate_check_dir()` | `lam-stop-hook.py` | パストラバーサル防止 |
| `_SCAN_EXCLUDE_DIRS` + `logs` 除外 | `lam-stop-hook.py` | シークレットスキャンのログ除外 |
| `sys.executable` 使用 | `lam-stop-hook.py` | ツール自動検出不使用（影式固有） |
| `python -m pytest` テストパターン | `post-tool-use.py` | 影式のテスト実行方式 |

### 6.2 settings.json 固有

| 項目 | 理由 |
|------|------|
| `python`（`python3` ではなく） | Windows 環境では `python3` コマンドがない |
| `Bash(git status *)` | `git status` のバリエーション対応 |
| `Bash(pip show *)` | パッケージ情報確認用 |
| `Bash(python *)` を ask **に入れない** | `settings.local.json` に委任（開発者ごとの差異を許容） |

### 6.3 .gitignore 固有

| 項目 | 理由 |
|------|------|
| `docs/memos` 選択的除外 | LAM リファレンス資材の管理 |
| `config.toml` | ユーザー設定ファイル |
| `# pytest` セクション | htmlcov, .coverage 除外 |

---

## 7. マイグレーションアクション一覧

### 7.1 必須（Critical）

| # | アクション | 対象ファイル | 理由 |
|---|-----------|------------|------|
| C-1 | `PostToolUseFailure` イベント登録を `settings.json` に追加 | `.claude/settings.json` | テスト失敗の確実な検出 |
| C-2 | `_PG_BLACKLISTED_ARGS` チェックを `pre-tool-use.py` に追加 | `.claude/hooks/pre-tool-use.py` | セキュリティ強化 |
| C-3 | `PostToolUseFailure` 対応を `post-tool-use.py` に追加 | `.claude/hooks/post-tool-use.py` | `is_failure_event` パラメータ + `hook_event_name` 取得 |
| C-4 | `.claude/review-state/` を `.gitignore` に追加 | `.gitignore` | analyzers 永続化ディレクトリの除外 |

### 7.2 推奨（Warning）

| # | アクション | 対象ファイル | 理由 |
|---|-----------|------------|------|
| W-1 | `_parse_junit_xml()` の例外ハンドリングを個別 catch に変更 | `.claude/hooks/post-tool-use.py` | LAM 4.5.0 準拠のエラー処理厳密化 |
| W-2 | `_record_fail()` / `_record_pass()` / `_read_prev_result()` の関数分離 | `.claude/hooks/post-tool-use.py` | 可読性向上（LAM 4.5.0 リファクタリング） |
| W-3 | `_handle_loop_log()` に `exit_code` パラメータ追加 | `.claude/hooks/post-tool-use.py` | LAM 4.5.0 互換性 |
| W-4 | `make test` パターンを `_TEST_CMD_PATTERN` に追加 | `.claude/hooks/post-tool-use.py` | テストコマンド検出の拡張 |
| W-5 | `python -m pytest`, `python3 -m pytest`, `python -c`, `python3 -c` を `settings.json` allow に追加 | `.claude/settings.json` | LAM 4.5.0 準拠 |
| W-6 | `**/test-results.xml` パターンへの変更を検討 | `.gitignore` | より包括的な除外 |

### 7.3 analyzers 導入（PM 級判断必要）

| # | アクション | 備考 |
|---|-----------|------|
| A-1 | `analyzers/` ディレクトリの全体導入判断 | 影式は Medium 規模 Python プロジェクト。現時点で必須ではないが将来有用 |
| A-2 | 導入する場合: 全 13 ファイルをコピー | `__init__.py` 含む |
| A-3 | 導入する場合: テストを `tests/test_analyzers/` に配置 | 影式のテスト構成に準拠 |
| A-4 | 導入する場合: 外部依存（`tree-sitter`, `bandit`）の追加判断 | `pyproject.toml` への追加が PM 級 |
| A-5 | `javascript_analyzer.py`, `rust_analyzer.py` の配置判断 | 不要だが LAM テンプレートとして残す選択肢あり |

### 7.4 lam-stop-hook.py 設計判断（PM 級）

| # | アクション | 備考 |
|---|-----------|------|
| S-1 | 影式の Green State 判定を保持するか、LAM 4.5.0 の安全ネット設計に戻すか判断 | 現行は stop-hook 内で G1/G2/G5 を実行。LAM 4.5.0 は /full-review に委任 |
| S-2 | 保持する場合: LAM 4.5.0 の STEP 1-4 共通部分の差分がないことを確認 | 確認済み: 共通部分に差分なし |

### 7.5 rules/ 差分（参考）

LAM 4.5.0 で追加されたルールファイル:
- `code-quality-guideline.md`: 重要度分類と判断基準（Critical/Warning/Info の定義）
- `planning-quality-guideline.md`: PLANNING フェーズの品質基準（Requirements Smells, RFC 2119 等）
- 意思決定プロトコル: "Three Agents" → "MAGI System" に名称変更 + Reflection ステップ追加

これらは本 diff の対象外だが、hooks 移行と並行して rules/ の更新も検討が必要。
