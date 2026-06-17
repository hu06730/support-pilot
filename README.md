# SupportPilot — 智能技术支持 Agent

基于 LangChain ReAct Agent 的智能技术支持系统，集成 RAG 文档问答、诊断工具、MCP 远端工具调用。

## 快速开始

### 1. 环境准备

```bash
cp .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY
```

### 2. Docker 启动

```bash
bash scripts/run_dev.sh
```

访问 http://localhost:8000

### 3. 本地开发

```bash
pip install poetry
poetry install

# 启动 MCP Server
python -m mcp_server.server

# 启动后端
python -m app.main
```

### 4. 导入示例文档

```bash
python scripts/seed_docs.py --dir data/samples --reset
```

## 项目结构

```
support-pilot/
├── app/                    # 后端主服务
│   ├── api/                #   路由层 (chat, upload)
│   ├── agent/              #   ReAct Agent 核心
│   ├── tools/              #   内置工具 (诊断 + RAG)
│   ├── rag/                #   RAG 子系统
│   ├── mcp/                #   MCP 客户端 (provider + client)
│   └── schemas/            #   数据模型
├── mcp_server/             # 独立 MCP Server
├── frontend/               # 前端 (HTML + JS)
├── tests/                  # 测试
├── scripts/                # CLI 脚本
└── data/                   # 运行时数据
```

## 功能

- **文档问答**: 上传 PDF/TXT，自动向量化，支持 RAG 检索
- **诊断工具**: ping_host / query_service_log / get_db_status
- **多步推理**: ReAct Agent 自动规划：查文档 → 调工具 → 综合回答
- **MCP 集成**: 天气查询、Jira 工单创建等远端工具
- **流式输出**: SSE 实时展示 Agent 思考过程
