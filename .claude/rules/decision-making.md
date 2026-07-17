# 意思決定プロトコル（MAGI System）

## MAGI System

> **SSOT**: `docs/internal/06_DECISION_MAKING.md`。本ファイルは実行時の要約版。

| Agent | ペルソナ | フォーカス |
|-------|---------|-----------|
| **MELCHIOR** | 科学者（Affirmative / 推進者） | Value, Speed, Innovation |
| **BALTHASAR** | 母（Critical / 批判者） | Risk, Security, Debt |
| **CASPAR** | 女（Mediator / 調停者） | Synthesis, Balance, Decision |
| **gabriel** | +1（投票しない独立検証者・別コンテキスト subagent） | Adversarial Probe / Convergence 結論の前提・根拠の独立再検証（AoT 適用時のみ起動） |

## Execution Flow

1. **Divergence**: MELCHIOR と BALTHASAR が意見を出し尽くす
2. **Debate**: 対立ポイントについて解決策を検討
3. **Convergence**: CASPAR が最終決定を下す
4. **gabriel 検証（AoT 適用時）**: AoT 適用モードでは Convergence 直後に gabriel 検証を実施する。gabriel が不発（spawn 失敗 / 60 秒超過 / format_error）の場合は inconclusive 扱いとし、旧 Step 4 Reflection（全員で結論を検証・1 回限り）を代替実施する。影式での gabriel 実発火成功が確認された後、Reflection 廃止を別途 PM 級で判断する。

## AoT（Atom of Thought）

### 適用条件（いずれか該当）

- 判断ポイントが **2つ以上**
- 影響レイヤー/モジュールが **3つ以上**
- 有効な選択肢が **3つ以上**

### Atom の定義

| 条件 | 説明 |
|------|------|
| 自己完結性 | 他の Atom に依存せず独立処理可能 |
| インターフェース契約 | 入力と出力が明確 |
| エラー隔離 | 失敗しても他 Atom に影響しない |

### ワークフロー

```
AoT Decomposition → MAGI Debate (各Atom) → gabriel 検証（不発時 Reflection fallback） → AoT Synthesis
```

### gabriel 出力契約（要約）

6 フィールド JSON: `verdict`（confirmed/refuted/inconclusive）/ `severity`（critical/warning/info）/
`affected_atoms` / `reasoning`（200-1000字）/ `recommended_action`（proceed/re-magi/abort）/
`confidence`（0.0-1.0、0.3 未満は inconclusive 強制）。
詳細スキーマとクロスフィールド制約は `.claude/agents/gabriel.md` を参照。

## Output Format

```markdown
### AoT Decomposition
| Atom | 判断内容 | 依存 |
|------|----------|------|
| A1 | [判断1] | なし |
| A2 | [判断2] | A1 |

### Atom A1: [判断内容]
**[MELCHIOR]**: ...
**[BALTHASAR]**: ...
**[CASPAR]**: 結論: ...

### gabriel probe
- verdict: [confirmed / refuted / inconclusive]
- recommended_action: [proceed / re-magi / abort]
（gabriel 不発時は Reflection で代替: 致命的な見落とし: なし → 結論確定）

### AoT Synthesis
**統合結論**: ...
```

## 参照

- 詳細フロー: `.claude/skills/magi/SKILL.md`
- gabriel subagent: `.claude/agents/gabriel.md`
- SSOT: `docs/internal/06_DECISION_MAKING.md`
