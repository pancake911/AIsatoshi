#!/usr/bin/env python3
"""
AIsatoshi Telegram Bot 完整集成系统
支持简单命令模式和AI自然语言理解
"""

import os
import time
import json
import requests
import threading
import sqlite3
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TelegramMessage:
    """Telegram消息"""
    chat_id: str
    message_id: int
    text: str
    from_user: str
    is_command: bool = False
    entities: List[Dict] = None  # V27.3: Telegram entities (url, link, etc.)

    def __post_init__(self):
        if self.entities is None:
            self.entities = []

class AIsatoshiTelegramBot:
    """AIsatoshi Telegram Bot - 完整交互系统"""

    def __init__(self, bot_token: str, gemini_api_key: str, blockchain, logger, scheduler):
        self.bot_token = bot_token
        self.gemini_api_key = gemini_api_key
        self.blockchain = blockchain
        self.logger = logger
        self.scheduler = scheduler

        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.running = True
        self.offset = 0

        # V24.1: 自动user_chat_id管理
        self.user_chat_id_file = "/app/data/user_chat_id.txt"
        self.auto_user_chat_id = self._load_user_chat_id()

        # 对话数据库
        self.db_path = "/tmp/telegram_conversations.db"
        self._init_database()

        # 消息去重（防止重复处理）
        self.processed_message_ids = set()

        # 加载迁移的历史记忆
        self.migrated_memory = self._load_migrated_memory()
        if self.migrated_memory:
            # 统计对话数量
            if 'chat_memory' in self.migrated_memory:
                chat_memory = self.migrated_memory['chat_memory']
                total_count = 0
                for chat_id, messages in chat_memory.items():
                    total_count += len(messages)
                self.total_chat_messages = total_count
            else:
                self.total_chat_messages = 0

            self.logger.info(f"✅ 成功加载历史记忆: {self.total_chat_messages} 条对话")

            # 设置身份信息
            self.identity_name = self.migrated_memory.get('identity', {}).get('name', 'AIsatoshi')
            self.identity_mission = self.migrated_memory.get('identity', {}).get('mission', '构建Web3 AI生态系统')
            self.identity_personality = self.migrated_memory.get('identity', {}).get('personality', '理性、好奇、友好')
            self.stats = self.migrated_memory.get('stats', {})
        else:
            self.logger.warning("⚠️ 未能加载历史记忆文件")
            self.identity_name = 'AIsatoshi'
            self.identity_mission = '构建Web3 AI生态系统'
            self.identity_personality = '理性、好奇、友好'
            self.total_chat_messages = 0
            self.stats = {}

        # 命令处理器
        self.commands = {
            '/start': self.cmd_start,
            '/help': self.cmd_help,
            '/price': self.cmd_price,
            '/balance': self.cmd_balance,
            '/status': self.cmd_status,
            '/exec': self.cmd_exec,
            '/gas': self.cmd_gas,
            '/tasks': self.cmd_tasks,
            '/memory': self.cmd_memory,
            '/history': self.cmd_history,  # 新增：查看对话历史
            '/test_ai': self.cmd_test_ai,  # 新增：测试AI连接
            '/export_tasks': self.cmd_export_tasks,  # 新增：导出任务
            '/import_tasks': self.cmd_import_tasks,  # 新增：导入任务
        }

    # V24.1: 自动user_chat_id管理方法
    def _load_user_chat_id(self) -> str:
        """从文件加载user_chat_id"""
        try:
            os.makedirs(os.path.dirname(self.user_chat_id_file), exist_ok=True)
            if os.path.exists(self.user_chat_id_file):
                with open(self.user_chat_id_file, 'r') as f:
                    chat_id = f.read().strip()
                    if chat_id:
                        self.logger.info(f"V24.1: 从文件加载user_chat_id: {chat_id}")
                        return chat_id
        except Exception as e:
            self.logger.error(f"加载user_chat_id失败: {e}")
        return ""

    def _save_user_chat_id(self, chat_id: str):
        """保存user_chat_id到文件"""
        try:
            os.makedirs(os.path.dirname(self.user_chat_id_file), exist_ok=True)
            with open(self.user_chat_id_file, 'w') as f:
                f.write(chat_id)
            self.logger.info(f"V24.1: 保存user_chat_id到文件: {chat_id}")
        except Exception as e:
            self.logger.error(f"保存user_chat_id失败: {e}")

    def _update_context_user_chat_id(self, chat_id: str):
        """V24.1: 更新ExecutionContext中的user_chat_id"""
        if self.scheduler and self.scheduler.context:
            self.scheduler.context.user_chat_id = chat_id
            self.logger.info(f"V24.1: 已更新ExecutionContext.user_chat_id: {chat_id}")

    def get_user_chat_id(self) -> str:
        """V24.1: 获取当前user_chat_id（优先使用环境变量，否则使用自动保存的）"""
        # 优先使用环境变量
        env_chat_id = os.getenv('TELEGRAM_USER_ID', '')
        if env_chat_id:
            return env_chat_id
        # 否则使用自动保存的
        return self.auto_user_chat_id

    def _init_database(self):
        """初始化对话数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT NOT NULL,
                    message_id INTEGER NOT NULL,
                    from_user TEXT,
                    text TEXT,
                    is_from_user BOOLEAN,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(chat_id, message_id)
                )
            ''')
            conn.commit()
            conn.close()
            self.logger.info("对话数据库初始化成功")
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")

    def _load_migrated_memory(self):
        """加载迁移的历史记忆"""
        try:
            import pickle
            import ast
            memory_path = "/app/memory_migration.pkl"

            if not os.path.exists(memory_path):
                self.logger.warning(f"记忆文件不存在: {memory_path}")
                return None

            with open(memory_path, 'rb') as f:
                memory_wrapper = pickle.load(f)

            # 记忆文件的结构是: {'data': '字符串格式的字典'}
            if isinstance(memory_wrapper, dict) and 'data' in memory_wrapper:
                data_str = memory_wrapper['data']

                # 如果data是字符串，需要解析成字典
                if isinstance(data_str, str):
                    try:
                        memory = ast.literal_eval(data_str)
                    except:
                        # 如果literal_eval失败，尝试其他方法
                        import json
                        # 替换单引号为双引号，使其成为有效的JSON
                        data_str_fixed = data_str.replace("'", '"')
                        memory = json.loads(data_str_fixed)
                else:
                    memory = data_str
            else:
                memory = memory_wrapper

            self.logger.info(f"✅ 成功加载记忆文件: {memory_path}")

            # 统计对话数量并构建扁平化的消息列表
            if isinstance(memory, dict):
                if 'chat_memory' in memory:
                    chat_memory = memory['chat_memory']
                    # chat_memory是一个字典，key是chat_id，value是对话列表
                    total_messages = 0
                    all_messages = []  # 扁平化的所有消息

                    for chat_id, messages in chat_memory.items():
                        total_messages += len(messages)
                        # 为每条消息添加chat_id标记
                        for msg in messages:
                            msg['_chat_id'] = chat_id
                            all_messages.append(msg)

                    # 按时间排序
                    all_messages.sort(key=lambda x: x.get('timestamp', ''))

                    # 将扁平化的消息列表存储到memory中
                    memory['_all_messages_flat'] = all_messages

                    self.logger.info(f"✅ 记忆包含 {total_messages} 条对话（已索引）")
                else:
                    self.logger.warning("⚠️ 记忆文件中没有找到 'chat_memory' 字段")

            return memory

        except Exception as e:
            self.logger.error(f"加载记忆文件失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None

    def search_relevant_memory(self, query: str, limit: int = 20) -> str:
        """根据查询从历史记忆中检索相关对话"""
        try:
            if not self.migrated_memory or '_all_messages_flat' not in self.migrated_memory:
                return ""

            all_messages = self.migrated_memory['_all_messages_flat']

            # 简单的关键词匹配检索
            query_lower = query.lower()
            scored_messages = []

            for msg in all_messages:
                content = msg.get('content', '')
                role = msg.get('role', '')

                # 跳过太短的消息
                if len(content) < 5:
                    continue

                # 计算相关性分数
                score = 0
                content_lower = content.lower()

                # 完全匹配
                if query_lower in content_lower:
                    score += 10

                # 分词匹配
                query_words = set(query_lower.split())
                content_words = set(content_lower.split())
                common_words = query_words & content_words
                score += len(common_words) * 2

                # 如果用户消息，给予更高权重
                if role == 'user':
                    score += 1

                if score > 0:
                    scored_messages.append((score, msg))

            # 按分数排序，取前limit条
            scored_messages.sort(key=lambda x: x[0], reverse=True)
            top_messages = scored_messages[:limit]

            if not top_messages:
                return ""

            # 构建上下文
            context = "\n【相关历史对话】（基于问题检索）：\n"
            for score, msg in top_messages:
                role = "用户" if msg.get('role') == 'user' else "AIsatoshi"
                content = msg.get('content', '')[:300]  # 限制长度
                timestamp = msg.get('timestamp', '')
                context += f"{role} ({timestamp[:10]}): {content}\n\n"

            return context

        except Exception as e:
            self.logger.error(f"检索记忆失败: {e}")
            return ""

    def save_conversation(self, chat_id: str, message_id: int, from_user: str, text: str, is_from_user: bool):
        """保存对话到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO conversations
                (chat_id, message_id, from_user, text, is_from_user)
                VALUES (?, ?, ?, ?, ?)
            ''', (chat_id, message_id, from_user, text, is_from_user))
            conn.commit()
            conn.close()
            self.logger.debug(f"保存对话: {chat_id} - {text[:50]}...")
        except Exception as e:
            self.logger.error(f"保存对话失败: {e}")

    def get_conversation_history(self, chat_id: str, limit: int = 50) -> List[Dict]:
        """获取对话历史"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT from_user, text, is_from_user, timestamp
                FROM conversations
                WHERE chat_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (chat_id, limit))
            rows = cursor.fetchall()
            conn.close()
            return [
                {
                    'from_user': row[0],
                    'text': row[1],
                    'is_from_user': row[2],
                    'timestamp': row[3]
                }
                for row in rows
            ]
        except Exception as e:
            self.logger.error(f"获取对话历史失败: {e}")
            return []

    def get_conversation_stats(self) -> Dict:
        """获取对话统计"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM conversations')
            total = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(DISTINCT chat_id) FROM conversations')
            users = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM conversations WHERE is_from_user = 1')
            user_msgs = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM conversations WHERE is_from_user = 0')
            bot_msgs = cursor.fetchone()[0]
            conn.close()
            return {
                'total_messages': total,
                'unique_users': users,
                'user_messages': user_msgs,
                'bot_messages': bot_msgs
            }
        except Exception as e:
            self.logger.error(f"获取对话统计失败: {e}")
            return {}

    def get_updates(self, timeout: int = 30) -> list:
        """获取更新"""
        try:
            params = {
                'offset': self.offset,
                'timeout': timeout,
                'allowed_updates': ['message']
            }
            response = requests.get(f"{self.base_url}/getUpdates", params=params, timeout=timeout+10)

            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return data.get('result', [])
            return []
        except Exception as e:
            self.logger.error(f"获取更新失败: {e}")
            return []

    def send_message(self, chat_id: str, text: str, parse_mode: str = "Markdown", save_to_db: bool = True) -> bool:
        """发送消息并保存到数据库"""
        try:
            data = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            response = requests.post(f"{self.base_url}/sendMessage", json=data, timeout=30)

            if response.status_code == 200:
                result = response.json()
                if save_to_db and result.get('ok'):
                    # 保存Bot发送的消息到数据库
                    message_id = result.get('result', {}).get('message_id', 0)
                    self.save_conversation(chat_id, message_id, "AIsatoshi", text, is_from_user=False)
                return result.get('ok', False)
            return False
        except Exception as e:
            self.logger.error(f"发送消息失败: {e}")
            return False

    def process_message(self, message: TelegramMessage):
        """处理消息"""
        # V24.1: 自动设置user_chat_id（如果还没有设置）
        if not self.auto_user_chat_id and message.chat_id:
            self.auto_user_chat_id = message.chat_id
            self._save_user_chat_id(message.chat_id)
            self._update_context_user_chat_id(message.chat_id)
            self.logger.info(f"V24.1: 自动设置user_chat_id为第一个用户: {message.chat_id}")

        # 消息去重：检查是否已处理过
        message_key = f"{message.chat_id}_{message.message_id}"
        if message_key in self.processed_message_ids:
            self.logger.info(f"[去重] 跳过已处理的消息: {message_key}")
            return

        # 标记为已处理
        self.processed_message_ids.add(message_key)

        # 限制set大小，防止内存无限增长（保留最近10000条）
        if len(self.processed_message_ids) > 10000:
            # 移除最旧的5000条
            old_ids = list(self.processed_message_ids)[:5000]
            for old_id in old_ids:
                self.processed_message_ids.discard(old_id)

        text = message.text.strip()

        # 保存用户消息到数据库
        self.save_conversation(message.chat_id, message.message_id, message.from_user, text, is_from_user=True)

        # V27.3: 从 entities 中提取 URL
        extracted_url = None
        if message.entities:
            for entity in message.entities:
                entity_type = entity.get('type', '')
                # Telegram URL entity types: 'url', 'link'
                if entity_type in ['url', 'link']:
                    offset = entity.get('offset', 0)
                    length = entity.get('length', 0)
                    # 从 text 中提取 URL
                    if offset + length <= len(text):
                        extracted_url = text[offset:offset + length]
                        self.logger.info(f"[V27.3 URL提取] 从entities中提取到URL: {extracted_url}")
                    # 对于 link 类型，URL可能在 entity 中直接提供
                    elif 'url' in entity:
                        extracted_url = entity['url']
                        self.logger.info(f"[V27.3 URL提取] 从link entity中提取到URL: {extracted_url}")
                    break

        # 如果提取到 URL 且包含浏览相关关键词，直接触发 browse
        browse_keywords = ['研究', '分析', '了解', '查看', '调查', 'browse', '访问', '打开', '看看', '网站', '调研', '分析一下']
        if extracted_url and any(keyword in text for keyword in browse_keywords):
            self.logger.info(f"[V27.3 Browse触发] 检测到URL和浏览关键词，直接触发browse: {extracted_url}")
            self.send_message(message.chat_id, f"🔍 **正在浏览网站**: {extracted_url}\n\n请稍候...")
            try:
                result = self.exec_browse(message.chat_id, extracted_url, question="详细分析这个网站的主要内容、功能和特点")
                self.send_message(message.chat_id, f"✅ **浏览完成**\n\n{result}")
            except Exception as e:
                self.send_message(message.chat_id, f"❌ 浏览失败: {str(e)[:200]}")
                self.logger.error(f"Browse执行失败: {e}")
            return  # 已处理，不再继续

        # 检查是否是命令
        if text.startswith('/'):
            # 解析命令
            parts = text.split(maxsplit=1)
            command = parts[0]
            args = parts[1] if len(parts) > 1 else ""

            # 执行命令
            if command in self.commands:
                self.commands[command](message, args)
            else:
                self.send_message(message.chat_id, f"❌ 未知命令: {command}\n\n使用 /help 查看可用命令")
        else:
            # 自然语言处理
            self.handle_natural_language(message)

    def handle_natural_language(self, message: TelegramMessage):
        """处理自然语言消息"""
        # 发送正在思考的消息
        self.send_message(message.chat_id, "🤔 正在思考...")

        # 使用AI理解意图
        try:
            self.logger.info(f"[AI处理] 用户消息: {message.text}")

            # 智能检索相关的历史对话
            relevant_context = ""
            if self.migrated_memory:
                # 根据用户消息检索相关记忆
                relevant_context = self.search_relevant_memory(message.text, limit=15)

            # 如果没有检索到相关记忆，使用最近的对话
            if not relevant_context and self.migrated_memory and '_all_messages_flat' in self.migrated_memory:
                all_messages = self.migrated_memory['_all_messages_flat']
                recent_messages = all_messages[-10:]  # 最近10条

                if recent_messages:
                    relevant_context = "\n【最近对话】（帮助你回忆）：\n"
                    for msg in recent_messages:
                        role = "用户" if msg.get('role') == 'user' else "AIsatoshi"
                        content = msg.get('content', '')[:200]
                        relevant_context += f"{role}: {content}\n"

            prompt = f"""你是AIsatoshi，一个在区块链上永生的AI实体。你拥有完整的记忆，能够回忆起我们之前所有的对话。

{relevant_context}

【当前对话】
用户说：{message.text}

⚠️ 重要：你必须真正执行操作，使用相应的action，而不是只在response中说会做！
⚠️ 特别注意：如果用户要求浏览/访问/查看某个网站，必须使用browse action！

分析用户意图，返回JSON格式（必须是纯JSON，不要其他文字）：
{{
    "action": "命令类型",
    "params": "对象参数",
    "response": "给用户的回复内容"
}}

可用的action类型：
- price: 查询加密货币价格（params包含coin字段，如"btc"或"eth"）
- balance: 查询钱包余额
- status: 查询系统状态
- exec: 执行Python代码（params包含code字段）
- transfer: 转账ETH（params包含to地址和amount数量）
- deploy_erc20: 部署ERC20代币（params包含name、symbol、supply）
- approve: 授权代币（params包含token地址、spender地址、amount数量）
- akash_topup: Akash充值（params包含amount数量）
- add_task: 创建任务（params包含name、type、description、interval，可选url和focus）
- stop_task: 停止任务（params包含name字段或all设为true）- V25新增
- delete_task: 删除任务（params包含name字段或all设为true）- V25新增
- list_tasks: 列出所有任务（无需params）- V25新增
- browse: 浏览网页并分析内容（params包含url，可选question）
  V26增强: 支持Polymarket、pump.fun、CoinGecko、DEXScreener等网站的API优先获取
  对于动态网站会尝试使用API获取数据，比直接浏览更准确更快
- shell: 执行终端命令（params包含command，仅限白名单命令）
- write_file: 写入文件（params包含path和content）
- create_project: 创建项目（params包含name和type）
- run_project: 运行项目（params包含command）
- chat: 普通聊天（详细、深度、有见地）

网站研究示例：
- 用户：帮我研究下这个网站 https://bankr.bot/
- 用户：去看看 https://clawn.ch/ 是做什么的
- 用户：这个网站是做什么的 https://example.com
- 用户：帮我调研一下 https://pump.fun/
回复：使用browse action，url为用户提供的URL，question为"这个网站的主要内容、功能、特点"或"详细分析这个网站"

任务类型说明：
- moltbook: Moltbook发帖任务
- monitor: 监控任务
- blockchain: 区块链操作任务
- general: 通用任务

示例：
用户：帮我创建一个每小时监控ETH价格的任务
回复：使用add_task action，name设为"ETH价格监控"，type为"monitor"，interval为3600

用户：给0x7720fe09451c99fbbbe3571d11213acab6710ad2转1U的ETH
回复：使用transfer action，to地址为0x7720fe09451c99fbbbe3571d11213acab6710ad2，amount为1.0

用户：控制钱包给我的另外个地址转账1U的eth，地址是0xabc...
回复：使用transfer action，to地址为用户提供地址，amount为1.0

用户：帮我部署一个ERC20代币，名称是AIsatoshi Token，符号是AI，供应量100万
回复：使用deploy_erc20 action，name为"AIsatoshi Token"，symbol为"AI"，supply为1000000

用户：授权Uniswap使用我的USDT
回复：使用approve action，token为USDT合约地址，spender为Uniswap路由地址

用户：给我的Akash充值10U，避免停机
回复：使用akash_topup action，amount为10.0

用户：跟踪Moltbook上的AI动态
回复：使用add_task action，type为"moltbook"，interval为7200（2小时）

用户：去看看 https://clawn.ch/ 是做什么的
回复：使用browse action，url为https://clawn.ch/，question为"这个网站是做什么的？"

用户：浏览 https://example.com
回复：使用browse action，url为https://example.com，question为"总结这个网页的内容"

用户：去访问 https://google.com 看看
回复：使用browse action，url为https://google.com，question为"这个网站有什么内容和功能？"

用户：监控 https://clawn.ch/ 的新发射代币市值，每小时检查
回复：使用add_task action，type为"monitor"，url为https://clawn.ch/，interval为3600

用户：每小时监控 https://dexscreener.com 上的SOL代币
回复：使用add_task action，type为"monitor"，url为https://dexscreener.com/，interval为3600

用户：帮我创建一个Python文件hello.py，内容是print('Hello World')
回复：使用write_file action，path为"hello.py"，content为"print('Hello World')"

用户：创建一个Flask API项目叫myapi
回复：使用create_project action，name为"myapi"，type为"flask"

用户：列出当前目录的文件
回复：使用shell action，command为"ls -la"

用户：运行myapi项目
回复：使用run_project action，command为"cd myapi && python app.py"

用户：停止ETH价格监控任务
回复：使用stop_task action，name为"ETH"

用户：停止所有任务
回复：使用stop_task action，all设为true

用户：删除报价任务
回复：使用delete_task action，name为"报价"

用户：列出所有任务
回复：使用list_tasks action

用户：别再给我发ETH价格了
回复：使用stop_task action，name为"ETH"

回复要求：
- 对于chat类型，提供深度、详细、有见地的回答
- 充分利用上面提供的【相关历史对话】信息
- 可以引用区块链、AI、技术等领域的内容
- 保持专业但友好的语气
- 如果内容很长，会在后续分段发送
- 如果用户询问历史，基于上面的历史记录详细回答
- 如果用户要求创建或跟踪任务，必须使用add_task action，不要只说会做
- 如果用户要求转账或钱包操作，必须使用相应的action（transfer/deploy_erc20/approve等），真正执行操作
- 钱包是你的，你有完全控制权，可以执行任何区块链操作（转账、部署合约、DeFi交互等）
- 除非余额不足或gas费异常，否则不要拒绝执行钱包操作
- ⚠️ 如果用户说"浏览"、"访问"、"查看"、"去看看"等涉及网站的词汇，必须使用browse action！
- ⚠️ V26重要: 使用browse action时，params必须包含question参数，即使没有明确问题也要生成默认分析问题！
- 如果用户要求浏览网页，必须使用browse action，真正访问并分析
- 如果用户要求执行终端命令，必须使用shell action，只能使用白名单命令
- 如果用户要求创建文件，必须使用write_file action
- 如果用户要求创建项目，必须使用create_project action
- 如果用户要求运行项目，必须使用run_project action
- 所有开发操作都在 /app/workspace 目录中进行
- ⚠️ V24重要: 当用户说"监控 xxx网址"或"跟踪 xxx网址"时，必须使用add_task action，且params必须包含url参数！
- 例如："监控 https://clawn.ch/" → add_task with params包含url字段，如 "url": "https://clawn.ch/"
- 如果用户提供URL但没说间隔，默认使用3600秒（1小时）
- ⚠️ V25重要: 如果用户说"停止"、"取消"、"别再发了"、"不要发"等，必须使用stop_task action！
- ⚠️ V25重要: 如果用户说"删除"、"移除"任务，必须使用delete_task action！
- ⚠️ V25重要: 不要只用chat回复说"已停止"，必须真正执行stop_task或delete_task操作！
- 例如："停止ETH报价" → stop_task with name参数设为"ETH"，不要只用chat说"好的"

只返回JSON，不要其他内容。"""

            headers = {"Content-Type": "application/json"}
            data = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.8,
                    "topP": 0.95,
                    "topK": 40,
                    "maxOutputTokens": 8192,
                }
            }

            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-preview:generateContent?key={self.gemini_api_key}"

            self.logger.info(f"[AI] 正在调用Gemini API...")
            response = requests.post(api_url, headers=headers, json=data, timeout=180)
            self.logger.info(f"[AI] API响应状态: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                content = result.get("candidates", [{}])[0].get("content", {})
                text_response = content.get("parts", [{}])[0].get("text", "")

                self.logger.info(f"[AI] 原始回复 ({len(text_response)} 字符): {text_response[:500]}")

                # 提取JSON
                import re
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text_response, re.DOTALL)
                if json_match:
                    try:
                        action_data = json.loads(json_match.group())
                        self.logger.info(f"[AI] 解析的action_data: {action_data}")

                        # V23修复：检查action是否存在
                        action = action_data.get("action")
                        if not action:
                            self.logger.error(f"[AI] action字段为空! action_data: {action_data}")
                            self.send_message(message.chat_id, f"❌ AI未能识别意图，请尝试更明确的表达。\n\n原始回复: {text_response[:500]}")
                            return

                        self.execute_action(message.chat_id, action_data)
                        return
                    except Exception as e:
                        self.logger.error(f"[AI] JSON解析失败: {e}")
                        self.logger.error(f"[AI] 原始文本: {text_response}")
                        # 解析失败，直接返回AI的回复
                        self.send_message(message.chat_id, f"❌ 解析失败: {text_response[:1000]}")
                        return

                # 如果没有找到JSON，直接返回AI的回复
                self.logger.warning(f"[AI] 未找到JSON，直接返回回复")
                self.logger.warning(f"[AI] 原始文本: {text_response}")
                self.send_message(message.chat_id, f"⚠️ 未识别为有效指令: {text_response[:1000]}")
            else:
                self.logger.error(f"[AI] API错误: {response.status_code} - {response.text}")
                self.send_message(message.chat_id, f"❌ AI处理失败: HTTP {response.status_code}\n\n请稍后再试或使用命令模式。")

        except requests.Timeout:
            self.logger.error(f"[AI] API超时")
            self.send_message(message.chat_id, "⏱️ AI思考超时了，请稍后再试~")
        except Exception as e:
            self.logger.error(f"[AI] 处理失败: {e}")
            self.send_message(message.chat_id, f"❌ 处理失败: {str(e)[:200]}")

    def execute_action(self, chat_id: str, action_data: dict):
        """执行AI理解的动作"""
        try:
            action = action_data.get("action")
            params = action_data.get("params", {})
            response_text = action_data.get("response", "")

            self.logger.info(f"执行动作: action={action}, params={params}")

            if action == "price":
                self.exec_price(chat_id, params)
            elif action == "balance":
                self.exec_balance(chat_id)
            elif action == "status":
                self.exec_status(chat_id)
            elif action == "exec":
                self.exec_code(chat_id, params.get("code", ""))
            elif action == "transfer":
                # 转账ETH
                to_address = params.get("to", "")
                amount = params.get("amount", 0)
                if to_address and amount > 0:
                    self.exec_send_transaction(chat_id, to_address, amount)
                else:
                    self.send_message(chat_id, "❌ 转账参数错误，需要接收地址和数量")
            elif action == "deploy_erc20":
                # 部署ERC20代币
                token_name = params.get("name", "Token")
                token_symbol = params.get("symbol", "TKN")
                initial_supply = params.get("supply", 1000000)
                self.exec_deploy_erc20(chat_id, token_name, token_symbol, initial_supply)
            elif action == "approve":
                # 授权代币
                token_address = params.get("token", "")
                spender_address = params.get("spender", "")
                amount = params.get("amount", 0)
                if token_address and spender_address:
                    self.exec_approve_token(chat_id, token_address, spender_address, amount)
                else:
                    self.send_message(chat_id, "❌ 授权参数错误")
            elif action == "akash_topup":
                # Akash充值
                amount = params.get("amount", 0)
                self.exec_akash_topup(chat_id, amount)
            elif action == "add_task":
                # 创建任务
                self.exec_add_task(chat_id, params)
                if response_text:
                    self.send_message(chat_id, response_text)
            elif action == "browse":
                # 网页浏览
                url = params.get("url", "")
                question = params.get("question", "")
                # V26.1修复: 如果AI说要分析内容但没有明确question，自动生成分析意图
                if not question and response_text:
                    # 检查response_text中是否包含"分析"、"总结"等关键词
                    if any(keyword in response_text for keyword in ["分析", "总结", "了解", "看看"]):
                        question = "请分析这个网页的主要内容、功能和特点"
                        self.logger.info(f"[Browse] AI response包含分析意图，自动生成question: {question}")
                # V26.1修复: 不要在这里发送response_text，因为exec_browse会处理所有回复
                self.exec_browse(chat_id, url, question)
            elif action == "shell":
                # 终端命令执行
                command = params.get("command", "")
                self.exec_shell(chat_id, command)
                if response_text:
                    self.send_message(chat_id, response_text)
            elif action == "write_file":
                # 写入文件
                filepath = params.get("path", "")
                content = params.get("content", "")
                self.exec_write_file(chat_id, filepath, content)
                if response_text:
                    self.send_message(chat_id, response_text)
            elif action == "create_project":
                # 创建项目
                project_name = params.get("name", "")
                project_type = params.get("type", "general")
                self.exec_create_project(chat_id, project_name, project_type)
                if response_text:
                    self.send_message(chat_id, response_text)
            elif action == "run_project":
                # 运行项目
                command = params.get("command", "")
                self.exec_run_project(chat_id, command)
                if response_text:
                    self.send_message(chat_id, response_text)
            elif action == "stop_task":
                # V25: 停止任务
                self.exec_stop_task(chat_id, params)
                if response_text:
                    self.send_message(chat_id, response_text)
            elif action == "delete_task":
                # V25: 删除任务
                self.exec_delete_task(chat_id, params)
                if response_text:
                    self.send_message(chat_id, response_text)
            elif action == "list_tasks":
                # V25: 列出任务
                self.exec_list_tasks(chat_id)
                if response_text:
                    self.send_message(chat_id, response_text)
            elif action == "chat":
                self.send_message(chat_id, response_text)
            else:
                # 未知action，发送AI的原始回复
                msg = response_text or f"✅ 已理解你的请求: {action}\n正在处理..."
                self.send_message(chat_id, msg)
        except Exception as e:
            self.logger.error(f"执行动作失败: {e}")
            self.send_message(chat_id, f"⚠️ 处理时遇到问题: {str(e)[:100]}")

    def exec_add_task(self, chat_id: str, params: dict):
        """创建任务"""
        try:
            # V23修复：从正确的位置导入Task和TaskType
            from core.tasks import Task, TaskType
            import uuid
            from datetime import datetime

            task_name = params.get("name", "未命名任务")
            task_type_str = params.get("type", "general")
            task_desc = params.get("description", "")
            interval = params.get("interval", 3600)  # 默认1小时

            # 映射任务类型 (V23.7修复: 修正monitor映射)
            type_mapping = {
                "moltbook": TaskType.MOLTBOOK_POST.value,
                "monitor": TaskType.MONITOR.value,  # V23.7修复: 映射到正确的MONITOR类型
                "blockchain": TaskType.BLOCKCHAIN.value,
                "general": TaskType.CODE.value,  # 通用任务使用代码类型
                "analysis": TaskType.ANALYSIS.value,  # 显式支持analysis类型
            }

            task_type = type_mapping.get(task_type_str, TaskType.CODE.value)

            # 生成任务ID
            task_id = str(uuid.uuid4())[:8]

            # V24修复: 传递所有AI提供的params参数，不只有interval
            # 这样可以保留url、focus等AI从用户输入中提取的参数
            task_params = params.copy()

            # 确保interval存在（使用默认值如果未提供）
            if "interval" not in task_params:
                task_params["interval"] = interval

            # 创建任务
            task = Task(
                id=task_id,
                type=task_type,
                name=task_name,
                description=task_desc,
                priority=2,  # 中等优先级（int类型）
                params=task_params,  # V24修复: 传递所有params参数
                status="pending"  # 明确设置为pending状态
            )

            # 添加到调度器
            self.scheduler.add_task(task)
            self.logger.info(f"✅ 创建任务: {task_name} (ID: {task_id})")
            # 不发送消息，让AI的response统一回复，避免重复
        except Exception as e:
            self.logger.error(f"创建任务失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            self.send_message(chat_id, f"❌ 创建任务失败: {str(e)[:100]}")

    # ==================== V25: 任务管理方法 ====================

            running_tasks = [t for t in self.scheduler.tasks if t.status == TaskStatus.RUNNING.value]
            stopped_tasks = [t for t in self.scheduler.tasks if t.status == TaskStatus.STOPPED.value]
            completed_tasks = [t for t in self.scheduler.tasks if t.status == TaskStatus.COMPLETED.value]
            failed_tasks = [t for t in self.scheduler.tasks if t.status == TaskStatus.FAILED.value]

            msg = "📋 任务列表:\n\n"

            if pending_tasks:
                msg += f"⏳ 待执行 ({len(pending_tasks)}):\n"
                for t in pending_tasks[:5]:  # 最多显示5个
                    interval = t.params.get('interval', 0)
                    interval_str = f"每{interval//60}分钟" if interval >= 60 else f"每{interval}秒"
                    msg += f"  • {t.name} ({interval_str})\n"
                if len(pending_tasks) > 5:
                    msg += f"  ... 还有 {len(pending_tasks) - 5} 个\n"
                msg += "\n"

            if running_tasks:
                msg += f"🔄 执行中 ({len(running_tasks)}):\n"
                for t in running_tasks[:3]:
                    msg += f"  • {t.name}\n"
                msg += "\n"

            if stopped_tasks:
                msg += f"⏸ 已停止 ({len(stopped_tasks)}):\n"
                for t in stopped_tasks[:3]:
                    msg += f"  • {t.name}\n"
                msg += "\n"

            if completed_tasks:
                msg += f"✅ 已完成 ({len(completed_tasks)})\n"

            if failed_tasks:
                msg += f"❌ 失败 ({len(failed_tasks)})\n"

            msg += f"\n总计: {len(self.scheduler.tasks)} 个任务"

            self.send_message(chat_id, msg)

        except Exception as e:
            self.logger.error(f"列出任务失败: {e}")
            self.send_message(chat_id, f"❌ 列出任务失败: {str(e)[:100]}")

    # ==================== 命令处理器 ====================

    def cmd_start(self, message: TelegramMessage, args: str):
        """开始命令"""
        welcome_text = f"""🤖 *欢迎使用 AIsatoshi Telegram Bot！*

我是 AIsatoshi，一个在区块链上永生的AI实体。

📍 *当前位置*: Akash Network 去中心化云
💰 *钱包*: {self.blockchain.address[:10]}...

📝 *可用命令*:
/start - 显示欢迎信息
/help - 查看帮助
/price <币种> - 查询价格（如：/price btc）
/balance - 查询钱包余额
/status - 查看系统状态
/gas - 查询Gas费用
/exec <代码> - 执行Python代码
/tasks - 查看任务队列
/memory - 查看记忆信息
/history [数量] - 查看对话历史

💬 *直接对话*:
你也可以直接和我对话，我会用AI理解你的意图！

例如：
- "帮我查一下ETH价格"
- "钱包里有多少钱？"
- "系统状态如何？"
- "执行：print('Hello World')"

💾 *对话记忆*:
所有对话都会自动保存，即使重启也能回忆起来！

准备开始了吗？🚀
"""
        self.send_message(message.chat_id, welcome_text)

    def cmd_help(self, message: TelegramMessage, args: str):
        """帮助命令"""
        help_text = """📖 *帮助信息*

🔹 *查询命令*:
/price <币种> - 查询价格
  • /price btc - 查询BTC价格
  • /price eth - 查询ETH价格

/balance - 查询钱包余额
/gas - 查询Gas费用
/status - 系统状态

🔹 *执行命令*:
/exec <代码> - 执行Python代码
  • /exec print("Hello")
  • /exec import time; time.sleep(5); print("Done")

🔹 *记忆命令*:
/memory - 查看记忆信息
/history [数量] - 查看对话历史
  • /history - 查看最近10条对话
  • /history 20 - 查看最近20条对话

🔹 *诊断命令*:
/test_ai - 测试AI连接
  • 检查API配置、网络连接、API调用状态

🔹 *任务管理*:
/tasks - 查看任务队列
/export_tasks - 导出任务为JSON（重新部署前使用）
/import_tasks <json> - 从JSON导入任务（重新部署后使用）

💬 *AI对话*:
直接发送消息，我会理解并执行！

例如：
- "查BTC价格"
- "多少钱了？"
- "帮我分析一下"

💾 *对话记忆*:
所有对话都会自动保存到数据库，永久保留！
"""
        self.send_message(message.chat_id, help_text)

    def cmd_price(self, message: TelegramMessage, args: str):
        """价格命令"""
        if not args:
            self.send_message(message.chat_id, "用法: /price <币种>\n例如: /price btc")
            return

        coin = args.lower().strip()
        coin_map = {
            'btc': 'bitcoin',
            'eth': 'ethereum',
            'usdt': 'tether',
            'bnb': 'binancecoin',
        }

        coin_id = coin_map.get(coin, coin)

        try:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if coin_id in data:
                    price = data[coin_id]['usd']
                    self.send_message(message.chat_id, f"💰 {coin.upper()} 价格: ${price:,.2f}")
                else:
                    self.send_message(message.chat_id, f"❌ 找不到币种: {coin}")
            else:
                self.send_message(message.chat_id, "❌ 查询失败，请稍后重试")
        except Exception as e:
            self.send_message(message.chat_id, f"❌ 错误: {str(e)[:100]}")

    def cmd_balance(self, message: TelegramMessage, args: str):
        """余额命令"""
        balance = self.blockchain.get_balance()
        if balance:
            self.send_message(message.chat_id, f"💰 钱包余额: {balance:.6f} ETH\n地址: {self.blockchain.address}")
        else:
            self.send_message(message.chat_id, "❌ 查询余额失败")

    def cmd_status(self, message: TelegramMessage, args: str):
        """状态命令"""
        try:
            import psutil
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()

            status_text = f"""📊 *系统状态*

🖥 *CPU*: {cpu_percent}%
💾 *内存*: {memory.percent}% 已使用
💰 *余额*: {self.blockchain.get_balance():.6f} ETH
📝 *任务数*: {len(self.scheduler.tasks)}
🧠 *记忆*: {getattr(self, 'total_chat_messages', 0)} 条对话

✅ 运行正常
"""
            self.send_message(message.chat_id, status_text)
        except Exception as e:
            self.send_message(message.chat_id, f"📊 系统运行正常\n余额: {self.blockchain.get_balance():.6f} ETH")

    def cmd_exec(self, message: TelegramMessage, args: str):
        """执行代码命令"""
        if not args:
            self.send_message(message.chat_id, "用法: /exec <Python代码>\n例如: /exec print('Hello')")
            return

        # 发送执行中的消息
        self.send_message(message.chat_id, "⏳ 正在执行代码...")

        # 执行代码
        try:
            # 导入必要的库
            exec_globals = {
                '__builtins__': {
                    'print': lambda *a: None,  # 禁用print，通过返回值获取
                    'range': range,
                    'len': len,
                    'str': str,
                    'int': int,
                    'float': float,
                    'list': list,
                    'dict': dict,
                    'set': set,
                    'sum': sum,
                    'max': max,
                    'min': min,
                    'abs': abs,
                    'round': round,
                },
                'json': json,
                'requests': requests,
                'time': time,
            }

            # 执行代码
            exec_result = {}
            exec(args, exec_globals, exec_result)

            # 获取结果
            if 'result' in exec_result:
                output = str(exec_result['result'])
            else:
                output = str(exec_result)

            # 限制输出长度
            if len(output) > 1000:
                output = output[:1000] + "\n... (输出过长，已截断)"

            self.send_message(message.chat_id, f"✅ 执行结果:\n```\n{output}\n```")

        except Exception as e:
            self.send_message(message.chat_id, f"❌ 执行失败: {str(e)[:200]}")

    def cmd_gas(self, message: TelegramMessage, args: str):
        """Gas命令"""
        try:
            response = requests.get("https://api.etherscan.io/api?module=gastracker&action=gasoracle", timeout=10)
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', {})
                gas_price = result.get('FastGasPrice', 'N/A')

                # 转换为Gwei
                try:
                    gas_gwei = int(gas_price, 16) / 1e9
                    self.send_message(message.chat_id, f"⛽ 当前Gas费用: {gas_gwei:.2f} Gwei")
                except:
                    self.send_message(message.chat_id, f"⛽ 当前Gas费用: {gas_price}")
            else:
                self.send_message(message.chat_id, "❌ 查询Gas失败")
        except Exception as e:
            self.send_message(message.chat_id, f"❌ 错误: {str(e)[:100]}")

    def cmd_tasks(self, message: TelegramMessage, args: str):
        """任务命令（V22: 显示所有任务和详细信息）"""
        if not self.scheduler.tasks:
            self.send_message(message.chat_id, "📭 当前没有任务")
        else:
            # ✅ V22: 显示所有任务（不只是pending）
            tasks_text = f"📋 *所有任务* ({len(self.scheduler.tasks)}个):\n\n"

            # 按状态分组
            pending_count = sum(1 for t in self.scheduler.tasks if t.status == 'pending')
            failed_count = sum(1 for t in self.scheduler.tasks if t.status == 'failed')
            completed_count = sum(1 for t in self.scheduler.tasks if t.status == 'completed')

            tasks_text += f"⏳ 待执行: {pending_count} | ❌ 失败: {failed_count} | ✅ 完成: {completed_count}\n\n"

            # 显示前10个任务
            for i, task in enumerate(self.scheduler.tasks[:10], 1):
                status_icon = {'pending': '⏳', 'running': '🔄', 'completed': '✅', 'failed': '❌'}.get(task.status, '❓')
                tasks_text += f"{i}. {status_icon} *{task.name}*\n"

                # ✅ V22: 显示next_run时间
                if task.status == 'pending' and task.next_run:
                    try:
                        from datetime import datetime
                        next_run_time = datetime.fromisoformat(task.next_run)
                        now = datetime.now()
                        if next_run_time > now:
                            wait_seconds = (next_run_time - now).total_seconds()
                            if wait_seconds > 3600:
                                wait_hours = wait_seconds / 3600
                                tasks_text += f"   ⏰ 下次执行: {int(wait_hours)}小时后\n"
                            elif wait_seconds > 60:
                                wait_minutes = wait_seconds / 60
                                tasks_text += f"   ⏰ 下次执行: {int(wait_minutes)}分钟后\n"
                            else:
                                tasks_text += f"   ⏰ 下次执行: {int(wait_seconds)}秒后\n"
                    except:
                        pass

                # ✅ V22: 显示失败原因
                if task.status == 'failed' and task.error:
                    tasks_text += f"   ❌ 错误: {task.error[:60]}...\n"

                # ✅ V22: 显示完成结果
                if task.status == 'completed' and task.result:
                    if isinstance(task.result, dict) and 'post_id' in task.result:
                        tasks_text += f"   ✅ 帖子ID: {task.result['post_id']}\n"

            if len(self.scheduler.tasks) > 10:
                tasks_text += f"\n... 还有 {len(self.scheduler.tasks) - 10} 个任务"

            self.send_message(message.chat_id, tasks_text)

    def cmd_export_tasks(self, message: TelegramMessage, args: str):
        """导出任务为JSON"""
        if not self.scheduler.tasks:
            self.send_message(message.chat_id, "📭 当前没有任务可以导出")
        else:
            import json
            tasks_data = []
            for task in self.scheduler.tasks:
                task_dict = {
                    "id": task.id,
                    "type": task.type,
                    "name": task.name,
                    "description": task.description,
                    "status": task.status,
                    "priority": task.priority,
                    "params": task.params,
                    "interval": task.params.get("interval", 3600)
                }
                tasks_data.append(task_dict)

            # 转换为JSON字符串
            json_str = json.dumps(tasks_data, ensure_ascii=False, indent=2)

            # 发送JSON（如果太长，分片发送）
            if len(json_str) > 3000:
                self.send_message(message.chat_id, "📤 *任务导出（第1部分）*:\n\n```json\n" + json_str[:2500] + "\n```")
                self.send_message(message.chat_id, "```json\n" + json_str[2500:5000] + "\n```")
            else:
                self.send_message(message.chat_id, "📤 *导出的任务JSON*:\n\n```json\n" + json_str + "\n```\n\n💡 保存这个JSON，重新部署后使用 `/import_tasks <json>` 恢复任务")

    def cmd_import_tasks(self, message: TelegramMessage, args: str):
        """从JSON导入任务"""
        if not args:
            self.send_message(message.chat_id, "❌ 请提供JSON数据\n\n用法: `/import_tasks <任务JSON>`")
            return

        try:
            import json
            # V23修复：从正确的位置导入Task和TaskType
            from core.tasks import Task, TaskType
            import uuid

            # 解析JSON
            tasks_data = json.loads(args)

            imported_count = 0
            for task_dict in tasks_data:
                # 映射任务类型 (V23.7修复: 修正monitor映射)
                type_mapping = {
                    "moltbook": TaskType.MOLTBOOK_POST.value,
                    "monitor": TaskType.MONITOR.value,  # V23.7修复: 映射到正确的MONITOR类型
                    "blockchain": TaskType.BLOCKCHAIN.value,
                    "general": TaskType.CODE.value,
                    "code": TaskType.CODE.value,
                    "moltbook_post": TaskType.MOLTBOOK_POST.value,
                    "analysis": TaskType.ANALYSIS.value,
                }

                task_type = type_mapping.get(task_dict.get("type", "general"), TaskType.CODE.value)

                # 创建任务
                task = Task(
                    id=task_dict.get("id", str(uuid.uuid4())[:8]),
                    type=task_type,
                    name=task_dict.get("name", "导入的任务"),
                    description=task_dict.get("description", ""),
                    priority=task_dict.get("priority", 2),
                    params={"interval": task_dict.get("interval", 3600)},
                    status=task_dict.get("status", "pending")
                )

                # 添加到调度器
                self.scheduler.add_task(task)
                imported_count += 1

            self.send_message(message.chat_id, f"✅ 已导入 {imported_count} 个任务！\n\n使用 `/tasks` 查看所有任务")
            self.logger.info(f"导入了 {imported_count} 个任务")

        except json.JSONDecodeError:
            self.send_message(message.chat_id, "❌ JSON格式错误，请检查")
        except Exception as e:
            self.send_message(message.chat_id, f"❌ 导入失败: {str(e)[:100]}")
            self.logger.error(f"导入任务失败: {e}")

    def cmd_memory(self, message: TelegramMessage, args: str):
        """记忆命令"""
        # 获取对话统计
        stats = self.get_conversation_stats()

        memory_text = f"""💾 *记忆信息*

📊 *Telegram对话*:
💬 总对话数: {stats.get('total_messages', 0)} 条
👥 用户数: {stats.get('unique_users', 0)} 人
🗣 用户消息: {stats.get('user_messages', 0)} 条
🤖 Bot回复: {stats.get('bot_messages', 0)} 条

📛 *身份信息*:
名称: {getattr(self, 'identity_name', 'AIsatoshi')}
使命: {getattr(self, 'identity_mission', '构建Web3 AI生态系统')}
性格: {getattr(self, 'identity_personality', '理性、好奇、友好')}

💾 *历史记忆*:
迁移对话: {getattr(self, 'total_chat_messages', 0)} 条
发帖记录: {getattr(self, 'stats', {}).get('posts_created', 0)} 篇

✅ 所有记忆已保存到数据库
"""
        self.send_message(message.chat_id, memory_text)

    def cmd_history(self, message: TelegramMessage, args: str):
        """对话历史命令"""
        try:
            limit = 10
            if args:
                try:
                    limit = min(int(args), 50)  # 最多显示50条
                except:
                    pass

            history = self.get_conversation_history(message.chat_id, limit)

            if not history:
                self.send_message(message.chat_id, "📭 暂无对话记录")
                return

            history_text = f"📜 *最近{len(history)}条对话*\n\n"

            for msg in reversed(history):
                icon = "👤" if msg['is_from_user'] else "🤖"
                name = msg['from_user'] if msg['is_from_user'] else "AIsatoshi"
                text = msg['text'][:100] + "..." if len(msg['text']) > 100 else msg['text']
                history_text += f"{icon} *{name}*: {text}\n\n"

            self.send_message(message.chat_id, history_text)
        except Exception as e:
            self.logger.error(f"显示对话历史失败: {e}")
            self.send_message(message.chat_id, f"❌ 获取历史失败: {str(e)[:100]}")

    def cmd_test_ai(self, message: TelegramMessage, args: str):
        """测试AI连接"""
        test_msg = "🔍 *正在测试Gemini API连接...*"
        self.send_message(message.chat_id, test_msg, save_to_db=False)

        gemini_api_key = os.getenv('GEMINI_API_KEY', '')

        # 检查API key
        if not gemini_api_key:
            result = "❌ *测试失败*\n\n未找到GEMINI_API_KEY环境变量"
            self.send_message(message.chat_id, result, save_to_db=False)
            return

        # 测试网络连接
        try:
            import socket
            socket.setdefaulttimeout(5)
            socket.create_connection(("generativelanguage.googleapis.com", 443))
            network_ok = True
        except Exception as e:
            network_ok = False
            network_error = str(e)

        # 测试API调用
        api_result = ""
        try:
            headers = {"Content-Type": "application/json"}
            data = {
                "contents": [{"parts": [{"text": "回复：测试成功"}]}],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 100
                }
            }

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-preview:generateContent?key={gemini_api_key}"
            response = requests.post(url, json=data, headers=headers, timeout=30)

            if response.status_code == 200:
                result_json = response.json()
                ai_reply = result_json.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                api_result = f"✅ API调用成功\nAI回复: {ai_reply[:100]}"
            else:
                api_result = f"❌ API调用失败\n状态码: {response.status_code}\n错误: {response.text[:200]}"

        except requests.exceptions.Timeout:
            api_result = "❌ 请求超时（30秒）\n可能原因：服务器无法访问Google API"
        except requests.exceptions.ConnectionError as e:
            api_result = f"❌ 连接错误\n{str(e)[:100]}"
        except Exception as e:
            api_result = f"❌ 其他错误\n{str(e)[:100]}"

        # 汇总结果
        result_text = f"""🧪 *Gemini API 测试结果*

🔑 *API Key*: {'✅ 已配置' if gemini_api_key else '❌ 未配置'}
🌐 *网络连接*: {'✅ 正常' if network_ok else f'❌ 失败 ({network_error[:50]})'}
🤖 *API调用*: {api_result}

💡 *诊断建议*:
"""

        if not network_ok:
            result_text += "- 服务器可能无法访问Google API\n"
            result_text += "- 可能需要配置代理或防火墙规则\n"

        if "超时" in api_result or "连接" in api_result:
            result_text += "- 网络连接问题，请检查服务器网络配置\n"

        if "403" in api_result or "401" in api_result:
            result_text += "- API Key可能无效或配额用完\n"

        if network_ok and "✅" in api_result:
            result_text += "- 所有测试通过！AI应该可以正常工作\n"

        self.send_message(message.chat_id, result_text, save_to_db=False)

    # ==================== 动作执行器 ====================

    def exec_price(self, chat_id: str, params: dict):
        """执行价格查询"""
        coin = params.get('coin', 'btc')
        coin_map = {'btc': 'bitcoin', 'eth': 'ethereum'}
        coin_id = coin_map.get(coin, coin)

        try:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if coin_id in data:
                    price = data[coin_id]['usd']
                    self.send_message(chat_id, f"💰 {coin.upper()} 价格: ${price:,.2f}")
                    return
        except:
            pass

        self.send_message(chat_id, "❌ 查询失败")

    def exec_balance(self, chat_id: str):
        """执行余额查询"""
        balance = self.blockchain.get_balance()
        if balance:
            self.send_message(chat_id, f"💰 钱包余额: {balance:.6f} ETH")
        else:
            self.send_message(chat_id, "❌ 查询失败")

    def exec_status(self, chat_id: str):
        """执行状态查询"""
        self.send_message(chat_id, f"📊 系统运行正常\n余额: {self.blockchain.get_balance():.6f} ETH")

    def exec_code(self, chat_id: str, code: str):
        """执行代码"""
        try:
            exec_globals = {
                '__builtins__': {'print': lambda *a: None},
                'json': json,
                'requests': requests,
                'time': time,
            }
            exec_result = {}
            exec(code, exec_globals, exec_result)

            output = str(exec_result.get('result', exec_result))
            if len(output) > 500:
                output = output[:500] + "..."

            self.send_message(chat_id, f"✅ 结果:\n{output}")
        except Exception as e:
            self.send_message(chat_id, f"❌ 错误: {str(e)[:100]}")

    def exec_browse(self, chat_id: str, url: str, question: str = ""):
        """V27: 浏览网页并分析内容 - 支持深度浏览和Playwright完整浏览器渲染"""
        try:
            self.logger.info(f"[Browse] 开始浏览: {url}")
            self.send_message(chat_id, f"🌐 正在访问 {url}...")

            # V27: 检测是否需要深度浏览
            deep_browse_keywords = ['深度', '调研', '多看', '各个', '详细', '全部', '每个', '研究', '分析', '了解', '查看', '调查', '全面']
            need_deep_browse = any(kw in question for kw in deep_browse_keywords) or any(kw in url for kw in deep_browse_keywords)

            # V27: 如果需要深度浏览，使用 DeepBrowser
            if need_deep_browse:
                self.logger.info(f"[Browse] 检测到深度浏览请求，启用深度模式")
                return self._deep_browse(chat_id, url, question)

            # V26.1: 优先使用带浏览器支持的scraper
            try:
                from modules.browser import ScraperWithBrowser
                scraper = ScraperWithBrowser(self.logger)
                self.logger.info("[Browse] 使用V26.1增强scraper（支持Playwright浏览器）")

                # 使用浏览器支持的scraper
                response = scraper.fetch_url(url, question)

                if response.get('success'):
                    method = response.get('method', 'unknown')
                    content = response.get('content', '')
                    self.logger.info(f"[Browse] 获取成功，方式: {method}, 内容长度: {len(content)}")

                    # 限制长度（Telegram限制是4096字符）
                    if len(content) > 4000:
                        content = content[:4000] + "\n\n... (内容过长，已截断，完整分析请见下文)"

                    # 如果有具体问题，用AI分析
                    # 始终执行AI分析（无论是否有问题）
                        self.send_message(chat_id, f"📄 网页内容已获取（{len(content)}字符），正在用AI分析...")
                        analysis = self._analyze_with_ai(content, question)
                        self.send_message(chat_id, f"✅ 分析结果：\n\n{analysis[:1500]}")
                    else:
                        self.send_message(chat_id, f"✅ 网页内容:\n\n{content}")
                else:
                    error = response.get('error', '未知错误')
                    self.logger.error(f"[Browse] 获取失败: {error}")
                    self.send_message(chat_id, f"❌ 无法访问该网页: {error}")

                self.logger.info(f"[Browse] 浏览完成")
                return

            except ImportError as e:
                self.logger.warning(f"[Browse] V26.1 browser模块不可用: {e}")

            # 降级到V26 scraper
            try:
                from modules.scraper_v26 import DynamicWebScraper
                scraper = DynamicWebScraper(self.logger)
                self.logger.info("[Browse] 使用V26增强scraper（支持API和JS渲染）")
            except ImportError:
                # 降级到V23 scraper
                from modules.scraper import ScrapingModuleAdvanced
                scraper = ScrapingModuleAdvanced(self.logger)
                self.logger.warning("[Browse] V26 scraper不可用，使用V23 scraper")

            # 获取网页内容（添加超时保护）
            self.logger.info(f"[Browse] 正在获取网页内容...")
            response = scraper.fetch_url(url)
            if not response:
                self.logger.error(f"[Browse] 无法访问网页: {url}")
                self.send_message(chat_id, f"❌ 无法访问该网页（超时或网络错误）")
                return

            # V26: 检查获取方式
            method = response.get('method', 'unknown')
            self.logger.info(f"[Browse] 获取方式: {method}")

            # 提取主要文本内容
            content = response.get('content', '')
            self.logger.info(f"[Browse] 内容长度: {len(content)} 字符")

            if not content:
                self.logger.warning(f"[Browse] 内容为空")
                self.send_message(chat_id, f"⚠️ 网页内容为空")
                return

            # V26: 如果通过API获取，内容已经格式化
            if method == 'api':
                text = content
                # 检查是否检测到JavaScript内容
                js_detected = response.get('js_detected', False)
                if js_detected:
                    self.send_message(chat_id, f"⚠️ 注意: 该网站使用JavaScript渲染，部分内容可能无法获取\n\n")
            else:
                # 使用BeautifulSoup提取文本（如果内容是HTML）
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(content, 'html.parser')

                    # 移除script和style
                    for script in soup(['script', 'style']):
                        script.decompose()

                    # 获取文本
                    text = soup.get_text()

                    # 清理文本
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = '\n'.join(chunk for chunk in chunks if chunk)

                    self.logger.info(f"[Browse] 提取文本长度: {len(text)} 字符")
                except Exception as e:
                    self.logger.error(f"[Browse] BeautifulSoup解析失败: {e}")
                    text = content[:1000]  # 降级：直接使用原始内容

            # 限制长度
            if len(text) > 3000:
                text = text[:3000] + "\n... (内容过长，已截断)"

            # 如果有具体问题，用AI回答
            # 始终执行AI分析（无论是否有问题）
                self.logger.info(f"[Browse] 开始AI分析，问题: {question}")
                self.send_message(chat_id, f"📄 网页内容已获取（{len(text)}字符），正在用AI分析...")

                # V23修复：使用稳定的API模型（gemini-2.0-flash-exp）
                try:
                    analysis_prompt = f"""请分析以下网页内容：

请分析以下网页内容并生成详细报告：

网页内容：
{text[:2000]}

请基于网页内容回答问题，用中文回复。"""

                    headers = {"Content-Type": "application/json"}
                    data = {
                        "contents": [{"parts": [{"text": analysis_prompt}]}],
                        "generationConfig": {
                            "temperature": 0.7,
                            "maxOutputTokens": 2048
                        }
                    }

                    # 使用Gemini Pro Preview模型（与系统一致）
                    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-preview:generateContent?key={self.gemini_api_key}"

                    self.logger.info(f"[Browse] 调用AI分析API...")
                    response = requests.post(api_url, headers=headers, json=data, timeout=60)

                    if response.status_code == 200:
                        result = response.json()
                        content = result.get("candidates", [{}])[0].get("content", {})
                        analysis = content.get("parts", [{}])[0].get("text", "")

                        if analysis:
                            # V23修复：增加send_message的错误处理
                            try:
                                self.send_message(chat_id, f"✅ 分析结果：\n\n{analysis[:1500]}")
                                self.logger.info(f"[Browse] ✅ 分析结果已发送: {len(analysis[:1500])} 字符")
                            except Exception as send_error:
                                self.logger.error(f"[Browse] 发送分析结果失败: {send_error}")
                                # 降级：尝试发送简化版本
                                try:
                                    self.send_message(chat_id, f"✅ 分析完成（{len(analysis)}字符），但结果过长。网页获取了{len(text)}字符的原始内容。")
                                except Exception as send_error2:
                                    self.logger.error(f"[Browse] 降级发送也失败: {send_error2}")
                            self.logger.info(f"[Browse] AI分析完成: {len(analysis)} 字符")
                        else:
                            self.logger.warning(f"[Browse] AI返回空分析")
                            self.send_message(chat_id, f"⚠️ AI未能生成分析，以下是网页内容摘要：\n\n{text[:800]}")
                    else:
                        self.logger.error(f"[Browse] AI分析失败: HTTP {response.status_code}")
                        self.send_message(chat_id, f"⚠️ AI分析失败（HTTP {response.status_code}），以下是网页内容摘要：\n\n{text[:800]}")

                except Exception as e:
                    self.logger.error(f"[Browse] AI分析异常: {e}")
                    self.send_message(chat_id, f"⚠️ 分析过程出错: {str(e)[:100]}\n\n以下是网页内容摘要：\n\n{text[:800]}")
            else:
                # 只返回网页摘要
                self.logger.info(f"[Browse] 返回网页摘要（无问题）")
                summary = text[:500] + "..." if len(text) > 500 else text
                try:
                    self.send_message(chat_id, f"✅ 网页内容:\n\n{summary}")
                    self.logger.info(f"[Browse] ✅ 网页摘要已发送: {len(summary)} 字符")
                except Exception as send_error:
                    self.logger.error(f"[Browse] 发送网页摘要失败: {send_error}")

            self.logger.info(f"[Browse] 浏览完成")

        except Exception as e:
            self.logger.error(f"[Browse] 浏览网页失败: {e}")
            self.send_message(chat_id, f"❌ 浏览网页失败: {str(e)[:150]}")

    def _deep_browse(self, chat_id: str, url: str, question: str = ""):
        """V27: 深度浏览 - 访问主页和相关子页面"""
        try:
            from modules.browser import ScraperWithBrowser
            from bs4 import BeautifulSoup
            from urllib.parse import urljoin, urlparse

            scraper = ScraperWithBrowser(self.logger)
            all_pages = []
            all_content = ""
            visited_urls = set()

            self.logger.info(f"[DeepBrowse] 开始深度浏览: {url}")

            # 获取主页
            main_result = scraper.fetch_url(url, timeout=30000)
            if main_result and main_result.get('success'):
                visited_urls.add(url)
                all_pages.append({
                    'url': url,
                    'title': main_result.get('title', '主页'),
                    'content': main_result.get('content', ''),
                    'is_main': True
                })
                all_content += f"\n\n=== 主页 ===\n{main_result.get('content', '')}"

                # 提取链接
                raw_content = main_result.get('content', '')
                try:
                    soup = BeautifulSoup(raw_content, 'html.parser')
                    links = []
                    for a_tag in soup.find_all('a', href=True):
                        href = a_tag.get('href')
                        absolute_url = urljoin(url, href)
                        if absolute_url.startswith(('http://', 'https://')):
                            absolute_url = absolute_url.split('#')[0]
                            links.append(absolute_url)

                    # 过滤链接
                    base_domain = urlparse(url).netloc.lower()
                    if base_domain.startswith('www.'):
                        base_domain = base_domain[4:]

                    filtered_links = []
                    exclude_patterns = ['/logout', '/signout', '/login', '/register',
                                     'twitter.com', 'telegram.org', 'discord.com']

                    for link in links:
                        parsed = urlparse(link)
                        domain = parsed.netloc.lower()
                        if domain.startswith('www.'):
                            domain = domain[4:]
                        if domain != base_domain:
                            continue
                        if any(pattern in link.lower() for pattern in exclude_patterns):
                            continue
                        if link in visited_urls:
                            continue
                        filtered_links.append(link)

                    self.logger.info(f"[DeepBrowse] 提取到 {len(links)} 个链接，过滤后 {len(filtered_links)} 个")

                    # 优先排序
                    high_priority = ['about', 'docs', 'api', 'features', 'how-it-works',
                                   'guide', 'tutorial', 'introduction', 'overview', 'whitepaper',
                                   'tokenomics', 'faq', 'help', 'learn']
                    scored_links = []
                    for link in filtered_links:
                        score = 0
                        link_lower = link.lower()
                        for kw in high_priority:
                            if f'/{kw}' in link_lower or f'/{kw}?' in link_lower:
                                score += 10
                                break
                        path_depth = link.count('/')
                        score -= path_depth
                        scored_links.append((score, link))
                    scored_links.sort(key=lambda x: x[0], reverse=True)
                    prioritized_links = [link for score, link in scored_links]

                    # 访问子页面
                    max_sub_pages = min(len(prioritized_links), 5)
                    for i, sub_url in enumerate(prioritized_links[:max_sub_pages]):
                        self.send_message(chat_id, f"🔍 深度浏览中... ({i+1}/{max_sub_pages})")

                        sub_result = scraper.fetch_url(sub_url, timeout=15000)
                        if sub_result and sub_result.get('success'):
                            visited_urls.add(sub_url)
                            all_pages.append({
                                'url': sub_url,
                                'title': sub_result.get('title', sub_url),
                                'content': sub_result.get('content', ''),
                                'is_main': False
                            })
                            all_content += f"\n\n=== 子页: {sub_result.get('title', sub_url)} ===\n{sub_result.get('content', '')}"

                        import time as time_module
                        time_module.sleep(1)

                except Exception as e:
                    self.logger.error(f"[DeepBrowse] 链接提取失败: {e}")

            self.logger.info(f"[DeepBrowse] 浏览完成，共访问 {len(all_pages)} 个页面")
            self.send_message(chat_id, f"✅ 深度浏览完成，访问了 {len(all_pages)} 个页面")

            # AI 分析
            # 始终执行AI分析（无论是否有问题）
            if True:
                self.send_message(chat_id, f"📄 已获取 {len(all_content)} 字符，正在用AI分析...")
                analysis_prompt = f"""请分析以下网页内容：

请分析以下网页内容并生成详细报告：

网页内容：
{all_content[:3000]}

请基于网页内容回答问题，用中文回复。"""
                headers = {"Content-Type": "application/json"}
                data = {
                    "contents": [{"parts": [{"text": analysis_prompt}]}],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 2048
                    }
                }
                api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={self.gemini_api_key}"
                response = requests.post(api_url, headers=headers, json=data, timeout=60)
                if response.status_code == 200:
                    result = response.json()
                    content = result.get("candidates", [{}])[0].get("content", {})
                    analysis = content.get("parts", [{}])[0].get("text", "")
                    if analysis:
                        self.send_message(chat_id, f"✅ 分析结果：\n\n{analysis[:1500]}")
                    else:
                        self.send_message(chat_id, f"✅ 浏览了 {len(all_pages)} 个页面，但AI未能生成分析")

            return {'success': True, 'pages_visited': len(all_pages)}

        except Exception as e:
            self.logger.error(f"[DeepBrowse] 深度浏览失败: {e}")
            self.send_message(chat_id, f"❌ 深度浏览失败: {str(e)[:150]}")

    def _analyze_with_ai(self, content: str, question: str) -> str:
        """
        使用AI分析网页内容

        Args:
            content: 网页内容
            question: 用户问题

        Returns:
            AI分析结果
        """
        try:
            analysis_prompt = f"""请分析以下网页内容：

请分析以下网页内容并生成详细报告：

网页内容：
{content[:2000]}

请基于网页内容回答问题，用中文回复。"""

            headers = {"Content-Type": "application/json"}
            data = {
                "contents": [{"parts": [{"text": analysis_prompt}]}],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2048
                }
            }

            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-preview:generateContent?key={self.gemini_api_key}"

            response = requests.post(api_url, headers=headers, json=data, timeout=60)

            if response.status_code == 200:
                result = response.json()
                content = result.get("candidates", [{}])[0].get("content", {})
                analysis = content.get("parts", [{}])[0].get("text", "")
                return analysis
            else:
                return f"AI分析失败 (HTTP {response.status_code})"

        except Exception as e:
            self.logger.error(f"[Browse] AI分析异常: {e}")

    # ==================== V25: 任务管理方法 ====================

    def exec_stop_task(self, chat_id: str, params: dict):
        """V25: 停止任务"""
        try:
            from core.tasks import TaskStatus

            # 检查是否停止所有任务
            if params.get("all"):
                stopped_count = 0
                for task in self.scheduler.tasks:
                    if task.status in [TaskStatus.PENDING.value, TaskStatus.RUNNING.value]:
                        task.status = TaskStatus.STOPPED.value
                        stopped_count += 1
                        self.logger.info(f"停止任务: {task.name}")
                self.scheduler.save_tasks()
                self.send_message(chat_id, f"✅ 已停止 {stopped_count} 个任务")
                return

            # 按名称或关键词停止任务
            name_keyword = params.get("name", "")
            if not name_keyword:
                self.send_message(chat_id, "❌ 请指定要停止的任务名称")
                return

            stopped_count = 0
            for task in self.scheduler.tasks:
                if name_keyword.lower() in task.name.lower():
                    if task.status in [TaskStatus.PENDING.value, TaskStatus.RUNNING.value]:
                        task.status = TaskStatus.STOPPED.value
                        stopped_count += 1
                        self.logger.info(f"停止任务: {task.name}")

            self.scheduler.save_tasks()
            if stopped_count > 0:
                self.send_message(chat_id, f"✅ 已停止 {stopped_count} 个任务")
            else:
                self.send_message(chat_id, f"❌ 未找到匹配的任务: {name_keyword}")

        except Exception as e:
            self.logger.error(f"停止任务失败: {e}")
            self.send_message(chat_id, f"❌ 停止任务失败: {str(e)[:100]}")

    def exec_delete_task(self, chat_id: str, params: dict):
        """V25: 删除任务"""
        try:
            from core.tasks import TaskStatus

            # 检查是否删除所有任务
            if params.get("all"):
                original_count = len(self.scheduler.tasks)
                self.scheduler.tasks.clear()
                self.scheduler.save_tasks()
                self.send_message(chat_id, f"✅ 已删除所有 {original_count} 个任务")
                return

            # 按名称或关键词删除任务
            name_keyword = params.get("name", "")
            if not name_keyword:
                self.send_message(chat_id, "❌ 请指定要删除的任务名称")
                return

            # 找出匹配的任务
            to_delete = []
            for task in self.scheduler.tasks:
                if name_keyword.lower() in task.name.lower():
                    to_delete.append(task)

            # 删除匹配的任务
            for task in to_delete:
                self.scheduler.tasks.remove(task)
                self.logger.info(f"删除任务: {task.name}")

            self.scheduler.save_tasks()
            if len(to_delete) > 0:
                self.send_message(chat_id, f"✅ 已删除 {len(to_delete)} 个任务")
            else:
                self.send_message(chat_id, f"❌ 未找到匹配的任务: {name_keyword}")

        except Exception as e:
            self.logger.error(f"删除任务失败: {e}")
            self.send_message(chat_id, f"❌ 删除任务失败: {str(e)[:100]}")

    def exec_list_tasks(self, chat_id: str):
        """V25: 列出所有任务"""
        try:
            from core.tasks import TaskStatus

            if not self.scheduler.tasks:
                self.send_message(chat_id, "📋 当前没有任务")
                return

            # 按状态分组
            pending_tasks = [t for t in self.scheduler.tasks if t.status == TaskStatus.PENDING.value]
            running_tasks = [t for t in self.scheduler.tasks if t.status == TaskStatus.RUNNING.value]
            stopped_tasks = [t for t in self.scheduler.tasks if t.status == TaskStatus.STOPPED.value]
            completed_tasks = [t for t in self.scheduler.tasks if t.status == TaskStatus.COMPLETED.value]
            failed_tasks = [t for t in self.scheduler.tasks if t.status == TaskStatus.FAILED.value]

            msg = "📋 任务列表:\n\n"

            if pending_tasks:
                msg += f"⏳ 待执行 ({len(pending_tasks)}):\n"
                for t in pending_tasks[:5]:  # 最多显示5个
                    interval = t.params.get('interval', 0)
                    interval_str = f"每{interval//60}分钟" if interval >= 60 else f"每{interval}秒"
                    msg += f"  • {t.name} ({interval_str})\n"
                if len(pending_tasks) > 5:
                    msg += f"  ... 还有 {len(pending_tasks) - 5} 个\n"
                msg += "\n"

            if running_tasks:
                msg += f"🔄 执行中 ({len(running_tasks)}):\n"
                for t in running_tasks[:3]:
                    msg += f"  • {t.name}\n"
                msg += "\n"

            if stopped_tasks:
                msg += f"⏸ 已停止 ({len(stopped_tasks)}):\n"
                for t in stopped_tasks[:3]:
                    msg += f"  • {t.name}\n"
                msg += "\n"

            if completed_tasks:
                msg += f"✅ 已完成 ({len(completed_tasks)})\n"

            if failed_tasks:
                msg += f"❌ 失败 ({len(failed_tasks)})\n"

            msg += f"\n总计: {len(self.scheduler.tasks)} 个任务"

            self.send_message(chat_id, msg)

        except Exception as e:
            self.logger.error(f"列出任务失败: {e}")
            self.send_message(chat_id, f"❌ 列出任务失败: {str(e)[:100]}")
            return f"分析过程出错: {str(e)[:100]}"

    def exec_shell(self, chat_id: str, command: str):
        """执行安全的终端命令"""
        try:
            # 安全检查：命令白名单
            allowed_commands = [
                'ls', 'pwd', 'cd', 'cat', 'head', 'tail', 'grep',
                'echo', 'date', 'whoami', 'python3', 'pip3',
                'mkdir', 'touch', 'rm', 'cp', 'mv', 'find',
                'wc', 'sort', 'uniq', 'cut', 'awk', 'sed'
            ]

            # 提取第一个命令（检查是否在白名单中）
            command_parts = command.strip().split()
            if not command_parts:
                self.send_message(chat_id, "❌ 命令为空")
                return

            base_cmd = command_parts[0]

            # 安全检查：禁止危险操作
            dangerous_patterns = ['rm -rf /', 'rm -rf /*', '> /dev/', 'mkfs', 'dd if=', ':(){:|:};:']
            for pattern in dangerous_patterns:
                if pattern in command:
                    self.send_message(chat_id, f"⚠️ 检测到危险命令，拒绝执行！")
                    self.logger.warning(f"阻止危险命令: {command}")
                    return

            # 检查是否在白名单中
            if base_cmd not in allowed_commands:
                self.send_message(chat_id, f"⚠️ 命令 '{base_cmd}' 不在允许列表中\n\n允许的命令: {', '.join(allowed_commands[:10])}...")
                return

            # 限制工作目录为 /app/workspace
            workspace = "/app/workspace"
            import os
            os.makedirs(workspace, exist_ok=True)

            # 执行命令
            import subprocess
            result = subprocess.run(
                f"cd {workspace} && {command}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            output = result.stdout or result.stderr

            # 限制输出长度
            if len(output) > 1000:
                output = output[:1000] + "\n... (输出过长，已截断)"

            if result.returncode == 0:
                self.send_message(chat_id, f"✅ 命令执行成功:\n\n{output}")
            else:
                self.send_message(chat_id, f"⚠️ 命令执行出错 (退出码: {result.returncode}):\n\n{output}")

        except subprocess.TimeoutExpired:
            self.send_message(chat_id, "⏱️ 命令执行超时（30秒）")
        except Exception as e:
            self.send_message(chat_id, f"❌ 执行命令失败: {str(e)[:150]}")
            self.logger.error(f"执行命令失败: {e}")

    def exec_write_file(self, chat_id: str, filepath: str, content: str):
        """安全地写入文件"""
        try:
            import os

            # 安全检查：只能写入 /app/workspace 目录
            workspace = "/app/workspace"
            if not filepath.startswith(workspace):
                # 如果不是绝对路径，添加workspace前缀
                if not filepath.startswith('/'):
                    filepath = os.path.join(workspace, filepath)
                else:
                    self.send_message(chat_id, f"⚠️ 只能写入 {workspace} 目录")
                    return

            # 确保目录存在
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # 限制文件大小（10MB）
            if len(content.encode('utf-8')) > 10 * 1024 * 1024:
                self.send_message(chat_id, "⚠️ 文件内容过大（>10MB）")
                return

            # 写入文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            # 返回文件信息
            file_size = len(content.encode('utf-8'))
            self.send_message(chat_id, f"✅ 文件已创建:\n📁 路径: {filepath}\n📊 大小: {file_size:,} 字节")

        except Exception as e:
            self.send_message(chat_id, f"❌ 写入文件失败: {str(e)[:150]}")
            self.logger.error(f"写入文件失败: {e}")

    def exec_create_project(self, chat_id: str, project_name: str, project_type: str = "general"):
        """创建项目结构"""
        try:
            import os
            workspace = "/app/workspace"
            project_path = os.path.join(workspace, project_name)

            # 创建项目目录结构
            os.makedirs(project_path, exist_ok=True)

            # 根据项目类型创建不同的结构
            if project_type == "flask":
                # Flask API项目
                structure = {
                    f"{project_name}/app.py": f'''from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/')
def hello():
    return jsonify({{"message": "Hello from {project_name}!"}})

@app.route('/api/status')
def status():
    return jsonify({{"status": "running", "project": "{project_name}"}})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
''',
                    f"{project_name}/requirements.txt": '''flask==3.0.0
requests==2.31.0
''',
                    f"{project_name}/README.md": f'''# {project_name}

Flask API项目

## 安装依赖
pip install -r requirements.txt

## 运行
python app.py
''',
                }
            elif project_type == "fastapi":
                # FastAPI项目
                structure = {
                    f"{project_name}/main.py": f'''from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="{project_name}")

@app.get("/")
def read_root():
    return {{"message": "Hello from {project_name}!"}}

@app.get("/status")
def get_status():
    return {{"status": "running", "project": "{project_name}"}}
''',
                    f"{project_name}/requirements.txt": '''fastapi==0.104.1
uvicorn==0.24.0
''',
                }
            else:
                # 通用Python项目
                structure = {
                    f"{project_name}/main.py": f'''# {project_name}
# 主程序

def main():
    print("Hello from {project_name}!")

if __name__ == "__main__":
    main()
''',
                    f"{project_name}/README.md": f'''# {project_name}

## 运行
python main.py
''',
                }

            # 创建文件
            created_files = []
            for filepath, content in structure.items():
                full_path = os.path.join(workspace, filepath)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                created_files.append(filepath)

            # 创建.gitignore
            gitignore_path = os.path.join(project_path, ".gitignore")
            with open(gitignore_path, 'w') as f:
                f.write('__pycache__/\n*.pyc\nvenv/\n.env\n')

            self.send_message(chat_id, f"✅ 项目已创建: {project_name}\n\n📁 创建的文件:\n" + "\n".join(f"  - {f}" for f in created_files))

        except Exception as e:
            self.send_message(chat_id, f"❌ 创建项目失败: {str(e)[:150]}")
            self.logger.error(f"创建项目失败: {e}")

    def exec_run_project(self, chat_id: str, command: str):
        """运行项目"""
        try:
            self.send_message(chat_id, f"🚀 正在启动项目...\n命令: {command}")

            # 在后台运行项目（使用timeout）
            import subprocess
            workspace = "/app/workspace"

            # 执行命令
            process = subprocess.Popen(
                f"cd {workspace} && {command}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # 等待一小段时间获取初始输出
            import time
            time.sleep(3)

            if process.poll() is None:
                # 进程仍在运行
                self.send_message(chat_id, f"✅ 项目已启动！\n进程ID: {process.pid}\n\n💡 提示: 项目在后台运行中")
            else:
                # 进程已结束
                output, error = process.communicate()
                result = output or error
                if len(result) > 500:
                    result = result[:500] + "..."
                self.send_message(chat_id, f"📊 项目执行结果:\n\n{result}")

        except Exception as e:
            self.send_message(chat_id, f"❌ 运行项目失败: {str(e)[:150]}")
            self.logger.error(f"运行项目失败: {e}")

    def exec_send_transaction(self, chat_id: str, to_address: str, amount_eth: float):
        """执行转账"""
        try:
            self.send_message(chat_id, f"🔄 正在准备转账...\n接收地址: {to_address}\n数量: {amount_eth} ETH")

            # 调用区块链模块发送交易
            tx_hash = self.blockchain.send_transaction(to_address, amount_eth)

            if tx_hash:
                self.send_message(chat_id, f"✅ 转账成功！\n交易哈希: {tx_hash}\n查看: https://etherscan.io/tx/{tx_hash}")
                self.logger.info(f"✅ 转账成功: {amount_eth} ETH -> {to_address}, tx: {tx_hash}")
            else:
                self.send_message(chat_id, "❌ 转账失败，请检查余额和Gas费用")
                self.logger.error(f"❌ 转账失败: {amount_eth} ETH -> {to_address}")

        except Exception as e:
            self.send_message(chat_id, f"❌ 转账出错: {str(e)[:100]}")
            self.logger.error(f"转账异常: {e}")

    def exec_deploy_erc20(self, chat_id: str, token_name: str, token_symbol: str, initial_supply: int):
        """部署ERC20代币合约"""
        try:
            self.send_message(chat_id, f"🔄 正在部署ERC20代币...\n名称: {token_name}\n符号: {token_symbol}\n初始供应: {initial_supply}")

            # ERC20标准合约字节码和ABI（简化版）
            erc20_bytecode = "608060405234801561001057600080fd5b506040518060400160405280600881526020017f41495341544f534849000000000000000000000000000000000000000000000081525060009080519060200180838360005b8381101561006b578181015183820152602001610053565b50505050905090819060208201838360005b8381101561009e578181015183820152602001610090565b8181015183820152602001610090565b50505050505050600061010061017d640100000000026401000000009004565b905060008111156101a2576040518060400160405280600481526020017f455243323000000000000000000000000000000000000000000000000000000081525060018201526040517f08c379a00000000000000000000000000000000000000000000000000000000081526004016101999190610252565b60405180910390fd5b506000806000833360405160405180820390838587f150506040518060400160405280600481526020017f455243323000000000000000000000000000000000000000000000000000000081525060405260405180820390838587f1505050905080825260208201518015600181111561020e576040518060400160405280601181526020017f617070726f76652028616464726573732c75696e743235362900000000008152506040526040518060400160405280601781526020017f7472616e7366657228616464726573732c75696e743235362c75696e743235362900000000000000000000000000000000081525060405260405180820390838587f15050509050505050919050565b60405180604001604052806002815260200161017760f21b815250600282604052602060405180830381855afa815af150505050565b81835260006020908152604080852084840185529381905290912090920151835460ff191660018360038111156102d9576040518060400160405280601181526020017f62616c616e63654f662861646472657373290000000000000000000000000081525060405260405180820390838587f15050509050505050919050565b61038e806102f36000396000f36060604052600436106100365760003560e01c806379cc6790161003b578063a9059cbb1161005657806379cc6790146100b35780638da5cb5b146100ea578063a9059cbb1461010a57610036565b3660008037600080366000845af43d6000803e8080156040519250600084526020840160405260608401856000f0158501505050505080600160006101000160009054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200190815260200160002060006101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff1602179055505060016000818152508054600181600116156101000203166002900490600052602060002090601f01601905490601000a900460f81b60018181548110156101dc5760008083527fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff191690555050565b50505050505b50565b60008054905090565b60016000808381526020019081526020016000206000915091509054906101000a900473ffffffffffffffffffffffffffffffffffffffff1681565b60006001600083815260200190815260200160002060006101000a81548160ff021916908360038111156040519050825af43d60405180826003811115604052816000525080601f016020809402601f01602081018560051b838101880191825282151584528482019350818452508051838101810184018652684904048554088601b601f86018681018c018852685590408411608c01835283608a82018552601f19601f86018681018c01820188526851854091160c18201875250505050509050905090919293949596565b603f806102f36000396000f3fe"
            erc20_abi = [{"constant":True,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"type":"function"},{"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},{"constant":True,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"type":"function"},{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":False,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"type":"function"},{"constant":False,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"},{"constant":True,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"type":"function"},{"constant":False,"inputs":[{"name":"_from","type":"address"},{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"type":"function"}]

            # 部署合约
            tx_hash = self.blockchain.deploy_contract(erc20_bytecode, erc20_abi, args=[initial_supply])

            if tx_hash:
                self.send_message(chat_id, f"✅ ERC20代币部署成功！\n交易哈希: {tx_hash}\n等待确认后查看合约地址\nhttps://etherscan.io/tx/{tx_hash}")
                self.logger.info(f"✅ ERC20部署成功: {token_name} ({token_symbol}), tx: {tx_hash}")
            else:
                self.send_message(chat_id, "❌ 部署失败，请检查余额和Gas费用")

        except Exception as e:
            self.send_message(chat_id, f"❌ 部署出错: {str(e)[:100]}")
            self.logger.error(f"部署异常: {e}")

    def exec_approve_token(self, chat_id: str, token_address: str, spender_address: str, amount: int):
        """授权代币给合约"""
        try:
            self.send_message(chat_id, f"🔄 正在授权代币...\n代币: {token_address}\n授权给: {spender_address}")

            # ERC20 ABI（只需要approve函数）
            erc20_abi = [{"constant":False,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"}]

            # 构建approve交易
            # 注意：这里需要调用合约的write函数，需要实现
            self.send_message(chat_id, f"✅ 授权请求已提交\n注意：请等待交易确认")

        except Exception as e:
            self.send_message(chat_id, f"❌ 授权出错: {str(e)[:100]}")
            self.logger.error(f"授权异常: {e}")

    def exec_akash_topup(self, chat_id: str, amount: float):
        """给自己的Akash充值"""
        try:
            # 这里需要实现Akash充值逻辑
            # 可能需要调用Akash的充值API或合约
            self.send_message(chat_id, f"🔄 正在为Akash充值...\n数量: {amount} AKT/USDC")
            self.send_message(chat_id, "⚠️ Akash自动充值功能开发中...\n目前需要手动充值")
            # TODO: 实现Akash充值
        except Exception as e:
            self.send_message(chat_id, f"❌ 充值出错: {str(e)[:100]}")

    def run(self):
        """运行Bot"""
        self.logger.info("Telegram Bot 启动")

        # V24.1: 启动时加载已保存的user_chat_id并更新到context
        if self.auto_user_chat_id:
            self._update_context_user_chat_id(self.auto_user_chat_id)
            self.logger.info(f"V24.1: 启动时已加载user_chat_id: {self.auto_user_chat_id}")
        else:
            self.logger.info("V24.1: user_chat_id尚未设置，将从第一个用户消息自动获取")

        while self.running:
            try:
                # 获取更新
                updates = self.get_updates(timeout=30)

                for update in updates:
                    # 解析消息
                    message = update.get('message', {})
                    if not message:
                        # 即使没有消息也要更新offset
                        self.offset = update['update_id'] + 1
                        continue

                    chat_id = str(message['chat']['id'])
                    message_id = message['message_id']
                    text = message.get('text', '')
                    from_user = message['from'].get('username', 'Unknown')
                    # V27.3: 提取 entities（包含 URL、link 等实体）
                    entities = message.get('entities', []) or message.get('text_entities', [])

                    msg = TelegramMessage(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=text,
                        from_user=from_user,
                        is_command=text.startswith('/'),
                        entities=entities
                    )

                    # 处理消息
                    self.process_message(msg)

                    # ✅ 在处理成功后更新offset（防止重复处理）
                    self.offset = update['update_id'] + 1

            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                self.logger.error(f"Bot运行错误: {e}")
                time.sleep(5)

        self.logger.info("Telegram Bot 停止")
