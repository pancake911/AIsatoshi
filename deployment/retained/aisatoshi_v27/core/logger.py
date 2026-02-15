"""
AIsatoshi V27 - 日志系统

提供统一的日志记录功能，支持不同级别和格式化输出。
"""

import logging
import sys
from datetime import datetime
from typing import Optional
from pathlib import Path


class Logger:
    """AIsatoshi日志系统

    提供结构化的日志输出，支持控制台和文件输出。
    """

    # 日志级别映射
    LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }

    def __init__(
        self,
        name: str = "AIsatoshi",
        level: str = "INFO",
        log_file: Optional[str] = None,
        data_dir: str = "/app/data"
    ):
        """初始化日志系统

        Args:
            name: 日志器名称
            level: 日志级别
            log_file: 日志文件路径（可选）
            data_dir: 数据目录，用于默认日志文件
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.LEVELS.get(level.upper(), logging.INFO))

        # 清除现有处理器
        self.logger.handlers.clear()

        # 创建格式化器
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 添加控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # 添加文件处理器（如果指定）
        if log_file:
            log_path = Path(log_file)
        else:
            log_path = Path(data_dir) / "aisatoshi.log"

        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        except Exception as e:
            self.logger.warning(f"无法创建日志文件 {log_path}: {e}")

        self.debug(f"日志系统初始化完成: {name} ({level})")

    def debug(self, message: str, **kwargs):
        """记录DEBUG级别日志"""
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """记录INFO级别日志"""
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """记录WARNING级别日志"""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """记录ERROR级别日志"""
        self.logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs):
        """记录CRITICAL级别日志"""
        self.logger.critical(message, **kwargs)

    def exception(self, message: str, **kwargs):
        """记录异常信息"""
        self.logger.exception(message, **kwargs)

    # 特殊方法用于AI相关日志
    def ai_request(self, prompt: str, max_length: int = 100):
        """记录AI请求"""
        truncated = prompt[:max_length] + "..." if len(prompt) > max_length else prompt
        self.info(f"[AI请求] {truncated}")

    def ai_response(self, response: str, max_length: int = 100):
        """记录AI响应"""
        truncated = response[:max_length] + "..." if len(response) > max_length else response
        self.info(f"[AI响应] {truncated}")

    def ai_error(self, error: str):
        """记录AI错误"""
        self.error(f"[AI错误] {error}")

    # 任务相关日志
    def task_created(self, task_id: str, task_name: str):
        """记录任务创建"""
        self.info(f"[任务创建] ID={task_id} 名称={task_name}")

    def task_started(self, task_id: str, task_name: str):
        """记录任务开始"""
        self.info(f"[任务开始] ID={task_id} 名称={task_name}")

    def task_completed(self, task_id: str, task_name: str, result: str = ""):
        """记录任务完成"""
        self.info(f"[任务完成] ID={task_id} 名称={task_name} 结果={result[:50]}...")

    def task_failed(self, task_id: str, task_name: str, error: str):
        """记录任务失败"""
        self.error(f"[任务失败] ID={task_id} 名称={task_name} 错误={error}")

    # 记忆相关日志
    def memory_saved(self, memory_type: str, count: int = 1):
        """记录记忆保存"""
        self.debug(f"[记忆保存] 类型={memory_type} 数量={count}")

    def memory_loaded(self, count: int):
        """记录记忆加载"""
        self.info(f"[记忆加载] 数量={count}")

    def memory_searched(self, query: str, results: int):
        """记录记忆搜索"""
        self.debug(f"[记忆搜索] 查询={query[:50]}... 结果数={results}")

    # 进化相关日志
    def evolution_learning(self, patterns: int = 0, methods: int = 0):
        """记录进化学习"""
        self.info(f"[进化学习] 模式={patterns} 方法={methods}")

    def evolution_summary(self, period: str, summary: str):
        """记录进化总结"""
        self.info(f"[进化总结] 周期={period} 摘要={summary[:100]}...")

    # Telegram相关日志
    def telegram_message(self, direction: str, content: str, max_length: int = 100):
        """记录Telegram消息"""
        truncated = content[:max_length] + "..." if len(content) > max_length else content
        self.info(f"[Telegram.{direction}] {truncated}")

    def telegram_error(self, error: str):
        """记录Telegram错误"""
        self.error(f"[Telegram错误] {error}")

    # 区块链相关日志
    def blockchain_transaction(self, tx_hash: str, details: str = ""):
        """记录区块链交易"""
        self.info(f"[区块链交易] hash={tx_hash} {details}")

    def blockchain_error(self, error: str):
        """记录区块链错误"""
        self.error(f"[区块链错误] {error}")

    # 启动横幅
    def banner(self):
        """打印启动横幅"""
        banner = f"""
{'=' * 60}
🤖 AIsatoshi V27 - 记忆原生 + 进化原生 + 任务继承原生
{'=' * 60}
启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'=' * 60}
        """
        self.info(banner)

    # 分隔线
    def separator(self, title: str = ""):
        """打印分隔线"""
        if title:
            self.info(f"--- {title} ---")
        else:
            self.info("-" * 40)


def get_logger(name: str = "AIsatoshi", level: str = "INFO", **kwargs) -> Logger:
    """获取日志器实例的便捷方法"""
    return Logger(name=name, level=level, **kwargs)
