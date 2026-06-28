import os
import sys
import shutil
import logging
import tkinter as tk
from tkinter import messagebox, ttk

from pyer import pyer_config as cfg
from pyer import pyer_logic as logic

# --- UI 主體與變數宣告最前端配置 ---
root = tk.Tk()
root.title("Pyer - Python 終極整合助手")
root.geometry("500x600")
root.resizable(False, False)

notebook = ttk.Notebook(root)
tab_env = ttk.Frame(notebook)
tab_pip = ttk.Frame(notebook)
notebook.add(tab_env, text=" 📁 虛擬環境管理 ")
notebook.add(tab_pip, text=" 📦 Pip 套件管理 ")
notebook.pack(fill="both", expand=True, padx=10, pady=5)

if cfg.CURRENT_VENV_NAME:  
    CREATE_STATE, ACTIVATE_STATE, DELETE_STATE, DEACTIVATE_STATE = tk.NORMAL, tk.DISABLED, tk.DISABLED, tk.NORMAL
    notice_msg = f"* 目前已啟動虛擬環境 [{cfg.CURRENT_VENV_NAME}]，關閉前鎖定現有環境管理功能"
else:  
    CREATE_STATE, ACTIVATE_STATE, DELETE_STATE, DEACTIVATE_STATE = tk.NORMAL, tk.NORMAL, tk.NORMAL, tk.DISABLED
    notice_msg = ""

bg_create_btn = "#4CAF50" if CREATE_STATE == tk.NORMAL else "#E0E0E0"
bg_activate_btn = "#2196F3" if ACTIVATE_STATE == tk.NORMAL else "#E0E0E0"
bg_delete_btn = "#F44336" if DELETE_STATE == tk.NORMAL else "#E0E0E0"
bg_deactivate_btn = "#FF9800" if DEACTIVATE_STATE == tk.NORMAL else "#E0E0E0"

var_create_use_uv = tk.BooleanVar(value=(True if cfg.VENV_UV_PATH else False))
var_create_auto_activate = tk.BooleanVar(value=True)
var_create_auto_cd = tk.BooleanVar(value=False)
var_activate_auto_cd = tk.BooleanVar(value=False)

label_status = tk.Label(root, text="", fg="gray", font=("Arial", 9))

# --- 功能函式區 ---
def refresh_list(select_name=None):
    venvs = logic.scan_venvs()
    combo_venvs['values'] = venvs
    if len(venvs) > 0:
        if select_name in venvs: combo_venvs.set(select_name)
        elif cfg.CURRENT_VENV_NAME in venvs: combo_venvs.set(cfg.CURRENT_VENV_NAME)
        elif cfg.IS_INSIDE_VENV_DIR and cfg.CURRENT_DIR_NAME in venvs: combo_venvs.set(cfg.CURRENT_DIR_NAME)
        else: combo_venvs.current(0)
    else:
        combo_venvs.set("未偵測到虛擬環境")

def refresh_package_list():
    listbox_installed.delete(0, tk.END)
    packages = logic.get_installed_packages()
    for pkg in packages:
        listbox_installed.insert(tk.END, pkg)

def update_entry_placeholder():
    """動態更新輸入欄位之預設推薦名稱，智慧繞過已佔用檔名"""
    suggested = logic.get_next_suggested_name("my_env")
    entry_create.delete(0, tk.END)
    entry_create.insert(0, suggested)

def do_create():
    name = entry_create.get().strip()
    if not name: return messagebox.showerror("錯誤", "請輸入虛擬環境名稱！")
    
    # 🌟【尊重意志・堅固報錯】如果使用者手動輸入的名稱真的已存在，像以前一樣狠狠拒絕！
    if os.path.exists(name): 
        return messagebox.showerror("錯誤", f"資料夾 '{name}' 已存在！請更換名稱或刪除舊環境。")
    
    use_uv = var_create_use_uv.get()
    core_text = "uv" if use_uv else "傳統 venv"
    
    label_status.config(text=f"正在使用 {core_text} 建立環境 {name}...", fg="#2196F3")
    root.update()
    
    try:
        logic.create_venv_exec(name, use_uv)
        label_status.config(text="建立成功！", fg="#4CAF50")
        
        if var_create_auto_activate.get():
            cmds = logic.generate_commands(name, var_create_auto_cd.get())
            messagebox.showinfo("成功", f"環境 {name} 建立成功！\n關閉視窗後將自動執行指定動作。")
            logic.write_action_and_exit(root, cmds)
        else:
            messagebox.showinfo("成功", f"環境 {name} 建立成功！")
            refresh_list(select_name=name)
            # 建立成功後，自動更新輸入框，推播下一個推薦序號
            update_entry_placeholder()
    except Exception as e:
        label_status.config(text="建立失敗", fg="#F44336")
        messagebox.showerror("錯誤", f"建立失敗: {str(e)}")

def do_activate():
    name = combo_venvs.get()
    if name == "未偵測到虛擬環境" or not name: return messagebox.showerror("錯誤", "請選擇虛擬環境！")
    cmds = logic.generate_commands(name, var_activate_auto_cd.get())
    logic.write_action_and_exit(root, cmds)

def do_deactivate():
    logic.write_action_and_exit(root, ["deactivate"])

def do_delete():
    name = combo_venvs.get()
    if name == "未偵測到虛擬環境" or not name: return messagebox.showerror("錯誤", "請選擇環境！")
    if messagebox.askyesno("確認刪除", f"確定要徹底刪除虛擬環境 [{name}] 嗎？"):
        try:
            # 剔除後綴還原真正名稱以執行 shutil
            real_name = name.split(" (")[0]
            shutil.rmtree(real_name)
            messagebox.showinfo("成功", f"已成功刪除虛擬環境 {real_name}")
            refresh_list()
            # 刪除環境釋放名稱後，同步讓輸入框推薦最靠前的名字
            update_entry_placeholder()
        except Exception as e:
            messagebox.showerror("錯誤", f"刪除失敗: {str(e)}")

def dummy_pip_action():
    messagebox.showinfo("提示", "這只是介面測試，目前暫無實際 Pip 功能。")


# ==================== 視覺佈局區塊 ====================
frame_create = tk.LabelFrame(tab_env, text=" 1. 建立新虛擬環境 ", padx=15, pady=10)
frame_create.pack(fill="x", padx=15, pady=5)

frame_input = tk.Frame(frame_create)
frame_input.pack(fill="x", pady=(0, 5))
tk.Label(frame_input, text="環境名稱:", font=("Arial", 10), state=CREATE_STATE).pack(side="left")
entry_create = tk.Entry(frame_input, font=("Arial", 11), state=CREATE_STATE)
entry_create.pack(side="left", fill="x", expand=True, padx=5)

# 初始化智慧型推薦序號名稱
update_entry_placeholder()

UV_CHECK_STATE = tk.NORMAL if (True if cfg.VENV_UV_PATH else False) else tk.DISABLED
chk_create_uv = tk.Checkbutton(frame_create, text="使用 uv 核心快速建立虛擬環境 (速度極快)", variable=var_create_use_uv, state=UV_CHECK_STATE)
chk_create_uv.pack(anchor="w")

chk_create_auto = tk.Checkbutton(frame_create, text="建立成功後自動啟動", variable=var_create_auto_activate, state=CREATE_STATE)
chk_create_auto.pack(anchor="w")

chk_create_cd = tk.Checkbutton(frame_create, text="同步切換(cd)至資料夾", variable=var_create_auto_cd, state=CREATE_STATE)
chk_create_cd.pack(anchor="w", pady=(0, 5))

tk.Button(frame_create, text="➕ 執行建立", command=do_create, bg=bg_create_btn, fg="white" if CREATE_STATE == tk.NORMAL else "gray", font=("Arial", 10, "bold"), state=CREATE_STATE).pack(fill="x")

# 區塊二：現有環境管理
frame_manage = tk.LabelFrame(tab_env, text=" 2. 現有環境管理 (啟動/刪除) ", padx=15, pady=10)
frame_manage.pack(fill="x", padx=15, pady=5)
combo_venvs = ttk.Combobox(frame_manage, font=("Arial", 11), state="readonly")
combo_venvs.pack(fill="x", pady=(0, 5))

chk_activate_cd = tk.Checkbutton(frame_manage, text="啟動時同步切換(cd)", variable=var_activate_auto_cd, state=ACTIVATE_STATE)
chk_activate_cd.pack(anchor="w", pady=(0, 10))

frame_btn_group = tk.Frame(frame_manage)
frame_btn_group.pack(fill="x")
tk.Button(frame_btn_group, text="🚀 啟動環境", command=do_activate, bg=bg_activate_btn, fg="white" if ACTIVATE_STATE == tk.NORMAL else "gray", font=("Arial", 10, "bold"), state=ACTIVATE_STATE).pack(side="left", fill="x", expand=True, padx=(0, 5))
tk.Button(frame_btn_group, text="🗑️ 刪除環境", command=do_delete, bg=bg_delete_btn, fg="white" if DELETE_STATE == tk.NORMAL else "gray", font=("Arial", 10, "bold"), state=DELETE_STATE).pack(side="right", fill="x", expand=True, padx=(5, 0))

# 區塊三：目前狀態控制
frame_exit = tk.LabelFrame(root, text=" 3. 目前狀態控制 ", padx=15, pady=10)
frame_exit.pack(fill="x", padx=15, pady=5)
btn_text = f"❌ 關閉/退出目前環境 ({cfg.CURRENT_VENV_NAME})" if cfg.CURRENT_VENV_NAME else "❌ 目前不在任何虛擬環境中"
tk.Button(frame_exit, text=btn_text, state=DEACTIVATE_STATE, command=do_deactivate, bg=bg_deactivate_btn, fg="white" if DEACTIVATE_STATE == tk.NORMAL else "gray", font=("Arial", 10, "bold"), pady=5).pack(fill="x")

if notice_msg: tk.Label(tab_env, text=notice_msg, fg="#F44336", font=("Arial", 10, "bold")).pack(pady=5)

# ==================== 頁籤二：Pip 套件管理 ====================
PIP_STATE = tk.NORMAL if cfg.CURRENT_VENV_NAME else tk.DISABLED
frame_pip_left = tk.LabelFrame(tab_pip, text=" 📥 安裝新套件 ", padx=10, pady=10)
frame_pip_left.pack(side="left", fill="both", expand=True, padx=(10, 5), pady=10)
tk.Label(frame_pip_left, text="💡 推薦常用快捷勾選:", font=("Arial", 9, "bold"), state=PIP_STATE).pack(anchor="w", pady=(0, 5))

recommend_pkgs = ["requests", "beautifulsoup4", "pandas", "numpy", "scikit-learn"]
checked_packages = {}
for pkg in recommend_pkgs:
    var = tk.BooleanVar(value=False)
    checked_packages[pkg] = var
    tk.Checkbutton(frame_pip_left, text=pkg, variable=var, state=PIP_STATE, font=("Arial", 9)).pack(anchor="w")

tk.Label(frame_pip_left, text="🔍 手動輸入套件名稱:", font=("Arial", 9, "bold"), state=PIP_STATE).pack(anchor="w", pady=(15, 2))
entry_custom_pkg = tk.Entry(frame_pip_left, font=("Arial", 11), state=PIP_STATE)
entry_custom_pkg.pack(fill="x", pady=(0, 10))
tk.Button(frame_pip_left, text="🚀 執行安裝", command=dummy_pip_action, bg="#E0E0E0", fg="gray", font=("Arial", 10, "bold"), state=PIP_STATE).pack(fill="x", pady=5)

frame_pip_right = tk.LabelFrame(tab_pip, text=" 📋 已安裝套件清單 ", padx=10, pady=10)
frame_pip_right.pack(side="right", fill="both", expand=True, padx=(5, 10), pady=10)
scrollbar = tk.Scrollbar(frame_pip_right)
scrollbar.pack(side="right", fill="y")
listbox_installed = tk.Listbox(frame_pip_right, yscrollcommand=scrollbar.set, font=("Courier", 9), state=PIP_STATE)
listbox_installed.pack(fill="both", expand=True)
scrollbar.config(command=listbox_installed.yview)
tk.Button(frame_pip_right, text="🗑️ 移除選中套件", command=dummy_pip_action, bg="#E0E0E0", fg="gray", font=("Arial", 10, "bold"), state=PIP_STATE).pack(fill="x", pady=(5, 0))

if not cfg.CURRENT_VENV_NAME:
    tk.Label(tab_pip, text="⚠️ 請先在第一頁籤啟動虛擬環境\n才可管理該環境的 Pip 套件", fg="#F44336", font=("Arial", 12, "bold"), bg="#F0F0F0", bd=2, relief="solid").place(relx=0.5, rely=0.5, anchor="center")

# 底部狀態列配置
if cfg.CURRENT_VENV_NAME:
    manager_text = "UV" if cfg.IS_UV_ENVIRONMENT else "傳統 VENV"
else:
    manager_text = "UV (全域優先)" if (True if cfg.VENV_UV_PATH else False) else "傳統 VENV"

python_ver_info = cfg.format_python_version_summary()
status_text = f"Python: {python_ver_info}  |  終端機核心: {str(cfg.SHELL_TYPE).upper()}  |  管理程式: {manager_text}  |  狀態: " + ("已進入環境" if cfg.CURRENT_VENV_NAME else "處於環境路徑下" if cfg.IS_INSIDE_VENV_DIR else "全域環境")
label_status.config(text=status_text)
label_status.pack(pady=5)

# 初始化選單與清單
try:
    refresh_list()
    if cfg.CURRENT_VENV_NAME: refresh_package_list()
except Exception as e:
    logging.error(f"實體初始化元件崩潰: {str(e)}")

if os.path.exists(cfg.TMP_FILE_PATH): os.remove(cfg.TMP_FILE_PATH)
logging.info("主畫面 mainloop 準備啟動...")
root.mainloop()


def main():
    """Launch the pyer GUI."""
    root.mainloop()


if __name__ == "__main__":
    main()
