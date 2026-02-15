#!/bin/bash
# AIsatoshi V27-SECURE - 构建和推送脚本
#
# 安全修复版本 - 修复私钥泄露问题
# ✅ 添加 .dockerignore 防止敏感文件被打包进镜像
set -e

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
IMAGE_NAME="pancakekevin911/aisatoshi:v27-secure"
TARGET_ARCH="linux/amd64"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🔒 AIsatoshi V27-SECURE 构建和推送${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}V27-SECURE = V27 + 安全修复 (.dockerignore)${NC}"
echo ""
echo "镜像: $IMAGE_NAME"
echo "架构: $TARGET_ARCH"
echo ""

# 确保在正确的目录
cd "$(dirname "$0")/.."

# 检查 .dockerignore (安全关键)
if [ ! -f ".dockerignore" ]; then
    echo -e "${RED}❌ .dockerignore 不存在 - 安全风险！${NC}"
    exit 1
fi
echo -e "${GREEN}✅ .dockerignore 存在${NC}"

# 验证 .dockerignore 内容
if grep -q "deploy_" .dockerignore; then
    echo -e "${GREEN}✅ .dockerignore 包含 deploy_ 文件${NC}"
else
    echo -e "${RED}❌ .dockerignore 未排除 deploy_ 文件${NC}"
    exit 1
fi

# 检查 Dockerfile
if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}❌ Dockerfile 不存在${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Dockerfile 存在${NC}"

# 检查 main.py
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ main.py 不存在${NC}"
    exit 1
fi
echo -e "${GREEN}✅ main.py 存在${NC}"

# 设置目标平台
export DOCKER_DEFAULT_PLATFORM=$TARGET_ARCH

echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}📦 开始构建 Docker 镜像${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# 构建
if docker build --no-cache -t $IMAGE_NAME . ; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✅ 构建成功！${NC}"
    echo -e "${GREEN}========================================${NC}"

    # 检查镜像架构
    ARCH=$(docker inspect --format='{{.Architecture}}' $IMAGE_NAME 2>/dev/null || echo "unknown")
    echo "镜像架构: $ARCH"

    if [ "$ARCH" != "amd64" ]; then
        echo -e "${RED}❌ 架构错误: $ARCH (应为 amd64)${NC}"
        exit 1
    fi

    # 安全验证 - 检查镜像中是否有敏感文件
    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}🔒 安全验证${NC}"
    echo -e "${YELLOW}========================================${NC}"

    SENSITIVE_FILES=$(docker run --rm $IMAGE_NAME ls -la /app/ 2>/dev/null | grep -E "\.yaml|\.env" | grep -v "Total" || true)

    if [ -n "$SENSITIVE_FILES" ]; then
        echo -e "${RED}❌ 发现敏感文件在镜像中:${NC}"
        echo "$SENSITIVE_FILES"
        exit 1
    else
        echo -e "${GREEN}✅ 镜像中无敏感 YAML/ENV 文件${NC}"
    fi

    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}📤 推送到 Docker Hub${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""

    # 推送
    if docker push $IMAGE_NAME; then
        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}✅ 推送完成！${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo -e "${GREEN}🚀 下一步：${NC}"
        echo "   1. ⚠️  立即转移旧钱包资金到新钱包"
        echo "   2. 更新 deploy_v27-secure.yaml 中的密钥"
        echo "   3. 上传到 Akash 部署"
        echo ""
        echo -e "${GREEN}镜像: $IMAGE_NAME${NC}"
        echo -e "${GREEN}YAML: deploy_v27-secure.yaml${NC}"
        echo ""
    else
        echo -e "${RED}❌ 推送失败${NC}"
        exit 1
    fi
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}❌ 构建失败${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi
