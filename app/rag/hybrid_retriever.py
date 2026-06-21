"""混合检索器 — 向量 + BM25 + RRF 融合 + Rerank + Query 扩展。"""

from __future__ import annotations

from langchain_core.documents import Document

from app.rag.vectorstore import get_vectorstore
from app.rag.bm25 import bm25_cache
from app.rag.intent import classify_intent
from app.rag.reranker import keyword_rerank
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
    use_query_expansion: bool = False,
) -> list[Document]:
    """混合检索：向量相似度 + BM25 关键词 + RRF 融合。

    Args:
        query: 查询文本
        top_k: 返回结果数
        vector_weight: 向量检索权重（None 则自动意图分类）
        bm25_weight: BM25 检索权重（None 则自动意图分类）
        use_query_expansion: 是否启用 Query 扩展（异步，需要 event loop）

    Returns:
        融合排序后的 Document 列表
    """
    k = top_k or settings.rag_top_k

    # Query 扩展（可选）
    queries = [query]
    if use_query_expansion:
        try:
            import asyncio
            from app.rag.query_expansion import expand_query
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 已在 async 上下文中，用 sync 方式调用
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    queries = pool.submit(lambda: asyncio.run(expand_query(query, n=2))).result()
            else:
                queries = loop.run_until_complete(expand_query(query, n=2))
        except Exception as e:
            logger.warning("Query 扩展失败，使用原始查询: %s", e)
            queries = [query]

    # 意图分类 → 动态权重
    if vector_weight is None or bm25_weight is None:
        intent = classify_intent(query)
        vw, bw = intent.vector_weight, intent.bm25_weight
        logger.info("意图分类: %s, 向量权重=%.1f, BM25权重=%.1f", intent.intent, vw, bw)
    else:
        vw, bw = vector_weight, bm25_weight

    # ── 向量检索（支持多 Query）──
    vs = get_vectorstore()
    vector_results: dict[str, tuple[Document, int]] = {}
    for q in queries:
        vector_docs = vs.similarity_search_with_relevance_scores(q, k=k * 2)
        for rank, (doc, _score) in enumerate(vector_docs):
            doc_key = doc.page_content[:100]
            if doc_key not in vector_results:
                vector_results[doc_key] = (doc, rank)

    # ── BM25 检索（支持多 Query）──
    collection_name = settings.chroma_collection_name
    corpus, doc_ids = _build_bm25_index(collection_name)
    bm25_index = bm25_cache.get_or_build(collection_name, corpus, doc_ids)
    bm25_results: dict[str, tuple[Document, int]] = {}
    for q in queries:
        bm25_hits = bm25_index.search(q, top_k=k * 2)
        for rank, (doc_id, _score) in enumerate(bm25_hits):
            try:
                result = vs._collection.get(ids=[doc_id], include=["documents", "metadatas"])
                if result["documents"]:
                    doc = Document(
                        page_content=result["documents"][0],
                        metadata=result["metadatas"][0] if result["metadatas"] else {},
                    )
                    doc_key = doc.page_content[:100]
                    if doc_key not in bm25_results:
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
    fused_results = [doc for doc, _score in sorted_results]

    # Rerank 重排序
    results = keyword_rerank(query, fused_results, top_k=k)

    logger.info("混合检索完成: 向量=%d, BM25=%d, 融合=%d, rerank后=%d",
                len(vector_results), len(bm25_results), len(fused_results), len(results))
    return results


def vector_only_search(query: str, top_k: int | None = None) -> list[Document]:
    """纯向量检索。"""
    vs = get_vectorstore()
    k = top_k or settings.rag_top_k
    return vs.similarity_search(query, k=k)
