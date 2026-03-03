# D-7: SQLite VACUUM 実行方式

**決定対象**: requirements.md Section 8 D-7 — 長期運用での DB 肥大化防止のための VACUUM 実行方式
**関連 FR**: （直接対応する FR なし。04-unified-design.md「容量・性能の考慮」、01-memory-system.md「長期運用」に対応）
**関連 NFR**: NFR-5（起動10秒以内）、NFR-9（データ安全性）
**ステータス**: 提案（承認待ち）

---

## 1. コンテキスト

### なぜこの決定が必要か

影式は常駐アプリケーションであり、`observations` テーブルへは日常的な対話を通じて継続的に INSERT が行われる。04-unified-design.md および 01-memory-system.md では長期運用時の容量見積もりとして「数ヶ月で数万レコード」を想定している。

SQLite では、レコードが大量に蓄積されると DB ファイルサイズが増加するが、このプロジェクトでは **DELETE が発生しない** という重要な特性がある。

SQLite の `VACUUM` コマンドは、主に以下の用途で使われる:
1. DELETE によって生じた未使用ページの解放（ファイルサイズ縮小）
2. インデックスの断片化解消（検索パフォーマンス改善）
3. `auto_vacuum` が無効な場合の定期メンテナンス

この特性を踏まえ、Phase 1 での VACUUM 実行方式を明確にする。

### 対象 DB の運用特性分析

| テーブル | 変更種別 | 肥大化リスク | VACUUM の効果 |
|---------|---------|------------|--------------|
| observations | INSERT のみ | 継続的に増加するが未使用ページは発生しない | **限定的**（断片化解消のみ） |
| observations_fts | INSERT トリガー経由 | observations に連動して増加 | **限定的** |
| day_summary | INSERT（1日1行） | 年間 365 行。増加ペースは無視できる | **ほぼなし** |
| curiosity_targets | Phase 1 では空 | 問題なし | **なし** |

**重要な結論**: Phase 1 では `DELETE` が発生しないため、VACUUM の主要効果（未使用ページ解放によるファイルサイズ縮小）は得られない。VACUUM を実行しても DB ファイルサイズはほとんど変化しない。

---

## 2. 選択肢分析

### 選択肢 A: 起動時 VACUUM

アプリケーション起動時に毎回 `VACUUM` を実行する。

```python
# 擬似コード
def initialize_db(conn):
    conn.execute("VACUUM")
    conn.commit()
```

- **メリット**:
  - 実装がシンプル（1行）
  - 定期実行のロジック（最終実行日の記録・比較）が不要

- **デメリット**:
  - VACUUM は DB 全体を一時ファイルにコピーするため、数万レコード規模では数秒〜十数秒かかる可能性がある
  - NFR-5（起動10秒以内）を直接脅かす最大のリスク要因
  - 毎回実行するため、DELETE なし＝ファイルサイズ変化なしの状況で無駄な処理を繰り返す
  - ユーザーが「起動が遅い」と感じる体験の悪化

### 選択肢 B: N日ごとの定期実行

最終 VACUUM 実行日を記録し、N日（例: 30日）が経過していれば起動時に実行する。

```python
# 擬似コード
def maybe_vacuum(conn, config_dir: Path, interval_days: int = 30):
    last_vacuum_file = config_dir / ".last_vacuum"
    today = datetime.date.today()

    if last_vacuum_file.exists():
        last_date = datetime.date.fromisoformat(last_vacuum_file.read_text().strip())
        if (today - last_date).days < interval_days:
            return  # まだ実行しない

    conn.execute("VACUUM")
    conn.commit()
    last_vacuum_file.write_text(today.isoformat())
```

- **メリット**:
  - NFR-5 への影響を N 日に 1 回に限定できる
  - 将来 DELETE が発生した場合にも対応できる汎用的な方式

- **デメリット**:
  - Phase 1 では DELETE なし＝VACUUM の実質的な効果がほぼない状況で、30日ごとに起動を重くする
  - 最終実行日の記録・管理ファイルが必要（設計上の複雑さが増す）
  - VACUUM 実行時のユーザー体験悪化は選択肢 A と同様

### 選択肢 C: 手動実行のみ（自動 VACUUM なし）

Phase 1 では自動 VACUUM を実装せず、将来的に必要になれば追加する。ユーザーや開発者が sqlite3 CLI で手動実行。

- **メリット**:
  - Phase 1 の運用特性（DELETE なし、効果なし）に最も適合
  - YAGNI 原則に完全適合
  - NFR-5 への影響ゼロ
  - 実装コスト ゼロ

- **デメリット**:
  - 将来 DELETE が発生した場合（Phase 2 以降）、フォローが必要
  - 長期運用で FTS5 断片化が発生した場合に対処手段がない（ユーザーは対処方法を知らない可能性がある）

### 選択肢 D: auto_vacuum=INCREMENTAL

DB 作成時に `PRAGMA auto_vacuum = INCREMENTAL` を設定し、必要に応じて `PRAGMA incremental_vacuum` を実行する。

```sql
-- DB 作成時（初回のみ。以降は変更不可）
PRAGMA auto_vacuum = INCREMENTAL;

-- 定期的なインクリメンタル VACUUM（起動時など）
PRAGMA incremental_vacuum(100);  -- 最大100ページを解放
```

- **メリット**:
  - ページ単位の段階的解放で、VACUUM の処理を分散できる
  - `incremental_vacuum(N)` でページ数を制限できるため起動時間への影響を制御しやすい

- **デメリット**:
  - `auto_vacuum = INCREMENTAL` は DB 作成時に設定する必要があり、**既存 DB には適用不可**
  - `auto_vacuum = INCREMENTAL` は内部的に各ページにポインタを追加するため DB ファイルサイズが若干増加する
  - DELETE なし状態では `incremental_vacuum` を実行しても解放するページが存在せず無意味
  - 設定方法が複雑で、メリットが Phase 1 では得られない

---

## 3. Three Agents Perspective

**[Affirmative]（推進者）**:

選択肢 B（30日定期）を推したい。影式は長期常駐アプリケーションであり、Phase 2 以降で DELETE（古いデータの整理・忘却曲線による削除）が必要になる可能性がある。その時点で VACUUM の仕組みがないと後付けになる。30日ごとなら NFR-5 への影響は月1回の起動にしか出ず、ユーザーが気づかない可能性もある。

**[Critical]（批判者）**:

現在の Phase 1 運用特性（INSERT のみ、DELETE なし）において VACUUM の実質的な効果はほぼゼロ。選択肢 A・B・D のいずれも、DELETE によって生じた未使用ページを解放する機能であり、DELETE が発生しない限りファイルサイズは変化しない。「将来に備えて」という理由で現在不要な仕組みを実装することは YAGNI 原則に反する。NFR-5（起動10秒以内）は基本的な品質指標であり、30日に1回でも不確定要因として残すべきではない。選択肢 C（手動のみ）が Phase 1 として最も正直な決定。

**[Mediator]（調停者）**:

批判者の指摘は技術的に正確であり、Phase 1 の運用特性に基づけば選択肢 C が最適と判断する。ただし、将来の拡張を完全に閉じるのではなく、「Phase 2 で DELETE が必要になった場合に VACUUM 仕組みを追加する」という方針を ADR として明記しておく。選択肢 D の `auto_vacuum=INCREMENTAL` については、既存 DB に適用不可という致命的な制約から Phase 1 での採用は不可。

**採用: 選択肢 C（手動のみ）+ Phase 2 での定期実行追加を予定として記録**

---

## 4. 決定

**採用**: 選択肢 C — Phase 1 では自動 VACUUM を実装しない

**理由**:
1. Phase 1 の observations は INSERT のみで DELETE が発生しない。VACUUM の主効果（未使用ページ解放によるファイルサイズ縮小）は得られない
2. FTS5 インデックスの断片化は発生するが、Phase 1 の数万レコード規模では検索パフォーマンスへの影響は無視できるレベル
3. NFR-5（起動10秒以内）への不確定な影響を排除する
4. YAGNI 原則に適合する最もシンプルな選択
5. Phase 2 以降で DELETE（忘却・整理）が必要になった時点で選択肢 B（定期 VACUUM）を追加実装する

**Phase 2 への引き継ぎ事項**:
- Phase 2 で observations の DELETE（忘却曲線適用による古いレコードの削除）を実装する場合は、起動時 or 定期実行の VACUUM を追加すること
- `auto_vacuum` 設定は DB 作成時にしか変更できないため、変更する場合は DB 再作成（マイグレーション）が必要

---

## 5. 詳細仕様

### 5.1 DB 初期化時の設定

VACUUM に関連して DB 初期化時に設定するプラグマ:

```sql
-- WAL モード（推奨設定、VACUUM とは独立）
PRAGMA journal_mode = WAL;

-- auto_vacuum は使用しない（Phase 1 では NONE のまま）
-- PRAGMA auto_vacuum = NONE;  -- デフォルト値のため明示不要

-- キャッシュサイズ（パフォーマンス用途、VACUUM とは独立）
PRAGMA cache_size = -2000;  -- 2MB のページキャッシュ
```

**注意**: `journal_mode = WAL` は VACUUM と組み合わせ注意点がある。WAL モードでは `VACUUM` 実行時に WAL ファイルがチェックポイントされる。Phase 1 では手動 VACUUM しか行わないため問題ない。

### 5.2 手動 VACUUM 実行手順（開発者・ユーザー向けドキュメント）

長期運用後に手動で VACUUM を実行する場合の手順:

```bash
# アプリケーションを終了してから実行
sqlite3 /path/to/data/memory.db "VACUUM;"
```

または Python スクリプト:

```python
# 擬似コード: standalone メンテナンススクリプト（Phase 1 では提供しなくてよい）
import sqlite3
conn = sqlite3.connect("data/memory.db")
conn.execute("VACUUM")
conn.close()
print("VACUUM 完了")
```

### 5.3 DB サイズ監視（Phase 2 への準備）

Phase 1 では実装しないが、Phase 2 で定期 VACUUM を追加する際の参考:

```python
# 擬似コード: Phase 2 での定期 VACUUM 実装イメージ
import datetime
import sqlite3
from pathlib import Path

def maybe_vacuum_db(conn: sqlite3.Connection, state_dir: Path, interval_days: int = 30) -> None:
    """
    interval_days が経過していれば VACUUM を実行する。
    Phase 2 で DELETE 運用が始まったら追加実装。
    """
    last_vacuum_file = state_dir / ".last_vacuum_date"
    today = datetime.date.today()

    if last_vacuum_file.exists():
        last_date = datetime.date.fromisoformat(last_vacuum_file.read_text().strip())
        if (today - last_date).days < interval_days:
            return

    conn.execute("VACUUM")
    conn.commit()
    last_vacuum_file.write_text(today.isoformat())
```

### 5.4 FTS5 インデックスのオプティマイズ（VACUUM の代替）

VACUUM に代わる軽量なメンテナンス操作として、FTS5 の `optimize` コマンドが利用可能。これは VACUUM より大幅に軽量で、FTS5 インデックスの断片化を解消する。

```sql
-- FTS5 インデックスのオプティマイズ（Phase 1 での代替メンテナンス）
-- observations_fts の断片化を解消するが、DB ファイルサイズには影響しない
INSERT INTO observations_fts(observations_fts) VALUES('optimize');
```

この操作は比較的軽量だが、Phase 1 では FTS5 の断片化による検索パフォーマンス劣化は観察されてから対応することとし、起動時の自動実行は行わない。

---

## 6. 影響範囲

| 影響先 | 内容 |
|--------|------|
| DB 初期化スクリプト | `journal_mode = WAL` 等の基本プラグマのみ設定。VACUUM 関連の追加実装なし |
| 起動シーケンス | VACUUM による起動時間への影響はゼロ |
| NFR-5（起動10秒以内） | VACUUM 実行なしのため影響なし。NFR-5 に対して安全側の選択 |
| Phase 2 タスク | observations の DELETE 実装時に定期 VACUUM（選択肢 B ベース）を追加する |
| ドキュメント | 長期運用時の手動 VACUUM 手順をユーザーガイドに記載（Phase 1 完了後） |

---

## 参照

- requirements.md Section 8 D-7
- docs/memos/middle-draft/04-unified-design.md「容量・性能（長期運用）」
- docs/memos/middle-draft/01-memory-system.md「容量・性能の考慮（長期運用）」
- [SQLite VACUUM 公式ドキュメント](https://www.sqlite.org/lang_vacuum.html)
- [SQLite FTS5 optimize コマンド](https://www.sqlite.org/fts5.html#the_optimize_command)
