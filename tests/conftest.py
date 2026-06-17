"""共享 fixtures — mock LLM、TestClient、临时 Chroma。"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# 确保项目根目录在 sys.path 中
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 设置测试环境变量（避免调用真实 OpenAI API）
os.environ.setdefault("OPENAI_API_KEY", "sk-test-fake-key")
os.environ.setdefault("CHROMA_PERSIST_DIR", "/tmp/test_chroma")
os.environ.setdefault("MCP_SERVER_URLS", "")


@pytest.fixture
def tmp_chroma_dir(tmp_path):
    """提供临时 Chroma 持久化目录。"""
    chroma_dir = tmp_path / "chroma"
    chroma_dir.mkdir()
    os.environ["CHROMA_PERSIST_DIR"] = str(chroma_dir)
    yield str(chroma_dir)
    os.environ.pop("CHROMA_PERSIST_DIR", None)


@pytest.fixture
def sample_text_file(tmp_path):
    """创建一个测试用 TXT 文件。"""
    f = tmp_path / "test_doc.txt"
    f.write_text(
        "# 数据库排障指南\n\n"
        "## 连接超时\n"
        "1. 检查连接池配置\n"
        "2. 确认数据库服务是否正常运行\n"
        "3. 检查网络连通性\n\n"
        "## 性能优化\n"
        "1. 添加索引\n"
        "2. 优化查询语句\n",
        encoding="utf-8",
    )
    return f


@pytest.fixture
def mock_mcp_provider():
    """Mock MCPProvider，返回空工具列表。"""
    provider = AsyncMock()
    provider.get_all_tools.return_value = []
    provider.health_check.return_value = {}
    return provider
