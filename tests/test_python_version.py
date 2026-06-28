import sys, os, platform
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pyer_config import get_python_version_info

def test_get_python_version_info_returns_dict():
    info = get_python_version_info()
    assert isinstance(info, dict)
    assert "full_version" in info
    assert "version_info" in info
    assert "implementation" in info
    assert "executable" in info
    assert "is_venv" in info
    assert "global_python" in info

def test_version_info_tuple():
    info = get_python_version_info()
    assert isinstance(info["version_info"], tuple)
    assert len(info["version_info"]) == 5
    assert isinstance(info["version_info"][0], int)

def test_implementation_string():
    info = get_python_version_info()
    assert isinstance(info["implementation"], str)
    assert len(info["implementation"]) > 0

def test_executable_path():
    info = get_python_version_info()
    assert isinstance(info["executable"], str)
    assert "python" in info["executable"].lower()

def test_is_venv_bool():
    info = get_python_version_info()
    assert isinstance(info["is_venv"], bool)

def test_global_python_string():
    info = get_python_version_info()
    assert isinstance(info["global_python"], str)

def test_full_version_string():
    info = get_python_version_info()
    assert isinstance(info["full_version"], str)
    assert "3." in info["full_version"]


def test_build_status_text_returns_string():
    """build_status_text() 回傳純字串，無 Tkinter 相依。"""
    from pyer_config import build_status_text
    result = build_status_text()
    assert isinstance(result, str)
    assert "Python" in result
    assert "Python" in result
    assert "全域" in result or "已進入" in result or "路徑下" in result
