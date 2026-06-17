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
        )
    return _embeddings_instance
