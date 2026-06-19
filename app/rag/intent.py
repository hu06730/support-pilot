"""查询意图分类 — 根据关键词动态调整向量/BM25 权重。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IntentWeights:
    vector_weight: float
    bm25_weight: float
    intent: str


# 意图规则：关键词 → (向量权重, BM25权重)
INTENT_RULES: list[tuple[list[str], float, float, str]] = [
    # 概念理解类 → 偏向语义检索
    (["为什么", "区别", "原理", "概念", "理解", "含义"], 0.7, 0.3, "conceptual"),
    # 精确查找类 → 偏向关键词检索
    (["是什么", "多少", "定义", "名称", "版本号", "端口", "地址"], 0.3, 0.7, "factual_lookup"),
    # 操作流程类 → 均衡
    (["怎么做", "如何", "流程", "步骤", "操作", "配置", "搭建"], 0.5, 0.5, "procedural"),
    # 合规规范类 → 强偏向关键词
    (["规定", "标准", "条例", "规范", "要求", "制度"], 0.2, 0.8, "compliance"),
]


def classify_intent(query: str) -> IntentWeights:
    """根据查询内容判断意图，返回对应的检索权重。"""
    for keywords, vec_w, bm25_w, intent_name in INTENT_RULES:
        for kw in keywords:
            if kw in query:
                return IntentWeights(
                    vector_weight=vec_w,
                    bm25_weight=bm25_w,
                    intent=intent_name,
                )

    # 默认：均衡权重
    return IntentWeights(vector_weight=0.5, bm25_weight=0.5, intent="default")
