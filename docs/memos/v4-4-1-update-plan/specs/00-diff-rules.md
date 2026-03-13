# .claude/rules/ 差分分析

> LAM v4.0.1 → v4.4.1 へのアップデートに伴う差分分析
> 比較日: 2026-03-13

## 概要

| 分類 | ファイル |
|------|---------|
| 共通（両方に存在） | `core-identity.md`, `decision-making.md`, `phase-rules.md`, `security-commands.md`, `permission-levels.md`, `upstream-first.md`, `auto-generated/README.md`, `auto-generated/trust-model.md` |
| LAM v4.4.1 で新規追加 | `test-result-output.md` |
| 影式にのみ存在（影式固有） | `building-checklist.md` |

LAM v4.0.1 → v4.4.1 の主要な変更テーマは以下の3点:
1. **TDD 内省パイプライン v2 への刷新** — JUnit XML ベースのテスト結果読み取りに移行（exitCode 依存を廃止）、閾値を3回→2回に引き下げ、`/retro` 主導の人間判断フローに変更
2. **security-commands.md の三分類化** — 従来の Allow/高リスクの二分類から、Allow/実行禁止(deny)/承認必須(ask) の三分類に再編
3. **用語・パス統一** — `docs/memos/` → `docs/artifacts/`、`/daily` → `/quick-save`、`/pattern-review` → `/retro` Step 2.5 等の用語変更

---

## 共通ファイルの差分

### core-identity.md

#### 変更: Context Compression の書き出し先

**影式（現行）**:
```
1. 決定事項と未解決タスクを `docs/tasks/` または `docs/memos/` に書き出す
```

**LAM v4.4.1**:
```
1. 決定事項と未解決タスクを `docs/tasks/` または `docs/artifacts/` に書き出す
```

`docs/memos/` → `docs/artifacts/` への用語変更。

#### 削除された項目（v4.0.1 → v4.4.1 間）

なし。v4.0.1 時点で既に Subagent 委任判断テーブル、コンテキスト節約原則は core-identity.md から削除済み。

#### 共通部分（変更なし）

- Active Retrieval（能動的検索原則）の3項目: 同一
- 権限等級（PG/SE/PM）セクション: 同一

#### 影式固有の保持すべき内容

影式現行版は v4.0.1 移行時に以下を保持している:
- **Subagent 委任判断テーブル**: LAM v4.0.1 で削除されたが影式で保持。v4.4.1 にも存在しない。保持判断が必要
- **コンテキスト節約原則（3項目）**: 同上

---

### decision-making.md

#### 差分

**なし**。影式現行版と LAM v4.4.1 は完全に同一。

v4.0.1 移行時に SSOT 参照注記を追加済みであり、v4.4.1 での変更はない。

---

### phase-rules.md

このファイルに最も大きな差分がある。

#### PLANNING セクション

##### 変更: 許可事項のパス

**影式（現行）**:
```
- `docs/specs/`, `docs/adr/`, `docs/tasks/`, `docs/memos/` への出力
```

**LAM v4.4.1**:
```
- `docs/specs/`, `docs/adr/`, `docs/tasks/`, `docs/artifacts/` への出力
```

`docs/memos/` → `docs/artifacts/` への用語変更。

##### その他

承認ゲート、禁止事項は同一。

#### BUILDING セクション

##### 変更: TDD 内省パイプライン — v1 から v2 への刷新

**影式（現行）**（v4.0.1 ベース）:
```markdown
### TDD 内省パイプライン（Wave 4）

テスト失敗→成功のサイクルを PostToolUse hook が自動記録する。
蓄積されたパターンが閾値（3回）に到達すると、ルール候補が自動生成される。

- パターン記録: `.claude/tdd-patterns.log`（自動、PG級）
- パターン詳細: `docs/memos/tdd-patterns/`
- ルール候補: `.claude/rules/auto-generated/draft-*.md`（PM級で起票・承認）
- 審査コマンド: `/pattern-review`
```

**LAM v4.4.1**:
```markdown
### TDD 内省パイプライン v2

PostToolUse hook がテスト結果（JUnit XML）を読み取り、FAIL→PASS 遷移を自動記録する。
`/retro` 実行時に人間がパターン分析を行い、同一パターンが閾値（2回）以上出現する場合にルール候補を提案する。

- パターン記録: `.claude/tdd-patterns.log`（自動、PG級）
- パターン詳細: `docs/artifacts/tdd-patterns/`
- ルール候補: `.claude/rules/auto-generated/draft-*.md`（PM級で起票・承認）
- パターン分析: `/retro` Step 2.5
- 審査コマンド: `/pattern-review`

詳細: `.claude/rules/auto-generated/trust-model.md`
```

主な差分:
1. セクション名が「Wave 4」→「v2」に変更
2. JUnit XML ベースの検出方式に変更（exitCode 依存を廃止）
3. 閾値が 3回 → 2回 に引き下げ
4. `docs/memos/tdd-patterns/` → `docs/artifacts/tdd-patterns/` にパス変更
5. パターン分析フローが `/retro` Step 2.5 に移動（人間主導）。`/pattern-review` はルール候補の PM級承認コマンドとして存続
6. trust-model.md への参照リンクが追加

##### 共通部分（変更なし）

- 必須事項（4項目）: 同一
- TDD 品質チェック（R-1, R-4）: 同一
- 仕様同期ルール（S-1, S-3, S-4）: 同一
- 禁止事項（3項目）: 同一

#### AUDITING セクション

##### 変更: 「必須」から `/full-review` 参照の削除

**影式（現行）** には以下の項目がある:
```
- `/full-review` で監査→修正→検証を一気通貫で実施可能
```

**LAM v4.4.1** にはこの行がない。

##### 削除: Green State 5条件との対応テーブル

**影式（現行）** には以下のセクションがある:
```markdown
### Green State 5条件との対応

監査完了条件は `docs/internal/07_SECURITY_AND_AUTOMATION.md` Section 5 の Green State（G1〜G5）に対応する:

| 監査完了条件 | Green State | 識別子 |
|:-----------|:-----------|:-------|
| テスト結果: 全件 PASSED | テスト全パス | G1 |
| ruff: All checks passed | lint エラーゼロ | G2 |
| PG/SE級 Issue: 全件修正済み | 対応可能 Issue ゼロ | G3 |
| 仕様書との整合確認 | 仕様差分ゼロ | G4 |
| セキュリティチェック通過 | セキュリティチェック通過 | G5 |
```

**LAM v4.4.1** にはこのセクションがない。これは影式固有の追加であり、LAM テンプレートには元々存在しない。

##### 削除: AUDITING ルール識別子

**影式（現行）** にある A-1〜A-4 の識別子セクションが **LAM v4.4.1** には存在しない:
```markdown
### AUDITING ルール識別子

- **A-1**: 全重篤度への対応義務（Critical/Warning/Info）
- **A-2**: 対応不可 Issue の明示（PM級は承認ゲートへ）
- **A-3**: 修正後の再検証（テスト + ruff）
- **A-4**: 仕様ズレの同時修正（Atomic Commit）
```

これは影式固有の追加。

##### 削除: 影式固有の修正後再検証義務、監査レポート完了条件

以下の影式固有セクションが LAM v4.4.1 には存在しない（元から LAM テンプレートにはない）:

- 「影式固有: 修正後の再検証義務（A-3 由来）」
- 「影式固有: 監査レポート完了条件」

##### 共通部分（変更なし）

- 修正ルール（v4.0.0）: 同一
- コード品質チェック: 同一
- コード明確性チェック: 同一
- ドキュメント・アーキテクチャ: 同一
- 改善提案の禁止事項: 同一
- レポート形式: 同一

#### BUILDING セクション（影式固有）

以下は影式の phase-rules.md にのみ存在し、LAM v4.4.1 にも存在しない:

- 「影式固有: Phase 完了判定（L-4 由来）」— スモークテスト要件

#### フェーズ警告テンプレート

変更なし。同一。

---

### security-commands.md

このファイルは大幅に再構成されている。

#### 変更: Allow List

**影式（現行）**:
```
| ファイル読取 | `ls`, `cat`, `grep`, `find`, `pwd`, `du`, `file` |
| Git 読取 | `git status`, `git log`, `git diff`, `git show`, `git branch` |
| テスト | `pytest`, `npm test`, `go test` |
| Python | `python`, `python -m pytest`, `python -m ruff`, `python -c`, `pip`, `pyenv` |
| パッケージ情報 | `npm list`, `pip list` |
| プロセス情報 | `ps` |
```

**LAM v4.4.1**:
```
| ファイル読取 | `ls`, `cat`, `grep`, `pwd`, `du`, `file` |
| Git 読取 | `git status`, `git log`, `git diff`, `git show`, `git branch` |
| テスト | `pytest`, `npm test`, `go test` |
| パッケージ情報 | `npm list`, `pip list` |
| プロセス情報 | `ps` |
```

差分:
1. `find` が Allow List から削除（後述の `ask` に移動）
2. Python カテゴリ（`python`, `python -m pytest`, `python -m ruff`, `python -c`, `pip`, `pyenv`）が削除（影式固有）

#### 変更: 高リスクコマンド → 三分類に再編

**影式（現行）** は「高リスクコマンド（Layer 0: 承認必須）」として一括管理:
```
| ファイル削除 | `rm`, `rm -rf` | データ消失 |
| 権限変更 | `chmod`, `chown` | セキュリティ |
| システム変更 | `apt`, `brew`, `systemctl`, `reboot` | システム破壊 |
| ファイル操作 | `mv`, `cp`, `mkdir`, `touch` | 意図しない変更 |
| Git 書込 | `git push`, `git commit`, `git merge` | リモート影響 |
| ネットワーク | `curl`, `wget`, `ssh` | 外部通信 |
| 実行 | `npm start`, `python main.py`, `make` | リソース枯渇 |
```

**LAM v4.4.1** は **実行禁止(deny)** と **承認必須(ask)** の二セクションに分離:

**実行禁止コマンド（Layer 0: deny）**:
```
| ファイル削除 | `rm`, `rm -rf` | 不可逆なデータ消失 |
| ファイル移動 | `mv` | 不可逆なファイル消失・上書き |
| 権限変更 | `chmod`, `chown` | セキュリティ境界の破壊 |
| システム変更 | `apt`, `brew`, `systemctl`, `reboot` | システム設定の変更 |
```

**承認必須コマンド（Layer 0: ask）**:
```
| ファイル操作 | `cp`, `mkdir`, `touch` | 意図しない変更 |
| Git 書込 | `git push`, `git commit`, `git merge` | リモート影響 |
| ネットワーク | `curl`, `wget`, `ssh` | 外部通信 |
| 実行 | `npm start`, `python main.py`, `make` | リソース枯渇 |
```

主な差分:
1. `rm`, `rm -rf` が deny に昇格（現行は ask 扱い）
2. `mv` が deny に昇格し、ファイル操作(ask) から分離
3. `chmod`, `chown` が deny に昇格
4. `find` に関する注記が追加: 「v4.3.1 で `ask` に移動（`-delete`, `-exec rm` 等の破壊的パターンは `deny`）」

#### 変更: 末尾の説明文

**影式（現行）**:
```
上記に含まれないコマンドは **高リスク扱い**（承認必須）。

> Layer 1（`settings.json`）では、上記コマンドの多くが `deny` または `ask` に分類されている。
「止めて」「ストップ」等の指示で直ちに停止。
```

**LAM v4.4.1**:
```
上記に含まれないコマンドは **高リスク扱い**（承認必須）。

> Layer 1（`settings.json`）で deny / ask の実際の制御粒度を設定する。
> `find` は v4.3.1 で `ask` に移動（`-delete`, `-exec rm` 等の破壊的パターンは `deny`）。
「止めて」「ストップ」等の指示で直ちに停止。
```

#### 変更: v4.0.0 ネイティブ権限モデルセクション

**影式（現行）**:
```
v4.0.0 以降、コマンド安全基準は以下の三層で管理される:

- **Layer 0（プロンプティング）**: 本ファイルの Allow/Deny List。憲法的ルールとして常に有効
- **Layer 1（ネイティブ権限）**: ...
- **Layer 2（PreToolUse hook）**: `.claude/hooks/pre-tool-use.py` で...
```

**LAM v4.4.1**:
```
v4.0.0 以降、コマンド安全基準は以下の二層で管理される:

- **Layer 1（ネイティブ権限）**: ...
- **Layer 2（PreToolUse hook）**: `.claude/hooks/pre-tool-use.py` で...

本ファイルの Allow/Deny List は Layer 0（憲法的プロンプティング）として引き続き有効。
```

差分: 「三層」→「二層」に変更。Layer 0 の記述が箇条書き内からセクション末尾の説明文に移動。実質的な意味は同一。

---

### permission-levels.md

#### 変更: 冒頭の SSOT 宣言

**影式（現行）**:
```markdown
> **SSOT**: 本ファイルが PG/SE/PM 分類の唯一の定義源（ドメイン別 SSOT）。
> phase-rules.md の AUDITING セクション、core-identity.md の権限等級サマリーから参照される。
> 注: `.claude/rules/` 内の各ファイルは担当ドメインの SSOT として機能する。
> プロセス全体の SSOT は `docs/internal/` にある（`00_PROJECT_STRUCTURE.md` 等）。
```

**LAM v4.4.1**:
```markdown
v4.0.0 で導入された変更のリスクレベルに応じた三段階分類。
全てのツール操作・ファイル変更はこの等級に基づいて処理される。
```

影式現行版の SSOT 宣言は影式固有の追加。LAM v4.4.1 では簡潔な概要文に変更。

#### 変更: PG級の定義

**影式（現行）**:
```
以下は AI が自律的に修正してよい。ユーザーへの確認・報告は不要。

- フォーマット修正（ruff format, prettier）
- typo 修正（コメント・ドキュメント内）
- lint 違反の自動修正（ruff check --fix）
- import 整理（isort 相当）
- 不要な空白・末尾改行の除去
```

**LAM v4.4.1**:
```
自明な修正。プロジェクトの振る舞いを変えない変更。

- フォーマット修正（prettier, ruff format 等）
- typo 修正
- lint 違反の自動修正（eslint --fix, ruff check --fix 等）
- import 整理
- テスト失敗の自明な修正（型ミスマッチ等）
- 不要な空白・末尾改行の除去
```

差分:
1. 説明文がより簡潔・汎用的に変更
2. typo 修正から「（コメント・ドキュメント内）」の限定が削除
3. import 整理から「（isort 相当）」の注記が削除
4. **「テスト失敗の自明な修正（型ミスマッチ等）」が追加**（新規）

#### 変更: SE級の定義

**影式（現行）**:
```
- テストの追加・修正
- 内部リファクタリング（公開 API 変更なし）
- ドキュメント細部の更新（`docs/specs/`, `docs/adr/` 以外）
- minor/patch レベルの依存パッケージ更新
- ログメッセージ・コメントの変更
```

**LAM v4.4.1**:
```
- テストの追加・修正
- 内部リファクタリング（公開 API 不変）
- ドキュメントの細部更新（`docs/` 配下、ただし `docs/specs/` と `docs/adr/` を除く）
- 依存パッケージの minor/patch update
- 内部関数の名前変更（外部インターフェース不変）
- ログ出力の追加・修正
- コメントの追加・修正
```

差分:
1. 「公開 API 変更なし」→「公開 API 不変」（表現のみ）
2. ドキュメント更新の説明がより明確に（`docs/` 配下と明示）
3. **「内部関数の名前変更（外部インターフェース不変）」が追加**（新規）
4. 「ログメッセージ・コメントの変更」が「ログ出力の追加・修正」「コメントの追加・修正」に分離・拡張

#### 変更: PM級の定義

**影式（現行）**:
```
- 仕様変更（`docs/specs/` の内容変更）
- アーキテクチャ変更（新モジュール追加、依存関係変更）
- `.claude/rules/` の変更
- 公開 API / Protocol の変更
- major レベルの依存パッケージ更新
- テストや機能の削除
```

**LAM v4.4.1**:
```
- 仕様変更（`docs/specs/` の変更）
- アーキテクチャ変更（`docs/adr/` の変更）
- `.claude/rules/` の追加・変更
- `.claude/settings*.json` の変更
- 公開 API の変更
- 依存パッケージの major update
- フェーズの巻き戻し
- テストの削除
- 機能の削除
```

差分:
1. アーキテクチャ変更の説明変更:「（新モジュール追加、依存関係変更）」→「（`docs/adr/` の変更）」
2. **`.claude/settings*.json` の変更が追加**（新規）
3. 「公開 API / Protocol の変更」→「公開 API の変更」（Protocol の明示が削除）
4. **「フェーズの巻き戻し」が追加**（新規）
5. 「テストや機能の削除」→「テストの削除」「機能の削除」に分離

#### 変更: フェーズとの二軸設計テーブル

**影式（現行）**:
```
| 等級 | PLANNING | BUILDING | AUDITING |
|------|----------|----------|----------|
| PG | — | 自動修正可 | 自動修正可 |
| SE | — | 修正 + 報告 | 修正 + 報告 |
| PM | 設計文書のみ | 承認後に実装 | 指摘のみ（承認ゲート） |
```

**LAM v4.4.1**:
```
| | PLANNING | BUILDING | AUDITING |
|--|----------|----------|----------|
| PG | - | 自動修正可 | 自動修正可 |
| SE | - | 修正後報告 | 修正後報告 |
| PM | 承認ゲート | 承認ゲート | 承認ゲート |
```

差分:
1. PM の PLANNING が「設計文書のみ」→「承認ゲート」に変更
2. PM の BUILDING が「承認後に実装」→「承認ゲート」に統一
3. PM の AUDITING が「指摘のみ（承認ゲート）」→「承認ゲート」に統一

#### 変更: ファイルパスベースの分類テーブル

**影式（現行）**（影式固有パスを含む）:
```
| `docs/internal/*.md` | PM | プロセス SSOT 変更（影式固有） |
| `pyproject.toml` | PM | プロジェクト設定変更（影式固有） |
| `src/kage_shiki/` 配下 | SE | ソースコード変更（影式固有） |
| `tests/` 配下 | SE | テストコード変更 |
| `config/` 配下 | SE | 設定ファイル変更（影式固有） |
```

**LAM v4.4.1**:
```
| `.claude/settings*.json` | PM | 設定変更 |
| `src/` 配下 | SE | ソースコード変更（デフォルト） |
```

差分:
1. `.claude/settings*.json` が PM として追加
2. `docs/internal/*.md` が削除（LAM 汎用テンプレートには不要）
3. `pyproject.toml` が削除（影式固有）
4. `src/kage_shiki/` → `src/` に汎用化
5. `tests/` 配下が削除（LAM v4.4.1 では `src/` 以外は「その他: SE」で包含）
6. `config/` 配下が削除（影式固有）

#### 変更: 迷った場合の判断例

**影式（現行）**:
```
- 「テストを追加するだけ」→ SE級
- 「テストを削除する」→ PM級（機能の削除に相当）
- 「既存メソッドの内部ロジック変更」→ SE級
- 「新しい public メソッド追加」→ SE級（Protocol 変更なら PM級）
- 「config.toml テンプレートの変更」→ PM級（設定仕様の変更）
- 「docs/internal/ の変更」→ PM級（SSOT）
- 「tests/ の新規テスト追加」→ SE級
```

**LAM v4.4.1**:
```
- 「テストの大幅な書き換え」→ SE級（公開 API は変わらない）
- 「README の構成変更」→ SE級（仕様書ではない）
- 「.claude/commands/ の変更」→ SE級（ルールではなくコマンド）
- 「package.json の scripts 変更」→ SE級（ビルド設定）
- 「.gitignore の変更」→ SE級
```

完全に異なる例セットに置換。LAM v4.4.1 は汎用例、影式は Python/Protocol 固有の例を含む。

#### 変更: 参照セクション

**影式（現行）**: `phase-rules.md`, `core-identity.md`, `security-commands.md` を参照

**LAM v4.4.1**:
```
- `docs/specs/v4.0.0-immune-system-requirements.md` Section 5.1 (権限等級の原定義)
- `docs/internal/07_SECURITY_AND_AUTOMATION.md` Section 5 (Hooks-Based Permission System)
- `docs/internal/02_DEVELOPMENT_FLOW.md` (フェーズ別の権限適用)
```

参照先が docs/specs/ と docs/internal/ の SSOT に変更。

---

### upstream-first.md

#### 変更: ファイル構造の大幅再編

影式（現行）は v4.0.1 テンプレートのフラットな構成を維持しているが、LAM v4.4.1 では構造化されたセクションに再編。

##### 変更: 概要セクションの追加

**LAM v4.4.1** で以下が追加:
```markdown
## 概要

Claude Code の hooks、settings、permissions 等のプラットフォーム機能を実装・修正する際は、
**実装前に最新の公式ドキュメントを確認する**こと。

## 背景

Claude Code は活発に開発されており、設定書式やAPI が頻繁に変更される。
過去の記憶や既存実装に基づいて書くと、旧書式で実装してしまい手戻りが発生する。
```

影式（現行）では見出しなしの冒頭文として同様の趣旨を記載。

##### 変更: ルールの構造化

**影式（現行）** のトップレベル:
```markdown
# Upstream First — プラットフォーム仕様優先原則

## 原則
...
## 確認先
...
## 確認手順
...
## 注意事項
...
```

**LAM v4.4.1** の構造:
```markdown
# Upstream First（上流仕様優先）原則

## 概要
## 背景
## ルール
### 必須: 実装前の仕様確認
### 確認先
### 確認手順
### 適用タイミング
## 権限等級
## Wave 開始前の一括すり合わせ（推奨）
### 対象範囲
```

##### 変更: 確認先 URL

**影式（現行）**:
```
| Hooks | https://docs.anthropic.com/en/docs/claude-code/hooks |
| Settings | https://docs.anthropic.com/en/docs/claude-code/settings |
| Permissions | https://docs.anthropic.com/en/docs/claude-code/permissions |
| Skills | https://docs.anthropic.com/en/docs/claude-code/skills |
| Sub-agents | https://docs.anthropic.com/en/docs/claude-code/sub-agents |
| MCP | https://docs.anthropic.com/en/docs/claude-code/mcp |
```

**LAM v4.4.1**:
```
| Hooks | https://code.claude.com/docs/en/hooks |
| Settings | https://code.claude.com/docs/en/settings |
| Permissions | https://code.claude.com/docs/en/permissions |
| Skills | https://code.claude.com/docs/en/skills |
| Sub-agents | https://code.claude.com/docs/en/sub-agents |
```

差分:
1. **URL ドメインが変更**: `docs.anthropic.com/en/docs/claude-code/` → `code.claude.com/docs/en/`
2. MCP の行が削除

##### 変更: 確認手順

**影式（現行）**:
```
1. **context7 MCP** で最新ドキュメントを取得（利用可能な場合）
2. context7 が利用不可の場合、**WebFetch** で公式 URL を直接取得
3. 取得した仕様と既存実装の**差分を特定**
4. 差分があればユーザーに報告し、対応方針を確認
5. 承認後に実装を開始
```

**LAM v4.4.1**:
```
1. context7 MCP で該当ドキュメントを検索・取得（推奨）
2. context7 が利用不可 or 対応外の場合は WebFetch でフォールバック（対話モードのみ）
3. 現行実装との差分を特定
4. 差分があれば修正方針をユーザーに報告
5. 承認後に実装
```

差分:
1. Step 2 に「（対話モードのみ）」の制限が追加
2. 表現の簡潔化

##### 変更: 注意事項 → 統合

**影式（現行）**:
```markdown
## 注意事項

- `/full-review` 等の自動フロー内では WebFetch を使用しない（コンテキスト消費を避ける）
- Wave 開始前に一括ですり合わせることを推奨
- 公式ドキュメントに記載がない挙動を発見した場合、`docs/memos/` に記録する
```

**LAM v4.4.1** では:
- WebFetch 制限は確認手順の注記に統合（「無応答リスクのため」と理由変更）
- Wave 開始前の一括すり合わせは独立セクションに昇格し、対象範囲の詳細を追加
- `docs/memos/` → 記載なし（この項目は削除）

##### 追加: 適用タイミング

**LAM v4.4.1** で新規追加:
```markdown
### 適用タイミング

- Wave の開始時（新しい hook/settings を実装する前）
- 起動時エラーが発生した時
- プラットフォーム機能に関する変更を行う時
```

##### 追加: 権限等級

**LAM v4.4.1** で新規追加:
```markdown
## 権限等級

本ルールファイル自体の変更: **PM級**
```

##### 追加: 一括すり合わせの対象範囲

**LAM v4.4.1** で新規追加:
```markdown
### 対象範囲

- **更新すべき**: 設計書のプラットフォーム API 依存箇所、タスク定義の完了条件
- **更新不要**: 要件書（「何をやるか」でありAPI書式に依存しない）、ADR（決定の記録）、ビジネスロジック部分
```

##### 削除: 影式固有の確認対象

**影式（現行）** には「必須: 実装前の仕様確認」の対象として以下が列挙されているが、LAM v4.4.1 では構造が異なるため直接比較が困難。ただし同等の内容はカバーされている。

---

### auto-generated/README.md

#### 変更: 大幅な書き換え

**影式（現行）**:
```markdown
# auto-generated/ — TDD 内省ルール

## ライフサイクル

1. **PostToolUse hook** がテスト失敗→成功パターンを検出
2. `.claude/tdd-patterns.log` に記録（PG級、自動）
3. 同一パターンが **3回** に到達すると `draft-NNN.md` を自動生成
4. `/pattern-review` で PM級承認
5. 承認後 `rule-NNN.md` として配置

## ファイル命名

| パターン | 意味 |
|---------|------|
| `draft-NNN.md` | 承認待ちのルール候補 |
| `rule-NNN.md` | 承認済みの自動生成ルール |
| `trust-model.md` | 信頼度モデル定義 |

## ルール寿命管理

- 各ルールに `last_matched` 日付メタデータを付与
- **90日以上未使用**のルールは `/daily` で棚卸し通知
- 棚卸し対象は PM級承認で削除または更新

## 権限等級

- パターン記録（`.claude/tdd-patterns.log` への追記）: **PG級**
- ルール候補の生成・変更・削除: **PM級**
```

**LAM v4.4.1**:
```markdown
# 自動生成ルール

## ライフサイクル

1. PostToolUse hook がテスト結果（JUnit XML）を読み取り、
   FAIL→PASS 遷移を .claude/tdd-patterns.log に記録
   （FAIL→PASS 遷移時に systemMessage で /retro を推奨）

2. /retro 実行時（人間が判断）に tdd-patterns.log を分析
   → 同一パターンが閾値（初期値: 2回）以上出現する場合
   → draft-NNN.md としてルール候補を提案

3. PM級として人間に承認要求
   → 承認: このディレクトリに配置
   → 却下: draft を削除

4. ルール寿命管理
   → 90日以上未使用のルールを /quick-save (Daily記録) で棚卸し通知
   → 削除は PM級（人間承認必須）

## ファイル命名規則

- `draft-NNN.md`: 承認待ちルール候補
- `rule-NNN.md`: 承認済みルール
- `trust-model.md`: 信頼度モデルの定義

## 権限等級

- このディレクトリ配下のファイル追加・変更: **PM級**（人間承認必須）
- パターン記録（`.claude/tdd-patterns.log`）: **PG級**（自動記録）

## 参照

- 仕様書: `docs/specs/tdd-introspection-v2.md`
- 信頼度モデル: `trust-model.md`（本ディレクトリ内）
- テスト結果ルール: `.claude/rules/test-result-output.md`
- パターン詳細記録先: `docs/artifacts/tdd-patterns/`
- パターンログ: `.claude/tdd-patterns.log`
- ルール候補: `.claude/rules/auto-generated/draft-*.md`
```

主な差分:
1. タイトル変更: 「TDD 内省ルール」→「自動生成ルール」
2. ライフサイクルが v2 フローに全面更新（JUnit XML、`/retro`、閾値2回）
3. ファイル命名がテーブル形式からリスト形式に変更
4. ルール寿命管理が `/daily` → `/quick-save (Daily記録)` に変更
5. 参照セクションが大幅に追加（仕様書、テスト結果ルール、パターン詳細記録先等）

---

### auto-generated/trust-model.md

#### 変更: 全面書き換え

**影式（現行）** は v4.0.1 テンプレートの v1 仕様。**LAM v4.4.1** は v2 仕様に全面更新。

主な差分:

1. **タイトル変更**: 「信頼度モデル — TDD 内省パイプライン」→「信頼度モデル」
2. **データソースセクション追加**: JUnit XML ベースに変更。exitCode が PostToolUse 入力に存在しない問題の記録を含む
3. **観測回数テーブル → 観測と分析のフロー**: 段階表（1回→2回→3回→3回+）がフロー図に置換
4. **閾値変更**: 3回 → 2回。理由: `/retro` が人間実行であり誤爆リスクが低いため
5. **パターン照合ロジック変更**: 「MVP: 手動照合」「完全実装: キーワード照合」の二段階から、`/retro` Step 2.5 での具体的な4ステップ手順に変更
6. **ルール候補フォーマット変更**: メタデータのステータスに `rejected` が追加（v1 では `draft / approved / retired`）
7. **用語変更**: `docs/memos/tdd-patterns/` → `docs/artifacts/tdd-patterns/`
8. **参照セクション**: `docs/specs/tdd-introspection-v2.md` と `test-result-output.md` への参照が追加
9. **権限等級セクション追加**: 明示的に PG級/PM級 の分類を記載

---

## LAM v4.4.1 で新規追加されたファイル

### test-result-output.md

**内容要約**: TDD 内省パイプライン v2 の基盤として、テスト実行結果を JUnit XML 形式で `.claude/test-results.xml` に出力することを必須とするルール。

主要ポイント:
- テストフレームワーク導入・変更時に JUnit XML 出力設定を追加する義務
- `.gitignore` に `.claude/test-results.xml` を追加する義務
- Python (pytest), JavaScript/TypeScript (Jest, Vitest), Go, Rust の言語別設定リファレンス
- PostToolUse hook がテスト結果ファイルを読み取る前提
- 結果ファイルが存在しない場合は WARNING ログ出力のみ（テスト動作に影響なし）
- 本ルール自体の変更は PM級、設定追加は PG級

**影式への適用時の注意点**:
- 影式は Python (pytest) を使用。`pyproject.toml` の `[tool.pytest.ini_options]` に `addopts = "--junitxml=.claude/test-results.xml"` を追加する必要がある
- 現行の `.gitignore` に `.claude/test-results.xml` を追加する必要がある
- PostToolUse hook の実装が前提。影式で TDD 内省パイプライン v2 を有効化する際に同時導入

---

## 影式にのみ存在するファイル（影式固有）

### building-checklist.md

**内容**: Phase 1 監査・Retro で発見された不具合パターンの防止ルール集。LAM テンプレート（v4.0.1, v4.4.1 いずれ）には存在しない。

**推奨: 影式固有ルールとして保持**

R-1, R-4, S-1, S-3, S-4 は LAM テンプレートの phase-rules.md にコア版が存在するため、building-checklist.md ではそれらへの参照に留め、影式固有ルール（R-2, R-3, R-5〜R-11, S-2）を定義する現行構成を維持する。v4.0.1 移行時に既にこの構成に整理済み。

---

## 移行時の注意事項

### 1. TDD 内省パイプライン v2 への移行が最大の変更

v4.4.1 の最大の変更は TDD 内省パイプライン v1 → v2 への刷新。これは以下のファイルに横断的に影響する:
- `phase-rules.md`: BUILDING セクションの内省パイプライン記述
- `auto-generated/README.md`: ライフサイクル全体の書き換え
- `auto-generated/trust-model.md`: 信頼度モデルの全面更新
- `test-result-output.md`: 新規追加

v2 への移行には PostToolUse hook の実装と JUnit XML 出力設定が前提となる。影式で hooks を実装済みかどうかを確認し、未実装なら段階的導入を計画すること。

### 2. security-commands.md の三分類化は実運用に影響

`rm`, `mv`, `chmod`/`chown` が deny（AI 実行禁止）に昇格。現行の影式ではこれらは ask（承認必須）扱いのため、実運用上の制約が強化される。`.claude/settings.json` の permissions 設定との整合確認が必要。

また、Layer 数の表記が「三層」→「二層」に変更されている（Layer 0 の記述が箇条書き内からセクション末尾の説明文に移動、実質的意味は同一）。影式の security-commands.md の `v4.0.0` セクションの Layer 数表記を更新すること。

### 3. docs/memos/ → docs/artifacts/ の用語変更

LAM v4.4.1 では `docs/memos/` が `docs/artifacts/` に変更されている。影式では `docs/memos/` を広く使用しているため、この用語変更を採用するかどうかは PM級の判断が必要。採用する場合、ディレクトリ名変更に伴う既存参照の一括更新が発生する。

### 4. URL ドメインの変更

upstream-first.md の確認先 URL が `docs.anthropic.com` → `code.claude.com` に変更。最新の正しいドメインを確認して適用すること。

### 5. permission-levels.md の影式固有パスは保持必須

LAM v4.4.1 のファイルパスベース分類は汎用化されているため、影式固有のパス（`docs/internal/*.md`, `pyproject.toml`, `src/kage_shiki/`, `config/`）を移行時に再追加すること。

### 6. ファイル構成の変更

移行後の `.claude/rules/` の想定構成:

```
.claude/rules/
├── core-identity.md          ← v4.4.1 ベースに更新（docs/artifacts/ パス変更）
├── decision-making.md        ← 変更なし
├── phase-rules.md            ← v4.4.1 ベースに更新（TDD 内省 v2） + 影式固有保持
├── security-commands.md      ← v4.4.1 ベースに更新（三分類化） + Python コマンド保持
├── permission-levels.md      ← v4.4.1 ベースに更新 + 影式固有パス再追加
├── upstream-first.md         ← v4.4.1 ベースに更新（URL 変更、構造化）
├── building-checklist.md     ← 影式固有を保持（変更なし）
├── test-result-output.md     ← 新規追加（v4.4.1）
├── auto-generated/
│   ├── README.md             ← v4.4.1 ベースに更新（v2 フロー）
│   └── trust-model.md        ← v4.4.1 ベースに更新（v2 モデル）
```
