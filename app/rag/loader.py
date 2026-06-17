"""文档加载 & 分块。"""

from __future__ import annotations

import os
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def load_document(file_path: str | Path) -> list[Document]:
    """根据后缀加载 PDF / TXT，返回 Document 列表。"""
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        from langchain_community.document_loaders import PyPDFLoader
        loader = PyPDFLoader(str(file_path))
    elif suffix in (".txt", ".md"):
        from langchain_community.document_loaders import TextLoader
        loader = TextLoader(str(file_path), encoding="utf-8")
    else:
        raise ValueError(f"不支持的文件格式: {suffix}")

    docs = loader.load()
    logger.info("加载文件 %s → %d 页/段", file_path.name, len(docs))
    return docs


def split_documents(
    docs: list[Document],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[Document]:
    """将文档切分为可嵌入的小块。"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size or settings.rag_chunk_size,
        chunk_overlap=chunk_overlap or settings.rag_chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", "。", ".", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    # 给每个 chunk 打上来源 metadata
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i
    logger.info("分块完成: %d 块 (chunk_size=%d)", len(chunks), chunk_size or settings.rag_chunk_size)
    return chunks


def load_and_split(file_path: str | Path) -> list[Document]:
    """一步到位：加载 → 分块。"""
    docs = load_document(file_path)
    return split_documents(docs)
