# テスト結果ファイル出力ルール

## 概要

TDD 内省パイプライン v2 の基盤として、テスト実行結果を JUnit XML 形式で
`.claude/test-results.xml` に出力することを必須とする。

## ルール

### 必須: JUnit XML 出力設定

テストフレームワーク導入・変更時に、JUnit XML 出力設定を追加すること。

出力先: `.claude/test-results.xml`

### 必須: .gitignore への追加

`.claude/test-results.xml` を `.gitignore` に追加すること。
テスト結果ファイルはローカル実行の成果物であり、リポジトリに含めない。

## 言語別設定リファレンス

### Python (pytest)

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "--junitxml=.claude/test-results.xml"
```

### JavaScript/TypeScript (Jest)

```json
// package.json or jest.config.js
{
  "jest": {
    "reporters": [
      "default",
      ["jest-junit", { "outputDirectory": ".claude", "outputName": "test-results.xml" }]
    ]
  }
}
```

### JavaScript/TypeScript (Vitest)

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    reporters: ['default', 'junit'],
    outputFile: { junit: '.claude/test-results.xml' },
  },
});
```

### Go

```bash
go test ./... -v 2>&1 | go-junit-report > .claude/test-results.xml
```

### Rust

```bash
cargo test -- --format=junit > .claude/test-results.xml
```

## PostToolUse hook との連携

- PostToolUse hook がテスト実行後に `.claude/test-results.xml` を読み取る
- FAIL→PASS 遷移を検出し、`.claude/tdd-patterns.log` に記録する
- 結果ファイルが存在しない場合は WARNING ログ出力のみ（テスト動作に影響なし）

## 権限等級

- 本ルールファイル自体の変更: **PM級**
- テストフレームワークへの JUnit XML 出力設定追加: **PG級**
