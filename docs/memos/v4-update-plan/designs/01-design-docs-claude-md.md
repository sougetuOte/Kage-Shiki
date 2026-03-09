# 設計: docs/internal / CLAUDE.md / CHEATSHEET.md 移行

**作成日**: 2026-03-10
**ステータス**: レビュー待ち
**前提資料**: `specs/00-diff-docs-internal.md`, `specs/00-diff-claude-md.md`, `000-index.md`

---

## 概要

LAM 4.0.1 への移行において、プロジェクトの「憲法」層（CLAUDE.md）、「クイックリファレンス」層（CHEATSHEET.md）、「プロセス SSOT」層（docs/internal/）の 3 層をどうマージするかの設計判断を記録する。

基本方針は `000-index.md` Section 4 の衝突解決ポリシーに従い、**Template-First**（LAM 4.0.1 をベースに影式固有カスタマイズを上乗せ）で進める。

---

## 判断1: CLAUDE.md のマージ戦略

### 現状の差分

| 項目 | 影式現行 | LAM 4.0.1 |
|------|---------|-----------|
| Identity | `影式 (Kage-Shiki)` 明記 | `本プロジェクト`（汎用） |
| Project Scale | Medium | Medium to Large |
| Project Overview | 技術スタック表あり | なし（汎用化で削除） |
| Execution Modes AUDITING | 修正禁止（指摘のみ） | 修正禁止（指摘のみ）※ phase-rules.md 側で緩和 |
| References | `docs/memos/middle-draft/` 行あり | なし |
| Initial Instruction | `影式 (Kage-Shiki) プロジェクトの` 修飾あり | プロジェクト名なし |

### 選択肢

| 選択肢 | 内容 | メリット | デメリット |
|--------|------|---------|-----------|
| A. LAM 4.0.1 ベース + 影式上乗せ | LAM 4.0.1 を土台に、Identity/Project Overview/References を手動追加 | テンプレートの構造改善を取り込める。将来の LAM アップデートとの差分が最小 | 手動マージの作業量 |
| B. 影式現行ベース + LAM 差分パッチ | 影式現行を維持し、LAM 4.0.1 の変更点のみ反映 | 影式固有情報が確実に保持される | テンプレートの構造的改善を見逃しやすい |
| C. 完全書き直し | 両方を参照しつつ新規作成 | 最適な構造にできる | 作業量最大。ミスのリスク |

### 推奨案: A（LAM 4.0.1 ベース + 影式上乗せ）

#### 具体的な変更内容

1. **Identity**: LAM 4.0.1 の汎用文をベースに、影式プロジェクト名と説明を復元
   ```
   あなたは **影式 (Kage-Shiki)** プロジェクトの **"Living Architect"...
   ```

2. **Project Scale**: `Medium` を維持
   - 理由: 影式は Python 単一言語、1 開発者、モジュール数 6。`Medium to Large` は過大
   - LAM 4.0.1 の `Medium to Large` はテンプレートのデフォルト値であり、プロジェクト実態に合わせて変更すべき項目

3. **Project Overview**: Identity セクション直後に復元
   - 技術スタック表（Python 3.12+, tkinter, pystray, anthropic, SQLite + FTS5, TOML, pytest）
   - LAM 4.0.1 にはこのセクション自体がないため、影式固有セクションとして追加

4. **Execution Modes テーブル**: AUDITING 列のガードレールを更新
   - 現行: `修正禁止（指摘のみ）`
   - 変更後: `PM級修正禁止（PG/SE級は許可）`
   - 理由: phase-rules.md の v4.0.0 変更と整合させる

5. **References**: 設計文書行（`docs/memos/middle-draft/`）を維持
   - 影式では実際に使用中のディレクトリ

6. **Initial Instruction**: 影式プロジェクト名を復元

7. **Active Migration Notice**: CLAUDE.md 末尾（Initial Instruction の後）に配置
   - 移行完了後に削除するセクション
   - 既に追加済み（Phase 0 で実施済み）

### 変更しない項目

- Hierarchy of Truth: 差分なし
- Core Principles: 差分なし
- Context Management: 差分なし
- MEMORY.md Policy: 差分なし

---

## 判断2: CHEATSHEET.md のマージ戦略

### 現状の差分サマリー

| カテゴリ | 影式にあり LAM にない | LAM にあり影式にない |
|---------|---------------------|---------------------|
| セクション | 技術スタック, 日常ワークフロー, `/ship` QR, 設計中間文書 QR | 権限等級(PG/SE/PM), 補助コマンド分離, Atom テーブル, `/release`, セッション開始 QR, ADR/Rules QR |
| 構造 | ワークフローコマンド（一括） | ワークフローコマンド + 補助コマンド（分離） |
| Rules一覧 | building-checklist, spec-sync, audit-fix-policy | permission-levels（代替） |

### 選択肢

| 選択肢 | 内容 | メリット | デメリット |
|--------|------|---------|-----------|
| A. LAM 4.0.1 ベース + 影式固有セクション追加 | LAM 構造を採用し、影式固有を手動追加 | 権限等級・コマンド分離の構造改善を取り込める | 日常ワークフローの再配置が必要 |
| B. 影式現行ベース + LAM 新セクション追加 | 影式構造を維持し、権限等級等を追加 | 既存の日常ワークフローが確実に保持 | Rules一覧の整理が中途半端 |

### 推奨案: A（LAM 4.0.1 ベース + 影式固有セクション追加）

#### 具体的な変更内容

1. **タイトル**: `影式 (Kage-Shiki) チートシート` を維持（テンプレートの汎用名は不採用）

2. **はじめに**: LAM 4.0.1 の改善を取り込みつつ、影式に不要な QUICKSTART.md 参照は除外
   - 「LAM の設定は自動で読み込まれる」の説明は有用なため採用

3. **プロジェクト技術スタック**: 影式固有セクションとして維持（ディレクトリ構造の直前に配置）

4. **ディレクトリ構造**: LAM 4.0.1 を採用
   - `hooks/`, `logs/` ディレクトリを追加
   - CLAUDE.md 説明を `憲法（コア原則 + 技術スタック）` に維持（影式は技術スタックを含むため）
   - `docs/memos/middle-draft/` 行を維持

5. **権限等級（PG/SE/PM）セクション**: LAM 4.0.1 から新規追加
   - PreToolUse hook の説明を含む
   - フック分類の誤判定率計測手順を含む

6. **Rules ファイル一覧**: LAM 4.0.1 を採用しつつ影式固有ルールを追加
   ```
   | permission-levels.md | 権限等級分類基準（PG/SE/PM）v4.0.0 新規 |
   | building-checklist.md | BUILDING 品質チェックリスト（R-1〜R-11）影式固有 |
   | spec-sync.md | 仕様・実装同期ルール（S-2）影式固有 |
   | audit-fix-policy.md | 監査修正ポリシー（A-1〜A-4）影式固有 |
   ```
   - 注: spec-sync.md は S-2 のみ残留（S-1/S-3/S-4 は phase-rules.md に統合）
   - audit-fix-policy.md は影式で実証済みのため保持（PG/SE/PM との併用）

7. **フェーズコマンド**: AUDITING の禁止事項を `PM級の修正禁止（PG/SE級は許可）` に更新

8. **コマンド分類の再編**: LAM 4.0.1 の「ワークフローコマンド」「補助コマンド」分離を採用
   - ワークフローコマンド: `/ship`, `/full-review`, `/release`
   - 補助コマンド: `/focus`, `/daily`, `/adr-create`, `/security-review`, `/impact-analysis`
   - 影式固有: `/wave-plan`, `/retro` を補助コマンドに追加

9. **日常ワークフロー**: 影式固有セクションとして維持
   - Wave ベースの作業フロー記述は影式で実運用中
   - LAM 4.0.1 で削除されたのはテンプレート汎用化のためであり、影式では有用

10. **AoT クイックガイド**: LAM 4.0.1 の Atom テーブル形式を追加

11. **クイックリファレンス**: 両方の項目をマージ
    - 維持: `/ship`, 設計中間文書
    - 追加: セッション開始、ADR、Rules

---

## 判断3: docs/internal/ のマージ戦略

### 3-1: 00_PROJECT_STRUCTURE.md

#### 変更点

| 項目 | 方針 |
|------|------|
| Section 1: Directory Structure | **影式の kage_shiki パッケージ構造を維持**。LAM 4.0.1 の `backend/frontend/` は汎用テンプレートであり不採用。`.claude/` 配下に `hooks/`, `logs/`, `settings.json` を追加 |
| Section 2C: ADR Naming | → 判断4 で決定 |
| Section 3: SSOT 3層アーキテクチャ | **LAM 4.0.1 から新規追加**。影式は暗黙的に運用していた構造を明文化。hooks/ を含む形で追加 |
| Section 3→4: File Naming Conventions | セクション番号を 3→4 に変更。JS/TS の例示は不要（影式は Python のみ） |

#### 具体的なマージ結果イメージ

```
Section 1: Directory Structure — 影式固有の kage_shiki 構造 + .claude/ 配下拡充
Section 2: Asset Placement Rules — 現行維持 + ADR命名規則変更（判断4次第）
Section 3: SSOT 3層アーキテクチャ — LAM 4.0.1 から追加
Section 4: File Naming Conventions — 現行維持（Python のみ）
```

### 3-2: 02_DEVELOPMENT_FLOW.md

#### 変更点

| 項目 | 方針 |
|------|------|
| Dependency Traversal | `grep_search` → `Grep` / `Glob` に更新（LAM 4.0.1 採用） |
| テスト環境 Note | **影式固有の pytest Note を維持** |
| Step 5: walkthrough パス | `walkthrough.md` → `docs/memos/walkthrough-<feature>.md` に更新（LAM 4.0.1 採用） |
| Automated TDD Introspection | **LAM 4.0.1 から新規追加**。Phase 2 セクション末尾に配置 |
| 権限等級に基づく修正制御 | **LAM 4.0.1 から新規追加**。Phase 3 セクション末尾に配置 |
| Wave-Based Development | **影式固有セクションを維持**（Wave 実績サマリー含む） |
| Advanced Workflows | **影式固有セクションを維持** |
| Quality Rules Integration | **影式固有セクションを維持**。ルール参照先テーブルは spec-sync.md の縮小（S-2 のみ）と audit-fix-policy.md の保持を反映して更新 |

#### 保護すべき影式固有セクション

以下は LAM テンプレートに存在しないが、影式の実運用で検証済みであり削除不可:

- Wave 実績サマリー（Phase 1 MVP の記録）
- Quality Rules Integration（R-1〜R-6, S-1〜S-4, A-1〜A-4 のマッピング）
- Advanced Workflows（`/wave-plan`, `/retro` を含む）

### 3-3: 03_QUALITY_STANDARDS.md

#### 方針: 影式固有セクションの保護のみ

LAM 4.0.1 との差分は Section 6（Python Coding Conventions）と Section 7（Building Defect Prevention）のみ。これらは影式固有であり、LAM テンプレートには存在しない。

- **変更なし**: Section 1〜5（設計原則〜コード明確性）は差分がないため変更不要
- **保護**: Section 6（Python 規約）、Section 7（R-1〜R-6 不具合防止ルール）は影式固有として維持
- **確認のみ**: Section 8（Technology Trend Awareness）は差分なし

### 3-4: 07_SECURITY_AND_AUTOMATION.md

#### 変更点

| 項目 | 方針 |
|------|------|
| Section 1: Core Principle | 差分なし。変更不要 |
| Section 2: Command Lists | **影式固有のコマンドを維持**（pytest 詳細オプション、ruff、pip、python -m kage_shiki）。LAM 4.0.1 の汎用コマンド（npm test, go test 等）は不採用 |
| Section 3-4: Automation/Emergency | 差分なし。変更不要 |
| Section 5: Hooks-Based Permission System | **LAM 4.0.1 から新規追加**。権限等級、PostToolUse、Stop hook の説明 |
| Section 6: Recommended Security Tools | **LAM 4.0.1 から新規追加**。影式で使用可能なツール（pip-audit, safety）を含む |

#### Section 2 のマージ詳細

影式現行の Allow/Deny List を維持し、LAM 4.0.1 の Layer 0/1/2 モデルへの参照を Section 5 で追加する形にする。影式の Linting (Read/Write) と Package Install カテゴリは LAM テンプレートには存在しないが、実運用で必要なため維持。

### 3-5: その他のファイル

| ファイル | 方針 |
|---------|------|
| 01_REQUIREMENT_MANAGEMENT.md | 差分なし。変更不要 |
| 04_RELEASE_OPS.md | 差分なし。影式固有コメント（PyInstaller 検討メモ）を維持 |
| 05_MCP_INTEGRATION.md | 差分なし。影式固有の Phase 1 MVP Note を維持 |
| 06_DECISION_MAKING.md | 差分なし。変更不要 |
| 99_reference_generic.md | フェーズモードタグ（`[PLANNING]` 等）を追加。Starter Kit のファイル名を明示化。軽微な変更 |
| 08_SESSION_MANAGEMENT.md | **影式独自ファイル**。変更不要（LAM テンプレートに対応なし） |
| 09_SUBAGENT_STRATEGY.md | **影式独自ファイル**。変更不要（LAM テンプレートに対応なし） |

---

## 判断4: ADR 命名規則の変更

### 現状

- **影式現行**: `YYYY-MM-DD_{decision_title}.md`（日付方式）
- **LAM 4.0.1**: `NNNN-kebab-case-title.md`（連番方式）
- **既存 ADR**: なし（`docs/adr/` ディレクトリ自体が未作成）

### 選択肢

| 選択肢 | 内容 | メリット | デメリット |
|--------|------|---------|-----------|
| A. 連番方式に変更 | LAM 4.0.1 を採用。`NNNN-kebab-case-title.md` | テンプレート準拠。`ls` での自然な並び順 | 日付が一見してわからない |
| B. 日付方式を維持 | 影式現行のまま | 作成日が明白 | テンプレートからの乖離 |
| C. ハイブリッド | `NNNN-YYYY-MM-DD-title.md` | 両方の利点 | 冗長。どちらのテンプレートとも異なる |

### 推奨案: A（連番方式に変更）

理由:
1. **既存 ADR がゼロ**: 移行コストがない。既存ファイルのリネームが不要
2. **テンプレート準拠**: 将来の LAM アップデートとの互換性を維持
3. **ADR 内に日付を記載**: ADR テンプレート（`adr-template` スキル）は本文内に日付フィールドを持つため、ファイル名に日付がなくても問題ない
4. **連番の利点**: ADR 間の参照が `Supersedes: 0003` のように簡潔になる

#### 移行作業

- `00_PROJECT_STRUCTURE.md` Section 2C の命名規則を更新
- `adr-template` スキルの出力ファイル名パターンを確認（Phase 2 で対応）

---

## 判断5: Green State 定義の影式版

### LAM 4.0.1 の Green State 5条件

LAM 4.0.1 (`green-state-definition.md`) は以下の 5 条件を定義:

1. テスト全パス
2. lint エラーゼロ
3. 対応可能 Issue ゼロ
4. 仕様差分ゼロ
5. セキュリティチェック通過

### 影式版の具体化

| 条件 | ID | 判定コマンド | 判定基準 | 備考 |
|------|:--:|:------------|:---------|:-----|
| テスト全パス | G1 | `pytest tests/ -v --tb=short` | 終了コード 0、FAILED 0 件 | 現在 722 件。全件 PASSED であること |
| lint エラーゼロ | G2 | `ruff check src/ tests/` | 終了コード 0、違反 0 件 | `ruff format --check` は G2 に含めない（フォーマットは PG級自動修正可） |
| 対応可能 Issue ゼロ | G3 | 監査レポートの手動確認 | Critical/Warning のうち「対応可能」と判定されたものが 0 件 | audit-fix-policy A-1/A-2 に基づく。自動化困難なため手動判定 |
| 仕様差分ゼロ | G4 | `docs/specs/` と実装の手動照合 | spec-sync S-1 に基づく差分がないこと | 自動化困難。`/full-review` の quality-auditor が検出した仕様ドリフトが 0 件であること |
| セキュリティチェック通過 | G5 | `pip-audit --desc` | 終了コード 0、脆弱性 0 件 | pip-audit 未導入の場合は `pip list --outdated` で代替（MVP） |

### MVP vs 完全実装

| 項目 | MVP（Phase 1-2 移行時） | 完全実装（Phase 3 hooks 導入後） |
|------|----------------------|-------------------------------|
| G1 | 手動で `pytest` 実行、結果を目視確認 | Stop hook が自動判定 |
| G2 | 手動で `ruff check` 実行、結果を目視確認 | Stop hook が自動判定 |
| G3 | `/full-review` レポートを目視確認 | Stop hook が監査レポートを解析 |
| G4 | `/full-review` の quality-auditor 結果を目視確認 | PostToolUse hook + doc-sync-flag で自動検出 |
| G5 | 手動で `pip-audit` 実行（未導入なら skip） | Stop hook が自動判定 |
| 統合判定 | `/full-review` 実行後にチェックリストで手動確認 | Stop hook が 5 条件を自動評価し、全パスで自律ループ停止 |

### `/full-review` との連携

`/full-review` コマンド（Phase 2 で更新）が Green State チェックを統合:

```
/full-review 実行
  → 4 エージェント並列監査
  → 修正（PG/SE級は自動、PM級は指摘のみ）
  → Green State チェック（G1〜G5）
  → 全条件パス → 完了報告
  → 未パス → 対応可能なら修正ループ、不可なら理由を報告
```

### Green State 定義ファイルの配置

- `docs/specs/green-state-definition.md` として影式版を配置（LAM 4.0.1 のテンプレートをベースに影式のコマンド・基準を記入）
- Phase 2 の作業項目に含める

---

## 変更影響サマリー

### Phase 1 での変更ファイル一覧

| ファイル | 変更種別 | 影響度 |
|---------|---------|--------|
| `CLAUDE.md` | 更新（Execution Modes テーブル修正） | 低 |
| `CHEATSHEET.md` | 大幅更新（権限等級追加、コマンド再編、日常ワークフロー維持） | 中 |
| `docs/internal/00_PROJECT_STRUCTURE.md` | 更新（SSOT 3層追加、.claude/ 拡充、ADR命名変更） | 中 |
| `docs/internal/02_DEVELOPMENT_FLOW.md` | 更新（TDD Introspection追加、ツール名更新、権限等級修正制御追加） | 中 |
| `docs/internal/07_SECURITY_AND_AUTOMATION.md` | 大幅更新（Section 5, 6 追加） | 中 |
| `docs/internal/99_reference_generic.md` | 軽微更新（モードタグ追加） | 低 |
| `docs/internal/03_QUALITY_STANDARDS.md` | 変更なし（保護確認のみ） | なし |
| `docs/internal/08_SESSION_MANAGEMENT.md` | 変更なし | なし |
| `docs/internal/09_SUBAGENT_STRATEGY.md` | 変更なし | なし |

### リスク評価

| リスク | 影響 | 確率 | 対策 |
|--------|------|------|------|
| 影式固有ルール（R-2〜R-11）の消失 | 高 | 低 | building-checklist.md を独立ファイルとして保持。マージ後に参照可能性を検証 |
| AUDITING 修正ルール変更による運用混乱 | 中 | 中 | audit-fix-policy.md を保持し PG/SE/PM との併用で段階的移行 |
| Phase 完了判定スモークテストの消失 | 高 | 低 | phase-rules.md の BUILDING セクションに影式固有として明記 |
| 日常ワークフローの消失 | 中 | 低 | CHEATSHEET.md に影式固有セクションとして維持 |
