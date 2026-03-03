# D-13: observations.session_id の生成規則

**決定対象**: requirements.md Section 8 D-13 — observations.session_id の形式と生成方式
**関連 FR**: FR-3.12（SessionContext の保持）, FR-3.3（observations への即時書込）, FR-3.4（FTS5 検索）
**ステータス**: 提案（承認待ち）

---

## 1. コンテキスト

### なぜこの決定が必要か

requirements.md Section 4.2 の SQLite スキーマでは、`observations` テーブルに `session_id TEXT` カラムが定義されている。このカラムは `SessionContext`（in-memory バッファ）と `observations` テーブルのレコードを関連付けるために使用される。

```sql
CREATE TABLE observations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    content     TEXT NOT NULL,
    speaker     TEXT NOT NULL,
    created_at  REAL NOT NULL,
    session_id  TEXT,          -- セッション識別子
    embedding   BLOB
);
```

FR-3.12 の定義:
> セッション中の会話ターンを SessionContext（in-memory バッファ）として保持する。セッション開始から現在までの会話がコンテキストウィンドウに含まれる。次回起動時には引き継がない。

session_id は:
1. **アプリケーション起動時に1回生成され**、そのセッション中の全 observations に付与される
2. **次回起動時には新しい session_id が生成される**（セッション間の分離）
3. DB に保存され、デバッグや将来の分析に使用される

### session_id の用途整理

| 用途 | Phase 1 | Phase 2 以降 |
|------|---------|-------------|
| 起動ごとの observations のグルーピング | 必須 | 継続 |
| デバッグ時の「今セッションのレコード」特定 | 必須 | 継続 |
| FTS5 検索での session_id フィルタ | 任意（現状は全期間検索） | 任意 |
| セッション間の関係分析 | 不要 | 将来的に検討 |

---

## 2. 選択肢分析

### 選択肢 A: UUID v4

Python 標準ライブラリ `uuid.uuid4()` で生成する。

```python
import uuid
session_id = str(uuid.uuid4())
# 例: "f47ac10b-58cc-4372-a567-0e02b2c3d479"
```

- **形式**: `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`（36文字、ハイフン含む）
- **一意性**: 128ビットのランダム値。衝突確率は無視できるレベル（2^122 分の1）
- **生成コスト**: `os.urandom()` を使用するため、エントロピープール依存だが通常は即座

- **メリット**:
  - 一意性が理論上保証されており、同日複数回起動でも衝突しない
  - Python 標準ライブラリのみで実現（`import uuid`）
  - SQLite のインデックス対象として問題のない長さ（36文字）
  - 業界標準であり、将来的な外部ツールとの連携でも問題が起きにくい

- **デメリット**:
  - 人間可読性が低い（「f47ac10b-58cc-...」から「2026-03-03 14:32 の起動」を識別できない）
  - デバッグ時に `observations` テーブルを目視で確認する際、どの起動のセッションかが直感的にわからない
  - 36文字はやや長め（ただし SQLite での文字列比較はインデックスで高速）

### 選択肢 B: 起動日時ベース（YYYYMMDD_HHMMSS）

アプリケーション起動時刻を文字列化する。

```python
from datetime import datetime
session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
# 例: "20260303_143207"
```

- **形式**: `YYYYMMDD_HHMMSS`（15文字）
- **一意性**: 同一秒に複数起動した場合に衝突する可能性がある

- **メリット**:
  - 人間可読性が高い（「20260303_143207 = 2026-03-03 14:32:07 の起動」と一目でわかる）
  - デバッグ時に `SELECT * FROM observations WHERE session_id = '20260303_143207'` で直感的に検索できる
  - 15文字と短く、インデックス効率が良い
  - `created_at`（Unix timestamp）と情報が重複するが、可読性のトレードオフとして許容できる

- **デメリット**:
  - 同一秒内に2回起動した場合（テスト実行時、クラッシュ直後の即座再起動）に衝突する
  - 衝突した場合、複数セッションの observations が同じ session_id で混在する（混乱の原因）
  - 日時情報が固定長のためソート性はあるが、UUID より意味的な一意性が弱い

**一意性の考察**: 通常ユーザーが同一秒に2回起動することは稀だが、開発・テスト環境では十分ありえる。衝突した場合の影響は「2つのセッションが同じ session_id を持つ」であり、デバッグ時の混乱を招く。

### 選択肢 C: 連番（AUTOINCREMENT）

SQLite の別テーブル（sessions テーブル）または Python 側のカウンターで連番を管理する。

```python
# Python 側での管理例
def get_next_session_id(conn) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(CAST(session_id AS INTEGER)), 0) + 1 FROM observations"
    ).fetchone()
    return row[0]

session_id = str(get_next_session_id(conn))
# 例: "1", "2", "3", ...
```

- **メリット**:
  - 最も短く（"1", "2", ...）、ソート性がある
  - デバッグ時に「セッション番号」として直感的

- **デメリット**:
  - `MAX(session_id)` クエリが初回起動時は OK だが、データが増えると（数万レコード）パフォーマンスが気になる
  - observations テーブルが空の初回は `MAX` が NULL を返す → COALESCE 等の対処が必要
  - 他の DB ツールや将来の分析で「セッション番号 3 のデータ」と言われたとき、日時情報が全くわからない
  - 専用の sessions テーブルを作るならスキーマが増える（Phase 1 スコープ外）

---

## 3. Three Agents Perspective

**[Affirmative]（推進者）**:

選択肢 B（起動日時ベース）を推す。デバッグ時の利便性は開発効率に直結する。SQLite を直接確認するとき、`session_id = '20260303_143207'` は直感的に意味を持つが、`session_id = 'f47ac10b-58cc-...'` は UUID をコピペしないと確認できない。同一秒衝突のリスクはあるが、ユーザーが意図的に同一秒に2回起動する操作は通常発生しない。テスト環境でも `time.sleep(1)` を挟めば回避できる。

**[Critical]（批判者）**:

選択肢 B の「同一秒衝突」リスクを軽視すべきでない。特に自動テストでは複数のテストケースが連続して `session_id` を生成するため、1秒の粒度では衝突が頻発する。これはテストの信頼性を損なう。選択肢 A（UUID v4）は標準ライブラリで一意性を保証でき、人間可読性の低さは DB ビューアやログ出力で補完できる。また、`created_at`（Unix timestamp）の情報があれば「どの起動か」は追跡できるため、session_id 自体に日時情報を埋め込む必要はない。

**[Mediator]（調停者）**:

両者の主張を統合し、**ハイブリッド方式**（起動日時 + ランダム短縮文字列）を採用する。

```python
import uuid
from datetime import datetime

# 起動日時（分精度）+ UUID の先頭8文字
# 例: "20260303_1432_f47ac10b"
dt_part = datetime.now().strftime("%Y%m%d_%H%M")
uuid_part = uuid.uuid4().hex[:8]
session_id = f"{dt_part}_{uuid_part}"
```

- 形式: `YYYYMMDD_HHMM_xxxxxxxx`（22文字）
- 人間可読性: 日時（分精度）が含まれるためデバッグ時に一目でわかる
- 一意性: 同一分内での衝突は UUID の8文字（約42億通り）でほぼ解消
- 長さ: UUID v4（36文字）より短く、日時のみ（15文字）より長いが許容範囲

ただし、このハイブリッド方式は「選択肢 A でも選択肢 B でもない第3の選択肢」であり、シンプルさを損なう可能性がある。要件の実態（デバッグ頻度、テスト環境での衝突頻度）を考慮した最終判断が必要。

**調停結論**: ハイブリッド方式（起動日時 + UUID 先頭8文字）を採用。人間可読性と一意性の両立。

---

## 4. 決定

**採用**: ハイブリッド方式 — 起動日時（分精度 `YYYYMMDD_HHMM`）+ UUID v4 先頭8文字

**形式**: `YYYYMMDD_HHMM_xxxxxxxx`
**例**: `20260303_1432_f47ac10b`
**文字数**: 22文字（固定長）

**理由**:
1. **人間可読性**: `20260303_1432` で「2026年3月3日 14時32分頃の起動」が一目で識別できる
2. **一意性**: UUID 先頭8文字（16進数、約42億通り）で同一分内の衝突確率をほぼゼロに低減
3. **簡潔さ**: UUID v4 フルの36文字より短く、DB インデックス効率が良い
4. **実装コスト**: `uuid` + `datetime` の両方が標準ライブラリのみで実現

---

## 5. 詳細仕様

### 5.1 session_id 生成関数

```python
# 擬似コード: agent/agent_core.py 内に配置。SessionContext の初期化時に生成する（D-1 のモジュール責務定義に従う）
import uuid
from datetime import datetime


def generate_session_id() -> str:
    """
    アプリケーション起動時に1回呼び出してセッション識別子を生成する。

    形式: YYYYMMDD_HHMM_xxxxxxxx
    例: "20260303_1432_f47ac10b"

    - 日時部: 分精度（秒は含めない。可読性と一意性のバランス）
    - UUID部: uuid4().hex の先頭8文字（16進数8桁 = 32ビット、約42億通り）

    Returns:
        str: 22文字の固定長セッション識別子
    """
    dt_part = datetime.now().strftime("%Y%m%d_%H%M")
    uuid_part = uuid.uuid4().hex[:8]
    return f"{dt_part}_{uuid_part}"
```

### 5.2 SessionContext への組み込み

```python
# 擬似コード: SessionContext の初期化
class SessionContext:
    """
    セッション中の会話バッファ（in-memory）。
    次回起動時には引き継がない（FR-3.12）。
    """
    def __init__(self):
        self.session_id: str = generate_session_id()
        self.turns: list[dict] = []  # {"speaker": "user"|"mascot", "content": str}

    def add_turn(self, speaker: str, content: str) -> None:
        self.turns.append({"speaker": speaker, "content": content})
```

### 5.3 observations への書き込み時の使用

```python
# 擬似コード: observations への即時書込（FR-3.3）
import time

def save_observation(conn, session_ctx: SessionContext, content: str, speaker: str) -> None:
    """
    observations テーブルに即時書込する（FR-3.3）。
    session_id は SessionContext から取得する。
    """
    conn.execute(
        "INSERT INTO observations (content, speaker, created_at, session_id) "
        "VALUES (?, ?, ?, ?)",
        (content, speaker, time.time(), session_ctx.session_id)
    )
    conn.commit()
    # FTS5 同期は D-4 で決定した INSERT トリガーが自動実行する
```

### 5.4 session_id のインデックス

Phase 1 では session_id でのフィルタ検索頻度は低い（デバッグ用途が主）。インデックスは必要に応じて追加する。

```sql
-- 必要になった場合のインデックス定義（Phase 1 では任意）
-- CREATE INDEX IF NOT EXISTS idx_observations_session_id ON observations (session_id);
```

FTS5 検索（Cold Memory）は全期間の observations を対象とするため、session_id フィルタは Phase 1 では使用しない。

### 5.5 バリデーション（形式の検証）

テスト用に session_id の形式を検証する正規表現:

```python
import re

SESSION_ID_PATTERN = re.compile(r"^\d{8}_\d{4}_[0-9a-f]{8}$")

def is_valid_session_id(session_id: str) -> bool:
    """session_id が期待する形式であるかを検証する（テスト・アサーション用）。"""
    return bool(SESSION_ID_PATTERN.match(session_id))
```

### 5.6 将来の拡張（Phase 2 以降）

Phase 2 以降で session_id を活用する可能性のある用途:
- セッション単位での会話件数・日時の集計（`GROUP BY session_id`）
- 特定セッションの全発言一括参照（「先週木曜日のセッション」）
- SessionContext に起動日時を格納してウォームメモリに活用

これらは Phase 2 以降に設計するため、Phase 1 の session_id 形式がこれらをブロックしないことを確認済み（`YYYYMMDD_HHMM_xxxxxxxx` は文字列として自然にソート可能）。

---

## 6. 影響範囲

| 影響先 | 内容 |
|--------|------|
| SessionContext クラス | 初期化時に `generate_session_id()` を呼ぶ |
| observations 書き込みパス | `session_ctx.session_id` を INSERT に渡す |
| 起動シーケンス（Section 5.5 Step 10） | `SessionContext` 初期化時に session_id が生成される |
| FR-3.3（即時書込） | session_id の値が確定した状態で INSERT される |
| FR-3.12（SessionContext） | session_id の生成が SessionContext 内で完結する |
| テスト | `generate_session_id()` の出力が `SESSION_ID_PATTERN` にマッチすること、および同時に2回呼んでも異なる値が返ること（UUID 部分の一意性） |

---

## 参照

- requirements.md Section 4.2（SQLite スキーマ）、Section 8 D-13、FR-3.3、FR-3.12
- docs/memos/middle-draft/01-memory-system.md（ストレージ設計、SessionContext）
- [Python uuid モジュール公式ドキュメント](https://docs.python.org/ja/3/library/uuid.html)
- [Python datetime.strftime 公式ドキュメント](https://docs.python.org/ja/3/library/datetime.html#strftime-and-strptime-format-codes)
