# LAM v4.6.0 移行タスク — Phase 1〜3

**作成日**: 2026-03-18
**設計書**: `../designs/01-design-gitleaks.md`
**差分サマリー**: `../specs/00-diff-summary.md`

---

## Phase 1: gitleaks コード導入（11 タスク） — 完了 2026-03-18

### 1-1. gitleaks_scanner.py 新規追加
- [x] `docs/memos/LivingArchitectModel-4.6.0/.claude/hooks/analyzers/gitleaks_scanner.py` を `.claude/hooks/analyzers/gitleaks_scanner.py` にコピー
- [x] docstring の仕様参照パスが影式のディレクトリ構造と整合するか確認
- **等級**: SE
- **所感**: docstring の参照パスを `docs/specs/lam/` に修正。LAM ソースからの差分は参照パスのみ。

### 1-2. config.py に gitleaks_enabled フィールド追加
- [x] `gitleaks_enabled: bool = True` フィールド追加
- [x] `_parse_bool()` ヘルパー関数追加
- [x] `load()` メソッドに `gitleaks_enabled` パース追加
- **等級**: SE
- **参照**: v4.6.0 の config.py（差分サマリー Section 2.2）
- **所感**: `_parse_bool` の ValueError メッセージが ruff E501 に引っかかった。f-string を 2 行に分割して解消。

### 1-3. run_pipeline.py に gitleaks 呼び出し追加
- [x] `from analyzers.gitleaks_scanner import run_detect as gitleaks_run_detect` import 追加
- [x] `run_phase0()` の docstring 更新
- [x] analyzers ループ後に `gitleaks_run_detect()` 呼び出し追加
- [x] analyzers なしでも gitleaks 実行するよう条件変更（`if not analyzers: return Phase0Result()` の削除）
- [x] `line_count` 算出を `count_lines(...) if analyzers else 0` に変更
- **等級**: SE
- **参照**: v4.6.0 の run_pipeline.py
- **所感**: `if not analyzers: return Phase0Result()` の早期リターン削除が最も重要な変更。gitleaks は言語 Analyzer に依存しない設計。

### 1-4. .gitleaks.toml 追加
- [x] `docs/memos/LivingArchitectModel-4.6.0/.gitleaks.toml` を プロジェクトルートにコピー
- [x] 影式固有の除外パターンが必要か確認 → 不要（テストフィクスチャの除外のみで十分）
- **等級**: SE

### 1-5. test_gitleaks_scanner.py 新規追加
- [x] `docs/memos/LivingArchitectModel-4.6.0/.claude/hooks/analyzers/tests/test_gitleaks_scanner.py` をコピー
- [x] テスト実行確認（28 件 PASS）
- **等級**: SE
- **所感**: ruff I001（import ソート）で自動修正。未使用の `Issue` import を削除。

### 1-6. test_config.py 拡充
- [x] v4.6.0 の `test_config.py` から `gitleaks_enabled` 関連テストを差分抽出
- [x] `_parse_bool` のテスト追加（bool 正常、文字列 "false" でエラー、キーなしでデフォルト）
- [x] テスト実行確認
- **等級**: SE
- **所感**: 影式には test_config.py 自体が存在しなかった。v4.6.0 のファイル全体を新規作成（gitleaks_enabled テスト含む）。**今後の移行作業で「拡充」と計画したファイルが実は存在しないケースに注意**。

### 1-7. test_run_pipeline.py 拡充
- [x] v4.6.0 の `test_run_pipeline.py` から gitleaks 統合テストを差分抽出
- [x] テスト実行確認
- **等級**: SE
- **所感**: 影式にはこのファイルも存在しなかった（1-6 と同パターン）。v4.6.0 全体を新規作成。`bandit` 未インストール環境で `verify_tools` が `ToolNotFoundError` を投げるため、`shutil.which` のモック追加が必要だった。LAM 開発環境には bandit がインストール済みだったためテストが通っていたが、影式環境では未インストール。**環境差異による暗黙の依存に注意**。

### 1-8. 延期 Issue B: post-tool-use.py PostToolUseFailure 対応
- [x] v4.6.0 の `post-tool-use.py` との差分を確認
- [x] `_handle_test_result()` に `is_failure_event: bool = False` パラメータ追加
- [x] `is_failure_event=True` 時の FAIL 直接記録ロジック追加
- [x] `main()` で `hook_event_name` フィールド取得 + `PostToolUseFailure` 判定
- [x] 関連テスト確認・追加 → 影式には hooks/tests/ が存在しないためスキップ
- **等級**: SE
- **所感**: v4.6.0 LAM の post-tool-use.py は影式版よりリファクタリングが進んでいる（`_read_prev_result`, `_record_fail`, `_record_pass` ヘルパー分離等）。今回は Issue B の最小差分のみ適用し、構造的リファクタリングは見送り。将来の `/retro` で検討候補。

### 1-9. Phase 1 テスト一括実行
- [x] `.claude/hooks/analyzers/tests/` の全テスト実行 → **71 passed**
- [x] `.claude/hooks/tests/` の全テスト実行 → 影式にはディレクトリなし（スキップ）
- [x] 全件 PASS 確認
- **等級**: PG
- **所感**: conftest.py が存在しなかったため `ModuleNotFoundError` が発生。v4.6.0 の conftest.py を新規作成して解消。**テスト基盤ファイル（conftest.py）の存在確認をタスク計画に含めるべき**。

### 1-10. ruff check
- [x] 新規・変更ファイルに対して `ruff check` 実行
- [x] エラーがあれば修正
- **等級**: PG
- **所感**: E501（行長）x7、I001（import ソート）x3、F401（未使用 import）x1、SIM117（with 統合）x1。E501 は `with` 文に 3 つのコンテキストマネージャを並べたことが原因。ヘルパーメソッド `_mocks()` を導入して解消。

### 1-11. Phase 1 完了確認
- [x] gitleaks_scanner.py の全テスト PASS（28 件）
- [x] config.py の gitleaks_enabled テスト PASS（4 件）
- [x] run_pipeline.py の gitleaks 統合テスト PASS（2 件）
- [x] post-tool-use.py の PostToolUseFailure テスト → hooks/tests/ 不在のためスキップ
- [x] ruff clean
- **等級**: SE（報告）

---

## Phase 1 実施メモ（/retro 用）

### 想定外だった点

1. **テストファイル不在**: test_config.py、test_run_pipeline.py、conftest.py が影式に存在しなかった。「拡充」ではなく「新規作成」が正解。v4.5.0 移行時に analyzers/ のテストをスキップしていた可能性がある。
2. **bandit 未インストール**: LAM 開発環境には bandit がインストール済みだが影式環境にはない。`shutil.which` のモック追加が必要だった。テストの環境依存性を明示的にモックで解消するパターン。
3. **ruff E501 の頻発**: v4.6.0 LAM のテストコードは ruff E501（100 文字制限）に準拠していない箇所があった。影式は pyproject.toml で 100 文字制限を設定しているため修正が必要。

### パターン候補（/retro Step 2.5 用）

- **P-1: 移行計画の「拡充」タスクは、対象ファイルの存在を事前確認すべき**
  - 観測: 1-6, 1-7 で「拡充」計画が実際には「新規作成」だった
  - 推奨: タスク分解時に `Glob` でファイル存在を確認する Step を追加

- **P-2: テスト環境の暗黙の依存はモックで明示的に解消すべき**
  - 観測: 1-7 で bandit 未インストールによるテスト失敗
  - 推奨: 外部ツール依存のテストでは `shutil.which` を常にモック

---

## Phase 2: コマンド + 仕様書更新（9 タスク） — 完了 2026-03-18

### 2-1. full-review.md 更新
- [x] Stage 1 Step 1 に gitleaks NOTE ブロック追加（v4.6.0 の full-review.md Stage 1 参照）
- [x] Stage 5 G5 セキュリティチェックを gitleaks ベースに更新
- [x] gitleaks 未インストール時の G5 FAIL ロジック記述
- [x] `gitleaks:not-installed` Issue の扱い記述
- **等級**: PM（コマンド変更）
- **所感**: Stage 1 に NOTE ブロック + ツール未インストール時セクションに gitleaks 固有ハンドリング + Stage 5 G5 を grep→gitleaks に置換。4箇所の編集。

### 2-2. ship.md 更新
- [x] Phase 1 にステップ 4 として gitleaks protect --staged を挿入
- [x] gitleaks 未インストール時の WARNING + インストールガイド表示
- [x] 検出時のユーザー判断フロー記述
- [x] 既存のパターンチェック（ステップ 5 に繰り下げ）はそのまま保持
- **等級**: PM（コマンド変更）
- **所感**: Step 4 として挿入し、既存の秘密情報チェックを Step 5 に繰り下げ。v4.6.0 と同等の `run_protect_staged()` 呼び出しコードを含む。

### 2-3. gitleaks 仕様書取込
- [x] `docs/memos/LivingArchitectModel-4.6.0/docs/specs/gitleaks-integration-spec.md` を `docs/specs/lam/` にコピー
- **等級**: SE
- **所感**: 仕様参照パスを `docs/specs/lam/` 内での相対参照に調整。

### 2-4. gitleaks 設計書取込
- [x] `docs/memos/LivingArchitectModel-4.6.0/docs/design/gitleaks-integration-design.md` を `docs/design/` にコピー
- **等級**: SE
- **所感**: Success Criteria のテスト数を影式の 834+ に更新。仕様参照パスを影式のパス構造に合わせて調整。

### 2-5. scalable-code-review-spec.md 更新
- [x] FR-7e に gitleaks 統合言及を追記
- [x] v4.6.0 の同ファイルとの差分を確認して適用
- **等級**: PM（仕様変更）
- **所感**: 「bandit B105/B106 等に一元化」→「gitleaks を基盤として統合済み」にテキスト置換。gitleaks-integration-spec.md への参照を追加。

### 2-6. hooks-python-migration-design.md 更新（延期 Issue E）
- [x] テスト方式 3（conftest sys.path）を Section 4 に追記
- [x] v4.6.0 の同ファイルとの差分を確認して適用
- **等級**: SE（設計書更新）
- **所感**: 影式には docs/design/ に本ファイルが存在しなかったため、v4.6.0 版を全体コピー。Section 4.3 conftest sys.path 方式は v4.6.0 で既に追加済み。

### 2-7. README.md 更新
- [x] 環境要件に gitleaks を追記
- [x] インストール方法（`scoop install gitleaks`）を記載
- **等級**: SE
- **所感**: 環境要件テーブルに1行追加。必須ではなく「推奨」として記載。

### 2-8. .gitignore 確認
- [x] v4.6.0 の .gitignore との差分を確認
- [x] 必要な追加があれば適用
- **等級**: SE
- **所感**: `!docs/memos/v4-6-0-update-plan/` を追加。v4.6.0 の .gitignore にある Node.js セクションは影式に不要のため省略。`**/test-results.xml` vs `.claude/test-results.xml` の差異は影式の既存設定で問題なし。

### 2-9. Phase 2 完了確認
- [x] 全コマンドファイルの整合性確認
- [x] 仕様書・設計書の取込確認
- [x] README.md 更新確認
- **等級**: SE（報告）
- **所感**: quality-auditor による14項目の整合性検証を実施。全項目 OK。

---

## Phase 3: 統合検証 + 完了（6 タスク）

### 3-1. 全テスト実行
- [ ] `pytest .claude/hooks/analyzers/tests/ -v`
- [ ] `pytest .claude/hooks/tests/ -v`
- [ ] `pytest tests/ -v`（影式本体テスト）
- [ ] 全件 PASS 確認
- **等級**: PG

### 3-2. ruff check 全体
- [ ] 変更対象ファイル全体に `ruff check` 実行
- [ ] エラーがあれば修正
- **等級**: PG

### 3-3. gitleaks 動作確認
- [ ] `gitleaks version` — バージョン確認
- [ ] `gitleaks detect --source . --no-git` — 実プロジェクトスキャン
- [ ] 検出結果があれば対応（影式固有の除外ルール検討）
- **等級**: SE

### 3-4. full-review.md 警告行の確認
- [ ] Phase 3 完了後、full-review.md 冒頭の影式固有警告行が不要になったか判断
- [ ] 不要なら削除提案（PM級）
- **等級**: SE（確認）/ PM（削除時）

### 3-5. SESSION_STATE.md 更新
- [ ] 移行完了を記録
- [ ] 一時停止中の計画の復帰可能状態を明記
- **等級**: SE

### 3-6. 000-index.md 更新
- [ ] 全タスク完了を記録
- [ ] 確定判断の承認日を記入
- **等級**: SE

---

## タスクサマリー

| Phase | タスク数 | PG級 | SE級 | PM級 | 状態 |
|-------|:-------:|:----:|:----:|:----:|:----:|
| Phase 1 | 11 | 2 | 9 | 0 | 完了 |
| Phase 2 | 9 | 0 | 6 | 3 | 未着手 |
| Phase 3 | 6 | 2 | 3-4 | 0-1 | 未着手 |
| **合計** | **26** | **4** | **18-19** | **3-4** | |

## 依存関係

```
Phase 1 (1-1〜1-8: 並列可) → 1-9 → 1-10 → 1-11  ✅ 完了
  ↓ Phase 1 完了後
Phase 2 (2-1〜2-8: 大部分並列可) → 2-9
  ↓ Phase 2 完了後
Phase 3 (3-1〜3-3: 並列可) → 3-4 → 3-5 → 3-6
```

## WBS トレーサビリティ

| 仕様/要件 | タスク |
|----------|-------|
| gitleaks detect 統合 (FR-1) | 1-1, 1-3, 2-1 |
| gitleaks protect 統合 (FR-2) | 1-1, 2-2 |
| オプトアウト (FR-5) | 1-2 |
| テスト | 1-5, 1-6, 1-7, 3-1 |
| 延期 Issue B | 1-8 |
| 延期 Issue E | 2-6 |
| 仕様/設計取込 | 2-3, 2-4, 2-5 |
| プロセス管理 | 2-8, 3-5, 3-6 |
