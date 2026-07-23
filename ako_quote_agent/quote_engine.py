"""
quote_engine.py - AKO 报价智能体报价计算引擎
负责根据表单数据计算装配式建筑报价。
铁律 #9-#11: 配置校验、禁止魔法数字、禁止网络拉取。

成本体系基于：阿格陶粒墙成本及售价推算.xlsx
- 外墙总计基准: 2337.40 元/m³ (@150mm = 350.43 元/㎡)
- 内墙总计基准: 1027.96 元/m³ (@150mm = 154.19 元/㎡)
- 钢材基准价: 4000 元/吨 (4 元/kg)，钢材用量按设计可调
"""

import os
import sys
import json
from typing import Dict, Optional

# 引入共享定价核心
_SHARED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "AKO_shared")
if os.path.isdir(_SHARED_DIR) and _SHARED_DIR not in sys.path:
    sys.path.insert(0, _SHARED_DIR)
try:
    from pricing_core import (
        TAX_RATE, TRANSPORT_RATE_PER_KM, INSTALLATION_RATE_PER_SQM,
        DEFAULT_TRANSPORT_DISTANCE_KM, MIN_ORDER_AREA_SQM, PRICE_BOOK_VERSION,
    )
except ImportError:
    # fallback: 共享模块不可用时使用内置常量
    TAX_RATE = 0.09
    TRANSPORT_RATE_PER_KM = 15.0
    INSTALLATION_RATE_PER_SQM = 80.0
    DEFAULT_TRANSPORT_DISTANCE_KM = 50
    MIN_ORDER_AREA_SQM = 10.0
    PRICE_BOOK_VERSION = "1.1.0"

from logger import get_logger

logger = get_logger("ako_quote")

# ──────────────────────────────────────────────
# 钢材定价（铁律 #10: 禁止硬编码魔法数字）
# ──────────────────────────────────────────────

# 钢材基准价：4000 元/吨 = 4 元/kg（含加工费）
STEEL_PRICE_PER_KG = 4.0

# 默认每平方米钢材用量（kg/㎡），按墙板类型
# 外墙：14 kg/㎡（原 xlsx 基准，可按项目设计调整）
# 内墙：0.75 kg/㎡（仅预埋件/连接钢管，不含结构钢筋）
DEFAULT_STEEL_KG_PER_SQM = {
    "外墙": 14.0,
    "内墙": 0.75,
    "隔墙": 0.75,
}

# ──────────────────────────────────────────────
# 墙板类型基准总价（元/m³，含所有成本+税+利润，不含钢材）
# 原 xlsx 总计 - 原钢材成本 = 基准价
#   外墙: 2337.40 - 562 = 1775.40 元/m³
#   内墙: 1027.96 - 20  = 1007.96 元/m³
# ──────────────────────────────────────────────
WALL_TYPE_BASE_PRICE_PER_M3 = {
    "外墙": 1775.40,
    "内墙": 1007.96,
    "隔墙": 1007.96,  # 参照内墙
}

# ──────────────────────────────────────────────
# 原材料直接成本明细（元/m³，数据来源：xlsx）
# ──────────────────────────────────────────────
MATERIAL_COST_BREAKDOWN = {
    "外墙": {
        "水泥 (P.O 42.5)": 216.0,
        "陶粒": 55.0,
        "发泡剂原液": 160.0,
        "安装螺栓+卡扣+密封五金件": 50.0,
        "防潮密封胶+防水处理": 20.0,
        "外墙漆/真石漆（一线品牌）": 400.0,
    },
    "内墙": {
        "水泥 (P.O 42.5)": 216.0,
        "陶粒": 55.0,
        "发泡剂原液": 160.0,
        "安装螺栓+卡扣+密封五金件": 50.0,
        "防潮密封胶+防水处理": 20.0,
    },
}

# ──────────────────────────────────────────────
# 间接成本明细（元/m³，数据来源：xlsx）
# ──────────────────────────────────────────────
INDIRECT_COST_BREAKDOWN = {
    "外墙": {
        "推广费": 12.0,
        "勘测费": 10.0,
        "BIM全流程设计+图纸深化": 70.0,
        "工厂生产+质检人工": 60.0,
        "运输-主干道运费": 100.0,
        "运输-二次转运费": 30.0,
        "安装-吊车/小型机械租赁": 30.0,
        "安装-现场安装人工": 50.0,
        "售后质保维护备用金": 15.0,
        "生产线+模具+设备折旧": 20.0,
        "办公运营+人员+资质+水电": 25.0,
    },
    "内墙": {
        "推广费": 8.0,
        # 勘测费: 0（大型施工场景免勘测）
        # BIM设计: 0（已按面积分摊）
        "工厂生产+质检人工": 60.0,
        "运输-主干道运费": 100.0,
        # 运输-二次转运费: 0（大型施工场景无二次转运）
        "安装-吊车/小型机械租赁": 30.0,
        "安装-现场安装人工": 50.0,
        "售后质保维护备用金": 15.0,
        "生产线+模具+设备折旧": 20.0,
        "办公运营+人员+资质+水电": 25.0,
    },
}

# 税费 + 合理利润（元/m³，数据来源：xlsx；钢材部分另计）
TAX_AND_PROFIT_PER_M3 = {
    "外墙": {"税费": 210.37, "合理利润": 350.61},
    "内墙": {"税费": 92.52, "合理利润": 154.19},
}

# 厚度系数（150mm 为基准的精确比例）
THICKNESS_MULTIPLIER = {
    100: 100 / 150,   # 0.667
    120: 120 / 150,   # 0.800
    150: 1.00,
    200: 200 / 150,   # 1.333
    250: 250 / 150,   # 1.667
}

# 标准箱体基础价（元）
STANDARD_BOX_BASE_PRICE = 15000.0

# 箱体面积单价（元/㎡）
STANDARD_BOX_AREA_PRICE = 350.0

# 配置文件路径（可选的外部映射表）
MAPPING_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pricing_config.json")


# ──────────────────────────────────────────────
# 启动配置校验（铁律 #9）
# ──────────────────────────────────────────────

def _validate_config() -> None:
    """
    启动时校验：若依赖外部 Excel/JSON 映射表缺失，则终止启动。
    当前版本使用内置常量，若存在 pricing_config.json 则覆盖。
    """
    global WALL_TYPE_BASE_PRICE_PER_M3, THICKNESS_MULTIPLIER, STANDARD_BOX_BASE_PRICE
    global STANDARD_BOX_AREA_PRICE, STEEL_PRICE_PER_KG, DEFAULT_STEEL_KG_PER_SQM
    global MATERIAL_COST_BREAKDOWN, INDIRECT_COST_BREAKDOWN, TAX_AND_PROFIT_PER_M3

    if os.path.exists(MAPPING_FILE):
        try:
            with open(MAPPING_FILE, "r", encoding="utf-8") as f:
                ext = json.load(f)
            WALL_TYPE_BASE_PRICE_PER_M3.update(ext.get("wall_type_base_price_per_m3", {}))
            raw_thickness = ext.get("thickness_multiplier", {})
            THICKNESS_MULTIPLIER.update({int(k): v for k, v in raw_thickness.items()})
            STANDARD_BOX_BASE_PRICE = ext.get("standard_box_base_price", STANDARD_BOX_BASE_PRICE)
            STANDARD_BOX_AREA_PRICE = ext.get("standard_box_area_price", STANDARD_BOX_AREA_PRICE)
            STEEL_PRICE_PER_KG = ext.get("steel_price_per_kg", STEEL_PRICE_PER_KG)
            DEFAULT_STEEL_KG_PER_SQM.update(ext.get("default_steel_kg_per_sqm", {}))
            MATERIAL_COST_BREAKDOWN.update(ext.get("material_cost_breakdown", {}))
            INDIRECT_COST_BREAKDOWN.update(ext.get("indirect_cost_breakdown", {}))
            TAX_AND_PROFIT_PER_M3.update(ext.get("tax_and_profit_per_m3", {}))
            logger.info(f"已加载外部定价配置: {MAPPING_FILE}")
        except Exception as e:
            logger.critical(f"外部定价配置加载失败: {e}")
            raise SystemExit("配置缺失，终止启动")
    else:
        logger.info("使用内置定价常量（未检测到 pricing_config.json）")


# 启动时执行校验
_validate_config()


# ──────────────────────────────────────────────
# 报价计算核心
# ──────────────────────────────────────────────

def calculate_quote(form_data: dict) -> Dict:
    """
    根据表单数据计算报价。

    form_data 字段:
        - project_name: 项目名称
        - area: 面积（㎡）
        - wall_type: 墙板类型（外墙/内墙/隔墙）
        - thickness: 厚度（mm）
        - contact: 联系人
        - phone: 联系电话
        - box_type: 箱体类型（可选，"standard" 为标准箱体）
        - transport_distance: 运输距离 km（可选）
        - steel_kg_per_sqm: 每平方米钢材用量 kg（可选，默认按墙板类型）

    Returns:
        报价结果字典（含明细分解）
    """
    area = float(form_data.get("area", 0))
    wall_type = form_data.get("wall_type", "外墙")
    thickness = int(form_data.get("thickness", 150))
    project_name = form_data.get("project_name", "未命名项目")
    contact = form_data.get("contact", "")
    phone = form_data.get("phone", "")
    box_type = form_data.get("box_type", None)
    transport_distance = float(
        form_data.get("transport_distance", DEFAULT_TRANSPORT_DISTANCE_KM)
    )

    # 校验面积
    if area < MIN_ORDER_AREA_SQM:
        raise ValueError(f"面积 {area}㎡ 低于最低起订面积 {MIN_ORDER_AREA_SQM}㎡")

    # 墙板类型校验
    if wall_type not in WALL_TYPE_BASE_PRICE_PER_M3:
        raise ValueError(f"不支持的墙板类型: {wall_type}，可选: {list(WALL_TYPE_BASE_PRICE_PER_M3.keys())}")

    # 厚度系数
    thickness_factor = THICKNESS_MULTIPLIER.get(thickness)
    if thickness_factor is None:
        raise ValueError(f"不支持的厚度: {thickness}mm，可选: {list(THICKNESS_MULTIPLIER.keys())}")

    # 钢材用量：优先使用表单传入值，否则使用默认值
    steel_kg_per_sqm = float(
        form_data.get("steel_kg_per_sqm", DEFAULT_STEEL_KG_PER_SQM.get(wall_type, 0))
    )

    # ── 体积计算 ──
    thickness_m = thickness / 1000.0
    volume_m3 = area * thickness_m

    # ── 1. 钢材成本（按每平方米用量 × 面积 × 钢材单价） ──
    steel_cost = steel_kg_per_sqm * area * STEEL_PRICE_PER_KG

    # ── 2. 原材料直接成本（按体积，不含钢材） ──
    material_items = {}
    material_subtotal = 0.0
    for item_name, unit_price_per_m3 in MATERIAL_COST_BREAKDOWN.get(wall_type, {}).items():
        item_cost = unit_price_per_m3 * volume_m3
        material_items[item_name] = round(item_cost, 2)
        material_subtotal += item_cost
    material_subtotal = round(material_subtotal, 2)

    # 原材料合计（含钢材）
    total_material = round(material_subtotal + steel_cost, 2)

    # ── 3. 间接成本（按体积） ──
    indirect_items = {}
    indirect_subtotal = 0.0
    for item_name, unit_price_per_m3 in INDIRECT_COST_BREAKDOWN.get(wall_type, {}).items():
        item_cost = unit_price_per_m3 * volume_m3
        indirect_items[item_name] = round(item_cost, 2)
        indirect_subtotal += item_cost
    indirect_subtotal = round(indirect_subtotal, 2)

    # ── 4. 箱体费用（如果指定了箱体类型） ──
    box_cost = 0.0
    if box_type == "standard":
        box_cost = STANDARD_BOX_BASE_PRICE + (area * STANDARD_BOX_AREA_PRICE)
    box_cost = round(box_cost, 2)

    # ── 5. 运输费（按运输距离） ──
    transport_cost = round(transport_distance * TRANSPORT_RATE_PER_KM, 2)

    # ── 6. 安装费（按面积） ──
    installation_cost = round(area * INSTALLATION_RATE_PER_SQM, 2)

    # ── 7. 成本小计（不含税、不含利润） ──
    cost_subtotal = round(
        total_material + indirect_subtotal + box_cost + transport_cost + installation_cost, 2
    )

    # ── 8. 税金 ──
    tax_amount = round(cost_subtotal * TAX_RATE, 2)

    # ── 9. 合理利润（按成本小计的 15%） ──
    profit_rate = 0.15
    profit_amount = round(cost_subtotal * profit_rate, 2)

    # ── 10. 含税含利总价 ──
    total = round(cost_subtotal + tax_amount + profit_amount, 2)

    # ── 组装结果 ──
    result = {
        "project_name": project_name,
        "contact": contact,
        "phone": phone,
        "area": area,
        "wall_type": wall_type,
        "thickness": thickness,
        "thickness_m": thickness_m,
        "volume_m3": round(volume_m3, 4),
        "thickness_factor": thickness_factor,
        "transport_distance": transport_distance,
        # 钢材
        "steel_price_per_kg": STEEL_PRICE_PER_KG,
        "steel_kg_per_sqm": steel_kg_per_sqm,
        "steel_cost": round(steel_cost, 2),
        # 原材料明细
        "material_items": material_items,
        "material_subtotal": material_subtotal,
        "total_material": total_material,
        # 间接成本明细
        "indirect_items": indirect_items,
        "indirect_subtotal": indirect_subtotal,
        # 其他费用
        "box_cost": box_cost,
        "transport_cost": transport_cost,
        "installation_cost": installation_cost,
        # 汇总
        "cost_subtotal": cost_subtotal,
        "tax_rate": TAX_RATE,
        "tax_amount": tax_amount,
        "profit_rate": profit_rate,
        "profit_amount": profit_amount,
        "total": total,
        "price_book_version": PRICE_BOOK_VERSION,
    }

    logger.info(
        f"报价计算完成: 项目={project_name}, 面积={area}㎡, "
        f"钢材用量={steel_kg_per_sqm}kg/㎡, 钢材成本={steel_cost:.2f}元, "
        f"总计={total:.2f}元"
    )
    return result