# 権限等級分類基準

> **SSOT**: 本ファイルが PG/SE/PM 分類の唯一の定義源（ドメイン別 SSOT）。
> phase-rules.md の AUDITING セクション、core-identity.md の権限等級サマリーから参照される。
> 注: `.claude/rules/` 内の各ファイルは担当ドメインの SSOT として機能する。
> プロセス全体の SSOT は `docs/internal/` にある（`00_PROJECT_STRUCTURE.md` 等）。

## PG級（自動修正・報告不要）

自明な修正。プロジェクトの振る舞いを変えない変更。

- フォーマット修正（ruff format, prettier 等）
- typo 修正
- lint 違反の自動修正（ruff check --fix 等）
- import 整理
- テスト失敗の自明な修正（型ミスマッチ等）
- 不要な空白・末尾改行の除去

## SE級（修正後に報告）

技術的な判断を含むが、公開 API や仕様に影響しない変更。修正後にユーザーへ報告する。

- テストの追加・修正
- 内部リファクタリング（公開 API 不変）
- ドキュメントの細部更新（`docs/` 配下、ただし `docs/specs/` と `docs/adr/` を除く）
- 依存パッケージの minor/patch update
- 内部関数の名前変更（外部インターフェース不変）
- ログ出力の追加・修正
- コメントの追加・修正

## PM級（判断を仰ぐ）

プロジェクトの方向性・仕様・アーキテクチャに影響する変更。人間の承認が必須。
AUDITING フェーズでは指摘のみ。

- 仕様変更（`docs/specs/` の変更）
- アーキテクチャ変更（`docs/adr/` の変更）
- `.claude/rules/` の追加・変更
- `.claude/settings*.json` の変更
- 公開 API の変更
- 依存パッケージの major update
- フェーズの巻き戻し
- テストの削除
- 機能の削除

## フェーズとの二軸設計

| | PLANNING | BUILDING | AUDITING |
|--|----------|----------|----------|
| PG | - | 自動修正可 | 自動修正可 |
| SE | - | 修正後報告 | 修正後報告 |
| PM | 承認ゲート | 承認ゲート | 承認ゲート |

## ファイルパスベースの分類（PreToolUse hook 用）

| パスパターン | 等級 | 理由 |
|-------------|------|------|
| `docs/specs/*.md` | PM | 仕様変更 |
| `docs/adr/*.md` | PM | アーキテクチャ変更 |
| `docs/internal/*.md` | PM | プロセス SSOT 変更（影式固有） |
| `.claude/rules/*.md`, `.claude/rules/*/*.md` | PM | ルール変更（サブディレクトリ含む） |
| `.claude/settings*.json` | PM | 設定変更 |
| `pyproject.toml` | PM | プロジェクト設定変更（影式固有） |
| `docs/` 配下（上記以外） | SE | ドキュメント更新 |
| `src/kage_shiki/` 配下 | SE | ソースコード変更（影式固有） |
| `tests/` 配下 | SE | テストコード変更 |
| `config/` 配下 | SE | 設定ファイル変更（影式固有） |
| `.claude/hooks/analyzers/*_analyzer.py`（新規） | PM | 動的モジュールロード対象（`auto_discover`） |
| その他 | SE | 安全側に倒す |

> **注意**: `.claude/hooks/analyzers/` 配下の `*_analyzer.py` は `base.py` の `auto_discover()` により
> フック起動時に動的ロード（`exec_module`）される。悪意あるコードが `*_analyzer.py` として
> 配置された場合、Claude Code のツール呼び出し時に自動実行されるリスクがある。
> 新規 Analyzer の追加は PM 級として承認ゲートを設ける。

## 迷った場合

迷ったら **SE級に丸める**（安全側に倒す）。

典型的な判断例:
- 「テストの大幅な書き換え」→ SE級（公開 API は変わらない）
- 「README の構成変更」→ SE級（仕様書ではない）
- 「.claude/skills/ のワークフロー系 SKILL.md の変更」→ SE級（ルールではなくコマンド。旧 .claude/commands/ は 2026-07-18 に skills へ移行済み）
- 「.gitignore の変更」→ SE級
- 「config.toml テンプレートの変更」→ PM級（設定仕様の変更）
- 「docs/internal/ の変更」→ PM級（SSOT）
- 「tests/ の新規テスト追加」→ SE級

## Auto mode での PM 級の扱い（2026-04-29 Retro 由来）

Auto mode で `/full-review` 等を実行中、PM 級修正が必要になった場合の扱い。

### 原則

PM 級は人間承認必須。Auto mode でも自動実行してはならない。

### 例外: 「仕様の意味を変えない PM 級補記」

以下の **すべて** を満たす場合、Auto mode で自動進行可:

1. **`docs/specs/` の変更** で、既存記述の修正ではなく **追記** である
2. **実装の事後ドキュメント化** で、コードと仕様書の解離を埋める変更である
3. **仕様の意味を変えない**: 既に実装済みの定数値・引数仕様の根拠を補記するだけ
4. **監査レポートに明示**: `docs/artifacts/audit-reports/` のレポートに「PM 級だが Auto 進行した変更」の節を設ける

### 通知義務

Auto mode で例外条件に基づき PM 級補記を行った場合、最終報告時に以下の形式で **明示通知** すること:

```
⚠️ PM 級の Auto 進行: docs/specs/xxx.md に補記
   内容: <変更要約>
   仕様の意味は不変。ユーザーは事後確認をお願いします。
```

### 例外に該当しない PM 級（Auto 進行禁止 — 必ず一時停止）

- **仕様の意味を変える修正**（受入条件・制約・閾値・FR/NFR 内容の変更等）
- ADR（`docs/adr/`）の追加・変更
- `.claude/rules/` の変更
- `.claude/settings*.json` の変更
- `pyproject.toml` の変更
- 公開 API の変更
- フェーズの巻き戻し
- テストの削除
- 機能の削除

これらは Auto mode でも処理を一時停止し、ユーザーの判断を仰ぐこと。
状態ファイル（`lam-loop-state.json` 等）に `pm_pending: true` をセットして応答終了する。

### 根拠

Wave 2 full-review iter 1 で W-F（design.md Section 4.1 への実装定数根拠補記）が PM 級判定だったが Auto mode で自動進行した。仕様の意味は変わらないとはいえ、明示的承認なく `docs/specs/` を変更したのは越境のリスクがあった。本セクションで「仕様の意味を変えない補記」のみ Auto 許容することで、Auto mode の進捗性と PM 級ガードレールのバランスを取る。

## 参照

- `docs/internal/07_SECURITY_AND_AUTOMATION.md` Section 5 (Hooks-Based Permission System)
- `docs/internal/02_DEVELOPMENT_FLOW.md` (フェーズ別の権限適用)
- phase-rules.md: フェーズ別の修正ルール
- core-identity.md: 権限等級サマリー
- security-commands.md: コマンド安全基準（Layer 0）
