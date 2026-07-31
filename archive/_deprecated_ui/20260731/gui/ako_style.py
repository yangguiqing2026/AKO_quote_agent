"""
ako_style.py - AKO 品牌视觉规范 (GUI 级)
所有颜色、字体、样式定义集中管理，适配 qfluentwidgets。

品牌色系：
  奶油金 rgb(235,218,185) → 主背景
  深棕黑 rgb(35,30,28)    → 文字/边框
  琥珀金 rgb(160,140,100)  → 按钮高亮
  冷暖灰 rgb(195,190,180)  → 卡片背景
"""

# ── AKO 品牌色彩系统 ──
AKO_COLORS = {
    "main_bg": "#EBE2B9",        # 奶油金 - 窗口底色、侧边栏底色
    "panel_bg": "#C3BEB4",       # 冷暖灰 - 内容区卡片底色、表格交替行
    "accent": "#A08C64",         # 琥珀金 - 选中项、高亮按钮、当前标签页下划线
    "text": "#231E1C",           # 深棕黑 - 所有文字、图标、边框
    "highlight": "#A08C64",      # 琥珀金 - 总价数字、关键指标
    "danger": "#8B3A3A",         # 深红 - 删除按钮、错误提示
    "success": "#5B7A3A",        # 橄榄绿 - 计算完成、保存成功
    "white": "#FFFDF7",          # 暖白 - 输入框背景
    "light_border": "#231E1C",   # 深棕黑边框
    "hover_accent": "#B89B6E",   # 浅琥珀金悬停
    "disabled_text": "#8A8680",
    "nav_bg": "#231E1C",         # 导航栏深棕黑背景
    "nav_text": "#EBE2B9",       # 导航栏奶油金文字
    "nav_hover": "#A08C64",      # 导航项悬停琥珀金
    "card_bg": "#C3BEB4",        # 卡片背景 (冷暖灰)
    "input_bg": "#FFFDF7",       # 输入框背景 (暖白)
}

# ── 字体配置 ──
FONT_FAMILY = "Microsoft YaHei, SimHei, sans-serif"
MONO_FONT = "Consolas, 'Courier New', monospace"

AKO_FONTS = {
    "window_title": {"family": FONT_FAMILY, "size": 14, "weight": "bold"},
    "tab_title": {"family": FONT_FAMILY, "size": 12, "weight": "medium"},
    "table_content": {"family": FONT_FAMILY, "size": 11, "weight": "normal"},
    "total_price": {"family": MONO_FONT, "size": 18, "weight": "bold"},
    "status_bar": {"family": FONT_FAMILY, "size": 10, "weight": "normal"},
}

# ── 全局 Qt 样式表 (作为 qfluentwidgets 的补充) ──
GLOBAL_STYLESHEET = f"""
QMainWindow {{
    background-color: {AKO_COLORS["main_bg"]};
}}

QWidget {{
    font-family: "{FONT_FAMILY}";
    font-size: 12px;
    color: {AKO_COLORS["text"]};
}}

QMenuBar {{
    background-color: {AKO_COLORS["panel_bg"]};
    color: {AKO_COLORS["text"]};
    border-bottom: 1px solid {AKO_COLORS["light_border"]};
    padding: 2px;
}}

QMenuBar::item:selected {{
    background-color: {AKO_COLORS["accent"]};
    color: {AKO_COLORS["white"]};
}}

QMenu {{
    background-color: {AKO_COLORS["panel_bg"]};
    border: 1px solid {AKO_COLORS["light_border"]};
}}

QMenu::item:selected {{
    background-color: {AKO_COLORS["accent"]};
    color: {AKO_COLORS["white"]};
}}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {{
    background-color: {AKO_COLORS["input_bg"]};
    border: 1px solid {AKO_COLORS["light_border"]};
    border-radius: 4px;
    padding: 6px 10px;
    color: {AKO_COLORS["text"]};
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QTextEdit:focus {{
    border: 2px solid {AKO_COLORS["accent"]};
}}

QTableView {{
    background-color: {AKO_COLORS["input_bg"]};
    border: 1px solid {AKO_COLORS["light_border"]};
    border-radius: 6px;
    gridline-color: {AKO_COLORS["light_border"]};
    selection-background-color: {AKO_COLORS["accent"]};
    selection-color: {AKO_COLORS["white"]};
}}

QTableView::item {{
    padding: 6px 10px;
}}

QTableView::item:alternate {{
    background-color: {AKO_COLORS["panel_bg"]};
}}

QHeaderView::section {{
    background-color: {AKO_COLORS["panel_bg"]};
    color: {AKO_COLORS["text"]};
    border: 1px solid {AKO_COLORS["light_border"]};
    padding: 8px 10px;
    font-weight: bold;
    font-size: 12px;
}}

QGroupBox {{
    background-color: {AKO_COLORS["panel_bg"]};
    border: 1px solid {AKO_COLORS["light_border"]};
    border-radius: 8px;
    margin-top: 16px;
    padding-top: 16px;
    font-weight: bold;
    color: {AKO_COLORS["text"]};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {AKO_COLORS["text"]};
}}

QStatusBar {{
    background-color: {AKO_COLORS["panel_bg"]};
    color: {AKO_COLORS["text"]};
    border-top: 1px solid {AKO_COLORS["light_border"]};
    padding: 4px 10px;
    font-size: 10px;
}}

QProgressBar {{
    background-color: {AKO_COLORS["main_bg"]};
    border: 1px solid {AKO_COLORS["light_border"]};
    border-radius: 4px;
    text-align: center;
    color: {AKO_COLORS["text"]};
}}

QProgressBar::chunk {{
    background-color: {AKO_COLORS["accent"]};
    border-radius: 3px;
}}

QScrollBar:vertical {{
    background-color: {AKO_COLORS["main_bg"]};
    width: 10px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical {{
    background-color: {AKO_COLORS["accent"]};
    border-radius: 5px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {AKO_COLORS["hover_accent"]};
}}

QScrollBar:horizontal {{
    background-color: {AKO_COLORS["main_bg"]};
    height: 10px;
    border-radius: 5px;
}}

QScrollBar::handle:horizontal {{
    background-color: {AKO_COLORS["accent"]};
    border-radius: 5px;
    min-width: 20px;
}}

QLabel#totalPrice {{
    color: {AKO_COLORS["highlight"]};
    font-family: "{MONO_FONT}";
    font-size: 22px;
    font-weight: bold;
}}

QLabel#sectionTitle {{
    color: {AKO_COLORS["text"]};
    font-size: 15px;
    font-weight: bold;
}}

QLabel#errorLabel {{
    color: {AKO_COLORS["danger"]};
    font-size: 11px;
}}

QLabel#successLabel {{
    color: {AKO_COLORS["success"]};
    font-size: 11px;
}}
"""