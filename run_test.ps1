Write-Host "Запуск режима тестирования..." -ForegroundColor Cyan
Write-Host "Создаю тестовый контейнер" -ForegroundColor Green
docker compose -f docker-compose.yml -f docker-compose.test.yml up --build -d