#!/usr/bin/env python3
"""
AIsatoshi V30.0 - 主入口
"""

import os
import sys
import logging
import signal
import threading
import time

# 添加 src 到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from bot.telegram import create_telegram_bot
from bot.commands import create_command_handler
from bot.message_handler import create_message_handler
from memory.storage import create_memory_storage
from blockchain.wallet import create_wallet


class AIsatoshi:
    """AIsatoshi V30.0 主应用"""

    def __init__(self):
        self.logger = self._setup_logging()
        self.running = False

        # 验证配置
        if not config.validate():
            self.logger.error("❌ 配置验证失败，请检查环境变量")
            sys.exit(1)

        # 初始化模块
        self.memory = create_memory_storage(self.logger)
        self.wallet = create_wallet(self.logger)

        # Telegram Bot
        self.telegram = create_telegram_bot(self.logger)
        self.commands = create_command_handler(self.logger)
        self.message_handler = create_message_handler(
            self.logger,
            self.telegram,
            self.commands
        )

        # 设置消息回调
        self.telegram.on_message = self.message_handler.handle

        # 钱包地址
        self.address = self.wallet.get_address()
        self.logger.info(f"📍 钱包地址: {self.address}")

    def _setup_logging(self) -> logging.Logger:
        """设置日志"""
        logging.basicConfig(
            level=getattr(logging, config.LOG_LEVEL),
            format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        return logging.getLogger(__name__)

    def start(self):
        """启动应用"""
        self.running = True

        # 打印启动信息
        self._print_banner()

        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # 启动 Telegram 轮询（在后台线程）
        self.polling_thread = threading.Thread(
            target=self.telegram.start_polling,
            daemon=True
        )
        self.polling_thread.start()

        self.logger.info("✅ AIsatoshi V30.0 已启动")

        # 主线程等待
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

        self.stop()

    def stop(self):
        """停止应用"""
        self.running = False
        self.telegram.stop()
        self.memory.save()
        self.logger.info("👋 AIsatoshi 已停止")

    def _signal_handler(self, signum, frame):
        """信号处理器"""
        self.logger.info(f"收到信号 {signum}，正在停止...")
        self.stop()
        sys.exit(0)

    def _print_banner(self):
        """打印启动信息"""
        print(f"""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║   🤖 AIsatoshi V{config.VERSION}                                 ║
║   构建: {config.BUILD_DATE}                              ║
║                                                            ║
║   ✅ 分段发送消息            ✅ 深度浏览网页               ║
║   ✅ AI 自然语言理解         ✅ 记忆系统                   ║
║   ✅ Playwright 完整浏览器   ✅ 钱包操作                   ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
        """)


def main():
    """主入口"""
    app = AIsatoshi()
    app.start()


if __name__ == "__main__":
    main()
