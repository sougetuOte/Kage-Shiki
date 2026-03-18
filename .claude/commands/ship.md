---
description: "Ship — 変更の棚卸し・論理コミット・後処理"
---

# Ship — 変更の棚卸し・論理コミット・後処理

変更ファイルを棚卸しし、論理グループに分けてコミットし、ユーザーへの手動作業を通知する。
変更出荷ワークフロー。

配置先: `<project>/.claude/commands/ship.md`
呼び出し: Claude Code 内で `/ship`
引数（任意）: `/ship dry-run`（コミットせず計画のみ表示）

---

## Phase 1: 棚卸し（Inventory）

1. `git status` で全変更ファイルを取得（untracked 含む）
2. `git diff --stat` でステージ済み・未ステージの変更量を確認
3. 各ファイルの変更内容を簡潔に要約（1ファイル1行）
4. **gitleaks シークレットスキャン**（staged changes）:
   ```bash
   # Python スクリプトで実行
   python -c "
   import sys; sys.path.insert(0, '.claude/hooks')
   from analyzers.gitleaks_scanner import run_protect_staged, is_available, get_install_guide
   if not is_available():
       print('gitleaks 未インストール: シークレットスキャンをスキップします')
       print(get_install_guide())
   else:
       issues = run_protect_staged()
       if issues:
           for i in issues:
               print(f'  {i.file}:{i.line} -- {i.message} ({i.rule_id})')
       else:
           print('シークレット検出なし')
   "
   ```
   - **検出なし**: Step 5 へ
   - **検出あり**: 検出内容を表示し、ユーザーに判断を求める
     - 「承知の上で続行」→ Step 5 へ
     - それ以外 → コミット中止
   - **gitleaks 未インストール**: WARNING + インストールガイドを表示し、コミットは許可する
5. 秘密情報チェック: `.env`, `credentials`, `*.key`, `settings.local.json`, `secret`, `token`, `password`, `api_key` パターンを含むファイルを除外候補に
6. 結果を一覧表示:

```
--- Ship: 棚卸し ---
変更: X files | 新規: X files | 削除: X files
除外候補: [秘密情報ファイルがあれば列挙]
```

## Phase 2: ドキュメント同期（Doc Sync）

Phase 1 の棚卸し結果を踏まえ、ドキュメントの同期を行う。

### 2-1. doc-sync-flag 参照

PostToolUse hook が自動生成する `.claude/doc-sync-flag` を参照する。
このファイルには src/ 配下の変更ファイルパスが1行1パスで記録されている。

- ファイルが存在しない or 空 → 2-2 をスキップし、従来フローへフォールバック
- ファイルが存在 → 2-2 へ進む

### 2-2. 変更の PG/SE/PM 分類

変更ファイルを権限等級（`.claude/rules/permission-levels.md`）で分類する:

- **PG級のみ** → Doc Sync スキップ
- **SE/PM級の変更あり** → 2-3 へ進む

### 2-3. ドキュメント更新案の生成

SE/PM級の変更がある場合:

1. 対応する `docs/specs/` ファイルを特定（ファイル名パターンマッチ）
2. `doc-writer` エージェントで更新案を生成（差分形式）
3. 更新案をユーザーに提示:
   - CHANGELOG.md への追記が必要か確認
   - README.md / README_en.md / CHEATSHEET.md への反映が必要か確認
4. PM級の設計判断を検出 → ADR 起票を提案
5. ユーザーが「今は不要」と判断した場合はスキップ可

### 2-4. フラグクリア

Doc Sync チェック完了後（承認・スキップに関わらず）、`.claude/doc-sync-flag` を削除する。
これにより次セッションではフラグがリセットされる。

### `.claude/doc-sync-flag` が存在しない場合（従来フロー）

影式従来フローで以下のドキュメントを現状と照合する:

| ファイル | 更新条件 | 更新内容 |
|---------|---------|---------|
| `CHANGELOG.md` | **毎回** | 変更内容を `[Unreleased]` セクションに追記 |
| `README.md` | 新モジュール追加・フェーズ進行時 | Phase 進捗セクションの更新 |
| `README_en.md` | README.md と同期 | 英語版の対応箇所を更新 |
| `CHEATSHEET.md` | 新コマンド・ルール・スキル追加時 | 該当テーブルに追記 |

#### 判断フロー

1. **CHANGELOG.md**: 今回の変更内容を要約し、適切なカテゴリ（feat/fix/docs/chore 等）で追記する
2. **README.md / README_en.md**: 新規 `src/` モジュールの追加や Phase の進行があれば進捗セクションを更新する。なければスキップ
3. **CHEATSHEET.md**: `.claude/rules/`, `.claude/commands/`, `.claude/skills/` に変更があれば該当テーブルを更新する。なければスキップ

### 出力

```
--- Doc Sync ---
モード: doc-sync-flag / 従来フロー
CHANGELOG.md: 更新（X エントリ追記）
README.md: スキップ（新モジュールなし）
README_en.md: スキップ
CHEATSHEET.md: 更新（ルール1件追加）
```

ドキュメント更新があった場合、Phase 3 のグループ分けに `docs` グループとして含める。

## Phase 3: 論理グループ分け（Grouping）

変更を以下の基準で論理グループに分類（最大5グループ）:

### 分類基準
- **同じ目的** の変更をまとめる（例: 「README 系の更新」）
- **同じレイヤー** の変更をまとめる（例: 「docs/internal の最適化」）
- **依存関係** があるファイルは同じグループ（例: 仕様書 + それに基づく実装）

### グループテーブルを表示

```
| Group | 目的 | ファイル数 | ファイル一覧 |
|-------|------|-----------|-------------|
| A | [目的] | N | file1, file2, ... |
| B | [目的] | N | file3, file4, ... |
```

### 判断に迷うファイルの扱い
- 複数グループにまたがるファイル → 主要な目的のグループに入れる
- どこにも属さないファイル → 「chore: その他」グループ

## Phase 4: コミット計画 + ユーザー確認（Plan）

各グループのコミットメッセージ案を生成:

```
| Group | コミットメッセージ | prefix |
|-------|-------------------|--------|
| A | docs: README/CHEATSHEET を Kage-Shiki に適応 | docs |
| B | chore: docs/internal を Python 向けに最適化 | chore |
```

### prefix 規則
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント変更
- `chore`: 設定・ツール・保守作業
- `refactor`: リファクタリング
- `test`: テスト

### 停止判断基準
以下に該当するグループは **コミットしない** でユーザーに報告:
- 変更が中途半端（WIP 状態が明らか）
- 仕様書と実装の整合性が取れていない
- テストが必要だが未実行
- 秘密情報が含まれる

コミット計画をユーザーに提示し、承認を求める:

```
--- Ship: コミット計画 ---
[グループテーブル + コミットメッセージ]

実行しますか？
1. 全グループをコミット
2. グループを選択してコミット
3. dry-run（何もしない）
```

引数に `dry-run` が指定されていた場合はここで停止。

## Phase 5: コミット実行 + Git push + 完了報告

ユーザー承認後:
1. グループ順に `git add [files]` + `git commit`
2. 各コミット完了を報告
3. `git push` でリモートに反映（ユーザー確認後）
4. 手動作業がある場合は通知

```
--- Ship 完了 ---
コミット: X 件（Group A, B, ...）
スキップ: X 件（理由: ...）
Push: 完了 / 未実施

次のステップ:
  /quick-save       （セッション状態を保存）
```
