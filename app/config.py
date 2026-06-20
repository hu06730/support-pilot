"""集中配置 — 通过环境变量 / .env 文件加载。"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根目录（config.py 所在目录的上一级）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.exists() else "",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── OpenAI / 兼容 API ──
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    # ── Chroma ──
    chroma_persist_dir: str = str(_PROJECT_ROOT / "data" / "chroma")
    chroma_collection_name: str = "support_docs"

    # ── MCP ──
    mcp_server_urls: str = "http://mcp-server:5000"
    mcp_connect_timeout: int = 10
    mcp_tool_prefix: bool = True

    # ── FastAPI ──
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # ── Agent ──
    agent_max_iterations: int = 10
    agent_verbose: bool = True

    # ── RAG ──
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 200
    rag_top_k: int = 4


settings = Settings()
