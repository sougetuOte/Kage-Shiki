# Phase 1 MVP 設計書インデックス

**フェーズ**: PLANNING — design サブフェーズ
**根拠**: `requirements.md`（承認済み Rev.3）
**作成日**: 2026-03-03

---

## 設計項目一覧

| # | 項目 | ファイル | 関連 FR | ステータス |
|---|------|---------|---------|-----------|
| D-1 | src/ ディレクトリ構成 | `design-d01-directory-structure.md` | 全体 | 提案（承認待ち） |
| D-2 | ログ設計 | `design-d02-logging.md` | FR-1.5 | 提案（承認待ち） |
| D-3 | プロンプトテンプレート設計 | `design-d03-prompt-template.md` | FR-3.11, FR-6.1〜6.5 | 提案（承認待ち） |
| D-4 | FTS5 同期トリガー実装 | `design-d04-fts5-sync.md` | FR-3.2 | 提案（承認待ち） |
| D-5 | ウィザード画面フロー | `design-d05-wizard-flow.md` | FR-5.1〜5.9 | 提案（承認待ち） |
| D-6 | エラーメッセージ一覧 | `design-d06-error-messages.md` | FR-7.1〜7.5 | 提案（承認待ち） |
| D-7 | SQLite VACUUM 実行方式 | `design-d07-sqlite-vacuum.md` | 長期運用 | 提案（承認待ち） |
| D-8 | 整合性チェック3類型 | `design-d08-consistency-check.md` | FR-6.4 | 提案（承認待ち） |
| D-9 | トレイ通知の実現可否 | `design-d09-tray-notification.md` | FR-7.2 | 提案（承認待ち） |
| D-10 | .env ファイル設定 | `design-d10-env-file.md` | NFR-8 | 提案（承認待ち） |
| D-11 | Windows 終了シグナル捕捉 | `design-d11-windows-shutdown.md` | FR-3.9 | 提案（承認待ち） |
| D-12 | ウィザード使用モデル | `design-d12-wizard-model.md` | FR-5.7 | 提案（承認待ち） |
| D-13 | session_id 生成規則 | `design-d13-session-id.md` | FR-3.12 | 提案（承認待ち） |
| D-14 | personality_trends 承認フロー | `design-d14-personality-trends-approval.md` | FR-4.6 | 提案（承認待ち） |
| D-15 | max_tokens デフォルト値 | `design-d15-max-tokens.md` | Anthropic API | 提案（承認待ち） |

## 依存関係

```
D-1（ディレクトリ構成）──→ 全 D-item が参照
D-12（ウィザードモデル）──→ D-5（ウィザードフロー）
D-15（max_tokens）──→ D-3（プロンプトテンプレート）
```

## 参照文書

| 文書 | パス |
|------|------|
| 要件定義（承認済み） | `requirements.md` |
| 統合設計案（SSOT） | `docs/memos/middle-draft/04-unified-design.md` |
| 記憶システム設計 | `docs/memos/middle-draft/01-memory-system.md` |
| 人格システム設計 | `docs/memos/middle-draft/02-personality-system.md` |
| GUI・ボディ設計 | `docs/memos/middle-draft/06-gui-and-body.md` |
| キャラクター設計 | `docs/memos/middle-draft/07-character-design.md` |
| プロジェクト構成 | `docs/internal/00_PROJECT_STRUCTURE.md` |
