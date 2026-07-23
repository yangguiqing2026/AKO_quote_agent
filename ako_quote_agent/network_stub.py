"""
network_stub.py - AKO 报价智能体网络模块预留接口
备案后实现：从虚拟主机 fetch.php 取任务、POST PDF 到 mail.php、心跳等。
铁律 #20: 不得只写 pass，必须定义好 TypedDict 入参出参，内部抛出 NotImplementedError。
"""

from typing import TypedDict, Optional, List


class TaskData(TypedDict):
    """任务数据结构"""
    id: str
    timestamp: float
    started_at: Optional[float]
    status: str
    form_data: dict
    user_email: str
    notify_type: str
    result: Optional[dict]
    synced: bool
    retry_count: int


class HeartbeatResponse(TypedDict):
    """心跳响应结构"""
    agent_id: str
    status: str
    timestamp: float


def fetch_task_from_remote(token: str, base_url: str) -> Optional[TaskData]:
    """
    从虚拟主机 fetch.php 取待处理任务。

    Args:
        token: 认证 token
        base_url: 虚拟主机基础 URL

    Returns:
        TaskData 或 None（无待处理任务时）
    """
    raise NotImplementedError("备案后实现")


def send_pdf_to_remote(
    pdf_path: str,
    task_id: str,
    user_email: str,
    token: str,
    base_url: str
) -> bool:
    """
    POST PDF 文件到虚拟主机 mail.php，由服务端发送邮件。

    Args:
        pdf_path: PDF 文件本地路径
        task_id: 任务 ID
        user_email: 用户邮箱
        token: 认证 token
        base_url: 虚拟主机基础 URL

    Returns:
        是否发送成功
    """
    raise NotImplementedError("备案后实现")


def heartbeat(agent_id: str, token: str, base_url: str) -> bool:
    """
    ping 虚拟主机 heartbeat.php，上报 Agent 存活状态。

    Args:
        agent_id: Agent 唯一标识
        token: 认证 token
        base_url: 虚拟主机基础 URL

    Returns:
        心跳是否成功
    """
    raise NotImplementedError("备案后实现")


def query_task_status(task_id: str, token: str, base_url: str) -> Optional[TaskData]:
    """
    查询虚拟主机 status.php 上的任务状态。

    Args:
        task_id: 任务 ID
        token: 认证 token
        base_url: 虚拟主机基础 URL

    Returns:
        TaskData 或 None
    """
    raise NotImplementedError("备案后实现")


def sync_local_tasks(tasks: List[TaskData], token: str, base_url: str) -> bool:
    """
    将本地任务状态批量同步到虚拟主机。

    Args:
        tasks: 需要同步的任务列表
        token: 认证 token
        base_url: 虚拟主机基础 URL

    Returns:
        是否同步成功
    """
    raise NotImplementedError("备案后实现")
