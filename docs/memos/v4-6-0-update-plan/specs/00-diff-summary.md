# LAM v4.5.0 → v4.6.0 差分サマリー

**作成日**: 2026-03-18
**対象**: 影式 (Kage-Shiki) v4.5.0 適用済み環境への LAM v4.6.0 差分適用
**前回移行参考**: `docs/memos/v4-5-0-update-plan/`

---

## 1. バージョン間の主要変更

LAM v4.6.0 は **gitleaks 統合**を中心とした集中型更新。v4.5.0 の大規模更新（96タスク）と異なり、影響範囲は限定的。

### 1.1 新規コンセプト

| コンセプト | 概要 | 影響範囲 |
|-----------|------|---------|
| **gitleaks 統合** | 言語・ファイル形式を問わない包括的シークレット検出 | analyzers/, full-review.md, ship.md |
| **G5 gitleaks 必須化** | gitleaks 未インストールで G5 FAIL | full-review Stage 5, Green State 定義 |
| **明示的オプトアウト** | `review-config.json` の `gitleaks_enabled: false` | config.py |

### 1.2 延期 Issue 解消（A〜G）

v4.5.0 で残っていた延期 Issue 7件が全件解消された:

| Issue | 内容 | 解消方法 |
|-------|------|---------|
| A | SECRET_PATTERN JSON/YAML 対応 | gitleaks 統合で解決 |
| B | PostToolUseFailure ランタイム検証 | 正常動作確認 |
| C | PG 引数制御 | 既に実装済みと確認 |
| D | .md/.txt スキャン対象追加 | gitleaks 統合で解決 |
| E | テスト方式記述更新 | docs 更新 |
| F | pre-compact.py テスト拡充 | テスト追加 |
| G | セキュリティスキャンテスト | 既存 + gitleaks で十分 |

---

## 2. ファイル別差分一覧

### 2.1 新規追加ファイル

#### Hooks（`.claude/hooks/analyzers/`）

| ファイル | 概要 | 影式での対応 |
|---------|------|------------|
| `gitleaks_scanner.py` | gitleaks ラッパー（detect/protect/parse） | **導入** |

#### テスト（`.claude/hooks/analyzers/tests/`）

| ファイル | 概要 | 影式での対応 |
|---------|------|------------|
| `test_gitleaks_scanner.py` | gitleaks テスト 28件 | **導入** |

#### 仕様書（`docs/specs/`）

| ファイル | 概要 | 影式での対応 |
|---------|------|------------|
| `gitleaks-integration-spec.md` | gitleaks 統合仕様書 | **取込** |

#### 設計書（`docs/design/`）

| ファイル | 概要 | 影式での対応 |
|---------|------|------------|
| `gitleaks-integration-design.md` | gitleaks 統合設計書 | **取込** |

#### タスク（`docs/tasks/`）

| ファイル | 概要 | 影式での対応 |
|---------|------|------------|
| `gitleaks-integration-tasks.md` | gitleaks 統合タスク定義 | **取込**（参考用） |

#### 設定ファイル

| ファイル | 概要 | 影式での対応 |
|---------|------|------------|
| `.gitleaks.toml` | gitleaks 設定（除外ルール等） | **導入** |

### 2.2 更新ファイル

#### Hooks（`.claude/hooks/analyzers/`）

| ファイル | 変更内容 | 影響度 |
|---------|---------|-------|
| `config.py` | `gitleaks_enabled: bool = True` フィールド追加 + `_parse_bool()` ヘルパー | **中** |
| `run_pipeline.py` | gitleaks_scanner import + `run_phase0()` に gitleaks 呼び出し追加 + analyzers なしでも gitleaks 実行 | **高** |

#### コマンド（`.claude/commands/`）

| ファイル | 変更内容 | 影響度 |
|---------|---------|-------|
| `full-review.md` | Stage 1 Step 1 に gitleaks NOTE 追加、Stage 5 G5 を gitleaks ベースに更新 | **高** |
| `ship.md` | Phase 1 に gitleaks protect --staged 統合 | **高** |

#### 仕様書（`docs/specs/`）

| ファイル | 変更内容 | 影響度 |
|---------|---------|-------|
| `scalable-code-review-spec.md` | FR-7e に gitleaks 統合言及 | **低** |

#### 設計書（`docs/design/`）

| ファイル | 変更内容 | 影響度 |
|---------|---------|-------|
| `hooks-python-migration-design.md` | テスト方式 3（conftest sys.path）追記 | **低** |

#### ルートファイル

| ファイル | 変更内容 | 影響度 |
|---------|---------|-------|
| `README.md` | gitleaks を環境要件として追記 | **低** |

#### テスト（既存テスト拡充 7件）

| ファイル | 変更内容 | 影響度 |
|---------|---------|-------|
| `test_config.py` | `gitleaks_enabled` パース + `_parse_bool` テスト | **中** |
| `test_run_pipeline.py` | gitleaks 統合テスト | **中** |
| その他 hooks/tests/ | 延期 Issue 対応テスト | **低** |

### 2.3 スキップ対象

| ファイル/機能 | 理由 |
|-------------|------|
| `README_en.md` | 英語版は影式では不要 |
| `docs/artifacts/retro-gitleaks-integration.md` | LAM 開発時の振り返り。影式の固有学習ではない |
| `docs/artifacts/release-notes-staging.md` | LAM リリースノート |
| `docs/slides/` | v4.5.0 と同判断（影式には既存なし） |
| `QUICKSTART.md` / `QUICKSTART_en.md` | v4.5.0 と同判断 |
| LAM 開発時の audit-reports | LAM 固有 |

---

## 3. 影式固有の判断ポイント

### 3.1 gitleaks 導入の是非

| 観点 | 分析 |
|------|------|
| 影式の環境 | Windows 11 + Python 3.12 → gitleaks は Windows でも動作 |
| メリット | シークレット検出が言語・ファイル形式を問わず包括的になる |
| リスク | gitleaks 未インストール時に G5 FAIL になる（開発者体験の低下） |
| **結論** | **導入する**。gitleaks は `scoop install gitleaks` で導入可能。未インストール時の G5 FAIL は正しい設計（シークレット漏洩リスクの方が重要） |

### 3.2 ship.md への gitleaks protect 統合

| 観点 | 分析 |
|------|------|
| 影式の `/ship` | 現行は秘密情報パターンチェックのみ |
| LAM v4.6.0 | gitleaks protect --staged を Phase 1 に統合 |
| **結論** | **LAM に従い統合**。既存のパターンチェックと gitleaks は補完関係 |

### 3.3 review-config.json の gitleaks_enabled

| 観点 | 分析 |
|------|------|
| 影式の現状 | review-config.json は未使用（デフォルト設定で運用） |
| **結論** | **config.py に gitleaks_enabled を追加**。明示的オプトアウト手段の確保は正しい設計 |

### 3.4 延期 Issue B〜G

| 観点 | 分析 |
|------|------|
| Issue B-G | LAM 開発時の固有 Issue |
| **結論** | **影式には直接適用されない**。ただし B（PostToolUseFailure 検証）と F（pre-compact テスト拡充）は差分確認の上で取り込む |

---

## 4. 推奨移行順序

v4.6.0 は変更範囲が限定的（gitleaks 集中）のため、Phase 構成をコンパクト化する。

```
Phase 1: gitleaks コード導入
  - gitleaks_scanner.py 新規追加
  - config.py に gitleaks_enabled フィールド追加
  - run_pipeline.py に gitleaks 呼び出し追加
  - .gitleaks.toml 追加
  - テスト追加（test_gitleaks_scanner.py + 既存テスト拡充）

Phase 2: コマンド + 仕様書更新
  - full-review.md 更新（Stage 1 gitleaks NOTE + Stage 5 G5 更新）
  - ship.md 更新（Phase 1 gitleaks protect）
  - README.md 更新（環境要件追記）
  - gitleaks 仕様書・設計書取込

Phase 3: 統合検証 + 完了
  - 全テスト実行（既存 834 + gitleaks テスト）
  - ruff check クリーン
  - gitleaks インストール確認
  - SESSION_STATE.md 更新
```

### 移行リスク評価

| Phase | リスク | 理由 |
|-------|-------|------|
| Phase 1 | **低** | gitleaks_scanner.py は独立モジュール。config.py と run_pipeline.py の変更は局所的 |
| Phase 2 | **低** | コマンド + ドキュメント変更のみ |
| Phase 3 | **低** | 検証のみ |

---

## 5. 影式固有保持項目

v4.5.0 移行で識別済みの 10 項目は全て保持（v4.6.0 で変更なし）。

追加確認:

| # | 確認項目 | 結論 |
|---|---------|------|
| 1 | full-review.md の影式固有警告行 | 保持（Phase 3 完了後に削除） |
| 2 | ship.md の影式独自フロー | gitleaks 統合箇所のみ更新、他は保持 |
| 3 | Context 閾値 20% | v4.6.0 で変更なし。影式は引き続き 20% を維持 |

---

## 6. 次のステップ

| 順序 | 作業 | 出力先 |
|------|------|-------|
| 1 | 移行設計 | `designs/01-design-gitleaks.md` |
| 2 | タスク分解 | `tasks/02-tasks-phase1-3.md` |
| 3 | 承認 → 実施 | Phase 1〜3 |
