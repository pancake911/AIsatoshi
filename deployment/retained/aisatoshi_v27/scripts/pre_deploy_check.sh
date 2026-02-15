#!/bin/bash
# AIsatoshi V27 - 预部署检查脚本
#
# 这是V27的关键功能：在部署前进行完整检查
# 避免V26之后版本的部署失败问题

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查计数器
PASS=0
FAIL=0

check_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((PASS++))
}

check_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((FAIL++))
}

check_warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
}

echo "========================================="
echo "AIsatoshi V27 预部署检查"
echo "========================================="
echo ""

# ============================================
# 1. 架构检查
# ============================================
echo "【1/8】架构检查..."

TARGET_ARCH="linux/amd64"
export DOCKER_DEFAULT_PLATFORM=$TARGET_ARCH
check_pass "目标架构设置为: $TARGET_ARCH"

# ============================================
# 2. 文件完整性检查
# ============================================
echo ""
echo "【2/8】文件完整性检查..."

REQUIRED_FILES=(
    "main.py"
    "requirements.txt"
    "Dockerfile"
    "core/__init__.py"
    "core/config.py"
    "core/logger.py"
    "core/exceptions.py"
    "models/__init__.py"
    "models/message.py"
    "models/task.py"
    "models/memory.py"
    "models/evolution.py"
    "storage/__init__.py"
    "storage/database.py"
    "storage/conversation_store.py"
    "storage/task_store.py"
    "storage/memory_store.py"
    "storage/evolution_store.py"
    "services/__init__.py"
    "services/memory_manager.py"
    "services/evolution_engine.py"
    "services/ai_engine.py"
    "services/telegram_service.py"
    "services/task_scheduler.py"
    "services/web_scraper.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        check_pass "文件存在: $file"
    else
        check_fail "文件缺失: $file"
    fi
done

# ============================================
# 3. 代码语法检查
# ============================================
echo ""
echo "【3/8】代码语法检查..."

if python3 -m py_compile main.py 2>/dev/null; then
    check_pass "main.py 语法检查通过"
else
    check_fail "main.py 存在语法错误"
fi

if python3 -c "import sys; sys.path.insert(0, '.'); from core.config import Config" 2>/dev/null; then
    check_pass "核心模块导入成功"
else
    check_fail "核心模块导入失败"
fi

# ============================================
# 4. 数据库初始化测试
# ============================================
echo ""
echo "【4/8】数据库初始化测试..."

# 创建临时数据目录
mkdir -p /tmp/aisatoshi_test_data

if python3 -c "
import sys
sys.path.insert(0, '.')
from storage.database import Database
db = Database('/tmp/aisatoshi_test_data/test.db')
print('数据库初始化成功')
" 2>/dev/null; then
    check_pass "数据库初始化测试通过"
else
    check_fail "数据库初始化测试失败"
fi

# 清理
rm -rf /tmp/aisatoshi_test_data

# ============================================
# 5. 依赖检查
# ============================================
echo ""
echo "【5/8】Python依赖检查..."

if python3 -c "import requests; print('requests: OK')" 2>/dev/null; then
    check_pass "requests 模块可用"
else
    check_fail "requests 模块缺失"
fi

if python3 -c "import sqlite3; print('sqlite3: OK')" 2>/dev/null; then
    check_pass "sqlite3 模块可用"
else
    check_fail "sqlite3 模块缺失"
fi

# ============================================
# 6. 配置验证检查
# ============================================
echo ""
echo "【6/8】配置验证检查..."

if [ -n "$AI_PRIVATE_KEY" ]; then
    check_pass "AI_PRIVATE_KEY 已设置"
else
    check_warn "AI_PRIVATE_KEY 未设置（将在部署时注入）"
fi

if [ -n "$GEMINI_API_KEY" ]; then
    check_pass "GEMINI_API_KEY 已设置"
else
    check_warn "GEMINI_API_KEY 未设置（将在部署时注入）"
fi

if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
    check_pass "TELEGRAM_BOT_TOKEN 已设置"
else
    check_warn "TELEGRAM_BOT_TOKEN 未设置（将在部署时注入）"
fi

# ============================================
# 7. Docker镜像检查
# ============================================
echo ""
echo "【7/8】Docker镜像构建检查..."

# 清理旧的测试镜像
docker rmi aisatoshi:v27-test 2>/dev/null || true

echo "构建测试镜像..."
if docker build --no-cache -t aisatoshi:v27-test . > /tmp/build.log 2>&1; then
    check_pass "Docker镜像构建成功"

    # 检查镜像架构
    ARCH=$(docker inspect --format='{{.Architecture}}' aisatoshi:v27-test 2>/dev/null || echo "unknown")
    if [ "$ARCH" = "amd64" ]; then
        check_pass "镜像架构正确: $ARCH"
    else
        check_fail "镜像架构错误: $ARCH (应为amd64)"
    fi

    # 测试镜像启动
    if docker run --rm aisatoshi:v27-test python3 -c "print('Container OK')" 2>/dev/null; then
        check_pass "镜像可以正常启动"
    else
        check_fail "镜像启动失败"
    fi
else
    check_fail "Docker镜像构建失败"
    echo "查看构建日志: cat /tmp/build.log"
fi

# ============================================
# 8. 版本一致性检查
# ============================================
echo ""
echo "【8/8】版本一致性检查..."

VERSION_IN_DOCKERFILE=$(grep "version=" Dockerfile | head -1 | cut -d'"' -f2 || echo "unknown")
echo "Dockerfile版本: $VERSION_IN_DOCKERFILE"

if [[ "$VERSION_IN_DOCKERFILE" == *"27"* ]]; then
    check_pass "Dockerfile版本正确: $VERSION_IN_DOCKERFILE"
else
    check_fail "Dockerfile版本不正确: $VERSION_IN_DOCKERFILE"
fi

# ============================================
# 总结
# ============================================
echo ""
echo "========================================="
echo "检查完成！"
echo "========================================="
echo -e "${GREEN}通过: $PASS${NC}"
echo -e "${RED}失败: $FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}🎉 所有检查通过！可以部署了！${NC}"
    echo ""
    echo "下一步:"
    echo "1. 构建: docker build -t pancakekevin911/aisatoshi:v27 ."
    echo "2. 推送: docker push pancakekevin911/aisatoshi:v27"
    echo "3. 部署: 上传 deploy_v27.yaml 到 Akash"
    exit 0
else
    echo -e "${RED}❌ 存在 $FAIL 项检查失败，请修复后再部署${NC}"
    exit 1
fi
