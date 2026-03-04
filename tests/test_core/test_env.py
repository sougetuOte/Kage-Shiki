"""API キー確認のテスト (T-04).

対応 FR: FR-1.6 — 起動時に ANTHROPIC_API_KEY 環境変数の存在を確認
対応設計: D-10 — python-dotenv 採用
"""

from pathlib import Path

import pytest

from kage_shiki.core.env import ensure_api_key, load_dotenv_file


class TestLoadDotenvFile:
    """load_dotenv_file() の動作検証."""

    def test_loads_env_from_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        """.env ファイルから環境変数がロードされること."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        env_file = tmp_path / ".env"
        env_file.write_text(
            "ANTHROPIC_API_KEY=sk-ant-from-dotenv\n", encoding="utf-8",
        )

        load_dotenv_file(env_path=env_file)

        import os
        assert os.environ.get("ANTHROPIC_API_KEY") == "sk-ant-from-dotenv"
        # cleanup
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    def test_does_not_override_existing_env(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        """既存の環境変数を上書きしないこと（override=False）."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-existing")
        env_file = tmp_path / ".env"
        env_file.write_text(
            "ANTHROPIC_API_KEY=sk-ant-from-dotenv\n", encoding="utf-8",
        )

        load_dotenv_file(env_path=env_file)

        import os
        assert os.environ.get("ANTHROPIC_API_KEY") == "sk-ant-existing"

    def test_missing_env_file_does_not_crash(self, tmp_path: Path) -> None:
        """.env ファイルが存在しなくてもクラッシュしないこと."""
        env_file = tmp_path / ".env"
        load_dotenv_file(env_path=env_file)  # should not raise


class TestEnsureApiKey:
    """ensure_api_key() の動作検証."""

    def test_returns_key_when_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """環境変数に ANTHROPIC_API_KEY が設定されている場合にキーを返すこと."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key-12345")
        result = ensure_api_key()
        assert result == "sk-ant-test-key-12345"

    def test_raises_system_exit_when_missing(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """環境変数が未設定の場合に SystemExit が発生すること."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(SystemExit, match="1"):
            ensure_api_key()

    def test_raises_system_exit_when_empty(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """環境変数が空文字の場合に SystemExit が発生すること."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")
        with pytest.raises(SystemExit, match="1"):
            ensure_api_key()

    def test_error_message_mentions_env_file_when_exists(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys,
    ) -> None:
        """.env ファイルが存在する場合のエラーメッセージに適切な案内があること."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        env_file = tmp_path / ".env"
        env_file.write_text("# empty", encoding="utf-8")

        with pytest.raises(SystemExit):
            ensure_api_key(env_path=env_file)

        captured = capsys.readouterr()
        assert ".env" in captured.err
        assert "見つかりました" in captured.err

    def test_error_message_when_no_env_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys,
    ) -> None:
        """.env ファイルが存在しない場合のエラーメッセージが適切であること."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        env_file = tmp_path / ".env"

        with pytest.raises(SystemExit):
            ensure_api_key(env_path=env_file)

        captured = capsys.readouterr()
        assert "ANTHROPIC_API_KEY" in captured.err
        assert "設定されていません" in captured.err

    def test_strips_whitespace(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """キー値の前後の空白が除去されること."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "  sk-ant-test  ")
        result = ensure_api_key()
        assert result == "sk-ant-test"


class TestDefaultEnvPath:
    """デフォルトパス定数の動作検証."""

    def test_load_dotenv_file_uses_default_path(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        """引数なしの load_dotenv_file() がデフォルトパスを使用すること."""
        import kage_shiki.core.env as env_module

        fake_env = tmp_path / ".env"
        fake_env.write_text(
            "ANTHROPIC_API_KEY=sk-ant-default-path-test\n", encoding="utf-8",
        )
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setattr(env_module, "_DEFAULT_ENV_PATH", fake_env)

        load_dotenv_file()  # 引数なし（デフォルトパス使用）

        import os
        assert os.environ.get("ANTHROPIC_API_KEY") == "sk-ant-default-path-test"
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    def test_ensure_api_key_uses_default_path(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        """引数なしの ensure_api_key() がデフォルトパスを使用すること."""
        import kage_shiki.core.env as env_module

        fake_env = tmp_path / ".env"
        fake_env.write_text("# empty", encoding="utf-8")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setattr(env_module, "_DEFAULT_ENV_PATH", fake_env)

        with pytest.raises(SystemExit):
            ensure_api_key()  # 引数なし
