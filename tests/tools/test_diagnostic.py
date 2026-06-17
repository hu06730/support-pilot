"""诊断工具单元测试。"""

import json

from app.tools.diagnostic import ping_host, query_service_log, get_db_status


class TestPingHost:
    def test_returns_valid_json(self):
        result = ping_host.invoke("192.168.1.1")
        data = json.loads(result)
        assert "host" in data
        assert "reachable" in data
        assert data["host"] == "192.168.1.1"

    def test_reachable_is_bool(self):
        result = ping_host.invoke("example.com")
        data = json.loads(result)
        assert isinstance(data["reachable"], bool)


class TestQueryServiceLog:
    def test_known_service(self):
        result = query_service_log.invoke({"service_name": "database", "keyword": "ERROR"})
        data = json.loads(result)
        assert data["service"] == "database"
        assert data["matches"] > 0

    def test_unknown_service(self):
        result = query_service_log.invoke({"service_name": "nonexistent", "keyword": "ERROR"})
        data = json.loads(result)
        assert data["service"] == "nonexistent"


class TestGetDbStatus:
    def test_returns_status_fields(self):
        result = get_db_status.invoke("test_db")
        data = json.loads(result)
        assert "database" in data
        assert "status" in data
        assert "active_connections" in data
        assert data["database"] == "test_db"

    def test_status_is_valid(self):
        result = get_db_status.invoke("prod_db")
        data = json.loads(result)
        assert data["status"] in ("healthy", "warning", "critical")
