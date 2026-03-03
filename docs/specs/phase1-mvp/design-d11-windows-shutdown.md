# D-11: Windows プロセス終了シグナルの捕捉方式

**決定対象**: requirements.md Section 8 D-11 — Windows 環境での安全なシャットダウン実装方式（FR-3.9）
**関連 FR**: FR-3.8（atexit フック）, FR-3.9（プロセス終了シグナル捕捉）, FR-7.5（サマリー生成失敗時の安全性）
**関連 NFR**: NFR-1（Windows 11）, NFR-3（外部依存最小化）, NFR-9（データ安全性）
**ステータス**: 提案（承認待ち）

---

## 1. コンテキスト

### なぜこの決定が必要か

影式の記憶システムは「シャットダウン時に当日の `observations` から日次サマリーを生成して `day_summary` に保存する」2層防御設計を採用している（FR-3.8, FR-3.9）。

**Layer 1: atexit フック（FR-3.8）**
Python の `atexit` モジュールは、`sys.exit()` 呼び出しや正常終了時にコールバックを実行する。pystray の「終了」メニュー → `sys.exit()` → `atexit` の流れは Phase 1 で確実に動作する正常終了パス。

**Layer 2: OS シグナル捕捉（FR-3.9）**
atexit は `os._exit()` や強制終了では実行されない。OS レベルのシグナルを捕捉してサマリー生成を実行する必要がある。

**Windows の制約**

| シグナル | Unix | Windows での動作 |
|---------|------|----------------|
| `SIGTERM` | プロセス終了要求 | **Python の `signal` モジュールでハンドラ登録できるが、Windows ではプロセスに SIGTERM を送る一般的な手段がない**。`os.kill(pid, signal.SIGTERM)` でプロセス自身に送ることはできるが、外部からのシャットダウン（Windows シャットダウン、コンソールクローズ）では発生しない |
| `SIGINT` | Ctrl+C | Python `signal.SIGINT` で捕捉可能 |
| `SIGBREAK` | Ctrl+Break | Windows のみ存在。Python `signal.SIGBREAK` で捕捉可能 |
| CTRL_CLOSE_EVENT | コンソールウィンドウ×ボタン | `SetConsoleCtrlHandler` で捕捉 |
| CTRL_SHUTDOWN_EVENT | Windows シャットダウン | `SetConsoleCtrlHandler` で捕捉 |
| CTRL_LOGOFF_EVENT | ユーザーログオフ | `SetConsoleCtrlHandler` で捕捉 |

requirements.md Section 9 の Critical 指摘「SIGTERM は Windows で未サポート」が FR-3.9 に反映済みであり、Windows 固有の実装が必要。

### GUI アプリケーションでのコンソールハンドラの適用範囲

影式 Phase 1 は tkinter GUI アプリケーションである。Windows では GUI アプリケーションはコンソールウィンドウを持たない場合がある（PyInstaller でビルドした場合など）。

ただし **開発実行時**（`python main.py` による起動）はコンソールが存在する。コンソールクローズ（×ボタン）や Windows シャットダウン時には `SetConsoleCtrlHandler` のコールバックが呼ばれる。

Phase 1 の開発・テスト環境では主にコンソール付きで動作するため、`SetConsoleCtrlHandler` は有効に機能する。

---

## 2. 選択肢分析

### 選択肢 A: ctypes で SetConsoleCtrlHandler を登録

Python 標準ライブラリの `ctypes` を使用して Windows API の `SetConsoleCtrlHandler` を直接呼び出す。

```python
# 擬似コード: ctypes による SetConsoleCtrlHandler 登録
import ctypes
import ctypes.wintypes

# ハンドラ関数の型定義
HandlerRoutine = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.DWORD)

CTRL_C_EVENT       = 0
CTRL_BREAK_EVENT   = 1
CTRL_CLOSE_EVENT   = 2
CTRL_LOGOFF_EVENT  = 5
CTRL_SHUTDOWN_EVENT = 6

def _ctrl_handler(ctrl_type: int) -> bool:
    """
    Windows コントロールイベントハンドラ。
    返り値 True = イベントを処理済み（チェーンの後続ハンドラを呼ばない）
    返り値 False = デフォルトのハンドラに委譲
    """
    if ctrl_type in (CTRL_CLOSE_EVENT, CTRL_SHUTDOWN_EVENT, CTRL_LOGOFF_EVENT):
        # 日次サマリー生成（ブロッキング処理を簡潔に実行）
        _run_shutdown_summary()
        return False  # デフォルト処理（プロセス終了）に委譲
    return False

_handler_ref = HandlerRoutine(_ctrl_handler)  # GC 対策のため参照を保持

def register_ctrl_handler():
    kernel32 = ctypes.windll.kernel32
    result = kernel32.SetConsoleCtrlHandler(_handler_ref, True)
    if not result:
        # 登録失敗（コンソールなし環境では失敗する可能性）
        # logging.warning("SetConsoleCtrlHandler の登録に失敗しました")
        pass
```

- **メリット**:
  - 追加の外部依存ゼロ（標準ライブラリ `ctypes` のみ）
  - NFR-3（外部依存最小化）に完全適合
  - CTRL_CLOSE_EVENT（コンソール×ボタン）、CTRL_SHUTDOWN_EVENT（Windows シャットダウン）、CTRL_LOGOFF_EVENT（ログオフ）を捕捉できる
  - Windows API 直接呼び出しのため、pywin32 と同等の機能を追加依存なしで実現

- **デメリット**:
  - ctypes の型定義が冗長で、誤りやすい
  - ハンドラ関数のライフタイム管理が必要（`_handler_ref` を GC されないよう参照保持）
  - Windows 専用コードのため、将来的な Mac/Linux 対応時（現時点では計画外）に除外処理が必要
  - コンソールなし環境（GUI 専用ビルド）では `SetConsoleCtrlHandler` が機能しない

### 選択肢 B: win32api.SetConsoleCtrlHandler（pywin32 依存）

`pywin32` パッケージの `win32api.SetConsoleCtrlHandler` を使用する。

```python
# 擬似コード（pywin32 必要）
import win32api
import win32con

def _ctrl_handler(ctrl_type):
    if ctrl_type in (win32con.CTRL_CLOSE_EVENT, win32con.CTRL_SHUTDOWN_EVENT):
        _run_shutdown_summary()
        return False
    return False

win32api.SetConsoleCtrlHandler(_ctrl_handler, True)
```

- **メリット**:
  - ctypes より可読性が高い
  - pywin32 は Windows 開発で広く使われており、安定している

- **デメリット**:
  - **NFR-3 に反する**。pywin32 は外部依存であり、requirements.md で「pystray, anthropic のみ」と定義された依存範囲を超える
  - PyInstaller でのバンドル時に pywin32 のビルドが複雑になる
  - ctypes で同等の機能を実現できるため、追加依存は正当化できない

### 選択肢 C: atexit + signal.signal(SIGTERM/SIGINT) のみ

Python 標準の `atexit` と `signal` モジュールのみで対応する。

```python
# 擬似コード
import atexit
import signal

atexit.register(_run_shutdown_summary)

def _sigint_handler(signum, frame):
    _run_shutdown_summary()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    raise KeyboardInterrupt

signal.signal(signal.SIGINT, _sigint_handler)
```

- **メリット**:
  - 実装がシンプル
  - クロスプラットフォーム（Windows/Mac/Linux）

- **デメリット**:
  - **Windows では CTRL_CLOSE_EVENT と CTRL_SHUTDOWN_EVENT を捕捉できない**
  - ユーザーがコンソールを×ボタンで閉じた場合、atexit は実行されるが `signal.SIGTERM` は発火しない（Windows ではプロセスが即座に強制終了される）
  - FR-3.9 の「CTRL_CLOSE_EVENT / CTRL_SHUTDOWN_EVENT を捕捉し、サマリー生成を試行する」要件を満たせない

### 選択肢 D: ctypes による SetConsoleCtrlHandler + atexit の二重化

選択肢 A（ctypes）と atexit（Layer 1 として既に FR-3.8 で確定）を組み合わせる。FR-3.8 と FR-3.9 が互いに補完し合う2層防御。

```
Layer 1: atexit（FR-3.8）
  → 正常終了（sys.exit(), pystray「終了」メニュー）で確実に動作
  → os._exit() では実行されない

Layer 2: SetConsoleCtrlHandler（FR-3.9、D-11 の決定事項）
  → CTRL_CLOSE_EVENT（コンソール×）、CTRL_SHUTDOWN_EVENT（Windows シャットダウン）で実行
  → atexit が実行されない強制終了時のフォールバック
```

- **メリット**:
  - 2層防御により、正常終了・コンソールクローズ・OS シャットダウン全てをカバー
  - atexit の二重実行を防ぐフラグ管理が必要だが、設計はシンプル
  - NFR-3 適合（追加外部依存なし）

- **デメリット**:
  - 選択肢 A に加えてサマリー生成の2重実行防止フラグが必要
  - コンソールなし環境（GUI 専用ビルド）では Layer 2 が機能しないが、Layer 1（atexit）がカバー

---

## 3. Three Agents Perspective

**[Affirmative]（推進者）**:

選択肢 D（ctypes + atexit の二重化）を強く推す。US-5「会話記録が失われないことを確信したい」はプロダクトの核心要件であり、2層防御は設計として正当。ctypes の型定義が冗長という批判はあるが、一度書いてしまえばメンテナンスは不要であり、NFR-3（外部依存最小化）を守りつつ最高の安全性を確保できる。`_handler_ref` のライフタイム管理も、モジュールレベルの変数として保持すれば問題ない。

**[Critical]（批判者）**:

ctypes 実装の複雑さを過小評価すべきでない。`WINFUNCTYPE` によるコールバック型定義、`windll.kernel32` 呼び出し、GC からの参照保護など、誤実装のポイントが多い。特に `SetConsoleCtrlHandler` のコールバックは **別スレッド**（Windows システムスレッド）で呼ばれるため、スレッドセーフでない操作（SQLite への書き込み、Python 非同期コードの呼び出し）には注意が必要。

また、tkinter GUI アプリケーションを PyInstaller で `--noconsole` フラグでビルドした場合、コンソールハンドラは機能しない。Layer 2 が無効になるケースを正直に仕様に記載すべき。

ただし Layer 1（atexit + pystray「終了」メニュー）は確実に動作するため、Layer 2 が無効になっても Day 1 の最悪ケースは「次回起動時に欠損補完（FR-3.10）が動作する」であり、データは失われない。

**[Mediator]（調停者）**:

選択肢 D（ctypes + atexit 二重化）を採用するが、ctypes のスレッドセーフ問題に対する対処を仕様に明記する。

具体的には、`SetConsoleCtrlHandler` のコールバック内では asyncio や tkinter を直接呼び出さず、スレッドセーフな同期プリミティブ（`threading.Event`）を使ってメインスレッドに通知するパターンを採用する。また、2重実行防止フラグ（`threading.Event` で実装）を必ず設ける。

コンソールなし環境での Layer 2 非機能は仕様上の既知制限として文書化し、Layer 1（atexit）による保護が前提であることを明記する。

**採用: 選択肢 D — ctypes + atexit の二重化**

---

## 4. 決定

**採用**: 選択肢 D — ctypes による SetConsoleCtrlHandler + atexit フック（FR-3.8）の2層防御

**理由**:
1. US-5（会話記録の安全性）を最大限に保護する2層防御設計
2. NFR-3（外部依存最小化）に適合（追加パッケージ不要）
3. Windows 11 での正常終了・コンソールクローズ・OS シャットダウン全てをカバー
4. Layer 2 が無効な場合でも Layer 1（atexit）が機能するため、実用上の安全性は確保される

---

## 5. 詳細仕様

### 5.1 捕捉するイベントと対応

| イベント種別 | ctypes 定数値 | 発火タイミング | 対応 |
|------------|-------------|--------------|------|
| `CTRL_C_EVENT` | 0 | Ctrl+C | デフォルトに委譲（atexit が動作） |
| `CTRL_BREAK_EVENT` | 1 | Ctrl+Break | デフォルトに委譲（atexit が動作） |
| `CTRL_CLOSE_EVENT` | 2 | コンソールウィンドウ×ボタン | サマリー生成を試行後、デフォルト委譲 |
| `CTRL_LOGOFF_EVENT` | 5 | ユーザーログオフ | サマリー生成を試行後、デフォルト委譲 |
| `CTRL_SHUTDOWN_EVENT` | 6 | Windows シャットダウン | サマリー生成を試行後、デフォルト委譲 |

**注**: CTRL_CLOSE_EVENT / CTRL_LOGOFF_EVENT / CTRL_SHUTDOWN_EVENT のハンドラには、Windows から処理時間の制限が課される（CTRL_SHUTDOWN_EVENT は約5秒）。サマリー生成はこの制限内に完了できるよう設計する必要がある。

> **Note**: シャットダウン時のサマリー生成は `day_summary` テーブルへの INSERT であり、`observations` への書き込みは発生しない。したがって D-4 の FTS5 INSERT トリガーはシャットダウン処理中には動作しない。

### 5.2 実装仕様（Python 擬似コード）

```python
# 擬似コード: shutdown_handler.py
import ctypes
import ctypes.wintypes
import threading
import logging

logger = logging.getLogger(__name__)

# Windows コントロールイベント定数
CTRL_C_EVENT        = 0
CTRL_BREAK_EVENT    = 1
CTRL_CLOSE_EVENT    = 2
CTRL_LOGOFF_EVENT   = 5
CTRL_SHUTDOWN_EVENT = 6

# Windows API 型定義
# BOOL WINAPI HandlerRoutine(_In_ DWORD dwCtrlType)
_HandlerRoutine = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.DWORD)

# 2重実行防止フラグ（atexit と SetConsoleCtrlHandler の両方から呼ばれるケースへの対策）
_shutdown_done = threading.Event()

# コールバック関数への参照保持（GC 対策。モジュールレベルで保持が必須）
_ctrl_handler_ref: _HandlerRoutine | None = None


def _make_ctrl_handler(shutdown_callback):
    """
    shutdown_callback: 引数なし・戻り値なしの同期関数。
    日次サマリー生成を実行する関数を渡す。
    """
    def handler(ctrl_type: int) -> bool:
        if ctrl_type in (CTRL_CLOSE_EVENT, CTRL_LOGOFF_EVENT, CTRL_SHUTDOWN_EVENT):
            if not _shutdown_done.is_set():
                _shutdown_done.set()
                logger.info(f"Windows コントロールイベント受信: ctrl_type={ctrl_type}")
                try:
                    shutdown_callback()
                except Exception as e:
                    logger.error(f"シャットダウン処理でエラー: {e}")
        # False を返すことで、デフォルトのハンドラ（プロセス終了）に委譲する
        return False

    return _HandlerRoutine(handler)


def register_windows_ctrl_handler(shutdown_callback) -> bool:
    """
    SetConsoleCtrlHandler を登録する。
    戻り値: 登録成功なら True、失敗（コンソールなし環境等）なら False。
    """
    global _ctrl_handler_ref

    _ctrl_handler_ref = _make_ctrl_handler(shutdown_callback)
    kernel32 = ctypes.windll.kernel32
    result = kernel32.SetConsoleCtrlHandler(_ctrl_handler_ref, True)
    if result:
        logger.info("Windows SetConsoleCtrlHandler 登録完了")
        return True
    else:
        error_code = kernel32.GetLastError()
        logger.warning(
            f"SetConsoleCtrlHandler の登録に失敗しました (GetLastError={error_code}). "
            "コンソールなし環境での動作かもしれません。atexit（Layer 1）が保護します。"
        )
        return False


def make_atexit_handler(shutdown_callback):
    """
    atexit 用のラッパー。2重実行防止フラグでガードする。
    """
    def atexit_handler():
        if not _shutdown_done.is_set():
            _shutdown_done.set()
            logger.info("atexit ハンドラ実行")
            try:
                shutdown_callback()
            except Exception as e:
                logger.error(f"atexit シャットダウン処理でエラー: {e}")

    return atexit_handler
```

### 5.3 アプリケーション初期化での登録

```python
# 擬似コード: main.py または app.py での登録
import atexit
from shutdown_handler import register_windows_ctrl_handler, make_atexit_handler

def run_shutdown_summary():
    """
    実際の日次サマリー生成処理。
    MemoryWorker の同期版メソッドを呼び出す。
    注意: この関数は tkinter メインスレッドとは別スレッドから呼ばれる可能性がある。
    SQLite への書き込みは WAL モードと適切なコネクション管理で安全に扱う。
    """
    # memory_worker.generate_daily_summary_sync() のような同期関数を呼び出す
    pass

# atexit 登録（Layer 1）
atexit.register(make_atexit_handler(run_shutdown_summary))

# Windows SetConsoleCtrlHandler 登録（Layer 2）
# 失敗してもアプリケーションの起動は継続する（Layer 1 がバックアップ）
register_windows_ctrl_handler(run_shutdown_summary)
```

### 5.4 スレッドセーフ上の注意事項

`SetConsoleCtrlHandler` のコールバックは **Windows のシステムスレッド** から呼ばれる（アプリケーションのメインスレッドではない）。以下の制約を守ること:

- **禁止**: tkinter の `root.after()` や `root.destroy()` を直接呼び出す（デッドロックの可能性）
- **禁止**: asyncio のイベントループに直接アクセスする
- **許可**: スレッドセーフな操作（`threading.Event.set()`、ファイルへの書き込み、`queue.Queue.put()`）
- **許可**: SQLite への書き込み（WAL モードでは並行書き込みが安全）

```python
# 推奨パターン: コールバック内ではスレッドセーフな操作のみ実行
def run_shutdown_summary():
    # SQLite への書き込みは WAL モードでスレッドセーフ
    db_conn = sqlite3.connect(db_path, check_same_thread=False)
    # ... サマリー生成処理 ...
    db_conn.close()
```

### 5.5 コンソールなし環境（PyInstaller --noconsole）での動作

PyInstaller で `--noconsole`（または `--windowed`）オプションでビルドした場合:
- コンソールウィンドウが存在しない
- `SetConsoleCtrlHandler` の登録は失敗する（`GetLastError` でエラーコードが返る）
- CTRL_CLOSE_EVENT はそもそも発生しない
- Windows シャットダウン時は `WM_QUERYENDSESSION` / `WM_ENDSESSION` メッセージが tkinter ウィンドウに送られる

この場合の対応（Phase 1 の既知制限事項）:
- Layer 2（SetConsoleCtrlHandler）は機能しない
- Layer 1（atexit）は `sys.exit()` 経由の正常終了では機能する
- Windows シャットダウン時の保護は Phase 1 では未完全（FR-7.5 のログ+次回補完で対応）

**Phase 2 以降での改善**: tkinter の `protocol("WM_DELETE_WINDOW", ...)` と組み合わせた `WM_ENDSESSION` ハンドリングを検討する。

### 5.6 受入テスト観点

| テスト | 確認方法 |
|-------|---------|
| 正常終了（pystray「終了」メニュー） | atexit ハンドラが実行され day_summary が生成されること |
| Ctrl+C での終了 | atexit ハンドラが実行されること |
| `_shutdown_done` フラグの2重実行防止 | atexit と SetConsoleCtrlHandler ハンドラを両方呼んだとき、shutdown_callback が1回のみ実行されること（ユニットテスト） |
| SetConsoleCtrlHandler 登録失敗時の継続 | コンソールなし環境でも起動が継続されること（モック使用） |

---

## 6. 影響範囲

| 影響先 | 内容 |
|--------|------|
| 起動シーケンス（Section 5.5 Step 10-12 相当） | `register_windows_ctrl_handler` と `atexit.register` を起動時に呼ぶ |
| MemoryWorker | 同期版の日次サマリー生成メソッドを提供する必要がある（async/await なしで呼べる形） |
| SQLite コネクション管理 | `check_same_thread=False` での接続か、シャットダウン専用コネクションを用意する |
| FR-3.8 との関係 | Layer 1。atexit で確実に動作する正常終了パス（設計変更なし） |
| FR-3.9 との関係 | Layer 2。本設計文書が実装方式を決定（ctypes + SetConsoleCtrlHandler） |
| NFR-3（外部依存） | ctypes は標準ライブラリのため追加依存ゼロ |
| NFR-9（データ安全性） | 2層防御により、主要なシャットダウンシナリオでサマリー生成が試行される |

---

## 参照

- requirements.md Section 8 D-11、FR-3.8、FR-3.9、Section 9（Critical 6: SIGTERM は Windows で未サポート）
- docs/memos/middle-draft/04-unified-design.md「シャットダウン時（2層防御）」
- docs/memos/middle-draft/01-memory-system.md「シャットダウン時（2層防御）」
- [Windows SetConsoleCtrlHandler 公式ドキュメント](https://learn.microsoft.com/ja-jp/windows/console/setconsolectrlhandler)
- [Python ctypes 公式ドキュメント](https://docs.python.org/ja/3/library/ctypes.html)
- [Python signal モジュール — Windows での注意事項](https://docs.python.org/ja/3/library/signal.html#signal.signal)
