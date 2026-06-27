import os
import sys
import subprocess
import logging
from pyer import pyer_config as cfg

def write_action_and_exit(root_window, commands_list):
    """寫入臨時指令腳本，強制關閉 UI 並中斷 Python 程序"""
    logging.info(f"準備寫入終端機的指令列表: {commands_list}")
    try:
        with open(cfg.TMP_FILE_PATH, "w", encoding="utf-8") as f:
            for cmd in commands_list:
                f.write(cmd + "\n")
    except Exception as e:
        logging.error(f"寫入臨時腳本失敗: {str(e)}")
    root_window.destroy()
    sys.exit(0)

def scan_venvs():
    """掃描當前目錄下的虛擬環境，並在名稱後面加上(管理程式名稱)"""
    venvs_raw = []
    try:
        for item in os.listdir("."):
            if os.path.isdir(item) and os.path.exists(os.path.join(item, "Scripts", "activate.bat")):
                venvs_raw.append(item)
    except Exception as e:
        logging.error(f"scan_venvs 讀取目錄異常: {str(e)}")

    processed_venvs = []
    for env in venvs_raw:
        if not env or not env.strip():
            continue
        cfg_file = os.path.join(env, "pyvenv.cfg")
        is_uv_sub = False
        if os.path.exists(cfg_file):
            try:
                with open(cfg_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().lower()
                    if "uv" in content or "creator = uv" in content:
                        is_uv_sub = True
            except Exception:
                pass
        
        suffix = " (UV)" if is_uv_sub else " (傳統 VENV)"
        processed_venvs.append(f"{env}{suffix}")

    return processed_venvs

def get_next_suggested_name(base_name):
    """【精準實作】僅預測下一個沒被佔用的安全名字，供 UI 輸入框預設顯示，絕不擅自建立"""
    if not os.path.exists(base_name):
        return base_name
    counter = 1
    while True:
        new_name = f"{base_name}_{counter}"
        if not os.path.exists(new_name):
            return new_name
        counter += 1

def generate_commands(target_env_name, should_cd):
    """根據 Shell 核心生成對應啟動指令"""
    clean_env_name = target_env_name.split(" (")
    
    cmds = []
    if cfg.IS_INSIDE_VENV_DIR:
        target_abs_path = os.path.abspath(".")
    else:
        target_abs_path = os.path.abspath(clean_env_name)
        if should_cd:
            if "powershell" in str(cfg.SHELL_TYPE).lower():
                cmds.append(f'Set-Location "{target_abs_path}"')
            else:
                cmds.append(f'cd /d "{target_abs_path}"')
            
    if "powershell" in str(cfg.SHELL_TYPE).lower():
        cmds.append(f'. "{os.path.join(target_abs_path, "Scripts", "Activate.ps1")}"')
    else:
        cmds.append(f'call "{os.path.join(target_abs_path, "Scripts", "activate.bat")}"')
    return cmds

def get_installed_packages():
    """安全背景執行 pip list 獲取當前套件清單"""
    if not cfg.CURRENT_VENV_PATH or not cfg.VENV_PIP_PATH or not os.path.exists(cfg.VENV_PIP_PATH):
        return []
    try:
        logging.info("開始背景執行 pip list 讀取套件...")
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        result = subprocess.run(
            [cfg.VENV_PIP_PATH, "list", "--format=columns"], 
            capture_output=True, text=True, check=True, startupinfo=startupinfo, encoding="utf-8"
        )
        lines = result.stdout.strip().split("\n")
        logging.info(f"成功讀取到套件，共計 {max(0, len(lines)-2)} 個")
        return lines[2:] if len(lines) > 2 else []
    except Exception as e:
        logging.error(f"背景讀取 pip list 失敗: {str(e)}")
        return [f"讀取失敗: {str(e)}"]

def create_venv_exec(name, use_uv):
    """安全建立虛擬環境：尊重使用者意志，直接建立傳入的實體名稱"""
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    clean_name = name.strip()
    
    if use_uv and cfg.VENV_UV_PATH:
        logging.info(f"實體調用全域絕對路徑建立 uv 環境: {cfg.VENV_UV_PATH} venv {clean_name}")
        subprocess.run([str(cfg.VENV_UV_PATH), "venv", clean_name], check=True, startupinfo=startupinfo)
    else:
        logging.info(f"使用標準傳統 venv 建立環境: python -m venv {clean_name}")
        subprocess.run([sys.executable, "-m", "venv", clean_name], check=True, startupinfo=startupinfo)
