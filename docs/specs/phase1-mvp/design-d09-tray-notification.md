# D-9: トレイ通知の実現可否

**決定対象**: requirements.md Section 8 — D-9「トレイ通知の実現可否（pystray バルーン通知の Windows 11 対応調査）」
**関連 FR**: FR-7.2
**ステータス**: 提案（承認待ち）

---

## 1. コンテキスト

### 1.1 なぜこの決定が必要か

FR-7.2 は「認証エラー（401/403）時にウィンドウ内メッセージ表示またはシステムトレイ通知でユーザーに案内する」と定義しており、通知手段の決定を本設計項目に委譲している。

マスコットウィンドウが非表示（トレイ格納中）の状態で API 認証エラーが発生した場合、ユーザーに通知する手段が `display_text()` だけでは不十分である。しかし、通知ライブラリの追加は NFR-3（外部依存最小化）と衝突する可能性がある。

### 1.2 通知が必要なケースの絞り込み

「トレイ通知が必要になるシナリオ」を正確に定義する。

| シナリオ | ウィンドウ表示状態 | 対応方法 |
|---------|----------------|---------|
| API 認証エラー（通常対話中） | 表示中 | `display_text()` で十分 |
| API 認証エラー（トレイ格納中） | 非表示 | **ここで通知が必要** |
| API 一般失敗（通常対話中） | 表示中 | `display_text()` で十分 |
| API 一般失敗（トレイ格納中） | 非表示 | 次回表示時に通知でも許容（認証エラーより軽微） |

つまり、トレイ通知が必要になるのは「**マスコットがトレイ格納中に API 認証エラーが発生した場合**」に限定される。認証エラーはユーザーのアクション（環境変数の修正）なしには解消されないため、通知の価値が高い。

### 1.3 NFR-3 との兼ね合い

NFR-3: 外部依存最小化。許容する外部ライブラリは `tkinter`（標準）、`pystray`、`anthropic` のみ。

新しいライブラリ（win10toast、plyer 等）の追加は NFR-3 に抵触する。一方、`pystray` は既に採用済みであり、`pystray.Icon.notify()` がこの用途に使えるなら追加依存は不要となる。

---

## 2. 選択肢分析

### 選択肢 A: pystray の `Icon.notify()` を使用

pystray には `Icon.notify(message, title)` メソッドが存在する（pystray 0.19.5 以降で安定）。

- **概要**: `pystray.Icon.notify("API キーを確認してください", "影式")` を呼び出すことでトレイバルーン通知を表示する
- **メリット**:
  - 追加ライブラリ不要（NFR-3 に完全準拠）
  - Windows 10 では動作実績あり
  - pystray は既に採用済みのため統合コストが最小
- **デメリット**:
  - **Windows 11 互換性問題（Issue #112）**: `Icon.notify()` は Windows 11 でバルーン通知が表示されないことが報告されている。`Shell_NotifyIcon` API によるバルーンチップは Windows 11 ではトースト通知に変換されるが、システム通知設定によっては完全に抑制される
  - エラーは発生しないが通知も表示されない（Silent failure）という挙動が報告されている
  - ユーザー側の通知設定に依存するため、動作保証ができない

**Windows 11 での動作確認状況**（調査結果）:
- `Shell_NotifyIcon` の NIF_INFO フラグを使ったバルーンチップは Windows 11 に存在するが、デフォルト設定では通知センターに表示されない
- Windows 11 ではシステムトレイアイコン右クリック → 「通知設定」から個別に有効化が必要なケースがある
- pystray Issue #112 で報告された問題は「エラーなし・表示なし」の Silent failure

### 選択肢 B: win10toast / win11toast ライブラリを使用

`win10toast`（Python製 Windows トースト通知ライブラリ）または `win11toast`（WinRT API ベースの新世代ライブラリ）を追加する。

- **概要**: `win11toast.notify("影式", "API キーを確認してください")` でトースト通知を表示
- **メリット**:
  - Windows 11 のトースト通知（WinRT）に対応しており、信頼性が高い
  - `win11toast` は Windows 11 のネイティブ通知 API を直接使用
- **デメリット**:
  - **NFR-3 違反**: 新しい外部依存が増える
  - `win10toast` は Python 3.11 以降で動作しないという報告あり（Issue #112）
  - `win11toast` は WinRT を使うため Python 3.12 での動作安定性の確認が必要
  - パッケージのメンテナンス状況が不安定（`win10toast` は事実上メンテナンス停止）

### 選択肢 C: plyer の notification を使用

クロスプラットフォーム通知ライブラリ `plyer` の `notification.notify()` を使用する。

- **概要**: `plyer.notification.notify(title="影式", message="API キーを確認してください", timeout=10)` を呼び出す
- **メリット**:
  - プラットフォームを抽象化しており、Windows/Mac/Linux で動作する
  - 比較的メンテナンスが継続されている
- **デメリット**:
  - **NFR-3 違反**: 新しい外部依存が増える
  - Windows 11 では内部的に `win10toast` を呼び出すため、同様の互換性問題が発生する可能性がある
  - 依存が増えるわりに Windows 11 対応が改善されない可能性がある

### 選択肢 D: トレイ通知を見送り → ウィンドウ内表示のみ

トレイ通知は実装せず、認証エラーは「次回ウィンドウが表示されたタイミングで通知する」ことに留める。

- **概要**: 認証エラー発生時に内部フラグを立て、`MascotView.show()` が呼ばれた際に `display_text()` でエラーメッセージを表示する
- **メリット**:
  - 追加ライブラリ不要（NFR-3 に完全準拠）
  - Windows 11 の通知設定に依存しない
  - 実装がシンプル
- **デメリット**:
  - マスコットがトレイ格納中は通知が届かない。ユーザーが気づくまでに時間がかかる
  - 認証エラーで LLM が動かない状態が続いても、ユーザーが気づかない可能性がある
  - ただし「次回ウィンドウ表示時に通知する」遅延通知で実用的には許容範囲

---

## 3. Three Agents Perspective

**[Affirmative]**（推進者）:
選択肢 A（pystray の `notify()`）が最善。理由は3つある。まず NFR-3 に完全準拠する唯一の能動的通知手段である。次に Windows 11 での問題はユーザー側の通知設定次第であり、設定が正しければ動作する。最後に、「通知が表示されない場合の fallback として選択肢 D を組み合わせる」ことで両方の利点を活かせる。具体的には `notify()` を試みたうえで、次回 `show()` 時にも重ねて通知する二段構えとする。

**[Critical]**（批判者）:
pystray の Windows 11 問題は「Silent failure」であるため、コードが動いても通知が届かないケースが存在する。ユーザー体験として「API キーが間違っているのにマスコットが無言のまま」という状況が継続するのは大きなリスクである。特に認証エラーはユーザーのアクションなしに解消しないため、通知の信頼性が重要。選択肢 D の「遅延通知」は、ユーザーがマスコットを開いた瞬間にエラーメッセージが表示される形になり、ある意味で確実である。追加ライブラリの拒否反応は理解できるが、MVP 品質として許容できるのかを再考すべきだ。

**[Mediator]**（調停者）:
トレイ通知の「必要性」と「確実性」のバランスを整理する。

- **認証エラーの発生頻度**: API キーを一度正しく設定すれば、認証エラーは滅多に発生しない（キーの期限切れ、使用量上限、キーの変更時のみ）
- **遅延通知の許容性**: ユーザーが「なぜか会話が返ってこない」と感じてウィンドウを開けば、そこで通知される。この遅延は実用上許容範囲である
- **NFR-3 の重み**: 影式の品質目標はシンプルで依存が少ないこと。追加ライブラリ1つが技術的負債になるリスクは軽視できない

結論: **選択肢 A + D の組み合わせ**を採用する。

具体的には:
1. 認証エラー発生時に `pystray.Icon.notify()` を試みる（確実に動けばラッキー）
2. 同時に内部フラグ（`pending_error_message`）を立てる
3. 次回 `MascotView.show()` 時に `pending_error_message` があれば `display_text()` で表示する（遅延通知）

この組み合わせにより、pystray 通知が動作する環境では即時通知、動作しない環境では遅延通知となり、いずれの場合も最終的にユーザーに伝わる。

---

## 4. 決定

**採用**: 選択肢 A + D の組み合わせ（pystray 通知 + 遅延通知フォールバック）
**新規ライブラリ追加**: なし（NFR-3 準拠）

**理由**:
- pystray は既採用ライブラリであり NFR-3 に違反しない
- Windows 11 の Silent failure リスクを遅延通知（選択肢 D）でカバーする
- 認証エラーの発生頻度が低く、遅延通知でも実用上問題ない
- 追加ライブラリの技術的負債を避ける

---

## 5. 詳細仕様

### 5.1 通知フロー

```
API 認証エラー発生（HTTP 401/403）
    │
    ├─ 1. pystray.Icon.notify() を試みる
    │       （成功: Windows 11 通知設定が有効な場合に表示される）
    │       （失敗: Silent failure の場合はエラーなし・通知なし）
    │
    ├─ 2. 内部フラグを立てる
    │       error_notification_pending = True
    │       error_notification_message = EM-007-message
    │
    └─ 3. MascotView の表示状態を確認
            ├─ is_visible() == True
            │       → 即時 display_text(EM-007-message)
            │         error_notification_pending = False
            │
            └─ is_visible() == False
                    → フラグを保持（遅延通知待ち）

    [後続: MascotView.show() が呼ばれた時]
    error_notification_pending == True なら
        → display_text(EM-007-message)
        → error_notification_pending = False
```

### 5.2 pystray.Icon.notify() の呼び出し仕様

```
引数:
  message: str  — 通知本文
  title: str    — 通知タイトル（"影式" 固定）

呼び出し条件:
  - MascotView.is_visible() == False の時のみ呼び出す
  - MascotView.is_visible() == True の場合は display_text() のみ使用

例外処理:
  - notify() は例外を発生させないが、
    try/except Exception でガードする
  - 例外発生時はログに記録し、遅延通知フラグで対処
```

### 5.3 遅延通知フラグの管理

| 変数 | 型 | 説明 |
|------|-----|------|
| `error_notification_pending` | `bool` | 未通知のエラーがある場合 True |
| `error_notification_message` | `str` | 次回表示時に表示するメッセージ |

管理場所: `TkinterMascotView` または `AgentCore` のいずれかに持たせる。
推奨: `AgentCore`（エラーの発生箇所が AgentCore 内のため、状態管理をそこに集約する）

`MascotView.show()` 呼び出し時に `AgentCore` への通知コールバックをトリガーするか、`show()` 内部でポーリングする仕組みを実装フェーズで決定する。

### 5.4 通知するエラーの絞り込み

トレイ通知（または遅延通知）の対象は **EM-007（API 認証エラー）のみ** とする。

| エラーID | トレイ/遅延通知 | 理由 |
|---------|--------------|------|
| EM-001 | 不要 | 起動失敗なのでウィンドウがある |
| EM-006 | 不要 | 自動回復するため遅延通知不要 |
| EM-007 | **対象** | ユーザーアクション必要、かつトレイ中に発生しうる |
| EM-008 | 不要 | 自動バッファで回復するため通知不要 |
| その他 | 不要 | ウィンドウ表示中に発生するか、自動回復する |

### 5.5 Windows 11 通知設定の依存性

pystray の `Icon.notify()` が Windows 11 で動作するかどうかはユーザー側の設定に依存する。

**動作する条件**（推定）:
- Windows 11 の「通知とアクション」設定でシステムトレイ通知が有効になっている
- アプリ固有の通知設定が「影式」に対して許可されている

**README に記載すべき事項**（実装フェーズで README を作成する際に追記）:
```
Windows 11 でトレイ通知を受け取るには、
システム設定 → 通知 → 通知を有効にする
を確認してください。
設定に関わらず、影式ウィンドウを開いた際にもエラーが通知されます。
```

### 5.6 将来的な改善パス

Phase 2 以降でトレイ通知の信頼性を改善する場合:

| オプション | 条件 | 内容 |
|----------|------|------|
| ctypes + Shell_NotifyIconA | 標準ライブラリのみ | Win32 API を直接呼び出すことで pystray のバグを回避。ただし実装コストが高い |
| win11toast | Phase 2 での依存追加を許容 | WinRT ベースで Windows 11 対応。NFR-3 緩和が必要 |
| 現状維持 | 認証エラーが実運用で問題になった場合 | 遅延通知で実用上十分と判断されれば変更不要 |

Phase 1 では追加対応は不要。実際の運用で「通知が届かない」問題が顕在化した場合に Phase 2 で検討する。

---

## 6. 影響範囲

| 影響先 | 内容 |
|--------|------|
| `TkinterMascotView` | `show()` 時の遅延通知チェック処理 |
| `AgentCore` | `error_notification_pending` フラグの管理、認証エラー検出時の通知トリガー |
| `pystray.Icon` インスタンス | `notify()` 呼び出しの追加（既存の `show`/`hide` 処理への影響なし） |
| D-6（エラーメッセージ） | EM-007 のメッセージ文面を参照 |
| `requirements.md` FR-7.2 | 本設計が「通知手段」として参照される |
| README（実装フェーズ） | Windows 11 通知設定の注意事項を追記 |

Sources:
- [pystray - PyPI](https://pypi.org/project/pystray/)
- [Notifications don't work on Windows 11 · Issue #112 · moses-palmer/pystray](https://github.com/moses-palmer/pystray/issues/112)
- [Reference — pystray 0.19.5 documentation](https://pystray.readthedocs.io/en/latest/reference.html)
- [win11toast · PyPI](https://pypi.org/project/win11toast/)
- [How to show balloon tip message in Windows notification center (Windows 11)? - Microsoft Q&A](https://learn.microsoft.com/en-us/answers/questions/1362368/how-to-show-balloon-tip-message-in-windows-notific-)
