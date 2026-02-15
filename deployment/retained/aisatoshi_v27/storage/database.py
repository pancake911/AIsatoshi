"""
AIsatoshi V27 - 数据库基类

提供数据库初始化和基础操作。
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
from core.exceptions import DatabaseError
from core.logger import Logger


class Database:
    """数据库基类

    提供SQLite数据库的基础操作。
    """

    def __init__(self, db_path: str, logger: Optional[Logger] = None):
        """初始化数据库

        Args:
            db_path: 数据库文件路径
            logger: 日志记录器
        """
        self.db_path = db_path
        self.logger = logger or Logger(name=f"Database-{os.path.basename(db_path)}")
        self._ensure_directory()

    def _ensure_directory(self):
        """确保数据库目录存在"""
        directory = os.path.dirname(self.db_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 返回字典式行
            conn.execute("PRAGMA foreign_keys = ON")  # 启用外键约束
            conn.execute("PRAGMA journal_mode = WAL")  # WAL模式，提高并发性能
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise DatabaseError(f"数据库操作失败: {e}")
        finally:
            if conn:
                conn.close()

    def execute(self, sql: str, params: Tuple = ()) -> sqlite3.Cursor:
        """执行SQL语句

        Args:
            sql: SQL语句
            params: 参数

        Returns:
            游标对象
        """
        with self.get_connection() as conn:
            return conn.execute(sql, params)

    def execute_many(self, sql: str, params_list: List[Tuple]) -> sqlite3.Cursor:
        """批量执行SQL语句

        Args:
            sql: SQL语句
            params_list: 参数列表

        Returns:
            游标对象
        """
        with self.get_connection() as conn:
            return conn.executemany(sql, params_list)

    def fetch_one(self, sql: str, params: Tuple = ()) -> Optional[Dict]:
        """获取单行结果

        Args:
            sql: SQL语句
            params: 参数

        Returns:
            行字典或None
        """
        with self.get_connection() as conn:
            row = conn.execute(sql, params).fetchone()
            return dict(row) if row else None

    def fetch_all(self, sql: str, params: Tuple = ()) -> List[Dict]:
        """获取所有结果

        Args:
            sql: SQL语句
            params: 参数

        Returns:
            行字典列表
        """
        with self.get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]

    def table_exists(self, table_name: str) -> bool:
        """检查表是否存在

        Args:
            table_name: 表名

        Returns:
            是否存在
        """
        result = self.fetch_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return result is not None

    def create_table(self, sql: str):
        """创建表

        Args:
            sql: CREATE TABLE SQL语句
        """
        try:
            self.execute(sql)
            self.logger.debug(f"表创建成功")
        except DatabaseError as e:
            self.logger.error(f"表创建失败: {e}")
            raise


# 数据库初始化脚本
def init_all_databases(data_dir: str = "/app/data", logger: Optional[Logger] = None) -> Dict[str, Database]:
    """初始化所有数据库

    Args:
        data_dir: 数据目录
        logger: 日志记录器

    Returns:
        数据库字典
    """
    if logger:
        logger.info("初始化AIsatoshi V27数据库...")

    # 确保目录存在
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(os.path.join(data_dir, "knowledge"), exist_ok=True)

    databases = {}

    # 初始化各个数据库
    try:
        from .conversation_store import ConversationStore
        from .task_store import TaskStore
        from .memory_store import MemoryStore
        from .evolution_store import EvolutionStore

        # 创建各个存储实例（会自动初始化表）
        databases['conversations'] = ConversationStore(
            os.path.join(data_dir, "conversations.db"), logger
        )
        databases['tasks'] = TaskStore(
            os.path.join(data_dir, "tasks.db"), logger
        )
        databases['memory'] = MemoryStore(
            os.path.join(data_dir, "memory.db"), logger
        )
        databases['evolution'] = EvolutionStore(
            os.path.join(data_dir, "evolution.db"), logger
        )

        if logger:
            logger.info("✅ 所有数据库初始化完成")

    except Exception as e:
        if logger:
            logger.error(f"❌ 数据库初始化失败: {e}")
        raise DatabaseError(f"数据库初始化失败: {e}")

    return databases
