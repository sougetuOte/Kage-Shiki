# .claude/ 追加ファイル差分分析

## 概要

本ドキュメントは、LAM 4.0.1 移行に伴い、既存の差分分析（CLAUDE.md、rules/、commands/skills/agents/、docs/internal/）でカバーされていなかった `.claude/` 配下の設定・状態・hookファイルの差分を分析する。

分析対象:
1. `current-phase.md` — フェーズ状態ファイル
2. `settings.json` — Claude Code 権限設定
3. `settings.local.json` — ローカル固有設定（現行のみ）
4. `hooks/` — hook スクリプト群
5. `states/` — フェーズ状態 JSON
6. `skills/skill-creator/references/` — スキル作成リファレンス

---

## current-phase.md 差分

### 差分の程度: 微差（1行のみ）

両ファイルの内容はほぼ同一。唯一の差分はパスの記述:

| 箇所 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| 行25: 参照するルール | `rules/phase-rules.md` | `.claude/rules/phase-rules.md` |

LAM 4.0.1 側が `.claude/` プレフィックス付きの完全パスを使用している。影式側は省略形。

### 移行判断

影式側のパスも動作上問題ないが、LAM 4.0.1 に合わせて `.claude/` プレフィックス付きに統一するのが望ましい。軽微な変更。

---

## settings.json 差分

### 差分の程度: 大（構造的な違いあり）

#### permissions.allow の差分

| エントリ | 現行 | LAM 4.0.1 | 備考 |
|---------|------|-----------|------|
| `Bash(git status *)` | あり | なし | 現行のみ。LAM 4.0.1 は `git status`（引数なし）のみ |
| `Bash(python *)` | allow | **ask** | LAM 4.0.1 では python 実行を ask に移動 |
| `Bash(python3 *)` | allow | なし | LAM 4.0.1 には python3 エントリ自体がない |
| `Bash(python -m *)` | allow | なし | LAM 4.0.1 には python -m エントリがない |
| `Bash(python3 -m *)` | allow | なし | LAM 4.0.1 には python3 -m エントリがない |
| `Bash(pip show *)` | allow（現行のみ） | なし | 影式固有の追加 |
| `Bash(npx prettier *)` | なし | allow | LAM 4.0.1 で新規追加（PG級ツール） |
| `Bash(npx eslint --fix *)` | なし | allow | LAM 4.0.1 で新規追加（PG級ツール） |
| `Bash(ruff check --fix *)` | なし | allow | LAM 4.0.1 で新規追加（PG級ツール） |
| `Bash(ruff format *)` | なし | allow | LAM 4.0.1 で新規追加（PG級ツール） |

**重要な差分**: LAM 4.0.1 では `python *` を **ask** に格下げしている。これは「python 実行はリスクがある」という判断に基づく。一方、影式では Python がメイン言語のため `python *` を allow にしている（`settings.local.json` でも重複して allow 設定）。

#### permissions.deny の差分

deny リストは両者完全に同一:
- `rm *`, `rm -rf *`, `mv *`, `chmod *`, `chown *`, `systemctl *`, `service *`, `reboot`, `shutdown *`, `apt *`, `yum *`, `brew *`

#### permissions.ask の差分

| エントリ | 現行 | LAM 4.0.1 | 備考 |
|---------|------|-----------|------|
| `Bash(python *)` | なし（allow） | ask | LAM 4.0.1 で ask に配置 |
| `Bash(git pull *)` | あり | あり | 同一 |
| `Bash(git fetch *)` | あり | あり | 同一 |
| `Bash(git clone *)` | あり | あり | 同一 |
| その他 git/curl/wget/ssh 等 | あり | あり | 同一 |

#### hooks セクション（LAM 4.0.1 のみ）

LAM 4.0.1 の `settings.json` には `hooks` セクションが追加されている。現行にはこのセクションがない:

```json
"hooks": {
  "PreToolUse": [
    { "hooks": [{ "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/pre-tool-use.sh" }] }
  ],
  "PostToolUse": [
    { "matcher": "Edit|Write|Bash",
      "hooks": [{ "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/post-tool-use.sh" }] }
  ],
  "Stop": [
    { "hooks": [{ "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/lam-stop-hook.sh" }] }
  ],
  "PreCompact": [
    { "hooks": [{ "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/pre-compact.sh" }] }
  ]
}
```

4つの hook イベント:
- **PreToolUse**: 全ツール呼び出し前に権限等級判定（PG/SE/PM）
- **PostToolUse**: Edit/Write/Bash 実行後に TDD パターン記録 + doc-sync-flag 設定
- **Stop**: 自律ループの収束判定（Green State チェック）
- **PreCompact**: コンテキスト圧縮前の SESSION_STATE.md 自動保存

### 移行時の注意

影式の `settings.local.json` で python/ruff/pytest 等を allow にしているため、LAM 4.0.1 の `settings.json` をそのまま採用しても `settings.local.json` が上書きする。ただし hooks セクションの統合が必要。

---

## settings.local.json（現行のみ）

### 内容

影式固有のローカル設定ファイル。Git にコミットされており、プロジェクト固有の追加権限と hook を定義:

#### permissions.allow
- `Bash(python *)`, `Bash(python3 *)` — Python 実行の許可
- `Bash(pip *)`, `Bash(pip3 *)`, `Bash(uv *)` — パッケージ管理
- `Bash(ruff *)`, `Bash(mypy *)`, `Bash(black *)`, `Bash(isort *)` — コード品質ツール
- `Bash(pytest *)` — テスト実行
- `Bash(python -m *)`, `Bash(python3 -m *)` — モジュール実行

#### hooks
- **Stop**: `python .claude/hooks/notify-sound.py stop` (timeout: 10秒) — 完了時に Windows サウンド再生
- **Notification**: `python .claude/hooks/notify-sound.py notification` (timeout: 10秒) — 承認待ち時にサウンド再生

### 影式での役割

1. **Python プロジェクト固有の権限拡張**: LAM 4.0.1 のジェネリックな settings.json では python が ask に分類されているが、影式は Python プロジェクトのため allow が必須
2. **通知サウンド**: Windows 環境固有の UX 改善機能。`tada.wav`（完了時）と `Windows Exclamation.wav`（承認待ち時）を4倍に増幅して再生

### 移行時の注意

LAM 4.0.1 の hooks（Stop に `lam-stop-hook.sh`）と影式固有の hooks（Stop に `notify-sound.py`）が競合する。Stop イベントに両方のフックを登録する必要がある。`settings.json` と `settings.local.json` の hooks は**マージされる**（Claude Code の仕様）ため、`settings.json` に LAM の Stop hook、`settings.local.json` に影式の Stop hook を配置すれば共存可能。

---

## hooks/ 差分

### 現行の hooks（影式固有）

#### notify-sound.py（1ファイルのみ）

Windows 専用の通知サウンドスクリプト。56行。

- **機能**: Stop/Notification イベントで WAV ファイルを増幅再生
- **サウンドマッピング**: `stop` → `tada.wav`, `notification` → `Windows Exclamation.wav`
- **増幅**: GAIN=4.0 で音量を4倍に増幅（`winsound` モジュール使用）
- **無効化**: 環境変数 `CLAUDE_NOTIFY_SOUND=0` で無効化可能
- **エラーハンドリング**: 例外を握り潰す（通知失敗でセッションをブロックしない）

LAM 4.0.1 には対応するファイルがない（プロジェクト固有機能のため）。

### LAM 4.0.1 の新規 hooks

#### pre-tool-use.sh（163行）

権限等級判定（PG/SE/PM）を行う PreToolUse hook。

**動作概要**:
1. stdin から JSON（tool_name, tool_input）を受信
2. 読取り専用ツール（Read/Glob/Grep/WebSearch/WebFetch）→ PG級で即時許可
3. ファイルパスベースで判定:
   - `docs/specs/*.md`, `docs/adr/*.md` → PM級（deny）
   - `.claude/rules/**/*.md` → PM級（deny）
   - `.claude/settings*.json` → PM級（deny）
   - `docs/`（上記以外）→ SE級（許可+ログ）
   - `src/` → SE級（許可+ログ）
   - その他 → SE級（安全側）
4. AUDITING フェーズでは PG級ツール（prettier/eslint/ruff）を許可
5. PM級判定時は `hookSpecificOutput` 形式で deny を返す
6. ログを `.claude/logs/permission.log` に記録（100文字トランケート）

**jq なし環境のフォールバック**: grep + sed で簡易パース。ツール名が取得できない場合は SE級扱い。

**Windows 環境での注意点**:
- bash スクリプトのため Git Bash/MSYS2 が必要
- `$CLAUDE_PROJECT_DIR` の展開がバックスラッシュパスだと動作しない可能性
- `sed -n` のパターン抽出が Windows の改行コード（CRLF）で失敗する可能性

#### post-tool-use.sh（161行）

PostToolUse hook。Edit/Write/Bash 実行後の処理。

**3つの責務**:
1. **TDD パターン検出**: テストコマンド（pytest/npm test/go test）の結果を記録
   - 失敗時: `.claude/tdd-patterns.log` に FAIL エントリ追記
   - 成功（前回失敗あり）: PASS（previously failed）エントリ追記
   - `.claude/last-test-result` に最新結果を保存
2. **doc-sync-flag 設定**: src/ 配下の Edit/Write を検知し `.claude/doc-sync-flag` に記録
   - 重複防止: 既記録パスはスキップ（承認疲れ防止）
   - 絶対パス→相対パス正規化
3. **ループログ記録**: `lam-loop-state.json` が存在する場合、tool_events 配列に追記
   - jq によるアトミック書き込み（Stop hook との競合防止）

**Windows 環境での注意点**:
- `date -u` コマンドは Git Bash で動作するが、形式が異なる場合がある
- ファイルパスの `${PROJECT_ROOT}/` プレフィックス除去ロジックがバックスラッシュで失敗する可能性

#### lam-stop-hook.sh（689行）

自律ループの収束判定を行う Stop hook。最も複雑なスクリプト。

**判定フロー（6ステップ）**:
1. **再帰防止チェック**: `stop_hook_active=true` なら即座に exit 0
2. **状態ファイル確認**: `lam-loop-state.json` がなければ通常停止
3. **反復上限チェック**: iteration >= max_iterations なら強制停止
4. **コンテキスト残量チェック**: PreCompact 発火フラグが直近10分以内なら停止
5. **Green State 判定**:
   - G1: テストフレームワーク自動検出（pytest/npm/go/make）+ 実行（timeout 120秒）
   - G2: lint ツール自動検出（ruff/npm lint/eslint/make lint）+ 実行（timeout 60秒）
   - G5: セキュリティチェック（npm audit/pip-audit/safety + シークレットスキャン）
6. **エスカレーション条件**: テスト数減少・同一Issue再発を検出

**収束時の動作**:
- Green State 達成 → ループログ保存 → 状態ファイル削除 → exit 0（停止）
- Green State 未達 → iteration インクリメント → `{"decision": "block", "reason": "..."}` を stdout に出力（継続）

**jq なし環境のフォールバック**: python3 → sed の三段階フォールバック。JSON パースユーティリティ関数（`json_get_string`, `json_get_number`, `json_get_bool`）を定義。

**Windows 環境での注意点**:
- `timeout` コマンドは Git Bash では `timeout` (GNU coreutils) が必要。Windows の `timeout` コマンドとは別物
- `stat -c %Y`（GNU）と `stat -f %m`（BSD）の両方をフォールバックしているが、Windows Git Bash では `stat --format=%Y` が正しい場合がある
- `mktemp` コマンドの動作は Git Bash で問題ないが、テンポラリディレクトリのパスが異なる
- `date -d` による日付パースは Git Bash で動作するが、MSYS2 の date とは挙動が異なる場合がある

#### pre-compact.sh（42行）

PreCompact hook。コンテキスト圧縮前の状態保存。

**動作**:
1. `.claude/pre-compact-fired` にタイムスタンプを記録（Stop hook が参照）
2. `SESSION_STATE.md` に PreCompact 発火セクションを追記/更新（冪等）
3. ループ中なら `lam-loop-state.json` のバックアップを作成

**注意**: PreCompact は公式ドキュメント未掲載だが動作確認済み（2026-03時点）とコメントあり。

**Windows 環境での注意点**:
- `sed -i` は Git Bash で動作するが、バックアップファイルの挙動が GNU sed と異なる場合がある
- `cp` コマンドは問題なし

### hooks テスト

LAM 4.0.1 には `.claude/hooks/tests/` 配下に5つのテストスクリプトがある:

#### test-helpers.sh（92行）

テスト共通ヘルパー関数。以下のアサーション関数を提供:
- `assert_exit`: 終了コードの検証
- `assert_stdout_contains`: stdout にパターンが含まれるか検証
- `assert_stdout_empty`: stdout が空か検証
- `assert_file_exists` / `assert_file_not_exists`: ファイル存在の検証
- `assert_json_field`: JSON ファイルのフィールド存在検証（jq 依存）

呼び出し元で `PASS=0`, `FAIL=0` を初期化する前提。

#### test-pre-tool-use.sh（141行）

PreToolUse hook の7テストケース:
- TC-1: shellcheck 構文チェック
- TC-2: Read ツール → PG 許可（exit 0）
- TC-3: Edit docs/specs/foo.md → PM deny
- TC-4: Edit .claude/rules/auto-generated/draft-001.md → PM deny（サブディレクトリ保護）
- TC-5: 絶対パス正規化 → PM deny
- TC-6: Edit src/main.py → SE 許可（exit 0）
- TC-7: ログトランケート（100文字超コマンド）

#### test-post-tool-use.sh（370行）

PostToolUse hook の10テストケース:
- T1: pytest 失敗 → tdd-patterns.log に FAIL 記録
- T2: pytest 成功（前回失敗あり）→ 失敗→成功パターン記録
- T3: Edit + src/ 配下 → doc-sync-flag に記録
- T4: Write + src/ 配下 → doc-sync-flag に記録
- T5: Edit + docs/ 配下 → doc-sync-flag に記録されない
- T6: ループ状態ファイルあり → tool_events 追記
- T7: jq なし環境のフォールバック
- T8: npm test 失敗 → 記録
- T9: go test 失敗 → 記録
- T10: 非テストコマンド → 記録されない

#### test-stop-hook.sh（309行）

Stop hook の7テストケース:
- TC-1: shellcheck 構文チェック
- TC-2: 状態ファイルなし → exit 0（通過）
- TC-3: iteration >= max_iterations → 停止 + 状態ファイル削除
- TC-4: stop_hook_active=true → 再帰防止で exit 0
- TC-5: テスト失敗環境 → decision:block + iteration インクリメント
- TC-6: PreCompact 直近発火 → コンテキスト圧迫で停止
- TC-7: 状態ファイルスキーマ正当性（全フィールド存在確認）

#### test-loop-integration.sh（360行）

ループ統合テストの5シナリオ:
- S-1: 正常収束（Green State 達成 → 自動停止）
- S-2: PM級エスカレーション（テスト失敗 → block 継続 / active=false → 停止）
- S-3: 上限到達停止（iteration < max → 継続 / iteration == max → 強制停止）
- S-4: コンテキスト枯渇（PreCompact 発火 → ループ停止）
- S-5: ライフサイクル全体（初期化 → 失敗サイクル → 成功サイクル → 収束）

---

## states/ 差分

### 現行の states ファイル

#### phase-1-mvp.json

```json
{
  "feature": "phase-1-mvp",
  "description": "影式 Phase 1: 基盤 (MVP)",
  "phase": "BUILDING",
  "subphase": "implementation",
  "status": {
    "requirements": "approved",
    "design": "approved",
    "tasks": "approved",
    "implementation": "in_progress"
  },
  "approvals": { "requirements": "2026-03-03", "design": "2026-03-03", "tasks": "2026-03-03" },
  "scope": ["tkinter GUI + pystray 常駐", "Anthropic API 接続 + config.toml", ...],
  "created_at": "2026-03-03",
  "updated_at": "2026-03-03"
}
```

#### phase-2-autonomy.json

```json
{
  "feature": "phase-2a-foundation",
  "description": "影式 Phase 2a: 基盤強化",
  "phase": "BUILDING",
  "subphase": "implementation",
  "status": { ... },
  "approvals": { "requirements": "2026-03-06", ... },
  "scope": ["T-27", "T-28", "T-29", "T-30", "T-31", "T-32"],
  "created_at": "2026-03-06",
  "updated_at": "2026-03-06"
}
```

### LAM 4.0.1 の states ファイル

#### v4.0.0-immune-system.json

```json
{
  "feature": "v4.0.0-immune-system",
  "description": "LAM第3世代進化: 憲法型ハーネス→免疫系への移行",
  "phase": "BUILDING",
  "status": { "requirements": "approved", "design": "approved", "tasks": "approved" },
  "current_wave": 4,
  "current_task": null,
  "completed_at": "2026-03-08",
  "completed_tasks": ["T0-1", "T0-2", ..., "T4-2"],
  "approvals": { ... },
  "pillars": [
    "権限等級システム (PG/SE/PM)",
    "ループ統合 (full-review + 構造チェック)",
    "TDD内省→ルール自動生成",
    "ドキュメント自動追従",
    "収束条件・停止基準"
  ]
}
```

### スキーマの違い

| フィールド | 現行 | LAM 4.0.1 | 備考 |
|-----------|------|-----------|------|
| `subphase` | あり | なし | LAM 4.0.1 では不使用 |
| `status.implementation` | あり | なし | LAM 4.0.1 では完了判定が異なる |
| `current_wave` | なし | あり | Wave ベースの進捗管理 |
| `current_task` | なし | あり | 現在実行中のタスク |
| `completed_at` | なし | あり | 完了日 |
| `completed_tasks` | なし | あり | 完了タスクのリスト |
| `pillars` | なし | あり | フィーチャーの柱（概要） |
| `scope` | 文字列配列 | なし | LAM 4.0.1 では pillars に置換 |

### マイグレーション要否

**不要**。states ファイルはプロジェクト固有の進捗管理ファイルであり、影式の既存ファイル（phase-1-mvp.json, phase-2-autonomy.json）は影式のフェーズ管理に使用されている。LAM 4.0.1 の v4.0.0-immune-system.json は LAM 開発の進捗記録であり、影式には関係ない。

ただし、新しい LAM の機能（Wave 管理、current_task、completed_tasks 等）を影式の states ファイルに取り入れる場合は、スキーマの拡張が必要。`subphase` と `status.implementation` は現行のまま維持してよい。

---

## skill-creator/references/ 差分

### output-patterns.md

**完全同一**。73行、内容に差分なし。

### workflows.md

**完全同一**。29行、内容に差分なし。

### 移行判断

skill-creator/references/ は変更不要。

---

## 移行時の注意事項

### 1. settings.json の統合戦略

- LAM 4.0.1 の `settings.json` をベースとし、影式固有の追加（`git status *`, `pip show *`）を追加する
- `python *` は LAM 4.0.1 では ask だが、影式では `settings.local.json` で allow にオーバーライドされるため問題なし
- **hooks セクション**: LAM 4.0.1 の4つの hook 定義を `settings.json` に追加する

### 2. settings.local.json との共存

- 現行の `settings.local.json` は Python 固有権限 + 通知サウンド hook を定義
- LAM 4.0.1 の hooks と影式の hooks を統合する際の方針:
  - `settings.json`: LAM 4.0.1 の hook（PreToolUse, PostToolUse, Stop[lam-stop-hook], PreCompact）
  - `settings.local.json`: 影式固有の hook（Stop[notify-sound], Notification[notify-sound]）
  - Claude Code は同一イベントの hooks を**配列として結合**するため、Stop イベントで両方の hook が実行される

### 3. hooks スクリプトの Windows 対応

LAM 4.0.1 の hook スクリプトは bash で書かれており、以下の Windows 固有の問題に注意:

| 問題 | 影響箇所 | 対策 |
|------|---------|------|
| `timeout` コマンド | lam-stop-hook.sh（テスト・lint 実行） | Git Bash の coreutils timeout を使用。Windows `timeout.exe` は別物 |
| パスセパレータ | 全 hook のパス正規化ロジック | `$CLAUDE_PROJECT_DIR` が `/c/work5/...` 形式（MSYS2 パス）で展開されることを前提 |
| `stat` コマンド | lam-stop-hook.sh（PreCompact タイムスタンプ） | GNU stat 形式に依存。Git Bash で動作確認が必要 |
| `date -d` | lam-stop-hook.sh（日付パース） | Git Bash の date で動作するが、MSYS2 のバージョンに依存 |
| `sed -i` | pre-compact.sh | Git Bash の sed は `-i` をサポートするが、バックアップファイルの挙動が異なる場合がある |
| CRLF 改行 | 全 hook | Git の `core.autocrlf` 設定により CRLF に変換されると動作しない。`.gitattributes` で `*.sh text eol=lf` を設定する必要がある |

### 4. hook テストの扱い

LAM 4.0.1 の `.claude/hooks/tests/` 配下のテストスクリプト（5ファイル）は、hook の動作検証に有用。影式に hook を導入する際は、これらのテストを同時に導入し、Windows 環境で動作確認すべき。

### 5. states ファイルのスキーマ

マイグレーション不要。影式の既存 states ファイルはそのまま維持する。LAM 4.0.1 の新フィールド（current_wave, completed_tasks 等）は影式で必要になった時点で追加すればよい。

### 6. auto-generated ルールディレクトリ

LAM 4.0.1 には `.claude/rules/auto-generated/` ディレクトリが新設されている（README.md + trust-model.md）。TDD 内省パイプラインによる自動ルール生成の仕組み。影式に導入する場合は:
- `.claude/rules/auto-generated/README.md` を配置
- `.claude/rules/auto-generated/trust-model.md` を配置
- PostToolUse hook の TDD パターン記録機能と連携

### 7. 新規ルールファイル

LAM 4.0.1 には以下の新規ルールファイルがある（本差分分析の対象外だが関連する）:
- `permission-levels.md` — PG/SE/PM 権限等級の詳細定義
- `upstream-first.md` — プラットフォーム仕様変更への追従ルール

これらは hooks の動作と密接に関連するため、hooks 導入時に同時に導入すべき。
