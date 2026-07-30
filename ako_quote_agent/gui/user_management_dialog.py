"""
user_management_dialog.py - 用户管理窗口（仅管理员可见）
基于账号管理方案 v1.0
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QTableView, QHeaderView, QMessageBox, QAbstractItemView,
)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt, QTimer

try:
    from .ako_style import AKO_COLORS
    from .auth_manager import AuthManager
except ImportError:
    from ako_style import AKO_COLORS
    from auth_manager import AuthManager


class UserManagementDialog(QDialog):
    """用户管理窗口"""

    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.auth = AuthManager()
        self.current_user = current_user
        self._init_ui()
        self._refresh_table()

    def _init_ui(self):
        self.setWindowTitle("用户管理（仅管理员可见）")
        self.resize(750, 500)
        self.setMinimumSize(600, 400)
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
                font-size: 10px;
                color: {AKO_COLORS["disabled_text"]};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # 标题
        title = QLabel("AKO 用户管理")
        title.setObjectName("title")
        layout.addWidget(title)

        hint = QLabel("当前登录: " + self.current_user.get("display_name", ""))
        hint.setObjectName("hint")
        layout.addWidget(hint)

        # 用户表格
        self.user_table = QTableView()
        self.user_model = QStandardItemModel()
        self.user_model.setHorizontalHeaderLabels([
            "序号", "用户名", "显示名", "角色", "状态",
            "最后登录"
        ])
        self.user_table.setModel(self.user_model)
        self.user_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.user_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.user_table.setAlternatingRowColors(True)
        self.user_table.horizontalHeader().setStretchLastSection(True)
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.user_table, 1)

        # 操作按钮
        btn_layout = QHBoxLayout()

        actions = [
            ("添加用户", self._on_add_user, "primaryBtn"),
            ("重置密码", self._on_reset_password, None),
            ("启用/禁用", self._on_toggle_user, None),
            ("删除", self._on_delete_user, "dangerBtn"),
            ("刷新", self._refresh_table, None),
        ]
        for text, handler, obj_name in actions:
            btn = QPushButton(text)
            if obj_name:
                btn.setObjectName(obj_name)
            btn.clicked.connect(handler)
            btn_layout.addWidget(btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _refresh_table(self):
        """刷新用户列表"""
        users = self.auth.get_all_users()
        self.user_model.removeRows(0, self.user_model.rowCount())

        for i, u in enumerate(users):
            status = "✓ 启用" if u["is_active"] else "✕ 禁用"
            last_login = u.get("last_login", "-")
            if last_login:
                last_login = last_login[:16] if len(last_login) > 16 else last_login

            row = [
                QStandardItem(str(i + 1)),
                QStandardItem(u["username"]),
                QStandardItem(u["display_name"]),
                QStandardItem(u["role"]),
                QStandardItem(status),
                QStandardItem(last_login),
            ]
            for cell in row:
                cell.setTextAlignment(Qt.AlignCenter)
            self.user_model.appendRow(row)

    def _get_selected_user(self):
        """获取选中行的用户名"""
        idx = self.user_table.currentIndex()
        if not idx.isValid():
            QMessageBox.warning(self, "提示", "请先选中一个用户")
            return None
        row = idx.row()
        username_item = self.user_model.item(row, 1)
        return username_item.text() if username_item else None

    def _on_add_user(self):
        """添加用户"""
        dialog = AddUserDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self._refresh_table()

    def _on_reset_password(self):
        """重置密码"""
        username = self._get_selected_user()
        if not username:
            return

        reply = QMessageBox.question(
            self, "确认重置",
            f"确定重置用户 {username} 的密码？\n\n"
            "密码将重置为初始密码，该用户下次登录时需强制修改密码。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        success, msg, new_pwd = self.auth.reset_password(username)
        if success:
            QMessageBox.information(
                self, "重置成功",
                f"{msg}\n\n新初始密码: {new_pwd}\n\n请将此密码告知该员工。"
            )
        else:
            QMessageBox.warning(self, "重置失败", msg)
        self._refresh_table()

    def _on_toggle_user(self):
        """启用/禁用"""
        username = self._get_selected_user()
        if not username:
            return
        if username == self.current_user.get("username"):
            QMessageBox.warning(self, "提示", "不可禁用自己")
            return

        success, msg = self.auth.toggle_user(username)
        if success:
            QMessageBox.information(self, "操作成功", msg)
        else:
            QMessageBox.warning(self, "操作失败", msg)
        self._refresh_table()

    def _on_delete_user(self):
        """删除用户"""
        username = self._get_selected_user()
        if not username:
            return
        if username == "admin":
            QMessageBox.warning(self, "提示", "不可删除 admin 账号")
            return
        if username == self.current_user.get("username"):
            QMessageBox.warning(self, "提示", "不可删除自己")
            return

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定删除用户 {username}？此操作不可逆。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        success, msg = self.auth.delete_user(username)
        if success:
            QMessageBox.information(self, "删除成功", msg)
        else:
            QMessageBox.warning(self, "删除失败", msg)
        self._refresh_table()


class AddUserDialog(QDialog):
    """添加用户子窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth = AuthManager()
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("添加新用户")
        self.setFixedSize(350, 280)
        self.setModal(True)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {AKO_COLORS["main_bg"]};
            }}
            QLabel {{
                font-weight: bold;
                color: {AKO_COLORS["text"]};
            }}
            QLineEdit {{
                background-color: {AKO_COLORS["white"]};
                border: 1px solid {AKO_COLORS["light_border"]};
                border-radius: 3px;
                padding: 8px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(8)

        title = QLabel("添加新用户")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 用户名
        layout.addWidget(QLabel("用户名（拼音全小写）:"))
        self.uname_input = QLineEdit()
        self.uname_input.setPlaceholderText("如: luozeguang")
        layout.addWidget(self.uname_input)

        # 显示名
        layout.addWidget(QLabel("显示名（中文姓名）:"))
        self.dname_input = QLineEdit()
        self.dname_input.setPlaceholderText("如: 罗泽广")
        layout.addWidget(self.dname_input)

        # 手机号
        layout.addWidget(QLabel("手机号（用于生成初始密码）:"))
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("如: 13385118522")
        layout.addWidget(self.phone_input)

        # 角色
        layout.addWidget(QLabel("角色:"))
        self.role_combo = QComboBox()
        self.role_combo.addItems(["user", "admin"])
        layout.addWidget(self.role_combo)

        hint = QLabel("初始密码将自动生成: ako + 手机号后4位")
        hint.setStyleSheet(f"color: {AKO_COLORS['disabled_text']}; font-size: 10px;")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

        layout.addSpacing(6)

        btn_layout = QHBoxLayout()
        confirm_btn = QPushButton("确认添加")
        confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AKO_COLORS["accent"]};
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
            }}
            QPushButton:hover {{
                background-color: {AKO_COLORS["hover_accent"]};
            }}
        """)
        confirm_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(confirm_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def _on_add(self):
        username = self.uname_input.text().strip()
        display_name = self.dname_input.text().strip()
        phone = self.phone_input.text().strip()
        role = self.role_combo.currentText()

        if not username or not display_name:
            QMessageBox.warning(self, "提示", "用户名和显示名不能为空")
            return

        success, msg, initial_pwd = self.auth.create_user(
            username, display_name, phone, role
        )

        if success:
            QMessageBox.information(
                self, "添加成功",
                f"{msg}\n\n用户名: {username}\n初始密码: {initial_pwd}\n\n"
                "请将初始密码告知该员工。"
            )
            self.accept()
        else:
            QMessageBox.warning(self, "添加失败", msg)