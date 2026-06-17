"""AgentExecutor 流式执行 + SSE 回调。"""

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncGenerator

from langchain.agents import AgentExecutor
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult

from app.utils.logger import get_logger

logger = get_logger(__name__)


class StreamingCallbackHandler(AsyncCallbackHandler):
    """将 Agent 的 Thought / Action / Observation 推入异步队列，供 SSE 消费。"""

    def __init__(self):
        self.queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()

    async def on_agent_action(self, action, **kwargs: Any) -> None:
        """Agent 决定调用工具时触发。"""
        await self.queue.put({
            "event": "action",
            "data": {
                "tool": action.tool,
                "input": action.tool_input,
                "log": action.log,
            },
        })

    async def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """工具执行完毕时触发。"""
        await self.queue.put({
            "event": "observation",
            "data": {"output": output},
        })

    async def on_agent_finish(self, finish, **kwargs: Any) -> None:
        """Agent 给出最终回答时触发。"""
        await self.queue.put({
            "event": "answer",
            "data": {"output": finish.return_values.get("output", "")},
        })
        await self.queue.put(None)  # 哨兵值，表示结束

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """LLM 流式 token（可选，用于细粒度流式）。"""
        pass

    async def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        logger.error("LLM 错误: %s", error)
        await self.queue.put({"event": "error", "data": {"message": str(error)}})
        await self.queue.put(None)


async def stream_agent_run(
    executor: AgentExecutor,
    user_message: str,
) -> AsyncGenerator[dict[str, Any], None]:
    """流式执行 Agent，yield 每一步的事件。"""
    handler = StreamingCallbackHandler()

    # 后台运行 Agent
    async def _run():
        try:
            result = await executor.ainvoke(
                {"input": user_message},
                config={"callbacks": [handler]},
            )
            # 如果 handler 没有触发 on_agent_finish（兜底）
            if handler.queue.empty():
                await handler.queue.put({
                    "event": "answer",
                    "data": {"output": result.get("output", "")},
                })
                await handler.queue.put(None)
        except Exception as e:
            logger.error("Agent 执行异常: %s", e)
            await handler.queue.put({"event": "error", "data": {"message": str(e)}})
            await handler.queue.put(None)

    task = asyncio.create_task(_run())

    try:
        while True:
            event = await handler.queue.get()
            if event is None:
                break
            yield event
    finally:
        if not task.done():
            task.cancel()
