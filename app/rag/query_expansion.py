"""Query 扩展 — 用 LLM 生成多个查询变体，提升检索召回率。

策略：
1. 多 Query 改写：将用户问题改写为 N 个不同表述
2. 每个变体独立检索，结果合并去重
"""

from __future__ import annotations

import json

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Query 改写 Prompt
REWRITE_PROMPT = """你是一个检索优化助手。用户的问题可能表述简短或模糊，导致检索效果不好。

请将用户的问题改写为 {n} 个不同的查询变体，覆盖不同的表述方式和关键词组合。

要求：
1. 保持原始问题的核心含义不变
2. 使用不同的关键词和句式
3. 包含更具体的技术术语
4. 输出 JSON 数组格式

用户问题：{query}

输出格式：{{"queries": ["变体1", "变体2", "变体3"]}}
只输出 JSON，不要其他内容。"""


async def expand_query(query: str, n: int = 3) -> list[str]:
    """用 LLM 将查询改写为多个变体。

    Args:
        query: 原始用户查询
        n: 生成的变体数量

    Returns:
        变体列表（包含原始查询）
    """
    try:
        llm = ChatOpenAI(
            model=settings.openai_model,
            openai_api_key=settings.openai_api_key,
            openai_api_base=settings.openai_base_url,
            temperature=0.3,
            max_tokens=200,
        )

        prompt = REWRITE_PROMPT.format(query=query, n=n)
        response = await llm.ainvoke([HumanMessage(content=prompt)])

        # 解析 JSON
        content = response.content.strip()
        # 处理可能的 markdown 代码块
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content
            content = content.replace("```json", "").replace("```", "").strip()

        data = json.loads(content)
        queries = data.get("queries", [])

        # 确保原始查询在列表中
        if query not in queries:
            queries.insert(0, query)

        logger.info("Query 扩展: '%s' → %d 个变体", query, len(queries))
        return queries[:n + 1]  # 最多 n+1 个（含原始）

    except Exception as e:
        logger.warning("Query 扩展失败，使用原始查询: %s", e)
        return [query]


async def expand_and_merge_results(
    query: str,
    search_fn,
    top_k: int = 5,
    expand_n: int = 2,
) -> list:
    """扩展查询并合并检索结果。

    Args:
        query: 原始查询
        search_fn: 检索函数 (query) -> list[Document]
        top_k: 最终返回数量
        expand_n: 扩展变体数量

    Returns:
        合并去重后的 Document 列表
    """
    # 扩展查询
    queries = await expand_query(query, n=expand_n)

    # 对每个变体检索
    all_docs = []
    seen_contents = set()

    for q in queries:
        docs = search_fn(q)
        for doc in docs:
            content_key = doc.page_content[:100]
            if content_key not in seen_contents:
                seen_contents.add(content_key)
                all_docs.append(doc)

    # 截取 top_k
    logger.info("Query 扩展检索: %d 个变体 → %d 个去重结果 → top_%d",
                len(queries), len(all_docs), top_k)
    return all_docs[:top_k]
