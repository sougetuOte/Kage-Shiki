# 設計: Hooks Windows 実装戦略

**作成日**: 2026-03-10
**ステータス**: 承認待ち
**対象 Phase**: Phase 3 (Hooks + 自動化)

---

## 概要

LAM 4.0.1 の免疫系アーキテクチャは 4 つの hooks スクリプト（pre-tool-use, post-tool-use, lam-stop-hook, pre-compact）を bash (.sh) で実装している。影式は Windows 11 環境で動作するため、これらの hooks を Windows 互換な形式で再実装する必要がある。

本文書では 4 つの判断ポイントについて設計を記述する。

---

## 判断1: hooks の実装言語

### 選択肢

| 選択肢 | 概要 |
|--------|------|
| A. bash (.sh) そのまま | Git Bash 依存で LAM テンプレートをそのまま使用 |
| B. Python (.py) で再実装 | 影式のメイン言語で全 hook を書き直し |
| C. PowerShell (.ps1) | Windows ネイティブのスクリプト言語 |
| D. ハイブリッド (bash + Python) | 軽量な hook は bash、複雑な hook は Python |

### 比較

| 評価軸 | bash (.sh) | Python (.py) | PowerShell (.ps1) | ハイブリッド |
|--------|-----------|-------------|-------------------|-------------|
| **Windows 互換性** | △ Git Bash 必須。CRLF問題、timeout/stat/date コマンドの差異あり | ◎ クロスプラットフォーム。影式は Python 3.12+ が前提 | ○ Windows ネイティブだが起動 300-500ms | △ 二言語のメンテ負担 |
| **起動速度** | ◎ 10-50ms | ○ 50-150ms（許容範囲） | × 300-500ms。複数 hook で累積 | ○ hook 依存 |
| **LAM テンプレートとの乖離** | ◎ 乖離なし | △ 全面書き直し。ロジックの同等性検証が必要 | × 完全に別言語 | ○ 部分的乖離 |
| **メンテナンス性** | × jq フォールバック等の複雑な bash。Windows 固有の罠多数 | ◎ 影式チーム全員が Python を書ける。json モジュール標準 | △ Python チームには馴染み薄い | × 二言語の知識が必要 |
| **JSON 処理** | × jq 依存 or grep/sed フォールバック | ◎ `json` モジュール標準搭載 | ○ ConvertFrom-Json 標準 | ○ hook 依存 |
| **既存実績** | なし | ◎ notify-sound.py が問題なく動作中 | なし | なし |
| **テスト容易性** | × bash テストは Windows で不安定 | ◎ pytest で統合テスト可能 | △ Pester 必要 | △ 二系統のテスト |

### Windows 環境での bash の具体的リスク

公式ドキュメントおよび実践報告（netnerds.net 2026-02）から確認された問題:

1. **CRLF 改行コード**: Git の `core.autocrlf=true`（Windows デフォルト）により `.sh` ファイルが CRLF に変換され、shebang が `#!/bin/bash\r\n` になり「bad interpreter」エラーが発生する。`.gitattributes` で `*.sh text eol=lf` の設定が必須
2. **パスマングリング**: Git Bash がバックスラッシュをエスケープシーケンスとして解釈し、`C:\Users\` が破壊される
3. **timeout コマンドの差異**: GNU coreutils の `timeout` と Windows の `timeout.exe` は完全に別物
4. **stat コマンドの差異**: `stat -c %Y`（GNU）が Git Bash で `stat --format=%Y` になる場合がある
5. **date -d コマンドの差異**: Git Bash の date と MSYS2 の date で挙動が異なる
6. **sed -i のバックアップ挙動**: GNU sed と Git Bash sed でバックアップファイルの扱いが異なる
7. **$_ 変数の展開**: bash が PowerShell の `$_` を先に展開してしまう（ハイブリッド時の問題）

### 決定: **B. Python (.py) で全 hook を再実装する**

**根拠**:

1. **影式は Python プロジェクト**: Python 3.12+ ランタイムが確実に存在する。新たな依存追加なし
2. **notify-sound.py の実績**: 既存の hook が Python で問題なく動作している。settings.json での `python .claude/hooks/xxx.py` 形式の実績もある
3. **Windows 互換性の確実性**: `os.path`, `pathlib`, `json`, `subprocess`, `datetime` 等の標準ライブラリでクロスプラットフォーム対応が容易。bash 固有の罠（CRLF, timeout, stat, date）を全て回避できる
4. **JSON 処理の安定性**: `json` モジュールが標準搭載。jq 依存や grep/sed フォールバックの複雑なロジックが不要
5. **テスト統合**: pytest で hook の単体テスト・統合テストが書ける。影式の既存テストインフラ（722件）に統合可能
6. **起動速度**: Python の起動は 50-150ms で、hook の目的（ログ記録、権限判定、状態チェック）に対して十分高速。公式ドキュメントのデフォルト timeout は 600 秒であり、ms 単位の差は無視できる

**リスク**: LAM テンプレートの bash 版との乖離が生じる。将来の LAM アップデートで bash 版が更新された場合、Python 版への手動マージが必要になる。ただし、ロジック自体は同等であるため、差分の特定は容易。

---

## 判断2: 各 hook の移植方針

### 共通設計

全 hook に共通する Python 実装の設計方針:

```python
# 共通パターン
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # .claude/hooks/ → project root

def read_stdin() -> dict:
    """stdin から JSON を読み取る。失敗時は空辞書を返す。"""
    try:
        return json.loads(sys.stdin.read())
    except Exception:
        return {}

def write_json(data: dict) -> None:
    """stdout に JSON を出力する。"""
    json.dump(data, sys.stdout, ensure_ascii=False)

def utc_now() -> str:
    """UTC タイムスタンプを ISO 8601 形式で返す。"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def normalize_path(file_path: str) -> str:
    """絶対パスを PROJECT_ROOT からの相対パスに正規化する。"""
    try:
        return str(Path(file_path).resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return file_path
```

**エラーハンドリング方針**: 全 hook は最外層で `try/except` し、例外発生時は `exit(0)` で終了する。hook の障害で Claude の動作をブロックしない。

**パスの扱い**: `pathlib.Path` を使用し、Windows バックスラッシュと Unix スラッシュの両方を透過的に処理する。正規化後の相対パスは POSIX 形式（フォワードスラッシュ）で統一する（`PurePosixPath` または `.as_posix()`）。

### pre-tool-use.py

**元の bash 版**: 163 行
**責務**: ファイルパスベースの PG/SE/PM 権限等級判定

**Python 移植設計**:

```
入力: stdin JSON { tool_name, tool_input: { file_path?, command? } }
出力:
  PG/SE級 → exit 0（許可）
  PM級 → stdout に hookSpecificOutput JSON（deny）

処理フロー:
  1. stdin JSON パース
  2. tool_name 取得
  3. 読み取り専用ツール判定 → PG級（Read, Glob, Grep, WebSearch, WebFetch）
  4. file_path / command 取得
  5. パス正規化（絶対→相対）
  6. パスパターンマッチング:
     - docs/specs/*.md, docs/adr/*.md → PM
     - .claude/rules/**/*.md → PM
     - .claude/settings*.json → PM
     - docs/* (上記以外) → SE
     - src/* → SE
     - その他 → SE
  7. AUDITING フェーズの特別処理（PG級ツール許可）
  8. ログ記録（.claude/logs/permission.log, 100文字トランケート）
  9. PM級の場合 hookSpecificOutput を stdout に出力
```

**bash 版からの改善点**:
- `re` モジュールによるパスマッチング（grep -qE の代替）
- `pathlib` による確実なパス正規化（Windows パス対応）
- jq フォールバックロジックが不要（`json.loads` 一発）
- `current-phase.md` の読み取りを `Path.read_text()` で安全に実行

**影式固有のカスタマイズ**:
- PM 保護パスに影式固有のパスを追加可能（設計段階では LAM テンプレートと同一）
- ログ出力の文字コードを UTF-8 に明示（日本語メッセージ対応）

### post-tool-use.py

**元の bash 版**: 161 行
**責務**: TDD パターン記録 + doc-sync-flag + ループログ記録

**Python 移植設計**:

```
入力: stdin JSON { tool_name, tool_input: { command?, file_path? }, tool_response: { exitCode?, stdout? } }
出力: なし（常に exit 0）

処理フロー:
  1. stdin JSON パース
  2. tool_name, command, file_path, exitCode, stdout を取得

  [責務1: TDD パターン記録]
  3. Bash ツール + テストコマンド判定（pytest, npm test, go test）
  4. 前回結果を .claude/last-test-result から読み取り
  5. 失敗時: .claude/tdd-patterns.log に FAIL エントリ追記
  6. 成功（前回失敗）: PASS (previously failed) エントリ追記
  7. .claude/last-test-result を更新

  [責務2: doc-sync-flag]
  8. Edit/Write ツール判定
  9. file_path を正規化
  10. src/ 配下かチェック（影式では kage_shiki/ も対象とすべきか検討）
  11. .claude/doc-sync-flag に未記録なら追記（重複防止）

  [責務3: ループログ]
  12. .claude/lam-loop-state.json が存在する場合
  13. tool_events 配列に追記
  14. アトミック書き込み（一時ファイル → rename）
```

**bash 版からの改善点**:
- テストコマンド判定を正規表現で明確に定義
- ファイル書き込みのアトミック性を `tempfile` + `os.replace()` で保証（Windows でも動作）
- jq なしフォールバックの「JSON を壊す」問題を完全に回避

**影式固有のカスタマイズ**:
- src/ パスの判定を影式のディレクトリ構造に合わせて調整（`src/kage_shiki/` が主要パス）

### lam-stop-hook.py

**元の bash 版**: 689 行（最も複雑）
**責務**: 自律ループの収束判定（Green State チェック）

**Python 移植設計**:

```
入力: stdin JSON { stop_hook_active? }
出力:
  停止 → exit 0（何も出力しない）
  継続 → stdout に { "decision": "block", "reason": "..." }

処理フロー:
  STEP 0: 再帰防止チェック（stop_hook_active=true → exit 0）
  STEP 1: lam-loop-state.json 確認（なし → exit 0, active=false → exit 0）
  STEP 2: 反復上限チェック（iteration >= max_iterations → 停止）
  STEP 3: コンテキスト残量チェック（PreCompact 直近10分以内 → 停止）
  STEP 4: Green State 判定
    G1: テスト実行（subprocess.run + timeout）
    G2: lint 実行（subprocess.run + timeout）
    G5: セキュリティチェック（依存脆弱性 + シークレットスキャン）
  STEP 5: エスカレーション条件（テスト数減少、同一Issue再発）
  STEP 5b: Green State 総合判定
  STEP 6: 継続（iteration インクリメント + block 出力）
```

**bash 版からの改善点**:
- `subprocess.run(timeout=...)` で `timeout` コマンドの代替（Windows 互換）
- `json` モジュールで状態ファイルの読み書き（jq/python3/sed の三段階フォールバック不要）
- `os.path.getmtime()` で `stat` コマンドの代替
- `datetime` で `date -d` の代替
- テスト/lint ツール検出ロジックを辞書駆動で整理（R-2 準拠）
- 一時ファイル処理を `tempfile.NamedTemporaryFile` で安全に実装

**影式固有のカスタマイズ**:
- G1: テストフレームワークは `pytest` 固定（影式は Python 単一言語）
- G2: lint ツールは `ruff` 固定
- G5: `pip-audit` または `safety` を検出（npm audit は不要）
- テスト実行コマンド: `python -m pytest`（影式の標準）

**設計上の注意**:
- lam-stop-hook は 689 行の巨大スクリプトだが、Python 化により 200-300 行に圧縮可能
- 関数分割を徹底し、各 STEP を独立した関数にする
- Green State の各条件（G1, G2, G5）も独立関数にする

### pre-compact.py

**元の bash 版**: 42 行（最も単純）
**責務**: コンテキスト圧縮前の状態保存

**Python 移植設計**:

```
入力: stdin JSON（内容は参照しない）
出力: なし（常に exit 0）

処理フロー:
  1. .claude/pre-compact-fired にタイムスタンプを記録
  2. SESSION_STATE.md に PreCompact 発火セクションを追記/更新（冪等）
  3. lam-loop-state.json が存在すればバックアップ作成
```

**bash 版からの改善点**:
- `sed -i` の代わりに Python でファイル内容を読み書き（冪等更新が明確）
- `shutil.copy2()` でバックアップ作成

---

## 判断3: settings.json のマージ戦略

### 現状分析

| ファイル | 役割 | hooks 定義 |
|---------|------|-----------|
| `.claude/settings.json` | プロジェクト共通設定（Git 管理） | なし |
| `.claude/settings.local.json` | ローカル固有設定（Git 管理※） | Stop + Notification（notify-sound.py） |
| LAM 4.0.1 `settings.json` | テンプレート | PreToolUse + PostToolUse + Stop + PreCompact |

※ 影式では `settings.local.json` も Git 管理されている（通常は gitignore 対象だが、チーム共有のため）。

### マージ方針

**原則**: `settings.json` に LAM 4.0.1 の hooks + permissions を導入し、`settings.local.json` に影式固有の hooks + Python 権限を維持する。Claude Code は同一イベントの hooks を配列として結合するため、Stop イベントで LAM の stop-hook と影式の notify-sound の両方が実行される。

#### settings.json（マージ後）

```json
{
  "permissions": {
    "allow": [
      "Bash(ls *)",
      "Bash(cat *)",
      "Bash(grep *)",
      "Bash(find *)",
      "Bash(pwd)",
      "Bash(du *)",
      "Bash(file *)",
      "Bash(git status)",
      "Bash(git status *)",
      "Bash(git log *)",
      "Bash(git diff *)",
      "Bash(git show *)",
      "Bash(git branch *)",
      "Bash(pytest *)",
      "Bash(npm test *)",
      "Bash(go test *)",
      "Bash(npm list *)",
      "Bash(pip list *)",
      "Bash(pip show *)",
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
      "Bash(brew *)"
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
      "Bash(cp *)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "hooks": [{
          "type": "command",
          "command": "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/pre-tool-use.py"
        }]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write|Bash",
        "hooks": [{
          "type": "command",
          "command": "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/post-tool-use.py"
        }]
      }
    ],
    "Stop": [
      {
        "hooks": [{
          "type": "command",
          "command": "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/lam-stop-hook.py"
        }]
      }
    ],
    "PreCompact": [
      {
        "hooks": [{
          "type": "command",
          "command": "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/pre-compact.py"
        }]
      }
    ]
  }
}
```

#### settings.local.json（変更なし）

```json
{
  "permissions": {
    "allow": [
      "Bash(python *)",
      "Bash(python3 *)",
      "Bash(pip *)",
      "Bash(pip3 *)",
      "Bash(uv *)",
      "Bash(ruff *)",
      "Bash(mypy *)",
      "Bash(black *)",
      "Bash(isort *)",
      "Bash(pytest *)",
      "Bash(python -m *)",
      "Bash(python3 -m *)"
    ]
  },
  "hooks": {
    "Stop": [
      {
        "hooks": [{
          "type": "command",
          "command": "python .claude/hooks/notify-sound.py stop",
          "timeout": 10
        }]
      }
    ],
    "Notification": [
      {
        "hooks": [{
          "type": "command",
          "command": "python .claude/hooks/notify-sound.py notification",
          "timeout": 10
        }]
      }
    ]
  }
}
```

### permissions の変更点

| 変更 | 説明 | 理由 |
|------|------|------|
| `python *` を settings.json の allow から削除 | LAM 4.0.1 では ask に分類 | settings.local.json で allow にオーバーライドされるため実影響なし。テンプレートとの整合性を優先 |
| `python3 *`, `python -m *`, `python3 -m *` を settings.json から削除 | 同上 | settings.local.json で allow にオーバーライド |
| `ruff check --fix *`, `ruff format *` を settings.json に追加 | LAM 4.0.1 の PG 級ツール | AUDITING フェーズでの自動修正に必要 |
| `npx prettier *`, `npx eslint --fix *` を settings.json に追加 | LAM 4.0.1 の PG 級ツール | 影式では不使用だが、テンプレート互換性のため含める |
| `git status *` を維持 | 影式固有 | LAM 4.0.1 にはないが、影式の運用で必要 |
| `pip show *` を維持 | 影式固有 | 依存パッケージの確認に使用 |

### Stop イベントの hooks 実行順序

Claude Code は settings.json と settings.local.json の hooks をマージする。Stop イベントでは:

1. `lam-stop-hook.py`（settings.json 由来） — ループ収束判定
2. `notify-sound.py stop`（settings.local.json 由来） — 完了サウンド再生

両方が実行される。lam-stop-hook.py が `{"decision": "block"}` を返した場合、Claude は停止せず次のサイクルに進む。この場合 notify-sound.py は実行されない（Stop イベントが完了しないため）。lam-stop-hook.py が何も出力せず exit 0 した場合（停止許可）、notify-sound.py が実行されてサウンドが再生される。

---

## 判断4: hooks のテスト戦略

### LAM 4.0.1 の bash テスト構成

| ファイル | テストケース数 | 内容 |
|---------|-------------|------|
| test-helpers.sh | - | 共通アサーション関数 |
| test-pre-tool-use.sh | 7 | 権限等級判定のスモークテスト |
| test-post-tool-use.sh | 10 | TDD パターン + doc-sync-flag |
| test-stop-hook.sh | 7 | ループ収束判定 |
| test-loop-integration.sh | 5 | ループ全体の統合テスト |

### Python テストへの移植方針

**決定**: bash テストは移植しない。代わりに pytest ベースのテストを新規作成する。

**理由**:
1. bash テストは bash スクリプトのテストとして設計されている（shellcheck, echo | bash 等）
2. Python 版 hook は Python の関数として実装するため、pytest で直接テスト可能
3. 影式の既存テストインフラ（pytest, conftest.py, tmp_path fixture 等）を活用可能
4. Windows 環境での bash テスト実行は不安定

### テストファイル構成

```
tests/
  test_hooks/
    __init__.py
    conftest.py            # 共通フィクスチャ（tmp_path, mock stdin/stdout）
    test_pre_tool_use.py   # pre-tool-use.py のテスト
    test_post_tool_use.py  # post-tool-use.py のテスト
    test_stop_hook.py      # lam-stop-hook.py のテスト
    test_pre_compact.py    # pre-compact.py のテスト
    test_integration.py    # ループ統合テスト
```

### テスト設計方針

**hook スクリプトの構造**: 各 hook の `.py` ファイルは、`main()` 関数と個別のロジック関数に分割する。`if __name__ == "__main__":` ガードの下で `main()` を呼ぶ構造にし、テストからは関数を直接インポートしてテストする。

```python
# .claude/hooks/pre-tool-use.py の構造例
def classify_permission(tool_name: str, file_path: str, command: str, phase: str) -> tuple[str, str]:
    """PG/SE/PM を判定し、(level, reason) を返す。"""
    ...

def main() -> None:
    input_data = read_stdin()
    ...

if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
```

```python
# tests/test_hooks/test_pre_tool_use.py
from importlib.util import spec_from_file_location, module_from_spec

def load_hook():
    """hook スクリプトをモジュールとしてロードする。"""
    spec = spec_from_file_location("pre_tool_use", ".claude/hooks/pre-tool-use.py")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

class TestClassifyPermission:
    def test_read_tool_is_pg(self):
        mod = load_hook()
        level, reason = mod.classify_permission("Read", "src/main.py", "", "")
        assert level == "PG"

    def test_specs_path_is_pm(self):
        mod = load_hook()
        level, reason = mod.classify_permission("Edit", "docs/specs/foo.md", "", "")
        assert level == "PM"
```

### テストカバレッジ目標

| hook | 最低テストケース数 | カバレッジ目標 |
|------|-------------------|-------------|
| pre-tool-use.py | 7（bash 版と同等） | 90%+ |
| post-tool-use.py | 10（bash 版と同等） | 90%+ |
| lam-stop-hook.py | 12（bash 版 7 + 統合 5） | 85%+（subprocess 呼び出し部分は mock） |
| pre-compact.py | 4 | 90%+ |

### テスト実行方法

```bash
# hook テストのみ実行
pytest tests/test_hooks/ -v

# 全テスト（既存 722 件 + hook テスト）
pytest
```

---

## リスクと対策

| # | リスク | 影響度 | 発生確率 | 対策 |
|---|--------|--------|---------|------|
| R1 | Python hook の起動遅延が累積し、操作体感に影響する | 中 | 低 | PreToolUse は全ツール呼び出しで発火するため最も影響大。50-150ms の遅延は公式 timeout（600s）に対して無視できるが、体感で遅いと感じた場合は hook 内のファイル I/O を最小化する |
| R2 | LAM テンプレートの bash 版が更新された場合、Python 版への手動マージが必要 | 中 | 中 | ロジックの同等性を担保するため、bash 版の各 STEP/責務を Python 版でも同一構造で実装する。差分の特定を容易にする |
| R3 | lam-stop-hook.py が subprocess で pytest/ruff を実行する際、Windows パスの問題が発生する | 中 | 低 | `subprocess.run()` に `shell=True` は使用しない。コマンドを list 形式で渡す。`shutil.which()` でコマンドの存在を事前確認 |
| R4 | settings.json と settings.local.json の hooks マージ順序が想定と異なる | 低 | 低 | 公式ドキュメントでマージ動作を確認済み。配列として結合される。Phase 3 の検証チェックリストで動作確認する |
| R5 | hook スクリプトのインポートパスが pytest から見えない | 低 | 中 | `importlib` を使用して動的にモジュールをロードする。conftest.py で共通のローダー関数を提供 |
| R6 | PreCompact イベントが公式ドキュメント未掲載（bash 版のコメント）で将来削除される可能性 | 低 | 低 | 2026-03 時点の公式 hooks reference には `PreCompact` が正式にイベントとして記載されている。リスクは解消済み |

### ロールバック計画

Phase 3 の hooks 導入が失敗した場合:

1. `.claude/hooks/` から LAM 4.0.1 の Python hook ファイルを削除
2. `settings.json` から hooks セクションを除去（permissions は維持可能）
3. `settings.local.json` の notify-sound.py hooks は影響なし
4. Phase 1-2 の成果は維持される（hooks は完全に独立）

---

## 調査結果: Claude Code hooks の Windows 対応状況

以下は WebSearch + WebFetch で確認した 2026-03 時点の公式情報:

### 公式ドキュメント（code.claude.com/docs/en/hooks）

- hooks のタイプは `command`, `http`, `prompt`, `agent` の 4 種類
- command hooks はシェルコマンドを実行する。stdin に JSON、stdout に結果
- **スクリプト言語の制限はない**: `command` フィールドに書かれたコマンドがそのまま実行される。`python script.py` でも `bash script.sh` でも可
- `$CLAUDE_PROJECT_DIR` でプロジェクトルートを参照可能
- イベントは 17 種類に拡大（SessionStart, UserPromptSubmit, PreToolUse, PermissionRequest, PostToolUse, PostToolUseFailure, Notification, SubagentStart, SubagentStop, Stop, TeammateIdle, TaskCompleted, InstructionsLoaded, ConfigChange, WorktreeCreate, WorktreeRemove, PreCompact, SessionEnd）
- デフォルト timeout: command=600s, prompt=30s, agent=60s

### Windows 実践報告（netnerds.net 2026-02）

- bash hook は Git Bash 経由で動作する（起動 10-50ms）
- PowerShell hook は起動に 300-500ms かかり、複数 hook で累積する
- Python は hooks の JSON パース用に使える（`python3 -c` 形式）
- CRLF 問題は `.gitattributes` で `*.sh text eol=lf` を設定すれば回避可能
- パスはフォワードスラッシュで統一すべき

### 影式への示唆

- `python .claude/hooks/xxx.py` 形式は公式に動作する
- notify-sound.py の既存実績が裏付け
- Python hook は bash hook と比較して起動が 50-100ms 程度遅いが、公式 timeout（600s）に対して無視できる差
