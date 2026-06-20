"""create_jira_ticket MCP 工具。"""

from __future__ import annotations

import random


async def create_jira_ticket(title: str, description: str, priority: str = "Medium") -> dict:
    """创建 Jira 工单，返回工单信息。"""
    ticket_key = f"PROJ-{random.randint(1000, 9999)}"
    return {
        "ticket_key": ticket_key,
        "title": title,
        "description": description,
        "priority": priority,
        "status": "Open",
        "url": f"https://jira.example.com/browse/{ticket_key}",
    }
