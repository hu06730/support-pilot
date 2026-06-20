"""认证接口 — 注册 / 登录。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.auth.jwt import hash_password, verify_password, create_token

router = APIRouter()

# 内存用户存储（生产环境应替换为数据库）
_users: dict[str, dict] = {
    "admin": {
        "username": "admin",
        "password_hash": hash_password("admin123"),
        "role": "admin",
    },
}


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest):
    """注册新用户。"""
    if body.username in _users:
        raise HTTPException(status_code=400, detail="用户名已存在")

    _users[body.username] = {
        "username": body.username,
        "password_hash": hash_password(body.password),
        "role": "user",
    }

    token = create_token(body.username, "user")
    return TokenResponse(access_token=token, username=body.username, role="user")


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    """用户登录。"""
    user = _users.get(body.username)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_token(body.username, user["role"])
    return TokenResponse(access_token=token, username=body.username, role=user["role"])
