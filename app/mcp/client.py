"""单个 MCP Server 连接封装。"""

from __future__ import annotations

import json
from typing import Any

import httpx
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, create_model

from app.utils.logger import get_logger

logger = get_logger(__name__)


class MCPClient:
    """封装与单个 MCP Server 的 SSE 连接。"""

    def __init__(self, server_url: str, timeout: int = 10):
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout
        self._tools: list[StructuredTool] | None = None

    async def connect_and_get_tools(self, prefix: str = "") -> list[StructuredTool]:
        """通过 MCP SSE 获取工具列表并转为 LangChain Tool。"""
        if self._tools is not None:
            return self._tools

        tools = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 1. 获取工具列表（通过 MCP 协议的 JSON-RPC）
                init_resp = await client.post(
                    f"{self.server_url}/messages/",
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {"name": "support-pilot", "version": "0.1.0"},
                        },
                    },
                )

                # 2. 列出工具
                list_resp = await client.post(
                    f"{self.server_url}/messages/",
                    json={
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/list",
                        "params": {},
                    },
                )

                if list_resp.status_code == 200:
                    data = list_resp.json()
                    tool_defs = data.get("result", {}).get("tools", [])
                    for tdef in tool_defs:
                        tool_name = tdef["name"]
                        prefixed_name = f"{prefix}__{tool_name}" if prefix else tool_name
                        lc_tool = self._create_langchain_tool(
                            name=prefixed_name,
                            description=tdef.get("description", ""),
                            schema=tdef.get("inputSchema", {}),
                            server_url=self.server_url,
                            original_name=tool_name,
                        )
                        tools.append(lc_tool)
                    logger.info("MCP %s: 加载 %d 个工具", self.server_url, len(tools))
                else:
                    logger.warning("MCP %s: tools/list 返回 %d", self.server_url, list_resp.status_code)

        except Exception as e:
            logger.error("MCP 连接失败 %s: %s", self.server_url, e)

        self._tools = tools
        return tools

    @staticmethod
    def _create_langchain_tool(
        name: str,
        description: str,
        schema: dict,
        server_url: str,
        original_name: str,
    ) -> StructuredTool:
        """将 MCP 工具定义转为 LangChain StructuredTool。"""
        # 从 JSON Schema 构建 Pydantic 参数模型
        properties = schema.get("properties", {})
        required_fields = set(schema.get("required", []))
        field_defs = {}
        for fname, fdef in properties.items():
            ftype = str  # 简化：统一用 str
            default = ... if fname in required_fields else fdef.get("default", "")
            field_defs[fname] = (ftype, Field(default=default, description=fdef.get("description", "")))

        ArgsModel = create_model(f"{name}_args", **field_defs)

        async def _call(**kwargs) -> str:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{server_url}/messages/",
                    json={
                        "jsonrpc": "2.0",
                        "id": 100,
                        "method": "tools/call",
                        "params": {"name": original_name, "arguments": kwargs},
                    },
                )
                if resp.status_code == 200:
                    result = resp.json().get("result", {})
                    content = result.get("content", [])
                    if content and content[0].get("type") == "text":
                        return content[0]["text"]
                    return json.dumps(result, ensure_ascii=False)
                return f"Error: MCP call returned {resp.status_code}"

        return StructuredTool(
            name=name,
            description=description,
            func=None,
            coroutine=_call,
            args_schema=ArgsModel,
        )
