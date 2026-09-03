Write-Host "`n--------------------------------------------------" -ForegroundColor Cyan
Write-Host "Запуск Производственного Режима..." -ForegroundColor Cyan
Write-Host "--------------------------------------------------" -ForegroundColor Cyan

# Удаление старых контейнеров
Write-Host "`n[1] Удаление старых контейнеров" -ForegroundColor Green
docker compose down

# Создание новых контейнеров
Write-Host "`n[2] Создание новых контейнеров" -ForegroundColor Green
docker compose up -d --build

# Проверка статуса
Write-Host "`n[3] Проверка статуса" -ForegroundColor Cyan
docker compose ps