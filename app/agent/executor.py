"""Agent 执行器 — 适配 LangGraph create_agent 返回的 CompiledStateGraph。"""

from __future__ import annotations

from typing import Any, AsyncGenerator

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

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
) -> AsyncGenerator[dict[str, Any], None]:
    """流式执行 Agent，yield 每一步的事件。

    事件格式:
    - {"event": "action", "data": {"tool": ..., "input": ...}}
    - {"event": "observation", "data": {"output": ...}}
    - {"event": "answer", "data": {"output": ...}}
    - {"event": "error", "data": {"message": ...}}
    """
    input_msg = {"messages": [HumanMessage(content=user_message)]}
    final_answer = None

    try:
        # 使用 astream 获取每一步的更新
        async for event in agent.astream(input_msg, stream_mode="updates"):
            for node_name, node_output in event.items():
                if node_name in ("__start__", "__end__"):
                    continue

                messages = node_output.get("messages", [])
                for msg in messages:
                    if isinstance(msg, AIMessage):
                        tool_calls = _extract_tool_calls(msg)
                        if tool_calls:
                            for tc in tool_calls:
                                yield {
                                    "event": "action",
                                    "data": {
                                        "tool": tc["tool"],
                                        "input": tc["input"],
                                    },
                                }
                        elif msg.content:
                            final_answer = msg.content

                    elif isinstance(msg, ToolMessage):
                        yield {
                            "event": "observation",
                            "data": {"output": msg.content},
                        }

    except Exception as e:
        logger.error("Agent 流式执行异常: %s", e)
        yield {"event": "error", "data": {"message": str(e)}}
        return

    # 输出最终回答
    if final_answer:
        yield {"event": "answer", "data": {"output": final_answer}}
    else:
        # 兜底：重新调用一次取最终结果
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
