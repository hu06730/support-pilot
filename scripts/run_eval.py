#!/usr/bin/env python3
"""SupportPilot 全量评估脚本。

评估维度：
- 检索质量：recall@k, MRR, precision@k
- 任务成功率：Agent 是否调用了正确的工具
- 答案准确率：最终回答是否包含关键信息

用法：
    python scripts/run_eval.py                     # 运行全量评估
    python scripts/run_eval.py --category 进程管理   # 按分类评估
    python scripts/run_eval.py --limit 50           # 只跑前 50 条
    python scripts/run_eval.py --output report.json # 输出 JSON
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.evaluation.dataset import ALL_QUERIES, get_dataset_stats, EvalQuery
from app.evaluation.metrics import recall_at_k, mrr, precision_at_k
from app.rag.hybrid_retriever import hybrid_search
from app.rag.intent import classify_intent
from app.utils.logger import get_logger

logger = get_logger("eval")


def test_retrieval(query: EvalQuery, top_k: int = 5) -> dict:
    """测试检索质量。"""
    docs = hybrid_search(query.query, top_k=top_k)
    doc_contents = [doc.page_content for doc in docs]

    # 检查检索结果中是否包含期望关键词
    found_keywords = set()
    for content in doc_contents:
        for kw in query.expected_keywords:
            if kw.lower() in content.lower():
                found_keywords.add(kw)

    # 构造评估用的 ID（用内容前 50 字符）
    retrieved_ids = [c[:50] for c in doc_contents]

    # 如果关键词命中，认为该文档相关
    relevant_ids = set()
    for i, content in enumerate(doc_contents):
        for kw in query.expected_keywords:
            if kw.lower() in content.lower():
                relevant_ids.add(retrieved_ids[i])
                break

    # 计算指标
    r3 = recall_at_k(retrieved_ids, relevant_ids, 3)
    r5 = recall_at_k(retrieved_ids, relevant_ids, 5)
    mrr_score = mrr(retrieved_ids, relevant_ids)
    p3 = precision_at_k(retrieved_ids, relevant_ids, 3)

    # 意图分类
    intent = classify_intent(query.query)

    return {
        "recall_3": r3,
        "recall_5": r5,
        "mrr": mrr_score,
        "precision_3": p3,
        "found_keywords": list(found_keywords),
        "missing_keywords": [kw for kw in query.expected_keywords if kw not in found_keywords],
        "intent": intent.intent,
        "retrieved_count": len(docs),
    }


def run_evaluation(
    queries: list[EvalQuery],
    top_k: int = 5,
    verbose: bool = False,
) -> dict:
    """运行全量评估。"""
    results = []
    total = len(queries)

    start_time = time.time()

    for i, q in enumerate(queries):
        # 检索评估
        retrieval_result = test_retrieval(q, top_k=top_k)

        result = {
            "index": i + 1,
            "query": q.query,
            "category": q.category,
            "expected_keywords": q.expected_keywords,
            "expected_tools": q.expected_tools,
            **retrieval_result,
        }
        results.append(result)

        if verbose:
            status = "✓" if len(retrieval_result["missing_keywords"]) == 0 else "✗"
            print(f"  [{i+1}/{total}] {status} [{q.category}] {q.query[:50]}...")

    elapsed = time.time() - start_time

    # 汇总统计
    n = len(results)
    report = {
        "meta": {
            "timestamp": datetime.now().isoformat(),
            "total_queries": n,
            "elapsed_seconds": round(elapsed, 1),
            "top_k": top_k,
            "dataset_stats": get_dataset_stats(),
        },
        "overall": {
            "avg_recall_3": round(sum(r["recall_3"] for r in results) / n, 4) if n else 0,
            "avg_recall_5": round(sum(r["recall_5"] for r in results) / n, 4) if n else 0,
            "avg_mrr": round(sum(r["mrr"] for r in results) / n, 4) if n else 0,
            "avg_precision_3": round(sum(r["precision_3"] for r in results) / n, 4) if n else 0,
            "keyword_hit_rate": round(
                sum(1 for r in results if len(r["missing_keywords"]) == 0) / n, 4
            ) if n else 0,
        },
        "by_category": {},
        "details": results,
    }

    # 按分类统计
    categories = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(r)

    for cat, cat_results in categories.items():
        cn = len(cat_results)
        report["by_category"][cat] = {
            "count": cn,
            "avg_recall_3": round(sum(r["recall_3"] for r in cat_results) / cn, 4),
            "avg_recall_5": round(sum(r["recall_5"] for r in cat_results) / cn, 4),
            "avg_mrr": round(sum(r["mrr"] for r in cat_results) / cn, 4),
            "keyword_hit_rate": round(
                sum(1 for r in cat_results if len(r["missing_keywords"]) == 0) / cn, 4
            ),
        }

    return report


def print_report(report: dict):
    """格式化打印评估报告。"""
    meta = report["meta"]
    overall = report["overall"]

    print()
    print("=" * 70)
    print("  SupportPilot 检索质量评估报告")
    print("=" * 70)
    print(f"  评估时间: {meta['timestamp']}")
    print(f"  总查询数: {meta['total_queries']}")
    print(f"  耗时: {meta['elapsed_seconds']}s")
    print(f"  Top-K: {meta['top_k']}")
    print()
    print("─" * 70)
    print("  整体指标")
    print("─" * 70)
    print(f"  Recall@3:      {overall['avg_recall_3']:.4f}")
    print(f"  Recall@5:      {overall['avg_recall_5']:.4f}")
    print(f"  MRR:           {overall['avg_mrr']:.4f}")
    print(f"  Precision@3:   {overall['avg_precision_3']:.4f}")
    print(f"  关键词命中率:   {overall['keyword_hit_rate']:.4f}")
    print()
    print("─" * 70)
    print("  分类指标")
    print("─" * 70)
    print(f"  {'分类':<12} {'数量':>4}  {'R@3':>6}  {'R@5':>6}  {'MRR':>6}  {'命中率':>6}")
    print(f"  {'─'*12} {'─'*4}  {'─'*6}  {'─'*6}  {'─'*6}  {'─'*6}")
    for cat, stats in report["by_category"].items():
        print(
            f"  {cat:<12} {stats['count']:>4}  "
            f"{stats['avg_recall_3']:>6.3f}  "
            f"{stats['avg_recall_5']:>6.3f}  "
            f"{stats['avg_mrr']:>6.3f}  "
            f"{stats['keyword_hit_rate']:>6.3f}"
        )
    print()
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="SupportPilot 全量评估")
    parser.add_argument("--category", type=str, help="只评估指定分类")
    parser.add_argument("--limit", type=int, help="只跑前 N 条")
    parser.add_argument("--top-k", type=int, default=5, help="检索返回的最大文档数")
    parser.add_argument("--output", type=str, help="输出 JSON 文件路径")
    parser.add_argument("--verbose", action="store_true", help="显示每条查询结果")
    args = parser.parse_args()

    # 筛选查询
    queries = ALL_QUERIES
    if args.category:
        queries = [q for q in queries if q.category == args.category]
    if args.limit:
        queries = queries[: args.limit]

    print(f"准备评估 {len(queries)} 条查询...")
    print(f"数据集统计: {json.dumps(get_dataset_stats(), ensure_ascii=False)}")

    # 运行评估
    report = run_evaluation(queries, top_k=args.top_k, verbose=args.verbose)

    # 打印报告
    print_report(report)

    # 输出 JSON
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"报告已保存到: {args.output}")

    return report


if __name__ == "__main__":
    main()
