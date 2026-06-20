"""检索评估器 — 运行评估并生成报告。"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.evaluation.metrics import recall_at_k, mrr, precision_at_k
from app.rag.hybrid_retriever import hybrid_search, vector_only_search
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class EvalCase:
    """评估用例。"""
    query: str
    relevant_keywords: list[str]  # 相关文档应包含的关键词
    description: str = ""


@dataclass
class EvalResult:
    """单条评估结果。"""
    query: str
    recall_3: float
    recall_5: float
    mrr_score: float
    precision_3: float
    found_keywords: list[str]


@dataclass
class EvalReport:
    """评估报告。"""
    total_cases: int
    avg_recall_3: float
    avg_recall_5: float
    avg_mrr: float
    avg_precision_3: float
    results: list[EvalResult] = field(default_factory=list)


# 默认评估数据集
DEFAULT_EVAL_DATASET: list[EvalCase] = [
    EvalCase(
        query="进程创建",
        relevant_keywords=["fork", "进程", "子进程", "父进程"],
        description="操作系统进程创建",
    ),
    EvalCase(
        query="页面置换算法",
        relevant_keywords=["FIFO", "LRU", "OPT", "页面", "置换", "缺页"],
        description="页面调度算法",
    ),
    EvalCase(
        query="进程通信方式",
        relevant_keywords=["管道", "消息队列", "共享内存", "信号", "IPC"],
        description="进程间通信",
    ),
    EvalCase(
        query="数据库连接池",
        relevant_keywords=["连接", "数据库", "连接池", "超时"],
        description="数据库连接问题",
    ),
    EvalCase(
        query="孤儿进程和僵尸进程",
        relevant_keywords=["孤儿", "僵尸", "zombie", "init"],
        description="进程状态",
    ),
    EvalCase(
        query="文件操作",
        relevant_keywords=["文件", "读写", "open", "read", "write"],
        description="文件系统操作",
    ),
    EvalCase(
        query="信号处理",
        relevant_keywords=["信号", "signal", "SIGINT", "kill"],
        description="信号机制",
    ),
    EvalCase(
        query="存储管理",
        relevant_keywords=["内存", "存储", "分配", "物理", "虚拟"],
        description="存储管理",
    ),
]


def _check_relevance(doc_content: str, keywords: list[str]) -> tuple[bool, list[str]]:
    """检查文档是否包含相关关键词。"""
    found = [kw for kw in keywords if kw.lower() in doc_content.lower()]
    return len(found) > 0, found


def run_evaluation(
    dataset: list[EvalCase] | None = None,
    top_k: int = 5,
) -> EvalReport:
    """运行检索评估。

    Args:
        dataset: 评估数据集（默认使用 DEFAULT_EVAL_DATASET）
        top_k: 检索返回的最大文档数

    Returns:
        EvalReport 评估报告
    """
    cases = dataset or DEFAULT_EVAL_DATASET
    results = []

    for case in cases:
        # 执行混合检索
        docs = hybrid_search(case.query, top_k=top_k)

        # 检查检索结果中是否包含相关关键词
        found_all_keywords = []
        doc_contents = []
        for doc in docs:
            is_relevant, found = _check_relevance(doc.page_content, case.relevant_keywords)
            found_all_keywords.extend(found)
            doc_contents.append(doc.page_content[:100])

        # 构造 retrieved_ids（用文档内容前 50 字符作为 ID）
        retrieved_ids = [doc.page_content[:50] for doc in docs]

        # 构造 relevant_ids（包含任意相关关键词的文档）
        # 注意：这里用关键词匹配作为近似，真实场景需要人工标注
        relevant_ids = set()
        for i, doc in enumerate(docs):
            is_relevant, _ = _check_relevance(doc.page_content, case.relevant_keywords)
            if is_relevant:
                relevant_ids.add(retrieved_ids[i])

        # 计算指标
        r3 = recall_at_k(retrieved_ids, relevant_ids, 3)
        r5 = recall_at_k(retrieved_ids, relevant_ids, 5)
        mrr_score = mrr(retrieved_ids, relevant_ids)
        p3 = precision_at_k(retrieved_ids, relevant_ids, 3)

        unique_keywords = list(set(found_all_keywords))
        results.append(EvalResult(
            query=case.query,
            recall_3=r3,
            recall_5=r5,
            mrr_score=mrr_score,
            precision_3=p3,
            found_keywords=unique_keywords,
        ))

        logger.info("评估 [%s]: recall@3=%.2f, recall@5=%.2f, mrr=%.2f, 关键词=%s",
                     case.query, r3, r5, mrr_score, unique_keywords)

    # 汇总
    n = len(results)
    report = EvalReport(
        total_cases=n,
        avg_recall_3=sum(r.recall_3 for r in results) / n if n else 0,
        avg_recall_5=sum(r.recall_5 for r in results) / n if n else 0,
        avg_mrr=sum(r.mrr_score for r in results) / n if n else 0,
        avg_precision_3=sum(r.precision_3 for r in results) / n if n else 0,
        results=results,
    )

    logger.info("=== 评估完成: %d 用例, avg_recall@3=%.2f, avg_recall@5=%.2f, avg_mrr=%.2f ===",
                report.total_cases, report.avg_recall_3, report.avg_recall_5, report.avg_mrr)

    return report


def print_report(report: EvalReport) -> str:
    """格式化打印评估报告。"""
    lines = [
        "=" * 60,
        "检索评估报告",
        "=" * 60,
        f"总用例数: {report.total_cases}",
        f"平均 Recall@3:  {report.avg_recall_3:.3f}",
        f"平均 Recall@5:  {report.avg_recall_5:.3f}",
        f"平均 MRR:       {report.avg_mrr:.3f}",
        f"平均 Precision@3: {report.avg_precision_3:.3f}",
        "-" * 60,
        "详细结果:",
    ]
    for r in report.results:
        lines.append(
            f"  [{r.query}] R@3={r.recall_3:.2f} R@5={r.recall_5:.2f} "
            f"MRR={r.mrr_score:.2f} 关键词={r.found_keywords}"
        )
    lines.append("=" * 60)
    return "\n".join(lines)
