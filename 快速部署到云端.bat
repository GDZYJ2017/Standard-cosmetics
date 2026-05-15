@echo off
chcp 65001 >nul
echo ========================================
echo 化妆品标准智能审查系统 - 快速部署脚本
echo ========================================
echo.

REM 检查 Git 是否安装
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Git，请先安装 Git: https://git-scm.com/
    pause
    exit /b 1
)

echo [1/5] 检查 Git 仓库状态...
echo.

REM 检查是否已初始化 Git
if not exist ".git" (
    echo [初始化] 正在初始化 Git 仓库...
    git init
    echo.
)

REM 检查是否有远程仓库
git remote -v | findstr origin >nul
if %errorlevel% neq 0 (
    echo [提示] 尚未配置远程仓库
    echo.
    set /p repo_url="请输入 GitHub 仓库地址 (例如: https://github.com/用户名/claw.git): "
    git remote add origin %repo_url%
    echo.
)

echo [2/5] 添加文件到 Git...
git add .
echo.

echo [3/5] 提交更改...
set /p commit_msg="请输入提交说明 (例如: 初始部署): "
if "%commit_msg%"=="" set commit_msg=部署到 Vercel 和 Railway
git commit -m "%commit_msg%"
echo.

echo [4/5] 推送到 GitHub...
git push -u origin main
if %errorlevel% neq 0 (
    echo [错误] 推送失败，请检查网络连接和仓库地址
    pause
    exit /b 1
)
echo.

echo [5/5] 部署准备完成！
echo.
echo ========================================
echo 下一步操作：
echo ========================================
echo.
echo 1. 部署后端到 Railway:
echo    - 访问 https://railway.app
echo    - 用 GitHub 登录
echo    - New Project → Deploy from GitHub repo
echo    - 选择本仓库
echo    - 添加环境变量 DEEPSEEK_API_KEY
echo    - 点击 Deploy
echo.
echo 2. 部署前端到 Vercel:
echo    - 访问 https://vercel.com
echo    - 用 GitHub 登录
echo    - Add New → Project
echo    - 导入本仓库
echo    - Framework Preset 选择 "Other"
echo    - 添加环境变量 VITE_API_URL (Railway 域名 + /api)
echo    - 点击 Deploy
echo.
echo 详细部署指南请查看: DEPLOY_VERCEL_RAILWAY.md
echo.
echo ========================================
pause
