"""诊断工具 — 模拟真实运维场景。"""

from __future__ import annotations

import json
import random

from langchain_core.tools import tool


@tool
def ping_host(host: str) -> str:
    """检测目标主机的网络连通性。输入主机名或 IP，返回 ping 结果。"""
    # 模拟：大部分成功，少量超时
    success = random.random() > 0.15
    latency = round(random.uniform(0.5, 120.0), 2) if success else None
    result = {
        "host": host,
        "reachable": success,
        "latency_ms": latency,
        "packet_loss": "0%" if success else "100%",
    }
    return json.dumps(result, ensure_ascii=False)


@tool
def query_service_log(service_name: str, keyword: str = "ERROR") -> str:
    """查询指定服务的日志，按关键词过滤。返回最近的匹配日志条目。"""
    # 模拟日志条目
    mock_logs = {
        "database": [
            {"timestamp": "2026-06-18T10:23:15Z", "level": "ERROR", "message": "Connection pool exhausted, active=95/100"},
            {"timestamp": "2026-06-18T10:23:16Z", "level": "WARN", "message": "Query timeout after 30s on replica-2"},
            {"timestamp": "2026-06-18T10:24:01Z", "level": "ERROR", "message": "Replication lag exceeded threshold: 120s"},
        ],
        "api-gateway": [
            {"timestamp": "2026-06-18T10:22:00Z", "level": "ERROR", "message": "Upstream 503 from auth-service"},
            {"timestamp": "2026-06-18T10:22:05Z", "level": "WARN", "message": "Rate limit triggered for client 192.168.1.50"},
        ],
        "auth-service": [
            {"timestamp": "2026-06-18T10:21:30Z", "level": "ERROR", "message": "Redis connection refused: ECONNREFUSED 10.0.0.5:6379"},
            {"timestamp": "2026-06-18T10:21:31Z", "level": "FATAL", "message": "Service degraded, falling back to in-memory cache"},
        ],
    }
    key = service_name.lower().replace(" ", "-")
    logs = mock_logs.get(key, [{"timestamp": "N/A", "level": "INFO", "message": f"No logs found for service '{service_name}'"}])
    filtered = [entry for entry in logs if keyword.upper() in entry.get("level", "") or keyword.upper() in entry.get("message", "").upper()]
    if not filtered:
        filtered = logs[:3]
    return json.dumps({"service": service_name, "keyword": keyword, "matches": len(filtered), "logs": filtered}, ensure_ascii=False)


@tool
def get_db_status(db_name: str) -> str:
    """获取数据库的连接状态和健康指标。"""
    # 模拟数据库状态
    active = random.randint(60, 98)
    max_conn = 100
    result = {
        "database": db_name,
        "status": "healthy" if active < 90 else "warning" if active < 95 else "critical",
        "active_connections": active,
        "max_connections": max_conn,
        "usage_pct": f"{active}%",
        "replication_lag_s": round(random.uniform(0, 5), 1),
        "uptime_hours": random.randint(100, 8000),
    }
    return json.dumps(result, ensure_ascii=False)


# 导出工具列表
DIAGNOSTIC_TOOLS = [ping_host, query_service_log, get_db_status]
