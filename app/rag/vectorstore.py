"""Chroma 向量数据库管理。"""

from __future__ import annotations

from pathlib import Path

import chromadb
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from app.config import settings
from app.rag.embeddings import get_embeddings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_vectorstore: Chroma | None = None


def get_vectorstore() -> Chroma:
    """返回单例 Chroma 实例（持久化模式）。"""
    global _vectorstore
    if _vectorstore is None:
        persist_dir = Path(settings.chroma_persist_dir)
        persist_dir.mkdir(parents=True, exist_ok=True)

        _vectorstore = Chroma(
            collection_name=settings.chroma_collection_name,
            embedding_function=get_embeddings(),
            persist_directory=str(persist_dir),
        )
        logger.info("Chroma 初始化完成: dir=%s, collection=%s", persist_dir, settings.chroma_collection_name)
    return _vectorstore


def add_documents(chunks: list[Document]) -> list[str]:
    """将分块写入 Chroma，返回文档 ID 列表。"""
    vs = get_vectorstore()
    ids = vs.add_documents(chunks)
    logger.info("写入 %d 个文档块到 Chroma", len(ids))
    return ids


def get_retriever(top_k: int | None = None):
    """返回检索器。"""
    vs = get_vectorstore()
    return vs.as_retriever(search_kwargs={"k": top_k or settings.rag_top_k})


def reset_collection():
    """清空并重建 collection（用于 seed 脚本）。"""
    global _vectorstore
    client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    try:
        client.delete_collection(settings.chroma_collection_name)
        logger.info("已删除 collection: %s", settings.chroma_collection_name)
    except Exception:
        pass
    _vectorstore = None
    get_vectorstore()
    logger.info("Collection 已重建")
