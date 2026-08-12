# -*- coding: utf-8 -*-
"""开机自启注册/注销脚本（API 配额仪表盘 补充工具）

用法（在项目根目录下）：
  python install_autostart.py register    # 注册开机自启（写 HKCU Run，用 pythonw 静默启动）
  python install_autostart.py unregister  # 取消开机自启
  python install_autostart.py status      # 查看当前状态

实现：写入注册表 HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
值为 "pythonw.exe" 指向本脚本同级 main.py。开机登录即常驻托盘，无控制台窗口。
"""
import os
import sys
import winreg

APP_NAME = "APIQuotaDashboard"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
MAIN_PY = os.path.join(PROJECT_ROOT, "main.py")


def _pythonw_path():
    """优先 pythonw.exe（无控制台）；找不到则退回 python.exe（会带一个控制台窗口）。"""
    exe = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if os.path.isfile(exe):
        return exe
    return sys.executable


def _cmd():
    return f'"{_pythonw_path()}" "{MAIN_PY}"'


def register():
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
        winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, _cmd())
    print(f"[autostart] 已注册开机自启：{_cmd()}")


def unregister():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, APP_NAME)
        print("[autostart] 已取消开机自启")
    except FileNotFoundError:
        print("[autostart] 当前未注册开机自启")


def status():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_QUERY_VALUE) as k:
            val, _ = winreg.QueryValueEx(k, APP_NAME)
        print(f"[autostart] 已注册：{val}")
    except FileNotFoundError:
        print("[autostart] 未注册")


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    {"register": register, "unregister": unregister, "status": status}.get(action, status)()
