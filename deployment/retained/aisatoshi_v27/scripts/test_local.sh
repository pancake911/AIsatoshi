#!/bin/bash
# AIsatoshi V27 - 本地测试脚本
#
# 在部署前测试核心功能

set -e

echo "========================================="
echo "AIsatoshi V27 本地功能测试"
echo "========================================="

# 设置测试环境变量
export AI_PRIVATE_KEY="0x0000000000000000000000000000000000000000000000000000000000000001"
export GEMINI_API_KEY="test_key_for_local_testing"
export TELEGRAM_BOT_TOKEN="test_token_for_local_testing"
export MOLTBOOK_API_KEY="test_key"
export LOG_LEVEL="DEBUG"

# 创建临时数据目录
TEST_DATA_DIR="/tmp/aisatoshi_test_$(date +%s)"
mkdir -p ${TEST_DATA_DIR}
export DATA_DIR="${TEST_DATA_DIR}"

echo "测试数据目录: ${TEST_DATA_DIR}"
echo ""

# 运行Python测试
python3 << 'EOF'
import sys
import os
sys.path.insert(0, '.')

print("【测试1】核心模块导入...")
try:
    from core.config import Config
    from core.logger import Logger
    from core.exceptions import AIsatoshiException
    print("✅ 核心模块导入成功")
except Exception as e:
    print(f"❌ 核心模块导入失败: {e}")
    sys.exit(1)

print("\n【测试2】数据模型导入...")
try:
    from models.message import TelegramMessage, AIResponse
    from models.task import Task, TaskStatus
    from models.memory import Memory, MemoryType
    from models.evolution import Pattern, Method
    print("✅ 数据模型导入成功")
except Exception as e:
    print(f"❌ 数据模型导入失败: {e}")
    sys.exit(1)

print("\n【测试3】存储层测试...")
try:
    from storage.database import Database
    from storage.memory_store import MemoryStore
    from storage.task_store import TaskStore
    from storage.conversation_store import ConversationStore
    from storage.evolution_store import EvolutionStore

    # 创建测试数据库
    db_path = os.path.join(os.environ['DATA_DIR'], 'test.db')
    db = Database(db_path)
    print("✅ 存储层导入成功")
except Exception as e:
    print(f"❌ 存储层导入失败: {e}")
    sys.exit(1)

print("\n【测试4】服务层测试...")
try:
    from services.memory_manager import MemoryManager
    from services.eolution_engine import EvolutionEngine
    from services.ai_engine import AIEngine
    from services.telegram_service import TelegramService
    from services.task_scheduler import TaskScheduler
    print("✅ 服务层导入成功")
except Exception as e:
    print(f"❌ 服务层导入失败: {e}")
    sys.exit(1)

print("\n【测试5】配置加载测试...")
try:
    # 设置测试环境变量
    os.environ['AI_PRIVATE_KEY'] = '0x' + '1' * 64
    os.environ['GEMINI_API_KEY'] = 'test_key'
    os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'

    config = Config.from_env()
    print(f"✅ 配置加载成功: {config.VERSION}")
except Exception as e:
    print(f"❌ 配置加载失败: {e}")
    sys.exit(1)

print("\n【测试6】数据库操作测试...")
try:
    # 创建内存存储
    memory_db = os.path.join(os.environ['DATA_DIR'], 'memory.db')
    memory_store = MemoryStore(memory_db)

    # 添加测试记忆
    from models.memory import Memory, MemoryType
    memory = Memory(
        id=0,
        type=MemoryType.FACT.value,
        content="测试记忆内容",
        importance=3
    )
    memory_id = memory_store.add_memory(memory)
    print(f"✅ 数据库操作成功，记忆ID: {memory_id}")
except Exception as e:
    print(f"❌ 数据库操作失败: {e}")
    sys.exit(1)

print("\n" + "=" * 50)
print("🎉 所有测试通过！")
print("=" * 50)
EOF

# 清理
echo ""
echo "清理测试数据..."
rm -rf ${TEST_DATA_DIR}

echo "测试完成！"
