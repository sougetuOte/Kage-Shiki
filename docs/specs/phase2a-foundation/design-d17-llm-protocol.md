# D-17: LLMProtocol 設計

**決定対象**: requirements.md Section 9 D-17「LLMProtocol 抽出（限定スコープ）」
**関連 FR**: FR-8.6
**制約**: C-3（`AnthropicClient` の内部実装はリファクタリングしない）、S-1（Phase 2a は Protocol 定義のみ。第2実装は Phase 3）
**ステータス**: 承認済み
**作成日**: 2026-03-06

---

## 1. コンテキスト

Phase 1 では `AgentCore`、`MemoryWorker`、`WizardController` が `LLMClient`（Anthropic SDK 直結実装）に直接依存している。
Phase 3 で LocalLLM（Qwen3.5-9B 等）を追加する際、上位ロジックを変更せずに差し替えられるよう、
`LLMProtocol`（`typing.Protocol`）を追加して依存を抽象化する。

**現行の依存関係（Phase 1）**:

```
AgentCore ──────────────→ LLMClient (Anthropic 直結)
MemoryWorker ────────────→ LLMClient (Anthropic 直結)
WizardController ────────→ LLMClient (Anthropic 直結)
```

**Phase 2a 後の依存関係**:

```
AgentCore ──────────────→ LLMProtocol (抽象)
MemoryWorker ────────────→ LLMProtocol (抽象)
WizardController ────────→ LLMProtocol (抽象)
                                ↑
                         LLMClient (Anthropic) が実装（変更なし）
```

---

## 2. 設計上の問題：どのメソッドを Protocol に含めるか

`LLMClient` には2つの公開メソッドがある。

| メソッド | シグネチャ（概要） | `AppConfig` への依存 |
|---------|---------------|-------------------|
| `send_message()` | `(system, messages, model, max_tokens, temperature) -> str` | なし（引数で完結） |
| `send_message_for_purpose()` | `(system, messages, purpose) -> str` | `AppConfig` を内部参照 |

`send_message_for_purpose()` は `AppConfig` の `VALID_PURPOSES`、`get_max_tokens()`、`get_model()`、`get_temperature()` を内部で呼び出す。
これらはすべて Anthropic モデル体系と設定形式に依存した実装詳細である。

---

## 3. Three Agents Perspective

### AoT Decomposition

| Atom | 判断内容 | 依存 |
|------|----------|------|
| A1 | Protocol に含めるメソッドの選択 | なし |
| A2 | `AnthropicClient` への改名可否 | A1 |
| A3 | 型注釈変更の影響範囲 | A1 |

---

### Atom A1: Protocol に含めるメソッドの選択

**[Affirmative]**

`send_message()` のみを Protocol に含めるべきである。理由：
- `send_message_for_purpose()` は `AppConfig.VALID_PURPOSES` という Anthropic 固有の概念（purpose スロット）に依存しており、LocalLLM には同一の purpose 体系が存在しない可能性が高い
- `send_message()` はプリミティブな「LLM への送受信」だけを抽象化しており、どの実装でも同様に実装可能
- 将来の実装（LocalLLM）が `send_message_for_purpose()` を実装しようとすると、`AppConfig` への依存が強制される

**[Critical]**

`send_message_for_purpose()` を Protocol に含めない場合、呼び出し側（`AgentCore`、`WizardController`）が `send_message_for_purpose()` を直接呼んでいる箇所のリファクタリングが必要になる。
Phase 1 のコードを見ると `agent_core.py` の `generate_session_start_message()` と `process_turn()` はいずれも `send_message_for_purpose()` を呼んでいる。Protocol を `send_message()` のみにすると、呼び出し側のコードを修正しなければならず、これは C-3（「既存実装はリファクタリングしない」）に反する可能性がある。

**[Mediator]**

以下の2点を総合して判断する：
1. C-3 は「`AnthropicClient` の内部実装はリファクタリングしない」という制約。`AgentCore` 等の呼び出し側の型注釈変更は C-3 の対象外
2. Phase 2a の目的は「型注釈を `LLMClient` から `LLMProtocol` に変更するのみ」（FR-8.6 受入条件）

**結論**: Protocol に含めるのは `chat()` という名前のプリミティブメソッドを1つだけ定義する（requirements.md 4.2 の設計意図に沿う）。

`send_message()` を Protocol メソッドとして採用し、名前を `chat()` に変更した新規 Protocol を定義する。
`LLMClient`（既存実装）は `chat()` メソッドを追加することで Protocol を満足させる（既存の `send_message()` は残し互換性を維持）。
`AgentCore`・`WizardController` の型注釈は `LLMClient` から `LLMProtocol` に変更するが、メソッド呼び出しは `send_message_for_purpose()` のままで変更しない。

> **補足**: `send_message_for_purpose()` は Protocol 外メソッドとして `LLMClient` に残す（S-2 の Protocol 外メソッド明示ルールに従う）。Phase 2a では `AgentCore` 等は引き続き `send_message_for_purpose()` を呼び出す。この呼び出しは Protocol 型ではなく `LLMClient` 型に依存するが、Phase 2a スコープでは第2実装が存在しないため問題ない。Phase 3 で LocalLLM を追加する際にリファクタリングする。

---

### Atom A2: `AnthropicClient` への改名可否

**[Affirmative]**

`LLMClient` を `AnthropicClient` に改名すると、Protocol が追加された後の名前体系が `LLMProtocol` / `AnthropicClient` となり直感的に理解しやすい。

**[Critical]**

C-3 は「リファクタリングしない」という制約であり、クラス名変更はリファクタリングに相当する。既存テストが `LLMClient` を直接参照しており、名前変更はテスト修正を必要とする。Phase 2a の範囲を超える工数が発生する。

**[Mediator]**

**結論**: 改名しない。`LLMClient` の名前はそのまま維持する。Protocol 名は `LLMProtocol` とし、両者が共存する形にする。Phase 3 で改名を検討する（ADR 候補として記録）。

---

### Atom A3: 型注釈変更の影響範囲

**[Mediator]**

以下のファイルの型注釈を変更する。変更は型注釈のみであり、メソッド呼び出しは変更しない。

| ファイル | 変更箇所 | 変更内容 |
|---------|---------|---------|
| `src/kage_shiki/agent/agent_core.py` | `AgentCore.__init__` の `llm_client` 引数型 | `LLMClient` → `LLMProtocol` |
| `src/kage_shiki/memory/memory_worker.py` | `MemoryWorker.__init__` の `llm` 引数型 | `LLMClient` → `LLMProtocol` |
| `src/kage_shiki/persona/wizard.py` | `WizardController.__init__` の `llm` 引数型 | `LLMClient` → `LLMProtocol` |

`main.py` の `LLMClient(config)` 生成・渡し側は変更しない（`LLMClient` は `LLMProtocol` を満足するため、型チェックは通る）。

---

### AoT Synthesis

**統合結論**:
- Protocol メソッドは `chat()` の1つのみ（プリミティブな送受信の抽象化）
- `LLMClient` クラス名はそのまま維持
- `LLMClient` に `chat()` メソッドを追加し Protocol 互換を確立（`send_message()` は残す）
- `AgentCore`、`MemoryWorker`、`WizardController` の引数型注釈を `LLMProtocol` に変更
- `send_message_for_purpose()` は Protocol 外メソッドとして `LLMClient` に残す

---

## 4. 決定

**採用**: `LLMProtocol` を `typing.Protocol` として `llm_client.py` に追加。`LLMClient` は Protocol を満足するように `chat()` メソッドを追加。

**理由**:
- `chat()` の1メソッドに絞ることで Protocol がシンプルに保たれる
- `send_message_for_purpose()` は Protocol 外（実装固有の便利メソッド）として正式に文書化
- C-3（内部実装不変）と整合する
- Phase 3 でのスムーズな LocalLLM 追加を可能にする

---

## 5. 詳細仕様

### 5.1 LLMProtocol 定義

```python
# src/kage_shiki/agent/llm_client.py に追加（既存コードは変更なし）

from typing import Protocol, runtime_checkable

@runtime_checkable
class LLMProtocol(Protocol):
    """LLM クライアントの抽象インターフェース.

    任意の LLM バックエンド（Anthropic API、LocalLLM 等）がこの Protocol を
    実装することで、AgentCore・MemoryWorker・WizardController は
    具体的な実装に依存しない。

    Phase 2a では AnthropicClient（既存の LLMClient）のみが実装する。
    Phase 3 以降で LocalLLM 等の第2実装を追加する際に活用する。

    Methods:
        chat: LLM に対話リクエストを送信し、応答テキストを返す。
    """

    def chat(
        self,
        messages: list[dict],
        *,
        system: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """LLM に対話リクエストを送信し、応答テキストを返す.

        Args:
            messages: Anthropic Messages API 形式の会話配列。
                各要素は {"role": "user"|"assistant", "content": str} の形式。
            system: システムプロンプト。
            model: モデル ID（例: "claude-haiku-4-5-20251001"）。
            max_tokens: 最大出力トークン数。
            temperature: サンプリング温度（0.0〜2.0）。

        Returns:
            LLM の応答テキスト。

        Raises:
            実装依存のエラー。AuthenticationError、LLMError 等。
        """
        ...
```

### 5.2 LLMClient への `chat()` メソッド追加

```python
# LLMClient クラスに追加するメソッド（既存の send_message() は変更しない）

def chat(
    self,
    messages: list[dict],
    *,
    system: str,
    model: str,
    max_tokens: int,
    temperature: float,
) -> str:
    """LLMProtocol を満足するための chat() メソッド.

    内部で send_message() に委譲する。
    LLMProtocol の実装として機能する（Phase 3 での差し替え口）。

    Args:
        messages: Anthropic Messages API 形式の会話配列。
        system: システムプロンプト。
        model: モデル ID。
        max_tokens: 最大出力トークン数。
        temperature: サンプリング温度。

    Returns:
        LLM の応答テキスト。
    """
    return self.send_message(
        system=system,
        messages=messages,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
    )
```

**Protocol 外メソッド（S-2 の明示）**:
`send_message_for_purpose()` は `LLMProtocol` に定義されていない `LLMClient` 固有の便利メソッドである。
`AgentCore`・`WizardController` は現状この便利メソッドを呼び出しており、型注釈が `LLMProtocol` に変わった後も
`send_message_for_purpose()` の呼び出しは `LLMClient` 型へのダウンキャストなしに動作する
（Python の構造的サブタイピングの性質上、`LLMProtocol` 型の変数でも実際には `LLMClient` インスタンスが
渡されるため実行時エラーは発生しない）。
ただし静的型チェッカーは `LLMProtocol` 型から `send_message_for_purpose()` を呼び出すことを
エラーとして報告する場合がある。この点は Phase 3 で対処する（型安全なアダプタの設計）。

### 5.3 AgentCore の型注釈変更

```python
# agent_core.py の AgentCore.__init__ の変更箇所のみ

# 変更前
from kage_shiki.agent.llm_client import LLMClient

class AgentCore:
    def __init__(
        self,
        ...
        llm_client: LLMClient,
        ...
    ) -> None:

# 変更後
from kage_shiki.agent.llm_client import LLMClient, LLMProtocol

class AgentCore:
    def __init__(
        self,
        ...
        llm_client: LLMProtocol,
        ...
    ) -> None:
```

`self._llm_client` の型アノテーション（インスタンス変数）も `LLMProtocol` に変更する。
`send_message_for_purpose()` の呼び出しは変更しない。

### 5.4 MemoryWorker の型注釈変更

```python
# memory_worker.py の MemoryWorker.__init__ の変更箇所のみ

# 変更前
from kage_shiki.agent.llm_client import LLMClient

class MemoryWorker:
    def __init__(
        self,
        db_conn: sqlite3.Connection,
        llm_client: LLMClient,
    ) -> None:

# 変更後
from kage_shiki.agent.llm_client import LLMClient, LLMProtocol

class MemoryWorker:
    def __init__(
        self,
        db_conn: sqlite3.Connection,
        llm_client: LLMProtocol,
    ) -> None:
```

### 5.5 WizardController の型注釈変更

```python
# wizard.py の WizardController.__init__ の変更箇所のみ

# 変更前
from kage_shiki.agent.llm_client import LLMClient

class WizardController:
    def __init__(self, llm: LLMClient, config: AppConfig) -> None:

# 変更後
from kage_shiki.agent.llm_client import LLMClient, LLMProtocol

class WizardController:
    def __init__(self, llm: LLMProtocol, config: AppConfig) -> None:
```

### 5.6 モジュール構成

```
src/kage_shiki/agent/llm_client.py
├── LLMError（例外クラス、変更なし）
├── AuthenticationError（例外クラス、変更なし）
├── LLMProtocol（新規追加 — typing.Protocol）
│   └── chat()
└── LLMClient（変更なし + chat() メソッド追加）
    ├── send_message()（変更なし）
    ├── send_message_for_purpose()（変更なし）（Protocol 外メソッド）
    └── chat()（新規追加 — send_message() への委譲）
```

---

## 6. テスト観点

### 6.1 Protocol 互換性テスト

| テストケース | 検証内容 |
|------------|---------|
| `isinstance(llm_client, LLMProtocol)` が `True` | `LLMClient` が `LLMProtocol` を構造的に満足する |
| `LLMProtocol` を実装したモッククラスが `isinstance` で `True` | テスト用モックが Protocol を満足する |
| `chat()` の引数シグネチャが Protocol と一致する | `LLMClient.chat()` のシグネチャ整合性 |

### 6.2 モック設計

```python
# テストで使用する LLMProtocol 実装のサンプル（設計のみ）

class MockLLMClient:
    """テスト用 LLMProtocol 実装.

    chat() のみを実装する。send_message_for_purpose() は提供しない。
    テストが LLMProtocol インターフェースのみに依存することを強制する。
    """

    def __init__(self, response: str = "テスト応答") -> None:
        self._response = response
        self.calls: list[dict] = []  # 呼び出し記録

    def chat(
        self,
        messages: list[dict],
        *,
        system: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        self.calls.append({
            "messages": messages,
            "system": system,
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
        })
        return self._response
```

> **注意**: `MockLLMClient` は `chat()` のみを実装する。`AgentCore` が `send_message_for_purpose()` を直接呼び出している現状では、統合テストのモックは `send_message_for_purpose()` も実装する必要がある（FR-8.11 のタイミングテスト参照）。この設計上の張力は Phase 3 での型安全リファクタリングで解消する。

### 6.3 既存テストへの影響

| 影響するテストファイル | 変更の有無 | 理由 |
|---------------------|----------|------|
| `tests/test_agent/test_agent_core.py` | 型注釈変更のみ、テストコードは変更なし | `AgentCore` の動作は変わらない |
| `tests/test_agent/test_llm_client.py` | `LLMProtocol` の新規テストを追加 | Protocol 互換性テスト |
| `tests/test_persona/test_wizard.py` | 型注釈変更のみ、テストコードは変更なし | `WizardController` の動作は変わらない |
| `tests/test_memory/test_memory_worker.py` | 型注釈変更のみ、テストコードは変更なし | `MemoryWorker` の動作は変わらない |

---

## 7. 影響範囲

| 影響先 | 内容 | 変更規模 |
|--------|------|---------|
| `src/kage_shiki/agent/llm_client.py` | `LLMProtocol` クラス追加、`LLMClient.chat()` メソッド追加 | 小（追加のみ） |
| `src/kage_shiki/agent/agent_core.py` | `AgentCore.__init__` の `llm_client` 型注釈変更 | 最小 |
| `src/kage_shiki/memory/memory_worker.py` | `MemoryWorker.__init__` の `llm` 型注釈変更 | 最小 |
| `src/kage_shiki/persona/wizard.py` | `WizardController.__init__` の `llm` 型注釈変更 | 最小 |
| `src/kage_shiki/main.py` | 変更なし | なし |
| `tests/test_agent/test_llm_client.py` | Protocol 互換性テスト追加 | 小（追加のみ） |
| D-19（ウィザード GUI） | `WizardController` の型を `LLMProtocol` として設計 | D-17 確定後 |
| D-20（統合テスト） | モックが `LLMProtocol` を実装する設計 | D-17 確定後 |

---

## 8. ADR 候補

以下の判断は設計記録として残す。

| 決定事項 | 内容 |
|---------|------|
| `send_message_for_purpose()` の Protocol 除外 | Phase 3 でのアダプタ設計検討を促す。LocalLLM 追加時に再議論 |
| `LLMClient` 改名の保留 | Phase 3 で `AnthropicClient` への改名を検討 |
| 静的型チェックの限界 | `send_message_for_purpose()` を `LLMProtocol` 型変数から呼び出す箇所は Phase 3 で型安全化 |
