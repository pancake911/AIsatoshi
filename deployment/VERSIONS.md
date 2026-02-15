# AIsatoshi 版本对比与选择指南

> **给 AI 助手**: 本文档帮助你快速理解各版本差异，选择合适的版本继续开发。

---

## 快速索引

| 版本 | 状态 | 核心特性 | 推荐场景 | 目录 |
|------|------|----------|----------|------|
| **V28.0** | ✅ 稳定 | 完整单文件集成，支持网站浏览分析 | 生产环境 | `versions/v28.0/` |
| **V29.0** | ⚠️ 待验证 | parse_mode=None 修复 Telegram 解析错误 | Telegram 报错时 | `versions/v29.0/` |
| **V29.1** | ⚠️ 待验证 | 记忆检索增强，URL 变体匹配 | 记忆不准确时 | `versions/v29.1/` |
| **V29.2** | ⚠️ 待验证 | 网络优化，超时调整 | 网络不稳定时 | `versions/v29.2/` |
| **V29.3** | ⚠️ 待验证 | 分段发送(3000字符/段) | 长消息被截断时 | `versions/v29.3/` |
| **V29.5** | ⚠️ 待验证 | _send_single_message 辅助函数 | 分段发送失败时 | `versions/v29.5/` |

---

## 版本详细说明

### V28.0 (2026-02-14) - 稳定基准版

**文件**: `versions/v28.0/telegram_bot_integration_v28.py`

**特性**:
- ✅ 完整单文件集成 (~106KB)
- ✅ 支持 Gemini AI 模型
- ✅ Moltbook API 集成
- ✅ 网站浏览与分析功能
- ✅ Telegram Bot 完整交互
- ✅ 记忆系统 (对话历史)

**限制**:
- ⚠️ Telegram 消息可能遇到 parse_mode 错误
- ⚠️ 长消息(>4096字符)可能被截断

**部署**: `versions/v28.0/deploy.yaml` (需更新)

---

### V29.0 (2026-02-15) - Telegram 解析修复

**修复**: `parse_mode=None` 避免 Telegram "unsupported parse_mode" 错误

**改动**:
```python
# 修改前
bot.send_message(chat_id, text, parse_mode='Markdown')

# 修改后
bot.send_message(chat_id, text)  # 不传 parse_mode，默认 None
```

**文件**: `versions/v29.0/`

**使用场景**: 当 V28 出现 "Bad Request: can't parse entities" 错误时

---

### V29.1 (2026-02-15) - 记忆检索增强

**新增**: URL 变体匹配逻辑

```python
# clawnch -> clawn.ch 自动匹配
# user.com -> www.user.com 自动匹配
```

**改动**:
- 记忆检索时自动规范化 URL
- AI prompt 优化: 记忆中有内容时直接回答

**使用场景**: 记忆系统检索不到历史对话时

---

### V29.2 (2026-02-15) - 网络优化

**调整**: Playwright 超时配置

```yaml
GEMINI_TIMEOUT: 180  # 增加到 180 秒
```

**使用场景**: 网站加载慢导致浏览失败时

---

### V29.3 (2026-02-15) - 分段发送

**新增**: 消息分段发送逻辑

```python
MAX_LENGTH = 3000
if len(message) > MAX_LENGTH:
    # 分多段发送
    for i in range(0, len(message), MAX_LENGTH):
        chunk = message[i:i+MAX_LENGTH]
        bot.send_message(chat_id, chunk)
```

**同时**: parse_mode=None 修复

**使用场景**: 长分析结果被截断时

---

### V29.5 (2026-02-15) - 分段发送重构

**重构**: `_send_single_message()` 辅助函数

```python
def _send_single_message(chat_id, text):
    """发送单条消息，自动处理 parse_mode"""
    if parse_mode is None:
        bot.send_message(chat_id, text)
    else:
        bot.send_message(chat_id, text, parse_mode=parse_mode)
```

**改进**:
- 更清晰的分段逻辑
- 默认 parse_mode=None (更安全)

**使用场景**: V29.3 分段发送仍有问题时

---

## 已知问题追踪

| 问题 | 首次出现 | 修复版本 | 状态 |
|------|----------|----------|------|
| Telegram parse_mode 错误 | V28 | V29.0 | ✅ 已修复 |
| 长消息截断 | V28-V29.0 | V29.3 | ✅ 已修复 |
| 记忆检索不准确 | V28 | V29.1 | ✅ 已修复 |
| main.py 版本不匹配 | V27-V29 | 待定 | ⚠️ 待解决 |

---

## 部署凭证

```yaml
AI_PRIVATE_KEY: b5860e25ca4f4b625e9c4c293f0f20d6a849dbd94499951794490dd31fc0f857
GEMINI_API_KEY: AIzaSyDQBaSyRvHXlehD_nNfyn5nHxh-o5UP-2Y
TELEGRAM_BOT_TOKEN: 8247983622:AAExJZBnjQk0LrPzS31qcYw-FEREuKS7b7Y
MOLTBOOK_API_KEY: moltbook_sk_FA4mnPQdCG933ndWKYwq3zZ025YppW3e
```

⚠️ **安全提示**: 这些凭证已暴露，仅用于测试。生产环境请更换！

---

## Docker 镜像

| 版本 | 镜像 |
|------|------|
| V28 | `pancakekevin911/aisatoshi:v28` |
| V29.0 | `pancakekevin911/aisatoshi:v29.0` |
| V29.3 | `pancakekevin911/aisatoshi:v29.3` |
| V29.5 | `pancakekevin911/aisatoshi:v29.5` |

---

## 给 AI 助手的快速开始

### 1. 了解现状
```bash
# 查看最新代码
cat versions/v29.5/telegram_bot_integration.py

# 查看部署配置
cat versions/v29.5/deploy.yaml
```

### 2. 部署指定版本
```bash
# 使用 V29.5
kubectl apply -f versions/v29.5/deploy.yaml
```

### 3. 开发新版本
1. 复制最新版本目录: `cp -r versions/v29.5 versions/v30.0`
2. 修改代码
3. 更新本 VERSIONS.md
4. 更新 CHANGELOG.md

---

## 问题诊断决策树

```
用户报告问题
    |
    ├─ Telegram 报错 "unsupported parse_mode"
    │   └─> 使用 V29.0+
    │
    ├─ 长消息被截断
    │   └─> 使用 V29.3+
    │
    ├─ 记忆检索不到历史
    │   └─> 使用 V29.1+
    │
    └─ 网站加载超时
        └─> 使用 V29.2+
```

---

**最后更新**: 2026-02-15
**维护者**: pancake911
