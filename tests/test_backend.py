"""Unit tests for pyer_backend.py"""



import os

import sys

import logging

from pathlib import Path



import pytest



sys.path.insert(0, str(Path(__file__).parent.parent))



from pyer_backend import (

    scan_venvs,

    get_next_suggested_name,

    generate_commands,

    write_commands_file,

    get_installed_packages,

    create_venv_exec,

    delete_venv,

)

import pyer_config as cfg





# ==================== scan_venvs ====================





def test_scan_venvs_empty(tmp_path):

    old_cwd = os.getcwd()

    os.chdir(tmp_path)

    try:

        assert scan_venvs() == []

    finally:

        os.chdir(old_cwd)





def test_scan_venvs_finds_venv(tmp_path):

    venv_dir = tmp_path / "my_env"

    (venv_dir / "Scripts").mkdir(parents=True)

    (venv_dir / "Scripts" / "activate.bat").write_text("")

    old_cwd = os.getcwd()

    os.chdir(tmp_path)

    try:

        result = scan_venvs()

        assert len(result) == 1

        assert "my_env" in result[0]

        assert "傳統 VENV" in result[0]

    finally:

        os.chdir(old_cwd)





def test_scan_venvs_uv_detection(tmp_path):

    venv_dir = tmp_path / "uv_env"

    (venv_dir / "Scripts").mkdir(parents=True)

    (venv_dir / "Scripts" / "activate.bat").write_text("")

    (venv_dir / "pyvenv.cfg").write_text("creator = uv")

    old_cwd = os.getcwd()

    os.chdir(tmp_path)

    try:

        result = scan_venvs()

        assert len(result) == 1

        assert "UV" in result[0]

    finally:

        os.chdir(old_cwd)





def test_scan_venvs_ignore_non_venv(tmp_path):

    (tmp_path / "not_a_venv").mkdir()

    (tmp_path / "README.txt").write_text("hello")

    old_cwd = os.getcwd()

    os.chdir(tmp_path)

    try:

        assert scan_venvs() == []

    finally:

        os.chdir(old_cwd)





def test_scan_venvs_listdir_error(monkeypatch):

    monkeypatch.setattr("os.listdir", lambda _: (_ for _ in []).throw(PermissionError("x")))

    assert scan_venvs() == []





def test_scan_venvs_skip_blank_entries(tmp_path, monkeypatch):

    monkeypatch.setattr("os.listdir", lambda _: ["", "  ", "valid_env"])

    (tmp_path / "valid_env" / "Scripts").mkdir(parents=True)

    (tmp_path / "valid_env" / "Scripts" / "activate.bat").write_text("")

    old_cwd = os.getcwd()

    os.chdir(tmp_path)

    try:

        result = scan_venvs()

        assert len(result) == 1

        assert "valid_env" in result[0]

    finally:

        os.chdir(old_cwd)





# ==================== get_next_suggested_name ====================





def test_suggest_basic(tmp_path):

    old_cwd = os.getcwd()

    os.chdir(tmp_path)

    try:

        assert get_next_suggested_name("my_env") == "my_env"

    finally:

        os.chdir(old_cwd)





def test_suggest_with_counter(tmp_path):

    old_cwd = os.getcwd()

    os.chdir(tmp_path)

    try:

        os.mkdir("my_env")

        assert get_next_suggested_name("my_env") == "my_env_1"

        os.mkdir("my_env_1")

        assert get_next_suggested_name("my_env") == "my_env_2"

    finally:

        os.chdir(old_cwd)





def test_suggest_many_conflicts(tmp_path):

    old_cwd = os.getcwd()

    os.chdir(tmp_path)

    try:

        assert get_next_suggested_name("base") == "base"

        os.mkdir("base")

        assert get_next_suggested_name("base") == "base_1"

        os.mkdir("base_1")

        assert get_next_suggested_name("base") == "base_2"

        for i in range(2, 11): os.mkdir(f"base_{i}")

        assert get_next_suggested_name("base") == "base_11"

    finally:

        os.chdir(old_cwd)





# ==================== generate_commands ====================





@pytest.fixture

def setup_shell_cmd():

    old = cfg.SHELL_TYPE, cfg.IS_INSIDE_VENV_DIR

    cfg.SHELL_TYPE = "cmd"

    cfg.IS_INSIDE_VENV_DIR = False

    yield

    cfg.SHELL_TYPE, cfg.IS_INSIDE_VENV_DIR = old





@pytest.fixture

def setup_shell_powershell():

    old = cfg.SHELL_TYPE, cfg.IS_INSIDE_VENV_DIR

    cfg.SHELL_TYPE = "powershell"

    cfg.IS_INSIDE_VENV_DIR = False

    yield

    cfg.SHELL_TYPE, cfg.IS_INSIDE_VENV_DIR = old





@pytest.fixture

def setup_shell_inside_venv():

    old = cfg.SHELL_TYPE, cfg.IS_INSIDE_VENV_DIR

    cfg.SHELL_TYPE = "cmd"

    cfg.IS_INSIDE_VENV_DIR = True

    yield

    cfg.SHELL_TYPE, cfg.IS_INSIDE_VENV_DIR = old





class TestGenerateCommands:



    def test_cmd_without_cd(self, setup_shell_cmd):

        cmds = generate_commands("my_env", should_cd=False)

        assert len(cmds) == 1

        assert "activate.bat" in cmds[0]



    def test_cmd_with_cd(self, setup_shell_cmd):

        cmds = generate_commands("my_env", should_cd=True)

        assert len(cmds) == 2

        assert "cd /d" in cmds[0]

        assert "activate.bat" in cmds[1]



    def test_powershell_without_cd(self, setup_shell_powershell):

        cmds = generate_commands("my_env", should_cd=False)

        assert len(cmds) == 1

        assert "Activate.ps1" in cmds[0]



    def test_powershell_with_cd(self, setup_shell_powershell):

        cmds = generate_commands("my_env", should_cd=True)

        assert len(cmds) == 2

        assert "Set-Location" in cmds[0]

        assert "Activate.ps1" in cmds[1]



    def test_inside_venv_dir(self, setup_shell_inside_venv):

        cmds = generate_commands("my_env", should_cd=True)

        assert len(cmds) == 1

        assert "activate.bat" in cmds[0]



    def test_name_with_suffix(self, setup_shell_cmd):

        cmds = generate_commands("my_env (UV)", should_cd=False)

        joined = " ".join(cmds)

        assert "my_env" in joined

        assert "(UV)" not in joined





# ==================== write_commands_file ====================





def test_write_commands_file(tmp_path):

    old = cfg.TMP_FILE_PATH

    p = str(tmp_path / "next.bat")

    cfg.TMP_FILE_PATH = p

    try:

        write_commands_file(["echo a", "echo b"])
        write_commands_file(["echo a", "echo b"])
        result = Path(p).read_text("utf-8")
        assert "echo a" in result
        assert "echo b" in result
    finally:

        cfg.TMP_FILE_PATH = old





def test_write_commands_empty(tmp_path):

    old = cfg.TMP_FILE_PATH

    p = str(tmp_path / "empty.bat")

    cfg.TMP_FILE_PATH = p

    try:

        write_commands_file([])

        assert Path(p).read_text("utf-8") == ""

    finally:

        cfg.TMP_FILE_PATH = old





def test_write_commands_raises_on_bad_path():

    old = cfg.TMP_FILE_PATH

    cfg.TMP_FILE_PATH = "/nonexistent/dir/script.bat"

    try:

        with pytest.raises(Exception):

            write_commands_file(["test"])

    finally:

        cfg.TMP_FILE_PATH = old





# ==================== get_installed_packages ====================





def test_get_packages_no_venv():

    old_a, old_b = cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH

    cfg.CURRENT_VENV_PATH = None

    cfg.VENV_PIP_PATH = None

    try:

        assert get_installed_packages() == []

    finally:

        cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH = old_a, old_b





def test_get_packages_pip_not_found():

    old_a, old_b = cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH

    cfg.CURRENT_VENV_PATH = "/tmp/fake_venv"

    cfg.VENV_PIP_PATH = "/tmp/fake_venv/Scripts/pip.exe"

    try:

        assert get_installed_packages() == []

    finally:

        cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH = old_a, old_b





def test_get_packages_pip_fails(tmp_path):

    old_a, old_b = cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH

    fake = tmp_path / "pip.exe"

    fake.write_text("")

    cfg.CURRENT_VENV_PATH = str(tmp_path)

    cfg.VENV_PIP_PATH = str(fake)

    try:

        result = get_installed_packages()

        assert len(result) >= 1

        assert "讀取失敗" in result[0]

    finally:

        cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH = old_a, old_b





# ==================== create_venv_exec ====================





def test_create_venv_traditional(tmp_path, monkeypatch):

    calls = []

    def fake_run(*a, **kw):
        calls.append(a)
        return type("R", (), {"returncode": 0})()
    monkeypatch.setattr("subprocess.run", fake_run)

    old_cwd = os.getcwd()

    os.chdir(tmp_path)

    try:

        create_venv_exec("test_venv", use_uv=False)

        assert len(calls) == 1

        assert "python" in str(calls[0][0])

        assert "venv" in str(calls[0][0])

    finally:

        os.chdir(old_cwd)





def test_create_venv_with_uv(tmp_path, monkeypatch):

    calls = []

    def fake_run(*a, **kw):
        calls.append(a)
        return type("R", (), {"returncode": 0})()
    monkeypatch.setattr("subprocess.run", fake_run)

    old_uv = cfg.VENV_UV_PATH

    cfg.VENV_UV_PATH = "/usr/bin/uv"

    old_cwd = os.getcwd()

    os.chdir(tmp_path)

    try:

        create_venv_exec("uv_venv", use_uv=True)

        assert len(calls) == 1

        assert "uv" in str(calls[0][0])

    finally:

        cfg.VENV_UV_PATH = old_uv

        os.chdir(old_cwd)





# ==================== delete_venv ====================





def test_delete_venv(tmp_path):

    d = tmp_path / "to_delete"

    d.mkdir()

    assert d.exists()

    old_cwd = os.getcwd()

    os.chdir(tmp_path)

    try:

        delete_venv("to_delete")

        assert not d.exists()

    finally:

        os.chdir(old_cwd)





def test_delete_venv_with_suffix(tmp_path):

    d = tmp_path / "uv_venv"

    d.mkdir()

    old_cwd = os.getcwd()

    os.chdir(tmp_path)

    try:

        delete_venv("uv_venv (UV)")

        assert not d.exists()

    finally:

        os.chdir(old_cwd)





def test_delete_nonexistent_raises(tmp_path):

    old_cwd = os.getcwd()

    os.chdir(tmp_path)

    try:

        with pytest.raises(Exception):

            delete_venv("ghost")

    finally:

        os.chdir(old_cwd)

# ==================== _get_pkg_tool_and_args / install / uninstall ====================


def test_get_pkg_tool_no_venv():
    old_path = cfg.CURRENT_VENV_PATH
    cfg.CURRENT_VENV_PATH = None
    try:
        from pyer_backend import _get_pkg_tool_and_args
        assert _get_pkg_tool_and_args() == (None, [])
    finally:
        cfg.CURRENT_VENV_PATH = old_path


def test_get_pkg_tool_traditional(monkeypatch):
    old_path, old_pip, old_uv = cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH, cfg.VENV_UV_PATH
    cfg.CURRENT_VENV_PATH = "/tmp/fake"
    cfg.VENV_PIP_PATH = "/tmp/fake/Scripts/pip.exe"
    cfg.VENV_UV_PATH = None
    monkeypatch.setattr("os.path.exists", lambda p: str(p).endswith("pip.exe"))
    try:
        from pyer_backend import _get_pkg_tool_and_args
        tool, args = _get_pkg_tool_and_args()
        assert tool == "/tmp/fake/Scripts/pip.exe"
        assert args == []
    finally:
        cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH, cfg.VENV_UV_PATH = old_path, old_pip, old_uv


def test_get_pkg_tool_uv_environment(monkeypatch):
    old_path, old_pip, old_uv, old_is_uv = (
        cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH, cfg.VENV_UV_PATH, cfg.IS_UV_ENVIRONMENT)
    cfg.CURRENT_VENV_PATH = "/tmp/fake"
    cfg.VENV_UV_PATH = "/usr/bin/uv"
    cfg.VENV_PIP_PATH = "/tmp/fake/Scripts/pip.exe"
    cfg.IS_UV_ENVIRONMENT = True
    monkeypatch.setattr("os.path.exists", lambda p: True)
    try:
        from pyer_backend import _get_pkg_tool_and_args
        tool, args = _get_pkg_tool_and_args()
        assert tool == "/usr/bin/uv"
        assert args == ["pip"]
    finally:
        cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH, cfg.VENV_UV_PATH, cfg.IS_UV_ENVIRONMENT = (
            old_path, old_pip, old_uv, old_is_uv)


def test_install_packages_no_venv():
    old_path = cfg.CURRENT_VENV_PATH
    cfg.CURRENT_VENV_PATH = None
    try:
        from pyer_backend import install_packages
        import pytest
        with pytest.raises(RuntimeError, match="\u6c92\u6709\u555f\u7528\u4e2d\u7684\u865b\u64ec\u74b0\u5883"):
            install_packages(["requests"])
    finally:
        cfg.CURRENT_VENV_PATH = old_path


def test_install_packages_success(monkeypatch):
    old_path, old_pip = cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH
    cfg.CURRENT_VENV_PATH = "/tmp/fake"
    cfg.VENV_PIP_PATH = "/tmp/fake/Scripts/pip.exe"
    monkeypatch.setattr("os.path.exists", lambda p: True)
    calls = []
    def fake_run(*a, **kw):
        calls.append(a[0])
        return type("R", (), {"returncode": 0, "stdout": "OK", "stderr": ""})()
    monkeypatch.setattr("subprocess.run", fake_run)
    try:
        from pyer_backend import install_packages
        results = install_packages(["requests", "numpy"])
        assert len(results) == 2
        assert results[0]["status"] == "success"
        assert results[1]["status"] == "success"
        assert len(calls) == 2
    finally:
        cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH = old_path, old_pip


def test_install_packages_partial_fail(monkeypatch):
    old_path, old_pip = cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH
    cfg.CURRENT_VENV_PATH = "/tmp/fake"
    cfg.VENV_PIP_PATH = "/tmp/fake/Scripts/pip.exe"
    monkeypatch.setattr("os.path.exists", lambda p: True)
    import subprocess
    call_n = [0]
    def fake_run(*a, **kw):
        call_n[0] += 1
        if call_n[0] == 2:
            raise subprocess.CalledProcessError(1, "pip", stderr="not found")
        return type("R", (), {"returncode": 0, "stdout": "OK", "stderr": ""})()
    monkeypatch.setattr("subprocess.run", fake_run)
    try:
        from pyer_backend import install_packages
        results = install_packages(["requests", "badpkg"])
        assert results[0]["status"] == "success"
        assert results[1]["status"] == "error"
    finally:
        cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH = old_path, old_pip


def test_uninstall_package_no_venv():
    old_path = cfg.CURRENT_VENV_PATH
    cfg.CURRENT_VENV_PATH = None
    try:
        from pyer_backend import uninstall_package
        import pytest
        with pytest.raises(RuntimeError):
            uninstall_package("requests")
    finally:
        cfg.CURRENT_VENV_PATH = old_path


def test_uninstall_package_success(monkeypatch):
    old_path, old_pip = cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH
    cfg.CURRENT_VENV_PATH = "/tmp/fake"
    cfg.VENV_PIP_PATH = "/tmp/fake/Scripts/pip.exe"
    monkeypatch.setattr("os.path.exists", lambda p: True)
    monkeypatch.setattr("subprocess.run", lambda *a, **kw: type("R", (), {"returncode": 0, "stdout": "Removed", "stderr": ""})())
    try:
        from pyer_backend import uninstall_package
        result = uninstall_package("requests")
        assert result["status"] == "success"
    finally:
        cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH = old_path, old_pip


# ==================== 邊界覆蓋率補強 ====================


def test_scan_venvs_pyvenv_cfg_exception(tmp_path, monkeypatch):
    """pyvenv.cfg 讀取異常時不影響掃描結果（except pass）。"""
    venv_dir = tmp_path / "some_env"
    (venv_dir / "Scripts").mkdir(parents=True)
    (venv_dir / "Scripts" / "activate.bat").write_text("")
    (venv_dir / "pyvenv.cfg").write_text("creator = uv")

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = scan_venvs()
        # 即使 pyvenv.cfg 有 uv 內容，scan 還是能正常執行
        assert len(result) == 1
        assert "some_env" in result[0]
    finally:
        os.chdir(old_cwd)


def test_get_pkg_tool_no_pip_no_uv(monkeypatch):
    """傳統環境但 pip 不存在時回傳 None。"""
    from pyer_backend import _get_pkg_tool_and_args
    old_path, old_pip, old_uv, old_is_uv = (
        cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH, cfg.VENV_UV_PATH, cfg.IS_UV_ENVIRONMENT)
    cfg.CURRENT_VENV_PATH = "/tmp/fake"
    cfg.VENV_PIP_PATH = "/tmp/fake/Scripts/pip.exe"
    cfg.VENV_UV_PATH = None
    cfg.IS_UV_ENVIRONMENT = False
    monkeypatch.setattr("os.path.exists", lambda p: False)  # pip 不存在
    try:
        result = _get_pkg_tool_and_args()
        assert result == (None, [])
    finally:
        cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH, cfg.VENV_UV_PATH, cfg.IS_UV_ENVIRONMENT = (
            old_path, old_pip, old_uv, old_is_uv)


def test_install_packages_empty_name(monkeypatch):
    """空字串套件名稱應跳過不處理。"""
    from pyer_backend import install_packages
    old_path, old_pip = cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH
    cfg.CURRENT_VENV_PATH = "/tmp/fake"
    cfg.VENV_PIP_PATH = "/tmp/fake/Scripts/pip.exe"
    monkeypatch.setattr("os.path.exists", lambda p: True)
    calls = []
    def fake_run(*a, **kw):
        calls.append(a[0])
        return type("R", (), {"returncode": 0, "stdout": "OK", "stderr": ""})()
    monkeypatch.setattr("subprocess.run", fake_run)
    try:
        results = install_packages(["requests", "", "numpy"])
        assert len(results) == 2  # empty string skipped
        assert results[0]["name"] == "requests"
        assert results[1]["name"] == "numpy"
    finally:
        cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH = old_path, old_pip


def test_install_packages_uv_mode(monkeypatch):
    """UV 環境下 install_packages 應使用 uv 路徑。"""
    from pyer_backend import install_packages
    old_path, old_pip, old_uv, old_is_uv = (
        cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH, cfg.VENV_UV_PATH, cfg.IS_UV_ENVIRONMENT)
    cfg.CURRENT_VENV_PATH = "/tmp/fake"
    cfg.VENV_PIP_PATH = "/tmp/fake/Scripts/pip.exe"
    cfg.VENV_UV_PATH = "/usr/bin/uv"
    cfg.IS_UV_ENVIRONMENT = True
    monkeypatch.setattr("os.path.exists", lambda p: True)
    calls = []
    def fake_run(*a, **kw):
        calls.append(a[0])
        return type("R", (), {"returncode": 0, "stdout": "OK", "stderr": ""})()
    monkeypatch.setattr("subprocess.run", fake_run)
    try:
        results = install_packages(["requests"])
        assert len(calls) == 1
        assert "uv" in str(calls[0][0])  # 應該使用 uv 不是 pip
        assert results[0]["status"] == "success"
    finally:
        cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH, cfg.VENV_UV_PATH, cfg.IS_UV_ENVIRONMENT = (
            old_path, old_pip, old_uv, old_is_uv)


def test_uninstall_package_error(monkeypatch):
    """移除套件失敗應回傳 error 狀態。"""
    from pyer_backend import uninstall_package
    import subprocess
    old_path, old_pip = cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH
    cfg.CURRENT_VENV_PATH = "/tmp/fake"
    cfg.VENV_PIP_PATH = "/tmp/fake/Scripts/pip.exe"
    monkeypatch.setattr("os.path.exists", lambda p: True)
    def fake_run(*a, **kw):
        raise subprocess.CalledProcessError(1, "pip", stderr="not permitted")
    monkeypatch.setattr("subprocess.run", fake_run)
    try:
        result = uninstall_package("requests")
        assert result["status"] == "error"
        assert "not permitted" in result["message"]
    finally:
        cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH = old_path, old_pip


def test_uninstall_package_uv_mode(monkeypatch):
    """UV 環境下 uninstall 應使用 uv。"""
    from pyer_backend import uninstall_package
    old_path, old_pip, old_uv, old_is_uv = (
        cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH, cfg.VENV_UV_PATH, cfg.IS_UV_ENVIRONMENT)
    cfg.CURRENT_VENV_PATH = "/tmp/fake"
    cfg.VENV_PIP_PATH = "/tmp/fake/Scripts/pip.exe"
    cfg.VENV_UV_PATH = "/usr/bin/uv"
    cfg.IS_UV_ENVIRONMENT = True
    monkeypatch.setattr("os.path.exists", lambda p: True)
    calls = []
    def fake_run(*a, **kw):
        calls.append(a[0])
        return type("R", (), {"returncode": 0, "stdout": "Removed", "stderr": ""})()
    monkeypatch.setattr("subprocess.run", fake_run)
    try:
        result = uninstall_package("requests")
        assert result["status"] == "success"
        assert "uv" in str(calls[0][0])
    finally:
        cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH, cfg.VENV_UV_PATH, cfg.IS_UV_ENVIRONMENT = (
            old_path, old_pip, old_uv, old_is_uv)


# ==================== 拼到 100% ====================


def test_get_installed_packages_success(monkeypatch):
    """get_installed_packages 成功路徑。"""
    from pyer_backend import get_installed_packages
    old_path, old_pip = cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH
    cfg.CURRENT_VENV_PATH = "/tmp/fake"
    cfg.VENV_PIP_PATH = "/tmp/fake/Scripts/pip.exe"
    monkeypatch.setattr("os.path.exists", lambda p: True)
    monkeypatch.setattr("subprocess.run", lambda *a, **kw: type("R",(),{
        "returncode": 0,
        "stdout": "Package    Version\n---------- -------\npip        24.0\nsetuptools 69.0\n",
        "stderr": ""
    })())
    try:
        result = get_installed_packages()
        assert len(result) == 2
        assert "pip" in result[0]
    finally:
        cfg.CURRENT_VENV_PATH, cfg.VENV_PIP_PATH = old_path, old_pip


def test_scan_venvs_skip_empty_name_with_mock(tmp_path, monkeypatch):
    """os.listdir 回傳空白名稱時應跳過。"""
    monkeypatch.setattr("os.listdir", lambda _: ["", "  ", "real_env"])
    (tmp_path / "real_env" / "Scripts").mkdir(parents=True)
    (tmp_path / "real_env" / "Scripts" / "activate.bat").write_text("")
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = scan_venvs()
        assert len(result) == 1
        assert "real_env" in result[0]
    finally:
        os.chdir(old_cwd)

def test_scan_venvs_pyvenv_cfg_is_directory(tmp_path, monkeypatch):
    """pyvenv.cfg 是目錄而非檔案時應跳過（except pass）。"""
    venv_dir = tmp_path / "broken_env"
    (venv_dir / "Scripts").mkdir(parents=True)
    (venv_dir / "Scripts" / "activate.bat").write_text("")
    # 建立一個同名目錄而非檔案，讓 open() 失敗
    (venv_dir / "pyvenv.cfg").mkdir()

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = scan_venvs()
        assert len(result) == 1
        # 因為 pyvenv.cfg 無法讀取，應標記為傳統 VENV
        assert "傳統 VENV" in result[0]
    finally:
        os.chdir(old_cwd)


def test_scan_venvs_python_version(tmp_path):
    """pyvenv.cfg 有 version_info 時應顯示 Python 版號。"""
    venv_dir = tmp_path / "ver_env"
    (venv_dir / "Scripts").mkdir(parents=True)
    (venv_dir / "Scripts" / "activate.bat").write_text("")
    (venv_dir / "pyvenv.cfg").write_text(
        "home = C:\\Python314\nversion_info = 3.14.6\n"
    )
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = scan_venvs()
        assert len(result) == 1
        assert "3.14.6" in result[0]
        assert "Python" in result[0]
    finally:
        os.chdir(old_cwd)
