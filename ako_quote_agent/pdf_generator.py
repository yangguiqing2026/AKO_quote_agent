"""
pdf_generator.py - AKO 报价智能体 PDF 生成器
使用 reportlab 生成含中文字体的报价单 PDF。
铁律 #12-#14: 硬编码中文字体路径、fallback、禁止默认字体。
"""

import os
import sys
import json
import platform
from pathlib import Path
from typing import Dict

# 统一命名模块
_SHARED_DIR = Path("D:/AKO_shared")
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))
from naming import generate_filename, get_file_id

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

from logger import get_logger

logger = get_logger("ako_pdf")

# 加载配置
_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
    _config = json.load(f)

# ──────────────────────────────────────────────
# AKO 品牌色系（铁律 #12-#14）
# ──────────────────────────────────────────────
COLOR_CREAM_GOLD = HexColor("#EBDAB9")      # 奶油金 RGB(235,218,185)
COLOR_COOL_GRAY = HexColor("#C3BEB4")       # 冷暖灰 RGB(195,190,180)
COLOR_DARK_BROWN = HexColor("#231E1C")      # 深棕黑 RGB(35,30,28)
COLOR_AMBER_GOLD = HexColor("#A08C64")      # 琥珀金 RGB(160,140,100)
COLOR_MOLTEN_GOLD = HexColor("#B99B5F")     # 熔金 RGB(185,155,95)
COLOR_BG_LIGHT = HexColor("#F5F0E8")        # 浅暖白背景
COLOR_WHITE = HexColor("#FEFCF8")           # 暖白（避免纯白 #FFFFFF 禁忌）

# ──────────────────────────────────────────────
# 中文字体注册（铁律 #12-#14）
# ──────────────────────────────────────────────
FONT_NAME = "AKOChinese"
_font_registered = False


def _register_chinese_font() -> str:
    """
    注册中文字体，硬编码路径。
    Windows: C:/Windows/Fonts/msyh.ttc
    Linux: /usr/share/fonts/truetype/wqy/wqy-zenhei.ttc
    fallback: reportlab 内置 TTFont
    """
    global _font_registered
    if _font_registered:
        return FONT_NAME

    fonts_config = _config["fonts"]
    system = platform.system()

    font_paths = []
    if system == "Windows":
        font_paths.append(fonts_config["windows"])
    elif system == "Linux":
        font_paths.append(fonts_config["linux"])

    # 通用 fallback 路径
    font_paths.extend([
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simsun.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    ])

    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont(FONT_NAME, font_path))
                logger.info(f"中文字体已注册: {font_path}")
                _font_registered = True
                return FONT_NAME
            except Exception as e:
                logger.warning(f"字体注册失败 {font_path}: {e}")
                continue

    # 最终 fallback
    logger.critical("所有中文字体路径均不可用，使用 reportlab 默认（可能乱码）")
    _font_registered = True
    return "Helvetica"


# ──────────────────────────────────────────────
# PDF 生成
# ──────────────────────────────────────────────

def generate_pdf(quote_result: Dict, task_id: str, output_dir: str = None) -> str:
    """
    根据报价结果生成 PDF 报价单。

    Args:
        quote_result: calculate_quote() 返回的报价字典
        task_id: 任务 ID
        output_dir: 输出目录，默认使用 pdf_dir 配置

    Returns:
        生成的 PDF 文件路径
    """
    font_name = _register_chinese_font()

    if output_dir is None:
        output_dir = _config["paths"]["pdf_dir"]
    os.makedirs(output_dir, exist_ok=True)

    # 统一命名
    output_path_obj = Path(output_dir)
    filename = generate_filename("报价单", "pdf", output_path_obj)
    pdf_path = str(output_path_obj / filename)

    # 创建文档
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
    )

    # 段落样式
    title_style = ParagraphStyle(
        "Title",
        fontName=font_name,
        fontSize=22,
        textColor=COLOR_DARK_BROWN,
        alignment=TA_CENTER,
        spaceAfter=6 * mm,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        fontName=font_name,
        fontSize=11,
        textColor=COLOR_AMBER_GOLD,
        alignment=TA_CENTER,
        spaceAfter=8 * mm,
    )
    heading_style = ParagraphStyle(
        "Heading",
        fontName=font_name,
        fontSize=13,
        textColor=COLOR_MOLTEN_GOLD,
        spaceBefore=6 * mm,
        spaceAfter=3 * mm,
    )
    body_style = ParagraphStyle(
        "Body",
        fontName=font_name,
        fontSize=10,
        textColor=COLOR_DARK_BROWN,
        leading=16,
    )
    small_style = ParagraphStyle(
        "Small",
        fontName=font_name,
        fontSize=8,
        textColor=COLOR_COOL_GRAY,
        alignment=TA_CENTER,
    )

    elements = []

    # ── 标题区 ──
    file_id = get_file_id(filename)
    elements.append(Paragraph("AKO 装配式建筑报价单", title_style))
    elements.append(Paragraph("AKO · 专业预制 · 品质交付", subtitle_style))
    # 文件编号（首页标识）
    fid_style = ParagraphStyle("FileID", fontName=font_name, fontSize=9,
                               textColor=COLOR_COOL_GRAY, alignment=TA_CENTER, spaceAfter=4*mm)
    elements.append(Paragraph(f"编号：{file_id}", fid_style))

    # ── 项目信息 ──
    elements.append(Paragraph("一、项目信息", heading_style))
    info_data = [
        ["报价单号", file_id],
        ["项目名称", quote_result.get("project_name", "")],
        ["联系人", quote_result.get("contact", "")],
        ["联系电话", quote_result.get("phone", "")],
    ]
    info_table = Table(info_data, colWidths=[40 * mm, 120 * mm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), COLOR_AMBER_GOLD),
        ("TEXTCOLOR", (1, 0), (1, -1), COLOR_DARK_BROWN),
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_BG_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_COOL_GRAY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)

    # ── 工程参数 ──
    elements.append(Paragraph("二、工程参数", heading_style))
    param_data = [
        ["参数", "数值"],
        ["墙板类型", quote_result.get("wall_type", "")],
        ["墙板厚度", f"{quote_result.get('thickness', 150)}mm"],
        ["施工面积", f"{quote_result.get('area', 0):.1f} ㎡"],
        ["墙板体积", f"{quote_result.get('volume_m3', 0):.2f} m³"],
        ["钢材用量", f"{quote_result.get('steel_kg_per_sqm', 0):.2f} kg/㎡"],
        ["钢材单价", f"¥ {quote_result.get('steel_price_per_kg', 4.0):.2f} /kg"],
        ["运输距离", f"{quote_result.get('transport_distance', 50)} km"],
    ]
    param_table = Table(param_data, colWidths=[45 * mm, 115 * mm])
    param_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_WHITE),
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_MOLTEN_GOLD),
        ("TEXTCOLOR", (0, 1), (0, -1), COLOR_AMBER_GOLD),
        ("TEXTCOLOR", (1, 1), (1, -1), COLOR_DARK_BROWN),
        ("BACKGROUND", (0, 1), (-1, -1), COLOR_BG_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_COOL_GRAY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(param_table)

    # ── 原材料直接成本明细 ──
    elements.append(Paragraph("三、原材料直接成本", heading_style))
    material_rows = [["材料项目", "金额（元）"]]
    material_items = quote_result.get("material_items", {})
    for item_name, item_cost in material_items.items():
        material_rows.append([item_name, f"¥ {item_cost:,.2f}"])
    material_rows.append(["钢材成本", f"¥ {quote_result.get('steel_cost', 0):,.2f}"])
    material_rows.append(["原材料合计（含钢材）", f"¥ {quote_result.get('total_material', 0):,.2f}"])
    material_table = Table(material_rows, colWidths=[100 * mm, 60 * mm])
    material_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_WHITE),
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_MOLTEN_GOLD),
        ("TEXTCOLOR", (0, 1), (0, -2), COLOR_AMBER_GOLD),
        ("TEXTCOLOR", (1, 1), (1, -2), COLOR_DARK_BROWN),
        ("BACKGROUND", (0, 1), (-1, -2), COLOR_BG_LIGHT),
        ("TEXTCOLOR", (0, -1), (-1, -1), COLOR_DARK_BROWN),
        ("BACKGROUND", (0, -1), (-1, -1), COLOR_CREAM_GOLD),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_COOL_GRAY),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(material_table)

    # ── 间接成本明细 ──
    elements.append(Paragraph("四、间接成本", heading_style))
    indirect_rows = [["成本项目", "金额（元）"]]
    indirect_items = quote_result.get("indirect_items", {})
    for item_name, item_cost in indirect_items.items():
        indirect_rows.append([item_name, f"¥ {item_cost:,.2f}"])
    indirect_rows.append(["间接成本小计", f"¥ {quote_result.get('indirect_subtotal', 0):,.2f}"])
    indirect_table = Table(indirect_rows, colWidths=[100 * mm, 60 * mm])
    indirect_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_WHITE),
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_MOLTEN_GOLD),
        ("TEXTCOLOR", (0, 1), (0, -2), COLOR_AMBER_GOLD),
        ("TEXTCOLOR", (1, 1), (1, -2), COLOR_DARK_BROWN),
        ("BACKGROUND", (0, 1), (-1, -2), COLOR_BG_LIGHT),
        ("TEXTCOLOR", (0, -1), (-1, -1), COLOR_DARK_BROWN),
        ("BACKGROUND", (0, -1), (-1, -1), COLOR_CREAM_GOLD),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_COOL_GRAY),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(indirect_table)

    # ── 其他费用 ──
    elements.append(Paragraph("五、其他费用", heading_style))
    other_rows = [
        ["费用项目", "金额（元）"],
        ["运输费用", f"¥ {quote_result.get('transport_cost', 0):,.2f}"],
        ["安装费用", f"¥ {quote_result.get('installation_cost', 0):,.2f}"],
    ]
    box_cost = quote_result.get("box_cost", 0)
    if box_cost > 0:
        other_rows.append(["箱体费用（标准箱体）", f"¥ {box_cost:,.2f}"])
    other_table = Table(other_rows, colWidths=[100 * mm, 60 * mm])
    other_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_WHITE),
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_MOLTEN_GOLD),
        ("TEXTCOLOR", (0, 1), (0, -1), COLOR_AMBER_GOLD),
        ("TEXTCOLOR", (1, 1), (1, -1), COLOR_DARK_BROWN),
        ("BACKGROUND", (0, 1), (-1, -1), COLOR_BG_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_COOL_GRAY),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(other_table)

    # ── 汇总 ──
    elements.append(Paragraph("六、费用汇总", heading_style))
    profit_rate_pct = quote_result.get("profit_rate", 0.15) * 100
    summary_data = [
        ["成本小计", f"¥ {quote_result.get('cost_subtotal', 0):,.2f}"],
        [f"税金（{quote_result.get('tax_rate', 0.09)*100:.0f}%）", f"¥ {quote_result.get('tax_amount', 0):,.2f}"],
        [f"合理利润（{profit_rate_pct:.0f}%）", f"¥ {quote_result.get('profit_amount', 0):,.2f}"],
        ["合计总价", f"¥ {quote_result.get('total', 0):,.2f}"],
    ]
    summary_table = Table(summary_data, colWidths=[80 * mm, 80 * mm])
    summary_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("TEXTCOLOR", (0, 0), (0, -1), COLOR_AMBER_GOLD),
        ("TEXTCOLOR", (1, 0), (1, -1), COLOR_DARK_BROWN),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("BACKGROUND", (0, -1), (-1, -1), COLOR_CREAM_GOLD),
        ("FONTSIZE", (0, -1), (-1, -1), 14),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_COOL_GRAY),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(summary_table)

    # ── 备注 ──
    elements.append(Spacer(1, 8 * mm))
    elements.append(Paragraph("备注：本报价单有效期 30 天，最终以合同为准。", body_style))
    elements.append(Spacer(1, 10 * mm))
    elements.append(Paragraph("AKO · 装配式建筑专家", small_style))

    # 生成 PDF
    doc.build(elements)

    # 校验文件大小（铁律：max_file_size_mb）
    max_mb = _config["pdf"]["max_file_size_mb"]
    file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
    if file_size_mb > max_mb:
        logger.warning(f"PDF 文件过大: {file_size_mb:.2f}MB > {max_mb}MB")

    logger.info(f"PDF 已生成: {pdf_path} ({file_size_mb:.2f}MB)")
    return pdf_path
