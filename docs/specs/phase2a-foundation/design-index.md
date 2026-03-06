# Phase 2a 基盤強化 設計書インデックス

**フェーズ**: PLANNING — design サブフェーズ
**根拠**: `requirements.md`（承認済み Rev.1）
**作成日**: 2026-03-06

---

## 設計項目一覧

| # | 項目 | ファイル | 関連 FR | ステータス |
|---|------|---------|---------|-----------|
| D-17 | LLMProtocol 設計 | `design-d17-llm-protocol.md` | FR-8.6 | 承認済み |
| D-18 | トランケートアルゴリズム設計 | `design-d18-truncation.md` | FR-8.7 | 承認済み |
| D-19 | ウィザード GUI 設計 | `design-d19-wizard-gui.md` | FR-8.8, FR-8.9, FR-8.10 | 承認済み |
| D-20 | 統合テスト設計 | `design-d20-integration-tests.md` | FR-8.3, FR-8.4, FR-8.5, FR-8.11 | 承認済み |

> **採番**: Phase 1 は D-1〜D-16。Phase 2a は D-17〜D-20 のグローバル連番。
> Phase 1 の起動シーケンス設計は `docs/specs/phase1-mvp/design-d16-startup-sequence.md` を参照。

---

## 依存関係

```
D-17（LLMProtocol）──→ D-19（ウィザード GUI）が型注釈で参照
D-17（LLMProtocol）──→ D-20（統合テスト）がモック設計で参照
D-18（トランケート）──→ D-20（統合テスト）がトランケート検証で参照
D-19（ウィザード GUI）──→ D-20（統合テスト）が応答タイミングテストで参照
```

---

## AoT 並列設計マップ

| Atom | 設計書 | 実装 Atom 依存 | 並列設計可否 |
|------|--------|--------------|------------|
| D-17 | `design-d17-llm-protocol.md` | なし | 可（D-18 と並列） |
| D-18 | `design-d18-truncation.md` | D-17 のインターフェース確定後 | D-17 と並列可 |
| D-19 | `design-d19-wizard-gui.md` | D-17 のシグネチャ確定後 | D-18 と並列可 |
| D-20 | `design-d20-integration-tests.md` | D-17, D-18, D-19 の概要確定後 | D-17〜19 の後 |

---

## テスト文書（設計書外）

| 成果物 | 出力先 | 関連 FR |
|--------|--------|---------|
| スモークテスト手順書 | `docs/testing/smoke-test.md` | FR-8.1 |
| GUI 手動テストチェックリスト | `docs/testing/gui-manual-test.md` | FR-8.2 |

---

## 参照文書

| 文書 | パス |
|------|------|
| 要件定義（承認済み） | `requirements.md` |
| Phase 1 設計書インデックス | `docs/specs/phase1-mvp/design-index.md` |
| Phase 1 プロンプトテンプレート設計 | `docs/specs/phase1-mvp/design-d03-prompt-template.md` |
| Phase 1 max_tokens 設計 | `docs/specs/phase1-mvp/design-d15-max-tokens.md` |
| Phase 1 起動シーケンス設計 | `docs/specs/phase1-mvp/design-d16-startup-sequence.md` |
| 統合設計案（SSOT） | `docs/memos/middle-draft/04-unified-design.md` |
| GUI・ボディ設計 | `docs/memos/middle-draft/06-gui-and-body.md` |
| Phase 2 バックログ | `docs/memos/phase2-backlog.md` |
| Phase 1 ホットフィックス教訓 | `docs/memos/hotfix-runtime-bugs-phase1.md` |
