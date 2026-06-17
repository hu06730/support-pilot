"""get_weather MCP 工具。"""

from __future__ import annotations

import random


async def get_weather(city: str) -> dict:
    """获取指定城市的天气信息。"""
    conditions = ["晴", "多云", "小雨", "阴", "雷阵雨"]
    return {
        "city": city,
        "temperature": round(random.uniform(-5, 38), 1),
        "condition": random.choice(conditions),
        "humidity": random.randint(20, 95),
        "wind_speed_kmh": round(random.uniform(0, 60), 1),
    }
