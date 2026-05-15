@echo off
cd /d C:\Users\dell\WorkBuddy\Claw\backend
start /B C:\Users\dell\anaconda3\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
