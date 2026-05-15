@echo off
chcp 65001 > nul
cd /d "C:\Users\dell\WorkBuddy\Claw\backend"
start "" /MIN "C:\Users\dell\anaconda3\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8000

