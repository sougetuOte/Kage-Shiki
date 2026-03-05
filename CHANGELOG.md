# Changelog — 影式 (Kage-Shiki)

All notable changes to this project will be documented in this file.

## [Unreleased]

### Phase 1: 基盤（MVP）— BUILDING 進行中

#### Wave 8 (2026-03-05)

- **T-25**: 起動シーケンス統合（main.py 13ステップ + バックグラウンドループ + 応答ポーリング + シャットダウンCB）
- **fix(C-01)**: AgentCore の PromptBuilder 外部注入化（getattr プライベート属性アクセス廃止）
- **fix(W-T25)**: process_turn に human_block 更新 + trends 承認フロー統合
- **feat**: `get_recent_day_summaries()` Warm Memory ロード関数 + `PersonaCore.to_markdown()` 日本語ラベル付き出力
- **feat**: TrendsProposalManager 起動時初期化 + トリガー評価接続
- **fix**: LLMClient コンストラクタ呼び出し修正（api_key 引数除去 — D-10 環境変数準拠）
- **audit**: full-review 12件修正（shutdown CB 例外捕捉、到達不能フォールバック除去、テスト allowlist 等）
- **docs**: D-16 設計仕様書 + design-index 追加

#### Wave 7 (2026-03-04)

- **T-14**: クリックイベント（突っつき）処理（POKE_EVENT_PREFIX + purpose="poke" 切替）
- **T-15**: 整合性チェック公開定数エイリアス + consistency_hit_count セッションカウンタ
- **T-16**: personality_trends 承認フロー（T1/T2 トリガー + 提案パース + 承認/却下判定）
- **T-17**: human_block 自己編集（マーカーパース + ガードレール5種 + 履歴フォーマット）
- **T-19**: シャットダウン2層防御（ctypes SetConsoleCtrlHandler + atexit + 2重実行防止）
- **T-23**: ウィザード方式C（白紙育成 + blank_freeze_threshold 凍結提案）
- **audit**: full-review 10件修正（dict.get() WARNING ログ化、VALID_SECTIONS 統合、Phase 2 マーク追記 等）

#### Wave 6 (2026-03-04)

- **T-13**: AgentCore ReAct ループ（FTS5 検索 + プロンプト構築 + LLM 呼出 + observations 書込 + 整合性チェック）
- **T-18**: MemoryWorker（日次サマリー生成 + 欠損日補完 + EM-009 フォールバック）
- **T-21**: WizardController 方式 B（自由記述 → AI 整形補完 → C1-C11 + S1-S7）
- **T-22**: プレビュー会話 + 凍結処理（freeze_and_save 公開 API 追加）
- **audit**: full-review 12件修正（カプセル化違反修正、例外ログ強化、タイムスタンプ分離 等）

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
