# ================================================
# 标准审查助手 - 生产环境 Dockerfile
# ================================================
FROM python:3.11-slim

LABEL maintainer="Cosmetic Standard Team"
LABEL description="化妆品标准智能审查系统 - 专为化妆品检验方法、补充检验方法等标准初稿设计的智能审查系统"

# 环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# 安装系统依赖（docx/pdf 解析 + 字体支持）
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 文档解析
    libxml2-dev \
    libxslt1-dev \
    antiword \
    unrtf \
    catdoc \
    # 浏览器自动化（如需要截图）
    # chromium \
    # curl（健康检查用）
    curl \
    # 字体（PDF/报告中文渲染）
    fonts-noto-cjk \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash app

WORKDIR /app

# 复制依赖文件并安装（利用 Docker 缓存层）
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# 复制应用代码（排除 .pyc 和 __pycache__）
COPY --chown=app:app backend/ /app/backend/
COPY --chown=app:app frontend/ /app/frontend/
COPY --chown=app:app data/ /app/data/

# 数据目录权限
RUN mkdir -p /app/data/uploads /app/data/standards /app/data/reports \
    && chown -R app:app /app/data

USER app

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# uvicorn：以 app 用户运行，绑定所有网卡
# 生产环境使用单进程 + nginx 做负载均衡（见 deploy/nginx.conf）
CMD ["python", "-m", "uvicorn", "backend.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000"]
