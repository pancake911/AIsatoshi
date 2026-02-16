#!/usr/bin/env python3
"""
AIsatoshi V30.0 - Telegram Bot 模块
支持分段发送消息
"""

import logging
import requests
from typing import Optional, Callable
from ..config import config


class TelegramBot:
    """Telegram Bot 客户端"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.token = config.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.running = True
        self.offset = 0

        # 消息处理回调
        self.on_message: Optional[Callable] = None

    def _send_single(
        self,
        chat_id: str,
        text: str,
        parse_mode: Optional[str] = None
    ) -> bool:
        """发送单条消息"""
        try:
            data = {
                'chat_id': chat_id,
                'text': text,
                'disable_web_page_preview': True
            }

            # 只在 parse_mode 不是 None 时才发送该字段
            if parse_mode is not None:
                data['parse_mode'] = parse_mode

            response = requests.post(
                f"{self.base_url}/sendMessage",
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                self.logger.debug(f"[Telegram] 消息已发送: {len(text)} 字符")
                return True
            else:
                self.logger.error(f"[Telegram] 发送失败: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            self.logger.error(f"[Telegram] 发送消息异常: {e}")
            return False

    def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: Optional[str] = None
    ) -> bool:
        """发送消息（支持分段）"""
        try:
            max_length = config.MAX_MESSAGE_LENGTH

            if len(text) > max_length:
                self.logger.info(f"[Telegram] 消息过长 ({len(text)} 字符)，分段发送")

                # 分段发送
                chunks = (len(text) + max_length - 1) // max_length
                for i in range(chunks):
                    chunk = text[i * max_length:(i + 1) * max_length]
                    if not self._send_single(chat_id, chunk, parse_mode):
                        self.logger.warning(f"[Telegram] 第 {i+1} 段发送失败")

                return True

            # 短消息直接发送
            return self._send_single(chat_id, text, parse_mode)

        except Exception as e:
            self.logger.error(f"[Telegram] send_message 失败: {e}")
            return False

    def get_updates(self, timeout: int = 30) -> list:
        """获取更新"""
        try:
            params = {
                'offset': self.offset,
                'timeout': timeout
            }

            response = requests.get(
                f"{self.base_url}/getUpdates",
                params=params,
                timeout=timeout + 10
            )

            if response.status_code == 200:
                data = response.json()
                updates = data.get('result', [])

                if updates:
                    self.offset = updates[-1]['update_id'] + 1

                return updates

            return []

        except Exception as e:
            self.logger.error(f"[Telegram] get_updates 失败: {e}")
            return []

    def process_updates(self, updates: list):
        """处理更新"""
        for update in updates:
            if 'message' in update:
                message = update['message']
                if self.on_message:
                    self.on_message(message)

    def start_polling(self):
        """开始轮询"""
        self.logger.info(f"[Telegram] 开始轮询...")

        while self.running:
            try:
                updates = self.get_updates()
                if updates:
                    self.logger.info(f"[Telegram] 收到 {len(updates)} 条消息")
                    self.process_updates(upsates)

            except Exception as e:
                self.logger.error(f"[Telegram] 轮询错误: {e}")

    def stop(self):
        """停止轮询"""
        self.running = False
        self.logger.info(f"[Telegram] 停止轮询")


def create_telegram_bot(logger: logging.Logger) -> TelegramBot:
    """创建 Telegram Bot 实例"""
    return TelegramBot(logger)
