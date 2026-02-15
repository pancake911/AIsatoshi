"""
AIsatoshi V27 - 进化存储

存储和检索进化记录。

V27核心特性：进化记录持久化，确保学习内容不丢失。
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from .database import Database
from models.evolution import Pattern, Method, Knowledge, EvolutionSummary
from core.exceptions import EvolutionError
from core.logger import Logger


class EvolutionStore(Database):
    """进化存储

    负责管理所有进化相关数据的持久化。
    """

    def __init__(self, db_path: str, logger: Optional[Logger] = None):
        """初始化进化存储

        Args:
            db_path: 数据库文件路径
            logger: 日志记录器
        """
        super().__init__(db_path, logger)
        self._init_tables()

    def _init_tables(self):
        """初始化数据库表"""
        # 模式表
        if not self.table_exists("patterns"):
            self.execute("""
                CREATE TABLE patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern TEXT NOT NULL UNIQUE,
                    frequency INTEGER DEFAULT 1,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    confidence REAL DEFAULT 0.5,
                    category TEXT,
                    metadata TEXT
                )
            """)
            self.execute("CREATE INDEX idx_pattern_freq ON patterns(frequency)")
            self.execute("CREATE INDEX idx_pattern_category ON patterns(category)")

        # 方法表
        if not self.table_exists("methods"):
            self.execute("""
                CREATE TABLE methods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_type TEXT NOT NULL,
                    method TEXT NOT NULL,
                    steps TEXT,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    last_used DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.execute("CREATE INDEX idx_method_task ON methods(task_type)")
            self.execute("CREATE INDEX idx_method_success ON methods(success_count)")

        # 知识表
        if not self.table_exists("knowledge"):
            self.execute("""
                CREATE TABLE knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    content TEXT NOT NULL,
                    confidence REAL DEFAULT 0.5,
                    source TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    verified BOOLEAN DEFAULT 0,
                    ref_data TEXT
                )
            """)
            self.execute("CREATE INDEX idx_knowledge_topic ON knowledge(topic)")
            self.execute("CREATE INDEX idx_knowledge_confidence ON knowledge(confidence)")

        # 进化总结表
        if not self.table_exists("evolution_summaries"):
            self.execute("""
                CREATE TABLE evolution_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    period TEXT NOT NULL,
                    date TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    insights TEXT,
                    patterns_learned INTEGER DEFAULT 0,
                    methods_learned INTEGER DEFAULT 0,
                    conversations_processed INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(period, date)
                )
            """)
            self.execute("CREATE INDEX idx_summary_period ON evolution_summaries(period, date)")

        self.logger.debug("进化数据库表初始化完成")

    # === 模式操作 ===

    def add_pattern(self, pattern: str, category: str = "",
                   confidence: float = 0.5) -> int:
        """添加或更新模式

        Args:
            pattern: 模式描述
            category: 类别
            confidence: 置信度

        Returns:
            模式ID
        """
        try:
            # 检查是否已存在
            existing = self.fetch_one(
                "SELECT id, frequency FROM patterns WHERE pattern = ?",
                (pattern,)
            )

            if existing:
                # 更新现有模式
                self.execute(
                    """UPDATE patterns
                    SET frequency = frequency + 1, last_seen = ?, confidence = ?
                    WHERE id = ?""",
                    (datetime.now().isoformat(), confidence, existing['id'])
                )
                return existing['id']
            else:
                # 插入新模式
                cursor = self.execute(
                    """INSERT INTO patterns (pattern, category, confidence)
                    VALUES (?, ?, ?)""",
                    (pattern, category, confidence)
                )
                self.logger.debug(f"新模式已学习: {pattern[:50]}...")
                return cursor.lastrowid

        except sqlite3.Error as e:
            self.logger.error(f"保存模式失败: {e}")
            raise EvolutionError(f"保存模式失败: {e}")

    def get_patterns(self, category: Optional[str] = None,
                    min_frequency: int = 1,
                    limit: int = 100) -> List[Pattern]:
        """获取模式

        Args:
            category: 类别过滤（可选）
            min_frequency: 最小频率
            limit: 最大数量

        Returns:
            模式列表
        """
        if category:
            rows = self.fetch_all(
                """SELECT * FROM patterns
                WHERE category = ? AND frequency >= ?
                ORDER BY frequency DESC, confidence DESC
                LIMIT ?""",
                (category, min_frequency, limit)
            )
        else:
            rows = self.fetch_all(
                """SELECT * FROM patterns
                WHERE frequency >= ?
                ORDER BY frequency DESC, confidence DESC
                LIMIT ?""",
                (min_frequency, limit)
            )

        return [
            Pattern(
                id=row['id'],
                pattern=row['pattern'],
                frequency=row['frequency'],
                last_seen=row['last_seen'],
                confidence=row['confidence'],
                category=row['category'] or "",
                metadata=json.loads(row['metadata']) if row['metadata'] else {},
            )
            for row in rows
        ]

    # === 方法操作 ===

    def add_method(self, task_type: str, method: str,
                   steps: List[str]) -> int:
        """添加方法

        Args:
            task_type: 任务类型
            method: 方法描述
            steps: 具体步骤

        Returns:
            方法ID
        """
        try:
            cursor = self.execute(
                """INSERT INTO methods (task_type, method, steps)
                VALUES (?, ?, ?)""",
                (task_type, method, json.dumps(steps))
            )
            self.logger.debug(f"新方法已学习: {method[:50]}...")
            return cursor.lastrowid

        except sqlite3.Error as e:
            self.logger.error(f"保存方法失败: {e}")
            raise EvolutionError(f"保存方法失败: {e}")

    def get_method(self, task_type: str) -> Optional[Method]:
        """获取指定任务类型的最佳方法

        Args:
            task_type: 任务类型

        Returns:
            方法对象或None
        """
        row = self.fetch_one(
            """SELECT * FROM methods
            WHERE task_type = ?
            ORDER BY success_count DESC, success_count * 1.0 / (success_count + failure_count + 1) DESC
            LIMIT 1""",
            (task_type,)
        )

        if row:
            return Method(
                id=row['id'],
                task_type=row['task_type'],
                method=row['method'],
                steps=json.loads(row['steps']) if row['steps'] else [],
                success_count=row['success_count'],
                failure_count=row['failure_count'],
                last_used=row['last_used'],
                created_at=row['created_at'],
            )
        return None

    def record_method_success(self, method_id: int) -> bool:
        """记录方法成功

        Args:
            method_id: 方法ID

        Returns:
            是否成功
        """
        try:
            self.execute(
                """UPDATE methods
                SET success_count = success_count + 1, last_used = ?
                WHERE id = ?""",
                (datetime.now().isoformat(), method_id)
            )
            return True

        except sqlite3.Error as e:
            self.logger.error(f"记录方法成功失败: {e}")
            return False

    def record_method_failure(self, method_id: int) -> bool:
        """记录方法失败

        Args:
            method_id: 方法ID

        Returns:
            是否成功
        """
        try:
            self.execute(
                """UPDATE methods
                SET failure_count = failure_count + 1, last_used = ?
                WHERE id = ?""",
                (datetime.now().isoformat(), method_id)
            )
            return True

        except sqlite3.Error as e:
            self.logger.error(f"记录方法失败: {e}")
            return False

    # === 知识操作 ===

    def add_knowledge(self, topic: str, content: str,
                     confidence: float = 0.5,
                     source: str = "conversation") -> int:
        """添加知识

        Args:
            topic: 主题
            content: 内容
            confidence: 置信度
            source: 来源

        Returns:
            知识ID
        """
        try:
            cursor = self.execute(
                """INSERT INTO knowledge (topic, content, confidence, source)
                VALUES (?, ?, ?, ?)""",
                (topic, content, confidence, source)
            )
            self.logger.debug(f"新知识已添加: {topic[:50]}...")
            return cursor.lastrowid

        except sqlite3.Error as e:
            self.logger.error(f"保存知识失败: {e}")
            raise EvolutionError(f"保存知识失败: {e}")

    def search_knowledge(self, query: str, limit: int = 10) -> List[Knowledge]:
        """搜索知识

        Args:
            query: 搜索关键词
            limit: 最大数量

        Returns:
            知识列表
        """
        rows = self.fetch_all(
            """SELECT * FROM knowledge
            WHERE topic LIKE ? OR content LIKE ?
            ORDER BY confidence DESC
            LIMIT ?""",
            (f"%{query}%", f"%{query}%", limit)
        )

        return [
            Knowledge(
                id=row['id'],
                topic=row['topic'],
                content=row['content'],
                confidence=row['confidence'],
                source=row['source'] or "",
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                verified=bool(row['verified']),
                references=json.loads(row['references']) if row['references'] else [],
            )
            for row in rows
        ]

    def get_reliable_knowledge(self, min_confidence: float = 0.7,
                               verified_only: bool = True) -> List[Knowledge]:
        """获取可靠知识

        Args:
            min_confidence: 最小置信度
            verified_only: 是否只获取已验证的

        Returns:
            知识列表
        """
        if verified_only:
            rows = self.fetch_all(
                """SELECT * FROM knowledge
                WHERE confidence >= ? AND verified = 1
                ORDER BY confidence DESC""",
                (min_confidence,)
            )
        else:
            rows = self.fetch_all(
                """SELECT * FROM knowledge
                WHERE confidence >= ?
                ORDER BY confidence DESC""",
                (min_confidence,)
            )

        return [
            Knowledge(
                id=row['id'],
                topic=row['topic'],
                content=row['content'],
                confidence=row['confidence'],
                source=row['source'] or "",
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                verified=bool(row['verified']),
                references=json.loads(row['references']) if row['references'] else [],
            )
            for row in rows
        ]

    # === 进化总结操作 ===

    def save_summary(self, period: str, date: str, summary: str,
                    insights: List[str] = None,
                    patterns_learned: int = 0,
                    methods_learned: int = 0,
                    conversations_processed: int = 0) -> int:
        """保存进化总结

        Args:
            period: 周期（daily/weekly）
            date: 日期
            summary: 总结内容
            insights: 洞察列表
            patterns_learned: 学习的模式数
            methods_learned: 学习的方法数
            conversations_processed: 处理的对话数

        Returns:
            总结ID
        """
        try:
            cursor = self.execute(
                """INSERT OR REPLACE INTO evolution_summaries
                (period, date, summary, insights, patterns_learned, methods_learned, conversations_processed)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    period,
                    date,
                    summary,
                    json.dumps(insights) if insights else None,
                    patterns_learned,
                    methods_learned,
                    conversations_processed,
                )
            )
            self.logger.evolution_summary(period, summary)
            return cursor.lastrowid

        except sqlite3.Error as e:
            self.logger.error(f"保存进化总结失败: {e}")
            raise EvolutionError(f"保存进化总结失败: {e}")

    def get_summary(self, period: str, date: str) -> Optional[EvolutionSummary]:
        """获取进化总结

        Args:
            period: 周期
            date: 日期

        Returns:
            总结对象或None
        """
        row = self.fetch_one(
            """SELECT * FROM evolution_summaries
            WHERE period = ? AND date = ?""",
            (period, date)
        )

        if row:
            return EvolutionSummary(
                id=row['id'],
                period=row['period'],
                date=row['date'],
                summary=row['summary'],
                insights=json.loads(row['insights']) if row['insights'] else [],
                patterns_learned=row['patterns_learned'],
                methods_learned=row['methods_learned'],
                conversations_processed=row['conversations_processed'],
                created_at=row['created_at'],
            )
        return None

    # === 统计 ===

    def get_stats(self) -> Dict[str, Any]:
        """获取进化统计

        Returns:
            统计信息字典
        """
        pattern_count = self.fetch_one("SELECT COUNT(*) as count FROM patterns")['count']
        method_count = self.fetch_one("SELECT COUNT(*) as count FROM methods")['count']
        knowledge_count = self.fetch_one("SELECT COUNT(*) as count FROM knowledge")['count']
        summary_count = self.fetch_one("SELECT COUNT(*) as count FROM evolution_summaries")['count']

        return {
            'patterns': pattern_count,
            'methods': method_count,
            'knowledge': knowledge_count,
            'summaries': summary_count,
        }
