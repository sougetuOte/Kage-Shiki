# タスク分解: Phase 4 — 統合検証 + 完了

**作成日**: 2026-03-10
**対象設計**: `000-index.md` Section 5, 6
**見積り**: 3 タスク
**前提**: Phase 1〜3 完了

---

## 依存関係

```
T4-1 (統合検証) → T4-2 (master マージ) → T4-3 (後処理)
```

---

## T4-1: 統合検証

**優先度**: 最高

### 作業内容

1. 全テスト実行: `pytest` — 全件 PASSED を確認
2. ruff check: `ruff check src/ tests/` — エラーゼロを確認
3. `/full-review` を新フォーマット（4 エージェント + PG/SE/PM）で実行
   - Green State G1〜G5 の判定結果を記録
   - 発見された Issue があれば修正
4. 移行結果レポートの作成:
   - Phase 1〜3 の変更サマリー
   - 新規ファイル一覧
   - 廃止ファイル一覧
   - テスト結果
   - 既知の制限事項

### 受入条件（= 成功基準 Section 6）

#### 機能的基準
- [ ] 全テスト PASSED（回帰なし）
- [ ] ruff check クリーン
- [ ] `/planning` → `/building` → `/auditing` のフェーズ切替が正常
- [ ] `/quick-save` → `/quick-load` のセッション管理が正常
- [ ] `/full-review` が新フォーマットで実行可能
- [ ] `/ship` が doc-sync-flag チェックを含む新フローで動作
- [ ] 影式固有コマンド (`/retro`, `/wave-plan`) が変更なく動作

#### 構造的基準
- [ ] 影式固有ルール (R-2〜R-11, S-2, L-4) が参照可能
- [ ] docs/internal/ の全ファイルが v4.0.1 内容を反映
- [ ] permission-levels.md が影式パス構造に合わせてカスタマイズ済み
- [ ] docs/specs/lam/ に LAM v4.0.0 仕様書が取り込まれている

#### 安全性基準
- [ ] hooks が Windows 環境でエラーなく動作
- [ ] settings.json の permissions が影式の運用と整合
- [ ] notify-sound.py が引き続き動作

#### 運用基準
- [ ] 移行後に影式 Phase 2a の作業を再開できること

---

## T4-2: master マージ + タグ

**優先度**: 最高
**依存**: T4-1 完了（全受入条件パス）

### 作業内容

1. lam-4.0.1-migration ブランチから master にマージ
2. `git tag post-lam-4.0.1` を作成
3. マージコミットメッセージ: `[LAM-4.0.1] 移行完了: v3.x → v4.0.1`

### 受入条件

- [ ] master ブランチにマージされている
- [ ] post-lam-4.0.1 タグが存在する
- [ ] マージ後も全テスト PASSED

---

## T4-3: 後処理（移行完了宣言）

**優先度**: 高
**依存**: T4-2

### 作業内容

1. `CLAUDE.md` から Active Migration Notice セクションを削除
2. `.claude/current-phase.md` から移行注記を削除
3. `SESSION_STATE.md` を最新化:
   - 「LAM 4.0.1 移行完了」を記載
   - 影式 Phase 2a の再開タスクを記載
   - スモークテスト再検証チェックリストへの参照を復元
4. 移行結果を `docs/memos/v4-update-plan/` に最終記録

### 受入条件

- [ ] CLAUDE.md から Active Migration Notice が削除されている
- [ ] current-phase.md から移行注記が削除されている
- [ ] SESSION_STATE.md が最新化されている
- [ ] 影式 Phase 2a の再開が可能な状態になっている

---

## Phase 4 完了後の次のステップ

移行完了後は以下の順序で影式の通常作業を再開する:

1. `docs/testing/retest-smoketest-2026-03-08.md` に従いスモークテスト再検証
2. Phase 2a 完了判定（全 20 項目パス後に宣言）
3. **新しい LAM 4.0.1 ルール下での慣らし運転**:
   - PG/SE/PM 分類が実作業で適切に機能するか確認
   - `/full-review` の新フォーマットが正常動作するか確認
   - hooks が作業フローを阻害しないか確認
   - 問題があれば `docs/memos/v4-update-plan/` に記録し、ルールを微調整
