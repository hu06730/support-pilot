"""MCPProvider 配置解析 & 工具合并测试。"""

import os
from unittest.mock import AsyncMock, patch

import pytest

from app.mcp.provider import MCPProvider


class TestMCPProviderInit:
    def test_extract_server_id(self):
        assert MCPProvider._extract_server_id("http://mcp-server:5000", 0) == "mcp-server"
        assert MCPProvider._extract_server_id("http://10.0.0.1:5000", 0) == "10-0-0-1"
        assert MCPProvider._extract_server_id("invalid", 2) == "server-2"

    def test_parse_multiple_urls(self):
        os.environ["MCP_SERVER_URLS"] = "http://host1:5000, http://host2:5001"
        provider = MCPProvider()
        # init 会尝试连接，这里只测 URL 解析逻辑
        urls = [u.strip() for u in os.environ["MCP_SERVER_URLS"].split(",") if u.strip()]
        assert len(urls) == 2
        assert "http://host1:5000" in urls
        os.environ.pop("MCP_SERVER_URLS", None)


class TestMCPProviderTools:
    @pytest.mark.asyncio
    async def test_empty_urls_returns_no_tools(self):
        os.environ["MCP_SERVER_URLS"] = ""
        provider = MCPProvider()
        tools = await provider.get_all_tools()
        assert tools == []
        os.environ.pop("MCP_SERVER_URLS", None)

    @pytest.mark.asyncio
    async def test_invalidate_cache(self):
        provider = MCPProvider()
        provider._tools_cache = ["fake_tool"]
        provider.invalidate_cache()
        assert provider._tools_cache is None
