# Changelog — 影式 (Kage-Shiki)

All notable changes to this project will be documented in this file.

## [Unreleased]

### Phase 2a: 基盤強化 — PLANNING 完了

#### PLANNING 完了 (2026-03-06)

- **docs(specs)**: Phase 2a 要件定義書 `requirements.md` 作成・承認（FR-8.1〜8.11、NFR-11〜12）
- **docs(specs)**: 設計書 D-17〜D-20 作成・承認（LLMProtocol / トランケート / ウィザードGUI / 統合テスト）
- **docs(specs)**: タスク分解 `tasks.md` 作成・承認（T-27〜T-32、6タスク、Wave 1〜3）
- **chore(.claude)**: `building-checklist.md` に R-11（Green直後3点ミニチェック）追加
- **chore(.claude)**: `spec-sync.md` に NFR チェック追加（Phase 1 Retro Try-2）
- **chore(.claude)**: `wave-plan.md` にタスク数上限追加

### Phase 1: 基盤（MVP）— 完了

#### ホットフィックス + 教訓反映 (2026-03-06)

- **fix(runtime)**: `__main__.py` 追加（`python -m kage_shiki` 起動対応）
- **fix(runtime)**: SQLite `check_same_thread=False`（スレッド間DB共有）
- **fix(runtime)**: tkinter スクロール付き Text ウィジェットに変更
- **fix(runtime)**: シャットダウン二重実行防止 + GUI 先行終了 + `root.destroy()`
- **fix(runtime)**: pystray Icon 終了時 stop 追加
- **fix(runtime)**: `day_summary` 既存チェック（UNIQUE 制約違反防止）
- **fix(runtime)**: セッション開始メッセージに現在時刻注入
- **test**: `test_memory_worker.py` 既存サマリーチェックのテスト追加
- **chore(.claude)**: `building-checklist.md` に R-7〜R-10 追加（スレッド安全性・永続状態・シャットダウン経路・GUI目視確認）
- **chore(.claude)**: `phase-rules.md` に Phase 完了判定（実動作スモークテスト必須化）追加
- **docs**: `phase2-backlog.md` に統合テスト強化タスク B-7〜B-11 追加

#### Wave 9 (2026-03-06)

- **T-26**: 結合テスト + E2E 検証（統合テスト 69 件追加、合計 649 tests / 97% coverage）
- **test**: test_e2e.py（基本対話・記憶システム・シャットダウンサマリー・欠損補完・Warm Memory・整合性チェック）
- **test**: test_wizard_e2e.py（方式 A/B/C 全パイプライン・凍結サイクル検証）
- **test**: test_config_reflection.py（config.toml 読み書き・用途別パラメータ解決・AgentCore 連携）
- **test**: test_error_handling.py（EM-001〜011 定義整合・ペルソナエラー・AgentCore エラー耐性）
- **fix(audit)**: AgentCore コンストラクタに trends_manager 引数追加（カプセル化修正）
- **fix(audit)**: cold_top_k を FTS5 検索に反映（config 設定値が未使用だった問題）
- **fix(audit)**: trends_proposal R-6 違反修正（未知種別のデフォルトフォールバック → 破棄）
- **fix(audit)**: load_human_block に OSError ハンドリング追加
- **fix(audit)**: db.py 正規表現・config.py マジックナンバー・shutdown_handler 型アノテーション
- **docs**: NFR-3 に Pillow 追記（仕様同期 S-1）

#### .claude/ 改善 + docs/internal/ 拡充 (2026-03-06)

- **chore(.claude)**: agents 改善（委任条件・役割境界・モデル指定）、rules 改善（AUDITING 実態合わせ・Subagent 委任原則）、settings.json python allow 統一
- **feat(.claude)**: `/retro`（KPT 振り返り）、`/wave-plan`（Wave 計画策定）コマンド新規追加
- **docs(internal)**: 02_DEVELOPMENT_FLOW 拡張（Wave 開発・Advanced Workflows・Quality Rules Integration）
- **docs(internal)**: 08_SESSION_MANAGEMENT 新規作成（セーブ/ロード仕様・コンテキスト残量管理）
- **docs(internal)**: 09_SUBAGENT_STRATEGY 新規作成（エージェント一覧・委任判断・並列パターン・モデル選択）
- **docs(internal)**: 05_MCP_INTEGRATION Phase 1 未導入の明記
- **docs**: CHEATSHEET 日常ワークフローセクション追加

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
