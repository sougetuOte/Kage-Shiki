# ADR-0001: LAM v4.0.0 免疫系アーキテクチャの導入

## メタ情報

| 項目 | 内容 |
|------|------|
| ステータス | Accepted |
| 決定日 | 2026-03-10 |
| 決定者 | Living Architect + ユーザー |
| 関連仕様 | `docs/specs/lam/v4.0.0-immune-system-requirements.md` |
| 関連設計 | `docs/specs/lam/v4.0.0-immune-system-design.md` |

## コンテキスト

LAM v3.x では品質管理がセッション単位の手動レビューに依存しており、以下の課題があった:

- `/full-review` が単発実行で収束保証がない
- 変更の権限レベルが未分類で、自動修正と要承認の境界が曖昧
- テスト失敗パターンの学習が行われず、同一ミスが再発

プロジェクトの規模拡大に伴い、品質を自動的に維持・回復する仕組みが必要となった。

## 決定

LAM v4.0.0 で **免疫系アーキテクチャ** を導入する。3 つのフィードバックループで構成:

1. **Loop 1: リアルタイム防御** — PreToolUse hook による PG/SE/PM 権限等級分類
2. **Loop 2: バッチ検証** — `/full-review` の自動ループ（Green State 5条件）
3. **Loop 3: 学習** — TDD 内省パイプラインによるルール自動生成

### 付随する決定

- `docs/specs/lam/` サブディレクトリの新設: LAM 仕様書が 7 ファイルに及ぶため、`00_PROJECT_STRUCTURE.md` の「巨大になる場合はディレクトリを切る」規則に基づきサブディレクトリ化
- `disable-model-invocation` / `allowed-tools` frontmatter の削除: LAM v4.0.0 では Subagent の権限を `permission-level` コメントで管理する方式に統一。Claude Code の frontmatter 制約は Layer 1（settings.json）で管理するため、SKILL.md レベルでの重複制約を廃止

## 3 Agents 評価

### [Affirmative]
- 手動レビューの負荷を大幅に削減
- 段階的導入設計（hooks 未導入でもフォールバック動作）で移行リスクが低い
- Green State 5条件による定量的な品質判定

### [Critical]
- hooks 導入前は Loop 1/2 が手動フォールバックのため効果が限定的
- 自動ループの最大 5 イテレーションでも収束しないケースへの対処が必要
- SSOT 3層の定義が `00_PROJECT_STRUCTURE.md` と新設計書で重複するリスク

### [Mediator]
段階的導入により移行リスクを最小化しつつ、hooks 導入後にフル機能が発揮される設計は妥当。SSOT 定義の重複は設計書から独自定義を削除し、`00_PROJECT_STRUCTURE.md` への参照に統一することで解消する。

## 影響

- `docs/internal/` は SSOT として最高権限を維持（変更なし）
- `.claude/rules/permission-levels.md` が権限等級の唯一の定義源
- `/full-review`, `/ship` 等の既存コマンドが免疫系フローに対応

## 参照

- `docs/specs/lam/v4.0.0-immune-system-requirements.md`
- `docs/specs/lam/v4.0.0-immune-system-design.md`
- `docs/specs/lam/green-state-definition.md`
- `docs/internal/00_PROJECT_STRUCTURE.md` — SSOT 3層アーキテクチャ
