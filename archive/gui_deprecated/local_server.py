"""
local_server.py - AKO 报价智能体 Flask HTTP 服务
提供 POST /submit 和 GET /status 接口，独立运行。
铁律 #1-#4: FileLock + os.replace 原子写入、makedirs、debug=False、127.0.0.1。
"""

import os
import json

# [DEPRECATED_GUI] from flask import Flask, request, jsonify

from logger import get_logger
from local_queue import add_task, get_task, mark_converted

logger = get_logger("ako_server")

# 加载配置
_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
    _config = json.load(f)

TOKEN = _config["token"]
DATA_DIR = _config["paths"]["data_dir"]

# 铁律 #2: 启动时自动 makedirs
os.makedirs(DATA_DIR, exist_ok=True)

# [DEPRECATED_GUI] app = Flask(__name__)


# [DEPRECATED_GUI] @app.route("/submit", methods=["POST"])
def submit():
    """
    POST /submit - 小程序表单提交入口
    请求体: { "token": "ako2024", "form_data": {...}, "user_email": "...", "notify_type": "email" }
    """
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"success": False, "error": "Invalid JSON body"}), 400

    # 校验 token
    if data.get("token") != TOKEN:
        logger.warning(f"Token 校验失败: {data.get('token')}")
        return jsonify({"success": False, "error": "Invalid token"}), 403

    form_data = data.get("form_data")
    if not form_data or not isinstance(form_data, dict):
        return jsonify({"success": False, "error": "Missing or invalid form_data"}), 400

    user_email = data.get("user_email", "")
    notify_type = data.get("notify_type", "email")

    # 入队
    task_id = add_task(form_data, user_email, notify_type)
    logger.info(f"任务已提交: {task_id}")

    return jsonify({"success": True, "task_id": task_id}), 200


# [DEPRECATED_GUI] @app.route("/status", methods=["GET"])
def status():
    """
    GET /status - 本地调试查询任务状态
    参数: ?task_id=xxx&token=ako2024
    """
    token = request.args.get("token", "")
    if token != TOKEN:
        return jsonify({"success": False, "error": "Invalid token"}), 403

    task_id = request.args.get("task_id", "")
    if not task_id:
        return jsonify({"success": False, "error": "Missing task_id"}), 400

    task = get_task(task_id)
    if task is None:
        return jsonify({"success": False, "error": "Task not found"}), 404

    return jsonify({"success": True, "task": task}), 200


# [DEPRECATED_GUI] @app.route("/leads/confirmed", methods=["POST"])
def leads_confirmed():
    """
    POST /leads/confirmed - business agent 确认线索入库后回调
    请求体: { "token": "ako2024", "task_id": "xxx", "project_id": "AKO-20260714-001" }
    """
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"success": False, "error": "Invalid JSON body"}), 400

    if data.get("token") != TOKEN:
        return jsonify({"success": False, "error": "Invalid token"}), 403

    task_id = data.get("task_id", "")
    project_id = data.get("project_id", "")
    if not task_id or not project_id:
        return jsonify({"success": False, "error": "Missing task_id or project_id"}), 400

    task = get_task(task_id)
    if task is None:
        return jsonify({"success": False, "error": "Task not found"}), 404

    mark_converted(task_id, project_id)
    logger.info(f"线索转化确认: {task_id} → {project_id}")
    return jsonify({"success": True, "task_id": task_id, "status": "converted"}), 200


# [DEPRECATED_GUI] @app.route("/health", methods=["GET"])
def health():
    """健康检查端点"""
    return jsonify({"status": "ok", "service": "AKO-Quote-Agent"}), 200


# ──────────────────────────────────────────────
# 启动入口
# ──────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("AKO 本地 Flask 服务启动中...")
    # 铁律 #3: debug=False 防止 Flask 重载导致文件锁混乱
    # 铁律 #4: 监听 127.0.0.1:5000
    # [DEPRECATED_GUI] app.run(
        host=_config["server"]["host"],
        port=_config["server"]["port"],
        debug=_config["server"]["debug"]
    )
