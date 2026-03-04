# D-15: max_tokens デフォルト値

**決定対象**: requirements.md Section 8 D-15「max_tokens デフォルト値 — config.toml [conversation] に追加 — Anthropic API 必須パラメータ」
**関連 FR**: FR-6.7（Anthropic API 経由で LLM を呼び出す。config.toml の models セクションで指定されたモデルを使用）、FR-5.7（ウィザードの LLM 呼び出し）、FR-3.8（日次サマリー生成）、FR-6.4（整合性チェック）
**ステータス**: 提案（承認待ち）

---

## 1. コンテキスト

Anthropic Messages API では `max_tokens` パラメータが必須である。指定しない場合は API エラーになるため、必ずコードに含める必要がある。

影式には複数の LLM 呼び出し用途があり、それぞれ適切な `max_tokens` が異なる。

| 用途 | 説明 | 期待する応答長の目安 |
|------|------|-----------------|
| 通常会話 | AgentCore の ReAct ループでのキャラクター応答 | 50〜500 tokens |
| クリック反応 | 「突っつかれた」イベントへの短い反応 | 30〜100 tokens |
| 人格生成（ウィザード） | persona_core.md（C1-C11）+ style_samples.md（S1-S7）の生成 | 1000〜2000 tokens |
| 日次サマリー生成 | memory_worker による5〜8文の日記形式 | 200〜600 tokens |
| 整合性チェック | FR-6.4 の人格一貫性確認（追加 API コールなし、プロンプト内指示方式） | — |
| human_block 更新 | ユーザー情報の抽出・整形 | 50〜200 tokens |
| 連想拡張（ウィザード） | キーワードから association_count 個の連想を生成 | 100〜300 tokens |

使用モデル（config.toml 参照）:

| スロット | デフォルトモデル | max output tokens |
|---------|---------------|-----------------|
| `conversation` | claude-haiku-4-5-20251001 | 8192 |
| `memory_worker` | claude-haiku-4-5-20251001 | 8192 |
| `utility` | claude-haiku-4-5-20251001 | 8192 |

Phase 1 では全スロットが Haiku。ユーザーが Sonnet / Opus に変更した場合も同じ `max_tokens` 設定が適用される。Sonnet 3.7 / Opus 3 の max output tokens は 64000（thinking モード時）であり、実用上の上限に差はない。

配置先（D-1 参照）: `agent/llm_client.py` での API 呼び出し + `core/config.py` の AppConfig。

---

## 2. 選択肢分析

### 選択肢 A: 全用途で単一の固定値（config.toml に設定なし）

`max_tokens = 1024` 等の固定値をコードに埋め込む。全ての API 呼び出しで同じ値を使用する。

- **概要**: 最もシンプル。設定不要
- **メリット**: 実装が単純。設定項目が増えない
- **デメリット**: 通常会話（50〜500 tokens）に 1024 を指定すると、モデルが長文を生成しようとする可能性がある（必ずしも max_tokens まで生成するわけではないが、上限の存在が生成に影響しうる）。ウィザードでの人格生成（1000〜2000 tokens）に 1024 では切れる危険がある

### 選択肢 B: config.toml に一つの max_tokens を設定可能

`[conversation]` セクションに `max_tokens = 1024` を追加し、全用途で同一の設定値を参照する。

```toml
[conversation]
temperature = 0.7
max_tokens = 1024      # 追加（全用途共通）
```

- **概要**: 選択肢 A と本質的に同じだが、ユーザーが config.toml で調整できる
- **メリット**: ユーザーが必要に応じて変更できる。記述がシンプル
- **デメリット**: 一つの値で全用途を賄うのは依然として不適切。「通常会話で使う値」が「人格生成にも適用される」設計は直感に反する

### 選択肢 C: 用途別に config.toml で max_tokens を設定

用途ごとに専用の `max_tokens` 設定を持つ。

```toml
[conversation]
temperature = 0.7
max_tokens = 512       # 通常会話（応答の長さ制限）

[wizard]
temperature = 0.9
max_tokens = 2048      # 人格生成（C1-C11 + S1-S7 を一度に生成）

[memory]
max_tokens = 800       # 日次サマリー（5-8文の日記）

[api]
max_retries = 3
# ...
```

- **概要**: 用途の意図を設定値で明示する
- **メリット**: 各用途に最適な値を設定できる。ユーザーが「会話が長すぎる」と感じたら `[conversation].max_tokens` を下げるといった調整が可能。モデル変更（Haiku → Sonnet）時に用途別に上限を調整できる
- **デメリット**: config.toml の設定項目が増える。ユーザーが設定の意味を理解して適切に変更できるか不明。設定の組み合わせによるバグ（例：`[wizard].max_tokens = 100` と低く設定してしまう）のリスクがある

### 選択肢 D: コードに用途別ハードコード + 主要設定のみ config.toml に露出

主要な用途（通常会話）のみ config.toml に設定し、他はコード内のデフォルト値として定義する。

```toml
[conversation]
temperature = 0.7
max_tokens = 512       # ユーザー調整可能な項目はここだけ
```

```python
# コード内定義（擬似コード。実装コードではない）
# agent/llm_client.py の定数定義のイメージ
MAX_TOKENS_DEFAULTS = {
    "conversation": 1024,        # config.toml の値を優先
    "wizard_generate": 2048,
    "wizard_preview": 1024,
    "wizard_association": 512,
    "memory_worker": 800,
    "memory_summary": 800,
    "human_block_update": 256,
    "poke": 256,
}
```

- **概要**: ユーザーが触るべき設定（通常会話）のみを外部化し、内部実装の詳細（wizard 生成時の上限等）はコードで管理する
- **メリット**: config.toml をシンプルに保てる。ユーザーに見せるべき設定と実装詳細を分離できる。用途ごとに適切な値を設定できる。YAGNI（過剰な設定の露出を避ける）に沿っている
- **デメリット**: コードの定数を変更するには再デプロイが必要。ただし影式は現時点でパッケージング配布を考慮していないため、ユーザーがコードを修正するハードルは config.toml と大差ない

---

## 3. Three Agents Perspective

**[Affirmative]**（推進者の視点）

用途別ハードコード + 主要設定のみ config.toml（選択肢 D）を推奨する。

「ユーザーが触るべき設定」と「実装の詳細」は分離すべきである。影式のユーザーは「AIとおしゃべりしたい人」であり、`wizard_generate` の `max_tokens` を調整したいニーズはほぼ存在しない。一方、「会話の応答が長すぎる/短すぎる」という体験に関わる `[conversation].max_tokens` はユーザーが直接調整できると有益である。

また、用途ごとの適切な値を事前に設計することで、「人格生成が途中で切れる」というバグを防止できる。固定値（選択肢 A/B）では Haiku の 8192 上限内に収まっていても、値が用途に合っていない場合の品質問題が発生する。

**[Critical]**（批判者の視点）

選択肢 D の懸念点は「コード内定数の増殖」である。用途が増えるほど（Phase 2 の DesireWorker, AgenticSearch 等）、`MAX_TOKENS_DEFAULTS` の項目が増え、見通しが悪くなる。

また、「通常会話に 512」という設定が本当に適切かは実証前である。キャラクターの応答は短文（50 tokens 以下）もあれば、長い説明（300+ tokens）もある。`max_tokens = 512` で切れるシナリオが発生した場合の対処が必要だ。

**[Mediator]**（調停者の結論）

選択肢 D を採用するが、以下の調整を加える。

1. 通常会話の `max_tokens` は 512 ではなく **1024** を推奨値とする。Haiku はもともと長文を嫌がる傾向があり、512 では意図せず truncate されるリスクが高い。1024 あれば通常の対話で切れることはない
2. wizard 生成は **2048** を推奨値とする。C1-C11 + S1-S7 を一度に生成する場合（方式 A/B）、1500〜2000 tokens は必要。余裕を持って 2048 に設定する
3. `max_tokens` の定数は `agent/llm_client.py` ではなく `core/config.py` の AppConfig に集約する（D-1 の依存ルールに従い、config は core に置く）

---

## 4. 決定

**採用**: 選択肢 D — コードに用途別デフォルト値 + 主要設定のみ config.toml に露出

**理由**:
1. **適切性**: 用途ごとに異なる max_tokens を設定することで、各 API 呼び出しが最適な長さで完結する
2. **YAGNI**: ユーザーが調整する必要がない設定を config.toml に露出しない
3. **品質保証**: 人格生成（2048）・日次サマリー（800）等、用途別の上限を事前に定義することで応答途中切れを防ぐ
4. **シンプル**: config.toml は `[conversation].max_tokens` のみを追加し、他はコードのデフォルト値として管理する

---

## 5. 詳細仕様

### 5.1 用途別 max_tokens デフォルト値一覧

| 用途 | 設定場所 | デフォルト値 | 根拠 |
|------|---------|------------|------|
| 通常会話（conversation） | config.toml `[conversation].max_tokens` | **1024** | 通常の対話応答（50〜500 tokens）に余裕を持たせる。ユーザー調整可能 |
| 人格生成 — 全パラメータ（wizard_generate） | コード定数 | **2048** | C1-C11 + S1-S7 を一括生成。1500〜2000 tokens 必要。W-1〜W-4, W-6 に適用（方式 B の整形補完を含む） |
| 人格生成 — プレビュー会話（wizard_preview） | コード定数 | **1024** | プレビューは通常会話（conversation）と同じ上限を適用。ウィザード中の確認用途として十分 |
| 連想拡張（wizard_association） | コード定数 | **512** | association_count 個（デフォルト5）の連想リストを生成 |
| 記憶ワーカー（memory_worker） | コード定数 | **800** | MemoryWorker が memory_summary 以外の用途（欠損補完・分類等）で使用する汎用呼び出し枠。memory_summary と同値だが用途が異なるため別定義 |
| 日次サマリー（memory_summary） | コード定数 | **800** | 5〜8文の日記形式。300〜600 tokens で収まるが余裕を持って 800 |
| human_block 更新（human_block_update） | コード定数 | **256** | ユーザー属性情報の抽出・整形。短いJSON様テキストを想定 |
| クリック反応（poke） | コード定数 | **256** | 「突っつかれた」への短い反応。長文は不要 |

### 5.2 config.toml への追加

既存の `[conversation]` セクションに `max_tokens` を追加する。

```toml
[conversation]
temperature = 0.7
max_tokens = 1024       # 通常会話の応答最大トークン数
                        # 短い返答でも問題ない（モデルは自然な長さで応答する）
                        # 長すぎる場合は 512 に下げてください
```

### 5.3 config.py での定義（擬似コード）

```python
# core/config.py のイメージ（実装コードではない）

# 有効な purpose の一覧（SSOT）
VALID_PURPOSES = frozenset({
    "conversation", "wizard_generate", "wizard_preview", "wizard_association",
    "memory_worker", "memory_summary", "human_block_update", "poke",
})

# 用途別 max_tokens マップ（conversation 以外の固定値）
_MAX_TOKENS_MAP = {
    "wizard_generate": 2048,
    "wizard_preview": 1024,      # conversation と同等
    "wizard_association": 512,
    "memory_worker": 800,        # memory_summary と同値だが用途が異なるため別定義
    "memory_summary": 800,
    "human_block_update": 256,
    "poke": 256,
}

# スタンドアロン関数として実装（AppConfig のメソッドではない）
# def get_max_tokens(config: AppConfig, purpose: str) -> int:
#   purpose が VALID_PURPOSES に含まれない場合: ValueError を送出
#   purpose が "conversation" の場合: config.conversation.max_tokens を返す
#   それ以外: _MAX_TOKENS_MAP[purpose] を返す

# 同様に get_temperature(), get_model() もスタンドアロン関数として実装
```

### 5.4 llm_client.py での使用パターン（擬似コード）

```python
# agent/llm_client.py の API 呼び出しのイメージ（実装コードではない）

# すべての API 呼び出しに max_tokens を明示する
# 呼び出し側（agent_core.py, memory_worker.py 等）が purpose を渡す

# パターン例:
#   通常会話の場合:
#     max_tokens = config.get_max_tokens("conversation")  # → 1024
#   日次サマリーの場合:
#     max_tokens = config.get_max_tokens("memory_summary")  # → 800
#   人格生成の場合:
#     max_tokens = config.get_max_tokens("wizard_generate")  # → 2048
```

### 5.5 モデル変更時の考慮

ユーザーが `[models].conversation` を Haiku → Sonnet → Opus に変更した場合の影響。

| モデル | max output tokens | D-15 の設定で問題があるか |
|--------|-----------------|----------------------|
| claude-haiku-4-5 | 8192 | 問題なし（1024 / 2048 はどちらも上限以内） |
| claude-sonnet-4-5 | 64000 | 問題なし |
| claude-opus-4-5 | 32000 | 問題なし |

全モデルで D-15 の設定値（最大 2048）は上限以内に収まる。モデル変更時の `max_tokens` 調整は不要。

### 5.6 整合性チェック（FR-6.4）との関係

FR-6.4 の整合性チェックは「追加 API コールなし」でシステムプロンプト内指示方式を採用している（requirements.md Section 9 Mediator 2 参照）。

よって、整合性チェック専用の `max_tokens` は不要である。整合性チェックは通常会話の API コール内で処理されるため、`conversation` の `max_tokens`（1024）が適用される。

---

## 6. 影響範囲

| 影響先 | 内容 |
|--------|------|
| D-1（ディレクトリ構成） | `core/config.py` に AppConfig の `conversation.max_tokens` を追加。`agent/llm_client.py` で参照 |
| D-3（プロンプトテンプレート） | 各プロンプト用途（conversation / wizard / summary）に対応する max_tokens が確定 |
| core/config.py | AppConfig に `conversation.max_tokens: int = 1024` + `get_max_tokens(purpose: str) -> int` メソッドを追加 |
| config.toml | `[conversation]` セクションに `max_tokens = 1024` を追加 |
| agent/llm_client.py | 全 API 呼び出しに `max_tokens = config.get_max_tokens(purpose)` を明示する |
| memory/memory_worker.py | サマリー生成 API 呼び出しで `purpose="memory_summary"` を渡す（→ 800） |
| persona/wizard.py | 人格生成 API 呼び出しで `purpose="wizard_generate"` を渡す（→ 2048） |
| FR-6.7（受入条件） | config.toml の `[models]` で指定されたモデルが使用される。加えて `max_tokens` が用途別に適切な値で設定されることが確認できる |
