# 設計書レビューレポート: Phase 2b Wave 3 着手前レビュー

**実施日**: 2026-07-20
**レビュアー**: Fable 5（メインモデル — モデル運用方針 2026-07-20 に基づく）
**対象**: 復帰パッケージ指定の優先順①〜⑥
（① design.md ② requirements.md ③ tasks.md ④ wave2-final 監査 ⑤ wave2 retro ⑥ phase2a-pending-fixes）
**体制**: Lane A = Fable 直（①②③精読）/ Lane B = subagent（④⑤⑥要約）/ Lane C = subagent（Wave 3 対象コード現状調査）
**手順書**: `docs/artifacts/work-procedure-2026-07-20-design-review.md`

Critical: 1件 / Warning: 4件 / Info: 3件
総合評価: **B**（設計自体は堅牢だが、外部依存の鮮度ドリフト 1 件が Wave 3 着手のブロッカー）

---

## Critical

### C-1: `duckduckgo-search` は凍結済み — `ddgs` へのリネームが必要【PM級・指摘のみ】

- **事実**（2026-07-20 WebSearch 裏取り済）: `duckduckgo-search` は **2025-07 に凍結**され、
  後継は **`ddgs`**（2026-05 時点 v9.14.x が活発にメンテ中）。旧パッケージは DDG の
  anti-bot 修正が止まっており、検索が経時劣化する。
  - https://pypi.org/project/duckduckgo-search/ / https://pypi.org/project/ddgs/
- **影響箇所**:
  - design.md §5.3 D-25（`from duckduckgo_search import DDGS`）
  - requirements.md NFR-13（「追加依存は duckduckgo-search のみ」）・§4.3 `search_api = "duckduckgo"`
  - tasks.md Task 3-1 / 実装開始チェックリスト（「duckduckgo-search が pyproject.toml に追加されている」）
- **要検証の仮定**: `ddgs` でも `DDGS().text()` 相当の API は互換維持とされるが、
  正確なシグネチャ（timeout 引数・戻り値形式）は実装直前に `ddgs` 公式 doc で確認すること
  （upstream-first 原則）。
- **推奨対処**: NFR-13 / D-25 / tasks を「`ddgs`」に置換する仕様修正。依存パッケージ名の変更は
  **仕様の意味を変える PM 級** のため Auto 進行せず、承認ゲートへ。

## Warning

### W-1: `search_parallel()` の Protocol 外配置が US-19（エンジン差し替え）と緊張【PM級・指摘のみ】

- design.md §5.2 は `search_parallel()` を Protocol 外の HaikuEngine 実装メソッドとし、
  §5.4 パイプラインがこれを呼ぶ。呼び出し側（agent_core）が具象型 `HaikuEngine` に依存する形になり、
  Phase 3 で LocalLLMEngine に差し替える際「上位ロジック無変更」（US-19 / FR-9.10 の狙い）が崩れる。
- S-2（Protocol 外メソッドの明示）自体は §5.2 注記で満たされているが、**分岐点の裁定**が必要:
  - **案 A（推奨）**: `search_parallel(queries) -> list[list[SearchResult]]` を Protocol に昇格する。
    LocalLLMEngine も並列検索を持つのが自然で、差し替え無変更が保たれる
  - 案 B: パイプライン側が Protocol の `search()` を自前で並列化する（エンジンは単一クエリのみ）
- いずれも specs 変更のため PM 級。**Wave 3 実装前に確定が必要**（Task 3-1/3-2 の契約に直結）。

### W-2: 「asyncio で並列」の実現手段が同期 API と噛み合っていない【SE級相当・design 補記推奨だが specs のため PM級】

- `DDGS().text()` は同期 API。`asyncio.gather` に同期関数を並べても並列にならず、
  `asyncio.to_thread()` / `run_in_executor` でのラップが必要（design §5.2/5.3 に記載なし）。
- 設計の意味（並列実行 + セマフォ制御）は不変のため、実装方式の補記で足りる。
  D-24 却下案の「threading.Thread 並列化（次善策として許容）」を主案に格上げする選択肢もある
  （`to_thread` は実質スレッドプールであり、asyncio を経由する意義はセマフォ・timeout 管理のみ）。

### W-3: design §5.2 と §8 のスレッド記述不整合

- §5.2「`search_parallel()` は **DesireWorker スレッド内**から呼び出される」に対し、
  §8 データフロー図と Task 3-2 では AgenticSearch パイプラインは
  **バックグラウンドスレッド**（`_run_background_loop` → `handle_autonomous_turn("curiosity")`）で実行される。
- 後者が正（Wave 2 実装・Lane C 確認とも整合）。`asyncio.run()` はどちらのスレッドでも動作するため
  実害は小さいが、Wave 3 実装者が誤読するリスクがある。§5.2 の該当文の訂正を推奨（specs のため PM 級）。

### W-4: curiosity 単独リセットの API が未定義【unverified 含む】

- design §5.2 エラーハンドリング「AgenticSearch の失敗は curiosity レベルをリセット」、
  §5.3 フォールバック「欲求の active を False にリセット」、Task 3-2 テスト観点
  「検索失敗時に curiosity レベルがリセットされる」に対し、DesireWorker の公開 API は
  `reset_all()`（全欲求）のみで、**単一欲求のリセット手段が設計上未定義**。
- `reset_all()` で代用すると talk/reflect/rest の active まで消える副作用がある。
- requirements §4.2 の「active: 実行後 or ユーザー入力時に False」の「実行後」経路が
  Wave 2 実装でどう実現されているかは今回未検証（**unverified** — Wave 3 着手時に
  `desire_worker.py` / `agent_core.py` の実態を確認し、必要なら `reset(desire_type)` 追加を
  Task 3-2 スコープに含める。API 追加は仕様追記 = PM 級）。

## Info

### I-1: §5.4 の「調べ始める」つぶやきと pending 確認の順序

- つぶやき生成 → `get_pending_targets` の順のため、競合ウィンドウ（発火後〜取得前に pending が
  消えるケース）で「調べると言ったのに調べない」状態になりうる。curiosity level は
  pending=0 で 0 になるため通常は発火せず、実害は稀。pending 確認を先行させる順序入替を推奨（実装時判断で可）。

### I-2: `decompose_query` が 2 個未満を返した場合の挙動が未定義

- 受入条件は「2〜max_subqueries 個」。LLM が 1 個/0 個を返した際の挙動（そのまま続行 / failed 遷移）が
  未定義（R-13 の精神）。実装時に決めてテストに含めれば足りる。

### I-3: db.py 既存負債（A-PF-1/2/3）は Wave 3 で顕在化しうるが blocker ではない

- AgenticSearch は主に `curiosity_targets` を更新し observations バッファ経路への負荷増は限定的。
  phase2a-pending-fixes.md の推奨どおり Wave 5 統合テスト後の対処で妥当。
  A-PF-6（`test_shutdown_event_stops_loop` flake）は Wave 完了時の再現性検証 2 回
  （phase-rules.md 反映済み）で捕捉する。

---

## 補足確認事項

- **retro アクションの反映状況**: Lane B が「未反映」と報告した A-1（再現性検証）/ A-2（裁定プロトコル）/
  A-4（PM級 Auto mode 通知）/ A-5（先行実装注記）は、現行 `.claude/rules/`
  （phase-rules.md / code-quality-guideline.md / permission-levels.md / building-checklist.md）に
  **反映済み**であることをルール本文で確認した。retro 時点（2026-04-29）の記録が古いだけであり、対処不要。
- **Wave 3 スコープの妥当性**: Lane C のコード調査結果（HaikuEngine 未実装 / パイプラインワーカー欠落 /
  purpose 配線は config に済み / main.py 結線は Wave 5 予定コメントあり）は tasks.md の
  Task 3-1 → 3-2 分割と完全に整合。タスク定義の追加分割は不要。
- **HGA 召喚ゲートについて**: Wave 3 は「新規ドメイン統合 = 既定で召喚」該当だが、本レビュー自体を
  Fable（メインモデル）が実施したため、別途のスポット召喚は不要と判断（召喚ゲートの趣旨を
  メイン常駐で充足。モデル運用方針 2026-07-20）。

## Wave 3 着手可否の判定

**条件付き GO**。以下の PM 級 4 点が対処対象:

> **⚠️ PM 級の Auto 進行（2026-07-20）**: 下表 4 点は、ユーザーの同日指示
> 「極力自律実行しなさい。選択肢は君の推奨を用いること」に基づき、レビュアー（Fable）の
> 推奨案（W-1 は案 A）で **specs/tasks へ反映済み**（design.md Rev.2 / requirements.md Rev.2 /
> tasks.md 改訂）。通常の PM 級承認ゲートを経ていないため、**ユーザーは事後確認をお願いします**。
> 差し戻しは git で可能。

| # | 指摘 | 必要な判断 |
|---|------|-----------|
| C-1 | duckduckgo-search → ddgs | specs/tasks の依存名置換の承認 |
| W-1 | search_parallel の Protocol 昇格 | 案 A（昇格・推奨）/ 案 B の裁定 |
| W-2 | asyncio.to_thread 補記 | design §5.2 への実装方式補記の承認 |
| W-3 | §5.2 スレッド記述訂正 | 「バックグラウンドスレッドから呼び出す」への訂正承認 |

W-4 は Wave 3 着手時のコード実態確認とセット（必要時のみ仕様追記を追加承認）。

## 既存 follow-up（本レビューのスコープ外・再掲）

- gabriel timeout 閾値再校正（60 秒 → 実測 171 秒）: PM 級 follow-up
- Reflection 廃止判断: gabriel 実運用安定後に PM 級で判断
- `.env` の ANTHROPIC_API_KEY ローテーション: ユーザー作業
