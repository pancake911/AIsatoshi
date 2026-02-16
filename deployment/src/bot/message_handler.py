#!/usr/bin/env python3
"""
AIsatoshi V30.0 - 消息处理模块
"""

import logging
import re
from typing import Dict, Any, Optional
from ..config import config
from .telegram import TelegramBot
from .commands import CommandHandler
from ..ai.gemini import create_gemini_client
from ..browser.deep_browse import create_deep_browser
from ..browser.scraper import create_scraper


class MessageHandler:
    """消息处理器"""

    def __init__(
        self,
        logger: logging.Logger,
        telegram_bot: TelegramBot,
        command_handler: CommandHandler
    ):
        self.logger = logger
        self.telegram = telegram_bot
        self.commands = command_handler

        # AI 和浏览器
        self.ai_client = create_gemini_client(logger)
        self.browser = create_deep_browser(logger)
        self.scraper = create_scraper(logger)

        # 记忆（简单版本）
        self.chat_history: Dict[str, list] = {}

    def handle(self, message: dict):
        """处理消息"""
        try:
            chat_id = str(message.get('chat', {}).get('id', ''))
            text = message.get('text', '').strip()

            if not text:
                return

            self.logger.info(f"[Message] 来自 {chat_id}: {text[:50]}")

            # 初始化聊天历史
            if chat_id not in self.chat_history:
                self.chat_history[chat_id] = []

            # 检查是否是命令
            if text.startswith('/'):
                parts = text.split(maxsplit=1)
                command = parts[0]
                args = parts[1] if len(parts) > 1 else ""

                if self.commands.handle(chat_id, command, args):
                    return

            # 处理自然语言
            self._handle_natural_language(chat_id, text, message)

        except Exception as e:
            self.logger.error(f"[Message] 处理失败: {e}")

    def _handle_natural_language(self, chat_id: str, text: str, message: dict):
        """处理自然语言消息"""
        # 发送"正在思考"
        self.telegram.send_message(chat_id, "🤔 正在思考...")

        # 检查是否有 URL
        urls = self._extract_urls(text, message)

        # 如果有 URL 且包含浏览关键词，直接浏览
        browse_keywords = ['浏览', '访问', '看看', '查看', '研究', '调研', '分析', '深度']
        if urls and any(kw in text for kw in browse_keywords):
            url = urls[0]
            self.logger.info(f"[Message] 检测到浏览请求: {url}")
            self._execute_browse(chat_id, url, text)
            return

        # AI 理解意图
        history = self.chat_history.get(chat_id, [])
        context = self._build_context(history)

        result = self.ai_client.chat(text, context, history)

        self.logger.info(f"[Message] AI 意图: {result.get('action')}")

        # 执行操作
        action = result.get('action', 'chat')
        params = result.get('params', {})
        response_text = result.get('response', '')

        if action == 'browse':
            url = params.get('url', urls[0] if urls else '')
            if url:
                question = params.get('question', f"这个网站是做什么的？")
                self._execute_browse(chat_id, url, question)
            else:
                self.telegram.send_message(chat_id, "❓ 请提供要浏览的网址")

        elif action == 'price':
            coin = params.get('coin', 'eth')
            self._execute_price(chat_id, coin)

        elif action == 'balance':
            self._execute_balance(chat_id)

        elif action == 'chat':
            # 直接使用 AI 的回复
            if response_text:
                self.telegram.send_message(chat_id, response_text)
            else:
                # 用 AI 生成回复
                from ..ai.prompts import CHAT_PROMPT
                prompt = CHAT_PROMPT.format(
                    context=context,
                    message=text
                )
                reply = self.ai_client.generate_content(prompt)
                self.telegram.send_message(chat_id, reply)

        # 保存到历史
        self.chat_history[chat_id].append({
            'role': 'user',
            'content': text,
            'action': action
        })

        # 限制历史长度
        if len(self.chat_history[chat_id]) > 50:
            self.chat_history[chat_id] = self.chat_history[chat_id][-50:]

    def _execute_browse(self, chat_id: str, url: str, question: str):
        """执行浏览"""
        try:
            self.telegram.send_message(chat_id, f"🌐 正在访问 {url}...")

            # 检查是否需要深度浏览
            deep_keywords = ['深度', '调研', '详细', '全面', '研究']
            need_deep = any(kw in question for kw in deep_keywords)

            if need_deep:
                # 深度浏览
                def progress_cb(current, total):
                    self.telegram.send_message(chat_id, f"🔍 深度浏览中... ({current}/{total})")

                result = self.browser.browse(url, question, max_pages=5, progress_callback=progress_cb)

                if result.get('success'):
                    self.telegram.send_message(
                        chat_id,
                        f"✅ 深度浏览完成，访问了 {result['pages_visited']} 个页面\n"
                        f"📄 正在分析 {result['total_chars']} 字符..."
                    )

                    content = result.get('all_content', '')
                    analysis = self.ai_client.analyze_webpage(content, question)
                    self.telegram.send_message(chat_id, f"✅ 分析结果：\n\n{analysis}")
                else:
                    self.telegram.send_message(chat_id, f"❌ 浏览失败: {result.get('error', '未知错误')}")

            else:
                # 单页面浏览
                result = self.scraper.fetch(url, timeout=30000)

                if result.get('success'):
                    self.telegram.send_message(
                        chat_id,
                        f"✅ 网页内容已获取（{result['char_count']} 字符），正在分析..."
                    )

                    content = result.get('content', '')
                    analysis = self.ai_client.analyze_webpage(content, question)
                    self.telegram.send_message(chat_id, f"✅ 分析结果：\n\n{analysis}")
                else:
                    self.telegram.send_message(chat_id, f"❌ 无法访问该网页")

        except Exception as e:
            self.logger.error(f"[Message] 浏览失败: {e}")
            self.telegram.send_message(chat_id, f"❌ 浏览失败: {str(e)[:100]}")

    def _execute_price(self, chat_id: str, coin: str):
        """查询价格"""
        # TODO: 实现价格查询
        self.telegram.send_message(chat_id, f"💰 {coin.upper()} 价格查询功能开发中...")

    def _execute_balance(self, chat_id: str):
        """查询余额"""
        # TODO: 实现余额查询
        self.telegram.send_message(chat_id, "💰 钱包余额查询功能开发中...")

    def _extract_urls(self, text: str, message: dict) -> list:
        """提取 URL"""
        urls = []

        # 从 entities 提取
        entities = message.get('entities', [])
        for entity in entities:
            if entity.get('type') in ['url', 'link']:
                offset = entity.get('offset', 0)
                length = entity.get('length', 0)
                if offset + length <= len(text):
                    url = text[offset:offset + length]
                    urls.append(url)

        # 从文本中提取（正则）
        url_pattern = r'https?://[^\s]+'
        urls.extend(re.findall(url_pattern, text))

        return list(set(urls))  # 去重

    def _build_context(self, history: list) -> str:
        """构建上下文"""
        if not history:
            return ""

        recent = history[-10:]
        context = "\n【最近对话】\n"
        for msg in recent:
            role = "用户" if msg.get('role') == 'user' else "AIsatoshi"
            content = msg.get('content', '')[:150]
            context += f"{role}: {content}\n"

        return context


def create_message_handler(
    logger: logging.Logger,
    telegram_bot: TelegramBot,
    command_handler: CommandHandler
) -> MessageHandler:
    """创建消息处理器"""
    return MessageHandler(logger, telegram_bot, command_handler)
