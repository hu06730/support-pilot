#!/usr/bin/env python3
"""批量导入示例文档到 Chroma 向量库。

用法:
    python scripts/seed_docs.py                  # 默认导入 data/samples/
    python scripts/seed_docs.py --dir ./my_docs  # 指定目录
    python scripts/seed_docs.py --reset           # 清空后重建
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 将项目根目录加入 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.rag.loader import load_and_split
from app.rag.vectorstore import add_documents, reset_collection
from app.utils.logger import get_logger

logger = get_logger("seed_docs")


def seed(directory: Path, reset: bool = False):
    if reset:
        logger.info("清空现有 collection...")
        reset_collection()

    files = sorted(
        f for f in directory.iterdir()
        if f.suffix.lower() in (".pdf", ".txt", ".md")
    )

    if not files:
        logger.warning("目录 %s 下没有可导入的文件", directory)
        return

    total_chunks = 0
    for f in files:
        try:
            chunks = load_and_split(f)
            add_documents(chunks)
            total_chunks += len(chunks)
            logger.info("✅ %s → %d 块", f.name, len(chunks))
        except Exception as e:
            logger.error("❌ %s 处理失败: %s", f.name, e)

    logger.info("=== 导入完成: %d 个文件, %d 个分块 ===", len(files), total_chunks)


def main():
    parser = argparse.ArgumentParser(description="批量导入文档到 Chroma")
    parser.add_argument("--dir", type=str, default="data/samples", help="文档目录路径")
    parser.add_argument("--reset", action="store_true", help="清空后重建 collection")
    args = parser.parse_args()

    directory = Path(args.dir)
    if not directory.exists():
        logger.error("目录不存在: %s", directory)
        sys.exit(1)

    seed(directory, reset=args.reset)


if __name__ == "__main__":
    main()
