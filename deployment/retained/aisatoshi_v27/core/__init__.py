"""
AIsatoshi V27 - 核心模块

这是AIsatoshi的核心基础层，提供配置、日志、异常等基础功能。

V27 = 记忆原生 + 进化原生 + 任务继承原生
"""

from .config import Config
from .logger import Logger
from .exceptions import (
    AIsatoshiException,
    ConfigurationError,
    StorageError,
    ServiceError,
    TaskError
)
from .constants import (
    VERSION,
    DEFAULT_LOG_LEVEL,
    DATA_DIR,
    WORKSPACE_DIR
)

__all__ = [
    'Config',
    'Logger',
    'AIsatoshiException',
    'ConfigurationError',
    'StorageError',
    'ServiceError',
    'TaskError',
    'VERSION',
    'DEFAULT_LOG_LEVEL',
    'DATA_DIR',
    'WORKSPACE_DIR',
]
