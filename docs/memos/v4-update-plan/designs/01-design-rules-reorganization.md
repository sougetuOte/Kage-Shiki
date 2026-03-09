# 設計: Rules ファイル再編

**作成日**: 2026-03-10
**ステータス**: Draft — 承認待ち
**対象 Phase**: Phase 1（基盤移行）

---

## 概要

LAM v3.x → v4.0.1 移行において、`.claude/rules/` 配下のファイル構成を再編する。
基本方針は 000-index.md の「Template-First」に従い、LAM 4.0.1 をベースとして影式固有カスタマイズを上乗せする。

### 移行後ファイル構成（結論先出し）

```
.claude/rules/
├── core-identity.md          # LAM 4.0.1 ベース + 影式固有（Subagent委任）
├── decision-making.md        # LAM 4.0.1 ベース（SSOT 参照追加のみ）
├── phase-rules.md            # LAM 4.0.1 ベース + 影式固有（A-3, L-4, S-2）
├── security-commands.md      # LAM 4.0.1 ベース + 影式 Python コマンド
├── permission-levels.md      # 新規（影式パス分類カスタマイズ済み）
├── upstream-first.md         # 新規（そのまま適用）
├── building-checklist.md     # 影式固有を保持（R-2〜R-11）※再編
├── auto-generated/
│   ├── README.md             # 新規（そのまま適用）
│   └── trust-model.md        # 新規（そのまま適用）
└── (廃止) audit-fix-policy.md
    (廃止) spec-sync.md
```

**ファイル数**: 8 → 9（+2 新規、-2 廃止、+1 ディレクトリ）

---

## 判断1: rules ファイルの再編方針

### 1-A: building-checklist.md の再編

#### 選択肢

| # | 案 | 説明 |
|---|---|------|
| A1 | **phase-rules.md に全統合** | R-1〜R-11, S-1〜S-4 すべてを phase-rules.md に記載。building-checklist.md を廃止 |
| A2 | **並存（現行維持）** | phase-rules.md は LAM 4.0.1 のまま（R-1, R-4, S-1, S-3, S-4）。building-checklist.md に R-2〜R-11, S-2 を維持 |
| A3 | **再編並存** | phase-rules.md に LAM コア + 拡張ポイント参照を記載。building-checklist.md を影式固有ルール（R-2〜R-11, S-2）のみに絞り、R-1/R-4/S-1/S-3/S-4 の重複を削除 |

#### 比較

| 観点 | A1 全統合 | A2 並存維持 | A3 再編並存 |
|------|----------|------------|------------|
| ファイル数 | 少（1ファイル） | 現状維持 | 現状維持 |
| phase-rules.md の肥大化 | 大（200行超） | なし | なし |
| 重複排除 | 完全 | R-1/R-4/S-1 等が重複 | 完全 |
| LAM テンプレートとの差分管理 | 困難（影式固有が混入） | 容易（別ファイル） | 容易（別ファイル） |
| 将来の LAM アップデート追従 | 困難 | 容易 | 容易 |
| 検索性（ルール番号で即座に見つかるか） | 良（1箇所） | 良（番号体系で分かる） | 良（番号体系で分かる） |

#### 決定: A3（再編並存）

**理由**:
- LAM 4.0.1 の拡張ポイント `(プロジェクト固有ルールを R-5 以降に追加可)` の設計意図に合致
- phase-rules.md を LAM テンプレートに近い状態に保つことで、将来の LAM アップデート追従が容易
- R-1/R-4/S-1/S-3/S-4 の重複を排除し、SSOT を明確にする
- 衝突解決ポリシー（000-index.md Section 4）の「並存」方針にも合致

#### 移行後の building-checklist.md 構成

```markdown
# 影式 BUILDING 品質チェックリスト（プロジェクト固有）

> LAM コアルール（R-1, R-4, S-1, S-3, S-4）は phase-rules.md を参照。
> 本ファイルは Phase 1 Retro / L-1〜L-5 由来の影式固有ルールを定義する。

## Red（テスト作成時）
- R-5: 異常系テストの義務

## Green（実装時）
- R-2: 有限セットは dict ディスパッチ
- R-3: 定数定義 → 使用の即時接続
- R-6: else のデフォルト値禁止

## Green 直後（実装完了時）
- R-11: Green 直後 3 点ミニチェック（(a) カプセル化, (b) R-6 再確認, (c) S-1 仕様突合）
- R-5 続: カバレッジ確認（各モジュール 90% 以上）
- R-7: スレッド安全性チェック（L-1 由来）
- R-8: 永続状態の「2回目起動」テスト（L-2 由来）
- R-9: シャットダウン経路の一意性チェック（L-3 由来）
- R-10: GUI 変更時の目視確認（L-5 由来）

## 仕様同期（影式固有補足）
- S-2: Protocol 外メソッドの明示
- S-1 補足: NFR（非機能要件）も突合対象に含める
```

### 1-B: spec-sync.md の廃止

#### 選択肢

| # | 案 | 説明 |
|---|---|------|
| B1 | **廃止** | S-1/S-3/S-4 は phase-rules.md に統合済み。S-2 と NFR 注記を building-checklist.md に移動 |
| B2 | **維持** | 現行のまま独立ファイルとして保持 |

#### 比較

| 観点 | B1 廃止 | B2 維持 |
|------|--------|--------|
| SSOT | 明確（phase-rules.md が S-1/S-3/S-4 の SSOT） | S-1 が 2 箇所に存在（曖昧） |
| LAM テンプレートとの整合 | 完全一致（LAM 4.0.1 に spec-sync.md なし） | 不整合（影式独自ファイル） |
| 影式固有情報の保全 | S-2 と NFR 注記は building-checklist.md で保全 | 全情報保全 |

#### 決定: B1（廃止）

**理由**:
- S-1/S-3/S-4 は LAM 4.0.1 の phase-rules.md に既に含まれており、SSOT の二重化を避ける
- 影式固有の S-2 と NFR 注記は building-checklist.md に移動することで保全される
- 000-index.md Section 5 の Phase 1 作業項目にも「spec-sync.md → S-2 を building-checklist.md に移動、ファイル自体は廃止」と記載済み

### 1-C: audit-fix-policy.md の廃止

#### 選択肢

| # | 案 | 説明 |
|---|---|------|
| C1 | **廃止** | A-3（修正後の再検証）を phase-rules.md の AUDITING セクションに統合。残りは PG/SE/PM で代替 |
| C2 | **PG/SE/PM と並存** | audit-fix-policy.md を影式固有ルールとして維持し、PG/SE/PM と両立させる |
| C3 | **再編して維持** | A-1 を PG/SE/PM 準拠に書き換え、A-3 は維持 |

#### 比較

| 観点 | C1 廃止 | C2 並存 | C3 再編維持 |
|------|--------|--------|------------|
| 矛盾解消 | 完全（PG/SE/PM が唯一の修正ルール） | A-1 と PM級禁止が矛盾 | 部分的 |
| 影式の A-3（再検証義務）保全 | phase-rules.md に統合 | 保全 | 保全 |
| ファイル数 | 削減 | 維持 | 維持 |
| 運用の明確性 | 高（修正ルールが 1 箇所） | 低（2 箇所参照） | 中 |

#### 決定: C1（廃止）

**理由**:
- A-1（全重篤度への対応義務）は LAM 4.0.1 の PM級制限と矛盾する。PM級の問題は AUDITING で修正禁止（指摘のみ）とするのが v4.0.0 の設計意図
- A-2（対応不可 Issue の明示）は PM級の承認ゲートに自然に包含される
- A-3（修正後の再検証: テスト追加、ruff check、全テスト実行）は影式固有の品質基準として価値が高い。phase-rules.md の AUDITING セクションにインライン化して保持する
- A-4（仕様ズレの同時修正）は S-1/S-4 でカバー済み
- 衝突解決ポリシー（000-index.md Section 4）で「audit-fix-policy.md → A-3 を phase-rules.md に統合、ファイル自体は廃止」と記載済み

---

## 判断2: phase-rules.md のマージ戦略

### 選択肢

| # | 案 | 説明 |
|---|---|------|
| D1 | **LAM 4.0.1 ベース + 影式追記** | LAM 4.0.1 の phase-rules.md を採用し、影式固有セクションを末尾やインラインに追記 |
| D2 | **現行ベース + LAM 差分パッチ** | 現行の phase-rules.md をベースに、LAM 4.0.1 の追加要素を差し込む |
| D3 | **完全新規作成** | 両者を統合した新しい phase-rules.md をゼロから作成 |

### 比較

| 観点 | D1 LAM ベース | D2 現行ベース | D3 新規作成 |
|------|-------------|-------------|------------|
| LAM テンプレート追従性 | 高 | 低 | 中 |
| 影式固有の保全 | 追記で保全 | 自然に保全 | 設計次第 |
| 作業量 | 中（追記のみ） | 中（差分適用） | 大 |
| 将来のアップデート | 容易（差分が明確） | 困難（ベースが独自） | 困難 |

### 決定: D1（LAM 4.0.1 ベース + 影式追記）

**理由**: Template-First 方針に合致。影式固有部分は明確にマーク付けすることで、将来の LAM アップデート時に影式追記部分を特定しやすくなる。

### 移行後の phase-rules.md セクション構成

```markdown
# フェーズ別ガードレール

## PLANNING
### 承認ゲート                    ← LAM 4.0.1 と同一
### 禁止                          ← LAM 4.0.1 と同一
### 許可                          ← LAM 4.0.1 と同一

---

## BUILDING
### 必須                          ← LAM 4.0.1 と同一
### TDD 品質チェック              ← LAM 4.0.1（R-1, R-4 + 影式拡張への参照リンク）
### 仕様同期ルール                ← LAM 4.0.1（S-1, S-3, S-4）
### TDD 内省パイプライン          ← LAM 4.0.1 新規（Wave 4）
### 禁止                          ← LAM 4.0.1 と同一

### 影式固有: Phase 完了判定（L-4 由来）  ← 影式追記
  1. python -m kage_shiki で起動、基本操作確認
  2. 2回目の起動で永続状態の引き継ぎ確認
  3. 終了操作後のプロセス残存なし確認
  テストカバレッジが高くても、実動作テスト未実施では Phase 完了としない。

---

## AUDITING
### AUDITING での修正ルール（v4.0.0）  ← LAM 4.0.1 新規（PG/SE/PM）
### 必須                          ← LAM 4.0.1 ベース
  + `/full-review` で監査→修正→検証を一気通貫で実施可能（影式追記）
### コード品質チェック            ← LAM 4.0.1 と同一
### コード明確性チェック          ← LAM 4.0.1 と同一
### ドキュメント・アーキテクチャ  ← LAM 4.0.1 と同一
### 改善提案の禁止事項            ← LAM 4.0.1 と同一
### レポート形式                  ← LAM 4.0.1 と同一

### 影式固有: 修正後の再検証義務（A-3 由来）  ← 影式追記
  修正した Issue については以下を実施:
  1. テスト追加（テストで検証可能な場合）
  2. ruff check でリント通過確認
  3. 全テスト実行で回帰なし確認

### 影式固有: 監査レポート完了条件  ← 影式追記
  対応可能な Issue（PG/SE級）: X件中 X件修正済み
  PM級 Issue: X件（指摘のみ、承認ゲートへ）
  テスト結果: 全件 PASSED
  ruff: All checks passed

---

## フェーズ警告テンプレート        ← LAM 4.0.1 と同一
```

### AUDITING 修正ルール変更の受け入れ

**変更内容**: 「修正禁止（指摘のみ）」→「PG/SE 級は許可、PM 級のみ禁止」

**受け入れ判断**: 受け入れる

**理由**:
- 現行の影式では audit-fix-policy.md で事実上「全修正」を義務化しており、phase-rules.md の「修正禁止」と矛盾していた
- PG/SE/PM の三段階分類により、この矛盾が解消される
- PG/SE 級の即時修正は影式の実運用でも効率改善になる
- PM 級の承認ゲートにより、アーキテクチャ判断を伴う修正は人間が関与する
- 衝突解決ポリシー（000-index.md Section 4）で「LAM 4.0.1 採用」と記載済み

### Phase 完了判定スモークテスト（L-4 由来）の配置

**配置先**: phase-rules.md の BUILDING セクション末尾に「影式固有」セクションとして追記

**理由**:
- デスクトップアプリケーション固有の要件であり、LAM 汎用テンプレートにはない
- BUILDING セクション内に配置することで、Phase 完了判定時に自然に参照される
- 「影式固有:」プレフィックスにより、LAM テンプレート部分との区別が明確

---

## 判断3: core-identity.md と security-commands.md のマージ

### 3-A: core-identity.md

#### Subagent 委任判断テーブルの扱い

**選択肢**:

| # | 案 | 説明 |
|---|---|------|
| E1 | **削除** | LAM 4.0.1 に倣い削除。docs/internal/ に情報があれば十分 |
| E2 | **core-identity.md に維持** | 現行のまま保持 |
| E3 | **CLAUDE.md に移動** | core-identity.md からは削除し、CLAUDE.md の Execution Modes 近辺に移動 |

**決定**: E2（core-identity.md に維持）

**理由**:
- 影式では Subagent 委任（lam-orchestrate）を実際に運用しており、判断基準が rules に記載されていることで毎セッション参照される
- LAM 4.0.1 で削除された理由は汎用テンプレート化（プロジェクト固有）であり、影式固有として維持する正当性がある
- コンテキスト節約原則の 3 項目も同様に維持する（Subagent 運用時の実践的ガイドライン）

#### 権限等級セクションの追加

LAM 4.0.1 の権限等級（PG/SE/PM）サマリーセクションをそのまま追加する。

#### 移行後の core-identity.md 構成

```markdown
# Living Architect 行動規範

## Active Retrieval（能動的検索原則）
  ← LAM 4.0.1 と同一（3 項目）

## 権限等級（PG/SE/PM）
  ← LAM 4.0.1 新規追加（PG/SE/PM サマリー + permission-levels.md 参照）

## Subagent 委任判断                ← 影式固有（維持）
  テーブル（4 条件）

## コンテキスト節約原則              ← 影式固有（維持）
  3 項目

## Context Compression
  ← LAM 4.0.1 と同一
```

### 3-B: security-commands.md

#### Python 固有コマンドの扱い

**決定**: Allow List に Python カテゴリを維持

**理由**:
- 影式は Python プロジェクトであり、`python`, `python -m pytest`, `python -m ruff`, `pip` 等は日常的に使用
- LAM 4.0.1 で削除された理由は汎用テンプレート化（言語非依存）であり、影式固有として維持する正当性がある
- Layer 0（プロンプティング）として Allow List に記載することで、settings.json の Layer 1 設定と整合する

#### Layer 0/1/2 三層モデルの導入

**決定**: LAM 4.0.1 の「v4.0.0: ネイティブ権限モデルへの移行」セクションをそのまま追加

**理由**:
- 三層モデルは LAM 4.0.1 の構造改善であり、影式でも有用
- hooks 実装（Phase 3）の前提知識としても必要
- 既存の Allow/Deny List は Layer 0 として引き続き有効

#### 移行後の security-commands.md 構成

```markdown
# コマンド実行安全基準

## Allow List（自動実行可）
  ← LAM 4.0.1 ベース + 影式 Python カテゴリ維持
  | Python | `python`, `python -m pytest`, `python -m ruff`, `python -c`, `pip`, `pyenv` |

## 高リスクコマンド（Layer 0: 承認必須）  ← セクション名変更（LAM 4.0.1）
  ← LAM 4.0.1 ベース（`python main.py` 追加）
  末尾の説明文を LAM 4.0.1 版に更新（Layer 1 参照追加）

## v4.0.0: ネイティブ権限モデルへの移行    ← LAM 4.0.1 新規追加
  Layer 0/1/2 の三層構造説明
  permission-levels.md 参照
```

---

## 判断4: 新規ルールファイルの影式カスタマイズ

### 4-A: permission-levels.md のファイルパス分類

#### 選択肢

| # | 案 | 説明 |
|---|---|------|
| F1 | **LAM 4.0.1 をそのまま適用** | `src/` 等の汎用パスパターンのまま使用 |
| F2 | **影式パス構造に合わせてカスタマイズ** | `src/kage_shiki/`, `config.toml` 等を追加 |

#### 決定: F2（影式パス構造に合わせてカスタマイズ）

**理由**:
- LAM 4.0.1 の permission-levels.md 自体に「ファイルパスベースの分類（PreToolUse hook 用）」テーブルがあり、プロジェクト固有のカスタマイズが想定されている
- 影式のディレクトリ構造（`src/kage_shiki/`, `config/`, `docs/internal/` 等）に合わせることで、Phase 3 の hooks 実装時にそのまま利用できる

#### 移行後の permission-levels.md ファイルパステーブル

LAM 4.0.1 のテーブルをベースに、以下の影式固有パスを追加:

```markdown
## ファイルパスベースの分類（PreToolUse hook 用）

| パスパターン | 等級 | 理由 |
|-------------|------|------|
| `docs/specs/*.md` | PM | 仕様変更 |
| `docs/adr/*.md` | PM | アーキテクチャ変更 |
| `docs/internal/*.md` | PM | プロセス SSOT 変更（影式固有） |
| `.claude/rules/*.md`, `.claude/rules/*/*.md` | PM | ルール変更 |
| `.claude/settings*.json` | PM | 設定変更 |
| `pyproject.toml` | PM | プロジェクト設定変更（影式固有） |
| `docs/` 配下（上記以外） | SE | ドキュメント更新 |
| `src/kage_shiki/` 配下 | SE | ソースコード変更（影式固有） |
| `tests/` 配下 | SE | テストコード変更 |
| `config/` 配下 | SE | 設定ファイル変更（影式固有） |
| その他 | SE | 安全側に倒す |
```

**変更点**:
- `src/` → `src/kage_shiki/`（影式のパッケージ構造）
- `docs/internal/*.md` を PM級に追加（SSOT であるため）
- `pyproject.toml` を PM級に追加
- `tests/` 配下を SE級として明示
- `config/` 配下を SE級として明示

#### 移行後の permission-levels.md 全体構成

```markdown
# 権限等級分類基準

## PG級（自動修正・報告不要）      ← LAM 4.0.1 と同一
## SE級（修正後に報告）            ← LAM 4.0.1 と同一
## PM級（判断を仰ぐ）             ← LAM 4.0.1 と同一

## フェーズとの二軸設計            ← LAM 4.0.1 と同一

## ファイルパスベースの分類        ← 影式カスタマイズ（上記テーブル）

## 迷った場合                      ← LAM 4.0.1 ベース + 影式固有の典型例追加
  追加例:
  - 「config.toml テンプレートの変更」→ PM級（設定仕様の変更）
  - 「docs/internal/ の変更」→ PM級（SSOT）
  - 「tests/ の新規テスト追加」→ SE級

## 参照                            ← LAM 4.0.1 と同一
```

### 4-B: upstream-first.md のそのまま適用可否

#### 選択肢

| # | 案 | 説明 |
|---|---|------|
| G1 | **そのまま適用** | LAM 4.0.1 の upstream-first.md を無変更で配置 |
| G2 | **影式固有の注記を追加** | context7 MCP の利用可能確認結果、影式固有の除外対象を追記 |

#### 決定: G1（そのまま適用）

**理由**:
- upstream-first.md は Claude Code プラットフォーム機能に関する汎用的なルールであり、プロジェクト固有のカスタマイズが不要
- 影式では `mcp__plugin_context7_context7` が利用可能であり、確認手順の context7 MCP が使える
- 影式固有のプラットフォーム依存（pystray, tkinter 等）はこのルールの対象外であり、混在させるべきでない
- 公式 URL の最新性は運用時に確認すればよく、ファイル自体の変更は不要

---

## 移行作業サマリー

### 新規作成

| ファイル | 内容 | カスタマイズ |
|---------|------|------------|
| `permission-levels.md` | 権限等級分類基準 | ファイルパステーブルを影式用に定義 |
| `upstream-first.md` | 上流仕様優先原則 | なし（そのまま適用） |
| `auto-generated/README.md` | TDD 内省ルールのライフサイクル | なし（そのまま適用） |
| `auto-generated/trust-model.md` | 信頼度モデル | なし（そのまま適用） |

### 更新

| ファイル | 主な変更 |
|---------|---------|
| `phase-rules.md` | TDD 品質チェック/仕様同期統合、AUDITING 修正ルール変更、TDD 内省追加、影式固有（A-3, L-4）追記 |
| `core-identity.md` | 権限等級セクション追加、Subagent 委任/コンテキスト節約は維持 |
| `security-commands.md` | Layer 0/1/2 三層モデル追加、セクション名変更、Python コマンドは維持 |
| `building-checklist.md` | R-1/R-4/S-1/S-3/S-4 の記載を削除（phase-rules.md に委譲）、S-2/NFR 注記を移入 |
| `decision-making.md` | SSOT 参照注記の 1 行追加のみ |

### 廃止

| ファイル | 理由 | 移行先 |
|---------|------|--------|
| `audit-fix-policy.md` | PG/SE/PM モデルに統合。A-3 のみ phase-rules.md に移動 | phase-rules.md AUDITING セクション |
| `spec-sync.md` | S-1/S-3/S-4 は phase-rules.md に統合済み。S-2/NFR は building-checklist.md に移動 | phase-rules.md + building-checklist.md |

### 変更なし

| ファイル | 備考 |
|---------|------|
| なし | 全ファイルに何らかの変更あり |

---

## リスクと緩和策

| リスク | 影響度 | 緩和策 |
|-------|-------|--------|
| phase-rules.md の肥大化（影式追記により） | 低 | 影式固有セクションは最小限に抑え、詳細は building-checklist.md に委譲 |
| audit-fix-policy.md 廃止による運用知識の散逸 | 低 | A-3 は phase-rules.md に統合、監査レポート完了条件も移植 |
| R-1〜R-11 の番号体系が 2 ファイルに分散 | 低 | phase-rules.md の TDD 品質チェックに building-checklist.md への参照リンクを記載 |
| 将来の LAM アップデートで phase-rules.md が再変更される | 中 | 影式固有セクションに「影式固有:」プレフィックスを付け、マージ時に識別可能にする |

---

## 検証チェックリスト（Phase 1 実装時に使用）

- [ ] 全 rules ファイルが Markdown として構文エラーなし
- [ ] phase-rules.md に R-1, R-4, S-1, S-3, S-4 が記載されている
- [ ] phase-rules.md に影式固有の A-3（再検証義務）が記載されている
- [ ] phase-rules.md に影式固有の L-4（スモークテスト）が記載されている
- [ ] building-checklist.md に R-2, R-3, R-5〜R-11, S-2 が記載されている
- [ ] building-checklist.md から R-1, R-4, S-1, S-3, S-4 の重複が排除されている
- [ ] core-identity.md に権限等級セクションが追加されている
- [ ] core-identity.md に Subagent 委任判断が維持されている
- [ ] security-commands.md に Python コマンドが維持されている
- [ ] security-commands.md に Layer 0/1/2 セクションが追加されている
- [ ] permission-levels.md のファイルパステーブルが影式用にカスタマイズされている
- [ ] upstream-first.md が LAM 4.0.1 と同一内容で配置されている
- [ ] auto-generated/ ディレクトリが作成されている
- [ ] audit-fix-policy.md が削除されている（または .deprecated に移動）
- [ ] spec-sync.md が削除されている（または .deprecated に移動）
- [ ] Claude Code 起動時にルールファイルが正常に読み込まれること
