#!/bin/bash
# AIsatoshi V27 - 构建和推送脚本
#
# 全新架构 V27 - 不是基于 V26 修改
set -e

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 配置
IMAGE_NAME="pancakekevin911/aisatoshi:v27"
TARGET_ARCH="linux/amd64"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🚀 AIsatoshi V27 构建和推送${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "V27 = 记忆原生 + 进化原生 + 任务继承原生"
echo ""
echo "镜像: $IMAGE_NAME"
echo "架构: $TARGET_ARCH"
echo ""

# 确保在正确的目录
cd "$(dirname "$0")/.."

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
        echo "🚀 下一步："
        echo "   1. 上传 deploy_v27.yaml 到 Akash"
        echo "   2. 或者: akash tx deployment send deploy_v27.yaml"
        echo ""
        echo "镜像: $IMAGE_NAME"
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
