"""
inbox_writer.py - 报价完成后写 business inbox，打通线索管道
格式: #项目名 #报价 #墙板类型 报价单号:xxx 总价:xxx元 面积:xxx㎡ 联系人:xxx
"""
import os
import json
from datetime import datetime

from logger import get_logger

logger = get_logger("ako_inbox")

# business agent 的微信 inbox 目录（环境变量优先，硬编码兜底）
_BUSINESS_INBOX = os.environ.get(
    "AKO_BUSINESS_INBOX",
    os.path.join(
        os.environ.get("AKO_BUSINESS_ROOT", r"D:\AKO_business_agent"),
        "data", "wechat_inbox"
    )
)


def write_quote_to_inbox(quote_result: dict, task_id: str) -> str | None:
    """
    报价完成后将快照写入 business agent 的微信 inbox。
    格式兼容 wechat_parser.parse_line() 的 #ProjectName #Tag 约定。

    Returns:
        写入的文件路径，失败返回 None
    """
    project_name = quote_result.get("project_name", "未命名项目")
    wall_type = quote_result.get("wall_type", "外墙")
    thickness = quote_result.get("thickness", 150)
    area = quote_result.get("area", 0)
    total = quote_result.get("total", 0)
    contact = quote_result.get("contact", "")
    phone = quote_result.get("phone", "")

    # 构造微信暗号格式的行（主消息，兼容 wechat_parser）
    content = (
        f"报价单号:{task_id} "
        f"总价:{total:,.0f}元 "
        f"面积:{area}㎡ "
        f"厚度:{thickness}mm "
        f"联系人:{contact} "
        f"电话:{phone}"
    )
    line = f"#{project_name} #报价 #{wall_type} {content}\n"

    # 附加成本快照（JSON），供 business_agent 交叉校验双引擎成本
    cost_snapshot = {
        "source": "quote_agent",
        "task_id": task_id,
        "price_book_version": quote_result.get("price_book_version", "unknown"),
        "cost_subtotal": quote_result.get("cost_subtotal", 0),
        "total_material": quote_result.get("total_material", 0),
        "indirect_subtotal": quote_result.get("indirect_subtotal", 0),
        "transport_cost": quote_result.get("transport_cost", 0),
        "installation_cost": quote_result.get("installation_cost", 0),
        "box_cost": quote_result.get("box_cost", 0),
        "tax_amount": quote_result.get("tax_amount", 0),
        "profit_amount": quote_result.get("profit_amount", 0),
        "total": quote_result.get("total", 0),
        "area": quote_result.get("area", 0),
        "wall_type": quote_result.get("wall_type", ""),
        "thickness": quote_result.get("thickness", 0),
        "volume_m3": quote_result.get("volume_m3", 0),
        "steel_cost": quote_result.get("steel_cost", 0),
        "steel_kg_per_sqm": quote_result.get("steel_kg_per_sqm", 0),
    }

    try:
        os.makedirs(_BUSINESS_INBOX, exist_ok=True)
        filename = f"quote_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = os.path.join(_BUSINESS_INBOX, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(line)
            # 成本快照行：以 #COST_SNAPSHOT 前缀 + JSON 单行，wechat_parser 解析时忽略
            json_snapshot = json.dumps(cost_snapshot, ensure_ascii=False, separators=(",", ":"))
            f.write(f"#COST_SNAPSHOT {json_snapshot}\n")
        logger.info(f"线索已写入 inbox: {filepath}")
        return filepath
    except OSError as e:
        logger.error(f"写入 inbox 失败: {e}")
        return None
