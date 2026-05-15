@echo off
chcp 65001 > nul
echo ============================================
echo   标准审查助手 - 启动中...
echo ============================================

REM 确保数据目录存在
if not exist "data\uploads" mkdir data\uploads
if not exist "data\standards" mkdir data\standards
if not exist "data\reports" mkdir data\reports

REM 启动后端服务器
echo 正在启动服务器（端口 8000）...
cd backend
C:\Users\dell\anaconda3\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000

pause
