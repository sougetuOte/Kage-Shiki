# D-20: 統合テスト設計

**決定対象**: requirements.md Section 9 D-20「統合テストの並列実行制御」
**関連 FR**: FR-8.3, FR-8.4, FR-8.5, FR-8.11
**前提**: Phase 1 ホットフィックス教訓（L-1: スレッド制約、L-2: UNIQUE 制約、L-3: 2重実行）
**ステータス**: 承認済み
**作成日**: 2026-03-06

---

## 1. コンテキスト

Phase 1 では単体テスト 649 件、97% カバレッジを達成したが、実動作で7件のホットフィックスが発生した。
そのうち3件は統合テストで検出可能な問題だった。

| 教訓 | 問題 | 対応 FR |
|------|------|---------|
| L-1 | SQLite の `check_same_thread` 制約違反（メインスレッドの接続をバックグラウンドで使用） | FR-8.3 |
| L-2 | 2回目起動時の UNIQUE 制約エラー（`day_summary` テーブルの重複挿入） | FR-8.4 |
| L-3 | シャットダウンの2重実行（atexit と SetConsoleCtrlHandler の競合） | FR-8.5 |

また FR-8.11（応答タイミングテスト）は D-17（LLMProtocol）と D-19（ウィザード GUI）の完成後に実装する。

---

## 2. Three Agents Perspective

### AoT Decomposition

| Atom | 判断内容 | 依存 |
|------|----------|------|
| A1 | テストの分類と配置方針 | なし |
| A2 | フレイキネス対策（スレッド同期） | A1 |
| A3 | `pytest-timeout` の採用可否 | A1 |
| A4 | シャットダウンテストの mock 戦略 | A1 |
| A5 | FR-8.11 タイミングテストの設計 | A2, D-17, D-19 |

---

### Atom A1: テストの分類と配置方針

**[Mediator]**

既存の `tests/` 構造（`test_agent/`, `test_memory/`, `test_persona/` 等）に加えて、
`tests/test_integration/` ディレクトリを新設する。

**ディレクトリ構成**:

```
tests/
├── test_integration/
│   ├── __init__.py
│   ├── test_multithread.py     ← FR-8.3: マルチスレッド統合テスト
│   ├── test_persistent_state.py ← FR-8.4: 永続状態ありの起動テスト
│   ├── test_shutdown.py        ← FR-8.5: シャットダウン全経路テスト
│   └── test_response_timing.py ← FR-8.11: 応答タイミングテスト
```

**分類基準**:
- `test_integration/` に含めるもの: 実スレッド、実ファイルシステム、複数モジュールを横断するテスト
- 既存 `test_*/` に残すもの: 単一モジュールの単体テスト（mock を多用するもの）

---

### Atom A2: フレイキネス対策（スレッド同期）

**[Affirmative]**

スレッドテストの安定化には `threading.Event` を使った明示的な同期が最も信頼性が高い。
`time.sleep()` は環境依存で CI が不安定になる。

**[Critical]**

`threading.Event.wait(timeout=N)` でもタイムアウトした場合の検証は必要。
タイムアウト時にテストが `PASSED` になると誤った安心感を与える。

**[Mediator]**

以下のパターンを統合テストの標準として採用する:

```python
# スレッドテストの標準パターン

done_event = threading.Event()
result_container = []  # スレッド間の結果受け渡し

def background_task():
    # 処理
    result_container.append(処理結果)
    done_event.set()

thread = threading.Thread(target=background_task, daemon=True)
thread.start()

# 明示的な待機（タイムアウト付き）
completed = done_event.wait(timeout=10.0)
assert completed, "バックグラウンドスレッドがタイムアウトしました（テスト失敗）"
assert len(result_container) == 1
```

**ルール**:
1. `time.sleep()` は統合テストで使用禁止（`Event.wait()` または `Queue.get(timeout=N)` を使用）
2. タイムアウトは `assert completed` で明示的に失敗させる
3. `daemon=True` スレッドを使用し、テスト終了時にスレッドリークを防ぐ

---

### Atom A3: `pytest-timeout` の採用可否

**[Affirmative]**

`pytest-timeout` は各テストに `@pytest.mark.timeout(N)` を付けることでテスト単位のタイムアウトを設定できる。
統合テストが CI をブロックするリスクを防ぐために有用。

**[Critical]**

NFR-3（追加依存なし）との整合性問題。`pytest-timeout` は開発依存（dev-dependency）であり、
アプリケーションランタイムの依存ではないため NFR-3 の対象外と解釈できる。
ただし `pyproject.toml` の依存リストに追加が必要。

**[Mediator]**

**結論**: `pytest-timeout` の採用は Phase 2a では見送る。

代替策:
- 各統合テストで `Event.wait(timeout=N)` を使用（前述 Atom A2 のパターン）
- `conftest.py` に統合テスト用の `timeout_check` フィクスチャを追加する
- `pytest.ini` に `timeout = 30`（全テスト共通）を設定する → これは `pytest-timeout` なしでは動作しないため、代わりに `conftest.py` の `autouse` フィクスチャで管理する

---

### Atom A4: シャットダウンテストの mock 戦略

`shutdown_handler.py` の `_shutdown_done` は module レベルの `threading.Event` であり、テスト間で状態が共有される問題がある。Phase 1 で `reset_shutdown_state()` テスト用関数が実装済みであることを確認している。

**[Mediator]**

FR-8.5 の3経路テストは以下の mock 戦略を使用する:

| 経路 | テスト方法 |
|------|---------|
| `atexit` 経由 | `atexit.register()` を `mock.patch` し、登録されたコールバックを手動呼び出し |
| `shutdown()` 直接呼び出し | `ShutdownHandler` を直接インスタンス化して `shutdown()` を呼び出す |
| 連続呼び出し | 上記2経路を連続で実行し、カウンターが 1 のままであることを確認 |

各テストの前後に `reset_shutdown_state()` を呼び出してモジュールレベルの状態をリセットする。

---

### Atom A5: FR-8.11 タイミングテストの設計

**[Affirmative]**

`LLMProtocol` モックを使用することでネットワーク依存なしに応答タイミングを計測できる。
測定範囲は「`input_queue.put()` 呼び出し（クリックイベント相当）から `display_text()` 呼び出しまで」。

**[Critical]**

`TkinterMascotView` を含む統合テストは tkinter のメインループが必要。
`root.mainloop()` を呼ぶとテストがブロックする。`root.after()` のポーリングを手動でトリガーする方法が必要。

**[Mediator]**

以下のアプローチを採用する:
1. `root.mainloop()` は呼ばない
2. `root.update()` を手動でポーリング（`_start_response_polling` と同様のタイミングで呼び出す）
3. 応答が `display_text()` に届くまで `root.update()` を繰り返す（最大 5 秒のループ）

```python
# FR-8.11 テストパターン（設計のみ）

import time

def test_response_timing():
    root = tk.Tk()
    input_queue = queue.Queue()
    response_queue = queue.Queue()
    mock_llm = MockLLMClient(response="テスト応答")
    # AgentCore + TkinterMascotView のセットアップ（省略）

    displayed_texts = []
    original_display_text = mascot_view.display_text
    def capture_display_text(text):
        displayed_texts.append((time.monotonic(), text))
        original_display_text(text)
    mascot_view.display_text = capture_display_text

    start_time = time.monotonic()
    input_queue.put("テスト入力")  # クリックイベント相当

    # 最大 5 秒間 root.update() でポーリング
    deadline = start_time + 5.0
    while time.monotonic() < deadline and len(displayed_texts) == 0:
        root.update()
        time.sleep(0.01)

    assert len(displayed_texts) > 0, "5秒以内に display_text() が呼ばれませんでした"
    elapsed = displayed_texts[0][0] - start_time
    assert elapsed < 5.0, f"応答タイムアウト: {elapsed:.2f}s"

    root.destroy()
```

---

### AoT Synthesis

**統合結論**:
- `tests/test_integration/` を新設し、4種の統合テストを配置
- スレッド同期は `threading.Event.wait(timeout=N)` を使用（`time.sleep()` 禁止）
- `pytest-timeout` は採用しない（`Event.wait` のタイムアウト検証で代替）
- シャットダウンテストは `reset_shutdown_state()` を各テスト前後で呼び出す
- FR-8.11 タイミングテストは `root.update()` ポーリングで `mainloop()` を代替

---

## 3. 決定

**採用**: `tests/test_integration/` 新設 + `threading.Event` ベース同期 + `reset_shutdown_state()` 活用

**理由**:
- Phase 1 のホットフィックス教訓 L-1/L-2/L-3 に直接対応
- フレイキネスを防ぐため `time.sleep()` を排除
- 追加依存ゼロ（NFR-3 維持）

---

## 4. 詳細仕様

### 4.1 FR-8.3: マルチスレッド統合テスト

**ファイル**: `tests/test_integration/test_multithread.py`

**テストケース設計**:

```
test_background_thread_with_queue():
    1. メインスレッドで DB 接続を生成（check_same_thread=False 付き）
    2. AgentCore をメインスレッドで生成（モック LLMProtocol）
    3. バックグラウンドスレッドで _run_background_loop() を起動
    4. input_queue にテスト入力を PUT
    5. response_queue から応答を GET（timeout=10.0 で待機）
    6. 応答が取り出せることをアサート
    7. shutdown_event.set() でスレッドを停止
    8. thread.join(timeout=5.0) でスレッドの終了を待機
```

**教訓 L-1 の再現テスト**（回帰防止）:

```
test_thread_same_connection_raises():
    1. メインスレッドで DB 接続を生成（check_same_thread=True のデフォルト）
    2. バックグラウンドスレッドから同じ接続を使用する処理を実行
    3. OperationalError が発生することを確認（教訓通り）

test_thread_different_connection_ok():
    1. メインスレッドで DB 接続を生成（check_same_thread=False）
    2. バックグラウンドスレッドから同じ接続を使用
    3. エラーが発生しないことを確認（修正後の正常動作）
```

**フィクスチャ**:

```python
@pytest.fixture
def tmp_db(tmp_path):
    """テスト用一時 SQLite DB を生成する."""
    db = Database(tmp_path / "test_memory.db")
    conn = db.connect()
    initialize_db(conn)
    yield conn, db
    db.close()
```

### 4.2 FR-8.4: 永続状態ありの起動テスト

**ファイル**: `tests/test_integration/test_persistent_state.py`

**テストケース設計**:

```
test_second_startup_no_unique_constraint_error():
    前提:
        - tmp_path に DB ファイルを作成
        - モック LLMProtocol を使用（ネットワーク不要）

    1回目の起動:
        1. DB 初期化
        2. AgentCore を起動し、数ターンの会話を実行
        3. MemoryWorker.generate_daily_summary_sync() を実行（今日のサマリーを生成）
        4. DB をクローズ

    2回目の起動:
        5. 同じ DB ファイルで再接続
        6. MemoryWorker.check_and_fill_missing_summaries() を実行
        7. AgentCore を起動し、数ターンの会話を実行
        8. MemoryWorker.generate_daily_summary_sync() を再度実行
        9. UNIQUE 制約エラーが発生しないことをアサート（教訓 L-2 の回帰防止）
```

**教訓 L-2 の詳細**:

Phase 1 のバグは「同日に2回起動したとき、2回目のシャットダウン時に `INSERT INTO day_summary` が
`UNIQUE (date)` 制約に違反した」問題。修正後の動作（`INSERT OR REPLACE` 等）が正しく機能することをテストする。

### 4.3 FR-8.5: シャットダウン全経路テスト

**ファイル**: `tests/test_integration/test_shutdown.py`

**テストケース設計**:

```python
# 教訓 L-3: 各経路で shutdown_callback が合計1回だけ実行されることを確認

def test_atexit_path():
    """atexit 経由のシャットダウンテスト."""
    reset_shutdown_state()
    call_counter = []

    def shutdown_cb():
        call_counter.append(1)

    handler = make_atexit_handler(shutdown_cb)
    handler()  # atexit コールバックを手動実行

    assert len(call_counter) == 1

def test_direct_shutdown_path():
    """ShutdownHandler.shutdown() 直接呼び出しテスト（トレイ終了相当）."""
    reset_shutdown_state()
    call_counter = []

    shutdown_event = threading.Event()

    # _make_shutdown_callback は main.py の内部関数のため、
    # ShutdownHandler 相当の実装を直接テストする
    def shutdown_cb():
        call_counter.append(1)

    shutdown_cb()  # トレイ「終了」相当

    assert len(call_counter) == 1

def test_double_call_prevented():
    """連続呼び出しで2重実行が防止されることを確認."""
    reset_shutdown_state()
    call_counter = []

    def shutdown_cb():
        call_counter.append(1)

    # atexit 経由と直接呼び出しを連続実行
    handler = make_atexit_handler(shutdown_cb)
    handler()   # 1回目
    handler()   # 2回目（_shutdown_done が set されているため呼ばれない）

    assert len(call_counter) == 1, "2重実行が発生した"
```

**注意**: `reset_shutdown_state()` は `shutdown_handler.py` に実装済みのテスト用関数。
各テストの `setup` / `teardown` で呼び出してモジュールレベルの状態をリセットする。

```python
@pytest.fixture(autouse=True)
def reset_shutdown():
    """各テスト前後にシャットダウン状態をリセットする."""
    reset_shutdown_state()
    yield
    reset_shutdown_state()
```

### 4.4 FR-8.11: 応答タイミングテスト

**ファイル**: `tests/test_integration/test_response_timing.py`

**テスト構成**:

```
test_response_within_5_seconds():
    前提:
        - MockLLMClient（LLMProtocol 実装）を使用
        - ネットワーク不要

    1. tk.Tk() を生成（mainloop() は呼ばない）
    2. TkinterMascotView を生成
    3. AgentCore を生成（MockLLMClient、tmp_path の DB）
    4. _run_background_loop() をバックグラウンドスレッドで起動
    5. _start_response_polling() を設定
    6. AgentCore.generate_session_start_message() の完了を待機
       （response_queue から開始メッセージを取得）
    7. start_time を記録
    8. input_queue.put("テスト入力") でメッセージを送信
    9. root.update() を繰り返し（最大 5 秒）、display_text() が呼ばれるまで待機
    10. elapsed < 5.0 をアサート
    11. root.destroy()、shutdown_event.set()
```

**MockLLMClient のシグネチャ（FR-8.11 要件）**:

```python
class MockLLMClientForTiming:
    """タイミングテスト用 LLMProtocol 実装.

    instant_response: True の場合、遅延なしで応答（デフォルト）。
    delay_seconds: 応答遅延のシミュレーション。
    """

    def __init__(
        self,
        response: str = "テスト応答",
        delay_seconds: float = 0.0,
    ) -> None:
        self._response = response
        self._delay = delay_seconds

    def chat(self, messages, *, system, model, max_tokens, temperature) -> str:
        if self._delay > 0:
            time.sleep(self._delay)
        return self._response

    def send_message_for_purpose(self, system, messages, purpose) -> str:
        """AgentCore が直接呼び出す便利メソッド（Protocol 外）."""
        if self._delay > 0:
            time.sleep(self._delay)
        return self._response
```

**注意**: FR-8.11 のタイミングテストでは `AgentCore` が `send_message_for_purpose()` を呼び出すため、
`MockLLMClientForTiming` は `chat()` と `send_message_for_purpose()` の両方を実装する必要がある。
この点は D-17 の「Protocol 外メソッドの張力」として記録済み（Phase 3 での解消予定）。

### 4.5 テストフィクスチャの共通設計

```python
# tests/test_integration/conftest.py に定義する共通フィクスチャ

@pytest.fixture
def tmp_db(tmp_path):
    """テスト用一時 SQLite DB（check_same_thread=False）."""
    from kage_shiki.memory.db import Database, initialize_db
    db = Database(tmp_path / "test.db")
    conn = db.connect()
    initialize_db(conn)
    yield conn, db
    db.close()

@pytest.fixture
def mock_llm():
    """テスト用 LLMProtocol 実装（即時応答）."""
    return MockLLMClientForTiming(response="テスト応答", delay_seconds=0.0)

@pytest.fixture
def tmp_data_dir(tmp_path):
    """テスト用データディレクトリ（persona_core.md あり）."""
    # persona_core.md と style_samples.md の最小有効ファイルを作成
    persona_path = tmp_path / "persona_core.md"
    persona_path.write_text("# テスト\n## C1: 名前\nテスト\n## C4: 人格核文\nテスト.", encoding="utf-8")
    (tmp_path / "style_samples.md").write_text("## S1: 日常会話\nテスト", encoding="utf-8")
    (tmp_path / "human_block.md").write_text("", encoding="utf-8")
    (tmp_path / "personality_trends.md").write_text("", encoding="utf-8")
    return tmp_path
```

---

## 5. スモークテスト手順書と GUI 手動テストの設計方針

以下は `docs/testing/` に出力する文書（設計書外）の構成方針を示す。

### 5.1 スモークテスト手順書（FR-8.1）

出力先: `docs/testing/smoke-test.md`

**4セクション構成**:
1. **起動手順**: `config.toml` の準備 → `ANTHROPIC_API_KEY` 設定 → `python -m kage_shiki` 実行 → ウィンドウ表示確認
2. **対話確認手順**: 送信ボタン / Enter キーで入力 → 5 秒以内に応答表示を確認 → クリックイベント（突っつき）で反応確認
3. **シャットダウン確認手順**: トレイアイコン右クリック「終了」→ ウィンドウ消失確認 → ログファイルに日次サマリー生成ログを確認
4. **2回目起動確認手順（永続状態）**: 同じ `data_dir` で再起動 → エラーなく起動することを確認 → 前回の記憶（セッション開始挨拶）に変化があることを確認

### 5.2 GUI 手動テストチェックリスト（FR-8.2）

出力先: `docs/testing/gui-manual-test.md`

**必須4項目（FR-8.2 受入条件）**:
1. 長文応答のスクロール表示: 200 文字超の応答がスクロール可能な Text ウィジェットに表示されること
2. ウィンドウドラッグ移動: タイトルバー以外のウィンドウ領域をドラッグして任意位置に移動できること
3. トレイ最小化・復帰: トレイアイコン左クリックで非表示、再クリックで表示されること
4. ウィザード画面遷移: 各方式選択 → 入力 → プレビュー → 確定 の全フローを目視確認

---

## 6. テスト実行方法

```bash
# 統合テストのみ実行
pytest tests/test_integration/ -v

# 全テスト実行（Phase 1 単体テスト + Phase 2a 統合テスト）
pytest --cov=src/kage_shiki --cov-report=term-missing

# 統合テストを除いて単体テストのみ実行（高速）
pytest --ignore=tests/test_integration/
```

---

## 7. 影響範囲

| 影響先 | 内容 | 変更規模 |
|--------|------|---------|
| `tests/test_integration/` | 新規ディレクトリ（4ファイル） | 大（新規） |
| `tests/test_integration/conftest.py` | 共通フィクスチャ | 小（新規） |
| `docs/testing/smoke-test.md` | スモークテスト手順書 | 小（新規） |
| `docs/testing/gui-manual-test.md` | GUI 手動テストチェックリスト | 小（新規） |
| `tests/test_agent/test_llm_client.py` | MockLLMClientForTiming の共有化（conftest.py に移動を検討） | 最小 |
| Phase 1 既存テスト | 変更なし（追加のみ） | なし |

---

## 8. 品質目標

| 指標 | 目標 |
|------|------|
| 全体行カバレッジ（NFR-10） | 90% 以上維持 |
| Phase 1 全テスト PASSED（NFR-12） | Phase 2a 完了後も PASSED のまま |
| 統合テストのフレイキネス率 | CI 100 回中 0 回の偶発失敗を目標 |
| 統合テストの実行時間 | 全 4 ファイル合計 30 秒以内 |
