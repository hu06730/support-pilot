"""BM25 关键词检索 — jieba 分词 + rank_bm25。"""

from __future__ import annotations

import pickle
from pathlib import Path

import jieba
from rank_bm25 import BM25Okapi

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BM25Index:
    """BM25 检索索引，支持内存 + 磁盘缓存。"""

    def __init__(self, corpus: list[str], doc_ids: list[str]):
        self.doc_ids = doc_ids
        self._empty = len(corpus) == 0
        if not self._empty:
            self._tokenized = [list(jieba.cut(text)) for text in corpus]
            self._bm25 = BM25Okapi(self._tokenized)
        else:
            self._tokenized = []
            self._bm25 = None

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """返回 (doc_id, score) 列表。"""
        if self._empty or self._bm25 is None:
            return []
        tokens = list(jieba.cut(query))
        scores = self._bm25.get_scores(tokens)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
        return [(self.doc_ids[i], float(s)) for i, s in ranked if s > 0]


class BM25Cache:
    """BM25 索引缓存（内存 + 磁盘）。"""

    def __init__(self):
        self._cache: dict[str, BM25Index] = {}
        self._cache_dir = Path(settings.chroma_persist_dir).parent / "bm25_cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def get_or_build(self, collection_name: str, corpus: list[str], doc_ids: list[str]) -> BM25Index:
        """获取缓存的索引，不存在则构建。"""
        if collection_name in self._cache:
            return self._cache[collection_name]

        # 尝试从磁盘加载
        disk_path = self._cache_dir / f"{collection_name}.pkl"
        if disk_path.exists():
            try:
                with open(disk_path, "rb") as f:
                    index = pickle.load(f)
                self._cache[collection_name] = index
                logger.info("BM25 索引从磁盘加载: %s", collection_name)
                return index
            except Exception:
                pass

        # 构建新索引
        index = BM25Index(corpus, doc_ids)
        self._cache[collection_name] = index

        # 持久化到磁盘
        try:
            with open(disk_path, "wb") as f:
                pickle.dump(index, f)
        except Exception as e:
            logger.warning("BM25 索引持久化失败: %s", e)

        logger.info("BM25 索引构建完成: %s (%d 文档)", collection_name, len(corpus))
        return index

    def invalidate(self, collection_name: str | None = None):
        """清除缓存。"""
        if collection_name:
            self._cache.pop(collection_name, None)
            disk_path = self._cache_dir / f"{collection_name}.pkl"
            disk_path.unlink(missing_ok=True)
        else:
            self._cache.clear()
            for f in self._cache_dir.glob("*.pkl"):
                f.unlink()


# 全局单例
bm25_cache = BM25Cache()
