#!/usr/bin/env python3
"""
AIsatoshi V27 - 主入口

V27 = 记忆原生 + 进化原生 + 任务继承原生

这是AIsatoshi的全新重构版本，从头开始设计，具有：
1. 原生记忆系统 - 所有对话和记忆自动持久化
2. 原生进化系统 - 自我学习和能力提升
3. 原生任务继承 - 任务在重启后自动恢复
4. 完整的部署前验证
"""

import os
import sys
import time
import signal
import threading
from typing import Optional

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 核心模块
from core.config import Config
from core.logger import Logger
from core.exceptions import AIsatoshiException

# 存储层
from storage.database import init_all_databases
from storage.conversation_store import ConversationStore
from storage.task_store import TaskStore
from storage.memory_store import MemoryStore
from storage.evolution_store import EvolutionStore

# 服务层
from services.memory_manager import MemoryManager
from services.evolution_engine import EvolutionEngine
from services.ai_engine import AIEngine
from services.telegram_service import TelegramService
from services.task_scheduler import TaskScheduler
from services.web_scraper import WebScraper


class AIsatoshiV27:
    """AIsatoshi V27 主类

    整合所有模块，提供统一的运行环境。
    """

    def __init__(self, config: Optional[Config] = None):
        """初始化AIsatoshi V27

        Args:
            config: 配置对象（可选，默认从环境变量加载）
        """
        # 加载配置
        if config is None:
            config = Config.from_env()
        self.config = config
        self.config.validate()

        # 初始化日志
        self.logger = Logger(
            name="AIsatoshi",
            level=config.LOG_LEVEL,
            data_dir=config.DATA_DIR
        )

        self.logger.banner()
        self.logger.info("初始化AIsatoshi V27...")

        # 存储层
        self.databases = {}
        self.conversation_store: Optional[ConversationStore] = None
        self.task_store: Optional[TaskStore] = None
        self.memory_store: Optional[MemoryStore] = None
        self.evolution_store: Optional[EvolutionStore] = None

        # 服务层
        self.memory_manager: Optional[MemoryManager] = None
        self.evolution_engine: Optional[EvolutionEngine] = None
        self.ai_engine: Optional[AIEngine] = None
        self.telegram_service: Optional[TelegramService] = None
        self.task_scheduler: Optional[TaskScheduler] = None
        self.web_scraper: Optional[WebScraper] = None

        # 状态
        self.running = False
        self.shutdown_event = threading.Event()

        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def initialize(self) -> bool:
        """初始化所有组件

        Returns:
            是否成功
        """
        try:
            self.logger.separator("初始化存储层")

            # 确保数据目录存在
            os.makedirs(self.config.DATA_DIR, exist_ok=True)
            os.makedirs(os.path.join(self.config.DATA_DIR, "knowledge"), exist_ok=True)

            # 初始化数据库
            self.databases = init_all_databases(self.config.DATA_DIR, self.logger)
            self.conversation_store = self.databases['conversations']
            self.task_store = self.databases['tasks']
            self.memory_store = self.databases['memory']
            self.evolution_store = self.databases['evolution']

            self.logger.info("存储层初始化完成")

            # 初始化服务层
            self.logger.separator("初始化服务层")

            # 记忆管理器
            self.memory_manager = MemoryManager(
                self.memory_store,
                self.conversation_store,
                self.logger
            )
            memory_stats = self.memory_manager.get_stats()
            self.logger.memory_loaded(memory_stats['memories']['total'])
            self.logger.info(f"对话记录: {memory_stats['conversations']['total_messages']} 条")

            # AI引擎
            self.ai_engine = AIEngine(self.config, self.logger)
            self.logger.info("AI引擎已就绪")

            # 进化引擎
            self.evolution_engine = EvolutionEngine(
                self.evolution_store,
                self.conversation_store,
                self.memory_store,
                self.logger,
                learn_interval=self.config.EVOLUTION_LEARN_INTERVAL,
            )
            self.logger.info("进化引擎已就绪")

            # 任务调度器
            self.task_scheduler = TaskScheduler(
                self.task_store,
                self.logger,
                check_interval=self.config.TASK_CHECK_INTERVAL,
            )
            self.logger.info("任务调度器已就绪")

            # Telegram服务
            self.telegram_service = TelegramService(self.config, self.logger)
            self._register_commands()
            self.logger.info("Telegram服务已就绪")

            # 网页浏览服务
            self.web_scraper = WebScraper(self.logger)
            self.logger.info("网页浏览服务已就绪")

            self.logger.separator("初始化完成")
            return True

        except AIsatoshiException as e:
            self.logger.error(f"初始化失败: {e}")
            return False
        except Exception as e:
            self.logger.exception(f"初始化异常: {e}")
            return False

    def _register_commands(self):
        """注册Telegram命令"""
        tg = self.telegram_service

        tg.register_command('/start', self._cmd_start)
        tg.register_command('/help', self._cmd_help)
        tg.register_command('/status', self._cmd_status)
        tg.register_command('/memory', self._cmd_memory)
        tg.register_command('/tasks', self._cmd_tasks)
        tg.register_command('/stop_task', self._cmd_stop_task)
        tg.register_command('/delete_task', self._cmd_delete_task)
        tg.register_command('/balance', self._cmd_balance)
        tg.register_command('/summary', self._cmd_summary)
        tg.register_command('/browse', self._cmd_browse)

        # 设置默认处理器（自然语言处理）
        tg.set_default_handler(self._handle_natural_language)

    # === 命令处理器 ===

    def _cmd_start(self, message, args):
        """处理 /start 命令"""
        self.telegram_service.send_markdown(
            message.chat_id,
            f"""🤖 *欢迎使用 AIsatoshi V27*

我是AIsatoshi，一个在区块链上永生的AI实体。

【核心特性】
- 记忆原生：我会记住我们所有的对话
- 进化原生：我会不断学习和进化
- 任务继承：我的任务会自动恢复

【可用命令】
/help - 查看所有命令
/status - 查看运行状态
/memory - 查看记忆统计
/tasks - 查看任务列表
/balance - 查询钱包余额
/summary - 查看进化总结

你也可以直接和我对话，我会理解你的意图！"""
        )

    def _cmd_help(self, message, args):
        """处理 /help 命令"""
        self.telegram_service.send_markdown(
            message.chat_id,
            """📖 *AIsatoshi V27 帮助*

【基础命令】
/start - 开始使用
/help - 显示帮助信息
/status - 查看运行状态

【记忆命令】
/memory - 查看记忆统计
/summary - 查看进化总结

【任务命令】
/tasks - 查看任务列表
/stop_task <id> - 停止任务
/delete_task <id> - 删除任务

【查询命令】
/balance - 查询钱包余额
/browse <URL> - 浏览网页（支持子页面）

【自然语言】
你也可以直接和我对话，比如：
- "比特币现在多少钱？"
- "帮我查询余额"
- "浏览这个网站 https://..."
- "创建一个监控任务"

我会记住你说的每一句话！"""
        )

    def _cmd_status(self, message, args):
        """处理 /status 命令"""
        stats = self._get_status()

        self.telegram_service.send_markdown(
            message.chat_id,
            f"""📊 *AIsatoshi V27 状态*

【运行状态】
{stats['status']}

【记忆统计】
- 总记忆数: {stats['memory_total']}
- 对话记录: {stats['conversations']}
- 用户数: {stats['users']}

【任务统计】
- 待执行: {stats['tasks_pending']}
- 运行中: {stats['tasks_running']}
- 已完成: {stats['tasks_completed']}

【进化统计】
- 学习周期: {stats['learning_cycles']}
- 学习模式: {stats['patterns']}
- 归纳方法: {stats['methods']}

【系统】
- 版本: V27
- 运行时间: {stats['uptime']}"""
        )

    def _cmd_memory(self, message, args):
        """处理 /memory 命令"""
        stats = self.memory_manager.get_stats()

        self.telegram_service.send_markdown(
            message.chat_id,
            f"""🧠 *记忆系统*

【对话记录】
- 总消息数: {stats['conversations']['total_messages']}
- 用户消息: {stats['conversations']['user_messages']}
- AI回复: {stats['conversations']['bot_messages']}
- 用户数: {stats['conversations']['unique_users']}

【记忆】
- 总记忆数: {stats['memories']['total']}
- 按类型: {stats['memories']['by_type']}
- 重要记忆: {stats['memories']['important']}

【处理统计】
- 已处理对话: {stats['processed']['conversations_processed']}
- 已学习事实: {stats['processed']['facts_learned']}"""
        )

    def _cmd_tasks(self, message, args):
        """处理 /tasks 命令"""
        tasks = self.task_scheduler.get_all_tasks()

        if not tasks:
            self.telegram_service.send_plain(
                message.chat_id,
                "📭 当前没有任务"
            )
            return

        # 按状态分组
        by_status = {}
        for task in tasks:
            status = task.status
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(task)

        # 构建响应
        lines = ["📋 *任务列表*\n"]

        for status, status_tasks in by_status.items():
            icon = {
                'pending': '⏳',
                'running': '🔄',
                'completed': '✅',
                'failed': '❌',
                'stopped': '⏹️',
            }.get(status, '❓')

            lines.append(f"\n*{status.upper()}* ({len(status_tasks)})")

            for task in status_tasks[:10]:  # 最多显示10个
                lines.append(f"{icon} `{task.id[:8]}...` - {task.name}")

        self.telegram_service.send_markdown(message.chat_id, "\n".join(lines))

    def _cmd_stop_task(self, message, args):
        """处理 /stop_task 命令"""
        if not args:
            self.telegram_service.send_plain(
                message.chat_id,
                "用法: /stop_task <任务ID>"
            )
            return

        task_id = args.strip()
        success = self.task_scheduler.stop_task(task_id)

        if success:
            self.telegram_service.send_plain(
                message.chat_id,
                f"✅ 任务已停止: {task_id}"
            )
        else:
            self.telegram_service.send_plain(
                message.chat_id,
                f"❌ 停止任务失败: {task_id}"
            )

    def _cmd_delete_task(self, message, args):
        """处理 /delete_task 命令"""
        if not args:
            self.telegram_service.send_plain(
                message.chat_id,
                "用法: /delete_task <任务ID>"
            )
            return

        task_id = args.strip()
        success = self.task_scheduler.delete_task(task_id)

        if success:
            self.telegram_service.send_plain(
                message.chat_id,
                f"✅ 任务已删除: {task_id}"
            )
        else:
            self.telegram_service.send_plain(
                message.chat_id,
                f"❌ 删除任务失败: {task_id}"
            )

    def _cmd_balance(self, message, args):
        """处理 /balance 命令"""
        # TODO: 实现余额查询
        self.telegram_service.send_plain(
            message.chat_id,
            "💰 余额查询功能开发中..."
        )

    def _cmd_summary(self, message, args):
        """处理 /summary 命令"""
        summary = self.evolution_engine.generate_summary()

        self.telegram_service.send_plain(
            message.chat_id,
            summary
        )

    def _cmd_browse(self, message, args):
        """处理 /browse 命令

        用法: /browse <URL>
        """
        if not args:
            self.telegram_service.send_plain(
                message.chat_id,
                "用法: /browse <URL>\n\n示例: /browse https://www.coingecko.com/en/coins/bitcoin"
            )
            return

        url = args.strip()

        # 发送正在浏览的消息
        self.telegram_service.send_plain(
            message.chat_id,
            f"🔍 正在浏览: {url}\n\n请稍候..."
        )

        # 执行浏览
        try:
            result = self.web_scraper.smart_browse(url)

            # 发送结果（会自动分段）
            self.telegram_service.send_markdown(
                message.chat_id,
                result
            )

        except Exception as e:
            self.telegram_service.send_plain(
                message.chat_id,
                f"❌ 浏览失败: {str(e)}"
            )

    # === 自然语言处理 ===

    def _handle_natural_language(self, message):
        """处理自然语言消息"""
        # 保存用户消息
        self.memory_manager.save_conversation(
            message.chat_id,
            message.message_id,
            'user',
            message.text
        )

        # 发送正在思考
        self.telegram_service.send_plain(
            message.chat_id,
            "🤔 正在思考..."
        )

        # 构建上下文
        context = self.memory_manager.build_context_for_ai(
            message.chat_id,
            message.text
        )

        # 理解意图
        response = self.ai_engine.understand(message.text, context)

        # 执行动作
        result = self._execute_action(message.chat_id, response)

        # 保存AI回复
        self.memory_manager.save_conversation(
            message.chat_id,
            message.message_id + 1,
            'assistant',
            response.response
        )

        # 发送回复
        self.telegram_service.send_markdown(
            message.chat_id,
            response.response
        )

    def _execute_action(self, chat_id: str, response) -> str:
        """执行AI决定的动作

        Args:
            chat_id: 聊天ID
            response: AI响应

        Returns:
            执行结果
        """
        action = response.action

        if action == 'chat':
            return ""  # 直接回复即可

        elif action == 'price':
            # 查询价格（使用WebScraper）
            params = response.params
            coin_id = params.get('coin_id', 'bitcoin')

            price_data = self.web_scraper.get_crypto_price(coin_id)
            if price_data:
                return "\n\n" + self.web_scraper._format_price_data(coin_id, price_data)
            return f"\n\n❌ 无法获取 {coin_id} 的价格数据"

        elif action == 'balance':
            # TODO: 查询余额
            return "\n\n💰 余额查询功能开发中..."

        elif action == 'browse':
            # 浏览网页
            params = response.params
            url = params.get('url', '')

            if not url:
                return "\n\n请提供要浏览的URL"

            try:
                result = self.web_scraper.smart_browse(url)
                return "\n\n" + result
            except Exception as e:
                return f"\n\n❌ 浏览失败: {str(e)}"

        elif action == 'add_task':
            # 添加任务
            params = response.params
            task = self.task_scheduler.create_task(
                task_type=params.get('type', 'general'),
                name=params.get('name', '新任务'),
                description=params.get('description', ''),
                params=params.get('params', {}),
            )
            return f"\n\n✅ 任务已创建: {task.id[:8]}..."

        elif action == 'list_tasks':
            # 列出任务
            tasks = self.task_scheduler.get_all_tasks(status='pending')
            if tasks:
                task_list = "\n".join([
                    f"- {task.name} ({task.id[:8]}...)"
                    for task in tasks[:5]
                ])
                return f"\n\n📋 待执行任务:\n{task_list}"
            return "\n\n📭 没有待执行任务"

        elif action == 'help':
            return "\n\n使用 /help 查看所有命令"

        else:
            return f"\n\n⚠️ 未知动作: {action}"

    def _get_status(self) -> dict:
        """获取系统状态"""
        memory_stats = self.memory_manager.get_stats()
        task_stats = self.task_scheduler.get_stats()
        evolution_stats = self.evolution_engine.get_stats()

        return {
            'status': '🟢 运行中' if self.running else '🔴 已停止',
            'memory_total': memory_stats['memories']['total'],
            'conversations': memory_stats['conversations']['total_messages'],
            'users': memory_stats['conversations']['unique_users'],
            'tasks_pending': task_stats.get('pending', 0),
            'tasks_running': task_stats.get('running', 0),
            'tasks_completed': task_stats.get('completed', 0),
            'learning_cycles': evolution_stats.get('learning_cycles', 0),
            'patterns': evolution_stats.get('patterns', 0),
            'methods': evolution_stats.get('methods', 0),
            'uptime': str(threading.current_thread()),
        }

    # === 运行控制 ===

    def run(self):
        """运行AIsatoshi V27"""
        # 初始化
        if not self.initialize():
            self.logger.error("初始化失败，无法启动")
            return

        self.running = True

        # 启动服务
        self.evolution_engine.start()
        self.task_scheduler.start()

        self.logger.separator("AIsatoshi V27 已启动")
        self.logger.info("开始监听Telegram消息...")

        # 运行Telegram Bot（阻塞）
        try:
            self.telegram_service.run()
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

    def shutdown(self):
        """关闭AIsatoshi V27"""
        if not self.running:
            return

        self.logger.info("正在关闭AIsatoshi V27...")
        self.running = False
        self.shutdown_event.set()

        # 停止服务
        if self.telegram_service:
            self.telegram_service.stop()
        if self.task_scheduler:
            self.task_scheduler.stop()
        if self.evolution_engine:
            self.evolution_engine.stop()

        self.logger.info("AIsatoshi V27 已关闭")

    def _signal_handler(self, signum, frame):
        """信号处理器"""
        self.logger.info(f"收到信号 {signum}，准备关闭...")
        self.shutdown()
        sys.exit(0)


def main():
    """主函数"""
    # 创建并运行AIsatoshi V27
    aisatoshi = AIsatoshiV27()
    aisatoshi.run()


if __name__ == "__main__":
    main()
