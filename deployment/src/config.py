#!/usr/bin/env python3
"""
AIsatoshi V30.0 - 配置模块
从环境变量读取配置，不包含任何硬编码的敏感信息
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    """应用配置"""

    # 版本信息
    VERSION: str = "30.0"
    BUILD_DATE: str = "2026-02-16"

    # Telegram (从环境变量读取)
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_USER_ID: str = os.getenv("TELEGRAM_USER_ID", "")

    # Gemini API (从环境变量读取)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
    GEMINI_TIMEOUT: int = int(os.getenv("GEMINI_TIMEOUT", "180"))

    # 区块链 (从环境变量读取)
    AI_PRIVATE_KEY: str = os.getenv("AI_PRIVATE_KEY", "")

    # Moltbook API (从环境变量读取)
    MOLTBOOK_API_KEY: str = os.getenv("MOLTBOOK_API_KEY", "")

    # 数据目录
    DATA_DIR: str = os.getenv("DATA_DIR", "/app/data")
    WORKSPACE_DIR: str = os.getenv("WORKSPACE_DIR", "/app/workspace")

    # 日志
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Telegram 配置
    TELEGRAM_API_URL: str = "https://api.telegram.org/bot{token}"

    # Gemini 配置
    GEMINI_API_URL: str = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    # 浏览器配置
    BROWSER_TIMEOUT: int = 30000  # ms
    BROWSER_HEADLESS: bool = True

    # 消息配置
    MAX_MESSAGE_LENGTH: int = 3000  # 分段发送阈值

    def validate(self) -> bool:
        """验证必需的配置"""
        required = [
            ("TELEGRAM_BOT_TOKEN", self.TELEGRAM_BOT_TOKEN),
            ("GEMINI_API_KEY", self.GEMINI_API_KEY),
            ("AI_PRIVATE_KEY", self.AI_PRIVATE_KEY),
        ]

        missing = [name for name, value in required if not value]
        if missing:
            print(f"❌ 缺少必需的环境变量: {', '.join(missing)}")
            return False
        return True


# 全局配置实例
config = Config()
