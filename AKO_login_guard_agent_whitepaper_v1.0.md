# AKO_login_guard Agent 白皮书

> **文档作者**: AKO_studio  
> **版本**: v1.0  
> **日期**: 2026-07-26  
> **性质**: 顶层设计文档，指导 VS Code 实现  
> **适用范围**: 所有 AKO Agent 桌面端（.exe 分发）

---

## 一、需求定位

**场景**: AKO_quote_agent 等 Agent 打包为单文件 `.exe` 分发给员工。员工双击即用，但必须确保**只有内部员工能打开**，防止商业数据外泄。

**约束**:
- 员工是电脑盲，不能要求配置环境、注册账号等复杂操作
- 部分场景可能离线运行（工地现场），不能依赖网络认证
- 密码必须加密，不能明文写在代码或配置文件里
- 你（管理员）需要能增删改员工账号
- 与 PySide6 主窗口无缝集成

---

## 二、架构设计

### 2.1 整体流程

```
员工双击 .exe
    ↓
┌─────────────────┐
│  AKO 登录窗口   │  ← 最先弹出，模态阻塞主程序
│  ┌───────────┐  │
│  │ 用户名     │  │
│  │ [________]│  │
│  │ 密码       │  │
│  │ [________]│  │
│  │ [记住我 □] │  │
│  │           │  │
│  │ [  登 录  ]│  │
│  └───────────┘  │
└─────────────────┘
    ↓ 验证通过
┌─────────────────┐
│ AKO_quote_agent │  ← 主窗口正常加载
│   主程序窗口    │
└─────────────────┘
    ↓ 验证失败
弹窗提示 → 3次失败 → 程序强制退出
```

### 2.2 安全模型

| 层级 | 机制 | 说明 |
|------|------|------|
| 存储加密 | **bcrypt / argon2** 哈希 | 密码永不存明文，只存哈希值 |
| 用户表 | **SQLite 本地加密** | 用户数据存本地，但数据库文件加密 |
| 防拷贝 | **机器码绑定（可选）** | 高级方案：账号与员工电脑硬件绑定 |
| 防暴力破解 | **3次失败锁定 + 延迟** | 连续3次错误，程序退出，需重新双击 |
| 传输安全 | **不适用** | 纯本地认证，无网络传输 |

---

## 三、用户数据模型

### 3.1 用户表结构（SQLite）

```sql
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT UNIQUE NOT NULL,       -- 登录名（如：luozeguang）
    password_hash TEXT NOT NULL,            -- bcrypt 哈希值
    display_name TEXT,                      -- 显示名（如：罗泽广）
    role        TEXT DEFAULT 'user',        -- 角色：admin / user
    created_at  TEXT,                     -- ISO 8601 时间
    last_login  TEXT,                       -- 最后登录时间
    is_active   INTEGER DEFAULT 1           -- 1=启用，0=禁用
);
```

### 3.2 初始管理员账号

程序首次运行时，自动创建默认管理员：

| 字段 | 值 |
|------|-----|
| username | `admin` |
| password_hash | bcrypt(`ako2026`) |
| display_name | `系统管理员` |
| role | `admin` |

**首次登录后必须强制修改 admin 密码**。

---

## 四、登录窗口界面设计

### 4.1 窗口规格

| 属性 | 设定值 |
|------|--------|
| 窗口尺寸 | 400 × 320 像素 |
| 窗口类型 | 模态对话框（QDialog），阻塞主程序 |
| 标题 | `AKO 内部系统登录` |
| 图标 | AKO Logo |
| 背景色 | #EBDAB9（奶油金） |
| 不可调整大小 | 固定尺寸，防止布局错乱 |

### 4.2 界面布局

```
┌────────────────────────────────┐
│      [AKO Logo 64px]           │
│      AKO 内部系统登录            │
│                                │
│  用户名                         │
│  ┌──────────────────────────┐  │
│  │  luozeguang              │  │  ← QLineEdit
│  └──────────────────────────┘  │
│                                │
│  密码                           │
│  ┌──────────────────────────┐  │
│  │  ••••••••                │  │  ← QLineEdit (EchoMode=Password)
│  └──────────────────────────┘  │
│                                │
│  [□ 记住我（7天内免登录）]      │  ← QCheckBox
│                                │
│  ┌──────────────────────────┐  │
│  │        登  录            │  │  ← QPushButton
│  └──────────────────────────┘  │
│                                │
│  首次登录？请联系管理员开通账号  │  ← QLabel（灰色小字）
└────────────────────────────────┘
```

### 4.3 交互逻辑

1. **启动即弹窗**: `QApplication` 初始化后，先 `exec()` 登录对话框，验证通过后才创建主窗口
2. **回车登录**: 密码框按回车键 = 点击登录按钮
3. **记住我**: 勾选后，生成加密 Token 存本地，7 天内免登录
4. **错误提示**: 用户名或密码错误时，密码框边框变红，状态栏显示红色文字，**不弹 QMessageBox**
5. **3次锁定**: 连续3次失败，程序 `sys.exit(1)` 强制退出

---

## 五、记住我（Token）机制

### 5.1 设计目的

员工每天开机都要用，每次输入密码麻烦。提供「7天免登录」选项，但 Token 必须安全。

### 5.2 Token 生成与验证

```
登录成功时（勾选"记住我"）:
    token = base64( username + ":" + sha256(machine_id + secret_key) )
    写入 ~/.ako/auth_token（文件权限 600）

下次启动时:
    读取 token → 解析 username → 验证 machine_id 是否匹配 → 直接放行
```

**安全要点**:
- Token 包含**机器码绑定**，复制到其他电脑无效
- `secret_key` 硬编码在代码中（通过 PyInstaller 打包后难以提取）
- Token 文件设置只读权限（Windows 下通过 `os.chmod`）
- Token 有效期 7 天，过期后必须重新输入密码

---

## 六、管理员功能

### 6.1 入口

登录成功后，主窗口菜单栏增加 **「系统」→「用户管理」**，仅 `role='admin'` 可见。

### 6.2 用户管理窗口

```
┌─────────────────────────────────────────────┐
│  用户管理（仅管理员可见）                     │
├─────────────────────────────────────────────┤
│  ┌────┬──────────┬──────────┬──────┬──────┐ │
│  │ 序号│ 用户名   │ 显示名   │ 角色 │ 状态 │ │
│  │ 1   │ admin    │ 管理员   │ admin│ 启用 │ │
│  │ 2   │ luozeguang│ 罗泽广  │ user │ 启用 │ │
│  │ 3   │ zhangsan │ 张三     │ user │ 禁用 │ │
│  └────┴──────────┴──────────┴──────┴──────┘ │
│                                             │
│  [添加用户] [重置密码] [启用/禁用] [删除]    │
└─────────────────────────────────────────────┘
```

### 6.3 功能清单

| 功能 | 说明 |
|------|------|
| 添加用户 | 输入用户名、显示名、初始密码（默认 `ako123456`，首次登录强制修改） |
| 重置密码 | 选中用户 → 重置为默认密码 → 该用户下次登录强制修改 |
| 启用/禁用 | 禁用后该账号无法登录 |
| 删除 | 物理删除用户记录，不可逆 |

---

## 七、与主程序的集成方式

### 7.1 启动顺序（关键）

```python
# 伪代码（VS Code 实现参考）

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Step 1: 检查 Token（记住我）
    auth = AuthManager()
    if auth.has_valid_token():
        user = auth.validate_token()
        if user:
            # Token 有效，直接进主程序
            main_window = MainWindow(user)
            main_window.show()
            sys.exit(app.exec())

    # Step 2: 弹出登录窗口
    login_dialog = LoginDialog()
    if login_dialog.exec() == QDialog.Accepted:
        user = login_dialog.get_user()
        if login_dialog.remember_me:
            auth.save_token(user)
        # Step 3: 验证通过，启动主窗口
        main_window = MainWindow(user)
        main_window.show()
        sys.exit(app.exec())
    else:
        # 登录取消或失败
        sys.exit(0)
```

### 7.2 主窗口接收用户信息

```python
class MainWindow(QMainWindow):
    def __init__(self, user):
        super().__init__()
        self.current_user = user  # 包含 username, display_name, role

        # 根据角色显示/隐藏管理员菜单
        if user.role != 'admin':
            self.menu_system.removeAction(self.action_user_mgmt)

        # 状态栏显示当前登录人
        self.statusBar().showMessage(f"当前用户: {user.display_name}")
```

---

## 八、安全加固建议

### 8.1 数据库加密

SQLite 数据库文件使用 **SQLCipher** 或 **pysqlcipher3** 加密，密码硬编码在代码中（通过打包后难以逆向）。

```python
# 连接加密数据库
import sqlite3
from pysqlcipher3 import dbapi2 as sqlite

conn = sqlite.connect('users.db')
conn.execute("PRAGMA key = 'AKO_SECRET_2026'")
```

### 8.2 防反编译（进阶）

| 措施 | 说明 |
|------|------|
| PyInstaller 打包 | 代码编译为 .pyc 后打包，非明文 |
| UPX 压缩 | 增加逆向难度 |
| 关键字符串混淆 | `secret_key` 不直接写明文，用字节数组拼接 |
| 机器码绑定 | Token 与 CPU 序列号 / 主板 UUID 绑定 |

### 8.3 防暴力破解

- 3次失败 → 程序退出
- 每次失败 → 密码框抖动动画（QPropertyAnimation）
- 不提示"用户名不存在" vs "密码错误"，统一提示"用户名或密码错误"（防止枚举用户名）

---

## 九、打包注意事项

### 9.1 依赖清单

```bash
pip install PySide6 bcrypt pysqlcipher3
```

### 9.2 auto-py-to-exe 配置

| 配置项 | 值 |
|--------|-----|
| Script | `AKO_quote_agent_gui.py`（入口文件包含登录逻辑） |
| Onefile | ✅ One File |
| Console | ✅ Window Based (hide console) |
| Icon | `ako_logo.ico` |
| Additional Files | `users.db`（加密数据库，首次运行自动创建可省略） |

### 9.3 首次部署流程

1. 你（管理员）在开发电脑上运行程序，自动创建 `users.db`
2. 用默认 `admin` / `ako2026` 登录，**立即修改密码**
3. 进入用户管理，添加所有员工账号
4. 将 `users.db` 连同 `.exe` 一起分发（或让 `.exe` 首次运行时自动创建空库）

**推荐**: `.exe` 首次运行时自动创建空数据库 + 默认 admin 账号，你只需把 `.exe` 发给员工，员工第一次打开自动初始化，你用 admin 登录后添加他们的账号。

---

## 十、员工使用流程（零学习成本）

```
员工收到 AKO_quote_agent.exe
    ↓
双击运行
    ↓
弹出登录窗口
    ↓
输入管理员给的用户名和密码
    ↓
勾选「记住我」（可选）
    ↓
点击「登录」
    ↓
进入 AKO_quote_agent 主界面，正常使用
    ↓
关闭程序
    ↓
下次双击 → 若勾选了记住我 → 直接进主界面
```

---

## 十一、与 AKO 体系的联动

1. **AKO_hub**: 登录成功后，向 hub 上报「用户登录事件」（用户名、时间、机器码）
2. **AKO_netwatch_agent**: 监控异常登录（如非工作时间、陌生机器码）
3. **AKO_law_agent**: 用户操作日志写入审计记录，符合数据安全合规
4. **AKO_tag_manager**: 员工创建的项目文件自动打标签 `#用户/{username}`

---

## 十二、代码生成约束（AI Compiler Rules）

1. **密码哈希**: 必须使用 `bcrypt.hashpw()`，严禁 MD5 / SHA1
2. **Token 安全**: 机器码 + secret_key 双重绑定，Token 文件设置 `os.chmod(path, 0o600)`
3. **错误处理**: 登录失败不暴露具体原因（不区分"用户不存在"和"密码错误"）
4. **UI 线程**: 登录验证在 UI 线程执行（本地 SQLite 毫秒级响应，无需 Worker）
5. **数据库路径**: 使用 `os.path.expanduser("~/.ako/users.db")`，兼容 Windows 和后续可能的 Mac

---

> **铁律提醒**: 本文档为规划级指南，所有代码实现由 VS Code 执行。AI 仅输出架构、组件清单、交互逻辑与安全规范，不直接编写业务代码。

---

*AKO_studio | 2026-07-26*
