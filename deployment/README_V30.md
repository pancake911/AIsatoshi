# AIsatoshi V30.0

> AI 驱动的 Telegram Bot，支持深度浏览和自然语言交互。

## 版本信息

- **版本**: V30.0
- **构建日期**: 2026-02-16
- **镜像**: `pancakekevin911/aisatoshi:v30.0`

## 特性

- ✅ **深度浏览** - Playwright 完整浏览器，支持多页面访问
- ✅ **分段发送** - 长消息自动分段，不超过 Telegram 限制
- ✅ **AI 理解** - Gemini AI 自然语言理解
- ✅ **记忆系统** - 对话历史持久化
- ✅ **钱包操作** - 区块链钱包功能

## 目录结构

```
aisatoshi/
├── src/                    # 所有源代码（单一来源）
│   ├── main.py             # 主入口
│   ├── config.py           # 配置（从环境变量读取）
│   ├── bot/                # Telegram Bot
│   │   ├── telegram.py      # Bot 客户端
│   │   ├── commands.py      # 命令处理
│   │   └── message_handler.py  # 消息处理
│   ├── ai/                 # AI 模块
│   │   ├── gemini.py        # Gemini API
│   │   └── prompts.py       # AI Prompts
│   ├── browser/            # 浏览器模块
│   │   ├── scraper.py       # Playwright Scraper
│   │   └── deep_browse.py   # 深度浏览（修复 bug）
│   ├── memory/             # 记忆模块
│   │   └── storage.py       # 记忆存储
│   └── blockchain/         # 区块链模块
│       └── wallet.py        # 钱包操作
├── docker/
│   └── Dockerfile          # 从头构建
├── requirements.txt
└── README.md
```

## 环境变量

```bash
# 必需
TELEGRAM_BOT_TOKEN=xxx
GEMINI_API_KEY=xxx
AI_PRIVATE_KEY=xxx

# 可选
MOLTBOOK_API_KEY=xxx
TELEGRAM_USER_ID=xxx
GEMINI_MODEL=gemini-2.0-flash-exp
LOG_LEVEL=INFO
DATA_DIR=/app/data
```

## 构建

```bash
cd ~/Desktop/aisatoshi
docker build -f docker/Dockerfile -t pancakekevin911/aisatoshi:v30.0 .
```

## 运行

```bash
docker run -d \
  -e TELEGRAM_BOT_TOKEN=xxx \
  -e GEMINI_API_KEY=xxx \
  -e AI_PRIVATE_KEY=xxx \
  pancakekevin911/aisatoshi:v30.0
```

## V30.0 修复内容

1. **深度浏览 bug 修复** - 直接使用 Playwright 提取的链接
2. **AI Prompt 简化** - 从 300 行减少到 50 行
3. **模块化架构** - 每个功能独立文件
4. **环境变量配置** - 不在代码中硬编码敏感信息
5. **从头构建 Docker** - 不依赖 aisatoshi 基础镜像

## 更新日志

- V30.0 (2026-02-16) - 全新架构，深度浏览修复
