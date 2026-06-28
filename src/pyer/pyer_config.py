import os
import sys
import shutil
import logging
import platform

# 初始化 Logger 機制
TOOL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_path = os.path.join(TOOL_DIR, "pyer_debug.log")
logging.basicConfig(
    filename=log_path,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8"
)

logging.info("--- Pyer Config 模組啟動 (打通全域 uv 偵測鏈結) ---")

# 精準獲取命令列字串參數
try:
    if len(sys.argv) > 1:
        SHELL_TYPE = sys.argv[1] # 修正回正確的單一字串拿取
    else:
        SHELL_TYPE = "cmd"
    logging.info(f"解析後的 SHELL_TYPE 結果: {SHELL_TYPE}")
except Exception as e:
    SHELL_TYPE = "cmd"
    logging.error(f"解析 sys.argv 失敗: {str(e)}")

# 安全解析虛擬環境變數
try:
    env_path_raw = os.environ.get("VIRTUAL_ENV")
    if env_path_raw and isinstance(env_path_raw, str) and env_path_raw.strip():
        CURRENT_VENV_PATH = env_path_raw
        CURRENT_VENV_NAME = os.path.basename(CURRENT_VENV_PATH)
    else:
        CURRENT_VENV_PATH = None
        CURRENT_VENV_NAME = None
    logging.info(f"安全解析環境變數成功 - 路徑: {CURRENT_VENV_PATH} | 名稱: {CURRENT_VENV_NAME}")
except Exception as e:
    CURRENT_VENV_PATH = None
    CURRENT_VENV_NAME = None
    logging.error(f"解析 VIRTUAL_ENV 發生異常: {str(e)}")

# 組裝標準 pip 檢查點
if CURRENT_VENV_PATH:
    VENV_PIP_PATH = os.path.join(CURRENT_VENV_PATH, "Scripts", "pip.exe")
else:
    VENV_PIP_PATH = None

# ==================== 【智慧型大修正】無條件探測全域與本地 uv ====================
IS_UV_ENVIRONMENT = False
VENV_UV_PATH = None

# 【關鍵修正】把尋找 uv 的邏輯移到最外層！不論有沒有啟動環境，都必須知道這台電腦有沒有裝 uv
global_uv = shutil.which("uv")
if global_uv:
    VENV_UV_PATH = global_uv
    logging.info(f"🔍 成功在系統全域環境變數中尋找到 uv 執行檔: {VENV_UV_PATH}")
elif CURRENT_VENV_PATH:
    # 全域找不到，且目前有進入虛擬環境時，才嘗試找本地內部
    local_uv = os.path.join(CURRENT_VENV_PATH, "Scripts", "uv.exe")
    if os.path.exists(local_uv):
        VENV_UV_PATH = local_uv
        logging.info(f"🔍 成功在虛擬環境內部 Scripts 中尋找到 uv 執行檔: {VENV_UV_PATH}")

# 判斷目前啟動的虛擬環境，是不是由 uv 所建立與管理的特徵
if CURRENT_VENV_PATH:
    cfg_path = os.path.join(CURRENT_VENV_PATH, "pyvenv.cfg")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8", errors="ignore") as cfg_f:
                cfg_content = cfg_f.read().lower()
                if "uv" in cfg_content or "creator = uv" in cfg_content:
                    IS_UV_ENVIRONMENT = True
                    logging.info("🎯 偵測特徵成功：目前已進入之虛擬環境為 UV 環境")
        except Exception as e:
            logging.error(f"讀取 pyvenv.cfg 失敗: {str(e)}")

logging.info(f"uv 終極探測結果 - 實體路徑: {VENV_UV_PATH} | 目前是否已進入 uv 環境: {IS_UV_ENVIRONMENT}")
# ============================================================================

if CURRENT_VENV_PATH:
    logging.info(f"配置虛擬環境專專屬 pip: {VENV_PIP_PATH}")
else:
    logging.info("全域環境下，不配置專屬 pip")

# 徹底清洗無謂的本地目錄探測
IS_INSIDE_VENV_DIR = False 

# 嚴防根目錄空字串死穴
try:
    raw_dir_name = os.path.basename(os.getcwd())
    CURRENT_DIR_NAME = raw_dir_name if raw_dir_name and raw_dir_name.strip() else "root_dir"
    logging.info(f"安全解析工作目錄名稱: {CURRENT_DIR_NAME}")
except Exception as e:
    CURRENT_DIR_NAME = "root_dir"
    logging.error(f"解析工作目錄異常: {str(e)}")

# 決定臨時指令腳本檔名
if "powershell" in str(SHELL_TYPE).lower():
    TMP_FILE_PATH = os.path.join(TOOL_DIR, "pyer_next.ps1")
else:
    TMP_FILE_PATH = os.path.join(TOOL_DIR, "pyer_next.bat")


# ==================== Python 版本資訊查詢 ====================

def get_python_version_info():
    """Return a dict with current Python version and environment info.

    Returns:
        dict with keys:
            full_version (str): sys.version string
            version_info (tuple): (major, minor, micro, releaselevel, serial)
            implementation (str): Python implementation (e.g. 'CPython')
            executable (str): path to current Python interpreter
            is_venv (bool): True if running inside a virtual environment
            global_python (str): path (or version string) of global/system Python
    """
    is_venv = bool(CURRENT_VENV_PATH) or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )

    # Find global/system Python path
    global_python = ""
    try:
        base_exec = getattr(sys, "base_exec_prefix", sys.prefix)
        candidates = []
        if os.name == "nt":  # Windows
            candidates = [
                os.path.join(base_exec, "python.exe"),
                os.path.join(base_exec, "python3.exe"),
            ]
        else:  # Linux/macOS
            candidates = [
                os.path.join(base_exec, "bin", "python3"),
                os.path.join(base_exec, "bin", "python"),
            ]
        for path in candidates:
            if os.path.exists(path):
                global_python = path
                break
        if not global_python:
            global_python = shutil.which("python3") or shutil.which("python") or sys.executable
    except Exception:
        global_python = sys.executable

    return {
        "full_version": sys.version.strip(),
        "version_info": (
            sys.version_info.major,
            sys.version_info.minor,
            sys.version_info.micro,
            sys.version_info.releaselevel,
            sys.version_info.serial,
        ),
        "implementation": platform.python_implementation(),
        "executable": sys.executable,
        "is_venv": is_venv,
        "global_python": global_python,
    }


def format_python_version_summary():
    """Return a human-readable summary string of the current Python version info.

    Returns:
        str: e.g. "Python 3.11.0 (CPython) [venv: my_venv]" or
             "Python 3.11.0 (CPython) [global: /usr/bin/python3]"
    """
    info = get_python_version_info()
    ver = ".".join(str(v) for v in info["version_info"][:3])
    impl = info["implementation"]

    if info["is_venv"]:
        location = "venv"
    else:
        location = "global"

    return f"Python {ver} ({impl}) [{location}]"
