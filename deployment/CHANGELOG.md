# AIsatoshi 更新日志

> 按时间倒序排列，最新的在上面

---

## V29.5 (2026-02-15) - 分段发送重构

### 改进
- `_send_single_message()` 辅助函数 - 更清晰的分段逻辑
- 默认 `parse_mode=None` (更安全)
- 分段发送实现优化

### 文件
- `versions/v29.5/telegram_bot_integration.py`
- `versions/v29.5/deploy.yaml`

---

## V29.3 (2026-02-15) - 分段发送

### 修复
- 超过3000字符自动分多段发送 (不是截断)
- `parse_mode=None` 时不发送该字段

### 文件
- `versions/v29.3/telegram_bot_integration.py`
- `versions/v29.3/deploy.yaml`
- `versions/v29.3/Dockerfile`

---

## V29.1 (2026-02-15) - 记忆检索增强

### 新增
- URL 变体匹配 (clawnch -> clawn.ch)
- AI prompt 优化：记忆中有内容时直接回答

### 文件
- `versions/v29.1/deploy.yaml`

---

## V29.0 (2026-02-15) - Telegram 解析修复

### 修复
- `parse_mode=None` 避免 Telegram 解析错误
- 存储完整分析结果到记忆
- 第二次询问从记忆读取，不重新浏览

### 文件
- `versions/v29.0/deploy.yaml`

---

## V28.0 (2026-02-14) - 完整集成版

### 特性
- 单文件集成 (~106KB, 2346 行)
- Gemini AI 模型支持
- Moltbook API 集成
- 网站浏览与分析 (Playwright)
- Telegram Bot 完整交互
- 记忆系统 (对话历史)

### 文件
- `versions/v28.0/telegram_bot_integration_v28.py`

---

## V27 - 模块化架构

### 变化
- 从单文件重构为模块化架构
- 5个核心服务模块
- 完整的存储层
- 任务调度系统

### 目录
- `retained/aisatoshi_v27/`

---

## V26 - Full Browser

### 新增
- 完整浏览器集成
- 网站截图功能
- 自动化测试

---

## V23-V25 - 早期版本

归档于 `retained/` 目录

---

## 凭证更新历史

| 日期 | 更改内容 |
|------|----------|
| 2025-02-14 | 安全重置 - 新钱包、新 Bot Token、新 API Key |
| 2026-02-15 | Moltbook API Key 保留使用 (已暴露) |

---

**最后更新**: 2026-02-15
