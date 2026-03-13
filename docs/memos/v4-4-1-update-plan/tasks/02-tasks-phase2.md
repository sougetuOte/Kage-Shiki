# Phase 2 タスク: ルール + docs/internal/ + CLAUDE.md

**ステータス**: Draft
**対象設計**:
- `01-design-rules-docs.md` — 全判断（.claude/rules/, docs/internal/, CLAUDE.md, CHEATSHEET.md）
**優先度**: 高（プロセス定義の基盤更新）
**依存**: Phase 1 完了

---

## タスク一覧（概要）

| グループ | タスク数 | 権限等級 | 規模 |
|---------|---------|---------|------|
| .claude/rules/ (9ファイル) | 9 | PM 級 | M 〜 L |
| docs/internal/ (11ファイル) | 6 | PM 級 | M 〜 L |
| CLAUDE.md | 4 | PM 級 | S 〜 M |
| CHEATSHEET.md | 1 | PM 級 | M |
| **合計** | **20** | PM 級 | **L** |

---

## Phase 2A: .claude/rules/ の更新（9ファイル）

### P2A-1: test-result-output.md の新規追加

**概要**: LAM v4.4.1 で新設されたルールファイルをそのまま追加。テスト結果ファイル（JUnit XML）出力の規約を定義する。

**対応設計**: `01-design-rules-docs.md` 判断1-1「test-result-output.md の追加」→ 決定 A1「そのまま追加」

**成果物**: `.claude/rules/test-result-output.md`

**変更内容**:
- LAM v4.4.1 の `test-result-output.md` をそのまま配置
- Python (pytest) 固定環境のため言語別設定セクションはそのまま維持

**影式固有の注意**:
- Python (pytest) 設定が明確に記載されているため追加注釈は不要
- 実際の pyproject.toml 変更は別途 Phase 3 タスクとして分離

**完了条件**:
- [ ] `.claude/rules/test-result-output.md` ファイルが配置済み
- [ ] 内容が LAM v4.4.1 バージョンと同一
- [ ] Python (pytest) 設定セクションが存在

---

### P2A-2: security-commands.md の三分類化と Python カテゴリ保持

**概要**: LAM v4.4.1 の三分類（Allow/Deny/Ask）を採用しつつ、影式固有の Python カテゴリを allow に維持。

**対応設計**: `01-design-rules-docs.md` 判断1-2「security-commands.md の三分類化」→ 決定 B1「v4.4.1 ベース + Python カテゴリ保持」

**成果物**: `.claude/rules/security-commands.md`

**変更構造**:
```markdown
## Allow List（自動実行可）
  ← LAM v4.4.1 ベース（find を削除）
  + Python カテゴリ維持（python, python -m pytest, python -m ruff 等）

## 実行禁止コマンド（Layer 0: deny）
  rm, mv, chmod, chown, apt, brew, systemctl, reboot 等
  + find の破壊的パターン（-delete, -exec rm 等）

## 承認必須コマンド（Layer 0: ask）
  cp, mkdir, touch, git push, curl, wget 等
  + find（一般検索）
  + python *（影式固有）
```

**影式固有の注意**:
- `ruff check --fix`, `ruff format` は allow から ask へ移動
- `pytest -v`, `pytest --tb=short` は allow 維持
- `pip list`, `pip show` は allow 維持

**完了条件**:
- [ ] Allow List から find を削除
- [ ] deny と ask が分離された二つのセクションが存在
- [ ] Python カテゴリ（python, pytest, ruff, pip, pyenv）が allow に存在
- [ ] find の破壊的パターンが deny に記載済み

---

### P2A-3: permission-levels.md の PG/SE/PM 定義拡充と影式固有パス再追加

**概要**: LAM v4.4.1 の定義拡充（"テスト失敗の自明な修正"、"プログラム巻き戻し"等）を取り入れつつ、影式固有パス（docs/internal/, pyproject.toml 等）を再追加。

**対応設計**: `01-design-rules-docs.md` 判断1-3「permission-levels.md の拡充」→ 決定 C1「v4.4.1 ベース + 影式固有パス再追加 + SSOT 宣言維持」

**成果物**: `.claude/rules/permission-levels.md`

**変更内容**:
```markdown
# 権限等級分類基準（SSOT）

> **SSOT**: 本ファイルが PG/SE/PM 分類の唯一の定義源

## PG級
  ← LAM v4.4.1 追加："テスト失敗の自明な修正（型ミス等）"

## SE級
  ← LAM v4.4.1 追加："内部関数の名前変更", "ログ出力の追加・修正"

## PM級
  ← LAM v4.4.1 追加："フェーズの巻き戻し", ".claude/settings*.json の変更"

## ファイルパスベースの分類
  + 影式固有パス再追加：
    | docs/internal/*.md | PM | プロセス SSOT 変更（影式固有） |
    | pyproject.toml | PM | プロジェクト設定変更（影式固有） |
    | src/kage_shiki/ | SE | ソースコード変更（影式固有） |
    | config/ | SE | 設定ファイル変更（影式固有） |
```

**影式固有の注意**:
- SSOT 宣言を本文に明記（LAM v4.4.1 では削除されたが影式では維持）
- 参照セクションは v4.4.1 バージョンに更新

**完了条件**:
- [ ] LAM v4.4.1 PG/SE/PM 定義が取り入れ済み
- [ ] SSOT 宣言が存在
- [ ] 影式固有パスがファイルパステーブルに再追加済み
- [ ] "迷った場合" セクションに影式固有の例を含む

---

### P2A-4: phase-rules.md の TDD 内省 v2 更新と影式固有セクション保持

**概要**: TDD 内省パイプラインを v1（exitCode 方式）から v2（JUnit XML 方式）へアップグレード。同時に影式固有の Green State 5条件と AUDITING ルール識別子（A-1〜A-4）を保護。

**対応設計**: `01-design-rules-docs.md` 判断1-4「phase-rules.md の TDD 内省 v2 更新」→ 決定 D1「v4.4.1 ベース + 影式固有セクション保持」

**成果物**: `.claude/rules/phase-rules.md`

**変更内容**:
```markdown
## BUILDING

### TDD 内省パイプライン（v1 → v2）
  PostToolUse: テスト結果（JUnit XML）読み取り
  Trigger: FAIL→PASS 遷移
  Threshold: 3回 → 2回に引き下げ
  分析: PostToolUse 自動 → /retro Step 2.5 人間主導に変更
  保存先: .claude/tdd-patterns.log
  成果物: .claude/rules/auto-generated/draft-*.md
  審査: /pattern-review

## AUDITING

### 影式固有: Green State 5条件との対応
  G1: テスト全パス ← pytest
  G2: lint エラーゼロ ← ruff
  G3: 対応可能 Issue ゼロ
  G4: 仕様差分ゼロ
  G5: セキュリティチェック通過

### 影式固有: AUDITING ルール識別子
  A-1: 全重篤度への対応義務
  A-2: 対応不可 Issue の明示
  A-3: 修正後の再検証義務
  A-4: 仕様ズレの同時修正（Atomic Commit）
```

**影式固有の注意**:
- v1 の exitCode 方式が実際には動作していなかったことが確認済み（PostToolUse stdin に exitCode フィールドなし）
- v2 移行はバグ修正であり必須
- 閾値 3→2 変更は v4.4.1 の改善点を採択
- `docs/memos/tdd-patterns/` → `docs/artifacts/tdd-patterns/` パス変更

**完了条件**:
- [ ] TDD 内省セクションが JUnit XML 方式（v2）に更新済み
- [ ] 閾値が 2 に設定済み
- [ ] `/retro` Step 2.5 への言及が含まれる
- [ ] 影式固有セクション（Green State, A-1〜A-4）が保護済み
- [ ] パスが docs/artifacts/tdd-patterns/ に変更済み

---

### P2A-5: core-identity.md の docs/artifacts/ パス変更

**概要**: Context Compression セクションの書き出し先を `docs/memos/` → `docs/artifacts/` に変更。最小限の変更。

**対応設計**: `01-design-rules-docs.md` 判断1-5「core-identity.md のパス変更」→ 決定「パス変更適用」

**成果物**: `.claude/rules/core-identity.md`

**変更内容**:
```markdown
## Context Compression

1. 決定事項と未解決タスクを `docs/tasks/` または `docs/artifacts/` に書き出す
   ← "docs/memos/" から変更
```

**影式固有の注意**:
- Subagent 委任判断テーブルとコンテキスト節約原則は維持
- 変更は 1 行のみ

**完了条件**:
- [ ] docs/memos/ → docs/artifacts/ に変更済み
- [ ] 残りのセクションは変更なし

---

### P2A-6: upstream-first.md の全面更新

**概要**: Claude Code 公式ドキュメントのドメインが変更（`docs.anthropic.com/en/docs/claude-code/` → `code.claude.com/docs/en/`）。構造的に全面再編成。

**対応設計**: `01-design-rules-docs.md` 判断1-6「upstream-first.md の全面更新」→ 決定 E1「v4.4.1 ベースで全面更新」

**成果物**: `.claude/rules/upstream-first.md`

**変更内容**:
- URL ドメイン: `code.claude.com/docs/en/` に変更
- セクション構造: 概要/背景/ルール/権限等級/一括すり合わせに再編
- 権限等級セクション追加: "本規則ファイル自体の変更は PM 級"
- MCP行削除 (v4.4.1)

**影式固有の注意**:
- 影式固有の追加事項なし
- upstream-first.md は v4.0.1 時点で既に "そのまま適用" 判定を受けている

**URL テーブル**:
| 機能 | URL |
|---|---|
| Hooks | `https://code.claude.com/docs/en/hooks` |
| Settings | `https://code.claude.com/docs/en/settings` |
| Permissions | `https://code.claude.com/docs/en/permissions` |
| Skills | `https://code.claude.com/docs/en/skills` |
| Sub-agents | `https://code.claude.com/docs/en/sub-agents` |

**完了条件**:
- [ ] URL が code.claude.com ドメインに変更済み
- [ ] セクション構造が再編成済み
- [ ] 権限等級セクションが追加済み

---

### P2A-7: auto-generated/README.md の v2 全面更新

**概要**: TDD 内省パイプライン v2 対応。ライフサイクルダイアグラム更新、閾値 3→2 変更。

**対応設計**: `01-design-rules-docs.md` 判断1-7「auto-generated の全面更新」

**成果物**: `.claude/rules/auto-generated/README.md`

**変更内容**:
```markdown
# auto-generated/ — TDD 内省ルール v2

ライフサイクル:
1. PostToolUse hook がテスト結果（JUnit XML）を読み取り
2. FAIL→PASS 遷移検出及び .claude/tdd-patterns.log に記録（PG級）
3. 同一パターン 2 回以上 → draft-NNN.md 生成（PM級）
4. /retro Step 2.5 で人間が分析
5. 承認後 rule-NNN.md に昇格（PM級）

新: 閾値 3回 → 2回に引き下げ
新: 参照セクション拡充 (docs/specs/tdd-introspection-v2.md 等)
```

**完了条件**:
- [ ] ライフサイクルが v2 に更新済み
- [ ] 閾値が 2 に設定済み
- [ ] JUnit XML への参照が含まれる

---

### P2A-8: auto-generated/trust-model.md の v2 全面更新

**概要**: TDD 内省データモデルを v1（exitCode）から v2（JUnit XML）に転換。観測段階テーブルの再設計。

**対応設計**: `01-design-rules-docs.md` 判断1-7「trust-model.md の v2 全面更新」

**成果物**: `.claude/rules/auto-generated/trust-model.md`

**変更内容**:
```markdown
# 信頼度モデル — TDD 内省パイプライン v2

データソース: .claude/test-results.xml (JUnit XML)
観測条件:
- FAIL→PASS 遷移が発生した場合のみ記録
- 同一パターン 2 回以上観測 → /retro で提案

新: rejected 状態追加（却下されたルール候補）
新: /retro Step 2.5 実行プロセスの詳細記述
```

**完了条件**:
- [ ] データソースが test-results.xml に変更済み
- [ ] 観測段階テーブルが v2 形式で再作成済み
- [ ] /retro Step 2.5 プロセスが記述済み

---

### P2A-9: building-checklist.md の保護確認

**概要**: 影式固有ファイルである building-checklist.md は変更不要。保護確認のみ実施。

**対応設計**: `01-design-rules-docs.md` 判断1-8「building-checklist.md の保護」

**検査項目**:
- [ ] building-checklist.md が v4.0.1 以降変更されていない
- [ ] R-1 〜 R-11 ルールが完全に存在
- [ ] ファイルが所定の位置（.claude/rules/）にある

---

## Phase 2B: docs/internal/ の更新（8ファイル）

### P2B-1: 00_PROJECT_STRUCTURE.md の artifacts/ 導入

**概要**: docs/artifacts/, .claude/agent-memory/ ディレクトリ追加。SSOT 層名称変更（"上位/下位" → "情報層 1/2/3"）。

**対応設計**: `01-design-rules-docs.md` 判断2-1「PROJECT_STRUCTURE の更新」→ 決定 F1「v4.4.1 ベースで更新」

**成果物**: `docs/internal/00_PROJECT_STRUCTURE.md`

**変更内容**:
```markdown
## docs/ 配下
  - artifacts/（新規）
    - knowledge/（知見蓄積）
    - audit-reports/（監査レポート）
    - tdd-patterns/（TDD パターン詳細）

## .claude/ 配下
  - agent-memory/（新規）
    - code-reviewer/
    - quality-auditor/
    等...

## SSOT 層名称
  Information Layer 1（Specifications: specs/）
  Information Layer 2（Process: internal/）
  Information Layer 3（Decision: adr/）
```

**影式固有の保持事項**:
- src/kage_shiki/ パッケージ構造
- docs/memos/middle-draft/ 記載

**完了条件**:
- [ ] docs/artifacts/ 及びサブディレクトリが記載済み
- [ ] .claude/agent-memory/ が記載済み
- [ ] SSOT 層名称が "情報層 1/2/3" に変更済み

---

### P2B-2: 02_DEVELOPMENT_FLOW.md の TDD 内省 v2 更新

**概要**: TDD 内省 v1 → v2 転換。Wave-Based Development セクションは影式固有として保護。

**対応設計**: `01-design-rules-docs.md` 判断2-2「DEVELOPMENT_FLOW の更新」→ 決定「変更事項のみ適用 + 影式固有セクション保持」

**成果物**: `docs/internal/02_DEVELOPMENT_FLOW.md`

**変更内容**:
- Phase 1 Step 6: task.md → docs/tasks/{feature_name}/overview.md
- Phase 2 Step 5: docs/memos/walkthrough → docs/artifacts/walkthrough（推奨に緩和）
- TDD 内省: v1 → v2（JUnit XML, 2回閾値）
- パス変更: docs/memos/ → docs/artifacts/

**影式固有の保護**:
- Wave-Based Development セクション維持（"影式固有:" プレフィックス追加）
- Quality Rules Integration (R-1〜R-6) 維持
- Advanced Workflows 維持

**完了条件**:
- [ ] TDD 内省が v2 に更新済み
- [ ] Wave-Based Development セクションが保護済み
- [ ] パスが docs/artifacts/ に変更済み

---

### P2B-3: 04_RELEASE_OPS.md の Quality Gate 更新

**概要**: デプロイ基準に "/retro 実施済み" を追加。Post-Mortem 保存先変更（docs/adr/ → docs/artifacts/）。

**対応設計**: `01-design-rules-docs.md` 判断2-4「RELEASE_OPS の更新」

**成果物**: `docs/internal/04_RELEASE_OPS.md`

**変更内容**:
```markdown
## Section 1: デプロイ基準
  Quality Gate Passed (all tests pass, no lint errors)
  + 新規: /retro 実施済み (Retrospective Done)

## Section 3: Post-Mortem
  保存先: docs/adr/（アーキテクチャ判断）または docs/artifacts/（一般的な失敗分析）
```

**完了条件**:
- [ ] "/retro 実施済み" が追加済み
- [ ] Post-Mortem 保存先が明確に分離済み

---

### P2B-4: 07_SECURITY_AND_AUTOMATION.md の deny/ask 分離

**概要**: LAM v4.4.1 の deny/ask 分離構造を適用。影式固有コマンド（ruff, pytest, pip 等）は適切な分類に再配置。

**対応設計**: `01-design-rules-docs.md` 判断2-6「SECURITY_AND_AUTOMATION の安全性更新」→ 決定 G1「v4.4.1 ベース + 影式固有コマンド保持」

**成果物**: `docs/internal/07_SECURITY_AND_AUTOMATION.md`

**変更内容**:
```markdown
## Section 2: Allow List
  ruff check, ruff format --check
  pytest -v, pytest --tb=short
  pip list, pip show
  等（find は削除、ask に移動）

## Section 2: Deny List
  rm, mv, chmod/chown, apt, brew, systemctl, reboot
  + find の破壊的パターン（-delete, -exec rm）

## Section 2: Ask List
  cp, mkdir, touch, git push, curl, wget
  + find（一般検索）
  + python main.py, npm start, make
```

**完了条件**:
- [ ] deny と ask が分離された二つのセクションが存在
- [ ] 影式固有コマンドが適切な分類に配置済み
- [ ] find の破壊的パターンが deny に明示済み

---

### P2B-5: 08_SESSION_MANAGEMENT.md の /full-save, /full-load 廃止反映

**概要**: 廃止された /full-save, /full-load を削除し、/quick-save, /quick-load, /ship の説明を追加。

**対応設計**: `01-design-rules-docs.md` 判断2-7「SESSION_MANAGEMENT の更新」

**成果物**: `docs/internal/08_SESSION_MANAGEMENT.md`

**変更内容**:
- /full-save の説明を削除または廃止ノートに変更
- /full-load の説明を削除または廃止ノートに変更
- /quick-save の説明を拡張（SESSION_STATE + Daily 記録 + ループログ）
- /quick-load の説明を拡張（SESSION_STATE + 復帰サマリー）
- /ship の使用に言及（git commit/push）

**完了条件**:
- [ ] /full-save, /full-load が廃止済み
- [ ] /quick-save, /quick-load の説明が拡張済み
- [ ] /ship への言及が追加されている

---

### P2B-6: 03_QUALITY_STANDARDS.md, 05_MCP, 06_DECISION, 99_reference の検討

**概要**: 残りの文書は最小限の変更のみ実施。

**内容**:
| ファイル | 変更 |
|------|------|
| 03_QUALITY_STANDARDS.md | 変更なし（影式固有 Section 6/7 保護） |
| 05_MCP_INTEGRATION.md | find 参照に注釈追加、docs/artifacts/ パス変更 |
| 06_DECISION_MAKING.md | 変更なし |
| 09_SUBAGENT_STRATEGY.md | 変更なし |
| 99_reference_generic.md | フレーズモードタグのインライン化 |

---

## Phase 2C: CLAUDE.md の更新（1 ファイル、4 セクション）

### P2C-1: Context Management の /full-save, /full-load 廃止

**概要**: CLAUDE.md のセーブ/ロード使用法を /quick-save, /quick-load, /ship で再編成。

**対応設計**: `01-design-rules-docs.md` 判断3-1「CLAUDE.md Context Management の更新」→ 決定 H1「v4.4.1 ベースで更新」

**成果物**: `CLAUDE.md` — Context Management セクション

**変更内容**:
```markdown
## セーブ/ロードの使い分け

- `/quick-save`: SESSION_STATE.md + Daily 記録 + ループログ（普段使い）
- `/quick-load`: SESSION_STATE.md 読込 + 復帰サマリー（日常の再開）
- git commit / push は `/ship` を使用

残量 25% 以下では `/quick-save` を使うこと。
```

**完了条件**:
- [ ] /full-save, /full-load への言及を削除
- [ ] /quick-save, /quick-load の説明が完成
- [ ] /ship への参照を追加

---

### P2C-2: Memory Policy の三層構造拡張

**概要**: Auto Memory / Subagent Persistent Memory / Knowledge Layer で構成された三層メモリモデルの定義。

**対応設計**: `01-design-rules-docs.md` 判断3-2「Memory Policy の三層化」→ 決定「v4.4.1 ベース採用」

**成果物**: `CLAUDE.md` — MEMORY.md Policy セクション

**変更内容**:
```markdown
## MEMORY.md Policy

### Layer 1: Auto Memory
  Claude 本体の自動記憶機能。ビルドコマンド、デバッグ知識、Subagent 役割ノウハウ等。

### Layer 2: Subagent Persistent Memory
  `.claude/agent-memory/<agent-name>/` に保存。Subagent が実行中に習得したプロジェクト固有パターン。

### Layer 3: Knowledge Layer
  `/retro` Step 4 で人間が整理した知識。`docs/artifacts/knowledge/` に保存。
```

**完了条件**:
- [ ] 三層構造が説明済み
- [ ] 各レイヤーの保存先を明示

---

### P2C-3: Hierarchy of Truth の SSOT 範囲維持

**概要**: 影式固有の 08_SESSION_MANAGEMENT.md, 09_SUBAGENT_STRATEGY.md を SSOT に含める（v4.4.1 は 00-07 のみ該当）。

**対応設計**: `01-design-rules-docs.md` 判断3-3「Hierarchy of Truth の SSOT 範囲」→ 決定 I1「SSOT: 00〜09 維持」

**成果物**: `CLAUDE.md` — Hierarchy of Truth セクション

**変更内容**:
```markdown
Architecture & Protocols: `docs/internal/`（SSOT: 00〜09）
  00: PROJECT_STRUCTURE
  01: REQUIREMENT_MANAGEMENT
  02: DEVELOPMENT_FLOW
  ...
  08: SESSION_MANAGEMENT（影式固有）
  09: SUBAGENT_STRATEGY（影式固有）
```

**完了条件**:
- [ ] 00〜09 範囲を明示
- [ ] 08, 09 の影式固有ファイルに言及

---

### P2C-4: References セクションの更新

**概要**: docs/memos/middle-draft/ 行を維持し、その他の参照を最新化。

**完了条件**:
- [ ] docs/memos/middle-draft/ の記載を維持
- [ ] 参照一覧が最新化済み

---

## Phase 2D: CHEATSHEET.md の更新（1 ファイル）

### P2D-1: CHEATSHEET.md の大規模再編成

**概要**: セッション管理コマンドの 2 種化、ワークフローコマンドの昇格、廃止コマンドの削除、スキル更新。

**対応設計**: `01-design-rules-docs.md` 判断4「CHEATSHEET.md の再編成」

**成果物**: `CHEATSHEET.md`

**主要変更**:

| セクション | 変更 |
|------|------|
| セッション管理 | 4種 → 2種（/quick-save, /quick-load） |
| ワークフロー | /wave-plan, /retro 昇格 |
| 削除 | /focus, /daily, /adr-create, /security-review, /impact-analysis |
| スキル | ultimate-think 削除、lam-orchestrate 説明拡張、ui-design-guide 追加 |
| 状態管理 | docs/artifacts/knowledge/, .claude/agent-memory/ 追加 |

**影式固有の保護**:
- 技術スタックセクション維持
- building-checklist.md ルール一覧維持
- 日常ワークフロー 7 パターン維持

**完了条件**:
- [ ] /quick-save, /quick-load のみセッション管理に残る
- [ ] 廃止コマンド 5 個が削除済み
- [ ] ui-design-guide が追加済み
- [ ] 影式固有セクションが保護済み

---

## 作業順序及び並列化の可能性

```
Phase 2A: .claude/rules/（9 ファイル）
  ├─ P2A-1 (test-result-output.md 新規): 1時間
  ├─ P2A-2 (security-commands.md): 1時間
  ├─ P2A-3 (permission-levels.md): 1時間
  ├─ P2A-4 (phase-rules.md): 1.5時間
  ├─ P2A-5 (core-identity.md): 30分
  ├─ P2A-6 (upstream-first.md): 1時間
  ├─ P2A-7 (auto-generated/README.md): 1時間
  ├─ P2A-8 (auto-generated/trust-model.md): 1時間
  └─ P2A-9 (building-checklist.md 保護確認): 15分

Phase 2B: docs/internal/（6 タスク）
  ├─ P2B-1 (00_PROJECT_STRUCTURE): 1時間
  ├─ P2B-2 (02_DEVELOPMENT_FLOW): 1時間
  ├─ P2B-3 (04_RELEASE_OPS): 30分
  ├─ P2B-4 (07_SECURITY_AND_AUTOMATION): 1時間
  ├─ P2B-5 (08_SESSION_MANAGEMENT): 30分
  └─ P2B-6 (残り文書の検討): 30分

Phase 2C: CLAUDE.md（4 セクション）
  ├─ P2C-1 (Context Management): 30分
  ├─ P2C-2 (Memory Policy): 30分
  ├─ P2C-3 (Hierarchy of Truth): 15分
  └─ P2C-4 (References): 15分

Phase 2D: CHEATSHEET.md（1 ファイル）
  └─ P2D-1 (CHEATSHEET 再編): 1時間

総作業量: 約14-15時間
権限等級: PM 級（仕様変更）
```

---

## Notes

- **並列化**: Phase 2A と 2B は独立して並列実行可能
- **順次性**: Phase 2C と 2D は Phase 2A, 2B 完了後に実行
- **レビュー**: PM 級変更のため各段階ごとに承認ゲートが必要
- **building-checklist.md の保護**: 影式固有ファイルとして変更なし（検討のみ）
