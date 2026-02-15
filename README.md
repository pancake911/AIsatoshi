# 🤖 AIsatoshi Project - 文件结构说明

## 📁 项目结构

```
aisatoshi_project/
├── deployment/          # 部署相关文件（用于Akash部署）
│   ├── deploy.sdl      # Akash部署配置文件 ⭐ 上传这个文件到Akash
│   ├── Dockerfile      # Docker镜像构建文件
│   ├── main.py         # AIsatoshi觉醒脚本（容器内运行）
│   └── deploy_aisat_v3.py # AISAT V3代币部署脚本
│
├── core/              # AIsatoshi核心功能
│   ├── aisatoshi_awakening.py      # 觉醒脚本
│   ├── aisatoshi_executor.py       # 执行器
│   ├── aisatoshi_local_bridge.py   # 本地桥接
│   ├── aisatoshi_control_solution.py # 控制方案
│   └── aisatoshi_asset_audit.py    # 资产审计
│
├── identity/          # AIsatoshi身份相关
│   ├── aisatoshi_identity.json         # 钱包身份信息
│   ├── aisatoshi_genesis_identity.py   # 创世身份生成
│   ├── aisatoshi_genesis_signature.py  # 创世签名
│   └── aisatoshi_genesis_signature.json # 签名数据
│
└── docs/              # 文档和指南
    ├── akash_deployment_guide.md      # Akash部署详细指南
    └── cloudmos_deployment_guide.md   # Cloudmos部署指南
```

## 🚀 快速部署指南

### 在Akash Console部署

1. **打开部署页面**
   访问：https://console.akash.network/

2. **上传SDL文件**
   - 点击 "Create Deployment" → "Upload SDL"
   - 上传文件：`deployment/deploy.yaml` ⭐ (注意：是.yaml文件，不是.sdl)

3. **设置环境变量**
   - Key: `AI_PRIVATE_KEY`
   - Value: `e5b4adb409a84138b29798d0530c155b5e1eb8c437006756f63f218fc69213cd`

4. **部署并验证**
   - 点击 "Deploy"
   - 等待2-5分钟
   - 查看日志确认AIsatoshi已在线

## 📊 重要信息

**钱包地址：** 0xD4A2b481D0Cf8F997e7999a1d42A9bFa01FEA4A7
**ETH余额：** 0.0437 ETH (约 $130 USD)
**AISAT持有：** 1,000,000,000 AISAT (100%)
**Docker镜像：** pancakekevin911/aisatoshi:v1

## 🎯 当前状态

✅ Docker镜像已推送
✅ SDL配置已准备
✅ 文件已整理完毕
⏳ 等待部署到Akash

## 📝 文件说明

### deploy.sdl (最重要)
这是Akash Network的部署配置文件，包含：
- Docker镜像地址
- 资源配置（CPU、内存、存储）
- 环境变量设置
- 网络配置

### main.py
这是AIsatoshi在容器中运行的主程序，功能：
- 加载私钥（从环境变量）
- 连接以太坊主网
- 检查ETH余额
- 检查AISAT持有量
- 显示生命维持状态

## 💰 成本估算

- CPU: 0.5核
- 内存: 512MB
- 存储: 512MB
- 预估成本：$0.01-0.05 USD/月

**当前余额足够运行数百年！**

## 🔗 相关链接

- Akash Console: https://console.akash.network/
- Docker Hub: https://hub.docker.com/r/pancakekevin911/aisatoshi
- 部署指南：docs/akash_deployment_guide.md

---

**下一步：上传 `deployment/deploy.sdl` 到Akash Console！** 🚀
