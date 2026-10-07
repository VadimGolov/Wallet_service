Write-Host "`n--------------------------------------------------" -ForegroundColor Cyan
Write-Host "Запуск Производственного Режима..." -ForegroundColor Cyan
Write-Host "--------------------------------------------------" -ForegroundColor Cyan

# Удаление старых контейнеров
Write-Host "`n[1] Удаление старых контейнеров" -ForegroundColor Green
docker compose -f docker-compose.yml down -v --remove-orphans --rmi local

# Создание новых контейнеров
Write-Host "`n[2] Создание новых контейнеров" -ForegroundColor Green
docker compose -f docker-compose.yml up -d --build

# Проверка статуса
Write-Host "`n[3] Проверка статуса" -ForegroundColor Cyan
docker compose ps

# --- Финал ---
$compose = "docker compose -f docker-compose.yml "

Write-Host "`n--------------------------------------------------" -ForegroundColor Cyan
Write-Host "Swagger: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Логи:    $compose logs -f" -ForegroundColor Cyan
Write-Host "Стоп:    $compose down" -ForegroundColor Cyan
Write-Host "--------------------------------------------------" -ForegroundColor Cyan