# .claude/rules/ 差分分析

> LAM 4.0.1 へのメジャーアップデートに伴う差分分析
> 比較日: 2026-03-10

## 概要

| 分類 | ファイル |
|------|---------|
| 共通（両方に存在） | `core-identity.md`, `decision-making.md`, `phase-rules.md`, `security-commands.md` |
| LAM 4.0.1 で新規追加 | `permission-levels.md`, `upstream-first.md`, `auto-generated/README.md`, `auto-generated/trust-model.md` |
| 現行にのみ存在（影式固有） | `audit-fix-policy.md`, `building-checklist.md`, `spec-sync.md` |

LAM 4.0.1 の主要な変更テーマは以下の3点:
1. **権限等級モデル（PG/SE/PM）の導入** — 変更リスクに応じた三段階分類で、AUDITING フェーズでの修正を部分的に解禁
2. **TDD 内省パイプライン** — テスト失敗パターンを自動記録し、閾値到達でルール候補を生成する仕組み
3. **Upstream First 原則** — Claude Code プラットフォーム機能の実装前に公式ドキュメントを確認する規約

---

## 共通ファイルの差分

### core-identity.md

#### 削除された項目

**Subagent 委任判断テーブル**: 現行版にある以下のテーブルが LAM 4.0.1 では削除されている:

```
| 条件 | 判断 |
|:-----|:-----|
| 単一ファイル・小規模変更 | メインで直接実施 |
| 複数ファイル・並列可能 | Subagent に委任（lam-orchestrate） |
| 深い分析・判断が必要 | メイン（Opus）で直接実施 |
| 定型的な検査・実行 | Subagent に委任 |
```

これは CLAUDE.md やプロセス文書側に移動された可能性がある。

**コンテキスト節約原則**: 現行版にある以下の3項目が LAM 4.0.1 では削除:

```
1. 大量のファイルを先回りして読み込まない（必要になった時点で読む）
2. Subagent の出力は要約して取り込む（全文をメインに展開しない）
3. 長大な出力が予想される場合は Subagent に委任してサマリーだけ受け取る
```

#### 追加された項目

**権限等級（PG/SE/PM）セクション**: v4.0.0 で導入された三段階分類の概要参照が追加:

```markdown
## 権限等級（PG/SE/PM）

v4.0.0 で導入された変更のリスクレベルに応じた三段階分類:

- **PG級**: 自動修正・報告不要（フォーマット、typo、lint 修正等）
- **SE級**: 修正後に報告（テスト追加、内部リファクタリング等）
- **PM級**: 判断を仰ぐ（仕様変更、アーキテクチャ変更等）

迷った場合は SE級に丸める（安全側に倒す）。
詳細: `.claude/rules/permission-levels.md`
```

#### 共通部分（変更なし）

- Active Retrieval（能動的検索原則）の3項目は同一
- Context Compression セクションは同一

---

### decision-making.md

#### 追加された項目

**SSOT 参照注記**: LAM 4.0.1 では冒頭に以下が追加:

```markdown
> **SSOT**: `docs/internal/06_DECISION_MAKING.md`。本ファイルは実行時の要約版。
```

#### 共通部分（変更なし）

- Three Agents Model テーブル: 同一
- Execution Flow（Divergence → Debate → Convergence）: 同一
- AoT（Atom of Thought）セクション全体: 適用条件、Atom の定義、ワークフロー、Output Format すべて同一

#### 差分まとめ

実質的な変更は SSOT 参照の1行追加のみ。影式では `docs/internal/06_DECISION_MAKING.md` が存在するか確認し、存在すれば同様の注記を追加するのが妥当。

---

### phase-rules.md

このファイルは最も大きな差分がある。

#### PLANNING セクション

変更なし。承認ゲート、禁止事項、許可事項はすべて同一。

#### BUILDING セクション

##### 変更: 「必須」は同一だが TDD 品質チェック関連が大幅に再構成

**現行版** では `building-checklist.md` に詳細ルール（R-1〜R-11, S-1〜S-4）を分離し、phase-rules.md 内の BUILDING セクションには以下しかない:

```
### 禁止
- 仕様書なし実装
- テストなし実装
- ドキュメント未更新
```

および Phase 完了判定（L-4 由来のスモークテスト）。

**LAM 4.0.1 版** では phase-rules.md 自体に TDD 品質チェックと仕様同期ルールをインライン化:

```markdown
### TDD 品質チェック

- [ ] R-1: 仕様突合 — FR/設計仕様のフィールド名・定数名と実装が文字単位で一致
- [ ] R-4: テスト網羅 — 各 FR/要件に対応するテストが存在する
- [ ] (プロジェクト固有ルールを R-5 以降に追加可)

### 仕様同期ルール

- S-1: Green 直後に対応する `docs/specs/` を確認し、実装と仕様の乖離がないか検証
- S-3: 仕様書の未実装項目には Phase/Wave マークを付与（暗黙スキップ禁止）
- S-4: Refactor で公開 API/インターフェースが変わった場合、仕様書を即時更新
```

つまり、影式固有の `building-checklist.md` と `spec-sync.md` の **コア部分** が LAM 4.0.1 では phase-rules.md 内に統合されている（ただし R-2, R-3, R-5〜R-11, S-2 は「プロジェクト固有ルール」として拡張ポイントとして残されている）。

##### 追加: TDD 内省パイプライン（Wave 4）

LAM 4.0.1 で新規追加:

```markdown
### TDD 内省パイプライン（Wave 4）

テスト失敗→成功のサイクルを PostToolUse hook が自動記録する。
蓄積されたパターンが閾値（3回）に到達すると、ルール候補が自動生成される。

- パターン記録: `.claude/tdd-patterns.log`（自動、PG級）
- パターン詳細: `docs/memos/tdd-patterns/`
- ルール候補: `.claude/rules/auto-generated/draft-*.md`（PM級で起票・承認）
- 審査コマンド: `/pattern-review`
```

##### 削除: Phase 完了判定（L-4 由来）

現行版にある以下のスモークテスト要件が LAM 4.0.1 では削除:

```
### Phase 完了判定（L-4 由来）

Phase 完了を宣言する前に、以下のスモークテストを実施する:
1. 実際に `python -m kage_shiki` で起動し、基本操作（入力→応答→終了）を確認
2. 2回目の起動で永続状態が正しく引き継がれることを確認
3. 終了操作後、プロセスとウィンドウが残存しないことを確認

テストカバレッジが高くても、実動作テスト未実施では Phase 完了としない。
```

これは影式固有（Python デスクトップアプリ特有）のルールであり、LAM 汎用テンプレートには含まれないのは妥当。

#### AUDITING セクション

##### 大幅変更: 修正ルールの再定義

**現行版** では AUDITING は「修正禁止（指摘のみ）」が基本ルール。ただし `audit-fix-policy.md` で「対応可能なものはすべて同セッション内で修正」と義務化しており、事実上矛盾がある。

**LAM 4.0.1 版** では権限等級に基づく明確な修正制御に変更:

```markdown
### AUDITING での修正ルール（v4.0.0）

権限等級（`.claude/rules/permission-levels.md`）に基づく修正制御:

- **PG級の修正**: 許可（自動修正可。フォーマット、typo、lint 違反等）
- **SE級の修正**: 許可（修正後に報告。テスト追加、内部リファクタリング等）
- **PM級の修正**: 禁止（指摘のみ、承認ゲート。仕様変更、ルール変更等）

> v3.x からの変更: 従来は「修正の直接実施禁止」だったが、
> v4.0.0 で PG/SE 級の修正を許可に緩和。
```

##### 追加: PG/SE/PM 分類の必須化

```
- 問題の PG/SE/PM 分類（権限等級に基づく）
```

##### 削除: `/full-review` 参照と audit-fix-policy.md 参照

現行版にある以下が削除:

```
- `/full-review` で監査→修正→検証を一気通貫で実施可能
- `audit-fix-policy.md` に従い、対応可能な Issue は全て修正する
```

これは権限等級モデルで AUDITING の修正ルールが明確化されたため、別ファイルでの補足が不要になったことによる。

#### フェーズ警告テンプレート

変更なし。同一。

---

### security-commands.md

#### Allow List

##### 変更: Python/パッケージ関連コマンドの整理

**現行版** には以下の行が存在するが LAM 4.0.1 にはない:

```
| Python | `python`, `python -m pytest`, `python -m ruff`, `python -c`, `pip`, `pyenv` |
```

LAM 4.0.1 は汎用テンプレートであるため、言語固有のコマンドは記載していない。影式ではこれを保持すべき。

#### Deny List

##### 変更: セクション名の変更

- 現行: `## Deny List（承認必須）`
- LAM 4.0.1: `## 高リスクコマンド（Layer 0: 承認必須）`

##### 変更: 実行カテゴリの例示

- 現行: `npm start`, `make`
- LAM 4.0.1: `npm start`, `python main.py`, `make`

##### 変更: 末尾の説明文

現行版:

```
上記に含まれないコマンドは **Deny List 扱い**（承認必須）。
「止めて」「ストップ」等の指示で直ちに停止。
```

LAM 4.0.1 版:

```
上記に含まれないコマンドは **高リスク扱い**（承認必須）。

> Layer 1（`settings.json`）では、上記コマンドの多くが `deny` または `ask` に分類されている。
「止めて」「ストップ」等の指示で直ちに停止。
```

#### 追加: v4.0.0 ネイティブ権限モデルへの移行セクション

LAM 4.0.1 で新規追加:

```markdown
## v4.0.0: ネイティブ権限モデルへの移行

v4.0.0 以降、コマンド安全基準は以下の二層で管理される:

- **Layer 1（ネイティブ権限）**: `.claude/settings.json` の `permissions`
  （allow/ask/deny）で粗粒度の境界を設定
- **Layer 2（PreToolUse hook）**: `.claude/hooks/pre-tool-use.sh` で
  ファイルパスベースの動的判定（PG/SE/PM 分類）

本ファイルの Allow/Deny List は Layer 0（憲法的プロンプティング）として引き続き有効。
Layer 1 の `permissions.allow` に PG級コマンド（`ruff format`, `eslint --fix` 等）が
追加されている。

権限等級の詳細: `.claude/rules/permission-levels.md`
```

---

## LAM 4.0.1 で新規追加されたファイル

### permission-levels.md

**内容要約**: 変更のリスクレベルに応じた三段階分類（PG/SE/PM）の定義書。

- **PG級**（自動修正・報告不要）: フォーマット、typo、lint 修正、import 整理、不要空白除去
- **SE級**（修正後に報告）: テスト追加・修正、内部リファクタリング、ドキュメント細部更新（specs/adr 除く）、minor/patch 依存更新、ログ・コメント変更
- **PM級**（判断を仰ぐ）: 仕様変更、アーキテクチャ変更、`.claude/rules/` 変更、公開 API 変更、major 依存更新、テスト/機能の削除

フェーズとの二軸設計テーブル、ファイルパスベースの分類テーブル（PreToolUse hook 用）、判断に迷う典型例も含む。

**影式への適用時の注意点**:
- ファイルパスベースの分類テーブルは影式のディレクトリ構造に合わせて調整が必要（`src/` → `src/kage_shiki/` など）
- 影式固有の PM級対象（`config.toml` テンプレート、`docs/internal/` 等）を追加する必要がある
- 現行の `audit-fix-policy.md` の「全重篤度への対応義務」ルールとの整合を取る必要がある（権限等級で PM級は指摘のみとなるため、現行ポリシーと矛盾する）

### upstream-first.md

**内容要約**: Claude Code のプラットフォーム機能（hooks, settings, permissions, skills, sub-agents, MCP）の実装・修正前に公式ドキュメントを確認する規約。

主要ポイント:
- 確認先の公式 URL テーブル（hooks, settings, permissions, skills, sub-agents）
- 確認手順: context7 MCP → WebFetch フォールバック → 差分特定 → 報告 → 承認後実装
- `/full-review` 等の自動フロー内では WebFetch を使用しない
- Wave 開始前の一括すり合わせ推奨

**影式への適用時の注意点**:
- context7 MCP の利用可否を確認する必要がある（影式では `mcp__plugin_context7_context7` が利用可能）
- 影式固有のプラットフォーム依存（pystray, tkinter 等）は本ルールの対象外であり、別途扱う必要がある
- 公式 URL が最新であるか確認が必要（Claude Code は頻繁に更新される）

### auto-generated/README.md

**内容要約**: TDD 内省パイプラインによって自動生成されたルールの配置先ディレクトリの説明。

主要ポイント:
- ライフサイクル: PostToolUse hook パターン検出 → tdd-patterns.log 記録 → 閾値到達で draft-NNN.md 生成 → PM級承認 → rule-NNN.md として配置
- ルール寿命管理: 90日以上未使用で `/daily` にて棚卸し通知
- ファイル命名: `draft-NNN.md`（承認待ち）、`rule-NNN.md`（承認済み）、`trust-model.md`
- 権限等級: ファイル追加・変更は PM級、パターン記録は PG級

**影式への適用時の注意点**:
- PostToolUse hook の実装が前提。影式では hooks 機能をまだ活用していない場合、Wave 4 として段階的に導入する必要がある
- `/daily` コマンドの実装が前提。存在しない場合は棚卸し通知機能が動作しない
- `/pattern-review` コマンドの実装も必要

### auto-generated/trust-model.md

**内容要約**: TDD 内省パイプラインの信頼度モデル定義。テスト失敗パターンからルール候補を生成するための段階化ロジック。

主要ポイント:
- 観測回数による段階: 1回（記録）→ 2回（注意）→ 3回（候補生成）→ 3回+（承認待ち）
- パターン照合ロジック: MVP は手動照合、完全実装でファイルパス・エラーメッセージのキーワード照合
- ルール候補のフォーマット定義（生成日、観測回数、ステータス、根拠パターンテーブル、推奨ルール文、適用範囲）
- ルール寿命管理: `last_matched` 日付メタデータ、90日未使用で棚卸し

**影式への適用時の注意点**:
- 影式の Phase 1 Retro で蓄積した経験則（R-2〜R-11, L-1〜L-5 等）は手動で策定されたもの。これらを信頼度モデルの「承認済みルール」として移行するか、既存の `building-checklist.md` に維持するかの判断が必要
- 初期閾値 3回は影式の開発規模（中規模）に対して妥当か検討が必要

---

## 現行にのみ存在するファイル（影式固有）

### audit-fix-policy.md

**内容**: 監査レポートの Critical/Warning/Info すべての Issue について、対応可能なものはすべて同セッション内で修正する義務を規定。A-1〜A-4 のルール。

**推奨: LAM 4.0.1 の権限等級モデルに統合し、本ファイルは廃止**

理由:
- LAM 4.0.1 の AUDITING セクションで PG/SE 級の修正が許可され、PM 級は指摘のみとなった。これにより audit-fix-policy.md の役割の大部分がカバーされる
- A-1（全重篤度への対応義務）は権限等級と矛盾する可能性がある（PM級の問題は「指摘のみ」が LAM 4.0.1 のルール）
- A-2（対応不可 Issue の明示）は LAM 4.0.1 の PM級の扱いに自然に含まれる
- A-3（修正後の再検証: テスト追加、ruff check、全テスト実行）は影式固有の品質基準として価値がある。phase-rules.md の AUDITING セクションにインライン化して保持すべき
- A-4（仕様ズレの同時修正）は S-1/S-4 でカバーされている

### building-checklist.md

**内容**: Phase 1 監査・Retro で発見された不具合パターンの防止ルール集。R-1〜R-11, S-1〜S-4 の詳細定義。Red/Green/Refactor の各ステップで適用。

**推奨: 影式固有ルールとして保持。ただしファイル構成を再編**

理由:
- LAM 4.0.1 の phase-rules.md には R-1, R-4, S-1, S-3, S-4 のコア版が統合されている
- R-2（dict ディスパッチ）、R-3（定数即時接続）、R-5（異常系テスト義務）、R-6（else デフォルト禁止）、R-7（スレッド安全性）、R-8（2回目起動テスト）、R-9（シャットダウン一意性）、R-10（GUI 目視確認）、R-11（Green 直後3点ミニチェック）は影式固有の経験則であり、汎用 LAM には含まれない
- これらは LAM 4.0.1 の `(プロジェクト固有ルールを R-5 以降に追加可)` という拡張ポイントに該当
- S-2（Protocol 外メソッドの明示）も影式固有

具体的なアクション:
- phase-rules.md の BUILDING セクションを LAM 4.0.1 ベースに更新
- R-5〜R-11, S-2 を影式固有ルールとして building-checklist.md に維持するか、phase-rules.md の TDD 品質チェックセクションに追記
- 将来的には TDD 内省パイプラインの「承認済みルール」として `auto-generated/` に移行する選択肢もある

### spec-sync.md

**内容**: 仕様・実装同期ルール。S-1〜S-4 の詳細定義と、Wave 4 監査で発見された仕様漏れパターンの再発防止。

**推奨: LAM 4.0.1 の phase-rules.md に統合し、影式固有の補足のみ保持**

理由:
- S-1, S-3, S-4 は LAM 4.0.1 の phase-rules.md「仕様同期ルール」セクションに含まれている（ただし簡略版）
- S-2（Protocol 外メソッドの明示）は影式固有。Protocol ベースの設計は影式のアーキテクチャに固有
- NFR（非機能要件）も S-1 の突合対象に含める旨の注記は影式固有の学び

具体的なアクション:
- S-1, S-3, S-4 は LAM 4.0.1 の phase-rules.md に統合（詳細版を採用するか簡略版を採用するか判断が必要）
- S-2 と NFR 注記は影式固有ルールとして building-checklist.md に移動するか、phase-rules.md に追記

---

## 移行時の注意事項

### 1. 権限等級モデルの導入は AUDITING ルールの根本的変更を伴う

現行の影式では `audit-fix-policy.md` で「対応可能な Issue はすべて修正」としているが、LAM 4.0.1 では PM級の修正は AUDITING フェーズで禁止される。この変更を受け入れるかどうかはプロジェクトオーナーの判断が必要（PM級）。

### 2. building-checklist.md の R-5〜R-11 は影式の資産

これらは Phase 1 の実開発経験から生まれた教訓であり、LAM 汎用テンプレートには含まれない。廃止ではなく、LAM 4.0.1 の拡張ポイント（`R-5 以降に追加可`）として明確に位置づけること。

### 3. Phase 完了判定（スモークテスト）は影式固有ルールとして必ず保持

LAM 4.0.1 にはスモークテスト要件がないが、デスクトップアプリケーションとしての影式には不可欠。phase-rules.md のカスタマイズ項目として残すこと。

### 4. hooks/settings.json の実装が前提となる新機能

以下の LAM 4.0.1 機能は hooks の実装が前提:
- TDD 内省パイプライン（PostToolUse hook）
- ファイルパスベースの権限判定（PreToolUse hook）
- Layer 1 ネイティブ権限（`.claude/settings.json` の permissions）

影式でこれらを導入する場合、hooks の実装を先行して行う必要がある。段階的導入を推奨。

### 5. ファイル構成の変更

移行後の `.claude/rules/` の想定構成:

```
.claude/rules/
├── core-identity.md          ← LAM 4.0.1 ベースに更新（権限等級追加）
├── decision-making.md        ← LAM 4.0.1 ベースに更新（SSOT 参照追加）
├── phase-rules.md            ← LAM 4.0.1 ベースに更新（最大の変更点）
├── security-commands.md      ← LAM 4.0.1 ベースに更新（Layer 追加） + 影式固有コマンド保持
├── permission-levels.md      ← 新規追加（影式用にパス分類をカスタマイズ）
├── upstream-first.md         ← 新規追加（そのまま適用可）
├── building-checklist.md     ← 影式固有を保持（R-5〜R-11, S-2, Phase完了判定）
├── auto-generated/
│   ├── README.md             ← 新規追加
│   └── trust-model.md        ← 新規追加
└── (audit-fix-policy.md)     ← 廃止候補（A-3 は phase-rules.md に統合）
    (spec-sync.md)            ← 廃止候補（S-1/S-3/S-4 は phase-rules.md に統合、S-2 は building-checklist.md へ）
```

### 6. CLAUDE.md の同時更新が必要

LAM 4.0.1 の CLAUDE.md では以下の変更がある:
- `Project Scale` が `Medium` → `Medium to Large` に変更
- プロジェクト固有セクション（Project Overview, 技術スタック表等）が削除（汎用テンプレート化）
- 設計文書の参照パス（`docs/memos/middle-draft/`）が削除
- `docs/slides/index.html` の参照が追加

影式の CLAUDE.md はプロジェクト固有情報を維持しつつ、LAM 4.0.1 の構造変更を反映する必要がある。
