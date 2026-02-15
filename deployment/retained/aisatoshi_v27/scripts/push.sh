#!/bin/bash
# AIsatoshi V27 - 推送脚本
#
# 将镜像推送到Docker Hub并验证

set -e

VERSION="v27"
IMAGE_NAME="pancakekevin911/aisatoshi"
FULL_IMAGE_NAME="${IMAGE_NAME}:${VERSION}"

echo "========================================="
echo "推送 AIsatoshi ${VERSION} 到 Docker Hub"
echo "========================================="

# 检查是否已登录
echo ""
echo "检查Docker登录状态..."
if ! docker info | grep -q "Username"; then
    echo "请先登录Docker Hub:"
    echo "docker login"
    exit 1
fi

# 推送镜像
echo ""
echo "推送镜像..."
docker push ${FULL_IMAGE_NAME}
docker push ${IMAGE_NAME}:latest

# 验证推送
echo ""
echo "验证推送..."
echo "拉取镜像测试..."
docker rmi ${FULL_IMAGE_NAME} 2>/dev/null || true
docker pull ${FULL_IMAGE_NAME}

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================="
    echo "✅ 推送成功！"
    echo "========================================="
    echo "镜像: ${FULL_IMAGE_NAME}"
    echo "架构: $(docker inspect --format='{{.Architecture}}' ${FULL_IMAGE_NAME})"
    echo ""
    echo "下一步: 上传 deploy_v27.yaml 到 Akash"
else
    echo "❌ 推送验证失败"
    exit 1
fi
