# Phase 3 タスク: Hooks + analyzers/ + settings.json + .gitignore

**ステータス**: Draft
**対象設計**: `designs/01-design-hooks-analyzers.md`
**優先度**: 高（移行全体で最もリスクが高い Phase）
**依存**: Phase 1, Phase 2 完了
**推定タスク数**: 21

---

## 1. 概要

### 1.1 Phase 3 の目的

Phase 3 は v4.5.0 移行において**最大のコード変更**を伴うフェーズである。
以下の 4 領域を対象とする:

1. **既存 hooks の差分適用** — `pre-tool-use.py`, `post-tool-use.py`, `lam-stop-hook.py`
2. **analyzers/ の新規導入** — Scalable Code Review 静的解析パイプライン（13 モジュール）
3. **settings.json の更新** — `PostToolUseFailure` イベント登録、allow リスト拡張
4. **.gitignore の更新** — `review-state/`, `v4-5-0-update-plan/` 選択的除外

### 1.2 前提条件

- Phase 1（ルール + docs/internal/ + CLAUDE.md + CHEATSHEET.md）完了
- Phase 2（コマンド / スキル / エージェント + specs/design 取込）完了
  - 特に `/full-review` が新 Stage 体系に更新済みであること（Stage 5 が Green State 判定を担当）
- 既存テスト 830+ が全て PASS の状態

### 1.3 完了条件

- 既存 hooks テスト（`tests/test_hooks/`）が全て PASS
- 新規テスト（`_PG_BLACKLISTED_ARGS`, `PostToolUseFailure`, 安全ネット）が PASS
- analyzers テスト（`tests/test_analyzers/`）が PASS（外部依存不要分）
- `ruff check .` クリーン
- 影式固有保持項目が全て維持されていること（Section 8 チェックリスト）

---

## 2. AoT Decomposition

### 2.1 Atom 分解

| Atom | 判断内容 | 依存 | 並列可否 |
|------|----------|------|----------|
| A1 | settings.json + .gitignore の更新 | なし | 独立 |
| A2 | pre-tool-use.py への `_PG_BLACKLISTED_ARGS` 追加 | なし | 独立 |
| A3 | post-tool-use.py の `PostToolUseFailure` 対応 + リファクタリング | A1（settings.json に PostToolUseFailure 登録済みが前提） | A1 後 |
| A4 | lam-stop-hook.py の全面書き換え（安全ネット化） | なし | 独立 |
| A5 | analyzers/ の新規導入 | なし | 独立 |
| A6 | テストの更新・追加 | A2, A3, A4, A5（実装完了が前提） | A2-A5 後 |

### 2.2 依存 DAG

```
A1 ─────────────────────────┐
A2 ─────────────────────────┤
A3 ← A1                    ├─→ A6
A4 ─────────────────────────┤
A5 ─────────────────────────┘
```

### 2.3 Wave 分割

設計文書のロールバック計画に基づき、以下の Wave に分割:

```
Wave A: A1（settings.json + .gitignore）— リスク低、独立
Wave B: A2 + A3（pre-tool-use + post-tool-use）— 中リスク
Wave C: A4（lam-stop-hook 全面書き換え）— 高リスク
Wave D: A5（analyzers/ 導入）— 低リスク、既存に影響なし
Wave E: A6（テスト更新・追加）— Wave A-D の検証
```

---

## 3. タスク一覧

### Wave A: settings.json + .gitignore（Atom A1）

#### T-301: settings.json に PostToolUseFailure イベント登録

| 項目 | 内容 |
|------|------|
| **説明** | `PostToolUseFailure` フックイベントを settings.json の hooks セクションに追加。Bash matcher で `post-tool-use.py` を実行 |
| **対象ファイル** | `.claude/settings.json` |
| **変更種別** | 追加 |
| **影式固有考慮** | コマンドプレフィックスは `python`（`python3` ではなく）を使用（Windows 環境） |
| **依存** | なし |
| **サイズ** | S |

追加内容:
```json
"PostToolUseFailure": [
  {
    "matcher": "Bash",
    "hooks": [{
      "type": "command",
      "command": "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/post-tool-use.py"
    }]
  }
]
```

**完了条件**:
- [ ] `PostToolUseFailure` が hooks セクションに追加されている
- [ ] コマンドプレフィックスが `python`（影式固有）であること
- [ ] JSON 構文エラーがないこと（`python -c "import json; json.load(open('.claude/settings.json'))"` で確認）

---

#### T-302: settings.json の allow リスト拡張

| 項目 | 内容 |
|------|------|
| **説明** | LAM v4.5.0 で追加された `python -m pytest *`, `python -c *` を allow に追加 |
| **対象ファイル** | `.claude/settings.json` |
| **変更種別** | 追加 |
| **影式固有考慮** | `python3` 系は追加しない（Windows 環境では `python3` コマンドなし）。`Bash(git status *)`, `Bash(pip show *)` の保持を確認 |
| **依存** | なし |
| **サイズ** | S |

追加エントリ:
- `Bash(python -m pytest *)`
- `Bash(python -c *)`

**完了条件**:
- [ ] 上記 2 エントリが allow に追加されている
- [ ] 既存の影式固有エントリ（`git status *`, `pip show *`）が保持されていること
- [ ] `Bash(python *)` が ask に**含まれていない**こと（settings.local.json に委任の運用を継続）

---

#### T-303: .gitignore に review-state/ と v4-5-0 除外を追加

| 項目 | 内容 |
|------|------|
| **説明** | analyzers の永続化ディレクトリ `.claude/review-state/` と、v4-5-0 移行資材の選択的追跡を .gitignore に追加 |
| **対象ファイル** | `.gitignore` |
| **変更種別** | 追加 |
| **影式固有考慮** | 既存の `!docs/memos/v4-update-plan/`, `!docs/memos/v4-4-1-update-plan/` のパターンを踏襲。`config.toml`, `# pytest` セクションの保持確認 |
| **依存** | なし |
| **サイズ** | S |

追加エントリ:
```gitignore
.claude/review-state/
!docs/memos/v4-5-0-update-plan/
```

**完了条件**:
- [ ] `.claude/review-state/` が追加されている
- [ ] `!docs/memos/v4-5-0-update-plan/` が追加されている
- [ ] 既存の影式固有エントリ（`config.toml`, `!docs/memos/v4-update-plan/`, `!docs/memos/v4-4-1-update-plan/`）が保持されていること

---

### Wave B: pre-tool-use.py + post-tool-use.py（Atom A2, A3）

#### T-304: pre-tool-use.py に `_PG_BLACKLISTED_ARGS` 定義を追加

| 項目 | 内容 |
|------|------|
| **説明** | PG 許可コマンドの引数に悪意あるオプション（`--config`, `--settings` 等）が含まれないかチェックするブラックリストを定義 |
| **対象ファイル** | `.claude/hooks/pre-tool-use.py` |
| **変更種別** | 追加 |
| **影式固有考慮** | 影式固有の PM パターン（`docs/internal/`, `pyproject.toml`）の保持。`normalized` パスを理由に含む出力形式の保持 |
| **依存** | なし |
| **サイズ** | S |

追加内容（`_AUDITING_PG_COMMANDS` の直後に定義）:
```python
# PG コマンドでもブラックリスト引数があれば SE に格上げ
_PG_BLACKLISTED_ARGS = frozenset({
    "--config",
    "--settings",
    "--rcfile",
    "--init-hook",
    "--load-plugins",
    "--ext",
    "--fixable",
    "--format",
    "--output-format",
    "--target-version",
})
```

**完了条件**:
- [ ] `_PG_BLACKLISTED_ARGS` が frozenset として定義されている
- [ ] 10 項目のブラックリスト引数が含まれている

---

#### T-305: pre-tool-use.py の AUDITING PG チェックに `_PG_BLACKLISTED_ARGS` 検証を追加

| 項目 | 内容 |
|------|------|
| **説明** | `_determine_level_and_reason()` の AUDITING PG 判定ロジック内で、PG コマンドにブラックリスト引数が含まれる場合は SE に格上げする処理を追加 |
| **対象ファイル** | `.claude/hooks/pre-tool-use.py` |
| **変更種別** | 変更 |
| **影式固有考慮** | 既存の `_determine_level_and_reason()` のシグネチャ・返り値は変更しない |
| **依存** | T-304 |
| **サイズ** | S |

変更箇所（`_determine_level_and_reason()` 内の AUDITING PG チェック部分）:
```python
# 変更前
if current_phase == "AUDITING":
    for pg_prefix in _AUDITING_PG_COMMANDS:
        if command == pg_prefix or command.startswith(pg_prefix + " "):
            return "PG", "AUDITING phase PG allow"

# 変更後
if current_phase == "AUDITING":
    for pg_prefix in _AUDITING_PG_COMMANDS:
        if command == pg_prefix or command.startswith(pg_prefix + " "):
            # ブラックリスト引数チェック
            cmd_args = command.split()
            if any(arg in _PG_BLACKLISTED_ARGS for arg in cmd_args):
                return "SE", f"AUDITING PG blocked: blacklisted arg in '{command[:80]}'"
            return "PG", "AUDITING phase PG allow"
```

**完了条件**:
- [ ] AUDITING PG 判定前にブラックリスト引数チェックが実施されること
- [ ] ブラックリスト引数を含むコマンドが SE に格上げされること
- [ ] 通常の PG コマンド（`ruff check --fix src/`）が引き続き PG として許可されること

---

#### T-306: post-tool-use.py に PostToolUseFailure 対応を追加

| 項目 | 内容 |
|------|------|
| **説明** | `main()` で `hook_event_name` を取得し、`PostToolUseFailure` イベント時に `is_failure_event=True` として処理する。`_handle_test_result()` に `is_failure_event` パラメータを追加 |
| **対象ファイル** | `.claude/hooks/post-tool-use.py` |
| **変更種別** | 変更 |
| **影式固有考慮** | `python -m pytest` テストパターンの保持。影式固有の `_TEST_CMD_PATTERN` を変更しない |
| **依存** | T-301（settings.json に PostToolUseFailure 登録済み） |
| **サイズ** | M |

主要変更:
1. `main()` に `hook_event_name = data.get("hook_event_name", "")` を追加
2. `is_failure = hook_event_name == "PostToolUseFailure"` の判定追加
3. `_handle_test_result()` に `is_failure_event` パラメータ追加
4. `is_failure_event=True` の場合、XML パース結果に関わらず FAIL として記録

**完了条件**:
- [ ] `hook_event_name` が `data.get()` で安全に取得されること
- [ ] `PostToolUseFailure` イベント時にテスト失敗が記録されること
- [ ] 通常の `PostToolUse` イベントでの動作が変わらないこと

---

#### T-307: post-tool-use.py の `_parse_junit_xml()` 例外ハンドリング厳密化

| 項目 | 内容 |
|------|------|
| **説明** | `except Exception` を `except ET.ParseError` + `except OSError` に分離。LAM v4.5.0 準拠 |
| **対象ファイル** | `.claude/hooks/post-tool-use.py` |
| **変更種別** | 変更 |
| **影式固有考慮** | なし |
| **依存** | なし |
| **サイズ** | S |

**完了条件**:
- [ ] `_parse_junit_xml()` が `ET.ParseError` と `OSError` を個別に catch すること
- [ ] 予期しない例外が伝播すること（呼び出し元の try/except で捕捉される）

---

#### T-308: post-tool-use.py の関数分離リファクタリング

| 項目 | 内容 |
|------|------|
| **説明** | `_handle_test_result()` 内のインライン処理を `_read_prev_result()`, `_record_fail()`, `_record_pass()` の 3 関数に分離。LAM v4.5.0 のリファクタリングを採用 |
| **対象ファイル** | `.claude/hooks/post-tool-use.py` |
| **変更種別** | リファクタリング |
| **影式固有考慮** | 分離後の各関数の動作が変わらないこと。`_append_to_tdd_log()` の呼び出しパターンは保持 |
| **依存** | T-306（PostToolUseFailure 対応と同時に実施推奨） |
| **サイズ** | M |

分離する関数:
```python
def _read_prev_result(last_result_file: Path) -> str:
    """前回のテスト結果を読み取る。存在しなければ空文字を返す。"""

def _record_fail(tdd_log, timestamp, test_cmd, tests, failures, failed_names, last_result_file):
    """テスト失敗を記録する。"""

def _record_pass(tdd_log, timestamp, test_cmd, tests, prev_result, last_result_file) -> str | None:
    """テスト成功を記録し、FAIL→PASS 遷移時は systemMessage を返す。"""
```

**完了条件**:
- [ ] 3 関数が分離されていること
- [ ] `_handle_test_result()` が 3 関数を呼び出す構造に変更されていること
- [ ] 動作が変更前と同一であること（テストで検証）

---

#### T-309: post-tool-use.py の `_handle_loop_log()` に `exit_code` パラメータ追加

| 項目 | 内容 |
|------|------|
| **説明** | `_handle_loop_log()` に `exit_code` パラメータを追加し、event dict に含める。LAM v4.5.0 互換 |
| **対象ファイル** | `.claude/hooks/post-tool-use.py` |
| **変更種別** | 変更 |
| **影式固有考慮** | なし |
| **依存** | なし |
| **サイズ** | S |

変更点:
- `_handle_loop_log()` のシグネチャに `exit_code: str = ""` を追加
- `event` dict に `"exit_code": exit_code` を追加
- `main()` の呼び出し箇所で空文字を渡す

**完了条件**:
- [ ] `_handle_loop_log()` に `exit_code` パラメータが追加されていること
- [ ] event dict に `exit_code` フィールドが含まれること

---

#### T-310: post-tool-use.py に `make test` パターン追加

| 項目 | 内容 |
|------|------|
| **説明** | `_TEST_CMD_PATTERN` に `make test` を追加。`_get_test_cmd_label()` に `make test` 分岐を追加 |
| **対象ファイル** | `.claude/hooks/post-tool-use.py` |
| **変更種別** | 追加 |
| **影式固有考慮** | `python\s+-m\s+pytest` パターンが保持されていること |
| **依存** | なし |
| **サイズ** | S |

**完了条件**:
- [ ] `_TEST_CMD_PATTERN` に `make\s+test` が追加されていること
- [ ] `_get_test_cmd_label()` に `make test` の分岐が追加されていること
- [ ] `python -m pytest` パターンが引き続き動作すること

---

### Wave C: lam-stop-hook.py 全面書き換え（Atom A4）

#### T-311: lam-stop-hook.py から Green State 判定ロジックを除去

| 項目 | 内容 |
|------|------|
| **説明** | 現行 ~540 行の lam-stop-hook.py から Green State 判定関連のロジック（~250 行）を除去。STEP 4-7 を安全ネットの STEP 4（block 出力）に置換 |
| **対象ファイル** | `.claude/hooks/lam-stop-hook.py` |
| **変更種別** | 全面書き換え |
| **影式固有考慮** | `datetime.UTC`（Python 3.12+ 短縮形）は保持。`contextlib.suppress` スタイルは LAM v4.5.0 の `try/except` スタイルに変更可 |
| **依存** | なし（ただし Phase 2 で `/full-review` Stage 5 が先に導入済みであること） |
| **サイズ** | L |

除去対象:
| 関数/定数 | 行数（概算） |
|-----------|------------|
| `_run_tests()` | ~25 |
| `_run_lint()` | ~18 |
| `_run_security()` | ~65 |
| `_evaluate_green_state()` | ~35 |
| `_check_escalation()` | ~20 |
| `_check_unanalyzed_tdd_patterns()` | ~20 |
| `_continue_loop()` (Green State 部分) | ~20 |
| `_check_issue_recurrence()` | ~12 |
| `_validate_check_dir()` | ~15 |
| 定数: `RESULT_PASS`, `RESULT_FAIL`, `_SECRET_PATTERN`, `_SAFE_PATTERN`, `_SCAN_EXCLUDE_DIRS` | ~14 |
| import: `re`, `shutil` | ~2 |

保持対象:
| 関数 | 機能 |
|------|------|
| `_check_recursion_and_state()` | STEP 1: 再帰防止 + pm_pending |
| `_check_max_iterations()` | STEP 2: 反復上限 |
| `_check_context_pressure()` | STEP 3: コンテキスト圧迫 |
| `_save_loop_log()` | ループ終了ログ |
| `_cleanup_state_file()` | 状態ファイル削除 |
| `_stop()`, `_block()` | 出力ヘルパー |
| `_log()`, `_get_log_file()` | ログヘルパー |

新しい STEP 構成:
```
STEP 1: 再帰防止 + 状態ファイル確認 + pm_pending チェック  (保持)
STEP 2: 反復上限チェック                                   (保持)
STEP 3: コンテキスト残量チェック                            (保持)
STEP 4: block 出力（安全ネット: iteration インクリメント）    (新規)
```

**完了条件**:
- [ ] 行数が ~540 行から ~150 行に削減されていること
- [ ] Green State 判定関数（`_run_tests`, `_run_lint`, `_run_security`, `_evaluate_green_state`）が存在しないこと
- [ ] STEP 1-3 の保持対象関数が変更されていないこと
- [ ] STEP 4 で無条件に block を出力すること
- [ ] docstring が更新されていること（「Green State チェック」→「安全ネット」）
- [ ] import 文から `re`, `shutil` が除去されていること
- [ ] `python -m py_compile` でシンタックスエラーがないこと

---

#### T-312: lam-stop-hook.py の docstring とコメントを更新

| 項目 | 内容 |
|------|------|
| **説明** | ファイル先頭 docstring の STEP 構成を 4 STEP に更新。各関数のコメントも安全ネット設計を反映 |
| **対象ファイル** | `.claude/hooks/lam-stop-hook.py` |
| **変更種別** | 変更 |
| **影式固有考慮** | LAM v4.5.0 準拠の docstring に変更するが、「影式固有調整」の注記は残す |
| **依存** | T-311 |
| **サイズ** | S |

新しい docstring:
```python
"""Stop hook — 自律ループの安全ネット.

STEP 1: 再帰防止 + 状態ファイル確認 + pm_pending チェック
STEP 2: 反復上限チェック
STEP 3: コンテキスト残量チェック（PreCompact 直近 10 分以内 → 停止）
STEP 4: 安全ネット（iteration インクリメント + block 出力）

停止 → exit 0（何も出力しない）
継続 → stdout に {"decision": "block", "reason": "..."}

LAM v4.5.0 準拠（安全ネット専用設計）。
Green State 判定は /full-review Stage 5 に移行。
"""
```

**完了条件**:
- [ ] docstring が新 STEP 構成を反映していること
- [ ] 「Green State」への言及が除去されていること（代わりに Stage 5 への参照）

---

### Wave D: analyzers/ 導入（Atom A5）

#### T-313: analyzers/ ディレクトリ構造の作成

| 項目 | 内容 |
|------|------|
| **説明** | `.claude/hooks/analyzers/` ディレクトリを作成し、`__init__.py` を配置 |
| **対象ファイル** | `.claude/hooks/analyzers/__init__.py` |
| **変更種別** | 新規作成 |
| **影式固有考慮** | なし（LAM v4.5.0 のパッケージ構成をそのまま導入） |
| **依存** | なし |
| **サイズ** | S |

**完了条件**:
- [ ] `.claude/hooks/analyzers/` ディレクトリが存在すること
- [ ] `__init__.py` が配置されていること

---

#### T-314: analyzers/ 基盤モジュールの導入（base.py, config.py, reducer.py）

| 項目 | 内容 |
|------|------|
| **説明** | データモデル定義（`Issue`, `ASTNode`, `LanguageAnalyzer`, `AnalyzerRegistry`）、設定管理（`ReviewConfig`）、重複排除（`deduplicate_issues()`）の 3 モジュールを導入 |
| **対象ファイル** | `.claude/hooks/analyzers/base.py`, `.claude/hooks/analyzers/config.py`, `.claude/hooks/analyzers/reducer.py` |
| **変更種別** | 新規作成（LAM v4.5.0 からのコピー） |
| **影式固有考慮** | 外部依存なし。LAM コードをそのまま使用（影式固有の改変なし） |
| **依存** | T-313 |
| **サイズ** | M |

**完了条件**:
- [ ] `base.py` に `Issue`, `ASTNode`, `LanguageAnalyzer`, `AnalyzerRegistry`, `ToolRequirement`, `ToolNotFoundError` が定義されていること
- [ ] `config.py` に `ReviewConfig` が定義されていること
- [ ] `reducer.py` に `deduplicate_issues()`, `classify_name()`, `check_naming_consistency()` が定義されていること
- [ ] 3 ファイルとも `python -m py_compile` でエラーがないこと

---

#### T-315: analyzers/ 解析モジュールの導入（python_analyzer.py, javascript_analyzer.py, rust_analyzer.py）

| 項目 | 内容 |
|------|------|
| **説明** | 3 言語の静的解析 Analyzer を導入。Python は ruff + bandit + ast、JS/TS は eslint + npm audit、Rust は cargo clippy + cargo audit |
| **対象ファイル** | `.claude/hooks/analyzers/python_analyzer.py`, `.claude/hooks/analyzers/javascript_analyzer.py`, `.claude/hooks/analyzers/rust_analyzer.py` |
| **変更種別** | 新規作成（LAM v4.5.0 からのコピー） |
| **影式固有考慮** | JS/Rust analyzer は影式では実質未使用だが、LAM テンプレートとして配置（将来の移行差分を最小化）。外部ツール（bandit, eslint, cargo）はオプショナル |
| **依存** | T-314（base.py が必要） |
| **サイズ** | M |

**完了条件**:
- [ ] 3 ファイルが配置されていること
- [ ] 各 Analyzer が `LanguageAnalyzer` ABC を継承していること
- [ ] `python -m py_compile` でエラーがないこと（外部ツール未インストールでもインポート可能）

---

#### T-316: analyzers/ パイプラインモジュールの導入（run_pipeline.py, orchestrator.py, scale_detector.py）

| 項目 | 内容 |
|------|------|
| **説明** | Phase 0 統合パイプライン、バッチオーケストレーション、スケール検出の 3 モジュールを導入 |
| **対象ファイル** | `.claude/hooks/analyzers/run_pipeline.py`, `.claude/hooks/analyzers/orchestrator.py`, `.claude/hooks/analyzers/scale_detector.py` |
| **変更種別** | 新規作成（LAM v4.5.0 からのコピー） |
| **影式固有考慮** | 影式は ~5K LOC で Plan A 未満だが、Stage 体系の基盤として導入。改変不要 |
| **依存** | T-314, T-315（base.py, config.py, 各 Analyzer が必要） |
| **サイズ** | M |

**完了条件**:
- [ ] 3 ファイルが配置されていること
- [ ] `run_pipeline.py` に `run_phase0()` が定義されていること
- [ ] `orchestrator.py` に `batch_chunks()`, `build_review_prompt()` 等が定義されていること
- [ ] `scale_detector.py` に `detect_scale()` が定義されていること

---

#### T-317: analyzers/ ユーティリティモジュールの導入（chunker.py, card_generator.py, state_manager.py）

| 項目 | 内容 |
|------|------|
| **説明** | AST チャンキング、カード生成、状態永続化の 3 モジュールを導入 |
| **対象ファイル** | `.claude/hooks/analyzers/chunker.py`, `.claude/hooks/analyzers/card_generator.py`, `.claude/hooks/analyzers/state_manager.py` |
| **変更種別** | 新規作成（LAM v4.5.0 からのコピー） |
| **影式固有考慮** | `chunker.py` は `tree-sitter`, `tree_sitter_python` に依存（オプショナル）。未インストール時は ImportError で graceful degradation すること |
| **依存** | T-314（base.py が必要） |
| **サイズ** | M |

**完了条件**:
- [ ] 3 ファイルが配置されていること
- [ ] `chunker.py` が tree-sitter 未インストール時にも import エラーを起こさないこと（try/except で保護されている前提）
- [ ] `state_manager.py` の保存先が `.claude/review-state/` であること（T-303 の .gitignore 追加と整合）

---

### Wave E: テスト更新・追加（Atom A6）

#### T-318: test_pre_tool_use.py に `_PG_BLACKLISTED_ARGS` テストを追加

| 項目 | 内容 |
|------|------|
| **説明** | AUDITING フェーズで PG コマンドにブラックリスト引数が含まれる場合の SE 格上げテストを追加 |
| **対象ファイル** | `tests/test_hooks/test_pre_tool_use.py` |
| **変更種別** | 追加 |
| **影式固有考慮** | 影式固有の PM パターン（`docs/internal/`, `pyproject.toml`）のテストが引き続き存在すること |
| **依存** | T-304, T-305 |
| **サイズ** | S |

追加テストケース:
- `test_auditing_pg_blocked_by_blacklisted_args` — `ruff check --fix --config evil.toml` が SE に格上げされること
- `test_auditing_pg_normal_args_allowed` — `ruff check --fix src/` が PG のままであること
- `test_blacklisted_args_outside_auditing` — AUDITING 以外のフェーズでは影響なし

**完了条件**:
- [ ] 上記 3 テストケースが PASS
- [ ] 既存テストが全て PASS（回帰なし）

---

#### T-319: test_post_tool_use.py に PostToolUseFailure テストと関数分離テストを追加

| 項目 | 内容 |
|------|------|
| **説明** | `PostToolUseFailure` イベント処理のテスト、`_read_prev_result()` / `_record_fail()` / `_record_pass()` の単体テスト、`_handle_loop_log()` の `exit_code` テストを追加 |
| **対象ファイル** | `tests/test_hooks/test_post_tool_use.py` |
| **変更種別** | 追加 |
| **影式固有考慮** | `python -m pytest` パターンのテストが引き続き存在すること |
| **依存** | T-306, T-307, T-308, T-309, T-310 |
| **サイズ** | M |

追加テストケース:
- `test_post_tool_use_failure_event` — `PostToolUseFailure` イベントで FAIL が記録されること
- `test_read_prev_result_*` — 前回結果読み取りの正常系・異常系
- `test_record_fail` — 失敗記録の動作
- `test_record_pass_with_transition` — FAIL→PASS 遷移時の systemMessage
- `test_handle_loop_log_exit_code` — exit_code が event dict に含まれること
- `test_make_test_pattern` — `make test` コマンドの検出
- `test_parse_junit_xml_specific_exceptions` — 個別例外ハンドリングの検証

**完了条件**:
- [ ] 上記テストケースが全て PASS
- [ ] 既存テストが全て PASS（回帰なし）

---

#### T-320: test_stop_hook.py の書き換え（Green State テスト除去 + 安全ネットテスト追加）

| 項目 | 内容 |
|------|------|
| **説明** | 現行の test_stop_hook.py から Green State 判定テスト（`test_green_state_*`, `test_escalation_*`, `test_run_tests_*`, `test_run_lint_*`, `test_security_*`）を除去し、安全ネットテストに置換 |
| **対象ファイル** | `tests/test_hooks/test_stop_hook.py` |
| **変更種別** | 全面書き換え |
| **影式固有考慮** | STEP 1-3 のテスト（再帰防止、max_iterations、context_pressure、pm_pending）は保持 |
| **依存** | T-311（lam-stop-hook.py 書き換え完了後） |
| **サイズ** | L |

除去するテスト:
- `test_green_state_*` 系
- `test_escalation_*` 系
- `test_run_tests_*` 系
- `test_run_lint_*` 系
- `test_security_*` 系
- `test_validate_check_dir_*` 系

追加するテスト:
- `test_safety_net_block` — STEP 1-3 を通過した場合に block が出力されること
- `test_iteration_increment` — iteration が正しくインクリメントされること
- `test_safety_net_no_external_process` — 外部プロセス（pytest, ruff 等）が呼び出されないこと

保持するテスト:
- `test_recursion_prevention` — STEP 1 再帰防止
- `test_max_iterations_*` — STEP 2 反復上限
- `test_context_pressure_*` — STEP 3 コンテキスト圧迫
- `test_pm_pending_*` — pm_pending フラグ
- `test_save_loop_log` — ループログ保存
- `test_cleanup_state_file` — 状態ファイル削除

**完了条件**:
- [ ] Green State 関連テストが除去されていること
- [ ] 安全ネットテストが追加されていること
- [ ] STEP 1-3 のテストが保持されていること
- [ ] 全テストが PASS

---

#### T-321: tests/test_analyzers/ ディレクトリとテストファイルの配置

| 項目 | 内容 |
|------|------|
| **説明** | LAM v4.5.0 の `analyzers/tests/` を影式の `tests/test_analyzers/` に配置。影式のテスト構成（`tests/` 配下）に準拠 |
| **対象ファイル** | `tests/test_analyzers/` 配下（conftest.py + 14 テストファイル + fixtures/） |
| **変更種別** | 新規作成（LAM v4.5.0 からのコピー + パス調整） |
| **影式固有考慮** | import パスの調整（LAM は `.claude/hooks/analyzers/tests/` から相対 import、影式は `tests/test_analyzers/` から絶対 import）。外部依存テストには `pytest.mark.skipif` を付与 |
| **依存** | T-313〜T-317（analyzers モジュール配置完了後） |
| **サイズ** | L |

配置ファイル:
```
tests/test_analyzers/
├── conftest.py
├── test_base.py
├── test_registry.py
├── test_config.py
├── test_python_analyzer.py       # ruff 必須、bandit は skipif
├── test_javascript_analyzer.py   # skipif(npm not found)
├── test_rust_analyzer.py         # skipif(cargo not found)
├── test_run_pipeline.py
├── test_orchestrator.py
├── test_chunker.py               # skipif(tree-sitter not found)
├── test_reducer.py
├── test_state_manager.py
├── test_card_generator.py
├── test_integration_pipeline.py
├── test_e2e_review.py            # skipif(外部ツール不足)
└── fixtures/e2e/
```

外部依存の skipif パターン:
```python
import shutil
import pytest

pytestmark = pytest.mark.skipif(
    shutil.which("bandit") is None,
    reason="bandit not installed"
)
```

**完了条件**:
- [ ] `tests/test_analyzers/` ディレクトリが存在すること
- [ ] 外部ツール未インストール時にテストが skip されること（FAIL ではなく SKIP）
- [ ] 外部依存不要のテスト（base, config, reducer, state_manager 等）が PASS
- [ ] `pyproject.toml` の `testpaths` 設定変更が不要であること（`tests/` 配下なので自動収集）

---

## 4. MAGI Review

### [MELCHIOR]: 並列性・効率

Wave A（T-301〜T-303）は完全独立であり、他の Wave と並列実行可能。
Wave B（T-304〜T-310）と Wave D（T-313〜T-317）も相互に独立しており並列実行可能。
Wave C（T-311〜T-312）は単独で高リスクだが、Wave B/D と依存関係がないため並列実行可能。
Wave E（T-318〜T-321）は Wave B/C/D の完了を待つ必要がある。

最適実行パス:
```
Time 1: Wave A + Wave B + Wave C + Wave D（全並列）
Time 2: Wave E（テスト、全 Wave 完了後）
```

ただし、**Wave C のロールバックリスク**を考慮すると、Wave A/B を先に完了・検証してから Wave C に進む方が安全。

### [BALTHASAR]: ギャップ・リスク・不足タスク

1. **リスク R7（二重判定期間）**: Phase 2 完了後〜Phase 3 完了前に `/full-review` を実行すると、Stage 5 の Green State 判定と lam-stop-hook の旧 Green State 判定が二重実行される。**Phase 3 完了まで `/full-review` を実行しないことを明文化すべき**。→ T-311 の前提条件に記載済み。

2. **テスト数の見積もり**: 既存 test_stop_hook.py から Green State テストを除去すると、テスト総数が減少する可能性がある。Phase 4 の検証で「830+ テストが全て PASS」の条件を満たすか確認が必要。→ 安全ネットテスト追加で補填するが、純減は不可避。

3. **analyzers/ の import パス**: LAM v4.5.0 の analyzers テストは相対 import を使用している可能性がある。影式の `tests/test_analyzers/` への配置時に import パスの調整が必要。→ T-321 で対応。

4. **不足タスク**: post-tool-use.py の docstring 更新タスクが明示されていない。→ T-306〜T-310 の変更に含めて実施。

5. **notify-sound.py の保護確認**: Wave 全体を通じて、notify-sound.py が変更されないことを最終確認するタスクがない。→ Section 8 の影式固有保持チェックリストで対応。

### [CASPAR]: 最終判定

Phase 3 のタスク分解は妥当。21 タスクに分解し、5 Wave でのロールバック可能な実行計画は設計文書と整合している。
最大リスクは Wave C（lam-stop-hook.py 全面書き換え）であり、Wave A/B の完了後に着手する順序が推奨される。
analyzers/ の導入（Wave D）は既存コードに影響を与えないため、Wave C と並列実行可能。

**追加推奨事項**:
- Wave C 着手前に、現行 test_stop_hook.py の「何を検証しているか」のリストを作成し、保持すべきテストを明確化する
- Wave E 完了後に `pytest --tb=short -q` で全テスト実行し、PASS/FAIL/SKIP の内訳を確認する

---

## 5. 実行順序

```
Phase 3 実行順序（推奨）
═══════════════════════

Step 1: Wave A（settings.json + .gitignore）
  ├─ T-301: settings.json に PostToolUseFailure 追加         [S]
  ├─ T-302: settings.json の allow リスト拡張                [S]
  └─ T-303: .gitignore に review-state/ 追加                [S]
  → JSON 構文チェック + git diff で確認
  → 所要時間: ~30 分

Step 2: Wave B（pre-tool-use + post-tool-use）— 並列可
  ├─ T-304: _PG_BLACKLISTED_ARGS 定義追加                   [S]
  ├─ T-305: AUDITING PG チェック拡張                         [S]
  ├─ T-306: PostToolUseFailure 対応                          [M]
  ├─ T-307: _parse_junit_xml() 例外厳密化                    [S]
  ├─ T-308: 関数分離リファクタリング                          [M]
  ├─ T-309: _handle_loop_log() exit_code 追加               [S]
  └─ T-310: make test パターン追加                           [S]
  → py_compile + 既存テスト実行で確認
  → 所要時間: ~2 時間

Step 3: Wave C（lam-stop-hook 全面書き換え）
  ├─ T-311: Green State 判定除去 + 安全ネット化               [L]
  └─ T-312: docstring 更新                                  [S]
  → py_compile + STEP 1-3 テストで確認
  → 所要時間: ~1.5 時間

Step 4: Wave D（analyzers/ 導入）— Step 2/3 と並列可
  ├─ T-313: ディレクトリ構造作成                              [S]
  ├─ T-314: 基盤モジュール導入                                [M]
  ├─ T-315: 解析モジュール導入                                [M]
  ├─ T-316: パイプラインモジュール導入                         [M]
  └─ T-317: ユーティリティモジュール導入                       [M]
  → py_compile で確認
  → 所要時間: ~1.5 時間

Step 5: Wave E（テスト更新・追加）— Step 2-4 完了後
  ├─ T-318: test_pre_tool_use.py テスト追加                  [S]
  ├─ T-319: test_post_tool_use.py テスト追加                 [M]
  ├─ T-320: test_stop_hook.py 全面書き換え                   [L]
  └─ T-321: tests/test_analyzers/ 配置                      [L]
  → 全テスト実行 + ruff check
  → 所要時間: ~2.5 時間

総所要時間: ~8 時間
```

---

## 6. ロールバック計画

| Wave | ロールバック方法 | 影響範囲 |
|------|----------------|---------|
| Wave A | `git revert` で settings.json + .gitignore を元に戻す | 他 Wave に影響なし（ただし PostToolUseFailure が無効になる） |
| Wave B | `git revert` で pre-tool-use.py + post-tool-use.py を元に戻す | Wave A の PostToolUseFailure 登録は残るが、handler 不在でも安全（hook は no-op） |
| Wave C | `git revert` で lam-stop-hook.py を元に戻す | Green State 判定が復活。Wave A/B に影響なし |
| Wave D | `git revert` で analyzers/ を削除 | 他 Wave に影響なし |
| Wave E | `git revert` でテストを元に戻す | 実装 Wave に影響なし |

---

## 7. リスク一覧

| # | リスク | 影響度 | 対策 |
|---|--------|--------|------|
| R1 | lam-stop-hook.py 書き換えで安全ネットが機能しなくなる | **高** | STEP 1-3 保持。STEP 4 は最小限コード。テストで検証 |
| R2 | Green State 判定の空白期間（stop-hook 除去〜full-review Stage 5 初回実行） | **高** | Phase 2 で Stage 体系導入済みが前提。Phase 3 完了まで /full-review 不実行 |
| R3 | analyzers/ の外部依存が解決できない | **低** | オプショナル扱い。skipif でテスト skip |
| R4 | `_PG_BLACKLISTED_ARGS` で正当な PG コマンドがブロック | **中** | ブラックリスト内容は `--config` 等の稀な引数。テストで確認 |
| R5 | `PostToolUseFailure` のスキーマ不整合 | **中** | `data.get()` で安全取得。未知イベントは無視 |
| R6 | test_stop_hook.py 書き換えで検証範囲が縮小 | **中** | 除去前にテスト一覧を作成。安全ネットテストで STEP 1-3 カバー |
| R7 | analyzers テストの import パス不整合 | **中** | T-321 で sys.path 調整を実施 |

---

## 8. 影式固有保持チェックリスト

Phase 3 の全 Wave 完了後に以下を確認する:

### hooks 関連

- [ ] `_hook_utils.py`: `_MAX_STDIN_BYTES`（1MB stdin 制限）が保持
- [ ] `_hook_utils.py`: `normalize_path()` の `resolve()` + `replace("\\", "/")` が保持
- [ ] `_hook_utils.py`: `datetime.UTC`（Python 3.12+ 短縮形）が保持
- [ ] `pre-tool-use.py`: PM パターンに `docs/internal/` と `pyproject.toml` が含まれている
- [ ] `pre-tool-use.py`: `_determine_level_and_reason()` で `normalized` パスを理由に含めている
- [ ] `post-tool-use.py`: `_TEST_CMD_PATTERN` に `python\s+-m\s+pytest` が含まれている
- [ ] `notify-sound.py`: **一切変更されていない**こと

### settings.json 関連

- [ ] hooks コマンドプレフィックスが `python`（`python3` ではなく）
- [ ] `Bash(git status *)` が allow に含まれている
- [ ] `Bash(pip show *)` が allow に含まれている
- [ ] `Bash(python *)` が ask に**含まれていない**（settings.local.json に委任）

### .gitignore 関連

- [ ] `!docs/memos/` 選択的除外パターンが保持
- [ ] `!docs/memos/v4-update-plan/` が保持
- [ ] `!docs/memos/v4-4-1-update-plan/` が保持
- [ ] `config.toml` が保持
- [ ] `# pytest` セクション（htmlcov, .coverage, .pytest_cache/）が保持

### 構成確認

- [ ] `.claude/hooks/analyzers/` に 13 ファイルが存在
- [ ] `tests/test_analyzers/` にテストファイルが存在
- [ ] `.gitignore` に `.claude/review-state/` が追加されている
- [ ] `PostToolUseFailure` が settings.json に登録されている
