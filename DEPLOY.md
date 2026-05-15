# 标准审查助手 - 云服务器部署指南

> 本指南将应用部署到云服务器（以腾讯云/阿里云 Ubuntu 22.04 为例），使用 Docker 容器化部署，支持团队长期正式使用。

---

## 目录

1. [快速开始（一键部署）](#1-快速开始一键部署)
2. [服务器选购与初始化](#2-服务器选购与初始化)
3. [环境配置详解](#3-环境配置详解)
4. [HTTPS 安全加固（可选）](#4-https-安全加固可选)
5. [团队访问方式](#5-团队访问方式)
6. [运维与维护](#6-运维与维护)
7. [故障排查](#7-故障排查)

---

## 1. 快速开始（一键部署）

### 前置条件

- 一台云服务器（Ubuntu 22.04，2核4G 起）
- Docker + docker-compose 已安装
- DeepSeek API Key

### 部署步骤

```bash
# 1. 上传代码到服务器（本地执行）
scp -r c:/Users/dell/WorkBuddy/Claw user@你的服务器IP:/opt/claw

# 2. SSH 登录服务器
ssh user@你的服务器IP

# 3. 进入项目目录
cd /opt/claw

# 4. 配置环境变量（必填）
cp .env.example .env
nano .env          # 填入 DEEPSEEK_API_KEY

# 5. 一键部署
bash deploy/deploy.sh
```

部署脚本会自动：
- 检查 Docker 环境
- 创建数据目录
- 构建并启动容器
- 验证服务健康状态

---

## 2. 服务器选购与初始化

### 推荐配置

| 用途 | 推荐配置 | 参考价格 |
|------|----------|----------|
| 小团队（1-10人） | 2核4G，50GB SSD | ¥30-50/月 |
| 中等团队（10-50人） | 4核8G，100GB SSD | ¥80-120/月 |
| 大团队或高并发 | 8核16G，200GB SSD | ¥200+/月 |

推荐服务商：
- **腾讯云**：轻量应用服务器（2核4G，¥38/月）
- **阿里云**：ECS 共享型 s6
- **华为云**：云耀云服务器

### 系统初始化（Ubuntu 22.04）

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# 安装 docker-compose（独立二进制）
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# 验证安装
docker --version
docker-compose --version

# 开放防火墙端口
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 8000/tcp  # 应用（初期直接访问）
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

---

## 3. 环境配置详解

### 上传代码到服务器

**方式 A：Git（推荐，便于后续更新）**

```bash
# 在服务器上克隆仓库
git clone https://your-git-repo/claw.git /opt/claw
```

**方式 B：SCP 本地上传**

```bash
# 本地执行（PowerShell）
scp -r C:\Users\dell\WorkBuddy\Claw user@server-ip:/opt/claw
```

### 配置环境变量

```bash
cd /opt/claw
cp .env.example .env
nano .env
```

必须修改的内容：

```env
# 填入你的 DeepSeek API Key（从 https://platform.deepseek.com/ 获取）
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 其他保持默认即可
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
DEBUG=false
```

### 启动服务

```bash
# 构建镜像（首次运行或代码更新后）
cd /opt/claw
docker-compose build

# 启动服务（后台运行）
docker-compose up -d

# 查看运行状态
docker-compose ps

# 查看实时日志
docker-compose logs -f claw

# 重启服务
docker-compose restart claw
```

### 验证服务

```bash
curl http://localhost:8000/
# 应返回 HTML 首页内容
```

---

## 4. HTTPS 安全加固（可选）

推荐使用 **Let's Encrypt** 免费证书，配合 Nginx 反代。

### 安装 Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 申请 SSL 证书（以域名为例）

```bash
# 假设你的域名是 review.your-domain.com
# 先确保 DNS 已解析到服务器 IP
sudo certbot --nginx -d review.your-domain.com
```

### 配置 Nginx + SSL

编辑 `deploy/nginx.conf`，取消 HTTPS 相关段的注释：

```nginx
server {
    listen 443 ssl http2;
    server_name review.your-domain.com;

    ssl_certificate     /etc/letsencrypt/live/review.your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/review.your-domain.com/privkey.pem;
    ...
}
```

重启 Nginx：
```bash
sudo nginx -t && sudo systemctl reload nginx
```

### 证书自动续期

Let's Encrypt 证书有效期 90 天，Certbot 会自动续期，只需确保定时任务存在：

```bash
sudo certbot renew --dry-run
```

---

## 5. 团队访问方式

### 直接 IP 访问（初期/内网）

```
http://服务器IP:8000
```

### 域名 + HTTPS（正式使用）

```
https://review.your-domain.com
```

### 局域网共享（无公网服务器时）

在同一 WiFi 下的同事直接访问：

```
http://192.168.x.x:8000
```

> ⚠️ 注意：此方式仅限局域网，外部网络无法访问。

### 分享给同事使用

建议将访问地址保存为浏览器书签，并告诉他们：
- 推荐使用 Chrome/Edge 浏览器
- 上传文件大小限制 50MB
- 审查时间取决于文档长度，通常 30秒 - 3分钟

---

## 6. 运维与维护

### 常用运维命令

```bash
# 查看服务状态
docker-compose ps

# 查看实时日志
docker-compose logs -f claw

# 重启服务
docker-compose restart claw

# 更新代码后重新部署
git pull
docker-compose up -d --build

# 更新 .env 后重载
docker-compose exec claw envsubst < /path/to/.env
docker-compose restart claw

# 停止服务
docker-compose down

# 完全清除（包括数据!慎用）
docker-compose down -v
```

### 数据备份

```bash
# 备份 data 目录（包含上传文件和报告）
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
tar -czf "claw_backup_${BACKUP_DATE}.tar.gz" \
    /opt/claw/data \
    /opt/claw/.env
```

### 定时备份到云存储（可选）

```bash
# 添加到 crontab，每天凌晨3点自动备份
crontab -e
# 0 3 * * * /opt/claw/scripts/backup.sh
```

---

## 7. 故障排查

### 服务无法启动

```bash
# 查看详细错误日志
docker-compose logs claw
docker-compose logs --tail=100 claw
```

### 端口被占用

```bash
# 查看 8000 端口占用
sudo lsof -i :8000

# 释放端口
sudo kill -9 <PID>
```

### 前端无法访问 API

```bash
# 确认容器健康状态
docker-compose ps

# 在容器内测试网络
docker-compose exec claw curl -v http://localhost:8000/api/standards

# 确认防火墙
sudo ufw status
sudo iptables -L -n | grep 8000
```

### 上传文件报错

```bash
# 检查 data 目录权限
ls -la /opt/claw/data/
# 正确权限应该是: drwxr-xr-x

# 修复权限
sudo chown -R 1000:1000 /opt/claw/data
```

### 内存不足（OOM）

如果服务器内存较小（2GB），可能需要添加 swap：

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 部署检查清单

```
[ ] 云服务器已购买并可以 SSH 登录
[ ] Ubuntu 22.04 已初始化
[ ] Docker + docker-compose 已安装
[ ] 防火墙已开放 8000/80/443 端口
[ ] DeepSeek API Key 已申请
[ ] 代码已上传到 /opt/claw
[ ] .env 文件已配置
[ ] docker-compose up -d 成功
[ ] curl http://localhost:8000 返回正常
[ ] 团队成员可正常访问使用
```

---

## 架构图

```
                                    ┌─────────────────┐
  团队成员浏览器 ─── HTTPS ────→   │  Nginx (可选)   │
                                    │  443 → 8000    │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │  Docker 容器    │
                                    │                 │
                                    │  FastAPI        │
                                    │  (uvicorn)      │
                                    │                 │
                                    │  /app/data/     │
                                    │  (数据卷挂载)    │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │  宿主机文件系统  │
                                    │  /opt/claw/     │
                                    │  ├─ data/       │
                                    │  ├─ frontend/   │
                                    │  └─ backend/     │
                                    └─────────────────┘
```
