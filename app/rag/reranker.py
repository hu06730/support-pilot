"""Rerank 重排序模块 — 对检索结果进行二次排序。"""

from __future__ import annotations

import re
from collections import Counter

from langchain_core.documents import Document

from app.utils.logger import get_logger

logger = get_logger(__name__)


def _tokenize(text: str) -> list[str]:
    """简单分词：中文按字，英文按空格。"""
    # 提取中文字符和英文单词
    chinese = re.findall(r'[一-鿿]', text)
    english = re.findall(r'[a-zA-Z]+', text.lower())
    return chinese + english


def keyword_rerank(
    query: str,
    documents: list[Document],
    top_k: int | None = None,
) -> list[Document]:
    """基于关键词重叠的轻量级 Rerank。

    计算查询与文档的关键词重叠度，重新排序。
    适用于没有外部 Rerank API 的场景。
    """
    if not documents:
        return []

    query_tokens = set(_tokenize(query))
    if not query_tokens:
        return documents

    scored_docs = []
    for doc in documents:
        doc_tokens = _tokenize(doc.page_content)
        doc_token_set = set(doc_tokens)

        # 计算重叠度
        overlap = query_tokens & doc_token_set
        overlap_ratio = len(overlap) / len(query_tokens) if query_tokens else 0

        # 计算查询词在文档中的出现频率
        doc_counter = Counter(doc_tokens)
        freq_score = sum(doc_counter.get(t, 0) for t in query_tokens)
        freq_norm = freq_score / (len(doc_tokens) + 1)  # 归一化

        # 综合得分
        score = overlap_ratio * 0.6 + freq_norm * 0.4
        scored_docs.append((doc, score))

    # 按得分降序排列
    scored_docs.sort(key=lambda x: x[1], reverse=True)

    result = [doc for doc, _ in scored_docs]
    if top_k:
        result = result[:top_k]

    logger.info("Rerank: %d 文档重排序完成", len(result))
    return result


def reciprocal_rank_fusion(
    ranked_lists: list[list[Document]],
    weights: list[float] | None = None,
    k: int = 60,
) -> list[Document]:
    """RRF 融合多个排序列表。

    用于混合检索的最终融合阶段。
    """
    if not ranked_lists:
        return []

    if weights is None:
        weights = [1.0] * len(ranked_lists)

    rrf_scores: dict[str, tuple[Document, float]] = {}

    for ranked_list, weight in zip(ranked_lists, weights):
        for rank, doc in enumerate(ranked_list):
            doc_key = doc.page_content[:100]
            score = weight / (k + rank + 1)
            if doc_key in rrf_scores:
                rrf_scores[doc_key] = (doc, rrf_scores[doc_key][1] + score)
            else:
                rrf_scores[doc_key] = (doc, score)

    sorted_results = sorted(rrf_scores.values(), key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in sorted_results]
