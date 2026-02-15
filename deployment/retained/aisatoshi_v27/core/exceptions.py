"""
AIsatoshi V27 - 异常定义

定义所有自定义异常类，提供清晰的错误分类。
"""

from typing import Optional, Any


class AIsatoshiException(Exception):
    """AIsatoshi基础异常类

    所有AIsatoshi相关异常的基类。
    """

    def __init__(self, message: str, details: Optional[Any] = None):
        self.message = message
        self.details = details
        super().__init__(self.format_message())

    def format_message(self) -> str:
        """格式化错误消息"""
        if self.details:
            return f"{self.message} | 详情: {self.details}"
        return self.message

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": str(self.details) if self.details else None
        }


# === 配置相关异常 ===

class ConfigurationError(AIsatoshiException):
    """配置错误

    当配置缺失或无效时抛出。
    """
    pass


class EnvironmentVariableError(ConfigurationError):
    """环境变量错误

    当必需的环境变量未设置时抛出。
    """
    pass


# === 存储相关异常 ===

class StorageError(AIsatoshiException):
    """存储错误

    当数据存储操作失败时抛出。
    """
    pass


class DatabaseError(StorageError):
    """数据库错误

    当数据库操作失败时抛出。
    """
    pass


class MemoryStoreError(StorageError):
    """记忆存储错误

    当记忆存储操作失败时抛出。
    """
    pass


class TaskStoreError(StorageError):
    """任务存储错误

    当任务存储操作失败时抛出。
    """
    pass


# === 服务相关异常 ===

class ServiceError(AIsatoshiException):
    """服务错误

    当服务操作失败时抛出。
    """
    pass


class AIServiceError(ServiceError):
    """AI服务错误

    当AI服务调用失败时抛出。
    """
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Any] = None):
        self.status_code = status_code
        super().__init__(message, details)


class TelegramServiceError(ServiceError):
    """Telegram服务错误

    当Telegram服务调用失败时抛出。
    """
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Any] = None):
        self.status_code = status_code
        super().__init__(message, details)


class BlockchainServiceError(ServiceError):
    """区块链服务错误

    当区块链操作失败时抛出。
    """
    pass


class WebScrapingError(ServiceError):
    """网页抓取错误

    当网页抓取失败时抛出。
    """
    pass


class MoltbookServiceError(ServiceError):
    """Moltbook服务错误

    当Moltbook操作失败时抛出。
    """
    pass


# === 任务相关异常 ===

class TaskError(AIsatoshiException):
    """任务错误

    当任务操作失败时抛出。
    """
    pass


class TaskNotFoundError(TaskError):
    """任务未找到错误

    当尝试访问不存在的任务时抛出。
    """
    pass


class TaskExecutionError(TaskError):
    """任务执行错误

    当任务执行失败时抛出。
    """
    pass


class TaskValidationError(TaskError):
    """任务验证错误

    当任务参数无效时抛出。
    """
    pass


# === 记忆相关异常 ===

class MemoryError(AIsatoshiException):
    """记忆错误

    当记忆操作失败时抛出。
    """
    pass


class MemoryNotFoundError(MemoryError):
    """记忆未找到错误

    当搜索的记忆不存在时抛出。
    """
    pass


# === 进化相关异常 ===

class EvolutionError(AIsatoshiException):
    """进化错误

    当进化系统操作失败时抛出。
    """
    pass


class LearningError(EvolutionError):
    """学习错误

    当学习过程失败时抛出。
    """
    pass


# === 网络相关异常 ===

class NetworkError(AIsatoshiException):
    """网络错误

    当网络请求失败时抛出。
    """
    pass


class TimeoutError(NetworkError):
    """超时错误

    当请求超时时抛出。
    """
    pass


# === 验证相关异常 ===

class ValidationError(AIsatoshiException):
    """验证错误

    当数据验证失败时抛出。
    """
    pass
