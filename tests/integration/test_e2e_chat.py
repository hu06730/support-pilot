"""端到端测试：上传 → 提问 → Agent 回答。"""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# 确保项目根目录在 sys.path 中
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

os.environ.setdefault("OPENAI_API_KEY", "sk-test-fake-key")
os.environ.setdefault("CHROMA_PERSIST_DIR", "/tmp/test_chroma")
os.environ.setdefault("MCP_SERVER_URLS", "")


class TestHealthEndpoint:
    """健康检查端点测试。"""

    def test_health_returns_ok(self):
        from fastapi.testclient import TestClient

        with patch("app.rag.embeddings.OpenAIEmbeddings"):
            from app.main import app
            client = TestClient(app)
            resp = client.get("/health")
            assert resp.status_code == 200
            assert resp.json()["status"] == "ok"


class TestDocumentsEndpoint:
    """文档管理端点测试。"""

    def test_documents_returns_list(self):
        from fastapi.testclient import TestClient

        with patch("app.rag.embeddings.OpenAIEmbeddings"):
            from app.main import app
            client = TestClient(app)
            resp = client.get("/documents")
            assert resp.status_code == 200
            data = resp.json()
            assert "documents" in data
            assert "total" in data


class TestMcpEndpoint:
    """MCP 管理端点测试。"""

    def test_mcp_status(self):
        from fastapi.testclient import TestClient

        with patch("app.rag.embeddings.OpenAIEmbeddings"):
            from app.main import app
            client = TestClient(app)
            resp = client.get("/mcp/status")
            assert resp.status_code == 200
            data = resp.json()
            assert "connected" in data
            assert "servers" in data
            assert "tools_count" in data


class TestHistoryEndpoint:
    """对话历史端点测试。"""

    def test_get_history_empty(self):
        from fastapi.testclient import TestClient

        with patch("app.rag.embeddings.OpenAIEmbeddings"):
            from app.main import app
            client = TestClient(app)
            resp = client.get("/history/test-session")
            assert resp.status_code == 200
            data = resp.json()
            assert data["session_id"] == "test-session"
            assert isinstance(data["messages"], list)

    def test_clear_history(self):
        from fastapi.testclient import TestClient

        with patch("app.rag.embeddings.OpenAIEmbeddings"):
            from app.main import app
            client = TestClient(app)
            resp = client.delete("/history/test-session")
            assert resp.status_code == 200
            assert resp.json()["message"] == "历史已清除"


class TestChatEndpoint:
    """对话端点测试（mock Agent）。"""

    def test_chat_without_agent_returns_error(self):
        """Agent 未初始化时返回错误。"""
        from fastapi.testclient import TestClient

        with patch("app.rag.embeddings.OpenAIEmbeddings"):
            from app.main import app
            app.state.agent = None
            client = TestClient(app)
            resp = client.post(
                "/chat",
                json={"message": "测试", "session_id": "test"},
            )
            assert resp.status_code == 200
            assert "Agent 未初始化" in resp.text


class TestDiagnosticTools:
    """诊断工具单测。"""

    def test_ping_host_returns_json(self):
        import json
        from app.tools.diagnostic import ping_host

        result = ping_host.invoke("test-host")
        data = json.loads(result)
        assert "host" in data
        assert "reachable" in data

    def test_get_db_status_returns_json(self):
        import json
        from app.tools.diagnostic import get_db_status

        result = get_db_status.invoke("test-db")
        data = json.loads(result)
        assert "database" in data
        assert "status" in data
        assert data["status"] in ("healthy", "warning", "critical")

    def test_query_service_log_returns_json(self):
        import json
        from app.tools.diagnostic import query_service_log

        result = query_service_log.invoke({"service_name": "database", "keyword": "ERROR"})
        data = json.loads(result)
        assert "service" in data
        assert data["service"] == "database"


class TestIntentClassifier:
    """意图分类测试。"""

    def test_factual_lookup(self):
        from app.rag.intent import classify_intent

        w = classify_intent("死锁的定义是什么")
        assert w.intent == "factual_lookup"
        assert w.bm25_weight > w.vector_weight

    def test_conceptual(self):
        from app.rag.intent import classify_intent

        w = classify_intent("为什么会出现死锁")
        assert w.intent == "conceptual"
        assert w.vector_weight > w.bm25_weight

    def test_procedural(self):
        from app.rag.intent import classify_intent

        w = classify_intent("如何解决死锁问题")
        assert w.intent == "procedural"
        assert w.vector_weight == w.bm25_weight

    def test_default(self):
        from app.rag.intent import classify_intent

        w = classify_intent("数据库")
        assert w.intent == "default"
        assert w.vector_weight == 0.5
        assert w.bm25_weight == 0.5


class TestBM25Index:
    """BM25 索引测试。"""

    def test_empty_corpus(self):
        from app.rag.bm25 import BM25Index

        index = BM25Index([], [])
        results = index.search("test", top_k=5)
        assert results == []

    def test_search_returns_results(self):
        from app.rag.bm25 import BM25Index

        corpus = ["数据库连接超时", "进程死锁问题", "网络延迟过高"]
        doc_ids = ["doc1", "doc2", "doc3"]
        index = BM25Index(corpus, doc_ids)
        results = index.search("数据库", top_k=3)
        assert len(results) > 0
        assert results[0][0] == "doc1"


class TestSSEFormatter:
    """SSE 格式化测试。"""

    def test_sse_event_format(self):
        from app.utils.sse import sse_event

        event = sse_event("message", {"content": "hello"})
        assert "event: message" in event
        assert '"content": "hello"' in event
        assert event.endswith("\n\n")
