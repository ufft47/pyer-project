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
