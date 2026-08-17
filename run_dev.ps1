Write-Host "Запуск режима разработки..." -ForegroundColor Cyan
Write-Host "Убираю старые контейнеры" -ForegroundColor Green
docker compose down
Write-Host "Создаю новые контейнеры" -ForegroundColor Green
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build