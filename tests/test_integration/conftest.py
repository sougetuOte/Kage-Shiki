"""統合テスト用共通フィクスチャ (T-26).

統合テストでは、LLM のみモック・SQLite は実スキーマ・GUI はモックの方針で
コンポーネント間の実データフローを検証する。
"""

import sqlite3
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from kage_shiki.agent.llm_client import LLMProtocol
from kage_shiki.core.config import AppConfig
from kage_shiki.memory.db import Database, initialize_db, save_observation
from kage_shiki.persona.persona_system import PersonaCore

# ---------------------------------------------------------------------------
# DB フィクスチャ
# ---------------------------------------------------------------------------


@pytest.fixture()
def integration_db(tmp_path: Path) -> tuple[Database, sqlite3.Connection]:
    """初期化済み DB（Database インスタンス + Connection）を返す."""
    db_path = tmp_path / "memory.db"
    db = Database(db_path)
    conn = db.connect()
    initialize_db(conn)
    yield db, conn
    db.close()


@pytest.fixture()
def db_conn(integration_db: tuple) -> sqlite3.Connection:
    """初期化済み DB 接続のみ返す（軽量版）."""
    _, conn = integration_db
    return conn


# ---------------------------------------------------------------------------
# LLM モックフィクスチャ
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_llm_client():
    """LLMProtocol のモック.

    send_message_for_purpose のデフォルト戻り値を設定。
    テストケースごとに side_effect でカスタマイズ可能。
    """
    client = MagicMock(spec=LLMProtocol)
    client.send_message_for_purpose.return_value = "モック応答テキスト"
    client.chat.return_value = "モック応答テキスト"
    return client


# ---------------------------------------------------------------------------
# Config フィクスチャ
# ---------------------------------------------------------------------------


@pytest.fixture()
def integration_config(tmp_path: Path) -> AppConfig:
    """統合テスト用 AppConfig（data_dir を tmp_path に設定）."""
    config = AppConfig()
    config.general.data_dir = str(tmp_path)
    return config


# ---------------------------------------------------------------------------
# PersonaCore テストデータ
# ---------------------------------------------------------------------------


SAMPLE_PERSONA_CORE = PersonaCore(
    c1_name="テスト花子",
    c2_first_person="あたし",
    c3_second_person="あなた",
    c4_personality_core="明るくて好奇心旺盛な性格。何事にも前向き。",
    c5_personality_axes="- 好奇心: とても高い\n- 社交性: 高い\n- 繊細さ: 普通",
    c6_speech_pattern="カジュアルで親しみやすい口調。語尾に「だよ」「ね」をよく使う。",
    c7_catchphrase="- えへへ\n- なるほどね！\n- すごいすごい！",
    c8_age_impression="高校生くらい",
    c9_values="友達を大切にすること。新しいことに挑戦すること。",
    c10_forbidden="- 暴力的な表現\n- 過度にネガティブな発言",
    c11_self_knowledge="自分はデスクトップマスコットだと理解しているが、それを表に出さない。",
)


@pytest.fixture()
def sample_persona_core() -> PersonaCore:
    """テスト用 PersonaCore インスタンス."""
    return SAMPLE_PERSONA_CORE


SAMPLE_STYLE_SAMPLES = """\
## S1: 日常会話
1. （雑談中）→「今日はいい天気だね！お出かけしたくなっちゃう」
2. （質問されて）→「えーっとね、あたしが知ってるのは...」

## S2: 喜び
1. （褒められて）→「えへへ、ありがとう！嬉しいな」

## S3: 怒り・不快
1. （嫌なことを言われて）→「もう、そういうの良くないよ？」

## S4: 悲しみ・寂しさ
1. （寂しい時）→「ちょっと寂しいかも...」

## S5: 困惑・不知
1. （知らないことを聞かれて）→「うーん、それはちょっとわからないかも」

## S6: ユーモア
1. （冗談を言う）→「なんちゃって！ふふっ」

## S7: 沈黙破り
1. （長い沈黙の後）→「ねぇねぇ、何してるの？」
"""


@pytest.fixture()
def sample_style_samples() -> str:
    """テスト用スタイルサンプルテキスト."""
    return SAMPLE_STYLE_SAMPLES


# ---------------------------------------------------------------------------
# PersonaSystem + ファイル生成フィクスチャ
# ---------------------------------------------------------------------------


@pytest.fixture()
def persona_data_dir(tmp_path: Path) -> Path:
    """テスト用ペルソナファイル群を生成して data_dir を返す."""
    data_dir = tmp_path

    # persona_core.md
    persona_md = """\
# テスト花子

## メタデータ

| 項目 | 値 |
|------|-----|
| 生成日時 | 2026-03-01T12:00:00+09:00 |
| 生成方式 | ai_generate |
| 凍結状態 | frozen |

## C1: 名前

テスト花子

## C2: 一人称

あたし

## C3: 二人称（ユーザーの呼び方）

あなた

## C4: 人格核文

明るくて好奇心旺盛な性格。何事にも前向き。

## C5: 性格軸

- 好奇心: とても高い
- 社交性: 高い
- 繊細さ: 普通

## C6: 口調パターン

カジュアルで親しみやすい口調。語尾に「だよ」「ね」をよく使う。

## C7: 口癖

- えへへ
- なるほどね！
- すごいすごい！

## C8: 年齢感

高校生くらい

## C9: 価値観

友達を大切にすること。新しいことに挑戦すること。

## C10: 禁忌

- 暴力的な表現
- 過度にネガティブな発言

## C11: 知識の自己認識

自分はデスクトップマスコットだと理解しているが、それを表に出さない。
"""
    (data_dir / "persona_core.md").write_text(persona_md, encoding="utf-8")
    (data_dir / "style_samples.md").write_text(
        SAMPLE_STYLE_SAMPLES, encoding="utf-8",
    )

    human_block = """\
# ユーザー情報

## 基本情報

（AI が会話中に検出した情報を追記）

## 好み・興味

## 習慣・パターン

## 更新履歴

"""
    (data_dir / "human_block.md").write_text(human_block, encoding="utf-8")

    trends = """\
# 傾向メモ

## 関係性の変化

（AI が提案 → ユーザー承認後に追記）

## 感情の傾向

## 新しい口癖候補（supplementary_styles）

## 提案履歴

"""
    (data_dir / "personality_trends.md").write_text(trends, encoding="utf-8")

    return data_dir


# ---------------------------------------------------------------------------
# テストデータ挿入ヘルパー
# ---------------------------------------------------------------------------


def insert_test_observations(
    conn: sqlite3.Connection,
    entries: list[tuple[str, str]],
    *,
    session_id: str = "20260301_1200_abcd1234",
    base_timestamp: float | None = None,
) -> None:
    """テスト用 observations を一括挿入する.

    Args:
        conn: DB 接続。
        entries: (content, speaker) のリスト。
        session_id: セッション ID。
        base_timestamp: 基準タイムスタンプ（None で現在時刻）。
    """
    ts = base_timestamp or time.time()
    for i, (content, speaker) in enumerate(entries):
        save_observation(conn, content, speaker, ts + i, session_id=session_id)
