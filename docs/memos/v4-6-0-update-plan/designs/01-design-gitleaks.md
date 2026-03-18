# LAM v4.6.0 移行設計書 — gitleaks 統合 + 延期 Issue 解消

**作成日**: 2026-03-18
**ステータス**: 承認済み
**差分サマリー**: `../specs/00-diff-summary.md`

---

## 1. Problem Statement

LAM v4.6.0 の主要変更である gitleaks 統合を影式に適用し、
シークレットスキャンを言語・ファイル形式非依存にする。
併せて、延期 Issue B/E の修正を取り込む。

## 2. Non-Goals

- gitleaks のカスタムルール作成（`.gitleaks.toml` はデフォルトで十分）
- 延期 Issue C/F の対応（不要と判断済み）
- docs/slides/ の更新（影式には既存なし）

## 3. 設計方針

### 3.1 Phase 1: gitleaks コード導入

#### 3.1.1 gitleaks_scanner.py（新規）

LAM v4.6.0 のファイルをそのまま導入:
- `is_available()` — PATH に gitleaks があるか
- `run_detect(project_root, config_path, enabled)` — リポジトリ全体スキャン
- `run_protect_staged(project_root, config_path, enabled)` — staged スキャン
- `_run_gitleaks(cmd, timeout)` — 共通実行ヘルパー
- `_parse_gitleaks_json(json_path)` — JSON → Issue 変換（シークレット値は格納しない）

ソース: `docs/memos/LivingArchitectModel-4.6.0/.claude/hooks/analyzers/gitleaks_scanner.py`

#### 3.1.2 config.py（更新）

- `gitleaks_enabled: bool = True` フィールド追加
- `_parse_bool()` ヘルパー追加（型安全パーサー）
- `load()` に `gitleaks_enabled` パース追加

#### 3.1.3 run_pipeline.py（更新）

- `from analyzers.gitleaks_scanner import run_detect as gitleaks_run_detect` import 追加
- `run_phase0()` に gitleaks 呼び出し追加
- analyzers なしでも gitleaks は実行（言語非依存）
- `line_count` 算出条件の変更（analyzers なしでも 0 を返す）

#### 3.1.4 .gitleaks.toml（新規）

LAM v4.6.0 のファイルを導入。除外ルール等のプロジェクト固有設定。

#### 3.1.5 テスト

- `test_gitleaks_scanner.py` — LAM v4.6.0 の 28 テストをそのまま導入
- `test_config.py` — `gitleaks_enabled` パーステスト + `_parse_bool` テスト追加
- `test_run_pipeline.py` — gitleaks 統合テスト追加

#### 3.1.6 延期 Issue B: PostToolUseFailure 対応

`post-tool-use.py` の変更:
- `_handle_test_result()` に `is_failure_event: bool = False` パラメータ追加
- `is_failure_event=True` 時は XML を読まず直接 FAIL 記録
- `main()` で `hook_event_name` を取得し `PostToolUseFailure` 判定

### 3.2 Phase 2: コマンド + 仕様書更新

#### 3.2.1 full-review.md（更新）

- Stage 1 Step 1 に gitleaks NOTE ブロック追加
- Stage 5 G5 セキュリティチェックを gitleaks ベースに更新
- gitleaks 未インストール時の G5 FAIL ロジック記述

#### 3.2.2 ship.md（更新）

Phase 1 にステップ 2 として gitleaks protect --staged を挿入:
```
1. git status + git diff
2. gitleaks protect --staged（新規）
3. 秘密情報パターンチェック（既存）
4. 結果表示
```

#### 3.2.3 仕様書・設計書取込

- `docs/specs/lam/gitleaks-integration-spec.md` — 新規取込（LAM 由来仕様書は `docs/specs/lam/` に格納）
- `docs/design/gitleaks-integration-design.md` — 新規取込
- `docs/specs/lam/scalable-code-review-spec.md` — FR-7e gitleaks 言及追記
- `docs/design/hooks-python-migration-design.md` — テスト方式 3 追記（延期 Issue E）

#### 3.2.4 README.md

gitleaks を環境要件として追記。

### 3.3 Phase 3: 統合検証

- 全テスト実行（既存 834 + gitleaks 28 + config/pipeline 拡充）
- ruff check クリーン
- `gitleaks detect --source .` で実プロジェクトスキャン
- `gitleaks version` 確認（8.30.0）

## 4. Alternatives Considered

| 案 | 判定 | 理由 |
|:---|:-----|:-----|
| gitleaks を推奨ツールとして文書化のみ | 却下 | シークレット漏洩は「すり抜けに気づかない」性質。パイプライン統合が必要 |
| 自前パターンの拡充で対応 | 却下 | gitleaks は 800+ ルール + エントロピー分析。保守コスト不合理 |
| gitleaks 未インストールで G5 PASS | 却下 | セキュリティの意味がなくなる |

## 5. Success Criteria

- gitleaks_scanner.py のテスト 28 件 PASS
- config.py の gitleaks_enabled テスト PASS
- run_pipeline.py の gitleaks 統合テスト PASS
- 全テスト（既存 + 新規）PASS
- ruff check クリーン
- `gitleaks detect` が実プロジェクトで動作確認
- full-review.md / ship.md が v4.6.0 の gitleaks 記述を含む
