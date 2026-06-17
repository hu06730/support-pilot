"""MCP Server 配置。"""

from __future__ import annotations

import os

MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "5000"))
