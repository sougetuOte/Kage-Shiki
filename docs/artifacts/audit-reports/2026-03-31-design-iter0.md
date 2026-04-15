# 監査統合レポート: Phase 2b 設計書

**対象**: `docs/specs/phase2b-autonomy/design.md`
**実施日**: 2026-03-31
**イテレーション**: 0
**監査者**: quality-auditor x2 + quality-auditor(impl) x1（並列）

---

## エグゼクティブサマリー

| 重要度 | 件数 |
|--------|------|
| Critical | 4 |
| Warning | 9 |
| Info | 6 |

**総合評価**: C（改善必要。Critical 4件は BUILDING 開始前に解決必須）

---

## Critical（BUILDING ブロッカー）

### [C-1] threading.Lock が DesireWorker に未設計（TOCTOU レースコンディション）
- **場所**: design.md Section 3.3, 4.3
- **問題**: `DesireLevel.active` への read/write が DesireWorker スレッドとバックグラウンドスレッドから lock なしで発生。`reset_all()` と `update_desires()` の排他制御が未設計
- **影響**: ユーザー入力後に自律発言が破棄されず GUI に届く可能性（US-17 違反）
- **等級**: PM（設計書変更）

### [C-2] `unprocessed_episodes` の取得方法が未設計
- **場所**: design.md Section 3.2（reflect 計算式）, Section 3.3
- **問題**: reflect 欲求の計算に必要な `unprocessed_episodes` を DB クエリで取得するか内部カウンタで管理するか未記述。DesireWorker スレッドからの DB アクセスのスレッド安全性（R-7: `check_same_thread`）も未設計
- **等級**: PM（設計書変更）

### [C-3] `summarize()` シグネチャの要件書との不一致（R-1 違反）
- **場所**: design.md Section 5.1 vs requirements.md Section 5.2
- **問題**: 要件書 `summarize(results) -> str` に対し、設計書は `summarize(topic, results) -> str` と `topic` 引数を追加。技術的には設計書が合理的だが R-1 違反
- **等級**: PM（要件書変更が必要）

### [C-4] `autonomous_queue` の蓄積問題が未設計
- **場所**: design.md Section 3.4
- **問題**: DesireWorker が閾値超過を連続通知した場合、`autonomous_queue` にイベントが蓄積する。ユーザー入力後も古い自律行動要求が残り、不要な LLM 呼び出しが発生する
- **等級**: PM（設計書変更、`maxsize=1` or drain 方式の決定が必要）

---

## Warning

### [W-1] FR-9.9 `day_summary` 参照が設計書に未記載
- **場所**: design.md Section 4.2（reflect プロンプト）
- **問題**: 要件書 FR-9.9 受入条件「day_summary を参照した内省テキスト」に対し、設計書の reflect プロンプトに day_summary 取得・注入ロジックがない
- **等級**: SE

### [W-2] 要件書の asyncio 記述が未修正（仕様ドリフト固定化）
- **場所**: requirements.md Section 5.1, 5.4
- **問題**: 設計書が threading.Timer 方式を採用したが、要件書には「asyncio ループ内で定期実行」が残存
- **等級**: PM

### [W-3] `create_curiosity_target` に `priority` 引数が欠落
- **場所**: design.md Section 6.1
- **問題**: 要件書「priority=5 でCreate」に対し、設計書シグネチャに priority 引数がない。派生テーマ登録時の priority 値も不明
- **等級**: PM

### [W-4] `ActionSchedule` が設計書に未登場
- **場所**: requirements.md Section 4.1 vs design.md
- **問題**: 要件書に `ActionSchedule` データクラスが定義されているが、設計書では `DesireLevel.active` で代替。対応関係が未記述
- **等級**: PM

### [W-5] config.toml 追加パラメータ 3件が要件書に未記載
- **場所**: design.md Section 7.1 vs requirements.md Section 4.3
- **問題**: `reflect_episode_threshold`, `rest_hours_threshold`, `rest_suppress_minutes` が設計書に追加されているが要件書に未反映
- **等級**: PM

### [W-6] `PromptBuilder` のシグネチャ変更が未設計
- **場所**: design.md Section 4, Section 2.2
- **問題**: `autonomous_turn=True` 時の独り言プロンプト注入に `build_system_prompt()` の変更が必要だが、変更方法が設計書に未記載
- **等級**: PM

### [W-7] `search()` vs `search_parallel()` の FR-9.7 との対応が不明確
- **場所**: design.md Section 5.2 vs requirements.md FR-9.7
- **問題**: 要件書は「search() が asyncio で並列実行」と記載するが、設計書では `search()` は同期、`search_parallel()` が並列担当。対応関係が未記述
- **等級**: SE

### [W-8] reflect テストケースが Section 9 に不在
- **場所**: design.md Section 9.4
- **問題**: FR-9.9 の `handle_autonomous_turn("reflect")` テストが未記載。Section 11 Success Criteria にも FR-9.9 がない
- **等級**: SE

### [W-9] `VALID_PURPOSES` 追加時の 4 dict 同時更新義務が未記載
- **場所**: design.md Section 7.3 vs config.py の既存構造
- **問題**: `_PURPOSE_MODEL_SLOTS`, `_MAX_TOKENS_MAP`, `_PURPOSE_TEMPERATURES` への同時追加が必要だが設計書に未記載
- **等級**: SE

---

## Info

- [I-1] `notify_user_input()` が要件書に未定義（S-2 準拠の Protocol 外メソッド注記が必要）
- [I-2] `threading.Timer` の再帰スケジューリングパターンが未明示
- [I-3] テスト例の `db_conn` 引数省略（Section 9.1）
- [I-4] `priority` の「低い値=高優先」の直感的逆転に対する docstring 不足
- [I-5] 可変層 L1 運用の設計書内での対応関係が未記述
- [I-6] `_run_background_loop` の拡張シグネチャが未示

---

## 修正方針

### SE級（設計書内の修正 — 即座対応可能）: 5件
W-1, W-7, W-8, W-9 + I-1〜I-6

### PM級（要件書変更または設計判断 — 承認必要）: 8件
C-1, C-2, C-3, C-4, W-2, W-3, W-4, W-5, W-6
