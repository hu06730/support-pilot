"""混合检索器 — 向量 + BM25 + RRF 融合。"""

from __future__ import annotations

from langchain_core.documents import Document

from app.rag.vectorstore import get_vectorstore
from app.rag.bm25 import bm25_cache
from app.rag.intent import classify_intent, IntentWeights
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# RRF 常数
RRF_K = 60


def _rrf_score(rank: int, weight: float) -> float:
    """RRF 评分公式：weight / (k + rank + 1)"""
    return weight / (RRF_K + rank + 1)


def _build_bm25_index(collection_name: str) -> tuple[list[str], list[str]]:
    """从 Chroma collection 中提取所有文档文本和 ID 构建 BM25 索引。"""
    vs = get_vectorstore()
    collection = vs._collection
    results = collection.get(include=["documents"])
    doc_ids = results["ids"]
    corpus = results["documents"]
    return corpus, doc_ids


def hybrid_search(
    query: str,
    top_k: int | None = None,
    vector_weight: float | None = None,
    bm25_weight: float | None = None,
) -> list[Document]:
    """混合检索：向量相似度 + BM25 关键词 + RRF 融合。

    Args:
        query: 查询文本
        top_k: 返回结果数
        vector_weight: 向量检索权重（None 则自动意图分类）
        bm25_weight: BM25 检索权重（None 则自动意图分类）

    Returns:
        融合排序后的 Document 列表
    """
    k = top_k or settings.rag_top_k

    # 意图分类 → 动态权重
    if vector_weight is None or bm25_weight is None:
        intent = classify_intent(query)
        vw, bw = intent.vector_weight, intent.bm25_weight
        logger.info("意图分类: %s, 向量权重=%.1f, BM25权重=%.1f", intent.intent, vw, bw)
    else:
        vw, bw = vector_weight, bm25_weight

    # ── 向量检索 ──
    vs = get_vectorstore()
    vector_docs = vs.similarity_search_with_relevance_scores(query, k=k * 2)
    vector_results: dict[str, tuple[Document, int]] = {}
    for rank, (doc, _score) in enumerate(vector_docs):
        doc_key = doc.page_content[:100]  # 用前 100 字符作为去重 key
        vector_results[doc_key] = (doc, rank)

    # ── BM25 检索 ──
    collection_name = settings.chroma_collection_name
    corpus, doc_ids = _build_bm25_index(collection_name)
    bm25_index = bm25_cache.get_or_build(collection_name, corpus, doc_ids)
    bm25_hits = bm25_index.search(query, top_k=k * 2)

    bm25_results: dict[str, tuple[Document, int]] = {}
    for rank, (doc_id, _score) in enumerate(bm25_hits):
        # 从 Chroma 获取文档内容
        try:
            result = vs._collection.get(ids=[doc_id], include=["documents", "metadatas"])
            if result["documents"]:
                doc = Document(
                    page_content=result["documents"][0],
                    metadata=result["metadatas"][0] if result["metadatas"] else {},
                )
                doc_key = doc.page_content[:100]
                bm25_results[doc_key] = (doc, rank)
        except Exception:
            continue

    # ── RRF 融合 ──
    rrf_scores: dict[str, tuple[Document, float]] = {}

    for doc_key, (doc, rank) in vector_results.items():
        score = _rrf_score(rank, vw)
        if doc_key in rrf_scores:
            rrf_scores[doc_key] = (doc, rrf_scores[doc_key][1] + score)
        else:
            rrf_scores[doc_key] = (doc, score)

    for doc_key, (doc, rank) in bm25_results.items():
        score = _rrf_score(rank, bw)
        if doc_key in rrf_scores:
            rrf_scores[doc_key] = (doc, rrf_scores[doc_key][1] + score)
        else:
            rrf_scores[doc_key] = (doc, score)

    # 排序取 top_k
    sorted_results = sorted(rrf_scores.values(), key=lambda x: x[1], reverse=True)[:k]
    results = [doc for doc, _score in sorted_results]

    logger.info("混合检索完成: 向量=%d, BM25=%d, 融合后=%d", len(vector_results), len(bm25_results), len(results))
    return results


def vector_only_search(query: str, top_k: int | None = None) -> list[Document]:
    """纯向量检索。"""
    vs = get_vectorstore()
    k = top_k or settings.rag_top_k
    return vs.similarity_search(query, k=k)
