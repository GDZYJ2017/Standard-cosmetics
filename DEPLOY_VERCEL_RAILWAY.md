# 化妆品标准智能审查系统 - Vercel + Railway 部署指南

> 本指南将前端部署到 Vercel（免费），后端部署到 Railway（免费额度够用），实现零成本云端部署。

---

## 目录

1. [部署架构](#部署架构)
2. [前置准备](#前置准备)
3. [部署后端到 Railway](#3-部署后端到-railway)
4. [部署前端到 Vercel](#4-部署前端到-vercel)
5. [配置前端 API 地址](#5-配置前端-api-地址)
6. [验证部署](#6-验证部署)
7. [日常运维](#7-日常运维)
8. [故障排查](#8-故障排查)

---

## 部署架构

```
┌─────────────────────────┐         ┌─────────────────────────┐
│   Vercel (前端)         │         │   Railway (后端)        │
│                         │         │                         │
│  - 静态 HTML/CSS/JS     │ ────→   │  - FastAPI + Python     │
│  - 零成本，自动 HTTPS    │  API    │  - DeepSeek AI 集成     │
│  - 全球 CDN 加速        │         │  - SQLite + 文件存储    │
│                         │         │  - 免费 500 小时/月     │
└─────────────────────────┘         └─────────────────────────┘
```

---

## 前置准备

### 1. 注册账号

- **GitHub**: https://github.com (必须有账号)
- **Vercel**: https://vercel.com (用 GitHub 登录)
- **Railway**: https://railway.app (用 GitHub 登录)
- **DeepSeek**: https://platform.deepseek.com (申请 API Key)

### 2. 推送代码到 GitHub

```bash
# 如果还没有 Git 仓库，先初始化
cd c:\Users\dell\WorkBuddy\Claw

# 初始化 Git（如果还没有）
git init

# 添加所有文件
git add .

# 提交
git commit -m "初始提交：化妆品标准智能审查系统"

# 在 GitHub 创建新仓库（不要初始化 README）
# 然后添加远程仓库
git remote add origin https://github.com/你的用户名/claw.git

# 推送
git branch -M main
git push -u origin main
```

---

## 3. 部署后端到 Railway

### 步骤 1: 连接 GitHub 仓库

1. 访问 https://railway.app
2. 点击 **"Login"** → 选择 **"GitHub"** 登录
3. 登录后点击 **"New Project"**
4. 选择 **"Deploy from GitHub repo"**
5. 选择你的 `claw` 仓库

### 步骤 2: 配置环境变量

在 Railway 项目页面：

1. 点击 **"Variables"** 标签
2. 添加以下环境变量：

```env
# 必填：DeepSeek API Key
DEEPSEEK_API_KEY=sk-你的API密钥

# 可选：使用默认值即可
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
DEBUG=false
```

### 步骤 3: 配置服务

Railway 会自动读取 `railway.toml` 配置文件，你应该会看到：

- **启动命令**: `python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}`
- **健康检查**: `/` 端口 `8000`
- **持久化存储**: `/app/data` (自动挂载)

### 步骤 4: 部署

1. 点击 **"Deploy"** 按钮
2. 等待部署完成（约 2-5 分钟）
3. 部署成功后，点击 **"Settings"** → **"Networking"**
4. 点击 **"Generate Domain"** 获取公网域名

你的后端地址类似：`https://cosmetic-standard-backend-production-xxxx.up.railway.app`

### 步骤 5: 测试后端 API

在浏览器访问：
```
https://你的railway域名/
https://你的railway域名/docs
```

应该能看到 API 文档页面。

---

## 4. 部署前端到 Vercel

### 步骤 1: 连接 GitHub 仓库

1. 访问 https://vercel.com
2. 点击 **"Log In"** → 选择 **"GitHub"** 登录
3. 登录后点击 **"Add New..."** → **"Project"**
4. 找到你的 `claw` 仓库，点击 **"Import"**

### 步骤 2: 配置项目

在项目配置页面：

1. **Project Name**: `cosmetic-standard-frontend`（自定义）
2. **Framework Preset**: 选择 **"Other"**
3. **Root Directory**: 保持 `./`
4. **Build Command**: 留空（已在 `vercel.json` 配置为 `null`）
5. **Output Directory**: 保持 `frontend`（已在 `vercel.json` 配置）

### 步骤 3: 配置环境变量（重要）

展开 **"Environment Variables"** 部分：

```env
# 添加后端 API 地址（替换为你的 Railway 域名）
VITE_API_URL=https://你的railway域名.up.railway.app/api
```

### 步骤 4: 部署

1. 点击 **"Deploy"**
2. 等待部署完成（约 30 秒 - 1 分钟）
3. 部署成功后，你会得到一个域名：

```
https://cosmetic-standard-frontend.vercel.app
```

---

## 5. 配置前端 API 地址

前端通过 `window.API_BASE` 变量配置后端 API 地址，有两种方式：

### 方式 1: 通过 URL 参数（推荐用于测试）

访问前端时添加 `?api=` 参数：
```
https://你的vercel域名.vercel.app?api=https://你的railway域名.up.railway.app/api
```

### 方式 2: 修改代码（推荐用于生产）

在前端 HTML 中硬编码 API 地址：

编辑 `frontend/index.html`，找到以下代码：

```javascript
window.API_BASE = window.API_BASE ||
    new URLSearchParams(location.search).get('api') ||
    '/api';
```

修改为：

```javascript
window.API_BASE = window.API_BASE ||
    new URLSearchParams(location.search).get('api') ||
    'https://你的railway域名.up.railway.app/api';
```

然后提交代码到 GitHub，Vercel 会自动重新部署。

---

## 6. 验证部署

### 1. 测试后端

```bash
# 测试健康检查
curl https://你的railway域名/

# 测试 API 文档
curl https://你的railway域名/docs

# 测试 API 端点
curl https://你的railway域名/api/standards
```

### 2. 测试前端

1. 打开浏览器访问：`https://你的vercel域名.vercel.app`
2. 检查页面是否正常加载
3. 尝试上传一个标准文件
4. 创建审查任务，观察是否正常

### 3. 检查浏览器控制台

按 F12 打开开发者工具，检查：
- **Console**: 是否有错误
- **Network**: API 请求是否成功（状态码 200）

---

## 7. 日常运维

### 更新代码

```bash
# 修改代码后提交
git add .
git commit -m "更新说明"
git push

# Vercel 和 Railway 会自动检测并重新部署
```

### 查看日志

**Railway 后端日志**:
1. 登录 Railway
2. 进入项目 → 点击 **"Deployments"**
3. 点击最新部署 → 查看 **"Logs"**

**Vercel 前端日志**:
1. 登录 Vercel
2. 进入项目 → 点击 **"Deployments"**
3. 点击最新部署 → 查看日志

### 查看环境变量

**Railway**:
- 项目页面 → **"Variables"** 标签

**Vercel**:
- 项目页面 → **"Settings"** → **"Environment Variables"**

### 自定义域名（可选）

**Vercel**:
1. 项目 → **"Settings"** → **"Domains"**
2. 添加你的自定义域名
3. 按提示配置 DNS

**Railway**:
1. 项目 → **"Settings"** → **"Domains"**
2. 添加自定义域名
3. 配置 DNS CNAME 记录

---

## 8. 故障排查

### 问题 1: 前端无法连接后端

**症状**: 前端报错 "Network Error" 或 "请求失败"

**解决方案**:
1. 检查 `window.API_BASE` 是否正确配置
2. 确认 Railway 后端正在运行（访问 `/docs` 测试）
3. 检查浏览器控制台的 CORS 错误

### 问题 2: Railway 部署失败

**症状**: Railway 显示 "Deploy Failed"

**解决方案**:
1. 查看部署日志
2. 检查 `requirements.txt` 是否完整
3. 确认 `railway.toml` 配置正确
4. 检查环境变量是否填写

**常见错误**:
```
ModuleNotFoundError: No module named 'fastapi'
```
→ 确保 `backend/requirements.txt` 包含所有依赖

### 问题 3: 前端页面空白

**症状**: 访问 Vercel 域名显示空白页

**解决方案**:
1. 检查 `vercel.json` 配置
2. 确认 `frontend/` 目录存在且有 `index.html`
3. 查看浏览器控制台错误

### 问题 4: API 调用 404

**症状**: 前端请求返回 404

**解决方案**:
1. 检查 API 路径是否正确（应该以 `/api` 开头）
2. 确认后端 `main.py` 中路由配置正确
3. 测试直接访问：`https://后端域名/api/standards`

### 问题 5: 文件上传失败

**症状**: 上传文件时报错

**解决方案**:
1. 检查 Railway 磁盘空间（免费额度 1GB）
2. 确认文件大小不超过 50MB
3. 查看后端日志

### 问题 6: Railway 免费额度用尽

**症状**: 服务停止运行

**解决方案**:
1. Railway 免费计划每月 500 小时（约 20 天连续运行）
2. 可以绑定信用卡获得额外 500 小时
3. 或者考虑升级到付费计划（$5/月起）

---

## 部署检查清单

```
[ ] GitHub 仓库已创建并推送代码
[ ] DeepSeek API Key 已申请
[ ] Railway 账号已注册并登录
[ ] Railway 后端已部署成功
[ ] Railway 环境变量已配置（DEEPSEEK_API_KEY）
[ ] Railway 域名已生成并记录
[ ] Vercel 账号已注册并登录
[ ] Vercel 前端已部署成功
[ ] Vercel 环境变量已配置（VITE_API_URL）
[ ] 前端 API_BASE 已正确指向后端
[ ] 前端页面可以正常访问
[ ] 上传标准文件测试成功
[ ] 创建审查任务测试成功
[ ] 查看审查报告测试成功
```

---

## 费用说明

### Vercel（前端）
- **免费额度**: 无限静态站点托管
- **带宽**: 100GB/月
- **构建时间**: 100 小时/月
- **HTTPS**: 免费自动配置
- **自定义域名**: 免费

### Railway（后端）
- **免费额度**: 500 小时/月（约 20 天连续运行）
- **存储空间**: 1GB
- **带宽**: 无限制
- **绑定信用卡**: 额外 +500 小时/月
- **付费计划**: $5/月起（无限运行时间）

### DeepSeek（AI API）
- **免费额度**: 新用户赠送一定额度
- **付费**: 按 token 计费，非常便宜
- **建议**: 充值 10 元可以用很久

---

## 后续优化建议

1. **数据库升级**: 从 SQLite 迁移到 PostgreSQL（Railway 支持）
2. **对象存储**: 使用 AWS S3 或 Cloudflare R2 存储文件
3. **CDN 加速**: Vercel 已自带全球 CDN
4. **监控告警**: 集成 Sentry 或 LogRocket
5. **CI/CD**: 配置 GitHub Actions 自动化测试
6. **域名绑定**: 使用自定义域名提升专业度

---

## 技术支持

如遇到问题，可以：
1. 查看 Railway/Vercel 官方文档
2. 检查项目日志
3. 在 GitHub Issues 提问

祝部署顺利！🚀
