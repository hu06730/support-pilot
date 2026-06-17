"""RAG 文档检索工具 — 包装为 LangChain Tool。"""

from __future__ import annotations

from langchain_core.tools import tool

from app.rag.vectorstore import get_retriever
from app.utils.logger import get_logger

logger = get_logger(__name__)


@tool
def document_search(query: str) -> str:
    """从技术文档库中检索与问题相关的文档片段。当用户提问涉及技术问题时，优先调用此工具查找文档。"""
    retriever = get_retriever()
    docs = retriever.invoke(query)

    if not docs:
        return "未找到相关文档片段。"

    results = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", "N/A")
        results.append(f"[片段 {i}] (来源: {source}, 页: {page})\n{doc.page_content}")

    logger.info("文档检索: query='%s', 返回 %d 个片段", query, len(results))
    return "\n\n---\n\n".join(results)


# 导出
RAG_TOOLS = [document_search]
