"""FastAPI 应用入口 — 生命周期管理 + 路由挂载。"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.mcp.provider import mcp_provider
from app.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化 MCP + Agent，关闭时清理。"""
    logger.info("=== SupportPilot 启动中 ===")

    # 1. 初始化 MCP Provider（连接所有 MCP Server）
    try:
        await mcp_provider.init()
        health = await mcp_provider.health_check()
        logger.info("MCP 健康检查: %s", health)
    except Exception as e:
        logger.warning("MCP 初始化失败（将仅使用内置工具）: %s", e)

    # 2. 构建 Agent
    from app.agent.react_agent import build_agent
    try:
        agent_graph = await build_agent(mcp_provider)
        app.state.agent = agent_graph
        logger.info("Agent 初始化完成")
    except Exception as e:
        logger.error("Agent 构建失败: %s", e)
        app.state.agent = None

    logger.info("=== SupportPilot 启动完成 ===")

    yield

    # 关闭清理
    logger.info("=== SupportPilot 关闭中 ===")
    await mcp_provider.shutdown()


# ── 创建 FastAPI 实例 ──
app = FastAPI(
    title="SupportPilot",
    description="智能技术支持 Agent — LangChain ReAct + RAG + MCP",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由
from app.api.chat import router as chat_router
from app.api.upload import router as upload_router
from app.api.documents import router as documents_router
from app.api.mcp import router as mcp_router

app.include_router(chat_router, tags=["chat"])
app.include_router(upload_router, tags=["upload"])
app.include_router(documents_router, tags=["documents"])
app.include_router(mcp_router, tags=["mcp"])

# 静态文件（前端）
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
async def root():
    """重定向到前端页面。"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")


@app.get("/health")
async def health():
    """健康检查端点。"""
    return {"status": "ok", "service": "support-pilot"}


def main():
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
