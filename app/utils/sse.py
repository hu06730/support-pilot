"""SSE 事件格式化辅助。"""

from __future__ import annotations

import json
from typing import Any


def sse_event(event: str, data: dict[str, Any] | str) -> str:
    """构造一条 SSE 消息。"""
    payload = json.dumps(data, ensure_ascii=False) if isinstance(data, dict) else data
    return f"event: {event}\ndata: {payload}\n\n"
