#!/bin/bash
# AIsatoshi V27 - 构建脚本
#
# 确保构建正确的架构（amd64）

set -e

VERSION="v27"
IMAGE_NAME="pancakekevin911/aisatoshi"
FULL_IMAGE_NAME="${IMAGE_NAME}:${VERSION}"

echo "========================================="
echo "构建 AIsatoshi ${VERSION}"
echo "========================================="

# 确保目标架构
export DOCKER_DEFAULT_PLATFORM=linux/amd64
echo "目标架构: linux/amd64"

# 清理旧镜像
echo ""
echo "清理旧镜像..."
docker rmi ${FULL_IMAGE_NAME} 2>/dev/null || true
docker rmi ${IMAGE_NAME}:latest 2>/dev/null || true

# 构建镜像
echo ""
echo "构建镜像..."
docker build --no-cache \
    --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
    --build-arg VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown") \
    -t ${FULL_IMAGE_NAME} \
    -f Dockerfile .

# 标记latest
docker tag ${FULL_IMAGE_NAME} ${IMAGE_NAME}:latest

# 显示镜像信息
echo ""
echo "========================================="
echo "构建完成！"
echo "========================================="
echo "镜像: ${FULL_IMAGE_NAME}"
docker images ${IMAGE_NAME}:${VERSION} --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
echo ""

# 验证架构
ARCH=$(docker inspect --format='{{.Architecture}}' ${FULL_IMAGE_NAME})
echo "架构: ${ARCH}"

if [ "$ARCH" = "amd64" ]; then
    echo "✅ 架构正确"
else
    echo "❌ 架构错误: $ARCH (应为amd64)"
    exit 1
fi
