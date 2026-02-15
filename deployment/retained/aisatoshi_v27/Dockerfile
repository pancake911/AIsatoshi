# AIsatoshi V27 - 生产部署

# 明确指定架构（Akash仅支持amd64）
FROM --platform=linux/amd64 python:3.9-slim

LABEL maintainer="AIsatoshi V27"
LABEL version="27.0.0"
LABEL description="AIsatoshi V27 - 记忆原生 + 进化原生 + 任务继承原生"

# 设置工作目录
WORKDIR /app

# 环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建数据目录（持久化！）
RUN mkdir -p /app/data /app/data/knowledge /app/workspace /tmp && \
    chmod 777 /app/data /app/workspace /tmp

# 健康检查
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)" || exit 1

# 启动
CMD ["python3", "main.py"]
