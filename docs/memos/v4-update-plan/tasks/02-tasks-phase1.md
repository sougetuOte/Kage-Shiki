# タスク分解: Phase 1 — 基盤移行

**作成日**: 2026-03-10
**対象設計**: `01-design-rules-reorganization.md`, `01-design-docs-claude-md.md`
**見積り**: 6 タスク、コード変更なし（ドキュメントのみ）

---

## 依存関係

```
T1-1 (phase-rules.md) ─┐
T1-2 (building-checklist.md) ─┤
T1-3 (新規ルール) ─────┤── T1-5 (CLAUDE.md / CHEATSHEET.md)
T1-4 (その他rules) ────┘        │
                                 │
T1-5 ──────────────── T1-6 (docs/internal/)
                                 │
                        Phase 1 検証
```

---

## T1-1: phase-rules.md の LAM 4.0.1 ベース再構築

**設計参照**: `01-design-rules-reorganization.md` 判断2 (D1)
**優先度**: 最高（他タスクの前提）

### 作業内容

1. LAM 4.0.1 の phase-rules.md をベースとして採用
2. PLANNING セクション: LAM 4.0.1 と同一（変更なし）
3. BUILDING セクション:
   - LAM 4.0.1 の TDD 品質チェック（R-1, R-4）を記載
   - LAM 4.0.1 の仕様同期ルール（S-1, S-3, S-4）を記載
   - LAM 4.0.1 の TDD 内省パイプラインを追加
   - building-checklist.md への参照リンクを追加
   - **影式固有**: Phase 完了判定スモークテスト（L-4 由来）を追記
4. AUDITING セクション:
   - LAM 4.0.1 の PG/SE/PM 修正ルールを導入
   - **影式固有**: A-3（修正後の再検証義務）をインライン追記
   - **影式固有**: 監査レポート完了条件（PG/SE/PM 対応版）を追記
   - `/full-review` で一気通貫実施可能の記載を維持
5. フェーズ警告テンプレート: LAM 4.0.1 と同一

### 受入条件

- [ ] R-1, R-4, S-1, S-3, S-4 が BUILDING セクションに記載されている
- [ ] L-4（スモークテスト）が「影式固有:」プレフィックス付きで記載されている
- [ ] A-3（再検証義務）が AUDITING セクションに記載されている
- [ ] PG/SE/PM 修正ルールが AUDITING セクションに記載されている
- [ ] building-checklist.md への参照リンクが存在する

---

## T1-2: building-checklist.md の再編

**設計参照**: `01-design-rules-reorganization.md` 判断1 (A3)
**優先度**: 高
**依存**: T1-1 と並行可能

### 作業内容

1. ヘッダーを変更: 「影式 BUILDING 品質チェックリスト（プロジェクト固有）」
2. LAM コアルール参照の注記を追加
3. R-1, R-4, S-1, S-3, S-4 の記載を**削除**（phase-rules.md に委譲）
4. 以下を維持:
   - Red: R-5（異常系テストの義務）
   - Green: R-2, R-3, R-6
   - Green 直後: R-11, R-5 続, R-7, R-8, R-9, R-10
5. spec-sync.md から S-2（Protocol 外メソッドの明示）を移入
6. spec-sync.md から NFR 注記（「NFR も S-1 の突合対象」）を移入

### 受入条件

- [ ] R-2, R-3, R-5〜R-11, S-2 が記載されている
- [ ] R-1, R-4, S-1, S-3, S-4 の重複記載がない
- [ ] phase-rules.md への参照注記がある
- [ ] NFR 注記が「仕様同期（影式固有補足）」セクションに存在する

---

## T1-3: 新規ルールファイルの作成

**設計参照**: `01-design-rules-reorganization.md` 判断4
**優先度**: 高
**依存**: なし（独立作業）

### 作業内容

1. `permission-levels.md` を新規作成
   - LAM 4.0.1 をベースに、影式パス構造用ファイルパステーブルをカスタマイズ
   - PM級: docs/specs/, docs/adr/, docs/internal/, .claude/rules/, .claude/settings*, pyproject.toml
   - SE級: docs/ (上記以外), src/kage_shiki/, tests/, config/
   - 「迷った場合」セクションに影式固有の典型例を追加
2. `upstream-first.md` を新規作成（LAM 4.0.1 をそのまま配置）
3. `auto-generated/README.md` を新規作成（LAM 4.0.1 をそのまま配置）
4. `auto-generated/trust-model.md` を新規作成（LAM 4.0.1 をそのまま配置）

### 受入条件

- [ ] permission-levels.md が影式パス構造に合わせてカスタマイズされている
- [ ] upstream-first.md が LAM 4.0.1 と同一内容で配置されている
- [ ] auto-generated/ ディレクトリとファイルが作成されている

---

## T1-4: 既存ルールファイルの更新 + 廃止ファイル処理

**設計参照**: `01-design-rules-reorganization.md` 判断3
**優先度**: 中
**依存**: T1-1, T1-2（統合内容が確定してから）

### 作業内容

1. `core-identity.md` 更新:
   - 権限等級（PG/SE/PM）セクションを追加（permission-levels.md 参照付き）
   - Subagent 委任判断テーブルを維持
   - コンテキスト節約原則を維持
   - Context Compression を維持
2. `security-commands.md` 更新:
   - Deny List セクション名を「高リスクコマンド（Layer 0: 承認必須）」に変更
   - 末尾に Layer 0/1/2 三層モデルセクションを追加
   - Python カテゴリを Allow List に維持
3. `decision-making.md` 更新:
   - SSOT 参照注記を 1 行追加（「詳細は docs/internal/06_DECISION_MAKING.md を参照」）
4. `audit-fix-policy.md` を削除
5. `spec-sync.md` を削除

### 受入条件

- [ ] core-identity.md に権限等級セクションがある
- [ ] core-identity.md に Subagent 委任判断が残っている
- [ ] security-commands.md に Python コマンドが残っている
- [ ] security-commands.md に Layer 0/1/2 セクションがある
- [ ] decision-making.md に SSOT 参照注記がある
- [ ] audit-fix-policy.md が削除されている
- [ ] spec-sync.md が削除されている

---

## T1-5: CLAUDE.md / CHEATSHEET.md の更新

**設計参照**: `01-design-docs-claude-md.md` 判断1, 判断2
**優先度**: 中
**依存**: T1-1〜T1-4（ルール構成が確定してから）

### 作業内容

#### CLAUDE.md
1. Execution Modes テーブル: AUDITING ガードレールを「PM級修正禁止（PG/SE級は許可）」に変更
2. Identity / Project Overview / References / Initial Instruction: 影式固有を維持
3. Project Scale: `Medium` を維持
4. Active Migration Notice: 既存のまま維持

#### CHEATSHEET.md
1. LAM 4.0.1 の構造を採用:
   - 権限等級（PG/SE/PM）セクションを新規追加
   - コマンド分類を再編（ワークフロー / 補助に分離）
   - AoT クイックガイドに Atom テーブル形式を追加
   - クイックリファレンスをマージ（セッション開始, ADR, Rules を追加）
2. 影式固有を維持:
   - タイトル: 「影式 (Kage-Shiki) チートシート」
   - プロジェクト技術スタック
   - 日常ワークフロー（Wave ベース）
   - `/ship` クイックリファレンス
3. Rules ファイル一覧を更新:
   - permission-levels.md を追加
   - audit-fix-policy.md, spec-sync.md を削除
   - building-checklist.md の説明を更新
4. ディレクトリ構造: hooks/, logs/ を追加
5. フェーズコマンド AUDITING: PM級修正禁止に更新

### 受入条件

- [ ] CLAUDE.md の Execution Modes テーブルが更新されている
- [ ] CHEATSHEET.md に権限等級セクションがある
- [ ] CHEATSHEET.md に日常ワークフローが残っている
- [ ] CHEATSHEET.md の Rules 一覧が最新の構成を反映している

---

## T1-6: docs/internal/ の更新

**設計参照**: `01-design-docs-claude-md.md` 判断3, 判断4
**優先度**: 中
**依存**: T1-1〜T1-4（ルール構成が確定してから）

### 作業内容

1. `00_PROJECT_STRUCTURE.md`:
   - .claude/ 配下に hooks/, logs/, settings.json を追加
   - Section 3 に SSOT 3 層アーキテクチャを新規追加（LAM 4.0.1）
   - Section 2C の ADR 命名規則を連番方式に変更
   - File Naming Conventions のセクション番号を 3→4 に変更
2. `02_DEVELOPMENT_FLOW.md`:
   - Dependency Traversal: grep_search → Grep / Glob に更新
   - walkthrough パスを docs/memos/walkthrough-<feature>.md に更新
   - Automated TDD Introspection セクションを Phase 2 末尾に追加
   - 権限等級に基づく修正制御セクションを Phase 3 末尾に追加
   - Quality Rules Integration テーブルを更新（spec-sync.md 縮小, audit-fix-policy.md 削除を反映）
   - 影式固有セクション（Wave, Advanced Workflows）を維持
3. `07_SECURITY_AND_AUTOMATION.md`:
   - Section 5（Hooks-Based Permission System）を新規追加
   - Section 6（Recommended Security Tools）を新規追加
   - Section 2 の影式固有コマンドを維持
4. `99_reference_generic.md`:
   - フェーズモードタグ（`[PLANNING]` 等）を追加
5. `03_QUALITY_STANDARDS.md`: Section 6, 7 の影式固有が残っていることを確認（変更なし）

### 受入条件

- [ ] 00_PROJECT_STRUCTURE.md に SSOT 3 層アーキテクチャが追加されている
- [ ] 00_PROJECT_STRUCTURE.md の ADR 命名規則が連番方式になっている
- [ ] 02_DEVELOPMENT_FLOW.md に TDD Introspection セクションがある
- [ ] 02_DEVELOPMENT_FLOW.md に Wave/Advanced Workflows が残っている
- [ ] 07_SECURITY_AND_AUTOMATION.md に Section 5, 6 が追加されている
- [ ] 03_QUALITY_STANDARDS.md の Section 6, 7 が保護されている

---

## Phase 1 検証チェックリスト

全タスク完了後に実施:

- [ ] Claude Code 起動時にルールファイルが正常に読み込まれること
- [ ] `/quick-load` が正常動作すること
- [ ] `/planning`, `/building`, `/auditing` の切替が正常動作すること
- [ ] 影式固有ルール (R-2〜R-11) が building-checklist.md で参照可能であること
- [ ] Phase 完了判定スモークテスト要件が phase-rules.md に残っていること
- [ ] Markdown 構文エラーがないこと

**コミット**: `[LAM-4.0.1] Phase 1: 基盤移行 — rules/docs/CLAUDE.md`
