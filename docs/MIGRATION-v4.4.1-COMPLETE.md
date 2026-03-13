# LAM v4.4.1 移行完了 — Migration Notice

**移行日**: 2026-03-14
**影式バージョン**: v4.4.1 based (Phase 5 完了)
**ステータス**: Production Ready

---

## 概要

LAM (Living Architect Model) フレームワークを v4.0.1 から v4.4.1 に移行しました。
以下の主要な変更が適用されています。

---

## ユーザー向け変更一覧

### セッション管理コマンドの簡素化

**変更前（v4.0.1）**:
- `/quick-save`: SESSION_STATE.md 記録のみ
- `/quick-load`: 1 行簡易報告
- `/full-save`: SESSION_STATE + git commit + push + Daily 記録
- `/full-load`: 詳細な状態確認

**変更後（v4.4.1）**:
- `/quick-save`: SESSION_STATE + Daily 記録 + ループログ保存（推奨セッション終了時コマンド）
- `/quick-load`: SESSION_STATE + 関連ドキュメント特定 + 復帰サマリー（推奨セッション再開時コマンド）
- `/ship`: git commit + push + ドキュメント同期（新規コマンド）

**影響**: 日常のセッション管理が 2 コマンド（quick-save/load）に簡潔化。git 操作は `/ship` に統一。

---

### 廃止されたコマンド

以下の 7 コマンドが廃止され、吸収先に統合されました:
- `/daily` → `/quick-save` Step 3 で Daily 記録
- `/focus` → 非推奨（ポモドーロ管理は別ツール推奨）
- `/full-load` → `/quick-load` の 4 ステップ化で完全吸収
- `/full-save` → `/quick-save` + `/ship` の 2 コマンド化で分離
- `/adr-create` → `adr-template` スキル経由
- `/impact-analysis` → `/building` Phase 4 に組込
- `/security-review` → `/full-review` Phase 1 に統合

---

### TDD 内省パイプライン v2 への移行

**変更点**:
- テスト結果検出が exitCode 方式（動作せず）から JUnit XML 方式に変更
- 検出閾値が 3 回 → 2 回に引き下げ
- パターン分析が PostToolUse 自動 → `/retro` Step 2.5 で人間主導に変更

**影響**: TDD パターン記録が正常に機能開始。規則提案のタイミングが早まります。

---

### full-review の全ファイルスキャン必須化

**変更点**: 毎イテレーションで指定範囲の全ファイルを探索する（差分チェックモード廃止）。

**理由**:
- 修正による周辺への波及影響の捕捉
- 修正で蓋をされていた潜在問題の露出
- 予期しない場所での影響発生の検出

---

### ディレクトリ構造の新規整備

新規ディレクトリ:
- `docs/artifacts/`: 監査レポート、知見蓄積、TDD パターン記録の新規保存先
- `docs/daily/`: 日次記録ファイルの格納ディレクトリ
- `.claude/agent-memory/`: Subagent の永続メモリ（将来対応）

**既存への影響**: `docs/memos/` は「生メモ・中間草案」として引き続き使用。両ディレクトリは役割分担で共存。

---

### Hooks の大規模強化

**変更点**:
- `hook_utils.py` → `_hook_utils.py` にリネーム + 新 API 追加（Windows retry 付き atomic write 等）
- pre-tool-use: out-of-root 検出、hookSpecificOutput 形式、AUDITING PG 特別処理
- post-tool-use: JUnit XML パース、失敗テスト名記録、FAIL→PASS 時の systemMessage 通知
- lam-stop-hook: convergence_reason 記録、pm_pending フラグ、シークレットスキャン、Issue 再発チェック、ループログ保存

---

### ADR・仕様書の追加

- ADR 0002〜0005（LAM v4.4.1 ADR-0001〜0004 を +1 シフトして取込）
- `docs/specs/lam/tdd-introspection-v2.md`（TDD 内省 v2 仕様）
- `docs/specs/lam/release-ops-revision.md`（Release Ops 改訂仕様）

---

## クイックリファレンス（新ワークフロー）

### セッション終了時
```
/quick-save  # SESSION_STATE + Daily 記録 + ループログ保存
```

### セッション再開時
```
/quick-load  # 前回状態復帰 + 復帰サマリー表示
```

### git コミット・プッシュ時
```
/ship  # ドキュメント同期 + コミット + プッシュ
```

### 監査実施時
```
/full-review <target>  # 対象の全ファイル網羅レビュー
```

### 振り返り時
```
/retro  # Wave/Phase 完了時の振り返りとパターン分析
```

---

## トラブルシューティング

### "_hook_utils.py" import エラー

**症状**: `from _hook_utils import ...` でエラー
**原因**: 古い `hook_utils.py` がまだ存在している可能性
**対応**: `.claude/hooks/hook_utils.py` を削除

### JUnit XML ファイルが生成されない

**症状**: `post-tool-use.py` が `.claude/test-results.xml` を見つけられない
**原因**: `pyproject.toml` の `addopts` に `--junitxml` が未設定
**対応**: `pyproject.toml` の `[tool.pytest.ini_options]` に `addopts = "--junitxml=.claude/test-results.xml"` を追加

---

## 参照資料

- `CLAUDE.md`: プロジェクト憲法（Context Management 更新済み）
- `CHEATSHEET.md`: クイックリファレンス（コマンド再編済み）
- `docs/internal/02_DEVELOPMENT_FLOW.md`: 開発フロー（TDD v2 対応済み）
- `docs/specs/lam/tdd-introspection-v2.md`: TDD 内省 v2 仕様
- `.claude/rules/phase-rules.md`: Phase 別ルール（TDD v2 記載）

---

**移行完了日**: 2026-03-14
**移行計画**: `docs/memos/v4-4-1-update-plan/`
