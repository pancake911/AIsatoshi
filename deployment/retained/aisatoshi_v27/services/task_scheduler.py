"""
AIsatoshi V27 - 任务调度器

V27核心功能：原生任务继承系统

负责：
- 任务调度和执行
- 任务状态管理
- 任务持久化
- 启动时自动恢复任务
"""

import threading
import time
import uuid
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from storage.task_store import TaskStore
from models.task import Task, TaskStatus, TaskPriority
from core.logger import Logger


class TaskScheduler:
    """任务调度器

    管理所有任务的调度和执行。
    """

    def __init__(
        self,
        task_store: TaskStore,
        logger: Optional[Logger] = None,
        check_interval: int = 60
    ):
        """初始化任务调度器

        Args:
            task_store: 任务存储
            logger: 日志记录器
            check_interval: 检查间隔（秒）
        """
        self.task_store = task_store
        self.logger = logger or Logger(name="TaskScheduler")
        self.check_interval = check_interval

        # 任务执行器
        self.executors: Dict[str, Callable] = {}

        # 状态
        self.running = False
        self.thread: Optional[threading.Thread] = None

        # 正在运行的任务
        self.running_tasks: Dict[str, threading.Thread] = {}

        self.logger.info("任务调度器已初始化")

    def register_executor(self, task_type: str, executor: Callable):
        """注册任务执行器

        Args:
            task_type: 任务类型
            executor: 执行函数
        """
        self.executors[task_type] = executor
        self.logger.debug(f"执行器已注册: {task_type}")

    def start(self):
        """启动任务调度器"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._schedule_loop, daemon=True)
        self.thread.start()
        self.logger.info("任务调度器已启动")

    def stop(self):
        """停止任务调度器"""
        self.running = False

        # 等待正在运行的任务完成
        for task_id, thread in self.running_tasks.items():
            self.logger.info(f"等待任务完成: {task_id}")
            thread.join(timeout=30)

        if self.thread:
            self.thread.join(timeout=5)

        self.logger.info("任务调度器已停止")

    def _schedule_loop(self):
        """调度循环"""
        while self.running:
            try:
                # 获取待执行的任务
                pending_tasks = self.task_store.get_pending_tasks()

                for task in pending_tasks:
                    if not self.running:
                        break

                    # 启动任务
                    self._execute_task(task)

                # 等待下一次检查
                for _ in range(self.check_interval):
                    if not self.running:
                        break
                    time.sleep(1)

            except Exception as e:
                self.logger.error(f"调度循环错误: {e}")
                time.sleep(10)

    def _execute_task(self, task: Task):
        """执行任务

        Args:
            task: 任务对象
        """
        # 检查是否已有执行器
        if task.type not in self.executors:
            self.logger.warning(f"没有执行器: {task.type}")
            return

        # 标记为运行中
        task.mark_running()
        self.task_store.save_task(task)

        # 在新线程中执行
        def run():
            try:
                self.logger.task_started(task.id, task.name)

                # 执行任务
                result = self.executors[task.type](task)

                # 任务完成
                task.mark_completed(result=str(result), reschedule=True)
                self.task_store.save_task(task)
                self.logger.task_completed(task.id, task.name)

            except Exception as e:
                # 任务失败
                task.mark_failed(str(e))
                self.task_store.save_task(task)
                self.logger.task_failed(task.id, task.name, str(e))

            finally:
                # 从运行列表中移除
                self.running_tasks.pop(task.id, None)

        thread = threading.Thread(target=run, daemon=True)
        self.running_tasks[task.id] = thread
        thread.start()

    # === 任务管理 ===

    def add_task(self, task: Task) -> bool:
        """添加任务

        Args:
            task: 任务对象

        Returns:
            是否成功
        """
        try:
            self.task_store.save_task(task)
            self.logger.info(f"任务已添加: {task.id} - {task.name}")
            return True

        except Exception as e:
            self.logger.error(f"添加任务失败: {e}")
            return False

    def create_task(
        self,
        task_type: str,
        name: str,
        description: str = "",
        params: Dict = None,
        interval: int = 3600,
        priority: int = TaskPriority.NORMAL.value
    ) -> Task:
        """创建任务

        Args:
            task_type: 任务类型
            name: 任务名称
            description: 任务描述
            params: 任务参数
            interval: 执行间隔
            priority: 优先级

        Returns:
            任务对象
        """
        task = Task(
            id=str(uuid.uuid4()),
            type=task_type,
            name=name,
            description=description,
            params=params or {},
            interval=interval,
            priority=priority,
        )

        self.add_task(task)
        return task

    def stop_task(self, task_id: str) -> bool:
        """停止任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功
        """
        task = self.task_store.get_task(task_id)
        if not task:
            self.logger.warning(f"任务不存在: {task_id}")
            return False

        task.mark_stopped()
        self.task_store.save_task(task)
        self.logger.info(f"任务已停止: {task_id}")

        return True

    def delete_task(self, task_id: str) -> bool:
        """删除任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功
        """
        return self.task_store.delete_task(task_id)

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务

        Args:
            task_id: 任务ID

        Returns:
            任务对象或None
        """
        return self.task_store.get_task(task_id)

    def get_all_tasks(self, status: Optional[str] = None) -> List[Task]:
        """获取所有任务

        Args:
            status: 过滤状态（可选）

        Returns:
            任务列表
        """
        return self.task_store.get_all_tasks(status=status)

    # === 统计 ===

    def get_stats(self) -> Dict:
        """获取任务统计

        Returns:
            统计信息字典
        """
        return self.task_store.get_stats()

    def get_running_count(self) -> int:
        """获取正在运行的任务数

        Returns:
            运行中的任务数
        """
        return len(self.running_tasks)
