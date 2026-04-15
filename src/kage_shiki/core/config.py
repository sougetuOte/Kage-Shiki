"""AppConfig dataclass + config.toml 読み書き (T-02).

対応 FR:
    FR-1.1: config.toml を読み込み、全設定値をアプリケーションに反映
    FR-1.2: config.toml が存在しない場合、デフォルト値で config.toml を生成
    FR-1.3: config.toml の値が不正な場合、デフォルト値にフォールバックし警告表示
"""

import logging
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# バリデーション定数
# ---------------------------------------------------------------------------

_TEMPERATURE_MIN = 0.0
_TEMPERATURE_MAX = 2.0
_OPACITY_MIN = 0.0
_OPACITY_MAX = 1.0
_DEFAULT_LOG_MAX_BYTES = 5 * 1024 * 1024  # 5MB

# get_max_tokens の固定値（D-15）
_MAX_TOKENS_WIZARD_GENERATE = 2048
_MAX_TOKENS_WIZARD_PREVIEW = 1024
_MAX_TOKENS_WIZARD_ASSOCIATION = 512
_MAX_TOKENS_MEMORY_WORKER = 800
_MAX_TOKENS_MEMORY_SUMMARY = 800
_MAX_TOKENS_HUMAN_BLOCK_UPDATE = 256
_MAX_TOKENS_POKE = 256

# Phase 2b: 自律発言用の固定 max_tokens
_MAX_TOKENS_AUTONOMOUS_TALK = 256
_MAX_TOKENS_AGENTIC_DECOMPOSE = 256
_MAX_TOKENS_AGENTIC_SUMMARIZE = 512
_MAX_TOKENS_AGENTIC_NOISE = 256

# 用途別 max_tokens マップ（conversation 以外の固定値）
_MAX_TOKENS_MAP: dict[str, int] = {
    "wizard_generate": _MAX_TOKENS_WIZARD_GENERATE,
    "wizard_preview": _MAX_TOKENS_WIZARD_PREVIEW,
    "wizard_association": _MAX_TOKENS_WIZARD_ASSOCIATION,
    "memory_worker": _MAX_TOKENS_MEMORY_WORKER,
    "memory_summary": _MAX_TOKENS_MEMORY_SUMMARY,
    "human_block_update": _MAX_TOKENS_HUMAN_BLOCK_UPDATE,
    "poke": _MAX_TOKENS_POKE,
    # Phase 2b: 自律発言・AgenticSearch 用 purpose（design.md Section 7.3）
    "autonomous_talk": _MAX_TOKENS_AUTONOMOUS_TALK,
    "agentic_decompose": _MAX_TOKENS_AGENTIC_DECOMPOSE,
    "agentic_summarize": _MAX_TOKENS_AGENTIC_SUMMARIZE,
    "agentic_noise": _MAX_TOKENS_AGENTIC_NOISE,
}

# 用途別モデルスロットマップ
_PURPOSE_MODEL_SLOTS: dict[str, str] = {
    "conversation": "conversation",
    "poke": "conversation",
    "wizard_preview": "conversation",
    "wizard_generate": "wizard",
    "wizard_association": "wizard",
    "memory_worker": "memory_worker",
    "memory_summary": "memory_worker",
    "human_block_update": "utility",
    # Phase 2b: 自律発言・AgenticSearch 用 purpose（design.md Section 7.3）
    "autonomous_talk": "conversation",
    "agentic_decompose": "utility",
    "agentic_summarize": "utility",
    "agentic_noise": "utility",
}

# ---------------------------------------------------------------------------
# Purpose 管理 (D-15) — SSOT
# ---------------------------------------------------------------------------

VALID_PURPOSES: frozenset[str] = frozenset({
    "conversation",
    "wizard_generate",
    "wizard_preview",
    "wizard_association",
    "memory_worker",
    "memory_summary",
    "human_block_update",
    "poke",
    # Phase 2b: 自律発言・AgenticSearch 用 purpose（design.md Section 7.3）
    "autonomous_talk",
    "agentic_decompose",
    "agentic_summarize",
    "agentic_noise",
})

# 用途別 temperature オーバーライド（None = config.conversation.temperature を使用）
_PURPOSE_TEMPERATURES: dict[str, float | None] = {
    "conversation": None,
    "wizard_generate": 0.9,
    "wizard_preview": None,
    "wizard_association": 0.9,
    "memory_worker": 0.3,
    "memory_summary": 0.3,
    "human_block_update": 0.3,
    "poke": None,
    # Phase 2b: 自律発言・AgenticSearch 用 purpose（design.md Section 7.3）
    "autonomous_talk": 0.9,
    "agentic_decompose": 0.3,
    "agentic_summarize": 0.3,
    "agentic_noise": 0.5,
}


# ---------------------------------------------------------------------------
# セクション dataclass
# ---------------------------------------------------------------------------


@dataclass
class GeneralConfig:
    """[general] セクション設定.

    Attributes:
        persona_frozen: ペルソナ固定フラグ。True のとき学習を停止する。
        data_dir: データディレクトリパス。
    """

    persona_frozen: bool = False
    data_dir: str = "./data"


@dataclass
class ModelsConfig:
    """[models] セクション設定.

    Attributes:
        conversation: 会話用モデル ID。
        memory_worker: 記憶ワーカー用モデル ID。
        utility: ユーティリティ用モデル ID。
        wizard: ウィザード用モデル ID。
    """

    conversation: str = "claude-haiku-4-5-20251001"
    memory_worker: str = "claude-haiku-4-5-20251001"
    utility: str = "claude-haiku-4-5-20251001"
    wizard: str = "claude-haiku-4-5-20251001"


@dataclass
class WizardConfig:
    """[wizard] セクション設定.

    Attributes:
        association_count: 連想キーワード数。
        temperature: サンプリング温度（0.0〜2.0）。
        candidate_count: 候補生成数。
        blank_freeze_threshold: 空白フリーズ閾値（会話数）。
    """

    association_count: int = 5
    temperature: float = 0.9
    candidate_count: int = 3
    blank_freeze_threshold: int = 20


@dataclass
class ConversationConfig:
    """[conversation] セクション設定.

    Attributes:
        temperature: サンプリング温度（0.0〜2.0）。
        max_tokens: 最大トークン数。
    """

    temperature: float = 0.7
    max_tokens: int = 1024


@dataclass
class GuiConfig:
    """[gui] セクション設定.

    Attributes:
        window_width: ウィンドウ幅（ピクセル）。
        window_height: ウィンドウ高さ（ピクセル）。
        opacity: ウィンドウ不透明度（0.0〜1.0）。
        topmost: 最前面固定フラグ。
        font_size: フォントサイズ（pt）。
        font_family: フォントファミリー。空文字はシステムデフォルト。
    """

    window_width: int = 400
    window_height: int = 450
    opacity: float = 0.95
    topmost: bool = True
    font_size: int = 14
    font_family: str = field(default="")


@dataclass
class MemoryConfig:
    """[memory] セクション設定.

    Attributes:
        warm_days: ウォームメモリ保持日数。
        cold_top_k: コールドメモリ上位 K 件。
        consistency_interval: 一貫性チェック間隔（メッセージ数）。
    """

    warm_days: int = 5
    cold_top_k: int = 5
    consistency_interval: int = 15


@dataclass
class ApiConfig:
    """[api] セクション設定.

    Attributes:
        max_retries: 最大リトライ回数。
        retry_backoff_base: リトライバックオフ基数（秒）。
        timeout: タイムアウト（秒）。
    """

    max_retries: int = 3
    retry_backoff_base: float = 2.0
    timeout: int = 30


@dataclass
class TrayConfig:
    """[tray] セクション設定.

    Attributes:
        minimize_to_tray: 最小化時にトレイに格納するか。
    """

    minimize_to_tray: bool = True


@dataclass
class LoggingConfig:
    """[logging] セクション設定.

    Attributes:
        level: コンソールログレベル。
        file_level: ファイルログレベル。
        max_bytes: ログファイル最大サイズ（バイト）。
        backup_count: ログファイルバックアップ数。
    """

    level: str = "INFO"
    file_level: str = "DEBUG"
    max_bytes: int = _DEFAULT_LOG_MAX_BYTES
    backup_count: int = 3


@dataclass
class DesireConfig:
    """[desire] セクション設定 (Phase 2b).

    DesireWorker の欲求計算・閾値・間隔を定義する。
    設計書 docs/specs/phase2b-autonomy/design.md Section 7.1 に準拠。

    Attributes:
        update_interval_sec: 欲求更新間隔（秒）。
        talk_threshold: talk 欲求の発現閾値。
        curiosity_threshold: curiosity 欲求の発現閾値。
        reflect_threshold: reflect 欲求の発現閾値。
        rest_threshold: rest 欲求の発現閾値。
        idle_minutes_for_talk: talk 閾値到達までの無入力時間（分）。
        idle_minutes_for_curiosity: curiosity 上昇開始までの無入力時間（分）。
        reflect_episode_threshold: reflect 発現までの observations 蓄積件数。
        rest_hours_threshold: rest 発現までの稼働時間（時間）。
        rest_suppress_minutes: rest 再通知抑制時間（分）。
    """

    update_interval_sec: float = 7.5
    talk_threshold: float = 0.7
    curiosity_threshold: float = 0.6
    reflect_threshold: float = 0.8
    rest_threshold: float = 0.9
    idle_minutes_for_talk: float = 30.0
    idle_minutes_for_curiosity: float = 15.0
    reflect_episode_threshold: int = 20
    rest_hours_threshold: float = 4.0
    rest_suppress_minutes: float = 60.0


# Phase 2b: AgenticSearch の有効値セット（R-2: frozenset ディスパッチ）
_VALID_AGENTIC_ENGINES: frozenset[str] = frozenset({"haiku", "local"})
_VALID_AGENTIC_SEARCH_APIS: frozenset[str] = frozenset({"duckduckgo", "brave"})


@dataclass
class AgenticSearchConfig:
    """[agentic_search] セクション設定 (Phase 2b).

    AgenticSearch エンジンの選択・検索 API・並列数を定義する。
    設計書 docs/specs/phase2b-autonomy/design.md Section 7.1 に準拠。

    Attributes:
        engine: エンジン種別（"haiku" | "local"）。
        search_api: 検索 API（"duckduckgo" | "brave"）。
        max_subqueries: サブクエリ最大数。
        max_concurrent_searches: 並列検索数上限。
    """

    engine: str = "haiku"
    search_api: str = "duckduckgo"
    max_subqueries: int = 3
    max_concurrent_searches: int = 3


@dataclass
class AppConfig:
    """アプリケーション全体設定.

    各セクションを対応する dataclass として保持する。

    Attributes:
        general: [general] セクション設定。
        models: [models] セクション設定。
        wizard: [wizard] セクション設定。
        conversation: [conversation] セクション設定。
        gui: [gui] セクション設定。
        memory: [memory] セクション設定。
        api: [api] セクション設定。
        tray: [tray] セクション設定。
        logging: [logging] セクション設定。
        desire: [desire] セクション設定 (Phase 2b)。
        agentic_search: [agentic_search] セクション設定 (Phase 2b)。
    """

    general: GeneralConfig = field(default_factory=GeneralConfig)
    models: ModelsConfig = field(default_factory=ModelsConfig)
    wizard: WizardConfig = field(default_factory=WizardConfig)
    conversation: ConversationConfig = field(default_factory=ConversationConfig)
    gui: GuiConfig = field(default_factory=GuiConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    api: ApiConfig = field(default_factory=ApiConfig)
    tray: TrayConfig = field(default_factory=TrayConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    desire: DesireConfig = field(default_factory=DesireConfig)
    agentic_search: AgenticSearchConfig = field(default_factory=AgenticSearchConfig)


# ---------------------------------------------------------------------------
# バリデーションヘルパー
# ---------------------------------------------------------------------------


def _is_valid_type(value: Any, expected_type: type) -> bool:
    """値が期待する型かどうかを判定する。

    Python では bool が int のサブクラスであるため、int フィールドに bool が
    入り込む問題を防ぐために型の厳密チェックを行う。

    Args:
        value: 検査対象の値。
        expected_type: 期待する型。

    Returns:
        型が一致する場合 True。
    """
    if expected_type is int and isinstance(value, bool):
        # bool は int のサブクラスだが、int フィールドには bool を受け付けない
        return False
    if expected_type is float and isinstance(value, int) and not isinstance(value, bool):
        # TOML では 1 は int、1.0 は float だが、float フィールドには int も許容する
        return True
    return isinstance(value, expected_type)


def _coerce_field(
    section_name: str,
    field_name: str,
    raw_value: Any,
    expected_type: type,
    default_value: Any,
    min_value: float | None = None,
    max_value: float | None = None,
) -> Any:
    """フィールド値を検証し、不正ならデフォルト値にフォールバックする。

    Args:
        section_name: TOML セクション名（ログ出力用）。
        field_name: フィールド名（ログ出力用）。
        raw_value: TOML から読み込んだ生の値。
        expected_type: 期待する型。
        default_value: フォールバック時に使用するデフォルト値。
        min_value: 数値の下限（None で無制限）。
        max_value: 数値の上限（None で無制限）。

    Returns:
        検証済みの値、または default_value。
    """
    # 型チェック（bool/int のサブクラス問題を考慮した厳密チェック）
    if not _is_valid_type(raw_value, expected_type):
        logger.warning(
            "config [%s].%s: expected %s, got %s (%r). Using default: %r",
            section_name,
            field_name,
            expected_type.__name__,
            type(raw_value).__name__,
            raw_value,
            default_value,
        )
        return default_value

    # TOML int → float 変換（_is_valid_type が許容した場合）
    if expected_type is float and isinstance(raw_value, int):
        raw_value = float(raw_value)

    # 範囲チェック
    if min_value is not None and raw_value < min_value:
        logger.warning(
            "config [%s].%s: value %r is below minimum %r. Using default: %r",
            section_name,
            field_name,
            raw_value,
            min_value,
            default_value,
        )
        return default_value

    if max_value is not None and raw_value > max_value:
        logger.warning(
            "config [%s].%s: value %r is above maximum %r. Using default: %r",
            section_name,
            field_name,
            raw_value,
            max_value,
            default_value,
        )
        return default_value

    return raw_value


# ---------------------------------------------------------------------------
# セクションパーサー
# ---------------------------------------------------------------------------


def _parse_general(data: dict[str, Any]) -> GeneralConfig:
    """[general] セクションをパースする。

    Args:
        data: [general] セクションの生データ。

    Returns:
        検証済み GeneralConfig。
    """
    defaults = GeneralConfig()
    return GeneralConfig(
        persona_frozen=_coerce_field(
            "general", "persona_frozen",
            data.get("persona_frozen", defaults.persona_frozen),
            bool, defaults.persona_frozen,
        ),
        data_dir=_coerce_field(
            "general", "data_dir",
            data.get("data_dir", defaults.data_dir),
            str, defaults.data_dir,
        ),
    )


def _parse_models(data: dict[str, Any]) -> ModelsConfig:
    """[models] セクションをパースする。

    Args:
        data: [models] セクションの生データ。

    Returns:
        検証済み ModelsConfig。
    """
    defaults = ModelsConfig()
    return ModelsConfig(
        conversation=_coerce_field(
            "models", "conversation",
            data.get("conversation", defaults.conversation),
            str, defaults.conversation,
        ),
        memory_worker=_coerce_field(
            "models", "memory_worker",
            data.get("memory_worker", defaults.memory_worker),
            str, defaults.memory_worker,
        ),
        utility=_coerce_field(
            "models", "utility",
            data.get("utility", defaults.utility),
            str, defaults.utility,
        ),
        wizard=_coerce_field(
            "models", "wizard",
            data.get("wizard", defaults.wizard),
            str, defaults.wizard,
        ),
    )


def _parse_wizard(data: dict[str, Any]) -> WizardConfig:
    """[wizard] セクションをパースする。

    Args:
        data: [wizard] セクションの生データ。

    Returns:
        検証済み WizardConfig。
    """
    defaults = WizardConfig()
    return WizardConfig(
        association_count=_coerce_field(
            "wizard", "association_count",
            data.get("association_count", defaults.association_count),
            int, defaults.association_count, min_value=1,
        ),
        temperature=_coerce_field(
            "wizard", "temperature",
            data.get("temperature", defaults.temperature),
            float, defaults.temperature,
            min_value=_TEMPERATURE_MIN, max_value=_TEMPERATURE_MAX,
        ),
        candidate_count=_coerce_field(
            "wizard", "candidate_count",
            data.get("candidate_count", defaults.candidate_count),
            int, defaults.candidate_count, min_value=1,
        ),
        blank_freeze_threshold=_coerce_field(
            "wizard", "blank_freeze_threshold",
            data.get("blank_freeze_threshold", defaults.blank_freeze_threshold),
            int, defaults.blank_freeze_threshold, min_value=0,
        ),
    )


def _parse_conversation(data: dict[str, Any]) -> ConversationConfig:
    """[conversation] セクションをパースする。

    Args:
        data: [conversation] セクションの生データ。

    Returns:
        検証済み ConversationConfig。
    """
    defaults = ConversationConfig()
    return ConversationConfig(
        temperature=_coerce_field(
            "conversation", "temperature",
            data.get("temperature", defaults.temperature),
            float, defaults.temperature,
            min_value=_TEMPERATURE_MIN, max_value=_TEMPERATURE_MAX,
        ),
        max_tokens=_coerce_field(
            "conversation", "max_tokens",
            data.get("max_tokens", defaults.max_tokens),
            int, defaults.max_tokens, min_value=1,
        ),
    )


def _parse_gui(data: dict[str, Any]) -> GuiConfig:
    """[gui] セクションをパースする。

    Args:
        data: [gui] セクションの生データ。

    Returns:
        検証済み GuiConfig。
    """
    defaults = GuiConfig()
    return GuiConfig(
        window_width=_coerce_field(
            "gui", "window_width",
            data.get("window_width", defaults.window_width),
            int, defaults.window_width, min_value=1,
        ),
        window_height=_coerce_field(
            "gui", "window_height",
            data.get("window_height", defaults.window_height),
            int, defaults.window_height, min_value=1,
        ),
        opacity=_coerce_field(
            "gui", "opacity",
            data.get("opacity", defaults.opacity),
            float, defaults.opacity,
            min_value=_OPACITY_MIN, max_value=_OPACITY_MAX,
        ),
        topmost=_coerce_field(
            "gui", "topmost",
            data.get("topmost", defaults.topmost),
            bool, defaults.topmost,
        ),
        font_size=_coerce_field(
            "gui", "font_size",
            data.get("font_size", defaults.font_size),
            int, defaults.font_size, min_value=1,
        ),
        font_family=_coerce_field(
            "gui", "font_family",
            data.get("font_family", defaults.font_family),
            str, defaults.font_family,
        ),
    )


def _parse_memory(data: dict[str, Any]) -> MemoryConfig:
    """[memory] セクションをパースする。

    Args:
        data: [memory] セクションの生データ。

    Returns:
        検証済み MemoryConfig。
    """
    defaults = MemoryConfig()
    return MemoryConfig(
        warm_days=_coerce_field(
            "memory", "warm_days",
            data.get("warm_days", defaults.warm_days),
            int, defaults.warm_days, min_value=0,
        ),
        cold_top_k=_coerce_field(
            "memory", "cold_top_k",
            data.get("cold_top_k", defaults.cold_top_k),
            int, defaults.cold_top_k, min_value=1,
        ),
        consistency_interval=_coerce_field(
            "memory", "consistency_interval",
            data.get("consistency_interval", defaults.consistency_interval),
            int, defaults.consistency_interval, min_value=0,
        ),
    )


def _parse_api(data: dict[str, Any]) -> ApiConfig:
    """[api] セクションをパースする。

    Args:
        data: [api] セクションの生データ。

    Returns:
        検証済み ApiConfig。
    """
    defaults = ApiConfig()
    return ApiConfig(
        max_retries=_coerce_field(
            "api", "max_retries",
            data.get("max_retries", defaults.max_retries),
            int, defaults.max_retries, min_value=0,
        ),
        retry_backoff_base=_coerce_field(
            "api", "retry_backoff_base",
            data.get("retry_backoff_base", defaults.retry_backoff_base),
            float, defaults.retry_backoff_base, min_value=0.0,
        ),
        timeout=_coerce_field(
            "api", "timeout",
            data.get("timeout", defaults.timeout),
            int, defaults.timeout, min_value=1,
        ),
    )


def _parse_tray(data: dict[str, Any]) -> TrayConfig:
    """[tray] セクションをパースする。

    Args:
        data: [tray] セクションの生データ。

    Returns:
        検証済み TrayConfig。
    """
    defaults = TrayConfig()
    return TrayConfig(
        minimize_to_tray=_coerce_field(
            "tray", "minimize_to_tray",
            data.get("minimize_to_tray", defaults.minimize_to_tray),
            bool, defaults.minimize_to_tray,
        ),
    )


def _parse_logging(data: dict[str, Any]) -> LoggingConfig:
    """[logging] セクションをパースする。

    Args:
        data: [logging] セクションの生データ。

    Returns:
        検証済み LoggingConfig。
    """
    defaults = LoggingConfig()
    return LoggingConfig(
        level=_coerce_field(
            "logging", "level",
            data.get("level", defaults.level),
            str, defaults.level,
        ),
        file_level=_coerce_field(
            "logging", "file_level",
            data.get("file_level", defaults.file_level),
            str, defaults.file_level,
        ),
        max_bytes=_coerce_field(
            "logging", "max_bytes",
            data.get("max_bytes", defaults.max_bytes),
            int, defaults.max_bytes, min_value=0,
        ),
        backup_count=_coerce_field(
            "logging", "backup_count",
            data.get("backup_count", defaults.backup_count),
            int, defaults.backup_count, min_value=0,
        ),
    )


def _parse_desire(data: dict[str, Any]) -> DesireConfig:
    """[desire] セクションをパースする (Phase 2b).

    Args:
        data: [desire] セクションの生データ。

    Returns:
        検証済み DesireConfig。
    """
    defaults = DesireConfig()
    return DesireConfig(
        update_interval_sec=_coerce_field(
            "desire", "update_interval_sec",
            data.get("update_interval_sec", defaults.update_interval_sec),
            float, defaults.update_interval_sec, min_value=0.1,
        ),
        talk_threshold=_coerce_field(
            "desire", "talk_threshold",
            data.get("talk_threshold", defaults.talk_threshold),
            float, defaults.talk_threshold, min_value=0.0, max_value=1.0,
        ),
        curiosity_threshold=_coerce_field(
            "desire", "curiosity_threshold",
            data.get("curiosity_threshold", defaults.curiosity_threshold),
            float, defaults.curiosity_threshold, min_value=0.0, max_value=1.0,
        ),
        reflect_threshold=_coerce_field(
            "desire", "reflect_threshold",
            data.get("reflect_threshold", defaults.reflect_threshold),
            float, defaults.reflect_threshold, min_value=0.0, max_value=1.0,
        ),
        rest_threshold=_coerce_field(
            "desire", "rest_threshold",
            data.get("rest_threshold", defaults.rest_threshold),
            float, defaults.rest_threshold, min_value=0.0, max_value=1.0,
        ),
        idle_minutes_for_talk=_coerce_field(
            "desire", "idle_minutes_for_talk",
            data.get("idle_minutes_for_talk", defaults.idle_minutes_for_talk),
            float, defaults.idle_minutes_for_talk, min_value=0.0,
        ),
        idle_minutes_for_curiosity=_coerce_field(
            "desire", "idle_minutes_for_curiosity",
            data.get("idle_minutes_for_curiosity", defaults.idle_minutes_for_curiosity),
            float, defaults.idle_minutes_for_curiosity, min_value=0.0,
        ),
        reflect_episode_threshold=_coerce_field(
            "desire", "reflect_episode_threshold",
            data.get("reflect_episode_threshold", defaults.reflect_episode_threshold),
            int, defaults.reflect_episode_threshold, min_value=1,
        ),
        rest_hours_threshold=_coerce_field(
            "desire", "rest_hours_threshold",
            data.get("rest_hours_threshold", defaults.rest_hours_threshold),
            float, defaults.rest_hours_threshold, min_value=0.0,
        ),
        rest_suppress_minutes=_coerce_field(
            "desire", "rest_suppress_minutes",
            data.get("rest_suppress_minutes", defaults.rest_suppress_minutes),
            float, defaults.rest_suppress_minutes, min_value=0.0,
        ),
    )


def _coerce_enum(
    section_name: str,
    field_name: str,
    raw_value: Any,
    valid_values: frozenset[str],
    default_value: str,
) -> str:
    """列挙値フィールドを検証し、無効値ならデフォルトにフォールバックする (Phase 2b).

    `_coerce_field` の str 型チェックを通過した後の追加バリデーションとして使用する。

    Args:
        section_name: TOML セクション名（ログ出力用）。
        field_name: フィールド名（ログ出力用）。
        raw_value: 型チェック済みの文字列値。
        valid_values: 有効値の frozenset。
        default_value: フォールバック値。

    Returns:
        valid_values に含まれる値、または default_value。
    """
    if raw_value not in valid_values:
        logger.warning(
            "config [%s].%s: %r is not a valid value. Valid: %s. Using default: %r",
            section_name,
            field_name,
            raw_value,
            sorted(valid_values),
            default_value,
        )
        return default_value
    return raw_value


def _parse_agentic_search(data: dict[str, Any]) -> AgenticSearchConfig:
    """[agentic_search] セクションをパースする (Phase 2b).

    Args:
        data: [agentic_search] セクションの生データ。

    Returns:
        検証済み AgenticSearchConfig。
    """
    defaults = AgenticSearchConfig()
    engine_raw = _coerce_field(
        "agentic_search", "engine",
        data.get("engine", defaults.engine),
        str, defaults.engine,
    )
    search_api_raw = _coerce_field(
        "agentic_search", "search_api",
        data.get("search_api", defaults.search_api),
        str, defaults.search_api,
    )
    return AgenticSearchConfig(
        engine=_coerce_enum(
            "agentic_search", "engine",
            engine_raw, _VALID_AGENTIC_ENGINES, defaults.engine,
        ),
        search_api=_coerce_enum(
            "agentic_search", "search_api",
            search_api_raw, _VALID_AGENTIC_SEARCH_APIS, defaults.search_api,
        ),
        max_subqueries=_coerce_field(
            "agentic_search", "max_subqueries",
            data.get("max_subqueries", defaults.max_subqueries),
            int, defaults.max_subqueries, min_value=1,
        ),
        max_concurrent_searches=_coerce_field(
            "agentic_search", "max_concurrent_searches",
            data.get("max_concurrent_searches", defaults.max_concurrent_searches),
            int, defaults.max_concurrent_searches, min_value=1,
        ),
    )


def _build_app_config(raw: dict[str, Any]) -> AppConfig:
    """生の TOML 辞書から AppConfig を構築する。

    Args:
        raw: tomllib.load() の戻り値。

    Returns:
        検証済み AppConfig。
    """
    return AppConfig(
        general=_parse_general(raw.get("general", {})),
        models=_parse_models(raw.get("models", {})),
        wizard=_parse_wizard(raw.get("wizard", {})),
        conversation=_parse_conversation(raw.get("conversation", {})),
        gui=_parse_gui(raw.get("gui", {})),
        memory=_parse_memory(raw.get("memory", {})),
        api=_parse_api(raw.get("api", {})),
        tray=_parse_tray(raw.get("tray", {})),
        logging=_parse_logging(raw.get("logging", {})),
        desire=_parse_desire(raw.get("desire", {})),
        agentic_search=_parse_agentic_search(raw.get("agentic_search", {})),
    )


# ---------------------------------------------------------------------------
# 公開 API
# ---------------------------------------------------------------------------


def generate_default_config(config_path: Path) -> None:
    """デフォルト config.toml をコメント付きで生成する。

    Args:
        config_path: 生成先のファイルパス。
    """
    d = AppConfig()
    content = f"""\
# 影式 (Kage-Shiki) 設定ファイル
# このファイルを編集してアプリケーションの動作をカスタマイズできます。

[general]
# ペルソナ学習を停止する場合は true に設定します。
persona_frozen = {str(d.general.persona_frozen).lower()}
# データディレクトリのパス（相対パスは実行ディレクトリからの相対）
data_dir = "{d.general.data_dir}"

[models]
# 各用途に使用する Claude モデル ID を指定します。
conversation = "{d.models.conversation}"
memory_worker = "{d.models.memory_worker}"
utility = "{d.models.utility}"
wizard = "{d.models.wizard}"

[wizard]
# ウィザード機能の設定です。
# 連想キーワード生成数
association_count = {d.wizard.association_count}
# サンプリング温度（0.0〜2.0）
temperature = {d.wizard.temperature}
# 候補生成数
candidate_count = {d.wizard.candidate_count}
# 空白フリーズ閾値（会話数）
blank_freeze_threshold = {d.wizard.blank_freeze_threshold}

[conversation]
# 会話 API の設定です。
# サンプリング温度（0.0〜2.0）
temperature = {d.conversation.temperature}
# 最大トークン数
max_tokens = {d.conversation.max_tokens}

[gui]
# GUI ウィンドウの設定です。
window_width = {d.gui.window_width}
window_height = {d.gui.window_height}
# ウィンドウ不透明度（0.0〜1.0）
opacity = {d.gui.opacity}
# 最前面固定
topmost = {str(d.gui.topmost).lower()}
font_size = {d.gui.font_size}
# 空文字はシステムデフォルトフォントを使用します。
font_family = "{d.gui.font_family}"

[memory]
# 記憶管理の設定です。
# ウォームメモリ保持日数
warm_days = {d.memory.warm_days}
# コールドメモリ上位 K 件
cold_top_k = {d.memory.cold_top_k}
# 一貫性チェック間隔（メッセージ数）
consistency_interval = {d.memory.consistency_interval}

[api]
# Anthropic API 接続設定です。
# 最大リトライ回数
max_retries = {d.api.max_retries}
# リトライバックオフ基数（秒）
retry_backoff_base = {d.api.retry_backoff_base}
# タイムアウト（秒）
timeout = {d.api.timeout}

[tray]
# システムトレイの設定です。
# 最小化時にトレイに格納するか
minimize_to_tray = {str(d.tray.minimize_to_tray).lower()}

[logging]
# ログ設定です。
# コンソールログレベル（DEBUG / INFO / WARNING / ERROR / CRITICAL）
level = "{d.logging.level}"
# ファイルログレベル
file_level = "{d.logging.file_level}"
# ログファイル最大サイズ（バイト）
max_bytes = {d.logging.max_bytes}
# ログファイルバックアップ数
backup_count = {d.logging.backup_count}

[desire]
# Phase 2b: DesireWorker の欲求計算・閾値・間隔です。
# 欲求更新間隔（秒）
update_interval_sec = {d.desire.update_interval_sec}
# 各欲求の発現閾値（0.0〜1.0）
talk_threshold = {d.desire.talk_threshold}
curiosity_threshold = {d.desire.curiosity_threshold}
reflect_threshold = {d.desire.reflect_threshold}
rest_threshold = {d.desire.rest_threshold}
# talk 閾値到達までの無入力時間（分）
idle_minutes_for_talk = {d.desire.idle_minutes_for_talk}
# curiosity 上昇開始までの無入力時間（分）
idle_minutes_for_curiosity = {d.desire.idle_minutes_for_curiosity}
# reflect 発現までの observations 蓄積件数
reflect_episode_threshold = {d.desire.reflect_episode_threshold}
# rest 発現までの稼働時間（時間）
rest_hours_threshold = {d.desire.rest_hours_threshold}
# rest 再通知抑制時間（分）
rest_suppress_minutes = {d.desire.rest_suppress_minutes}

[agentic_search]
# Phase 2b: AgenticSearch エンジンの設定です。
# エンジン種別（"haiku" | "local"）
engine = "{d.agentic_search.engine}"
# 検索 API（"duckduckgo" | "brave"）
search_api = "{d.agentic_search.search_api}"
# サブクエリ最大数
max_subqueries = {d.agentic_search.max_subqueries}
# 並列検索数上限
max_concurrent_searches = {d.agentic_search.max_concurrent_searches}
"""
    config_path.write_text(content, encoding="utf-8")


def load_config(config_path: Path) -> AppConfig:
    """config.toml を読み込み AppConfig を返す。不在時はデフォルト生成。

    config.toml が存在しない場合はデフォルト値で新規生成し、
    そのデフォルト AppConfig を返す。
    不正な値はデフォルト値にフォールバックし、logging.warning() で警告する。

    Args:
        config_path: 読み込む config.toml のパス。

    Returns:
        読み込んだ設定値を反映した AppConfig。
    """
    if not config_path.exists():
        logger.info("config.toml not found at %s. Generating default.", config_path)
        generate_default_config(config_path)
        return AppConfig()

    with open(config_path, "rb") as f:
        raw = tomllib.load(f)

    return _build_app_config(raw)


def get_max_tokens(config: AppConfig, purpose: str) -> int:
    """用途別の max_tokens を返す（D-15）。

    Args:
        config: アプリケーション設定。
        purpose: VALID_PURPOSES に含まれる用途識別子。

    Returns:
        指定された用途に対応する max_tokens 値。

    Raises:
        ValueError: 未知の purpose が指定された場合。
    """
    if purpose not in VALID_PURPOSES:
        raise ValueError(f"Unknown purpose: {purpose!r}")

    if purpose == "conversation":
        return config.conversation.max_tokens
    return _MAX_TOKENS_MAP[purpose]


def get_temperature(config: AppConfig, purpose: str) -> float:
    """用途別の temperature を返す（D-15）。

    Args:
        config: アプリケーション設定。
        purpose: VALID_PURPOSES に含まれる用途識別子。

    Returns:
        サンプリング温度。

    Raises:
        ValueError: 未知の purpose が指定された場合。
    """
    if purpose not in VALID_PURPOSES:
        raise ValueError(f"Unknown purpose: {purpose!r}")

    override = _PURPOSE_TEMPERATURES[purpose]
    if override is not None:
        return override
    return config.conversation.temperature


def get_model(config: AppConfig, purpose: str) -> str:
    """用途別のモデル ID を返す（D-15）。

    Args:
        config: アプリケーション設定。
        purpose: VALID_PURPOSES に含まれる用途識別子。

    Returns:
        モデル ID 文字列。

    Raises:
        ValueError: 未知の purpose が指定された場合。
    """
    if purpose not in VALID_PURPOSES:
        raise ValueError(f"Unknown purpose: {purpose!r}")

    slot = _PURPOSE_MODEL_SLOTS[purpose]
    return getattr(config.models, slot)
