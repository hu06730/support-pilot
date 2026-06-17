FROM python:3.11-slim

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Poetry
RUN pip install --no-cache-dir poetry

# 依赖文件（利用 Docker 缓存层）
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --only main || \
    pip install --no-cache-dir \
        fastapi uvicorn pydantic pydantic-settings \
        langchain langchain-openai langchain-community langchain-text-splitters \
        mcp langchain-mcp-adapters \
        chromadb pypdf tiktoken openai \
        python-dotenv sse-starlette aiofiles httpx

# 应用代码
COPY app/ ./app/
COPY mcp_server/ ./mcp_server/
COPY frontend/ ./frontend/

# 数据目录
RUN mkdir -p data/uploads data/chroma

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
