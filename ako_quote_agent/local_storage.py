"""
local_storage.py - AKO 报价智能体目录初始化 + 文件归档
负责创建必要的数据目录，并提供 PDF 归档功能。
"""

import os
import json
import shutil
from datetime import datetime

from logger import get_logger

logger = get_logger("ako_storage")

# 加载配置
_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
    _config = json.load(f)

DATA_DIR = _config["paths"]["data_dir"]
PDF_DIR = _config["paths"]["pdf_dir"]
LOG_DIR = _config["paths"]["log_dir"]


def init_dirs() -> None:
    """
    创建项目所需目录结构：
    - ./data/
    - ./pdfs/YYYY/  （按当前年份）
    - ./logs/
    铁律 #15
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    year_dir = os.path.join(PDF_DIR, str(datetime.now().year))
    os.makedirs(year_dir, exist_ok=True)

    logger.info(f"目录初始化完成: {DATA_DIR}, {year_dir}, {LOG_DIR}")


def get_pdf_dir_for_year(year: int = None) -> str:
    """获取指定年份的 PDF 存储目录，默认当前年份"""
    if year is None:
        year = datetime.now().year
    year_dir = os.path.join(PDF_DIR, str(year))
    os.makedirs(year_dir, exist_ok=True)
    return year_dir


def archive_pdf(source_path: str, task_id: str, year: int = None) -> str:
    """
    将生成的 PDF 文件归档到按年份组织的目录中。
    铁律 #16: ./pdfs/2026/AK-{task_id}.pdf

    Args:
        source_path: PDF 源文件路径
        task_id: 任务 ID
        year: 归档年份，默认当前年份

    Returns:
        归档后的完整路径
    """
    year_dir = get_pdf_dir_for_year(year)
    naming_format = _config["pdf"]["naming_format"]
    filename = naming_format.format(task_id=task_id)
    dest_path = os.path.join(year_dir, filename)

    shutil.copy2(source_path, dest_path)
    logger.info(f"PDF 已归档: {dest_path}")

    return dest_path
