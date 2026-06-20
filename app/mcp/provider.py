"""MCPProvider — 支持延迟加载 + 自动重连。"""

from __future__ import annotations

import asyncio

import httpx
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from app.config import settings
from app.mcp.client import create_mcp_client
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MCPProvider:
    """管理多个 MCP Server 连接，支持延迟加载和自动重连。"""

    def __init__(self):
        self._client: MultiServerMCPClient | None = None
        self._tools_cache: list[BaseTool] | None = None
        self._server_urls: dict[str, str] = {}
        self._connected: bool = False
        self._retry_task: asyncio.Task | None = None

    async def init(self) -> None:
        """启动时调用：解析 MCP_SERVER_URLS，尝试连接。"""
        urls = [u.strip() for u in settings.mcp_server_urls.split(",") if u.strip()]
        if not urls:
            logger.info("MCPProvider: 未配置 MCP_SERVER_URLS，跳过")
            return

        for i, url in enumerate(urls):
            server_id = self._extract_server_id(url, i)
            self._server_urls[server_id] = url
            logger.info("MCPProvider: 注册 server [%s] → %s", server_id, url)

        # 尝试首次连接（不阻塞启动）
        await self._try_connect()

        # 启动后台重连任务（如果首次连接失败）
        if not self._connected:
            self._retry_task = asyncio.create_task(self._background_retry())

    async def _try_connect(self) -> bool:
        """尝试连接 MCP Server 并加载工具。"""
        if not self._server_urls:
            return False

        self._client = create_mcp_client(
            server_urls=self._server_urls,
            timeout=settings.mcp_connect_timeout,
            tool_name_prefix=settings.mcp_tool_prefix,
        )

        try:
            tools = await asyncio.wait_for(
                self._client.get_tools(),
                timeout=settings.mcp_connect_timeout,
            )
            self._tools_cache = tools
            self._connected = True
            logger.info("MCPProvider: 连接成功，加载 %d 个工具", len(tools))
            for t in tools:
                logger.info("  - %s: %s", t.name, t.description[:60])
            return True
        except Exception as e:
            logger.warning("MCPProvider: 连接失败: %s", e)
            self._tools_cache = []
            self._connected = False
            self._client = None
            return False

    async def _background_retry(self) -> None:
        """后台任务：定期尝试重连 MCP Server。"""
        retry_interval = 30  # 每 30 秒重试一次
        max_retries = 20
        retries = 0

        while retries < max_retries and not self._connected:
            await asyncio.sleep(retry_interval)
            retries += 1
            logger.info("MCPProvider: 尝试重连 (%d/%d)...", retries, max_retries)
            if await self._try_connect():
                logger.info("MCPProvider: 重连成功！")
                # 重连成功后需要重建 Agent（通知上层）
                break

        if not self._connected:
            logger.warning("MCPProvider: 重连失败，将仅使用内置工具")

    async def get_all_tools(self) -> list[BaseTool]:
        """返回所有 MCP 工具。"""
        return self._tools_cache or []

    def is_connected(self) -> bool:
        """是否已连接到 MCP Server。"""
        return self._connected

    def invalidate_cache(self) -> None:
        """清空缓存。"""
        self._client = None
        self._tools_cache = None
        self._connected = False

    async def reconnect(self) -> bool:
        """手动触发重连。"""
        self.invalidate_cache()
        return await self._try_connect()

    async def shutdown(self) -> None:
        """应用关闭时调用。"""
        if self._retry_task and not self._retry_task.done():
            self._retry_task.cancel()
        self._client = None
        self._tools_cache = None
        self._connected = False
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
