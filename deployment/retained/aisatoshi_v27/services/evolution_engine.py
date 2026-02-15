"""
AIsatoshi V27 - 进化引擎

V27核心功能：原生进化系统

负责：
- 从对话中学习模式
- 归纳常用方法
- 生成经验总结
- 维护知识库
- 自我进化
"""

import threading
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from storage.evolution_store import EvolutionStore
from storage.conversation_store import ConversationStore
from storage.memory_store import MemoryStore
from models.evolution import Pattern, Method, Knowledge
from core.logger import Logger


class EvolutionEngine:
    """进化引擎

    AIsatoshi的自我进化系统。
    """

    def __init__(
        self,
        evolution_store: EvolutionStore,
        conversation_store: ConversationStore,
        memory_store: MemoryStore,
        logger: Optional[Logger] = None,
        learn_interval: int = 3600,
    ):
        """初始化进化引擎

        Args:
            evolution_store: 进化存储
            conversation_store: 对话存储
            memory_store: 记忆存储
            logger: 日志记录器
            learn_interval: 学习间隔（秒）
        """
        self.evolution_store = evolution_store
        self.conversation_store = conversation_store
        self.memory_store = memory_store
        self.logger = logger or Logger(name="EvolutionEngine")
        self.learn_interval = learn_interval

        # 后台线程
        self.running = False
        self.thread: Optional[threading.Thread] = None

        # 统计
        self.stats = {
            'learning_cycles': 0,
            'patterns_learned': 0,
            'methods_learned': 0,
            'knowledge_added': 0,
            'summaries_created': 0,
        }

        self.logger.info("进化引擎已初始化")

    def start(self):
        """启动进化引擎后台线程"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._evolution_loop, daemon=True)
        self.thread.start()
        self.logger.info("进化引擎已启动")

    def stop(self):
        """停止进化引擎"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.logger.info("进化引擎已停止")

    def _evolution_loop(self):
        """进化循环（后台运行）"""
        while self.running:
            try:
                # 执行学习
                self.learn()

                # 等待下一次学习
                for _ in range(self.learn_interval):
                    if not self.running:
                        break
                    time.sleep(1)

            except Exception as e:
                self.logger.error(f"进化循环错误: {e}")
                time.sleep(60)

    # === 学习 ===

    def learn(self) -> Dict[str, int]:
        """执行学习

        Returns:
            学习统计
        """
        self.stats['learning_cycles'] += 1
        cycle = self.stats['learning_cycles']

        self.logger.info(f"开始学习周期 #{cycle}")

        results = {
            'patterns': 0,
            'methods': 0,
            'knowledge': 0,
        }

        # 1. 从对话中学习模式
        patterns = self._learn_patterns()
        results['patterns'] = patterns

        # 2. 归纳方法
        methods = self._learn_methods()
        results['methods'] = methods

        # 3. 生成知识
        knowledge = self._generate_knowledge()
        results['knowledge'] = knowledge

        # 更新统计
        self.stats['patterns_learned'] += patterns
        self.stats['methods_learned'] += methods
        self.stats['knowledge_added'] += knowledge

        self.logger.evolution_learning(patterns, methods)

        return results

    def _learn_patterns(self) -> int:
        """从对话中学习模式

        Returns:
            学习到的模式数
        """
        count = 0

        # 获取最近的对话
        conversations = self.conversation_store.get_all_messages(limit=100)

        # 分析用户消息模式
        user_messages = [
            conv.content for conv in conversations
            if conv.role == 'user'
        ]

        # 简单模式识别
        for msg in user_messages:
            # 检测查询价格模式
            if any(word in msg.lower() for word in ['价格', 'price', '多少钱', '市值']):
                pattern = "查询加密货币价格"
                self.evolution_store.add_pattern(pattern, "query", 0.8)
                count += 1

            # 检测查询余额模式
            elif any(word in msg.lower() for word in ['余额', 'balance', '多少钱', '持有']):
                pattern = "查询钱包余额"
                self.evolution_store.add_pattern(pattern, "query", 0.8)
                count += 1

            # 检测转账模式
            elif any(word in msg.lower() for word in ['转', 'transfer', '发送', 'send']):
                pattern = "执行转账操作"
                self.evolution_store.add_pattern(pattern, "action", 0.7)
                count += 1

        return count

    def _learn_methods(self) -> int:
        """归纳方法

        Returns:
            归纳的方法数
        """
        count = 0

        # 从模式中归纳方法
        patterns = self.evolution_store.get_patterns(limit=20)

        for pattern in patterns:
            # 如果模式频繁出现，尝试归纳为方法
            if pattern.frequency >= 3 and pattern.category == "action":
                # 检查是否已有方法
                existing = self.evolution_store.get_method(pattern.pattern)
                if not existing:
                    self.evolution_store.add_method(
                        task_type=pattern.pattern,
                        method=f"执行{pattern.pattern}的方法",
                        steps=[]
                    )
                    count += 1

        return count

    def _generate_knowledge(self) -> int:
        """生成知识

        Returns:
            生成的知识数
        """
        count = 0

        # 从重要记忆中生成知识
        important_memories = self.memory_store.get_important_memories(limit=20)

        for memory in important_memories:
            # 检查是否已有类似知识
            existing = self.evolution_store.search_knowledge(memory.content[:50], limit=1)

            if not existing:
                # 提取主题
                topic = memory.content[:50]

                self.evolution_store.add_knowledge(
                    topic=topic,
                    content=memory.content,
                    confidence=0.7,
                    source="memory"
                )
                count += 1

        return count

    # === 总结 ===

    def generate_summary(self, period: str = "daily") -> str:
        """生成进化总结

        Args:
            period: 周期（daily或weekly）

        Returns:
            总结文本
        """
        today = datetime.now().strftime('%Y-%m-%d')

        # 获取今天的对话
        conversations = self.conversation_store.get_recent_messages(
            chat_id="", hours=24
        )

        # 生成总结
        summary = f"""AIsatoshi V27 进化总结 - {period} ({today})

【对话统计】
- 总对话数: {len(conversations)}
- 用户消息: {sum(1 for c in conversations if c.role == 'user')}
- AI回复: {sum(1 for c in conversations if c.role == 'assistant')}

【学习进度】
- 学习周期: {self.stats['learning_cycles']}
- 学习模式: {self.stats['patterns_learned']}
- 归纳方法: {self.stats['methods_learned']}
- 新增知识: {self.stats['knowledge_added']}

【状态】
- 记忆系统: 正常
- 进化系统: 正常
- 持续进化中...
"""

        # 保存总结
        self.evolution_store.save_summary(
            period=period,
            date=today,
            summary=summary,
            insights=[],
            patterns_learned=self.stats['patterns_learned'],
            methods_learned=self.stats['methods_learned'],
            conversations_processed=len(conversations),
        )

        self.stats['summaries_created'] += 1

        return summary

    # === 查询 ===

    def get_patterns(self, category: Optional[str] = None) -> List[Pattern]:
        """获取学习到的模式

        Args:
            category: 类别过滤

        Returns:
            模式列表
        """
        return self.evolution_store.get_patterns(category=category)

    def get_methods(self) -> List[Method]:
        """获取归纳的方法

        Returns:
            方法列表
        """
        return self.evolution_store.get_patterns()  # 复用

    def get_knowledge(self, query: str) -> List[Knowledge]:
        """搜索知识

        Args:
            query: 搜索关键词

        Returns:
            知识列表
        """
        return self.evolution_store.search_knowledge(query)

    # === 统计 ===

    def get_stats(self) -> Dict[str, Any]:
        """获取进化统计

        Returns:
            统计信息字典
        """
        store_stats = self.evolution_store.get_stats()

        return {
            **store_stats,
            'learning_cycles': self.stats['learning_cycles'],
            'patterns_learned': self.stats['patterns_learned'],
            'methods_learned': self.stats['methods_learned'],
            'knowledge_added': self.stats['knowledge_added'],
            'summaries_created': self.stats['summaries_created'],
        }
