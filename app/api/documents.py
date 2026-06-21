"""文档管理接口 — 列表 / 删除 / 去重检查。"""

from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.rag.vectorstore import get_vectorstore
from app.rag.bm25 import bm25_cache
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


def _get_collection():
    """获取 Chroma collection（每次调用重新获取，避免缓存问题）。"""
    vs = get_vectorstore()
    return vs._collection


def _compute_file_hash(file_path: Path) -> str:
    """计算文件 MD5 哈希。"""
    h = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


@router.get("/documents")
async def list_documents():
    """列出所有已上传的文档（从 Chroma 元数据中提取）。"""
    collection = _get_collection()
    results = collection.get(include=["metadatas", "documents"])

    if not results["ids"]:
        return {"documents": [], "total": 0}

    # 按 source 文件聚合
    docs_map: dict[str, dict] = {}
    for meta, doc_text in zip(results["metadatas"], results["documents"]):
        source = meta.get("source", "unknown")
        if source not in docs_map:
            filename = Path(source).name
            doc_id = filename.split("_")[0] if "_" in filename else filename
            original_name = filename.split("_", 1)[1] if "_" in filename else filename
            docs_map[source] = {
                "doc_id": doc_id,
                "filename": original_name,
                "source": source,
                "chunks": 0,
                "preview": "",
            }
        docs_map[source]["chunks"] += 1
        if not docs_map[source]["preview"]:
            docs_map[source]["preview"] = doc_text[:100]

    return {"documents": list(docs_map.values()), "total": len(docs_map)}


@router.get("/documents/check/{filename}")
async def check_duplicate(filename: str):
    """检查文档是否已上传（按文件名匹配）。"""
    collection = _get_collection()
    results = collection.get(include=["metadatas"])

    for meta in results["metadatas"]:
        source = meta.get("source", "")
        if filename in Path(source).name:
            return {"exists": True, "source": source}

    return {"exists": False}


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """删除指定文档及其所有分块。"""
    collection = _get_collection()

    # 查找该 doc_id 对应的所有分块
    try:
        results = collection.get(include=["metadatas"])
    except Exception as e:
        logger.error("Chroma get 失败: %s", e)
        raise HTTPException(status_code=500, detail=f"数据库查询失败: {e}")

    ids_to_delete = []
    source_to_delete = None

    for chunk_id, meta in zip(results["ids"], results["metadatas"]):
        source = meta.get("source", "")
        if doc_id in source:
            ids_to_delete.append(chunk_id)
            source_to_delete = source

    if not ids_to_delete:
        raise HTTPException(status_code=404, detail=f"未找到 doc_id={doc_id} 的文档")

    # 从 Chroma 删除
    try:
        collection.delete(ids=ids_to_delete)
        logger.info("从 Chroma 删除 %d 个分块 (doc_id=%s)", len(ids_to_delete), doc_id)
    except Exception as e:
        logger.error("Chroma 删除失败: %s", e)
        raise HTTPException(status_code=500, detail=f"删除失败: {e}")

    # 清除 BM25 缓存
    bm25_cache.invalidate(settings.chroma_collection_name)

    # 删除原始文件
    if source_to_delete:
        file_path = Path(source_to_delete)
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info("删除文件: %s", file_path)
            except Exception as e:
                logger.warning("文件删除失败: %s", e)

    return {
        "message": "文档删除成功",
        "doc_id": doc_id,
        "deleted_chunks": len(ids_to_delete),
    }
