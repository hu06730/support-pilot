"""MCPProvider — 基于 MultiServerMCPClient，配置驱动，支持多 MCP Server。"""

from __future__ import annotations

import httpx
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from app.config import settings
from app.mcp.client import create_mcp_client
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MCPProvider:
    """管理多个 MCP Server 连接，提供统一的工具获取接口。"""

    def __init__(self):
        self._client: MultiServerMCPClient | None = None
        self._tools_cache: list[BaseTool] | None = None
        self._server_urls: dict[str, str] = {}

    async def init(self) -> None:
        """启动时调用：解析 MCP_SERVER_URLS，建立连接并加载工具。"""
        urls = [u.strip() for u in settings.mcp_server_urls.split(",") if u.strip()]
        if not urls:
            logger.info("MCPProvider: 未配置 MCP_SERVER_URLS，跳过")
            return

        for i, url in enumerate(urls):
            server_id = self._extract_server_id(url, i)
            self._server_urls[server_id] = url
            logger.info("MCPProvider: 注册 server [%s] → %s", server_id, url)

        self._client = create_mcp_client(
            server_urls=self._server_urls,
            timeout=settings.mcp_connect_timeout,
            tool_name_prefix=settings.mcp_tool_prefix,
        )

        await self._load_tools()

    async def _load_tools(self) -> None:
        """通过 MultiServerMCPClient 加载所有工具。"""
        if self._client is None:
            return

        try:
            # 新版 API：直接调用 get_tools()，无需 context manager
            tools = await self._client.get_tools()
            self._tools_cache = tools
            logger.info("MCPProvider: 共加载 %d 个 MCP 工具", len(tools))
            for t in tools:
                logger.info("  - %s: %s", t.name, t.description[:60])
        except Exception as e:
            logger.warning("MCPProvider: 加载工具失败（MCP Server 可能未启动）: %s", e)
            self._tools_cache = []

    async def get_all_tools(self) -> list[BaseTool]:
        """返回所有 MCP 工具（供 Agent 使用）。"""
        return self._tools_cache or []

    def invalidate_cache(self) -> None:
        """清空缓存。"""
        self._client = None
        self._tools_cache = None

    async def shutdown(self) -> None:
        """应用关闭时调用。"""
        self._client = None
        self._tools_cache = None
        logger.info("MCPProvider: 已关闭")

    async def health_check(self) -> dict[str, bool]:
        """检查各 Server 连通性。"""
        result = {}
        for server_id, url in self._server_urls.items():
            try:
                async with httpx.AsyncClient(timeout=5) as http:
                    resp = await http.get(f"{url.rstrip('/')}/sse", timeout=3)
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


mcp_provider = MCPProvider()
