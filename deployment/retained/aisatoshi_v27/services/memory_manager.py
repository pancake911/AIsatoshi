"""
AIsatoshi V27 - 记忆管理器

V27核心功能：原生记忆系统

负责管理AIsatoshi的所有形式记忆：
- 对话记忆
- 事实记忆
- 事件记忆
- 偏好记忆
- 经验记忆

所有记忆都会持久化到数据库，确保跨部署保留。
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from storage.memory_store import MemoryStore
from storage.conversation_store import ConversationStore
from models.memory import Memory, MemoryType, Fact
from core.logger import Logger


class MemoryManager:
    """记忆管理器

    AIsatoshi的记忆系统核心。
    """

    def __init__(
        self,
        memory_store: MemoryStore,
        conversation_store: ConversationStore,
        logger: Optional[Logger] = None
    ):
        """初始化记忆管理器

        Args:
            memory_store: 记忆存储
            conversation_store: 对话存储
            logger: 日志记录器
        """
        self.memory_store = memory_store
        self.conversation_store = conversation_store
        self.logger = logger or Logger(name="MemoryManager")

        # 加载身份信息
        self._load_identity()

        # 统计信息
        self.stats = {
            'conversations_processed': 0,
            'facts_learned': 0,
            'summaries_created': 0,
        }

    def _load_identity(self):
        """加载身份信息"""
        identity = self.memory_store.get_all_identity()
        self.name = identity.get('name', 'AIsatoshi')
        self.mission = identity.get('mission', '构建Web3 AI生态系统')
        self.personality = identity.get('personality', '理性、好奇、友好')
        self.creator = identity.get('creator', '未知')

        self.logger.info(f"身份已加载: {self.name}")

    def set_identity(self, key: str, value: str):
        """设置身份信息

        Args:
            key: 键（name, mission, personality, creator等）
            value: 值
        """
        self.memory_store.set_identity(key, value)
        if key == 'name':
            self.name = value
        elif key == 'mission':
            self.mission = value
        elif key == 'personality':
            self.personality = value
        elif key == 'creator':
            self.creator = value

        self.logger.info(f"身份信息已更新: {key} = {value}")

    # === 对话记忆 ===

    def save_conversation(self, chat_id: str, message_id: int,
                         role: str, content: str) -> bool:
        """保存对话

        Args:
            chat_id: 聊天ID
            message_id: 消息ID
            role: 角色（user或assistant）
            content: 内容

        Returns:
            是否成功
        """
        try:
            self.conversation_store.add_conversation(
                chat_id, message_id, role, content
            )
            self.stats['conversations_processed'] += 1
            self.logger.debug(f"对话已保存: {chat_id} - {role}")
            return True

        except Exception as e:
            self.logger.error(f"保存对话失败: {e}")
            return False

    def get_conversation_history(self, chat_id: str, limit: int = 50) -> List[Dict]:
        """获取对话历史

        Args:
            chat_id: 聊天ID
            limit: 最大数量

        Returns:
            对话列表
        """
        conversations = self.conversation_store.get_conversation_history(
            chat_id, limit
        )

        return [
            {
                'role': conv.role,
                'content': conv.content,
                'timestamp': conv.timestamp,
            }
            for conv in conversations
        ]

    def get_recent_context(self, chat_id: str, hours: int = 24) -> List[Dict]:
        """获取最近的对话上下文

        Args:
            chat_id: 聊天ID
            hours: 最近几小时

        Returns:
            对话列表
        """
        conversations = self.conversation_store.get_recent_messages(
            chat_id, hours
        )

        return [
            {
                'role': conv.role,
                'content': conv.content,
                'timestamp': conv.timestamp,
            }
            for conv in conversations
        ]

    # === 事实记忆 ===

    def remember_fact(self, fact: str, importance: int = 3,
                     category: str = "") -> int:
        """记住一个事实

        Args:
            fact: 事实内容
            importance: 重要性（1-5）
            category: 类别

        Returns:
            记忆ID
        """
        memory = Memory(
            id=0,  # 将由数据库分配
            type=MemoryType.FACT.value,
            content=fact,
            importance=importance,
            metadata={'category': category} if category else {},
        )

        memory_id = self.memory_store.add_memory(memory)
        self.stats['facts_learned'] += 1
        self.logger.debug(f"已记住事实: {fact[:50]}...")

        return memory_id

    def recall_facts(self, context: str, limit: int = 5) -> List[str]:
        """回忆相关事实

        Args:
            context: 上下文关键词
            limit: 最大数量

        Returns:
            事实列表
        """
        memories = self.memory_store.search_memories(
            context, limit=limit, memory_type=MemoryType.FACT.value
        )

        return [mem.content for mem in memories]

    def get_important_facts(self, limit: int = 20) -> List[str]:
        """获取重要事实

        Args:
            limit: 最大数量

        Returns:
            事实列表
        """
        memories = self.memory_store.get_important_memories(
            min_importance=4, limit=limit
        )

        return [mem.content for mem in memories]

    # === 事件记忆 ===

    def remember_event(self, event: str, importance: int = 3) -> int:
        """记住一个事件

        Args:
            event: 事件描述
            importance: 重要性

        Returns:
            记忆ID
        """
        memory = Memory(
            id=0,
            type=MemoryType.EVENT.value,
            content=event,
            importance=importance,
            metadata={'timestamp': datetime.now().isoformat()},
        )

        memory_id = self.memory_store.add_memory(memory)
        self.logger.debug(f"已记住事件: {event[:50]}...")

        return memory_id

    # === 偏好记忆 ===

    def remember_preference(self, preference: str) -> int:
        """记住一个偏好

        Args:
            preference: 偏好描述

        Returns:
            记忆ID
        """
        memory = Memory(
            id=0,
            type=MemoryType.PREFERENCE.value,
            content=preferences,
            importance=4,  # 偏好很重要
        )

        memory_id = self.memory_store.add_memory(memory)
        self.logger.debug(f"已记住偏好: {preference[:50]}...")

        return memory_id

    def get_preferences(self) -> List[str]:
        """获取所有偏好

        Returns:
            偏好列表
        """
        memories = self.memory_store.get_recent_memories(
            limit=100, memory_type=MemoryType.PREFERENCE.value
        )

        return [mem.content for mem in memories]

    # === 搜索和检索 ===

    def search(self, query: str, limit: int = 20) -> List[Dict]:
        """搜索所有类型记忆

        Args:
            query: 搜索关键词
            limit: 最大数量

        Returns:
            记忆列表
        """
        memories = self.memory_store.search_memories(query, limit=limit)

        return [
            {
                'id': mem.id,
                'type': mem.type,
                'content': mem.content,
                'importance': mem.importance,
                'created_at': mem.created_at,
            }
            for mem in memories
        ]

    def search_conversations(self, query: str, limit: int = 20) -> List[Dict]:
        """搜索对话

        Args:
            query: 搜索关键词
            limit: 最大数量

        Returns:
            对话列表
        """
        conversations = self.conversation_store.search_conversations(
            query, limit
        )

        return [
            {
                'chat_id': conv.chat_id,
                'role': conv.role,
                'content': conv.content,
                'timestamp': conv.timestamp,
            }
            for conv in conversations
        ]

    # === 构建AI提示词上下文 ===

    def build_context_for_ai(self, chat_id: str, user_message: str,
                             max_length: int = 8000) -> str:
        """构建AI提示词上下文

        Args:
            chat_id: 聊天ID
            user_message: 用户消息
            max_length: 最大长度

        Returns:
            上下文字符串
        """
        context_parts = []

        # 1. 身份信息
        context_parts.append(f"""【你的身份】
名称: {self.name}
使命: {self.mission}
性格: {self.personality}
创建者: {self.creator}""")

        # 2. 对话历史（最近的）
        recent_context = self.get_recent_context(chat_id, hours=48)
        if recent_context:
            context_parts.append("\n【最近的对话】")
            for conv in recent_context[-10:]:  # 最近10条
                role = "用户" if conv['role'] == 'user' else "你"
                context_parts.append(f"{role}: {conv['content']}")

        # 3. 搜索相关记忆
        relevant_memories = self.search(user_message, limit=5)
        if relevant_memories:
            context_parts.append("\n【相关记忆】")
            for mem in relevant_memories:
                context_parts.append(f"- {mem['content']}")

        # 4. 重要事实
        important_facts = self.get_important_facts(limit=10)
        if important_facts:
            context_parts.append("\n【重要信息】")
            for fact in important_facts:
                context_parts.append(f"- {fact}")

        # 组合并限制长度
        full_context = "\n".join(context_parts)
        if len(full_context) > max_length:
            full_context = full_context[:max_length] + "\n...(已截断)"

        return full_context

    # === 统计 ===

    def get_stats(self) -> Dict[str, Any]:
        """获取记忆统计

        Returns:
            统计信息字典
        """
        memory_stats = self.memory_store.get_stats()
        conversation_stats = self.conversation_store.get_stats()

        return {
            'memories': memory_stats,
            'conversations': conversation_stats,
            'processed': self.stats,
        }

    def get_summary(self) -> str:
        """获取记忆系统摘要

        Returns:
            摘要字符串
        """
        stats = self.get_stats()

        return f"""AIsatoshi V27 记忆系统摘要:

- 总记忆数: {stats['memories']['total']}
- 对话记录: {stats['conversations']['total_messages']} 条
- 用户数: {stats['conversations']['unique_users']}
- 已处理对话: {stats['processed']['conversations_processed']}
- 已学习事实: {stats['processed']['facts_learned']}
"""
