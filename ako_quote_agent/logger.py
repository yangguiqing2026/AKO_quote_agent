"""
logger.py - AKO 报价智能体日志配置
使用 RotatingFileHandler，自动轮转，同时输出控制台。
"""

import logging
import os
import json
from logging.handlers import RotatingFileHandler

# 加载配置（PyInstaller-safe：config.json 不在临时目录则用内置默认值）
_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
_config = {}
if os.path.exists(_CONFIG_PATH):
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            _config = json.load(f)
    except Exception:
        pass

# 默认值（打包后 config.json 可能不可用）
LOG_DIR = _config.get("paths", {}).get("log_dir", os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs"))
MAX_BYTES = _config.get("log", {}).get("max_bytes", 5 * 1024 * 1024)
BACKUP_COUNT = _config.get("log", {}).get("backup_count", 3)
LOG_LEVEL = getattr(logging, _config.get("log", {}).get("level", "INFO").upper(), logging.INFO)

# 确保日志目录存在
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "agent.log")

# 日志格式
_FORMATTER = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def get_logger(name: str = "ako_agent") -> logging.Logger:
    """获取配置好的 logger 实例（单例模式，同名返回同一 logger）"""
    logger = logging.getLogger(name)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    logger.setLevel(LOG_LEVEL)

    # 文件 handler（RotatingFileHandler）
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setFormatter(_FORMATTER)
    logger.addHandler(file_handler)

    # 控制台 handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(_FORMATTER)
    logger.addHandler(console_handler)

    return logger
