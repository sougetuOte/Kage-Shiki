"""Phase 2b DesireWorker — 4 欲求（talk/curiosity/reflect/rest）の更新エンジン.

設計書: docs/specs/phase2b-autonomy/design.md Section 3
対応 FR: FR-9.1, FR-9.2

欲求レベルは永続化しない（要件書 Section 4.2）。
再起動時は level=0.0 / active=False で初期化される。
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass, field

from kage_shiki.core.config import DesireConfig

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# データクラス
# ---------------------------------------------------------------------------


@dataclass
class DesireLevel:
    """単一欲求の状態.

    要件書 Section 4.2 の DesireLevel データモデルに準拠。

    Attributes:
        level: 欲求レベル（0.0〜1.0）。
        threshold: 発現閾値（config から読み込み）。
        last_updated: 最終更新時刻（time.monotonic()）。
        active: 閾値超過で通知済みの間は True、`reset_all()` 後は False。
            通知重複抑制のガードとして機能する。
            **rest 欲求のみ例外**: rest は `rest_suppress_minutes` による
            独自の抑制ロジックを持つため、抑制期間中は level>threshold でも
            active=False のまま維持される。rest の「発現済み」判定は
            `_rest_last_notified_time` で管理され、active フラグは
            「連続通知の短期抑制」ではなく「長期通知抑制」のセマンティクスを
            持たない。この非対称性は設計上の意図であり、Timer のたびに
            抑制チェックのみが走ることを許容する（計算コストは無視できる）。
    """

    level: float = 0.0
    threshold: float = 0.0
    last_updated: float = 0.0
    active: bool = False


@dataclass
class DesireState:
    """全欲求の現在状態.

    Attributes:
        desires: 欲求タイプ -> DesireLevel のマッピング。
                 キー: "talk" | "curiosity" | "reflect" | "rest"
    """

    desires: dict[str, DesireLevel] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# 欲求計算関数（純粋関数、LLM 不要）
# ---------------------------------------------------------------------------

# curiosity 欲求の抑制閾値: idle 時間がこの値未満のときはユーザーがアクティブと
# 見なし curiosity を抑制する（分）。
_CURIOSITY_USER_ACTIVE_SUPPRESS_MINUTES = 2.0

# curiosity pending 飽和件数
_CURIOSITY_PENDING_SATURATION = 5


def _calc_talk_level(
    elapsed_idle_seconds: float,
    idle_minutes_for_talk: float,
) -> float:
    """talk 欲求レベルを計算する.

    level = min(1.0, elapsed_idle_minutes / idle_minutes_for_talk)

    Args:
        elapsed_idle_seconds: 最後のユーザー入力からの経過時間（秒）。
        idle_minutes_for_talk: talk 閾値到達までの無入力時間（分）。

    Returns:
        0.0〜1.0 の talk レベル。

    Note:
        `idle_minutes_for_talk <= 0` の場合はゼロ除算を避けて即座に 1.0 を返す
        防御的ガード（パラメータ誤設定時の安全動作）。
    """
    if idle_minutes_for_talk <= 0:
        return 1.0
    elapsed_minutes = elapsed_idle_seconds / 60.0
    return min(1.0, elapsed_minutes / idle_minutes_for_talk)


def _calc_curiosity_level(
    elapsed_idle_seconds: float,
    pending_count: int,
    idle_minutes_for_curiosity: float,
) -> float:
    """curiosity 欲求レベルを計算する.

    pending_weight = min(1.0, pending_count / 5)
    time_weight    = min(1.0, elapsed_idle_minutes / idle_minutes_for_curiosity)
    level          = pending_weight * time_weight

    ユーザーアクティブ（idle < 2分）のとき time_weight=0 で level=0 になる。
    pending=0 のとき level=0。

    Args:
        elapsed_idle_seconds: 最後のユーザー入力からの経過時間（秒）。
        pending_count: curiosity_targets の status=pending レコード数。
        idle_minutes_for_curiosity: curiosity 上昇開始までの無入力時間（分）。

    Returns:
        0.0〜1.0 の curiosity レベル。

    Note:
        `idle_minutes_for_curiosity <= 0` の場合はゼロ除算を避けて
        `time_weight=1.0` にフォールバックする防御的ガード。
    """
    if pending_count == 0:
        return 0.0

    elapsed_minutes = elapsed_idle_seconds / 60.0

    # ユーザーアクティブ中（idle < 2分）は time_weight=0 で抑制
    if elapsed_minutes < _CURIOSITY_USER_ACTIVE_SUPPRESS_MINUTES:
        return 0.0

    if idle_minutes_for_curiosity <= 0:
        time_weight = 1.0
    else:
        time_weight = min(1.0, elapsed_minutes / idle_minutes_for_curiosity)

    pending_weight = min(1.0, pending_count / _CURIOSITY_PENDING_SATURATION)
    return pending_weight * time_weight


def _calc_reflect_level(
    observation_count: int,
    reflect_episode_threshold: int,
) -> float:
    """reflect 欲求レベルを計算する.

    level = min(1.0, unprocessed_episodes / reflect_episode_threshold)

    Args:
        observation_count: 前回 reflect 発現以降に蓄積された observations 件数。
        reflect_episode_threshold: reflect 発現までの件数閾値。

    Returns:
        0.0〜1.0 の reflect レベル。

    Note:
        `reflect_episode_threshold <= 0` の場合はゼロ除算を避けて
        即座に 1.0 を返す防御的ガード。
    """
    if reflect_episode_threshold <= 0:
        return 1.0
    return min(1.0, observation_count / reflect_episode_threshold)


def _calc_rest_level(
    current_time: float,
    session_start_time: float,
    rest_hours_threshold: float,
) -> float:
    """rest 欲求レベルを計算する.

    uptime_hours = (current_time - session_start_time) / 3600
    level = min(1.0, uptime_hours / rest_hours_threshold)

    Args:
        current_time: 現在時刻（time.monotonic()）。
        session_start_time: セッション開始時刻（time.monotonic()）。
        rest_hours_threshold: rest 発現までの稼働時間（時間）。

    Returns:
        0.0〜1.0 の rest レベル。

    Note:
        `rest_hours_threshold <= 0` の場合はゼロ除算を避けて
        即座に 1.0 を返す防御的ガード。
        `time.monotonic()` を使用するのはシステム時計のスキュー
        （NTP 補正等）の影響を受けないためであり、再起動をまたぐ
        絶対時刻計算には使用しない（設計書 Section 3.2 参照）。
    """
    if rest_hours_threshold <= 0:
        return 1.0
    uptime_hours = (current_time - session_start_time) / 3600.0
    return min(1.0, uptime_hours / rest_hours_threshold)


# ---------------------------------------------------------------------------
# DesireWorker
# ---------------------------------------------------------------------------

# 欲求タイプの有限セット（R-2: dict ディスパッチで処理）
_DESIRE_TYPES = ("talk", "curiosity", "reflect", "rest")


class DesireWorker:
    """4 欲求（talk/curiosity/reflect/rest）のレベルを定期更新するワーカー.

    threading.Timer による定期実行で update_desires() を呼び出す。
    欲求が閾値を超えた際に on_threshold_exceeded コールバックを呼ぶ。

    スレッド安全性:
        _lock が update_desires() / reset_all() / get_state() / start() / stop()
        の状態遷移を排他制御する。コールバック（on_threshold_exceeded）は
        _lock 解放後に呼び出す（デッドロック防止、R-7）。コールバック内での
        例外は logger.error でログ記録して握りつぶさず、Timer ループは継続する
        （Noisy Failure）。

        notify_user_input() は `_last_user_input_time` への単一代入のみを行うため、
        GIL 保護により意図的に _lock を取得しない（高頻度呼び出し時のロック競合を
        避けるため）。Lock 境界の非対称性は意図的な設計判断。

    Note:
        notify_user_input() は要件書 Section 5.1 の Protocol 定義外メソッドであり、
        building-checklist.md S-2 に準拠して明示する。
    """

    def __init__(
        self,
        config: DesireConfig,
        get_pending_curiosity_count: Callable[[], int],
        get_observation_count: Callable[[], int],
        on_threshold_exceeded: Callable[[str], None],
        session_start_time: float | None = None,
    ) -> None:
        """DesireWorker を初期化する.

        Args:
            config: DesireConfig（閾値・間隔などの設定）。
            get_pending_curiosity_count: curiosity_targets の pending 件数を返すコールバック。
            get_observation_count: 前回 reflect 発現以降の observations 件数を返すコールバック。
            on_threshold_exceeded: 閾値超過時に呼び出すコールバック（引数: desire_type: str）。
            session_start_time: セッション開始時刻（`time.monotonic()` ベース）。
                省略時は現在時刻を使用する。テスト時に任意の値を注入して rest 欲求の
                uptime 計算を制御するためのカプセル化改善用パラメータ。
        """
        self._config = config
        self._get_pending_curiosity_count = get_pending_curiosity_count
        self._get_observation_count = get_observation_count
        self._on_threshold_exceeded = on_threshold_exceeded

        # 排他制御用 Lock（R-7）
        self._lock = threading.Lock()

        # 各欲求の状態を初期化
        threshold_map: dict[str, float] = {
            "talk": config.talk_threshold,
            "curiosity": config.curiosity_threshold,
            "reflect": config.reflect_threshold,
            "rest": config.rest_threshold,
        }
        self._desires: dict[str, DesireLevel] = {
            desire_type: DesireLevel(threshold=threshold_map[desire_type])
            for desire_type in _DESIRE_TYPES
        }

        now = time.monotonic()
        # セッション開始時刻（rest 欲求の uptime 計算に使用、テスト注入可能）
        self._session_start_time: float = (
            session_start_time if session_start_time is not None else now
        )

        # 最終ユーザー入力時刻（talk/curiosity の idle 計算に使用）
        self._last_user_input_time: float = now

        # rest 欲求の最終通知時刻（再通知抑制に使用）
        self._rest_last_notified_time: float = 0.0

        # 定期実行タイマー
        self._timer: threading.Timer | None = None
        self._running: bool = False
        # start/stop の世代カウンタ。stop→start を経た update_desires が古い
        # 世代の Timer を二重スケジュールすることを防ぐ（iter 1 W-A4-1 対応）。
        self._start_generation: int = 0

    # ------------------------------------------------------------------
    # パブリックメソッド
    # ------------------------------------------------------------------

    def start(self) -> None:
        """定期更新ループを開始する.

        すでに起動済みの場合は何もしない（冪等性）。
        threading.Timer は一回限りのため、update_desires() 末尾で
        次の Timer を再スケジュールする。

        Note:
            _lock を取得して _running / _timer の読み書きを排他制御する。
        """
        with self._lock:
            if self._running:
                return
            self._running = True
            self._start_generation += 1
            self._schedule_next_locked()

    def stop(self) -> None:
        """更新ループを停止し、次回タイマーをキャンセルする.

        すでに停止済みの場合は何もしない（冪等性）。
        実行中の update_desires() が完了するまで次の Timer は起動しない
        （cancel() で次回タイマーをキャンセルするのみ）。

        Note:
            _lock を取得して _running / _timer の読み書きを排他制御する。
            `_schedule_next_locked()` との競合ウィンドウを閉じ、stop 後に
            古い Timer が残存する可能性を排除する。
            `_start_generation` を進めることで、コールバック実行中の
            update_desires が古い世代の再スケジュールを行うことを防ぐ。
        """
        with self._lock:
            self._running = False
            self._start_generation += 1
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None

    def update_desires(self) -> None:
        """全欲求レベルを再計算し、閾値超過があれば on_threshold_exceeded を呼ぶ.

        入力値収集（`_last_user_input_time`, pending/observation カウント）は
        Lock 外で実施し、level 更新と active フラグ遷移を `_lock` 内で排他制御
        する。コールバック（`on_threshold_exceeded`）は `_lock` 解放後に呼び出す
        （デッドロック防止、R-7）。コールバック内の例外は `logger.error` で
        記録して握りつぶさず、Timer ループは継続する（Noisy Failure）。
        LLM 呼び出しなし（NFR-14 準拠）。

        次の Timer の再スケジュールは Lock 再取得後に `_start_generation` を
        チェックしてから行う。コールバック実行中に stop→start が発生して
        世代が進んでいる場合は schedule をスキップし、Timer 二重起動を防ぐ
        （iter 1 W-A4-1 対応）。
        """
        # 入力値は Lock 外で取得する（コールバックは DB クエリを含む可能性があり、
        # Lock 保持のデッドロック回避のため）。GIL 下での単一代入読み取りで整合する。
        now = time.monotonic()
        elapsed_idle_seconds = now - self._last_user_input_time
        pending_count = self._get_pending_curiosity_count()
        observation_count = self._get_observation_count()

        # 各欲求の計算関数（R-2: dict ディスパッチ）
        level_calculators: dict[str, Callable[[], float]] = {
            "talk": lambda: _calc_talk_level(
                elapsed_idle_seconds, self._config.idle_minutes_for_talk
            ),
            "curiosity": lambda: _calc_curiosity_level(
                elapsed_idle_seconds, pending_count, self._config.idle_minutes_for_curiosity
            ),
            "reflect": lambda: _calc_reflect_level(
                observation_count, self._config.reflect_episode_threshold
            ),
            "rest": lambda: _calc_rest_level(
                now, self._session_start_time, self._config.rest_hours_threshold
            ),
        }

        # Lock 内で level を更新し、通知すべき欲求タイプを収集する
        # コールバックは Lock 解放後に呼ぶ（デッドロック防止、R-7）
        exceeded_types: list[str] = []

        with self._lock:
            # 自分を起動した Timer の世代をスナップショット（W-A4-1 対応）
            my_generation = self._start_generation
            for desire_type in _DESIRE_TYPES:
                new_level = level_calculators[desire_type]()
                desire = self._desires[desire_type]
                desire.level = new_level
                desire.last_updated = now

                if new_level > desire.threshold and not desire.active:
                    # rest のみ再通知抑制ロジック
                    if desire_type == "rest":
                        suppress_secs = self._config.rest_suppress_minutes * 60.0
                        if now - self._rest_last_notified_time < suppress_secs:
                            continue
                        self._rest_last_notified_time = now

                    desire.active = True
                    exceeded_types.append(desire_type)

        # Lock 解放後にコールバックを呼ぶ（R-7）。
        # コールバック内の例外は握りつぶさずログ記録して処理継続する
        # （Noisy Failure パターン。Silent Failure 禁止、Timer ループ停止防止）。
        for desire_type in exceeded_types:
            try:
                self._on_threshold_exceeded(desire_type)
            except Exception:
                logger.error(
                    "on_threshold_exceeded callback raised for desire_type=%r",
                    desire_type,
                    exc_info=True,
                )

        # 次のタイマーをスケジュール。stop→start 世代跳躍時は schedule しない
        # （iter 1 W-A4-1: Timer 二重起動防止）。
        with self._lock:
            if self._running and self._start_generation == my_generation:
                self._schedule_next_locked()

    def reset_all(self) -> None:
        """全欲求の active を False にリセットする（FR-9.5）.

        _lock を取得して実行する。ユーザー入力時に呼び出す。

        Note:
            本メソッドは active フラグのみをリセットする。
            idle タイマー（`_last_user_input_time`）のリセットは
            `notify_user_input()` が担当するため、両者を組み合わせて使用する
            （設計書 Section 3.4 の使用例参照）。

            **呼び出しタイミング制約**: 本メソッドは「ユーザー入力受信時の
            メインスレッド」からの呼び出しを想定しており、`on_threshold_exceeded`
            コールバック**内部**から呼ぶことは推奨されない。理由は、コールバック
            自体が `update_desires()` の Lock 解放後・次サイクル Lock 再取得前に
            実行されるため、コールバック中の `reset_all()` で `active=False` に
            戻してしまうと、次の `update_desires()` サイクルで同じ欲求が再発火
            する可能性がある（active 汚染シナリオ）。
            ユーザー入力経路 (`main.py` の `_run_background_loop`) からのみ
            呼び出すこと。
        """
        with self._lock:
            for desire in self._desires.values():
                desire.active = False

    def notify_user_input(self) -> None:
        """ユーザー入力を通知し、idle タイマーをリセットする.

        _last_user_input_time を現在時刻に更新することで、
        talk/curiosity の idle 計算をリセットする。

        Note:
            本メソッドは要件書 Section 5.1 の Protocol 定義外メソッドであり、
            building-checklist.md S-2 に準拠して明示する。

            スレッド安全性: CPython の GIL 保護下における float 単一代入の
            アトミック性に依存し、意図的に `_lock` を取得しない。
            No-GIL ビルド（Python 3.13+ の free-threaded 環境）では
            `_lock` による保護が必要になる点に注意（iter 1 W-A4-2 対応）。
        """
        self._last_user_input_time = time.monotonic()

    def get_state(self) -> DesireState:
        """現在の DesireState を返す（テスト・デバッグ用）.

        Returns:
            内部状態のディープコピーから生成した DesireState。
            呼び出し元による変更が内部状態に影響しない。
        """
        with self._lock:
            return DesireState(desires=deepcopy(self._desires))

    # ------------------------------------------------------------------
    # プライベートメソッド
    # ------------------------------------------------------------------

    def _schedule_next_locked(self) -> None:
        """次の update_desires タイマーをスケジュールする（_lock 保持前提）.

        Precondition:
            - 呼び出し元が `self._lock` を取得していること
              （`_timer` の書き込みを排他制御するため）。
            - `self._timer` は None、または既に発火済みで `cancel()` 不要な状態であること。
              `threading.Timer` は一回限りのため、`update_desires()` の末尾から
              呼ばれる通常フローでは旧 Timer は既に実行完了直前であり参照上書きで
              問題ない。`start()` から呼ばれる場合は直前の `if self._running: return`
              ガード（L296）を経由するため、`_timer` が None（初回起動）か、
              直前の `stop()` が既に `_timer=None` をセット済み（再起動）のいずれか。
              事前に active な Timer を残したまま本メソッドを呼ぶと Timer 二重起動を
              引き起こすため禁止（世代管理は `_start_generation` で担保）。
            - 本メソッドは Timer のコールバック経路から呼ばれることを前提とし、
              テストコード等から `update_desires()` を直接呼ぶ場合は事前に
              `_running=False` を設定するか、呼び出し後に `stop()` でクリーンアップ
              する必要がある。

        Postcondition:
            - `self._timer` に新しい `threading.Timer` が割り当てられ、起動済み。
        """
        self._timer = threading.Timer(
            interval=self._config.update_interval_sec,
            function=self.update_desires,
        )
        self._timer.daemon = True
        self._timer.start()
