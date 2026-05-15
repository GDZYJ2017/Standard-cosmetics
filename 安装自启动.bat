@echo off
chcp 65001 > nul
title 标准审查助手 - 安装开机自启动

echo ============================================
echo   标准审查助手 - 设置开机自启动
echo ============================================
echo.

REM 安装依赖
echo [1/3] 安装依赖...
C:\Users\dell\anaconda3\python.exe -m pip install pystray pillow pywin32 --quiet 2>nul
echo       完成。

REM 设置开机自启
echo [2/3] 设置开机自启动...
C:\Users\dell\anaconda3\python.exe -c "import sys; sys.path.insert(0,r'%~dp0backend'); exec(open('%~dp0tray_service.py','r',encoding='utf-8').read()); create_shortcut()" 2>nul

REM 创建桌面快捷方式
echo [3/3] 创建桌面快捷方式...
C:\Users\dell\anaconda3\python.exe -c "
import os, sys
proj = r'%~dp0'.rstrip('\\')
vbs = os.path.join(proj, '_tray_launcher.vbs')
bat = os.path.join(proj, '_tray_service.bat')
with open(bat, 'w', encoding='gbk') as f:
    f.write('@echo off\r\nchcp 65001 > nul\r\ncd /d \"' + proj + '\"\r\nC:\\Users\\dell\\anaconda3\\python.exe \"' + os.path.join(proj, 'tray_service.py') + '\"\r\n')
with open(vbs, 'w', encoding='utf-8') as f:
    f.write('Set WshShell = CreateObject(\"WScript.Shell\")\r\nWshShell.Run \"\"\"' + bat + '\"\"\", 0, False\r\n')
try:
    from win32com.client import Dispatch
    shell = Dispatch('WScript.Shell')
    desktop = shell.SpecialFolders('Desktop')
    sc = shell.CreateShortCut(os.path.join(desktop, '标准审查助手.lnk'))
    sc.Targetpath = 'wscript.exe'
    sc.Arguments = '\"' + vbs + '\"'
    sc.WorkingDirectory = proj
    sc.Description = '标准审查助手'
    sc.save()
    print('       桌面快捷方式已创建')
except Exception as e:
    print('       创建失败: ' + str(e))
"

echo.
echo ============================================
echo   安装完成！
echo.
echo   以后只需双击桌面的「标准审查助手」图标
echo   服务会自动在后台启动，无需手动操作
echo   浏览器访问 http://localhost:8000 即可使用
echo ============================================
echo.
pause
