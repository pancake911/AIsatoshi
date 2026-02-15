"""
AIsatoshi V27 - 记忆存储

存储和检索记忆。

V27核心特性：记忆持久化，确保跨部署保留所有记忆。
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from .database import Database
from models.memory import Memory, Fact, MemoryAssociation
from core.exceptions import MemoryStoreError
from core.logger import Logger


class MemoryStore(Database):
    """记忆存储

    负责管理所有记忆的持久化。
    """

    def __init__(self, db_path: str, logger: Optional[Logger] = None):
        """初始化记忆存储

        Args:
            db_path: 数据库文件路径
            logger: 日志记录器
        """
        super().__init__(db_path, logger)
        self._init_tables()

    def _init_tables(self):
        """初始化数据库表"""
        # 记忆表
        if not self.table_exists("memories"):
            self.execute("""
                CREATE TABLE memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL CHECK(type IN
                        ('fact', 'event', 'preference', 'skill', 'experience', 'conversation', 'summary')),
                    content TEXT NOT NULL,
                    importance INTEGER DEFAULT 3,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    tags TEXT,
                    embedding TEXT
                )
            """)
            self.execute("CREATE INDEX idx_memory_type ON memories(type)")
            self.execute("CREATE INDEX idx_memory_importance ON memories(importance)")

        # 记忆关联表
        if not self.table_exists("memory_associations"):
            self.execute("""
                CREATE TABLE memory_associations (
                    memory_id INTEGER NOT NULL,
                    associated_id INTEGER NOT NULL,
                    strength REAL DEFAULT 1.0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (memory_id, associated_id),
                    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE,
                    FOREIGN KEY (associated_id) REFERENCES memories(id) ON DELETE CASCADE
                )
            """)
            self.execute("CREATE INDEX idx_assoc_strength ON memory_associations(strength)")

        # 身份信息表（存储AIsatoshi的身份信息）
        if not self.table_exists("identity"):
            self.execute("""
                CREATE TABLE identity (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

        self.logger.debug("记忆数据库表初始化完成")

    # === 记忆操作 ===

    def add_memory(self, memory: Memory) -> int:
        """添加记忆

        Args:
            memory: 记忆对象

        Returns:
            记忆ID
        """
        try:
            cursor = self.execute(
                """INSERT INTO memories
                (type, content, importance, metadata, tags)
                VALUES (?, ?, ?, ?, ?)""",
                (
                    memory.type,
                    memory.content,
                    memory.importance,
                    json.dumps(memory.metadata) if memory.metadata else None,
                    json.dumps(memory.tags) if memory.tags else None,
                )
            )
            memory_id = cursor.lastrowid
            self.logger.memory_saved(memory.type)
            return memory_id

        except sqlite3.Error as e:
            self.logger.error(f"添加记忆失败: {e}")
            raise MemoryStoreError(f"添加记忆失败: {e}")

    def get_memory(self, memory_id: int) -> Optional[Memory]:
        """获取记忆

        Args:
            memory_id: 记忆ID

        Returns:
            记忆对象或None
        """
        row = self.fetch_one("SELECT * FROM memories WHERE id = ?", (memory_id,))

        if row:
            return Memory(
                id=row['id'],
                type=row['type'],
                content=row['content'],
                importance=row['importance'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                metadata=json.loads(row['metadata']) if row['metadata'] else {},
                tags=json.loads(row['tags']) if row['tags'] else [],
            )
        return None

    def search_memories(self, query: str, limit: int = 20,
                       memory_type: Optional[str] = None,
                       min_importance: int = 1) -> List[Memory]:
        """搜索记忆

        Args:
            query: 搜索关键词
            limit: 最大数量
            memory_type: 记忆类型过滤（可选）
            min_importance: 最小重要性（可选）

        Returns:
            记忆列表
        """
        # 构建SQL查询
        conditions = ["content LIKE ?", "importance >= ?"]
        params = [f"%{query}%", min_importance]

        if memory_type:
            conditions.append("type = ?")
            params.append(memory_type)

        sql = f"SELECT * FROM memories WHERE {' AND '.join(conditions)} ORDER BY importance DESC, created_at DESC LIMIT ?"
        params.append(limit)

        rows = self.fetch_all(sql, tuple(params))

        return [
            Memory(
                id=row['id'],
                type=row['type'],
                content=row['content'],
                importance=row['importance'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                metadata=json.loads(row['metadata']) if row['metadata'] else {},
                tags=json.loads(row['tags']) if row['tags'] else [],
            )
            for row in rows
        ]

    def get_recent_memories(self, limit: int = 50,
                           memory_type: Optional[str] = None) -> List[Memory]:
        """获取最近的记忆

        Args:
            limit: 最大数量
            memory_type: 记忆类型过滤（可选）

        Returns:
            记忆列表
        """
        if memory_type:
            rows = self.fetch_all(
                "SELECT * FROM memories WHERE type = ? ORDER BY created_at DESC LIMIT ?",
                (memory_type, limit)
            )
        else:
            rows = self.fetch_all(
                "SELECT * FROM memories ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )

        return [
            Memory(
                id=row['id'],
                type=row['type'],
                content=row['content'],
                importance=row['importance'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                metadata=json.loads(row['metadata']) if row['metadata'] else {},
                tags=json.loads(row['tags']) if row['tags'] else [],
            )
            for row in rows
        ]

    def get_important_memories(self, min_importance: int = 4,
                               limit: int = 50) -> List[Memory]:
        """获取重要记忆

        Args:
            min_importance: 最小重要性
            limit: 最大数量

        Returns:
            记忆列表
        """
        rows = self.fetch_all(
            """SELECT * FROM memories
            WHERE importance >= ?
            ORDER BY importance DESC, created_at DESC
            LIMIT ?""",
            (min_importance, limit)
        )

        return [
            Memory(
                id=row['id'],
                type=row['type'],
                content=row['content'],
                importance=row['importance'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                metadata=json.loads(row['metadata']) if row['metadata'] else {},
                tags=json.loads(row['tags']) if row['tags'] else [],
            )
            for row in rows
        ]

    def update_memory(self, memory_id: int, content: Optional[str] = None,
                     importance: Optional[int] = None) -> bool:
        """更新记忆

        Args:
            memory_id: 记忆ID
            content: 新内容（可选）
            importance: 新重要性（可选）

        Returns:
            是否成功
        """
        try:
            updates = []
            params = []

            if content is not None:
                updates.append("content = ?")
                params.append(content)

            if importance is not None:
                updates.append("importance = ?")
                params.append(importance)

            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(memory_id)

            self.execute(
                f"UPDATE memories SET {', '.join(updates)} WHERE id = ?",
                tuple(params)
            )
            return True

        except sqlite3.Error as e:
            self.logger.error(f"更新记忆失败: {e}")
            raise MemoryStoreError(f"更新记忆失败: {e}")

    def delete_memory(self, memory_id: int) -> bool:
        """删除记忆

        Args:
            memory_id: 记忆ID

        Returns:
            是否成功
        """
        try:
            self.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            return True

        except sqlite3.Error as e:
            self.logger.error(f"删除记忆失败: {e}")
            raise MemoryStoreError(f"删除记忆失败: {e}")

    # === 身份信息操作 ===

    def set_identity(self, key: str, value: str) -> bool:
        """设置身份信息

        Args:
            key: 键
            value: 值

        Returns:
            是否成功
        """
        try:
            self.execute(
                """INSERT OR REPLACE INTO identity (key, value, updated_at)
                VALUES (?, ?, ?)""",
                (key, value, datetime.now().isoformat())
            )
            self.logger.debug(f"身份信息已设置: {key}")
            return True

        except sqlite3.Error as e:
            self.logger.error(f"设置身份信息失败: {e}")
            return False

    def get_identity(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """获取身份信息

        Args:
            key: 键
            default: 默认值

        Returns:
            值或默认值
        """
        result = self.fetch_one("SELECT value FROM identity WHERE key = ?", (key,))
        return result['value'] if result else default

    def get_all_identity(self) -> Dict[str, str]:
        """获取所有身份信息

        Returns:
            身份信息字典
        """
        rows = self.fetch_all("SELECT key, value FROM identity")
        return {row['key']: row['value'] for row in rows}

    # === 统计 ===

    def get_memory_count(self, memory_type: Optional[str] = None) -> int:
        """获取记忆数量

        Args:
            memory_type: 记忆类型过滤（可选）

        Returns:
            记忆数量
        """
        if memory_type:
            result = self.fetch_one(
                "SELECT COUNT(*) as count FROM memories WHERE type = ?",
                (memory_type,)
            )
        else:
            result = self.fetch_one("SELECT COUNT(*) as count FROM memories")

        return result['count'] if result else 0

    def get_stats(self) -> Dict[str, Any]:
        """获取记忆统计

        Returns:
            统计信息字典
        """
        total = self.fetch_one("SELECT COUNT(*) as count FROM memories")['count']

        # 按类型统计
        type_stats = {}
        for mem_type in ['fact', 'event', 'preference', 'skill', 'experience']:
            result = self.fetch_one(
                "SELECT COUNT(*) as count FROM memories WHERE type = ?",
                (mem_type,)
            )
            type_stats[mem_type] = result['count'] if result else 0

        # 重要记忆
        important = self.fetch_one(
            "SELECT COUNT(*) as count FROM memories WHERE importance >= 4"
        )['count']

        return {
            'total': total,
            'by_type': type_stats,
            'important': important,
        }
