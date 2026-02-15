"""
AIsatoshi V27 - 记忆模型

定义记忆相关的数据结构。

V27核心特性：记忆原生 - 所有记忆都会被持久化和检索。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class MemoryType(Enum):
    """记忆类型枚举"""
    FACT = "fact"                      # 事实记忆（客观事实）
    EVENT = "event"                    # 事件记忆（发生的事情）
    PREFERENCE = "preference"          # 偏好记忆（用户偏好）
    SKILL = "skill"                    # 技能记忆（学到的技能）
    EXPERIENCE = "experience"          # 经验记忆（积累的经验）
    CONVERSATION = "conversation"      # 对话记忆（对话历史）
    SUMMARY = "summary"                # 总结记忆（对话总结）


@dataclass
class Memory:
    """记忆基类

    所有类型的记忆的基础结构。
    """
    id: int
    type: str                          # MemoryType值
    content: str                       # 记忆内容
    importance: int = 3                # 重要性（1-5）
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    embedding: Optional[str] = None    # 用于语义搜索

    @property
    def age_seconds(self) -> int:
        """获取记忆年龄（秒）"""
        try:
            created = datetime.fromisoformat(self.created_at)
            return int((datetime.now() - created).total_seconds())
        except:
            return 0

    @property
    def age_hours(self) -> float:
        """获取记忆年龄（小时）"""
        return self.age_seconds / 3600

    @property
    def age_days(self) -> float:
        """获取记忆年龄（天）"""
        return self.age_hours / 24

    def is_recent(self, hours: int = 24) -> bool:
        """检查是否是最近记忆"""
        return self.age_hours < hours

    def is_important(self) -> bool:
        """检查是否重要"""
        return self.importance >= 4

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'type': self.type,
            'content': self.content,
            'importance': self.importance,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'metadata': self.metadata,
            'tags': self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Memory':
        """从字典创建"""
        return cls(
            id=data['id'],
            type=data['type'],
            content=data['content'],
            importance=data.get('importance', 3),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            metadata=data.get('metadata', {}),
            tags=data.get('tags', []),
        )


@dataclass
class Fact(Memory):
    """事实记忆

    存储客观事实，如：
    - 用户的名字
    - 用户喜欢的币种
    - 重要日期
    """
    fact_type: str = ""               # 事实类型：user_info, preference, etc.
    confidence: float = 1.0           # 置信度

    def __post_init__(self):
        """后处理"""
        if not self.type:
            self.type = MemoryType.FACT.value


@dataclass
class ConversationMemory:
    """对话记忆

    存储对话的完整上下文。
    """
    chat_id: str
    message_id: int
    role: str                          # 'user' or 'assistant'
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    summary_id: Optional[int] = None   # 关联的总结ID

    @property
    def is_from_user(self) -> bool:
        """是否来自用户"""
        return self.role == 'user'

    @property
    def is_from_assistant(self) -> bool:
        """是否来自助手"""
        return self.role == 'assistant'

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'chat_id': self.chat_id,
            'message_id': self.message_id,
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp,
            'summary_id': self.summary_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMemory':
        """从字典创建"""
        return cls(
            chat_id=data['chat_id'],
            message_id=data['message_id'],
            role=data['role'],
            content=data['content'],
            timestamp=data.get('timestamp'),
            summary_id=data.get('summary_id'),
        )


@dataclass
class ConversationSummary:
    """对话总结

    对一段对话的压缩总结，节省存储空间。
    """
    chat_id: str
    date: str                          # 日期（YYYY-MM-DD）
    summary: str                       # 总结内容
    message_count: int = 0             # 包含的消息数
    key_topics: List[str] = field(default_factory=list)
    importance: int = 3
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'chat_id': self.chat_id,
            'date': self.date,
            'summary': self.summary,
            'message_count': self.message_count,
            'key_topics': self.key_topics,
            'importance': self.importance,
            'created_at': self.created_at,
        }


@dataclass
class MemoryAssociation:
    """记忆关联

    表示两个记忆之间的关联关系。
    """
    memory_id: int
    associated_id: int
    strength: float = 1.0              # 关联强度（0-1）
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'memory_id': self.memory_id,
            'associated_id': self.associated_id,
            'strength': self.strength,
            'created_at': self.created_at,
        }
