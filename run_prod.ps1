Write-Host "Запуск производственного режима..." -ForegroundColor Cyan
Write-Host "Убираю старые контейнеры" -ForegroundColor Green
docker compose down
Write-Host "Создаю новые контейнеры" -ForegroundColor Green
docker compose up -d --build
Write-Host "Проверка статуса:" -ForegroundColor Cyan
docker compose ps