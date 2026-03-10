# タスク分解: Phase 3 — Hooks + 自動化

**作成日**: 2026-03-10
**対象設計**: `01-design-hooks-windows.md`
**見積り**: 5 タスク
**前提**: Phase 2 完了
**リスク**: 高（Windows 環境での hooks 動作が未検証）

---

## 依存関係

```
T3-1 (共通基盤) ──┬── T3-2 (pre-tool-use.py)
                  ├── T3-3 (post-tool-use.py)
                  ├── T3-4 (lam-stop-hook.py + pre-compact.py)
                  └── T3-5 (settings.json マージ)
                           │
                  T3-2〜T3-5 全完了
                           │
                    Phase 3 検証
```

---

## T3-1: hooks 共通基盤の構築

**設計参照**: `01-design-hooks-windows.md` 判断2（共通設計）
**優先度**: 最高（全 hook の前提）

### 作業内容

1. `.claude/hooks/` ディレクトリ構成を確認（notify-sound.py が既存）
2. 共通ユーティリティの実装:
   - `read_stdin()`: stdin から JSON 読み取り、失敗時は空辞書
   - `write_json()`: stdout に JSON 出力
   - `utc_now()`: UTC タイムスタンプ (ISO 8601)
   - `normalize_path()`: 絶対パス → PROJECT_ROOT 相対パス（POSIX 形式）
3. 共通設計方針の実装:
   - 最外層 `try/except` → `exit(0)`（hook 障害で Claude をブロックしない）
   - `pathlib.Path` による Windows/Unix 透過パス処理
   - 正規化後パスは POSIX 形式（`.as_posix()`）
4. テスト基盤: `tests/test_hooks/conftest.py` に共通フィクスチャ作成
   - mock stdin/stdout
   - tmp_path ベースの PROJECT_ROOT
   - hook モジュールの動的ローダー（`importlib`）

### 受入条件

- [ ] 共通ユーティリティが各 hook からインポート可能
- [ ] conftest.py にモジュールローダーと mock フィクスチャがある
- [ ] normalize_path が Windows パスを POSIX 形式に変換できる

---

## T3-2: pre-tool-use.py の実装

**設計参照**: `01-design-hooks-windows.md` 判断2 (pre-tool-use)
**優先度**: 高
**依存**: T3-1

### 作業内容

1. TDD Red: テストケース作成（7 件以上）
   - Read ツール → PG 級
   - docs/specs/*.md の Edit → PM 級
   - .claude/rules/ の Write → PM 級
   - src/kage_shiki/ の Edit → SE 級
   - Bash コマンド内のパス判定
   - AUDITING フェーズの特別処理
   - 不正 JSON 入力 → exit(0)
2. TDD Green: 実装
   - stdin JSON パース
   - 読み取り専用ツール判定（Read, Glob, Grep, WebSearch, WebFetch → PG 級）
   - パス正規化 + パターンマッチング（`re` モジュール）
   - PM 級パスパターン: docs/specs/, docs/adr/, docs/internal/, .claude/rules/, .claude/settings*, pyproject.toml
   - SE 級: その他
   - current-phase.md の読み取り（AUDITING フェーズ判定）
   - ログ記録: .claude/logs/permission.log（UTF-8, 100 文字トランケート）
   - PM 級 → hookSpecificOutput JSON を stdout に出力
3. TDD Refactor: 関数分割の最適化

### 受入条件

- [ ] 7 テストケース以上が PASSED
- [ ] カバレッジ 90%+
- [ ] Windows パス（バックスラッシュ）が正しく処理される
- [ ] 不正入力でクラッシュしない（exit(0) で安全に終了）

---

## T3-3: post-tool-use.py の実装

**設計参照**: `01-design-hooks-windows.md` 判断2 (post-tool-use)
**優先度**: 高
**依存**: T3-1

### 作業内容

1. TDD Red: テストケース作成（10 件以上）
   - [責務1] pytest 失敗 → tdd-patterns.log に FAIL 記録
   - [責務1] pytest 成功（前回失敗）→ PASS (previously failed) 記録
   - [責務1] pytest 成功（前回も成功）→ 記録なし
   - [責務1] 非テストコマンド → 何もしない
   - [責務2] src/ 配下の Edit → doc-sync-flag に記録
   - [責務2] docs/ 配下の Edit → doc-sync-flag に記録しない
   - [責務2] 重複パスの排除
   - [責務3] lam-loop-state.json 存在時 → tool_events 追記
   - [責務3] lam-loop-state.json 不存在時 → 何もしない
   - 不正 JSON 入力 → exit(0)
2. TDD Green: 3 つの責務を独立関数で実装
   - テストコマンド判定: 正規表現（pytest, npm test, go test）
   - doc-sync-flag: 重複防止付き追記
   - ループログ: アトミック書き込み（`tempfile` + `os.replace()`）
3. TDD Refactor

### 受入条件

- [ ] 10 テストケース以上が PASSED
- [ ] カバレッジ 90%+
- [ ] アトミック書き込みが実装されている（`os.replace()`）
- [ ] src/kage_shiki/ 配下の変更が doc-sync-flag に記録される

---

## T3-4: lam-stop-hook.py + pre-compact.py の実装

**設計参照**: `01-design-hooks-windows.md` 判断2 (stop-hook, pre-compact)
**優先度**: 高
**依存**: T3-1

### 作業内容

#### lam-stop-hook.py
1. TDD Red: テストケース作成（12 件以上）
   - 再帰防止（stop_hook_active=true → exit 0）
   - lam-loop-state.json なし → exit 0
   - active=false → exit 0
   - 反復上限到達 → 停止
   - コンテキスト残量不足（PreCompact 直近 10 分以内）→ 停止
   - G1 テスト失敗 → 継続
   - G2 lint 失敗 → 継続
   - G1+G2 パス → 停止（Green State 達成）
   - エスカレーション: テスト数減少 → 停止
   - エスカレーション: 同一 Issue 再発 → 停止
   - iteration インクリメント
   - 不正入力 → exit(0)
2. TDD Green:
   - STEP 0〜6 を独立関数で実装
   - G1: `subprocess.run(["python", "-m", "pytest", ...], timeout=120)`
   - G2: `subprocess.run(["ruff", "check", ...], timeout=60)`
   - G5: `subprocess.run(["pip-audit", ...], timeout=120)` — 未導入時はスキップ
   - テスト/lint ツール検出を辞書駆動（R-2 準拠）
   - `subprocess.run()` に `shell=True` を使用しない
3. TDD Refactor

#### pre-compact.py
1. TDD Red: テストケース作成（4 件以上）
   - pre-compact-fired にタイムスタンプ記録
   - SESSION_STATE.md に PreCompact セクション追記（冪等）
   - lam-loop-state.json のバックアップ作成
   - lam-loop-state.json 不存在時の安全な処理
2. TDD Green: 実装
3. TDD Refactor

### 受入条件

- [ ] lam-stop-hook.py: 12 テストケース以上 PASSED、カバレッジ 85%+
- [ ] lam-stop-hook.py: subprocess.run() に shell=True を使用していない
- [ ] pre-compact.py: 4 テストケース以上 PASSED、カバレッジ 90%+
- [ ] pre-compact.py: SESSION_STATE.md への書き込みが冪等である

---

## T3-5: settings.json のマージ + 統合テスト

**設計参照**: `01-design-hooks-windows.md` 判断3
**優先度**: 高
**依存**: T3-2, T3-3, T3-4（全 hook が実装済み）

### 作業内容

1. `settings.json` の更新:
   - permissions: LAM 4.0.1 の allow/deny/ask を導入
   - Python 固有コマンドは settings.local.json に委譲（settings.json からは削除）
   - ruff check --fix, ruff format を allow に追加
   - hooks: PreToolUse, PostToolUse, Stop, PreCompact の 4 定義を追加
   - コマンド形式: `python "$CLAUDE_PROJECT_DIR"/.claude/hooks/xxx.py`
2. `settings.local.json`: 変更なし（既存の Python 権限 + notify-sound.py を維持）
3. 統合テスト: `tests/test_hooks/test_integration.py`
   - settings.json の hooks 定義が正しい形式であること
   - 全 hook が `python xxx.py` で起動可能であること（dry-run）
   - notify-sound.py との共存確認
4. Green State 定義の影式版を確定（docs/specs/lam/green-state-definition.md への反映）

### 受入条件

- [ ] settings.json に 4 つの hooks 定義がある
- [ ] settings.local.json が変更されていない
- [ ] 統合テストが PASSED
- [ ] Claude Code 起動時に hooks がエラーなく読み込まれること
- [ ] notify-sound.py が引き続き動作すること

---

## Phase 3 検証チェックリスト

- [ ] hooks が Windows 環境で実行されること（エラーなし）
- [ ] pre-tool-use hook がファイルパスから PG/SE/PM を正しく判定すること
- [ ] post-tool-use hook がテスト実行結果を .claude/tdd-patterns.log に記録すること
- [ ] notify-sound.py が引き続き動作すること（共存確認）
- [ ] `/full-review` の自動ループが 1 回は正常に回ること
- [ ] pre-compact hook が auto-compact 前に状態を保存すること
- [ ] 全テスト（既存 722 件 + hook テスト）が PASSED

**コミット**: `[LAM-4.0.1] Phase 3: hooks + settings + Green State`
