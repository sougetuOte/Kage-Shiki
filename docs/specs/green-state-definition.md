# Green State 定義書

**バージョン**: 1.2 (影式版)
**作成日**: 2026-03-18
**ベース**: LAM v4.6.0 `green-state-definition.md` v1.1
**対応仕様**: `docs/specs/lam/v4.0.0-immune-system-requirements.md` P5-FR-1

---

## 1. 概要

Green State とは、自動ループが「品質基準を満たした」と判定し、正常収束するための条件セットである。`/full-review` の Stage 5 および Stop hook がこの条件を評価し、全条件を満たした場合にループを停止させる。

**核心原則: Green State は「スキャンして Issue がゼロ」の状態である。「修正後にゼロ」ではない。**

あるイテレーションで Issue を全件修正しても、それは Green State ではない。次のイテレーションで再スキャン（Stage 2）を実行し、**新規 Issue が 0件** であって初めて Green State が確定する。この原則により、修正の副作用で生まれた問題が見逃されることを防ぐ。

---

## 2. Green State 5条件

| # | 条件 | 判定方法 | 影式での実行コマンド |
|---|------|---------|-------------------|
| G1 | テスト全パス | テストフレームワークの実行結果 | `pytest tests/ -v --tb=short` |
| G2 | lint 全パス | lint ツールの実行結果 | `ruff check src/ tests/` |
| G3 | 対応可能 Issue 全解決 | 監査エージェントの Issue 判定 | `/full-review` Stage 2-3 の出力 |
| G4 | 仕様差分ゼロ | `docs/specs/` と実装の照合 | quality-auditor による検証 |
| G5 | セキュリティチェック通過 | 依存脆弱性 + シークレットスキャン | gitleaks + OWASP チェック |

---

## 3. 各条件の判定方法

### 3.1 G1: テスト全パス

**判定方法**: `pytest tests/ -v --tb=short` を実行し、全テストが PASS であること。

**影式での追加テスト対象**:
- `pytest .claude/hooks/analyzers/tests/ -v` — analyzers テスト
- `.claude/hooks/tests/` — hooks テスト（存在する場合）

**テスト数減少の検出**: 前サイクルと比較してテスト数が減少した場合はエスカレーション。

### 3.2 G2: lint 全パス

**判定方法**: `ruff check src/ tests/` を実行し、エラーがゼロであること。

### 3.3 G3: 対応可能 Issue 全解決

**判定基準**（`.claude/rules/code-quality-guideline.md` に準拠）:

| 重要度 | Green State 条件 |
|--------|-----------------|
| Critical | 0件（必須） |
| Warning | 0件（必須）。PG/SE 級は修正済み。PM 級は理由付き保留（deferred）可 |
| Info | **Green State を阻害しない**。件数にかかわらず監査通過 |

**核心ルール**: Critical と Warning の放置は禁止。Warning の残存 Issue は全て修正済みまたは deferred + 理由が記録されている状態を Green State とする。

### 3.4 G4: 仕様差分ゼロ

**判定方法**: quality-auditor が `docs/specs/` と実装コードの整合性を検証し、差分がないことを確認する。

### 3.5 G5: セキュリティチェック通過

**判定方法**: 以下のチェック全てを通過すること。

| チェック項目 | ツール | 判定基準 |
|:---|:---|:---|
| 依存脆弱性 | `pip audit` / `safety check` | Critical/High 脆弱性ゼロ |
| シークレット漏洩 | **gitleaks** | gitleaks Issue ゼロ（`gitleaks:not-installed` 含む） |
| 危険パターン | OWASP Top 10 チェック | eval/exec、SQL 文字列結合、pickle.load 等なし |

**gitleaks 未インストール時**: `gitleaks:not-installed` は Critical Issue として扱われ、**G5 は FAIL**。gitleaks をインストールして再実行すれば解消。
**明示的オプトアウト**（`review-config.json` で `gitleaks_enabled: false`）: スキップ + INFO ログ。G5 は PASS。
**依存脆弱性ツール未インストール時**: PASS（スキップ）扱い。ログに記録。

---

## 4. 理由付き保留（deferred）

### 4.1 フォーマット

```
deferred: [issue内容] — 理由: [保留理由] → 追跡先: docs/tasks/xxx.md
```

### 4.2 典型的な保留理由

| パターン | 例 |
|---------|-----|
| 権限等級による保留 | PM 級のため承認待ち |
| スコープ外 | Phase 2b スコープ |
| 設計判断が必要 | ADR 起票推奨 |

### 4.3 禁止パターン

- 理由なしの保留
- 「後で対応」のような曖昧な理由
- PG 級の Issue に対する保留（PG 級は自動修正すべき）

---

## 5. 参照

- `/full-review` Stage 5: Green State 判定の実行手順
- `.claude/rules/phase-rules.md` AUDITING セクション: Green State 5条件テーブル
- `.claude/rules/code-quality-guideline.md`: G3 の重要度分類基準
- `docs/specs/lam/gitleaks-integration-spec.md`: G5 の gitleaks 統合仕様
- `docs/internal/07_SECURITY_AND_AUTOMATION.md` Section 5: Stop Hook
