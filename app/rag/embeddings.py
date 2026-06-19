"""OpenAI Embeddings 工厂。"""

from __future__ import annotations

from langchain_openai import OpenAIEmbeddings

from app.config import settings

_embeddings_instance: OpenAIEmbeddings | None = None


def get_embeddings() -> OpenAIEmbeddings:
    """返回单例 OpenAIEmbeddings 实例。"""
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key,
            openai_api_base=settings.openai_base_url,
            check_embedding_ctx_length=False,  # 兼容百炼等非标准 API
            chunk_size=10,  # 百炼 API 批量上限 10 条
        )
    return _embeddings_instance
