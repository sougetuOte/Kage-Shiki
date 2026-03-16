# .claude/rules/ 差分分析

> LAM v4.4.1 → v4.5.0 へのアップデートに伴う差分分析
> 比較日: 2026-03-16

## 概要

| 分類 | ファイル |
|------|---------|
| 共通（両方に存在） | `core-identity.md`, `decision-making.md`, `phase-rules.md`, `security-commands.md`, `permission-levels.md`, `upstream-first.md`, `test-result-output.md`, `auto-generated/README.md`, `auto-generated/trust-model.md` |
| LAM v4.5.0 で新規追加 | `code-quality-guideline.md`, `planning-quality-guideline.md` |
| 影式にのみ存在（影式固有） | `building-checklist.md` |

LAM v4.4.1 → v4.5.0 の主要な変更テーマは以下の4点:
1. **MAGI System の導入** --- Three Agents Model に MAGI 名称（MELCHIOR/BALTHASAR/CASPAR）を付与し、Reflection ステップを追加
2. **PLANNING フェーズの品質基準強化** --- `planning-quality-guideline.md` 新設、Requirements Smells / RFC 2119 / SPIDR / WBS 100% Rule / Example Mapping を体系化
3. **AUDITING フェーズの品質基準明確化** --- `code-quality-guideline.md` 新設、重要度分類（Critical/Warning/Info）の判断基準を外出し、Green State 条件を Issue 観点で再定義
4. **TDD 品質チェックルールの拡張** --- R-5（テスト名と入力値の一致）、R-6（設計書出力ファイルからのアサーション生成）を phase-rules.md に新設

---

## 共通ファイルの差分

### core-identity.md

#### 差分

**影式（現行 v4.4.1 適用済み）**:
```markdown
# Living Architect 行動規範

## Active Retrieval（能動的検索原則）
...
## 権限等級（PG/SE/PM）
...
## Subagent 委任判断    ← 影式固有（LAM テンプレートにない）
...
## コンテキスト節約原則  ← 影式固有（LAM テンプレートにない）
...
## Context Compression

セッションが長くなった場合:
1. 決定事項と未解決タスクを `docs/tasks/` または `docs/artifacts/` に書き出す
2. ユーザーに「コンテキストをリセットします」と宣言
```

**LAM v4.5.0**:
```markdown
# Living Architect 行動規範

## Active Retrieval（能動的検索原則）
...
## 権限等級（PG/SE/PM）
...
## Context Compression

セッションが長くなった場合:
1. 決定事項と未解決タスクを `docs/tasks/` または `docs/artifacts/` に書き出す
2. ユーザーに「コンテキストをリセットします」と宣言
```

**差分なし**。v4.4.1 → v4.5.0 間で core-identity.md に変更はない。
影式固有の Subagent 委任判断テーブル、コンテキスト節約原則は引き続き LAM テンプレートに存在しない。

#### 影式固有の保持すべき内容

- **Subagent 委任判断テーブル**: v4.0.1 移行時から影式で独自保持。v4.5.0 にも存在しない。保持継続
- **コンテキスト節約原則（3項目）**: 同上

#### アクション

変更不要。

---

### decision-making.md

#### 変更: MAGI System の導入

**影式（現行 v4.4.1 適用済み）**:
```markdown
# 意思決定プロトコル

> **SSOT**: `docs/internal/06_DECISION_MAKING.md`。本ファイルは実行時の要約版。

## Three Agents Model

| Agent | ペルソナ | フォーカス |
|-------|---------|-----------|
| **Affirmative** | 推進者 | Value, Speed, Innovation |
| **Critical** | 批判者 | Risk, Security, Debt |
| **Mediator** | 調停者 | Synthesis, Balance, Decision |

## Execution Flow

1. **Divergence**: Affirmative と Critical が意見を出し尽くす
2. **Debate**: 対立ポイントについて解決策を検討
3. **Convergence**: Mediator が最終決定を下す
```

**LAM v4.5.0**:
```markdown
# 意思決定プロトコル（MAGI System）

## MAGI System

> **SSOT**: `docs/internal/06_DECISION_MAKING.md`。本ファイルは実行時の要約版。

| Agent | ペルソナ | フォーカス |
|-------|---------|-----------|
| **MELCHIOR** | 科学者（Affirmative / 推進者） | Value, Speed, Innovation |
| **BALTHASAR** | 母（Critical / 批判者） | Risk, Security, Debt |
| **CASPAR** | 女（Mediator / 調停者） | Synthesis, Balance, Decision |

## Execution Flow

1. **Divergence**: MELCHIOR と BALTHASAR が意見を出し尽くす
2. **Debate**: 対立ポイントについて解決策を検討
3. **Convergence**: CASPAR が最終決定を下す
4. **Reflection（新規追加）**: 全員で結論を検証（1回限り）。致命的な見落としがあれば修正
```

主な差分:
1. **タイトル変更**: 「意思決定プロトコル」→「意思決定プロトコル（MAGI System）」
2. **セクション名変更**: 「Three Agents Model」→「MAGI System」
3. **Agent 名に MAGI 名称を付与**: Affirmative → MELCHIOR、Critical → BALTHASAR、Mediator → CASPAR。旧名称はカッコ内に併記
4. **ペルソナの具体化**: 「推進者」→「科学者（Affirmative / 推進者）」等
5. **Reflection ステップの追加**: Execution Flow に Step 4 として「全員で結論を検証（1回限り）」が追加。これにより発散→収束の後に1回の検証ループが入る

#### 変更: AoT ワークフローと Output Format

**影式（現行）**:
```markdown
### ワークフロー

AoT Decomposition → Three Agents Debate (各Atom) → AoT Synthesis
```

**LAM v4.5.0**:
```markdown
### ワークフロー

AoT Decomposition → MAGI Debate (各Atom) → Reflection → AoT Synthesis
```

差分:
1. 「Three Agents Debate」→「MAGI Debate」
2. Reflection ステップがワークフローに挿入

#### 変更: Output Format

**影式（現行）**:
```markdown
**[Affirmative]**: ...
**[Critical]**: ...
**[Mediator]**: 結論: ...
```

**LAM v4.5.0**:
```markdown
**[MELCHIOR]**: ...
**[BALTHASAR]**: ...
**[CASPAR]**: 結論: ...

### Reflection
致命的な見落とし: なし → 結論確定
```

差分: Agent ラベルが MAGI 名称に変更。Reflection セクションが Output Format に追加。

#### 共通部分（変更なし）

- AoT 適用条件（3項目）: 同一
- Atom の定義テーブル: 同一
- AoT Decomposition テーブル形式: 同一
- AoT Synthesis: 同一

#### 影式固有の保持すべき内容

影式現行版には影式固有の追加はない。SSOT 参照注記は v4.5.0 にも存在する。

---

### phase-rules.md

このファイルに最も大きな差分がある。

#### PLANNING セクション

##### 追加: 品質基準セクション

**影式（現行）**: なし

**LAM v4.5.0** で新規追加:
```markdown
### 品質基準

成果物は `.claude/rules/planning-quality-guideline.md` に準拠すること:
- 仕様書: Requirements Smells 検出 + RFC 2119 キーワード統一
- 設計書: Design Doc チェックリスト（非スコープ・代替案・成功基準）
- タスク: SPIDR 分割 + WBS 100% Rule（仕様⇔タスクのトレーサビリティ）
- 明確化: Example Mapping（`/clarify` 併用）
```

PLANNING フェーズの品質要件を外部ガイドラインファイルに委譲する参照セクション。

##### その他

承認ゲート、禁止事項、許可事項は同一。

#### BUILDING セクション

##### 変更: TDD 品質チェックの拡張

**影式（現行 v4.4.1 適用済み）**:
```markdown
### TDD 品質チェック

- [ ] R-1: 仕様突合 — FR/設計仕様のフィールド名・定数名と実装が文字単位で一致
- [ ] R-4: テスト網羅 — 各 FR/要件に対応するテストが存在する
```

**LAM v4.5.0**:
```markdown
### TDD 品質チェック

- [ ] R-1: 仕様突合 — FR/設計仕様のフィールド名・定数名と実装が文字単位で一致
- [ ] R-4: テスト網羅 — 各 FR/要件に対応するテストが存在する
- [ ] R-5: テスト名と入力値の一致 — テスト名に含まれる数値・条件と、実際のテスト入力値が一致していること（例: `test_10k_boundary` なら入力は 10,000）
- [ ] R-6: 設計書出力ファイルからのアサーション生成 — 設計書に「ファイル X を生成する」と記載された出力は、Red ステップで `assert path.is_file()` を書くこと
```

差分:
1. **R-5 追加**: テスト名と入力値の一致。テスト名に含まれる数値・条件が実際のテスト入力と乖離するバグの防止
2. **R-6 追加**: 設計書出力ファイルからのアサーション生成。設計書の出力仕様をテストに直結させる

**注意**: 影式の `building-checklist.md` には既に独自の R-5（異常系テストの義務）、R-6（else のデフォルト値禁止）が存在する。LAM v4.5.0 の R-5/R-6 とは**名前が衝突**するが内容は異なる。移行時に識別子の整理が必要。

##### 共通部分（変更なし）

- 必須事項（4項目）: 同一
- 仕様同期ルール（S-1, S-3, S-4）: 同一
- TDD 内省パイプライン v2: 同一
- 禁止事項（3項目）: 同一

#### AUDITING セクション

##### 変更: 「必須」セクションの重要度分類に code-quality-guideline 参照を追加

**影式（現行 v4.4.1 適用済み）**:
```markdown
### 必須

- チェックリストに基づく網羅的確認
- 重要度分類: Critical / Warning / Info
- 問題の PG/SE/PM 分類（権限等級に基づく）
- 3 Agents Model 適用、根拠明示
```

**LAM v4.5.0**:
```markdown
### 必須

- チェックリストに基づく網羅的確認
- 重要度分類: Critical / Warning / Info（判断基準は `.claude/rules/code-quality-guideline.md` に準拠）
- 3 Agents Model 適用、根拠明示
- 問題の PG/SE/PM 分類（権限等級に基づく）
```

差分:
1. 重要度分類に `code-quality-guideline.md` への参照が追加
2. 項目の順序が微変更（PG/SE/PM 分類が末尾に移動）

##### 変更: Green State 条件の再定義

**影式（現行 v4.4.1 適用済み）** には以下の影式固有セクションがある:
```markdown
### Green State 5条件との対応

| 監査完了条件 | Green State | 識別子 |
|:-----------|:-----------|:-------|
| テスト結果: 全件 PASSED | テスト全パス | G1 |
| ruff: All checks passed | lint エラーゼロ | G2 |
| PG/SE級 Issue: 全件修正済み | 対応可能 Issue ゼロ | G3 |
| 仕様書との整合確認 | 仕様差分ゼロ | G4 |
| セキュリティチェック通過 | セキュリティチェック通過 | G5 |
```

**LAM v4.5.0** では全く異なるアプローチ:
```markdown
### Green State 条件

Critical = 0 かつ Warning = 0 → Green State（監査通過）

Info は件数にかかわらず Green State を阻害しない。
詳細な判断基準は `.claude/rules/code-quality-guideline.md` を参照。
```

差分:
1. 5条件テーブル方式（G1-G5）→ Issue 重要度ベースの条件（Critical=0 かつ Warning=0）に変更
2. `code-quality-guideline.md` に判断基準の詳細を委譲
3. Info が Green State を阻害しないことを明示

影式の G1-G5 テーブルは影式固有の追加であり、LAM v4.5.0 の Green State 条件は Issue 観点（G3 相当）のみを phase-rules.md で定義し、G1/G2/G4/G5 は `docs/specs/green-state-definition.md` に委譲している。

##### 共通部分（変更なし）

- 修正ルール（v4.0.0）: 同一
- コード品質チェック: 同一
- コード明確性チェック: 同一
- ドキュメント・アーキテクチャ: 同一
- 改善提案の禁止事項: 同一
- レポート形式: 同一

#### BUILDING セクション（影式固有）

以下は影式の phase-rules.md にのみ存在し、LAM v4.5.0 にも存在しない:
- 「影式固有: Phase 完了判定（L-4 由来）」--- スモークテスト要件

#### AUDITING セクション（影式固有）

以下は影式の phase-rules.md にのみ存在し、LAM v4.5.0 にも存在しない:
- 「影式固有: 修正後の再検証義務（A-3 由来）」
- 「影式固有: 監査レポート完了条件」
- 「AUDITING ルール識別子（A-1〜A-4）」

#### フェーズ警告テンプレート

変更なし。同一。

---

### security-commands.md

#### 変更: Allow List から Python カテゴリの削除

**影式（現行 v4.4.1 適用済み）**:
```
| Python | `python`, `python -m pytest`, `python -m ruff`, `python -c`, `pip`, `pyenv` ※1 |
```

**LAM v4.5.0**: Python カテゴリなし（影式固有であり、LAM テンプレートには元々ない）

その他の Allow List 項目は同一。

#### 変更: Allow List の pip list → pip show

**影式（現行 v4.4.1 適用済み）**:
```
| パッケージ情報 | `npm list`, `pip list`, `pip show` |
```

**LAM v4.5.0**:
```
| パッケージ情報 | `npm list`, `pip list` |
```

差分: `pip show` が LAM v4.5.0 には含まれていない。影式では v4.4.1 移行時に `pip show` を追加済み。

#### 変更: 実行禁止コマンド（deny）に find 破壊パターンを追加

**影式（現行 v4.4.1 適用済み）**: deny テーブルに4行（ファイル削除、ファイル移動、権限変更、システム変更）

**LAM v4.5.0**: deny テーブルに5行:
```
| ファイル削除 | `rm`, `rm -rf` | 不可逆なデータ消失 |
| ファイル移動 | `mv` | 不可逆なファイル消失・上書き |
| 権限変更 | `chmod`, `chown` | セキュリティ境界の破壊 |
| システム変更 | `apt`, `brew`, `systemctl`, `reboot` | システム設定の変更 |
| find 破壊パターン | `find -delete`, `find -exec rm`, `find -exec chmod`, `find -exec chown` | 再帰的な不可逆操作 |
```

差分: **`find` 破壊パターンが deny テーブルに独立行として追加**。v4.4.1 では注記（`> find は v4.3.1 で ask に移動（-delete, -exec rm 等の破壊的パターンは deny）`）のみだったが、v4.5.0 ではテーブル本体に昇格。

#### 変更: 承認必須コマンド（ask）に find を追加

**影式（現行 v4.4.1 適用済み）**: ask テーブルに4行（ファイル操作、Git 書込、ネットワーク、実行）

**LAM v4.5.0**: ask テーブルに5行:
```
| ファイル操作 | `cp`, `mkdir`, `touch` | 意図しない変更 |
| ファイル検索 | `find` | 通常検索（破壊パターンは deny） |
| Git 書込 | `git push`, `git commit`, `git merge` | リモート影響 |
| ネットワーク | `curl`, `wget`, `ssh` | 外部通信 |
| 実行 | `npm start`, `python main.py`, `make` | リソース枯渇 |
```

差分: **`find` が ask テーブルに独立行として追加**（「通常検索（破壊パターンは deny）」の注記付き）。

#### 変更: v4.0.0 ネイティブ権限モデルセクションの微修正

**影式（現行 v4.4.1 適用済み）**:
```
Layer 1 の `permissions.allow` に PG級コマンド（`ruff format`, `ruff check --fix` 等）が追加されている。
```

**LAM v4.5.0**:
```
Layer 1 の `permissions.allow` に PG級コマンド（`ruff format`, `eslint --fix` 等）が追加されている。
```

差分: PG級コマンドの例示が `ruff check --fix` → `eslint --fix` に変更。汎用化のため。

#### 変更: 実行禁止コマンドの説明文追加

**影式（現行 v4.4.1 適用済み）**: deny セクションにヘッダなし

**LAM v4.5.0**:
```markdown
## 実行禁止コマンド（Layer 0: deny）

不可逆または致命的な影響を持つコマンド。AI による実行を禁止する。
```

#### 変更: 承認必須コマンドの説明文追加

**影式（現行 v4.4.1 適用済み）**: ask セクションにヘッダなし

**LAM v4.5.0**:
```markdown
## 承認必須コマンド（Layer 0: ask）

システムに変更を加える、または外部と通信するコマンド。実行前に必ずユーザーの承認を得る。
```

#### その他

deny/ask の注記（`find` の v4.3.1 移動）、ネイティブ権限モデルの二層構造、Layer 0 の位置付け等は同一。

---

### permission-levels.md

#### 変更: SSOT 宣言の削除（影式固有 → LAM テンプレート標準）

**影式（現行 v4.4.1 適用済み）**:
```markdown
> **SSOT**: 本ファイルが PG/SE/PM 分類の唯一の定義源（ドメイン別 SSOT）。
> phase-rules.md の AUDITING セクション、core-identity.md の権限等級サマリーから参照される。
> 注: `.claude/rules/` 内の各ファイルは担当ドメインの SSOT として機能する。
> プロセス全体の SSOT は `docs/internal/` にある（`00_PROJECT_STRUCTURE.md` 等）。
```

**LAM v4.5.0**: 影式固有の SSOT 宣言は LAM テンプレートに存在しない（v4.4.1 と同様）。

#### 変更: SE級の説明文

**影式（現行 v4.4.1 適用済み）**:
```
修正は許可されるが、完了後にユーザーへ報告する。
```

**LAM v4.5.0**:
```
技術的な判断を含むが、公開 API や仕様に影響しない変更。
```

差分: 行動指示型（「報告する」）→ 定義型（「影響しない変更」）に変更。より簡潔で判断基準が明確。

#### 変更: PM級の説明文

**影式（現行 v4.4.1 適用済み）**: 説明文なし（項目リストのみ）

**LAM v4.5.0**:
```
プロジェクトの方向性・仕様・アーキテクチャに影響する変更。人間の承認が必須。
```

差分: PM級の趣旨を一文で説明する導入文が追加。

#### 変更: ファイルパスベースの分類

**影式（現行 v4.4.1 適用済み）**:
```
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

**LAM v4.5.0**:
```
| `docs/specs/*.md` | PM | 仕様変更 |
| `docs/adr/*.md` | PM | アーキテクチャ変更 |
| `.claude/rules/*.md`, `.claude/rules/*/*.md` | PM | ルール変更（サブディレクトリ含む） |
| `.claude/settings*.json` | PM | 設定変更 |
| `docs/` 配下（上記以外） | SE | ドキュメント更新 |
| `src/` 配下 | SE | ソースコード変更（デフォルト） |
| その他 | SE | 安全側に倒す |
```

差分:
1. `.claude/rules/` に「（サブディレクトリ含む）」の注記が追加
2. `docs/internal/*.md` が削除（影式固有）
3. `pyproject.toml` が削除（影式固有）
4. `src/kage_shiki/` → `src/`（汎用化）
5. `tests/` 配下が削除
6. `config/` 配下が削除（影式固有）

#### 変更: 迷った場合の判断例

**影式（現行 v4.4.1 適用済み）**:
```
- 「テストの大幅な書き換え」→ SE級（公開 API は変わらない）
- 「README の構成変更」→ SE級（仕様書ではない）
- 「.claude/commands/ の変更」→ SE級（ルールではなくコマンド）
- 「package.json の scripts 変更」→ SE級（ビルド設定）
- 「.gitignore の変更」→ SE級
- 「config.toml テンプレートの変更」→ PM級（設定仕様の変更）
- 「docs/internal/ の変更」→ PM級（SSOT）
- 「tests/ の新規テスト追加」→ SE級
```

**LAM v4.5.0**:
```
- 「テストの大幅な書き換え」→ SE級（公開 API は変わらない）
- 「README の構成変更」→ SE級（仕様書ではない）
- 「.claude/commands/ の変更」→ SE級（ルールではなくコマンド）
- 「package.json の scripts 変更」→ SE級（ビルド設定）
- 「.gitignore の変更」→ SE級
```

差分: 影式固有の例（`config.toml テンプレートの変更`、`docs/internal/ の変更`、`tests/ の新規テスト追加`）が v4.4.1 移行時の追加であり、LAM v4.5.0 にも含まれていない。

#### 変更: 参照セクション

**影式（現行 v4.4.1 適用済み）**:
```
- `docs/internal/07_SECURITY_AND_AUTOMATION.md` Section 5 (Hooks-Based Permission System)
- `docs/internal/02_DEVELOPMENT_FLOW.md` (フェーズ別の権限適用)
- phase-rules.md: フェーズ別の修正ルール
- core-identity.md: 権限等級サマリー
- security-commands.md: コマンド安全基準（Layer 0）
```

**LAM v4.5.0**:
```
- `docs/specs/v4.0.0-immune-system-requirements.md` Section 5.1 (権限等級の原定義)
- `docs/internal/07_SECURITY_AND_AUTOMATION.md` Section 5 (Hooks-Based Permission System)
- `docs/internal/02_DEVELOPMENT_FLOW.md` (フェーズ別の権限適用)
```

差分:
1. `docs/specs/v4.0.0-immune-system-requirements.md` への参照が追加
2. 影式独自追加の `phase-rules.md`, `core-identity.md`, `security-commands.md` への相互参照が LAM テンプレートには存在しない

#### その他（変更なし）

- PG/SE/PM 各等級の項目リスト: 同一
- フェーズとの二軸設計テーブル: 同一

---

### upstream-first.md

#### 変更: 確認対象の明示

**影式（現行 v4.4.1 適用済み）**: 「必須: 実装前の仕様確認」ルール文のみ

**LAM v4.5.0**:
```markdown
### 必須: 実装前の仕様確認

以下のいずれかに該当する変更を行う前に、公式ドキュメントを確認すること:

- `.claude/settings.json`（permissions, hooks 等）
- `.claude/hooks/` 配下のスクリプト（入出力形式、イベントタイプ）
- skills / subagents のフロントマター
- MCP サーバー設定
```

差分: 確認が必要な変更対象が具体的にリスト化された。

#### 変更: WebFetch 注意事項の表現

**影式（現行 v4.4.1 適用済み）**: 注意事項なし（v4.4.1 テンプレートの確認手順 Step 2 に `（対話モードのみ）` のみ）

**LAM v4.5.0**: 確認手順の後に注記ブロックを追加:
```markdown
> **注意**: `/full-review` 等の自動フロー内では WebFetch を使用しない（無応答リスクのため）。
> context7 が利用不可の場合は仕様確認をスキップし、対話モードでの確認を案内する。
```

差分: WebFetch 使用制限の理由と代替案が明示された。

#### その他（変更なし）

- 概要/背景: 同一
- 確認先テーブル（URL）: 同一
- 確認手順（5ステップ）: 同一
- 適用タイミング: 同一
- 権限等級: 同一
- Wave 開始前の一括すり合わせ: 同一

---

### test-result-output.md

#### 変更: 概要セクションの簡潔化

**影式（現行 v4.4.1 適用済み）**:
```markdown
## 概要

TDD 内省パイプライン v2 の基盤として、テスト実行結果を JUnit XML 形式で
`.claude/test-results.xml` に出力することを必須とする。
```

**LAM v4.5.0**:
```markdown
## 概要

TDD 内省パイプライン v2 の基盤として、テスト実行結果を構造化ファイルに出力することを必須とする。
```

差分: 「JUnit XML 形式で `.claude/test-results.xml` に出力」→「構造化ファイルに出力」に一般化。

#### 変更: ルールセクションの構造化

**影式（現行 v4.4.1 適用済み）**:
```markdown
## ルール

### 必須: JUnit XML 出力設定

テストフレームワーク導入・変更時に、JUnit XML 出力設定を追加すること。

出力先: `.claude/test-results.xml`

### 必須: .gitignore への追加

`.claude/test-results.xml` を `.gitignore` に追加すること。
テスト結果ファイルはローカル実行の成果物であり、リポジトリに含めない。
```

**LAM v4.5.0**:
```markdown
## ルール

テストフレームワークを導入・変更する際は、以下を必ず行うこと:

1. **JUnit XML 形式**の結果ファイルを `.claude/test-results.xml` に出力する設定を追加
2. `.gitignore` に `.claude/test-results.xml` を追加
```

差分: 2つのサブセクション（「必須: JUnit XML 出力設定」「必須: .gitignore への追加」）→ 番号付きリストに統合。より簡潔。

#### 追加: 理由セクション

**影式（現行 v4.4.1 適用済み）**: なし

**LAM v4.5.0** で新規追加:
```markdown
## 理由

PostToolUse hook がテスト成否を判定するために、構造化された結果ファイルが必要。
Claude Code の PostToolUse 入力には exit code が含まれないため、
テストフレームワーク自身が出力する結果ファイルが唯一の信頼できる情報源となる。
```

exit code 問題の背景説明が追加された。

#### 変更: 言語別設定リファレンスの拡充

**影式（現行 v4.4.1 適用済み）**: Python, Jest, Vitest, Go, Rust の5言語

**LAM v4.5.0**: 同じ5言語 + 以下の追加:

1. **Jest**: `devDependencies に jest-junit を追加すること。` の注記追加
2. **Go**: `go-junit-report` → `gotestsum` に変更。インストールコマンド追加
3. **Rust**: `cargo test -- --format=junit` → `cargo-nextest` / `cargo2junit` の2パターンに拡充
4. **「その他の言語」セクション追加**: 上記以外の言語でも JUnit XML 形式の出力手段を調査するよう指示

#### 追加: 適用タイミングセクション

**影式（現行 v4.4.1 適用済み）**: なし

**LAM v4.5.0** で新規追加:
```markdown
## 適用タイミング

- BUILDING フェーズでテストフレームワークを初めて導入するとき
- テストフレームワークを変更・追加するとき
- 新しい言語をプロジェクトに追加するとき
```

#### 変更: PostToolUse hook との連携 → 結果ファイルが存在しない場合

**影式（現行 v4.4.1 適用済み）**:
```markdown
## PostToolUse hook との連携

- PostToolUse hook がテスト実行後に `.claude/test-results.xml` を読み取る
- FAIL→PASS 遷移を検出し、`.claude/tdd-patterns.log` に記録する
- 結果ファイルが存在しない場合は WARNING ログ出力のみ（テスト動作に影響なし）
```

**LAM v4.5.0**:
```markdown
## 結果ファイルが存在しない場合

PostToolUse hook はテストコマンド検出後に `.claude/test-results.xml` を探す。
ファイルが存在しない場合は WARNING ログを出力し、TDD パターン記録をスキップする。
テスト自体の動作には影響しない。
```

差分: セクション名・構造を変更。内容は同等だが、「結果ファイルが存在しない場合」に焦点を当てた見出しに変更。

#### 変更: 権限等級セクションの微修正

**影式（現行 v4.4.1 適用済み）**:
```
- 本ルールファイル自体の変更: **PM級**
- テストFW設定の追加（本ルールに従った設定変更）: **PG級**
```

**LAM v4.5.0**:
```
- 本ルールファイルの変更: **PM級**
- テストFW設定の追加（本ルールに従った設定変更）: **PG級**
```

差分: 「自体の」の削除。実質同一。

#### 追加: 参照セクション

**影式（現行 v4.4.1 適用済み）**: なし

**LAM v4.5.0** で新規追加:
```markdown
## 参照

- 仕様書: `docs/specs/tdd-introspection-v2.md`
- 信頼度モデル: `.claude/rules/auto-generated/trust-model.md`
```

---

### auto-generated/README.md

#### 変更: 冒頭の説明文追加

**影式（現行 v4.4.1 適用済み）**:
```markdown
# 自動生成ルール

## ライフサイクル
...
```

**LAM v4.5.0**:
```markdown
# 自動生成ルール

このディレクトリには、TDD 内省パイプライン v2 によって自動生成されたルールが配置される。

## ライフサイクル
...
```

差分: ディレクトリの目的を説明する一文が追加。

#### 変更: 参照セクションの仕様書パスから lam/ プレフィックスの有無

**影式（現行 v4.4.1 適用済み）**:
```
- 仕様書: `docs/specs/lam/tdd-introspection-v2.md`
```

**LAM v4.5.0**:
```
- 仕様書: `docs/specs/tdd-introspection-v2.md`
```

差分: 影式では `docs/specs/lam/` サブディレクトリに配置しているが、LAM テンプレートでは `docs/specs/` 直下。影式固有のパス構造を保持する。

#### その他（変更なし）

ライフサイクルのフロー、ファイル命名規則、権限等級、参照セクションの他の項目は同一。

---

### auto-generated/trust-model.md

#### 変更: tdd-patterns.log の形式セクション追加

**影式（現行 v4.4.1 適用済み）**: tdd-patterns.log の形式セクションあり:
```markdown
## tdd-patterns.log の形式

TSV（タブ区切り）形式。PostToolUse hook が自動追記する。

{timestamp}\t{PASS|FAIL}\t{framework}\t{summary}\t"{failed_names}"
```

**LAM v4.5.0**: tdd-patterns.log の形式セクションなし。

差分: 影式では v4.4.1 移行時にこのセクションを追加済み。LAM v4.5.0 テンプレートにはこのセクションが含まれていない。影式固有の追加として保持する。

#### 変更: 観測と分析のフロー

**影式（現行 v4.4.1 適用済み）**:
```
テスト実行 → JUnit XML 出力 (.claude/test-results.xml)
    ↓
PostToolUse hook → tdd-patterns.log に FAIL/PASS 記録
    ↓
FAIL→PASS 遷移時 → systemMessage で /retro 推奨（通知A）
    ↓
/retro 実行（人間が判断）→ Step 2.5 でパターン分析
    ↓
頻出パターン（2回以上）→ ルール候補を draft-NNN.md として提案
    ↓
人間が承認/却下（PM級）
```

**LAM v4.5.0**:
```
テスト実行 → JUnit XML 出力
    ↓
PostToolUse hook → tdd-patterns.log に FAIL/PASS 記録
    ↓
FAIL→PASS 遷移時 → systemMessage で /retro 推奨（通知A）
    ↓
/retro 実行（人間が判断）→ Step 2.5 でパターン分析
    ↓
頻出パターン（2回以上）→ ルール候補を draft-NNN.md として提案
    ↓
人間が承認/却下（PM級）
```

差分: 「JUnit XML 出力 (.claude/test-results.xml)」→「JUnit XML 出力」（パス注記の削除）。実質同一。

#### 変更: v1 からの変更経緯の記述

**影式（現行 v4.4.1 適用済み）**: `(2026-03-13 判明)` の日付あり

**LAM v4.5.0**: 同一文面。変更なし。

#### 変更: 参照セクション

**影式（現行 v4.4.1 適用済み）**:
```
- 仕様書: `docs/specs/lam/tdd-introspection-v2.md`
- テスト結果ルール: `.claude/rules/test-result-output.md`
- パターン詳細記録先: `docs/artifacts/tdd-patterns/`
- パターンログ: `.claude/tdd-patterns.log`
- ルール候補: `.claude/rules/auto-generated/draft-*.md`
```

**LAM v4.5.0**:
```
- 仕様書: `docs/specs/tdd-introspection-v2.md`
- テスト結果ルール: `.claude/rules/test-result-output.md`
- パターンログ: `.claude/tdd-patterns.log`
- ルール候補: `.claude/rules/auto-generated/draft-*.md`
```

差分:
1. 仕様書パスの `lam/` プレフィックス: 前述の通り影式固有
2. **`パターン詳細記録先: docs/artifacts/tdd-patterns/` が LAM v4.5.0 から削除**

#### その他（変更なし）

- データソース: 同一
- 閾値テーブル: 同一
- パターン照合ロジック: 同一
- ルール候補のフォーマット: 同一
- ルール寿命管理: 同一
- 権限等級: 同一

---

## LAM v4.5.0 で新規追加されたファイル

### code-quality-guideline.md（新規）

**目的**: BUILDING（予防）と AUDITING（検出）の両フェーズで適用する、言語非依存の品質判断基準を定義。phase-rules.md の AUDITING セクションから重要度分類の詳細を外出ししたファイル。

**主要セクション**:

1. **三層モデル**: Layer 1（ツール領域: formatter/linter）、Layer 2（構造領域: Code Smells/Complexity）、Layer 3（設計領域: アーキテクチャ整合/仕様乖離）
2. **Critical の定義**: Error Swallowing、セキュリティ脆弱性、データ損失、仕様不一致、競合状態
3. **Warning の定義**: Cognitive Complexity > 15、SRP 違反、Code Smells（Feature Envy 等）、Deep Nesting > 3、Long Function > 50行、Parameter Explosion > 4引数、Duplication > 3回、Dead Code、テスト欠如
4. **Info の定義**: 命名微改善、コメント提案、代替案、リファクタリング候補
5. **Green State の Issue 条件**: `Critical = 0 かつ Warning = 0`。G3 の判定基準を定義（G1/G2/G4/G5 は別ファイル）
6. **判断フローチャート**: バグ→Critical、保守困難→Warning、それ以外→Info
7. **アンチパターン**: Bikeshedding、Style Policing、過剰な抽象化要求、行数削減
8. **BUILDING フェーズでの適用**: Refactor ステップでの確認項目
9. **AUDITING フェーズでの適用**: レポート各指摘への重要度ラベル付与例
10. **根拠**: Google Engineering Practices, Conventional Comments, Martin Fowler Code Smells, SonarSource Cognitive Complexity, SOLID

**影式への適用時の注意点**:
- 影式の `building-checklist.md` の R-5（異常系テストの義務）は、code-quality-guideline.md の Critical「Error Swallowing」と部分的に重複する。整合確認が必要
- 影式の phase-rules.md にある Green State 5条件テーブル（G1-G5）との統合方針を決める必要がある。v4.5.0 は G3 のみを code-quality-guideline.md で定義し、他は `docs/specs/green-state-definition.md` に委譲
- `03_QUALITY_STANDARDS.md` との関係: code-quality-guideline.md が具体的な閾値（50行、15 Complexity 等）を定義しており、影式の既存品質標準ドキュメントとの整合確認が必要

---

### planning-quality-guideline.md（新規）

**目的**: PLANNING フェーズで作成する成果物（仕様書、設計書、タスク定義）の品質基準を体系化。phase-rules.md の PLANNING セクションから参照される外部ガイドライン。

**主要セクション**:

1. **Requirements Smells**: 仕様書の曖昧さ検出。危険な単語リスト（曖昧な形容詞、計測不能な性能、逃げ道、無制限スコープ、曖昧な指示語、複合要件）とレビューフロー
2. **RFC 2119 キーワード**: MUST/SHOULD/MAY による義務レベルの統一。混在禁止、ふわっとした要件文の分類義務
3. **Design Doc チェックリスト**: Problem Statement、Non-Goals、Alternatives Considered、Success Criteria の4必須セクション。アンチパターン（Why不足、代替案空、計測不能な成功基準）
4. **SPIDR タスク分割**: Spike/Paths/Interfaces/Data/Rules の5軸。水平分割の禁止、垂直分割の推奨
5. **WBS 100% Rule**: 仕様の全 FR/NFR にタスクが存在するか（Gap チェック）、タスクが仕様にトレースできるか（Orphan チェック）
6. **Example Mapping**: 要件→ルール→具体例→未解決質問の4層構造。Red（未解決質問）が残る要件は実装に進まない

**影式への適用時の注意点**:
- 影式のこれまでの PLANNING フェーズにはこの水準の品質基準がなかった。新規導入
- `/clarify` スキル、`spec-template`、`design-architect`、`task-decomposer` との併用が想定されているが、これらのスキルが影式に存在するかを確認する必要がある
- RFC 2119 キーワードは影式の既存仕様書に遡及適用するかどうかはPM級の判断が必要

---

## 影式にのみ存在するファイル（影式固有）

### building-checklist.md

**内容**: Phase 1 監査・Retro で発見された不具合パターンの防止ルール集。LAM テンプレート（v4.0.1, v4.4.1, v4.5.0 いずれ）には存在しない。

**推奨: 影式固有ルールとして保持**

ただし、LAM v4.5.0 で phase-rules.md に R-5, R-6 が追加されたため、影式 building-checklist.md の R-5（異常系テストの義務）、R-6（else のデフォルト値禁止）と**識別子が衝突**する。以下のいずれかの対応が必要:

- **案A**: 影式の R-5/R-6 を R-12/R-13 等にリナンバリング
- **案B**: LAM の R-5/R-6 を影式では別の識別子で管理
- **案C**: building-checklist.md 内で LAM R-5/R-6 も統合管理

---

## 影式固有保持項目

v4.5.0 移行時に影式固有として保持すべき項目の一覧:

### core-identity.md
- Subagent 委任判断テーブル
- コンテキスト節約原則（3項目）

### phase-rules.md
- 「影式固有: Phase 完了判定（L-4 由来）」--- BUILDING セクション
- 「影式固有: 修正後の再検証義務（A-3 由来）」--- AUDITING セクション
- 「影式固有: 監査レポート完了条件」--- AUDITING セクション
- 「AUDITING ルール識別子（A-1〜A-4）」--- AUDITING セクション
- Green State 5条件テーブル（G1-G5）--- AUDITING セクション（v4.5.0 の Issue ベース Green State との統合方針を要検討）

### security-commands.md
- Python カテゴリ（Allow List）: `python`, `python -m pytest`, `python -m ruff`, `python -c`, `pip`, `pyenv`
- `pip show`（パッケージ情報カテゴリ）
- Python コマンドの allow 設定に関する ※1 注記（二段構成: `settings.json` と `settings.local.json`）

### permission-levels.md
- SSOT 宣言（冒頭4行）
- ファイルパスベース分類の影式固有行: `docs/internal/*.md`, `pyproject.toml`, `src/kage_shiki/`, `tests/`, `config/`
- 迷った場合の影式固有例: `config.toml テンプレートの変更`, `docs/internal/ の変更`, `tests/ の新規テスト追加`
- 相互参照（phase-rules.md, core-identity.md, security-commands.md）

### auto-generated/README.md
- 仕様書パスの `lam/` プレフィックス

### auto-generated/trust-model.md
- tdd-patterns.log の形式セクション（TSV 形式定義）
- 仕様書パスの `lam/` プレフィックス
- パターン詳細記録先の参照行

### building-checklist.md
- ファイル全体（影式固有、R-2〜R-11, S-2）

---

## 移行アクション一覧

### 1. decision-making.md --- MAGI System 導入

| 項目 | 内容 |
|------|------|
| 優先度 | 中 |
| 影響範囲 | decision-making.md のみ |
| 作業内容 | Three Agents Model → MAGI System に名称変更、Reflection ステップ追加、Output Format 更新 |
| 影式固有考慮 | なし |

### 2. phase-rules.md --- PLANNING 品質基準 + TDD ルール拡張 + Green State 再定義

| 項目 | 内容 |
|------|------|
| 優先度 | 高 |
| 影響範囲 | phase-rules.md, building-checklist.md（識別子衝突） |
| 作業内容（PLANNING）| 品質基準セクション追加（planning-quality-guideline.md への参照） |
| 作業内容（BUILDING）| R-5, R-6 追加。影式 building-checklist.md の R-5/R-6 とのリナンバリング |
| 作業内容（AUDITING）| 重要度分類に code-quality-guideline.md 参照追加、Green State 条件の再定義（影式 G1-G5 テーブルとの統合方針をPM判断） |
| 影式固有考慮 | 影式固有セクション（L-4, A-1〜A-4, 監査レポート完了条件）を保持 |

### 3. code-quality-guideline.md --- 新規追加

| 項目 | 内容 |
|------|------|
| 優先度 | 高 |
| 影響範囲 | 新規ファイル。phase-rules.md AUDITING セクションから参照 |
| 作業内容 | LAM v4.5.0 テンプレートをそのまま導入 |
| 影式固有考慮 | building-checklist.md の R-5（異常系テストの義務）との重複確認。`03_QUALITY_STANDARDS.md` との閾値整合確認 |

### 4. planning-quality-guideline.md --- 新規追加

| 項目 | 内容 |
|------|------|
| 優先度 | 高 |
| 影響範囲 | 新規ファイル。phase-rules.md PLANNING セクションから参照 |
| 作業内容 | LAM v4.5.0 テンプレートをそのまま導入 |
| 影式固有考慮 | 参照されるスキル（`/clarify`, `spec-template` 等）の存在確認 |

### 5. security-commands.md --- find 破壊パターンの deny 昇格

| 項目 | 内容 |
|------|------|
| 優先度 | 中 |
| 影響範囲 | security-commands.md |
| 作業内容 | deny テーブルに find 破壊パターン行を追加、ask テーブルに find 通常検索行を追加、deny/ask セクションの説明文追加、PG級コマンド例示の微修正 |
| 影式固有考慮 | Python カテゴリ、`pip show`、※1 注記を保持 |

### 6. permission-levels.md --- SE級/PM級説明文の改善

| 項目 | 内容 |
|------|------|
| 優先度 | 低 |
| 影響範囲 | permission-levels.md |
| 作業内容 | SE級説明文の更新（定義型に変更）、PM級説明文の追加、ファイルパスベース分類の `.claude/rules/` 注記更新、参照セクションに `docs/specs/v4.0.0-immune-system-requirements.md` 追加 |
| 影式固有考慮 | SSOT 宣言、影式固有パス、影式固有例を保持 |

### 7. upstream-first.md --- 確認対象の明示 + WebFetch 注意事項

| 項目 | 内容 |
|------|------|
| 優先度 | 低 |
| 影響範囲 | upstream-first.md |
| 作業内容 | 「必須: 実装前の仕様確認」に確認対象リスト追加、WebFetch 注意事項の注記ブロック追加 |
| 影式固有考慮 | なし |

### 8. test-result-output.md --- 言語別リファレンス拡充

| 項目 | 内容 |
|------|------|
| 優先度 | 低 |
| 影響範囲 | test-result-output.md |
| 作業内容 | 概要の一般化、ルールセクションの統合、理由セクション追加、Go/Rust リファレンス更新、「その他の言語」セクション追加、適用タイミングセクション追加、参照セクション追加 |
| 影式固有考慮 | 影式は Python (pytest) のみ使用。Go/Rust の更新は直接影響なし |

### 9. auto-generated/README.md --- 冒頭説明文追加

| 項目 | 内容 |
|------|------|
| 優先度 | 低 |
| 影響範囲 | auto-generated/README.md |
| 作業内容 | ディレクトリ説明の一文を追加 |
| 影式固有考慮 | 仕様書パスの `lam/` プレフィックスを保持 |

### 10. auto-generated/trust-model.md --- パターン詳細記録先の参照削除

| 項目 | 内容 |
|------|------|
| 優先度 | 低 |
| 影響範囲 | auto-generated/trust-model.md |
| 作業内容 | フロー図の微修正のみ |
| 影式固有考慮 | tdd-patterns.log の形式セクション、仕様書パスの `lam/` プレフィックス、パターン詳細記録先の参照行を保持 |

### 11. building-checklist.md --- R-5/R-6 識別子衝突への対応（PM級判断必要）

| 項目 | 内容 |
|------|------|
| 優先度 | 高 |
| 影響範囲 | building-checklist.md |
| 作業内容 | LAM v4.5.0 の R-5（テスト名と入力値の一致）、R-6（設計書出力ファイルからのアサーション生成）との識別子衝突を解消。影式の R-5 → R-12、R-6 → R-13 等にリナンバリングを推奨 |
| 影式固有考慮 | building-checklist.md 全体が影式固有。phase-rules.md への参照コメントの更新も必要 |

---

## 移行後の想定ファイル構成

```
.claude/rules/
├── core-identity.md              ← 変更なし（影式固有セクション保持）
├── decision-making.md            ← MAGI System 導入 + Reflection 追加
├── phase-rules.md                ← PLANNING 品質基準追加 + R-5/R-6 追加 + Green State 再定義 + 影式固有保持
├── security-commands.md          ← find 破壊パターン deny 昇格 + 影式固有保持
├── permission-levels.md          ← SE/PM 説明文改善 + 影式固有保持
├── upstream-first.md             ← 確認対象明示 + WebFetch 注意事項追加
├── building-checklist.md         ← R-5/R-6 リナンバリング（影式固有保持）
├── test-result-output.md         ← 言語別リファレンス拡充 + 理由/適用タイミング追加
├── code-quality-guideline.md     ← 新規追加（LAM v4.5.0）
├── planning-quality-guideline.md ← 新規追加（LAM v4.5.0）
├── auto-generated/
│   ├── README.md                 ← 冒頭説明文追加
│   └── trust-model.md            ← 微修正 + 影式固有保持
```
