# D-2: ログ設計

**決定対象**: requirements.md Section 8 D-2「ログ設計 — Python logging, ログレベル, ローテーション」
**関連 FR**: FR-1.5（INFO以上をコンソール+ファイル出力）
**ステータス**: 提案（承認待ち）

---

## 1. コンテキスト

影式は Windows 常駐アプリケーションである。ユーザーは開発者ではない可能性が高く、問題発生時にログが唯一の診断手段となる。

要件の要点を整理する。

| 要件 | 内容 |
|------|------|
| FR-1.5 | INFO 以上のログをコンソールとファイルに出力する |
| NFR-4 | 常駐時メモリ使用量 < 100MB |
| NFR-9 | 正常・異常終了で observations を失わない（ログとは別だが、ログのローテーション中断によるデータ混在を防ぐ必要がある） |
| 長期運用 | 常駐アプリとして数ヶ月〜数年動作する。ログファイルが際限なく増大しない設計が必須 |

Python 標準ライブラリの `logging` モジュールを使用する（NFR-3: 外部依存最小化の制約から、loguru 等のサードパーティライブラリは採用しない）。

配置先（D-1 参照）: `src/kage_shiki/core/logging_setup.py`
ログファイル出力先: `data/kage_shiki.log`（config.toml の `data_dir` に従う）

---

## 2. 選択肢分析

### 選択肢 A: ログレベル — 2段階運用（INFO / DEBUG の切り替え）

コンソールとファイルの両方に同一レベルで出力する。通常運用は INFO、デバッグ時に DEBUG に切り替える。

```toml
[logging]
level = "INFO"        # "DEBUG" に変更でデバッグモード
```

- **概要**: ログレベルを一つの設定値で制御するシンプルな方式
- **メリット**: 理解しやすい。ユーザーが config.toml で `level = "DEBUG"` に変更するだけでデバッグ情報が得られる
- **デメリット**: 通常運用時にコンソールに DEBUG ログが出ない。ファイルにのみ詳細ログを残したい場合に対応できない

### 選択肢 B: ログレベル — コンソール/ファイル分離運用

コンソールとファイルで異なるログレベルを設定する。

```toml
[logging]
console_level = "INFO"    # コンソールは INFO 以上（ユーザーが見る）
file_level = "DEBUG"      # ファイルは DEBUG 以上（開発者診断用）
```

- **概要**: ハンドラーごとにレベルフィルタを設定する Python logging の標準的な活用方法
- **メリット**: 通常運用でコンソールは INFO のみ表示でユーザーが混乱しない。ファイルには DEBUG が常時記録されており、問題発生後でも詳細が追える。FR-1.5 の「INFO 以上をコンソール+ファイル出力」要件を自然に満たしつつ、ファイルは追加情報を持てる
- **デメリット**: 設定値が2つになりやや複雑。ただし Python logging の慣例の範囲内

### 選択肢 C: ローテーション — なし（シンプルファイル出力）

ローテーションを行わず、起動ごとに `kage_shiki.log` に追記し続ける。

- **概要**: `logging.FileHandler` を直接使用
- **メリット**: 実装が最もシンプル
- **デメリット**: 常駐アプリとして数ヶ月運用すると、ログが数百MB〜数GBになる可能性がある。NFR-4（メモリ100MB以下）とは直接の関係はないが、ディスク消費の観点で問題。ユーザーが手動削除するしか対処法がない

### 選択肢 D: ローテーション — サイズベース（RotatingFileHandler）

ファイルサイズが上限に達したら、古いファイルを `kage_shiki.log.1` として退避し、新しいファイルに書き込む。

```python
# 擬似コード（実装コードではない）
handler = RotatingFileHandler(
    log_path,
    maxBytes=5 * 1024 * 1024,  # 5MB
    backupCount=3,              # 最大 3 世代 = 合計最大 20MB
    encoding="utf-8"
)
```

- **概要**: `logging.handlers.RotatingFileHandler` を使用
- **メリット**: ディスク消費が上限（maxBytes × backupCount）に抑えられる。設定値がシンプル。Python 標準ライブラリで実装可能
- **デメリット**: ログが時系列でなくファイルをまたいで連続する場合の追跡がやや手間。ただし影式のログ解析は単純なテキスト検索で十分

### 選択肢 E: ローテーション — 日時ベース（TimedRotatingFileHandler）

日付が変わったタイミングでファイルをローテーションする。

```python
# 擬似コード
handler = TimedRotatingFileHandler(
    log_path,
    when="midnight",    # 深夜0時にローテーション
    interval=1,
    backupCount=7,      # 7日分を保持
    encoding="utf-8"
)
```

- **概要**: `logging.handlers.TimedRotatingFileHandler` を使用
- **メリット**: 「今日のログ」「昨日のログ」と日付単位で整理できる。日次サマリー（memory_worker）の運用と概念が一致する
- **デメリット**: 常駐アプリの場合、「深夜0時のローテーション」はプロセスが継続稼働中に発生する。この処理は Python logging が内部的に処理するが、Windows 環境でのファイルロックに注意が必要。また、1日のログ量が多いか少ないかわからない段階では保持日数の設定が難しい

---

## 3. Three Agents Perspective

**[Affirmative]**（推進者の視点）

コンソール/ファイル分離運用（選択肢 B）+ サイズベースローテーション（選択肢 D）の組み合わせを強く推奨する。

影式のターゲットユーザーは非開発者であり、問題発生時の初動対応は「ログファイルをサポートに送る」または「ログファイルで自己診断する」ことになる。コンソールは INFO だけで清潔に保ちつつ、ファイルに DEBUG を常時記録しておくことで、発生後の問題追跡が劇的に向上する。

サイズベースローテーションは「5MB × 4ファイル（現在+3世代）= 最大 20MB」と上限が明確で、NFR-4（メモリ100MB）の数値よりずっと小さい。実装コストも低い。

**[Critical]**（批判者の視点）

懸念点は以下の2点である。

第一に、DEBUG ログを常時ファイル出力する場合、API 呼び出しのリクエスト/レスポンス内容が含まれることになる。persona_core.md の内容（個人的なキャラクター設定）や observations（会話履歴の断片）が DEBUG ログに記録されるリスクがある。ログの内容ポリシーを明示する必要がある。

第二に、TimedRotatingFileHandler（選択肢 E）は「日付単位の整理」の観点で魅力的だが、Windows のファイルロック問題は実績が乏しい。Phase 1 では実証的に安全な RotatingFileHandler を選ぶべきだ。

**[Mediator]**（調停者の結論）

選択肢 B（コンソール/ファイル分離）+ 選択肢 D（サイズベースローテーション）の組み合わせを採用する。

Critical の懸念（プライバシー）に対しては、DEBUG ログに LLM レスポンスの本文を含めない運用ルールを設ける。具体的には、「LLM が生成したテキスト本体」はログに出力しない（出力長・モデル名・呼び出し時間のみ記録）。これにより、ログファイルが流出しても会話内容は漏洩しない。

---

## 4. 決定

**採用**: コンソール/ファイル分離運用（選択肢 B）+ サイズベースローテーション（選択肢 D）の組み合わせ

**理由**:
1. **FR-1.5 の自然な実現**: コンソールに INFO 以上、ファイルに DEBUG 以上を出力する構造が要件と一致する
2. **診断性**: 問題発生後の追跡に必要な DEBUG 情報がファイルに残る
3. **ディスク安全性**: 最大 20MB（5MB × 4世代）に抑え、長期常駐でも安全
4. **標準ライブラリのみ**: NFR-3（外部依存最小化）を遵守。loguru 等のサードパーティ不要
5. **プライバシー保護**: LLM レスポンス本文をログに含めないルールで、ログファイル流出リスクを低減

---

## 5. 詳細仕様

### 5.1 ロガー設定概要

```
アーキテクチャ:
  root logger
    ├── ConsoleHandler（StreamHandler）  → stderr → レベル: INFO
    └── FileHandler（RotatingFileHandler）→ data/kage_shiki.log → レベル: DEBUG
```

ロガー名の命名規則: `kage_shiki.<module>` 形式を使用する。

| モジュール | ロガー名 |
|-----------|---------|
| core/config.py | `kage_shiki.core.config` |
| agent/agent_core.py | `kage_shiki.agent.core` |
| agent/llm_client.py | `kage_shiki.agent.llm` |
| memory/db.py | `kage_shiki.memory.db` |
| memory/memory_worker.py | `kage_shiki.memory.worker` |
| persona/persona_system.py | `kage_shiki.persona.system` |
| persona/wizard.py | `kage_shiki.persona.wizard` |
| gui/tkinter_view.py | `kage_shiki.gui.tkinter` |
| tray/system_tray.py | `kage_shiki.tray` |

### 5.2 ログフォーマット

**コンソール（INFO 以上）**:

```
[HH:MM:SS] LEVEL  kage_shiki.module  メッセージ
```

例:
```
[14:32:07] INFO   kage_shiki.core.config  config.toml を読み込みました
[14:32:08] WARNING kage_shiki.agent.llm  APIタイムアウト（リトライ 1/3）
```

**ファイル（DEBUG 以上）**:

```
YYYY-MM-DD HH:MM:SS,mmm LEVEL     kage_shiki.module  メッセージ
```

例:
```
2026-03-15 14:32:07,123 INFO      kage_shiki.core.config  config.toml を読み込みました
2026-03-15 14:32:08,456 DEBUG     kage_shiki.memory.db  FTS5検索: クエリ="天気" 件数=3 時間=0.012s
2026-03-15 14:32:09,789 WARNING   kage_shiki.agent.llm  APIタイムアウト（リトライ 1/3）
```

### 5.3 RotatingFileHandler パラメータ

| パラメータ | 値 | 理由 |
|----------|---|------|
| `maxBytes` | 5,242,880（5MB） | 常駐アプリの1日分ログとして適切なサイズ |
| `backupCount` | 3 | 現在 + 3世代 = 合計最大 20MB。ディスク消費を限定 |
| `encoding` | `utf-8` | Windows 環境での日本語文字化け防止 |
| `delay` | `True` | 初回書き込み時にファイル生成。起動時のファイル競合を防止 |

世代管理の例:
```
kage_shiki.log       ← 現在（最新）
kage_shiki.log.1     ← 1世代前
kage_shiki.log.2     ← 2世代前
kage_shiki.log.3     ← 3世代前（最古、次のローテーションで削除）
```

### 5.4 config.toml への追加セクション

```toml
[logging]
level = "INFO"          # コンソール出力レベル ("DEBUG", "INFO", "WARNING", "ERROR")
file_level = "DEBUG"    # ファイル出力レベル（通常は変更不要）
max_bytes = 5242880     # ログファイル最大サイズ（バイト）: デフォルト 5MB
backup_count = 3        # ログファイル世代数: デフォルト 3
```

### 5.5 ログ出力ポリシー（プライバシー保護）

以下の情報はログ（DEBUG 含む）に含めない。

| 禁止情報 | 代替記録内容 |
|---------|------------|
| LLM レスポンス本文（キャラクターの発言内容） | 応答文字数・入力トークン数・出力トークン数・処理時間 |
| ユーザー入力テキスト本文 | 入力文字数・タイムスタンプ |
| persona_core.md の内容 | ファイルパス・ハッシュ値・読み込み成否 |
| human_block.md の内容 | 更新の有無・更新セクション名 |

以下の情報はログに含めてよい。

| 許可情報 | ログレベル |
|---------|----------|
| 起動・終了の記録 | INFO |
| 設定値の読み込み結果（APIキー以外） | INFO |
| API 呼び出しのメタデータ（モデル名・トークン数・時間） | DEBUG |
| FTS5 検索クエリ・件数・時間 | DEBUG |
| DB 操作の成否・件数 | DEBUG |
| エラーのスタックトレース | ERROR |
| リトライ状況 | WARNING |

### 5.6 logging_setup.py の構造（擬似コード）

```python
# 実装コードではなく、モジュール構造の定義

# 関数: setup_logging(config: AppConfig, log_dir: Path) -> None
#   目的: アプリケーション起動時に一度だけ呼び出す
#   処理:
#     1. root logger のレベルを DEBUG に設定（最も低い = 全レベルを捕捉）
#     2. ConsoleHandler（StreamHandler to stderr）を追加
#        - レベル: config.logging.level（デフォルト INFO）
#        - フォーマット: "[HH:MM:SS] LEVEL  name  message"
#     3. RotatingFileHandler を追加
#        - パス: log_dir / "kage_shiki.log"
#        - レベル: config.logging.file_level（デフォルト DEBUG）
#        - maxBytes: config.logging.max_bytes（デフォルト 5MB）
#        - backupCount: config.logging.backup_count（デフォルト 3）
#        - encoding: "utf-8"
#        - フォーマット: "YYYY-MM-DD HH:MM:SS,mmm LEVEL  name  message"
#     4. anthropic ライブラリのロガーを WARNING 以上に設定
#        （anthropic SDK が DEBUG レベルで大量のログを出す場合の抑制）
#
# モジュール取得:
#   各モジュールは以下のイディオムでロガーを取得する
#   logger = logging.getLogger(__name__)
#   これにより "kage_shiki.agent.agent_core" 等の名前が自動的に付与される
```

### 5.7 起動シーケンスとの連携

`main.py` における logging_setup の呼び出しタイミング（FR-1.5 との関係）:

```
起動シーケンス（requirements.md Section 5.5 より）:
  1. config.toml 読み込み  ← この時点でログを出したいが、まだセットアップ前
  2. ANTHROPIC_API_KEY 確認
  3. data_dir 初期化       ← log_dir が確定する
  4. logging_setup 呼び出し ← ここで初めてファイルハンドラーが使える
  5. 以降の全処理はログ出力可能
```

課題: ステップ 1-3 の間にエラーが発生した場合のログ記録方法。

解決策: ステップ 1-3 では標準の `print()` を使用し、ステップ 4 以降で `logging` に切り替える。ステップ 1-3 で発生したエラーを、ステップ 4 後に `logger.warning()` で再記録するか、起動シーケンス全体のログをメモリバッファに一時保持して後から書き出す。

Phase 1 では `print()` + 後から `logging` で再記録する方式を採用する（シンプル優先）。

---

## 6. 影響範囲

| 影響先 | 内容 |
|--------|------|
| D-1（ディレクトリ構成） | `core/logging_setup.py` に実装。ログファイルは `data/kage_shiki.log` |
| main.py | `data_dir` 確定後に `setup_logging()` を呼び出す |
| 全モジュール | `logger = logging.getLogger(__name__)` パターンを使用 |
| core/config.py | AppConfig に `logging` セクション（level, file_level, max_bytes, backup_count）を追加 |
| config.toml | `[logging]` セクションを追加 |
| D-2 受入条件（FR-1.5） | INFO 以上がコンソール+ファイルに出力される。観察可能な条件: ログファイルが存在し、起動ログが INFO で記録されている |
