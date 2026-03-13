# Security & Automation Protocols (Command Safety)

本ドキュメントは、"Living Architect" がターミナルコマンドを実行する際の安全基準（Allow List / Deny List）と、自動化のルールを定義する。

## 1. Core Principle (基本原則)

- **Safety First**: システムの破壊、データの消失、意図しない外部通信を防ぐことを最優先とする。
- **Automation with Consent**: 安全が確認された操作は自動化し（Allow List）、リスクのある操作は必ずユーザーの承認を得る（Deny List）。

## 2. Command Lists (コマンドリスト)

### A. Allow List (Auto-Run Safe)

以下のコマンドは、**副作用がなく（Read-Only）、かつローカル環境で完結するもの**であるため、ユーザー承認なしで実行してよい（`SafeToAutoRun: true`）。

| Category               | Commands                                                      | Notes                              |
| :--------------------- | :------------------------------------------------------------ | :--------------------------------- |
| **File System (Read)** | `ls`, `cat`, `grep`, `pwd`, `du`, `file`                      | ファイル内容の読み取り、検索。     |
| **Git (Read)**         | `git status`, `git log`, `git diff`, `git show`, `git branch` | リポジトリ状態の確認。             |
| **Testing (Local)**    | `pytest`, `pytest -v`, `pytest --tb=short`                    | **ローカルでの**テスト実行。       |
| **Linting (Read)**     | `ruff check`, `ruff format --check`                           | コードスタイル確認（変更なし）。   |
| **Package Info**       | `pip list`, `pip show`                                        | インストール済みパッケージの確認。 |
| **Process Info**       | `ps`, `top` (batch mode)                                      | プロセス状態の確認。               |

### B-1. Deny List — 実行禁止（Layer 0: deny）

以下のコマンドは **不可逆な操作** であり、AI による実行を禁止する。

| Category                | Commands                                                            | Risks                                              |
| :---------------------- | :------------------------------------------------------------------ | :------------------------------------------------- |
| **File System (Delete)**| `rm`, `rm -rf`                                                      | 不可逆なデータ消失。                               |
| **File System (Move)**  | `mv`                                                                | 不可逆なファイル消失・上書き。                     |
| **Permission Change**   | `chmod`, `chown`                                                    | セキュリティ境界の破壊。                           |
| **System Mutation**     | `apt`, `yum`, `brew`, `systemctl`, `service`, `reboot`, `shutdown`  | システム設定の変更、パッケージ導入、再起動。       |
| **find (destructive)**  | `find -delete`, `find -exec rm`, `find -exec chmod`, `find -exec chown` | 再帰的な不可逆操作。                          |

### B-2. Ask List — 承認必須（Layer 0: ask）

以下のコマンドは **承認を得てから実行する**。

| Category                | Commands                                                                    | Risks                                                        |
| :---------------------- | :-------------------------------------------------------------------------- | :----------------------------------------------------------- |
| **File System (Write)** | `cp`, `touch`, `mkdir`                                                      | 意図しないファイル作成・コピー。                             |
| **File Search**         | `find`                                                                      | 通常検索（破壊的パターンは B-1 deny）。                      |
| **Git (Remote/Write)**  | `git push`, `git pull`, `git fetch`, `git clone`, `git commit`, `git merge` | リモートリポジトリへの影響、コンフリクト発生。               |
| **Network**             | `curl`, `wget`, `ssh`, `ping`, `nc`                                         | 外部へのデータ送信、不正なスクリプトのダウンロード。         |
| **Build/Run**           | `python main.py`, `python -m kage_shiki`                                    | アプリケーションの実行（無限ループやリソース枯渇のリスク）。 |
| **Linting (Write)**     | `ruff check --fix`, `ruff format`                                           | ファイルを自動修正する（変更を伴う）。v4.0.0 以降は PG級自動修正可（本ドキュメント Section 5 参照）。 |
| **Package Install**     | `pip install`, `pip uninstall`                                              | 環境への変更。                                               |

> **Note**: ファイルリネームが必要な場合、`mv` は Deny List に含まれるため以下の代替手段を用いる:
> - `Read` → `Write`（新名称で作成）→ `Write`（旧ファイルを空にするか削除依頼）
> - `git mv`（Git 追跡下のファイルの場合。ユーザー承認は必要）

### C. Gray Area Protocol (判断基準)

上記リストに含まれないコマンド、または引数によって挙動が大きく変わるコマンドについては、**原則として「Deny List」扱い（承認必須）**とする。

- 例: `make` (Makefile の中身によるため危険)
- 例: シェルスクリプト (`./script.sh`)

## 3. Automation Workflow

1.  **Check**: 実行したいコマンドが Allow List に含まれているか確認する。
2.  **Decide**:
    - **Included**: `SafeToAutoRun: true` を設定し、ツールを実行する。
    - **Excluded**: `SafeToAutoRun: false` を設定し、ユーザーに承認を求める。
3.  **Log**: 実行結果を確認し、エラーが出た場合はユーザーに報告する。

## 4. Emergency Stop

ユーザーから「止めて」「ストップ」等の指示があった場合、直ちに実行中のコマンドを停止（`Ctrl+C` / `SIGINT`）し、全ての自動化プロセスを中断すること。

## Section 5: Hooks-Based Permission System（v4.0.0）

v4.0.0 で導入された hooks ベースの権限管理システム。

### PreToolUse Hook

ファイルパスに基づく PG/SE/PM の動的判定を行う:

- PM級パス（承認必須）: `docs/specs/`, `docs/adr/`, `docs/internal/`, `.claude/rules/`, `pyproject.toml`
- SE級パス（修正後報告）: `src/kage_shiki/`, `tests/`, `config/`, `docs/`（上記以外）
- PG級ツール（常に許可）: Read, Glob, Grep, WebSearch, WebFetch

実装: `.claude/hooks/pre-tool-use.py`（Python 版、Windows 互換）
定義: `.claude/rules/permission-levels.md`

### PostToolUse Hook

テスト実行結果の自動記録とドキュメント同期フラグの管理:

1. **TDD パターン記録**: テスト失敗→成功パターンを `.claude/tdd-patterns.log` に記録
2. **doc-sync-flag**: `src/` 配下のファイル変更を `.claude/doc-sync-flag` に記録
3. **ループログ**: 自律ループ時の tool_events を `lam-loop-state.json` に追記

### Stop Hook (lam-stop-hook)

自律ループの収束判定（Green State チェック）:
- G1: テスト全パス、G2: lint エラーゼロ、G3: 対応可能 Issue ゼロ、G4: 仕様差分ゼロ、G5: セキュリティチェック通過

### PreCompact Hook

コンテキスト圧縮前の自動状態保存。SESSION_STATE.md にタイムスタンプを記録。

## Section 6: Recommended Security Tools（v4.0.0）

| ツール | 用途 | 影式での利用 |
|--------|------|------------|
| `ruff` | Python linter + formatter | 導入済み（PG級自動修正可） |
| `pip-audit` | Python 依存パッケージの脆弱性チェック | Green State G5 で使用 |
| `safety` | Python 依存パッケージの安全性チェック | pip-audit の代替 |
| `bandit` | Python セキュリティ静的解析 | 将来導入検討 |
