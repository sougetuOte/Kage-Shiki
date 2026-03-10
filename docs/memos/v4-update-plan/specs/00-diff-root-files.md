# ルートディレクトリファイル差分分析

## 概要

LAM 4.0.1 テンプレートと影式現行のルートディレクトリファイルを比較分析した。
共通ファイル 4 種（CHANGELOG.md, README.md, README_en.md, LICENSE）と、
LAM 4.0.1 で新規追加された 4 ファイル（CLAUDE_en.md, CHEATSHEET_en.md, QUICKSTART.md, QUICKSTART_en.md）が対象。

**結論**: LICENSE は同一。CHANGELOG/README は影式固有の内容であり LAM テンプレートとは完全に異なる用途のため、フォーマットの取り込みのみ検討。新規ファイル 4 種は影式への導入優先度が低い。

---

## CHANGELOG.md 差分

### 性質の違い

| 項目 | 影式現行 | LAM 4.0.1 テンプレート |
|------|---------|----------------------|
| タイトル | `# Changelog — 影式 (Kage-Shiki)` | `# Changelog` |
| 内容 | 影式プロジェクト固有の開発履歴（Phase 1/2a の Wave 単位記録） | LAM フレームワーク自体のバージョン履歴（v1.2.1 ~ v4.0.1） |
| バージョニング | `[Unreleased]` のみ（セマンティックバージョン未採用） | `[vX.Y.Z] - YYYY-MM-DD` 形式（セマンティックバージョン） |

### フォーマット・構造の差分

| 要素 | 影式現行 | LAM 4.0.1 |
|------|---------|-----------|
| セクション分類 | Phase/Wave 単位の時系列 | `Added/Changed/Fixed/Removed/Migration Notes` の Keep a Changelog 準拠 |
| バージョンタグ | なし | `[vX.Y.Z] - YYYY-MM-DD` |
| Migration Notes | なし | v4.0.0, v3.3.0 に記載あり（破壊的変更の移行ガイド） |

### 移行時の考慮

- 影式の CHANGELOG は開発日記的な時系列記録。LAM テンプレートの Keep a Changelog 形式（Added/Changed/Fixed/Removed）への移行は**任意**。
- 現状のフォーマットは影式の開発スタイルに合っており、無理に変更する必要はない。
- もしセマンティックバージョニングを導入するなら、フォーマットを合わせる価値がある。

---

## README.md 差分

### 性質の違い

| 項目 | 影式現行 | LAM 4.0.1 テンプレート |
|------|---------|----------------------|
| タイトル | `# 影式 (Kage-Shiki)` | `# The Living Architect Model` |
| 目的 | 影式アプリの製品 README | LAM フレームワークのテンプレート README |
| 冒頭引用 | `"Not yet divine. Not yet free."` | `"AI は単なるツールではない。パートナーだ。"` |

### LAM 4.0.1 で追加・変更されたセクション

1. **「初めての方へ」テーブル**: スライド / クイックスタート / チートシート への 3 ステップ導線（影式には該当なし、影式は製品 README のため）
2. **「コアコンセプト」セクション**: Active Retrieval, Gatekeeper Role 等 8 項目の概念説明（影式には不要、LAM テンプレート用）
3. **「収録内容」セクション**: 憲法・チートシート、運用プロトコル、Claude Code 拡張のファイル一覧表（影式にはすでに「開発プロセス」セクションで同等の情報を記載済み）
4. **「使い方」セクション（Option A/B/C）**: テンプレート使用、git clone、既存プロジェクトへの導入の 3 パターン（影式には不要、製品リポジトリのため）
5. **「コマンドを覚える必要はありません」**: 初心者向けメッセージ。影式には未採用
6. **ワークフローコマンド / 補助コマンド**: `/ship`, `/full-review`, `/release`, `/focus`, `/daily` 等のテーブル（影式の README には未記載だが CHEATSHEET には記載済み）

### 影式固有で保持すべき内容

- 製品概要（主な特徴、技術スタック）
- Phase ロードマップ + Phase 2a 進捗
- 実装済みモジュール一覧
- 環境要件（Python 3.12+ 必須）

### 移行時の考慮

- 影式の README は製品ドキュメントであり、LAM テンプレートの README（フレームワーク説明用）とは根本的に異なる。**構造の移植は不要**。
- ただし、ワークフローコマンド（`/ship`, `/full-review`）や補助コマンドのテーブルが影式 README に欠けている点は、必要に応じて追加を検討。
- 「コマンドを覚える必要はありません」のメッセージは影式 README には不要（開発者自身が使うため）。

---

## README_en.md 差分

### 性質の違い

| 項目 | 影式現行 | LAM 4.0.1 テンプレート |
|------|---------|----------------------|
| 内容 | 影式 README.md の英語版 | LAM テンプレート README.md の英語版 |
| 構造 | README.md と同一構造 | README.md（日本語版テンプレート）と同一構造 |

### LAM 4.0.1 での変更

README.md（日本語版）の差分と同等。英語版固有の差分はない。具体的には:

1. **「Getting Started」テーブル**: スライドは `index-en.html`、チートシートは `CHEATSHEET_en.md`、クイックスタートは `QUICKSTART_en.md` を参照
2. **「Contents」セクション**: `CLAUDE.md` / `CLAUDE_en.md` と `CHEATSHEET.md` / `CHEATSHEET_en.md` の日英両方をリストアップ
3. **「You Don't Need to Memorize Commands」セクション**: 追加
4. **「Workflow Commands」「Utility Commands」セクション**: 追加

### 移行時の考慮

- README.md と同様、影式固有の製品 README であるため LAM テンプレートの構造移植は不要。
- 影式 README_en.md は README.md と完全に対応しているため、README.md に変更があれば同期更新のみ。

---

## LICENSE 差分

**完全に同一**。

```
MIT License
Copyright (c) 2025 The Living Architect Contributors
```

両ファイルとも同一の MIT License テキスト。**変更不要**。

---

## LAM 4.0.1 新規ファイル

### CLAUDE_en.md

**内容**: `CLAUDE.md` の完全英語版。

| セクション | 内容 |
|-----------|------|
| Identity | "You are the Living Architect and Gatekeeper..." |
| Hierarchy of Truth | User Intent > Architecture > Specs > Code |
| Core Principles | Zero-Regression, Active Retrieval |
| Execution Modes | /planning, /building, /auditing |
| References | CHEATSHEET_en.md, index-en.html を参照 |
| Context Management | 英語で同じルール |
| MEMORY.md Policy | 英語で同じポリシー |
| Initial Instruction | 英語で同じ指示 |

**影式への導入判断**: **不要**。

- 影式は日本語プロジェクトであり、CLAUDE.md は日本語で維持されている。
- CLAUDE.md は AI への指示文書であり、ユーザー向けドキュメントではない。英語版を別ファイルで持つ意味が薄い。
- LAM テンプレートとして配布する場合は日英両方が必要だが、影式は配布物ではない。

### CHEATSHEET_en.md

**内容**: CHEATSHEET.md の完全英語版。LAM 4.0.1 の新機能を含む。

LAM 4.0.1 で追加された内容（現行影式 CHEATSHEET.md にないもの）:

| 項目 | 内容 |
|------|------|
| Permission Levels (PG/SE/PM) セクション | v4.0.0 新機能の権限等級説明 |
| PreToolUse hook セクション | ファイルパスベースの自動分類 |
| Hook classification false-positive measurement | 誤分類率の計測方法 |
| AUDITING の制限変更 | 「修正の直接実施禁止」→「No PM-level fixes (PG/SE allowed)」 |
| `/daily` の説明変更 | 「日次振り返り」→「Daily retrospective (includes KPI aggregation)」 |
| `/impact-analysis` の説明変更 | 「変更の影響分析」→「Change impact analysis (includes PG/SE/PM classification)」 |
| hooks ディレクトリ | `.claude/hooks/` がディレクトリ構造に追加 |
| logs ディレクトリ | `.claude/logs/` がディレクトリ構造に追加 |

**影式への導入判断**: **不要**（英語版として）。ただし、**上記の v4.0.0 新機能に関する差分は日本語版 CHEATSHEET.md への反映が必要**。これは CHEATSHEET.md 本体の更新タスクとして扱う。

### QUICKSTART.md

**内容**: LAM テンプレートの初心者向け導入ガイド（日本語、5 分想定）。

構成:
1. 前提条件（Claude Code CLI, Git, GitHub アカウント）
2. Step 1: テンプレートからリポジトリ作成
3. Step 2: Claude Code 起動 → `/planning` で要件定義（v4.0.1 修正: `claude init` 不要を明記）
4. Step 3: プロジェクトに合わせて LAM を適応（適応すべき/そのままでよいファイルの分類表）
5. Step 4: 最初の BUILDING セッション
6. FAQ（5 問）
7. 次のステップ

**影式への導入判断**: **不要**。

- QUICKSTART.md は LAM テンプレートの導入手順であり、影式プロジェクト（すでに LAM 導入済み）には無関係。
- Step 3 の「適応すべきファイル / そのままでよいファイル」の分類は、今回の移行作業の参考にはなる。

### QUICKSTART_en.md

**内容**: QUICKSTART.md の完全英語版。

**影式への導入判断**: **不要**（QUICKSTART.md と同じ理由）。

---

## 移行時の注意事項

### 1. 変更不要なもの

| ファイル | 理由 |
|---------|------|
| LICENSE | 同一内容 |
| CHANGELOG.md | 影式固有の開発履歴。フォーマット変更は任意 |
| README.md | 影式の製品 README として独自に維持 |
| README_en.md | README.md の英語版として独自に維持 |

### 2. 導入不要な新規ファイル

| ファイル | 理由 |
|---------|------|
| CLAUDE_en.md | 日本語プロジェクトであり不要。AI 指示文書の英語版を持つ意味が薄い |
| CHEATSHEET_en.md | 日本語プロジェクトであり不要。ただし v4.0 新機能の差分は日本語版に反映すべき |
| QUICKSTART.md | LAM テンプレート導入ガイド。影式はすでに導入済みのため不要 |
| QUICKSTART_en.md | 同上 |

### 3. 間接的に影響するもの

| 対象 | 必要なアクション |
|------|----------------|
| CHEATSHEET.md（現行） | LAM 4.0.1 の v4.0 新機能（PG/SE/PM, hooks, logs 等）のセクションを反映する必要あり。これは `.claude/rules/` や hooks 移行と連動するため、そちらのタスクと統合 |
| README.md（現行） | LAM 4.0.1 テンプレートで追加されたワークフローコマンド表が影式 README に欠けているが、CHEATSHEET で網羅済みのため優先度低 |

### 4. QUICKSTART.md の移行参考情報

QUICKSTART.md Step 3 に記載の分類は、影式の v4.0.1 移行時の参考になる:

**適応すべきファイル**（影式ではすでにプロジェクト固有に書き換え済み）:
- `CLAUDE.md` — Identity セクション
- `README.md` / `README_en.md`
- `CHANGELOG.md`

**そのままでよいファイル**（LAM 汎用基盤として移行対象）:
- `.claude/rules/` — 汎用ルール
- `.claude/hooks/` — 免疫システム（**新規導入対象**）
- `.claude/commands/` — フェーズ制御・ワークフロー
- `.claude/agents/`, `skills/` — サブエージェント・スキル
- `docs/internal/` — プロセス SSOT
