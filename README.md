---
ako_doc_id: AKO_README_QTE_001
ako_version: v0.1.0
ako_status: 草稿
ako_title: AKO 报价智能体 (AKO-Quote-Agent)
ako_category: Agent
ako_author: 杨越浩
ako_created: 2026-07-14
ako_source: AKO_DOC_001 v1.0.0
ako_project_root: D:\AKO_quote_agent
---

# AKO 报价智能体（QTE）

## 1. 结论前置

AKO 报价智能体（QTE）是 AKO 装配式建筑业务线的移动端报价系统，实现微信小程序填报表单 → 本地计算报价 → 生成 PDF 报价单 → 邮件发送给用户的完整闭环。当前处于**备案前纯本地运行**阶段，备案后无缝衔接阿里云虚拟主机，实现云端任务队列与邮件推送。核心能力包括：任务队列管理（含超时巡检与原子写入）、陶粒墙板/标准箱体报价计算、中文字体 PDF 生成、断网续传的数据回填机制。

## 2. 修订记录

| 版本 | 日期 | 修订人 | 修订内容 | 签发人 |
|------|------|--------|----------|--------|
| v0.1.0 | 2026-07-14 | 杨越浩 | 按 AKO_DOC_001 初始化，内容源自 AKO_quote_agent_whitepaper_v1.0.md | （待签发） |

## 3. 项目概述

### 3.1 定位

面向 AKO 装配式建筑（陶粒墙板、标准箱体）的移动端报价系统，为桐木岭地铁站口、花溪区等项目客户提供即时报价 PDF 生成服务。

### 3.2 核心能力

1. **任务队列管理**：基于 JSON 文件 + FileLock 原子写入的本地任务队列，支持超时巡检与自动回退
2. **报价计算引擎**：陶粒墙板/标准箱体结构报价，公式本地化配置，不依赖网络
3. **PDF 报价单生成**：硬编码中文字体路径（微软雅黑/文泉驿），支持按年月归档
4. **断网续传**：备案后网络模块上线时，本地 `synced` 标志位自动回填云端队列
5. **日志轮转**：RotatingFileHandler（5MB × 3 备份），同时输出控制台

### 3.3 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.10+ | 主语言 |
| Flask 2.3+ | 本地 HTTP 服务（接收小程序 POST） |
| filelock 3.12+ | 任务队列原子写入 |
| reportlab 4.0+ | PDF 生成 |
| logging (标准库) | 日志轮转 |

## 4. 快速开始

### 4.1 环境要求

- Python 3.10+
- Windows（中文字体 `C:/Windows/Fonts/msyh.ttc`）或 Linux（`wqy-zenhei.ttc`）
- 端口 5000 可用

### 4.2 安装

```bash
cd D:\AKO_quote_agent\ako_quote_agent
pip install -r requirements.txt
```

### 4.3 运行

```bash
# 终端 1：启动 Flask 服务
python local_server.py

# 终端 2：启动 Agent 主循环
python main.py
```

调试：

```bash
# 查询任务状态
curl "http://127.0.0.1:5000/status?task_id=a3f7b2d9&token=ako2024"

# 手动提交测试数据
curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"token":"ako2024","form_data":{"area":100},"user_email":"test@qq.com"}'
```

## 5. 项目结构

```
D:\AKO_quote_agent\
├── AKO_quote_agent_whitepaper_v1.0.md   # 架构白皮书
└── ako_quote_agent/
    ├── main.py                  # 主入口，主循环 + 保活
    ├── local_server.py          # Flask HTTP 服务（接收小程序请求）
    ├── local_queue.py           # 任务队列管理（增删改查 + 超时巡检）
    ├── quote_engine.py          # 报价计算引擎
    ├── pdf_generator.py         # PDF 生成器
    ├── local_storage.py         # 目录初始化 + 文件归档
    ├── logger.py                # 日志配置（RotatingFileHandler）
    ├── network_stub.py          # 网络模块预留接口（TypedDict）
    ├── inbox_writer.py          # Inbox 写入桥接
    ├── config.json              # 统一配置（token、字体路径、端口等）
    ├── requirements.txt         # 依赖清单
    ├── data/
    │   └── tasks.json           # 任务队列（初始化为空数组 []）
    ├── pdfs/
    │   └── 2026/                # 按年自动归档
    └── logs/
        └── agent.log            # 自动轮转日志
```

## 6. 相关文档

- 架构白皮书：`D:\AKO_quote_agent\AKO_quote_agent_whitepaper_v1.0.md`
- AKO 生态总文档：AKO_DOC_001 v1.0.0

## 7. 术语

| 术语 | 定义 |
|------|------|
| QTE | Quote Engine，报价引擎代号 |
| 备案前/备案后 | 以 ICP 备案为分界，备案前纯本地运行，备案后接入阿里云虚拟主机 PHP 队列 |
| 超时巡检 | 扫描 `status=processing` 且超过 300 秒未完成的任务，自动回退为 `pending` |
| 断网续传 | 本地 `done` 任务带 `synced: false`，网络恢复后自动 POST PDF 到云端并标记 `synced: true` |
| 原子写入 | FileLock + os.replace 保证 JSON 文件并发写入安全 |

---
> 作者：AKO_studio
> 日期：2026-07-30
