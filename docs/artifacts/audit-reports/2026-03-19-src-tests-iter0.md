# 監査統合レポート: src/kage_shiki/ + tests/

**日付**: 2026-03-19
**イテレーション**: 0（初回スキャン）
**対象**: src/kage_shiki/ (28ファイル) + tests/ (30ファイル)
**静的解析**: ruff clean, bandit clean, gitleaks no leaks

## サマリー

| 重要度 | 件数 |
|--------|------|
| Critical | 1 |
| Warning | 14 |
| Info | 10 |

| 権限等級 | 件数 |
|---------|------|
| PG | 0 |
| SE | 11 |
| PM | 4 |

---

## Critical (1件)

### [C-1] `_run_background_loop` の `except Exception` が認証エラーを無限リトライ [SE]

**ファイル**: `src/kage_shiki/main.py:112-116`
**観点**: ソースコード品質（Silent Failure 変種）

`process_turn` が `AuthenticationError`（API キー無効）を送出しても、ログを残して `EM-006` を返す処理に吸収される。認証エラーはリトライ不可であり、同一エラーを無限に繰り返す。

**修正案**: `AuthenticationError` を先に捕捉し、`shutdown_event.set()` でループを終了させる。

---

## Warning (14件)

### ソースコード品質 (5件)

**[W-1] `main()` 関数が 218行超過（Long Function）[SE]**
`src/kage_shiki/main.py:256-474`。13ステップの起動シーケンスを1関数に集約。

**[W-2] `set_character_name` と `set_persona_name` が同一実装で重複 + Protocol外未明示 (S-2) [SE]**
`src/kage_shiki/gui/tkinter_view.py:267-293`。`set_character_name` は使用されない Dead Code。

**[W-3] `trends_proposal.py` の `evaluate_triggers` が `self.prompt_addition` を副作用として更新 [SE]**
`src/kage_shiki/agent/trends_proposal.py:157-170`。戻り値と副作用が重複。

**[W-4] `_retry_on_lock` の `wrapper` が暗黙 None を返すパス + 型注釈なし [SE]**
`src/kage_shiki/memory/db.py:186-218`。R-13 精神に反する。到達不能パスの明示が必要。

**[W-5] `PromptBuilder.build_with_truncation` の `_estimate_current` が毎回インスタンス生成 [SE]**
`src/kage_shiki/agent/prompt_builder.py:314-330`。高負荷時のパフォーマンス懸念。

### テストコード品質 (6件)

**[W-6] `test_memory_worker.py` ポジショナル引数の直接アクセス [SE]**
`tests/test_memory/test_memory_worker.py:107`。`call_args.args[1]` がシグネチャ変更で無言で誤検知。

**[W-7] `test_wizard_gui.py` 他で `Path("/tmp/test")` ハードコード [SE]**
`tests/test_gui/test_wizard_gui.py:128,139,152,167` 他。Windows 環境で存在しないパス。

**[W-8] テスト不在: `prompt_builder.py` [SE]**
`tests/test_agent/test_prompt_builder.py` が存在しない。プロンプト構築ロジックの単体テスト不在。

**[W-9] テストファイル肥大化 3件 [SE]**
`test_agent_core.py` (1113行), `test_db.py` (887行), `test_wizard.py` (931行)。300行目安超過。

**[W-10] `test_skeleton.py` の `Path(__file__).parent.parent.parent` でプロジェクトルート算出 [SE]**
`tests/test_core/test_skeleton.py:44,63,69`。テストファイル移動時にサイレントに誤動作。

**[W-11] session スコープの `tk_root` テスト間状態漏れリスク [SE]**
`tests/test_gui/conftest.py:18`。`autouse` クリーンアップフィクスチャ追加を推奨。

### 仕様ドリフト (3件 — PM級)

**[W-12] FR-7.3 仕様ドリフト — DB ロック後のメモリバッファ未実装 [PM]**
`src/kage_shiki/memory/db.py:200-218`。仕様は「失敗時はメモリバッファに一時保持」を要求するが、`_retry_on_lock` は5回リトライ後に `raise` するのみ。EM-008 (`buffering {N} observations in memory`) も Dead Code。
**選択肢**: (A) メモリバッファ実装 (B) FR-7.3 仕様を「リトライのみ」に緩和

**[W-13] FR-4.4 仕様ドリフト — 手動編集検出後のユーザー確認フロー未実装 [PM]**
`src/kage_shiki/main.py:325-329`。`detect_manual_edit()` が `True` でも `logger.warning()` のみ。EM-011（再凍結確認ダイアログ）が Dead Code。
**選択肢**: (A) `show_warning_bar(EM-011)` 呼び出し実装 (B) FR-4.4 を「ログ出力のみ」に緩和

**[W-14] FR-4.4 仕様ドリフト — 手動編集ハッシュが起動間で永続化されていない [PM]**
`src/kage_shiki/persona/persona_system.py:220-224`。`_file_hash` は同セッション内でしか有効でなく、「前回凍結時との比較」が機能しない。
**選択肢**: (A) `freeze_and_save()` 時にハッシュをメタデータに永続化 (B) 仕様を「同セッション内の変更検出」に限定

---

## セキュリティ (Medium 3件 — Info 扱い)

**[I-S1]** `subprocess.Popen` の `sys.executable` 信頼性前提が未文書化 (`main.py:440`) [SE]
**[I-S2]** `check_same_thread=False` のスレッドセーフ設計意図が未文書化 (`db.py:133`) [SE]
**[I-S3]** `wizard.py` の `generation_metadata` にユーザー入力生テキスト保持 (`wizard.py:447`) [SE]

> セキュリティ監査総合: Critical/High 0件。現実的な攻撃経路は構成されない。

---

## Info (10件 — 修正不要)

省略。主な内容: config.py getattr 型安全性、db.py PRAGMA コメント不足、agent_core.py re-export、
wizard.py ネスト関数のテスト不可性、tkinter_view.py トグル状態参照不可、テスト名具体性不足、
truncation.py 未知モデルフォールバック無警告、weekday コメント不足、仕様書スコープ境界識別子競合。

---

## 前回レポート (2026-03-16) との対応

| 前回 Issue | 今回 | 状態 |
|-----------|------|------|
| C-1: `_retry_on_lock` 暗黙 None 返却 | W-4 | Warning に再分類（型安全性問題） |
| C-2: `persona_system.py` エラーハンドリング欠如 | 未検出 | 修正済み or 改善済みの可能性 |
| C-3: `shutdown_handler` テスト間共有 | 未検出 | 既知（設計上の選択） |
| C-4: `test_agent_core.py` ポジショナル引数 | W-6 相当 | テスト側に移動 |
| C-5: `test_truncation.py` 内容未検証 | 未検出 | 改善済みの可能性 |
| C-6: `test_e2e.py` テスト重複 | 未検出 | 改善済みの可能性 |
| PM: trends_proposal Shotgun Surgery | 据え置き | Phase 2b で対応 |
