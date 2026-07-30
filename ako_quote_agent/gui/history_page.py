"""
history_page.py - 报价历史记录页
展示历史报价列表，支持查看详情和删除。
"""
import json
import os
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QFrame,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from qfluentwidgets import (
    PushButton, InfoBar, InfoBarPosition,
    StrongBodyLabel, SubtitleLabel,
)

try:
    from .ako_style import AKO_COLORS
except ImportError:
    from ako_style import AKO_COLORS

# 历史记录文件路径
HISTORY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
HISTORY_FILE = os.path.join(HISTORY_DIR, "quote_history.json")


def _ensure_history_dir():
    """确保历史记录目录存在"""
    os.makedirs(HISTORY_DIR, exist_ok=True)


def save_to_history(quote_data):
    """保存报价记录到历史文件"""
    _ensure_history_dir()
    records = load_history()
    record = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "project_name": quote_data.get("project_name", ""),
        "wall_type": quote_data.get("wall_type", ""),
        "area": quote_data.get("area", 0),
        "thickness": quote_data.get("thickness", 0),
        "total": quote_data.get("total", 0),
        "detail": quote_data,
    }
    records.append(record)
    # 最多保留 500 条
    if len(records) > 500:
        records = records[-500:]
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_history():
    """加载历史记录"""
    _ensure_history_dir()
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def delete_history_record(record_id):
    """删除指定记录"""
    records = load_history()
    records = [r for r in records if r.get("id") != record_id]
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


class HistoryPage(QWidget):
    """报价历史页面"""

    record_selected = Signal(dict)  # 选择某条记录时发射

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_records()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # 标题
        title = StrongBodyLabel("📜 报价历史")
        title.setStyleSheet(
            f"font-size: 20px; font-weight: bold; color: {AKO_COLORS['text']};"
        )
        main_layout.addWidget(title)

        sub = SubtitleLabel("查看之前的报价记录，支持查看详情和删除")
        sub.setStyleSheet(
            f"font-size: 12px; color: {AKO_COLORS['disabled_text']};"
        )
        main_layout.addWidget(sub)

        # 操作按钮行
        btn_layout = QHBoxLayout()

        refresh_btn = PushButton("🔄 刷新")
        refresh_btn.setMinimumHeight(36)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AKO_COLORS['panel_bg']};
                color: {AKO_COLORS['text']};
                font-size: 13px;
                border: 1px solid {AKO_COLORS['light_border']};
                border-radius: 6px;
                padding: 6px 16px;
            }}
            QPushButton:hover {{
                background-color: {AKO_COLORS['accent']};
                color: {AKO_COLORS['white']};
            }}
        """)
        refresh_btn.clicked.connect(self._load_records)
        btn_layout.addWidget(refresh_btn)

        btn_layout.addStretch()

        self.btn_view_detail = PushButton("📋 查看详情")
        self.btn_view_detail.setMinimumHeight(36)
        self.btn_view_detail.setEnabled(False)
        self.btn_view_detail.setStyleSheet(f"""
            QPushButton {{
                background-color: {AKO_COLORS['accent']};
                color: {AKO_COLORS['white']};
                font-size: 13px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
            }}
            QPushButton:hover {{
                background-color: {AKO_COLORS['hover_accent']};
            }}
            QPushButton:disabled {{
                background-color: {AKO_COLORS['disabled_text']};
            }}
        """)
        self.btn_view_detail.clicked.connect(self._on_view_detail)
        btn_layout.addWidget(self.btn_view_detail)

        self.btn_delete = PushButton("🗑️ 删除")
        self.btn_delete.setMinimumHeight(36)
        self.btn_delete.setEnabled(False)
        self.btn_delete.setStyleSheet(f"""
            QPushButton {{
                background-color: {AKO_COLORS['danger']};
                color: white;
                font-size: 13px;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
            }}
            QPushButton:hover {{
                background-color: #A05050;
            }}
            QPushButton:disabled {{
                background-color: {AKO_COLORS['disabled_text']};
            }}
        """)
        self.btn_delete.clicked.connect(self._on_delete)
        btn_layout.addWidget(self.btn_delete)

        main_layout.addLayout(btn_layout)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "序号", "时间", "项目名称", "墙板类型", "面积(㎡)", "厚度(mm)", "总价(元)"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet(f"""
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
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.doubleClicked.connect(self._on_view_detail)
        main_layout.addWidget(self.table, 1)

        # 底部统计
        self.stats_label = QLabel("共 0 条记录")
        self.stats_label.setStyleSheet(
            f"font-size: 12px; color: {AKO_COLORS['disabled_text']};"
        )
        main_layout.addWidget(self.stats_label)

    def _load_records(self):
        """加载历史记录到表格"""
        records = load_history()
        # 倒序显示（最新在前）
        records.reverse()

        self.table.setRowCount(len(records))
        self._records = records

        for i, record in enumerate(records):
            # 序号
            seq_item = QTableWidgetItem(str(i + 1))
            seq_item.setTextAlignment(Qt.AlignCenter)
            seq_item.setData(Qt.UserRole, record.get("id", ""))
            self.table.setItem(i, 0, seq_item)

            # 时间
            time_item = QTableWidgetItem(record.get("time", ""))
            time_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 1, time_item)

            # 项目名称
            name_item = QTableWidgetItem(record.get("project_name", ""))
            self.table.setItem(i, 2, name_item)

            # 墙板类型
            wall_item = QTableWidgetItem(record.get("wall_type", ""))
            wall_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 3, wall_item)

            # 面积
            area_item = QTableWidgetItem(f"{record.get('area', 0):.2f}")
            area_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 4, area_item)

            # 厚度
            thick_item = QTableWidgetItem(str(record.get("thickness", 0)))
            thick_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 5, thick_item)

            # 总价
            total = record.get("total", 0)
            total_item = QTableWidgetItem(f"¥ {total:,.2f}")
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            total_item.setFont(QFont("Consolas", 11, QFont.Bold))
            total_item.setForeground(Qt.darkYellow)
            self.table.setItem(i, 6, total_item)

        self.stats_label.setText(f"共 {len(records)} 条记录")

    def _on_selection_changed(self):
        """选择变化时更新按钮状态"""
        has_selection = self.table.currentRow() >= 0
        self.btn_view_detail.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)

    def _get_selected_record(self):
        """获取当前选中的记录"""
        row = self.table.currentRow()
        if row < 0 or row >= len(self._records):
            return None
        return self._records[row]

    def _on_view_detail(self):
        """查看详情"""
        record = self._get_selected_record()
        if not record:
            return
        self.record_selected.emit(record.get("detail", record))

    def _on_delete(self):
        """删除记录"""
        record = self._get_selected_record()
        if not record:
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除项目「{record.get('project_name', '')}」的报价记录吗？\n"
            f"时间: {record.get('time', '')}\n"
            f"总价: ¥{record.get('total', 0):,.2f}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            record_id = record.get("id", "")
            if delete_history_record(record_id):
                InfoBar.success(
                    title="已删除",
                    content="报价记录已删除",
                    parent=self.window(),
                    position=InfoBarPosition.TOP,
                    duration=2000,
                )
                self._load_records()
            else:
                InfoBar.error(
                    title="错误",
                    content="删除失败",
                    parent=self.window(),
                    position=InfoBarPosition.TOP,
                    duration=2000,
                )

    def add_record(self, quote_data):
        """添加新记录并刷新"""
        save_to_history(quote_data)
        self._load_records()

    def refresh(self):
        """外部刷新"""
        self._load_records()