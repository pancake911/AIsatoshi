# AIsatoshi Telegram Bot

> AI 驱动的 Telegram Bot，支持网站浏览、分析和自然语言交互。

---

## 快速开始

### 给 AI 助手 / 新开发者

**从这两个文件开始**:

1. **[VERSIONS.md](VERSIONS.md)** - 版本对比和选择指南
2. **[CHANGELOG.md](CHANGELOG.md)** - 完整更新历史

### 当前版本状态

| 版本 | 状态 | 推荐用途 |
|------|------|----------|
| V28.0 | ✅ 稳定 | 生产环境 |
| V29.0-V29.5 | ⚠️ 待验证 | 修复版本 |

---

## 目录结构

```
AIsatoshi/
├── versions/           # 各版本独立代码
│   ├── v28.0/        # 稳定基准版
│   ├── v29.0/        # Telegram 解析修复
│   ├── v29.1/        # 记忆增强
│   ├── v29.2/        # 网络优化
│   ├── v29.3/        # 分段发送
│   └── v29.5/        # 分段重构
├── VERSIONS.md         # 版本对比指南 ⭐ 从这里开始
├── CHANGELOG.md       # 更新历史
└── README.md          # 本文件
```

---

## 部署

### 使用 Akash Network

```bash
# 选择版本
kubectl apply -f versions/v29.5/deploy.yaml
```

### 本地运行

```bash
# 1. 进入版本目录
cd versions/v29.5/

# 2. 设置环境变量
export AI_PRIVATE_KEY="..."
export GEMINI_API_KEY="..."
export TELEGRAM_BOT_TOKEN="..."

# 3. 运行
python telegram_bot_integration.py
```

---

## 核心功能

- ✅ **自然语言理解** - Gemini AI 驱动
- ✅ **网站浏览与分析** - Playwright 浏览器
- ✅ **记忆系统** - 对话历史持久化
- ✅ **Moltbook 集成** - 区块链任务执行
- ✅ **Telegram Bot** - 完整交互界面
- ✅ **分段发送** - 长消息自动分多段

---

## 故障诊断

| 问题 | 解决方案 |
|------|----------|
| Telegram 报错 "unsupported parse_mode" | 使用 V29.0+ |
| 长消息被截断 | 使用 V29.3+ |
| 记忆不准确 | 使用 V29.1+ |
| 网站加载超时 | 使用 V29.2+ |

---

## 凭证配置

⚠️ **测试凭证** (生产环境需更换):

```yaml
AI_PRIVATE_KEY: b5860e25ca4f4b625e9c4c293f0f20d6a849dbd94499951794490dd31fc0f857
GEMINI_API_KEY: AIzaSyDQBaSyRvHXlehD_nNfyn5nHxh-o5UP-2Y
TELEGRAM_BOT_TOKEN: 8247983622:AAExJZBnjQk0LrPzS31qcYw-FEREuKS7b7Y
MOLTBOOK_API_KEY: moltbook_sk_FA4mnPQdCG933ndWKYwq3zZ025YppW3e
```

---

## Docker 镜像

| 版本 | 镜像 |
|------|------|
| V28 | `pancakekevin911/aisatoshi:v28` |
| V29.0 | `pancakekevin911/aisatoshi:v29.0` |
| V29.3 | `pancakekevin911/aisatoshi:v29.3` |
| V29.5 | `pancakekevin911/aisatoshi:v29.5` |

---

## 文档

- [VERSIONS.md](VERSIONS.md) - 详细版本对比
- [CHANGELOG.md](CHANGELOG.md) - 完整更新日志

---

**项目**: AIsatoshi Telegram Bot
**维护者**: @pancake911
**仓库**: https://github.com/pancake911/AIsatoshi
