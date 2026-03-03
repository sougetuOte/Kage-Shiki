# D-4: FTS5 同期トリガー実装

**決定対象**: requirements.md Section 8 D-4 — FTS5 仮想テーブル（observations_fts）を observations と同期する方式
**関連 FR**: FR-3.2, FR-3.3, FR-3.4
**ステータス**: 提案（承認待ち）

---

## 1. コンテキスト

### なぜこの決定が必要か

requirements.md Section 4.2 で定義された SQLite スキーマには、`observations_fts` として FTS5 仮想テーブルが **外部コンテンツテーブル方式** で定義されている。

```sql
CREATE VIRTUAL TABLE observations_fts USING fts5(
    content,
    content='observations',
    content_rowid='id'
);
```

FTS5 の外部コンテンツテーブル方式（`content='observations'`）は、テキスト本体を observations テーブルから読み取る。これにより DB サイズの重複を避けられるが、**FTS5 インデックスは自動では更新されない** という制約がある。

observations テーブルに新規レコードが INSERT されたとき、observations_fts インデックスを同期する手段を明示的に設計しなければ、FR-3.4 の FTS5 検索（Cold Memory）が機能しない。

### Phase 1 の運用特性

- observations は **INSERT のみ**（UPDATE・DELETE は発生しない）
  - ユーザー発言・マスコット応答は追記型
  - 過去の発言を編集・削除する機能は Phase 1 のスコープ外
- FR-3.3: 各発言の即時書込（ユーザー送信ごとに INSERT 1回）
- FR-3.4: Cold Memory 検索は会話中に「必要に応じて」実行（随時クエリ）

---

## 2. 選択肢分析

### 選択肢 A: SQLite トリガー（INSERT/UPDATE/DELETE）

observations テーブルへの DML 操作をフックする SQLite トリガーを DB 内に定義する。

```sql
-- INSERT トリガー
CREATE TRIGGER observations_fts_insert
AFTER INSERT ON observations BEGIN
    INSERT INTO observations_fts(rowid, content)
    VALUES (new.id, new.content);
END;

-- UPDATE トリガー（将来の UPDATE に備えて定義しておく場合）
CREATE TRIGGER observations_fts_update
AFTER UPDATE ON observations BEGIN
    INSERT INTO observations_fts(observations_fts, rowid, content)
    VALUES ('delete', old.id, old.content);
    INSERT INTO observations_fts(rowid, content)
    VALUES (new.id, new.content);
END;

-- DELETE トリガー（将来の DELETE に備えて定義しておく場合）
CREATE TRIGGER observations_fts_delete
AFTER DELETE ON observations BEGIN
    INSERT INTO observations_fts(observations_fts, rowid, content)
    VALUES ('delete', old.id, old.content);
END;
```

- **メリット**:
  - DB 内で完結するため、アプリケーション側の同期コードが不要
  - 将来 UPDATE/DELETE が発生しても自動対応（スキーマで定義済みなら）
  - SQLite の制約でトランザクション内でアトミックに処理される
  - 複数の書き込み経路（将来的な管理ツール等）からの INSERT にも一貫して対応

- **デメリット**:
  - Phase 1 では UPDATE/DELETE が発生しないため、UPDATE/DELETE トリガーは死にコード（YAGNI 原則に反する）
  - INSERT トリガーだけならシンプルだが、将来の3トリガーセットを今から定義すると複雑さが増す
  - DB スキーマのマイグレーション管理が必要になる（テーブル変更時にトリガーも変更）

### 選択肢 B: アプリケーション側で明示的に同期（Python コード）

Python の MemoryWorker（またはリポジトリ層）が observations に INSERT した直後に、同じトランザクション内で observations_fts にも INSERT する。

```python
# 擬似コード: リポジトリ層での同期
def save_observation(conn, content, speaker, created_at, session_id):
    cursor = conn.execute(
        "INSERT INTO observations (content, speaker, created_at, session_id) "
        "VALUES (?, ?, ?, ?)",
        (content, speaker, created_at, session_id)
    )
    new_id = cursor.lastrowid
    conn.execute(
        "INSERT INTO observations_fts(rowid, content) VALUES (?, ?)",
        (new_id, content)
    )
    conn.commit()
```

- **メリット**:
  - Phase 1 の実際の要件（INSERT のみ）に対して最小限の実装
  - Python コードとして可視化されており、デバッグしやすい
  - DB スキーマに UPDATE/DELETE トリガーの「死にコード」を残さない
  - YAGNI 原則に適合

- **デメリット**:
  - アプリケーション側が FTS5 同期責任を持つため、直接 SQL を実行するパスが複数生まれた場合に同期漏れリスクがある
  - 将来 UPDATE/DELETE が必要になった場合、アプリケーション側での対応が必要（忘れるリスク）

### 選択肢 C: 外部コンテンツテーブルの rebuild（INSERT ごとではなく定期実行）

FTS5 の `INSERT INTO observations_fts(observations_fts) VALUES('rebuild')` を定期的に実行してインデックスを再構築する。

```sql
-- 定期実行（起動時やシャットダウン前）
INSERT INTO observations_fts(observations_fts) VALUES('rebuild');
```

- **メリット**:
  - 実装がシンプル（1行の SQL）
  - 会話中の即時同期が不要なタイミングで実行可能

- **デメリット**:
  - rebuild は observations テーブル全体を再スキャンするため、レコード数が増えるにつれて実行時間が増加
  - FR-3.4 の Cold Memory 検索は会話中にリアルタイムで必要 → rebuild のタイミング次第で直近の observations がインデックスに含まれないリスク
  - NFR-5（起動10秒以内）に悪影響を与える可能性（起動時 rebuild の場合）
  - 数万レコードに達した長期運用時の rebuild コストが予測困難

---

## 3. Three Agents Perspective

**[Affirmative]（推進者）**:

選択肢 A（SQLite トリガー）を推す。DB の整合性はDB側で保証するのが原則であり、アプリケーション層が同期責任を持つと、将来的に複数の書き込み経路（デバッグ用スクリプト、マイグレーションツール等）から直接 INSERT されたとき同期が壊れる。Phase 1 でも INSERT トリガー1本だけ定義すれば十分であり、UPDATE/DELETE トリガーは必要になったら追加すれば良い。トリガーの存在はスキーマ管理で追跡可能であり、Python コードよりも「正しい場所に書かれた責務」になる。

**[Critical]（批判者）**:

選択肢 A のうち UPDATE/DELETE トリガーを今から定義することには反対する。Phase 1 では observations の UPDATE/DELETE は発生しないと要件で確定しており、YAGNI 原則に反する。また、外部コンテンツテーブル方式でのトリガー定義は SQLite のドキュメントで推奨されているものの、FTS5 の `delete` コマンドの書き方（`INSERT INTO fts(fts, rowid, content) VALUES('delete', ...)` という非直感的な構文）は実装ミスのリスクがある。

選択肢 C は論外。会話中の検索がインデックス最新性に依存しているにもかかわらず、rebuild のタイミングが不定では FR-3.4 の受入条件を満たせない。

選択肢 B（アプリケーション同期）は現在の要件には適合しているが、将来リスクを抱える。`save_observation` という単一の入口を作り、その中で同期を行えばリスクは最小化できる。

**[Mediator]（調停者）**:

Phase 1 の要件は「INSERT のみ」であり、まず INSERT トリガー1本（選択肢 A の INSERT 部分のみ）を DB 内に定義する方式を採用する。

根拠:
1. INSERT トリガーの実装はシンプルで誤りにくい（3行の SQL）
2. DB 内での定義はアプリケーション側の同期漏れを防ぐ
3. UPDATE/DELETE トリガーは Phase 1 スコープ外のため定義しない（YAGNI）
4. 将来 UPDATE/DELETE が必要になったときはマイグレーションで追加すればよい
5. 選択肢 C（rebuild）は即時性とパフォーマンスの両面で不適

**採用: 選択肢 A の INSERT 部分のみ（INSERT トリガー単体）**

---

## 4. 決定

**採用**: 選択肢 A — SQLite INSERT トリガー（INSERT のみ、Phase 1 スコープに限定）

**理由**:
- FTS5 インデックスの同期責任を DB 層に持たせることで、アプリケーション側の同期漏れリスクを排除する
- Phase 1 では INSERT のみが発生するため、INSERT トリガー1本で十分（YAGNI 適合）
- UPDATE/DELETE トリガーは Phase 2 以降で observations の変更・削除が必要になった時点でマイグレーションにより追加する
- rebuild 方式（選択肢 C）は即時性要件（会話中 FTS5 検索）とパフォーマンスの両面で不採用

---

## 5. 詳細仕様

### 5.1 スキーマ定義（初期化 SQL に追加）

```sql
-- observations テーブルへの INSERT 後に FTS5 インデックスを同期する
-- Phase 1: INSERT のみ対応。UPDATE/DELETE は Phase 2 で必要になった時点で追加。
CREATE TRIGGER observations_fts_insert
AFTER INSERT ON observations BEGIN
    INSERT INTO observations_fts(rowid, content)
    VALUES (new.id, new.content);
END;
```

**注意**: FTS5 外部コンテンツテーブルへの直接 INSERT では、`content` カラムのみを指定する（speaker, created_at 等は FTS5 インデックスに含めない）。検索対象テキストは `content` フィールドのみで十分。

### 5.2 DB 初期化順序

トリガーはテーブル・仮想テーブルの作成後に定義する。

```sql
-- 0. WAL モード有効化（D-7 で定義済みの設定を転記）
PRAGMA journal_mode = WAL;

-- 1. observations テーブル
CREATE TABLE IF NOT EXISTS observations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    content     TEXT NOT NULL,
    speaker     TEXT NOT NULL,
    created_at  REAL NOT NULL,
    session_id  TEXT,
    embedding   BLOB
);

-- 2. FTS5 仮想テーブル（外部コンテンツテーブル方式）
CREATE VIRTUAL TABLE IF NOT EXISTS observations_fts USING fts5(
    content,
    content='observations',
    content_rowid='id'
);

-- 3. FTS5 同期トリガー（INSERT のみ）
CREATE TRIGGER IF NOT EXISTS observations_fts_insert
AFTER INSERT ON observations BEGIN
    INSERT INTO observations_fts(rowid, content)
    VALUES (new.id, new.content);
END;

-- 4. day_summary テーブル
CREATE TABLE IF NOT EXISTS day_summary (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT NOT NULL UNIQUE,
    summary     TEXT NOT NULL,
    created_at  REAL NOT NULL
);

-- 5. curiosity_targets テーブル（Phase 2 用予約）
CREATE TABLE IF NOT EXISTS curiosity_targets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    topic           TEXT NOT NULL,
    status          TEXT DEFAULT 'pending',
    priority        INTEGER DEFAULT 5,
    parent_id       INTEGER REFERENCES curiosity_targets(id),
    created_at      REAL NOT NULL,
    result_summary  TEXT
);

CREATE INDEX IF NOT EXISTS idx_curiosity_status
    ON curiosity_targets (status, priority);
```

### 5.3 FTS5 検索クエリ（Cold Memory 取得）

```python
# 擬似コード: Cold Memory 検索
def search_observations_fts(conn, query: str, top_k: int) -> list[dict]:
    """
    FTS5 全文検索で observations から上位 top_k 件を返す。
    FTS5 の BM25 スコアリングで関連度順に並ぶ。
    """
    rows = conn.execute(
        """
        SELECT o.id, o.content, o.speaker, o.created_at, o.session_id
        FROM observations_fts
        JOIN observations o ON observations_fts.rowid = o.id
        WHERE observations_fts MATCH ?
        ORDER BY bm25(observations_fts)
        LIMIT ?
        """,
        (query, top_k)
    ).fetchall()
    return [dict(row) for row in rows]
```

**注意**: FTS5 の BM25 スコアは負の値で返され、スコアが小さい（より負）ほど関連度が高い。`ORDER BY bm25(observations_fts)` は昇順（最も関連度が高いものが先頭）になる。

### 5.4 FTS5 インデックスの整合性確認（デバッグ用）

開発・テスト時のインデックス整合性確認:

```sql
-- FTS5 インデックスの整合性チェック（開発時のみ）
INSERT INTO observations_fts(observations_fts) VALUES('integrity-check');
```

このコマンドは FTS5 インデックスと外部コンテンツテーブルの整合性を検証する。不整合があると SQLite エラーが発生する。

### 5.5 Phase 2 での拡張方針

Phase 2 で observations の UPDATE または DELETE が必要になった場合、以下のトリガーをマイグレーションで追加する。

```sql
-- Phase 2 で必要になった時点で追加（Phase 1 では定義しない）

-- UPDATE トリガー
CREATE TRIGGER observations_fts_update
AFTER UPDATE ON observations BEGIN
    INSERT INTO observations_fts(observations_fts, rowid, content)
    VALUES ('delete', old.id, old.content);
    INSERT INTO observations_fts(rowid, content)
    VALUES (new.id, new.content);
END;

-- DELETE トリガー
CREATE TRIGGER observations_fts_delete
AFTER DELETE ON observations BEGIN
    INSERT INTO observations_fts(observations_fts, rowid, content)
    VALUES ('delete', old.id, old.content);
END;
```

---

## 6. 影響範囲

| 影響先 | 内容 |
|--------|------|
| `memory.db` 初期化スクリプト | CREATE TRIGGER 文を追加。DB 初期化関数内で定義 |
| MemoryWorker / リポジトリ層 | observations への INSERT 時に追加の同期コードは不要（トリガーが自動実行） |
| FR-3.3 の実装 | observations への INSERT だけで FTS5 も自動更新されるため実装がシンプル |
| FR-3.4 の実装 | FTS5 検索クエリは 5.3 の擬似コードを参照 |
| テスト | INSERT 後に FTS5 検索が機能することを確認するテストを必須とする |
| Phase 2 マイグレーション | UPDATE/DELETE が必要になった時点で 5.5 のトリガーを追加 |

---

## 参照

- requirements.md Section 4.2（SQLite スキーマ）
- requirements.md FR-3.2, FR-3.3, FR-3.4
- [SQLite FTS5 公式ドキュメント: External Content Tables](https://www.sqlite.org/fts5.html#external_content_tables)
- docs/memos/middle-draft/01-memory-system.md（記憶システム設計）
