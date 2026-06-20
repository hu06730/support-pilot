"""对话接口测试。"""

import os
from unittest.mock import AsyncMock

os.environ.setdefault("OPENAI_API_KEY", "sk-test")


class TestChatEndpoint:
    def test_chat_returns_sse(self):
        from fastapi.testclient import TestClient
        from app.main import app

        mock_agent = AsyncMock()
        mock_agent.astream_events.return_value = AsyncMock()
        app.state.agent = mock_agent

        client = TestClient(app)
        resp = client.post(
            "/chat",
            json={"message": "测试问题"},
            headers={"Accept": "text/event-stream"},
        )
        assert resp.status_code == 200
