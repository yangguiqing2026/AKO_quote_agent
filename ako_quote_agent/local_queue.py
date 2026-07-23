"""
local_queue.py - AKO 报价智能体任务队列管理
增删改查 + 超时巡检，使用 FileLock 保证原子写入。
"""

import os
import json
import time
import uuid
from typing import Optional, List, Dict

from filelock import FileLock

from logger import get_logger

logger = get_logger("ako_queue")

# 加载配置
_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
    _config = json.load(f)

DATA_DIR = _config["paths"]["data_dir"]
QUEUE_FILE = os.path.join(DATA_DIR, "tasks.json")
LOCK_FILE = QUEUE_FILE + ".lock"

PROCESSING_TIMEOUT = _config["queue"]["processing_timeout"]  # 300 秒
MAX_RETRY = _config["queue"]["max_retry"]                    # 3 次


def _ensure_queue_file() -> None:
    """确保队列文件存在，不存在则初始化为空数组"""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        logger.info(f"初始化任务队列文件: {QUEUE_FILE}")


def _load_queue() -> List[Dict]:
    """加载队列（内部函数，必须在 FileLock 内调用）"""
    _ensure_queue_file()
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_queue(tasks: List[Dict]) -> None:
    """保存队列（原子写入：先写临时文件，再 os.replace）"""
    tmp_file = QUEUE_FILE + ".tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    os.replace(tmp_file, QUEUE_FILE)


# ──────────────────────────────────────────────
# 公开 API
# ──────────────────────────────────────────────

def add_task(form_data: dict, user_email: str, notify_type: str = "email") -> str:
    """
    新增任务到队列尾部，返回 task_id。
    铁律 #8: uuid.uuid4().hex[:8]
    """
    task_id = uuid.uuid4().hex[:8]
    task = {
        "id": task_id,
        "timestamp": time.time(),
        "started_at": None,
        "status": "pending",
        "form_data": form_data,
        "user_email": user_email,
        "notify_type": notify_type,
        "result": None,
        "synced": False,
        "retry_count": 0
    }

    lock = FileLock(LOCK_FILE)
    with lock:
        tasks = _load_queue()
        tasks.append(task)
        _save_queue(tasks)

    logger.info(f"新任务入队: {task_id}")
    return task_id


def get_task(task_id: str) -> Optional[Dict]:
    """根据 task_id 查询单个任务"""
    lock = FileLock(LOCK_FILE)
    with lock:
        tasks = _load_queue()
    for t in tasks:
        if t["id"] == task_id:
            return t
    return None


def get_oldest_pending() -> Optional[Dict]:
    """获取最老的 pending 状态任务（FIFO）"""
    lock = FileLock(LOCK_FILE)
    with lock:
        tasks = _load_queue()
    for t in tasks:
        if t["status"] == "pending":
            return t
    return None


def update_task(task: Dict) -> None:
    """更新任务（根据 task.id 匹配）"""
    lock = FileLock(LOCK_FILE)
    with lock:
        tasks = _load_queue()
        for i, t in enumerate(tasks):
            if t["id"] == task["id"]:
                tasks[i] = task
                break
        _save_queue(tasks)
    logger.debug(f"任务已更新: {task['id']} -> {task['status']}")


def mark_processing(task_id: str) -> None:
    """将任务标记为 processing，设置 started_at。铁律 #6"""
    lock = FileLock(LOCK_FILE)
    with lock:
        tasks = _load_queue()
        for t in tasks:
            if t["id"] == task_id:
                t["status"] = "processing"
                t["started_at"] = time.time()
                break
        _save_queue(tasks)
    logger.info(f"任务 {task_id} -> processing")


def mark_done(task_id: str, result: dict) -> None:
    """将任务标记为 done"""
    lock = FileLock(LOCK_FILE)
    with lock:
        tasks = _load_queue()
        for t in tasks:
            if t["id"] == task_id:
                t["status"] = "done"
                t["result"] = result
                break
        _save_queue(tasks)
    logger.info(f"任务 {task_id} -> done")


def mark_failed(task_id: str) -> None:
    """
    将任务标记为 failed，retry_count += 1。
    若 retry_count >= MAX_RETRY，则标记为 dead。
    """
    lock = FileLock(LOCK_FILE)
    with lock:
        tasks = _load_queue()
        for t in tasks:
            if t["id"] == task_id:
                t["retry_count"] += 1
                if t["retry_count"] >= MAX_RETRY:
                    t["status"] = "dead"
                    logger.warning(f"任务 {task_id} 重试超限 -> dead")
                else:
                    t["status"] = "failed"
                    logger.warning(
                        f"任务 {task_id} -> failed (retry {t['retry_count']}/{MAX_RETRY})"
                    )
                break
        _save_queue(tasks)


def mark_converted(task_id: str, project_id: str) -> None:
    """标记线索已转化为 business agent 项目。铁律 #20: 双向通讯回调"""
    lock = FileLock(LOCK_FILE)
    with lock:
        tasks = _load_queue()
        for t in tasks:
            if t["id"] == task_id:
                t["status"] = "converted"
                t["converted_to"] = project_id
                t["converted_at"] = time.time()
                break
        _save_queue(tasks)
    logger.info(f"任务 {task_id} -> converted (→{project_id})")


def mark_synced(task_id: str) -> None:
    """将任务标记为已同步"""
    lock = FileLock(LOCK_FILE)
    with lock:
        tasks = _load_queue()
        for t in tasks:
            if t["id"] == task_id:
                t["synced"] = True
                break
        _save_queue(tasks)
    logger.info(f"任务 {task_id} -> synced")


def timeout_scan() -> List[str]:
    """
    超时巡检：扫描 status=processing 且 started_at 超过 PROCESSING_TIMEOUT 秒的任务，
    自动回退为 pending。铁律 #7
    返回被回退的 task_id 列表。
    """
    now = time.time()
    reverted = []

    lock = FileLock(LOCK_FILE)
    with lock:
        tasks = _load_queue()
        changed = False
        for t in tasks:
            if t["status"] == "processing" and t["started_at"] is not None:
                elapsed = now - t["started_at"]
                if elapsed > PROCESSING_TIMEOUT:
                    t["status"] = "pending"
                    t["started_at"] = None
                    reverted.append(t["id"])
                    changed = True
                    logger.warning(
                        f"超时巡检: 任务 {t['id']} 处理超时 ({elapsed:.0f}s) -> pending"
                    )
        if changed:
            _save_queue(tasks)

    return reverted


def get_all_tasks() -> List[Dict]:
    """获取全部任务列表"""
    lock = FileLock(LOCK_FILE)
    with lock:
        return _load_queue()
