"""
AIsatoshi V27 - 任务模型

定义任务相关的数据结构。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class TaskType(Enum):
    """任务类型枚举"""
    MOLTBOOK_POST = "moltbook_post"
    MONITOR = "monitor"
    BLOCKCHAIN = "blockchain"
    CODE = "code"
    ANALYSIS = "analysis"
    GENERAL = "general"


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Task:
    """任务

    表示AIsatoshi需要执行的任务。
    """
    id: str
    type: str
    name: str
    description: str = ""
    status: str = TaskStatus.PENDING.value
    priority: int = TaskPriority.NORMAL.value
    params: Dict[str, Any] = field(default_factory=dict)
    interval: int = 3600  # 执行间隔（秒）
    next_run: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    execution_count: int = 0
    last_execution: Optional[str] = None

    def __post_init__(self):
        """初始化后处理"""
        if not self.next_run and self.interval:
            # 设置初始next_run时间
            dt = datetime.now()
            from core.utils import format_iso_timestamp
            self.next_run = format_iso_timestamp(dt)

    @property
    def is_pending(self) -> bool:
        """是否待执行"""
        return self.status == TaskStatus.PENDING.value

    @property
    def is_running(self) -> bool:
        """是否正在执行"""
        return self.status == TaskStatus.RUNNING.value

    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.status == TaskStatus.COMPLETED.value

    @property
    def is_failed(self) -> bool:
        """是否失败"""
        return self.status == TaskStatus.FAILED.value

    @property
    def is_stopped(self) -> bool:
        """是否已停止"""
        return self.status == TaskStatus.STOPPED.value

    def should_run(self) -> bool:
        """检查任务是否应该执行"""
        if not self.is_pending:
            return False

        if not self.next_run:
            return True

        try:
            next_run_dt = datetime.fromisoformat(self.next_run)
            return datetime.now() >= next_run_dt
        except:
            return True

    def mark_running(self):
        """标记为运行中"""
        self.status = TaskStatus.RUNNING.value
        self.updated_at = datetime.now().isoformat()

    def mark_completed(self, result: str = "", reschedule: bool = False):
        """标记为完成"""
        self.status = TaskStatus.COMPLETED.value
        self.completed_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.result = result
        self.execution_count += 1
        self.last_execution = self.completed_at

        if reschedule and self.interval:
            # 计算下次执行时间
            from core.utils import format_iso_timestamp
            next_dt = datetime.now()
            from datetime import timedelta
            next_dt = next_dt + timedelta(seconds=self.interval)
            self.next_run = format_iso_timestamp(next_dt)
            self.status = TaskStatus.PENDING.value

    def mark_failed(self, error: str):
        """标记为失败"""
        self.status = TaskStatus.FAILED.value
        self.error = error
        self.updated_at = datetime.now().isoformat()

    def mark_stopped(self):
        """标记为已停止"""
        self.status = TaskStatus.STOPPED.value
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'type': self.type,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'params': self.params,
            'interval': self.interval,
            'next_run': self.next_run,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'completed_at': self.completed_at,
            'result': self.result,
            'error': self.error,
            'execution_count': self.execution_count,
            'last_execution': self.last_execution,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """从字典创建"""
        return cls(
            id=data['id'],
            type=data['type'],
            name=data['name'],
            description=data.get('description', ''),
            status=data.get('status', TaskStatus.PENDING.value),
            priority=data.get('priority', TaskPriority.NORMAL.value),
            params=data.get('params', {}),
            interval=data.get('interval', 3600),
            next_run=data.get('next_run'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            completed_at=data.get('completed_at'),
            result=data.get('result'),
            error=data.get('error'),
            execution_count=data.get('execution_count', 0),
            last_execution=data.get('last_execution'),
        )


@dataclass
class TaskExecution:
    """任务执行记录"""
    id: int
    task_id: str
    started_at: str
    completed_at: Optional[str] = None
    status: str = TaskStatus.PENDING.value
    result: Optional[str] = None
    error: Optional[str] = None

    @property
    def duration(self) -> Optional[float]:
        """获取执行时长（秒）"""
        if not self.completed_at:
            return None
        try:
            start = datetime.fromisoformat(self.started_at)
            end = datetime.fromisoformat(self.completed_at)
            return (end - start).total_seconds()
        except:
            return None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'status': self.status,
            'result': self.result,
            'error': self.error,
        }
