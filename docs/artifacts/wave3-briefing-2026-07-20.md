# Wave 3 実装ブリーフ（Opus セッション引き継ぎ）

**作成日**: 2026-07-20 / **作成者**: Fable 5（設計フェーズ主担当）
**宛先**: Wave 3 実装を担当する Opus メインセッション（モデル運用方針: BUILDING = Opus）
**形式**: tight brief 5-slot 準拠（`.claude/rules/model-delegation-prompting.md`）

## 1. objective

Phase 2b Wave 3 を TDD で実装する: **Task 3-1（HaikuEngine 実装）→ Task 3-2（AgenticSearch
パイプライン統合）** の逐次実行。`/building` モードで実施。

## 2. output format

- 各タスク完了ごとに TDD サイクル報告（Red → Green → Refactor + R-11 3 点ミニチェック）
- Wave 3 完了時: `/full-review` + 再現性検証 2 回（phase-rules.md A-1、5 分以上間隔）

## 3. tool guidance / 実装上の確定事項

### 依存パッケージ（C-1 確定・Web 裏取り済 2026-07-20）

- **`ddgs` を使用**（旧 `duckduckgo-search` は 2025-07 凍結。NFR-13 は Rev.3 で ddgs に改訂済み）
- `pyproject.toml` に `ddgs` を追加（追加依存はこれ 1 つのみ）

### ddgs 9.x API（実測裏取り済・実装直前に最終確認推奨）

```python
from ddgs import DDGS

# timeout はクラス初期化引数（デフォルト 5 秒）。設計の「search 10 秒」は init で指定する
results = DDGS(timeout=10).text(query, max_results=5)
# text() シグネチャ: text(query, region="us-en", safesearch="moderate",
#                        timelimit=None, max_results=10, page=1, backend="auto")
# 戻り値: list[dict[str, str]] — SearchResult(title, url, snippet) へのマッピング時、
# dict キー名（title/href/body 想定）は実装時に実レスポンスで確認すること（要検証）
# backend="auto" はメタサーチ（複数バックエンド）。日本語トピックなら region="jp-jp" を検討
```

### 仕様の正本

- `docs/specs/phase2b-autonomy/design.md` **Rev.3**（§5 全面・§3.3 reset・§6.1 CRUD 追加分・§7.1）
- `docs/specs/phase2b-autonomy/requirements.md` **Rev.3** / `docs/tasks/phase2b-autonomy-tasks.md` **改訂 2**
- レビュー経緯: `docs/artifacts/design-review-2026-07-20.md` + `docs/artifacts/hga-adversarial-wave3-2026-07-20.md`

### Wave 3 で新設・変更するもの（tasks 改訂 2 で確定済み）

| 対象 | 内容 | 由来 |
|------|------|------|
| `agentic_search.py` | HaikuEngine 実装 + Protocol に `search_parallel` 追加（既存テスト 214 行の更新含む） | W-1 |
| `desire_worker.py` | `reset(desire_type)` 追加（単一欲求 active=False、未知 type は KeyError） | A-3 |
| `db.py` | `recover_stale_searching_targets` / `curiosity_topic_exists` 追加 | A-1/A-2 |
| `config.py` | `AgenticSearchConfig.max_pending_targets = 20` 追加 | A-2 |
| `agent_core.py` | curiosity 本実装（パイプライン + ステージ境界 abort + `_should_abort_autonomous` helper + 終端 reset 呼び出し + 完了つぶやき必須） | A-3/A-4/A-7 |

### 実装時の要注意（HGA レビューの核心）

1. パイプライン順序は design Rev.3 §5.4 の**改訂版フロー**（pending 確認 → つぶやきの順。復旧 → 取得 → つぶやき → searching → [abort] decompose → [abort] search_parallel → [abort] summarize → [abort] noise → done → dedup+上限付き派生登録 → 完了つぶやき → reset）
2. abort 時は status を **pending に戻す**（failed ではない）
3. summarize / extract_noise_topics のプロンプトに**インジェクション防御指示**必須 + noise 戻り値のコード側検証（≤3 件・≤50 字・重複排除）
4. decompose 0 件時は topic 単体クエリに fallback（failed にしない）
5. 同期 `DDGS().text()` は `asyncio.to_thread` でラップして gather（直接 gather では並列にならない）
6. `asyncio.wait_for` timeout はスレッド停止ではない（結果破棄のみ）— テストの期待値に注意

## 4. task boundaries

- main.py への結線は **Wave 5**（触らない）。Wave 3 は AgentCore/新関数の単体+統合テストまで
- docs/specs の再変更が必要になったら PM 級 — Auto 進行せずユーザーへ
- Wave 4 残タスクは Task 4-2（トピック照合）のみ。先行実装する場合は S-3 の注記義務を遵守
- AUDITING（/full-review）時のモデルは**ユーザーと要相談**（モデル運用方針）

## 5. primary_sources

- ローカル SSOT: design.md Rev.3 / requirements.md Rev.3 / tasks.md 改訂 2（上記パス。他の派生資料は参考扱い）
- upstream: https://pypi.org/project/ddgs/ （API 最終確認用）/ https://github.com/deedy5/ddgs
