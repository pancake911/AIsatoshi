"""
AIsatoshi V27 - 常量定义

定义系统使用的所有常量。
"""

# 版本信息
VERSION = "v27"
VERSION_FULL = "27.0.0"

# 目录路径
DEFAULT_LOG_LEVEL = "INFO"
DATA_DIR = "/app/data"
WORKSPACE_DIR = "/app/workspace"
KNOWLEDGE_DIR = "/app/data/knowledge"

# 数据库文件路径
CONVERSATIONS_DB = "/app/data/conversations.db"
TASKS_DB = "/app/data/tasks.db"
MEMORY_DB = "/app/data/memory.db"
EVOLUTION_DB = "/app/data/evolution.db"

# === 任务相关常量 ===

# 任务类型
class TaskType:
    """任务类型枚举"""
    MOLTBOOK_POST = "moltbook_post"    # Moltbook发帖
    MONITOR = "monitor"                # 监控任务
    BLOCKCHAIN = "blockchain"          # 区块链操作
    CODE = "code"                      # 代码执行
    ANALYSIS = "analysis"              # 数据分析
    GENERAL = "general"                # 通用任务

# 任务状态
class TaskStatus:
    """任务状态枚举"""
    PENDING = "pending"                # 待执行
    RUNNING = "running"                # 执行中
    COMPLETED = "completed"            # 已完成
    FAILED = "failed"                  # 失败
    STOPPED = "stopped"                # 已停止
    CANCELLED = "cancelled"            # 已取消

# 任务优先级
class TaskPriority:
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

# === 记忆相关常量 ===

# 记忆类型
class MemoryType:
    """记忆类型枚举"""
    FACT = "fact"                      # 事实记忆
    EVENT = "event"                    # 事件记忆
    PREFERENCE = "preference"          # 偏好记忆
    SKILL = "skill"                    # 技能记忆
    EXPERIENCE = "experience"          # 经验记忆

# 记忆重要性
class MemoryImportance:
    """记忆重要性枚举"""
    TRIVIAL = 1
    LOW = 2
    NORMAL = 3
    IMPORTANT = 4
    CRITICAL = 5

# === 进化相关常量 ===

# 学习阶段
class LearningPhase:
    """学习阶段枚举"""
    PATTERN_EXTRACTION = "pattern_extraction"     # 模式提取
    METHOD_INDUCTION = "method_induction"         # 方法归纳
    KNOWLEDGE_INTEGRATION = "knowledge_integration" # 知识整合
    SUMMARY_GENERATION = "summary_generation"     # 总结生成

# === Telegram相关常量 ===

# 消息类型
class MessageType:
    """消息类型枚举"""
    TEXT = "text"
    COMMAND = "command"
    URL = "url"

# === AI相关常量 ===

# AI模型
class AIModel:
    """AI模型枚举"""
    GEMINI_FLASH = "gemini-2.0-flash-exp"
    GEMINI_PRO = "gemini-3-pro-preview"

# AI动作类型
class AIAction:
    """AI动作类型枚举"""
    CHAT = "chat"
    PRICE = "price"
    BALANCE = "balance"
    STATUS = "status"
    TRANSFER = "transfer"
    DEPLOY_ERC20 = "deploy_erc20"
    APPROVE = "approve"
    ADD_TASK = "add_task"
    STOP_TASK = "stop_task"
    DELETE_TASK = "delete_task"
    LIST_TASKS = "list_tasks"
    BROWSE = "browse"
    SHELL = "shell"
    WRITE_FILE = "write_file"
    CREATE_PROJECT = "create_project"
    RUN_PROJECT = "run_project"

# === 网页抓取相关常量 ===

# 抓取方法
class ScrapeMethod:
    """抓取方法枚举"""
    API = "api"                         # API优先
    BEAUTIFUL_SOUP = "beautiful_soup"   # HTML解析
    PLAYWRIGHT = "playwright"           # 浏览器渲染

# === 区块链相关常量 ===

# RPC节点（默认列表）
DEFAULT_RPC_ENDPOINTS = [
    "https://eth.llamarpc.com",
    "https://rpc.ankr.com/eth",
    "https://ethereum.publicnode.com",
    "https://1rpc.io/eth",
]

# AISAT代币合约地址
AISAT_CONTRACT_ADDRESS = "0xf50e5d3d7c7E36dE873D56610bBB94d341147FBE"

# === 系统相关常量 ===

# 时间间隔（秒）
CHECK_INTERVAL_SHORT = 30              # 短间隔检查
CHECK_INTERVAL_NORMAL = 60            # 正常间隔检查
CHECK_INTERVAL_LONG = 300             # 长间隔检查

# 超时时间（秒）
TIMEOUT_SHORT = 10
TIMEOUT_NORMAL = 30
TIMEOUT_LONG = 60
TIMEOUT_VERY_LONG = 180

# 限制
MAX_MESSAGE_LENGTH = 4096              # Telegram消息最大长度
MAX_CONTEXT_LENGTH = 10000             # AI上下文最大长度
MAX_RECENT_MESSAGES = 50               # 最近消息最大数量
MAX_SEARCH_RESULTS = 20                # 搜索结果最大数量

# === 错误消息 ===

ERROR_MESSAGES = {
    "no_api_key": "API密钥未配置",
    "invalid_request": "请求无效",
    "timeout": "请求超时",
    "rate_limit": "API速率限制",
    "network_error": "网络连接失败",
    "parse_error": "响应解析失败",
}
