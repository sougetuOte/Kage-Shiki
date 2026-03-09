# auto-generated/ — TDD 内省ルール

このディレクトリには TDD 内省パイプラインが自動生成したルール候補と承認済みルールを配置する。

## ライフサイクル

1. **PostToolUse hook** がテスト失敗→成功パターンを検出
2. `.claude/tdd-patterns.log` に記録（PG級、自動）
3. 同一パターンが **3回** に到達すると `draft-NNN.md` を自動生成
4. `/pattern-review` で PM級承認
5. 承認後 `rule-NNN.md` として配置

## ファイル命名

| パターン | 意味 |
|---------|------|
| `draft-NNN.md` | 承認待ちのルール候補 |
| `rule-NNN.md` | 承認済みの自動生成ルール |
| `trust-model.md` | 信頼度モデル定義 |

## ルール寿命管理

- 各ルールに `last_matched` 日付メタデータを付与
- **90日以上未使用**のルールは `/daily` で棚卸し通知
- 棚卸し対象は PM級承認で削除または更新

## 権限等級

- パターン記録（`.claude/tdd-patterns.log` への追記）: **PG級**
- ルール候補の生成・変更・削除: **PM級**
