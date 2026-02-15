# Versions 目录

> 每个子目录代表一个独立版本，包含该版本的完整代码和部署配置。

---

## 目录说明

### v28.0/ - 稳定基准版
- **文件**: `telegram_bot_integration_v28.py`
- **状态**: ✅ 生产稳定
- **用途**: 当前生产环境推荐版本

### v29.0/ - Telegram 解析修复
- **修复**: `parse_mode=None` 避免 Telegram 解析错误
- **用途**: 解决 V28 的 Telegram 报错

### v29.1/ - 记忆增强
- **新增**: URL 变体匹配，AI prompt 优化
- **用途**: 改善记忆检索准确性

### v29.2/ - 网络优化
- **调整**: Playwright 超时配置
- **用途**: 网络不稳定环境

### v29.3/ - 分段发送
- **新增**: 长消息自动分多段 (3000字符/段)
- **用途**: 解决长消息截断问题

### v29.5/ - 分段重构
- **重构**: `_send_single_message()` 辅助函数
- **用途**: 更稳定的分段发送实现

---

## 部署指定版本

```bash
# 示例：部署 V29.5
kubectl apply -f versions/v29.5/deploy.yaml
```

---

## 开发新版本

```bash
# 1. 复制最新版本
cp -r versions/v29.5 versions/v30.0

# 2. 修改代码
cd versions/v30.0
# 编辑文件...

# 3. 更新文档
# - 更新根目录 VERSIONS.md
# - 更新根目录 CHANGELOG.md
# - 更新本 README.md

# 4. 提交
git add versions/v30.0/
git commit -m "Add V30.0 - [描述]"
```
