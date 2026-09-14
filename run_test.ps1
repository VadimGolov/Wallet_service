Write-Host "`n--------------------------------------------------" -ForegroundColor Cyan
Write-Host "Запуск Режима Тестирования..." -ForegroundColor Cyan
Write-Host "--------------------------------------------------" -ForegroundColor Cyan

# Проверяем, существуют ли контейнеры
$containers = docker compose -f docker-compose.test.yml ps -q
if (-not $containers) {
    Write-Host "`n[1] Тестовые контейнеры не найдены" -ForegroundColor Yellow
    $rebuild = 'Y'
} else {
    Write-Host "`n[1] Тестовые контейнеры найдены" -ForegroundColor Green
    Write-Host "`nВы хотите пересобрать тестовые контейнеры? (Y/N): " -NoNewline -ForegroundColor Yellow
    $rebuild = Read-Host
}

if ($rebuild -eq 'Y' -or $rebuild -eq 'y') {
    if ($containers) {
        Write-Host "`n[2] Удаляю старые контейнеры и volume..." -ForegroundColor Yellow
        docker compose -f docker-compose.test.yml down -v --remove-orphans --rmi local
    }
    Write-Host "`n[3] Собираю новые контейнеры..." -ForegroundColor Yellow
    docker compose -f docker-compose.test.yml up -d --build --no-start
} else {
    Write-Host "`n[2] Использую существующие контейнеры..." -ForegroundColor Green
}

Write-Host "`n[4] Выполняю миграции..." -ForegroundColor Green
# docker compose -f docker-compose.test.yml up --abort-on-container-exit migrate
docker compose -f docker-compose.test.yml run --rm migrate

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nПри выполнении миграций произошла ошибка!" -ForegroundColor Red
    exit $LASTEXITCODE
} else {
    Write-Host "`nМиграции успешно выполнены" -ForegroundColor Green
}

Write-Host "`n--------------------------------------------------" -ForegroundColor Green
Write-Host "Запускаю тесты" -ForegroundColor Green
Write-Host "--------------------------------------------------" -ForegroundColor Green
# docker compose -f docker-compose.test.yml up --abort-on-container-exit test
docker compose -f docker-compose.test.yml run --rm test

Write-Host "`n--------------------------------------------------" -ForegroundColor Cyan
if ($LASTEXITCODE -eq 0) {
    Write-Host "Все тесты успешно пройдены" -ForegroundColor Green
} else {
    Write-Host "Есть проваленные тесты!" -ForegroundColor Red
}
Write-Host "--------------------------------------------------" -ForegroundColor Cyan

exit $LASTEXITCODE