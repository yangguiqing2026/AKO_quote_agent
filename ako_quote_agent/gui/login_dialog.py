"""
login_dialog.py - AKO 登录弹窗
基于 qfluentwidgets，品牌色系。
"""
import os

# [ARCHIVED_GUI] from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QCheckBox, QPushButton, QSpacerItem, QSizePolicy,
)
# [ARCHIVED_GUI] from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint
# [ARCHIVED_GUI] from PySide6.QtGui import QPixmap

from qfluentwidgets import (
    PushButton, PrimaryPushButton, MessageBox,
    InfoBar, InfoBarPosition, LineEdit, PasswordLineEdit,
    CheckBox, StateToolTip,
)

try:
    from .ako_style import AKO_COLORS, AKO_FONTS
except ImportError:
    from ako_style import AKO_COLORS, AKO_FONTS

try:
    from ..auth_manager import AuthManager
except ImportError:
    try:
        from .auth_manager import AuthManager
    except ImportError:
        from auth_manager import AuthManager


class LoginDialog(QDialog):
    """AKO 登录窗口 - 品牌奶油金主题"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth = AuthManager()
        self.user_info = None
        self.remember_me = False
        self.must_change_password = False
        self._shake_anim = None

        self._init_ui()

    def _init_ui(self):
        """初始化登录窗口 UI"""
        self.setWindowTitle("AKO 内部系统登录")
        self.setFixedSize(440, 480)
        self.setModal(True)
        self.setWindowFlags(
            Qt.Dialog | Qt.WindowCloseButtonHint | Qt.WindowTitleHint
        )

        # 窗口整体样式
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {AKO_COLORS["main_bg"]};
                border: 2px solid {AKO_COLORS["light_border"]};
                border-radius: 12px;
            }}
            QLabel {{
                color: {AKO_COLORS["text"]};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 24, 48, 24)
        layout.setSpacing(10)

        # Logo - 使用 Logo.ico
        logo_label = QLabel()
        icon_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Logo.ico"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Logo.ico"),
            "Logo.ico",
        ]
        for p in icon_paths:
            if os.path.exists(p):
                pixmap = QPixmap(p).scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                logo_label.setPixmap(pixmap)
                break
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setFixedSize(84, 84)
        logo_label.setStyleSheet(f"""
            QLabel {{
                background-color: {AKO_COLORS['accent']};
                border-radius: 14px;
                padding: 6px;
                border: none;
            }}
        """)
        layout.addWidget(logo_label, 0, Qt.AlignCenter)

        # 标题
        title = QLabel("AKO 内部系统登录")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {AKO_COLORS['text']};"
        )
        layout.addWidget(title)

        # 副标题
        subtitle = QLabel("请输入管理员分配的账号和密码")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(
            f"font-size: 12px; color: {AKO_COLORS['disabled_text']};"
        )
        layout.addWidget(subtitle)

        layout.addSpacing(12)

        # 用户名输入
        user_label = QLabel("用户名")
        user_label.setStyleSheet(
            f"font-weight: bold; font-size: 13px; color: {AKO_COLORS['text']};"
        )
        layout.addWidget(user_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("输入用户名（拼音全小写）")
        self.username_input.setMinimumHeight(42)
        self.username_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {AKO_COLORS["input_bg"]};
                border: 2px solid {AKO_COLORS["light_border"]};
                border-radius: 6px;
                padding: 8px 14px;
                font-size: 14px;
                color: {AKO_COLORS["text"]};
            }}
            QLineEdit:focus {{
                border: 2px solid {AKO_COLORS["accent"]};
            }}
        """)
        layout.addWidget(self.username_input)

        # 密码输入
        pwd_label = QLabel("密码")
        pwd_label.setStyleSheet(
            f"font-weight: bold; font-size: 13px; color: {AKO_COLORS['text']};"
        )
        layout.addWidget(pwd_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("输入密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(42)
        self.password_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {AKO_COLORS["input_bg"]};
                border: 2px solid {AKO_COLORS["light_border"]};
                border-radius: 6px;
                padding: 8px 14px;
                font-size: 14px;
                color: {AKO_COLORS["text"]};
            }}
            QLineEdit:focus {{
                border: 2px solid {AKO_COLORS["accent"]};
            }}
        """)
        self.password_input.returnPressed.connect(self._on_login)
        layout.addWidget(self.password_input)

        # 错误提示
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet(
            f"color: {AKO_COLORS['danger']}; font-size: 12px;"
        )
        layout.addWidget(self.error_label)

        # 记住我
        self.remember_check = QCheckBox("记住我（7天内免登录）")
        self.remember_check.setStyleSheet(
            f"font-size: 12px; color: {AKO_COLORS['text']};"
        )
        layout.addWidget(self.remember_check)

        layout.addSpacing(6)

        # 登录按钮
        login_btn = QPushButton("登  录")
        login_btn.setMinimumHeight(46)
        login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AKO_COLORS["accent"]};
                color: {AKO_COLORS["white"]};
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: {AKO_COLORS["hover_accent"]};
            }}
            QPushButton:pressed {{
                background-color: #8A7850;
            }}
        """)
        login_btn.clicked.connect(self._on_login)
        layout.addWidget(login_btn)

        # 底部提示
        footer = QLabel("首次登录？请联系管理员开通账号")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet(
            f"font-size: 11px; color: {AKO_COLORS['disabled_text']};"
        )
        layout.addWidget(footer)

        layout.addStretch()

    def _on_login(self):
        """登录按钮处理"""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            self._show_error("请输入用户名和密码")
            return

        success, result, must_change = self.auth.authenticate(username, password)

        if success:
            self.user_info = result
            self.remember_me = self.remember_check.isChecked()
            self.must_change_password = must_change

            if must_change:
                self.error_label.setText("")
                self.password_input.clear()
                self._on_force_change_password()
            else:
                if self.remember_me:
                    self.auth.generate_token(username)
                self.accept()
        else:
            self._show_error(result)
            self._shake_inputs()

    def _on_force_change_password(self):
        """首次登录强制修改密码"""
        try:
            from .change_password_dialog import ChangePasswordDialog
        except ImportError:
            from change_password_dialog import ChangePasswordDialog
        dialog = ChangePasswordDialog(
            self.user_info["username"],
            is_forced=True,
            parent=self
        )
        if dialog.exec() == QDialog.Accepted:
            self.must_change_password = False
            if self.remember_me:
                self.auth.generate_token(self.user_info["username"])
            self.accept()
        else:
            self._show_error("首次登录必须修改密码")
            self._shake_inputs()

    def _show_error(self, message: str):
        """显示错误信息"""
        self.error_label.setText(message)

        # 密码框红框效果
        self.password_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: #FFF0F0;
                border: 2px solid {AKO_COLORS["danger"]};
                border-radius: 6px;
                padding: 8px 14px;
                font-size: 14px;
                color: {AKO_COLORS["text"]};
            }}
        """)
        # 1.5秒后恢复
        # [ARCHIVED_GUI] from PySide6.QtCore import QTimer
        QTimer.singleShot(1500, self._clear_error_style)

    def _clear_error_style(self):
        """清除密码框错误样式"""
        self.password_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {AKO_COLORS["input_bg"]};
                border: 2px solid {AKO_COLORS["light_border"]};
                border-radius: 6px;
                padding: 8px 14px;
                font-size: 14px;
                color: {AKO_COLORS["text"]};
            }}
            QLineEdit:focus {{
                border: 2px solid {AKO_COLORS["accent"]};
            }}
        """)

    def _shake_inputs(self):
        """密码框左右抖动动画"""
        if self._shake_anim:
            self._shake_anim.stop()

        original_pos = self.password_input.pos()
        self._shake_anim = QPropertyAnimation(self.password_input, b"pos")
        self._shake_anim.setDuration(400)
        self._shake_anim.setEasingCurve(QEasingCurve.OutBounce)

        self._shake_anim.setKeyValueAt(0, original_pos)
        self._shake_anim.setKeyValueAt(0.1, original_pos + QPoint(10, 0))
        self._shake_anim.setKeyValueAt(0.2, original_pos + QPoint(-10, 0))
        self._shake_anim.setKeyValueAt(0.3, original_pos + QPoint(8, 0))
        self._shake_anim.setKeyValueAt(0.4, original_pos + QPoint(-8, 0))
        self._shake_anim.setKeyValueAt(0.5, original_pos + QPoint(5, 0))
        self._shake_anim.setKeyValueAt(0.6, original_pos + QPoint(-5, 0))
        self._shake_anim.setKeyValueAt(0.7, original_pos + QPoint(3, 0))
        self._shake_anim.setKeyValueAt(0.8, original_pos + QPoint(-3, 0))
        self._shake_anim.setKeyValueAt(1.0, original_pos)

        self._shake_anim.start()

    def get_user(self) -> dict:
        """获取登录后的用户信息"""
        return self.user_info