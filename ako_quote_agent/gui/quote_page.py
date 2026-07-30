AKO"""
quote_page.py - 报价计算页
输入项目名称、墙板类型、面积等参数，点击计算按钮调用 quote_engine。
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QDoubleSpinBox,
    QSpinBox, QGroupBox, QScrollArea, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView,
    QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from qfluentwidgets import (
    PushButton, PrimaryPushButton, ComboBox, LineEdit,
    DoubleSpinBox, SpinBox, InfoBar, InfoBarPosition,
    StateToolTip, CardWidget, BodyLabel, StrongBodyLabel,
    TableWidget,
)

try:
    from .ako_style import AKO_COLORS, AKO_FONTS
except ImportError:
    from ako_style import AKO_COLORS, AKO_FONTS

try:
    from ..quote_engine import calculate_quote
except ImportError:
    try:
        from quote_engine import calculate_quote
    except ImportError:
        # fallback
        def calculate_quote(data):
            return {"total": 0, "error": "quote_engine not available"}


class QuoteWorker(QThread):
    """后台报价计算线程，避免阻塞 UI"""
    result_ready = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, form_data):
        super().__init__()
        self.form_data = form_data

    def run(self):
        try:
            result = calculate_quote(self.form_data)
            self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))


class QuotePage(QWidget):
    """报价计算页面 - 品牌奶油金主题"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.calculation_worker = None
        self._init_ui()

    def _init_ui(self):
        # 主布局：上方输入区 + 下方结果表格
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 8)
        main_layout.setSpacing(8)

        # ── 输入卡片（紧凑、不滚动，完整显示所有选项） ──
        input_card = QFrame()
        input_card.setObjectName("inputCard")
        input_card.setMinimumHeight(270)
        input_card.setMaximumHeight(300)
        input_card.setStyleSheet(f"""
            QFrame#inputCard {{
                background-color: {AKO_COLORS['card_bg']};
                border: 2px solid {AKO_COLORS['light_border']};
                border-radius: 10px;
            }}
        """)
        card_layout = QVBoxLayout(input_card)
        card_layout.setContentsMargins(16, 10, 16, 8)
        card_layout.setSpacing(6)

        # 表单网格
        form_grid = QGridLayout()
        form_grid.setSpacing(12)
        form_grid.setColumnStretch(1, 1)
        form_grid.setColumnStretch(3, 1)

        # 行 0: 项目名称
        lbl_project = QLabel("项目名称 *")
        lbl_project.setStyleSheet(
            f"font-weight: bold; color: {AKO_COLORS['text']}; font-size: 13px;"
        )
        form_grid.addWidget(lbl_project, 0, 0)
        self.input_project_name = QLineEdit()
        self.input_project_name.setPlaceholderText("请输入项目名称")
        self.input_project_name.setMinimumHeight(36)
        self.input_project_name.setStyleSheet(self._input_style())
        form_grid.addWidget(self.input_project_name, 0, 1)

        # 墙板类型
        lbl_wall = QLabel("墙板类型 *")
        lbl_wall.setStyleSheet(
            f"font-weight: bold; color: {AKO_COLORS['text']}; font-size: 13px;"
        )
        form_grid.addWidget(lbl_wall, 0, 2)
        self.combo_wall_type = QComboBox()
        self.combo_wall_type.addItems(["外墙", "内墙", "隔墙"])
        self.combo_wall_type.setMinimumHeight(36)
        self.combo_wall_type.setStyleSheet(self._combo_style())
        form_grid.addWidget(self.combo_wall_type, 0, 3)

        # 行 1: 面积
        lbl_area = QLabel("面积 (㎡) *")
        lbl_area.setStyleSheet(
            f"font-weight: bold; color: {AKO_COLORS['text']}; font-size: 13px;"
        )
        form_grid.addWidget(lbl_area, 1, 0)
        self.spin_area = QDoubleSpinBox()
        self.spin_area.setRange(10, 999999)
        self.spin_area.setDecimals(2)
        self.spin_area.setValue(100)
        self.spin_area.setSuffix(" ㎡")
        self.spin_area.setMinimumHeight(36)
        self.spin_area.setStyleSheet(self._spin_style())
        form_grid.addWidget(self.spin_area, 1, 1)

        # 厚度
        lbl_thickness = QLabel("厚度 (mm)")
        lbl_thickness.setStyleSheet(
            f"font-weight: bold; color: {AKO_COLORS['text']}; font-size: 13px;"
        )
        form_grid.addWidget(lbl_thickness, 1, 2)
        self.combo_thickness = QComboBox()
        self.combo_thickness.addItems(["100", "120", "150", "200", "250"])
        self.combo_thickness.setCurrentIndex(2)  # 默认 150
        self.combo_thickness.setMinimumHeight(36)
        self.combo_thickness.setStyleSheet(self._combo_style())
        form_grid.addWidget(self.combo_thickness, 1, 3)

        # 行 2: 运输距离
        lbl_transport = QLabel("运输距离 (km)")
        lbl_transport.setStyleSheet(
            f"font-weight: bold; color: {AKO_COLORS['text']}; font-size: 13px;"
        )
        form_grid.addWidget(lbl_transport, 2, 0)
        self.spin_distance = QDoubleSpinBox()
        self.spin_distance.setRange(0, 9999)
        self.spin_distance.setDecimals(1)
        self.spin_distance.setValue(50)
        self.spin_distance.setSuffix(" km")
        self.spin_distance.setMinimumHeight(36)
        self.spin_distance.setStyleSheet(self._spin_style())
        form_grid.addWidget(self.spin_distance, 2, 1)

        # 钢材用量
        lbl_steel = QLabel("钢材用量 (kg/㎡)")
        lbl_steel.setStyleSheet(
            f"font-weight: bold; color: {AKO_COLORS['text']}; font-size: 13px;"
        )
        form_grid.addWidget(lbl_steel, 2, 2)
        self.spin_steel = QDoubleSpinBox()
        self.spin_steel.setRange(0, 999)
        self.spin_steel.setDecimals(2)
        self.spin_steel.setValue(14.0)
        self.spin_steel.setSuffix(" kg/㎡")
        self.spin_steel.setMinimumHeight(36)
        self.spin_steel.setStyleSheet(self._spin_style())
        self.spin_steel.setToolTip("外墙默认14 kg/㎡，内墙默认0.75 kg/㎡")
        form_grid.addWidget(self.spin_steel, 2, 3)

        # 行 3: 联系人
        lbl_contact = QLabel("联系人")
        lbl_contact.setStyleSheet(
            f"font-weight: bold; color: {AKO_COLORS['text']}; font-size: 13px;"
        )
        form_grid.addWidget(lbl_contact, 3, 0)
        self.input_contact = QLineEdit()
        self.input_contact.setPlaceholderText("客户联系人")
        self.input_contact.setMinimumHeight(36)
        self.input_contact.setStyleSheet(self._input_style())
        form_grid.addWidget(self.input_contact, 3, 1)

        # 联系电话
        lbl_phone = QLabel("联系电话")
        lbl_phone.setStyleSheet(
            f"font-weight: bold; color: {AKO_COLORS['text']}; font-size: 13px;"
        )
        form_grid.addWidget(lbl_phone, 3, 2)
        self.input_phone = QLineEdit()
        self.input_phone.setPlaceholderText("客户联系电话")
        self.input_phone.setMinimumHeight(36)
        self.input_phone.setStyleSheet(self._input_style())
        form_grid.addWidget(self.input_phone, 3, 3)

        # 行 4: 箱体类型
        lbl_box = QLabel("箱体类型")
        lbl_box.setStyleSheet(
            f"font-weight: bold; color: {AKO_COLORS['text']}; font-size: 13px;"
        )
        form_grid.addWidget(lbl_box, 4, 0)
        self.combo_box_type = QComboBox()
        self.combo_box_type.addItems(["无", "标准箱体"])
        self.combo_box_type.setMinimumHeight(36)
        self.combo_box_type.setStyleSheet(self._combo_style())
        form_grid.addWidget(self.combo_box_type, 4, 1)

        card_layout.addLayout(form_grid)

        # 墙板类型变化时自动调整钢材默认值
        self.combo_wall_type.currentTextChanged.connect(self._on_wall_type_changed)

        main_layout.addWidget(input_card)
        main_layout.addSpacing(12)

        # ── 计算按钮（放在卡片下方，分隔线之前） ──
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(4, 4, 4, 0)
        btn_layout.addStretch()

        self.btn_calculate = PushButton("计  算")
        self.btn_calculate.setMinimumSize(160, 44)
        self.btn_calculate.setCursor(Qt.PointingHandCursor)
        self.btn_calculate.setStyleSheet(f"""
            QPushButton {{
                background-color: {AKO_COLORS["accent"]};
                color: {AKO_COLORS["white"]};
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 10px 30px;
            }}
            QPushButton:hover {{
                background-color: {AKO_COLORS["hover_accent"]};
            }}
            QPushButton:pressed {{
                background-color: #8A7850;
            }}
            QPushButton:disabled {{
                background-color: {AKO_COLORS["disabled_text"]};
            }}
        """)
        self.btn_calculate.clicked.connect(self._on_calculate)
        btn_layout.addWidget(self.btn_calculate)

        btn_clear = PushButton("清 空")
        btn_clear.setMinimumSize(120, 44)
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.setStyleSheet(f"""
            QPushButton {{
                background-color: {AKO_COLORS["panel_bg"]};
                color: {AKO_COLORS["text"]};
                font-size: 14px;
                border: 1px solid {AKO_COLORS["light_border"]};
                border-radius: 8px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: {AKO_COLORS["accent"]};
                color: {AKO_COLORS["white"]};
            }}
        """)
        btn_clear.clicked.connect(self._on_clear)
        btn_layout.addWidget(btn_clear)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        # ── 分隔线 ──
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(
            f"background-color: {AKO_COLORS['light_border']}; max-height: 2px;"
        )
        main_layout.addWidget(sep)

        # ── 下半部分：结果表格 ──
        result_label = StrongBodyLabel("📊 报价明细")
        result_label.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {AKO_COLORS['text']};"
        )
        main_layout.addWidget(result_label)

        # 总价卡片
        self.total_frame = QFrame()
        self.total_frame.setObjectName("totalCard")
        self.total_frame.setStyleSheet(f"""
            QFrame#totalCard {{
                background-color: {AKO_COLORS['accent']};
                border-radius: 10px;
                padding: 12px;
            }}
        """)
        total_layout = QHBoxLayout(self.total_frame)
        total_layout.setContentsMargins(16, 10, 16, 10)

        total_text = QLabel("💰 含税总价（含利润 15%）：")
        total_text.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {AKO_COLORS['white']};"
        )
        total_layout.addWidget(total_text)

        self.label_total_price = QLabel("¥ 0.00")
        self.label_total_price.setObjectName("totalPrice")
        self.label_total_price.setStyleSheet(
            f"font-size: 26px; font-weight: bold; color: {AKO_COLORS['white']};"
        )
        total_layout.addWidget(self.label_total_price)
        total_layout.addStretch()
        self.total_frame.setVisible(False)
        main_layout.addWidget(self.total_frame)

        # 汇总信息行
        self.summary_info = QLabel("")
        self.summary_info.setStyleSheet(
            f"font-size: 12px; color: {AKO_COLORS['text']}; padding: 4px 0;"
        )
        self.summary_info.setWordWrap(True)
        self.summary_info.setVisible(False)
        main_layout.addWidget(self.summary_info)

        # 明细表格
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(6)
        self.result_table.setHorizontalHeaderLabels([
            "费用项目", "明细项", "单位", "数量", "单价(元)", "合价(元)"
        ])
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.result_table.setMinimumHeight(300)
        self.result_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {AKO_COLORS['input_bg']};
                border: 1px solid {AKO_COLORS['light_border']};
                border-radius: 8px;
                gridline-color: {AKO_COLORS['light_border']};
                font-size: 12px;
            }}
            QTableWidget::item {{
                padding: 6px 10px;
            }}
            QTableWidget::item:alternate {{
                background-color: {AKO_COLORS['panel_bg']};
            }}
            QHeaderView::section {{
                background-color: {AKO_COLORS['panel_bg']};
                color: {AKO_COLORS['text']};
                font-weight: bold;
                border: 1px solid {AKO_COLORS['light_border']};
                padding: 8px 6px;
            }}
        """)
        main_layout.addWidget(self.result_table, 3)

    def _input_style(self):
        return f"""
            QLineEdit {{
                background-color: {AKO_COLORS['input_bg']};
                border: 1px solid {AKO_COLORS['light_border']};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                color: {AKO_COLORS['text']};
            }}
            QLineEdit:focus {{
                border: 2px solid {AKO_COLORS['accent']};
            }}
        """

    def _combo_style(self):
        return f"""
            QComboBox {{
                background-color: {AKO_COLORS['input_bg']};
                border: 1px solid {AKO_COLORS['light_border']};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                color: {AKO_COLORS['text']};
            }}
            QComboBox:focus {{
                border: 2px solid {AKO_COLORS['accent']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {AKO_COLORS['input_bg']};
                border: 1px solid {AKO_COLORS['light_border']};
                selection-background-color: {AKO_COLORS['accent']};
                selection-color: {AKO_COLORS['white']};
            }}
        """

    def _spin_style(self):
        return f"""
            QDoubleSpinBox {{
                background-color: {AKO_COLORS['input_bg']};
                border: 1px solid {AKO_COLORS['light_border']};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                color: {AKO_COLORS['text']};
            }}
            QDoubleSpinBox:focus {{
                border: 2px solid {AKO_COLORS['accent']};
            }}
        """

    def _on_wall_type_changed(self, wall_type):
        """墙板类型变更时自动设置钢材默认值"""
        defaults = {"外墙": 14.0, "内墙": 0.75, "隔墙": 0.75}
        if wall_type in defaults:
            self.spin_steel.setValue(defaults[wall_type])

    def _on_clear(self):
        """清空输入"""
        self.input_project_name.clear()
        self.combo_wall_type.setCurrentIndex(0)
        self.spin_area.setValue(100)
        self.combo_thickness.setCurrentIndex(2)
        self.spin_distance.setValue(50)
        self.spin_steel.setValue(14.0)
        self.input_contact.clear()
        self.input_phone.clear()
        self.combo_box_type.setCurrentIndex(0)
        self.result_table.setRowCount(0)
        self.total_frame.setVisible(False)
        self.summary_info.setVisible(False)
        self.label_total_price.setText("¥ 0.00")

    def _on_calculate(self):
        """点击计算按钮"""
        # 验证必填项
        project_name = self.input_project_name.text().strip()
        if not project_name:
            self._show_info("请输入项目名称", "warning")
            self.input_project_name.setFocus()
            return

        area = self.spin_area.value()
        if area < 10:
            self._show_info("面积不能低于 10 ㎡", "warning")
            return

        # 构建表单数据
        box_type_val = self.combo_box_type.currentText()
        form_data = {
            "project_name": project_name,
            "area": area,
            "wall_type": self.combo_wall_type.currentText(),
            "thickness": int(self.combo_thickness.currentText()),
            "contact": self.input_contact.text().strip(),
            "phone": self.input_phone.text().strip(),
            "transport_distance": self.spin_distance.value(),
            "steel_kg_per_sqm": self.spin_steel.value(),
            "box_type": "standard" if box_type_val == "标准箱体" else None,
        }

        # 禁用按钮
        self.btn_calculate.setEnabled(False)
        self.btn_calculate.setText("计算中...")

        # 启动后台计算
        self.calculation_worker = QuoteWorker(form_data)
        self.calculation_worker.result_ready.connect(self._on_result)
        self.calculation_worker.error_occurred.connect(self._on_error)
        self.calculation_worker.finished.connect(self._on_finished)
        self.calculation_worker.start()

    def _on_result(self, result):
        """计算结果回调"""
        self._populate_result_table(result)

    def _on_error(self, error_msg):
        """计算错误回调"""
        self._show_info(f"计算失败: {error_msg}", "error")

    def _on_finished(self):
        """计算完成，恢复按钮"""
        self.btn_calculate.setEnabled(True)
        self.btn_calculate.setText("计  算")

    def _populate_result_table(self, result):
        """填充结果表格"""
        self.result_table.setRowCount(0)

        rows = []
        seq = 0

        # ── 项目信息 ──
        seq += 1
        rows.append(("项目信息", "项目名称", "", 1, "",
                     result.get("project_name", "")))
        seq += 1
        rows.append(("项目信息", f"面积 / 厚度",
                     "", 1, "",
                     f"{result.get('area', 0)}㎡ / {result.get('thickness', 0)}mm"))
        seq += 1
        rows.append(("项目信息", f"体积",
                     "m³", 1, "",
                     f"{result.get('volume_m3', 0):.2f}"))

        # ── 钢材成本 ──
        seq += 1
        rows.append(("钢材成本", f"钢材用量",
                     "kg", result.get("steel_kg_per_sqm", 0),
                     f"{result.get('steel_price_per_kg', 0):.2f}",
                     f"{result.get('steel_cost', 0):.2f}"))

        # ── 原材料明细 ──
        material = result.get("material_items", {})
        for item_name, item_cost in material.items():
            seq += 1
            rows.append(("原材料", item_name, "", 1, "", f"{item_cost:.2f}"))
        seq += 1
        rows.append(("原材料", "原材料合计", "", 1, "",
                     f"{result.get('material_subtotal', 0):.2f}"))

        # ── 间接成本明细 ──
        indirect = result.get("indirect_items", {})
        for item_name, item_cost in indirect.items():
            seq += 1
            rows.append(("间接成本", item_name, "", 1, "", f"{item_cost:.2f}"))
        seq += 1
        rows.append(("间接成本", "间接成本合计", "", 1, "",
                     f"{result.get('indirect_subtotal', 0):.2f}"))

        # ── 其他费用 ──
        box_cost = result.get("box_cost", 0)
        if box_cost > 0:
            seq += 1
            rows.append(("其他费用", "箱体费用", "", 1, "", f"{box_cost:.2f}"))
        seq += 1
        rows.append(("其他费用", "运输费",
                     "", 1, "", f"{result.get('transport_cost', 0):.2f}"))
        seq += 1
        rows.append(("其他费用", "安装费",
                     "", 1, "", f"{result.get('installation_cost', 0):.2f}"))

        # ── 汇总 ──
        seq += 1
        rows.append(("汇总", "成本小计（未税未利）", "", 1, "",
                     f"{result.get('cost_subtotal', 0):.2f}"))
        seq += 1
        rows.append(("汇总", f"税金 ({result.get('tax_rate', 0) * 100:.0f}%)",
                     "", 1, "", f"{result.get('tax_amount', 0):.2f}"))
        seq += 1
        rows.append(("汇总", f"合理利润 ({result.get('profit_rate', 0) * 100:.0f}%)",
                     "", 1, "", f"{result.get('profit_amount', 0):.2f}"))

        seq += 1
        rows.append(("汇总 ▶", "含税含利总价",
                     "", 1, "", f"{result.get('total', 0):.2f}"))

        # 填充
        self.result_table.setRowCount(len(rows))
        for i, (cat, item, unit, qty, price, amount) in enumerate(rows):
            # 类别列
            cat_item = QTableWidgetItem(str(cat))
            cat_item.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
            cat_item.setForeground(Qt.gray)
            self.result_table.setItem(i, 0, cat_item)

            # 项目列
            item_cell = QTableWidgetItem(str(item))
            item_cell.setFont(QFont("Microsoft YaHei", 11))
            self.result_table.setItem(i, 1, item_cell)

            # 单位
            unit_cell = QTableWidgetItem(str(unit))
            unit_cell.setTextAlignment(Qt.AlignCenter)
            self.result_table.setItem(i, 2, unit_cell)

            # 数量
            qty_cell = QTableWidgetItem(
                f"{qty:.2f}" if isinstance(qty, (int, float)) and qty != 1 else str(qty)
            )
            qty_cell.setTextAlignment(Qt.AlignCenter)
            self.result_table.setItem(i, 3, qty_cell)

            # 单价
            price_cell = QTableWidgetItem(
                f"{price:.2f}" if isinstance(price, (int, float)) and float(price) != 0 else str(price)
            )
            price_cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.result_table.setItem(i, 4, price_cell)

            # 合价
            amount_cell = QTableWidgetItem(
                f"{amount:.2f}" if isinstance(amount, (int, float)) else str(amount)
            )
            amount_cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if "总价" in str(item):
                amount_cell.setFont(QFont("Consolas", 12, QFont.Bold))
                amount_cell.setForeground(Qt.darkYellow)
            self.result_table.setItem(i, 5, amount_cell)

        # 显示总价
        total = result.get("total", 0)
        self.label_total_price.setText(f"¥ {total:,.2f}")
        self.total_frame.setVisible(True)

        # 显示汇总信息
        summary_text = (
            f"面积: {result.get('area', 0)}㎡ | "
            f"墙板类型: {result.get('wall_type', '')} | "
            f"厚度: {result.get('thickness', 0)}mm | "
            f"体积: {result.get('volume_m3', 0):.2f}m³ | "
            f"运输距离: {result.get('transport_distance', 0)}km | "
            f"定价版本: {result.get('price_book_version', '')}"
        )
        self.summary_info.setText(summary_text)
        self.summary_info.setVisible(True)

    def _show_info(self, message, level="info"):
        """显示提示信息"""
        if level == "error":
            InfoBar.error(
                title="错误",
                content=message,
                parent=self.window(),
                position=InfoBarPosition.TOP,
                duration=3000,
            )
        elif level == "warning":
            InfoBar.warning(
                title="提示",
                content=message,
                parent=self.window(),
                position=InfoBarPosition.TOP,
                duration=2000,
            )
        else:
            InfoBar.success(
                title="成功",
                content=message,
                parent=self.window(),
                position=InfoBarPosition.TOP,
                duration=3000,
            )