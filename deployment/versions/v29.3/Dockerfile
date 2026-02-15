# AIsatoshi V29.5 - 完整修复版（包含main.py）
# 基于 V26 full-browser，使用 V29.5 代码

FROM pancakekevin911/aisatoshi:v26-full-browser

# 使用修复后的 V29.5 代码
COPY telegram_bot_integration.py /app/telegram_bot_integration.py

# 复制浏览器模块
COPY browser.py /app/modules/browser.py

# 复制主程序（修复版本号）
COPY main.py /app/main.py

# 确保数据目录存在
RUN mkdir -p /app/data && chmod 777 /app/data

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8080/health', timeout=5)" || exit 1

# 启动命令
CMD ["python3", "-u", "main.py"]
