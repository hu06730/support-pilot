"""文档上传接口。"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, File, UploadFile, HTTPException

from app.config import settings
from app.rag.loader import load_and_split
from app.rag.vectorstore import add_documents
from app.schemas.models import UploadResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """上传文档（PDF/TXT/MD），自动向量化写入 Chroma。"""
    # 校验文件类型
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {suffix}，仅支持 {ALLOWED_EXTENSIONS}")

    # 保存到 uploads 目录
    upload_dir = Path(settings.chroma_persist_dir).parent / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    doc_id = uuid.uuid4().hex[:12]
    save_path = upload_dir / f"{doc_id}_{file.filename}"

    async with aiofiles.open(save_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    logger.info("文件已保存: %s (%d bytes)", save_path, len(content))

    # 加载 → 分块 → 写入 Chroma
    try:
        chunks = load_and_split(save_path)
        ids = add_documents(chunks)
    except Exception as e:
        logger.error("文档处理失败: %s", e)
        raise HTTPException(status_code=500, detail=f"文档处理失败: {e}")

    return UploadResponse(
        filename=file.filename,
        chunks=len(chunks),
        doc_id=doc_id,
    )
