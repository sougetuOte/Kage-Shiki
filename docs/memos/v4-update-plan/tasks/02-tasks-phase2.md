# タスク分解: Phase 2 — コマンド / スキル / エージェント

**作成日**: 2026-03-10
**対象設計**: `01-design-commands-agents.md`
**見積り**: 6 タスク
**前提**: Phase 1 完了

---

## 依存関係

```
T2-1 (エージェント更新) ──┐
                          ├── T2-3 (full-review.md)
T2-2 (他コマンド更新) ────┤
                          │
T2-3 ─── T2-4 (ship.md)  │
                          │
T2-5 (スキル更新) ────────┘  ← 独立
T2-6 (LAM 仕様書) ──────────  ← 独立
```

---

## T2-1: エージェント定義の更新

**設計参照**: `01-design-commands-agents.md` 判断1
**優先度**: 最高（full-review の前提）

### 作業内容

1. 全 8 エージェントに `# permission-level: PG/SE/PM` コメントを追加
2. `quality-auditor.md`:
   - model は `opus` のまま維持
   - Step 3 に仕様ドリフトチェックを追加
   - Step 3b に構造整合性チェックを追加
3. `test-runner.md`:
   - model を `haiku` に変更
   - 本文変更なし
4. `code-reviewer.md`:
   - PG/SE/PM 分類出力の追加
5. `doc-writer.md`:
   - ドキュメント自動追従モードの追加（doc-sync-flag 連携の記述）
6. 他 4 エージェント: frontmatter に permission-level コメントを追加

### 受入条件

- [ ] 全 8 エージェントに permission-level コメントがある
- [ ] quality-auditor が opus のまま + 仕様ドリフトチェックが追加されている
- [ ] test-runner の model が haiku になっている
- [ ] code-reviewer に PG/SE/PM 分類出力がある

---

## T2-2: コマンド更新（full-review / ship 以外）

**設計参照**: `01-design-commands-agents.md` 判断4
**優先度**: 高
**依存**: なし（独立作業）

### 作業内容

1. `auditing.md`: 権限等級修正ルール（PG/SE/PM）追加
2. `building.md`: TDD 内省パイプライン連携（影式 R-1〜R-6 参照は維持）
3. `daily.md`: KPI 集計セクション追加（K2, K3 は「hooks 導入後に計測開始」注記付き）
4. `project-status.md`: Wave 進捗 + KPI ダッシュボード統合版に再構築
5. `impact-analysis.md`: PG/SE/PM 分類ステップ追加
6. `security-review.md`: 権限等級対応表 + 自動化ツール連携
7. `retro.md`: frontmatter に description 追加 + 権限等級 PM 注記
8. `wave-plan.md`: frontmatter に description 追加 + 権限等級 SE 注記
9. その他（adr-create, focus, full-load/save, quick-load/save, planning）: 軽微な差分適用

### 受入条件

- [ ] auditing.md に PG/SE/PM 修正ルールがある
- [ ] project-status.md に Wave 進捗テーブルと KPI ダッシュボードの両方がある
- [ ] retro.md, wave-plan.md に frontmatter が追加されている
- [ ] 影式固有コマンド（retro, wave-plan）の本文が変更されていないこと

---

## T2-3: full-review.md の移行

**設計参照**: `01-design-commands-agents.md` 判断2
**優先度**: 最高（最大の変更）
**依存**: T2-1（エージェント構成確定後）

### 作業内容

1. LAM 4.0.1 版をベースに採用
2. 4 エージェント構成を定義:
   - #1 code-reviewer (src/) — コード品質
   - #2 code-reviewer (tests/) — テスト品質
   - #3 quality-auditor (全体) — アーキテクチャ + 仕様ドリフト + R-1〜R-6 適合
   - #4 code-reviewer (全体) — セキュリティ (OWASP Top 10)
3. Green State 5 条件（影式版: G1〜G5）を記載
4. 自動ループ制御: hooks 有無で分岐
   - hooks 導入済み → lam-stop-hook による自動ループ（最大 5 回）
   - hooks 未導入 → 修正報告 + ユーザーに再実行提案（手動ループ）
5. Phase 0/0.5（ループ初期化 + context7 MCP 検出）を記載
6. 差分チェック / フルスキャン切替を記載
7. 影式固有: building-checklist.md 参照、spec-sync ルール参照

### 受入条件

- [ ] 4 エージェント構成が定義されている
- [ ] Green State G1〜G5 が影式のツール名で記載されている
- [ ] 自動ループの手動フォールバック分岐が存在する
- [ ] building-checklist.md への参照がある

---

## T2-4: ship.md の doc-sync-flag 対応

**設計参照**: `01-design-commands-agents.md` 判断3
**優先度**: 中
**依存**: T2-3（full-review のフローと整合させるため）

### 作業内容

1. Phase 2（ドキュメント同期）に doc-sync-flag 分岐を追加:
   - doc-sync-flag 存在時 → LAM 4.0.1 フロー
   - doc-sync-flag 不存在時 → 影式従来フロー（CHANGELOG, README, README_en, CHEATSHEET の固定チェック）
2. Phase 構成: 7 段階を維持（現行 Phase 6 + 6.2 を統合）
3. 影式固有ドキュメント（README_en.md, CHEATSHEET.md）のチェックを維持

### 受入条件

- [ ] doc-sync-flag の有無で分岐する記述がある
- [ ] doc-sync-flag 不存在時に影式従来フローが実行される
- [ ] README_en.md のチェックが残っている

---

## T2-5: スキル更新

**設計参照**: `01-design-commands-agents.md` 判断5
**優先度**: 低（独立作業）
**依存**: なし

### 作業内容

1. 全スキルに `version: 1.0.0` を追加（adr-template, lam-orchestrate, skill-creator, spec-template, ultimate-think）
2. `lam-orchestrate`:
   - ループ統合セクション追加（lam-loop-state.json スキーマ、ライフサイクル、hooks 連携）
   - frontmatter の `disable-model-invocation`, `allowed-tools`, `argument-hint` 削除
3. `ultimate-think`:
   - `version: 1.0.0` 追加
   - `disable-model-invocation: true` 削除
   - `--no-web` 条件分岐の記述削除
4. `adr-template`: 出力ファイル名パターンを連番方式に更新（Phase 1 T1-6 の ADR 命名規則変更と整合）
5. `spec-template`: 権限等級セクション追加
6. **ui-design-guide**: スコープ外（Phase 2b 以降）

### 受入条件

- [ ] 全スキルに version: 1.0.0 がある
- [ ] lam-orchestrate にループ統合セクションがある
- [ ] ultimate-think の frontmatter が更新されている
- [ ] adr-template の出力ファイル名が連番方式になっている

---

## T2-6: LAM 仕様書の取り込み

**設計参照**: `01-design-commands-agents.md` 判断6
**優先度**: 低（独立作業）
**依存**: なし

### 作業内容

1. `docs/specs/lam/` ディレクトリを作成
2. LAM 4.0.1 の 7 仕様書をそのままコピー:
   - v4.0.0-immune-system-requirements.md
   - v4.0.0-immune-system-design.md
   - green-state-definition.md（影式版: G1〜G5 を具体化）
   - evaluation-kpi.md
   - loop-log-schema.md
   - doc-writer-spec.md
   - v3.9.0-improvement-adoption.md
3. `daily.md` の参照パスを `docs/specs/lam/evaluation-kpi.md` に変更
4. green-state-definition.md のみ影式版として具体化（判定コマンド、基準値を記入）

### 受入条件

- [ ] docs/specs/lam/ に 7 ファイルが配置されている
- [ ] green-state-definition.md に影式の G1〜G5 具体値がある
- [ ] daily.md の参照パスが更新されている

---

## Phase 2 検証チェックリスト

- [ ] `/auditing` で権限等級 (PG/SE/PM) の分類が出力されること
- [ ] `/building` で TDD サイクルの R-1〜R-6 参照が有効であること
- [ ] `/impact-analysis` で PG/SE/PM 分類ステップが表示されること
- [ ] `/daily` で KPI セクションの骨格が表示されること
- [ ] `/project-status` で Wave 進捗 + KPI の両方が出力されること
- [ ] `/ship` が doc-sync-flag の存在を確認するステップを含むこと
- [ ] 影式固有コマンド (`/retro`, `/wave-plan`) が変更なく動作すること

**コミット**: `[LAM-4.0.1] Phase 2: commands/skills/agents + specs`
