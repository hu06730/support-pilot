"""结构化日志 — JSON 格式 + 请求 ID 追踪。"""

from __future__ import annotations

import logging
import sys
import uuid
from contextvars import ContextVar

from app.config import settings

# 请求级别的 trace_id（通过 ContextVar 实现协程安全）
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="-")


class StructuredFormatter(logging.Formatter):
    """JSON 结构化日志格式。"""

    def format(self, record: logging.LogRecord) -> str:
        trace_id = getattr(record, "trace_id", trace_id_var.get("-"))
        return (
            f'{{"time":"{self.formatTime(record, self.datefmt)}",'
            f'"level":"{record.levelname}",'
            f'"logger":"{record.name}",'
            f'"trace_id":"{trace_id}",'
            f'"message":"{record.getMessage()}"}}'
        )


def get_logger(name: str) -> logging.Logger:
    """获取结构化日志器。"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter(datefmt="%Y-%m-%dT%H:%M:%S"))
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    return logger


def generate_trace_id() -> str:
    """生成唯一请求 ID。"""
    return uuid.uuid4().hex[:16]
