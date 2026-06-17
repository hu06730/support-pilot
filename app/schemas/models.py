"""请求 / 响应 Pydantic 模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── Chat ──

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="用户消息")
    session_id: str = Field(default="default", description="会话 ID")


class ChatResponse(BaseModel):
    answer: str
    steps: list[dict] = Field(default_factory=list, description="Agent 推理步骤")


# ── Upload ──

class UploadResponse(BaseModel):
    filename: str
    chunks: int
    doc_id: str
    message: str = "文档上传并索引成功"
