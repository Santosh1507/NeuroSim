@echo off
cd /d C:\Users\gandh\Desktop\MiroFish\backend
python -m uvicorn main:app --host 127.0.0.1 --port 8001
