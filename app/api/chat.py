"""对话接口 — SSE 流式输出。"""

from __future__ import annotations

import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.schemas.models import ChatRequest
from app.utils.sse import sse_event
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/chat")
async def chat(request: Request, body: ChatRequest):
    """SSE 流式对话接口。"""
    # 从 app state 获取 agent executor
    agent_executor = request.app.state.agent_executor
    if agent_executor is None:
        return StreamingResponse(
            iter([sse_event("error", {"message": "Agent 未初始化"})]),
            media_type="text/event-stream",
        )

    from app.agent.executor import stream_agent_run

    async def event_generator():
        try:
            async for event in stream_agent_run(agent_executor, body.message):
                yield sse_event(event["event"], event["data"])
        except Exception as e:
            logger.error("对话流异常: %s", e)
            yield sse_event("error", {"message": str(e)})
        finally:
            yield sse_event("done", {"status": "complete"})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
