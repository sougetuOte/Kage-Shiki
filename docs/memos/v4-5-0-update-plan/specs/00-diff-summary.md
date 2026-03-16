# LAM v4.4.1 → v4.5.0 差分サマリー

**作成日**: 2026-03-16
**対象**: 影式 (Kage-Shiki) v4.4.1 適用済み環境への LAM v4.5.0 差分適用
**前回移行参考**: `docs/memos/v4-4-1-update-plan/`

---

## 1. バージョン間の主要変更

LAM v4.5.0 は Scalable Code Review (Phase 3-5) と MAGI System 導入を中心とした大規模更新。

### 1.1 新規コンセプト

| コンセプト | 概要 | 影響範囲 |
|-----------|------|---------|
| **MAGI System** | Three Agents Model の進化版。MELCHIOR/BALTHASAR/CASPAR に改名 + Reflection ステップ追加 | 全 rules, commands, agents, docs/internal, skills |
| **Scalable Code Review** | analyzers/ パイプライン。静的解析・AST チャンキング・依存グラフ・契約カード | hooks/, full-review.md, specs |
| **Stage 体系** | full-review の 11 Phase → 6 Stage への再編 | full-review.md |
| **Plan A-D** | プロジェクト規模に応じた自動スケール検出 | analyzers/scale_detector.py, full-review.md |
| **/clarify スキル** | 文書精緻化インタビュー（曖昧さ・矛盾・欠落の検出） | skills/, docs/internal |
| **品質ガイドライン** | code-quality-guideline.md, planning-quality-guideline.md | rules/ |

### 1.2 名称変更（全ファイル横断）

| 旧 (v4.4.1) | 新 (v4.5.0) | 備考 |
|-------------|------------|------|
| Three Agents Model | MAGI System | 後方互換: 旧名を括弧書きで併記 |
| Affirmative | MELCHIOR（科学者） | 推進者ロール |
| Critical | BALTHASAR（母） | 批判者ロール |
| Mediator | CASPAR（女） | 調停者ロール |

---

## 2. ファイル別差分一覧

### 2.1 新規追加ファイル

#### ルール（`.claude/rules/`）

| ファイル | 概要 | 影式での対応 |
|---------|------|------------|
| `code-quality-guideline.md` | Critical/Warning/Info 三層品質基準 + Green State 再定義 | **導入** — レビュー精度向上に直結 |
| `planning-quality-guideline.md` | Requirements Smells, RFC 2119, SPIDR, WBS 100%, Example Mapping | **導入** — 計画品質向上に直結 |

#### スキル（`.claude/skills/`）

| ファイル | 概要 | 影式での対応 |
|---------|------|------------|
| `magi/SKILL.md` | AoT + MAGI System + Reflection | **導入** — 旧 Three Agents を置換 |
| `magi/references/anchor-format.md` | 構造化思考アンカーファイルテンプレート | **導入** |
| `clarify/SKILL.md` | 文書精緻化インタビュー | **導入** |
| `lam-orchestrate/references/magi-skill.md` | lam-orchestrate 内 MAGI 参照 | **導入** |

#### Hooks（`.claude/hooks/analyzers/`）

| ファイル | 概要 | 影式での対応 |
|---------|------|------------|
| `__init__.py` | パッケージ初期化 | **導入**（将来対応含む） |
| `base.py` | Issue/ASTNode/LanguageAnalyzer 基底クラス | **導入** |
| `config.py` | ReviewConfig（除外設定・チャンクサイズ等） | **導入** |
| `orchestrator.py` | バッチオーケストレーション・プロンプト生成 | **導入** |
| `scale_detector.py` | Plan A-D スケール検出 | **導入** |
| `run_pipeline.py` | Phase 0 静的解析パイプライン | **導入** |
| `card_generator.py` | ファイル/モジュール/契約カード生成 | **導入** |
| `chunker.py` | AST ベースコードチャンキング | **導入** |
| `reducer.py` | Issue 重複排除・命名チェック | **導入** |
| `state_manager.py` | レビュー状態永続化 | **導入** |
| `python_analyzer.py` | Python 静的解析（ruff + bandit） | **導入** |
| `javascript_analyzer.py` | JS/TS 静的解析 | **導入**（影式は Python のみだが汎用性のため） |
| `rust_analyzer.py` | Rust 静的解析 | **導入**（同上） |
| `analyzers/tests/` (12ファイル + fixtures) | analyzers テストスイート | **導入** |

#### Hooks テスト（`.claude/hooks/tests/`）

| ファイル | 概要 | 影式での対応 |
|---------|------|------------|
| `conftest.py` | hooks テスト共通 fixture | **更新**（差分確認要） |

#### 仕様書（`docs/specs/`）

| ファイル | 概要 | 影式での対応 |
|---------|------|------------|
| `magi-skill-spec.md` | MAGI スキル仕様書 | **取込** |
| `scalable-code-review-spec.md` | SCR 基本仕様 | **取込** |
| `scalable-code-review-phase5-spec.md` | SCR Phase 5（Stage 再編）仕様 | **取込** |
| `scalable-code-review.md` | SCR 概要 | **取込** |

#### 設計書（`docs/design/`）

| ファイル | 概要 | 影式での対応 |
|---------|------|------------|
| `scalable-code-review-design.md` | SCR 設計書 | **取込** |

### 2.2 更新ファイル

#### ルール（`.claude/rules/`）

| ファイル | 変更内容 | 影響度 |
|---------|---------|-------|
| `decision-making.md` | Three Agents → MAGI 命名、Reflection ステップ追加 | **高** |
| `phase-rules.md` | PLANNING に品質基準参照追加、BUILDING に R-5/R-6 追加、AUDITING Green State 再定義（Info 非阻害） | **高** |
| `core-identity.md` | Subagent 委任判断セクション削除（CLAUDE.md に統合済み） | **中** |
| `permission-levels.md` | `.claude/rules/*/*.md` サブディレクトリパターン追加、影式固有パス削除（汎用化） | **中** |
| `security-commands.md` | Python コマンド注釈削除（影式固有）、整理 | **低** |
| `upstream-first.md` | context7 優先を明文化、/full-review 内 WebFetch 禁止注記 | **低** |
| `test-result-output.md` | Go/Rust の設定詳細化 | **低** |
| `auto-generated/README.md` | 参照パス微修正 | **低** |
| `auto-generated/trust-model.md` | v2 版補足追加、参照パス微修正 | **低** |

#### コマンド（`.claude/commands/`）

| ファイル | 変更内容 | 影響度 |
|---------|---------|-------|
| `full-review.md` | **全面再編**: 6 Stage 体系 + Plan A-D + Scale Detection + 契約カード + True Green State | **最大** |
| `planning.md` | `/magi` 参照追加、品質基準参照 | **中** |
| `building.md` | Pre-flight 分析義務化、R-5/R-6 参照 | **中** |
| `auditing.md` | `/full-review` との使い分け明確化、Broken Windows 概念 | **中** |
| `wave-plan.md` | SPIDR タスク分割、`/magi` 参照 | **中** |
| `retro.md` | Step 2.5 TDD パターン分析の詳細化 | **低** |
| `ship.md` | doc-sync-flag 連携の精緻化 | **低** |
| `pattern-review.md` | MVP ステータス明確化、90日寿命管理 | **低** |
| `project-status.md` | KPI ダッシュボード参照 | **低** |
| `quick-load.md` | コンテキスト節約の明示化 | **低** |
| `quick-save.md` | KPI 集計テンプレート | **低** |

#### エージェント（`.claude/agents/`）

| ファイル | 変更内容 | 影響度 |
|---------|---------|-------|
| `quality-auditor.md` | MAGI 命名、構造整合性チェック Step 3b 追加 | **高** |
| `requirement-analyst.md` | **PM級に昇格**、AoT Step 1.5 追加 | **高** |
| `task-decomposer.md` | **Haiku に変更**、AoT Step 3.5 + SPIDR | **高** |
| `tdd-developer.md` | Pre-flight チェックリスト + code-quality-guideline 参照 | **中** |
| `code-reviewer.md` | "Clarity over Brevity" 原則追加 | **中** |
| `design-architect.md` | AoT Step 1.5 追加 | **低** |
| `doc-writer.md` | Doc Sync モード詳細化 | **低** |
| `test-runner.md` | **PG級に降格**、Haiku 維持 | **低** |

#### スキル（`.claude/skills/`）

| ファイル | 変更内容 | 影響度 |
|---------|---------|-------|
| `lam-orchestrate/SKILL.md` | /magi 参照に置換、Plan Change Protocol | **高** |
| `lam-orchestrate/references/anchor-format.md` | MAGI 命名 | **中** |
| `adr-template/SKILL.md` | MAGI 命名 | **低** |
| `spec-template/SKILL.md` | RFC 2119 + 権限等級セクション | **低** |
| `skill-creator/SKILL.md` | 微修正 | **低** |
| `ui-design-guide/SKILL.md` | 変更なし | **なし** |

#### docs/internal/

| ファイル | 変更内容 | 影響度 |
|---------|---------|-------|
| `06_DECISION_MAKING.md` | **大規模**: AoT Section 5 (5.1-5.5) + Reflection Section 6 新設 | **最大** |
| `01_REQUIREMENT_MANAGEMENT.md` | MAGI + /clarify 統合セクション追加 | **高** |
| `02_DEVELOPMENT_FLOW.md` | MAGI + /clarify + R-5/R-6 参照 | **高** |
| `07_SECURITY_AND_AUTOMATION.md` | Permission Layer 0/1/2 整理 | **中** |
| `00_PROJECT_STRUCTURE.md` | current-phase.md 明示、ディレクトリ詳細化 | **中** |
| `03_QUALITY_STANDARDS.md` | Python 固有セクション汎用化（影式は保持） | **低** |
| `05_MCP_INTEGRATION.md` | MCP ガイド拡充 | **低** |
| `04_RELEASE_OPS.md` | 微修正 | **低** |
| `99_reference_generic.md` | 微修正 | **低** |

#### ルートファイル

| ファイル | 変更内容 | 影響度 |
|---------|---------|-------|
| `CLAUDE.md` | Context 閾値 20%→10%、Memory Policy 微修正、設計文書パス削除（汎用化） | **中** |
| `CHEATSHEET.md` | MAGI 命名、/magi + /clarify 追加、StatusLine 参照 | **中** |
| `README.md` | MAGI 命名 | **低** |
| `.gitignore` | `review-state/`, `doc-sync-flag`, `pre-compact-fired`, `last-test-result` 追加 | **低** |
| `settings.json` | 差分確認要 | **低** |

### 2.3 スキップ対象

| ファイル/機能 | 理由 |
|-------------|------|
| `docs/slides/` (12 HTML) | 影式には既存なし。CLAUDE.md で将来作成予定と記載済み |
| `QUICKSTART.md`, `QUICKSTART_en.md` | 個人プロジェクトのため不要（v4.4.1 と同判断） |
| `README_en.md`, `CLAUDE_en.md`, `CHEATSHEET_en.md` | 英語版は影式では不要 |
| `agent-memory/code-reviewer/*` | LAM 開発時の固有学習。影式独自の蓄積で上書きされる |
| `/release` コマンド | LAM v4.5.0 の commands/ に存在しない。CHEATSHEET.md 上の記述は将来予定 |

---

## 3. 影式固有の判断ポイント

### 3.1 analyzers/ 導入の是非

| 観点 | 分析 |
|------|------|
| 影式の規模 | ~5K LOC → Plan A-D の閾値（10K LOC）未満 |
| 言語 | Python 単一 → python_analyzer.py のみ実質的に使用 |
| メリット | full-review の Stage 体系は規模に関わらず有用。将来の拡大にも対応 |
| **結論** | **導入する**。規模未満でも Stage 体系とパイプライン基盤は品質向上に寄与。Plan 未発動でも Stage 0-5 のフロー自体が改善 |

### 3.2 task-decomposer の Haiku 化

| 観点 | 分析 |
|------|------|
| LAM の意図 | 定型的 SPIDR 分割はコスト最適化で Haiku に |
| 影式の現状 | Opus/Sonnet 推奨環境 |
| **結論** | **LAM に従い Haiku に変更**。タスク分解は定型的で Haiku で十分 |

### 3.3 requirement-analyst の PM 級昇格

| 観点 | 分析 |
|------|------|
| LAM の意図 | 要件承認ゲートの権限を明示 |
| 影式の運用 | 現行 SE 級で問題なし |
| **結論** | **LAM に従い PM 級に変更**。要件定義は仕様変更に直結するため妥当 |

### 3.4 CLAUDE.md Context 閾値

| 観点 | 分析 |
|------|------|
| LAM 4.5.0 | 10% で警告 |
| 影式 (v4.4.1) | 20% で警告 |
| **結論** | **影式は 20% を維持**。LAM はテンプレートとしてギリギリまで使う想定だが、影式は安全側に倒す運用を継続 |

### 3.5 03_QUALITY_STANDARDS.md の Python 固有セクション

| 観点 | 分析 |
|------|------|
| LAM 4.5.0 | 汎用化のため Python 固有 Section 6/7 を削除 |
| 影式 | Python プロジェクトとして Section 6/7 は有用 |
| **結論** | **影式は Section 6/7 を保持**。v4.4.1 と同じ判断 |

### 3.6 R-5/R-6 識別子衝突（2026-03-16 承認済み）

影式の building-checklist.md の R-5（異常系テスト）/ R-6（else デフォルト値禁止）と
LAM v4.5.0 の phase-rules.md の R-5（テスト名一致）/ R-6（設計書アサーション）が衝突。

| 観点 | 分析 |
|------|------|
| **結論** | **影式側を R-12/R-13 にリナンバ**。LAM との識別子一貫性を確保。影響範囲は building-checklist.md 内で閉じる |

### 3.7 quality-auditor モデル（2026-03-16 承認済み）

| 観点 | 分析 |
|------|------|
| 影式 v4.4.1 | Opus（v4.0.1 移行時に意図的に維持） |
| LAM v4.5.0 | Sonnet（code-quality-guideline.md で品質基準を明文化したため） |
| **結論** | **Sonnet に変更**。品質基準の定量化により Opus の優位性が減少。コスト最適化を優先 |

### 3.8 lam-stop-hook 設計差異（2026-03-16 承認済み）

| 観点 | 分析 |
|------|------|
| 影式 v4.4.1 | stop-hook 内で Green State 判定（G1/G2/G5）を実行（~670行） |
| LAM v4.5.0 | stop-hook は安全ネットのみ（~150行）。Green State 判定は full-review Stage 5 |
| **結論** | **LAM 設計に移行**。full-review Stage 5 との二重判定を解消。保守コスト大幅削減 |

### 3.9 SSOT 3層の方向性（2026-03-16 承認済み）

| 観点 | 分析 |
|------|------|
| 影式 v4.4.1 | 情報層 1: CLAUDE.md → 情報層 2: docs/internal/ → 情報層 3: CHEATSHEET.md |
| LAM v4.5.0 | 情報層 1: docs/internal/ → 情報層 2: .claude/rules/ → CLAUDE.md はブートストラップ |
| **結論** | **LAM に追従**。CLAUDE.md は既に実質的に参照ハブ。00_PROJECT_STRUCTURE.md の記述を合わせる |

---

## 4. 推奨移行順序

```
Phase 1: ルール + docs/internal/ + CLAUDE.md
  - MAGI 命名変更（全 rules）
  - 新規ルール 2 件追加（code-quality-guideline, planning-quality-guideline）
  - docs/internal/ 更新（06, 01, 02, 07, 00, 03, 05, 04, 99）
  - CLAUDE.md, CHEATSHEET.md 更新

Phase 2: コマンド / スキル / エージェント
  - full-review.md 全面再編（Stage 体系）
  - 新規スキル 2 件（/magi, /clarify）
  - lam-orchestrate 更新
  - 全エージェント更新（MAGI 命名 + 機能追加）
  - 全コマンド更新
  - 新規 specs/design 取込

Phase 3: Hooks + analyzers/
  - 既存 hooks 差分適用（_hook_utils, pre-tool-use, post-tool-use, lam-stop-hook, pre-compact）
  - analyzers/ ディレクトリ新規導入（13 モジュール）
  - analyzers/tests/ 新規導入
  - hooks/tests/ 差分適用
  - settings.json 更新
  - .gitignore 更新

Phase 4: 統合検証 + 完了
  - 全テスト実行（既存 830 + 新規 analyzers テスト）
  - ruff check クリーン
  - /full-review を新 Stage 体系で実行
  - SESSION_STATE.md 更新
```

### 移行リスク評価

| Phase | リスク | 理由 |
|-------|-------|------|
| Phase 1 | **低** | ドキュメント + ルール変更のみ |
| Phase 2 | **中** | コマンド構造が大きく変わるが、既存テストへの影響なし |
| Phase 3 | **高** | analyzers/ は新規 Python コード。テスト互換性の確認必須 |
| Phase 4 | **低** | 検証のみ |

---

## 5. 影式固有保持項目一覧

v4.4.1 移行時に識別済みの 25 項目に加え、以下を追加確認:

| # | 保持項目 | ファイル | 理由 |
|---|---------|---------|------|
| 1 | Project Overview テーブル | CLAUDE.md | 影式固有の技術スタック定義 |
| 2 | R-2〜R-11, S-2 | building-checklist.md | Phase 1 Retro 由来の実証済みルール |
| 3 | L-4 スモークテスト | phase-rules.md | 影式固有の Phase 完了判定 |
| 4 | Python Coding Conventions | 03_QUALITY_STANDARDS.md Sec 6/7 | Python プロジェクト固有 |
| 5 | Context 閾値 20% | CLAUDE.md | 安全側運用の継続 |
| 6 | pyproject.toml パス分類 | permission-levels.md | 影式固有の PM 級パス |
| 7 | `config/` パス分類 | permission-levels.md | 影式固有の SE 級パス |
| 8 | Python コマンド allow 設定 | security-commands.md ※1 注記 | 影式固有の二段構成 |
| 9 | notify-sound.py | hooks/ | 影式固有の通知機能 |
| 10 | A-3/A-4 監査ルール | phase-rules.md | 影式固有の再検証義務 |

---

## 6. 次のステップ

| 順序 | 作業 | 出力先 |
|------|------|-------|
| 1 | 領域別詳細差分 | `specs/00-diff-*.md` |
| 2 | 移行設計 | `designs/01-design-*.md` |
| 3 | タスク分解 | `tasks/02-tasks-*.md` |
| 4 | 承認 → 実施 | Phase 1〜4 |
