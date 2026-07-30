"""
AKO_quote_agent GUI 入口文件
用于 PyInstaller 打包和直接运行。

用法：
    python AKO_quote_agent_gui.py          # 跳过登录，直接进入主界面
    python AKO_quote_agent_gui.py --login  # 需要登录验证
"""
import sys
import os

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ako_quote_agent.gui.launcher import run_gui

if __name__ == "__main__":
    skip_login = "--login" not in sys.argv
    run_gui(skip_login=skip_login)