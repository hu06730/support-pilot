"""对话历史管理 — SQLite 持久化。"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# 数据库路径
_DB_PATH = Path(settings.chroma_persist_dir).parent / "conversations.db"

MAX_HISTORY_TURNS = 10  # 最多保留最近 N 轮


def _get_conn() -> sqlite3.Connection:
    """获取数据库连接（自动创建表）。"""
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_session ON messages(session_id)
    """)
    conn.commit()
    return conn


def add_message(session_id: str, role: str, content: str) -> None:
    """添加一条消息到历史。"""
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()

        # 裁剪超出限制的历史
        conn.execute("""
            DELETE FROM messages WHERE session_id = ? AND id NOT IN (
                SELECT id FROM messages WHERE session_id = ?
                ORDER BY id DESC LIMIT ?
            )
        """, (session_id, session_id, MAX_HISTORY_TURNS * 2))
        conn.commit()
    finally:
        conn.close()


def get_history(session_id: str) -> list[dict]:
    """获取指定 session 的对话历史。"""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT role, content, created_at FROM messages WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_langchain_messages(session_id: str) -> list[BaseMessage]:
    """将对话历史转为 LangChain 消息格式。"""
    messages = []
    for entry in get_history(session_id):
        if entry["role"] == "user":
            messages.append(HumanMessage(content=entry["content"]))
        elif entry["role"] == "assistant":
            messages.append(AIMessage(content=entry["content"]))
    return messages


def clear_history(session_id: str) -> None:
    """清除指定 session 的历史。"""
    conn = _get_conn()
    try:
        conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        conn.commit()
    finally:
        conn.close()


def get_all_sessions() -> list[str]:
    """列出所有 session_id。"""
    conn = _get_conn()
    try:
        rows = conn.execute("SELECT DISTINCT session_id FROM messages").fetchall()
        return [row["session_id"] for row in rows]
    finally:
        conn.close()
