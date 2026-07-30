"""
auth_manager.py - AKO_login_guard 认证核心模块
基于白皮书 v1.0 + 账号管理 v1.0
SQLite + bcrypt + Token 机制
"""
import os
import sqlite3
import hashlib
import json
import uuid
import time
import base64
import subprocess
from datetime import datetime, timedelta
from functools import partial

import bcrypt

# ── 路径配置 ──
AKO_DIR = os.path.join(os.path.expanduser("~"), ".ako")
DB_PATH = os.path.join(AKO_DIR, "users.db")
TOKEN_PATH = os.path.join(AKO_DIR, "auth_token")
AUDIT_LOG_PATH = os.path.join(AKO_DIR, "audit.log")
SECRET_KEY = bytes([65, 75, 79, 95, 83, 69, 67, 82, 69, 84, 95, 50, 48, 50, 54])  # "AKO_SECRET_2026"
DB_ENCRYPT_KEY = "AKO_DB_KEY_2026"

# ── 常量 ──
MAX_FAILED_ATTEMPTS = 3
TOKEN_VALIDITY_DAYS = 7
BCRYPT_ROUNDS = 12
DEFAULT_ADMIN_PASSWORD = "ako2026"


def _get_machine_id():
    """获取机器唯一标识（不绑定硬件，仅作基础标识）"""
    try:
        result = subprocess.run(
            ["wmic", "csproduct", "get", "uuid"],
            capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().split("\n")
        if len(lines) > 1:
            return lines[1].strip()
    except Exception:
        pass
    # Fallback: 使用主机名 + 用户名组合
    import socket
    return f"{socket.gethostname()}:{os.environ.get('USERNAME', 'unknown')}"


def _ensure_ako_dir():
    """确保 .ako 目录存在"""
    os.makedirs(AKO_DIR, exist_ok=True)


def _write_audit_log(message: str):
    """写入审计日志"""
    _ensure_ako_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}\n"
    try:
        with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass


# ──────────────────────────────────────────────
# AuthManager - 单例认证管理器
# ──────────────────────────────────────────────

class AuthManager:
    """认证管理器，管理用户数据库、Token、登录验证。"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        _ensure_ako_dir()
        self._init_db()

    def _init_db(self):
        """初始化数据库和默认管理员账号"""
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                display_name TEXT,
                phone       TEXT,
                role        TEXT DEFAULT 'user',
                must_change_password INTEGER DEFAULT 1,
                password_history TEXT DEFAULT '[]',
                failed_attempts INTEGER DEFAULT 0,
                locked_until TEXT,
                is_active   INTEGER DEFAULT 1,
                created_at  TEXT,
                last_login  TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS tokens (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT NOT NULL,
                token_hash  TEXT UNIQUE NOT NULL,
                machine_id  TEXT,
                created_at  TEXT,
                expires_at  TEXT,
                is_valid    INTEGER DEFAULT 1
            )
        """)

        # 检查是否有管理员账号
        cursor = conn.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND is_active=1")
        count = cursor.fetchone()[0]

        if count == 0:
            # 创建默认管理员
            pw_hash = bcrypt.hashpw(
                DEFAULT_ADMIN_PASSWORD.encode(),
                bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
            ).decode()
            now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            conn.execute(
                "INSERT INTO users (username, password_hash, display_name, phone, role, "
                "must_change_password, is_active, created_at) VALUES (?,?,?,?,?,?,?,?)",
                ("admin", pw_hash, "系统管理员", "", "admin", 1, 1, now)
            )
            conn.commit()
            _write_audit_log("SYSTEM CREATE user=admin display_name=系统管理员 (默认管理员创建)")

        conn.commit()
        conn.close()

    # ── 密码哈希 ──

    def hash_password(self, password: str) -> str:
        """生成 bcrypt 密码哈希"""
        return bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
        ).decode()

    def verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码"""
        try:
            return bcrypt.checkpw(password.encode(), password_hash.encode())
        except Exception:
            return False

    # ── 密码复杂度校验 ──

    def validate_password_strength(self, password: str, username: str = "",
                                    password_history: list = None) -> tuple:
        """
        校验密码强度。
        Returns: (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "密码至少需要8位"

        has_letter = any(c.isalpha() for c in password)
        has_digit = any(c.isdigit() for c in password)
        if not (has_letter and has_digit):
            return False, "密码必须包含字母和数字"

        if username and password.lower() == username.lower():
            return False, "密码不可与用户名相同"

        if password_history:
            for old_hash in password_history:
                if self.verify_password(password, old_hash):
                    return False, "新密码不可与最近3次历史密码相同"

        return True, ""

    # ── Token 管理 ──

    def generate_token(self, username: str) -> str:
        """生成加密 Token"""
        machine_id = _get_machine_id()
        token_data = f"{username}:{machine_id}:{SECRET_KEY.decode()}:{time.time()}"
        token_hash = hashlib.sha256(token_data.encode()).hexdigest()
        token = base64.b64encode(
            f"{username}:{token_hash}:{machine_id}".encode()
        ).decode()

        # 存入数据库
        now = datetime.now()
        expires = now + timedelta(days=TOKEN_VALIDITY_DAYS)
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO tokens (username, token_hash, machine_id, created_at, expires_at) "
            "VALUES (?,?,?,?,?)",
            (username, token_hash, machine_id,
             now.strftime("%Y-%m-%dT%H:%M:%S"),
             expires.strftime("%Y-%m-%dT%H:%M:%S"))
        )
        conn.commit()
        conn.close()

        # 写入 Token 文件
        _ensure_ako_dir()
        try:
            with open(TOKEN_PATH, "w", encoding="utf-8") as f:
                f.write(token)
        except Exception:
            pass

        return token

    def validate_token(self) -> dict:
        """验证本地 Token 是否有效。Returns user dict or None."""
        if not os.path.exists(TOKEN_PATH):
            return None

        try:
            with open(TOKEN_PATH, "r", encoding="utf-8") as f:
                token = f.read().strip()

            decoded = base64.b64decode(token).decode()
            parts = decoded.split(":", 2)
            if len(parts) < 3:
                return None

            username, token_hash, machine_id = parts
            current_machine_id = _get_machine_id()

            # 机器码验证（宽松模式）
            if machine_id != current_machine_id:
                # 允许同一主机名
                if machine_id.split(":")[0] != current_machine_id.split(":")[0]:
                    return None

            # 数据库验证
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.execute(
                "SELECT t.expires_at, u.username, u.display_name, u.role, u.is_active "
                "FROM tokens t JOIN users u ON t.username = u.username "
                "WHERE t.token_hash = ? AND t.is_valid = 1",
                (token_hash,)
            )
            row = cursor.fetchone()
            conn.close()

            if row:
                expires_at, uname, dname, role, is_active = row
                if is_active == 0:
                    return None
                if datetime.fromisoformat(expires_at) < datetime.now():
                    return None
                return {
                    "username": uname,
                    "display_name": dname,
                    "role": role,
                }
        except Exception:
            pass

        return None

    def invalidate_tokens(self, username: str):
        """注销某用户的所有 Token"""
        conn = sqlite3.connect(DB_PATH)
        conn.execute("UPDATE tokens SET is_valid=0 WHERE username=?", (username,))
        conn.commit()
        conn.close()
        # 删除本地 Token 文件
        if os.path.exists(TOKEN_PATH):
            try:
                os.remove(TOKEN_PATH)
            except Exception:
                pass

    def invalidate_all_tokens(self):
        """清除所有 Token"""
        conn = sqlite3.connect(DB_PATH)
        conn.execute("UPDATE tokens SET is_valid=0 WHERE is_valid=1")
        conn.commit()
        conn.close()
        if os.path.exists(TOKEN_PATH):
            try:
                os.remove(TOKEN_PATH)
            except Exception:
                pass

    def clear_local_token(self):
        """清除本地 Token 文件"""
        if os.path.exists(TOKEN_PATH):
            try:
                os.remove(TOKEN_PATH)
            except Exception:
                pass

    # ── 登录验证 ──

    def authenticate(self, username: str, password: str) -> tuple:
        """
        验证用户名密码。
        Returns: (success: bool, user_dict_or_error_msg: dict|str, must_change: bool)
        """
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute(
            "SELECT username, password_hash, display_name, role, is_active, "
            "must_change_password, failed_attempts, locked_until "
            "FROM users WHERE username=?",
            (username,)
        )
        row = cursor.fetchone()

        if not row:
            conn.close()
            _write_audit_log(f"LOGIN failed user={username} (用户不存在)")
            return False, "用户名或密码错误", False

        (uname, pw_hash, dname, role, is_active,
         must_change, failed_attempts, locked_until) = row

        # 检查是否被禁用
        if is_active == 0:
            conn.close()
            _write_audit_log(f"LOGIN failed user={username} (账号已禁用)")
            return False, "账号已被禁用，请联系管理员", False

        # 检查是否锁定
        if locked_until:
            lock_time = datetime.fromisoformat(locked_until)
            if lock_time > datetime.now():
                conn.close()
                _write_audit_log(f"LOGIN failed user={username} (账号已锁定至 {locked_until})")
                return False, f"账号已锁定，请于 {locked_until[:16]} 后再试", False

        # 验证密码
        if not self.verify_password(password, pw_hash):
            failed_attempts += 1
            now = datetime.now()
            if failed_attempts >= MAX_FAILED_ATTEMPTS:
                # 锁定 30 分钟
                lock_until = (now + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%S")
                conn.execute(
                    "UPDATE users SET failed_attempts=?, locked_until=? WHERE username=?",
                    (failed_attempts, lock_until, username)
                )
                conn.commit()
                conn.close()
                _write_audit_log(f"LOGIN LOCKOUT user={username} ({failed_attempts}/{MAX_FAILED_ATTEMPTS})")
                return False, f"密码错误次数过多，账号已锁定30分钟", False
            else:
                conn.execute(
                    "UPDATE users SET failed_attempts=? WHERE username=?",
                    (failed_attempts, username)
                )
                conn.commit()
                conn.close()
                _write_audit_log(
                    f"LOGIN failed user={username} ({failed_attempts}/{MAX_FAILED_ATTEMPTS})"
                )
                return False, f"用户名或密码错误（剩余尝试次数: {MAX_FAILED_ATTEMPTS - failed_attempts}）", False

        # 登录成功
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        conn.execute(
            "UPDATE users SET failed_attempts=0, locked_until=NULL, last_login=? WHERE username=?",
            (now, username)
        )
        conn.commit()
        conn.close()

        _write_audit_log(f"LOGIN success user={username}")

        return True, {
            "username": uname,
            "display_name": dname,
            "role": role,
        }, bool(must_change)

    # ── 用户管理 ──

    def get_all_users(self) -> list:
        """获取所有用户列表"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute(
            "SELECT id, username, display_name, phone, role, is_active, "
            "must_change_password, failed_attempts, created_at, last_login "
            "FROM users ORDER BY id"
        )
        users = []
        for row in cursor:
            users.append({
                "id": row[0],
                "username": row[1],
                "display_name": row[2],
                "phone": row[3] or "",
                "role": row[4],
                "is_active": bool(row[5]),
                "must_change_password": bool(row[6]),
                "failed_attempts": row[7],
                "created_at": row[8] or "",
                "last_login": row[9] or "",
            })
        conn.close()
        return users

    def create_user(self, username: str, display_name: str,
                    phone: str = "", role: str = "user") -> tuple:
        """
        创建新用户。
        Returns: (success, message, initial_password)
        """
        # 验证用户名
        if not username or not username.islower() or not username.isalpha():
            return False, "用户名必须为全小写英文字母", ""
        if len(username) < 4 or len(username) > 20:
            return False, "用户名长度需在4-20位之间", ""

        # 检查重名
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute("SELECT COUNT(*) FROM users WHERE username=?", (username,))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return False, f"用户名 {username} 已存在", ""

        # 生成初始密码：ako + 手机号后4位
        if phone and len(phone) >= 4:
            initial_password = "ako" + phone[-4:]
        else:
            # [REMOVED_SECRET] initial_password = "ako123456"

        pw_hash = self.hash_password(initial_password)
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        conn.execute(
            "INSERT INTO users (username, password_hash, display_name, phone, role, "
            "must_change_password, password_history, is_active, created_at) "
            "VALUES (?,?,?,?,?,1,'[]',1,?)",
            (username, pw_hash, display_name, phone, role, now)
        )
        conn.commit()
        conn.close()

        _write_audit_log(f"CREATE user={username} display_name={display_name} role={role}")
        return True, f"用户 {display_name} 创建成功", initial_password

    def reset_password(self, username: str) -> tuple:
        """管理员重置用户密码"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute(
            "SELECT display_name, phone FROM users WHERE username=?",
            (username,)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "用户不存在", ""

        display_name, phone = row
        if phone and len(phone) >= 4:
            new_password = "ako" + phone[-4:]
        else:
            # [REMOVED_SECRET] new_password = "ako123456"

        pw_hash = self.hash_password(new_password)
        conn.execute(
            "UPDATE users SET password_hash=?, must_change_password=1, "
            "failed_attempts=0, locked_until=NULL WHERE username=?",
            (pw_hash, username)
        )
        conn.commit()
        conn.close()

        # 清除该用户所有 Token
        self.invalidate_tokens(username)

        _write_audit_log(f"RESET_PASSWORD user={username}")
        return True, f"{display_name} 的密码已重置", new_password

    def change_password(self, username: str, old_password: str,
                        new_password: str, skip_old_check: bool = False) -> tuple:
        """修改密码（员工自助或首次强制修改）"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute(
            "SELECT password_hash, password_history FROM users WHERE username=?",
            (username,)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "用户不存在"

        pw_hash = row[0]
        history = json.loads(row[1]) if row[1] else []

        # 旧密码验证（非强制修改时需要）
        if not skip_old_check:
            if not self.verify_password(old_password, pw_hash):
                conn.close()
                return False, "当前密码错误"

        # 新密码复杂度校验
        is_valid, err_msg = self.validate_password_strength(
            new_password, username, history
        )
        if not is_valid:
            conn.close()
            return False, err_msg

        # 新密码不能与当前密码相同
        if self.verify_password(new_password, pw_hash):
            conn.close()
            return False, "新密码不可与当前密码相同"

        # 更新密码
        new_hash = self.hash_password(new_password)
        history.append(pw_hash)
        if len(history) > 3:
            history = history[-3:]

        conn.execute(
            "UPDATE users SET password_hash=?, password_history=?, "
            "must_change_password=0, failed_attempts=0 WHERE username=?",
            (new_hash, json.dumps(history), username)
        )
        conn.commit()
        conn.close()

        # 清除 Token
        self.invalidate_tokens(username)

        _write_audit_log(f"CHANGE_PASSWORD user={username}")
        return True, "密码修改成功"

    def toggle_user(self, username: str) -> tuple:
        """启用/禁用用户"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute(
            "SELECT is_active, display_name FROM users WHERE username=?",
            (username,)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "用户不存在"

        new_status = 0 if row[0] else 1
        conn.execute(
            "UPDATE users SET is_active=?, locked_until=NULL, failed_attempts=0 "
            "WHERE username=?",
            (new_status, username)
        )
        conn.commit()
        conn.close()

        if new_status == 0:
            self.invalidate_tokens(username)

        action = "DISABLE" if new_status == 0 else "ENABLE"
        _write_audit_log(f"{action} user={username}")
        status_text = "已禁用" if new_status == 0 else "已启用"
        return True, f"用户 {row[1]} {status_text}"

    def delete_user(self, username: str) -> tuple:
        """删除用户（物理删除）"""
        if username == "admin":
            return False, "不可删除 admin 账号"

        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM users WHERE username=?", (username,))
        conn.execute("DELETE FROM tokens WHERE username=?", (username,))
        conn.commit()
        conn.close()

        _write_audit_log(f"DELETE user={username}")
        return True, f"用户 {username} 已删除"

    def check_admin_exists(self) -> bool:
        """检查是否有可用的管理员账号"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute(
            "SELECT COUNT(*) FROM users WHERE role='admin' AND is_active=1"
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0