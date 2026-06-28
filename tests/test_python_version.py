"""Tests for Python version info feature."""
import sys
import platform
from pyer import pyer_config as cfg


def test_get_python_version_info_returns_dict():
    """get_python_version_info() should return a dict."""
    info = cfg.get_python_version_info()
    assert isinstance(info, dict)


def test_get_python_version_info_has_required_keys():
    """The dict should contain all expected keys."""
    info = cfg.get_python_version_info()
    required_keys = {
        "full_version",
        "version_info",
        "implementation",
        "executable",
        "is_venv",
        "global_python",
    }
    assert required_keys.issubset(info.keys())


def test_get_python_version_info_full_version_non_empty():
    """full_version should be a non-empty string."""
    info = cfg.get_python_version_info()
    assert isinstance(info["full_version"], str)
    assert len(info["full_version"]) > 0


def test_get_python_version_info_version_info_matches_sys():
    """version_info tuple should match sys.version_info."""
    info = cfg.get_python_version_info()
    version_tuple = info["version_info"]
    assert isinstance(version_tuple, tuple)
    assert len(version_tuple) >= 3
    assert version_tuple[0] == sys.version_info.major
    assert version_tuple[1] == sys.version_info.minor


def test_get_python_version_info_implementation_matches_platform():
    """implementation should match platform.python_implementation()."""
    info = cfg.get_python_version_info()
    assert info["implementation"] == platform.python_implementation()


def test_get_python_version_info_executable_is_string():
    """executable should be a string path."""
    info = cfg.get_python_version_info()
    assert isinstance(info["executable"], str)
    assert len(info["executable"]) > 0


def test_get_python_version_info_is_venv_is_bool():
    """is_venv should be a boolean."""
    info = cfg.get_python_version_info()
    assert isinstance(info["is_venv"], bool)


def test_get_python_version_info_global_python_is_string():
    """global_python should be a non-empty string containing a path or version."""
    info = cfg.get_python_version_info()
    assert isinstance(info["global_python"], str)
    assert len(info["global_python"]) > 0


def test_get_python_version_info_global_python_differs_in_venv():
    """When inside a venv, global_python should differ from sys.executable."""
    info = cfg.get_python_version_info()
    if info["is_venv"]:
        assert info["global_python"] != info["executable"]
