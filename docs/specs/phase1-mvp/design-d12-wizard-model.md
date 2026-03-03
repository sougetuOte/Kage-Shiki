# D-12: ウィザードが使用するモデルスロット

**決定対象**: requirements.md Section 8 — D-12「ウィザードが使用するモデルスロット（`[models].utility` 流用 or `[models].wizard` 新設）」
**関連 FR**: FR-5.7, FR-5.5
**ステータス**: 提案（承認待ち）

---

## 1. コンテキスト

### 1.1 なぜこの決定が必要か

ウィザード処理には複数の LLM 呼び出しが含まれる（FR-5.7）。各呼び出しで「どのモデルを使うか」を config.toml の既存スロットから選ぶか、新しいスロットを追加するかを決定する必要がある。

現在の config.toml の `[models]` セクションには以下の3スロットが定義されている:

| スロット | 現在の用途 | config.toml の説明 |
|---------|-----------|------------------|
| `conversation` | 通常対話用 | 対話用（段階的に上位モデルへ移行可能） |
| `memory_worker` | 記憶整理・サマリー用 | 記憶整理・サマリー用 |
| `utility` | 前処理・分類用 | 前処理・分類用 |

また `[wizard]` セクションには:
```toml
[wizard]
association_count = 5
temperature = 0.9
candidate_count = 3
blank_freeze_threshold = 20
```
が定義されており、temperature=0.9 というウィザード固有の高めの値が設定されている。

### 1.2 ウィザード内の LLM 呼び出し箇所

ウィザード処理には以下の LLM 呼び出しが存在する:

| 呼び出し箇所 | 内容 | 必要な特性 |
|------------|------|----------|
| W-1: 連想拡張 | キーワードから association_count 個の連想を生成 | 創造性重要、temperature 0.9 |
| W-2: 候補生成（方式 A） | 連想結果から C1-C11 を持つ候補を candidate_count 個生成 | 創造性重要、temperature 0.9 |
| W-3: 整形・補完（方式 B） | ユーザー記述を C1-C11 形式に整形・補完 | 精度重要、temperature 低め可 |
| W-4: スタイルサンプル生成 | C1-C11 から S1-S7 を生成 | 創造性重要、temperature 0.9 |
| W-5: プレビュー会話 | 生成した人格でユーザーと会話 | 人格再現が重要、conversation モデルと一致が望ましい |
| W-6: 方式 C 凍結提案 | observations から C1-C11 草案を生成 | 精度重要、creative 性も必要 |

### 1.3 `utility` スロットの本来の用途との比較

`utility` スロットの本来の用途は「前処理・分類」（requirements.md）。具体的には:
- FTS5 検索クエリの整形
- human_block 更新要否の判定
- AgentCore の ReAct ループ内でのアクション分類

これらは **精度と速度が重要で、創造性は不要** な処理である。ウィザードの連想拡張・候補生成（W-1〜W-2, W-4）は **創造性が最重要** で、temperature=0.9 という高い値を使う。この2つは用途が根本的に異なる。

---

## 2. 選択肢分析

### 選択肢 A: 既存の `[models].utility` を流用

全てのウィザード呼び出し（W-1〜W-6）で `models.utility` のモデルを使用する。temperature は `wizard.temperature`（0.9）を使用。

- **概要**: 新スロットを追加せず、utility モデルをウィザードでも流用する
- **メリット**:
  - config.toml に変更なし
  - シンプル（スロット数が増えない）
  - Phase 1 では全スロットが同じモデル（Haiku）のため、実質的な差異がない
- **デメリット**:
  - ウィザードが utility の「前処理・分類用」という語義に反する
  - ユーザーが utility モデルを変更した場合、ウィザードにも影響する（意図しない連鎖）
  - プレビュー会話（W-5）で utility モデルを使うと、通常対話の conversation モデルとは異なる体験になる可能性がある（もし将来的にモデルをスロットごとに変えた場合）

### 選択肢 B: `[models].wizard` を新設

`[models]` に `wizard` スロットを追加し、ウィザード固有のモデルを設定できるようにする。

```toml
[models]
conversation = "claude-haiku-4-5-20251001"
memory_worker = "claude-haiku-4-5-20251001"
utility = "claude-haiku-4-5-20251001"
wizard = "claude-haiku-4-5-20251001"   # 新規追加
```

- **概要**: ウィザード専用スロットを新設し、全 W-1〜W-4, W-6 で使用。W-5（プレビュー会話）は `models.conversation` を使用する
- **メリット**:
  - ユーザーがウィザードモデルだけを変更できる
  - `utility` の語義を汚染しない
  - プレビュー会話（W-5）と他のウィザード処理のモデルを明示的に分離できる
- **デメリット**:
  - config.toml に1行追加される
  - Phase 1 では全スロットが同じモデルのため、実質的な差異がない
  - ウィザードは初回起動時のみ使用するため、スロットが追加されても常時使われない

### 選択肢 C: 処理段階ごとに異なるスロット

| 処理 | 使用スロット |
|------|-----------|
| W-1〜W-2, W-4（創造的生成） | `wizard`（新規、または `utility` 流用） |
| W-3（整形・補完） | `utility` |
| W-5（プレビュー会話） | `conversation` |
| W-6（凍結提案） | `memory_worker` |

- **概要**: 処理の性質に合わせてスロットを使い分ける
- **メリット**:
  - 各処理に最適なモデルを指定できる
  - プレビュー会話が確実に `conversation` モデルを使う
  - 整形処理は `utility` の本来用途に近い
- **デメリット**:
  - 設定の複雑さが上がる（どのスロットが何に使われるかをユーザーが理解しづらい）
  - Phase 1 では全スロットが同じモデルのため、複雑さに見合うメリットがない（YAGNI）
  - ウィザードコードの依存が複数スロットに広がり、保守性が低下

---

## 3. Three Agents Perspective

**[Affirmative]**（推進者）:
選択肢 C が最も論理的に整合している。プレビュー会話（W-5）は「生成した人格でのリアルな会話体験を確認する場」であり、本番対話と同じ `conversation` モデルを使わないと「実際の動作を確認している」ことにならない。逆に言えば、プレビューが `conversation` と異なるモデルで動くと、凍結後の本番体験がプレビューと違ったものになり、ユーザーの期待を裏切る。これはウィザードの設計意図（FR-5.5: ユーザーが人格の雰囲気を確認できる）に反する。

**[Critical]**（批判者）:
YAGNI 原則を強調する。Phase 1 では全スロットが `claude-haiku-4-5-20251001` に設定されており、どのスロットを使っても結果は同じである。設計の複雑さを増やすのは将来の「もしかしたら変えるかもしれない」という仮定に基づいており、現時点では根拠がない。選択肢 B の `wizard` スロット新設は、Phase 1 のスコープで必要のない設定項目をユーザーに見せることになる。選択肢 A の流用でも `temperature` は `wizard.temperature`（0.9）を使えば十分であり、スロット名の語義の問題は「実装コメントで補足する」程度で許容できる。

**[Mediator]**（調停者）:
プレビュー会話（W-5）の問題を重視する。

選択肢 C の「全処理を異なるスロットに分ける」部分は YAGNI に抵触するが、**プレビュー会話だけは `conversation` モデルを使うべき**という原則は今後も変わらない。この1点だけを確定し、残りは最もシンプルな選択肢で処理する。

具体的な結論:
- **W-5（プレビュー会話）**: `models.conversation` を使用（確定）
- **W-1〜W-4, W-6（その他のウィザード処理）**: 新規スロット `models.wizard` を追加し、これを使用する

W-3（整形・補完）も創造性が要求される場面があるため（ユーザー記述の不足分を補完する）、`utility` と分けることが望ましい。`wizard` スロットと `utility` スロットを明示的に分離することで、将来ユーザーが「ウィザードの生成品質を上げたい」と思った時に `wizard` を Sonnet に変更できる。

選択肢 B + プレビューは `conversation` という形を採用する。

---

## 4. 決定

**採用**: 選択肢 B の変形（`[models].wizard` 新設 + W-5 は `models.conversation`）

**config.toml への変更**:
```toml
[models]
conversation = "claude-haiku-4-5-20251001"
memory_worker = "claude-haiku-4-5-20251001"
utility = "claude-haiku-4-5-20251001"
wizard = "claude-haiku-4-5-20251001"   # 人格生成ウィザード用（連想拡張・候補生成・整形補完）
```

**処理ごとのモデルスロット割り当て**:

| 処理 | スロット | 理由 |
|------|---------|------|
| W-1: 連想拡張 | `models.wizard` | 創造性重要 |
| W-2: 候補生成（方式 A） | `models.wizard` | 創造性重要 |
| W-3: 整形・補完（方式 B） | `models.wizard` | utility の語義と分離 |
| W-4: スタイルサンプル生成 | `models.wizard` | 創造性重要 |
| W-5: プレビュー会話 | `models.conversation` | 本番体験と一致させるため |
| W-6: 方式 C 凍結提案 | `models.wizard` | 会話分析・生成が必要 |

**理由**:
- プレビュー会話（W-5）は必ず `conversation` モデルを使い、ウィザード完了後の体験と一致させる（FR-5.5 の意図を守る）
- それ以外のウィザード処理は `wizard` スロットに集約し、`utility` の「前処理・分類」という語義を保護する
- Phase 1 では全スロットが同じモデルのため実質的な差異はないが、将来の設定分離に備えた構造を確保する

---

## 5. 詳細仕様

### 5.1 config.toml への追記内容

```toml
[models]
conversation = "claude-haiku-4-5-20251001"   # 通常対話用
memory_worker = "claude-haiku-4-5-20251001"  # 記憶整理・サマリー用
utility = "claude-haiku-4-5-20251001"        # 前処理・分類用
wizard = "claude-haiku-4-5-20251001"         # 人格生成ウィザード用（連想拡張・候補生成・整形補完）
```

### 5.2 temperature の適用ルール

| 処理 | temperature | 出典 |
|------|------------|------|
| W-1〜W-4, W-6 | `wizard.temperature`（デフォルト 0.9） | `[wizard]` セクション |
| W-5（プレビュー会話） | `conversation.temperature`（デフォルト 0.7） | `[conversation]` セクション |

W-5 はあくまで「会話の体験確認」であり、creative な生成ではないため temperature は通常対話と同じ値を使う。

### 5.3 AppConfig の型定義への影響

`AppConfig.models` クラスに `wizard` フィールドを追加する:

```
AppConfig
  └── models: ModelsConfig
        ├── conversation: str
        ├── memory_worker: str
        ├── utility: str
        └── wizard: str  ← 追加
```

デフォルト値は `"claude-haiku-4-5-20251001"`（conversation と同じ）。

### 5.4 WizardController からのモデル参照

`WizardController` は `AppConfig` を受け取り、以下の方法でモデルを参照する:

| 処理 | 参照する設定 |
|------|-----------|
| W-1〜W-4, W-6 | `config.models.wizard` + `config.wizard.temperature` |
| W-5 | `config.models.conversation` + `config.conversation.temperature` |

### 5.5 プレビュー会話（W-5）の体験保証

プレビュー会話が本番体験と一致することを保証するために以下を確認する:

1. **システムプロンプト**: プレビュー会話と本番対話で同じシステムプロンプト構造を使用する（`persona_core.md`、`style_samples.md` の草案を注入）
2. **モデル**: `models.conversation` を使用（本番と同一）
3. **temperature**: `conversation.temperature`（0.7）を使用（本番と同一）
4. **コンテキスト**: ウィザード内で生成した C1-C11 草案・S1-S7 草案をシステムプロンプトに注入する

> **注意**: プレビュー会話は `observations` に保存しない。確定前の会話履歴を永続化すると、正式な記憶と混同される可能性がある。

### 5.6 ユーザー向けドキュメント（config.toml コメント）

config.toml に以下のコメントを付与する:

```toml
[models]
# 通常対話用モデル。好みに応じて Sonnet/Opus にアップグレード可能
conversation = "claude-haiku-4-5-20251001"
# 記憶整理・日次サマリー生成用モデル
memory_worker = "claude-haiku-4-5-20251001"
# 前処理・分類用モデル（FTS5 クエリ整形、更新判定等）
utility = "claude-haiku-4-5-20251001"
# 人格生成ウィザード用モデル（連想拡張・候補生成・整形補完）
# プレビュー会話は conversation モデルを使用
wizard = "claude-haiku-4-5-20251001"
```

---

## 6. 影響範囲

| 影響先 | 内容 |
|--------|------|
| `config.toml` | `[models]` に `wizard` スロットを追加 |
| `AppConfig` / `ModelsConfig` | `wizard: str` フィールドの追加 |
| `WizardController` | W-1〜W-4, W-6 で `config.models.wizard` + `config.wizard.temperature` を使用。W-5 で `config.models.conversation` + `config.conversation.temperature` を使用 |
| D-5（ウィザードフロー） | プレビュー会話（W-5）が `models.conversation` を使うことをフロー仕様に反映（参照依存） |
| D-3（プロンプトテンプレート設計） | ウィザード用プロンプト（W-1〜W-6 のテンプレート）の設計で `wizard` スロットを参照 |
| `requirements.md` 4.3.5（config.toml 定義） | `[models]` セクションの定義に `wizard` を追記（仕様書の更新が必要） |
