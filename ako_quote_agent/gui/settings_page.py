"""
settings_page.py - 设置页
系统参数设置、定价配置查看。
"""
import json
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QDoubleSpinBox, QGroupBox,
    QScrollArea, QFrame, QTextEdit, QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from qfluentwidgets import (
    PushButton, PrimaryPushButton, InfoBar, InfoBarPosition,
    StrongBodyLabel, SubtitleLabel, CardWidget,
)

try:
    from .ako_style import AKO_COLORS
except ImportError:
    from ako_style import AKO_COLORS

# 配置文件路径
CONFIG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRICING_CONFIG = os.path.join(CONFIG_DIR, "pricing_config.json")


def load_pricing_config():
    """加载定价配置"""
    if not os.path.exists(PRICING_CONFIG):
        return {}
    try:
        with open(PRICING_CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_pricing_config(config):
    """保存定价配置"""
    try:
        with open(PRICING_CONFIG, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


class SettingsPage(QWidget):
    """设置页面"""

    config_changed = Signal()  # 配置变更信号

    def __init__(self, user: dict = None, parent=None):
        super().__init__(parent)
        self.current_user = user or {}
        self._init_ui()
        self._load_config()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # 标题
        title = StrongBodyLabel("⚙️ 系统设置")
        title.setStyleSheet(
            f"font-size: 20px; font-weight: bold; color: {AKO_COLORS['text']};"
        )
        main_layout.addWidget(title)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")

        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background-color: transparent;")
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(16)

        # ── 用户信息卡片 ──
        user_card = QFrame()
        user_card.setStyleSheet(f"""
            QFrame {{
                background-color: {AKO_COLORS['card_bg']};
                border: 2px solid {AKO_COLORS['light_border']};
                border-radius: 10px;
                padding: 12px;
            }}
        """)
        user_layout = QVBoxLayout(user_card)
        user_layout.setContentsMargins(16, 12, 16, 12)
        user_layout.setSpacing(6)

        user_title = QLabel("👤 当前用户")
        user_title.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {AKO_COLORS['text']};"
        )
        user_layout.addWidget(user_title)

        username = self.current_user.get("username", "未知")
        role = self.current_user.get("role", "user")
        self.user_info_label = QLabel(f"用户名: {username}    角色: {role}")
        self.user_info_label.setStyleSheet(
            f"font-size: 12px; color: {AKO_COLORS['text']};"
        )
        user_layout.addWidget(self.user_info_label)

        # 修改密码按钮
        change_pwd_btn = PushButton("修改密码")
        change_pwd_btn.setMinimumHeight(34)
        change_pwd_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AKO_COLORS['accent']};
                color: {AKO_COLORS['white']};
                font-size: 12px;
                border: none;
                border-radius: 5px;
                padding: 6px 16px;
            }}
            QPushButton:hover {{
                background-color: {AKO_COLORS['hover_accent']};
            }}
        """)
        change_pwd_btn.clicked.connect(self._on_change_password)
        user_layout.addWidget(change_pwd_btn)

        scroll_layout.addWidget(user_card)

        # ── 定价配置卡片 ──
        pricing_card = QFrame()
        pricing_card.setStyleSheet(f"""
            QFrame {{
                background-color: {AKO_COLORS['card_bg']};
                border: 2px solid {AKO_COLORS['light_border']};
                border-radius: 10px;
                padding: 12px;
            }}
        """)
        pricing_layout = QVBoxLayout(pricing_card)
        pricing_layout.setContentsMargins(16, 12, 16, 12)
        pricing_layout.setSpacing(10)

        pricing_title = QLabel("💲 定价参数")
        pricing_title.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {AKO_COLORS['text']};"
        )
        pricing_layout.addWidget(pricing_title)

        form_grid = QGridLayout()
        form_grid.setSpacing(10)

        # 钢材基准价
        form_grid.addWidget(
            QLabel("钢材基准价 (元/kg):"),
            0, 0
        )
        self.spin_steel_price = QDoubleSpinBox()
        self.spin_steel_price.setRange(0, 9999)
        self.spin_steel_price.setDecimals(2)
        self.spin_steel_price.setValue(4.0)
        self.spin_steel_price.setMinimumHeight(32)
        self.spin_steel_price.setStyleSheet(self._spin_style())
        form_grid.addWidget(self.spin_steel_price, 0, 1)

        # 运输费率
        form_grid.addWidget(
            QLabel("运输费率 (元/km):"),
            0, 2
        )
        self.spin_transport_rate = QDoubleSpinBox()
        self.spin_transport_rate.setRange(0, 9999)
        self.spin_transport_rate.setDecimals(2)
        self.spin_transport_rate.setValue(15.0)
        self.spin_transport_rate.setMinimumHeight(32)
        self.spin_transport_rate.setStyleSheet(self._spin_style())
        form_grid.addWidget(self.spin_transport_rate, 0, 3)

        # 安装费率
        form_grid.addWidget(
            QLabel("安装费率 (元/㎡):"),
            1, 0
        )
        self.spin_install_rate = QDoubleSpinBox()
        self.spin_install_rate.setRange(0, 9999)
        self.spin_install_rate.setDecimals(2)
        self.spin_install_rate.setValue(80.0)
        self.spin_install_rate.setMinimumHeight(32)
        self.spin_install_rate.setStyleSheet(self._spin_style())
        form_grid.addWidget(self.spin_install_rate, 1, 1)

        # 默认运输距离
        form_grid.addWidget(
            QLabel("默认运输距离 (km):"),
            1, 2
        )
        self.spin_default_distance = QDoubleSpinBox()
        self.spin_default_distance.setRange(0, 9999)
        self.spin_default_distance.setDecimals(1)
        self.spin_default_distance.setValue(50)
        self.spin_default_distance.setMinimumHeight(32)
        self.spin_default_distance.setStyleSheet(self._spin_style())
        form_grid.addWidget(self.spin_default_distance, 1, 3)

        # 最低起订面积
        form_grid.addWidget(
            QLabel("最低起订面积 (㎡):"),
            2, 0
        )
        self.spin_min_area = QDoubleSpinBox()
        self.spin_min_area.setRange(0, 9999)
        self.spin_min_area.setDecimals(1)
        self.spin_min_area.setValue(10)
        self.spin_min_area.setMinimumHeight(32)
        self.spin_min_area.setStyleSheet(self._spin_style())
        form_grid.addWidget(self.spin_min_area, 2, 1)

        # 税率
        form_grid.addWidget(
            QLabel("税率:"),
            2, 2
        )
        self.spin_tax_rate = QDoubleSpinBox()
        self.spin_tax_rate.setRange(0, 0.5)
        self.spin_tax_rate.setDecimals(3)
        self.spin_tax_rate.setSingleStep(0.01)
        self.spin_tax_rate.setValue(0.09)
        self.spin_tax_rate.setMinimumHeight(32)
        self.spin_tax_rate.setStyleSheet(self._spin_style())
        form_grid.addWidget(self.spin_tax_rate, 2, 3)

        # 标准箱体基础价
        form_grid.addWidget(
            QLabel("标准箱体基础价 (元):"),
            3, 0
        )
        self.spin_box_base = QDoubleSpinBox()
        self.spin_box_base.setRange(0, 999999)
        self.spin_box_base.setDecimals(2)
        self.spin_box_base.setValue(15000)
        self.spin_box_base.setMinimumHeight(32)
        self.spin_box_base.setStyleSheet(self._spin_style())
        form_grid.addWidget(self.spin_box_base, 3, 1)

        # 箱体面积单价
        form_grid.addWidget(
            QLabel("箱体面积单价 (元/㎡):"),
            3, 2
        )
        self.spin_box_area_price = QDoubleSpinBox()
        self.spin_box_area_price.setRange(0, 99999)
        self.spin_box_area_price.setDecimals(2)
        self.spin_box_area_price.setValue(350)
        self.spin_box_area_price.setMinimumHeight(32)
        self.spin_box_area_price.setStyleSheet(self._spin_style())
        form_grid.addWidget(self.spin_box_area_price, 3, 3)

        pricing_layout.addLayout(form_grid)

        # 保存按钮
        save_btn_layout = QHBoxLayout()
        save_btn_layout.addStretch()

        save_btn = PrimaryPushButton("💾 保存定价配置")
        save_btn.setMinimumHeight(38)
        save_btn.clicked.connect(self._on_save_config)
        save_btn_layout.addWidget(save_btn)

        reset_btn = PushButton("🔄 恢复默认")
        reset_btn.setMinimumHeight(38)
        reset_btn.clicked.connect(self._on_reset_default)
        save_btn_layout.addWidget(reset_btn)

        save_btn_layout.addStretch()
        pricing_layout.addLayout(save_btn_layout)

        scroll_layout.addWidget(pricing_card)

        # ── 关于信息卡片 ──
        about_card = QFrame()
        about_card.setStyleSheet(f"""
            QFrame {{
                background-color: {AKO_COLORS['card_bg']};
                border: 2px solid {AKO_COLORS['light_border']};
                border-radius: 10px;
                padding: 12px;
            }}
        """)
        about_layout = QVBoxLayout(about_card)
        about_layout.setContentsMargins(16, 12, 16, 12)
        about_layout.setSpacing(6)

        about_title = QLabel("ℹ️ 关于 AKO_quote_agent")
        about_title.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {AKO_COLORS['text']};"
        )
        about_layout.addWidget(about_title)

        about_text = QLabel(
            "AKO_quote_agent v1.1.0\n"
            "装配式建筑智能报价系统\n"
            "基于阿格陶粒墙成本体系计算\n"
            "定价标准: T/CECS 10154-2021\n"
            "© AKO Studio 2025"
        )
        about_text.setStyleSheet(
            f"font-size: 12px; color: {AKO_COLORS['text']}; line-height: 1.6;"
        )
        about_layout.addWidget(about_text)

        scroll_layout.addWidget(about_card)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll, 1)

    def _spin_style(self):
        return f"""
            QDoubleSpinBox {{
                background-color: {AKO_COLORS['input_bg']};
                border: 1px solid {AKO_COLORS['light_border']};
                border-radius: 5px;
                padding: 6px 10px;
                font-size: 12px;
                color: {AKO_COLORS['text']};
            }}
            QDoubleSpinBox:focus {{
                border: 2px solid {AKO_COLORS['accent']};
            }}
        """

    def _load_config(self):
        """加载定价配置到界面"""
        config = load_pricing_config()
        if not config:
            return

        if "steel_price_per_kg" in config:
            self.spin_steel_price.setValue(config["steel_price_per_kg"])
        if "transport_rate_per_km" in config:
            self.spin_transport_rate.setValue(config["transport_rate_per_km"])
        if "installation_rate_per_sqm" in config:
            self.spin_install_rate.setValue(config["installation_rate_per_sqm"])
        if "default_transport_distance_km" in config:
            self.spin_default_distance.setValue(config["default_transport_distance_km"])
        if "min_order_area_sqm" in config:
            self.spin_min_area.setValue(config["min_order_area_sqm"])
        if "tax_rate" in config:
            self.spin_tax_rate.setValue(config["tax_rate"])
        if "standard_box_base_price" in config:
            self.spin_box_base.setValue(config["standard_box_base_price"])
        if "standard_box_area_price" in config:
            self.spin_box_area_price.setValue(config["standard_box_area_price"])

    def _on_save_config(self):
        """保存定价配置"""
        config = {
            "steel_price_per_kg": self.spin_steel_price.value(),
            "transport_rate_per_km": self.spin_transport_rate.value(),
            "installation_rate_per_sqm": self.spin_install_rate.value(),
            "default_transport_distance_km": self.spin_default_distance.value(),
            "min_order_area_sqm": self.spin_min_area.value(),
            "tax_rate": self.spin_tax_rate.value(),
            "standard_box_base_price": self.spin_box_base.value(),
            "standard_box_area_price": self.spin_box_area_price.value(),
        }

        if save_pricing_config(config):
            InfoBar.success(
                title="保存成功",
                content="定价配置已保存，下次计算时生效",
                parent=self.window(),
                position=InfoBarPosition.TOP,
                duration=3000,
            )
            self.config_changed.emit()
        else:
            InfoBar.error(
                title="保存失败",
                content="无法写入配置文件",
                parent=self.window(),
                position=InfoBarPosition.TOP,
                duration=3000,
            )

    def _on_reset_default(self):
        """恢复默认值"""
        reply = QMessageBox.question(
            self,
            "确认恢复",
            "确定要恢复默认定价参数吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.spin_steel_price.setValue(4.0)
            self.spin_transport_rate.setValue(15.0)
            self.spin_install_rate.setValue(80.0)
            self.spin_default_distance.setValue(50.0)
            self.spin_min_area.setValue(10.0)
            self.spin_tax_rate.setValue(0.09)
            self.spin_box_base.setValue(15000.0)
            self.spin_box_area_price.setValue(350.0)
            InfoBar.success(
                title="已恢复",
                content="已恢复默认值（未保存到文件）",
                parent=self.window(),
                position=InfoBarPosition.TOP,
                duration=2000,
            )

    def _on_change_password(self):
        """打开修改密码窗口"""
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