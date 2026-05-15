#!/bin/bash
# ================================================
# 标准审查助手 - 一键部署脚本（Linux/macOS）
# 用法: bash deploy/deploy.sh
# ================================================
set -e

APP_NAME="claw-review"
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="$APP_DIR/data"
PORT=8000

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()    { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo ""
echo "========================================"
echo "  标准审查助手 - 部署脚本"
echo "========================================"
echo ""

# ---------- 前置检查 ----------
command -v docker >/dev/null 2>&1 || error "Docker 未安装，请先安装 Docker: https://docs.docker.com/get-docker/"
command -v docker-compose >/dev/null 2>&1 || command -v docker >/dev/null 2>&1 || error "docker-compose 未安装"

# ---------- 确认环境变量 ----------
ENV_FILE="$APP_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    warn ".env 文件不存在，从 .env.example 复制..."
    cp "$APP_DIR/.env.example" "$ENV_FILE"
    warn "请编辑 $ENV_FILE 填入 DEEPSEEK_API_KEY 后重新运行此脚本"
    exit 1
fi

if ! grep -q "DEEPSEEK_API_KEY=sk-" "$ENV_FILE" 2>/dev/null; then
    warn "检测到 DEEPSEEK_API_KEY 可能未配置，请确认 $ENV_FILE"
fi

# ---------- 创建数据目录 ----------
info "创建数据目录..."
mkdir -p "$DATA_DIR/uploads" "$DATA_DIR/standards" "$DATA_DIR/reports"
chmod -R 755 "$DATA_DIR"

# ---------- 拉取最新代码 ----------
if [ -d "$APP_DIR/.git" ]; then
    info "拉取最新代码..."
    cd "$APP_DIR"
    git pull origin main
fi

# ---------- 构建并启动 ----------
info "构建 Docker 镜像..."
docker-compose build --pull

info "启动服务（后台运行）..."
docker-compose up -d

# ---------- 检查健康状态 ----------
sleep 8
HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" http://localhost:$PORT/ || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo ""
    info "========================================"
    info "  部署成功！"
    info "========================================"
    echo ""
    echo "  访问地址: http://$(hostname -I | awk '{print $1}'):$PORT"
    echo "  查看日志: docker-compose logs -f claw"
    echo "  停止服务: docker-compose down"
    echo ""
else
    error "服务启动失败（HTTP $HTTP_CODE），请运行 'docker-compose logs claw' 查看错误"
fi
