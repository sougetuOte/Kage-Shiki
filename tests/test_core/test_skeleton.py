"""T-01: プロジェクト骨格の検証テスト.

対応 FR:
    FR-1.4: data_dir 初期化の前提となるディレクトリ構成
"""


def test_kage_shiki_package_importable():
    """kage_shiki パッケージがインポート可能であること."""
    import kage_shiki

    assert hasattr(kage_shiki, "__version__")


def test_version_is_string():
    """__version__ が文字列であること."""
    from kage_shiki import __version__

    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_subpackages_importable():
    """全サブパッケージがインポート可能であること."""
    import importlib

    subpackages = [
        "kage_shiki.core",
        "kage_shiki.agent",
        "kage_shiki.memory",
        "kage_shiki.persona",
        "kage_shiki.gui",
        "kage_shiki.tray",
    ]
    for pkg in subpackages:
        mod = importlib.import_module(pkg)
        assert mod is not None, f"Failed to import {pkg}"


def test_directory_structure(project_root):
    """D-1 で定義されたディレクトリ構成が存在すること."""
    src_root = project_root / "src" / "kage_shiki"

    expected_dirs = [
        src_root / "core",
        src_root / "agent",
        src_root / "memory",
        src_root / "persona",
        src_root / "gui",
        src_root / "tray",
    ]

    for d in expected_dirs:
        assert d.is_dir(), f"Directory {d} does not exist"
        assert (d / "__init__.py").is_file(), f"{d}/__init__.py does not exist"


def test_pyproject_toml_exists(project_root):
    """pyproject.toml が存在すること."""
    assert (project_root / "pyproject.toml").is_file()


def test_env_example_exists(project_root):
    """.env.example テンプレートが存在すること."""
    assert (project_root / ".env.example").is_file()
