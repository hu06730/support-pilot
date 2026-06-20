"""JWT 认证模块 — 密码哈希 + Token 签发/验证。"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError

# JWT 配置
SECRET_KEY = "support-pilot-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24  # 24 小时


def hash_password(password: str) -> str:
    """PBKDF2-SHA256 密码哈希。"""
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return f"{salt}${h.hex()}"


def verify_password(plain: str, hashed: str) -> bool:
    """验证密码。"""
    try:
        salt, h = hashed.split("$", 1)
        check = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), 100000)
        return check.hex() == h
    except Exception:
        return False


def create_token(user_id: str, role: str = "user") -> str:
    """签发 JWT Token。"""
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """验证并解码 JWT Token。"""
    return jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
