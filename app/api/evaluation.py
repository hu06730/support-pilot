"""评估接口 — 运行检索评估。"""

from __future__ import annotations

from fastapi import APIRouter

from app.evaluation.evaluator import run_evaluation, print_report

router = APIRouter()


@router.post("/evaluation/run")
async def run_eval():
    """运行检索评估，返回报告。"""
    report = run_evaluation()
    return {
        "total_cases": report.total_cases,
        "avg_recall_3": round(report.avg_recall_3, 3),
        "avg_recall_5": round(report.avg_recall_5, 3),
        "avg_mrr": round(report.avg_mrr, 3),
        "avg_precision_3": round(report.avg_precision_3, 3),
        "details": [
            {
                "query": r.query,
                "recall_3": round(r.recall_3, 3),
                "recall_5": round(r.recall_5, 3),
                "mrr": round(r.mrr_score, 3),
                "precision_3": round(r.precision_3, 3),
                "found_keywords": r.found_keywords,
            }
            for r in report.results
        ],
    }
