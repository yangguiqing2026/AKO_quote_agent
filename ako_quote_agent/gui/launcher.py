"""
launcher.py - AKO_quote_agent GUI 启动脚本
集成 AKO_login_guard 登录验证，品牌奶油金主题。
"""
import sys
import os

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

try:
    from gui.auth_manager import AuthManager
    from gui.login_dialog import LoginDialog
    from gui.main_window import AKOMainWindow
except ImportError:
    # 兼容直接 python launcher.py 运行
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from auth_manager import AuthManager
    from login_dialog import LoginDialog
    from main_window import AKOMainWindow


def _find_icon_path():
    """查找 Logo.ico 路径"""
    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Logo.ico"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Logo.ico"),
        "Logo.ico",
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None


def run_gui(skip_login=False):
    """启动 AKO_quote_agent GUI（含登录验证）"""
    # 高 DPI 适配
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("AKO_quote_agent")
    app.setOrganizationName("AKO_studio")

    # 设置任务栏图标
    icon_path = _find_icon_path()
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))

    # 跳过登录模式：用测试用户直接进入主界面
    if skip_login:
        user = {"username": "admin", "role": "admin"}
        main_window = AKOMainWindow(user)
        if icon_path:
            main_window.setWindowIcon(QIcon(icon_path))
        main_window.show()
        return sys.exit(app.exec())

    auth = AuthManager()

    # Step 1: 检查 Remember Me Token
    user = auth.validate_token()
    if user:
        # Token 有效，直接进主程序
        main_window = AKOMainWindow(user)
        if icon_path:
            main_window.setWindowIcon(QIcon(icon_path))
        main_window.show()
        return sys.exit(app.exec())

    # Step 2: 弹出登录窗口
    login_dialog = LoginDialog()
    if icon_path:
        login_dialog.setWindowIcon(QIcon(icon_path))
    if login_dialog.exec() == LoginDialog.Accepted:
        user = login_dialog.get_user()
        remember = login_dialog.remember_me

        if user:
            # 如果勾选了记住我但还没有 Token
            if remember:
                auth.generate_token(user["username"])

            # Step 3: 启动主窗口
            main_window = AKOMainWindow(user)
            if icon_path:
                main_window.setWindowIcon(QIcon(icon_path))
            main_window.show()
            return sys.exit(app.exec())
        else:
            return sys.exit(1)
    else:
        return sys.exit(0)


if __name__ == "__main__":
    run_gui()