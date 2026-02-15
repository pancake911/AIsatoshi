"""
AIsatoshi V27 - 存储层

提供所有数据持久化功能。

V27核心特性：所有数据存储在/app/data目录，确保跨部署保留。
"""

from .database import Database, init_all_databases
from .memory_store import MemoryStore
from .task_store import TaskStore
from .conversation_store import ConversationStore
from .evolution_store import EvolutionStore

__all__ = [
    'Database',
    'init_all_databases',
    'MemoryStore',
    'TaskStore',
    'ConversationStore',
    'EvolutionStore',
]
