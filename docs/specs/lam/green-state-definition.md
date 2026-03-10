# Green State 定義（影式版）

LAM v4.0.0 の Green State 5条件を影式プロジェクトに具体化したもの。
`/full-review` の Phase 4 で検証される収束条件。

## Green State 5条件

| ID | 条件 | 検証コマンド | 合格基準 |
|----|------|-------------|---------|
| G1 | テスト全パス | `pytest tests/ -v --tb=short` | 0 failed |
| G2 | lint エラーゼロ | `ruff check src/ tests/` | All checks passed |
| G3 | 対応可能 Issue ゼロ | Phase 3 修正後の残 PG/SE 級 Issue 確認 | PG/SE 級 Issue = 0 |
| G4 | 仕様差分ゼロ | `docs/specs/` と実装の突合（quality-auditor Step 3） | ドリフト検出 = 0 |
| G5 | セキュリティチェック通過 | code-reviewer #4（OWASP Top 10）の結果 | Critical/High = 0 |

## 判定ロジック

```
Green State = G1 AND G2 AND G3 AND G4 AND G5
```

- **全条件 AND**: 1つでも未達なら Green State 未達
- PM級 Issue は G3 の対象外（承認ゲートで別管理）

## 影式固有の補足

### G1: テスト全パス
- カバレッジ目標: 各モジュール 90% 以上（NFR）
- `pytest --cov=kage_shiki --cov-report=term-missing` で確認

### G3: 対応可能 Issue ゼロ
- PG級: 自動修正で解消
- SE級: 修正 + 報告で解消
- PM級: カウント対象外（指摘のみ、承認ゲートへ）

### G4: 仕様差分ゼロ
- 影式の仕様書は `docs/specs/phase1-mvp/`、`docs/specs/phase2a-foundation/` 等の Phase 別ディレクトリに格納
- building-checklist.md の R-1（仕様突合）と S-1（仕様同期）が基準

## 参照

- `docs/internal/03_QUALITY_STANDARDS.md` — Quality Gates
- `.claude/rules/building-checklist.md` — R-1〜R-11
- `.claude/rules/permission-levels.md` — PG/SE/PM 分類基準
