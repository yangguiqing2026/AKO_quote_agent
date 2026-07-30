"""
AKO_quote_agent GUI 模块
提供基于 PySide6 + qfluentwidgets 的桌面客户端界面。

品牌色系：
  奶油金 rgb(235,218,185) → 主背景
  深棕黑 rgb(35,30,28)    → 文字/边框
  琥珀金 rgb(160,140,100)  → 按钮高亮
  冷暖灰 rgb(195,190,180)  → 卡片背景

模块结构：
  - ako_style.py      品牌视觉规范
  - login_dialog.py   登录弹窗
  - main_window.py    主窗口（左侧导航 + 右侧内容区)
  - quote_page.py     报价计算页
  - history_page.py   报价历史页
  - settings_page.py  系统设置页
  - launcher.py       启动入口
  - auth_manager.py   认证管理
  - change_password_dialog.py  修改密码窗口
  - user_management_dialog.py  用户管理窗口
"""

from .launcher import run_gui
from .main_window import AKOMainWindow
from .login_dialog import LoginDialog
from .ako_style import AKO_COLORS, AKO_FONTS, GLOBAL_STYLESHEET

__all__ = [
    "run_gui",
    "AKOMainWindow",
    "LoginDialog",
    "AKO_COLORS",
    "AKO_FONTS",
    "GLOBAL_STYLESHEET",
]