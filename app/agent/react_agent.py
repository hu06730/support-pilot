"""ReAct Agent 组装 — 合并内置工具 + RAG 工具 + MCP 工具。"""

from __future__ import annotations

from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.config import settings
from app.tools.diagnostic import DIAGNOSTIC_TOOLS
from app.tools.rag_tool import RAG_TOOLS
from app.mcp.provider import MCPProvider
from app.agent.prompts import REACT_SYSTEM_PROMPT
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def build_agent(mcp_provider: MCPProvider) -> AgentExecutor:
    """组装完整的 ReAct Agent（内置 + RAG + MCP 工具）。"""

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
        temperature=0,
        streaming=True,
    )

    # ── Prompt（使用 ReAct 标准格式）──
    from langchain_core.prompts import PromptTemplate

    # ReAct 需要的工具描述字符串
    tool_desc = "\n".join(f"- {t.name}: {t.description}" for t in all_tools)
    tool_names_str = ", ".join(tool_names)

    react_prompt = PromptTemplate.from_template(
        REACT_SYSTEM_PROMPT + """

## 工具列表
{tools}

## 工具名称
{tool_names}

## 必须严格遵守以下格式（每一步都要完整输出）

Question: 用户的输入问题
Thought: 我需要思考下一步该做什么
Action: 工具名称
Action Input: 工具的输入参数
Observation: 工具返回的结果
... (Thought/Action/Action Input/Observation 可以重复多次)
Thought: 我现在知道最终答案了
Final Answer: 给用户的最终回答

## 开始！

Question: {input}
{agent_scratchpad}"""
    )

    # ── 创建 Agent ──
    agent = create_react_agent(
        llm=llm,
        tools=all_tools,
        prompt=react_prompt,
    )

    # ── 包装为 Executor ──
    executor = AgentExecutor(
        agent=agent,
        tools=all_tools,
        max_iterations=settings.agent_max_iterations,
        verbose=settings.agent_verbose,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )

    logger.info("ReAct Agent 构建完成: %d 个工具, max_iter=%d", len(all_tools), settings.agent_max_iterations)
    return executor
