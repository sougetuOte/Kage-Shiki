# 復帰 + LAM 現代化 作業手順書（並列実行計画）

**作成日**: 2026-07-18
**根拠**: `D:\work7\claude.md_dev2` 復帰パッケージ v1.0（2026-07-02）+ 本家 LAM 10 日ドリフト調査（本日実施）
**実行体制**: ユーザー指示により自律実行（選択は Living Architect 推奨を採用）/ 並列最大 3
**Fable 定額期限**: 2026-07-20 15:59 JST（HGA 召喚は期限内に気楽に使用 — ユーザー指示）

---

## 0. 検証済み事実（Wave R0 — 完了）

| 項目 | 結果 |
|------|------|
| pytest | **991 passed**（16.34s）/ カバレッジ 93% — 2026-04-29 記録と完全一致 |
| ruff check | All checks passed（ruff 0.15.5） |
| Python venv | 3.12.5 正常 |
| git | master / clean / HEAD `900134e`（SESSION_STATE と一致） |
| current-phase | BUILDING（Wave 2 完了時点のまま） |
| 中断点 | Phase 2b Wave 3 未着手 — パッケージの認識と一致、環境ドリフトなし |
| ~/.claude/settings.json | `defaultMode` 未設定（AutoMode 未採用）を確認 |
| agents 8 ファイル | `memory: project` 全て未設定を確認 |

## 1. delta 判断表（パッケージ v1 + 10 日ドリフト補正）

### v1 確定分（L1=Fable 判断焼き込み済 → そのまま実行）

| # | 項目 | 実行内容 |
|---|------|---------|
| D1 | CLAUDE.md §作業体制 | 3.5 層委譲モデル + 担当層判断基準を影式向けに転記適応 |
| D2 | HGA 型 Fable 召喚 | `.claude/rules/hga-summoning.md` 新設 + `docs/artifacts/hga-summon-log.md` 雛形 + CLAUDE.md 参照行。**v1 時点でなく本家 7/18 現行版**（下調べパイプライン・tight brief 5-slot・実測単価 #5-#14 込み）を基に起草 |
| D3 | CLAUDE.md §Execution Permission Modes (Advisory) | 本家転記 + 「defaultMode 未設定を確認済み（2026-07-18）」の現況注記 |
| D4 | CLAUDE.md §Context Management | 絶対値閾値（180K/200K）へ既存節を更新。本家固有インシデント小節は持ち込まない |
| D5 | agents `memory: project` | 8 ファイル（+ 新設 gabriel = 9）へ追加。**事前に upstream 仕様確認**（upstream-first 原則） |

### 10 日ドリフト由来の新規候補（Living Architect 推奨 → HGA 敵対レビュー後に確定）

| # | 項目 | 推奨 | 根拠 |
|---|------|------|------|
| N1 | **gabriel 最小移植**（MAGI 3+1） | **採用** | Reflection 結論変更率 0% は構造問題（同一文脈再処理）でプロジェクト非依存 = 影式の decision-making.md も同じ形骸化を抱える。hooks 依存なし・Markdown 移植のみ・本家で実運用発火実績あり。magi_dispatch.py + テスト 63 件は初回見送り（SKILL.md の宣言的分岐表で運用可） |
| N2 | **model-delegation-prompting.md 移植** | **採用** | 移植コスパ最良（79 行・ほぼ自己完結）。Sonnet 5 リテラル解釈等の failure mode は影式の subagent 運用（lam-orchestrate / full-review）に直結 |
| N3 | fable-l3-protocol.md（L3 同化） | **見送り（v2 送り）** | 正本が外部リポジトリ（Fable-Alembic）にあり、/ship 改修・subagent 注入・hook 前提など埋込依存が広い。Wave 3 未着手のまま導入すると中断中マイルストーンの足元を崩す — v1 の ADR-0008 Phase B 保留と同じ理由構造 |
| N4 | terminology.md | **見送り維持** | v1 判断（遡及改名は churn のみ）から変化なし |
| N5 | py_invoke.sh / shim 回避 | **見送り維持** | hooks 改修を伴う（不可侵 #6）。Wave 3 完了後に ADR-0008 Phase B と一括再検討 |
| N6 | rule-001 | **移植せず** | 内容は LAM 実装密結合。承認済みルールの書式見本として参照パスのみ knowledge 化検討（任意） |

### currency 補正（v1 記載から変わった外部事実）

- Fable 5 定額アクセスは **2026-07-20 15:59 JST まで延長**（v1 記載の 7-07 から変更）。以降クレジット従量（入力 $10/MTok・出力 $50/MTok）
- 本家 gabriel は BUILDING 完了（2026-07-05）+ 実運用発火実績あり — v1 の「本家未着手」前提は失効

## 2. 並列実行計画（最大 3 並列）

```
Wave R1（並列 2）: 諮問・裏取り
  ├─ [HGA] Fable 召喚: 本手順書の delta 判断（特に N1 採用 / N3 見送り）への敵対レビュー
  └─ [upstream] claude-code-guide: memory: project / defaultMode の公式仕様裏取り

Wave R2（並列 3）: 文書起草・適用 ※ CLAUDE.md は Stream A に集約し編集衝突を排除
  ├─ Stream A（L1 直）: CLAUDE.md 統合改訂 = D1 + D3 + D4 + D2/N1 への参照行
  ├─ Stream B（Sonnet）: D2 = hga-summoning.md 影式版 + hga-summon-log.md 雛形
  │                      + N2 = model-delegation-prompting.md 影式版
  └─ Stream C（Sonnet）: N1 = agents/gabriel.md + skills/magi/SKILL.md v2 全面書換
                         + rules/decision-making.md（Reflection→gabriel）
                         + docs/internal/06_DECISION_MAKING.md 同期

Wave R3（逐次・軽量）: D5 = agents 9 ファイルへ memory: project 追加（R2 完了後 — gabriel.md 含むため）

Wave R4（逐次）: 検証 + 記録
  ├─ 整合チェック（参照リンク・不可侵リスト非侵害・rules 間矛盾）
  ├─ pytest 再実行（文書変更のみだが回帰ゼロ確認）
  ├─ SESSION_STATE.md 更新（quick-save 相当）
  └─ 完了報告 + PM 級 Auto 進行の明示通知 + 復帰時レビュー対象リスト①〜⑥提示
```

**依存関係**: R1 → R2（HGA verdict で N1/N3 が覆る場合は R2 スコープ修正）。R2 → R3（gabriel.md 生成待ち）。R3 → R4。
**Stream 間衝突回避**: CLAUDE.md は Stream A 専有。Stream B/C は新規ファイル + 既存別ファイルのみ。

## 3. 権限等級の取り扱い（重要）

CLAUDE.md・`.claude/rules/`・`docs/internal/` の変更は **PM 級**。本来は人間承認必須だが、
本セッションはユーザーが「自律実行・選択は AI 推奨を採用」と明示指示しており（Hierarchy of Truth
第 1 位 = User Intent）、承認ゲートを事後報告に切り替える。ただし:

- 全 PM 級変更を Wave R4 の完了報告で「⚠️ PM 級の Auto 進行」形式で明示列挙する
- 不可侵リスト 7 項目（02-lam-delta.md）は引き続き厳守:
  SESSION_STATE 直接書換禁止（quick-save フロー経由のみ）/ Wave 2 由来ルールの削除・弱体化禁止
  / phase2b specs・tasks 変更禁止 / paused-plans 変更禁止 / hooks・settings.json 改修禁止 / .env 読取禁止
- decision-making.md の Reflection→gabriel 置換は「弱体化」でなく「実測で無効と判明した安全網の強化置換」
  と位置付けるが、既存ルールの改変であるため完了報告で特記する
- `D:\work7\` 配下は read-only。Wave 3 実装には着手しない

## 4. 完了条件

1. D1〜D5 + N1〜N2 適用済み / N3〜N6 見送り理由記録済み（本書）
2. pytest 991 passed 維持・不可侵リスト非侵害
3. HGA 召喚ログに本セッション召喚を記録（新設した影式版ログの初エントリ）
4. SESSION_STATE.md 更新済み（復帰完了 + delta 適用状態 + 次ステップ = 設計書レビュー①〜⑥）

## 5. 中断・再開方法

中断時は `/quick-save` で「Wave R# まで完了」を記録。再開時は本書 §2 の未完了 Wave から継続する。
Wave R2 途中で中断した場合、項目別コミット（§7）前なら `git status` 確認の上で全戻し（git checkout）
を既定とする（混成状態の持ち越し禁止）。

---

## 6. HGA 召喚 #K1 verdict 反映（2026-07-18 / L1 裁定）

Fable 敵対レビュー（Critical 3 / Warning 13 / Info 8）を受けた裁定。
反映基準: **critical = 計画修正必須 / warning = 個別裁定し採否記録 / info = 記録のみ**。

### Critical 3 件への対応（全て採用）

| # | 指摘 | 対応 |
|---|------|------|
| F1 | gabriel 移植物が LAM 固有参照（FR-W-C-* / magi_dispatch.py / wave_c テスト等）の宙吊りを抱える | Stream C ブリーフに **自己完結化を必須指示**: 影式に存在しないファイルへの参照禁止・規範根拠はインライン化・出典は「本家 LAM 由来」注記のみ |
| F19 | D4 絶対値閾値 180K/200K が影式の 1M 環境で未校正 | **絶対値方式は維持**（本家根拠 = 「1M でも auto-compact が 200K 付近で発火する疑い」+ upstream #65247 は 1M 環境にこそ適用される）。ただし本家の「仮説・要実測」注記を必ず転記し、影式も 1M 環境である旨を明記 |
| F24 | PM 級一括自律の警告義務・記録欠落 | 本書 §3 を改訂（下記 §6.1）。加えて PreToolUse hook が PM パスで `permissionDecision: "ask"` を出すことを実機確認済 = **人間承認プロンプトは物理的に残る** |

### 主要 Warning の裁定（採用分）

- **F3（最重要分岐）**: N1 を **並存 2 段階方式** に変更。gabriel を追加しつつ、Reflection は
  「gabriel 不発時（timeout / format_error / spawn 失敗）の fallback」として残置。
  影式での実発火成功後に廃止を判断（追跡タスクとして記録）。R4 に **gabriel dry-run** を追加（F16）
- **F2**: timeout 60 秒 / format_error は自動計測せず「L1 手動判定規範」として明記
- **F4**: gabriel tools は frontmatter（Read/Glob/Grep のみ）を正とし、本家 SKILL.md の
  Write/Edit 記述矛盾は移植時に修正
- **F5**: reasoning 執筆規律（主犯名指し・可動部指定・加算分解禁止）は自己完結化し、
  Fable-Alembic / 第 0 原則への参照は持ち込まない（N3 見送りと整合）
- **F6**: opt-out 条項は L1 統治判断として確定: 「ユーザー明示 + 理由記録の 2 条件。
  Auto mode 中の AI 自身による opt-out は禁止」
- **F10**: Stream B ブリーフに currency 再校正指示（移行期注記は 7/20 15:59 に更新・
  本家実測単価/envelope は「本家参考値（影式未実測）」と出典明記）
- **F11**: upstream 裏取り完了（memory: project は公式機構）→ gabriel.md に直接同梱、R3 は残り 8 ファイル
- **F14**: 生成ファイルパスを事前凍結（§2 記載の 5 パスで確定）
- **F15**: gabriel/MAGI 記述の SSOT は Stream C の decision-making.md。R4 整合チェックの
  修正ループは **iter 上限 2 + L1 裁定**（code-quality-guideline.md A-2 裁定プロトコル準用）
- **F17**: `.claude/skills/magi/references/anchor-format.md`（実在確認済）の gabriel 対応同期を C に追加
- **F20**: §作業体制に日付付き移行期注記（7/20 15:59 まで Fable 直用許容）を追加
- **F21**: D3 に「permission-levels.md の Auto mode PM 級ガードレールが優先し AutoMode と独立稼働」の関係定義を含める
- **F25**: R4 で **項目別論理コミット**（D1/D3/D4 → D2+N2 → N1 → D5 → 記録類の 5 分割）により差し戻し粒度を確保

### Info の記録

- F7: 「Reflection 変更率 0%」は小標本（7 件）であり抑止効果は未測定 — 並存方式への変更で吸収
- F9: gabriel.md 新設は安全側で **PM 級扱い** として報告列挙
- F12: **N7 = ADR-0010**: ファイル変更なし。適用原則のみ採用（スキル/agent は project 層 vendored 実体で保持・グローバル層に置かない）
- F23: 完了後の残り定額期間（〜7/20 15:59）の本命は設計書レビュー①〜⑥ + Wave 3 設計判断への Fable 投入 — 本セッションは効率優先
- F27: 不可侵リストは 7 項目（SESSION_STATE / Wave 2 由来ルール / phase2b specs / phase2b tasks / paused-plans / hooks・settings.json / .env）

### 6.1 §3 改訂: 警告義務の履行記録

**明示警告**: 本計画の PM 級事後報告方式は、permission-levels.md「Auto mode での PM 級の扱い」の
明文（`.claude/rules/` 変更等は Auto 進行禁止 — 必ず一時停止）と矛盾する運用である。
これは以下のユーザー指示（2026-07-18、逐語）を Hierarchy of Truth 第 1 位として適用した結果である:

> 「そして並列化や先取りが出来るものは考慮すること。並列の最大数は３。実行前に並列化を前提とした
> 作業手順書を作成しなさい。自律実行を心がけること。選択肢は君の推奨を用いること。」

**本適用は本セッション限定の一回限りであり、先例として一般化しない**（次セッション以降は
permission-levels.md の明文が引き続き有効）。また PreToolUse hook の PM 級 ask ゲートは
無効化せず、プロンプトが出た場合はユーザーの実承認に従う。

## 7. 項目別コミット計画（Wave R4）

1. `docs(revival)`: 手順書 + HGA verdict 反映
2. `docs(claude-md)`: D1 + D3 + D4（CLAUDE.md 統合改訂）
3. `feat(rules)`: D2 + N2（hga-summoning + summon-log 雛形 + model-delegation-prompting）
4. `feat(magi)`: N1（gabriel 並存移植一式）
5. `feat(agents)`: D5（memory: project ×9）
6. `docs(session)`: SESSION_STATE 更新（quick-save フロー経由）
