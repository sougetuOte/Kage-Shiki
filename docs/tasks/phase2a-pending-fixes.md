# Phase 2a 既存コード改善タスク（deferred）

**起票日**: 2026-04-15
**契機**: Phase 2b Wave 1 full-review (docs/artifacts/audit-reports/2026-04-15-wave1-iter0.md)
**スコープ**: Phase 2a 実装で既に存在する改善対象。Wave 1 スコープ外として deferred。
**権限等級**: PM（実施時期・優先度の判断要）

---

## Task A-PF-1: `_pending_observations` のメモリ上限

**File**: `src/kage_shiki/memory/db.py:51` 周辺
**Source**: Wave 1 full-review Agent 4 W-3
**問題**:
`save_observation_safe()` が DB ロック時に `_pending_observations` にエントリを
append する設計だが、バッファに上限がない。DB ロックが長期間継続するシナリオ
（高頻度書き込みや DB ファイルロック）で、メモリが無制限に肥大化する。

**影響**:
ローカル常駐アプリで数時間稼働した場合、数万件のバッファが積み上がると
プロセスのメモリが肥大化する。OS スワップや OOM の原因となりうる。

**修正方針**:
- `_pending_observations` に上限（例: 500 件）を設ける
- 超過時は最古エントリを破棄 + `logger.warning()` で通知
- もしくはリングバッファ化 (`collections.deque(maxlen=N)`)
- 上限値は `config.memory.pending_observation_cap`（新設）で設定可能にする

**テスト要件**:
- 上限超過時に最古エントリが破棄されること
- WARNING ログが出力されること
- 既存の `save_observation_safe` テストが継続して成功すること

---

## Task A-PF-3: `_pending_lock` 保持中の `save_observation()` 呼び出し

**File**: `src/kage_shiki/memory/db.py:447-458`
**Source**: Wave 1 full-review iter 1 Agent 1 W-2
**問題**:
`_flush_pending_observations()` が `_pending_lock` 内で `save_observation()` を呼び出している。`save_observation` は `@_retry_on_lock` デコレータにより最大 0.4 秒間（4 回 × 0.1 秒）ブロックする可能性がある。`_pending_lock` が長時間保持されると、他スレッドからの `save_observation_safe()` 呼び出しがバッファ追加のためにロック待ちになり、本来「DB ロック中はメモリバッファに逃がす」という設計意図が損なわれる。

**影響**:
バックグラウンドスレッドからの observations バッファリングが DB ロック中に直列化される。Phase 2b 以降でバックグラウンドスレッド呼び出しが増えると顕在化する可能性がある。

**修正方針**:
`_pending_lock` 内では `_pending_observations` リストの状態変更のみを行い、実際の `save_observation()` 呼び出しは Lock 外で実行する（スナップショット方式）。

```python
# 擬似コード
with _pending_lock:
    snapshot = list(_pending_observations)
    _pending_observations.clear()

# Lock 外でフラッシュ
for entry in snapshot:
    try:
        save_observation(conn, *entry)
    except sqlite3.OperationalError:
        with _pending_lock:
            _pending_observations.insert(0, entry)  # 戻す
        break
```

---

## Task A-PF-4: `db.py` セクション見出しコメント重複

**File**: `src/kage_shiki/memory/db.py:433, 594`
**Source**: Wave 1 full-review iter 1 Agent 1 W-3
**問題**:
`# FR-7.3: DB ロック時メモリバッファ` というセクション見出しコメントが 2 箇所に存在し、コードナビゲーション時に混乱を招く。

**修正方針**:
line 594 のセクションを `# FR-7.3: save_observation の安全ラッパー（メモリバッファ連携）` 等に変更して区別する。PG 級の軽微な整理。

---

## Task A-PF-6: integration test_shutdown_event_stops_loop のフレーク

**File**: `tests/test_integration/test_startup.py::TestRunBackgroundLoop::test_shutdown_event_stops_loop`
**Source**: Wave 1 full-review iter 0 および iter 4 の完全スキャン実行時に観測
**問題**:
`test_shutdown_event_stops_loop` は個別実行では常に pass するが、フルスイート実行時に稀に失敗する。テスト間の順序依存もしくは並行性のフレークと推測される。

**観測**:
- iter 0: フルスイート 951 件中 1 件失敗、個別実行で pass
- iter 4: フルスイート 954 件中 1 件失敗、個別実行で pass → 再実行で 954 passed
- 再現性は低く、約 1/3〜1/5 の確率で発生する様子

**修正方針**:
- shutdown event の同期を Event の wait に一本化
- スレッド終了確認を `thread.join(timeout)` + `assert not thread.is_alive()` に統一
- テストの setup で `_reset_globals()` 的な fixture を追加してテスト間干渉を排除

**優先度**: Medium — CI で頻繁に偶発失敗するなら実害あり、現状は低頻度のため Wave 1 blocker ではない。

---

## Task A-PF-5: Phase 2a test_config.py のログレベル検証欠落

**File**: `tests/test_core/test_config.py` (`test_invalid_int_field_falls_back_to_default`, `test_opacity_negative_falls_back_to_default` 等)
**Source**: Wave 1 full-review iter 4 Agent 2 W-2
**問題**:
Phase 2a の一部 fallback テストで `caplog.records` のレベル検証が欠落している:

- `test_invalid_int_field_falls_back_to_default`: `assert len(caplog.records) > 0` のみで、WARNING レベルである保証なし
- `test_opacity_negative_falls_back_to_default`: `caplog.at_level(logging.WARNING)` を使うが `caplog.records` のアサーションが欠落している

実装が `logger.info` に変わっても誤検知なくテストがパスしてしまう。

**影響**: Phase 2a コードに対する回帰検知能力がやや弱い。Wave 1 Phase 2b 追加分のテスト (`test_load_config_desire_fallback_on_invalid_type`) では iter 0 W-13 対応で既にフィールド単位の具体マッチに改善済み。

**修正方針**:
```python
warning_records = [
    r for r in caplog.records if r.levelno >= logging.WARNING
]
assert len(warning_records) > 0
assert any("[section].field" in r.getMessage() for r in warning_records)
```

**優先度**: Low — Phase 2a の既存カバレッジ問題であり、テスト自体の機能は十分。

---

## Task A-PF-2: `_flush_pending_observations` の Silent Failure

**File**: `src/kage_shiki/memory/db.py:457-458`
**Source**: Wave 1 full-review Agent 4 W-4
**問題**:
`_flush_pending_observations()` のフラッシュループ内で `sqlite3.OperationalError`
が発生した場合、`break` で脱出するのみで呼び出し元に通知がない。ログ出力も
なく、フラッシュが慢性的に失敗しているケース（DB 常時ロック）が無音のまま
継続する。

**影響**:
デバッグ時に「なぜ observations が DB に反映されないか」を追跡困難。
Silent Failure アンチパターンに該当。

**修正方針**:
- `break` する箇所で `logger.debug("Flush interrupted: DB still locked, %d remaining", len(_pending_observations))` を追加
- フラッシュ連続失敗回数を閾値で監視し、閾値超過時に WARNING を出す
- （任意）メトリクス集計用に失敗カウンタを追加

**テスト要件**:
- DB ロック時に debug ログが出力されること
- 連続失敗時の WARNING 出力を検証

---

## 優先度

両タスクとも**即時性は低い**が、以下のタイミングで実施を推奨:

1. **Phase 2b Wave 5 統合テスト後**: 長時間稼働スモークテストで現象が観測されれば即対応
2. **Phase 3 準備時**: Phase 3 の設計着手前に Phase 2a 負債を清算する一環として
3. **メモリプロファイリング実施時**: `memory_profiler` 等で肥大化が観測された場合

## 権限等級と承認フロー

- 本ファイル自体の作成・更新: **PM級**（`docs/tasks/` 配下）
- 実装着手時: **PM級承認** → BUILDING フェーズで実施
- コード修正自体: SE級（公開 API 不変の内部改善）

## 関連ドキュメント

- 監査レポート: `docs/artifacts/audit-reports/2026-04-15-wave1-iter0.md` W-18
- code-quality-guideline.md: Silent Failure / リソース枯渇の判定基準
