$env:FLASK_APP = "app:create_app()"
$env:FLASK_ENV = "development"
$env:FLASK_DEBUG = "true"
$env:FLASK_DEV_AUTH = "true"
Set-Location "C:\Users\gandh\Desktop\MiroFish\backend"
python -m flask run --port 5001 --host 0.0.0.0 --no-reload
