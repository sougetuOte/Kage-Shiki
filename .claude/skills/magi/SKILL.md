---
name: magi
description: >
  MAGI System — AoT 分解 + MELCHIOR/BALTHASAR/CASPAR 合議 + gabriel adversarial probe（不発時 Reflection
  fallback）による構造化意思決定フレームワーク。判断ポイント 2+ / 影響レイヤー 3+ / 選択肢 3+ で使用。
  Use when facing complex decisions with multiple trade-offs or architectural choices.
when_to_use: "判断ポイント 2+ / 影響レイヤー 3+ / 選択肢 3+ の複雑な意思決定・アーキテクチャ選択を行うとき。"
---

# /magi — 構造化意思決定（MAGI System）

名前の由来: エヴァンゲリオンの MAGI システム（3 つの独立した思考体による合議意思決定）+ **gabriel adversarial verifier**（投票権を持たない 4 番目の独立検証者）。

## MAGI System

**SSOT**: `docs/internal/06_DECISION_MAKING.md` を精読すること。

| MAGI | ペルソナ | フォーカス |
|:-----|:--------|:----------|
| **MELCHIOR** | 科学者（推進者）[旧: Affirmative] | Value, Speed, Innovation |
| **BALTHASAR** | 母（批判者）[旧: Critical] | Risk, Security, Debt |
| **CASPAR** | 女（調停者）[旧: Mediator] | Synthesis, Balance, Decision（Step 3 で完結） |
| **gabriel** | +1（投票しない独立検証者・別コンテキスト subagent） | Adversarial probe / 外部視点からの Convergence 検証 / **AoT 適用時のみ起動** |

## 適用条件

以下のいずれかに該当する場合に発動する:

- 判断ポイントが 2 つ以上
- 影響するレイヤー/モジュールが 3 つ以上
- 有効な選択肢が 3 つ以上

**ユーザーが明示的に `/magi` を呼び出した場合は、条件に合致しなくても必ず実行する。**

条件に合致しないかつ明示呼出しでない場合は「従来手法で十分です」と案内する。

## モード判定: AoT 適用 vs 軽量モード

MAGI は 2 つのモードを持つ:

- **AoT 適用モード**: 判断ポイント 2+ / 影響 3+ / 選択肢 3+ の **いずれか** を満たす → Step 0-5 実施（gabriel probe 含む）
- **軽量モード（非 AoT）**: 上記条件を満たさない → Step 1-3 のみ / **gabriel probe は起動しない**（MUST NOT）

MAGI ログ冒頭で必ずモード（`AoT` または `軽量`）を宣言する。

## 実行フロー

### Step 0: AoT Decomposition（分解 / AoT 適用モードのみ）

議題を独立した Atom（判断単位）に分解し、依存 DAG を構築する。

Atom の 3 条件:
- **自己完結性**: 他の Atom に依存せず独立処理可能
- **インターフェース契約**: 入力と出力が明確
- **エラー隔離**: 失敗しても他 Atom に影響しない

```markdown
### AoT Decomposition

| Atom | 判断内容 | 依存 |
|:-----|:---------|:-----|
| A1 | [判断1] | なし |
| A2 | [判断2] | A1 |
```

### Step 1: Divergence（発散）

MELCHIOR と BALTHASAR がそれぞれの立場から意見を出し尽くす。

- **MELCHIOR**: メリット、開発効率、革新性を列挙
- **BALTHASAR**: リスク、セキュリティ懸念、保守コストを列挙

### Step 2: Debate（議論）

対立するポイントについて、具体的な解決策や緩和策を検討する。

### Step 3: Convergence（収束）

CASPAR が議論を整理し、結論を下す。**CASPAR は Step 3 で完結し、gabriel の結果を受けて再処理を行わない**（純調停者化）。

```markdown
### Atom A1: [判断内容]

**[MELCHIOR]**: ...
**[BALTHASAR]**: ...
**[CASPAR]**: 結論: ...
```

### Step 4: gabriel adversarial probe（AoT 適用モードのみ）

CASPAR の Convergence 結論に対し、**独立コンテキスト**で動作する gabriel subagent（`.claude/agents/gabriel.md`）が adversarial verification を実施する。MELCHIOR/BALTHASAR/CASPAR の 3 ペルソナは同一会話コンテキストの中で処理されるため盲点が相関しうる。gabriel は別コンテキストの独立検証者として、外部視点からの異議申し立てを構造的に可能にする（本家 LAM の MAGI v2 (gabriel 統合) 由来・実運用発火実績あり (2026-07-05)）。

**起動条件**:
- AoT Decomposition（Step 0）が実施されていること
- gabriel opt-out 記録がないこと（下記 Step 4.2 参照）

**gabriel の役割**: CASPAR の統合結論を **そのまま正としてではなく**、結論に至った前提・根拠・棄却された代替案を独立に再検証する。

**プローブ観点（rubric 5 観点）**:
1. **論理的一貫性**: 各 Atom の結論に矛盾がないか
2. **仕様整合**: CASPAR の結論が既存仕様（`docs/specs/` / `docs/internal/`）と矛盾しないか
3. **リスク見落とし**: MELCHIOR / BALTHASAR が検討していない重大なリスクの有無
4. **前提検証**: AoT Decomposition で設定した Atom の依存関係が結論に反映されているか
5. **境界条件**: 結論が適用できないエッジケース（スコープ外・例外）が未記録ではないか

**呼び出し方法**: Task ツール経由で `subagent_type=gabriel` を起動する。gabriel は独立コンテキストで動作し、Read/Glob/Grep のみ利用可（Write・Edit・Bash・Agent ツール禁止 / 暴走リスク抑制）。

**タイムアウト**: 60 秒を目安とする（SHOULD）。呼び出し元で経過時間を計測し、超過時は下記「gabriel 不発時の fallback」を実施する。

**gabriel 出力**: 6 フィールド JSON（`.claude/agents/gabriel.md` 参照）:
- `verdict`: `confirmed` / `refuted` / `inconclusive`
- `severity`: `critical` / `warning` / `info`
- `affected_atoms`: Atom 識別子リスト（`verdict=refuted` 時は非空必須）
- `reasoning`: 判定理由（200-1000 字）
- `recommended_action`: `proceed` / `re-magi` / `abort`
- `confidence`: 0.0-1.0（0.3 未満は `verdict=inconclusive` 強制）

#### gabriel 不発時の fallback（Reflection）

AoT 適用モードでは Convergence 直後に gabriel 検証を実施する。gabriel が **不発**（spawn 失敗 / 60 秒超過 / format_error（JSON 必須フィールド欠損・型不一致）のいずれか）の場合は `inconclusive` 扱いとし、旧 Step 4 Reflection（全員で結論を検証・1 回限り）を代替実施する。影式での gabriel 実発火成功が確認された後、Reflection 廃止を別途 PM 級で判断する。

Reflection のルール（gabriel 不発時のみ適用）:
- **修正条件**: 致命的な見落とし（セキュリティ、データ損失、仕様違反）が見つかった場合のみ結論を修正する
- **Bikeshedding 防止**: 「もっと良い案がある」程度では覆さない
- **回数制限**: 最大 1 回。Reflection の Reflection は禁止

```markdown
### Reflection（gabriel 不発時の fallback）

致命的な見落とし: なし → 結論確定
```

> 参考: 本家 LAM の MAGI v2 (gabriel 統合) 由来・実運用発火実績あり (2026-07-05) の計測では、Reflection 単体の結論変更率は 0%（7 件全件「致命的な見落とし: なし → 結論確定」）であり、小標本ながら「無効な安全網」の兆候が観測された。これが gabriel 導入の根拠のひとつである。

### Step 4.1: verdict 別分岐処理

gabriel の返り値に応じて以下のいずれかの経路を辿る。**優先順位は `recommended_action=abort` > `severity=critical` > `warning` > `info` > `confirmed` > `inconclusive`**。

| gabriel 出力 | 挙動 |
|:------------|:-----|
| `recommended_action=abort`（verdict / severity 問わず） | **即時人間エスカレーション**（再 MAGI なし / MAGI 結論を「保留」記録） |
| `verdict=refuted & severity=critical`（初回） | **再 MAGI 1 ラウンド**（`gabriel.reasoning` を Divergence 入力に追加）→ Step 1 に戻る |
| `verdict=refuted & severity=critical`（2 回目） | **人間エスカレーション**（再 MAGI 上限到達 / MAGI 結論を「保留」記録） |
| `verdict=refuted & severity=warning` | MAGI 結論に **gabriel 指摘を併記** + 警告ラベル |
| `verdict=refuted & severity=info` | **記録のみ** / MAGI 結論不変 |
| `verdict=confirmed` | MAGI 結論を確定（gabriel 補強として記録） |
| `verdict=inconclusive` | MAGI 結論を確定（inconclusive 注記を添付） |
| gabriel 不発（timeout / format_error / spawn 失敗） | 上記「gabriel 不発時の fallback」に従い Reflection を実施 |

**再 MAGI カウンター**: 1 ラウンド上限。2 回目の critical refute で自動的に人間エスカレーション。カウンターは MAGI ログセッション単位で管理する。

> timeout・format_error・spawn 失敗の該否判定は自動計測ツールを持たず、**L1（Living Architect）の手動判断規範**とする。本家 LAM には verdict 別分岐の Python 実装（dispatch スクリプト）が存在するが、影式では初回移植の対象外とする。

### Step 4.2: opt-out 経路

以下 2 条件を **すべて** 満たす場合のみ gabriel probe をスキップできる:

1. opt-out 理由を MAGI ログに 1 文以上記録すること
2. **ユーザー（人間）** がスキップを明示的に指示すること

**Auto mode 中に AI 自身が gabriel probe を opt-out することは禁止する**（MUST NOT）。試行された場合は MAGI ログに「opt-out 試行 / 却下」を記録し、通常通り gabriel probe を実施する。

**opt-out 記録形式**:
```markdown
### gabriel opt-out

- 理由: [opt-out の理由を 1 文以上記述]
- opt-out 宣言者: ユーザー（人間）
- 記録日時: YYYY-MM-DD
```

**正当理由の例**:
- 時間的緊急性（締め切り前の軽微な仕様確認等）
- gabriel 判定に必要な情報が揮発的で正確な判定が期待できない場合
- ユーザーがリスクを承知の上で速度優先を選択する場合

### Step 5: AoT Synthesis（統合 / AoT 適用モードのみ）

各 Atom の結論 + gabriel probe 結果（不発時は Reflection 結果）を統合し、最終決定と Action Items を導出する。

```markdown
### AoT Synthesis

**統合結論**: [CASPAR の Convergence 結論を記述]

**gabriel probe 結果**:
- verdict: [confirmed / refuted / inconclusive]
- severity: [critical / warning / info]
- confidence: [0.0-1.0]
- affected_atoms: [Atom 識別子リスト]
- reasoning: [gabriel の判定理由]
- recommended_action: [proceed / re-magi / abort]

（gabriel 不発の場合は上記の代わりに Reflection 結果を記載する）

**最終結論**:
[gabriel 結果を反映した後の最終結論。warning/info の場合は CASPAR 結論に指摘を併記]

**Action Items**:
1. ...
2. ...
```

## §4.1 軽量モード（非 AoT）でのステップ体系

AoT 適用条件を満たさない軽量 MAGI では以下のステップ体系となる:

- Step 0（AoT Decomposition）: **存在しない**
- Step 1（Divergence）: 実施
- Step 2（Debate）: 実施
- Step 3（Convergence）: CASPAR 結論で完結（直接結論確定）
- Step 4（gabriel probe / Reflection fallback）: **起動しない**（MUST NOT）
- Step 5（AoT Synthesis）: 存在しない

MAGI ログ記録時は「MAGI 軽量モード」と明示し、Step 番号体系の混乱を避ける。

## verdict 別ログテンプレート

> **共通注記**: JSON 出力時は §Step 4 の required フィールド 6 件（verdict / severity / affected_atoms / reasoning / recommended_action / confidence）を必ず出力する。以下のログ表示形式は代表フィールドのみを示している。

**confirmed**:
```markdown
### gabriel probe

- verdict: confirmed
- confidence: X.XX
- reasoning: [gabriel の判定理由]
- 処理: MAGI 結論を確定（gabriel 補強として記録）
```

**refuted + severity=critical**:
```markdown
### gabriel probe

- verdict: refuted
- severity: critical
- affected_atoms: [A1, A2]
- reasoning: [gabriel の判定理由]
- 処理: MAGI 結論を破棄し、再 MAGI 1 ラウンドを指示する（初回のみ / 上限 1 回）

> [CRITICAL by gabriel]: [reasoning の要約]
> MAGI 結論を破棄します。gabriel.reasoning を新入力として再 MAGI を実施してください。
```

**refuted + severity=warning**:
```markdown
### gabriel probe

- verdict: refuted
- severity: warning
- affected_atoms: [A1, A2]
- reasoning: [gabriel の判定理由]
- 処理: 以下の指摘を MAGI 結論に併記して進む

> [WARNING by gabriel]: [reasoning の要約]
> 最終判断はユーザー（人間）に委ねます。
```

**refuted + severity=info**:
```markdown
### gabriel probe

- verdict: refuted
- severity: info
- affected_atoms: [A1]
- reasoning: [gabriel の判定理由]
- 処理: 以下の指摘を記録するのみ。MAGI 結論は変更しない

> [INFO by gabriel]: [reasoning の要約]
> 指摘を記録するのみ、結論は変更されない。
```

**inconclusive**:
```markdown
### gabriel probe

- verdict: inconclusive
- confidence: X.XX
- reasoning: [gabriel の判定理由]
- 処理: MAGI 結論を確定（inconclusive 注記を添付）

> [NOTE]: gabriel は確信をもって判定できませんでした（confidence=X.XX）。
> 結論は CASPAR の判断を維持します。
```

**abort**（verdict / severity 問わず）:
```markdown
### gabriel probe

- verdict: [任意]
- severity: [任意]
- recommended_action: abort
- reasoning: [abort 判定理由 / なぜ直ちに人間判断が必須か]
- 処理: MAGI 結論を保留し、人間エスカレーションを直ちに行う（再 MAGI なし）

> [ABORT by gabriel]: 即時人間判断必須。
> MAGI 結論を「保留」として記録し、人間（ユーザー）の対応を待ちます。
```

**gabriel 不発**（timeout / format_error / spawn 失敗 → Reflection fallback）:
```markdown
### gabriel probe

- 状態: 不発（timeout / format_error / spawn 失敗）
- 処理: Reflection にフォールバック（下記参照）

### Reflection（gabriel 不発時の fallback）

致命的な見落とし: なし → 結論確定
（or: 致命的な見落とし: [内容] → 結論修正: [修正内容]）
```

## アンカーファイル

思考過程を必ず `docs/artifacts/YYYY-MM-DD-magi-{用途}.md` に書き出す。
フォーマットは `references/anchor-format.md` を参照。

- 書き込み権限: CASPAR のみ（Single-Writer）
- 読み取り権限: 全 MAGI + gabriel（Multi-Reader）
- 削除: ユーザーのみ可能

## 参照

- SSOT: `docs/internal/06_DECISION_MAKING.md`
- gabriel subagent: `.claude/agents/gabriel.md`
- decision-making ルール: `.claude/rules/decision-making.md`
- アンカーフォーマット: `.claude/skills/magi/references/anchor-format.md`
- 出典: 本家 LAM の MAGI v2 (gabriel 統合) 由来・実運用発火実績あり (2026-07-05)
