Write-Host "Запуск режима разработки (volume + reload)..." -ForegroundColor Cyan
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build