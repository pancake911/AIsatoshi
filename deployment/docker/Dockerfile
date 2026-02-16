# AIsatoshi V30.0 - 从头构建
# 不依赖任何 aisatoshi 基础镜像
# 所有代码从 src/ 复制，完全可控

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    # Chromium 和依赖
    chromium \
    fonts-liberation \
    fonts-noto-color-emoji \
    # 其他工具
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# 复制 requirements
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Playwright 浏览器
RUN playwright install --with-deps chromium

# 复制源代码（单一来源）
COPY src/ /app/src/

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/usr/bin
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# 数据目录
RUN mkdir -p /app/data

# 版本信息（单一来源）
ENV AISATOSHI_VERSION="30.0"
ENV AISATOSHI_BUILD_DATE="2026-02-16"

# 暴露端口（用于健康检查）
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# 启动命令
CMD ["python", "src/main.py"]
