"""MCPProvider — 配置驱动，支持多 MCP Server，解耦 Agent 与 MCP 连接细节。"""

from __future__ import annotations

import asyncio

from langchain_core.tools import BaseTool

from app.config import settings
from app.mcp.client import MCPClient
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MCPProvider:
    """管理多个 MCP Server 连接，提供统一的工具获取接口。"""

    def __init__(self):
        self._clients: dict[str, MCPClient] = {}
        self._tools_cache: list[BaseTool] | None = None
        self._tool_source: dict[str, str] = {}  # tool_name → server_url

    async def init(self) -> None:
        """启动时调用：解析 MCP_SERVER_URLS，建立所有连接。"""
        urls = [u.strip() for u in settings.mcp_server_urls.split(",") if u.strip()]
        for i, url in enumerate(urls):
            server_id = self._extract_server_id(url, i)
            client = MCPClient(url, timeout=settings.mcp_connect_timeout)
            self._clients[server_id] = client
            logger.info("MCPProvider: 注册 server [%s] → %s", server_id, url)

        # 并发预加载工具
        await self._load_all_tools()

    async def _load_all_tools(self) -> None:
        """并发从所有 Server 拉取工具列表。"""
        all_tools: list[BaseTool] = []
        tasks = []
        for server_id, client in self._clients.items():
            prefix = server_id if settings.mcp_tool_prefix else ""
            tasks.append(client.connect_and_get_tools(prefix=prefix))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for (server_id, _), result in zip(self._clients.items(), results):
            if isinstance(result, Exception):
                logger.error("MCPProvider: server [%s] 加载失败: %s", server_id, result)
                continue
            for tool in result:
                self._tool_source[tool.name] = server_id
                all_tools.append(tool)

        self._tools_cache = all_tools
        logger.info("MCPProvider: 共加载 %d 个 MCP 工具", len(all_tools))

    async def get_all_tools(self) -> list[BaseTool]:
        """返回所有 MCP 工具（供 Agent 使用）。"""
        if self._tools_cache is None:
            await self._load_all_tools()
        return self._tools_cache or []

    def invalidate_cache(self) -> None:
        """强制刷新工具缓存。"""
        self._tools_cache = None
        for client in self._clients.values():
            client._tools = None

    async def health_check(self) -> dict[str, bool]:
        """检查各 Server 连通性。"""
        result = {}
        for server_id, client in self._clients.items():
            try:
                import httpx
                async with httpx.AsyncClient(timeout=5) as http:
                    resp = await http.get(f"{client.server_url}/sse", timeout=3)
                    result[server_id] = resp.status_code in (200, 405)
            except Exception:
                result[server_id] = False
        return result

    @staticmethod
    def _extract_server_id(url: str, index: int) -> str:
        """从 URL 提取简短标识。"""
        try:
            host = url.split("//")[1].split(":")[0].split("/")[0]
            return host.replace(".", "-").replace(" ", "")
        except Exception:
            return f"server-{index}"


# 全局单例
mcp_provider = MCPProvider()
