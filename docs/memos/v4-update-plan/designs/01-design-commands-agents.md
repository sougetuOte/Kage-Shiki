# 設計: コマンド / スキル / エージェント移行

**作成日**: 2026-03-10
**ステータス**: Accepted（Phase 2 実装完了）
**関連**: [差分分析](../specs/00-diff-commands-skills-agents.md) | [マスターインデックス](../000-index.md)

---

## 概要

LAM v3.x → v4.0.1 移行の Phase 2（コマンド / スキル / エージェント）における
6つの設計判断を記録する。各判断について選択肢を列挙し、トレードオフを分析し、推奨案を提示する。

### 判断の依存関係

```
判断1 (モデル選択) ─── 独立
判断2 (full-review) ── 判断1 に依存（エージェント構成）、判断3 に関連（自動ループ）
判断3 (ship.md) ────── Phase 3 hooks に依存
判断4 (影式固有) ───── 独立
判断5 (スキル更新) ── 独立
判断6 (LAM 仕様書) ── 独立
```

---

## 判断1: エージェントのモデル選択

### 背景

LAM 4.0.1 では 2 つのエージェントでモデル変更が提案されている:

| エージェント | 現行 | LAM 4.0.1 | 変更理由（LAM側） |
|-------------|------|-----------|-----------------|
| quality-auditor | opus | sonnet | コスト最適化 |
| test-runner | sonnet | haiku | コスト最適化 |
| 他 6 エージェント | 変更なし | 変更なし | — |

### 選択肢

#### quality-auditor: opus vs sonnet

| 観点 | 選択肢A: opus 維持 | 選択肢B: sonnet に変更 |
|------|-------------------|----------------------|
| 分析品質 | 高い。仕様ドリフト検出・アーキテクチャ判断で優位 | 十分だが、複雑な構造整合性の見落としリスクあり |
| コスト | 高い（opus は sonnet の約5倍） | 低い |
| 速度 | 遅い | 速い |
| 影式での実績 | Phase 1 で opus による監査の実績あり。R-2〜R-11 はこの品質水準で発見された | 未検証 |
| v4.0.0 新機能との整合 | 仕様ドリフト + 構造整合性チェックは高い推論能力が必要 | sonnet でもチェックリスト駆動なら対応可能 |

#### test-runner: sonnet vs haiku

| 観点 | 選択肢A: sonnet 維持 | 選択肢B: haiku に変更 |
|------|---------------------|---------------------|
| テスト実行品質 | 高い（失敗分析が詳細） | テスト実行自体は問題なし。失敗分析の深さは低下 |
| コスト | 中程度 | 低い（sonnet の約1/10） |
| 速度 | 中程度 | 速い |
| 影式での実績 | 現行で使用中、問題なし | 未検証 |
| タスク特性 | テスト実行・結果集計は定型作業。深い推論は不要 | 定型作業に適している |

### 推奨案

| エージェント | 推奨 | 根拠 |
|-------------|------|------|
| **quality-auditor** | **opus 維持**（選択肢A） | v4.0.0 で追加される仕様ドリフトチェック・構造整合性チェックは高い推論能力を必要とする。影式は Phase 1 Retro で opus 品質の監査から R-2〜R-11 を導出した実績がある。コスト増は許容し、品質を優先する。000-index.md の衝突解決ポリシーとも一致 |
| **test-runner** | **haiku に変更**（選択肢B） | テスト実行・カバレッジ集計は定型作業であり、haiku で十分。コスト削減と速度向上のメリットが大きい。失敗分析が不十分な場合はメインセッション（opus/sonnet）で補完できる |
| **他 6 エージェント** | **変更なし** | frontmatter に `# permission-level` コメントを追加するのみ |

### 実装メモ

- quality-auditor.md: model は `opus` のまま維持。Step 3 に仕様ドリフトチェック + Step 3b に構造整合性チェックを追加
- test-runner.md: model を `haiku` に変更。本文変更なし
- 全 8 エージェントに `# permission-level: PG/SE/PM` コメントを追加

---

## 判断2: full-review.md の移行方針

### 背景

full-review.md は LAM 4.0.1 で**最も差分が大きいコマンド**。主な変更:

1. **3 → 4 エージェント構成**: セキュリティ監査エージェントの独立
2. **Green State 5 条件**: Phase 4 の検証基準の厳格化
3. **自動ループ**: Stop hook による自動イテレーション（最大 5 回）
4. **Phase 0/0.5**: ループ初期化 + context7 MCP 検出
5. **差分チェック / フルスキャン**: fullscan_pending フラグ管理

### 選択肢

#### A: LAM 4.0.1 版をベースに影式固有を追加

LAM 4.0.1 の full-review.md を採用し、影式固有の要素を上乗せする。

**メリット**: LAM テンプレートの新機能（4 エージェント、Green State、差分/フルスキャン）を完全に取り込める
**デメリット**: 自動ループは Stop hook 依存のため Phase 3 まで動作しない

#### B: 現行版をベースに LAM 4.0.1 の要素を段階的に追加

現行の 3 エージェント構成を維持しつつ、Green State 等を追加する。

**メリット**: 段階的移行で安全
**デメリット**: エージェント構成の変更が中途半端になり、後で再度大きな修正が必要

#### C: LAM 4.0.1 版ベース + 自動ループは手動フォールバック

LAM 4.0.1 版を採用するが、自動ループ部分だけ手動ループ（ユーザーが `/full-review` を再実行）にフォールバックする。

**メリット**: 構造的には完全移行。自動ループだけが Phase 3 で有効化される形になり、Phase 2 と Phase 3 の責任が明確に分かれる
**デメリット**: Phase 2 の時点では手動再実行が必要

### 推奨案: **選択肢C**

理由:

1. **構造の一貫性**: 4 エージェント構成、Green State、Phase 0/0.5 を Phase 2 の時点で完全に導入する。これにより Phase 3 で hooks を追加するだけで自動ループが有効化される
2. **手動フォールバックの設計**: 自動ループ部分に以下の分岐を記述する:

```markdown
### 自動ループ制御

hooks 導入済みの場合:
  → lam-stop-hook による自動ループ（最大 5 イテレーション）

hooks 未導入の場合（Phase 2 時点）:
  → Phase 4 で Green State 未達の場合、修正内容を報告しユーザーに再実行を提案
  → ユーザーが `/full-review` を再実行することで手動ループ
```

3. **影式固有の保持事項**:
   - 品質監査エージェントは `building-checklist.md` の R-1〜R-6 適合性チェックを含む
   - 仕様ズレ発見時は `spec-sync.md` (S-1〜S-4) に従い同時修正
   - モデル選択ガイドは削除（エージェント定義側に委任、判断1と整合）

### 4 エージェント構成の詳細

| # | エージェント | 対象 | 観点 | モデル |
|---|------------|------|------|-------|
| 1 | code-reviewer | `src/` 全 `.py` | コード品質、エラーハンドリング、命名規則 | opus |
| 2 | code-reviewer | `tests/` 全 `.py` | テスト品質、FR 対応、fixture 共通化 | opus |
| 3 | quality-auditor | プロジェクト全体 | アーキテクチャ、仕様ドリフト、構造整合性、R-1〜R-6 適合 | opus |
| 4 | code-reviewer | プロジェクト全体 | セキュリティ（OWASP Top 10: インジェクション、認証、シークレット、依存脆弱性、データ露出、デシリアライゼーション） | opus |

### Green State 5 条件（影式版）

| ID | 条件 | 検証方法 |
|----|------|---------|
| G1 | テスト全パス | `pytest tests/ -v --tb=short` |
| G2 | lint エラーゼロ | `ruff check src/ tests/` |
| G3 | 対応可能 Issue ゼロ | Phase 3 修正後の残 Issue 確認 |
| G4 | 仕様差分ゼロ | `docs/specs/` と実装の突合 |
| G5 | セキュリティチェック通過 | エージェント4 の結果 |

---

## 判断3: ship.md の doc-sync-flag 対応

### 背景

LAM 4.0.1 の ship.md は Phase 2（Doc Sync）で `doc-sync-flag` ファイルを参照する。
このファイルは PostToolUse hook が生成するもので、Phase 3 (hooks 導入) 前には存在しない。

### 選択肢

#### A: doc-sync-flag を前提とした設計に完全移行

LAM 4.0.1 版をそのまま採用。Phase 2 の時点では doc-sync-flag が存在しないため、
Doc Sync ステップが空振りする。

**メリット**: Phase 3 で hooks 導入後に自動的に機能する
**デメリット**: Phase 2 の時点でドキュメント同期チェックが機能しない（現行より劣化）

#### B: 現行の手動 Doc Sync を維持し、doc-sync-flag 対応はコメントで予約

現行の Phase 1.5（CHANGELOG, README, README_en, CHEATSHEET の固定チェック）を維持。
doc-sync-flag 対応部分はコメントアウトまたは条件分岐として記述。

**メリット**: Phase 2 の時点で現行の Doc Sync 品質を維持
**デメリット**: Phase 3 で再度修正が必要

#### C: フォールバック付き統合設計

doc-sync-flag の有無で分岐する設計にする:

```markdown
### Phase 2: ドキュメント同期

#### doc-sync-flag が存在する場合（hooks 導入後）
→ LAM 4.0.1 フロー（フラグから変更ファイル読取 → PG/SE/PM 分類 → doc-writer 呼出）

#### doc-sync-flag が存在しない場合（hooks 未導入）
→ 影式従来フロー（CHANGELOG, README, README_en, CHEATSHEET の固定チェック）
```

**メリット**: 両方の状態で正しく動作する。Phase 3 で hooks 導入後、自動的に新フローに移行
**デメリット**: 分岐が入るためコマンドが若干複雑になる

### 推奨案: **選択肢C（フォールバック付き統合設計）**

理由:

1. **無停止移行**: Phase 2 の時点で既存の Doc Sync 品質を維持しつつ、Phase 3 で自動的に新フローに移行
2. **影式固有ドキュメントの保護**: `README_en.md` と `CHEATSHEET.md` のチェックは doc-sync-flag フローにはない。フォールバック側に含めることで、これらが引き続きチェックされる
3. **Phase 構成の簡素化**: LAM 4.0.1 は 5 段階（Phase 1→2→3→4→5）だが、影式の手動削除候補チェック（Phase 6）とユーザー作業通知（Phase 6.2）は有用なため維持する

### ship.md の Phase 構成（移行後）

| Phase | 内容 | 変更点 |
|-------|------|--------|
| 1 | 棚卸し | 現行維持 |
| 2 | ドキュメント同期 | doc-sync-flag 分岐 + 影式固有チェック維持 |
| 3 | 論理グループ分け | 現行維持 |
| 4 | コミット計画 + ユーザー確認 | 現行維持 |
| 5 | コミット実行 | 現行維持 |
| 6 | 手動作業通知 + ユーザー作業 | 現行の Phase 6 + 6.2 を統合 |
| 7 | 完了報告 | 現行維持 |

---

## 判断4: 影式固有コマンドの扱い

### 背景

影式には LAM 4.0.1 テンプレートに存在しない固有コマンドがある:
- `retro.md`: Wave/Phase 完了時の振り返り（KPT）
- `wave-plan.md`: 次 Wave のタスク選定と実行順序策定
- `project-status.md`: Wave 進捗の集計（LAM 4.0.1 では KPI ダッシュボードに置換）

### retro.md / wave-plan.md

#### 選択肢

| 選択肢 | 内容 |
|--------|------|
| A: そのまま維持 | 変更なし。LAM 4.0.1 の新概念との整合は意識しない |
| B: 軽微な整合性調整 | frontmatter に description 追加 + 権限等級の言及を追加 |

#### 推奨案: **選択肢B（軽微な整合性調整）**

理由:
- LAM 4.0.1 の全コマンドが frontmatter に description を持つため、一貫性のために追加
- 内容自体は影式固有の実運用で検証済みであり、変更する理由がない
- 権限等級の観点では、retro.md は PM 級（設計判断に影響）、wave-plan.md は SE 級（タスク編成）

具体的な変更:

```markdown
# retro.md に追加
---
description: "Wave/Phase 完了時の振り返り（KPT）を実施"
---
# 権限等級: PM（振り返りの結論がルール・プロセスに影響するため）

# wave-plan.md に追加
---
description: "次 Wave のタスク選定と実行順序を策定"
---
# 権限等級: SE（タスク編成は設計判断を含むため）
```

### project-status.md

#### 選択肢

| 選択肢 | 内容 |
|--------|------|
| A: Wave 進捗のみ維持 | 現行のまま。KPI は導入しない |
| B: KPI ダッシュボードに置換 | LAM 4.0.1 版を採用。Wave 進捗セクションは削除 |
| C: Wave 進捗 + KPI を統合 | 両方を含む統合版を作成 |

#### 推奨案: **選択肢C（統合版）**

理由:
- Wave 進捗は影式のタスク管理に不可欠（Phase 1 の 10 Wave + Phase 2 の進行管理）
- KPI（K1〜K5）は v4.0.0 の定量評価基盤として有用
- ただし K2（平均ループイテレーション）と K3（フック介入率）は Phase 3 (hooks 導入) まで計測不可

統合版の構成:

```markdown
# プロジェクト状態

## 現在: [phase / subPhase]

## 機能進捗
[現行の機能テーブル]

## Wave 進捗（影式固有）
[現行の Wave テーブル]

## KPI ダッシュボード（v4.0.0）
| KPI | 値 | 目標 | 備考 |
|-----|---:|:----:|------|
| K1: タスク完了率 | XX% | 100% | |
| K2: 平均ループイテレーション | — | ≤3 | hooks 導入後に計測開始 |
| K3: フック介入率 | — | ≤5% | hooks 導入後に計測開始 |
| K4: コンテキスト枯渇率 | XX% | ≤10% | |
| K5: 同一Issue再発率 | XX% | 0% | |
```

---

## 判断5: スキルの更新方針

### 5-1: version: 1.0.0 の一律追加

#### 推奨案: **全スキルに追加**

理由: LAM 4.0.1 で全スキルが version フィールドを持つ。Claude Code の skills 仕様への準拠として追加する。影響は frontmatter のみで、動作への影響はない。

対象: adr-template, lam-orchestrate, skill-creator, spec-template, ultimate-think

### 5-2: lam-orchestrate のループ統合セクション追加

#### 背景

LAM 4.0.1 の lam-orchestrate には v4.0.0 の自動ループ機構の全体記述が追加されている:
- `lam-loop-state.json` のスキーマ定義
- ループライフサイクル（初期化→状態更新→終了処理）
- hooks との連携
- エスカレーション条件

#### 選択肢

| 選択肢 | 内容 |
|--------|------|
| A: ループ統合セクションを Phase 2 で追加 | 全文を追加。hooks 未導入でも「仕様としての定義」は有用 |
| B: ループ統合セクションは Phase 3 で追加 | hooks 導入と同時に追加。Phase 2 では追加しない |

#### 推奨案: **選択肢A（Phase 2 で追加）**

理由:
- lam-orchestrate はスキルの「仕様書」的な性格が強い。ループ統合セクションは hooks の動作仕様を定義するものであり、仕様定義は hooks 実装前に存在すべき
- full-review.md の手動フォールバック（判断2）がこのスキーマを参照する可能性がある
- frontmatter の変更: `disable-model-invocation`, `allowed-tools`, `argument-hint` を削除（LAM 4.0.1 に合わせる）。upstream-first ルールに従い、Claude Code の最新仕様を確認した上で判断する

### 5-3: ui-design-guide の導入判断

#### 背景

LAM 4.0.1 で新規追加されたスキル。UI/UX 設計チェックリスト（WCAG 2.1 AA、状態設計、レスポンシブ、フォーム UX、パフォーマンス）を提供する。

#### 選択肢

| 選択肢 | 内容 |
|--------|------|
| A: そのまま導入 | LAM 4.0.1 版をそのまま配置 |
| B: tkinter 向けにカスタマイズして導入 | Web 固有項目（レスポンシブ、LCP/CLS、バンドルサイズ）を除外し、tkinter 固有項目（ウィジェット配置、イベントバインド等）を追加 |
| C: 導入しない | 影式は tkinter ベースであり、Web UI ガイドの適用範囲が限定的 |

#### 推奨案: **選択肢B（tkinter 向けカスタマイズ）ただし優先度は低い**

理由:
- 状態設計（Empty, Loading, Error, Success, Partial）とアクセシビリティの設計原則は tkinter でも有用
- レスポンシブ設計、LCP/CLS、バンドルサイズは tkinter に適用不可
- ただし Phase 2 の主要作業ではない。**Phase 2 のスコープ外とし、Phase 2b 以降の影式通常作業で必要になった時点で作成する**ことを推奨

### 5-4: ultimate-think の frontmatter 変更

#### 推奨案: **LAM 4.0.1 に合わせて更新**

変更内容:
- `version: 1.0.0` 追加
- `disable-model-invocation: true` 削除（LAM 4.0.1 で削除。Claude Code の仕様変更への追従と推定）
- `--no-web` 条件分岐の記述削除（LAM 4.0.1 で削除）
- `references/anchor-format.md` は同一のため変更なし

---

## 判断6: docs/specs/ LAM 仕様書の取り込み方針

### 背景

LAM 4.0.1 には 7 つの仕様書が `docs/specs/` に含まれている:

| ファイル | 内容 |
|---------|------|
| v4.0.0-immune-system-requirements.md | 免疫系アーキテクチャ要件定義 |
| v4.0.0-immune-system-design.md | 免疫系アーキテクチャ設計 |
| green-state-definition.md | Green State 5 条件の詳細定義 |
| evaluation-kpi.md | KPI (K1〜K5) の定義 |
| loop-log-schema.md | ループログのスキーマ定義 |
| doc-writer-spec.md | doc-writer エージェントの詳細仕様 |
| v3.9.0-improvement-adoption.md | v3.9.0 改善の採用記録 |

### 選択肢

#### A: docs/specs/ 直下にそのままコピー

**メリット**: LAM テンプレートとの対応が明確
**デメリット**: 影式固有の仕様書（`docs/specs/kage-shiki/`）と混在する

#### B: docs/specs/lam/ サブディレクトリに配置

**メリット**: 影式固有仕様と LAM フレームワーク仕様が明確に分離される
**デメリット**: コマンドやエージェントからの参照パスが変わる（`docs/specs/evaluation-kpi.md` → `docs/specs/lam/evaluation-kpi.md`）

#### C: docs/specs/ 直下に配置 + ファイル名でプレフィックス分離

`lam-` プレフィックスを付与（例: `lam-green-state-definition.md`）。

**メリット**: 1 ディレクトリで管理でき、名前で区別可能
**デメリット**: LAM テンプレートの元ファイル名と異なるため、アップデート時の対応が面倒

#### D: 影式用に内容を編集して docs/specs/ 直下に配置

影式に不要な部分（Web フレームワーク前提の記述等）を削除し、影式固有の注記を追加。

**メリット**: 影式に最適化された仕様書
**デメリット**: LAM テンプレートとの差分管理が困難。将来のアップデート時にマージが複雑

### 推奨案: **選択肢B（docs/specs/lam/ サブディレクトリ）**

理由:

1. **関心の分離**: 影式固有仕様（`docs/specs/kage-shiki/`）と LAM フレームワーク仕様が明確に分かれる。影式の SSOT 構造と整合
2. **参照パスの変更は軽微**: コマンドやエージェントで参照している箇所は `daily.md` の `docs/specs/evaluation-kpi.md` のみ。これを `docs/specs/lam/evaluation-kpi.md` に変更すればよい
3. **アップデート容易性**: 将来 LAM v4.x → v5.x の移行時に、`docs/specs/lam/` を丸ごと差し替えできる
4. **内容はそのままコピー**: 影式向けの編集は行わない。LAM 仕様書はフレームワークの参照定義であり、プロジェクト固有の編集は入れるべきでない。影式固有の解釈が必要な場合は別文書で注記する

### 配置構造

```
docs/specs/
├── lam/                              ← 新規ディレクトリ
│   ├── v4.0.0-immune-system-requirements.md
│   ├── v4.0.0-immune-system-design.md
│   ├── green-state-definition.md
│   ├── evaluation-kpi.md
│   ├── loop-log-schema.md
│   ├── doc-writer-spec.md
│   └── v3.9.0-improvement-adoption.md
└── kage-shiki/                       ← 既存の影式固有仕様
    └── ...
```

---

## まとめ: 推奨案一覧

| 判断 | 推奨案 | Phase 2 での作業量 |
|------|--------|-------------------|
| 1. モデル選択 | quality-auditor=opus維持、test-runner=haiku変更 | 小（frontmatter変更のみ） |
| 2. full-review | LAM 4.0.1 ベース + 自動ループは手動フォールバック | 大（コマンド全面書き換え） |
| 3. ship.md | doc-sync-flag フォールバック付き統合設計 | 中（Phase 2 に分岐追加） |
| 4. 影式固有 | retro/wave-plan は frontmatter追加、project-status は Wave+KPI統合 | 小〜中 |
| 5. スキル | version追加、ループ統合追加、ui-design-guide はスコープ外 | 小〜中 |
| 6. LAM 仕様書 | docs/specs/lam/ にそのままコピー | 小（ファイルコピー） |

### Phase 2 作業の推奨順序

1. エージェント frontmatter 更新（判断1） — 基盤、他の作業に影響
2. full-review.md 移行（判断2） — 最大の変更、早期に着手
3. 他コマンドの差分適用（判断3, 4） — full-review と並行可
4. スキル更新（判断5） — 独立作業
5. LAM 仕様書取り込み（判断6） — 独立作業、最後でよい
