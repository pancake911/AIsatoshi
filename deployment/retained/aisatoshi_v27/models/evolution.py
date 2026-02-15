"""
AIsatoshi V27 - 进化模型

定义进化系统相关的数据结构。

V27核心特性：进化原生 - AIsatoshi能够自我学习和进化。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime


@dataclass
class Pattern:
    """模式

    AIsatoshi从对话中学习到的模式。
    """
    id: int
    pattern: str                       # 模式描述
    frequency: int = 1                 # 出现频率
    last_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence: float = 0.5            # 置信度
    category: str = ""                 # 类别：user_behavior, query_pattern, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_common(self) -> bool:
        """是否是常见模式"""
        return self.frequency >= 3

    def increment(self):
        """增加频率计数"""
        self.frequency += 1
        self.last_seen = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'pattern': self.pattern,
            'frequency': self.frequency,
            'last_seen': self.last_seen,
            'confidence': self.confidence,
            'category': self.category,
            'metadata': self.metadata,
        }


@dataclass
class Method:
    """方法

    AIsatoshi归纳出的解决问题的方法。
    """
    id: int
    task_type: str                     # 任务类型
    method: str                        # 方法描述
    steps: List[str] = field(default_factory=list)  # 具体步骤
    success_count: int = 0             # 成功次数
    failure_count: int = 0             # 失败次数
    last_used: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def total_uses(self) -> int:
        """总使用次数"""
        return self.success_count + self.failure_count

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_uses == 0:
            return 0.5
        return self.success_count / self.total_uses

    @property
    def is_effective(self) -> bool:
        """是否有效（成功率>70%）"""
        return self.success_rate > 0.7

    def record_success(self):
        """记录成功"""
        self.success_count += 1
        self.last_used = datetime.now().isoformat()

    def record_failure(self):
        """记录失败"""
        self.failure_count += 1
        self.last_used = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'task_type': self.task_type,
            'method': self.method,
            'steps': self.steps,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'last_used': self.last_used,
            'created_at': self.created_at,
        }


@dataclass
class Knowledge:
    """知识

    AIsatoshi通过学习和推理获得的知识。
    """
    id: int
    topic: str                         # 主题
    content: str                       # 内容
    confidence: float = 0.5            # 置信度（0-1）
    source: str = ""                   # 来源：conversation, learning, inference
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    verified: bool = False             # 是否已验证
    references: List[int] = field(default_factory=list)  # 引用的记忆ID

    @property
    def is_reliable(self) -> bool:
        """是否可靠（置信度>0.7且已验证）"""
        return self.confidence > 0.7 and self.verified

    def update_confidence(self, delta: float):
        """更新置信度"""
        self.confidence = max(0, min(1, self.confidence + delta))
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'topic': self.topic,
            'content': self.content,
            'confidence': self.confidence,
            'source': self.source,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'verified': self.verified,
            'references': self.references,
        }


@dataclass
class EvolutionSummary:
    """进化总结

    AIsatoshi的定期进化总结。
    """
    id: int
    period: str                        # 周期：daily, weekly
    date: str                          # 日期
    summary: str                       # 总结内容
    insights: List[str] = field(default_factory=list)  # 洞察
    patterns_learned: int = 0          # 学习到的模式数
    methods_learned: int = 0           # 学习到的方法数
    conversations_processed: int = 0   # 处理的对话数
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def is_daily(self) -> bool:
        """是否是每日总结"""
        return self.period == "daily"

    @property
    def is_weekly(self) -> bool:
        """是否是每周总结"""
        return self.period == "weekly"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'period': self.period,
            'date': self.date,
            'summary': self.summary,
            'insights': self.insights,
            'patterns_learned': self.patterns_learned,
            'methods_learned': self.methods_learned,
            'conversations_processed': self.conversations_processed,
            'created_at': self.created_at,
        }


@dataclass
class LearningRecord:
    """学习记录

    记录每次学习的详细信息。
    """
    id: int
    learning_type: str                # 学习类型：pattern, method, knowledge
    content: str                      # 学习内容
    source_conversation_id: Optional[int] = None  # 来源对话
    confidence: float = 0.5
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'learning_type': self.learning_type,
            'content': self.content,
            'source_conversation_id': self.source_conversation_id,
            'confidence': self.confidence,
            'created_at': self.created_at,
        }
