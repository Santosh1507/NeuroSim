Set-Location "C:\Users\gandh\Desktop\MiroFish\backend"
$env:PYTHONUNBUFFERED = "1"
python -m uvicorn main:app --host 127.0.0.1 --port 8001 2>&1 | Out-File -FilePath "backend.log" -Append
