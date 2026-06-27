"""Pyer 純後端 — 無 tkinter，回傳純資料結構。"""

import os
import sys
import subprocess
import shutil
import logging

import pyer_config as cfg


def scan_venvs() -> list[str]:
    """掃描 CWD 下的虛擬環境，回傳名稱清單（含 UV/傳統標記）。"""
    venvs_raw = []
    try:
        for item in os.listdir("."):
            if os.path.isdir(item) and os.path.exists(
                os.path.join(item, "Scripts", "activate.bat")
            ):
                venvs_raw.append(item)
    except Exception as e:
        logging.error(f"scan_venvs 讀取目錄異常: {str(e)}")

    processed = []
    for env in venvs_raw:
        if not env or not env.strip():
            continue
        cfg_file = os.path.join(env, "pyvenv.cfg")
        is_uv = False
        if os.path.exists(cfg_file):
            try:
                with open(cfg_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().lower()
                    if "uv" in content or "creator = uv" in content:
                        is_uv = True
            except Exception:
                pass
        suffix = " (UV)" if is_uv else " (傳統 VENV)"
        processed.append(f"{env}{suffix}")

    return processed


def get_next_suggested_name(base_name: str = "my_env") -> str:
    """建議下一個沒被佔用的目錄名稱（不實際建立）。"""
    if not os.path.exists(base_name):
        return base_name
    counter = 1
    while True:
        new_name = f"{base_name}_{counter}"
        if not os.path.exists(new_name):
            return new_name
        counter += 1


def generate_commands(target_env_name: str, should_cd: bool) -> list[str]:
    """產生啟動虛擬環境的終端機指令。"""
    clean = target_env_name.split(" (")[0]

    cmds = []
    if cfg.IS_INSIDE_VENV_DIR:
        target_path = os.path.abspath(".")
    else:
        target_path = os.path.abspath(clean)
        if should_cd:
            if "powershell" in str(cfg.SHELL_TYPE).lower():
                cmds.append(f'Set-Location "{target_path}"')
            else:
                cmds.append(f'cd /d "{target_path}"')

    if "powershell" in str(cfg.SHELL_TYPE).lower():
        cmds.append(f'. "{os.path.join(target_path, "Scripts", "Activate.ps1")}"')
    else:
        cmds.append(f'call "{os.path.join(target_path, "Scripts", "activate.bat")}"')
    return cmds


def write_commands_file(commands_list: list[str]) -> str:
    """將終端機指令寫入暫存檔，回傳檔案路徑。

    不回傳 tkinter 物件、不 destroy 視窗、不 exit。
    """
    logging.info(f"準備寫入終端機的指令列表: {commands_list}")
    try:
        with open(cfg.TMP_FILE_PATH, "w", encoding="utf-8") as f:
            for cmd in commands_list:
                f.write(cmd + "\n")
        logging.info(f"指令已寫入: {cfg.TMP_FILE_PATH}")
    except Exception as e:
        logging.error(f"寫入臨時腳本失敗: {str(e)}")
        raise
    return cfg.TMP_FILE_PATH


def get_installed_packages() -> list[str]:
    """執行 pip list，回傳套件清單。"""
    if (
        not cfg.CURRENT_VENV_PATH
        or not cfg.VENV_PIP_PATH
        or not os.path.exists(cfg.VENV_PIP_PATH)
    ):
        return []
    try:
        logging.info("開始背景執行 pip list 讀取套件...")
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        result = subprocess.run(
            [cfg.VENV_PIP_PATH, "list", "--format=columns"],
            capture_output=True,
            text=True,
            check=True,
            startupinfo=startupinfo,
            encoding="utf-8",
        )
        lines = result.stdout.strip().split("\n")
        logging.info(f"成功讀取到套件，共計 {max(0, len(lines) - 2)} 個")
        return lines[2:] if len(lines) > 2 else []
    except Exception as e:
        logging.error(f"背景讀取 pip list 失敗: {str(e)}")
        return [f"讀取失敗: {str(e)}"]


def create_venv_exec(name: str, use_uv: bool) -> None:
    """建立虛擬環境。成功不回傳，失敗 raise。"""
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    clean_name = name.strip()

    if use_uv and cfg.VENV_UV_PATH:
        logging.info(f"使用 uv 建立: {cfg.VENV_UV_PATH} venv {clean_name}")
        subprocess.run(
            [str(cfg.VENV_UV_PATH), "venv", clean_name],
            check=True,
            startupinfo=startupinfo,
        )
    else:
        logging.info(f"使用傳統 venv 建立: python -m venv {clean_name}")
        subprocess.run(
            [sys.executable, "-m", "venv", clean_name],
            check=True,
            startupinfo=startupinfo,
        )


def delete_venv(folder_name: str) -> None:
    """刪除虛擬環境資料夾。"""
    real_name = folder_name.split(" (")[0]
    logging.info(f"刪除虛擬環境: {real_name}")
    shutil.rmtree(real_name)
