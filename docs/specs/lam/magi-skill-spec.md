# /magi スキル要件仕様書

**バージョン**: 1.1
**作成日**: 2026-03-16 / **更新日**: 2026-07-18（gabriel 統合 = MAGI 3+1 体制。Step 4 を
gabriel adversarial probe に置換し、Reflection は gabriel 不発時の fallback に位置変更。
本改訂は gabriel 初回発火（dry-run）が検出した仕様ドリフトの同時修正 — A-4 準拠）
**ステータス**: draft
**SSOT 参照**: `docs/internal/06_DECISION_MAKING.md`（AoT + MAGI System + gabriel）
**名前の由来**: エヴァンゲリオンの MAGI システム（3 つの独立した思考体による合議意思決定）

---

## 1. 目的

AoT（Atom of Thought）分解 + MAGI System（MELCHIOR / BALTHASAR / CASPAR）
+ gabriel adversarial probe（不発時 Reflection fallback）による構造化意思決定を、
独立したスキル `/magi` として提供する。

### Problem Statement

現在、AoT + Three Agents は `lam-orchestrate` スキル内に統合されている（Section「構造化思考」）。
しかし、タスク分解・並列実行が不要な場面では `lam-orchestrate` を呼び出しづらい:

- `/wave-plan` での Wave 構成判断
- `/full-review` での Issue 分類・修正方針決定
- 設計トレードオフ分析（PLANNING フェーズ）
- 命名・技術選定などの単発判断

Plan E の PLANNING で AoT + Three Agents を 3 回手動適用した実績が需要を証明。

### 解決後の理想状態

- `/magi` で構造化意思決定を単独起動できる
- `lam-orchestrate` からは `/magi` を内部参照で呼び出す（重複コードなし）
- 適用条件に合致する場面で自動提案される
- gabriel（独立 adversarial verifier）により結論の品質が別コンテキストで検証される

---

## 2. MAGI System ペルソナ定義

Three Agents Model を MAGI System に改名し、ペルソナ名をエヴァンゲリオン準拠に統一する。

| MAGI | 旧名 | ペルソナ | フォーカス |
|:-----|:-----|:--------|:----------|
| **MELCHIOR** | Affirmative | 科学者（推進者） | Value, Speed, Innovation |
| **BALTHASAR** | Critical | 母（批判者） | Risk, Security, Debt |
| **CASPAR** | Mediator | 女（調停者） | Synthesis, Balance, Decision |

> **SSOT 変更（PM級）**: `docs/internal/06_DECISION_MAKING.md` のペルソナ名を
> Affirmative/Critical/Mediator → MELCHIOR/BALTHASAR/CASPAR に変更する。
> 旧名は括弧書きで併記する（後方互換）。

---

## 3. 実行フロー

```
Step 0: AoT Decomposition（分解）
  └─ 議題を独立した Atom に分解し、依存 DAG を構築

Step 1: Divergence（発散）
  └─ MELCHIOR と BALTHASAR がそれぞれの立場から意見を出し尽くす

Step 2: Debate（議論）
  └─ 対立ポイントについて解決策・緩和策を検討

Step 3: Convergence（収束）
  └─ CASPAR が議論を統合し、結論を下す

Step 4: gabriel adversarial probe（2026-07-18 改訂）
  └─ 別コンテキストの独立 subagent（.claude/agents/gabriel.md）が結論を敵対検証
  └─ 6 フィールド JSON verdict を宣言的分岐表（SKILL.md）で処理
  └─ gabriel 不発（spawn 失敗 / 240 秒超過 / format_error）時は旧 Reflection を fallback 実施

Step 5: AoT Synthesis（統合）
  └─ 各 Atom の結論を統合し、最終決定 + Action Items を導出
```

---

## 4. 機能要件

### FR-M1: スキル単独起動

ユーザーが `/magi <議題>` で呼び出すと、上記 Step 0〜5 を実行する（MUST）。
ユーザーが明示的に `/magi` を呼び出した場合は、適用条件に合致しなくても実行する（MUST）。

### FR-M2: 適用条件の自動判定

適用条件（いずれか該当で発動）:

| 条件 | 定量的目安 |
|:-----|:---------|
| 複数の独立した判断を含む | 判断ポイントが 2 つ以上 |
| 影響範囲が複数ドメイン | 影響するレイヤー/モジュールが 3 つ以上 |
| 選択肢が多い | 有効な選択肢が 3 つ以上 |

条件に合致しない場合かつユーザー明示呼出しでない場合は「従来手法で十分です」と案内する（SHOULD）。

### FR-M3: gabriel adversarial probe（2026-07-18 改訂）

AoT 適用モードでは Step 3（Convergence）完了後に Step 4（gabriel probe）を実行する（MUST）。
軽量 MAGI（非 AoT）では gabriel を起動しない（MUST NOT）。

gabriel probe のルール:
- **独立性**: 別コンテキストの subagent（`.claude/agents/gabriel.md` / Read・Glob・Grep のみ）が検証する
- **出力契約**: 6 フィールド JSON（verdict / severity / affected_atoms / reasoning /
  recommended_action / confidence）。分岐処理は `.claude/skills/magi/SKILL.md` の宣言的分岐表に従う
- **再 MAGI 上限**: refuted+critical による再 MAGI は最大 1 回。2 回目は人間エスカレーション（MUST）
- **opt-out**: ユーザー（人間）の明示指示 + 理由記録の 2 条件。Auto mode 中の AI 自身による opt-out は禁止

Reflection fallback のルール（gabriel 不発時のみ）:
- **発動条件**: gabriel の spawn 失敗 / 240 秒超過（2026-07-20 実測再校正・暫定。実測 3 回蓄積後に再校正） / format_error（L1 手動判定）
- **内容**: 旧 Step 4 Reflection（全員で結論を検証・1 回限り・致命的な見落としのみ修正・
  Bikeshedding 防止・Reflection の Reflection 禁止）を代替実施する
- **廃止条件**: 影式での gabriel 実発火の安定を確認後、Reflection 廃止を PM 級で判断する
  （初回発火は 2026-07-18 dry-run で成功済み）

### FR-M4: 出力フォーマット

`06_DECISION_MAKING.md` Section 5.5 の出力フォーマットを MAGI 命名に更新した形式に準拠する。

```markdown
### AoT Decomposition

| Atom | 判断内容 | 依存 |
|:-----|:---------|:-----|
| A1 | [判断1] | なし |
| A2 | [判断2] | A1 |

### Atom A1: [判断内容]

**[MELCHIOR]**: ...
**[BALTHASAR]**: ...
**[CASPAR]**: 結論: ...

### gabriel probe

verdict: confirmed / severity: info / recommended_action: proceed / confidence: 0.85
（不発時: 「gabriel 不発 → Reflection fallback: 致命的な見落とし: なし → 結論確定」）

### AoT Synthesis

**統合結論**: ...
**Action Items**: ...
```

### FR-M5: lam-orchestrate との統合

`/magi` の SKILL.md を `lam-orchestrate` の `references/` ディレクトリに配置する（MUST）。
`lam-orchestrate` の「構造化思考」セクションは `/magi` の参照に置換する。

### FR-M6: 他スキルからの自動提案

以下のスキルの SKILL.md に「適用条件（FR-M2）に合致する場面で `/magi` を提案せよ」と記述する（SHOULD）:

- `/wave-plan`: Wave 構成の判断時
- `/planning`: 設計トレードオフ分析時
- `/full-review`: Issue 分類・修正方針決定時

### FR-M7: アンカーファイル出力

思考過程を `docs/artifacts/YYYY-MM-DD-magi-{用途}.md` に常に書き出す（MUST）。
`lam-orchestrate` の既存アンカーファイル仕様
（`.claude/skills/lam-orchestrate/references/anchor-format.md`）と統一する。

---

## 5. 非機能要件

### NFR-M1: SSOT 更新

`docs/internal/06_DECISION_MAKING.md` を MAGI 命名に更新する（PM級承認済み）。
旧ペルソナ名（Affirmative/Critical/Mediator）は括弧書きで併記し、後方互換を維持する。
`.claude/rules/decision-making.md`（実行時要約版）も同期更新する。

### NFR-M2: 既存スキルへの影響最小化

`lam-orchestrate` の動作を壊さない。統合は `lam-orchestrate` 側の「構造化思考」
セクションを `/magi` 参照に置換する形で行う。

### NFR-M3: コンテキスト効率

SSOT の全文をスキルファイルに埋め込まない（MUST NOT）。
SSOT への参照（ファイルパス）のみを記述し、実行時に読み込む。

---

## 6. スコープ外（Non-Goals）

- `lam-orchestrate` のタスク分解・並列実行機能の変更
- MAGI 投票メカニズム（多数決システム）の導入
- Chain of Draft / Tree of Thoughts / Graph of Thoughts の取り込み
- `/clarify` スキルとの Three Agents 実装共有（両者は独立）

---

## 7. 成功基準

| 基準 | 計測方法 |
|:-----|:--------|
| `/magi <議題>` で MAGI System + gabriel probe（AoT 適用時）が実行される | 手動テスト |
| 出力に MELCHIOR/BALTHASAR/CASPAR のペルソナ名が使用される | 出力フォーマット確認 |
| gabriel probe の 6 フィールド JSON verdict が出力に含まれる（不発時は Reflection fallback の「致命的な見落とし:」行） | 出力確認（初回発火 2026-07-18 dry-run 済） |
| `lam-orchestrate` から `/magi` が参照される | `references/` に SKILL.md が配置されていること |
| 他スキル（wave-plan, planning, full-review）に提案指示が記述される | 各 SKILL.md に `/magi` 提案の記述があること |
| アンカーファイルが常に生成される | `docs/artifacts/` にファイルが存在すること |
| SSOT が MAGI 命名に更新されている | `06_DECISION_MAKING.md` のペルソナ名が MELCHIOR/BALTHASAR/CASPAR であること |
| 既存テストが全 PASSED | 回帰なし |

---

## 8. 参照

- SSOT: `docs/internal/06_DECISION_MAKING.md`
- lam-orchestrate: `.claude/skills/lam-orchestrate/SKILL.md`
- アンカーフォーマット: `.claude/skills/lam-orchestrate/references/anchor-format.md`
- decision-making ルール: `.claude/rules/decision-making.md`
- gabriel agent 定義: `.claude/agents/gabriel.md`（2026-07-18 追加 / 本家 LAM の MAGI v2 由来）
- Reflection 根拠: [Multi-Agent Reflexion (MAR)](https://arxiv.org/html/2512.20845)
- AoT 根拠: [Atom of Thoughts (NeurIPS 2025)](https://arxiv.org/html/2502.12018)
- メモリ: `project_ultimate_think_revival.md`
