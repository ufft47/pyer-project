"""Tests for Python version info formatting."""
from pyer import pyer_config as cfg


def test_format_python_version_summary_returns_string():
    """format_python_version_summary() should return a non-empty string."""
    result = cfg.format_python_version_summary()
    assert isinstance(result, str)
    assert len(result) > 0


def test_format_python_version_summary_contains_version_numbers():
    """The formatted string should contain the version numbers."""
    result = cfg.format_python_version_summary()
    info = cfg.get_python_version_info()
    version_str = ".".join(str(v) for v in info["version_info"][:3])
    assert version_str in result


def test_format_python_version_summary_contains_implementation():
    """The formatted string should include the Python implementation name."""
    result = cfg.format_python_version_summary()
    info = cfg.get_python_version_info()
    assert info["implementation"] in result


def test_format_python_version_summary_contains_venv_or_global():
    """The formatted string should mention whether it's a venv or global Python."""
    result = cfg.format_python_version_summary()
    info = cfg.get_python_version_info()
    if info["is_venv"]:
        assert "venv" in result.lower() or "虛擬" in result or "環境" in result
    else:
        assert "global" in result.lower() or "全域" in result
