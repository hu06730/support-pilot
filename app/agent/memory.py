"""对话历史管理 — 内存存储，按 session_id 隔离。"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from app.utils.logger import get_logger

logger = get_logger(__name__)

# session_id → list of (role, content, timestamp)
_history: dict[str, list[dict]] = defaultdict(list)

MAX_HISTORY_TURNS = 10  # 最多保留最近 N 轮


def add_message(session_id: str, role: str, content: str) -> None:
    """添加一条消息到历史。"""
    _history[session_id].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat(),
    })
    # 超出限制时裁剪
    if len(_history[session_id]) > MAX_HISTORY_TURNS * 2:
        _history[session_id] = _history[session_id][-MAX_HISTORY_TURNS * 2:]


def get_history(session_id: str) -> list[dict]:
    """获取指定 session 的对话历史。"""
    return list(_history.get(session_id, []))


def get_langchain_messages(session_id: str) -> list[BaseMessage]:
    """将对话历史转为 LangChain 消息格式（传给 Agent）。"""
    messages = []
    for entry in _history.get(session_id, []):
        if entry["role"] == "user":
            messages.append(HumanMessage(content=entry["content"]))
        elif entry["role"] == "assistant":
            messages.append(AIMessage(content=entry["content"]))
    return messages


def clear_history(session_id: str) -> None:
    """清除指定 session 的历史。"""
    _history.pop(session_id, None)


def get_all_sessions() -> list[str]:
    """列出所有 session_id。"""
    return list(_history.keys())
