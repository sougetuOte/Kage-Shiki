# Phase 5 タスク: 統合検証 + 完了

**ステータス**: Draft
**対象設計**: 全設計文書のクロスチェック + スモークテスト
**優先度**: 高（完了条件の確認）
**依存**: Phase 1-4 完了

---

## タスク一覧（概要）

| # | タスク | 検証対象 | 権限等級 | 規模 |
|---|--------|---------|---------|------|
| P5-1 | 差分積分の最終確認 | Phase 1-4 の全変更が予定通り適用 | PG 級 | M |
| P5-2 | スモークテスト実施 | 基本機能の動作確認 | PG 級 | M |
| P5-3 | 参照完全性チェック | ファイル参照が断絶していない | PG 級 | M |
| P5-4 | 後続作業の PM 承認ゲート | trust-model v2 化, RELEASE_OPS 改訂, agent-memory 等 | PM 級 | S |
| P5-5 | 完了報告と migration notice | 移行完了アナウンス、ユーザーガイド | SE 級 | S |

---

## Phase 5A: 差分積分の最終確認

### P5-1: Phase 1-4 の全変更チェックリスト実行

**概要**: 設計文書から導出した全タスクが完了したかを機械的に確認。

**対象ファイル**: 本 Phase-Wise タスク分解ドキュメント（02-tasks-phase1.md 〜 02-tasks-phase4.md）

**確認対象**:

```
[ ] Phase 1: settings.json
  ├─ [ ] P1-1: find -delete 等の deny パターン追加
  ├─ [ ] P1-2: find を ask に移動
  ├─ [ ] P1-3: python * を ask に追加
  └─ [ ] P1-4: 動作確認 OK

[ ] Phase 2: ルール + docs/internal/ + CLAUDE.md
  ├─ Phase 2A: .claude/rules/ (9ファイル)
  │  ├─ [ ] P2A-1: test-result-output.md 新規追加
  │  ├─ [ ] P2A-2: security-commands.md 三分類化 + Python 保持
  │  ├─ [ ] P2A-3: permission-levels.md 拡充 + 影式パス再追加
  │  ├─ [ ] P2A-4: phase-rules.md TDD v2 更新
  │  ├─ [ ] P2A-5: core-identity.md パス変更
  │  ├─ [ ] P2A-6: upstream-first.md 全面更新
  │  ├─ [ ] P2A-7: auto-generated/README.md v2 更新
  │  ├─ [ ] P2A-8: auto-generated/trust-model.md v2 更新
  │  └─ [ ] P2A-9: building-checklist.md 保護確認
  ├─ Phase 2B: docs/internal/ (6ファイル)
  │  ├─ [ ] P2B-1: 00_PROJECT_STRUCTURE.md artifacts/ + agent-memory/ 追加
  │  ├─ [ ] P2B-2: 02_DEVELOPMENT_FLOW.md TDD v2 + Wave セクション保護
  │  ├─ [ ] P2B-3: 04_RELEASE_OPS.md Quality Gate 更新
  │  ├─ [ ] P2B-4: 07_SECURITY_AND_AUTOMATION.md deny/ask 分離
  │  ├─ [ ] P2B-5: 08_SESSION_MANAGEMENT.md /full-save/load 廃止 反映
  │  └─ [ ] P2B-6: その他文書検討
  ├─ Phase 2C: CLAUDE.md (4セクション)
  │  ├─ [ ] P2C-1: Context Management 更新
  │  ├─ [ ] P2C-2: Memory Policy 三層化
  │  ├─ [ ] P2C-3: Hierarchy of Truth SSOT 00~09 維持
  │  └─ [ ] P2C-4: References 更新
  └─ Phase 2D: CHEATSHEET.md
     └─ [ ] P2D-1: 再編成 (セッション2種, ワークフロー昇格, スキル更新)

[ ] Phase 3: コマンド / スキル / エージェント
  ├─ Phase 3A: コマンド廃止
  │  └─ [ ] P3A-1: daily, focus, full-load, full-save, adr-create, impact-analysis, security-review 削除
  ├─ Phase 3B: quick-save/load 拡張
  │  ├─ [ ] P3B-1: docs/daily/, loop-log-schema.md, evaluation-kpi.md 新規作成
  │  ├─ [ ] P3B-2: quick-save.md 3 ステップ化
  │  ├─ [ ] P3B-3: quick-load.md 4 ステップ化
  │  └─ [ ] P3B-4: wave-plan.md /ship 案内追加
  ├─ Phase 3C: full-review 拡張
  │  ├─ [ ] P3C-1: 引数必須化 + building-checklist 参照
  │  ├─ [ ] P3C-2: pm_pending フラグ フロー 実装
  │  └─ [ ] P3C-3: レポート永続化 (docs/artifacts/audit-reports/)
  ├─ Phase 3D: retro/ship/auditing 更新
  │  ├─ [ ] P3D-1: retro.md Step 2.5 TDD パターン分析追加
  │  ├─ [ ] P3D-2: ship.md Phase 構成 7→5 簡素化
  │  ├─ [ ] P3D-3: auditing.md 出力先変更
  │  ├─ [ ] P3D-4: building/planning パス更新
  │  └─ [ ] P3D-5: pattern-review.md 閾値 3→2
  ├─ Phase 3E: ultimate-think 廃止
  │  ├─ [ ] P3E-1: anchor-format.md lam-orchestrate/references/ 移動（先に実行）
  │  └─ [ ] P3E-2: ultimate-think/ ディレクトリ削除（P3E-1 完了後）
  └─ Phase 3F: エージェント 更新
     ├─ [ ] P3F-1: 全 8 エージェント フロントマター化
     ├─ [ ] P3F-2: quality-auditor model:opus 明示
     └─ [ ] P3F-3: design-architect permission-level:PM 明示

[ ] Phase 4: ディレクトリ + Hooks
  ├─ Phase 4A: ディレクトリ準備
  │  ├─ [ ] P4A-1: docs/artifacts/ (knowledge/, audit-reports/, tdd-patterns/) 作成
  │  ├─ [ ] P4A-2: .gitignore lam-loop-state.json, test-results.xml 追加
  │  ├─ [ ] P4A-3: CLAUDE.md Memory Policy 三層化
  │  └─ [ ] P4A-4: PROJECT_STRUCTURE 確認
  ├─ Phase 4B: ADR 番号衝突解決
  │  ├─ [ ] P4B-1: ADR-0002 (Model Routing Strategy)
  │  ├─ [ ] P4B-2: ADR-0003 (Stop Hook Implementation)
  │  ├─ [ ] P4B-3: ADR-0004 (context7 vs WebFetch)
  │  └─ [ ] P4B-4: ADR-0005 (Bash read Commands)
  ├─ Phase 4C: specs/lam/
  │  ├─ [ ] P4C-1: tdd-introspection-v2.md
  │  └─ [ ] P4C-2: release-ops-revision.md
  └─ Phase 4D: Hooks
     ├─ [ ] P4D-1: _hook_utils.py リネーム + 新 API 追加
     ├─ [ ] P4D-2: pre-tool-use.py 更新
     ├─ [ ] P4D-3: post-tool-use.py JUnit XML パース
     ├─ [ ] P4D-4: lam-stop-hook.py 拡張
     └─ [ ] P4D-5: pre-compact.py import 更新
     （P4D-6〜P4D-8 は影式に存在しないため対象外）
```

**実行方法**:

```bash
# 各 Phase タスク完了を一覧確認
for phase in 1 2 3 4; do
  echo "Phase $phase チェックリスト:"
  grep "^\s*\[ \]" docs/memos/v4-4-1-update-plan/tasks/02-tasks-phase${phase}.md | wc -l
done

# ファイル差分を確認
git status --short | head -50  # 全変更ファイルを表示
```

**完了条件**:
- [ ] 全 Phase 1-4 チェックリスト項目が確認 OK
- [ ] git status で予期しないファイル削除がない
- [ ] 予期しない新規ファイルがない

---

## Phase 5B: スモークテスト実施

### P5-2: 基本機能のスモークテスト実行

**概要**: 影式が起動し、基本的なコマンドが動作することを確認。TDD 内省 v2, Hooks の整合性等を検証。

**テスト項目**:

#### テスト 1: アプリケーション起動

```bash
python -m kage_shiki &
sleep 2

# ウィンドウが起動して、基本操作可能か確認
# - 入力欄へのテキスト入力
# - 送信ボタンのクリック
# - 応答の表示

kill %1
```

**期待結果**: アプリケーションが正常に起動し、GUI が操作可能

---

#### テスト 2: ルール・ドキュメントの形式チェック

```bash
# JSON 形式チェック
python -c "import json; json.load(open('.claude/settings.json')); print('OK')"
python -c "import json; json.load(open('.claude/lam-loop-state.json'))" 2>/dev/null && echo "OK (if exists)"

# マークダウン形式チェック
ruff check docs/ 2>&1 | grep -i "syntax error" || echo "OK"

# Python ファイル形式チェック
python -m py_compile .claude/hooks/_hook_utils.py
python -m py_compile .claude/hooks/pre-tool-use.py
python -m py_compile .claude/hooks/post-tool-use.py
python -m py_compile .claude/hooks/lam-stop-hook.py
```

**期待結果**: JSON, マークダウン, Python のシンタックスエラーなし

---

#### テスト 3: TDD 内省 v2（JUnit XML）の動作確認

```bash
# pytest を実行し、JUnit XML が生成されるか確認
pytest tests/ --junitxml=.claude/test-results.xml -q

# XML ファイルが生成され、形式が有効か確認
python -c "import xml.etree.ElementTree as ET; ET.parse('.claude/test-results.xml'); print('XML OK')"

# post-tool-use hook が動作可能か（構文チェック）
python -m py_compile .claude/hooks/_hook_utils.py && echo "Hook syntax OK"
```

**期待結果**:
- `.claude/test-results.xml` が生成
- XML 形式が有効
- Hook の import エラーなし

---

#### テスト 4: ファイル参照の完全性チェック

```bash
# tdd-patterns パスが統一されているか確認
grep -r "docs/memos/tdd-patterns" .claude/rules/ docs/internal/ 2>/dev/null | wc -l
# → 0 であることを確認（全て docs/artifacts/tdd-patterns/ に変更済み）

# audit-reports パスが統一されているか確認
grep -r "docs/memos/audit-report" .claude/commands/ 2>/dev/null | wc -l
# → 0 であることを確認（全て docs/artifacts/audit-reports/ に変更済み）
```

**期待結果**:
- `docs/memos/tdd-patterns` への古い参照がない
- `docs/memos/audit-report` への古い参照がない

---

#### テスト 5: エージェント・スキルの形式チェック

```bash
# permission-level フロントマター確認
head -3 .claude/agents/*.md | grep "^# permission-level:"
# → 全エージェントで "# permission-level: XX" が表示

# ultimate-think が削除されているか確認
test ! -d .claude/skills/ultimate-think && echo "ultimate-think OK (deleted)"

# anchor-format.md が lam-orchestrate/references/ に配置されているか確認
test -f .claude/skills/lam-orchestrate/references/anchor-format.md && echo "anchor-format OK"
```

**期待結果**:
- 全 8 エージェントに permission-level フロントマター
- ultimate-think ディレクトリなし
- anchor-format.md が正しい位置にある

---

#### テスト 6: Hooks 整合性チェック

```bash
# _hook_utils.py が存在し、古い hook_utils.py がないか
test ! -f .claude/hooks/hook_utils.py && echo "Old hook_utils.py OK (deleted)"
test -f .claude/hooks/_hook_utils.py && echo "New _hook_utils.py OK"

# notify-sound.py は変更されていないか（単独スクリプト）
grep "import.*hook_utils" .claude/hooks/notify-sound.py || echo "notify-sound OK (no hook_utils import)"

# 全 hook ファイルが _hook_utils をインポートしているか
grep "from _hook_utils import" .claude/hooks/*.py | wc -l
# → 4 (pre-tool-use, post-tool-use, lam-stop-hook, pre-compact)
```

**期待結果**:
- 古い hook_utils.py が削除されている
- _hook_utils.py が存在
- 全 hook（notify-sound を除く）が _hook_utils を import

---

### P5-2 実行スクリプト（統合実行）

作成ファイル: `.claude/scripts/smoke-test-v4.4.1.sh`

```bash
#!/bin/bash
set -e

echo "=== Phase 5 Smoke Test for LAM v4.4.1 Migration ==="
echo ""

echo "[ Test 1 ] JSON Syntax"
python -c "import json; json.load(open('.claude/settings.json'))" && echo "✓ OK"

echo "[ Test 2 ] Markdown Syntax (basic)"
ruff check docs/internal/ 2>&1 | head -3 || echo "✓ OK (no critical errors)"

echo "[ Test 3 ] Python Syntax (Hooks)"
python -m py_compile .claude/hooks/_hook_utils.py
python -m py_compile .claude/hooks/pre-tool-use.py
python -m py_compile .claude/hooks/post-tool-use.py
echo "✓ OK"

echo "[ Test 4 ] pytest JUnit XML"
pytest tests/ --junitxml=.claude/test-results.xml -q
python -c "import xml.etree.ElementTree as ET; ET.parse('.claude/test-results.xml')" && echo "✓ OK"

echo "[ Test 5 ] File References (tdd-patterns)"
count=$(grep -r "docs/memos/tdd-patterns" .claude/rules/ docs/internal/ 2>/dev/null | wc -l || echo 0)
[ $count -eq 0 ] && echo "✓ OK (no old references)" || echo "✗ FAIL ($count old refs found)"

echo "[ Test 6 ] Agent Permission Levels"
count=$(grep "^# permission-level:" .claude/agents/*.md | wc -l)
[ $count -eq 8 ] && echo "✓ OK (all 8 agents)" || echo "✗ FAIL ($count agents)"

echo "[ Test 7 ] ultimate-think Deletion"
test ! -d .claude/skills/ultimate-think && echo "✓ OK (deleted)" || echo "✗ FAIL (still exists)"

echo "[ Test 8 ] Hooks Import"
count=$(grep "from _hook_utils import" .claude/hooks/*.py | wc -l)
[ $count -eq 4 ] && echo "✓ OK (all 4 hooks)" || echo "✗ FAIL ($count hooks)"

echo ""
echo "=== All Tests Completed ==="
```

**実行方法**:
```bash
bash .claude/scripts/smoke-test-v4.4.1.sh
```

**完了条件**:
- [ ] 全 8 つのテストが PASS
- [ ] pytest が実行可能
- [ ] 老いたファイル参照がない

---

## Phase 5C: 参照完全性チェック

### P5-3: 内部参照の一貫性確認

**概要**: ドキュメント参照、URL、パス参照が正確かを検証。broken link がないか確認。

**チェック項目**:

```
[ ] docs/internal/ の相互参照
  ├─ 00_PROJECT_STRUCTURE → 01, 02, 03, 04, 05, 06, 07
  ├─ 02_DEVELOPMENT_FLOW → building-checklist.md
  ├─ 04_RELEASE_OPS → 03_QUALITY_STANDARDS
  └─ 07_SECURITY_AND_AUTOMATION → settings.json

[ ] .claude/rules/ の参照
  ├─ phase-rules.md → docs/artifacts/tdd-patterns/
  ├─ permission-levels.md → docs/internal/ (00~09)
  └─ upstream-first.md → https://code.claude.com/docs/en/

[ ] CLAUDE.md の参照
  ├─ Hierarchy of Truth → docs/internal/ (00~09)
  ├─ Memory Policy → docs/artifacts/knowledge/
  └─ セーブ/ロード → quick-save, quick-load, /ship

[ ] .claude/commands/ の参照
  ├─ full-review.md → building-checklist.md
  ├─ quick-save.md → docs/daily/
  ├─ quick-load.md → docs/artifacts/
  ├─ retro.md → docs/artifacts/tdd-patterns/
  ├─ ship.md → docs/artifacts/audit-reports/
  └─ auditing.md → docs/artifacts/audit-reports/
```

**実行スクリプト**:

```bash
# URL チェック（https:// が有効か）
grep -r "https://code.claude.com/docs/en/" .claude/rules/ | wc -l
# → upstream-first.md 内で複数ヒット

# パス参照チェック
grep -r "docs/artifacts/" .claude/rules/ .claude/commands/ | wc -l
# → 期待値: 7+ (tdd-patterns, audit-reports, knowledge への参照)

# old パス参照の確認
grep -r "docs/memos/tdd-patterns" . 2>/dev/null | grep -v ".git" | wc -l
# → 0 であること
```

**完了条件**:
- [ ] 全ての内部参照が有効
- [ ] broken link なし
- [ ] 新 URL（code.claude.com）が統一されている

---

## Phase 5D: PM 承認ゲート（後続作業）

### P5-4: 後続タスク（別 PM 承認）の明示

**概要**: Phase 5 完了後、追加の PM 承認が必要な作業を明示。

**対象作業**:

#### A. trust-model.md の v2 仕様化（Phase 5 後、別承認）

**内容**: `.claude/rules/auto-generated/trust-model.md` を v2 仕様（JUnit XML, 2 回閾値）に完全更新。

**前提**:
- `docs/specs/lam/tdd-introspection-v2.md` が Phase 4C で取り込み済み
- `post-tool-use.py` が Phase 4D で JUnit XML パース対応済み

**実施時期**: Phase 5 スモークテスト全 PASS 後
**権限等級**: PM 級

---

#### B. 04_RELEASE_OPS.md の改訂（Phase 5 後、別承認）

**内容**: `docs/internal/04_RELEASE_OPS.md` を LAM v4.4.1 の release-ops-revision に基づいて改訂。

**前提**:
- `docs/specs/lam/release-ops-revision.md` が Phase 4C で取り込み済み
- Retrospective Done がデプロイ基準に追加

**実施時期**: Phase 5 スモークテスト全 PASS 後
**権限等級**: PM 級

---

#### C. .claude/agent-memory/ ディレクトリ の作成（code-reviewer エージェント導入時）

**内容**: Subagent Persistent Memory のためのディレクトリ構造を初期化。

**前提**:
- CLAUDE.md の Memory Policy が三層化済み（Phase 4A-3）
- code-reviewer.md エージェントを導入する際に同時実施

**実施時期**: code-reviewer エージェント導入時（将来）
**権限等級**: SE 級

---

#### D. 未整備の新機能（phase-rules.md TDD 内省 v2 以降）の段階的導入

**内容**:
- TDD パターン分析（/retro Step 2.5）の初回実行
- 新 hooks（pm_pending, secret scan 等）の動作確認
- 新コマンド（/ship の doc-sync-flag フロー等）の実際運用

**実施時期**: 実際の開発サイクル開始時
**権限等級**: 混在（PG + SE）

---

**PM 承認ゲート テンプレート**:

```markdown
## [date] — Phase 5 後続タスク承認リクエスト

Phase 1-4 の LAM v4.4.1 移行が完了しました。
以下の後続タスクについて PM 級承認をお願いします。

### 優先度高
- [ ] A. trust-model.md v2 仕様化（実装: SE 級）
- [ ] B. RELEASE_OPS.md 改訂（実装: SE 級）

### 優先度中・低
- [ ] C. agent-memory/ 作成（実装: SE 級、実施: code-reviewer 導入時）
- [ ] D. 新機能段階的導入（実装: 実動作テスト）

ご承認いただいた項目から順次進めます。
```

**完了条件**:
- [ ] 後続タスク A, B の PM 承認取得
- [ ] タスク C, D の実施時期が明確化

---

## Phase 5E: 完了報告とユーザーガイド

### P5-5: Migration Notice の作成と配置

**概要**: LAM v4.4.1 移行の完了を示すドキュメントを作成。ユーザーへの影響通知とガイドを記載。

**成果物**: `docs/MIGRATION-v4.4.1-COMPLETE.md`

**内容テンプレート**:

```markdown
# LAM v4.4.1 移行完了 — Migration Notice

**移行日**: [YYYY-MM-DD]
**影式バージョン**: v4.4.1 based (Phase 5 完了)
**ステータス**: ✓ Production Ready

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
- `/focus` → 非推奨（ポモドーロ管理は別ツル推奨）
- `/full-load` → `/quick-load` の 4 ステップ化で完全吸収
- `/full-save` → `/quick-save` + `/ship` の 2 コマンド化で分離
- `/adr-create` → `adr-template` スキル経由
- `/impact-analysis` → `/building` Phase 4 に組込
- `/security-review` → `/full-review` Phase 1 に統合

**対応**: 既存スクリプトやドキュメントで廃止コマンド参照がある場合は吸収先に変更してください。

---

### TDD 内省パイプライン v2 への移行

**変更点**:
- テスト結果検出が exitCode 方式 (動作せず) から JUnit XML 方式に変更
- 検出閾値が 3 回 → 2 回に引き下げ
- パターン分析が PostToolUse 自動 → `/retro` Step 2.5 で人間主導に変更

**影響**: TDD パターン記録が正常に機能開始。規則提案のタイミングが早まります。

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
- `hook_utils.py` → `_hook_utils.py` にリネーム + 新 API 追加
- pre-tool-use: out-of-root 検出、AUDITING PG 特別処理、PM パターン厳密化
- post-tool-use: JUnit XML パース、失敗テスト名記録
- lam-stop-hook: convergence_reason 記録、pm_pending フラグ、シークレットスキャン拡張

**影響**: 権限判定精度向上、セキュリティスキャン強化、ループの安定性向上。

---

### 後続作業スケジュール

以下の作業は Phase 5 後、別承認で進行予定:

1. **trust-model.md v2 仕様化**: TDD 内省 v2 データモデルの完全統一（予定: 1〜2 週間以内）
2. **RELEASE_OPS.md 改訂**: デプロイ基準への Retrospective Done 統合（予定: 同時期）
3. **agent-memory ディレクトリ初期化**: code-reviewer エージェント導入時（予定: 次 Phase）

---

## 推奨アクション

### 即座（移行直後）

- [ ] `/quick-save` で新 Daily 記録機能を試行（docs/daily/ 確認）
- [ ] `/quick-load` で復帰サマリー形式を確認
- [ ] `/ship` で git commit/push が正常動作するか確認

### 1 週間以内

- [ ] 廃止コマンド（/daily, /focus 等）の スクリプト参照をクリーンアップ
- [ ] `.claude/commands/release.md` で `/ship` への切替を確認
- [ ] TDD パターン分析（/retro Step 2.5）の初回実行試行

### 2 週間以内

- [ ] trust-model v2 の承認 & trust-model.md 更新（PM 承認取得後）
- [ ] RELEASE_OPS.md 改訂の承認 & 反映（PM 承認取得後）

---

## トラブルシューティング

### "/_hook_utils.py" import エラー

**症状**: `from _hook_utils import ...` でエラー
**原因**: 古い `hook_utils.py` がまだ存在している可能性
**対応**: `rm .claude/hooks/hook_utils.py` で削除

### JUnit XML ファイルが生成されない

**症状**: `post-tool-use.py` が `.claude/test-results.xml` を見つけられない
**原因**: `pyproject.toml` の `addopts` に `--junitxml` が未設定
**対応**: `pyproject.toml` の `[tool.pytest.ini_options]` に `addopts = "--junitxml=.claude/test-results.xml"` を追加

### docs/daily/ が空

**症状**: `/quick-save` の Step 3 が Daily 記録を保存していない
**原因**: `docs/specs/lam/evaluation-kpi.md` が未配置
**対応**: Phase 4C で `evaluation-kpi.md` が取り込まれている確認

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
/full-review <target>  # 対象ファイル/ディレクトリの詳細監査
```

### 振り返り時
```
/retro  # Wave/Phase 完了時の振り返りとパターン分析
```

---

## 参照資料

- `CLAUDE.md`: プロジェクト憲法（Context Management 更新済み）
- `CHEATSHEET.md`: クイックリファレンス（コマンド再編済み）
- `docs/internal/02_DEVELOPMENT_FLOW.md`: 開発フロー（TDD v2 対応済み）
- `docs/specs/lam/tdd-introspection-v2.md`: TDD 内省 v2 仕様
- `.claude/rules/phase-rules.md`: Phase 別ルール（TDD v2 記載）

---

**移行完了日**: [YYYY-MM-DD]
**検証者**: [name]
**承認者**: [PM name]
```

**完了条件**:
- [ ] MIGRATION-v4.4.1-COMPLETE.md が docs/ に配置
- [ ] ユーザーガイドの主要セクション（廃止コマンド、TDD v2、新ディレクトリ）が記載
- [ ] トラブルシューティングセクションがある

---

## 全 Phase 完了チェックリスト

```
=== LAM v4.4.1 移行 全体完了チェック ===

Phase 1: セキュリティ修正 + settings.json
  [ ] find 破壊的パターンを deny に追加
  [ ] find を allow から ask に移動
  [ ] python * を ask に追加

Phase 2: ルール + docs/internal/ + CLAUDE.md + CHEATSHEET.md
  [ ] .claude/rules/ 9ファイル更新完了
  [ ] docs/internal/ 11ファイル更新/確認完了
  [ ] CLAUDE.md 更新完了
  [ ] CHEATSHEET.md 再編成完了

Phase 3: コマンド / スキル / エージェント
  [ ] 7 コマンド廃止完了
  [ ] quick-save/load 拡張完了
  [ ] full-review 拡張完了
  [ ] retro/ship/auditing/building/planning 更新完了
  [ ] ultimate-think 廃止完了
  [ ] 全 8 エージェント更新完了

Phase 4: ディレクトリ + Hooks
  [ ] docs/artifacts/ 新規ディレクトリ作成完了
  [ ] .gitignore 更新完了
  [ ] ADR 0002〜0005 取り込み完了
  [ ] specs/lam/ スペック取り込み完了
  [ ] _hook_utils.py リネーム + API 追加完了
  [ ] 全 hook ファイル（4ファイル）import 更新完了
  [ ] notify-sound.py が変更されていないこと（影式固有保護）

Phase 5: 統合検証 + 完了
  [ ] 差分積分の最終チェック完了
  [ ] スモークテスト全項目 PASS
  [ ] 参照完全性チェック完了
  [ ] 後続タスク（A, B）の PM 承認取得
  [ ] MIGRATION-v4.4.1-COMPLETE.md 作成・配置

=== 全 Phase 完了！===
```

---

## Notes

- **Rollback 計画**: いずれかの Phase で重大な問題が発生した場合、git revert で該当 Phase をロールバック可能
- **段階的運用**: Phase 1-4 完了後も、Phase 5 の後続タスク（trust-model v2, RELEASE_OPS 改訂）は別途 PM 承認で進行
- **影式固有保護**: building-checklist.md (R-1〜R-11), docs/memos/middle-draft/, 影式固有 ADR-0001 等は全移行フェーズで保護
