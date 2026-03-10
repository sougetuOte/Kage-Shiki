# CLAUDE.md / CHEATSHEET.md 差分分析

## 概要

LAM 4.0.1 は v4.0.0 で導入された「免疫システム」（権限等級 PG/SE/PM、hooks、TDD 内省パイプライン）を中心とした大規模アップデートである。CLAUDE.md はプロジェクト固有情報を除去しテンプレート化（汎用化）されており、CHEATSHEET.md には新機能の操作ガイドが追加されている。影式プロジェクト固有のカスタマイズ（Project Overview、技術スタック、building-checklist 等）は LAM テンプレートには存在せず、マージ時に手動で保持する必要がある。

主要な変更点:
1. **権限等級（PG/SE/PM）の導入**: 全ファイル変更に対するリスク分類の三段階モデル
2. **hooks 機構の追加**: PreToolUse / PostToolUse / Stop / PreCompact の自動化
3. **TDD 内省パイプライン**: テスト失敗パターンの自動記録とルール候補の自動生成
4. **AUDITING フェーズの緩和**: PG/SE 級の修正を許可（従来は修正禁止）
5. **Upstream First 原則**: プラットフォーム仕様の事前確認を義務化
6. **CLAUDE.md のスリム化**: プロジェクト固有情報を除去し、テンプレートとして汎用化

---

## CLAUDE.md 差分

### 新規追加セクション

LAM 4.0.1 の CLAUDE.md には現行にない新規セクションは存在しない。構造的には現行の方がセクション数が多い。LAM 4.0.1 はむしろ CLAUDE.md を最小限に絞り、詳細を `.claude/rules/` や CHEATSHEET.md に委譲する設計思想に変わっている。

### 変更セクション

#### 1. Identity

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| プロジェクト名 | `影式 (Kage-Shiki)` を明記 | `本プロジェクト` と汎用表記 |
| Project Scale | `Medium` | `Medium to Large` |

- **変更の意図**: テンプレートとしての汎用化。影式固有の名称を除去し、どのプロジェクトにも適用可能にした。Project Scale は `Medium to Large` に拡張され、より大規模なプロジェクトへの対応を示唆。

#### 2. References テーブル

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| 設計文書行 | `docs/memos/middle-draft/` を含む | 行自体が削除 |
| 概念説明スライド | あり | あり（同一） |

- **変更の意図**: `docs/memos/middle-draft/` は影式固有のディレクトリ。テンプレートでは不要なため削除。

#### 3. Initial Instruction

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| 報告文言 | `影式 (Kage-Shiki) プロジェクトの「Living Architect Model」として振る舞う準備ができているかを報告せよ` | `「Living Architect Model」として振る舞う準備ができているかを報告せよ` |

- **変更の意図**: プロジェクト固有名称の除去（テンプレート汎用化）。

#### 4. security-commands.md（rules 内）

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| セクション名 | `Deny List（承認必須）` | `高リスクコマンド（Layer 0: 承認必須）` |
| Allow List | `Python` カテゴリに `python`, `python -m pytest`, `python -m ruff`, `python -c`, `pip`, `pyenv` を含む | `Python` カテゴリなし（言語固有コマンドを除去） |
| 実行例 | `npm start`, `make` | `npm start`, `python main.py`, `make` |
| Layer 説明 | なし | `v4.0.0: ネイティブ権限モデルへの移行` セクションを追加。Layer 0/1/2 の三層構造を説明 |
| 末尾注記 | なし | Layer 1（`settings.json`）と Layer 2（`PreToolUse hook`）への参照を追加 |

- **変更の意図**: コマンド安全基準を三層モデル（Layer 0: プロンプティング、Layer 1: settings.json、Layer 2: hooks）に拡張。Python 固有コマンドは Allow List からは除去されたが、Layer 1 の settings.json で管理する設計に移行。

#### 5. core-identity.md（rules 内）

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| Subagent 委任判断 | テーブルあり（4 条件） | 削除 |
| コンテキスト節約原則 | 3 項目あり | 削除 |
| 権限等級セクション | なし | PG/SE/PM の説明を追加 |

- **変更の意図**: Subagent 委任判断とコンテキスト節約原則は `docs/internal/` に移動したと推定。代わりに v4.0.0 の中核概念である権限等級の要約を配置。

#### 6. decision-making.md（rules 内）

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| SSOT 参照 | なし | `> **SSOT**: docs/internal/06_DECISION_MAKING.md。本ファイルは実行時の要約版。` を追加 |

- **変更の意図**: SSOT の所在を明示し、rules ファイルが要約版であることを明確化。

#### 7. phase-rules.md（rules 内）

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| BUILDING - TDD 品質チェック | なし（building-checklist.md で管理） | R-1, R-4 を直接記載（最小限） |
| BUILDING - 仕様同期ルール | なし（spec-sync.md で管理） | S-1, S-3, S-4 を直接記載 |
| BUILDING - TDD 内省パイプライン | なし | Wave 4 の TDD 内省パイプラインの説明を追加 |
| BUILDING - Phase 完了判定 | L-4 由来のスモークテスト（影式固有） | 削除（テンプレート汎用化） |
| AUDITING - 修正ルール | `修正禁止（指摘のみ）` | PG/SE 級は許可、PM 級のみ禁止に緩和 |
| AUDITING - 全般 | `audit-fix-policy.md` 参照 | `audit-fix-policy.md` への参照なし（inline 化） |
| AUDITING - PG/SE/PM 分類 | なし | 問題の権限等級分類を必須に |

- **変更の意図**: AUDITING フェーズの大幅緩和が最大の変更。従来は「修正の直接実施禁止」だったが、PG/SE 級の修正を許可し、PM 級のみ承認ゲートとした。また、TDD 品質チェックと仕様同期ルールを phase-rules.md に集約し、別ファイル参照を減らした。

### 削除セクション

#### 1. Project Overview

現行 CLAUDE.md にある技術スタックテーブル（Python 3.12+, tkinter, pystray, anthropic, SQLite + FTS5, TOML, pytest）が LAM 4.0.1 では完全に削除されている。

- **理由**: テンプレートとしての汎用化。プロジェクト固有の技術選定情報は各プロジェクトが独自に記載する想定。

### 削除された rules ファイル

#### 1. building-checklist.md

現行にある R-1 ~ R-11 の詳細な TDD 品質チェックリストが LAM 4.0.1 のテンプレートには存在しない。

- **理由**: R-1, R-4 のみ phase-rules.md に統合。R-2 ~ R-11 は影式プロジェクトの Phase 1 Retro で生成された固有ルールであり、テンプレートには含まれない。

#### 2. spec-sync.md

現行にある S-1 ~ S-4 の仕様同期ルールが独立ファイルとしては存在しない。

- **理由**: S-1, S-3, S-4 は phase-rules.md の BUILDING セクションに統合。S-2（Protocol 外メソッドの明示）は影式固有ルールとして省略。

#### 3. audit-fix-policy.md

現行にある A-1 ~ A-4 の監査修正ポリシーが LAM 4.0.1 のテンプレートには存在しない。

- **理由**: AUDITING フェーズの修正ルールが PG/SE/PM 分類に置き換わったため、従来の「全 Issue 修正義務」ポリシーは不要になった。ただし影式では A-1 ~ A-4 を引き続き有用なプロジェクト固有ルールとして保持する価値がある。

### 新規追加された rules ファイル（LAM 4.0.1 にのみ存在）

#### 1. permission-levels.md

PG/SE/PM の三段階権限分類の詳細定義。ファイルパスベースの分類基準、フェーズとの二軸設計を含む。v4.0.0 の中核機能。

#### 2. upstream-first.md

Claude Code のプラットフォーム機能（hooks, settings, permissions 等）を実装する際に、公式ドキュメントを事前確認する義務を定めたルール。context7 MCP / WebFetch でのフォールバック手順を含む。

#### 3. auto-generated/ ディレクトリ

TDD 内省パイプラインによる自動生成ルールの格納先。`README.md`（ライフサイクル説明）と `trust-model.md`（信頼度モデル定義）を含む。

### 新規追加された構造要素（LAM 4.0.1 にのみ存在）

#### 1. `.claude/hooks/` ディレクトリ

- `pre-tool-use.sh`: ファイルパスベースの PG/SE/PM 自動判定
- `post-tool-use.sh`: テスト失敗パターンの自動記録
- `lam-stop-hook.sh`: Stop イベントのハンドリング
- `pre-compact.sh`: コンパクト前の自動セーブ
- `tests/`: hooks のテストスクリプト群

#### 2. `.claude/settings.json`

ネイティブ権限モデル（Layer 1）の設定。Allow/Ask/Deny のコマンド分類。

#### 3. `.claude/logs/` ディレクトリ

権限判定ログ（`permission.log`）やループ検出ログの格納先。

#### 4. `.claude/states/v4.0.0-immune-system.json`

v4.0.0 免疫システム機能の進捗状態管理。

#### 5. 新規コマンド: `/pattern-review`

TDD 内省パイプラインで蓄積されたパターンとルール候補を審査するコマンド。

#### 6. 新規コマンド: `/release`

リリースフロー（CHANGELOG -> commit -> push -> tag）を実行するコマンド。

#### 7. 新規スキル: `ui-design-guide`

UI 設計ガイドのスキル（現行には存在しない）。

### 影式固有カスタマイズ（保持すべき）

以下は現行 CLAUDE.md で影式プロジェクト固有にカスタマイズされた内容であり、LAM テンプレートには存在しないが、マージ時に保持する必要がある。

#### CLAUDE.md 内

1. **Identity のプロジェクト名**: `影式 (Kage-Shiki)` の名称と説明文
2. **Project Overview セクション全体**: 技術スタックテーブル（Python 3.12+, tkinter, pystray, anthropic, SQLite + FTS5, TOML, pytest）
3. **References の設計文書行**: `docs/memos/middle-draft/`
4. **Initial Instruction のプロジェクト名**: `影式 (Kage-Shiki) プロジェクトの` の修飾

#### rules ファイル内

5. **building-checklist.md**: R-2 ~ R-11 の影式固有チェックリスト項目（Phase 1 Retro / L-1 ~ L-5 由来）
6. **spec-sync.md の S-2**: Protocol 外メソッドの明示ルール（影式の Protocol アーキテクチャ固有）
7. **audit-fix-policy.md**: A-1 ~ A-4 の監査修正ポリシー全体
8. **phase-rules.md の Phase 完了判定**: L-4 由来のスモークテスト（`python -m kage_shiki` での実動作確認）
9. **security-commands.md の Python カテゴリ**: `python`, `python -m pytest`, `python -m ruff`, `python -c`, `pip`, `pyenv` の Allow List

---

## CHEATSHEET.md 差分

### 新規追加セクション

#### 1. 権限等級（PG/SE/PM）セクション

LAM 4.0.1 で新設。PG/SE/PM の三段階分類テーブル、PreToolUse hook の説明、フック分類の誤判定率計測手順を含む。現行には存在しない。

#### 2. 補助コマンドセクション

現行では「ワークフローコマンド」に全コマンドが列挙されていたが、LAM 4.0.1 では「ワークフローコマンド」と「補助コマンド」に分離。`/daily` に「KPI 集計含む」の説明が追加。`/impact-analysis` に「PG/SE/PM 分類含む」が追加。

#### 3. AoT クイックガイドの Atom テーブル形式

LAM 4.0.1 で追加:
```
| Atom | 内容 | 依存 | 並列可否(任意) |
```
現行にはこのテーブル形式の記載がない。

#### 4. クイックリファレンスの追加項目

LAM 4.0.1 で追加:
- 「次のセッションを始めるときは？」: `/quick-load` と `/full-load` の使い分け
- 「ADRはどこ？」: `docs/adr/`
- 「Rulesはどこ？」: `.claude/rules/`

現行にあって LAM 4.0.1 にない項目:
- 「変更をコミットしたい？」: `/ship`
- 「設計中間文書はどこ？」: `docs/memos/middle-draft/`

### 変更セクション

#### 1. タイトル

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| タイトル | `# 影式 (Kage-Shiki) チートシート` | `# Living Architect Model チートシート` |

- **変更の意図**: テンプレート汎用化。

#### 2. はじめに

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| セクション名 | `## はじめに` | `## はじめに（初めて使う方へ）` |
| 参照先 | 概念説明スライドのみ | 概念説明スライド + QUICKSTART.md |
| 手順 1 | `Claude Code CLI を起動する` | `Claude Code CLI を起動する（LAM の設定は自動で読み込まれる）` |
| 手順 2 | `プロジェクトルートで Claude が CLAUDE.md を読み込む` | `/planning で設計フェーズを開始し、要件を定義する` |
| 手順 3 | `/planning で設計フェーズを開始する` | `要件確定後、LAM をプロジェクトに適応させる（AI に依頼するだけ）` |

- **変更の意図**: 初心者向けの導線強化。QUICKSTART.md への誘導を追加。手順を 3 ステップに再構成し、LAM の自動読み込みと適応プロセスを明示。

#### 3. ディレクトリ構造

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| hooks/ | なし | `hooks/` ディレクトリを追加（PreToolUse / PostToolUse / Stop / PreCompact） |
| logs/ | なし | `logs/` ディレクトリを追加（permission.log, loop-*.json） |
| CLAUDE.md 説明 | `憲法（コア原則 + 技術スタック）` | `憲法（コア原則のみ）` |
| CHEATSHEET.md 説明 | `このファイル` | `このファイル（クイックリファレンス）` |
| docs/memos/middle-draft/ | あり | 削除 |

#### 4. Rules ファイル一覧

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| building-checklist.md | あり | 削除（phase-rules.md に統合） |
| spec-sync.md | あり | 削除（phase-rules.md に統合） |
| audit-fix-policy.md | あり | 削除（PG/SE/PM に置換） |
| permission-levels.md | なし | 新規追加（`v4.0.0 新規` タグ付き） |

#### 5. フェーズコマンド

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| `/auditing` 禁止事項 | `修正の直接実施禁止` | `PM級の修正禁止（PG/SE級は許可）` |

- **変更の意図**: AUDITING フェーズでの修正ルールの緩和を反映。

#### 6. サブエージェント

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| doc-writer 呼び出し例 | `「ドキュメントを更新して」` | `「ドキュメントを更新して」「仕様を策定して」` |

- **変更の意図**: doc-writer の用途拡大を反映。

#### 7. スキル

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| 表示順 | adr-template, spec-template, skill-creator, lam-orchestrate, ultimate-think | lam-orchestrate, ultimate-think, skill-creator, adr-template, spec-template |

- **変更の意図**: 使用頻度の高い lam-orchestrate と ultimate-think を上位に配置。

#### 8. ワークフローコマンド

| 項目 | 現行 | LAM 4.0.1 |
|------|------|-----------|
| `/ship` 説明 | `変更の棚卸し → 論理グループ分け → コミット → 手動作業通知` | `論理グループ分けコミット（棚卸し -> 分類 -> コミット）` |
| `/full-review` | `全ソース網羅レビュー + 全 Issue 修正（3エージェント並列監査）` | `並列監査 + 全修正 + 検証（一気通貫）` + `<対象>` 引数追加 |
| `/release` | なし | 新規追加: `リリース（CHANGELOG -> commit -> push -> tag）` |
| `/wave-plan` | あり | 削除（ワークフローコマンドから除外） |
| `/retro` | あり | 削除（ワークフローコマンドから除外） |

### 削除セクション

#### 1. プロジェクト技術スタック

現行にある技術スタックテーブル（Python 3.12+ 等）が LAM 4.0.1 では削除。テンプレート汎用化のため。

#### 2. 日常ワークフロー

現行にある以下のワークフロー記述が LAM 4.0.1 では削除:
- 一日の開始
- Wave 開始
- 作業中（TDD サイクル）
- Wave 終了
- Phase 終了
- 一日の終了
- 割り込み・中断

- **理由推定**: これらの詳細なワークフローは `docs/internal/02_DEVELOPMENT_FLOW.md` 等に委譲し、CHEATSHEET.md はコマンドリファレンスに特化する方針に変更。

### 影式固有カスタマイズ（保持すべき）

1. **タイトル**: `影式 (Kage-Shiki) チートシート` の名称
2. **プロジェクト技術スタック**: Python 3.12+ 等のテーブル全体
3. **building-checklist.md の Rules 一覧への記載**: R-1 ~ R-11
4. **spec-sync.md の Rules 一覧への記載**: S-1 ~ S-4
5. **audit-fix-policy.md の Rules 一覧への記載**: A-1 ~ A-4
6. **日常ワークフロー**: Wave ベースの作業フロー記述（影式で実際に運用中）
7. **クイックリファレンスの `/ship`**: 「変更をコミットしたい？」の項目
8. **クイックリファレンスの設計中間文書**: `docs/memos/middle-draft/` の参照

---

## 移行時の注意事項

### マージ戦略

LAM 4.0.1 テンプレートを「ベース」として採用し、影式固有カスタマイズを上乗せする **Template-First 戦略** を推奨する。

1. **CLAUDE.md**: LAM 4.0.1 をベースに、Project Overview（技術スタック）と Identity のプロジェクト名を手動追加
2. **CHEATSHEET.md**: LAM 4.0.1 をベースに、技術スタック・日常ワークフロー・影式固有の Rules 一覧を手動追加
3. **rules/**: LAM 4.0.1 の新規ファイル（permission-levels.md, upstream-first.md, auto-generated/）を導入し、既存の影式固有ルール（building-checklist.md, spec-sync.md, audit-fix-policy.md）は保持
4. **hooks/**: LAM 4.0.1 の hooks ディレクトリを新規導入
5. **settings.json**: LAM 4.0.1 の settings.json を導入し、影式固有の Python コマンド Allow を追加

### コンフリクト予測

| ファイル | コンフリクト箇所 | 解決方針 |
|---------|----------------|---------|
| `CLAUDE.md` | Identity セクション | LAM 4.0.1 ベース + 影式名称追加 |
| `CLAUDE.md` | Project Overview | LAM 4.0.1 にはないため手動追加 |
| `phase-rules.md` | BUILDING セクション | LAM 4.0.1 の TDD 品質チェック + 影式の R-2~R-11 を building-checklist.md で保持 |
| `phase-rules.md` | AUDITING セクション | LAM 4.0.1 の PG/SE/PM ベースに移行。audit-fix-policy.md は補助ルールとして保持 |
| `phase-rules.md` | Phase 完了判定 | 影式固有のスモークテスト（L-4 由来）を手動追加 |
| `core-identity.md` | Subagent 委任判断 | 影式で有用なら保持、不要なら削除 |
| `security-commands.md` | Allow List | LAM 4.0.1 ベース + Python コマンドカテゴリを手動追加 |
| `CHEATSHEET.md` | 日常ワークフロー | LAM 4.0.1 にはないため手動追加 |

### 推奨事項

1. **段階的移行**: 全ファイルを一度に差し替えるのではなく、以下の順序で移行する
   - Phase 1: CLAUDE.md + CHEATSHEET.md の更新
   - Phase 2: rules/ の更新（新規追加 -> 既存修正）
   - Phase 3: hooks/ + settings.json の導入
   - Phase 4: commands/ の差分確認と更新

2. **影式固有ルールの再配置**: building-checklist.md, spec-sync.md, audit-fix-policy.md は LAM テンプレートでは phase-rules.md に統合されているが、影式の詳細な R-2~R-11 等は独立ファイルとして保持する方が管理しやすい。phase-rules.md からの参照リンクを設ける形が望ましい。

3. **AUDITING 緩和の影響評価**: PG/SE 級の修正許可は影式の audit-fix-policy.md（A-1: 全重篤度への対応義務）と親和性が高い。両方を併用することで「PG/SE 級は自動修正可、PM 級は承認後に修正」という運用が可能。

4. **docs/internal/ の差分確認**: 本分析は CLAUDE.md と CHEATSHEET.md のみを対象としている。LAM 4.0.1 の `docs/internal/` も更新されている可能性が高く、別途差分分析が必要。

5. **hooks のテスト**: hooks 導入前に、LAM 4.0.1 同梱の `.claude/hooks/tests/` を実行し、影式環境（Windows + Python）での動作を確認すること。

6. **settings.json の精査**: LAM 4.0.1 の `.claude/settings.json` の permissions 設定が影式の運用と整合するか確認が必要。特に Python 関連コマンド（`python -m ruff`, `pip` 等）の allow/deny 分類。
