"""
AIsatoshi V27 - 对话存储

存储和检索Telegram对话记录。

V27核心特性：对话持久化，确保跨部署保留记忆。
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .database import Database
from models.memory import ConversationMemory, ConversationSummary
from core.exceptions import StorageError
from core.logger import Logger


class ConversationStore(Database):
    """对话存储

    负责管理所有对话记录的持久化。
    """

    def __init__(self, db_path: str, logger: Optional[Logger] = None):
        """初始化对话存储

        Args:
            db_path: 数据库文件路径
            logger: 日志记录器
        """
        super().__init__(db_path, logger)
        self._init_tables()

    def _init_tables(self):
        """初始化数据库表"""
        # 对话表
        if not self.table_exists("conversations"):
            self.execute("""
                CREATE TABLE conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT NOT NULL,
                    message_id INTEGER NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(chat_id, message_id)
                )
            """)
            self.execute("CREATE INDEX idx_chat_timestamp ON conversations(chat_id, timestamp)")

        # 对话总结表
        if not self.table_exists("conversation_summaries"):
            self.execute("""
                CREATE TABLE conversation_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    message_count INTEGER DEFAULT 0,
                    key_topics TEXT,
                    importance INTEGER DEFAULT 3,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(chat_id, date)
                )
            """)
            self.execute("CREATE INDEX idx_summary_date ON conversation_summaries(date)")

        self.logger.debug("对话数据库表初始化完成")

    # === 对话操作 ===

    def add_conversation(self, chat_id: str, message_id: int, role: str,
                        content: str, timestamp: Optional[str] = None) -> int:
        """添加对话记录

        Args:
            chat_id: 聊天ID
            message_id: 消息ID
            role: 角色（user或assistant）
            content: 内容
            timestamp: 时间戳（可选）

        Returns:
            记录ID
        """
        try:
            if timestamp is None:
                timestamp = datetime.now().isoformat()

            cursor = self.execute(
                """INSERT OR IGNORE INTO conversations
                (chat_id, message_id, role, content, timestamp)
                VALUES (?, ?, ?, ?, ?)""",
                (chat_id, message_id, role, content, timestamp)
            )
            row_id = cursor.lastrowid

            if row_id:
                self.logger.debug(f"保存对话: {chat_id} - {role} - {content[:30]}...")
            return row_id

        except sqlite3.Error as e:
            raise StorageError(f"添加对话失败: {e}")

    def get_conversation_history(self, chat_id: str, limit: int = 50,
                                 before: Optional[str] = None) -> List[ConversationMemory]:
        """获取对话历史

        Args:
            chat_id: 聊天ID
            limit: 最大数量
            before: 在此时间之前

        Returns:
            对话列表
        """
        if before:
            rows = self.fetch_all(
                """SELECT * FROM conversations
                WHERE chat_id = ? AND timestamp < ?
                ORDER BY timestamp DESC LIMIT ?""",
                (chat_id, before, limit)
            )
        else:
            rows = self.fetch_all(
                """SELECT * FROM conversations
                WHERE chat_id = ?
                ORDER BY timestamp DESC LIMIT ?""",
                (chat_id, limit)
            )

        return [
            ConversationMemory(
                chat_id=row['chat_id'],
                message_id=row['message_id'],
                role=row['role'],
                content=row['content'],
                timestamp=row['timestamp'],
            )
            for row in rows
        ]

    def get_recent_messages(self, chat_id: str, hours: int = 24) -> List[ConversationMemory]:
        """获取最近的对话

        Args:
            chat_id: 聊天ID
            hours: 最近几小时

        Returns:
            对话列表
        """
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        rows = self.fetch_all(
            """SELECT * FROM conversations
            WHERE chat_id = ? AND timestamp > ?
            ORDER BY timestamp ASC""",
            (chat_id, cutoff)
        )

        return [
            ConversationMemory(
                chat_id=row['chat_id'],
                message_id=row['message_id'],
                role=row['role'],
                content=row['content'],
                timestamp=row['timestamp'],
            )
            for row in rows
        ]

    def get_all_messages(self, limit: int = 1000) -> List[ConversationMemory]:
        """获取所有对话（用于全局搜索）

        Args:
            limit: 最大数量

        Returns:
            对话列表
        """
        rows = self.fetch_all(
            """SELECT * FROM conversations
            ORDER BY timestamp DESC LIMIT ?""",
            (limit,)
        )

        return [
            ConversationMemory(
                chat_id=row['chat_id'],
                message_id=row['message_id'],
                role=row['role'],
                content=row['content'],
                timestamp=row['timestamp'],
            )
            for row in rows
        ]

    def search_conversations(self, query: str, limit: int = 20) -> List[ConversationMemory]:
        """搜索对话

        Args:
            query: 搜索关键词
            limit: 最大数量

        Returns:
            对话列表
        """
        rows = self.fetch_all(
            """SELECT * FROM conversations
            WHERE content LIKE ?
            ORDER BY timestamp DESC LIMIT ?""",
            (f"%{query}%", limit)
        )

        return [
            ConversationMemory(
                chat_id=row['chat_id'],
                message_id=row['message_id'],
                role=row['role'],
                content=row['content'],
                timestamp=row['timestamp'],
            )
            for row in rows
        ]

    def get_conversation_count(self, chat_id: Optional[str] = None) -> int:
        """获取对话数量

        Args:
            chat_id: 聊天ID（可选，不指定则返回总数）

        Returns:
            对话数量
        """
        if chat_id:
            result = self.fetch_one(
                "SELECT COUNT(*) as count FROM conversations WHERE chat_id = ?",
                (chat_id,)
            )
        else:
            result = self.fetch_one("SELECT COUNT(*) as count FROM conversations")

        return result['count'] if result else 0

    def get_stats(self) -> Dict[str, Any]:
        """获取对话统计

        Returns:
            统计信息字典
        """
        total = self.fetch_one("SELECT COUNT(*) as count FROM conversations")['count']
        users = self.fetch_one("SELECT COUNT(DISTINCT chat_id) as count FROM conversations")['count']
        user_msgs = self.fetch_one("SELECT COUNT(*) as count FROM conversations WHERE role='user'")['count']
        bot_msgs = self.fetch_one("SELECT COUNT(*) as count FROM conversations WHERE role='assistant'")['count']

        return {
            'total_messages': total,
            'unique_users': users,
            'user_messages': user_msgs,
            'bot_messages': bot_msgs,
        }

    # === 对话总结操作 ===

    def save_summary(self, summary: ConversationSummary) -> int:
        """保存对话总结

        Args:
            summary: 对话总结对象

        Returns:
            记录ID
        """
        try:
            cursor = self.execute(
                """INSERT OR REPLACE INTO conversation_summaries
                (chat_id, date, summary, message_count, key_topics, importance)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    summary.chat_id,
                    summary.date,
                    summary.summary,
                    summary.message_count,
                    json.dumps(summary.key_topics),
                    summary.importance,
                )
            )
            return cursor.lastrowid

        except sqlite3.Error as e:
            raise StorageError(f"保存总结失败: {e}")

    def get_summary(self, chat_id: str, date: str) -> Optional[ConversationSummary]:
        """获取对话总结

        Args:
            chat_id: 聊天ID
            date: 日期（YYYY-MM-DD）

        Returns:
            对话总结对象或None
        """
        row = self.fetch_one(
            """SELECT * FROM conversation_summaries
            WHERE chat_id = ? AND date = ?""",
            (chat_id, date)
        )

        if row:
            return ConversationSummary(
                chat_id=row['chat_id'],
                date=row['date'],
                summary=row['summary'],
                message_count=row['message_count'],
                key_topics=json.loads(row['key_topics']) if row['key_topics'] else [],
                importance=row['importance'],
                created_at=row['created_at'],
            )
        return None

    def get_recent_summaries(self, chat_id: str, days: int = 7) -> List[ConversationSummary]:
        """获取最近的对话总结

        Args:
            chat_id: 聊天ID
            days: 最近几天

        Returns:
            对话总结列表
        """
        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        rows = self.fetch_all(
            """SELECT * FROM conversation_summaries
            WHERE chat_id = ? AND date >= ?
            ORDER BY date DESC""",
            (chat_id, cutoff)
        )

        return [
            ConversationSummary(
                chat_id=row['chat_id'],
                date=row['date'],
                summary=row['summary'],
                message_count=row['message_count'],
                key_topics=json.loads(row['key_topics']) if row['key_topics'] else [],
                importance=row['importance'],
                created_at=row['created_at'],
            )
            for row in rows
        ]

    def get_all_summaries(self, limit: int = 50) -> List[ConversationSummary]:
        """获取所有对话总结

        Args:
            limit: 最大数量

        Returns:
            对话总结列表
        """
        rows = self.fetch_all(
            """SELECT * FROM conversation_summaries
            ORDER BY date DESC LIMIT ?""",
            (limit,)
        )

        return [
            ConversationSummary(
                chat_id=row['chat_id'],
                date=row['date'],
                summary=row['summary'],
                message_count=row['message_count'],
                key_topics=json.loads(row['key_topics']) if row['key_topics'] else [],
                importance=row['importance'],
                created_at=row['created_at'],
            )
            for row in rows
        ]
