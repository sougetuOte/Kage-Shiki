# 設計: .claude/rules/ / docs/internal/ / CLAUDE.md / CHEATSHEET.md 移行

**作成日**: 2026-03-13
**ステータス**: Draft
**対象 Phase**: LAM v4.0.1 → v4.4.1 移行
**前提資料**:
- `specs/00-diff-rules.md`（rules/ 差分分析）
- `specs/00-diff-docs.md`（docs/internal/ + CLAUDE.md + CHEATSHEET.md 差分分析）

---

## 概要

LAM v4.0.1 → v4.4.1 移行において、以下の 4 層を対象にマージ戦略を決定する。

| 対象層 | 含むファイル |
|--------|------------|
| .claude/rules/ | 既存 8 ファイル + 新規 1 ファイル（test-result-output.md） |
| docs/internal/ | 00〜07, 08, 09, 99（計 11 ファイル） |
| CLAUDE.md | プロジェクト憲法 |
| CHEATSHEET.md | クイックリファレンス |

基本方針は前回（v4.0.1 移行）と同様に **Template-First**（LAM v4.4.1 をベースに影式固有カスタマイズを上乗せ）で進める。

---

## 判断1: .claude/rules/ の更新方針

### 対象ファイルの全体像（結論先出し）

```
.claude/rules/
├── core-identity.md          ← v4.4.1 ベースに更新（docs/artifacts/ パス変更）+ 影式固有保持
├── decision-making.md        ← 変更なし（差分なし）
├── phase-rules.md            ← v4.4.1 ベースに更新（TDD 内省 v2）+ 影式固有セクション保持
├── security-commands.md      ← v4.4.1 ベースに更新（三分類化）+ Python カテゴリ保持
├── permission-levels.md      ← v4.4.1 ベースに更新（定義拡充）+ 影式固有パス再追加
├── upstream-first.md         ← v4.4.1 ベースに全面更新（URL 変更、構造化、権限等級追加）
├── building-checklist.md     ← 影式固有を保持（変更なし）
├── test-result-output.md     ← 新規追加（v4.4.1 そのまま適用）
├── auto-generated/
│   ├── README.md             ← v4.4.1 ベースに全面更新（v2 ライフサイクル）
│   └── trust-model.md        ← v4.4.1 ベースに全面更新（v2 モデル）
```

---

### 1-1: test-result-output.md の追加

#### 差分の概要

LAM v4.4.1 で新規追加されたファイル。影式には存在しない。

主要ポイント:
- テストフレームワーク導入・変更時に JUnit XML 出力設定を追加する義務
- `.gitignore` に `.claude/test-results.xml` を追加する義務
- Python (pytest), JavaScript/TypeScript (Jest, Vitest), Go, Rust の言語別設定リファレンス
- PostToolUse hook がテスト結果ファイルを読み取る前提
- 本ルール変更は PM 級、設定追加は PG 級

#### 選択肢

| # | 案 | 説明 |
|---|----|----|
| A1 | **そのまま追加** | LAM v4.4.1 の test-result-output.md を無変更で配置 |
| A2 | **影式向けに注記追加** | Python (pytest) 固有の設定手順を強調した注記を追加 |

#### 比較

| 観点 | A1 そのまま | A2 注記追加 |
|------|-----------|------------|
| テンプレート追従性 | 高 | 中（追記箇所がある） |
| 実用性 | 中（影式は Python のみ） | 高（影式に必要な設定が明確） |
| 将来の LAM アップデート追従 | 容易 | 容易（注記箇所が明確） |

#### 決定: A1（そのまま追加）

**理由**:
- test-result-output.md は言語別設定リファレンスを含む汎用的な構成になっており、Python 向けの設定（`pyproject.toml` に `--junitxml=.claude/test-results.xml` を追加）も明確に記載されている
- 影式向けの追記は不要な肥大化を招く
- TDD 内省パイプライン v2 の有効化は `pyproject.toml` と `.gitignore` の実際の変更タスクとして別途管理すべきであり、ルールファイルに埋め込む必要はない

**付随作業（実装時に別途対応）**:
- `pyproject.toml` の `[tool.pytest.ini_options]` に `addopts = "--junitxml=.claude/test-results.xml"` を追加（PM 級）
- `.gitignore` に `.claude/test-results.xml` を追加（PG 級）

---

### 1-2: security-commands.md の三分類化と Python カテゴリ保持

#### 差分の概要

影式（現行）は Allow List と高リスクコマンドの二分類だが、LAM v4.4.1 は三分類に再編:
- Allow List（自動実行可）
- 実行禁止コマンド（Layer 0: deny）— `rm`, `mv`, `chmod/chown`, `apt/brew/systemctl`
- 承認必須コマンド（Layer 0: ask）— `cp/mkdir/touch`, `git push/commit/merge`, `curl/wget`, `npm start/python main.py/make`

また `find` が Allow List から `ask` に移動（破壊的パターンは `deny`）。

影式固有: Python カテゴリ（`python`, `python -m pytest`, `python -m ruff`, `python -c`, `pip`, `pyenv`）は LAM v4.4.1 では削除されている。

#### 選択肢

| # | 案 | 説明 |
|---|----|----|
| B1 | **v4.4.1 ベース + Python カテゴリ保持** | LAM v4.4.1 の三分類構造を採用し、Allow List に Python カテゴリを影式固有として維持 |
| B2 | **v4.4.1 完全採用** | Python カテゴリを削除し、LAM v4.4.1 をそのまま採用 |

#### 比較

| 観点 | B1 Python 保持 | B2 完全採用 |
|------|--------------|------------|
| 実用性 | 高（pytest, ruff は日常的に使用） | 低（Python コマンドの扱いが曖昧になる） |
| テンプレート追従性 | 高（Python カテゴリのみ差異） | 完全 |
| settings.json との整合 | 維持（Allow に対応する設定が継続） | 要確認（Layer 1 を見直す必要） |

#### 決定: B1（v4.4.1 ベース + Python カテゴリ保持）

**理由**:
- 影式は Python プロジェクトであり、`python`, `python -m pytest`, `python -m ruff`, `pip` 等は全セッションで日常的に使用される
- v4.0.1 移行時に同じ判断でカテゴリを維持しており、v4.4.1 でも変更する理由がない
- Layer 0（プロンプティング）の Allow List に記載することで、settings.json の Layer 1 設定と整合する

#### 移行後の security-commands.md 構成

```markdown
# コマンド実行安全基準

## Allow List（自動実行可）
  ← LAM v4.4.1 ベース（find を削除）
  + 影式固有: Python カテゴリ（python, python -m pytest, python -m ruff, python -c, pip, pyenv）

## 実行禁止コマンド（Layer 0: deny）   ← LAM v4.4.1 新セクション
  rm, rm -rf, mv, chmod, chown, apt, brew, systemctl, reboot

## 承認必須コマンド（Layer 0: ask）    ← LAM v4.4.1 新セクション
  cp, mkdir, touch, git push, git commit, git merge, curl, wget, ssh,
  npm start, python main.py, make
  + find（通常検索; -delete/-exec rm 等の破壊パターンは deny）

## v4.0.0: ネイティブ権限モデルへの移行
  ← LAM v4.4.1 版（三層 → 二層表現に更新）
  本ファイルの Allow/Deny List は Layer 0 として引き続き有効（末尾注記に変更）
```

**`find` の扱いについての補足**:
v4.4.1 の変更（`find` を Allow から ask に移動）は受け入れる。影式の `find` の主な用途はファイル検索であり、ask（承認必須）のままでも Glob/Grep ツールで代替可能なため、運用上の問題は少ない。破壊的パターン（`-delete`, `-exec rm`）は deny として明示することでセキュリティが向上する。

---

### 1-3: permission-levels.md の PG/SE/PM 定義拡充と影式固有パス再追加

#### 差分の概要

LAM v4.4.1 では定義が拡充されている:
- PG 級: 「テスト失敗の自明な修正（型ミスマッチ等）」が追加
- SE 級: 「内部関数の名前変更」「ログ出力の追加・修正」「コメントの追加・修正」が追加・細分化
- PM 級: 「フェーズの巻き戻し」「`.claude/settings*.json` の変更」が追加、「テストや機能の削除」が分離
- フェーズとの二軸設計テーブル: PM 行が「承認ゲート」に統一

また影式固有パス（`docs/internal/*.md`, `pyproject.toml`, `src/kage_shiki/`, `config/`）が LAM v4.4.1 では汎用化のために削除されているため、移行時に再追加が必要。

冒頭の SSOT 宣言は LAM v4.4.1 で簡潔な概要文に変更されているが、影式では SSOT の明確化が有用なため保持を検討する。

#### 選択肢

| # | 案 | 説明 |
|---|----|----|
| C1 | **v4.4.1 ベース + 影式固有パス再追加 + SSOT 宣言維持** | v4.4.1 の定義拡充を取り込み、影式固有パスと SSOT 宣言を上乗せ |
| C2 | **v4.4.1 ベース + 影式固有パス再追加のみ** | SSOT 宣言は v4.4.1 版に簡素化 |

#### 比較

| 観点 | C1 SSOT 宣言維持 | C2 SSOT 宣言簡素化 |
|------|----------------|------------------|
| 明確性 | 高（ファイルの役割が一読で分かる） | 中 |
| テンプレート追従性 | 中 | 高 |
| 情報量 | 高（参照関係が明文化） | 低 |

#### 決定: C1（v4.4.1 ベース + 影式固有パス再追加 + SSOT 宣言維持）

**理由**:
- SSOT 宣言は hooks 実装時のファイルパスベース判定の出所を明確にするために有用
- v4.4.1 の PG/SE/PM 定義拡充（「テスト失敗の自明な修正」「フェーズの巻き戻し」等）は影式でも適用可能な改善であり、積極的に取り込む
- 影式固有パスは PreToolUse hook の判定ロジックの基盤であり、汎用化は許容できない
- 参照セクションは v4.4.1 版（docs/specs/ + docs/internal/ への参照）に更新しつつ、影式固有の参照も維持する

#### 移行後の permission-levels.md 全体構成

```markdown
# 権限等級分類基準

> SSOT 宣言（影式固有・維持）

## PG級（自動修正・報告不要）
  ← v4.4.1 拡充（テスト失敗の自明な修正を追加）

## SE級（修正後に報告）
  ← v4.4.1 拡充（内部関数の名前変更、ログ出力追加・修正、コメント追加・修正を追加）

## PM級（判断を仰ぐ）
  ← v4.4.1 拡充（フェーズの巻き戻し、.claude/settings*.json 変更を追加）
     「テストや機能の削除」→「テストの削除」「機能の削除」に分離

## フェーズとの二軸設計
  ← v4.4.1 版（PM 行を「承認ゲート」に統一）

## ファイルパスベースの分類（PreToolUse hook 用）
  ← v4.4.1 ベース + 影式固有パスを再追加
  | docs/internal/*.md  | PM | プロセス SSOT 変更（影式固有） |
  | pyproject.toml      | PM | プロジェクト設定変更（影式固有） |
  | src/kage_shiki/ 配下 | SE | ソースコード変更（影式固有） |
  | tests/ 配下         | SE | テストコード変更 |
  | config/ 配下        | SE | 設定ファイル変更（影式固有） |
  | .claude/settings*.json | PM | 設定変更（v4.4.1 追加） |

## 迷った場合
  ← v4.4.1 例（汎用）+ 影式固有例を保持
  影式固有例:
  - 「config.toml テンプレートの変更」→ PM 級（設定仕様の変更）
  - 「docs/internal/ の変更」→ PM 級（SSOT）
  - 「tests/ の新規テスト追加」→ SE 級

## 参照
  ← v4.4.1 参照（docs/specs/, docs/internal/ SSOT への参照）
  + 影式固有: phase-rules.md, core-identity.md, security-commands.md
```

---

### 1-4: phase-rules.md の TDD 内省 v2 更新と影式固有セクション保持

#### 差分の概要

最も大きな差分がある。主な変更点:
- PLANNING: `docs/memos/` → `docs/artifacts/` へのパス変更
- BUILDING — TDD 内省パイプライン: v1（3回閾値、PostToolUse 自動、`/pattern-review`）→ v2（JUnit XML、2回閾値、`/retro` Step 2.5 で人間判断）
- AUDITING: `Green State 5条件との対応テーブル`（影式固有）、`AUDITING ルール識別子 A-1〜A-4`（影式固有）、`/full-review` 参照が LAM v4.4.1 には存在しない

#### 選択肢

| # | 案 | 説明 |
|---|----|----|
| D1 | **v4.4.1 ベース + 影式固有セクション保持** | TDD 内省 v2 に更新しつつ、AUDITING の影式固有セクションを維持 |
| D2 | **v4.4.1 完全採用** | 影式固有セクションを全て削除 |
| D3 | **影式現行ベース + v4.4.1 差分適用** | TDD 内省部分のみ v2 に更新、その他は現行維持 |

#### 比較

| 観点 | D1 固有保持 | D2 完全採用 | D3 現行ベース |
|------|-----------|-----------|------------|
| TDD 内省 v2 取り込み | 完全 | 完全 | 完全 |
| Green State / A-1〜A-4 | 保持 | 消失 | 保持 |
| テンプレート追従性 | 高（差異が明確） | 完全 | 低 |
| 実運用への影響 | なし | 影式固有品質基準の喪失 | なし |

#### 決定: D1（v4.4.1 ベース + 影式固有セクション保持）

**理由**:
- TDD 内省 v2（JUnit XML ベース）への更新は受け入れる。v1 は `exitCode` が PostToolUse の入力に存在しないため実際には動作していなかったことが判明しており、v2 への移行は修正として必要
- AUDITING の影式固有セクション（Green State 5条件、A-1〜A-4、修正後再検証義務）は影式の監査フローの品質基準として実運用で検証済みであり、削除は品質基準の実質的な後退を意味する
- `影式固有:` プレフィックスにより LAM テンプレート部分との区別が明確であり、将来の LAM アップデート追従も容易

#### 移行後の phase-rules.md セクション構成

```
## PLANNING
  - 許可事項: docs/memos/ → docs/artifacts/ に更新

## BUILDING
  ### TDD 品質チェック               ← 変更なし（building-checklist.md 参照維持）
  ### 仕様同期ルール                 ← 変更なし
  ### TDD 内省パイプライン v2        ← v4.4.1 に全面更新（JUnit XML、2回閾値、/retro）
  ### 禁止事項                       ← 変更なし
  ### 影式固有: Phase 完了判定（L-4 由来）  ← 維持

## AUDITING
  ### AUDITING での修正ルール（v4.0.0）  ← 変更なし
  ### 必須                            ← v4.4.1 に合わせて /full-review 参照を削除
  ### コード品質チェック              ← 変更なし
  ### コード明確性チェック            ← 変更なし
  ### ドキュメント・アーキテクチャ    ← 変更なし
  ### 改善提案の禁止事項              ← 変更なし
  ### レポート形式                    ← 変更なし
  ### 影式固有: 修正後の再検証義務（A-3 由来）  ← 維持
  ### 影式固有: 監査レポート完了条件          ← 維持
  ### Green State 5条件との対応             ← 維持
  ### AUDITING ルール識別子（A-1〜A-4）      ← 維持

## フェーズ警告テンプレート          ← 変更なし
```

**TDD 内省パイプライン v2 の詳細（更新後の記述）**:
```
### TDD 内省パイプライン v2

PostToolUse hook がテスト結果（JUnit XML）を読み取り、FAIL→PASS 遷移を自動記録する。
/retro 実行時に人間がパターン分析を行い、同一パターンが閾値（2回）以上出現する場合にルール候補を提案する。

- パターン記録: .claude/tdd-patterns.log（自動、PG 級）
- パターン詳細: docs/artifacts/tdd-patterns/
- ルール候補: .claude/rules/auto-generated/draft-*.md（PM 級で起票・承認）
- パターン分析: /retro Step 2.5
- 審査コマンド: /pattern-review

詳細: .claude/rules/auto-generated/trust-model.md
```

---

### 1-5: core-identity.md の docs/artifacts/ パス変更

#### 差分の概要

変更点は 1 箇所のみ:
- Context Compression セクション: 書き出し先が `docs/memos/` → `docs/artifacts/` に変更

影式固有の保持内容（Subagent 委任判断テーブル、コンテキスト節約原則）は v4.4.1 にも存在しないが、v4.0.1 移行時の判断と同様に維持する。

#### 決定: パス変更を適用、影式固有セクションを維持

**理由**:
- `docs/memos/` → `docs/artifacts/` は全体的なパス統一の一部であり、適用することで整合性が保たれる
- Subagent 委任判断テーブルとコンテキスト節約原則は v4.0.1 移行時の判断（E2：維持）から変更する理由がない

**変更内容（最小限）**:
```markdown
## Context Compression
  1. 決定事項と未解決タスクを `docs/tasks/` または `docs/artifacts/` に書き出す  ← docs/memos/ から変更
```

---

### 1-6: upstream-first.md の URL 変更・構造化・権限等級追加

#### 差分の概要

LAM v4.4.1 では構造化されたセクションに大幅再編:
- URL ドメイン変更: `docs.anthropic.com/en/docs/claude-code/` → `code.claude.com/docs/en/`
- セクション構造: フラット → 概要/背景/ルール（必須・確認先・確認手順・適用タイミング）/権限等級/一括すり合わせに再編
- 権限等級セクション追加: 本ルールファイル自体の変更は PM 級と明示
- MCP の行が削除
- WebFetch 制限の理由が「コンテキスト消費」→「無応答リスク」に変更
- Wave 開始前の一括すり合わせが独立セクションに昇格し、対象範囲（更新すべき/不要）が明示

#### URL ドメインの検証

2026-03-13 時点での確認:
- `code.claude.com/docs/en/overview` — 実在確認済み（`docs.anthropic.com` → `code.claude.com` への 301 リダイレクト確認済み）
- LAM v4.4.1 の記載 URL（`code.claude.com/docs/en/`）は有効

#### 選択肢

| # | 案 | 説明 |
|---|----|----|
| E1 | **v4.4.1 ベースに全面更新** | LAM v4.4.1 の構造・URL・内容をそのまま採用 |
| E2 | **現行構造維持 + URL 変更のみ** | セクション構造は現行のまま、URL のみ更新 |

#### 比較

| 観点 | E1 全面更新 | E2 URL のみ |
|------|-----------|------------|
| テンプレート追従性 | 完全 | 低 |
| 内容の改善（権限等級、対象範囲等） | 取り込む | 取り込まない |
| 作業量 | 中（ファイル全体の書き直し） | 小（URL のみ） |
| 影式固有の削除リスク | 低（影式固有の追記は元々なかった） | なし |

#### 決定: E1（v4.4.1 ベースに全面更新）

**理由**:
- upstream-first.md は影式固有の追記が v4.0.1 時点でも「なし（そのまま適用）」だった（G1 判断）
- v4.4.1 の構造改善（権限等級の明示、適用タイミングの整理、一括すり合わせ対象範囲の明示）は実運用上も有益
- `docs/memos/` への記録は `docs/artifacts/` に変更されており、削除された項目は他のファイルでカバーされる

**URL の確定値**:
| 機能 | URL |
|------|-----|
| Hooks | `https://code.claude.com/docs/en/hooks` |
| Settings | `https://code.claude.com/docs/en/settings` |
| Permissions | `https://code.claude.com/docs/en/permissions` |
| Skills | `https://code.claude.com/docs/en/skills` |
| Sub-agents | `https://code.claude.com/docs/en/sub-agents` |

※ MCP の行は LAM v4.4.1 に倣い削除。

---

### 1-7: auto-generated/README.md と trust-model.md の全面更新

#### 差分の概要

両ファイルとも TDD 内省パイプライン v2 対応で全面書き換え。

**README.md の主な変更**:
- ライフサイクルが JUnit XML → PostToolUse → FAIL→PASS 遷移 → `/retro`（人間判断）→ PM 承認のフローに変更
- 閾値: 3回 → 2回
- ルール寿命管理: `/daily` → `/quick-save (Daily 記録)`
- 参照セクションの大幅追加（`docs/specs/tdd-introspection-v2.md` 等）

**trust-model.md の主な変更**:
- データソース: `tool_response.exitCode`（動作せず）→ `.claude/test-results.xml`（JUnit XML）
- 観測段階テーブル: 4段階（1〜3+回）→ フロー図（FAIL→PASS 遷移 → 2回以上: `/retro` で提案）
- ルール候補ステータスに `rejected` 追加
- `/retro` Step 2.5 での具体的な手順を記述

#### 決定: v4.4.1 ベースに全面更新（両ファイルとも）

**理由**:
- v1 の動作前提（`exitCode` が PostToolUse 入力に存在する）が誤りであることが確認されており、v1 のまま維持することは意味がない
- 閾値を 3回 → 2回 に引き下げることで、人間が `/retro` を実行するタイミングで確実にパターンが検出される設計になる
- 両ファイルとも影式固有の追記は元々ほぼなく（TDD 内省は汎用フロー）、v4.4.1 テンプレートをそのまま採用できる

---

### 1-8: building-checklist.md の保持

#### 差分の概要

LAM v4.4.1 には存在しない影式固有ファイル。v4.0.1 移行時に `phase-rules.md` の LAM コアルール（R-1, R-4, S-1, S-3, S-4）を排除し、影式固有ルール（R-2, R-3, R-5〜R-11, S-2）のみを定義する構成に整理済み。

#### 決定: 変更なし（影式固有を保持）

**理由**:
- R-7〜R-11 はデスクトップアプリケーション（スレッド安全性、永続状態、シャットダウン、GUI 目視確認）に固有のルールであり、LAM 汎用テンプレートには含まれない
- v4.4.1 の `phase-rules.md` TDD 品質チェックに「プロジェクト固有ルールを R-5 以降に追加可」の拡張ポイントが引き続き存在しており、影式固有ファイルとの整合性は維持されている

---

### 判断1 総括: .claude/rules/ 変更サマリー

| ファイル | 変更種別 | 主な変更内容 |
|---------|---------|------------|
| `test-result-output.md` | **新規追加** | LAM v4.4.1 そのまま適用 |
| `security-commands.md` | **更新** | 三分類化（deny/ask 分離）+ Python カテゴリ保持 + find を ask に移動 |
| `permission-levels.md` | **更新** | PG/SE/PM 定義拡充 + 影式固有パス再追加 + 参照先変更 |
| `phase-rules.md` | **更新** | TDD 内省 v2 + docs/artifacts/ パス変更 + 影式固有セクション保持 |
| `core-identity.md` | **更新** | docs/artifacts/ パス変更のみ（1行） |
| `upstream-first.md` | **全面更新** | URL 変更 + 構造化 + 権限等級追加 |
| `auto-generated/README.md` | **全面更新** | v2 ライフサイクル |
| `auto-generated/trust-model.md` | **全面更新** | v2 モデル |
| `building-checklist.md` | **変更なし** | 影式固有を保持 |
| `decision-making.md` | **変更なし** | 差分なし |

---

## 判断2: docs/internal/ の更新方針

### 2-1: 00_PROJECT_STRUCTURE.md

#### 差分の概要

| 変更箇所 | 内容 |
|---------|------|
| docs/ 配下 | `artifacts/`（knowledge/, audit-reports/, tdd-patterns/）が新設 |
| .claude/ 配下 | `agent-memory/` が追加 |
| Section 3 SSOT 層名称 | 「上位層」「下位層」→「情報層 1」「情報層 2」「情報層 3」に変更 |
| Section 3 情報層 2 の詳細 | `commands/`, `hooks/`, `agents/`, `skills/` を明示 |
| Section 3 Permission Layer Note | 権限 Layer 0/1/2 との混同防止注記を追加 |
| Section 2A 中間成果物保存先 | `docs/memos/` → `docs/artifacts/` |
| Section 2D Subagent Persistent Memory | `.claude/agent-memory/<agent-name>/` が新規追加 |
| Section 2E STATE 参照コマンド | `/full-load` → `/quick-load` |

#### 選択肢

| # | 案 | 説明 |
|---|----|----|
| F1 | **v4.4.1 ベースに更新** | 新規ディレクトリ追加、SSOT 層名称変更、Subagent Memory 追加を全て取り込む |
| F2 | **必要最小限の更新** | 実際に使用するディレクトリ（artifacts/）追加と SESSION 参照コマンド変更のみ |

#### 比較

| 観点 | F1 全取り込み | F2 最小限 |
|------|-------------|---------|
| SSOT 整合性 | 完全 | 部分的 |
| docs/ 構造の明確化 | 高 | 低 |
| agent-memory/ 導入準備 | 完了 | 未対応 |

#### 決定: F1（v4.4.1 ベースに更新）

**理由**:
- `docs/artifacts/` はパス統一の核心であり、project structure で明示することで他ファイルの参照先変更の根拠となる
- `agent-memory/` は Subagent Persistent Memory の前提となるディレクトリであり、先に構造に記録しておくことで将来の導入がスムーズになる
- SSOT 層名称の明確化（「情報層 1/2/3」）は Permission Layer 0/1/2 との混同を防ぐ実用的な改善

**影式固有の維持事項**:
- `src/kage_shiki/` パッケージ構造（`backend/frontend/` の汎用テンプレートは不採用）
- `docs/memos/middle-draft/` の記載（影式で実際に使用）
- `tests/` の説明に `pytest` を明示

---

### 2-2: 02_DEVELOPMENT_FLOW.md

#### 差分の概要

| 変更箇所 | 内容 |
|---------|------|
| Phase 1 冒頭文 | Phase 3 (定期監査) への言及を追加 |
| Phase 1 Step 6 | `implementation_plan.md` → `docs/tasks/{feature_name}-tasks.md` |
| Phase 2 Step 1 | `task.md` → `docs/tasks/{feature_name}-tasks.md` |
| Phase 2 Step 5 | `docs/memos/walkthrough-*` → `docs/artifacts/walkthrough-*` |
| Phase 2 Step 5 | `必須` → `推奨` に緩和 |
| TDD 内省パイプライン | v1 → v2（JUnit XML、2回閾値、/retro） |
| Wave-Based Development | LAM v4.4.1 で全削除 |

#### Wave-Based Development セクションの扱い

影式現行版にある Wave-Based Development（Wave 定義、実績サマリー）、Quality Rules Integration、Advanced Workflows の 3 セクションが LAM v4.4.1 では全削除されている。

**決定: 影式固有として保持**

**理由**:
- Wave 実績サマリー（Phase 1 MVP の記録）は影式プロジェクトの歴史的記録であり、削除する理由がない
- Quality Rules Integration（R-1〜R-6, S-1〜S-4, A-1〜A-4 のマッピング）は影式のルール体系の全体像を示すもので、実運用時の参照価値が高い
- LAM v4.4.1 で削除された理由はテンプレート汎用化であり、影式固有として維持する正当性がある
- `影式固有:` プレフィックスを付与することで LAM テンプレート部分との区別を明確にする

**変更内容（適用する変更のみ）**:
- Phase 1/2 のパス変更（`task.md` → `docs/tasks/`, `docs/memos/` → `docs/artifacts/`）
- TDD 内省パイプライン v1 → v2
- Step 5 の `必須` → `推奨` 変更

---

### 2-3: 03_QUALITY_STANDARDS.md

#### 差分の概要

Section 1〜5 および Section 8（Technology Trend Awareness）は差分なし。

影式固有セクション:
- Section 6: Python Coding Conventions（PEP 8, Type Hints, ruff, Docstrings）
- Section 7: Building Defect Prevention（R-1〜R-6 一覧）

これらは LAM v4.4.1 に存在しない。

#### 決定: 変更なし（影式固有セクションを保護確認のみ）

**理由**:
- Section 1〜5 は差分なしのため変更不要
- Section 6〜7 は影式固有であり、Python コーディング規約と不具合防止ルールは影式の品質水準を維持するために不可欠
- v4.0.1 移行時と同じ判断（「保護確認のみ」）を踏襲する

---

### 2-4: 04_RELEASE_OPS.md

#### 差分の概要

| 変更箇所 | 内容 |
|---------|------|
| Section 1 デプロイ基準 | Performance Check → **Quality Gate Passed** に統合、`/retro` 実施済み（Retrospective Done）を追加 |
| Section 2 リリースフロー | ステップ名が汎用化（Staging Verification → Verification 等） |
| Section 3 Post-Mortem | 記録先が `docs/adr/` → `docs/artifacts/` + アーキテクチャ判断時は `docs/adr/` |
| Section 4 PATCH 説明 | 「後方互換性のあるバグ修正」→「後方互換性のあるバグ修正、ドキュメント修正、内部改善」 |

影式固有の HTML コメント（`<!-- Phase 2b 以降でパッケージング方法... -->`）は LAM v4.4.1 にない。

#### 決定: v4.4.1 ベースに更新、影式固有コメント保持

**理由**:
- Quality Gate Passed（`/retro` 実施済みを含む）はリリース品質の向上であり、採用する
- Post-Mortem 記録先を `docs/artifacts/` に変更することで、全体的なパス統一と整合する
- 影式固有の HTML コメント（PyInstaller 検討メモ）は将来の実装判断のために保持する

---

### 2-5: 05_MCP_INTEGRATION.md

#### 差分の概要

| 変更箇所 | 内容 |
|---------|------|
| Allow List 内 find | あり → v4.3.1 で ask に移動の注記 |
| Heimdall Integration Rule | `docs/memos/` → `docs/artifacts/` |

影式固有の「Phase 1 MVP Note」は維持。Section 2〜6 は差分なし。

#### 決定: v4.4.1 差分のみ適用、影式固有 Note を維持

**変更内容**:
- `find` の Allow List 内記載に `v4.3.1 で ask に移動` の注記を追加
- `docs/memos/` → `docs/artifacts/` パス変更（Heimdall Integration Rule）

---

### 2-6: 07_SECURITY_AND_AUTOMATION.md

#### 差分の概要

最も大きな変更を含む:

| 変更箇所 | 内容 |
|---------|------|
| Section 2 Allow List | `find` を除外（ask に移動） |
| Section 2 Deny List 構造 | 単一 Deny List → **B-1: deny（実行禁止）+ B-2: ask（承認必須）に分離** |
| Section 2 Deny List — deny | `rm`, `mv`, `chmod/chown`, `apt/brew/systemctl`, `find -delete/-exec rm/-exec chmod` |
| Section 2 Deny List — ask | `cp/touch/mkdir`, `find`, `git push/commit/merge`, `curl/wget`, `npm start/python main.py/make` |
| Section 3 Automation | v4.0.0 注記（Section 5 への参照）を追加 |
| Section 5 多層モデル | Permission Layer 0/1/2 テーブルを新設、用語注意 Note を追加 |

影式固有の保持すべき内容:
- Section 2 Allow List: `ruff check`, `ruff format --check`（Linting カテゴリ）
- Section 2 Allow List: pytest 詳細オプション（`pytest -v`, `pytest --tb=short`）
- Section 2 Deny List: `ruff check --fix`, `ruff format`（Linting Write）
- Section 2 Deny List: `pip install`, `pip uninstall`（Package Install）
- Section 2 Deny List: `python -m kage_shiki`（Build/Run）
- Section 5 PreToolUse: 影式固有パス（`pyproject.toml`, `src/kage_shiki/`, `config/`）
- Section 6 Security Tools: 影式固有ツール列（ruff, pip-audit, safety, bandit）

#### 選択肢

| # | 案 | 説明 |
|---|----|----|
| G1 | **v4.4.1 ベース + 影式固有コマンド保持** | deny/ask 分離を採用し、影式固有のコマンドを適切な分類に配置 |
| G2 | **現行構造維持 + deny/ask 分離のみ** | 影式固有構造を維持し、deny/ask の概念だけ取り込む |

#### 影式固有コマンドの配置方針

| コマンド | 現行 | 移行後 | 理由 |
|---------|------|--------|------|
| `ruff check`, `ruff format --check` | Allow | Allow | Linting 読み取り操作は安全 |
| `pytest -v`, `pytest --tb=short` | Allow | Allow | テスト実行は安全 |
| `ruff check --fix`, `ruff format` | Deny(Linting) | ask | コード変更を伴うが意図的な操作 |
| `pip install`, `pip uninstall` | Deny(Package) | ask | 環境変更を伴うが意図的な操作 |
| `python -m kage_shiki` | Deny(Build/Run) | ask | 起動操作であり承認が適切 |

#### 決定: G1（v4.4.1 ベース + 影式固有コマンド保持）

**理由**:
- deny/ask 分離は `rm`/`mv` のような不可逆操作と `git commit` のような承認が必要な操作を明確に分ける改善であり、影式でも採用する
- 影式固有のコマンドは deny/ask の適切な分類に再配置することで、v4.4.1 の構造に整合させつつ保持できる
- Section 5 の PreToolUse 影式固有パスと Section 6 の影式固有ツール列は変更なく維持

---

### 2-7: 08_SESSION_MANAGEMENT.md

#### 差分の概要

LAM v4.4.1 にはこのファイルが存在しない。影式独自ファイル。

v4.4.1 の変更（`/full-save`, `/full-load` 廃止）への追従が必要:
- `/full-save`: SESSION_STATE.md + git commit + push + daily を担当していた
- `/full-load`: 詳細な状態確認 + 復帰報告を担当していた
- 移行後: `/quick-save` が SESSION_STATE.md + Daily 記録を担う、git commit は `/ship` に委譲

#### 決定: /full-save, /full-load 廃止に追従

**変更内容**:
- `/full-save` の説明・使い分けガイドを削除または廃止コメントに変更
- `/full-load` の説明・使い分けガイドを削除または廃止コメントに変更
- `/quick-save` の説明を拡充（SESSION_STATE.md + Daily 記録 + ループログ）
- `/quick-load` の説明を拡充（SESSION_STATE.md + 関連ドキュメント特定 + 復帰サマリー）
- git commit 操作は `/ship` を使用する旨を明示

---

### 2-8: 09_SUBAGENT_STRATEGY.md

#### 差分の概要

LAM v4.4.1 にはこのファイルが存在しない。影式独自ファイル。差分なし。

#### 決定: 変更なし

---

### 2-9: 99_reference_generic.md

#### 差分の概要

| 変更箇所 | 内容 |
|---------|------|
| Section B フェーズモードタグ | 独立セクション → 各 Phase 見出しに inline 化 |
| Section D Starter Kit | `00..07` → `00_PROJECT_STRUCTURE .. 07_SECURITY_AND_AUTOMATION` に明確化 |

#### 決定: v4.4.1 差分を適用

**変更内容**:
- フェーズモードタグを各 Phase 見出しに inline 化（`## Phase 1 [PLANNING]` 等）
- Starter Kit のファイル名を明示化

---

### 判断2 総括: docs/internal/ 変更サマリー

| ファイル | 変更種別 | 主な変更内容 |
|---------|---------|------------|
| `00_PROJECT_STRUCTURE.md` | **更新** | docs/artifacts/ 追加、agent-memory/ 追加、SSOT 層名称変更 |
| `01_REQUIREMENT_MANAGEMENT.md` | **変更なし** | 差分なし |
| `02_DEVELOPMENT_FLOW.md` | **更新** | TDD 内省 v2、パス変更。Wave-Based Development セクション保持 |
| `03_QUALITY_STANDARDS.md` | **変更なし** | Section 6, 7 影式固有を保護確認のみ |
| `04_RELEASE_OPS.md` | **更新** | Quality Gate Passed, Retrospective Done 追加、汎用化 |
| `05_MCP_INTEGRATION.md` | **軽微更新** | find → ask 注記、docs/artifacts/ パス変更 |
| `06_DECISION_MAKING.md` | **変更なし** | 差分なし |
| `07_SECURITY_AND_AUTOMATION.md` | **更新** | deny/ask 分離、Permission Layer Note、影式固有コマンド保持 |
| `08_SESSION_MANAGEMENT.md` | **更新** | /full-save, /full-load 廃止に追従 |
| `09_SUBAGENT_STRATEGY.md` | **変更なし** | 差分なし |
| `99_reference_generic.md` | **軽微更新** | フェーズモードタグ inline 化、Starter Kit 明確化 |

---

## 判断3: CLAUDE.md の更新方針

### 差分の概要

| 変更箇所 | 内容 |
|---------|------|
| Context Management | `/full-save`, `/full-load` 廃止。`/quick-save` が拡充（Daily 記録含む） |
| Memory Policy | 三層構造に拡張（Auto Memory 用途拡大、Subagent Persistent Memory 追加、Knowledge Layer 追加） |
| Hierarchy of Truth | Architecture の参照範囲が `00〜09` → `00-07`（SSOT）に変更 |
| `/auditing` ガードレール | 表現の微調整（実質同一） |

影式固有の保持事項:
- Identity: `影式 (Kage-Shiki)` の名称と説明文
- Project Scale: `Medium`（v4.4.1 の `Medium to Large` は過大）
- Project Overview: 技術スタックテーブル全体
- Hierarchy of Truth: 08, 09 を含む `SSOT: 00〜09` の範囲
- References: `docs/memos/middle-draft/` の行
- Initial Instruction: プロジェクト名修飾

### 3-1: Context Management の更新

#### 選択肢

| # | 案 | 説明 |
|---|----|----|
| H1 | **v4.4.1 ベース（/full-save, /full-load 廃止）を採用** | 4種から2種に削減、/quick-save と /quick-load を拡充 |
| H2 | **4種のまま維持** | 影式固有の詳細なセーブ/ロード体系を保持 |

#### 決定: H1（v4.4.1 ベースに更新）

**理由**:
- `/full-save` の主要機能（git commit + push）は `/ship` に委譲することで、セッション管理とバージョン管理の責務が分離される。これは設計としてより明確
- `/quick-save` の拡充（Daily 記録を含む）により、日常操作が 1 コマンドに集約される
- 08_SESSION_MANAGEMENT.md もこの変更に追従するため、CLAUDE.md との整合が保たれる

**変更後の Context Management セクション**:
```markdown
### セーブ/ロードの使い分け
- /quick-save: SESSION_STATE.md + Daily 記録 + ループログ（普段使い）
- /quick-load: SESSION_STATE.md 読込 + 関連ドキュメント特定 + 復帰サマリー（日常の再開）
- git commit / push は /ship を使用

残量 25% 以下では /quick-save を使うこと。
```

### 3-2: Memory Policy の三層構造拡張

#### 差分の詳細

| 項目 | 影式現行 | v4.4.1 |
|------|---------|--------|
| Auto Memory | Subagent ノウハウ限定 | 作業効率に関する学習（ビルドコマンド、デバッグ知見等）に拡大 |
| Subagent Persistent Memory | なし | `.claude/agent-memory/<agent-name>/` での知見蓄積 |
| Knowledge Layer | なし | `docs/artifacts/knowledge/`（/retro Step 4） |
| 参照先 | docs/internal/05_MCP_INTEGRATION.md Section 6 | セクション内に自己完結 |

#### 決定: v4.4.1 ベースの三層構造を採用

**理由**:
- Auto Memory の用途拡大は現実的な改善。「Subagent ノウハウ限定」の制約は過剰に狭かった
- Subagent Persistent Memory（agent-memory/）と Knowledge Layer（artifacts/knowledge/）は将来の Subagent 高度化に向けた基盤であり、先行して定義しておくことに価値がある
- 参照先の自己完結化は CLAUDE.md が肥大化しないよう、簡潔な記述を維持する

### 3-3: Hierarchy of Truth の調整

#### 選択肢

| # | 案 | 説明 |
|---|----|----|
| I1 | **`SSOT: 00〜09` を維持** | 影式固有の 08, 09 も SSOT として含める |
| I2 | **`SSOT: 00-07`（v4.4.1 準拠）に変更** | LAM テンプレートに合わせて 08, 09 を SSOT から外す |

#### 決定: I1（`SSOT: 00〜09` を維持）

**理由**:
- 08_SESSION_MANAGEMENT.md と 09_SUBAGENT_STRATEGY.md は影式の運用で有用性が実証されており、SSOT としての地位を保持する
- Hierarchy of Truth でこれらを「参考」に格下げすると、セッション管理のルール優先度が曖昧になる

---

## 判断4: CHEATSHEET.md の更新方針

### 差分の概要

変更点は多岐にわたる。主要な変更軸:

1. セッション管理コマンド: 4種 → 2種（quick-save/load のみ）
2. ワークフローコマンド: `/wave-plan`, `/retro` が補助コマンドから昇格
3. 補助コマンド: 5件削除（/focus, /daily, /adr-create, /security-review, /impact-analysis）
4. スキル: `ultimate-think` 削除、`lam-orchestrate` 説明拡充、`ui-design-guide` 追加
5. 状態管理: `docs/artifacts/knowledge/`, `.claude/agent-memory/` 追加
6. サブエージェント: Memory 列追加

影式固有の保持事項:
- プロジェクト技術スタックセクション全体
- `building-checklist.md` の Rules 一覧記載
- 日常ワークフロー 7パターン
- クイックリファレンスの `/ship`、設計中間文書

### 4-1: セッション管理コマンドの2種化

#### 決定: v4.4.1 準拠（/full-save, /full-load を廃止）

CLAUDE.md の判断（H1）と整合。

**変更後の記述**:
| コマンド | 機能 | コンテキスト消費 |
|---------|------|----------------|
| `/quick-save` | SESSION_STATE.md + Daily 記録 + ループログ | 3-4% |
| `/quick-load` | SESSION_STATE.md 読込 + 関連ドキュメント特定 + 復帰サマリー | 2-3% |

git commit / push は `/ship` を使用。

### 4-2: ワークフローコマンドの再編

#### 決定: /wave-plan, /retro を補助コマンドからワークフローコマンドに昇格

**理由**:
- `/wave-plan` と `/retro` は影式の開発サイクルにおいて中核的なコマンドであり、補助コマンドの位置付けは実態に合っていない
- LAM v4.4.1 での昇格判断を影式でも採用する
- `/release` も新規追加

**削除する補助コマンド**:
- `/focus`: 用途が他のコマンドに包含
- `/daily`: `/quick-save` の Daily 記録機能に統合
- `/adr-create`: `/pattern-review` 等に統合
- `/security-review`: `/full-review` に統合
- `/impact-analysis`: Phase 1 Pre-Flight に統合

### 4-3: スキルの更新

#### 決定: v4.4.1 準拠

| 変更 | 内容 |
|------|------|
| `ultimate-think` 削除 | `lam-orchestrate` に統合 |
| `lam-orchestrate` 説明拡充 | 「タスク分解・並列実行 + 構造化思考（AoT + Three Agents）」 |
| `ui-design-guide` 追加 | v4.4.1 新規 |

### 4-4: 状態管理の更新

#### 決定: v4.4.1 準拠

| 追加 | 内容 |
|------|------|
| `docs/artifacts/knowledge/` | /retro Step 4 の知見保存先 |
| `.claude/agent-memory/` | Subagent Persistent Memory |

### 4-5: 影式固有セクションの保持

以下は LAM v4.4.1 にないが影式固有として維持:

| セクション | 維持理由 |
|-----------|---------|
| プロジェクト技術スタック | 技術選定の根拠となる参照情報。CLAUDE.md の Project Overview と対応 |
| building-checklist.md の記載 | 影式固有ルールファイルの存在を明示 |
| 日常ワークフロー 7パターン | Wave ベースの作業フローは影式で実運用中 |
| クイックリファレンスの /ship | git commit/push の日常操作として必須 |
| クイックリファレンスの設計中間文書 | docs/memos/middle-draft/ は現在も使用中 |

---

## 判断5: URL ドメイン変更の対応

### 差分の概要

LAM v4.4.1 では Claude Code 公式ドキュメントの URL ドメインが変更:

| 変更前 | 変更後 |
|--------|--------|
| `docs.anthropic.com/en/docs/claude-code/` | `code.claude.com/docs/en/` |

影響範囲: `upstream-first.md` の確認先テーブル

### ドメインの正当性確認

2026-03-13 時点での WebSearch 結果:
- `https://code.claude.com/docs/en/overview` — 実在確認済み
- `docs.anthropic.com/en/docs/claude-code/*` → `code.claude.com/docs/en/*` への 301 リダイレクトを WebFetch で直接確認済み（2026-03-13）

**結論**: LAM v4.4.1 の URL 変更（`code.claude.com/docs/en/`）は正しい最新ドメインに対応している。

### 決定: code.claude.com ドメインに変更

**変更箇所**: `upstream-first.md` の確認先テーブル

**変更後の URL テーブル**:
| 機能 | URL |
|------|-----|
| Hooks | `https://code.claude.com/docs/en/hooks` |
| Settings | `https://code.claude.com/docs/en/settings` |
| Permissions | `https://code.claude.com/docs/en/permissions` |
| Skills | `https://code.claude.com/docs/en/skills` |
| Sub-agents | `https://code.claude.com/docs/en/sub-agents` |

MCP の行は LAM v4.4.1 に倣い削除（MCP 仕様は別途確認先があるため）。

---

## AoT 分析: 設計 Atom 分解

### Atom テーブル

| Atom | 内容 | 依存 | 並列可否 |
|------|------|------|---------|
| A1 | docs/artifacts/ ディレクトリ新設の決定 | なし | - |
| A2 | .claude/rules/ 更新（TDD 内省 v2、三分類化等） | A1（パス依存） | A3 と並列可 |
| A3 | docs/internal/ 更新（00, 02, 04, 07 等） | A1（パス依存） | A2 と並列可 |
| A4 | CLAUDE.md 更新（Context Management、Memory Policy） | A1 | A5 と並列可 |
| A5 | CHEATSHEET.md 更新（コマンド再編、スキル更新等） | A1 | A4 と並列可 |

**並列設計**: A1 の決定（docs/artifacts/ 採用）を確定した後、A2〜A5 は実装時に並列処理可能。

### Three Agents 適用: 影式固有セクション保持の是非

#### Atom: Wave-Based Development セクションの保持（02_DEVELOPMENT_FLOW.md）

**[Affirmative]**: Wave 実績サマリーと Quality Rules Integration は影式プロジェクトの知識資産。削除すると過去の教訓（L-1〜L-5 由来のルール根拠）が失われる。

**[Critical]**: LAM v4.4.1 が削除した理由はテンプレートの肥大化防止と汎用化であり、影式でも 02 ファイルの肥大化につながる。内容を docs/artifacts/ に移行する選択肢もある。

**[Mediator]**: 結論として保持する。根拠: (1) Wave 実績は過去のコミットに記録されているが、開発フローの文脈で参照できることの価値がある。(2) 「影式固有:」プレフィックスにより LAM 部分との区別が明確。(3) 肥大化リスクは低い（セクション自体はコンパクト）。移行先としての docs/artifacts/ は監査レポート等の揮発的成果物向けであり、プロセス定義の格納には不適切。

---

## リスクと緩和策

| リスク | 影響度 | 確率 | 緩和策 |
|-------|-------|------|--------|
| TDD 内省 v2 移行で PostToolUse hook が未実装の場合、パターン記録が機能しない | 中 | 中 | test-result-output.md の追加と pyproject.toml 設定変更を同時に実施。hook 未実装の場合は WARNING ログのみで機能は継続 |
| docs/artifacts/ 移行で既存の docs/memos/ 参照が断絶する | 高 | 高 | 移行時に docs/memos/ 配下の実使用ディレクトリを確認し、段階的に参照先を更新する |
| /full-save 廃止で git commit 操作の手順が変わり混乱する | 中 | 低 | CHEATSHEET.md と 08_SESSION_MANAGEMENT.md の両方に `/ship` を使用する旨を明示 |
| permission-levels.md の影式固有パスを再追加し忘れる | 高 | 中 | 本設計文書のチェックリストに明示し、実装時の確認事項として管理 |
| upstream-first.md の新 URL が将来変更される | 低 | 低 | upstream-first.md 自体がその確認の入口であるため、変更時に気づく仕組みがある |

---

## 検証チェックリスト（実装時に使用）

### .claude/rules/

- [ ] `test-result-output.md` が新規追加されている
- [ ] `security-commands.md` に deny セクション（rm, mv, chmod/chown 等）と ask セクション（cp, git push 等）が存在する
- [ ] `security-commands.md` の Allow List に Python カテゴリ（python, pytest, ruff, pip, pyenv）が残っている
- [ ] `security-commands.md` から `find` が Allow List に存在しない（ask セクションにある）
- [ ] `permission-levels.md` に「テスト失敗の自明な修正」（PG 級）が記載されている
- [ ] `permission-levels.md` に「フェーズの巻き戻し」（PM 級）が記載されている
- [ ] `permission-levels.md` のファイルパステーブルに影式固有パス（src/kage_shiki/, pyproject.toml, docs/internal/, config/）が存在する
- [ ] `phase-rules.md` の TDD 内省パイプラインが v2（JUnit XML、2回閾値、/retro）になっている
- [ ] `phase-rules.md` に影式固有の L-4 スモークテスト、Green State 5条件、A-1〜A-4 が保持されている
- [ ] `core-identity.md` の Context Compression 書き出し先が `docs/artifacts/` になっている
- [ ] `upstream-first.md` の確認先 URL が `code.claude.com/docs/en/` になっている
- [ ] `upstream-first.md` に権限等級セクション（本ルール変更は PM 級）が存在する
- [ ] `auto-generated/README.md` のライフサイクルが v2（JUnit XML、/retro 経由）になっている
- [ ] `auto-generated/trust-model.md` が v2 モデル（データソース: test-results.xml）になっている
- [ ] `phase-rules.md` と `trust-model.md` の tdd-patterns パスが `docs/artifacts/tdd-patterns/` になっている
- [ ] `building-checklist.md` が変更されていない

### docs/internal/

- [ ] `00_PROJECT_STRUCTURE.md` に `docs/artifacts/` ディレクトリが記載されている
- [ ] `00_PROJECT_STRUCTURE.md` に `.claude/agent-memory/` が記載されている
- [ ] `00_PROJECT_STRUCTURE.md` の SSOT 層名称が「情報層 1/2/3」になっている
- [ ] `02_DEVELOPMENT_FLOW.md` の TDD 内省が v2 になっている
- [ ] `02_DEVELOPMENT_FLOW.md` の Wave-Based Development セクションが保持されている
- [ ] `03_QUALITY_STANDARDS.md` の Section 6（Python）、Section 7（R-1〜R-6）が保持されている
- [ ] `04_RELEASE_OPS.md` に Retrospective Done がデプロイ基準として記載されている
- [ ] `07_SECURITY_AND_AUTOMATION.md` に deny/ask の分離した Deny List が存在する
- [ ] `07_SECURITY_AND_AUTOMATION.md` Section 2 に影式固有コマンド（ruff, pytest 詳細, pip install 等）が保持されている
- [ ] `08_SESSION_MANAGEMENT.md` から /full-save, /full-load が廃止されている
- [ ] `99_reference_generic.md` のフェーズモードタグが各 Phase 見出しに inline 化されている

### CLAUDE.md

- [ ] Context Management が /quick-save, /quick-load の 2種になっている
- [ ] Memory Policy が三層構造（Auto Memory / Subagent Persistent Memory / Knowledge Layer）になっている
- [ ] Hierarchy of Truth の Architecture 参照範囲が `00〜09` を維持している
- [ ] Identity に「影式 (Kage-Shiki)」が明記されている
- [ ] Project Overview（技術スタックテーブル）が保持されている
- [ ] References に `docs/memos/middle-draft/` 行が保持されている

### CHEATSHEET.md

- [ ] セッション管理コマンドが /quick-save, /quick-load の 2種になっている
- [ ] /wave-plan, /retro がワークフローコマンドセクションに移動している
- [ ] /focus, /daily, /adr-create, /security-review, /impact-analysis が削除されている
- [ ] `ui-design-guide` スキルが追加されている
- [ ] `ultimate-think` スキルが削除されている
- [ ] `docs/artifacts/knowledge/` と `.claude/agent-memory/` が状態管理に追加されている
- [ ] プロジェクト技術スタックセクションが保持されている
- [ ] building-checklist.md が Rules 一覧に記載されている
- [ ] 日常ワークフロー 7パターンが保持されている
