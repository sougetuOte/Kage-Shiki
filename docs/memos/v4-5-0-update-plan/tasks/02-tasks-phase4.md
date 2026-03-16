# Phase 4 タスク: 統合検証 + 完了

**ステータス**: Draft
**対象設計**: 全設計文書のクロスチェック + スモークテスト
**優先度**: 高（完了条件の確認）
**依存**: Phase 1, Phase 2, Phase 3 完了
**推定タスク数**: 13

---

## 1. 概要

### 1.1 Phase 4 の目的

Phase 4 は v4.5.0 移行の**最終検証フェーズ**である。Phase 1-3 で適用した全変更が正しく動作し、影式プロジェクトの整合性が維持されていることを確認する。

主要検証項目:
1. **全テスト実行** — 既存 830+ テスト + 新規 analyzers テストが全て PASS
2. **lint クリーン** — `ruff check .` がエラーゼロ
3. **`/full-review` 初回実行** — 新 Stage 体系での初回レビュー実行
4. **影式固有保持検証** — 47+ 項目の影式固有保持項目が全て維持
5. **完了ドキュメント** — SESSION_STATE.md 更新、CHANGELOG.md エントリ

### 1.2 前提条件

- Phase 1（ルール + docs/internal/ + CLAUDE.md + CHEATSHEET.md）完了
- Phase 2（コマンド / スキル / エージェント + specs/design 取込）完了
- Phase 3（Hooks + analyzers/ + settings.json + .gitignore）完了
- Phase 3 の Wave E（テスト）まで全て完了

### 1.3 完了条件

- 全テスト PASS（既存 + 新規）
- `ruff check .` クリーン
- `/full-review` を新 Stage 体系で実行完了（Stage 0-5）
- 影式固有保持項目 47+ 件が全て検証済み
- SESSION_STATE.md 更新済み
- CHANGELOG.md に v4.5.0 移行エントリ追加済み

---

## 2. AoT Decomposition

### 2.1 Atom 分解

| Atom | 判断内容 | 依存 | 並列可否 |
|------|----------|------|----------|
| B1 | 回帰テスト実行（既存 830+ テスト） | なし | 独立 |
| B2 | 新規テスト実行（analyzers テスト） | なし | B1 と並列可 |
| B3 | lint チェック | なし | B1/B2 と並列可 |
| B4 | 差分積分の最終確認（Phase 1-3 全タスク完了チェック） | なし | 独立 |
| B5 | 影式固有保持検証 | B4（チェックリスト作成後に検証） | B4 後 |
| B6 | `/full-review` 初回実行 | B1, B2, B3（全テスト・lint クリーン確認後） | B1-B3 後 |
| B7 | 参照完全性チェック | なし | 独立 |
| B8 | 完了ドキュメント作成 | B1-B7（全検証完了後） | 最後 |

### 2.2 依存 DAG

```
B1 ──────┐
B2 ──────┼──→ B6
B3 ──────┘
B4 ──→ B5
B7 ──────────────────┐
                     ├──→ B8
B5 ──────────────────┤
B6 ──────────────────┘
```

---

## 3. タスク一覧

### Group A: テスト・lint 実行（Atom B1, B2, B3）

#### T-401: 既存テストの回帰テスト実行

| 項目 | 内容 |
|------|------|
| **説明** | 既存の 830+ テストを全て実行し、回帰がないことを確認。Phase 3 で除去した Green State テスト分の減少は許容（ただし SKIP/FAIL は許容しない） |
| **対象ファイル** | `tests/` 配下全体 |
| **変更種別** | 検証のみ（コード変更なし） |
| **影式固有考慮** | `tests/test_hooks/test_stop_hook.py` の Green State テスト除去分でテスト総数が減少するが、FAIL は 0 であること |
| **依存** | Phase 3 全完了 |
| **サイズ** | M |

実行コマンド:
```bash
pytest tests/ --junitxml=.claude/test-results.xml -v --tb=short 2>&1 | tail -20
```

**完了条件**:
- [ ] テスト結果: failures=0, errors=0
- [ ] テスト総数を記録（Phase 3 での増減を把握）
- [ ] `tests/test_hooks/` のテストが全て PASS
- [ ] SKIP が存在する場合、理由が外部依存の欠如（skipif）のみであること

---

#### T-402: analyzers テストの実行と結果確認

| 項目 | 内容 |
|------|------|
| **説明** | `tests/test_analyzers/` のテストを実行。外部依存（tree-sitter, bandit, eslint, cargo）が未インストールのテストは SKIP として許容 |
| **対象ファイル** | `tests/test_analyzers/` 配下 |
| **変更種別** | 検証のみ |
| **影式固有考慮** | 影式は Python 単一言語プロジェクトのため、JS/Rust analyzer テストは SKIP が想定される。Python analyzer テストは ruff が利用可能なため PASS が期待される |
| **依存** | Phase 3 Wave D, Wave E 完了 |
| **サイズ** | M |

実行コマンド:
```bash
pytest tests/test_analyzers/ -v --tb=short 2>&1 | tail -30
```

**完了条件**:
- [ ] failures=0, errors=0
- [ ] SKIP のテストがある場合、全て外部依存の skipif によるものであること
- [ ] 基盤テスト（test_base, test_config, test_reducer, test_state_manager）が全て PASS
- [ ] PASS/SKIP の内訳を記録

---

#### T-403: ruff check 実行

| 項目 | 内容 |
|------|------|
| **説明** | `ruff check .` を実行し、lint エラーがゼロであることを確認。analyzers/ の新規コードも対象 |
| **対象ファイル** | プロジェクト全体 |
| **変更種別** | 検証のみ |
| **影式固有考慮** | `.claude/hooks/analyzers/` が ruff の対象に含まれること。pyproject.toml の ruff 設定（exclude 等）に analyzers/ が除外されていないことを確認 |
| **依存** | なし |
| **サイズ** | S |

実行コマンド:
```bash
ruff check . --statistics
```

**完了条件**:
- [ ] `All checks passed!` が表示されること
- [ ] analyzers/ 内のファイルがチェック対象に含まれていること

---

### Group B: 差分積分・影式固有保持検証（Atom B4, B5）

#### T-404: Phase 1-3 全タスク完了の最終確認

| 項目 | 内容 |
|------|------|
| **説明** | Phase 1-3 の全タスク分解文書を読み直し、完了条件が全て満たされているか機械的に確認 |
| **対象ファイル** | `docs/memos/v4-5-0-update-plan/tasks/02-tasks-phase1.md`, `02-tasks-phase2.md`, `02-tasks-phase3.md` |
| **変更種別** | 検証のみ |
| **影式固有考慮** | 各 Phase で影式固有保持チェックリストが全て確認済みであること |
| **依存** | なし |
| **サイズ** | M |

確認対象:
```
[ ] Phase 1: ルール + docs/internal/ + CLAUDE.md + CHEATSHEET.md
  ├─ [ ] MAGI 命名変更が全 rules に反映
  ├─ [ ] 新規ルール 2 件（code-quality-guideline, planning-quality-guideline）追加
  ├─ [ ] docs/internal/ 更新完了
  ├─ [ ] CLAUDE.md 更新完了
  └─ [ ] CHEATSHEET.md 更新完了

[ ] Phase 2: コマンド / スキル / エージェント
  ├─ [ ] full-review.md が Stage 体系に全面再編
  ├─ [ ] 新規スキル 2 件（/magi, /clarify）追加
  ├─ [ ] lam-orchestrate 更新完了
  ├─ [ ] 全エージェント更新完了
  ├─ [ ] 全コマンド更新完了
  └─ [ ] 新規 specs/design 取込完了

[ ] Phase 3: Hooks + analyzers/ + settings.json + .gitignore
  ├─ [ ] settings.json に PostToolUseFailure 登録
  ├─ [ ] pre-tool-use.py に _PG_BLACKLISTED_ARGS 追加
  ├─ [ ] post-tool-use.py に PostToolUseFailure 対応 + リファクタリング
  ├─ [ ] lam-stop-hook.py が安全ネット設計に書き換え済み
  ├─ [ ] analyzers/ に 13 モジュール配置
  ├─ [ ] tests/test_analyzers/ にテスト配置
  ├─ [ ] .gitignore に review-state/ 追加
  └─ [ ] notify-sound.py が未変更
```

**完了条件**:
- [ ] 全 Phase の完了条件が確認 OK
- [ ] 予期しないファイル削除がないこと（`git status` で確認）

---

#### T-405: 影式固有保持項目の総合検証

| 項目 | 内容 |
|------|------|
| **説明** | 000-index.md Section「影式固有保持項目一覧」（10 件）+ 各 Phase のチェックリストを統合し、47+ 項目を一括検証 |
| **対象ファイル** | プロジェクト全体 |
| **変更種別** | 検証のみ |
| **影式固有考慮** | これが最も重要な検証項目。LAM v4.5.0 への移行で影式固有の特性が失われていないことの最終確認 |
| **依存** | T-404 |
| **サイズ** | L |

統合チェックリスト:

**CLAUDE.md 関連**:
- [ ] Project Overview テーブル（Python 3.12+, tkinter, pystray, anthropic, SQLite, TOML, pytest）が保持
- [ ] Context 閾値 20% が保持（LAM は 10%）
- [ ] Memory Policy の影式固有調整が保持

**rules 関連**:
- [ ] `building-checklist.md`: R-2〜R-11, S-2 が保持（R-5/R-6 は R-12/R-13 にリナンバ済み）
- [ ] `phase-rules.md`: L-4 スモークテスト（影式固有 Phase 完了判定）が保持
- [ ] `phase-rules.md`: A-3/A-4 監査ルール（影式固有再検証義務）が保持
- [ ] `permission-levels.md`: `pyproject.toml` が PM 級パスに含まれている
- [ ] `permission-levels.md`: `config/` が SE 級パスに含まれている
- [ ] `security-commands.md`: Python コマンド allow 設定の二段構成（※1 注記）が保持

**docs/internal/ 関連**:
- [ ] `03_QUALITY_STANDARDS.md`: Python Coding Conventions（Section 6/7）が保持
- [ ] `00_PROJECT_STRUCTURE.md`: 影式固有ディレクトリ（src/kage_shiki/ 等）が記載

**hooks 関連**:
- [ ] `_hook_utils.py`: `_MAX_STDIN_BYTES`（1MB stdin 制限）
- [ ] `_hook_utils.py`: `normalize_path()` の Windows 対応（resolve + backslash 変換）
- [ ] `_hook_utils.py`: `datetime.UTC`（Python 3.12+ 短縮形）
- [ ] `pre-tool-use.py`: PM パターンに `docs/internal/` と `pyproject.toml`
- [ ] `pre-tool-use.py`: `normalized` パスを理由に含む出力形式
- [ ] `post-tool-use.py`: `python -m pytest` テストパターン
- [ ] `notify-sound.py`: 一切変更なし（影式固有通知機能）

**settings.json 関連**:
- [ ] hooks コマンドプレフィックスが `python`（Windows 環境）
- [ ] `Bash(git status *)` が allow
- [ ] `Bash(pip show *)` が allow
- [ ] `Bash(python *)` が ask に**含まれていない**

**.gitignore 関連**:
- [ ] `!docs/memos/` 選択的除外パターン
- [ ] `!docs/memos/v4-update-plan/`
- [ ] `!docs/memos/v4-4-1-update-plan/`
- [ ] `config.toml`
- [ ] `# pytest` セクション

**エージェント関連**:
- [ ] `design-architect.md`: permission-level が PM（LAM は SE だが影式は PM 維持）
- [ ] `quality-auditor.md`: model が Sonnet に変更済み（v4.5.0 決定）

**構成関連**:
- [ ] `.claude/hooks/analyzers/` に 13 ファイル存在
- [ ] `tests/test_analyzers/` にテスト存在
- [ ] `.claude/review-state/` が .gitignore に追加済み

**完了条件**:
- [ ] 上記全チェック項目が OK
- [ ] NG 項目がある場合、修正済みであること

---

### Group C: /full-review 初回実行（Atom B6）

#### T-406: /full-review 実行前の前提確認

| 項目 | 内容 |
|------|------|
| **説明** | `/full-review` を新 Stage 体系で実行する前に、前提条件を確認。テスト全 PASS、lint クリーン、lam-stop-hook が安全ネット設計であることを確認 |
| **対象ファイル** | なし（確認のみ） |
| **変更種別** | 検証のみ |
| **影式固有考慮** | Phase 3 で lam-stop-hook の Green State 判定を除去したため、`/full-review` Stage 5 が唯一の Green State 判定手段であることを確認 |
| **依存** | T-401, T-402, T-403 |
| **サイズ** | S |

確認項目:
- [ ] T-401: 既存テスト全 PASS
- [ ] T-402: analyzers テスト PASS（SKIP は許容）
- [ ] T-403: ruff check クリーン
- [ ] lam-stop-hook.py が安全ネット設計（Green State 判定なし）
- [ ] full-review.md が Stage 体系に更新済み（Phase 2 完了）

**完了条件**:
- [ ] 全前提条件が確認 OK

---

#### T-407: /full-review 初回実行（新 Stage 体系）

| 項目 | 内容 |
|------|------|
| **説明** | `/full-review` を新 Stage 体系（Stage 0-5）で初回実行。対象は `.claude/hooks/` ディレクトリ（Phase 3 の変更が最も大きい領域）。Stage 5（True Green State）が正常に動作することを確認 |
| **対象ファイル** | `.claude/hooks/` |
| **変更種別** | 検証（レビュー実行） |
| **影式固有考慮** | analyzers/ パイプライン（Stage 0）が影式の ~5K LOC 規模で正常に動作するか確認。Plan A 未満の場合は Stage 0 がスキップされる可能性あり |
| **依存** | T-406 |
| **サイズ** | L |

実行手順:
1. `/full-review .claude/hooks/` を実行
2. Stage 0（Pre-flight / 静的解析）の出力を確認
3. Stage 1-4（レビュー本体）の出力を確認
4. **Stage 5（True Green State）** の出力を特に確認:
   - G1: テスト全パス確認
   - G2: lint エラーゼロ確認
   - G3: 対応可能 Issue ゼロ確認
   - G4: 仕様差分ゼロ確認
   - G5: セキュリティチェック通過確認

**完了条件**:
- [ ] `/full-review` が Stage 0-5 の順序で実行されること
- [ ] Stage 5 で Green State 判定が行われること
- [ ] レビュー結果に Critical issues がないこと（Warning/Info は許容）
- [ ] analyzers/ パイプラインがエラーなく動作すること（SKIP は許容）

---

#### T-408: /full-review 結果の Issue 対応

| 項目 | 内容 |
|------|------|
| **説明** | T-407 の `/full-review` で検出された Issue を権限等級に基づき対応。PG/SE 級は修正、PM 級は指摘のみ |
| **対象ファイル** | `/full-review` で指摘されたファイル |
| **変更種別** | 修正（PG/SE 級のみ） |
| **影式固有考慮** | Phase 3 の変更に起因する Issue を優先的に対応。影式固有保持項目に影響する修正は PM 級として扱う |
| **依存** | T-407 |
| **サイズ** | M（Issue 数に依存） |

対応方針:
- **PG 級**: 自動修正（フォーマット、typo、lint 違反）
- **SE 級**: 修正後に報告（テスト追加、内部リファクタリング）
- **PM 級**: 指摘のみ（仕様変更、アーキテクチャ変更は Phase 4 の範囲外）

**完了条件**:
- [ ] PG/SE 級 Issue が全件修正済み
- [ ] PM 級 Issue が列挙され、承認ゲートへ送られていること
- [ ] 修正後にテスト再実行し、回帰なし確認

---

### Group D: 参照完全性チェック（Atom B7）

#### T-409: 内部参照の一貫性確認

| 項目 | 内容 |
|------|------|
| **説明** | ドキュメント間の相互参照、ファイルパス参照が正確かを検証。v4.5.0 移行で変更されたパス・名称が全て反映されていること |
| **対象ファイル** | プロジェクト全体 |
| **変更種別** | 検証のみ |
| **影式固有考慮** | 影式固有パス（`docs/memos/middle-draft/`, `src/kage_shiki/`）への参照が断絶していないこと |
| **依存** | なし |
| **サイズ** | M |

チェック項目:

```bash
# 1. 旧名称 "Three Agents" の残存確認（MAGI に変更済みのはず）
grep -r "Three Agents" .claude/ docs/ --include="*.md" | grep -v "旧" | grep -v "MAGI"
# → 0 件であること（後方互換の括弧書き併記は許容）

# 2. 旧 Stage/Phase 番号の残存確認（full-review が 6 Stage に再編済み）
grep -r "Phase 1.*lint" .claude/commands/full-review.md
# → 旧 Phase 番号ではなく Stage 番号であること

# 3. Green State の参照先確認
grep -r "Green State" .claude/hooks/ docs/internal/ .claude/rules/
# → lam-stop-hook.py 内に Green State への言及がないこと
# → full-review.md / phase-rules.md が Stage 5 を参照していること

# 4. analyzers/ への参照が正しいこと
grep -r "analyzers/" .claude/commands/ docs/specs/
# → パスが .claude/hooks/analyzers/ であること

# 5. 新規スキル /magi, /clarify への参照
grep -r "/magi\|/clarify" .claude/commands/ .claude/rules/ docs/internal/
# → 参照が存在すること

# 6. 影式固有パスの断絶チェック
grep -r "docs/memos/middle-draft" CLAUDE.md .claude/rules/
# → 参照が有効であること
```

**完了条件**:
- [ ] 旧名称の残存が 0 件（後方互換併記を除く）
- [ ] 全参照パスが有効
- [ ] 断絶リンクなし

---

#### T-410: specs/design 取込の完全性確認

| 項目 | 内容 |
|------|------|
| **説明** | Phase 2 で取り込んだ specs/design ドキュメントが正しく配置され、他ドキュメントからの参照が有効であることを確認 |
| **対象ファイル** | `docs/specs/`, `docs/design/` |
| **変更種別** | 検証のみ |
| **影式固有考慮** | なし |
| **依存** | なし |
| **サイズ** | S |

確認対象:
- [ ] `docs/specs/lam/magi-skill-spec.md` が存在
- [ ] `docs/specs/lam/scalable-code-review-spec.md` が存在
- [ ] `docs/specs/lam/scalable-code-review-phase5-spec.md` が存在
- [ ] `docs/specs/lam/scalable-code-review.md` が存在
- [ ] `docs/design/scalable-code-review-design.md` が存在

**完了条件**:
- [ ] 上記 5 ファイルが全て存在
- [ ] `full-review.md` からの参照が有効

---

### Group E: 完了ドキュメント（Atom B8）

#### T-411: SESSION_STATE.md の更新

| 項目 | 内容 |
|------|------|
| **説明** | 現在のセッション状態を SESSION_STATE.md に記録。v4.5.0 移行完了を反映 |
| **対象ファイル** | `SESSION_STATE.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | SESSION_STATE.md は .gitignore に含まれているが、移行完了の記録として重要 |
| **依存** | T-401〜T-410 全完了 |
| **サイズ** | S |

記載内容:
```markdown
## 現在の状態
- LAM バージョン: v4.5.0 移行完了
- 最終テスト結果: 全 PASS（YYYY-MM-DD）
- 最終 lint 結果: クリーン
- /full-review 初回実行: Stage 0-5 完了

## 移行サマリー
- Phase 1: ルール + docs/internal/ ✓
- Phase 2: コマンド / スキル / エージェント ✓
- Phase 3: Hooks + analyzers/ ✓
- Phase 4: 統合検証 ✓
```

**完了条件**:
- [ ] SESSION_STATE.md が更新されていること

---

#### T-412: CHANGELOG.md に v4.5.0 移行エントリを追加

| 項目 | 内容 |
|------|------|
| **説明** | CHANGELOG.md に LAM v4.5.0 移行の変更内容を記録 |
| **対象ファイル** | `CHANGELOG.md` |
| **変更種別** | 追加 |
| **影式固有考慮** | 影式固有の判断（Context 閾値 20% 維持、design-architect PM 維持等）も記載 |
| **依存** | T-401〜T-410 全完了 |
| **サイズ** | M |

エントリテンプレート:
```markdown
## [Unreleased] — LAM v4.5.0 移行

### Added
- MAGI System（Three Agents Model の進化版）— MELCHIOR/BALTHASAR/CASPAR + Reflection
- Scalable Code Review パイプライン（analyzers/ 13 モジュール）
- /full-review Stage 体系（11 Phase → 6 Stage への再編）
- /magi スキル（AoT + MAGI + Reflection）
- /clarify スキル（文書精緻化インタビュー）
- code-quality-guideline.md（Critical/Warning/Info 品質基準）
- planning-quality-guideline.md（計画品質基準）
- PostToolUseFailure イベントサポート
- _PG_BLACKLISTED_ARGS セキュリティチェック
- specs/design 4 件取込

### Changed
- lam-stop-hook.py: Green State 判定を除去、安全ネット専用に再設計（~540行→~150行）
- post-tool-use.py: 関数分離リファクタリング + PostToolUseFailure 対応
- pre-tool-use.py: AUDITING PG ブラックリスト引数チェック追加
- quality-auditor: Opus → Sonnet に変更
- task-decomposer: Haiku に変更
- requirement-analyst: PM 級に昇格
- R-5/R-6 → R-12/R-13 にリナンバ（LAM 識別子衝突解消）

### Preserved（影式固有）
- Context 閾値 20%（LAM は 10%）
- design-architect PM 級維持（LAM は SE）
- Python Coding Conventions（03_QUALITY_STANDARDS Section 6/7）
- notify-sound.py（影式固有通知フック）
- Windows 対応（python コマンドプレフィックス、normalize_path）
- stdin バイト制限（_MAX_STDIN_BYTES）
```

**完了条件**:
- [ ] CHANGELOG.md に v4.5.0 移行エントリが追加されていること
- [ ] Added/Changed/Preserved が正確に記載されていること

---

#### T-413: 000-index.md のステータス更新

| 項目 | 内容 |
|------|------|
| **説明** | 移行計画のインデックスファイルの全タスクステータスを「完了」に更新 |
| **対象ファイル** | `docs/memos/v4-5-0-update-plan/000-index.md` |
| **変更種別** | 更新 |
| **影式固有考慮** | なし |
| **依存** | T-401〜T-412 全完了 |
| **サイズ** | S |

**完了条件**:
- [ ] tasks/ セクションの全 Phase ステータスが「完了」
- [ ] 移行完了日が記載されていること

---

## 4. MAGI Review

### [MELCHIOR]: 並列性・効率

Group A（T-401〜T-403）は全て独立しており、並列実行可能。特に `pytest` と `ruff check` は同時実行で時間短縮が期待できる。

Group B（T-404〜T-405）と Group D（T-409〜T-410）も Group A と並列実行可能。

Group C（T-406〜T-408）は Group A の完了を待つ必要があるが、`/full-review` の実行自体が最も時間を要する作業であるため、先行タスクを迅速に完了させることが重要。

最適実行パス:
```
Time 1: T-401 + T-402 + T-403 + T-404 + T-409 + T-410（全並列）
Time 2: T-405（T-404 完了後）
Time 3: T-406 → T-407 → T-408（順次実行）
Time 4: T-411 + T-412 + T-413（全完了後、並列可）
```

### [BALTHASAR]: ギャップ・リスク・不足タスク

1. **テスト総数の変化**: Phase 3 で Green State テスト（推定 15-25 件）を除去し、安全ネットテスト（推定 5-8 件）+ analyzers テスト（推定 50+ 件）を追加。総数は増加するが、**既存テストの 830+ という基準値は変動する**。T-401 でテスト総数を記録し、変動の妥当性を確認すべき。

2. **/full-review の実行時間**: 新 Stage 体系での `/full-review` は analyzers パイプライン（Stage 0）を含むため、初回実行に時間がかかる可能性がある。タイムアウトの考慮が必要。

3. **PM 級 Issue の扱い**: T-408 で PM 級 Issue が検出された場合、Phase 4 の範囲外として記録するが、**移行完了の判断に影響するか**の基準が不明確。→ PM 級 Issue は「後続タスク」として記録し、Phase 4 完了の阻害要因としないことを明文化すべき。

4. **ロールバックの困難さ**: Phase 4 は検証フェーズであり、コード変更は T-408（Issue 対応）のみ。T-408 の修正で問題が発生した場合は `git revert` でロールバック可能。

5. **不足タスク候補**: `pyproject.toml` の ruff 設定で analyzers/ が除外されていないかの確認。→ T-403 の実行時に自然に検出されるため、個別タスク化は不要。

### [CASPAR]: 最終判定

Phase 4 のタスク分解は妥当。13 タスクに分解し、5 Group での実行計画は適切。

**最大の懸念点**は T-407（/full-review 初回実行）の結果に依存する部分が大きいこと。Stage 体系の初回実行で予期しない問題が発生する可能性があるが、T-408 で対応可能。

**追加推奨事項**:
- T-401 の実行後、テスト総数の変動を明示的に記録する（「830 → N 件」の形式）
- T-407 の実行結果を `docs/memos/v4-5-0-update-plan/` に保存し、移行記録として残す
- PM 級 Issue は「後続タスク」セクションに集約し、Phase 4 完了後に承認ゲートを設ける

---

## 5. 実行順序

```
Phase 4 実行順序（推奨）
═══════════════════════

Step 1: Group A + Group B-1 + Group D（並列実行）
  ├─ T-401: 既存テスト回帰テスト実行                        [M]
  ├─ T-402: analyzers テスト実行                            [M]
  ├─ T-403: ruff check 実行                                [S]
  ├─ T-404: Phase 1-3 全タスク完了確認                      [M]
  ├─ T-409: 内部参照の一貫性確認                            [M]
  └─ T-410: specs/design 取込の完全性確認                   [S]
  → 所要時間: ~1.5 時間

Step 2: Group B-2（T-404 完了後）
  └─ T-405: 影式固有保持項目の総合検証                      [L]
  → 所要時間: ~1 時間

Step 3: Group C（T-401〜T-403 完了後）
  ├─ T-406: /full-review 実行前の前提確認                   [S]
  ├─ T-407: /full-review 初回実行（Stage 0-5）              [L]
  └─ T-408: /full-review 結果の Issue 対応                  [M]
  → 所要時間: ~2 時間

Step 4: Group E（全完了後）
  ├─ T-411: SESSION_STATE.md 更新                          [S]
  ├─ T-412: CHANGELOG.md エントリ追加                      [M]
  └─ T-413: 000-index.md ステータス更新                    [S]
  → 所要時間: ~30 分

総所要時間: ~5 時間
```

---

## 6. 検証チェックリスト（Phase 4 最終完了条件）

### テスト・lint

- [ ] 既存テスト: failures=0, errors=0
- [ ] analyzers テスト: failures=0, errors=0（SKIP は許容）
- [ ] `ruff check .`: `All checks passed!`
- [ ] テスト総数の変動が記録されていること

### /full-review

- [ ] Stage 0-5 が順序通り実行されたこと
- [ ] Stage 5（True Green State）で判定が行われたこと
- [ ] Critical issues がゼロであること
- [ ] PG/SE 級 Issue が全件修正済みであること
- [ ] PM 級 Issue が後続タスクとして記録されていること

### 影式固有

- [ ] T-405 のチェックリストが全て OK
- [ ] 47+ 項目の影式固有保持項目が全て維持されていること

### 参照完全性

- [ ] 旧名称（Three Agents 等）の残存がないこと
- [ ] 全参照パスが有効であること
- [ ] specs/design の 5 ファイルが全て存在すること

### ドキュメント

- [ ] SESSION_STATE.md が更新済み
- [ ] CHANGELOG.md に v4.5.0 移行エントリが追加済み
- [ ] 000-index.md の全ステータスが「完了」

### 最終確認

- [ ] `git status` で予期しない変更がないこと
- [ ] 全 Phase 1-4 の完了条件が満たされていること

---

## 7. 後続タスク（Phase 4 完了後）

Phase 4 完了後、以下の作業が PM 級承認待ちとなる:

| # | タスク | 権限等級 | 実施時期 |
|---|--------|---------|---------|
| F-1 | T-408 で検出された PM 級 Issue の対応 | PM | 承認後即時 |
| F-2 | 移行完了の確定アナウンス | SE | Phase 4 完了直後 |
| F-3 | 新機能の実運用テスト（/magi, /clarify, analyzers パイプライン） | SE | 次回開発サイクル |
| F-4 | TDD パターン分析（/retro Step 2.5）の初回実行 | SE | 次回 /retro 実行時 |

---

## 8. リスク一覧

| # | リスク | 影響度 | 対策 |
|---|--------|--------|------|
| R1 | テスト総数が 830 から大幅に減少 | **中** | Phase 3 で除去した Green State テスト分と追加テスト分を明示的に計上。減少が想定範囲内か確認 |
| R2 | /full-review Stage 0 で analyzers パイプラインエラー | **中** | Plan A 未満の場合 Stage 0 はスキップされる可能性あり。エラー時は Stage 1 から続行 |
| R3 | /full-review で Critical issues が検出される | **中** | Phase 4 内で PG/SE 級を修正。PM 級は後続タスクに記録 |
| R4 | 影式固有保持項目の見落とし | **高** | T-405 のチェックリストで網羅的に検証。不足があれば即時修正 |
| R5 | ruff check で analyzers/ の新規コードにエラー | **低** | LAM v4.5.0 のコードは lint 済みの前提。エラーがあれば PG 級で即時修正 |
