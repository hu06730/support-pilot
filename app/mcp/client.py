"""MCP 客户端 — 基于 langchain-mcp-adapters 的 MultiServerMCPClient。"""

from __future__ import annotations

from langchain_mcp_adapters.client import MultiServerMCPClient

from app.utils.logger import get_logger

logger = get_logger(__name__)


def build_mcp_connections(
    server_urls: dict[str, str],
    timeout: float = 10,
) -> dict[str, dict]:
    """将 server_urls 映射为 MultiServerMCPClient 需要的 connections 配置。

    Args:
        server_urls: {server_id: url} 字典
        timeout: 连接超时秒数

    Returns:
        MultiServerMCPClient connections 格式
    """
    connections = {}
    for server_id, url in server_urls.items():
        connections[server_id] = {
            "transport": "sse",
            "url": f"{url.rstrip('/')}/sse",
            "timeout": timeout,
        }
        logger.info("MCP 连接配置: [%s] → %s/sse", server_id, url.rstrip("/"))
    return connections


def create_mcp_client(
    server_urls: dict[str, str],
    timeout: float = 10,
    tool_name_prefix: bool = True,
) -> MultiServerMCPClient:
    """创建 MultiServerMCPClient 实例。

    Args:
        server_urls: {server_id: url} 字典
        timeout: 连接超时
        tool_name_prefix: 是否给工具名加 server 前缀

    Returns:
        MultiServerMCPClient 实例（需 async with 使用）
    """
    connections = build_mcp_connections(server_urls, timeout)
    return MultiServerMCPClient(
        connections=connections,
        tool_name_prefix=tool_name_prefix,
        handle_tool_errors=True,
    )
