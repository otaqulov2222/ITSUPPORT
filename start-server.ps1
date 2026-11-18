# Pharmacy AI — shu kompyuter server sifatida
# Postgres + Redis: Docker | API + Bot: lokal Python

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "== Docker: Postgres + Redis ==" -ForegroundColor Cyan
docker compose up -d postgres redis

Write-Host "== Demo xodim seed ==" -ForegroundColor Cyan
& ".\backend\.venv\Scripts\python.exe" ".\scripts\seed_demo_employee.py"

Write-Host "== API :8000 ==" -ForegroundColor Cyan
Start-Process -FilePath ".\backend\.venv\Scripts\uvicorn.exe" -ArgumentList "app.main:app --host 0.0.0.0 --port 8000" -WorkingDirectory "$PSScriptRoot\backend"

Start-Sleep -Seconds 3

Write-Host "== Telegram bot ==" -ForegroundColor Cyan
Start-Process -FilePath ".\backend\.venv\Scripts\python.exe" -ArgumentList "-m app.bot.runner" -WorkingDirectory "$PSScriptRoot\backend"

Write-Host ""
Write-Host "Tayyor:" -ForegroundColor Green
Write-Host "  API:      http://127.0.0.1:8000/docs"
Write-Host "  Health:   http://127.0.0.1:8000/health"
Write-Host "  Bot:      @vaksinamed_it_support_bot"
Write-Host "  Demo tel: +998901234567"
Write-Host "  Admin:    admin@pharmacy.uz / ChangeMeNow!123"
