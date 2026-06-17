#!/usr/bin/env bash
# 一行启动开发环境
# 用法: bash scripts/run_dev.sh [--watch]

set -euo pipefail

cd "$(dirname "$0")/.."

# 检查 .env
if [ ! -f .env ]; then
    echo "⚠️  未找到 .env 文件，复制模板..."
    cp .env.example .env
    echo "📝 请编辑 .env 填入 OPENAI_API_KEY"
    exit 1
fi

if [ "${1:-}" = "--watch" ]; then
    echo "🚀 启动开发环境（watch 模式）..."
    docker compose up --build --watch
else
    echo "🚀 启动开发环境..."
    docker compose up --build
fi
