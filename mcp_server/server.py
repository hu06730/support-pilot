"""MCP Server 入口 — 通过 SSE transport 暴露工具。"""

from __future__ import annotations

import json

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount

from mcp_server.config import MCP_HOST, MCP_PORT
from mcp_server.tools.weather import get_weather
from mcp_server.tools.jira import create_jira_ticket

# ── 创建 MCP Server 实例 ──
server = Server("support-pilot-mcp")


@server.list_tools()
async def list_tools():
    """声明本 Server 提供的工具。"""
    from mcp.types import Tool
    return [
        Tool(
            name="get_weather",
            description="获取指定城市的天气信息，包括温度、天气状况、湿度和风速。",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称，如 'Beijing'"},
                },
                "required": ["city"],
            },
        ),
        Tool(
            name="create_jira_ticket",
            description="创建 Jira 工单，用于记录运维问题或任务。返回工单编号和链接。",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "工单标题"},
                    "description": {"type": "string", "description": "工单详细描述"},
                    "priority": {
                        "type": "string",
                        "enum": ["Low", "Medium", "High", "Critical"],
                        "description": "优先级",
                        "default": "Medium",
                    },
                },
                "required": ["title", "description"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """路由工具调用到具体实现。"""
    if name == "get_weather":
        result = await get_weather(arguments["city"])
    elif name == "create_jira_ticket":
        result = await create_jira_ticket(
            title=arguments["title"],
            description=arguments["description"],
            priority=arguments.get("priority", "Medium"),
        )
    else:
        result = {"error": f"Unknown tool: {name}"}

    return [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]


# ── Starlette 应用（SSE transport）──
sse_transport = SseServerTransport("/messages/")


async def handle_sse(request):
    async with sse_transport.connect_sse(request.scope, request.receive, request._send) as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())


app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse),
        Mount("/messages/", app=sse_transport.handle_post_message),
    ],
)


def main():
    import uvicorn
    uvicorn.run(app, host=MCP_HOST, port=MCP_PORT)


if __name__ == "__main__":
    main()
