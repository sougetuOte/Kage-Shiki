# 権限等級分類基準

> **SSOT**: 本ファイルが PG/SE/PM 分類の唯一の定義源（ドメイン別 SSOT）。
> phase-rules.md の AUDITING セクション、core-identity.md の権限等級サマリーから参照される。
> 注: `.claude/rules/` 内の各ファイルは担当ドメインの SSOT として機能する。
> プロセス全体の SSOT は `docs/internal/` にある（`00_PROJECT_STRUCTURE.md` 等）。

## PG級（自動修正・報告不要）

以下は AI が自律的に修正してよい。ユーザーへの確認・報告は不要。

- フォーマット修正（ruff format, prettier）
- typo 修正（コメント・ドキュメント内）
- lint 違反の自動修正（ruff check --fix）
- import 整理（isort 相当）
- 不要な空白・末尾改行の除去

## SE級（修正後に報告）

修正は許可されるが、完了後にユーザーへ報告する。

- テストの追加・修正
- 内部リファクタリング（公開 API 変更なし）
- ドキュメント細部の更新（`docs/specs/`, `docs/adr/` 以外）
- minor/patch レベルの依存パッケージ更新
- ログメッセージ・コメントの変更

## PM級（判断を仰ぐ）

修正前にユーザーの承認が必要。AUDITING フェーズでは指摘のみ。

- 仕様変更（`docs/specs/` の内容変更）
- アーキテクチャ変更（新モジュール追加、依存関係変更）
- `.claude/rules/` の変更
- 公開 API / Protocol の変更
- major レベルの依存パッケージ更新
- テストや機能の削除

## フェーズとの二軸設計

| 等級 | PLANNING | BUILDING | AUDITING |
|------|----------|----------|----------|
| PG | — | 自動修正可 | 自動修正可 |
| SE | — | 修正 + 報告 | 修正 + 報告 |
| PM | 設計文書のみ | 承認後に実装 | 指摘のみ（承認ゲート） |

## ファイルパスベースの分類（PreToolUse hook 用）

| パスパターン | 等級 | 理由 |
|-------------|------|------|
| `docs/specs/*.md` | PM | 仕様変更 |
| `docs/adr/*.md` | PM | アーキテクチャ変更 |
| `docs/internal/*.md` | PM | プロセス SSOT 変更（影式固有） |
| `.claude/rules/*.md`, `.claude/rules/*/*.md` | PM | ルール変更 |
| `.claude/settings*.json` | PM | 設定変更 |
| `pyproject.toml` | PM | プロジェクト設定変更（影式固有） |
| `docs/` 配下（上記以外） | SE | ドキュメント更新 |
| `src/kage_shiki/` 配下 | SE | ソースコード変更（影式固有） |
| `tests/` 配下 | SE | テストコード変更 |
| `config/` 配下 | SE | 設定ファイル変更（影式固有） |
| その他 | SE | 安全側に倒す |

## 迷った場合

迷ったら **SE級に丸める**（安全側に倒す）。

典型的な判断例:
- 「テストを追加するだけ」→ SE級
- 「テストを削除する」→ PM級（機能の削除に相当）
- 「既存メソッドの内部ロジック変更」→ SE級
- 「新しい public メソッド追加」→ SE級（Protocol 変更なら PM級）
- 「config.toml テンプレートの変更」→ PM級（設定仕様の変更）
- 「docs/internal/ の変更」→ PM級（SSOT）
- 「tests/ の新規テスト追加」→ SE級

## 参照

- phase-rules.md: フェーズ別の修正ルール
- core-identity.md: 権限等級サマリー
- security-commands.md: コマンド安全基準（Layer 0）
