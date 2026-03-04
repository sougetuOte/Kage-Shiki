# Changelog — 影式 (Kage-Shiki)

All notable changes to this project will be documented in this file.

## [Unreleased]

### Phase 1: 基盤（MVP）— BUILDING 進行中

#### Wave 5 (2026-03-04)

- **T-06**: session_id 生成（ハイブリッド形式）+ observations CRUD 5関数 + FTS5 検索
- **T-12**: PromptBuilder（S1-S7 SystemPrompt + Messages 配列 + Cold Memory 注入）
- **T-20**: WizardController 方式 A（連想拡張 + 候補生成 + スタイルサンプル生成）
- **audit**: full-review 19件修正（必須フィールド検証、TOML int→float、docstring 単位修正 等）
- **chore**: 通知サウンドを wav 増幅再生に変更 + Notification 承認待ち対応

#### Wave 4 (2026-03-03)

- **T-09**: PersonaSystem 補助パーサー（style_samples, human_block, personality_trends）
- **T-24**: エラーメッセージ定義（EM-001〜EM-011）+ show_error_screen / show_warning_bar
- **audit**: db.py PRAGMA 検証・二重接続ガード + テスト共通化
- **docs**: D-4 trigram tokenizer 追記、D-6 Protocol 外メソッド方針明文化
- **chore**: レビュールール（spec-sync, audit-fix-policy）+ /full-review スキル + 完了通知 Hook

#### Wave 3 (2026-03-02)

- **T-03**: env.py 環境変数管理（API キー検証 + .env ロード）
- **T-04**: logging_setup.py ログ設定（RotatingFileHandler + フォーマット）
- **T-07**: LLMClient（purpose ベースモデルスロット + リトライ + ストリーミング）
- **T-08**: PersonaSystem（3段階ペルソナロード + 凍結制御 + 手動編集検出）
- **T-11**: SystemTray（pystray 統合 + メニュー + 通知 + フォールバック）
- **audit**: 全ソース監査修正（178 tests, 98% cov）
- **docs**: D-1, D-2, D-15 仕様書を実装に同期

#### Wave 1-2 (2026-03-01)

- **T-01**: プロジェクト骨格（ディレクトリ構造 + pyproject.toml）
- **T-02**: AppConfig（TOML パーサー + バリデーション + デフォルト生成）
- **T-10**: MascotView Protocol + TkinterMascotView（枠なしウィンドウ + ドラッグ移動）
- **T-05**: SQLite DB 初期化 + FTS5 トリガー + WAL モード
- **audit**: ruff lint 対応

### Project Initialization (2026-02-28)

- プロジェクト作成・基盤ファイル適応
- 参考文献調査・中間文書作成 (`docs/memos/middle-draft/`)
- AoT + Three Agents 統合設計分析
- Phase 1 MVP 仕様書群を追加（要件定義・設計・タスク）
- docs/internal の Python 向け最適化
