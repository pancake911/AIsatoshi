"""
AIsatoshi V27 - 配置管理

从环境变量安全加载所有配置，不使用任何硬编码值。
"""

import os
from dataclasses import dataclass
from typing import Optional


class ConfigurationError(Exception):
    """配置错误"""
    pass


@dataclass
class Config:
    """AIsatoshi配置类

    所有配置从环境变量读取，确保安全性和灵活性。
    """

    # 版本信息
    VERSION: str = "v27"

    # === 必需配置 ===
    # AI私钥（从环境变量读取，绝不硬编码）
    AI_PRIVATE_KEY: str = ""

    # Gemini API密钥
    GEMINI_API_KEY: str = ""

    # Telegram Bot Token
    TELEGRAM_BOT_TOKEN: str = ""

    # === 可选配置 ===
    # Moltbook API密钥
    MOLTBOOK_API_KEY: Optional[str] = None

    # Telegram用户Chat ID（可选，自动检测）
    TELEGRAM_USER_ID: Optional[str] = None

    # === 运行配置 ===
    # 日志级别
    LOG_LEVEL: str = "INFO"

    # 数据目录
    DATA_DIR: str = "/app/data"

    # 工作空间目录
    WORKSPACE_DIR: str = "/app/workspace"

    # 数据库路径
    CONVERSATIONS_DB: str = "/app/data/conversations.db"
    TASKS_DB: str = "/app/data/tasks.db"
    MEMORY_DB: str = "/app/data/memory.db"
    EVOLUTION_DB: str = "/app/data/evolution.db"

    # === API配置 ===
    # Gemini API模型
    GEMINI_MODEL: str = "gemini-3.0-pro-preview"

    # Gemini API超时
    GEMINI_TIMEOUT: int = 180

    # === Telegram配置 ===
    # Telegram API基础URL
    TELEGRAM_API_URL: str = "https://api.telegram.org/bot"

    # Telegram获取更新超时
    TELEGRAM_GETUPDATES_TIMEOUT: int = 30

    # === 区块链配置 ===
    # 以太坊RPC节点列表
    ETH_RPC_ENDPOINTS: list = None

    # === 任务配置 ===
    # 任务检查间隔（秒）
    TASK_CHECK_INTERVAL: int = 60

    # === 进化配置 ===
    # 进化学习间隔（秒）
    EVOLUTION_LEARN_INTERVAL: int = 3600

    # 每日总结时间（小时）
    DAILY_SUMMARY_HOUR: int = 0

    @classmethod
    def from_env(cls) -> "Config":
        """从环境变量加载配置

        这是唯一推荐的配置加载方式。
        """
        # 检查必需的环境变量
        ai_private_key = os.getenv("AI_PRIVATE_KEY", "")
        if not ai_private_key:
            raise ConfigurationError(
                "AI_PRIVATE_KEY 环境变量未设置。"
                "请在部署时设置此环境变量。"
            )

        gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        if not gemini_api_key:
            raise ConfigurationError(
                "GEMINI_API_KEY 环境变量未设置。"
                "请在部署时设置此环境变量。"
            )

        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        if not telegram_token:
            raise ConfigurationError(
                "TELEGRAM_BOT_TOKEN 环境变量未设置。"
                "请在部署时设置此环境变量。"
            )

        # RPC节点列表
        rpc_endpoints = os.getenv("ETH_RPC_ENDPOINTS", "").split(",") if os.getenv("ETH_RPC_ENDPOINTS") else [
            "https://eth.llamarpc.com",
            "https://rpc.ankr.com/eth",
            "https://ethereum.publicnode.com",
            "https://1rpc.io/eth",
        ]

        # 创建配置对象
        return cls(
            AI_PRIVATE_KEY=ai_private_key,
            GEMINI_API_KEY=gemini_api_key,
            TELEGRAM_BOT_TOKEN=telegram_token,
            MOLTBOOK_API_KEY=os.getenv("MOLTBOOK_API_KEY"),
            TELEGRAM_USER_ID=os.getenv("TELEGRAM_USER_ID"),
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
            DATA_DIR=os.getenv("DATA_DIR", "/app/data"),
            WORKSPACE_DIR=os.getenv("WORKSPACE_DIR", "/app/workspace"),
            CONVERSATIONS_DB=os.getenv("CONVERSATIONS_DB", "/app/data/conversations.db"),
            TASKS_DB=os.getenv("TASKS_DB", "/app/data/tasks.db"),
            MEMORY_DB=os.getenv("MEMORY_DB", "/app/data/memory.db"),
            EVOLUTION_DB=os.getenv("EVOLUTION_DB", "/app/data/evolution.db"),
            GEMINI_MODEL=os.getenv("GEMINI_MODEL", "gemini-3.0-pro-preview"),
            GEMINI_TIMEOUT=int(os.getenv("GEMINI_TIMEOUT", "180")),
            ETH_RPC_ENDPOINTS=rpc_endpoints,
            TASK_CHECK_INTERVAL=int(os.getenv("TASK_CHECK_INTERVAL", "60")),
            EVOLUTION_LEARN_INTERVAL=int(os.getenv("EVOLUTION_LEARN_INTERVAL", "3600")),
            DAILY_SUMMARY_HOUR=int(os.getenv("DAILY_SUMMARY_HOUR", "0")),
        )

    def validate(self) -> bool:
        """验证配置是否有效"""
        errors = []

        if not self.AI_PRIVATE_KEY or len(self.AI_PRIVATE_KEY) < 10:
            errors.append("AI_PRIVATE_KEY 无效")

        if not self.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY 未设置")

        if not self.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN 未设置")

        if errors:
            raise ConfigurationError(f"配置验证失败: {', '.join(errors)}")

        return True

    def __str__(self) -> str:
        """返回配置摘要（隐藏敏感信息）"""
        return f"""AIsatoshi {self.VERSION} 配置摘要:
- 日志级别: {self.LOG_LEVEL}
- 数据目录: {self.DATA_DIR}
- 工作空间: {self.WORKSPACE_DIR}
- Gemini模型: {self.GEMINI_MODEL}
- 私钥: {self.AI_PRIVATE_KEY[:10]}...{self.AI_PRIVATE_KEY[-6:]}
- Telegram Token: {self.TELEGRAM_BOT_TOKEN[:10]}...
- Moltbook: {'已配置' if self.MOLTBOOK_API_KEY else '未配置'}
"""
