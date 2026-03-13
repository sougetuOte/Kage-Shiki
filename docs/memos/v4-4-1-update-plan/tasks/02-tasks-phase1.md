# Phase 1 タスク: セキュリティ修正 + settings.json

**ステータス**: Draft
**対象設計**:
- `01-design-hooks-settings.md` — 判断5: settings.json セキュリティ修正
**優先度**: 高（セキュリティリスク排除）

---

## タスク一覧

| # | タスク名 | 対象ファイル | 権限等級 | 依存 | 完了条件 |
|---|---------|-----------|---------|------|---------|
| P1-1 | `find` コマンドの破壊的パターンを deny に追加 | `.claude/settings.json` | PM 級 | なし | find の `-delete`, `-exec rm`, `-exec chmod`, `-exec chown` パターンが deny に追加され、JSON が有効化 |
| P1-2 | `find` を allow から ask に移動 | `.claude/settings.json` | PM 級 | P1-1 | find 通常検索が ask セクションに存在 |
| P1-3 | ~~`python *` を ask に追加~~ **スキップ** | `.claude/settings.json` | — | — | Python プロジェクトのため allow 維持（W-7 解消） |
| P1-4 | settings.json の動作確認 | （検証） | PG 級 | P1-1, P1-2, P1-3 | 形式エラーなし、ruff format でフォーマット統一 |

---

## 詳細

### P1-1: `find` コマンドの破壊的パターンを deny に追加

**概要**: LAM v4.4.1 のセキュリティ修正を適用。`find` の `-delete`, `-exec rm`, `-exec chmod`, `-exec chown` パターンを deny リストに追加し、不可逆操作を明確に禁止する。

**対応設計**: `01-design-hooks-settings.md` Section「判断5: settings.json セキュリティ修正」

**変更内容**:
```json
// .claude/settings.json の permissions.deny セクションに以下を追加
{
  "permissions": {
    "deny": [
      // ... 既存項目 ...
      "Bash(find * -delete *)",
      "Bash(find * -exec rm *)",
      "Bash(find * -exec chmod *)",
      "Bash(find * -exec chown *)"
    ]
  }
}
```

**影式固有の注意**:
- `notify-sound.py` は `hook_utils` を import しない単独スクリプト。本変更の影響を受けない。
- 破壊的パターンの明示化により、settings.json の意図が明確になる

**完了条件**:
- [ ] 4つの deny パターンが settings.json に追加されている
- [ ] JSON 形式は有効（括弧・カンマの対応が正確）
- [ ] 対応する `Bash(find *)` は ask に移動済み（P1-2 完了待ち）

---

### P1-2: `find` を allow から ask に移動

**概要**: LAM v4.4.1 に従い、`find` コマンドを allow リストから削除し、ask セクションに移動する。`find . -delete` 等の破壊的オプションと、`find . -name xxx` 等の通常検索を同一カテゴリとしないため。

**対応設計**: `01-design-hooks-settings.md` Section「判断5: settings.json セキュリティ修正」

**変更内容**:
```json
{
  "permissions": {
    "allow": [
      // ... find を削除 ...
      "Bash(ls *)",
      "Bash(cat *)",
      // "Bash(find *)" ← 削除
      "Bash(pwd)",
      // ...
    ],
    "ask": [
      // ... 既存項目 ...
      "Bash(find *)",     // 追加
      "Bash(python *)"    // 別タスク P1-3 で追加
    ]
  }
}
```

**影式固有の注意**:
- 影式は `find` の主な用途が ファイル検索（`find . -name`, `find . -type f` 等）であり、ask（承認必須）のままでも Glob/Grep で代替可能
- settings.local.json で既に allow にオーバーライドされている可能性があるため、実際の影響は小さい

**完了条件**:
- [ ] allow セクションから "Bash(find *)" が削除されている
- [ ] ask セクションに "Bash(find *)" が追加されている
- [ ] JSON 形式が有効

---

### P1-3: `python *` を ask に追加

**概要**: LAM v4.4.1 では削除された Python カテゴリを、影式固有として ask に追加する。Python スクリプト実行は意図的な操作であり、承認を求めることが適切。

**対応設計**: `01-design-hooks-settings.md` Section「判断5: settings.json セキュリティ修正」

**変更内容**:
```json
{
  "permissions": {
    "ask": [
      // ... 既存項目 ...
      "Bash(find *)",
      "Bash(python *)"    // 追加（影式固有）
    ]
  }
}
```

**影式固有の注意**:
- `settings.local.json` で既に allow にオーバーライドされていることが多いため、本変更の実際の影響は限定的
- 本変更は Layer 0（プロンプティング）での定義を明確化する意味があり、settings.local.json での上書きを想定している

**完了条件**:
- [ ] ask セクションに "Bash(python *)" が追加されている
- [ ] JSON 形式が有効

---

### P1-4: settings.json の動作確認

**概要**: settings.json の JSON 形式チェック、ruff format による統一確認を実施。

**対応設計**: N/A（検証タスク）

**検証内容**:

```bash
# 1. JSON 形式チェック
python -c "import json; json.load(open('.claude/settings.json'))" && echo "OK"

# 2. ruff format 実行（ファイル形式の統一はなし。JSON ファイルなので ruff 不適用）
# 代わりに jq で整形確認
jq . .claude/settings.json > /dev/null && echo "Valid JSON"
```

**完了条件**:
- [ ] JSON 形式エラーなし（python -c で確認）
- [ ] 4つの deny パターンが存在することを確認
- [ ] find が allow から削除、ask に移動していることを確認
- [ ] python * が ask に追加されていることを確認

---

## 依存関係図

```
P1-1 (deny パターン追加)
  ↓
P1-2 (find を ask に移動)
  ↓
P1-3 (python * を ask に追加)
  ↓
P1-4 (動作確認) ← 並列実行不可
```

---

## タスクサイズ評価

| タスク | サイズ | 理由 |
|--------|--------|------|
| P1-1 | S | JSON に4行追加（破壊的パターン）のみ |
| P1-2 | S | JSON の1エントリ削除と追加 |
| P1-3 | S | JSON に1行追加 |
| P1-4 | S | 形式チェックと確認のみ |
| **合計** | **S** | 設定ファイル変更のみで実装なし |

---

## 作業フロー

```
Phase 1: セキュリティ修正 + settings.json
  ├── P1-1: deny パターン追加
  ├── P1-2: find を ask に移動
  ├── P1-3: python を ask に追加
  └── P1-4: 動作確認 ✓ 完了

次 Phase: ルール + docs/internal/ + CLAUDE.md
```

---

## Notes

- **影式固有の保護項目**: `git status *`, `pip show *` は許可状態（allow）を維持
- **settings.local.json の影響**: ローカルオーバーライドが有効であれば、本変更の実際の影響は限定的
- **テストの必要性**: hooks 移動後、実際には settings.json が hook から参照されないため、機能テスト不要（設定ファイルのみ検証）
