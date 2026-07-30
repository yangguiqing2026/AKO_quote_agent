"""
main_window.py - AKO_quote_agent 主窗口
左侧导航栏（报价/历史/设置）+ 右侧内容区，品牌奶油金主题。
"""
import os

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QStackedWidget, QStatusBar,
    QPushButton, QMenu, QMessageBox,
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QAction, QFont, QIcon, QPixmap

from qfluentwidgets import (
    InfoBar, InfoBarPosition, PushButton,
    StrongBodyLabel, SubtitleLabel, FluentIcon,
)

try:
    from .ako_style import AKO_COLORS, AKO_FONTS, GLOBAL_STYLESHEET
except ImportError:
    from ako_style import AKO_COLORS, AKO_FONTS, GLOBAL_STYLESHEET

try:
    from .quote_page import QuotePage
except ImportError:
    from quote_page import QuotePage

try:
    from .history_page import HistoryPage
except ImportError:
    from history_page import HistoryPage

try:
    from .settings_page import SettingsPage
except ImportError:
    from settings_page import SettingsPage


class NavButton(QPushButton):
    """自定义导航按钮 - 深棕黑背景 + 奶油金文字"""

    def __init__(self, icon_text, text, parent=None):
        super().__init__(parent)
        self.icon_text = icon_text
        self.label_text = text
        self._is_active = False
        self._init_style()

    def _init_style(self):
        self.setText(f"  {self.icon_text}  {self.label_text}")
        self.setMinimumHeight(48)
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.setFont(QFont("Microsoft YaHei", 13))
        self._update_style()

    def _update_style(self):
        if self._is_active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {AKO_COLORS['accent']};
                    color: {AKO_COLORS['white']};
                    font-size: 13px;
                    font-weight: bold;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 16px;
                    text-align: left;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {AKO_COLORS['nav_text']};
                    font-size: 13px;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 16px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: {AKO_COLORS['nav_hover']};
                    color: {AKO_COLORS['white']};
                }}
            """)

    def set_active(self, active):
        self._is_active = active
        self._update_style()


class AKOMainWindow(QMainWindow):
    """AKO_quote_agent 主窗口 - 左侧导航 + 右侧内容区"""

    def __init__(self, user: dict = None):
        super().__init__()
        self.current_user = user or {}
        self._nav_buttons = []

        self._init_ui()
        self._init_nav()
        self._init_pages()
        self._init_statusbar()
        self._init_menu()

        # 默认显示报价页
        self._switch_to_page(0)

    def _init_ui(self):
        """初始化主窗口框架"""
        self.setWindowTitle("AKO_quote_agent - 智能报价系统")
        self.resize(1280, 860)
        self.setMinimumSize(1024, 680)

        # 居中
        screen = self.screen().availableGeometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2,
        )

        # 全局样式
        self.setStyleSheet(GLOBAL_STYLESHEET)

        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        self.central_layout = QHBoxLayout(central)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.setSpacing(0)

    def _init_nav(self):
        """初始化左侧导航栏"""
        # 导航栏容器
        self.nav_frame = QFrame()
        self.nav_frame.setFixedWidth(200)
        self.nav_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {AKO_COLORS['nav_bg']};
                border-right: 2px solid {AKO_COLORS['light_border']};
                border-radius: 0;
            }}
        """)

        nav_layout = QVBoxLayout(self.nav_frame)
        nav_layout.setContentsMargins(10, 16, 10, 16)
        nav_layout.setSpacing(6)

        # Logo 区域 - 使用 Logo.ico，圆角样式同按钮
        logo_label = QLabel()
        # 查找图标路径
        icon_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Logo.ico"),
en'ji            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Logo.ico"),
            "Logo.ico",
        ]
        for p in icon_paths:
            if os.path.exists(p):
                pixmap = QPixmap(p).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                logo_label.setPixmap(pixmap)
                break
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setFixedSize(80, 80)
        logo_label.setStyleSheet(f"""
            QLabel {{
                background-color: {AKO_COLORS['accent']};
                border-radius: 12px;
                padding: 6px;
                border: none;
            }}
        """)
        nav_layout.addWidget(logo_label, 0, Qt.AlignCenter)

        brand_label = QLabel("AKO 报价系统")
        brand_label.setAlignment(Qt.AlignCenter)
        brand_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: bold;
                color: {AKO_COLORS['nav_text']};
                background-color: transparent;
                border: none;
                padding-bottom: 8px;
            }}
        """)
        nav_layout.addWidget(brand_label)

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"""
            QFrame {{
                background-color: {AKO_COLORS['accent']};
                max-height: 1px;
                margin: 4px 8px;
            }}
        """)
        nav_layout.addWidget(sep)

        nav_layout.addSpacing(4)

        # 导航按钮
        nav_items = [
            ("📋", "报价"),
            ("📜", "历史",),
            ("⚙️", "设置"),
        ]

        self.btn_group = []  # 手工管理互斥
        for i, (icon, text) in enumerate(nav_items):
            btn = NavButton(icon, text)
            btn.clicked.connect(lambda checked, idx=i: self._switch_to_page(idx))
            nav_layout.addWidget(btn)
            self._nav_buttons.append(btn)
            self.btn_group.append(btn)

        nav_layout.addStretch()

        # 底部用户信息和退出
        user_frame = QFrame()
        user_frame.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border: none;
                border-top: 1px solid {AKO_COLORS['accent']};
                padding-top: 8px;
            }}
        """)
        user_layout = QVBoxLayout(user_frame)
        user_layout.setContentsMargins(8, 6, 8, 2)
        user_layout.setSpacing(4)

        username = self.current_user.get("username", "用户")
        user_info = QLabel(f"👤 {username}")
        user_info.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                color: {AKO_COLORS['nav_text']};
                background-color: transparent;
                border: none;
            }}
        """)
        user_layout.addWidget(user_info)

        logout_btn = QPushButton("🚪 退出登录")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setMinimumHeight(32)
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {AKO_COLORS['nav_text']};
                font-size: 11px;
                border: 1px solid {AKO_COLORS['accent']};
                border-radius: 5px;
                padding: 4px 10px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {AKO_COLORS['danger']};
                color: white;
                border-color: transparent;
            }}
        """)
        logout_btn.clicked.connect(self._on_logout)
        user_layout.addWidget(logout_btn)

        nav_layout.addWidget(user_frame)

        self.central_layout.addWidget(self.nav_frame)

    def _switch_to_page(self, idx):
        """切换页面"""
        self.stacked.setCurrentIndex(idx)

        # 更新导航按钮状态
        for i, btn in enumerate(self._nav_buttons):
            btn.set_active(i == idx)

    def _init_pages(self):
        """初始化右侧内容区 + 三个页面"""
        # 右侧内容区
        content_frame = QFrame()
        content_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {AKO_COLORS['main_bg']};
                border: none;
            }}
        """)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 顶部标题栏
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(52)
        self.title_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {AKO_COLORS['nav_bg']};
                border-bottom: 2px solid {AKO_COLORS['accent']};
            }}
        """)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(20, 0, 20, 0)

        self.page_title_label = StrongBodyLabel("📋 报价")
        self.page_title_label.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {AKO_COLORS['nav_text']}; border: none;"
        )
        title_layout.addWidget(self.page_title_label)
        title_layout.addStretch()

        content_layout.addWidget(self.title_bar)

        # 栈式页面
        self.stacked = QStackedWidget()
        self.stacked.setStyleSheet(
            f"background-color: {AKO_COLORS['main_bg']}; border: none;"
        )

        # 创建三个页面
        self.quote_page = QuotePage()
        self.history_page = HistoryPage()
        self.settings_page = SettingsPage(self.current_user)

        self.stacked.addWidget(self.quote_page)    # index 0
        self.stacked.addWidget(self.history_page)   # index 1
        self.stacked.addWidget(self.settings_page)  # index 2

        # 页面切换时更新标题
        self.stacked.currentChanged.connect(self._on_page_changed)

        content_layout.addWidget(self.stacked, 1)

        self.central_layout.addWidget(content_frame, 1)

        # 报价计算完成后自动添加到历史记录
        self._bridge_quote_to_history()

    def _on_page_changed(self, idx):
        """页面变化时更新顶部标题"""
        titles = ["📋 报价", "📜 历史", "⚙️ 设置"]
        if 0 <= idx < len(titles):
            self.page_title_label.setText(titles[idx])

        # 切换到历史页时刷新
        if idx == 1:
            self.history_page.refresh()

    def _init_statusbar(self):
        """初始化底部状态栏"""
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {AKO_COLORS['panel_bg']};
                color: {AKO_COLORS['text']};
                border-top: 1px solid {AKO_COLORS['light_border']};
                padding: 4px 12px;
                font-size: 11px;
            }}
        """)
        self.setStatusBar(self.status_bar)

        self.sb_user = QLabel(
            f"用户: {self.current_user.get('username', '---')}"
        )
        self.sb_version = QLabel("AKO_quote_agent v1.1.0")
        self.sb_version.setStyleSheet(
            f"color: {AKO_COLORS['disabled_text']};"
        )

        self.status_bar.addWidget(self.sb_user)
        self.status_bar.addPermanentWidget(self.sb_version)

    def _init_menu(self):
        """初始化系统菜单"""
        menu_bar = self.menuBar()
        menu_bar.setStyleSheet(f"""
            QMenuBar {{
                background-color: {AKO_COLORS['panel_bg']};
                color: {AKO_COLORS['text']};
                border-bottom: 1px solid {AKO_COLORS['light_border']};
                padding: 2px;
            }}
            QMenuBar::item:selected {{
                background-color: {AKO_COLORS['accent']};
                color: {AKO_COLORS['white']};
                border-radius: 3px;
            }}
        """)

        # 系统菜单
        system_menu = menu_bar.addMenu("系统")
        system_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {AKO_COLORS['panel_bg']};
                border: 1px solid {AKO_COLORS['light_border']};
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {AKO_COLORS['accent']};
                color: {AKO_COLORS['white']};
            }}
        """)

        # 修改密码
        change_pwd = QAction("修改密码", self)
        change_pwd.triggered.connect(self._on_change_password)
        system_menu.addAction(change_pwd)

        # 用户管理（admin 专属）
        if self.current_user.get("role") == "admin":
            system_menu.addSeparator()
            user_mgmt = QAction("用户管理", self)
            user_mgmt.triggered.connect(self._on_user_management)
            system_menu.addAction(user_mgmt)

        system_menu.addSeparator()
        logout_action = QAction("退出登录", self)
        logout_action.triggered.connect(self._on_logout)
        system_menu.addAction(logout_action)

        # 帮助菜单
        help_menu = menu_bar.addMenu("帮助")
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _on_change_password(self):
        """修改密码"""
        try:
            from .change_password_dialog import ChangePasswordDialog
        except ImportError:
            from change_password_dialog import ChangePasswordDialog
        dialog = ChangePasswordDialog(
            self.current_user.get("username", ""),
            is_forced=False,
            parent=self,
        )
        dialog.exec()

    def _on_user_management(self):
        """用户管理"""
        try:
            from .user_management_dialog import UserManagementDialog
        except ImportError:
            from user_management_dialog import UserManagementDialog
        dialog = UserManagementDialog(self.current_user, parent=self)
        dialog.exec()

    def _on_logout(self):
        """退出登录"""
        reply = QMessageBox.question(
            self,
            "确认退出",
            "确定要退出登录吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                from .auth_manager import AuthManager
            except ImportError:
                from auth_manager import AuthManager
            auth = AuthManager()
            auth.clear_local_token()
            self.close()

    def _on_about(self):
        """关于对话框"""
        QMessageBox.about(
            self,
            "关于 AKO_quote_agent",
            "<h3>AKO_quote_agent v1.1.0</h3>"
            "<p>装配式建筑智能报价系统</p>"
            "<p>基于阿格陶粒墙成本体系计算</p>"
            "<p>定价标准: T/CECS 10154-2021</p>"
            "<br>"
            "<p>© AKO Studio 2025</p>",
        )

    def _bridge_quote_to_history(self):
        """桥接报价页计算结果到历史记录"""
        # 连接报价页 QuoteWorker 的 result_ready 信号
        # 当新的 QuoteWorker 被创建时，我们需要 hook 它
        # 通过替换 quote_page 的 _on_result 方法来实现拦截
        original_on_result = self.quote_page._on_result

        def hooked_on_result(result):
            original_on_result(result)
            if result and "total" in result:
                self.add_quote_to_history(result)
                self.status_bar.showMessage(
                    f"报价已保存到历史: {result.get('project_name', '')} "
                    f"¥{result.get('total', 0):,.2f}",
                    5000,
                )

        self.quote_page._on_result = hooked_on_result

    def add_quote_to_history(self, quote_data):
        """将报价结果添加到历史记录"""
        self.history_page.add_record(quote_data)

    def closeEvent(self, event):
        """关闭窗口时确保退出"""
        event.accept()