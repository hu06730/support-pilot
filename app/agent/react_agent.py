"""Agent 组装 — 使用 langchain create_agent（LangGraph）。"""

from __future__ import annotations

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from app.config import settings
from app.tools.diagnostic import DIAGNOSTIC_TOOLS
from app.tools.rag_tool import RAG_TOOLS
from app.mcp.provider import MCPProvider
from app.agent.prompts import REACT_SYSTEM_PROMPT
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def build_agent(mcp_provider: MCPProvider):
    """组装完整的 Agent（内置 + RAG + MCP 工具）。

    返回 LangGraph CompiledStateGraph，支持 ainvoke / astream。
    """
    # ── 收集所有工具 ──
    builtin_tools = DIAGNOSTIC_TOOLS
    rag_tools = RAG_TOOLS
    mcp_tools = await mcp_provider.get_all_tools()

    all_tools = builtin_tools + rag_tools + mcp_tools
    tool_names = [t.name for t in all_tools]
    logger.info("Agent 工具列表: %s", tool_names)

    # ── LLM ──
    llm = ChatOpenAI(
        model=settings.openai_model,
        openai_api_key=settings.openai_api_key,
        openai_api_base=settings.openai_base_url,
        temperature=0,
        streaming=True,
    )

    # ── 创建 Agent（LangGraph）──
    agent = create_agent(
        model=llm,
        tools=all_tools,
        system_prompt=REACT_SYSTEM_PROMPT,
        debug=settings.agent_verbose,
    )

    logger.info("Agent 构建完成: %d 个工具", len(all_tools))
    return agent
