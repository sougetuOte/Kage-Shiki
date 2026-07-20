# HGA 型 Fable 召喚規律（影式移植版）

**移植元**: 本家 LAM（`D:\work7\LivingArchitectModel`、read-only 参照）の `.claude/rules/hga-summoning.md`
（ADR-0009「HGA 型 Fable 召喚アプローチ」運用規律 / hga-approach 討議録 由来）を影式向けに適応した。
以降、本ファイル中でこれらの本家専用資料に言及する箇所は全て「本家 LAM 由来
（`D:\work7\LivingArchitectModel`、read-only 参照）」を指す。影式内には ADR-0009 相当の文書は存在しない。

**移植日**: 2026-07-18

Fable 5 は常駐させず、低頻度・高 stakes の局面にのみ「儀式的に召喚する上位オラクル」として起用する
（HolyGuardianAngel = HGA 型）。日常の判断・実装・査定は既存の委譲モデル
（`CLAUDE.md` §作業体制）が引き続き担う。

## 体制

| 層 | 担当 | 役割 |
|----|------|------|
| L1 | Opus | 媒体・正本保持。ブリーフの選別・圧縮、Fable への召喚、召喚結果の統合 |
| HGA | Fable | スポット召喚のみ（使い捨て・leaf）。設計上の分岐点と根拠を返す |
| L2 | Sonnet | 資料取得・肉付け（Fable が要求した追加資料の取得、確定した設計軸の実装） |
| L3 | Haiku | 事実突合・軽集計 |

人間との協議は **Opus 側のみ**で行う。Fable を人間の判断待ちで開けたまま保持しない
（下記「ステートレス規律」参照）。

## 召喚ゲート

以下いずれかに該当する場合に Fable を召喚する（内部確信度に依存しない、事前観測可能な軸）。

| 軸 | 判定 |
|----|------|
| spec/design 初期 | **無条件召喚**（stakes・novelty がともに最大のため判断すら不要） |
| 不可逆な設計コミット | **無条件召喚** |
| 新規／複数ドメイン統合 | **既定で召喚** |
| MAGI 敵対テスト（「合意しろ」でなく「壊せ／最悪ケースを出せ」）で自力で塞げない破綻 | 召喚 |
| 過去に rework／ドリフトを出した問題種別に該当 | 召喚 |

**影式の召喚ゲート実例**: Phase 2b Wave 3（HaikuEngine 実装 → AgenticSearch パイプライン統合）は
新規ドメイン統合に該当し既定で召喚する。

MAGI の split は非対称シグナルとして扱う。MELCHIOR / BALTHASAR / CASPAR は同一モデル（Opus）の
別ペルソナであり盲点が相関するため、**割れた場合は真の crux として召喚する**（正の信号は有効）。
**割れない場合でも安全の証明にはならない**（負の信号は無効）。上表の召喚ゲートで判定すること。

## 召喚手順

1. **（無条件召喚ゾーンのみ）2 段召喚の crux-scoping**: フルブリーフの前に 2-3k の問題スケッチ
   のみを Fable に渡し、「crux の所在と必要資料」を先に問う。返ってきた指示に基づいて Opus が
   本ブリーフを編む
2. **ブリーフ構成（15-20k）**: crux + 索引 push + currency push（下表）+ hedge 指示を含める。
   索引 push は「Opus が要約対象から外した原資料の目次・ファイル名一覧」を数百トークンで同梱する
   ことを**必須部品**とする（ブリーフに載らない資料の存在を Fable が pull できるようにするため）
3. **召喚**: 出力を「設計上の分岐点と根拠のみ」に縛る指示を必ず添える。実装詳細を書かせない。
   「Opus-tier で実装可能な方向に制約せよ」を明示する
4. **資料要求往復**: 原則 1 回以内に抑える。初回ブリーフに「Fable が要求しそうな資料」を
   予め同梱しておくことで往復自体を減らす
5. **正本化**: 召喚結果（分岐点と根拠）を Opus が正本として保持する。以降の肉付け・実装は
   Sonnet に指示する

**大型探索型の分岐**: 予想 tool_uses 10+ の資料収集主体召喚は、上記手順ではなく
下記「下調べパイプライン（research 委譲パターン）」に従い、Fable brief + Opus subagent 下請け構成にする。
判断・crux 追及型（旧 #1・#4 型）は本手順を維持。

## currency push

Fable は自分の知識が古いと気づけないため、鮮度ギャップは pull では回収できない。召喚前に
Opus が currency sweep を行い、以下をブリーフに畳み込む（**push 必須**）。

| push する currency | 中身 |
|---|---|
| バージョン pin | 使う言語/ランタイム/主要 lib の現行版を日付付きで断定 |
| 変化点 delta（最重要） | 直近の非推奨化・API 改変・改名・新推奨パターンだけ（全部でなく差分） |
| 新規参入 | cutoff 後に生えた/成熟した選択肢 |
| 環境現況 | 実スタックの現在値 |

### hedge 指示（ブリーフに必ず含める 2 項）

- バージョン/API の事実はブリーフ記載を正とし、記載外の事実に依存する箇所は
  **要検証の仮定**として明示させる
- 応答が safety routing で Opus に降格された兆候があれば明示させる
  （routing は transcript で可視のため、Fable の自己申告と併せて監視する）

## ステートレス規律

人間との協議は Opus 側のみで完結させる。Fable への再召喚は**確定争点のみ**をステートレスに
渡す。人間の判断待ちで Fable セッションを開けたまま保持することを **MUST NOT**。
1 召喚内の資料要求往復は原則 1 回以内で可とする。

再召喚はブリーフの再 push のみで済むため、TTL 漏れは「守る対象」ではなく「無視してよい対象」
として扱う。再送コストは 1 回あたり概算 $0.15 程度（フル召喚 $1-4 とは別物）であり、
被害は指数でなく線形に留まる（本家 LAM 実測値 / 影式では未実測の参考値）。

## 漏れ回収の 3 経路

以下 3 経路は混同しやすいため区別すること。

| 経路 | 内容 | 回収手段 |
|------|------|---------|
| 見える漏れ | 索引 push で存在が示された資料 | Fable が pull 要求可 |
| 鮮度（currency） | 知識の鮮度ギャップ | Fable からは要求不能・push のみ |
| 概念的 crux | ブリーフ・索引双方に現れない天井起因の不足 | 既約・2 段召喚で縮小するが完全解消はしない |

## 別予算 2 枠

以下は下記 §envelope 定義の**実 $ envelope（影式では本家に準ずる目安）および Opus quota envelope
（weekly cap 20% 以内）の両方の外**とする。計上ラベルを分離し、コスト暴発源を切り分ける。

| 枠 | 内容 |
|----|------|
| 対話モード召喚 | 真の行き詰まり時のみ、人間を含めた協議を行う召喚 |
| branch モード | Fable に Sonnet を直接ぶら下げる tight な適応探索のみ（稀・バウンド付き） |

### envelope 定義

Fable = credit 従量（実 $）、Opus subagent = subscription quota（weekly cap %）に切り分けて監視する。

| envelope 軸 | 対象 | 目安 |
|:-----------|:-----|:-----|
| **実 $ envelope** | Fable brief 分のみ（メーター実 $） | **本家に準ずる（月 $10-40 目安）・影式での実測により調整** |
| **Opus quota envelope** | Opus subagent の subscription 消費 | weekly cap **20% 以内**（大型探索 3-5 回/週相当） |

### 実測単価（本家 LAM 実測値 / 2026-07 / 影式では未実測の参考値）

- Fable 単独召喚（旧型）: **$1.84（tool_uses=0 短答）〜 $12.66（tool_uses 17 大型）** / 平均 ~$5-8/回
- 下調べパイプライン（Fable brief + Opus 下請け）: Fable brief 分 **~$0.20/回**
- **envelope 監視は API 実メータリング（jsonl 集計）基準**（`docs/artifacts/hga-summon-log.md`
  §day-1 実測メモ 参照。影式での実測値は初召喚後に追記する）
- branch モード（$13+/回）は別予算枠を維持

## 下調べパイプライン（research 委譲パターン）

大型探索型の召喚（tool_uses 10+ / 資料収集主体）は、Fable 単独ではなく
**Fable brief + Opus subagent 下請け** の 2 段構成で実施する。「下調べは Fable の弱点、
Opus の強み」を反映した委譲パターン。

### 根拠（本家 LAM 由来 / 一般的なモデル特性のため影式にもそのまま適用）

- **Fable は doc pull / web 検索が苦手**（community 定説 / 実測でも本体は tool 使用が薄い）
- **Opus は Fable より単価が低い**（credit 従量の実 $ 単価比較）
- **Opus は Claude Code 上で subscription 吸収**（credit 従量ではなく weekly quota 消費）→ 実 $ には効かない
- **Anthropic 内部評価**: Opus lead + Sonnet subagent は単独 Opus 比で優位（multi-agent research system 論文）
- **retrieval 能力**: Opus は Sonnet より長文検索精度で優位（8-needle 1M MRCR v2 系ベンチマーク）

### 委譲先モデル選定

| 委譲先 | 用途 | 判断 |
|:------|:-----|:-----|
| **Opus** | 検索・doc pull・retrieval 全般（**primary**） | 単価優位 + subscription 吸収 + retrieval 優位で最適 |
| Sonnet 5 | **使わない**（下調べ用途では） | 公式 Sonnet 5 プロンプトガイドが「literal interpretation / does not silently generalize / does not infer requests you didn't make」と明記。loose brief で under-deliver するため下調べ用途に不適。詳細は `.claude/rules/model-delegation-prompting.md` 参照 |
| Haiku 4.5 | 事実突合・rubric 採点のみ | 判断・多段推論には非採用（既存規律通り） |

### tight brief 5-slot テンプレート

Anthropic 公式 multi-agent research paper の failure mode（「research the semiconductor shortage」で
subagent が異なる時期を独立探索し labor division 失敗）を修正する形式。全 5 slot 必須。

1. **objective**（何を達成するか / 単一文で）
2. **output format**（返却形式 / JSON or 箇条書き or dimension 別）
3. **tool guidance**（使うべきツール・情報源の順序 / 具体パス OK）
4. **task boundaries**（触らない領域・停止条件）
5. **primary_sources**（絶対視すべき一次資料の URL または context7 library ID）

#### primary_sources 追加の根拠

subagent (Sonnet) は「与えられた一次資料を絶対視する癖」と「context7 等の rich source を能動的に
引かない癖」を持つ。本家 LAM 実測では、subagent がプロジェクト内のローカル派生文書を
公式スキーマの一次情報源と誤認し、フィールドを「非公式」と誤判定した事例が確認されている
（本家 LAM 由来）。L1（Opus）側で context7 の該当ライブラリを fetch して公式仕様と照合し、
subagent の誤判定を訂正した。

primary_sources を明示的に指定することで:
- subagent が最初から正しい一次資料を絶対視する（誤ったローカル文書を一次と誤認しない）
- context7 library ID を書いておけば subagent が能動的に fetch する動線が生まれる
- L1 監督工程での upstream 裏取り往復回数を削減できる

#### primary_sources の書式例

```
5. **primary_sources** (絶対視すべき一次資料 / 該当する場合):
   - context7 library: `/websites/code_claude` (topic: skill frontmatter / hooks 等)
   - upstream URL: https://code.claude.com/docs/en/skills
   - ローカル SSOT: `docs/specs/<該当仕様>.md` §<節番号> (これのみ / 他の派生資料は参考扱い)
```

「該当する場合」は、外部ライブラリ / SaaS API / プラットフォーム機能に触れる brief でのみ必須。
純粋にプロジェクト内部の実装検証 brief では省略可（「該当なし」を 5. に明記して skip）。

### grounding bolt-on（全 subagent 共通）

以下のブロックを全 subagent プロンプトに boilerplate として同梱する（既存の hedge 指示と統合可）。

```
Ground your claims: before reporting any finding as fact, audit it against a tool result
from this session. If you cannot point to the file, line, or command output that proves it,
mark it "unverified".
```

### loose brief の唯一例外

**adversarial coverage-first review**（MAGI 敵対テスト / spec-critic 型）のみ、Anthropic 公式が
明示的に loose 推奨。それ以外の召喚（下調べ・要件確認・crux 追及）は全て tight brief。

```
Report every issue you find, including ones you are uncertain about or consider low-severity.
Do not filter for importance or confidence at this stage - a separate verification step will
do that. Your goal here is coverage.
```

### Sonnet L2 委譲時の追加防御

**背景**（本家 LAM 実測 / Wave C Spike）: Sonnet L2 subagent (`model="sonnet"`) が
meta-response 早期終了する failure mode が確認されている。「the agent is running in the background /
I'll wait for it to complete」型の応答で早期終了し、実作業は孫 subagent (spawnDepth 2) に
丸投げされる。**Sonnet 5 の literal interpretation 特性 + subagent が既定 background 実行される
組み合わせが原因と推定**（本家 LAM 由来）。

**対策 (C + A の組み合わせ)**:

**C (構造的)**: Sonnet 委譲時は frontmatter で nested spawn を封じる:

```yaml
# .claude/agents/<sonnet-executor>.md 内
disallowedTools: [Agent]  # 孫 subagent spawn を封じ、Sonnet に「自分でやる」以外の選択肢を残さない
```

または委譲プロンプト側で明示的に指示:

```
You are the executor. You do NOT have permission to delegate this task to another subagent.
Complete all work in your own context and return the deliverable directly.
```

**A (保険的)**: Sonnet 委譲プロンプトの冒頭に boilerplate 追加:

```
You are the DIRECT EXECUTOR for this task. Do not describe your intent to work "in the
background" — you ARE the background worker. Do not delegate further. Write results
directly to the requested file/format before ending your turn.
```

**適用範囲**: HGA 下調べパイプラインの Sonnet 委譲だけでなく、通常の委譲モデルの L2 委譲にも
適用推奨。

### 技術制約: subagent depth 制限 = 5

**公式仕様** (https://code.claude.com/docs/en/sub-agents 「Nested subagents」節):
> Depth is counted as the number of subagent levels below the main conversation, regardless
> of whether each level runs in the foreground or background. **A subagent at depth five
> doesn't receive the Agent tool and can't spawn further.** The limit is fixed and not
> configurable.

**実測**（本家 LAM 由来 / Wave C Spike）: Sonnet L2 subagent (depth 1) が孫 subagent (depth 2) を
正常に spawn し、孫が実作業を完遂した事例を確認。

**現行運用ガイド**: 技術的には depth 5 まで spawn 可だが、**実運用では depth 1 (flat fan-out)
を推奨**する。理由:

- 深さが増えるほど各段の failure mode (meta-response 早期終了 / literal 過剰解釈等) が
  積み重なり、最終成果物への到達確度が低下する
- コスト・レイテンシが線形以上に増える
- 統合コストが増える (L1 が全 depth の中間結果を統合する必要)
- Fable HGA 召喚の下調べパイプラインでは **Fable brief → Opus subagent (depth 1) 直接**
  で構成し、Opus 内での nested spawn は不要 (Opus が Read/WebFetch 等を直接使う)

**例外的に depth 2+ を許容するケース**:
- コスト最適化のため大型探索を Sonnet に arbitration させ、実 retrieval を孫 (Opus 等) が担う場合
- ただしこの構成は本規律の「Sonnet 委譲時の追加防御」§ で述べた failure mode の影響を受けやすい
- 深さ 2 以上を採用する際は必ず Sonnet 側に `disallowedTools: [Agent]` を設定するか、
  L1 が孫の完走を明示的にモニタリングする体制を組む

### コスト構造（本家 LAM 実測値 / 影式では未実測の参考値）

| 成分 | 支払い形態 | 目安/回 |
|:-----|:----------|-------:|
| Fable brief（in + out 少量） | credit 実 $ | **~$0.20** |
| Opus subagent（retrieval 主体） | subscription quota | weekly cap **3-5%** |
| **合計 実 $** | | **~$0.20** |

Fable 単独大型探索（$12.66 想定）に対し、下調べパイプライン化で **実 $ は 1/50 以下**（$0.20 圏）。
ただし subscription quota は消費するため、L1 常用 Opus と合算した weekly cap 監視は必須。

### 適用ゲート

以下いずれかに該当する召喚に本パターンを適用する。

- 予想 tool_uses 10 回以上（資料収集主体）
- 複数ドメインの資料統合（プロジェクト内 + 外部 doc + web 情報 等）
- crux 探索より前段の下調べフェーズ

適用しないケース（Fable 単独維持）:
- 索引 push で自己完結できる crux 判断のみ
- 敵対テスト / coverage 探索（loose brief 例外に該当）
- 数百トークンの短答（下請け起動コストが overhead）

## 召喚記録

**全召喚を `docs/artifacts/hga-summon-log.md` に追記すること（MUST）**。争点 E の再論禁止規律と
envelope 監視の実行基盤となる。

## 争点 E（枠棄却）再論禁止規律

「HGA 型そのものを棄却すべきか」という枠外検討（争点 E）は、**プロジェクト立ち上げ／大転換時
のみ**問う。毎召喚では問わない（$50/MTok 出力の膨張防止）。一度回答を得たら**決定として記録し、
条件変化（価格レジーム変化・サブスク復帰・Fable 能力の大幅変化）まで再論しない**
（本家 LAM 由来の ADR-0009 決定記録が原型。影式では本ファイル自体を決定記録として扱う）。

## day-1 実測チェックリスト

| # | 確かめること | 状況 |
|---|---|---|
| 1 | プロンプトキャッシュがクレジット従量 Fable に効くか | **解決済み**（公式確認 / read 0.1x。本家 LAM 実測値 / 影式では未実測の参考値） |
| 2 | 自己修復ループの往復回数を実際に抑えられるか | **実測済**（本家 LAM 実測値 / 索引 push で往復 0 回を確認。影式では未実測の参考値） |
| 3 | Fable が Claude Code で web/tool を使えるか | **解決済み**（本家 LAM の実セッションで確認 / 影式では未実測の参考値） |
| 4 | routing/Opus フォールバックの発火頻度と可視性 | 公式仕様は transcript 可視通知。**監視で対応**（発火領域は攻撃的セキュリティ等で設計討議では稀） |
| 5 | ブリーフの実効入力トークン / input・output 分離 | **解決済**（本家 LAM 実測値 / 影式では未実測の参考値。jsonl 直読み手段が確立済み。cache_creation がコストの過半を支配する内訳が判明している） |
| 6 | 影式での envelope 監視手順（jsonl 集計）の確立 | **未実測（影式固有タスク）**。影式での初召喚時に `docs/artifacts/hga-summon-log.md` へ実測値を記録し、集計手順を確立する |

## Fable サブスク継続注記（旧: 移行期注記）

定額アクセス期間（〜2026-07-20 15:59 JST）終了後も、Fable サブスクリプションは
**従来の週間利用上限の半分まで利用可能な形で継続**する（ユーザー指示 2026-07-20）。
HGA 型での Fable 利用は引き続き可 — 無制限ではないが、**必要とあればためらわない程度**に
使ってよい。本規律のスポット召喚ゲートと envelope 監視は既定として維持する。
（クレジット従量前提の実 $ envelope 記述は、サブスク継続により参考値扱いとする）

## 参照

- `docs/artifacts/hga-summon-log.md`（召喚記録）
- `CLAUDE.md` §作業体制（委譲モデルとの整合）
- `.claude/rules/model-delegation-prompting.md`（Sonnet 5 / Haiku 4.5 への委譲プロンプト指針）
- `.claude/rules/decision-making.md`（MAGI System / MELCHIOR・BALTHASAR・CASPAR の定義）
- 本家 LAM 由来（`D:\work7\LivingArchitectModel`、read-only 参照）: ADR-0009「HGA 型 Fable 召喚
  アプローチ」/ hga-approach 討議録 / 本家 `docs/artifacts/hga-summon-log.md`。本規律の実測値・
  根拠の一次出典であり、影式内には対応文書が存在しない

## 権限等級

本ファイルの変更: **PM級**
