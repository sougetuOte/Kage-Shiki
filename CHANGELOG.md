# Changelog — 影式 (Kage-Shiki)

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed (LAM v4.5.0 移行 Phase 1-3)

- **refactor**: MAGI System 導入 — Three Agents Model を MELCHIOR/BALTHASAR/CASPAR に改名 + Reflection ステップ追加
  - 影響: rules/ (decision-making, phase-rules), docs/internal/ (06_DM, 01_RM, 02_DF), CHEATSHEET.md, commands/planning, agents/quality-auditor 等
- **feat**: code-quality-guideline.md 新規追加 — Critical/Warning/Info 三層品質基準 + Green State Issue 条件
- **feat**: planning-quality-guideline.md 新規追加 — Requirements Smells, RFC 2119, SPIDR, WBS 100%, Example Mapping
- **feat**: /magi スキル新設 — AoT + MAGI System + Reflection による構造化意思決定
- **feat**: /clarify スキル新設 — 文書精緻化インタビュー（曖昧さ・矛盾・欠落検出）
- **feat**: ui-design-guide スキル新設 — UI/UX 設計チェックリスト
- **refactor**: full-review.md を 6 Stage 体系に全面再編（Scalable Code Review 統合）
- **refactor**: lam-orchestrate — /magi スキル統合、hooks 連携拡充、エスカレーション 6 条件化
- **refactor**: 全エージェント — permission-level フロントマター移動、quality-auditor Sonnet 化、tdd-developer Pre-flight 追加
- **refactor**: SSOT 3 層再構成（docs/internal/ が情報層 1、CLAUDE.md はブートストラップ）
- **refactor**: R-5/R-6 リナンバリング（影式固有 R-5→R-12, R-6→R-13）+ LAM R-5/R-6 追加
- **docs**: SCR specs 4 件 + design 1 件取込（docs/specs/lam/, docs/design/）
- **docs**: v4.4.1 未反映 3 件対応（Memory 列、99_reference、Memory Policy 名）
- **refactor**: lam-stop-hook.py 全面書き換え（541→226行、安全ネット化。Green State判定をfull-review Stage 5に移管）
- **feat**: analyzers/ 13モジュール新規導入（Scalable Code Review 静的解析パイプライン基盤）
- **security**: pre-tool-use.py に _PG_BLACKLISTED_ARGS チェック追加（10項目）
- **feat**: PostToolUseFailure イベント対応（settings.json + post-tool-use.py）
- **test**: stop-hook テスト書き換え（Green State→安全ネット）+ integration テスト更新（834 tests）

- **fix(audit)**: src/tests full-review GREEN STATE 達成 — Critical 1 + Warning 14 修正
  - C-1: main.py AuthenticationError 捕捉追加
  - W-2: tkinter_view set_character_name 削除、set_persona_name 統一
  - W-3: trends_proposal 副作用削除
  - W-4/W-12: db.py 到達不能パス削除 + メモリバッファ実装 + threading.Lock
  - W-13/W-14: EM-011 削除 + FR-4.4 仕様緩和（PM承認済み）
  - tests: project_root フィクスチャ化、tmp_path 化、_cleanup_tk_root 追加
  - 836 tests / 92% coverage / ruff clean / gitleaks + bandit clean

### Fixed

- **fix(audit)**: full-review 4 イテレーション監査 — .claude/ + tests/test_hooks/ の品質 Issue 全修正
  - hooks: 型ヒント修正、stdin バイト制限、XXE コメント是正、secret scan ログ除外、改行エスケープ
  - agents: YAML フロントマター前の無効コメント行を削除（全 8 ファイル）
  - commands: `# permission-level` を HTML コメント化、フロントマター追加（quick-load/save/ship）
  - docs: CHEATSHEET stale refs 修正、building.md 閾値 3→2、wave-plan 矛盾解消
  - specs: v4.0.0-immune-system-design 閾値 3→2、anchor-format "ultimate-think" 修正
  - security-commands: Python allow 脚注を二段構成に修正
  - pyproject.toml: `--junitxml` 追加 + version 0.2.0
  - tests: +3 テスト（settings.local PM 判定、XML `<error>` 要素、絶対パス doc-sync）
  - 830 tests / 92% coverage / ruff clean

## [0.2.0] - 2026-03-14

Phase 1 全機能実装 + Phase 2a 統合テスト完了 + LAM v4.4.1 フレームワーク移行。
827 tests / 92% coverage / ruff clean。

### Added (LAM v4.4.1 移行)

- TDD 内省パイプライン v2（JUnit XML 方式、閾値 2 回、/retro Step 2.5）
- Hooks 大規模化（_hook_utils、hookSpecificOutput、out-of-root 検出、secret scan）
- ADR 0002〜0005（モデルルーティング、Stop hook、context7、Bash allow-list）
- full-review 全ファイルスキャン必須化（差分チェックモード廃止）
- docs/artifacts/ ディレクトリ新設（knowledge, audit-reports, tdd-patterns）
- docs/specs/lam/ に tdd-introspection-v2.md, release-ops-revision.md 取込
- trust-model.md v2 仕様化（TSV ログ形式、パターン照合ロジック）

### Changed (LAM v4.4.1 移行)

- LAM フレームワークを v4.0.1 → v4.4.1 に移行
- コマンド再編: quick-save/load 拡張、/ship 新設
- Release Flow を Web サービス前提からプロジェクト種別非依存に汎用化
- 権限等級に影式固有パターン追加（docs/internal/, pyproject.toml）
- 全 8 エージェントに permission-level フロントマター追加

### Removed (LAM v4.4.1 移行)

- 廃止コマンド 7 件: /daily, /focus, /full-load, /full-save, /adr-create, /impact-analysis, /security-review
- ultimate-think スキル（lam-orchestrate に統合）
- hook_utils.py（_hook_utils.py に置換）

### LAM 4.0.1 移行 (2026-03-10)

- 全8エージェントに permission-level 注記追加
- full-review 4エージェント並列構成・Green State G1-G5・自動ループ制御追加
- docs/specs/lam/ 新規作成（免疫システム要件・設計、Green State 定義 等 計7ファイル）
- ADR-0001 免疫システムアーキテクチャ決定記録
- Hooks + Automation 基盤（pre-tool-use, post-tool-use, lam-stop-hook, pre-compact）

### Phase 2a: 基盤強化

#### スモークテスト修正 (2026-03-08)

- **fix(gui)**: 突っつきボタン(♪)追加、チャット追記表示、ユーザー名表示対応
- **fix(gui)**: ウィザード — キーワード区切り日本語対応、凍結完了メッセージ改善
- **fix(main)**: on_click接続、ウィザード再起動コールバック、キャラ名/ユーザー名設定、root.destroy追加
- **fix(memory)**: FTS5クエリサニタイズ（特殊文字エスケープ）
- **fix(persona)**: ウィザード — リスト値→文字列変換
- **fix(tray)**: toggle表示/最小化、ウィザードメニュー、wizard_callback追加
- **fix(config)**: window_height デフォルト 300→450
- **test**: FTS5特殊文字・リスト値変換・toggle/wizard関連テスト追加
- **test**: 722 tests / 92% coverage

#### Wave 3 + Full Review (2026-03-07)

- **T-32**: 応答タイミング統合テスト `test_response_timing.py` 新規（FR-8.11, D-20 Section 4.4）
- **fix(gui)**: `tkinter_view.py` `_warning_bar_toggle` 未初期化修正
- **fix(gui)**: `wizard_gui.py` ValueError 後の画面遷移漏れ修正
- **docs(specs)**: D-17 仕様を実装に同期（`send_message_for_purpose` Protocol 昇格を反映）
- **chore**: `pyproject.toml` に `pytest.mark.integration` マーカー登録
- **chore**: Full Review 監査 — 修正7件（据置は Phase 2b 追跡済み）
- **test**: 711 tests / 92% coverage（Wave 2: 710 tests → +1 test）

#### Wave 2 + Full Review + 構造リファクタリング (2026-03-07)

- **T-31**: ウィザードGUI `gui/wizard_gui.py` 新規（FR-8.8, D-19）
- **feat(agent)**: `LLMProtocol` に `send_message_for_purpose` 追加（テスト mock の spec 統一）
- **refactor(agent)**: `PromptBuilder` を `agent/prompt_builder.py` に分離（agent_core.py から ~350行抽出、re-export 維持）
- **refactor(agent)**: `format_history_line` 共通ヘルパー追加（human_block_updater / trends_proposal の履歴フォーマット重複解消）
- **refactor(test)**: テスト fixture 統一 — `tests/conftest.py` に共通 `mock_llm(spec=LLMProtocol)` / `config()` 配置
- **fix(main)**: `_run_wizard` の未使用 `api_key` 引数削除、EM-003 テンプレートキー修正
- **fix(main)**: `root.destroy()` 競合修正、シャットダウン二重実行防止の設計意図コメント追加
- **fix(test)**: `test_e2e.py` Cold Memory assertion の vacuous truth バグ修正
- **fix(agent)**: `trends_proposal.py` R-6 違反修正（未知 trigger_type で raise ValueError）
- **fix(persona)**: `load_personality_trends` に OSError 処理追加（load_human_block と対称化）
- **chore**: Full Review 監査 — Critical 5件 + Warning 14件 + Info 9件 修正（対応不可 4件は追跡記録済み）
- **chore(memory)**: `db.py` PRAGMA 値を名前付き定数化、Unreachable 行削除
- **docs**: 設計書 d16/d18 に PromptBuilder 分離を反映、00_PROJECT_STRUCTURE.md 更新
- **test**: 710 tests / 93% coverage（Wave 1: 687 tests → +23 tests）

#### Wave 1 (2026-03-06)

- **T-27**: スモークテスト手順書 `docs/testing/smoke-test.md`（FR-8.1）+ GUI手動テスト手順書 `docs/testing/gui-manual-test.md`（FR-8.2）
- **T-28**: `LLMProtocol`（`typing.Protocol`, `@runtime_checkable`）抽出 + `LLMClient.chat()` 委譲メソッド追加（FR-8.6, D-17）
- **T-28**: `AgentCore`, `MemoryWorker`, `WizardController` の型注釈を `LLMProtocol` に変更
- **T-29**: トランケートアルゴリズム `build_with_truncation()` 実装（FR-8.7, D-18）
- **T-29**: `agent/truncation.py` 新規（定数 + `estimate_tokens` + `get_effective_token_limit`）
- **T-30**: 統合テスト追加 — マルチスレッド（FR-8.3）、永続状態（FR-8.4）、シャットダウン（FR-8.5）
- **fix(test)**: `process_turn` の `build_with_truncation` 切替に伴う既存テストモック修正（2件）
- **test**: 687 tests / 97% coverage（Phase 1: 649 tests → +38 tests）

#### PLANNING 完了 (2026-03-06)

- **docs(specs)**: Phase 2a 要件定義書 `requirements.md` 作成・承認（FR-8.1〜8.11、NFR-11〜12）
- **docs(specs)**: 設計書 D-17〜D-20 作成・承認（LLMProtocol / トランケート / ウィザードGUI / 統合テスト）
- **docs(specs)**: タスク分解 `tasks.md` 作成・承認（T-27〜T-32、6タスク、Wave 1〜3）
- **chore(.claude)**: `building-checklist.md` に R-11（Green直後3点ミニチェック）追加
- **chore(.claude)**: `spec-sync.md` に NFR チェック追加（Phase 1 Retro Try-2）
- **chore(.claude)**: `wave-plan.md` にタスク数上限追加

### Phase 1: 基盤（MVP）

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
