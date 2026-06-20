"""MCP 管理接口 — 状态查询 / 手动重连。"""

from __future__ import annotations

from fastapi import APIRouter

from app.mcp.provider import mcp_provider
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/mcp/status")
async def mcp_status():
    """查询 MCP Server 连接状态。"""
    health = await mcp_provider.health_check()
    tools = await mcp_provider.get_all_tools()
    return {
        "connected": mcp_provider.is_connected(),
        "servers": health,
        "tools_count": len(tools),
        "tools": [t.name for t in tools],
    }


@router.post("/mcp/reconnect")
async def mcp_reconnect():
    """手动触发 MCP Server 重连。"""
    success = await mcp_provider.reconnect()
    tools = await mcp_provider.get_all_tools()
    return {
        "success": success,
        "connected": mcp_provider.is_connected(),
        "tools_count": len(tools),
        "tools": [t.name for t in tools],
    }
