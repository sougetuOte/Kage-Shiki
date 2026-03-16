# 設計: Phase 1 — Rules + docs/internal/ + CLAUDE.md + CHEATSHEET.md 移行

**作成日**: 2026-03-16
**ステータス**: Draft
**対象**: LAM v4.4.1 → v4.5.0 移行 Phase 1
**前提資料**:
- `specs/00-diff-summary.md`（全体サマリー + 承認済み判断）
- `specs/00-diff-rules.md`（rules/ 差分分析）
- `specs/00-diff-docs-internal.md`（docs/internal/ + CLAUDE.md + CHEATSHEET.md 差分分析）
- `v4-4-1-update-plan/designs/01-design-rules-docs.md`（前回移行設計参照）

---

## 1. 概要

### 1.1 Phase 1 の目的

LAM v4.5.0 の変更のうち、ドキュメント層（rules、docs/internal/、CLAUDE.md、CHEATSHEET.md）を影式に適用する。既存テストやソースコードへの影響がなく、リスクが最も低い Phase として先行実施する。

### 1.2 Phase 1 の範囲

| 対象層 | 含むファイル数 | 主な変更テーマ |
|--------|-------------|--------------|
| `.claude/rules/` | 既存 9 + サブディレクトリ 2 + 新規 2 | MAGI System 導入、品質ガイドライン新設、R-5/R-6 追加 |
| `docs/internal/` | 9 ファイル（00〜07, 99） | MAGI 命名、SSOT 3層再構成、/clarify 統合 |
| `CLAUDE.md` | 1 ファイル | SSOT 3層追従、Memory Policy 更新 |
| `CHEATSHEET.md` | 1 ファイル | MAGI 命名、/magi + /clarify 追加 |

### 1.3 Phase 1 に含まないもの

- コマンド / スキル / エージェント（Phase 2）
- Hooks / analyzers/（Phase 3）
- 統合検証（Phase 4）

### 1.4 承認済み判断（2026-03-16）

| # | 判断 | 結論 |
|---|------|------|
| 1 | R-5/R-6 識別子衝突 | 影式の R-5→R-12, R-6→R-13 にリナンバ。LAM の R-5/R-6 を phase-rules.md に採用 |
| 2 | SSOT 3層 | LAM に追従。docs/internal/ が情報層 1、CLAUDE.md はブートストラップ |
| 3 | Context 閾値 | 影式の 20% を維持（LAM の 10% は採用しない） |
| 4 | 03_QS Python セクション | 影式の Section 6/7 を保持 |

---

## 2. 移行戦略

基本方針は前回（v4.4.1）と同様に **Template-First**（LAM v4.5.0 をベースに影式固有カスタマイズを上乗せ）で進める。

---

### 2.0 事前確認（Phase 1 開始前に実施）

1. **`docs/specs/green-state-definition.md` の存在確認**: 影式に該当ファイルが存在するか確認する。
   - 存在する場合: code-quality-guideline.md は G3（Issue 解決）の詳細基準として位置づけ
   - 存在しない場合: phase-rules.md の G1-G5 テーブルが Green State の SSOT。code-quality-guideline.md は G3 の判定基準を定義するファイルとして整合させる
2. **コンテキスト消費量の見積もり**: 現行 `.claude/rules/` の合計行数と、新規追加（code-quality-guideline.md ~100行 + planning-quality-guideline.md ~80行）による増加率を計測する
3. **`03_QUALITY_STANDARDS.md` Section 7 の R-5/R-6 参照確認**: grep で R-5, R-6 への参照を確認し、リナンバリング対象箇所を特定する

---

### 2.1 .claude/rules/ の各ファイル

#### 2.1.1 decision-making.md — MAGI System 導入 + Reflection 追加

**変更種別**: 更新（中規模）

**具体的な変更内容**:
1. タイトル変更: `# 意思決定プロトコル` → `# 意思決定プロトコル（MAGI System）`
2. セクション名変更: `## Three Agents Model` → `## MAGI System`
3. SSOT 注記の位置を変更: セクション見出し直下 → `## MAGI System` 直下
4. Agent テーブルの名称変更:
   - Affirmative → MELCHIOR（科学者（Affirmative / 推進者））
   - Critical → BALTHASAR（母（Critical / 批判者））
   - Mediator → CASPAR（女（Mediator / 調停者））
5. Execution Flow の名称変更 + Reflection 追加:
   - Step 1: Affirmative と Critical → MELCHIOR と BALTHASAR
   - Step 3: Mediator → CASPAR
   - **Step 4 新設**: `Reflection（新規追加）: 全員で結論を検証（1回限り）。致命的な見落としがあれば修正`
6. AoT ワークフロー: `Three Agents Debate` → `MAGI Debate`、Reflection ステップ挿入
7. Output Format ラベル変更 + Reflection セクション追加:
   ```
   **[MELCHIOR]**: ...
   **[BALTHASAR]**: ...
   **[CASPAR]**: 結論: ...

   ### Reflection
   致命的な見落とし: なし → 結論確定
   ```

**影式固有考慮**: なし（影式固有の追記は存在しない）

---

#### 2.1.2 phase-rules.md — PLANNING 品質基準 + R-5/R-6 + Green State 再定義

**変更種別**: 更新（大規模）。最も差分が大きいファイル。

**具体的な変更内容**:

**(A) PLANNING セクション — 品質基準サブセクション新設**:
```markdown
### 品質基準

成果物は `.claude/rules/planning-quality-guideline.md` に準拠すること:
- 仕様書: Requirements Smells 検出 + RFC 2119 キーワード統一
- 設計書: Design Doc チェックリスト（非スコープ・代替案・成功基準）
- タスク: SPIDR 分割 + WBS 100% Rule（仕様⇔タスクのトレーサビリティ）
- 明確化: Example Mapping（`/clarify` 併用）
```
挿入位置: 承認ゲートと禁止の間。

**(B) BUILDING セクション — R-5/R-6 追加**:
TDD 品質チェックに以下を追加:
```markdown
- [ ] R-5: テスト名と入力値の一致 — テスト名に含まれる数値・条件と、実際のテスト入力値が一致していること
- [ ] R-6: 設計書出力ファイルからのアサーション生成 — 設計書に「ファイル X を生成する」と記載された出力は、Red ステップで `assert path.is_file()` を書くこと
```
既存の `(プロジェクト固有ルールは building-checklist.md を参照: R-2, R-3, R-5〜R-11, S-2)` の参照コメントも更新:
→ `(プロジェクト固有ルールは building-checklist.md を参照: R-2, R-3, R-12, R-13, R-7〜R-11, S-2)`

**(C) AUDITING セクション — 必須の更新**:
```markdown
### 必須

- チェックリストに基づく網羅的確認
- 重要度分類: Critical / Warning / Info（判断基準は `.claude/rules/code-quality-guideline.md` に準拠）
- MAGI System 適用、根拠明示
- 問題の PG/SE/PM 分類（権限等級に基づく）
```
変更点: (1) code-quality-guideline.md への参照追加、(2) `3 Agents Model` → `MAGI System`、(3) 項目順序の微調整

**(D) AUDITING セクション — Green State 条件の再定義**:

既存の Green State 5条件テーブル（G1-G5）の**前に** v4.5.0 の Issue ベース条件を追加:
```markdown
### Green State 条件

Critical = 0 かつ Warning = 0 → Green State（監査通過）

Info は件数にかかわらず Green State を阻害しない。
詳細な判断基準は `.claude/rules/code-quality-guideline.md` を参照。
```

既存の G1-G5 テーブルは「影式固有: Green State 5条件との対応」として保持。v4.5.0 の Issue ベース条件は G3 に相当し、G1/G2/G4/G5 は影式の追加要件として位置付ける。

**(E) 影式固有セクション — 全て保持**:
- `影式固有: Phase 完了判定（L-4 由来）`
- `影式固有: 修正後の再検証義務（A-3 由来）`
- `影式固有: 監査レポート完了条件`
- `AUDITING ルール識別子（A-1〜A-4）`

---

#### 2.1.3 building-checklist.md — R-5/R-6 リナンバリング

**変更種別**: 更新（小規模）

**具体的な変更内容**:
1. `R-5: 異常系テストの義務` → `R-12: 異常系テストの義務`
2. `R-6: else のデフォルト値禁止` → `R-13: else のデフォルト値禁止`
3. Red セクションの見出し内 `R-5` → `R-12`
4. Green セクションの見出し内 `R-6` → `R-13`
5. Green 直後セクション内の `R-6 再確認` → `R-13 再確認`
6. Green 直後セクション内の `R-5 続: カバレッジ確認` → `R-12 続: カバレッジ確認`

**影響範囲**: building-checklist.md 内で閉じる。phase-rules.md の参照コメントも合わせて更新（2.1.2 (B) で対応済み）。

---

#### 2.1.4 code-quality-guideline.md — 新規追加

**変更種別**: 新規追加

**方針**: LAM v4.5.0 テンプレートをそのまま導入（影式固有の変更なし）。

**主要セクション**:
- 三層モデル（ツール領域 / 構造領域 / 設計領域）
- Critical / Warning / Info の定義と閾値
- Green State の Issue 条件（Critical = 0 かつ Warning = 0）
- 判断フローチャート
- アンチパターン（Bikeshedding 等）
- BUILDING / AUDITING フェーズでの適用

**影式との整合確認**:
- building-checklist.md R-12（異常系テストの義務）と code-quality-guideline.md Critical「Error Swallowing」は補完関係（衝突なし）。R-12 は「テストを書く」義務、Critical は「検出時の重要度」定義
- 03_QUALITY_STANDARDS.md の閾値との関係: code-quality-guideline.md の閾値（Cognitive Complexity > 15、50行等）は 03_QS に未記載の新規基準であり、矛盾なし

---

#### 2.1.5 planning-quality-guideline.md — 新規追加

**変更種別**: 新規追加

**方針**: LAM v4.5.0 テンプレートをそのまま導入（影式固有の変更なし）。

**主要セクション**:
- Requirements Smells（危険な単語リスト）
- RFC 2119 キーワード（MUST/SHOULD/MAY）
- Design Doc チェックリスト
- SPIDR タスク分割
- WBS 100% Rule
- Example Mapping

**注意**: Phase 2 で導入される `/clarify` スキルとの連携が想定されているが、Phase 1 時点ではスキル未導入。phase-rules.md の品質基準参照は先行して配置し、スキルは Phase 2 で追加する。

---

#### 2.1.6 security-commands.md — find 破壊パターン deny 昇格 + 説明文追加

**変更種別**: 更新（中規模）

**具体的な変更内容**:

1. **deny テーブルに find 破壊パターンを独立行として追加**:
   ```
   | find 破壊パターン | `find -delete`, `find -exec rm`, `find -exec chmod`, `find -exec chown` | 再帰的な不可逆操作 |
   ```

2. **ask テーブルに find 通常検索を独立行として追加**:
   ```
   | ファイル検索 | `find` | 通常検索（破壊パターンは deny） |
   ```

3. **deny セクションに説明文追加**:
   ```markdown
   不可逆または致命的な影響を持つコマンド。AI による実行を禁止する。
   ```

4. **ask セクションに説明文追加**:
   ```markdown
   システムに変更を加える、または外部と通信するコマンド。実行前に必ずユーザーの承認を得る。
   ```

5. **v4.0.0 セクションの PG 級コマンド例示微修正**: `ruff check --fix` → `ruff format`（影式は ruff を使用しているため、この例示は影式にも適切。ただし `ruff check --fix` も引き続き有用なため、両方を記載する形にする）

**影式固有の保持**:
- Python カテゴリ（Allow List）: `python`, `python -m pytest`, `python -m ruff`, `python -c`, `pip`, `pyenv` ※1
- `pip show`（パッケージ情報カテゴリ）
- ※1 注記（二段構成: `settings.json` と `settings.local.json`）

---

#### 2.1.7 permission-levels.md — SE/PM 説明文改善 + 参照更新

**変更種別**: 更新（小規模）

**具体的な変更内容**:

1. **SE級の説明文更新**:
   `修正は許可されるが、完了後にユーザーへ報告する。`
   → `技術的な判断を含むが、公開 API や仕様に影響しない変更。修正後にユーザーへ報告する。`
   （LAM v4.5.0 の定義型表現を採用しつつ、影式の行動指示「報告する」も併記）

2. **PM級の説明文追加**:
   `プロジェクトの方向性・仕様・アーキテクチャに影響する変更。人間の承認が必須。`

3. **ファイルパスベース分類の `.claude/rules/` 注記更新**:
   `ルール変更` → `ルール変更（サブディレクトリ含む）`

4. **参照セクションに追加**:
   `docs/specs/v4.0.0-immune-system-requirements.md` は影式に該当ファイルが存在しないため**追加しない**。

**影式固有の保持**:
- SSOT 宣言（冒頭 4 行）
- 影式固有パス: `docs/internal/*.md`, `pyproject.toml`, `src/kage_shiki/`, `tests/`, `config/`
- 影式固有例: `config.toml テンプレートの変更`, `docs/internal/ の変更`, `tests/ の新規テスト追加`
- 相互参照: phase-rules.md, core-identity.md, security-commands.md

---

#### 2.1.8 upstream-first.md — 確認対象明示 + WebFetch 注意事項

**変更種別**: 更新（小規模）

**具体的な変更内容**:

1. **「必須: 実装前の仕様確認」に確認対象リストを追加**:
   ```markdown
   以下のいずれかに該当する変更を行う前に、公式ドキュメントを確認すること:

   - `.claude/settings.json`（permissions, hooks 等）
   - `.claude/hooks/` 配下のスクリプト（入出力形式、イベントタイプ）
   - skills / subagents のフロントマター
   - MCP サーバー設定
   ```

2. **確認手順の後に WebFetch 注意事項を追加**:
   ```markdown
   > **注意**: `/full-review` 等の自動フロー内では WebFetch を使用しない（無応答リスクのため）。
   > context7 が利用不可の場合は仕様確認をスキップし、対話モードでの確認を案内する。
   ```

**影式固有考慮**: なし

---

#### 2.1.9 test-result-output.md — 構造改善 + 言語別リファレンス拡充

**変更種別**: 更新（中規模）

**具体的な変更内容**:

1. **概要の一般化**: `JUnit XML 形式で .claude/test-results.xml に出力` → `構造化ファイルに出力`
2. **ルールセクションの統合**: 2つのサブセクション → 番号付きリスト
3. **理由セクション新設**: exit code 問題の背景説明
4. **Go リファレンス更新**: `go-junit-report` → `gotestsum`
5. **Rust リファレンス拡充**: `cargo-nextest` / `cargo2junit` の 2 パターン
6. **「その他の言語」セクション追加**
7. **適用タイミングセクション新設**
8. **PostToolUse 連携 → 「結果ファイルが存在しない場合」にセクション名変更**
9. **参照セクション新設**: `docs/specs/tdd-introspection-v2.md`, `trust-model.md`（影式パスは `docs/specs/lam/tdd-introspection-v2.md` を使用）

**影式固有考慮**: 影式は Python (pytest) のみ使用。Go/Rust の更新は直接影響ないが、テンプレート整合のため取り込む。

---

#### 2.1.10 core-identity.md — 変更なし

v4.4.1 → v4.5.0 間で LAM テンプレートに差分なし。影式固有セクション（Subagent 委任判断、コンテキスト節約原則）も引き続き保持。変更不要。

---

#### 2.1.11 auto-generated/README.md — 冒頭説明文追加

**変更種別**: 更新（軽微）

**具体的な変更内容**:
1. `# 自動生成ルール` の直下にディレクトリ目的の説明文を追加:
   ```markdown
   このディレクトリには、TDD 内省パイプライン v2 によって自動生成されたルールが配置される。
   ```

**影式固有の保持**: 仕様書パスの `lam/` プレフィックス（`docs/specs/lam/tdd-introspection-v2.md`）

---

#### 2.1.12 auto-generated/trust-model.md — フロー図微修正

**変更種別**: 更新（軽微）

**具体的な変更内容**:
1. フロー図の `JUnit XML 出力 (.claude/test-results.xml)` → `JUnit XML 出力`（パス注記の削除）

**影式固有の保持**:
- tdd-patterns.log の形式セクション（TSV 形式定義）
- 仕様書パスの `lam/` プレフィックス
- パターン詳細記録先の参照行（`docs/artifacts/tdd-patterns/`）

---

### 2.2 docs/internal/ の各ファイル

#### 2.2.1 00_PROJECT_STRUCTURE.md — SSOT 3層再構成

**変更種別**: 更新（大規模、Section 3 を中心に）

**具体的な変更内容**:

**(A) Section 1: Directory Structure**:
- `.claude/` 配下に `commands/`, `rules/`, `skills/`, `agents/`, `settings.json` を明示（v4.5.0 拡充）
- `docs/` 配下に `slides/`、`daily/` を明示

**(B) Section 2: Asset Placement Rules**:
- TDD Patterns に `.claude/tdd-patterns.log` 注記追加
- Subagent Persistent Memory の説明文拡充

**(C) Section 3: SSOT 3層アーキテクチャ（大幅変更）**:

v4.5.0 に追従し、情報層の方向を再構成:

```
情報層 1: docs/internal/（プロセス SSOT = What & Why）
    ↓ 参照
情報層 2: .claude/rules/, commands/, hooks/, agents/, skills/（実行ルール = How）
    ↓ 要約
情報層 3: CHEATSHEET.md（クイックリファレンス、独自情報を持たない）

CLAUDE.md: ブートストラップ（プロジェクト憲法、参照ハブ）
```

テーブル形式 → ASCII 矢印図に変更。
Permission Layer との混同防止注記を維持。

**(D) Section 4: File Naming Conventions**: 差分なし

**影式固有の保持**:
- `src/kage_shiki/` パッケージ構造（汎用の `backend/frontend/` は不採用）
- `docs/memos/middle-draft/` の記載
- `tests/` の説明に `pytest` を明示

---

#### 2.2.2 01_REQUIREMENT_MANAGEMENT.md — MAGI + /clarify 統合

**変更種別**: 更新（中規模）

**具体的な変更内容**:

1. **Section E: Perspective Check の MAGI 化**:
   - `Affirmative / Critical / Mediator` → `MELCHIOR / BALTHASAR / CASPAR`
   - `「Critical Agent」` → `BALTHASAR（批判者）`
   - `/magi` スキル参照を追加: `複雑な判断には /magi スキルの活用を推奨`

2. **Section F: Clarification 新設**:
   ```markdown
   ### F. Clarification（文書精緻化）

   仕様書ドラフト完成後に `/clarify` で曖昧さ・矛盾・欠落を検出する。
   「適切に」「必要に応じて」等の曖昧修飾語は数値・条件に置換すること。
   詳細: `.claude/rules/planning-quality-guideline.md`
   ```

3. **Section 2: Definition of Ready の更新**:
   `解釈の揺れがない` → `解釈の揺れがない。/clarify で精緻化済みであること`

**影式固有考慮**: なし

---

#### 2.2.3 02_DEVELOPMENT_FLOW.md — MAGI + /clarify + R-5/R-6 参照

**変更種別**: 更新（中規模）

**具体的な変更内容**:

1. **Phase 1 冒頭文**: `Phase 1 (設計) および Phase 2 (実装)` → `Phase 1 (設計)、Phase 2 (実装)、および Phase 3 (定期監査)`
2. **Phase 1 AoT セクション**:
   - `AoT フレームワークとの連携` → `MAGI System（構造化意思決定）との連携`
   - `/magi` スキル参照追加
   - `Three Agents Debate` → `MAGI Debate`
3. **Phase 1 文書精緻化（/clarify）サブセクション新設**
4. **Phase 2 TDD 内省**: `src/` 配下のファイル変更検知とドキュメント同期フラグ設定の記述追加
5. **Phase 3 権限等級**: `詳細は .claude/rules/permission-levels.md を参照` を追加

**影式固有の保持**:
- テスト環境 Note（pytest）
- Wave-Based Development セクション全体
- Quality Rules Integration セクション全体
- Advanced Workflows セクション全体

---

#### 2.2.4 03_QUALITY_STANDARDS.md — 変更なし

Section 1-5 は差分なし。影式固有の Section 6（Python Coding Conventions）と Section 7（Building Defect Prevention）を保持。承認済み判断 #4 に基づく。

**注意**: Section 7 の R-5/R-6 への言及がある場合は、R-12/R-13 に更新する。

---

#### 2.2.5 04_RELEASE_OPS.md — デプロイ基準更新

**変更種別**: 更新（小規模）

**具体的な変更内容**:
1. Section 1 Deployment Criteria: `All Tests Green` を独立チェック項目として分離
2. Section 1: `Quality Gate Passed` を汎用化（「プロジェクトが定めるリリース品質基準」）
3. Section 3: Post-Mortem 記録先の表現整理

**影式固有の保持**: HTML コメント（`<!-- Phase 2b 以降でパッケージング方法... -->`）

---

#### 2.2.6 05_MCP_INTEGRATION.md — 微修正

**変更種別**: 更新（軽微）

**具体的な変更内容**:
1. MCP サーバー表記: `Phase 2 以降で検討` → `Optional`（テンプレート汎用化に合わせる）

**影式固有の保持**: Phase 1 MVP Note（MCP 未導入）

---

#### 2.2.7 06_DECISION_MAKING.md — MAGI System 全面導入 + Reflection 新設

**変更種別**: 更新（最大規模）

**具体的な変更内容**:

1. **タイトル変更**: `Three Agents Model` → `MAGI System / "Three Agents" Model`
2. **Section 1 Agent 名**: Affirmative → MELCHIOR、Critical → BALTHASAR、Mediator → CASPAR（旧名をカッコ内に併記）
3. **Section 2 Execution Flow**: 全ステップで MAGI 名称に変更
4. **Section 3 Output Format**: ラベルを MAGI 名称に変更
5. **Section 5 AoT**:
   - 5.4 ワークフロー名: `AoT + Three Agents` → `AoT + MAGI`
   - Step 1-3: MAGI 名称に変更
   - **Step 4 Reflection 新設**: 全員で結論を検証（1回限り）
   - 旧 Step 4 → 新 Step 5（AoT Synthesis）
   - 5.5 出力フォーマット: MAGI ラベル + Reflection セクション追加
6. **Section 6 Reflection 新設**:
   - 6.1 目的: 致命的な見落としの最終確認
   - 6.2 ルール: 修正条件は致命的な見落としのみ、Bikeshedding 防止、回数制限 1 回
   - 6.3 出力フォーマット
   - 6.4 参照: Multi-Agent Reflexion (MAR) 論文

**影式固有考慮**: なし

---

#### 2.2.8 07_SECURITY_AND_AUTOMATION.md — Permission Layer 整理

**変更種別**: 更新（中規模）

**具体的な変更内容**:

1. **Section 2 Allow List**: `find` の v4.3.1 移動注記追加
2. **Section 2 Deny List**: B-2 Approval Required — Network を簡素化（`ping, nc` を削除）
3. **Section 3 Automation Workflow**: `SafeToAutoRun` → `Allow List に含まれる / 含まれない` に簡素化（v4.4.1 時に未反映だった項目を今回対応）
4. **Section 5 Stop Hook**: `docs/specs/green-state-definition.md` 参照追加
5. **Section 6 Recommended Security Tools**: Anthropic 公式ツール + 言語別脆弱性スキャン + CI/CD 統合例の 3 カテゴリに拡充（影式固有ツール列も保持）

**影式固有の保持**:
- Section 2: pytest/ruff 固有コマンドリスト、`pip install/uninstall`
- Section 5: PreToolUse の影式固有パス（`pyproject.toml`, `src/kage_shiki/`, `config/`）
- Section 6: 影式固有ツール列（ruff, pip-audit, safety, bandit）

---

#### 2.2.9 99_reference_generic.md — Phase 4 タグ追加

**変更種別**: 更新（軽微）

**具体的な変更内容**:
1. Phase 4 に `[RELEASE]` タグ追加

---

### 2.3 CLAUDE.md の変更方針

**変更種別**: 更新（中規模）

**具体的な変更内容**:

**(A) Hierarchy of Truth — Architecture 参照範囲**:
LAM v4.5.0 は `00-07` だが、影式は 08, 09 を含む `00〜09` を**維持**（前回と同じ判断）。

**(B) Context Management — 閾値維持**:
影式の 20% を維持。LAM の 10% は採用しない（承認済み判断 #3）。
残量 25% 条件も保持。

**(C) Context Management — git 注記微修正**:
`git commit / push は /ship を使用` → `git commit が必要なら /ship を使用`（v4.5.0 の表現に合わせる）

**(D) Memory Policy — 更新**:
1. セクション名: `MEMORY.md Policy` → `Memory Policy`（v4.4.1 で指摘済み、未反映だった項目を今回対応）
2. Layer 番号は影式固有として保持（可読性のため）
3. Auto Memory 説明の拡充: `ビルドコマンド、デバッグ知見、ワークフロー習慣など作業効率に関する学習` + MEMORY.md パス明示
4. Subagent Memory 説明の拡充: `.claude/agents/` からの指示、「Claude Code の公式フロントマター機能ではない」と明記
5. Knowledge Layer 参照先: `docs/internal/05_MCP_INTEGRATION.md Section 6` → `docs/artifacts/knowledge/README.md`（ファイルが存在しない場合は `docs/artifacts/knowledge/` に留める）

**(E) Execution Modes — /auditing 表現微修正**:
`PM級修正禁止（PG/SE級は許可）` → `PG/SE修正可、PM指摘のみ`（v4.5.0 表現に合わせる）

**影式固有の保持**:
- Identity: `影式 (Kage-Shiki)` の名称と説明文
- Project Scale: `Medium`
- Project Overview: 技術スタックテーブル全体
- Hierarchy of Truth: `SSOT: 00〜09`
- References: `docs/memos/middle-draft/` の行、`docs/slides/index.html`（将来作成予定）
- Context Management: 閾値 20%、残量 25% 条件
- Initial Instruction: プロジェクト名修飾

---

### 2.4 CHEATSHEET.md の変更方針

**変更種別**: 更新（中規模）

**具体的な変更内容**:

**(A) ディレクトリ構造**:
- `CLAUDE.md` 説明: `憲法（コア原則 + 技術スタック）` → `憲法（コア原則）`（技術スタックは Project Overview であり、コア原則ではない）
- `.claude/` 配下に `agent-memory/` 記載を追加（影式固有保持項目）
- `logs/` 説明: `permission.log, loop-*.txt` → `permission.log, loop-*.txt（実行時生成）`

**(B) Rules ファイル一覧**:
- `decision-making.md` 説明: `意思決定プロトコル` → `意思決定プロトコル（MAGI System）`
- `code-quality-guideline.md` 行を追加
- `planning-quality-guideline.md` 行を追加

**(C) セッション管理コマンド**:
- `/quick-save` コスト: `3-4%` → `3-5%`
- `/quick-load` コスト: `2-3%` → `1-2%`

**(D) サブエージェント**:
- Memory 列を追加（v4.4.1 で指摘済み、未反映だった項目を今回対応）:
  - `code-reviewer`: `auto`
  - その他: `-`

**(E) スキル**:
- `lam-orchestrate` 説明: `タスク分解・並列実行 + 構造化思考（AoT + Three Agents）` → `タスク分解・並列実行 + /magi 統合`
- `/magi` 新規追加: 構造化意思決定（AoT + MAGI System + Reflection）
- `/clarify` 新規追加: 文書精緻化（曖昧さ・矛盾・欠落検出）
- `ui-design-guide` 新規追加: UI/UX 設計チェックリスト

**(F) ワークフローコマンド**:
- `/full-review` 説明: `並列監査 + 全修正 + 検証（4エージェント、一気通貫）` → `並列監査 + 全修正 + 検証（一気通貫）`
- `/wave-plan`: `[N]` 引数追加
- `/retro`: `[wave|phase]` 引数明示

**(G) 状態管理**:
- `docs/artifacts/knowledge/` 説明: `retro Step 4 の知見保存先` → `プロジェクト知見の構造化蓄積（/retro 経由）`
- `.claude/agent-memory/` 説明: `Subagent Persistent Memory` → `Subagent の自動学習記録`

**(H) 参照ドキュメント (SSOT)**:
- `06_DECISION_MAKING.md` 説明: `意思決定（3 Agents + AoT）` → `意思決定（MAGI System + AoT + Reflection）`
- `99_reference_generic.md` を追加（v4.4.1 で指摘済み、未反映だった項目を今回対応）

**(I) AoT クイックガイド → /magi クイックガイド**:
- セクション名: `AoT（Atom of Thought）クイックガイド` → `/magi（構造化意思決定）クイックガイド`
- MAGI System の役割説明を追加（MELCHIOR/BALTHASAR/CASPAR）
- ワークフロー更新:
  ```
  0. Decomposition: 議題を Atom に分解
  1-3. MAGI Debate: 各 Atom で MELCHIOR/BALTHASAR/CASPAR 合議
  4. Reflection: 結論の致命的見落としを検証（1回限り）
  5. Synthesis: 統合結論 → 実装
  ```

**(J) /clarify クイックガイド 新設**:
```markdown
## /clarify（文書精緻化）クイックガイド

**いつ使う？**
- 仕様書・設計書のドラフト完成後
- 文書間の横断チェック

**使い方**
1. 対象文書を指定して `/clarify` を実行
2. 曖昧さ・矛盾・欠落の指摘を確認
3. 修正を適用
```

**影式固有の保持**:
- プロジェクト技術スタックセクション全体
- `building-checklist.md` の Rules 一覧記載
- 日常ワークフロー 7 パターン
- クイックリファレンスの `/ship`、設計中間文書
- `docs/memos/middle-draft/` のディレクトリ構造記載
- 08_SESSION_MANAGEMENT.md, 09_SUBAGENT_STRATEGY.md の参照ドキュメント記載

---

## 3. 影式固有保持項目のチェックリスト

Phase 1 完了時に以下が破壊されていないことを確認する。

### .claude/rules/

- [ ] `core-identity.md`: Subagent 委任判断テーブルが存在する
- [ ] `core-identity.md`: コンテキスト節約原則（3 項目）が存在する
- [ ] `phase-rules.md`: `影式固有: Phase 完了判定（L-4 由来）`が存在する
- [ ] `phase-rules.md`: `影式固有: 修正後の再検証義務（A-3 由来）`が存在する
- [ ] `phase-rules.md`: `影式固有: 監査レポート完了条件`が存在する
- [ ] `phase-rules.md`: `AUDITING ルール識別子（A-1〜A-4）`が存在する
- [ ] `phase-rules.md`: Green State 5 条件テーブル（G1-G5）が存在する
- [ ] `building-checklist.md`: R-2, R-3, R-7〜R-11, S-2 が存在する（R-12, R-13 にリナンバ済み）
- [ ] `security-commands.md`: Python カテゴリ（Allow List）が存在する
- [ ] `security-commands.md`: `pip show` が存在する
- [ ] `security-commands.md`: ※1 注記（二段構成）が存在する
- [ ] `permission-levels.md`: SSOT 宣言（冒頭）が存在する
- [ ] `permission-levels.md`: 影式固有パス（`docs/internal/`, `pyproject.toml`, `src/kage_shiki/`, `tests/`, `config/`）が存在する
- [ ] `permission-levels.md`: 影式固有例（`config.toml テンプレート`, `docs/internal/`, `tests/`）が存在する
- [ ] `permission-levels.md`: 相互参照（phase-rules.md, core-identity.md, security-commands.md）が存在する
- [ ] `auto-generated/README.md`: 仕様書パスが `docs/specs/lam/` プレフィックス付きである
- [ ] `auto-generated/trust-model.md`: tdd-patterns.log の形式セクションが存在する
- [ ] `auto-generated/trust-model.md`: 仕様書パスが `docs/specs/lam/` プレフィックス付きである
- [ ] `auto-generated/trust-model.md`: パターン詳細記録先（`docs/artifacts/tdd-patterns/`）が存在する

### docs/internal/

- [ ] `00_PROJECT_STRUCTURE.md`: `src/kage_shiki/` パッケージ構造が存在する
- [ ] `00_PROJECT_STRUCTURE.md`: `docs/memos/middle-draft/` が記載されている
- [ ] `02_DEVELOPMENT_FLOW.md`: テスト環境 Note（pytest）が存在する
- [ ] `02_DEVELOPMENT_FLOW.md`: Wave-Based Development セクションが存在する
- [ ] `02_DEVELOPMENT_FLOW.md`: Quality Rules Integration セクションが存在する
- [ ] `02_DEVELOPMENT_FLOW.md`: Advanced Workflows セクションが存在する
- [ ] `03_QUALITY_STANDARDS.md`: Section 6（Python Coding Conventions）が存在する
- [ ] `03_QUALITY_STANDARDS.md`: Section 7（Building Defect Prevention）が存在する
- [ ] `05_MCP_INTEGRATION.md`: Phase 1 MVP Note が存在する
- [ ] `07_SECURITY_AND_AUTOMATION.md`: pytest/ruff 固有コマンドリストが存在する
- [ ] `07_SECURITY_AND_AUTOMATION.md`: 影式固有パス（PreToolUse）が存在する
- [ ] `07_SECURITY_AND_AUTOMATION.md`: 影式固有ツール列（Section 6）が存在する

### CLAUDE.md

- [ ] Identity に `影式 (Kage-Shiki)` が明記されている
- [ ] Project Overview（技術スタックテーブル）が存在する
- [ ] Project Scale が `Medium` である
- [ ] Hierarchy of Truth の Architecture 参照範囲が `00〜09` である
- [ ] References に `docs/memos/middle-draft/` が存在する
- [ ] Context Management の閾値が 20% である
- [ ] Context Management に残量 25% 条件が存在する
- [ ] Initial Instruction にプロジェクト名が含まれている

### CHEATSHEET.md

- [ ] プロジェクト技術スタックセクションが存在する
- [ ] `building-checklist.md` が Rules 一覧に記載されている
- [ ] 日常ワークフロー 7 パターンが存在する
- [ ] クイックリファレンスに `/ship` が存在する
- [ ] クイックリファレンスに `docs/memos/middle-draft/` が存在する
- [ ] ディレクトリ構造に `docs/memos/middle-draft/` が存在する
- [ ] 参照ドキュメントに `08_SESSION_MANAGEMENT.md` が存在する
- [ ] 参照ドキュメントに `09_SUBAGENT_STRATEGY.md` が存在する

---

## 4. 検証チェックリスト（Phase 1 完了条件）

### 4.1 MAGI System 移行の完全性

- [ ] `decision-making.md`: MAGI 名称 + Reflection が適用されている
- [ ] `phase-rules.md` AUDITING: `MAGI System` に変更されている
- [ ] `06_DECISION_MAKING.md`: Section 1-6 全て MAGI 化 + Reflection 新設
- [ ] `01_REQUIREMENT_MANAGEMENT.md`: Perspective Check が MAGI 化
- [ ] `02_DEVELOPMENT_FLOW.md`: AoT → MAGI System 連携に変更
- [ ] `CHEATSHEET.md`: /magi クイックガイドに変更
- [ ] 旧名称（Three Agents, Affirmative, Critical, Mediator）が単独で出現しない（MAGI 名称のカッコ内併記は許可）

### 4.2 新規ファイルの追加

- [ ] `code-quality-guideline.md` が `.claude/rules/` に存在する
- [ ] `planning-quality-guideline.md` が `.claude/rules/` に存在する

### 4.3 R-5/R-6 リナンバリングの整合性

- [ ] `building-checklist.md` に R-12, R-13 が存在する（旧 R-5, R-6）
- [ ] `building-checklist.md` に R-5, R-6 が存在しない
- [ ] `phase-rules.md` BUILDING に LAM の R-5, R-6 が存在する
- [ ] `phase-rules.md` の参照コメントが `R-12, R-13` に更新されている
- [ ] `03_QUALITY_STANDARDS.md` Section 7 の R-5/R-6 参照が R-12/R-13 に更新されている（該当する場合）

### 4.4 SSOT 3 層再構成

- [ ] `00_PROJECT_STRUCTURE.md` Section 3 が v4.5.0 の 3 層構成になっている
- [ ] CLAUDE.md の Hierarchy of Truth と 00 の SSOT 3 層が矛盾しない

### 4.5 v4.4.1 未反映項目の対応

- [ ] CHEATSHEET.md: サブエージェントに Memory 列が追加されている
- [ ] CHEATSHEET.md: 参照ドキュメントに `99_reference_generic.md` が追加されている
- [ ] CLAUDE.md: Memory Policy セクション名が `Memory Policy` になっている
- [ ] `07_SECURITY_AND_AUTOMATION.md` Section 3: `SafeToAutoRun` が `Allow List` 判定に変更されている

### 4.6 影式固有保持（セクション 3 のチェックリスト全項目パス）

- [ ] セクション 3 の全チェック項目が確認済み

### 4.7 内部整合性

- [ ] 全ファイルで `docs/specs/lam/` パスが統一されている（影式固有）
- [ ] `find` が Allow List に存在しない（全ファイルで ask に移動）
- [ ] Green State 条件が phase-rules.md と code-quality-guideline.md で矛盾しない

---

## 5. リスクと対策

| # | リスク | 影響度 | 確率 | 対策 |
|---|-------|-------|------|------|
| 1 | MAGI 名称の適用漏れ（旧名称の残存） | 中 | 中 | Phase 1 完了時に全ファイルで `Affirmative`, `Critical`（Agent 名として単独出現するもの）, `Three Agents` を grep し、残存がないことを確認 |
| 2 | R-5/R-6 リナンバリングの参照漏れ | 中 | 中 | `R-5`, `R-6` を grep し、building-checklist.md 以外に旧番号への参照がないことを確認。03_QS Section 7 も対象 |
| 3 | SSOT 3 層変更と CLAUDE.md Hierarchy of Truth の矛盾 | 高 | 低 | CLAUDE.md の Hierarchy of Truth は `docs/internal/` を User Intent に次ぐ第 2 位としており、v4.5.0 の「docs/internal/ が情報層 1」と整合。矛盾リスクは低い |
| 4 | code-quality-guideline.md の閾値と影式既存基準の競合 | 低 | 低 | building-checklist.md は「何をテストすべきか」、code-quality-guideline.md は「Issue の重要度分類」であり、責務が異なる。競合なし |
| 5 | /clarify, /magi スキルの参照先が Phase 1 時点で未存在 | 低 | 確定 | Phase 1 ではドキュメント内の参照記述のみ。スキル実体は Phase 2 で導入。参照が壊れることは許容する（コマンドが見つからないだけで、ドキュメントとしては正しい） |
| 6 | planning-quality-guideline.md の RFC 2119 キーワードが影式既存仕様書に遡及適用を要求する可能性 | 中 | 低 | Phase 1 では「新規仕様書から適用」とし、既存仕様書への遡及適用は PM 級判断として別途扱う |

---

## 移行後の想定ファイル構成

```
.claude/rules/
├── core-identity.md              ← 変更なし
├── decision-making.md            ← MAGI System + Reflection
├── phase-rules.md                ← 品質基準参照 + R-5/R-6 + Green State 再定義 + 影式固有保持
├── security-commands.md          ← find 破壊パターン deny + 説明文 + 影式固有保持
├── permission-levels.md          ← SE/PM 説明文 + 注記更新 + 影式固有保持
├── upstream-first.md             ← 確認対象明示 + WebFetch 注意事項
├── building-checklist.md         ← R-12/R-13 リナンバ（影式固有保持）
├── test-result-output.md         ← 構造改善 + 言語別拡充
├── code-quality-guideline.md     ← 新規（LAM v4.5.0）
├── planning-quality-guideline.md ← 新規（LAM v4.5.0）
├── auto-generated/
│   ├── README.md                 ← 冒頭説明文追加
│   └── trust-model.md            ← フロー図微修正 + 影式固有保持

docs/internal/
├── 00_PROJECT_STRUCTURE.md       ← SSOT 3層再構成 + .claude/ 拡充
├── 01_REQUIREMENT_MANAGEMENT.md  ← MAGI + /clarify 統合
├── 02_DEVELOPMENT_FLOW.md        ← MAGI + /clarify + R-5/R-6 参照
├── 03_QUALITY_STANDARDS.md       ← 変更なし（Section 6/7 保持）
├── 04_RELEASE_OPS.md             ← デプロイ基準更新
├── 05_MCP_INTEGRATION.md         ← 微修正
├── 06_DECISION_MAKING.md         ← MAGI 全面導入 + Reflection 新設
├── 07_SECURITY_AND_AUTOMATION.md ← Permission Layer 整理 + Section 6 拡充
├── 99_reference_generic.md       ← Phase 4 タグ追加

CLAUDE.md                         ← Memory Policy + SSOT 追従 + v4.4.1 未反映対応
CHEATSHEET.md                     ← MAGI + /magi + /clarify + v4.4.1 未反映対応
```
