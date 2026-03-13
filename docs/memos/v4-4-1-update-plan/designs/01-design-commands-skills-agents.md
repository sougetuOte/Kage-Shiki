# 設計: コマンド / スキル / エージェント移行（v4.0.1 → v4.4.1）

**作成日**: 2026-03-13
**ステータス**: Draft
**対象 Phase**: Phase 2b（LAM v4.4.1 移行）
**関連**: [差分分析](../specs/00-diff-commands-skills-agents.md) | [差分サマリー](../specs/00-diff-summary.md)

---

## 概要

LAM v4.0.1 移行済みの影式（Kage-Shiki）プロジェクトを LAM v4.4.1 に移行するにあたり、
commands / skills / agents の設計判断を記録する。

v4.4.1 移行は v3.x → v4.0.1 移行より変更規模は小さいが、**7コマンドの廃止**と
**出力パスの全面変更**（`docs/memos/` → `docs/artifacts/`）、
および **ultimate-think スキルの廃止** が主要な変更となる。

### 判断の依存関係

```
判断1 (7コマンド廃止)   ─── 判断2・3・4 に影響（吸収先コマンドの拡張）
判断2 (quick-save/load)  ── 独立（影式で使用頻度高）
判断3 (full-review)      ── 独立（最大の差分）
判断4 (retro)            ── 独立（TDD 内省 v2 の採否）
判断5 (ship)             ── 独立（Phase 構成変更）
判断6 (ultimate-think)   ── 判断7（lam-orchestrate 更新）に依存
判断7 (エージェント)     ── 判断3（full-review での quality-auditor 役割）に関連
```

### AoT 分解

| Atom | 設計内容 | 依存 | 並列可否 |
|------|---------|------|---------|
| D1 | 7コマンド廃止戦略 | なし | 独立 |
| D2 | quick-save/load 拡張 | D1（full-save/full-load の吸収確認） | D3〜D7 と並列可 |
| D3 | full-review 大幅拡張 | なし | D2 と並列可 |
| D4 | retro Step 2.5 追加 | なし | 独立 |
| D5 | ship Phase 構成変更 | D1（doc-sync-flag フロー確認） | 独立 |
| D6 | ultimate-think 廃止 | なし | D7 と同時設計 |
| D7 | エージェント更新方針 | D3（quality-auditor の役割変化） | D6 と同時設計 |

---

## 判断1: 7コマンド廃止戦略

### 背景

LAM v4.4.1 でコマンド数が 18 → 11 に削減される。削除される 7 コマンドと吸収先は以下の通り:

| 廃止コマンド | 吸収先 | 廃止理由（LAM 側） |
|-------------|--------|-----------------|
| `daily.md` | `quick-save.md` Step 3 | Daily 記録と KPI 集計を quick-save に統合 |
| `focus.md` | 廃止（外部ツールに委譲） | ポモドーロ機能は専用ツールで代替 |
| `full-load.md` | `quick-load.md` | quick-load が 4 ステップ化し full-load 機能を完全吸収 |
| `full-save.md` | `quick-save.md` + `/ship` | セーブと git コミットを分離。機能の責務が明確化 |
| `adr-create.md` | `adr-template` スキル経由 | コマンドよりスキル呼び出しで統一 |
| `impact-analysis.md` | `building.md` Step 4 | 実装前の Pre-Flight として building フローに組み込み |
| `security-review.md` | `full-review.md` Phase 1 #4 | セキュリティ監査を full-review の 1 エージェントとして統合 |

### 影式での各コマンドの使用頻度評価

| コマンド | 使用頻度 | 主な用途 |
|---------|---------|---------|
| `daily.md` | 高（毎セッション終了時） | KPI 集計と日次記録 |
| `focus.md` | 低（ほぼ未使用） | ポモドーロタイマー。影式ではセッション集中管理を別手段で実施 |
| `full-load.md` | 中（数日ぶりの復帰時） | 詳細な状態確認 + 復帰報告 |
| `full-save.md` | 中（一日の終わり） | git commit + push + daily 記録 |
| `adr-create.md` | 低（ADR 起票時） | ADR ドキュメント生成 |
| `impact-analysis.md` | 低（大規模変更前） | 依存関係調査 |
| `security-review.md` | 低（phase 完了前） | セキュリティチェック |

### 選択肢

#### 選択肢 A: 全廃止（LAM v4.4.1 に完全準拠）

全 7 コマンドを廃止し、LAM v4.4.1 の吸収先で代替する。

**メリット**:
- LAM テンプレートとの完全な整合性
- コマンド数削減でユーザー体験がシンプルになる
- 吸収先コマンドの機能が十分にカバーしている

**デメリット**:
- `daily.md` 廃止により KPI 集計のタイミングが変わる（毎日 → セッション終了時）
- `full-save.md` の「git commit + push」統合機能は `quick-save` + `/ship` の 2 コマンドに分かれる
- `full-load.md` の詳細な状態確認機能が quick-load の構造化サマリーに縮小

#### 選択肢 B: 段階的廃止（高頻度コマンドを暫定維持）

`daily.md` と `full-save.md` のみ暫定維持し、他 5 件を廃止する。

**メリット**:
- 影式での daily 運用フローへの影響を最小化
- 移行リスクを分散できる

**デメリット**:
- LAM テンプレートとの乖離が維持期間中続く
- どのタイミングで完全廃止するかが不明確
- `quick-save.md` の拡張（Step 2, Step 3）が必要なのに old `daily.md` も残存すると重複

#### 選択肢 C: 影式で独自維持（廃止しない）

LAM v4.4.1 に移行しつつ、影式固有コマンドとして全 7 件を維持する。

**メリット**:
- 現行の影式運用に影響なし

**デメリット**:
- LAM テンプレートとの乖離が増大する一方
- `quick-save.md` の拡張（Step 3 に daily 統合）と `daily.md` が並存し、二重管理になる
- v4.5 以降の移行がさらに困難になる

### 推奨案: 選択肢 A（全廃止）

**根拠**:

1. **吸収先が十分にカバーしている**: `full-load.md` の機能は `quick-load.md` の 4 ステップ化で完全吸収。`security-review.md` は `full-review.md` Phase 1 #4 に統合済み。
2. **`daily.md` は quick-save に自然統合される**: セッション終了時に `quick-save` を実行することが標準フローであり、そこで daily 記録と KPI 集計を行う方が操作の一貫性が高い。別途 `/daily` を叩く手間が省ける。
3. **`full-save.md` の分離は設計上の改善**: 「状態保存」と「コミット」を同一コマンドで行うことは責務過多であった。`quick-save`（保存）と `/ship`（コミット）の分離は意図を明確にする。
4. **focus.md は実態として未使用**: 影式ではポモドーロ機能を使用していないため、廃止しても影響なし。
5. **段階的廃止は移行コストを増やす**: 二重管理期間を設けるメリットが乏しい。

**影式固有の確認事項**:
- CLAUDE.md の「セーブ/ロードの使い分け」セクションを更新し、廃止コマンドへの言及を削除すること（PM 級変更のため承認後に実施）

---

## 判断2: quick-save / quick-load の拡張

### 背景

v4.4.1 の `quick-save.md` は 3 ステップに拡張され、`daily.md` と `full-load.md` の機能を吸収する。

#### quick-save の変更内容

| Step | 現行 | v4.4.1 |
|------|------|--------|
| Step 1 | SESSION_STATE.md 記録 | SESSION_STATE.md 記録（同一） |
| Step 2 | なし | **新規**: ループログ保存（`.claude/logs/loop-*.txt` が存在する場合） |
| Step 3 | なし | **新規**: Daily 記録（`docs/daily/YYYY-MM-DD.md`）+ KPI 集計 |
| 完了報告 | 簡易 | `/ship` 案内 + Daily ファイルパス表示に拡張 |

#### quick-load の変更内容

| Step | 現行 | v4.4.1 |
|------|------|--------|
| Step 1 | SESSION_STATE.md を読んで 1 行報告 | SESSION_STATE.md 読み込み + フォールバック追加 |
| Step 2 | なし | **新規**: 次ステップに必要なドキュメントを特定（読み込みはまだ行わない） |
| Step 3 | 1 行報告形式 | 構造化復帰サマリー（前回日付/Phase/完了要約/未完了/次ステップ/参照予定ファイル） |
| Step 4 | ユーザー指示待ち | ユーザー指示待ち（同一） |

#### 新規依存ファイル

v4.4.1 版の quick-save が参照する未作成ファイル:

| 参照先 | 説明 | 状態 |
|--------|------|------|
| `docs/daily/YYYY-MM-DD.md` | 日次記録ファイル格納ディレクトリ | 未作成（ディレクトリ） |
| `docs/specs/loop-log-schema.md` | ループログスキーマ定義 | 未作成 |
| `docs/specs/evaluation-kpi.md` | KPI 定義（K1〜K5 計算式含む） | 未作成（`docs/specs/lam/evaluation-kpi.md` は存在する可能性があるが別ファイル） |

### 選択肢

#### 選択肢 A: v4.4.1 版で完全置き換え

両コマンドを v4.4.1 版で置き換える。新規依存ファイルは移行作業の一部として事前作成する。

**メリット**:
- LAM テンプレートとの完全な整合性
- quick-save が「セッション終了の一撃コマンド」として完成する
- quick-load の構造化サマリーは復帰時の情報量が現行より多く実用的

**デメリット**:
- 新規依存ファイル（`docs/daily/`, `docs/specs/loop-log-schema.md`, `docs/specs/evaluation-kpi.md`）の事前作成が必要

#### 選択肢 B: quick-save のみ v4.4.1 版へ置き換え（quick-load は現行維持）

quick-save を拡張し、quick-load は現行の簡易版を維持する。

**メリット**:
- quick-load の変更リスクを抑えられる

**デメリット**:
- quick-load の現行版（1 行報告形式）は情報量が乏しく、v4.4.1 版の方が実用性が高い
- 中途半端な移行状態になる

#### 選択肢 C: 両コマンドとも現行維持

v4.4.1 の変更を採用せず現行版を維持する。

**デメリット**:
- `daily.md` 廃止（判断1）との整合が取れない。daily 機能が消える

### 推奨案: 選択肢 A（v4.4.1 版で完全置き換え）

**根拠**:

1. **quick-load の改善は実用的**: 現行の 1 行報告形式は復帰時に次のステップが不明確になりやすい。v4.4.1 の構造化サマリーは参照予定ファイルまで明示するため、先読み読み込みを防ぎつつ情報量が増える。
2. **新規依存ファイルの作成は Phase 2b の作業スコープ内**: `docs/daily/`、`docs/specs/loop-log-schema.md`、`docs/specs/evaluation-kpi.md` の作成は他の設計変更と同時並行で対応できる。
3. **`daily.md` 廃止（判断1）との整合**: `daily.md` を廃止するならば、quick-save Step 3 に daily 機能が入っていなければ KPI 集計が消えてしまう。

**影式固有の確認事項**:
- `docs/specs/evaluation-kpi.md` と `docs/specs/lam/evaluation-kpi.md` の関係を整理する。LAM フレームワーク仕様書を `docs/specs/lam/` に置く方針（v4.0.1 移行時の判断6）を継承し、影式では `docs/specs/lam/evaluation-kpi.md` を SSOT として扱う。quick-save からは `docs/specs/lam/evaluation-kpi.md` を参照するよう調整する。

---

## 判断3: full-review の大幅拡張

### 背景

v4.4.1 の `full-review.md` は v4.0.1 版からさらに大幅に詳細化されている。主要変更点:

| 変更領域 | v4.0.1 現行（影式） | v4.4.1 |
|---------|-------------------|--------|
| 引数 | なし（暗黙的に全体対象） | 必須（対象ファイル/ディレクトリを明示） |
| `lam-loop-state.json` スキーマ | 基本フィールドのみ | `pm_pending`, `tool_events` フィールドを追加 |
| Phase 2 レポート | 簡易（PG/SE/PM 分類 + 一覧表示） | `docs/artifacts/audit-reports/` への永続化（`YYYY-MM-DD-iterN.md`）、PM 級承認ゲートフロー詳細化 |
| Phase 3 PM 級処理 | 簡易（指摘のみ） | `pm_pending` フラグの set/clear bash スクリプトを明示 |
| Phase 4 Green State | 基本 5 条件（G1〜G5） | 「真の Green State」定義追加、フルスキャン発動スクリプト、状態ファイル更新手順 |
| `/auditing` との使い分け | なし | 手動段階的監査 vs ワンショット自動修正の使い分けガイド追加 |

#### 影式固有の保護対象

| 項目 | 現行の記述 | v4.4.1 での扱い | 方針 |
|------|-----------|----------------|------|
| `building-checklist.md` R-1〜R-11 参照 | Phase 1 の quality-auditor に記述あり | 汎用版では削除（building-checklist.md に分離済みの想定） | 影式版で保持 |
| `pytest tests/ -v --tb=short` | Phase 4 G1 検証コマンド | 汎用コマンドに変更（ツール非依存化） | 影式版で保持 |
| `ruff check src/ tests/` | Phase 4 G2 検証コマンド | 汎用コマンドに変更 | 影式版で保持 |

### 選択肢

#### 選択肢 A: v4.4.1 版をベースに影式固有参照を追加

v4.4.1 の full-review.md をベースとし、以下を上乗せする:
- Phase 1 の quality-auditor 呼び出しに `building-checklist.md` R-1〜R-11 参照を追加
- Phase 4 の G1/G2 検証コマンドを影式固有コマンド（pytest/ruff）に明示

**メリット**:
- 引数必須化、pm_pending フラグ、レポート永続化など新機能を完全取り込み
- 影式固有の品質基準（R-1〜R-11）を維持

**デメリット**:
- 影式固有部分の追加箇所が分散するため、将来 v4.5 移行時にマージが若干手間

#### 選択肢 B: 現行版をベースに v4.4.1 の差分を選択的に追加

現行の full-review.md を維持し、必要な要素だけを取り込む。

**デメリット**:
- 引数必須化や pm_pending フラグなど相互に連携している変更を部分的に取り込むのは難しく、整合性の維持が困難

### 推奨案: 選択肢 A（v4.4.1 ベース + 影式固有参照追加）

**根拠**:

1. **引数必須化は設計上の改善**: 明示的な対象指定により、意図せぬ全体スキャンを防ぐ。
2. **pm_pending フラグフローは重要**: PM 級 Issue の承認ゲートを明示的に管理することで、「承認なしに PM 級変更が実施される」リスクを排除できる。
3. **レポート永続化は追跡可能性の向上**: `docs/artifacts/audit-reports/YYYY-MM-DD-iterN.md` に記録することで、監査履歴が残る。これは影式プロジェクトの成長記録としても有用。
4. **影式固有の保護は追加で実現可能**: v4.4.1 ベースに対して影式固有の参照（R-1〜R-11、pytest/ruff コマンド）を追加する作業は局所的であり、整合性を維持しやすい。

**実装メモ**:
- Phase 1 の quality-auditor 呼び出しブロックに以下を追加: 「影式固有: `building-checklist.md` の R-1〜R-11 品質ルール適合性を確認する」
- Phase 4 G1 に「`pytest tests/ -v --tb=short`」、G2 に「`ruff check src/ tests/`」を明示
- `docs/artifacts/audit-reports/` ディレクトリを移行作業中に作成する

---

## 判断4: retro の Step 2.5 TDD パターン分析追加

### 背景

v4.4.1 の `retro.md` は Step 2.5（TDD パターン分析）が新設されている。
これは TDD 内省パイプライン v2 への移行に対応するもので、
v4.0.1 の「PostToolUse hook が自動検出（閾値 3 回）」から
「`/retro` 実行時に人間が分析（閾値 2 回）」へとパラダイムシフトしている。

| 項目 | v4.0.1 現行（影式） | v4.4.1 |
|------|-------------------|--------|
| 閾値 | 3 回 | 2 回 |
| 分析主体 | PostToolUse hook（自動） | `/retro` Step 2.5（人間主導） |
| データソース | `tool_response.exitCode` | `.claude/tdd-patterns.log`（直接読み込み）|
| ANALYZED マーカー | なし | 処理済みエントリに `ANALYZED` を追記 |
| Knowledge Layer 出力 | なし | `docs/artifacts/knowledge/` への知見蓄積 |

その他の変更:

| 項目 | 現行 | v4.4.1 |
|------|------|--------|
| Step 4 アクション反映先 | `docs/xxx` | `docs/artifacts/knowledge/xxx.md` 追加 |
| Step 5 出力先 | `docs/memos/retro-wave-{N}.md` | `docs/artifacts/retro-wave-{N}.md` |
| permission-level 記述 | ボディ内 `# permission-level: PM` | 削除（v4.4.1 にはなし） |

### 選択肢

#### 選択肢 A: v4.4.1 版を採用（Step 2.5 追加 + 出力パス変更）

Step 2.5 を追加し、出力パスを `docs/artifacts/` に変更する。
permission-level の記述は影式固有として維持。

**メリット**:
- TDD 内省の分析が人間主導になり、誤検出のリスクが低下
- ANALYZED マーカーにより、処理済みパターンの追跡が可能
- Knowledge Layer への知見蓄積で、プロジェクト固有の知識が蓄積される

**デメリット**:
- Step 2.5 の実行には `.claude/tdd-patterns.log` に十分なデータが蓄積されている必要がある
- 波 (Wave) 完了ごとの `/retro` 実行負荷が若干増加する

#### 選択肢 B: 出力パス変更のみ（Step 2.5 は未採用）

出力パスの変更（`docs/memos/` → `docs/artifacts/`）のみ実施し、Step 2.5 は導入しない。

**デメリット**:
- TDD 内省パイプライン v2 の恩恵を受けられない
- `pattern-review.md` の変更（閾値 2 回、JUnit XML 参照）との整合が取れない

### 推奨案: 選択肢 A（v4.4.1 版を採用）

**根拠**:

1. **人間主導の分析は品質が高い**: 自動検出では文脈を考慮できないが、`/retro` での人間主導分析はパターンの妥当性を判断しながら進められる。
2. **閾値 2 回への引き下げは適切**: 3 回では「気づき」が遅すぎる場合があった。Wave 1〜2 程度のデータでもパターン候補を抽出できるようになる。
3. **Knowledge Layer は長期的資産**: `docs/artifacts/knowledge/` への知見蓄積は、将来のセッションでの参照資産になる。影式プロジェクトの「記憶を引き継ぐ」コンセプトとも整合する。
4. **出力パス変更は全コマンド横断的**: retro だけでなく、auditing.md の出力先変更とも合わせて `docs/artifacts/` に統一する。

**影式固有の保護事項**:
- `permission-level: PM` の記述はボディ内に維持する。retro.md は振り返りの結論がルール・プロセスに影響するため、PM 級の明示は重要である。v4.4.1 が削除しているのは汎用テンプレートの都合であり、影式では維持する。

---

## 判断5: ship の Phase 構成変更（7 → 5 Phase）

### 背景

v4.4.1 の `ship.md` は Phase 構成が 7 Phase から 5 Phase に簡略化されている。
主要な変更点:

| 変更点 | 現行（影式） | v4.4.1 |
|--------|------------|--------|
| Phase 2 Doc Sync | 影式従来フロー（CHANGELOG/README/README_en/CHEATSHEET の固定チェック）+ doc-sync-flag 分岐 | doc-sync-flag ファーストフロー（doc-writer エージェント呼び出し） |
| Phase 3〜4 | 論理グループ分け（3）+ コミット計画（4）を独立 Phase | 統合（新 Phase 3 = 旧 Phase 3 + 旧 Phase 4） |
| Phase 6 手動作業通知 | 独立 Phase | Phase 5 の後セクションに格下げ |
| Phase 7 完了報告 | あり（詳細） | 廃止（Phase 5 の手動作業通知で終了） |
| 引数 | `/ship dry-run` | `dry-run`（任意引数）に変更 |
| Phase 1 秘密情報パターン | 基本セット | 拡充（`secret`, `token`, `password` 追加） |

#### 影式固有の保護対象

| 項目 | 理由 |
|------|------|
| README_en.md チェック | 英語版 README は影式固有ドキュメント。汎用テンプレートには存在しない |
| CHEATSHEET.md チェック | 影式固有のクイックリファレンス。汎用テンプレートには存在しない |
| Phase 7 完了報告 | 影式ではコミット数/スキップ数/手動削除候補数/ユーザー作業数の集計が有用 |

### 選択肢

#### 選択肢 A: v4.4.1 ベース + 影式固有ドキュメントチェック維持

v4.4.1 の 5 Phase 構成を採用しつつ、以下を維持:
- Phase 2 の doc-sync-flag ファーストフローを採用
- ただし `doc-sync-flag` 未存在時のフォールバックとして README_en.md / CHEATSHEET.md のチェックを保持
- 完了報告は v4.4.1 の簡略版に統一（Phase 7 廃止）

**メリット**:
- doc-writer エージェント呼び出しにより、ドキュメント同期の品質が向上
- Phase 数削減により、コマンドが簡潔になる
- 秘密情報パターン拡充によりセキュリティが向上

**デメリット**:
- 完了報告の詳細集計（コミット数等）が省略される

#### 選択肢 B: 現行の 7 Phase 構成を維持しつつ doc-sync-flag 対応を追加

現行のフォールバック付き設計（v4.0.1 移行時の判断3・選択肢C）をそのまま維持し、
v4.4.1 で変更された部分のみ取り込む。

**メリット**:
- 完了報告の詳細集計が維持される

**デメリット**:
- Phase 構成が v4.4.1 と乖離したまま残り、将来の移行で再度変更が必要
- Phase 3+4 の統合はシンプル化であり、デメリットがない

### 推奨案: 選択肢 A（v4.4.1 ベース + 影式固有ドキュメントチェック維持）

**根拠**:

1. **Phase 3+4 の統合は改善**: 「グループ分け」と「コミット計画」は実質的に連続する作業であり、独立 Phase に分ける必然性がない。統合することで操作フローが簡潔になる。
2. **doc-sync-flag ファーストフローの採用**: doc-writer エージェントへの委任は、ドキュメント更新の品質一貫性を高める。影式固有ドキュメント（README_en.md, CHEATSHEET.md）はフォールバックパスで対応。
3. **完了報告の簡略化は許容**: コミット数等の集計は `git log --oneline -N` の出力で代替できる。専用の Phase 7 がなくても情報は得られる。
4. **秘密情報パターン拡充は即時採用**: セキュリティ向上の変更であり、採用しない理由がない。

**実装メモ**:
- Phase 2 の構成:
  - doc-sync-flag が存在する場合 → doc-writer エージェント呼び出し（v4.4.1 フロー）
  - doc-sync-flag が存在しない場合 → README_en.md / CHEATSHEET.md / CHANGELOG の固定チェック（影式従来フロー）
- 完了報告は Phase 5 後の手動作業通知セクションに統合し、`git log --oneline -N` で確認を案内

---

## 判断6: ultimate-think 廃止と lam-orchestrate への統合

### 背景

v4.4.1 で `ultimate-think` スキルが廃止され、その機能が `lam-orchestrate` の「構造化思考」セクションに統合された。

| 変更点 | 詳細 |
|--------|------|
| ultimate-think の機能 | AoT + Three Agents + Reflection を統合した構造化思考 |
| 吸収先 | `lam-orchestrate/SKILL.md` の「構造化思考」セクション |
| anchor-format.md の移動 | `ultimate-think/references/` → `lam-orchestrate/references/` |
| lam-orchestrate Subagent 選択テーブル | 5 行 → 9 行に拡充（quality-auditor, requirement-analyst, design-architect, task-decomposer を追加） |
| ループ統合スキーマ | `lam-loop-state.json` の定義を full-review に SSOT 委譲 |
| hooks 連携テーブル | 3 hook の参照タイミング・データフローを詳述 |
| エスカレーション条件 | 3 条件 → 6 条件に拡充 |

### 選択肢

#### 選択肢 A: 廃止 + lam-orchestrate に統合（LAM v4.4.1 準拠）

ultimate-think を削除し、lam-orchestrate に構造化思考セクションを追加する。
anchor-format.md も `lam-orchestrate/references/` に移動する。

**メリット**:
- LAM テンプレートとの完全な整合性
- lam-orchestrate が「オーケストレーション + 構造化思考」の一元的なエントリポイントになる
- Subagent 選択テーブルの 9 行拡充により、どのエージェントに委任すべきかが明確になる

**デメリット**:
- ultimate-think を個別に呼び出していた場合のリファレンスが変わる（`/ultimate-think` → lam-orchestrate 経由）

#### 選択肢 B: ultimate-think を影式固有スキルとして維持

ultimate-think を廃止せず、lam-orchestrate にも統合しない。

**デメリット**:
- LAM テンプレートとの乖離が増大
- lam-orchestrate の Subagent 選択テーブル拡充（9 行）を取り込めない
- anchor-format.md の二重管理になる

### 推奨案: 選択肢 A（廃止 + lam-orchestrate に統合）

**根拠**:

1. **lam-orchestrate への統合は設計上合理的**: 構造化思考（AoT + Three Agents）はオーケストレーションの一部であり、独立スキルよりもオーケストレータに内包する方が概念的に整合する。
2. **Subagent 選択テーブルの 9 行拡充は即時価値がある**: quality-auditor、requirement-analyst、design-architect、task-decomposer の追加により、委任判断の精度が向上する。影式プロジェクトでは全エージェントが定義されているため、この拡充は直接的に有効。
3. **anchor-format.md の移動は機械的な作業**: ファイルの移動と参照先更新のみ。内容変更なし。
4. **ultimate-think は影式での個別呼び出し実績が少ない**: 実際には lam-orchestrate 経由で暗黙的に利用されていた機能であり、廃止しても利用者への影響は限定的。

**実装メモ**:
- `ultimate-think/` ディレクトリを削除
- `lam-orchestrate/references/` ディレクトリを作成し、`anchor-format.md` をコピー（移動）
- lam-orchestrate/SKILL.md に「構造化思考」セクションを追加（v4.4.1 の内容をベースに影式固有の注記を追加する場合は最小限に留める）

---

## 判断7: エージェント更新方針

### 背景

v4.4.1 では全 8 エージェントに permission-level のフロントマター化が適用されている。
加えて、一部エージェントで model / permission-level の変更がある。

#### 変更一覧

| エージェント | permission-level 位置変更 | model 変更 | permission-level 等級変更 |
|------------|-------------------------|-----------|--------------------------|
| code-reviewer | ボディ → フロントマター | なし | なし（SE 維持） |
| quality-auditor | ボディ → フロントマター | opus → **sonnet** | なし（SE 維持） |
| doc-writer | ボディ → フロントマター | なし | なし（SE 維持） |
| design-architect | ボディ → フロントマター | なし | **PM → SE** |
| requirement-analyst | なし → フロントマター追加 | なし | PM（新規明示） |
| task-decomposer | なし → フロントマター追加 | なし | SE（新規明示）+ model コメント追加 |
| tdd-developer | なし → フロントマター追加 | なし | SE（新規明示） |
| test-runner | なし → フロントマター追加 | sonnet → **haiku** | PG（新規明示）|

#### code-reviewer の変更

- F 評価の追加（A/B/C/D → A/B/C/D/F）
- 出力形式の変更（Issue の `[PG/SE/PM]` 位置が末尾 → 先頭）

#### quality-auditor の変更

- model: opus → sonnet（コスト最適化）
- Step 3 タイトル変更（仕様ドリフトチェックと構造整合性チェックを統合）
- ドリフト種別が 3 種 → 4 種（「Phase/Wave 未到達」を追加）
- R-1〜R-11 品質ルール適合性チェック（影式固有）が削除

### 選択肢の評価

#### A: フロントマター化は全採用、model/permission は影式判断を優先

全 8 エージェントのフロントマター化を実施しつつ、以下の影式固有判断を適用:

- **quality-auditor**: model を **opus 維持**（v4.0.1 移行時の判断と継続）
- **design-architect**: permission-level を **PM 維持**（設計判断の重要性）
- **quality-auditor Step 3b**: R-1〜R-11 品質ルール適合性チェックを **維持**
- **test-runner**: model を **haiku に変更**（v4.0.1 移行時の判断と継続）
- **code-reviewer**: F 評価追加を **採用**

**メリット**:
- フロントマター化は構造的な改善であり全採用が望ましい
- 影式固有の品質判断（opus 維持、PM 維持）を継続できる

**デメリット**:
- LAM テンプレートとの model/permission の乖離が続く

#### B: LAM v4.4.1 に完全準拠

全変更を LAM テンプレート通りに採用。quality-auditor を sonnet に、design-architect を SE に変更。

**デメリット**:
- quality-auditor の sonnet 化により、深い仕様ドリフト検出・アーキテクチャ判断の品質低下リスク
- design-architect の SE 化により、設計判断の PM 承認ゲートが機能しなくなる

### 推奨案: 選択肢 A（フロントマター化は全採用、model/permission は影式判断を優先）

**根拠**:

#### quality-auditor: opus 維持の理由

v4.0.1 移行時（01-design-commands-agents.md 判断1）と同じ判断を継続する。
影式プロジェクトは Phase 1 の opus による監査から R-2〜R-11 を導出した実績がある。
v4.4.1 で quality-auditor に追加された「ドリフト種別 4 種」や「スキーマ整合性チェック 5 観点」は
高い推論能力を必要とする。LAM が sonnet 化している理由はコスト最適化であり、
影式では品質を優先する。

#### design-architect: PM 維持の理由

LAM が SE に降格している理由は「PLANNING フェーズでの委任を推奨」という説明であり、
等級降格の根拠としては弱い。影式では設計判断（データモデル、API 設計、コンポーネント分割）は
アーキテクチャ変更に相当し、PM 級承認ゲートが必要である。
design-architect を SE にすることで、設計変更が承認なしに実施されるリスクがある。

#### test-runner: haiku 採用の理由

v4.0.1 移行時の判断と同一。テスト実行・カバレッジ集計は定型作業であり haiku で十分。
コスト削減と速度向上のメリットが大きい。

#### code-reviewer: F 評価追加の理由

「致命的な品質問題を持つコード」に対して F 評価が付けられるようになることは、
評価の精度向上であり、採用しない理由がない。

#### ui-design-guide スキル: 影式（tkinter）での適用性

v4.4.1 で新設されたスキル。Web 固有項目（レスポンシブ設計、LCP/CLS、バンドルサイズ）は
tkinter には直接適用できないが、以下は有用:
- 状態設計（Empty, Loading, Error, Success, Partial）
- アクセシビリティの設計原則

**判断**: v4.0.1 移行時の判断5-3と同様に、**影式固有にカスタマイズして導入するが優先度は低い**。
Phase 2b のスコープとして位置づけるが、GUI 機能の拡張時に必要になった時点で整備する。
Web 固有のチェック項目を除外し、tkinter 固有項目（ウィジェット配置、イベントバインド、
スクロール実装、ダイアログ設計）に置き換えたバージョンを作成する。

**実装メモ（全エージェント）**:
- フロントマター内への `# permission-level: XX` 移動は全 8 エージェントに適用
- quality-auditor: Step 3b（R-1〜R-11 品質ルール適合性チェック）を維持し、影式固有セクションとして明示する
- task-decomposer: v4.4.1 の model コメント「コスト最適化のため意図的に Haiku を採用」を追加
- requirement-analyst: permission-level: PM をフロントマターに追加

---

## リスクと対策

### R1: 新規依存ファイルが未作成のまま本番運用される

**リスク**: `docs/daily/`, `docs/specs/loop-log-schema.md`, `docs/specs/evaluation-kpi.md`,
`docs/artifacts/audit-reports/`, `docs/artifacts/knowledge/`,
`lam-orchestrate/references/anchor-format.md` が未作成の状態で
対応するコマンドを実行するとエラーまたは混乱が生じる。

**対策**: 移行作業のタスクリストに「新規ディレクトリ・ファイルの事前作成」を最初のフェーズとして組み込む。
具体的には:
- `docs/daily/` ディレクトリ作成（空の `.gitkeep` を配置）
- `docs/artifacts/audit-reports/`, `docs/artifacts/knowledge/` ディレクトリ作成
- `docs/specs/loop-log-schema.md` は `docs/specs/lam/loop-log-schema.md` へのシムリンク的な参照整理
- `lam-orchestrate/references/` ディレクトリ作成と `anchor-format.md` の移動

### R2: CLAUDE.md の廃止コマンド参照が残存する

**リスク**: CLAUDE.md の「セーブ/ロードの使い分け」セクションが廃止コマンド（`full-save`, `full-load`）を
参照したままになる。

**対策**: コマンド廃止後、CLAUDE.md の更新を PM 級変更として承認ゲートを通す。
参照内容を `quick-save`/`quick-load`/`/ship` に更新する。

### R3: TDD 内省パイプライン v2 への移行で既存パターンログが処理不能になる

**リスク**: 閾値が 3 回 → 2 回に変わることで、既存の `.claude/tdd-patterns.log` 内の
「2 回観測済み・ANALYZED 未付与」のエントリが次の `/retro` で全て候補として検出される。

**対策**: `/retro` での Step 2.5 実施前に、既存ログを一度レビューして
古い・無効なエントリに手動で `ANALYZED` を付与しておく。

### R4: quality-auditor の opus 維持によるコスト増

**リスク**: LAM テンプレートが sonnet に変更した理由（コスト最適化）を無視しているため、
長期的なランニングコストが増加する。

**対策**: 現時点では影式プロジェクトの規模（Medium Scale）において、
full-review での quality-auditor 呼び出し頻度は月数回程度であり、
コスト増は許容範囲内と判断。将来プロジェクト規模が拡大した場合に改めて再評価する。

---

## 影式固有の総括

### 維持すべき影式固有要素

| 要素 | 場所 | 理由 |
|------|------|------|
| R-1〜R-11 品質ルール適合性チェック | quality-auditor Step 3b, full-review Phase 1 | 影式 Phase 1 Retro から導出された実績ある品質基準 |
| `pytest tests/ -v --tb=short` | full-review Phase 4 G1 | 影式の Python/pytest 環境固有 |
| `ruff check src/ tests/` | full-review Phase 4 G2 | 影式の Python/ruff 環境固有 |
| README_en.md チェック | ship.md Phase 2 フォールバック | 影式固有ドキュメント |
| CHEATSHEET.md チェック | ship.md Phase 2 フォールバック | 影式固有ドキュメント |
| quality-auditor model: opus | quality-auditor.md | 品質優先判断 |
| design-architect permission-level: PM | design-architect.md | 設計判断の重要性 |
| retro.md permission-level: PM | retro.md ボディ | 振り返りの結論がルール・プロセスに影響 |

### LAM v4.4.1 変更のうち影式が積極採用すべきもの

| 変更 | 採用コマンド/スキル/エージェント | 採用理由 |
|------|--------------------------------|---------|
| quick-save Step 2〜3（ループログ + daily 記録）| quick-save.md | daily.md 廃止の吸収先として必須 |
| quick-load 4 ステップ化 | quick-load.md | 復帰時の情報量向上 |
| full-review 引数必須化 | full-review.md | 意図しない全体スキャンの防止 |
| full-review pm_pending フラグフロー | full-review.md | PM 級承認ゲートの明示的管理 |
| full-review レポート永続化 | full-review.md | 監査履歴の追跡可能性向上 |
| retro Step 2.5 TDD パターン分析 | retro.md | TDD 内省 v2 への移行 |
| retro/auditing 出力パス変更（docs/artifacts/）| retro.md, auditing.md | 成果物の一元管理 |
| ship doc-sync-flag ファーストフロー | ship.md | doc-writer 活用 |
| ship Phase 3+4 統合 | ship.md | フロー簡素化 |
| lam-orchestrate 構造化思考セクション | lam-orchestrate/SKILL.md | ultimate-think 廃止の吸収 |
| lam-orchestrate Subagent テーブル 9 行拡充 | lam-orchestrate/SKILL.md | 委任判断の精度向上 |
| code-reviewer F 評価追加 | code-reviewer.md | 評価精度向上 |
| 全エージェント permission-level フロントマター化 | 全 8 エージェント | 構造的整合性 |
| test-runner model: haiku | test-runner.md | コスト削減（v4.0.1 判断の継続） |

---

## まとめ: 推奨案一覧

| 判断 | 推奨案 | 作業規模 |
|------|--------|---------|
| 1. 7コマンド廃止 | 全廃止（吸収先が十分カバー） | 小（ファイル削除 + 影式 CLAUDE.md 更新） |
| 2. quick-save/load 拡張 | v4.4.1 版で完全置き換え | 中（新規依存ファイル作成含む） |
| 3. full-review 大幅拡張 | v4.4.1 ベース + 影式固有参照追加 | 大（コマンド全面更新） |
| 4. retro Step 2.5 追加 | v4.4.1 版採用 + permission-level PM 維持 | 小〜中 |
| 5. ship Phase 構成変更 | v4.4.1 ベース + 影式固有ドキュメントチェック維持 | 中 |
| 6. ultimate-think 廃止 | 廃止 + lam-orchestrate に統合 | 中（anchor-format.md 移動含む） |
| 7. エージェント更新 | フロントマター化は全採用、model/permission は影式判断を優先 | 小〜中（全 8 エージェント） |

### Phase 2b 作業の推奨順序

1. 新規ディレクトリ・ファイルの事前作成（リスク R1 対策）
2. 全エージェントの permission-level フロントマター化（判断7・基盤整備）
3. 廃止コマンド 7 件の削除（判断1）
4. quick-save / quick-load の v4.4.1 版置き換え（判断2）
5. full-review の大幅拡張（判断3・最大変更）
6. retro, ship, auditing, building, planning の差分適用（判断4, 5）
7. ultimate-think 廃止 + lam-orchestrate 統合（判断6）
8. code-reviewer / quality-auditor の差分適用（判断7の残余）
9. CLAUDE.md の廃止コマンド参照更新（PM 級承認後）
