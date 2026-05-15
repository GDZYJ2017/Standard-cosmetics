# 化妆品标准智能审查系统

专为化妆品检验方法、补充检验方法等标准初稿设计的智能审查系统。

## 技术架构

- **后端**: FastAPI + Python
- **前端**: 原生 HTML/CSS/JS
- **AI**: DeepSeek API
- **存储**: SQLite

## 部署

### 方案一：Vercel + Railway（推荐，免费）

**零成本部署，适合团队使用！**

#### 1. 部署后端到 Railway

1. 访问 [railway.app](https://railway.app)，用 GitHub 登录
2. 点击 "New Project" → "Deploy from GitHub repo"
3. 选择本仓库
4. 在 Variables 添加环境变量：
   - `DEEPSEEK_API_KEY` = 你的 DeepSeek API Key
5. 等待部署完成，记下 Railway 给的域名（如 `xxx.up.railway.app`）

#### 2. 部署前端到 Vercel

1. 访问 [vercel.com](https://vercel.com)，用 GitHub 登录
2. 点击 "Add New" → "Project"
3. 选择本仓库
4. Framework Preset 选择 "Other"
5. 在 Environment Variables 添加：
   - `VITE_API_URL` = `https://你的railway域名/api`
6. 点击 Deploy

#### 3. 访问

- 前端地址: `https://你的vercel域名.vercel.app`
- 后端地址: `https://你的railway域名.up.railway.app`
- API 文档: `https://你的railway域名/docs`

📖 **详细部署指南**: [DEPLOY_VERCEL_RAILWAY.md](DEPLOY_VERCEL_RAILWAY.md)

⚡ **快速开始**: 双击运行 `快速部署到云端.bat`

📋 **检查清单**: [部署检查清单.md](部署检查清单.md)

---

### 方案二：Docker 单机部署

```bash
# 构建
docker build -t claw .

# 运行
docker run -d -p 8000:8000 \
  -e DEEPSEEK_API_KEY=你的APIKey \
  -v claw_data:/app/data \
  --name claw \
  claw
```

访问 `http://localhost:8000`

---

### 方案三：本地开发

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY
python -m uvicorn backend.main:app --port 8000 --reload
```

访问 `http://localhost:8000`

---

## API 文档

部署完成后访问: `https://你的railway域名/docs`

## License

MIT
