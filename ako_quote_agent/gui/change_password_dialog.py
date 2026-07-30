"""
change_password_dialog.py - 修改密码窗口
支持：首次强制修改 / 员工自助修改
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSpacerItem,
)
from PySide6.QtCore import Qt

try:
    from .ako_style import AKO_COLORS
    from .auth_manager import AuthManager
except ImportError:
    from ako_style import AKO_COLORS
    from auth_manager import AuthManager


class ChangePasswordDialog(QDialog):
    """修改密码对话框"""

    def __init__(self, username: str, is_forced: bool = False, parent=None):
        super().__init__(parent)
        self.username = username
        self.is_forced = is_forced
        self.auth = AuthManager()
        self._init_ui()

    def _init_ui(self):
        title_text = "首次登录，请修改密码" if self.is_forced else "修改密码"
        self.setWindowTitle(title_text)
        self.setFixedSize(380, 340 if self.is_forced else 320)
        self.setModal(True)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {AKO_COLORS["main_bg"]};
            }}
            QLabel#title {{
                font-size: 16px;
                font-weight: bold;
                color: {AKO_COLORS["text"]};
            }}
            QLabel#hint {{
                font-size: 11px;
                color: {AKO_COLORS["disabled_text"]};
            }}
            QLabel#errorLabel {{
                color: {AKO_COLORS["danger"]};
                font-size: 11px;
            }}
            QLabel#successLabel {{
                color: {AKO_COLORS["success"]};
                font-size: 11px;
            }}
            QLineEdit {{
                background-color: {AKO_COLORS["white"]};
                border: 1px solid {AKO_COLORS["light_border"]};
                border-radius: 3px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {AKO_COLORS["accent"]};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 20, 32, 20)
        layout.setSpacing(10)

        title = QLabel(title_text)
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        if self.is_forced:
            hint = QLabel("密码要求：至少8位，包含字母和数字")
            hint.setObjectName("hint")
            hint.setAlignment(Qt.AlignCenter)
            hint.setWordWrap(True)
            layout.addWidget(hint)

        layout.addSpacing(8)

        # 当前密码（非强制修改时显示）
        if not self.is_forced:
            old_label = QLabel("当前密码")
            old_label.setStyleSheet(f"font-weight: bold;")
            layout.addWidget(old_label)
            self.old_password = QLineEdit()
            self.old_password.setEchoMode(QLineEdit.Password)
            self.old_password.setPlaceholderText("输入当前密码")
            self.old_password.setMinimumHeight(36)
            layout.addWidget(self.old_password)

        # 新密码
        new_label = QLabel("新密码")
        new_label.setStyleSheet(f"font-weight: bold;")
        layout.addWidget(new_label)
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.Password)
        self.new_password.setPlaceholderText("输入新密码")
        self.new_password.setMinimumHeight(36)
        layout.addWidget(self.new_password)

        # 确认密码
        confirm_label = QLabel("确认新密码")
        confirm_label.setStyleSheet(f"font-weight: bold;")
        layout.addWidget(confirm_label)
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.Password)
        self.confirm_password.setPlaceholderText("再次输入新密码")
        self.confirm_password.setMinimumHeight(36)
        self.confirm_password.returnPressed.connect(self._on_confirm)
        layout.addWidget(self.confirm_password)

        # 错误/成功提示
        self.msg_label = QLabel("")
        self.msg_label.setObjectName("errorLabel")
        self.msg_label.setAlignment(Qt.AlignCenter)
        self.msg_label.setWordWrap(True)
        layout.addWidget(self.msg_label)

        layout.addSpacing(4)

        # 按钮
        btn_layout = QHBoxLayout()

        confirm_btn = QPushButton("确认修改")
        confirm_btn.setMinimumHeight(38)
        confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AKO_COLORS["accent"]};
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {AKO_COLORS["hover_accent"]};
            }}
        """)
        confirm_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(confirm_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.setMinimumHeight(38)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def _on_confirm(self):
        """确认修改密码"""
        new_pwd = self.new_password.text()
        confirm_pwd = self.confirm_password.text()

        if not new_pwd:
            self._show_error("请输入新密码")
            return

        if new_pwd != confirm_pwd:
            self._show_error("两次输入的密码不一致")
            return

        old_pwd = ""
        if not self.is_forced:
            old_pwd = self.old_password.text()
            if not old_pwd:
                self._show_error("请输入当前密码")
                return

        success, msg = self.auth.change_password(
            self.username, old_pwd, new_pwd,
            skip_old_check=self.is_forced
        )

        if success:
            self.msg_label.setObjectName("successLabel")
            self.msg_label.setStyleSheet(f"color: {AKO_COLORS['success']};")
            self.msg_label.setText("密码修改成功！")
            # Delay accept
            from PySide6.QtCore import QTimer
            QTimer.singleShot(800, self.accept)
        else:
            self._show_error(msg)

    def _show_error(self, msg):
        self.msg_label.setObjectName("errorLabel")
        self.msg_label.setStyleSheet(f"color: {AKO_COLORS['danger']};")
        self.msg_label.setText(msg)