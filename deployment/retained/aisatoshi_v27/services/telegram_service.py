"""
AIsatoshi V27 - Telegram服务

处理Telegram Bot的所有交互。
"""

import time
import requests
from typing import Dict, Any, Optional, List, Callable
from core.config import Config
from core.logger import Logger
from core.exceptions import TelegramServiceError
from models.message import TelegramMessage, MessageEntity


class TelegramService:
    """Telegram服务

    处理所有Telegram Bot交互。
    """

    def __init__(self, config: Config, logger: Optional[Logger] = None):
        """初始化Telegram服务

        Args:
            config: 配置对象
            logger: 日志记录器
        """
        self.config = config
        self.logger = logger or Logger(name="TelegramService")

        self.token = config.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.token}"

        # 消息处理器
        self.commands: Dict[str, Callable] = {}
        self.default_handler: Optional[Callable] = None

        # 状态
        self.running = False
        self.offset = 0

        # 自动chat_id管理
        self.user_chat_id: Optional[str] = config.TELEGRAM_USER_ID

        # 消息去重
        self.processed_messages = set()

        self.logger.info("Telegram服务已初始化")

    def register_command(self, command: str, handler: Callable):
        """注册命令处理器

        Args:
            command: 命令（带/前缀）
            handler: 处理函数
        """
        self.commands[command] = handler
        self.logger.debug(f"命令已注册: {command}")

    def set_default_handler(self, handler: Callable):
        """设置默认处理器

        Args:
            handler: 处理函数
        """
        self.default_handler = handler

    # === 消息发送 ===

    def send_message(self, chat_id: str, text: str,
                    parse_mode: str = "Markdown",
                    disable_preview: bool = True) -> bool:
        """发送消息

        Args:
            chat_id: 聊天ID
            text: 消息内容
            parse_mode: 解析模式
            disable_preview: 是否禁用预览

        Returns:
            是否成功
        """
        # 处理长消息（Telegram限制4096字符）
        messages = self._split_long_message(text)

        for msg in messages:
            try:
                data = {
                    'chat_id': chat_id,
                    'text': msg,
                    'parse_mode': parse_mode,
                    'disable_web_page_preview': disable_preview,
                }

                response = requests.post(
                    f"{self.base_url}/sendMessage",
                    json=data,
                    timeout=30
                )
                response.raise_for_status()

                self.logger.telegram_message("out", msg)

            except requests.RequestException as e:
                self.logger.telegram_error(str(e))
                return False

        return True

    def send_markdown(self, chat_id: str, text: str) -> bool:
        """发送Markdown格式的消息

        Args:
            chat_id: 聊天ID
            text: Markdown文本

        Returns:
            是否成功
        """
        return self.send_message(chat_id, text, parse_mode="Markdown")

    def send_plain(self, chat_id: str, text: str) -> bool:
        """发送纯文本消息

        Args:
            chat_id: 聊天ID
            text: 文本内容

        Returns:
            是否成功
        """
        return self.send_message(chat_id, text, parse_mode="")

    # === 消息接收 ===

    def get_updates(self, timeout: int = 30) -> List[Dict]:
        """获取更新

        Args:
            timeout: 超时时间

        Returns:
            更新列表
        """
        try:
            params = {
                'offset': self.offset,
                'timeout': timeout,
                'allowed_updates': ['message']
            }

            response = requests.get(
                f"{self.base_url}/getUpdates",
                params=params,
                timeout=timeout + 10
            )
            response.raise_for_status()

            data = response.json()

            if data.get('ok'):
                return data.get('result', [])
            return []

        except requests.RequestException as e:
            self.logger.telegram_error(f"获取更新失败: {e}")
            return []

    def process_updates(self, updates: List[Dict]):
        """处理更新

        Args:
            updates: 更新列表
        """
        for update in updates:
            # 更新offset
            self.offset = update['update_id'] + 1

            # 提取消息
            message = update.get('message', {})
            if not message:
                continue

            # 解析消息
            try:
                telegram_msg = self._parse_message(message)

                # 检查是否已处理
                msg_key = f"{telegram_msg.chat_id}_{telegram_msg.message_id}"
                if msg_key in self.processed_messages:
                    continue
                self.processed_messages.add(msg_key)

                # 限制去重set大小
                if len(self.processed_messages) > 10000:
                    old_keys = list(self.processed_messages)[:5000]
                    for key in old_keys:
                        self.processed_messages.discard(key)

                # 自动设置chat_id
                if not self.user_chat_id:
                    self.user_chat_id = telegram_msg.chat_id
                    self.logger.info(f"自动设置chat_id: {self.user_chat_id}")

                # 处理消息
                self._handle_message(telegram_msg)

            except Exception as e:
                self.logger.error(f"处理消息失败: {e}")

    def _parse_message(self, message: Dict) -> TelegramMessage:
        """解析Telegram消息

        Args:
            message: 原始消息字典

        Returns:
            TelegramMessage对象
        """
        chat = message.get('chat', {})
        from_user = message.get('from', {})

        chat_id = str(chat.get('id', ''))
        message_id = message.get('message_id', 0)
        text = message.get('text', '')
        from_name = from_user.get('username', from_user.get('first_name', 'Unknown'))

        # 解析entities
        entities = []
        for entity in message.get('entities', []):
            entity_type = entity.get('type', '')
            entities.append(MessageEntity(
                type=entity_type,
                offset=entity.get('offset', 0),
                length=entity.get('length', 0),
                url=entity.get('url'),
            ))

        # 检查是否是命令
        is_command = text.startswith('/')

        return TelegramMessage(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            from_user=from_name,
            is_command=is_command,
            entities=entities,
        )

    def _handle_message(self, message: TelegramMessage):
        """处理消息

        Args:
            message: TelegramMessage对象
        """
        self.logger.telegram_message("in", message.text)

        text = message.text.strip()

        # 检查是否是命令
        if message.is_command:
            parts = text.split(maxsplit=1)
            command = parts[0]
            args = parts[1] if len(parts) > 1 else ""

            if command in self.commands:
                self.commands[command](message, args)
            else:
                self.send_message(
                    message.chat_id,
                    f"未知命令: {command}\n使用 /help 查看可用命令"
                )
        else:
            # 自然语言处理
            if self.default_handler:
                self.default_handler(message)
            else:
                self.send_message(
                    message.chat_id,
                    "我没有理解你的请求。使用 /help 查看我能做什么。"
                )

    # === 运行循环 ===

    def run(self):
        """运行Telegram Bot主循环"""
        self.running = True
        self.logger.info("Telegram Bot已启动")

        while self.running:
            try:
                # 获取更新
                updates = self.get_updates(
                    timeout=self.config.TELEGRAM_GETUPDATES_TIMEOUT
                )

                # 处理更新
                if updates:
                    self.process_updates(updates)

            except KeyboardInterrupt:
                self.logger.info("收到停止信号")
                break
            except Exception as e:
                self.logger.error(f"主循环错误: {e}")
                time.sleep(5)

    def stop(self):
        """停止Bot"""
        self.running = False
        self.logger.info("Telegram Bot已停止")

    # === 工具方法 ===

    def _split_long_message(self, text: str, max_length: int = 4000) -> List[str]:
        """智能分割长消息

        优化点：
        1. 保留代码块完整性
        2. 在句子边界分割
        3. 添加分页标记（1/2）

        Args:
            text: 原文本
            max_length: 最大长度（Telegram限制4096，留一些余量）

        Returns:
            消息列表
        """
        if len(text) <= max_length:
            return [text]

        messages = []

        # 首先检查是否包含代码块
        code_blocks = []
        def extract_code_block(match):
            code_blocks.append(match.group(0))
            return f"__CODE_BLOCK_{len(code_blocks)-1}__"

        # 提取代码块
        import re
        text_processed = re.sub(r'```[\s\S]*?```', extract_code_block, text)

        # 按段落分割
        paragraphs = text_processed.split('\n\n')

        current = ""
        for paragraph in paragraphs:
            # 检查是否需要分割
            test_len = len(current) + len(paragraph) + 2
            if test_len > max_length and current:
                # 当前段落会超长，先保存当前内容
                messages.append(current.strip())
                current = paragraph
            elif test_len > max_length:
                # 单个段落就超长，需要强制分割
                if current:
                    messages.append(current.strip())
                # 在句子边界分割
                sentences = paragraph.replace('。', '。\n').replace('！', '！\n').replace('？', '？\n').split('\n')
                for sentence in sentences:
                    if len(current) + len(sentence) + 1 > max_length:
                        if current:
                            messages.append(current.strip())
                        current = sentence
                    else:
                        if current:
                            current += ' ' + sentence
                        else:
                            current = sentence
                if current:
                    messages.append(current.strip())
                    current = ""
            else:
                if current:
                    current += '\n\n' + paragraph
                else:
                    current = paragraph

        if current:
            messages.append(current.strip())

        # 恢复代码块
        final_messages = []
        for msg in messages:
            # 恢复代码块标记
            for i, code in enumerate(code_blocks):
                msg = msg.replace(f"__CODE_BLOCK_{i}__", code)
            final_messages.append(msg)

        # 如果消息仍然太长，强制分割
        result = []
        for msg in final_messages:
            while len(msg) > max_length:
                result.append(msg[:max_length])
                msg = msg[max_length:]
            if msg:
                result.append(msg)

        # 添加分页标记
        if len(result) > 1:
            result = [
                f"{msg}\n\n__({i+1}/{len(result)})__"
                for i, msg in enumerate(result)
            ]

        return result

    def get_chat_id(self) -> Optional[str]:
        """获取当前chat_id

        Returns:
            chat_id或None
        """
        return self.user_chat_id

    def get_me(self) -> Optional[Dict]:
        """获取Bot信息

        Returns:
            Bot信息字典
        """
        try:
            response = requests.get(f"{self.base_url}/getMe", timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('result') if data.get('ok') else None
        except requests.RequestException:
            return None
