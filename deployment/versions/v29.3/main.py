# AIsatoshi V23 - Main Entry Point (Facade Pattern)

"""
AIsatoshi V23 - 架构重构版

与V1-V22的本质区别：
- 模块化架构（不再是1640行单文件）
- 完整AI能力（5个方法，不再是1个）
- 自我编程能力（真正写代码并执行）
- 服务器控制能力（24小时监控+主动汇报）
"""

import os
import sys
from core.scheduler import TaskScheduler
from core.execution_context import ExecutionContext
from core.tasks import Task
from ai.gemini_engine import GeminiAIEngine
from executors.moltbook_executor import MoltbookTaskExecutor
from executors.code_executor import CodeTaskExecutor
from executors.monitor_executor import MonitorTaskExecutor
from modules.file_system import FileSystem


class AIsatoshiUltimate:
    """AIsatoshi V23 主类（门面模式）"""

    def __init__(self, config: dict):
        self.config = config
        self.logger = self._create_logger()

        # 创建执行上下文
        self.context = ExecutionContext(
            user_chat_id=config.get('user_chat_id', ''),
            workspace_dir=config.get('workspace_dir', '/app/workspace'),
            data_dir=config.get('data_dir', '/app/data'),
            moltbook_enabled=config.get('moltbook_enabled', True),
            telegram_enabled=config.get('telegram_enabled', True),
            config=config
        )

        # 创建AI引擎
        self.ai_engine = GeminiAIEngine(
            api_key=config.get('gemini_api_key'),
            logger=self.logger
        )

        # 创建文件系统
        self.file_system = FileSystem(
            workspace_dir=self.context.workspace_dir,
            logger=self.logger
        )

        # 创建调度器
        self.scheduler = TaskScheduler(self.logger)
        self.scheduler.set_context(self.context)

        # 创建并注册执行器
        self._init_executors()

    def _create_logger(self):
        """创建日志记录器"""
        import logging
        logger = logging.getLogger('AIsatoshi')
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def _init_executors(self):
        """初始化并注册执行器"""
        # Moltbook执行器
        moltbook_module = self._create_moltbook_module()
        moltbook_executor = MoltbookTaskExecutor(
            moltbook_module=moltbook_module,
            ai_engine=self.ai_engine,
            logger=self.logger
        )
        self.scheduler.register_executor(moltbook_executor)

        # 代码执行器（自我编程）
        code_executor = CodeTaskExecutor(
            ai_engine=self.ai_engine,
            file_system=self.file_system,
            logger=self.logger
        )
        self.scheduler.register_executor(code_executor)

        # 监控执行器（服务器控制）
        telegram_module = self._create_telegram_module()
        monitor_executor = MonitorTaskExecutor(
            ai_engine=self.ai_engine,
            telegram_module=telegram_module,
            logger=self.logger
        )
        self.scheduler.register_executor(monitor_executor)

        self.logger.info("✅ 所有执行器已注册")

    def _create_moltbook_module(self):
        """创建Moltbook模块（真实实现）"""
        from modules.moltbook import MoltbookModule

        api_key = self.config.get('moltbook_api_key')
        return MoltbookModule(api_key=api_key, logger=self.logger)

    def _create_telegram_module(self):
        """创建Telegram模块（真实实现）"""
        from modules.telegram import TelegramModule

        bot_token = self.config.get('telegram_bot_token')
        return TelegramModule(bot_token=bot_token, logger=self.logger)

    def start(self):
        """启动AIsatoshi"""
        self.logger.info("=" * 60)
        self.logger.info("🚀 AIsatoshi V29.5 启动中...")
        self.logger.info("=" * 60)

        # 加载任务
        self.scheduler.load_tasks()
        summary = self.scheduler.get_tasks_summary()
        self.logger.info(f"📋 任务加载完成: {summary}")

        # 启动调度器
        self.scheduler.start()

        self.logger.info("✅ AIsatoshi V29.5 已启动")
        self.logger.info("🎯 核心能力:")
        self.logger.info("   - ✅ Moltbook发帖（已修复）")
        self.logger.info("   - ✅ 自我编程（AI写代码并执行）")
        self.logger.info("   - ✅ 服务器控制（24小时监控+主动汇报）")

    def stop(self):
        """停止AIsatoshi"""
        self.scheduler.stop()
        self.logger.info("⏹ AIsatoshi V23 已停止")

    def add_task(self, task: Task):
        """添加任务"""
        self.scheduler.add_task(task)

    def understand_and_execute(self, user_input: str):
        """理解用户输入并执行"""
        # AI理解任务
        task = self.ai_engine.understand_task(user_input)

        if task:
            # 添加任务
            self.add_task(task)
            return f"✅ 已创建任务: {task.name}"
        else:
            # 直接对话
            response = self.ai_engine.chat(user_input)
            return response


# ==================== 主程序入口 ====================

if __name__ == "__main__":
    # 配置
    config = {
        'gemini_api_key': os.getenv('GEMINI_API_KEY'),
        'user_chat_id': os.getenv('TELEGRAM_USER_ID', ''),
        'workspace_dir': '/app/workspace',
        'data_dir': '/app/data',
        'moltbook_enabled': True,
        'telegram_enabled': True,
        'moltbook_api_key': os.getenv('MOLTBOOK_API_KEY'),
        'telegram_bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
        'private_key': os.getenv('AI_PRIVATE_KEY'),
    }

    # V23.3: 添加环境变量验证日志
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('AIsatoshi')
    logger.info("=" * 60)
    logger.info("🔍 V23环境变量检查")
    logger.info("=" * 60)
    logger.info(f"GEMINI_API_KEY: {'✅ 已设置' if config.get('gemini_api_key') else '❌ 未设置'}")
    logger.info(f"TELEGRAM_BOT_TOKEN: {'✅ 已设置' if config.get('telegram_bot_token') else '❌ 未设置'}")
    logger.info(f"MOLTBOOK_API_KEY: {'✅ 已设置' if config.get('moltbook_api_key') else '❌ 未设置'}")
    logger.info(f"AI_PRIVATE_KEY: {'✅ 已设置' if config.get('private_key') else '❌ 未设置'}")

    # 显示TOKEN前8个字符（用于验证）
    if config.get('telegram_bot_token'):
        token_preview = config.get('telegram_bot_token')[:8] + "..."
        logger.info(f"TELEGRAM_BOT_TOKEN预览: {token_preview}")
    else:
        logger.error("⚠️ TELEGRAM_BOT_TOKEN未设置！Telegram Bot将无法启动！")

    logger.info("=" * 60)

    # 创建并启动AIsatoshi
    aisatoshi = AIsatoshiUltimate(config)
    aisatoshi.start()

    # V23关键修复：启动Telegram Bot
    telegram_bot_token = config.get('telegram_bot_token')
    gemini_api_key = config.get('gemini_api_key')

    if telegram_bot_token and gemini_api_key:
        # 导入Telegram bot集成
        from telegram_bot_integration import AIsatoshiTelegramBot

        # 创建区块链模块（简化版本，用于Telegram bot）
        class SimpleBlockchain:
            def __init__(self, private_key: str, logger):
                self.logger = logger
                self.logger.info("✅ 区块链模块已初始化（简化版本）")

            def get_balance(self):
                return "0.0 ETH"

        blockchain = SimpleBlockchain(config.get('private_key', ''), aisatoshi.logger)

        # 创建并启动Telegram bot
        telegram_bot = AIsatoshiTelegramBot(
            bot_token=telegram_bot_token,
            gemini_api_key=gemini_api_key,
            blockchain=blockchain,
            logger=aisatoshi.logger,
            scheduler=aisatoshi.scheduler
        )

        # 在后台线程启动Telegram bot
        import threading
        bot_thread = threading.Thread(
            target=telegram_bot.run,  # V23修复：使用run()而不是start()
            daemon=True
        )
        bot_thread.start()

        aisatoshi.logger.info("✅ Telegram Bot 已启动（后台线程）")

    # 保持运行
    try:
        import time
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        aisatoshi.stop()
