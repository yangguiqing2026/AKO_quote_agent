"""
main.py - AKO 报价智能体主入口
主循环 + 保活，轮询任务队列 → 报价计算 → PDF 生成 → 归档。
铁律 #19: 主循环包裹 try...except，禁止因脏数据退出进程。
"""

import os
import sys
import time
import json
import traceback
import uuid

from logger import get_logger
from local_storage import init_dirs, archive_pdf, get_pdf_dir_for_year
from local_queue import (
    get_oldest_pending,
    mark_processing,
    mark_done,
    mark_failed,
    timeout_scan,
    get_all_tasks,
)
from quote_engine import calculate_quote
from pdf_generator import generate_pdf
from inbox_writer import write_quote_to_inbox

logger = get_logger("ako_agent")

# 加载配置
_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
    _config = json.load(f)

POLL_INTERVAL = _config["queue"]["poll_interval"]          # 10 秒
AGENT_ID = uuid.uuid4().hex[:8]


def process_task(task: dict) -> None:
    """
    处理单个任务：报价计算 → PDF 生成 → 归档 → 标记完成。
    """
    task_id = task["id"]
    logger.info(f"开始处理任务: {task_id}")

    # 标记为 processing
    mark_processing(task_id)

    try:
        # ① 报价计算
        form_data = task["form_data"]
        quote_result = calculate_quote(form_data)

        # ② PDF 生成（先输出到临时目录）
        temp_dir = os.path.join(_config["paths"]["pdf_dir"], "_temp")
        os.makedirs(temp_dir, exist_ok=True)
        pdf_path = generate_pdf(quote_result, task_id, output_dir=temp_dir)

        # ③ PDF 归档到年份目录
        archived_path = archive_pdf(pdf_path, task_id)

        # ④ 标记完成
        result = {
            "pdf_path": archived_path,
            "quote": quote_result,
        }
        mark_done(task_id, result)

        # ⑤ 写 business inbox（线索管道）
        write_quote_to_inbox(quote_result, task_id)

        # 清理临时文件
        try:
            os.remove(pdf_path)
        except OSError:
            pass

        logger.info(f"任务 {task_id} 处理完成，PDF: {archived_path}")

    except Exception as e:
        logger.error(f"任务 {task_id} 处理失败: {e}\n{traceback.format_exc()}")
        mark_failed(task_id)


def main_loop() -> None:
    """
    Agent 主循环：
    ① 超时巡检
    ② 取最老 pending 任务
    ③ 处理任务
    ④ 循环
    铁律 #19: try...except 包裹，禁止因脏数据退出。
    """
    logger.info(f"AKO Agent 启动 (ID: {AGENT_ID})，轮询间隔 {POLL_INTERVAL}s")

    while True:
        try:
            # ① 超时巡检
            reverted = timeout_scan()
            if reverted:
                logger.info(f"超时巡检回退任务: {reverted}")

            # ② 取最老 pending 任务
            task = get_oldest_pending()

            if task is None:
                # 无待处理任务，等待后重试
                time.sleep(POLL_INTERVAL)
                continue

            # ③ 处理任务
            process_task(task)

        except Exception as e:
            # 铁律 #19: 捕获异常，记录日志，5 秒后继续
            logger.error(f"主循环异常: {e}\n{traceback.format_exc()}")
            time.sleep(5)


# ──────────────────────────────────────────────
# 启动入口
# ──────────────────────────────────────────────
if __name__ == "__main__":
    # 初始化目录结构
    init_dirs()

    logger.info("=" * 50)
    logger.info("AKO-Quote-Agent v1.0 启动")
    logger.info("=" * 50)

    try:
        main_loop()
    except KeyboardInterrupt:
        logger.info("Agent 收到中断信号，优雅退出")
    except Exception as e:
        logger.critical(f"Agent 致命错误: {e}\n{traceback.format_exc()}")
        sys.exit(1)
