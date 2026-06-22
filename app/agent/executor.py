"""Agent 执行器 — 支持 token 级流式输出 + 对话历史。"""

from __future__ import annotations

from typing import Any, AsyncGenerator

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, AIMessageChunk

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _extract_tool_calls(ai_msg: AIMessage) -> list[dict]:
    """从 AIMessage 中提取工具调用信息。"""
    calls = []
    if hasattr(ai_msg, "tool_calls") and ai_msg.tool_calls:
        for tc in ai_msg.tool_calls:
            calls.append({
                "tool": tc.get("name", "unknown"),
                "input": tc.get("args", {}),
            })
    return calls


async def stream_agent_run(
    agent,
    user_message: str,
    history: list[BaseMessage] | None = None,
) -> AsyncGenerator[dict[str, Any], None]:
    """流式执行 Agent，支持 token 级输出。

    事件格式:
    - {"event": "token", "data": {"content": "..."}}         # LLM 逐 token
    - {"event": "action", "data": {"tool": ..., "input": ...}}  # 工具调用
    - {"event": "observation", "data": {"output": ...}}        # 工具结果
    - {"event": "answer", "data": {"output": ...}}             # 最终回答
    - {"event": "error", "data": {"message": ...}}             # 错误
    """
    messages: list[BaseMessage] = list(history or [])
    messages.append(HumanMessage(content=user_message))
    input_msg = {"messages": messages}

    final_answer = None

    try:
        # 使用 astream_events 获取 token 级流式输出
        async for event in agent.astream_events(
            input_msg,
            version="v2",
            recursion_limit=settings.agent_max_iterations,
        ):
            kind = event.get("event", "")

            # LLM 生成的 token
            if kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if isinstance(chunk, AIMessageChunk) and chunk.content:
                    yield {"event": "token", "data": {"content": chunk.content}}

            # 工具调用开始
            elif kind == "on_tool_start":
                tool_name = event.get("name", "unknown")
                tool_input = event.get("data", {}).get("input", {})
                yield {
                    "event": "action",
                    "data": {"tool": tool_name, "input": tool_input},
                }

            # 工具调用结束
            elif kind == "on_tool_end":
                output = event.get("data", {}).get("output", "")
                if isinstance(output, str):
                    yield {"event": "observation", "data": {"output": output}}
                elif isinstance(output, list):
                    # MCP 工具返回格式
                    text_parts = [item.get("text", "") for item in output if isinstance(item, dict)]
                    yield {"event": "observation", "data": {"output": "\n".join(text_parts)}}

            # 完整的 AIMessage（用于提取最终回答）
            elif kind == "on_chat_model_end":
                msg = event.get("data", {}).get("output")
                if isinstance(msg, AIMessage) and msg.content and not _extract_tool_calls(msg):
                    final_answer = msg.content

    except Exception as e:
        logger.error("Agent 流式执行异常: %s", e)
        yield {"event": "error", "data": {"message": str(e)}}
        return

    # 输出最终回答
    if final_answer:
        yield {"event": "answer", "data": {"output": final_answer}}
    else:
        try:
            result = await agent.ainvoke(input_msg)
            last_messages = result.get("messages", [])
            for msg in reversed(last_messages):
                if isinstance(msg, AIMessage) and msg.content:
                    yield {"event": "answer", "data": {"output": msg.content}}
                    return
            yield {"event": "answer", "data": {"output": "未能生成回答。"}}
        except Exception as e:
            logger.error("Agent 兜底调用失败: %s", e)
            yield {"event": "error", "data": {"message": str(e)}}
