"""检索评估指标 — recall@k / MRR。"""

from __future__ import annotations


def recall_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """计算 recall@k。

    Args:
        retrieved_ids: 检索返回的文档 ID 列表（按相关性排序）
        relevant_ids: 真正相关的文档 ID 集合
        k: 取前 k 个结果

    Returns:
        recall@k 值（0.0 ~ 1.0）
    """
    if not relevant_ids:
        return 0.0

    retrieved_top_k = set(retrieved_ids[:k])
    hits = retrieved_top_k & relevant_ids
    return len(hits) / len(relevant_ids)


def mrr(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    """计算 MRR (Mean Reciprocal Rank)。

    Args:
        retrieved_ids: 检索返回的文档 ID 列表（按相关性排序）
        relevant_ids: 真正相关的文档 ID 集合

    Returns:
        MRR 值（0.0 ~ 1.0）
    """
    for i, doc_id in enumerate(retrieved_ids):
        if doc_id in relevant_ids:
            return 1.0 / (i + 1)
    return 0.0


def precision_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """计算 precision@k。

    Args:
        retrieved_ids: 检索返回的文档 ID 列表
        relevant_ids: 真正相关的文档 ID 集合
        k: 取前 k 个结果

    Returns:
        precision@k 值（0.0 ~ 1.0）
    """
    if k == 0:
        return 0.0

    retrieved_top_k = set(retrieved_ids[:k])
    hits = retrieved_top_k & relevant_ids
    return len(hits) / k
