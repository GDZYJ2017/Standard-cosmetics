#!/bin/bash
# Railway 启动脚本

# 进入 backend 目录
cd backend

# 启动 uvicorn
exec python -m uvicorn main:app --host 0.0.0.0 --port $PORT
