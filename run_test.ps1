Write-Host "`n--------------------------------------------------" -ForegroundColor Cyan
Write-Host "Запуск Режима Тестирования..." -ForegroundColor Cyan
Write-Host "--------------------------------------------------" -ForegroundColor Cyan

# Поднимаем тестовый контейнер
Write-Host "`n[1] Создаю тестовый контейнер" -ForegroundColor Green
docker compose -f docker-compose.test.yml up --abort-on-container-exit