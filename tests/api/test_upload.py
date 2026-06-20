"""上传接口测试。"""

import os
from unittest.mock import patch

import pytest

# 需要先设置环境变量再 import app
os.environ.setdefault("OPENAI_API_KEY", "sk-test")


class TestUploadEndpoint:
    """上传端点测试（mock Chroma + OpenAI）。"""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        os.environ["CHROMA_PERSIST_DIR"] = str(tmp_path / "chroma")
        yield
        os.environ.pop("CHROMA_PERSIST_DIR", None)

    def test_upload_rejects_bad_extension(self):
        from fastapi.testclient import TestClient

        with patch("app.rag.embeddings.OpenAIEmbeddings"):
            from app.main import app
            client = TestClient(app)
            resp = client.post(
                "/upload",
                files={"file": ("test.exe", b"binary content", "application/octet-stream")},
            )
            assert resp.status_code == 400
            assert "不支持" in resp.json()["detail"]
