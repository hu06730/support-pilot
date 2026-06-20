# SupportPilot — 智能技术支持 Agent

基于 RAG + Agent + MCP 的智能技术支持系统，面向 IT 运维场景，支持文档问答、诊断工具调用、MCP 远端工具集成。

## 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (HTML/JS)                       │
│              Token 级 SSE 流式对话 + 文档管理面板                 │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP
┌────────────────────────────▼────────────────────────────────────┐
│                     FastAPI Server (port 8000)                  │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌──────────────────┐  │
│  │ /chat    │ │ /upload  │ │/documents │ │ /mcp/status      │  │
│  │ SSE 流式 │ │ 文档上传 │ │ 列表/删除 │ │ 连接状态/重连     │  │
│  └────┬─────┘ └────┬─────┘ └───────────┘ └──────────────────┘  │
│       │            │                                            │
│  ┌────▼────────────▼────────────────────────────────────────┐   │
│  │              LangGraph ReAct Agent                       │   │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐  │   │
│  │  │ Thought │→│  Action  │→│Observe   │→│ Final Answer│  │   │
│  │  └─────────┘ └──────────┘ └──────────┘ └─────────────┘  │   │
│  └────┬────────────┬──────────────┬─────────────────────────┘   │
│       │            │              │                              │
│  ┌────▼────┐ ┌─────▼─────┐ ┌─────▼──────────┐                  │
│  │  RAG    │ │ 诊断工具  │ │  MCP Client    │                  │
│  │ 检索    │ │ ping/log/ │ │  天气/Jira     │                  │
│  └────┬────┘ │ db_status │ └─────┬──────────┘                  │
│       │      └───────────┘       │                              │
│  ┌────▼────────────────────┐ ┌───▼──────────────┐              │
│  │    混合检索引擎          │ │   MCP Server     │              │
│  │ ┌────────┐ ┌──────────┐ │ │  (port 5000)     │              │
│  │ │Chroma  │ │BM25+jieba│ │ │  get_weather     │              │
│  │ │向量检索│ │关键词检索│ │ │  create_jira     │              │
│  │ └───┬────┘ └────┬─────┘ │ └──────────────────┘              │
│  │     │  RRF 融合  │       │                                   │
│  │     └─────┬─────┘       │                                   │
│  │     意图分类→动态权重    │                                   │
│  └───────────┴─────────────┘                                   │
└─────────────────────────────────────────────────────────────────┘
```

## 核心特性

### 🔍 混合检索引擎
- **向量语义检索**：Chroma + text-embedding-v3（阿里云百炼）
- **BM25 关键词检索**：jieba 中文分词 + BM25Okapi
- **RRF 融合排序**：Reciprocal Rank Fusion 算法
- **意图分类**：自动识别查询意图，动态调整向量/BM25 权重

### 🤖 多步推理 Agent
- LangGraph ReAct Agent，自动规划：查文档 → 调工具 → 给建议
- 支持 6 种工具：文档检索 + 3 个诊断工具 + MCP 远端工具
- Token 级 SSE 流式输出，实时展示推理过程

### 🔌 MCP 协议集成
- 独立 MCP Server（SSE transport）
- 延迟加载 + 后台 30s 自动重连
- 配置驱动，支持多 Server

### 📄 文档处理流水线
- PyMuPDF 高质量 PDF 解析（支持中文）
- 递归分块 + 自动向量化
- BM25 索引自动构建

## 技术栈

| 层级 | 技术 |
|------|------|
| **后端框架** | Python 3.10+ / FastAPI |
| **Agent 框架** | LangChain / LangGraph |
| **向量数据库** | Chroma |
| **关键词检索** | rank_bm25 + jieba |
| **嵌入模型** | text-embedding-v3（阿里云百炼） |
| **推理模型** | qwen-plus（阿里云百炼） |
| **MCP 协议** | langchain-mcp-adapters |
| **前端** | HTML + Vanilla JS |
| **测试** | pytest + pytest-asyncio |
| **部署** | Docker + docker-compose |

## 快速开始

### 1. 环境配置

```bash
cd support-pilot
cp .env.example .env
# 编辑 .env 填入 API Key
```

`.env` 配置：
```bash
OPENAI_API_KEY=你的API Key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL=qwen-plus
EMBEDDING_MODEL=text-embedding-v3
MCP_SERVER_URLS=http://localhost:5000
```

### 2. 安装依赖

```bash
pip install poetry
poetry install
```

### 3. 启动服务

```bash
# 启动 MCP Server
python -m mcp_server.server &

# 启动主服务
python -m app.main
```

### 4. 访问

- **前端**：http://localhost:8000
- **API 文档**：http://localhost:8000/docs
- **健康检查**：http://localhost:8000/health

## API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/chat` | POST | SSE 流式对话（token 级，支持多轮） |
| `/upload` | POST | 文档上传（PDF/TXT/MD/DOCX） |
| `/documents` | GET | 文档列表 |
| `/documents/{id}` | DELETE | 删除文档 |
| `/history/{session_id}` | GET | 查询对话历史 |
| `/history/{session_id}` | DELETE | 清除对话历史 |
| `/mcp/status` | GET | MCP 连接状态 |
| `/mcp/reconnect` | POST | 手动重连 MCP |

## 项目结构

```
support-pilot/
├── app/                        # 后端主服务
│   ├── api/                    #   路由层
│   │   ├── chat.py             #     对话接口（SSE 流式）
│   │   ├── upload.py           #     文档上传
│   │   ├── documents.py        #     文档管理
│   │   └── mcp.py              #     MCP 管理
│   ├── agent/                  #   Agent 核心
│   │   ├── react_agent.py      #     LangGraph Agent 组装
│   │   ├── executor.py         #     流式执行器（token 级）
│   │   ├── memory.py           #     对话历史管理
│   │   └── prompts.py          #     系统提示词
│   ├── tools/                  #   内置工具
│   │   ├── diagnostic.py       #     诊断工具（ping/log/db）
│   │   └── rag_tool.py         #     文档检索工具
│   ├── rag/                    #   RAG 子系统
│   │   ├── parsers.py          #     文档解析（PyMuPDF）
│   │   ├── loader.py           #     加载 & 分块
│   │   ├── embeddings.py       #     嵌入工厂
│   │   ├── vectorstore.py      #     Chroma 管理
│   │   ├── hybrid_retriever.py #     混合检索（向量+BM25+RRF）
│   │   ├── intent.py           #     意图分类
│   │   └── bm25.py             #     BM25 索引
│   ├── mcp/                    #   MCP 子系统
│   │   ├── provider.py         #     MCP Provider（延迟加载+重连）
│   │   └── client.py           #     MCP 客户端
│   ├── schemas/                #   数据模型
│   ├── utils/                  #   工具函数
│   ├── config.py               #   配置管理
│   └── main.py                 #   FastAPI 入口
├── mcp_server/                 # 独立 MCP Server
│   ├── server.py               #   MCP Server（SSE transport）
│   └── tools/                  #   MCP 工具（天气/Jira）
├── frontend/                   # 前端界面
├── tests/                      # 测试
│   ├── api/                    #   API 测试
│   ├── tools/                  #   工具单测
│   ├── rag/                    #   RAG 测试
│   ├── mcp/                    #   MCP 测试
│   └── integration/            #   集成测试
├── scripts/                    # CLI 脚本
├── .github/workflows/ci.yml    # GitHub Actions CI
├── docker-compose.yml          # Docker 编排
├── pyproject.toml              # Poetry 依赖
└── README.md
```

## 测试

```bash
# 运行全部测试
pytest tests/ -v

# 运行特定测试
pytest tests/tools/ -v           # 工具单测
pytest tests/rag/ -v             # RAG 测试
pytest tests/integration/ -v     # 集成测试
```

当前测试覆盖：**33 个测试用例，全部通过**

## 核心数据流

```
用户提问 "数据库连接超时怎么办"
  │
  ▼
POST /chat → Agent 推理
  │
  ├── 意图分类: "factual_lookup" → BM25 权重 0.7
  │
  ├── Action: document_search("数据库连接超时")
  │     ├── 向量检索: Chroma 相似度
  │     ├── BM25 检索: jieba 关键词匹配
  │     └── RRF 融合 → 返回相关文档片段
  │
  ├── Action: get_db_status("production_db")
  │     └── 返回: {status: "warning", connections: 92/100}
  │
  └── Final Answer: 诊断结果 + 建议 + 工单号
        │
        ▼
  SSE Token 流式 → 前端打字机效果
```

## License

MIT
