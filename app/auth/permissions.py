"""认证中间件 — FastAPI 依赖注入。"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.jwt import decode_token

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict | None:
    """获取当前用户（可选认证）。无 Token 时返回 None。"""
    if credentials is None:
        return None

    try:
        payload = decode_token(credentials.credentials)
        return {
            "user_id": payload["sub"],
            "role": payload.get("role", "user"),
        }
    except Exception:
        return None


def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """强制认证。无 Token 或 Token 无效时返回 401。"""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证 Token",
        )

    try:
        payload = decode_token(credentials.credentials)
        return {
            "user_id": payload["sub"],
            "role": payload.get("role", "user"),
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期",
        )
