"""对话接口 — SSE 流式输出 + 对话历史。"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.schemas.models import ChatRequest
from app.agent.memory import add_message, get_langchain_messages
from app.utils.sse import sse_event
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/chat")
async def chat(request: Request, body: ChatRequest):
    """SSE 流式对话接口，支持多轮上下文。"""
    agent = request.app.state.agent
    if agent is None:
        return StreamingResponse(
            iter([sse_event("error", {"message": "Agent 未初始化"})]),
            media_type="text/event-stream",
        )

    from app.agent.executor import stream_agent_run

    # 保存用户消息到历史
    add_message(body.session_id, "user", body.message)
    # 获取历史上下文
    history = get_langchain_messages(body.session_id)

    async def event_generator():
        final_answer = ""
        try:
            async for event in stream_agent_run(agent, body.message, history=history):
                yield sse_event(event["event"], event["data"])
                # 收集最终回答
                if event["event"] == "answer":
                    final_answer = event["data"].get("output", "")
        except Exception as e:
            logger.error("对话流异常: %s", e)
            yield sse_event("error", {"message": str(e)})
        finally:
            # 保存助手回答到历史
            if final_answer:
                add_message(body.session_id, "assistant", final_answer)
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


@router.get("/history/{session_id}")
async def get_history(session_id: str):
    """获取指定 session 的对话历史。"""
    from app.agent.memory import get_history as _get_history
    return {"session_id": session_id, "messages": _get_history(session_id)}


@router.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """清除指定 session 的对话历史。"""
    from app.agent.memory import clear_history as _clear_history
    _clear_history(session_id)
    return {"message": "历史已清除", "session_id": session_id}
