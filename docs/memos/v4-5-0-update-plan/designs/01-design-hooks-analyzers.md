# 設計: Phase 3 — Hooks + analyzers/ + settings.json + .gitignore

**作成日**: 2026-03-16
**ステータス**: Draft
**対象 Phase**: Phase 3 (LAM v4.4.1 → v4.5.0 移行)
**前回参考**: `docs/memos/v4-4-1-update-plan/designs/01-design-hooks-settings.md`

---

## 1. 概要

Phase 3 は v4.5.0 移行の中で**最もリスクが高い**フェーズである。対象は以下の 4 領域:

1. **既存 hooks の差分適用** — `pre-tool-use.py`, `post-tool-use.py`, `lam-stop-hook.py` の更新
2. **analyzers/ の新規導入** — Scalable Code Review の静的解析パイプライン（13 モジュール）
3. **settings.json の更新** — `PostToolUseFailure` イベント登録、allow リスト拡張
4. **.gitignore の更新** — `review-state/` 等の追加

### 最大の変更点: lam-stop-hook.py の設計転換

現行の影式 `lam-stop-hook.py`（540 行）は stop-hook 内で Green State 判定（G1/G2/G5）を実行する独自設計。
LAM v4.5.0 は「stop-hook は安全ネットのみ（~150 行）、Green State 判定は `/full-review` Stage 5」という設計。
**承認済み決定: LAM 設計に移行する**。

---

## 2. 移行戦略

### 2.1 既存 hooks: ファイル別変更計画

#### `_hook_utils.py` — 変更なし

v4.4.1 移行で完全移行済み。v4.5.0 との差分は影式固有改善（stdin バイト制限、Windows パス正規化）のみで、LAM 側に新規追加関数はない。**作業不要**。

#### `pre-tool-use.py` — 小規模追加

| 変更 | 内容 | 優先度 |
|------|------|--------|
| `_PG_BLACKLISTED_ARGS` 追加 | `--config`, `--settings` 等 10 項目のブラックリスト定義 | **必須**（セキュリティ強化） |
| AUDITING PG チェック拡張 | プレフィックスマッチ後に `_PG_BLACKLISTED_ARGS` チェックを追加 | **必須** |
| read-only ログ出力 | LAM v4.5.0 は read-only ツールもログ記録 | 任意（ログ量増加とのトレードオフ） |

影式固有保持: PM パターン 2 項目（`docs/internal/`, `pyproject.toml`）、`normalized` パス含み理由文字列。

#### `post-tool-use.py` — 中規模リファクタリング

| 変更 | 内容 | 優先度 |
|------|------|--------|
| `PostToolUseFailure` 対応 | `hook_event_name` 取得 + `is_failure_event` パラメータ | **必須** |
| `_read_prev_result()` 関数分離 | インライン処理を関数に抽出 | 推奨（可読性） |
| `_record_fail()` 関数分離 | 同上 | 推奨 |
| `_record_pass()` 関数分離 | 同上 | 推奨 |
| `_parse_junit_xml()` 例外厳密化 | `except Exception` → `except ET.ParseError` + `except OSError` | 推奨 |
| `_handle_loop_log()` に `exit_code` 追加 | LAM v4.5.0 互換 | 推奨 |
| `make test` パターン追加 | `_TEST_CMD_PATTERN` に追加 | 推奨 |

影式固有保持: `python -m pytest` テストパターン。

#### `lam-stop-hook.py` — **全面書き換え**（詳細は Section 3）

現行 540 行 → 目標 ~150 行。Green State 判定ロジック（STEP 4-7 の大部分）を除去し、安全ネット専用に再設計。

#### `pre-compact.py` — 変更なし

v4.4.1 との差分なし。v4.5.0 とも差分なし。**作業不要**。

#### `notify-sound.py` — 変更なし

影式固有フック。LAM に存在しない。**保持、変更不要**。

### 2.2 analyzers/: 導入戦略

#### ディレクトリ構成

```
.claude/hooks/analyzers/
├── __init__.py              # パッケージ初期化
├── base.py                  # Issue/ASTNode/LanguageAnalyzer 基底 + Registry
├── config.py                # ReviewConfig
├── orchestrator.py          # バッチ並列 + プロンプト生成
├── scale_detector.py        # Plan A-D スケール検出
├── run_pipeline.py          # Phase 0 静的解析パイプライン
├── card_generator.py        # 概要カード + 依存グラフ + 契約カード
├── chunker.py               # AST チャンキング
├── reducer.py               # 重複排除 + 命名規則チェック
├── state_manager.py         # レビュー状態永続化
├── python_analyzer.py       # Python: ruff + bandit + ast
├── javascript_analyzer.py   # JS/TS: eslint + npm audit
└── rust_analyzer.py         # Rust: cargo clippy + cargo audit
```

#### 導入方針

- **全 13 モジュールをそのまま導入**（承認済み決定）
- JavaScript/Rust analyzer は影式では実質未使用だが、LAM テンプレートとして配置（削除は将来の移行差分を増やすだけ）
- 影式固有の改変は行わない（LAM コードをそのまま使用）
- `chunker.py` の外部依存（`tree-sitter`, `tree_sitter_python`）は**オプショナル扱い**とする。未インストール時は graceful degradation（影式の現行規模では AST チャンキング不要）

#### 外部依存の判断

| パッケージ | 必須/オプション | 理由 |
|-----------|---------------|------|
| `tree-sitter` | オプション | chunker.py 用。Plan B 以上で初めて有効 |
| `tree_sitter_python` | オプション | 同上 |
| `bandit` | オプション | python_analyzer.py のセキュリティスキャン用。ruff だけでも基本機能は動作 |

**pyproject.toml への追加は見送り**。必要になった時点で `pip install` する運用とする（影式は ~5K LOC で Plan A 未満）。

### 2.3 settings.json: 変更内容

| 変更 | 内容 |
|------|------|
| **PostToolUseFailure 追加** | Bash matcher で `post-tool-use.py` を実行する新規イベント登録 |
| **allow 追加**: `python -m pytest *` | LAM v4.5.0 新規。影式の標準テスト実行形式でもある |
| **allow 追加**: `python -c *` | LAM v4.5.0 新規。analyzers パイプラインで使用 |

影式固有保持:
- コマンドプレフィックス: `python`（`python3` ではなく）— Windows 環境
- `Bash(git status *)`, `Bash(pip show *)` — 影式固有 allow
- `Bash(python *)` は ask **に入れない** — `settings.local.json` に委任の運用を継続

変更後の hooks セクション:

```json
{
  "hooks": {
    "PreToolUse": [ ... ],
    "PostToolUse": [ ... ],
    "PostToolUseFailure": [
      {
        "matcher": "Bash",
        "hooks": [{
          "type": "command",
          "command": "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/post-tool-use.py"
        }]
      }
    ],
    "Stop": [ ... ],
    "PreCompact": [ ... ]
  }
}
```

### 2.4 .gitignore: 追加エントリ

| エントリ | 理由 |
|---------|------|
| `.claude/review-state/` | analyzers の永続化ディレクトリ（**必須**） |
| `!docs/memos/v4-5-0-update-plan/` | v4.5.0 移行資材の追跡（影式固有） |

`**/test-results.xml` への変更は見送り（現行の `.claude/test-results.xml` で十分機能する）。

### 2.5 Hook テスト: マージ戦略

影式のテストは `tests/test_hooks/` に配置（v4.4.1 移行時の決定を踏襲）。

#### 既存テストへの影響

| テストファイル | 影響 | 対応 |
|-------------|------|------|
| `test_hook_utils.py` | なし | 変更不要 |
| `test_pre_tool_use.py` | `_PG_BLACKLISTED_ARGS` テスト追加 | LAM v4.5.0 のテストケースをマージ |
| `test_post_tool_use.py` | `PostToolUseFailure` テスト追加、関数分離のテスト追加 | LAM v4.5.0 のテストケースをマージ |
| `test_stop_hook.py` | **全面書き換え** | Green State テストを除去、安全ネットテストに置換 |
| `test_pre_compact.py` | なし | 変更不要 |
| `test_integration.py` | 軽微な影響 | stop-hook テストの更新に追従 |

#### analyzers テスト

LAM v4.5.0 の `analyzers/tests/`（15 ファイル + fixtures）を `tests/test_analyzers/` に配置。

```
tests/test_analyzers/
├── conftest.py
├── test_base.py
├── test_registry.py
├── test_config.py
├── test_python_analyzer.py
├── test_javascript_analyzer.py
├── test_rust_analyzer.py
├── test_run_pipeline.py
├── test_orchestrator.py
├── test_chunker.py
├── test_reducer.py
├── test_state_manager.py
├── test_card_generator.py
├── test_integration_pipeline.py
├── test_e2e_review.py
└── fixtures/e2e/
```

`pyproject.toml` の `testpaths` 設定は現行のまま（`tests/` 配下なので自動収集される）。

---

## 3. lam-stop-hook 移行の詳細設計

### 3.1 設計転換の背景

| 観点 | 現行（影式 v4.4.1） | 目標（LAM v4.5.0 設計） |
|------|-------------------|----------------------|
| 責務 | 安全ネット + Green State 判定 | **安全ネットのみ** |
| 行数 | ~540 行 | ~150 行 |
| 外部プロセス呼び出し | pytest, ruff, pip-audit, シークレットスキャン | **なし** |
| 判定ロジック | G1/G2/G5 を自身で実行・評価 | ループ上限・コンテキスト圧迫のみ |
| Green State の場所 | stop-hook 内 | `/full-review` Stage 5（Claude 側） |

### 3.2 除去するもの

以下の関数・ロジックを**完全に除去**する:

| 除去対象 | 行数（概算） | 理由 |
|---------|------------|------|
| `_run_tests()` | ~25 行 | G1 判定 → `/full-review` Stage 5 に移行 |
| `_run_lint()` | ~18 行 | G2 判定 → 同上 |
| `_run_security()` | ~65 行 | G5 判定 → 同上 |
| `_evaluate_green_state()` | ~35 行 | Green State 総合判定 → 同上 |
| `_check_escalation()` | ~20 行 | エスカレーション → 同上 |
| `_check_unanalyzed_tdd_patterns()` | ~20 行 | TDD パターン通知 → 同上 |
| `_continue_loop()` (Green State 部分) | ~20 行 | fail_parts ロジック → 同上 |
| `_check_issue_recurrence()` | ~12 行 | Issue 再発 → 同上 |
| `_validate_check_dir()` | ~15 行 | CWD 検証（Green State 実行時のみ必要だった） |
| `RESULT_PASS`, `RESULT_FAIL` 定数 | ~2 行 | Green State 判定用 |
| `_SECRET_PATTERN`, `_SAFE_PATTERN` | ~8 行 | シークレットスキャン用 |
| `_SCAN_EXCLUDE_DIRS` | ~4 行 | 同上 |
| `import re, shutil` | ~2 行 | Green State 判定用 |

**合計除去量**: ~250 行

### 3.3 保持するもの

| 保持対象 | 機能 | LAM v4.5.0 との対応 |
|---------|------|-------------------|
| `_check_recursion_and_state()` | STEP 1: 再帰防止 + 状態確認 + pm_pending | 同一 |
| `_check_max_iterations()` | STEP 2: 反復上限 | 同一 |
| `_check_context_pressure()` | STEP 3: コンテキスト圧迫 | 同一 |
| `_save_loop_log()` | ループ終了ログ | 同一 |
| `_cleanup_state_file()` | 状態ファイル削除 | 同一 |
| `_stop()`, `_block()` | 出力ヘルパー | 同一 |
| `_log()`, `_get_log_file()` | ログヘルパー | 同一 |

### 3.4 新しい STEP 構成

```
STEP 1: 再帰防止 + 状態ファイル確認 + pm_pending チェック  (保持)
STEP 2: 反復上限チェック                                   (保持)
STEP 3: コンテキスト残量チェック                            (保持)
STEP 4: block 出力（安全ネット: 無条件で継続を指示）          (新規: 旧 STEP 4-7 を置換)
```

STEP 4 は「ループを止めるべき条件」に該当しなかった場合の**フォールバック**として block を出力する。
Green State の判定は `/full-review` Stage 5 が担当し、Claude 側で `/stop` コマンドを発行する。

### 3.5 新しい main() の概要

```python
def main() -> None:
    project_root = get_project_root()
    state_file = project_root / ".claude" / "lam-loop-state.json"
    pre_compact_flag = project_root / ".claude" / "pre-compact-fired"
    log_file = _get_log_file(project_root)

    input_data = read_stdin_json()

    # STEP 1: 再帰防止・状態ファイル確認・pm_pending
    state = _check_recursion_and_state(input_data, state_file, log_file)

    # STEP 2: 反復上限チェック
    iteration, max_iterations = _check_max_iterations(
        state, state_file, project_root, log_file
    )

    # STEP 3: コンテキスト残量チェック
    _check_context_pressure(
        pre_compact_flag, state, state_file, project_root, log_file
    )

    # STEP 4: 安全ネット — iteration をインクリメントして block
    new_iteration = iteration + 1
    state["iteration"] = new_iteration
    atomic_write_json(state_file, state)
    _block(log_file, f"safety net: cycle {new_iteration}/{max_iterations}")
```

### 3.6 `/full-review` Stage 5 による代替

Green State 判定は `/full-review` の Stage 5（True Green State）に移行する。
Stage 5 は Claude 側で以下を実行:

1. テスト全パス確認（G1）
2. lint エラーゼロ確認（G2）
3. 対応可能 Issue ゼロ確認（G3）
4. 仕様差分ゼロ確認（G4）
5. セキュリティチェック通過確認（G5）

stop-hook が自身で G1/G2/G5 を実行する場合と比較して:

| 観点 | stop-hook 内判定（旧） | full-review Stage 5（新） |
|------|---------------------|------------------------|
| G3, G4 の判定 | 不可能（Claude の判断が必要） | 可能 |
| 判定精度 | G1/G2/G5 のみ（部分的） | G1-G5 全条件（完全） |
| 実行速度 | pytest + ruff 実行で 30-60 秒 | Claude 側で判定（hook の実行時間ゼロ） |
| 二重実行 | full-review とは別に独自実行 → 冗長 | 一元化 |
| 保守コスト | ~540 行の複雑なロジック | ~150 行の単純な安全ネット |

### 3.7 テストへの影響

`test_stop_hook.py` の Green State 関連テストを除去し、安全ネットのテストに置換する。

**除去するテスト（概算）**:
- `test_green_state_*` 系
- `test_escalation_*` 系
- `test_run_tests_*` 系
- `test_run_lint_*` 系
- `test_security_*` 系

**追加するテスト**:
- `test_safety_net_block` — 正常時に block を出力すること
- `test_iteration_increment` — iteration が正しくインクリメントされること
- STEP 1-3 のテストは既存を維持（再帰防止、max_iterations、context_pressure）

#### テスト戦略

- 現行 `test_stop_hook.py` の Green State 判定テスト（`_run_tests`, `_run_lint`, `_run_security` 関連）は**削除**する
- 安全ネットのテスト（再帰防止、上限チェック、コンテキスト圧迫、pm_pending）は**保持**する
- Green State 判定の動作確認は Phase 4（統合検証）で `/full-review` Stage 5 を通じて実施する
- `test_stop_hook.py` の行数は現行の約 540 行から約 290 行に縮小する見込み（Green State テスト除去分）

---

## 4. 影式固有保持項目のチェックリスト

Phase 3 の実装時に、以下の影式固有項目が**誤って除去・上書きされないこと**を確認する。

### hooks 関連

- [ ] `_hook_utils.py`: `_MAX_STDIN_BYTES`（1MB stdin 制限）が保持されていること
- [ ] `_hook_utils.py`: `normalize_path()` の `resolve()` + `replace("\\", "/")` が保持されていること
- [ ] `_hook_utils.py`: `datetime.UTC`（Python 3.12+ 短縮形）が保持されていること
- [ ] `pre-tool-use.py`: PM パターンに `docs/internal/` と `pyproject.toml` が含まれていること
- [ ] `pre-tool-use.py`: `_determine_level_and_reason()` で `normalized` パスを理由に含めていること
- [ ] `post-tool-use.py`: `_TEST_CMD_PATTERN` に `python\s+-m\s+pytest` が含まれていること
- [ ] `notify-sound.py`: 変更されていないこと

### settings.json 関連

- [ ] hooks コマンドプレフィックスが `python`（`python3` ではなく）であること
- [ ] `Bash(git status *)` が allow に含まれていること
- [ ] `Bash(pip show *)` が allow に含まれていること
- [ ] `Bash(python *)` が ask に**含まれていない**こと（settings.local.json に委任）

### .gitignore 関連

- [ ] `!docs/memos/` 選択的除外パターンが保持されていること
- [ ] `config.toml` が保持されていること
- [ ] `# pytest` セクション（htmlcov, .coverage）が保持されていること

---

## 5. 検証チェックリスト（Phase 3 完了条件）

### 5.1 テスト

- [ ] 既存 hooks テスト（`tests/test_hooks/`）が全て PASS
- [ ] 新規 `_PG_BLACKLISTED_ARGS` テストが PASS
- [ ] 新規 `PostToolUseFailure` テストが PASS
- [ ] `test_stop_hook.py` の書き換え後テストが全て PASS
- [ ] analyzers テスト（`tests/test_analyzers/`）が全て PASS（外部依存不要のもの）
- [ ] 全テスト実行で回帰なし

### 5.2 lint

- [ ] `ruff check .` がクリーン

### 5.3 機能確認

- [ ] `pre-tool-use.py`: AUDITING フェーズで `ruff check --fix --config evil.toml` がブロックされること
- [ ] `post-tool-use.py`: Bash コマンド失敗時に `PostToolUseFailure` イベントが処理されること
- [ ] `lam-stop-hook.py`: 安全ネットとして block を出力すること（Green State 判定が**実行されない**こと）
- [ ] `settings.json`: `PostToolUseFailure` イベントが正しく登録されていること

### 5.4 影式固有保持

- [ ] Section 4 のチェックリストが全て確認済み

### 5.5 構成確認

- [ ] `.claude/hooks/analyzers/` に 13 ファイルが存在すること
- [ ] `tests/test_analyzers/` にテストファイルが存在すること
- [ ] `.gitignore` に `.claude/review-state/` が追加されていること

---

## 6. リスクと対策

| # | リスク | 影響度 | 対策 |
|---|--------|--------|------|
| R1 | lam-stop-hook.py 書き換えで安全ネットが機能しなくなる | **高**（無限ループ発生） | STEP 1-3 の既存ロジックは保持。STEP 4 の block 出力は最小限のコード。書き換え後に test_stop_hook.py で検証 |
| R2 | Green State 判定が stop-hook からも full-review からも実行されない空白期間 | **高** | Phase 2 で full-review の Stage 体系が先に導入済みであることを前提とする。Phase 2 → 3 の順序を厳守 |
| R3 | analyzers/ の外部依存（tree-sitter, bandit）が影式環境で解決できない | **低** | オプショナル扱い。未インストール時は graceful degradation。影式の現行規模では不要 |
| R4 | `_PG_BLACKLISTED_ARGS` の追加で正当な PG コマンドがブロックされる | **中** | ブラックリストの内容（`--config`, `--settings` 等）は通常の ruff/format 実行に含まれない引数。テストで確認 |
| R5 | `PostToolUseFailure` イベントのスキーマが影式の post-tool-use.py と不整合 | **中** | `hook_event_name` フィールドの存在確認を `data.get()` で安全に行う。未知のイベントは無視 |
| R6 | test_stop_hook.py の全面書き換えで既存テストの検証範囲が狭まる | **中** | 書き換え前に既存テストの「何を検証しているか」をリスト化。安全ネットテストで STEP 1-3 を確実にカバー |
| R7 | Phase 2 完了後〜Phase 3 完了前の /full-review 二重判定 | **高** | Phase 2 で Stage 体系に更新済みだが、lam-stop-hook が旧設計のため二重判定が発生。**Phase 3 完了まで /full-review を実行しない**。Phase 4 で統合検証 |

### ロールバック計画

Phase 3 は以下の Wave に分割し、各 Wave で独立してロールバック可能とする:

```
Wave A: settings.json + .gitignore 更新（リスク低、独立）
Wave B: pre-tool-use.py + post-tool-use.py 更新（中リスク、既存テストで検証）
Wave C: lam-stop-hook.py 全面書き換え + test_stop_hook.py 書き換え（高リスク）
Wave D: analyzers/ 導入 + テスト配置（低リスク、既存に影響なし）
```

Wave C で問題が発生した場合、`git revert` で即座に現行の lam-stop-hook.py に復帰できる。
Wave A/B は Wave C に依存しないため、Wave C のロールバックが Wave A/B に影響することはない。
