"""对话接口测试。"""

import os
from unittest.mock import patch, AsyncMock

import pytest

os.environ.setdefault("OPENAI_API_KEY", "sk-test")


class TestChatEndpoint:
    def test_chat_returns_sse(self):
        from fastapi.testclient import TestClient

        with patch("app.rag.embeddings.OpenAIEmbeddings"), \
             patch("app.agent.react_agent.build_agent", new_callable=AsyncMock) as mock_build:
            mock_executor = AsyncMock()
            mock_executor.ainvoke.return_value = {"output": "测试回答"}
            mock_build.return_value = mock_executor

            from app.main import app
            app.state.agent_executor = mock_executor

            client = TestClient(app)
            resp = client.post(
                "/chat",
                json={"message": "测试问题"},
                headers={"Accept": "text/event-stream"},
            )
            assert resp.status_code == 200
