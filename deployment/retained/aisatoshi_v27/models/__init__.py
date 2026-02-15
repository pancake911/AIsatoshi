"""
AIsatoshi V27 - 数据模型层

定义所有核心数据结构。
"""

from .message import TelegramMessage, MessageEntity
from .task import Task, TaskType, TaskStatus, TaskPriority
from .memory import Memory, MemoryType, Fact, ConversationMemory
from .evolution import Pattern, Method, Knowledge, EvolutionSummary

__all__ = [
    # Message
    'TelegramMessage',
    'MessageEntity',
    # Task
    'Task',
    'TaskType',
    'TaskStatus',
    'TaskPriority',
    # Memory
    'Memory',
    'MemoryType',
    'Fact',
    'ConversationMemory',
    # Evolution
    'Pattern',
    'Method',
    'Knowledge',
    'EvolutionSummary',
]
