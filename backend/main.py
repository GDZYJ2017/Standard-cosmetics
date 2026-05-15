import os
import sys
import logging

# Railway 环境中，工作目录已经是 backend/，不需要添加路径
# 本地开发时，确保从项目根目录运行
if os.getenv('RAILWAY_ENVIRONMENT') or os.path.exists('/app'):
    # Railway 环境：直接使用相对导入
    pass
else:
    # 本地开发环境：添加项目根目录到 path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from models.database import init_db
from api.standards import router as api_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="化妆品标准智能审查系统",
    description="专为化妆品检验方法、补充检验方法等标准初稿设计的智能审查系统",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 路由
app.include_router(api_router)

# 静态文件
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def serve_index():
    """返回前端主页面"""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "标准审查助手 API 运行中", "docs": "/docs"}


# 支持相对路径访问前端资源（css/js 直接在根路径下可访问）
from starlette.responses import FileResponse as _FR
@app.get("/css/{path:path}")
async def serve_css(path: str):
    f = os.path.join(FRONTEND_DIR, "css", path)
    if os.path.isfile(f):
        return _FR(f)
    return _FR(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/js/{path:path}")
async def serve_js(path: str):
    f = os.path.join(FRONTEND_DIR, "js", path)
    if os.path.isfile(f):
        return _FR(f)
    return _FR(os.path.join(FRONTEND_DIR, "index.html"))


@app.on_event("startup")
async def startup():
    await init_db()
    logger.info("标准审查助手启动完成")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="warning"
    )
