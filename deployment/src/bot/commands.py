#!/usr/bin/env python3
"""
AIsatoshi V30.0 - 命令处理模块
"""

import logging
from typing import Dict, Any, Callable
from ..config import config


class CommandHandler:
    """命令处理器"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.commands: Dict[str, Callable] = {}

        # 注册基础命令
        self._register_commands()

    def _register_commands(self):
        """注册命令"""
        self.commands = {
            '/start': self.cmd_start,
            '/help': self.cmd_help,
            '/price': self.cmd_price,
            '/balance': self.cmd_balance,
            '/status': self.cmd_status,
            '/tasks': self.cmd_tasks,
        }

    def handle(self, chat_id: str, command: str, args: str = "") -> bool:
        """处理命令"""
        handler = self.commands.get(command)
        if handler:
            try:
                handler(chat_id, args)
                return True
            except Exception as e:
                self.logger.error(f"[Commands] {command} 执行失败: {e}")
                return False
        return False

    def cmd_start(self, chat_id: str, args: str):
        """启动命令"""
        self.logger.info(f"[Commands] /start from {chat_id}")

    def cmd_help(self, chat_id: str, args: str):
        """帮助命令"""
        self.logger.info(f"[Commands] /help from {chat_id}")

    def cmd_price(self, chat_id: str, args: str):
        """查询价格"""
        self.logger.info(f"[Commands] /price {args}")

    def cmd_balance(self, chat_id: str, args: str):
        """查询余额"""
        self.logger.info(f"[Commands] /balance from {chat_id}")

    def cmd_status(self, chat_id: str, args: str):
        """状态查询"""
        self.logger.info(f"[Commands] /status from {chat_id}")

    def cmd_tasks(self, chat_id: str, args: str):
        """任务列表"""
        self.logger.info(f"[Commands] /tasks from {chat_id}")


def create_command_handler(logger: logging.Logger) -> CommandHandler:
    """创建命令处理器"""
    return CommandHandler(logger)
