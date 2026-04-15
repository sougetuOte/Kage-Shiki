"""T-DW: DesireWorker のユニットテスト.

対応 FR:
    FR-9.1: DesireWorker が 4 欲求（talk/curiosity/reflect/rest）のレベルを
            update_interval_sec 間隔で更新する
    FR-9.2: 欲求レベルが閾値を超過した場合、on_threshold_exceeded コールバックで通知する

テストケース一覧:
    1.  test_desire_level_defaults          — DesireLevel デフォルト値
    2.  test_desire_state_structure         — DesireState.desires が 4 キーを持つ
    3.  test_worker_init_all_zero_inactive  — 起動時に全欲求が level=0.0/active=False
    4.  test_talk_level_linear_increase     — talk: idle 30分で level=1.0
    5.  test_talk_level_partial             — talk: idle 15分で level=0.5
    6.  test_talk_level_capped_at_1         — talk: idle 60分でも level=1.0 に収まる
    7.  test_curiosity_level_pending_idle   — curiosity: pending_count * idle 乗積
    8.  test_curiosity_zero_when_no_pending — curiosity: pending=0 なら level=0
    9.  test_curiosity_active_user_suppress — curiosity: idle < 2分のとき time_weight=0
    10. test_reflect_level_linear           — reflect: obs/threshold で線形増加
    11. test_reflect_level_capped_at_1      — reflect: obs >= threshold で level=1.0
    12. test_rest_level_linear              — rest: uptime/threshold で線形増加
    13. test_rest_level_capped_at_1         — rest: uptime >= threshold で level=1.0
    14. test_threshold_exceeded_callback    — 閾値超過で on_threshold_exceeded 呼ばれる
    15. test_no_duplicate_callback_when_active — active=True 中は追加通知抑制
    16. test_reset_all_clears_active        — reset_all() で全欲求 active=False
    17. test_notify_user_input_resets_idle  — notify_user_input() で idle リセット
    18. test_get_state_returns_desire_state — get_state() が DesireState を返す
    19. test_lock_prevents_concurrent_update — Lock が update_desires/reset_all を排他制御
    20. test_start_stop_idempotent          — start()/stop() の冪等性
    21. test_rest_suppress_minutes          — rest の rest_suppress_minutes 再通知抑制
    22. test_callbacks_after_lock_release   — Lock 解放後にコールバックが呼ばれる
        （デッドロック防止）
"""

import logging
import threading
from collections.abc import Callable
from unittest.mock import MagicMock, patch

import pytest

from kage_shiki.agent.desire_worker import DesireLevel, DesireState, DesireWorker
from kage_shiki.core.config import DesireConfig

# ---------------------------------------------------------------------------
# ヘルパー・フィクスチャ
# ---------------------------------------------------------------------------


def _make_config(**kwargs: object) -> DesireConfig:
    """テスト用 DesireConfig を生成する。デフォルトは短い閾値で高速テスト向け。"""
    defaults = {
        "update_interval_sec": 7.5,
        "talk_threshold": 0.7,
        "curiosity_threshold": 0.6,
        "reflect_threshold": 0.8,
        "rest_threshold": 0.9,
        "idle_minutes_for_talk": 30.0,
        "idle_minutes_for_curiosity": 15.0,
        "reflect_episode_threshold": 20,
        "rest_hours_threshold": 4.0,
        "rest_suppress_minutes": 60.0,
    }
    defaults.update(kwargs)
    return DesireConfig(**defaults)  # type: ignore[arg-type]


def _make_worker(
    config: DesireConfig | None = None,
    get_pending_curiosity_count: Callable[[], int] | None = None,
    get_observation_count: Callable[[], int] | None = None,
    on_threshold_exceeded: Callable[[str], None] | None = None,
    session_start_time: float | None = None,
) -> DesireWorker:
    """テスト用 DesireWorker を生成する。"""
    return DesireWorker(
        config=config or _make_config(),
        get_pending_curiosity_count=get_pending_curiosity_count or (lambda: 0),
        get_observation_count=get_observation_count or (lambda: 0),
        on_threshold_exceeded=on_threshold_exceeded or (lambda desire_type: None),
        session_start_time=session_start_time,
    )


# ---------------------------------------------------------------------------
# 1. DesireLevel デフォルト値
# ---------------------------------------------------------------------------


class TestDesireLevel:
    def test_desire_level_defaults(self) -> None:
        """DesireLevel デフォルト値: level=0.0, threshold=0.0, last_updated=0.0, active=False."""
        dl = DesireLevel()
        assert dl.level == 0.0
        assert dl.threshold == 0.0
        assert dl.last_updated == 0.0
        assert dl.active is False

    def test_desire_level_custom_values(self) -> None:
        """DesireLevel にカスタム値を設定できる。"""
        dl = DesireLevel(level=0.5, threshold=0.7, last_updated=100.0, active=True)
        assert dl.level == 0.5
        assert dl.threshold == 0.7
        assert dl.last_updated == 100.0
        assert dl.active is True


# ---------------------------------------------------------------------------
# 2. DesireState 構造
# ---------------------------------------------------------------------------


class TestDesireState:
    def test_desire_state_structure(self) -> None:
        """DesireState.desires は dict[str, DesireLevel] を持つ。"""
        desires = {k: DesireLevel() for k in ("talk", "curiosity", "reflect", "rest")}
        state = DesireState(desires=desires)
        assert set(state.desires.keys()) == {"talk", "curiosity", "reflect", "rest"}
        for v in state.desires.values():
            assert isinstance(v, DesireLevel)


# ---------------------------------------------------------------------------
# 3. DesireWorker 初期化
# ---------------------------------------------------------------------------


class TestDesireWorkerInit:
    def test_worker_init_all_zero_inactive(self) -> None:
        """DesireWorker 生成時、全欲求が level=0.0 / active=False で初期化される（FR-9.1 (1)）。"""
        worker = _make_worker()
        state = worker.get_state()
        assert set(state.desires.keys()) == {"talk", "curiosity", "reflect", "rest"}
        for desire_type, dl in state.desires.items():
            assert dl.level == 0.0, f"{desire_type}: level should be 0.0"
            assert dl.active is False, f"{desire_type}: active should be False"

    def test_worker_init_thresholds_from_config(self) -> None:
        """DesireWorker 生成時、各欲求の threshold が config から正しく設定される。"""
        config = _make_config(
            talk_threshold=0.7,
            curiosity_threshold=0.6,
            reflect_threshold=0.8,
            rest_threshold=0.9,
        )
        worker = _make_worker(config=config)
        state = worker.get_state()
        assert state.desires["talk"].threshold == 0.7
        assert state.desires["curiosity"].threshold == 0.6
        assert state.desires["reflect"].threshold == 0.8
        assert state.desires["rest"].threshold == 0.9


# ---------------------------------------------------------------------------
# 4-6. talk 欲求
# ---------------------------------------------------------------------------


class TestTalkDesire:
    def _make_talk_worker(
        self,
        idle_minutes_for_talk: float = 30.0,
        on_threshold_exceeded: Callable[[str], None] | None = None,
    ) -> DesireWorker:
        config = _make_config(
            idle_minutes_for_talk=idle_minutes_for_talk,
            talk_threshold=0.7,
        )
        return _make_worker(
            config=config,
            on_threshold_exceeded=on_threshold_exceeded,
        )

    def test_talk_level_linear_increase(self) -> None:
        """talk: idle 30分で level=1.0 になる（FR-9.1 受入条件 (2)）。"""
        worker = self._make_talk_worker(idle_minutes_for_talk=30.0)
        base_time = 1000.0

        with patch("time.monotonic", return_value=base_time):
            worker.notify_user_input()

        # idle 30分後
        with patch("time.monotonic", return_value=base_time + 30 * 60):
            worker.update_desires()

        state = worker.get_state()
        assert state.desires["talk"].level == pytest.approx(1.0)

    def test_talk_level_partial(self) -> None:
        """talk: idle 15分で level=0.5 になる。"""
        worker = self._make_talk_worker(idle_minutes_for_talk=30.0)
        base_time = 1000.0

        with patch("time.monotonic", return_value=base_time):
            worker.notify_user_input()

        with patch("time.monotonic", return_value=base_time + 15 * 60):
            worker.update_desires()

        state = worker.get_state()
        assert state.desires["talk"].level == pytest.approx(0.5)

    def test_talk_level_capped_at_1(self) -> None:
        """talk: idle 60分でも level は 1.0 を超えない（FR-9.1 受入条件 (2)）。"""
        worker = self._make_talk_worker(idle_minutes_for_talk=30.0)
        base_time = 1000.0

        with patch("time.monotonic", return_value=base_time):
            worker.notify_user_input()

        with patch("time.monotonic", return_value=base_time + 60 * 60):
            worker.update_desires()

        state = worker.get_state()
        assert state.desires["talk"].level == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# 7-9. curiosity 欲求
# ---------------------------------------------------------------------------


class TestCuriosityDesire:
    def _make_curiosity_worker(
        self,
        pending_count: int = 0,
        idle_minutes_for_curiosity: float = 15.0,
        on_threshold_exceeded: Callable[[str], None] | None = None,
    ) -> DesireWorker:
        config = _make_config(
            idle_minutes_for_curiosity=idle_minutes_for_curiosity,
            curiosity_threshold=0.6,
        )
        return _make_worker(
            config=config,
            get_pending_curiosity_count=lambda: pending_count,
            on_threshold_exceeded=on_threshold_exceeded,
        )

    def test_curiosity_level_pending_idle(self) -> None:
        """curiosity: pending_count=5, idle=15分 で level=1.0 になる。"""
        worker = self._make_curiosity_worker(
            pending_count=5,
            idle_minutes_for_curiosity=15.0,
        )
        base_time = 1000.0

        with patch("time.monotonic", return_value=base_time):
            worker.notify_user_input()

        with patch("time.monotonic", return_value=base_time + 15 * 60):
            worker.update_desires()

        state = worker.get_state()
        # pending_weight = min(1.0, 5/5) = 1.0, time_weight = min(1.0, 15/15) = 1.0
        assert state.desires["curiosity"].level == pytest.approx(1.0)

    def test_curiosity_zero_when_no_pending(self) -> None:
        """curiosity: pending=0 のとき level=0（FR-9.6「pending なしは何もしない」準拠）。"""
        worker = self._make_curiosity_worker(pending_count=0)
        base_time = 1000.0

        with patch("time.monotonic", return_value=base_time):
            worker.notify_user_input()

        with patch("time.monotonic", return_value=base_time + 60 * 60):
            worker.update_desires()

        state = worker.get_state()
        assert state.desires["curiosity"].level == pytest.approx(0.0)

    def test_curiosity_active_user_suppress(self) -> None:
        """curiosity: idle < 2分のとき time_weight=0 になり level=0 になる。"""
        worker = self._make_curiosity_worker(
            pending_count=5,
            idle_minutes_for_curiosity=15.0,
        )
        base_time = 1000.0

        with patch("time.monotonic", return_value=base_time):
            worker.notify_user_input()

        # idle 1分（< 2分）
        with patch("time.monotonic", return_value=base_time + 1 * 60):
            worker.update_desires()

        state = worker.get_state()
        assert state.desires["curiosity"].level == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# 10-11. reflect 欲求
# ---------------------------------------------------------------------------


class TestReflectDesire:
    def _make_reflect_worker(
        self,
        observation_count: int = 0,
        reflect_episode_threshold: int = 20,
    ) -> DesireWorker:
        config = _make_config(
            reflect_episode_threshold=reflect_episode_threshold,
            reflect_threshold=0.8,
        )
        return _make_worker(
            config=config,
            get_observation_count=lambda: observation_count,
        )

    def test_reflect_level_linear(self) -> None:
        """reflect: observation_count=10, threshold=20 で level=0.5 になる。"""
        worker = self._make_reflect_worker(observation_count=10, reflect_episode_threshold=20)

        with patch("time.monotonic", return_value=1000.0):
            worker.update_desires()

        state = worker.get_state()
        assert state.desires["reflect"].level == pytest.approx(0.5)

    def test_reflect_level_capped_at_1(self) -> None:
        """reflect: observation_count >= threshold で level=1.0 に収まる。"""
        worker = self._make_reflect_worker(observation_count=25, reflect_episode_threshold=20)

        with patch("time.monotonic", return_value=1000.0):
            worker.update_desires()

        state = worker.get_state()
        assert state.desires["reflect"].level == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# 12-13. rest 欲求
# ---------------------------------------------------------------------------


class TestRestDesire:
    def _make_rest_worker(
        self,
        rest_hours_threshold: float = 4.0,
    ) -> DesireWorker:
        config = _make_config(
            rest_hours_threshold=rest_hours_threshold,
            rest_threshold=0.9,
        )
        return _make_worker(config=config)

    def _make_rest_worker_with_session(
        self, rest_hours_threshold: float, session_start: float,
    ) -> DesireWorker:
        """セッション開始時刻を注入した rest 欲求テスト用 worker を作る (W-7)."""
        config = _make_config(
            rest_hours_threshold=rest_hours_threshold,
            rest_threshold=0.9,
        )
        return _make_worker(config=config, session_start_time=session_start)

    def test_rest_level_linear(self) -> None:
        """rest: uptime=2h, threshold=4h で level=0.5 になる (W-7: session 注入)."""
        session_start = 1000.0
        worker = self._make_rest_worker_with_session(
            rest_hours_threshold=4.0, session_start=session_start,
        )

        # uptime 2 時間後
        with patch("time.monotonic", return_value=session_start + 2 * 3600):
            worker.update_desires()

        state = worker.get_state()
        assert state.desires["rest"].level == pytest.approx(0.5)

    def test_rest_level_capped_at_1(self) -> None:
        """rest: uptime >= threshold で level=1.0 に収まる (W-7: session 注入)."""
        session_start = 1000.0
        worker = self._make_rest_worker_with_session(
            rest_hours_threshold=4.0, session_start=session_start,
        )

        with patch("time.monotonic", return_value=session_start + 8 * 3600):
            worker.update_desires()

        state = worker.get_state()
        assert state.desires["rest"].level == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# 14. 閾値超過コールバック
# ---------------------------------------------------------------------------


class TestThresholdCallback:
    def test_threshold_exceeded_callback(self) -> None:
        """閾値超過時に on_threshold_exceeded が正しい desire_type で呼ばれる（FR-9.2 (1)）。"""
        callback = MagicMock()
        config = _make_config(
            talk_threshold=0.7,
            idle_minutes_for_talk=30.0,
        )
        worker = _make_worker(
            config=config,
            on_threshold_exceeded=callback,
        )
        base_time = 1000.0

        with patch("time.monotonic", return_value=base_time):
            worker.notify_user_input()

        # idle 30分で talk level=1.0 > threshold=0.7
        with patch("time.monotonic", return_value=base_time + 30 * 60):
            worker.update_desires()

        callback.assert_called_once_with("talk")

    def test_callback_for_reflect(self) -> None:
        """reflect が閾値超過したとき on_threshold_exceeded("reflect") が呼ばれる。"""
        callback = MagicMock()
        config = _make_config(
            reflect_threshold=0.8,
            reflect_episode_threshold=20,
        )
        worker = _make_worker(
            config=config,
            get_observation_count=lambda: 20,
            on_threshold_exceeded=callback,
        )

        with patch("time.monotonic", return_value=1000.0):
            worker.update_desires()

        callback.assert_called_once_with("reflect")


# ---------------------------------------------------------------------------
# 15. 連続通知抑制
# ---------------------------------------------------------------------------


class TestDuplicateNotificationSuppression:
    def test_no_duplicate_callback_when_active(self) -> None:
        """active=True 中は同一欲求の追加コールバックが抑制される（FR-9.2 受入条件 (2)）。"""
        callback = MagicMock()
        config = _make_config(
            talk_threshold=0.7,
            idle_minutes_for_talk=30.0,
        )
        worker = _make_worker(config=config, on_threshold_exceeded=callback)
        base_time = 1000.0

        with patch("time.monotonic", return_value=base_time):
            worker.notify_user_input()

        # 1回目: 閾値超過
        with patch("time.monotonic", return_value=base_time + 30 * 60):
            worker.update_desires()

        # 2回目: active=True のまま再度 update_desires
        with patch("time.monotonic", return_value=base_time + 35 * 60):
            worker.update_desires()

        # コールバックは1回のみ呼ばれる
        assert callback.call_count == 1


# ---------------------------------------------------------------------------
# 16. reset_all
# ---------------------------------------------------------------------------


class TestResetAll:
    def test_reset_all_clears_active(self) -> None:
        """reset_all() で全欲求の active が False にリセットされる（FR-9.5）。"""
        callback = MagicMock()
        config = _make_config(
            talk_threshold=0.7,
            idle_minutes_for_talk=30.0,
            reflect_threshold=0.8,
            reflect_episode_threshold=20,
        )
        worker = _make_worker(
            config=config,
            get_observation_count=lambda: 20,
            on_threshold_exceeded=callback,
        )
        base_time = 1000.0

        with patch("time.monotonic", return_value=base_time):
            worker.notify_user_input()

        # 両欲求を閾値超過させる
        with patch("time.monotonic", return_value=base_time + 30 * 60):
            worker.update_desires()

        # active=True を確認
        state = worker.get_state()
        assert state.desires["talk"].active is True
        assert state.desires["reflect"].active is True

        # reset_all で全 active=False に
        with patch("time.monotonic", return_value=base_time + 30 * 60):
            worker.reset_all()

        state = worker.get_state()
        for desire_type, dl in state.desires.items():
            assert dl.active is False, f"{desire_type}.active should be False after reset_all"

    def test_reset_all_allows_new_callback(self) -> None:
        """reset_all() 後に再び閾値超過すると新たにコールバックが呼ばれる。"""
        callback = MagicMock()
        config = _make_config(
            talk_threshold=0.7,
            idle_minutes_for_talk=30.0,
        )
        worker = _make_worker(config=config, on_threshold_exceeded=callback)
        base_time = 1000.0

        with patch("time.monotonic", return_value=base_time):
            worker.notify_user_input()

        # T+30分: 1 回目の閾値超過（idle=30分で talk level=1.0 > 0.7）
        first_fire_time = base_time + 30 * 60
        with patch("time.monotonic", return_value=first_fire_time):
            worker.update_desires()

        assert callback.call_count == 1

        # T+30分の時点で reset_all + notify_user_input でリセット
        # （ユーザー入力が到着し、active フラグと idle タイマーがリセットされる）
        reset_time = first_fire_time
        with patch("time.monotonic", return_value=reset_time):
            worker.reset_all()
            worker.notify_user_input()

        # T+1時間30分: リセット後にさらに 1 時間経過。idle=60 分なので talk level=1.0。
        # 再び閾値超過、コールバックが 2 回目に発火する。
        second_fire_time = reset_time + 60 * 60
        with patch("time.monotonic", return_value=second_fire_time):
            worker.update_desires()

        assert callback.call_count == 2


# ---------------------------------------------------------------------------
# 17. notify_user_input
# ---------------------------------------------------------------------------


class TestNotifyUserInput:
    def test_notify_user_input_resets_idle(self) -> None:
        """notify_user_input() で idle タイマーがリセットされ、talk level が下がる。"""
        config = _make_config(
            talk_threshold=0.7,
            idle_minutes_for_talk=30.0,
        )
        worker = _make_worker(config=config)
        first_time = 1000.0

        with patch("time.monotonic", return_value=first_time):
            worker.notify_user_input()

        # idle 30分後: level=1.0 のはず
        with patch("time.monotonic", return_value=first_time + 30 * 60):
            worker.update_desires()

        state = worker.get_state()
        assert state.desires["talk"].level == pytest.approx(1.0)

        # ユーザー入力でリセット
        reset_time = first_time + 30 * 60
        with patch("time.monotonic", return_value=reset_time):
            worker.notify_user_input()

        # リセット直後 (idle=0): level=0 のはず
        with patch("time.monotonic", return_value=reset_time):
            worker.update_desires()

        state = worker.get_state()
        assert state.desires["talk"].level == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# 18. get_state
# ---------------------------------------------------------------------------


class TestGetState:
    def test_get_state_returns_desire_state(self) -> None:
        """get_state() が DesireState インスタンスを返す。"""
        worker = _make_worker()
        state = worker.get_state()
        assert isinstance(state, DesireState)
        assert isinstance(state.desires, dict)

    def test_get_state_returns_copy(self) -> None:
        """get_state() が返す DesireState の変更が内部状態に影響しない。"""
        worker = _make_worker()
        state = worker.get_state()
        state.desires["talk"].level = 0.99

        # 内部状態は変わっていない
        state2 = worker.get_state()
        assert state2.desires["talk"].level == 0.0


# ---------------------------------------------------------------------------
# 19. スレッド安全性
# ---------------------------------------------------------------------------


class TestThreadSafety:
    def test_worker_has_threading_lock(self) -> None:
        """DesireWorker が threading.Lock インスタンスを保持していること (W-9)."""
        worker = _make_worker()
        # Python の threading.Lock() は `_thread.lock` 型のため isinstance 判定ではなく
        # acquire/release が可能な Lock プロトコルであることを検証する。
        assert hasattr(worker._lock, "acquire")
        assert hasattr(worker._lock, "release")
        assert worker._lock.acquire(blocking=False)
        worker._lock.release()

    def test_lock_prevents_concurrent_update(self) -> None:
        """Lock が reset_all を正しく直列化することを検証する (W-9, iter 4 W-1 決定論化).

        検証内容:
          1. holder_thread が `_lock` を取得したまま release_event を待つ
          2. 別スレッドで `reset_all()` を起動（内部で `_lock` 取得待ち）
          3. holder 解放前に reset_thread が `is_alive()` であることを確認
             = reset_all が Lock 取得で blocked している（= Lock 機能している）
          4. holder 解放後に reset_thread が完了することを確認
             = Lock が解放されれば reset_all が完了できる

        `reset_thread.is_alive()` は即時に判定できるため、0.5 秒の長い wait に
        頼らない。CI 速度の影響を受けず、Lock が機能していない場合は即座に
        `is_alive()=False` で検出される（reset_all は極めて高速に完了するため）。
        ごく短い join timeout(10ms) は「reset_thread が起動して Lock 取得試行に
        到達するまでの待機」のみに使う（CPU スケジューリング遅延対策）。
        """
        worker = _make_worker()
        release_event = threading.Event()
        acquired_lock_event = threading.Event()

        def holder() -> None:
            with worker._lock:
                acquired_lock_event.set()
                release_event.wait(timeout=2.0)

        holder_thread = threading.Thread(target=holder)
        holder_thread.start()
        assert acquired_lock_event.wait(timeout=2.0), "holder_thread が Lock 取得に失敗"

        reset_thread = threading.Thread(target=worker.reset_all)
        reset_thread.start()

        # reset_thread が完了していないことを短時間で確認（Lock 機能中）。
        # join(timeout=0.1) は「完了を 0.1 秒待つ」操作であり、その後の
        # `is_alive()` 呼び出しで「0.1 秒以内に完了していない」ことを確認する。
        # Lock が機能していない場合、reset_all は極めて高速（1ms 以下）に
        # 完了するため 0.1 秒の join で即座に終了し is_alive()=False になる。
        reset_thread.join(timeout=0.1)
        assert reset_thread.is_alive(), (
            "reset_all が Lock 保持中に完了した: Lock が機能していない"
        )

        # Lock を解放 → reset_all が完了できるはず
        release_event.set()
        holder_thread.join(timeout=2.0)
        reset_thread.join(timeout=2.0)
        assert not reset_thread.is_alive(), "reset_all が Lock 解放後も完了しない"

    def test_concurrent_access_no_exceptions(self) -> None:
        """複数スレッドから update_desires/reset_all を並行実行しても例外が出ない。"""
        results: list[str] = []
        errors: list[Exception] = []

        config = _make_config(reflect_episode_threshold=1, reflect_threshold=0.5)

        def counting_callback(desire_type: str) -> None:
            results.append(desire_type)

        worker = _make_worker(
            config=config,
            get_observation_count=lambda: 5,
            on_threshold_exceeded=counting_callback,
        )

        def updater() -> None:
            try:
                for _ in range(10):
                    with patch("time.monotonic", return_value=1000.0):
                        worker.update_desires()
                    worker.reset_all()
            except Exception as e:  # noqa: BLE001  # テストスレッド内の例外を収集
                errors.append(e)

        threads = [threading.Thread(target=updater) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5.0)

        assert not errors, f"Exceptions during concurrent access: {errors}"


# ---------------------------------------------------------------------------
# 20. start/stop 冪等性
# ---------------------------------------------------------------------------


class TestStartStop:
    def test_start_stop_idempotent(self) -> None:
        """start()/stop() を複数回呼んでもエラーにならない（冪等性）。"""
        worker = _make_worker()

        # 二重 start はエラーにならない（or 無視される）
        worker.start()
        first_timer = worker._timer  # type: ignore[attr-defined]
        assert first_timer is not None
        worker.start()
        # iter 1 W-5: 二重 start でも Timer は1つのまま（世代が進まない）
        second_timer = worker._timer  # type: ignore[attr-defined]
        assert second_timer is first_timer, (
            "二重 start で新しい Timer が生成された（冪等性違反）"
        )

        # stop() でタイマーをキャンセル
        worker.stop()

        # 二重 stop もエラーにならない
        worker.stop()

    def test_stop_without_start(self) -> None:
        """start() なしで stop() を呼んでもエラーにならない。"""
        worker = _make_worker()
        worker.stop()  # should not raise

    def test_start_schedules_timer(self) -> None:
        """start() 後にタイマーが設定されて _running=True になる。"""
        worker = _make_worker()
        worker.start()
        try:
            assert worker._running is True  # type: ignore[attr-defined]
            assert worker._timer is not None  # type: ignore[attr-defined]
        finally:
            worker.stop()


# ---------------------------------------------------------------------------
# 境界値: ガード節（idle_minutes_for_talk=0, reflect_threshold=0, rest_threshold=0）
# ---------------------------------------------------------------------------


class TestBoundaryValues:
    def test_talk_level_when_idle_minutes_is_zero(self) -> None:
        """idle_minutes_for_talk=0 のとき talk level は常に 1.0 になる（防御的ガード節）。"""
        config = _make_config(idle_minutes_for_talk=0.0, talk_threshold=0.7)
        worker = _make_worker(config=config)
        base_time = 1000.0

        with patch("time.monotonic", return_value=base_time):
            worker.notify_user_input()
            worker.update_desires()

        state = worker.get_state()
        assert state.desires["talk"].level == pytest.approx(1.0)

    def test_reflect_level_when_threshold_is_zero(self) -> None:
        """reflect_episode_threshold=0 のとき reflect level は常に 1.0 になる（防御的ガード節）。"""
        config = _make_config(reflect_episode_threshold=0, reflect_threshold=0.5)
        worker = _make_worker(config=config, get_observation_count=lambda: 0)

        with patch("time.monotonic", return_value=1000.0):
            worker.update_desires()

        state = worker.get_state()
        assert state.desires["reflect"].level == pytest.approx(1.0)

    def test_rest_level_when_hours_threshold_is_zero(self) -> None:
        """rest_hours_threshold=0 のとき rest level は常に 1.0 になる（防御的ガード節）。"""
        config = _make_config(rest_hours_threshold=0.0, rest_threshold=0.5)
        session_start = 1000.0
        worker = _make_worker(config=config, session_start_time=session_start)

        with patch("time.monotonic", return_value=session_start):
            worker.update_desires()

        state = worker.get_state()
        assert state.desires["rest"].level == pytest.approx(1.0)

    def test_curiosity_level_when_idle_minutes_is_zero(self) -> None:
        """idle_minutes_for_curiosity=0 のとき curiosity は time_weight=1.0 として計算される。

        防御的ガード節のテスト。
        """
        config = _make_config(
            idle_minutes_for_curiosity=0.0,
            curiosity_threshold=0.5,
        )
        worker = _make_worker(
            config=config,
            get_pending_curiosity_count=lambda: 5,
        )
        base_time = 1000.0

        with patch("time.monotonic", return_value=base_time):
            worker.notify_user_input()

        # idle > 2分 が必要
        with patch("time.monotonic", return_value=base_time + 3 * 60):
            worker.update_desires()

        state = worker.get_state()
        # pending_weight=1.0, time_weight=1.0(ガード節) → level=1.0
        assert state.desires["curiosity"].level == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# 21. rest 再通知抑制
# ---------------------------------------------------------------------------


class TestRestSuppression:
    def test_rest_suppress_minutes(self) -> None:
        """rest: 一度発現後、rest_suppress_minutes 以内は再通知しない (W-7: session 注入)."""
        callback = MagicMock()
        config = _make_config(
            rest_threshold=0.9,
            rest_hours_threshold=4.0,
            rest_suppress_minutes=60.0,  # 60分間は再通知しない
        )
        session_start = 1000.0
        worker = _make_worker(
            config=config, on_threshold_exceeded=callback, session_start_time=session_start,
        )

        # uptime 4h: rest level=1.0 > 0.9
        with patch("time.monotonic", return_value=session_start + 4 * 3600):
            worker.update_desires()

        assert callback.call_count == 1

        # 30分後（suppress 期間内）に reset_all + update_desires
        worker.reset_all()
        with patch("time.monotonic", return_value=session_start + 4 * 3600 + 30 * 60):
            worker.update_desires()

        # 抑制されて再通知なし
        assert callback.call_count == 1

    def test_rest_suppress_expired_allows_callback(self) -> None:
        """rest: rest_suppress_minutes 経過後は再通知が許可される (W-7: session 注入)."""
        callback = MagicMock()
        config = _make_config(
            rest_threshold=0.9,
            rest_hours_threshold=4.0,
            rest_suppress_minutes=60.0,
        )
        session_start = 1000.0
        worker = _make_worker(
            config=config, on_threshold_exceeded=callback, session_start_time=session_start,
        )

        # uptime 4h: 1回目超過
        with patch("time.monotonic", return_value=session_start + 4 * 3600):
            worker.update_desires()

        assert callback.call_count == 1
        worker.reset_all()

        # suppress 期間（60分）経過後
        with patch("time.monotonic", return_value=session_start + 4 * 3600 + 61 * 60):
            worker.update_desires()

        assert callback.call_count == 2


# ---------------------------------------------------------------------------
# 22. Lock 解放後にコールバック（デッドロック防止）
# ---------------------------------------------------------------------------


class TestCallbackLockSafety:
    """コールバックの Lock 解放後呼び出しと例外時の Timer 継続を検証する (W-10, W-3)."""

    def test_update_desires_reschedules_timer_when_running(self) -> None:
        """_running=True の update_desires 呼び出しで次の Timer がスケジュールされる (W-10)."""
        worker = _make_worker()
        worker._running = True  # type: ignore[attr-defined]

        try:
            with patch("time.monotonic", return_value=1000.0):
                worker.update_desires()
            assert worker._timer is not None  # type: ignore[attr-defined]
        finally:
            worker.stop()

    def test_callback_can_reacquire_lock(self) -> None:
        """コールバック内で _lock を再取得できる（Lock 解放後呼び出し、R-7 準拠）."""
        worker_ref: list[DesireWorker] = []
        lock_acquirable_in_callback = False

        def callback_tries_lock(desire_type: str) -> None:
            nonlocal lock_acquirable_in_callback
            acquired = worker_ref[0]._lock.acquire(timeout=1.0)  # type: ignore[attr-defined]
            if acquired:
                worker_ref[0]._lock.release()  # type: ignore[attr-defined]
                lock_acquirable_in_callback = True

        config = _make_config(talk_threshold=0.7, idle_minutes_for_talk=30.0)
        worker = _make_worker(config=config, on_threshold_exceeded=callback_tries_lock)
        worker_ref.append(worker)

        base_time = 1000.0
        with patch("time.monotonic", return_value=base_time):
            worker.notify_user_input()
        with patch("time.monotonic", return_value=base_time + 30 * 60):
            worker.update_desires()

        assert lock_acquirable_in_callback, (
            "Lock was not acquirable in callback — possible deadlock or "
            "callback invoked before Lock release (R-7 violation)"
        )

    def test_callback_exception_logged_and_loop_continues(
        self, caplog: pytest.LogCaptureFixture,
    ) -> None:
        """コールバック例外を logger.error で記録し Timer ループが継続する (iter 1 W-4 強化)."""
        def raising_callback(desire_type: str) -> None:
            raise RuntimeError(f"test failure for {desire_type}")

        config = _make_config(talk_threshold=0.7, idle_minutes_for_talk=30.0)
        worker = _make_worker(
            config=config, on_threshold_exceeded=raising_callback,
        )
        # start() 経由で _running を True にする（世代カウンタも正しく更新）
        worker.start()

        base_time = 1000.0
        with patch("time.monotonic", return_value=base_time):
            worker.notify_user_input()

        try:
            with caplog.at_level(logging.ERROR), patch(
                "time.monotonic", return_value=base_time + 30 * 60,
            ):
                # 例外を呼び出し元に伝播させない
                worker.update_desires()

            # ERROR レベルの log record が記録されていること
            error_records = [
                r for r in caplog.records
                if r.levelno == logging.ERROR
                and "on_threshold_exceeded callback raised" in r.getMessage()
            ]
            assert len(error_records) >= 1, (
                "ERROR level log with callback failure message not found"
            )
            # exc_info に例外メッセージが含まれていること
            record = error_records[0]
            assert record.exc_info is not None
            assert "test failure for talk" in str(record.exc_info[1])

            # 次の Timer がスケジュールされていることを確認（ループ継続）
            assert worker._timer is not None  # type: ignore[attr-defined]
        finally:
            worker.stop()
