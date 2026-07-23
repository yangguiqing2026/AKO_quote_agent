# AKO-Quote-Agent-Whitepaper-v1.0

---

## YAML 头

```yaml
project: AKO-Quote-Agent
version: v1.0
date: 2026-07-12
author: AKO Architecture Team
status: 已锁定 / 待开发
```

---

## 1. 项目概述

**项目名称**：AKO-Quote-Agent  
**中文名称**：AKO 报价智能体  
**所属业务线**：AKO-（主业务线）  
**项目代号**：AKO-Quote-Agent  

**核心目标**：实现微信小程序填报表单 → 本地计算报价 → 生成 PDF 报价单 → 邮件发送给用户的完整闭环。备案前纯本地运行，备案后无缝衔接云端。

**适用场景**：AKO 装配式建筑（陶粒墙板、标准箱体）的移动端报价系统，面向桐木岭地铁站口、花溪区等项目客户。

---

## 2. 架构总览

### 2.1 备案前架构（当前阶段）

```
微信小程序填表
    └── wx.request (POST JSON)
        └── 本地 Flask 服务 (127.0.0.1:5000)
            │ (FileLock + os.replace 原子写入)
            ▼
        ./data/tasks.json (任务队列)
            │
            ▼ (轮询读取)
        本地 Python Agent (main.py)
            │ ① 超时巡检 (processing→pending)
            │ ② 报价计算
            │ ③ PDF 生成 (硬编码中文字体)
            ▼
        ./pdfs/2026/ (按项目编号归档)
```

### 2.2 备案后架构（预留接口）

```
微信小程序填表
    └── 阿里云虚拟主机 PHP 队列
        │ (5 接口 + dashboard 监控面板)
        ▼
    本地 Python Agent 轮询 fetch.php
        │ ① 取任务
        │ ② 计算报价
        │ ③ 生成 PDF
        ▼
    本地 POST PDF → mail.php
        │
        ▼
    QQ 邮箱 SMTP (smtp.qq.com:465)
        │
        ▼
    用户邮箱收 PDF 附件
```

---

## 3. 技术栈

| 层级 | 技术 | 版本要求 |
|------|------|---------|
| 小程序端 | 微信小程序原生 | 基础库 2.30+ |
| 本地服务 | Flask | 2.3+ |
| 文件锁 | filelock | 3.12+ |
| PDF 生成 | reportlab | 4.0+ |
| 日志 | logging (标准库) | Python 3.10+ |
| 网络预留 | requests | 2.31+ |

---

## 4. 文件架构

```
ako_quote_agent/
├── main.py                  # 主入口，主循环 + 保活
├── local_server.py          # Flask HTTP 服务，独立运行
├── local_queue.py           # 任务队列管理（增删改查 + 超时巡检）
├── quote_engine.py        # 报价计算引擎
├── pdf_generator.py         # PDF 生成器
├── local_storage.py         # 目录初始化 + 文件归档
├── logger.py                # 日志配置（RotatingFileHandler）
├── network_stub.py          # 网络模块预留接口（TypedDict）
├── config.json              # 统一配置（token、字体路径、端口等）
├── requirements.txt         # 依赖清单
├── data/
│   └── tasks.json           # 任务队列（初始为空数组 []）
├── pdfs/
│   └── 2026/                # 按年自动生成
└── logs/
    └── agent.log            # 自动轮转
```

---

## 5. 接口规范

### 5.1 local_server.py

#### POST /submit

**功能**：小程序表单提交入口

**请求头**：
```
Content-Type: application/json
```

**请求体**：
```json
{
  "token": "ako2024",
  "form_data": {
    "project_name": "桐木岭地铁站",
    "area": 120.5,
    "wall_type": "外墙",
    "thickness": 150,
    "contact": "张三",
    "phone": "13800138000"
  },
  "user_email": "user@example.com",
  "notify_type": "email"
}
```

**响应体**：
```json
{
  "success": true,
  "task_id": "a3f7b2d9"
}
```

**错误响应**：
```json
{
  "success": false,
  "error": "Invalid token"
}
```

#### GET /status

**功能**：本地调试查询任务状态

**请求参数**：
```
?task_id=a3f7b2d9&token=ako2024
```

**响应体**：
```json
{
  "task": {
    "id": "a3f7b2d9",
    "timestamp": 1752291600.0,
    "started_at": null,
    "status": "pending",
    "form_data": {...},
    "user_email": "user@example.com",
    "notify_type": "email",
    "result": null,
    "synced": false,
    "retry_count": 0
  }
}
```

### 5.2 network_stub.py（备案后实现）

```python
from typing import TypedDict, Optional

class TaskData(TypedDict):
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

def fetch_task_from_remote(token: str, base_url: str) -> Optional[TaskData]:
    # 从虚拟主机 fetch.php 取待处理任务
    raise NotImplementedError("备案后实现")

def send_pdf_to_remote(
    pdf_path: str,
    task_id: str,
    user_email: str,
    token: str,
    base_url: str
) -> bool:
    # POST PDF 文件到虚拟主机 mail.php
    raise NotImplementedError("备案后实现")

def heartbeat(agent_id: str, token: str, base_url: str) -> bool:
    # ping 虚拟主机 heartbeat.php
    raise NotImplementedError("备案后实现")
```

---

## 6. 状态机

```
pending
  │
  ▼ (本地 Agent 取到任务)
processing ←──────┐
  │               │
  ▼ (计算完成)    │ (超时 5 分钟)
done              │
  │               │
  ▼ (synced: False│
   且网络可用)    │
synced            │
  │               │
  ▼ (计算失败)    │
failed ───────────┘
  │ (重试 3 次)
  ▼ (重试超限)
dead
```

**状态流转规则**：

| 状态 | 流转条件 | 动作 |
|------|---------|------|
| pending → processing | 本地 Agent 取到 oldest pending 任务 | 设置 started_at = time.time() |
| processing → done | 报价计算成功 + PDF 生成成功 | 设置 result = {...} |
| processing → pending | started_at 超过 300 秒未变 done | 超时巡检自动回退 |
| processing → failed | 报价计算或 PDF 生成报错 | retry_count += 1 |
| failed → processing | retry_count < 3 | 重新进入处理队列 |
| failed → dead | retry_count >= 3 | 人工排查 |
| done → synced | 网络模块可用 + POST 成功 | synced = True |

---

## 7. 配置规范（config.json）

```json
{
  "token": "ako2024",
  "server": {
    "host": "127.0.0.1",
    "port": 5000,
    "debug": false
  },
  "paths": {
    "data_dir": "./data",
    "pdf_dir": "./pdfs",
    "log_dir": "./logs"
  },
  "fonts": {
    "windows": "C:/Windows/Fonts/msyh.ttc",
    "linux": "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "fallback": "reportlab.pdfbase.ttfonts.TTFont"
  },
  "queue": {
    "processing_timeout": 300,
    "max_retry": 3,
    "poll_interval": 10,
    "heartbeat_interval": 30
  },
  "pdf": {
    "max_file_size_mb": 5,
    "naming_format": "AK-{task_id}.pdf"
  },
  "log": {
    "max_bytes": 5242880,
    "backup_count": 3,
    "level": "INFO"
  },
  "network": {
    "base_url": "https://akobuild.cloud",
    "enabled": false
  }
}
```

---

## 8. 强制铁律（20 条）

### 8.1 local_server.py

1. **必须** 使用 `FileLock` + `os.replace` 实现原子写入
2. **必须** 启动时自动 `makedirs(DATA_DIR, exist_ok=True)`
3. **必须** `debug=False` 防止 Flask 重载导致文件锁混乱
4. **必须** 监听 `127.0.0.1:5000`，仅本地可访问

### 8.2 local_queue.py

5. **所有** 增删改查函数内部必须调用 `_load_queue` / `_save_queue`
6. **必须** 包含 `started_at` 字段，用于超时巡检
7. **启动时** 执行超时巡检：扫描 `status=processing` 且 `started_at < (now - 300秒)` 的任务，自动回退为 `pending`
8. **必须** 使用 `uuid.uuid4().hex[:8]` 生成任务 ID

### 8.3 quote_engine.py

9. **启动时** 配置校验：若依赖外部 Excel/JSON 映射表缺失，则 `raise SystemExit("配置缺失，终止启动")`
10. **禁止** 硬编码魔法数字，所有常量必须在文件顶部定义
11. **报价公式** 写死或读本地配置，禁止运行时从网络拉取

### 8.4 pdf_generator.py

12. **中文字体** 必须硬编码绝对路径：
    - Windows: `C:/Windows/Fonts/msyh.ttc`
    - Linux: `/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc`
13. **必须** 设置 fallback：若均不存在，使用 `reportlab.pdfbase.ttfonts.TTFont` 并记录 `logger.critical`
14. **绝不允许** 使用默认字体导致乱码或崩溃

### 8.5 local_storage.py

15. **必须** 提供 `init_dirs()` 函数，创建 `./data/`、`./pdfs/YYYY/`、`./logs/`
16. **PDF 归档格式**：`./pdfs/2026/AK-{task_id}.pdf`

### 8.6 logger.py

17. **必须** 使用 `logging.handlers.RotatingFileHandler`：
    - `maxBytes = 5 * 1024 * 1024`（5MB）
    - `backupCount = 3`
18. **同时** 输出到控制台（便于调试）

### 8.7 main.py

19. **主循环** 必须包裹 `try...except Exception as e`：
    - 捕获后 `logger.error(traceback.format_exc())`
    - `time.sleep(5)` 继续
    - **禁止** 因单条脏数据导致进程退出

### 8.8 network_stub.py

20. **不得** 只写 `pass`，必须定义好 `TypedDict` 入参出参，内部抛出 `NotImplementedError("备案后实现")`

---

## 9. 备案后衔接

### 9.1 数据回填机制

- 本地 `tasks.json` 中每个 `done` 任务强制带 `synced: false`
- 网络模块上线后，`main.py` 在 `done` 状态下额外执行：
  ```python
  if not task['synced'] and config['network']['enabled']:
      success = send_pdf_to_remote(...)
      if success:
          task['synced'] = True
          update_task(task)
  ```
- 该机制支持断网续传，即使云端暂时不可用，本地队列依然稳健推进

### 9.2 虚拟主机 PHP 接口（预留）

| 接口 | 功能 | 状态 |
|------|------|------|
| `submit.php` | 接收小程序表单，存队列 | 备案后实现 |
| `fetch.php` | 本地轮询取待处理任务 | 备案后实现 |
| `mail.php` | 接收 PDF 文件，调用邮件推送 | 备案后实现 |
| `heartbeat.php` | 接收本地心跳 | 备案后实现 |
| `status.php` | 查询任务状态 | 备案后实现 |
| `dashboard.php` | 监控面板 | 备案后实现 |

### 9.3 邮件配置（预留）

- **SMTP 地址**：`smtp.qq.com`
- **端口**：`465`（SSL）
- **密码**：QQ 邮箱授权码（非登录密码）
- **发件人**：用户个人 QQ 邮箱

---

## 10. 验收标准

| 验收项 | 标准 |
|--------|------|
| 小程序提交 | 通过 `wx.request` 成功 POST 到 `127.0.0.1:5000/submit`，返回 `task_id` |
| 文件锁 | 并发提交 100 次，无 `JSONDecodeError` 或数据丢失 |
| 超时巡检 | 手动将任务改为 `processing` 且不处理，300 秒后自动回退 `pending` |
| PDF 生成 | 含中文字体，无乱码，文件大小 < 5MB |
| 日志轮转 | 手动写入 6MB 日志，确认只保留最近 3 个备份 |
| 主循环保活 | 注入异常数据，进程不退出，5 秒后继续处理 |
| 网络 stub | 调用任意函数均抛出 `NotImplementedError`，参数类型正确 |

---

## 11. 附录

### 11.1 依赖安装

```bash
pip install flask filelock reportlab
pip freeze > requirements.txt
```

### 11.2 启动命令

```bash
# 终端 1：启动 Flask 服务
python local_server.py

# 终端 2：启动 Agent 主循环
python main.py
```

### 11.3 调试命令

```bash
# 查询任务状态
curl "http://127.0.0.1:5000/status?task_id=a3f7b2d9&token=ako2024"

# 手动提交测试数据
curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"token":"ako2024","form_data":{"area":100},"user_email":"test@qq.com"}'
```

---

**文档结束**
