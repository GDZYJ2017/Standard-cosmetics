"""重新设置开机自启动和桌面快捷方式 - 用 pythonw 避免控制台窗口"""
import os
from win32com.client import Dispatch

proj = r'c:\Users\dell\WorkBuddy\Claw'
python = r'C:\Users\dell\anaconda3\pythonw.exe'
script = os.path.join(proj, 'tray_service.py')

shell = Dispatch('WScript.Shell')

# 1. 开机自启动
startup = shell.SpecialFolders('Startup')
sc = shell.CreateShortCut(os.path.join(startup, '标准审查助手.lnk'))
sc.Targetpath = python
sc.Arguments = f'"{script}"'
sc.WorkingDirectory = proj
sc.Description = '标准审查助手后台服务'
sc.save()
print('OK: 开机自启动已设置')

# 2. 桌面快捷方式
desktop = shell.SpecialFolders('Desktop')
dc = shell.CreateShortCut(os.path.join(desktop, '标准审查助手.lnk'))
dc.Targetpath = python
dc.Arguments = f'"{script}"'
dc.WorkingDirectory = proj
dc.Description = '标准审查助手'
dc.save()
print('OK: 桌面快捷方式已创建')

print('完成！')
