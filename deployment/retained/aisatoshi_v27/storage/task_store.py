"""
AIsatoshi V27 - 任务存储

存储和检索任务信息。

V27核心特性：任务持久化，确保重启后任务自动恢复。
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from .database import Database
from models.task import Task, TaskStatus, TaskExecution
from core.exceptions import TaskStoreError
from core.logger import Logger


class TaskStore(Database):
    """任务存储

    负责管理所有任务的持久化。
    """

    def __init__(self, db_path: str, logger: Optional[Logger] = None):
        """初始化任务存储

        Args:
            db_path: 数据库文件路径
            logger: 日志记录器
        """
        super().__init__(db_path, logger)
        self._init_tables()

    def _init_tables(self):
        """初始化数据库表"""
        # 任务表
        if not self.table_exists("tasks"):
            self.execute("""
                CREATE TABLE tasks (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL CHECK(status IN
                        ('pending', 'running', 'completed', 'failed', 'stopped', 'cancelled')),
                    priority INTEGER DEFAULT 2,
                    params TEXT,
                    interval INTEGER DEFAULT 3600,
                    next_run DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME,
                    result TEXT,
                    error TEXT,
                    execution_count INTEGER DEFAULT 0,
                    last_execution DATETIME
                )
            """)
            self.execute("CREATE INDEX idx_task_status ON tasks(status)")
            self.execute("CREATE INDEX idx_task_next_run ON tasks(next_run)")

        # 任务执行记录表
        if not self.table_exists("task_executions"):
            self.execute("""
                CREATE TABLE task_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME,
                    status TEXT NOT NULL,
                    result TEXT,
                    error TEXT,
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
                )
            """)
            self.execute("CREATE INDEX idx_execution_task ON task_executions(task_id)")

        self.logger.debug("任务数据库表初始化完成")

    # === 任务操作 ===

    def save_task(self, task: Task) -> bool:
        """保存任务

        Args:
            task: 任务对象

        Returns:
            是否成功
        """
        try:
            self.execute(
                """INSERT OR REPLACE INTO tasks
                (id, type, name, description, status, priority, params, interval,
                 next_run, created_at, updated_at, completed_at, result, error,
                 execution_count, last_execution)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    task.id,
                    task.type,
                    task.name,
                    task.description,
                    task.status,
                    task.priority,
                    json.dumps(task.params) if task.params else None,
                    task.interval,
                    task.next_run,
                    task.created_at,
                    task.updated_at,
                    task.completed_at,
                    task.result,
                    task.error,
                    task.execution_count,
                    task.last_execution,
                )
            )
            self.logger.task_created(task.id, task.name)
            return True

        except sqlite3.Error as e:
            self.logger.error(f"保存任务失败: {e}")
            raise TaskStoreError(f"保存任务失败: {e}")

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务

        Args:
            task_id: 任务ID

        Returns:
            任务对象或None
        """
        row = self.fetch_one("SELECT * FROM tasks WHERE id = ?", (task_id,))

        if row:
            return Task(
                id=row['id'],
                type=row['type'],
                name=row['name'],
                description=row['description'] or "",
                status=row['status'],
                priority=row['priority'],
                params=json.loads(row['params']) if row['params'] else {},
                interval=row['interval'],
                next_run=row['next_run'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                completed_at=row['completed_at'],
                result=row['result'],
                error=row['error'],
                execution_count=row['execution_count'],
                last_execution=row['last_execution'],
            )
        return None

    def get_all_tasks(self, status: Optional[str] = None) -> List[Task]:
        """获取所有任务

        Args:
            status: 过滤状态（可选）

        Returns:
            任务列表
        """
        if status:
            rows = self.fetch_all(
                "SELECT * FROM tasks WHERE status = ? ORDER BY priority DESC, created_at ASC",
                (status,)
            )
        else:
            rows = self.fetch_all(
                "SELECT * FROM tasks ORDER BY priority DESC, created_at ASC"
            )

        return [
            Task(
                id=row['id'],
                type=row['type'],
                name=row['name'],
                description=row['description'] or "",
                status=row['status'],
                priority=row['priority'],
                params=json.loads(row['params']) if row['params'] else {},
                interval=row['interval'],
                next_run=row['next_run'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                completed_at=row['completed_at'],
                result=row['result'],
                error=row['error'],
                execution_count=row['execution_count'],
                last_execution=row['last_execution'],
            )
            for row in rows
        ]

    def get_pending_tasks(self) -> List[Task]:
        """获取待执行的任务

        Returns:
            待执行任务列表
        """
        now = datetime.now().isoformat()
        rows = self.fetch_all(
            """SELECT * FROM tasks
            WHERE status = 'pending' AND (next_run IS NULL OR next_run <= ?)
            ORDER BY priority DESC, next_run ASC""",
            (now,)
        )

        return [
            Task(
                id=row['id'],
                type=row['type'],
                name=row['name'],
                description=row['description'] or "",
                status=row['status'],
                priority=row['priority'],
                params=json.loads(row['params']) if row['params'] else {},
                interval=row['interval'],
                next_run=row['next_run'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                completed_at=row['completed_at'],
                result=row['result'],
                error=row['error'],
                execution_count=row['execution_count'],
                last_execution=row['last_execution'],
            )
            for row in rows
        ]

    def update_task_status(self, task_id: str, status: str,
                          result: Optional[str] = None,
                          error: Optional[str] = None) -> bool:
        """更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态
            result: 结果（可选）
            error: 错误信息（可选）

        Returns:
            是否成功
        """
        try:
            updated_at = datetime.now().isoformat()

            if status == TaskStatus.COMPLETED.value:
                completed_at = updated_at
                self.execute(
                    """UPDATE tasks SET status = ?, updated_at = ?,
                    completed_at = ?, result = ?, error = NULL
                    WHERE id = ?""",
                    (status, updated_at, completed_at, result, task_id)
                )
            else:
                self.execute(
                    """UPDATE tasks SET status = ?, updated_at = ?,
                    result = ?, error = ? WHERE id = ?""",
                    (status, updated_at, result, error, task_id)
                )

            return True

        except sqlite3.Error as e:
            self.logger.error(f"更新任务状态失败: {e}")
            raise TaskStoreError(f"更新任务状态失败: {e}")

    def update_task_next_run(self, task_id: str, next_run: str) -> bool:
        """更新任务下次执行时间

        Args:
            task_id: 任务ID
            next_run: 下次执行时间

        Returns:
            是否成功
        """
        try:
            self.execute(
                "UPDATE tasks SET next_run = ? WHERE id = ?",
                (next_run, task_id)
            )
            return True

        except sqlite3.Error as e:
            self.logger.error(f"更新任务时间失败: {e}")
            raise TaskStoreError(f"更新任务时间失败: {e}")

    def delete_task(self, task_id: str) -> bool:
        """删除任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功
        """
        try:
            self.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            self.execute("DELETE FROM task_executions WHERE task_id = ?", (task_id,))
            self.logger.info(f"任务已删除: {task_id}")
            return True

        except sqlite3.Error as e:
            self.logger.error(f"删除任务失败: {e}")
            raise TaskStoreError(f"删除任务失败: {e}")

    def get_task_count(self, status: Optional[str] = None) -> int:
        """获取任务数量

        Args:
            status: 过滤状态（可选）

        Returns:
            任务数量
        """
        if status:
            result = self.fetch_one(
                "SELECT COUNT(*) as count FROM tasks WHERE status = ?",
                (status,)
            )
        else:
            result = self.fetch_one("SELECT COUNT(*) as count FROM tasks")

        return result['count'] if result else 0

    def get_stats(self) -> Dict[str, int]:
        """获取任务统计

        Returns:
            统计信息字典
        """
        stats = {}
        for status in ['pending', 'running', 'completed', 'failed', 'stopped']:
            result = self.fetch_one(
                "SELECT COUNT(*) as count FROM tasks WHERE status = ?",
                (status,)
            )
            stats[status] = result['count'] if result else 0
        return stats

    # === 任务执行记录 ===

    def start_execution(self, task_id: str) -> int:
        """开始任务执行

        Args:
            task_id: 任务ID

        Returns:
            执行记录ID
        """
        try:
            cursor = self.execute(
                "INSERT INTO task_executions (task_id, started_at, status) VALUES (?, ?, ?)",
                (task_id, datetime.now().isoformat(), 'running')
            )
            return cursor.lastrowid

        except sqlite3.Error as e:
            raise TaskStoreError(f"创建执行记录失败: {e}")

    def complete_execution(self, execution_id: int, status: str,
                          result: Optional[str] = None,
                          error: Optional[str] = None) -> bool:
        """完成任务执行

        Args:
            execution_id: 执行记录ID
            status: 状态
            result: 结果（可选）
            error: 错误（可选）

        Returns:
            是否成功
        """
        try:
            self.execute(
                """UPDATE task_executions
                SET completed_at = ?, status = ?, result = ?, error = ?
                WHERE id = ?""",
                (datetime.now().isoformat(), status, result, error, execution_id)
            )
            return True

        except sqlite3.Error as e:
            raise TaskStoreError(f"更新执行记录失败: {e}")

    def get_executions(self, task_id: str, limit: int = 10) -> List[TaskExecution]:
        """获取任务执行记录

        Args:
            task_id: 任务ID
            limit: 最大数量

        Returns:
            执行记录列表
        """
        rows = self.fetch_all(
            """SELECT * FROM task_executions
            WHERE task_id = ?
            ORDER BY started_at DESC LIMIT ?""",
            (task_id, limit)
        )

        return [
            TaskExecution(
                id=row['id'],
                task_id=row['task_id'],
                started_at=row['started_at'],
                completed_at=row['completed_at'],
                status=row['status'],
                result=row['result'],
                error=row['error'],
            )
            for row in rows
        ]
