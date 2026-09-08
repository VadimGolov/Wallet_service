Write-Host "`n--------------------------------------------------" -ForegroundColor Cyan
Write-Host "Запуск Режима Тестирования..." -ForegroundColor Cyan
Write-Host "--------------------------------------------------" -ForegroundColor Cyan

# Проверяем, существует ли образ для тестового сервиса
$image_exists = docker compose -p test -f docker-compose.test.yml ps -a

if (-not $image_exists) {
    Write-Host "`nТестоые Контейнеры пока не созданы" -ForegroundColor Yellow
    Write-Host "`n[1] Создаю новые тестовые контейнеры..." -ForegroundColor Green
    docker compose -p test -f docker-compose.test.yml up --build --abort-on-container-exit
    exit 1
} else {
    Write-Host "`nТестоые Контейнеры уже созданы" -ForegroundColor Green
}

    # Шаг 1: Спрашиваем про сборку контейнера
Write-Host "`n[1] Вы хотите пересобрать тестовые контейнеры? (Y/N): " -NoNewline -ForegroundColor Yellow
$delete = Read-Host

if ($delete -eq 'Y' -or $delete -eq 'y') {
    # Удаляем тестовый контейнер и volume с данными
    Write-Host "`n[2] Удаляю тестовые контейнеры и volume с данными" -ForegroundColor Green
    docker compose -p docker-compose.test.yml down -v

    # Поднимаем новый тестовый контейнер
    Write-Host "`n[3] Создаю новые тестовые контейнеры..." -ForegroundColor Green
    docker compose -p test -f docker-compose.test.yml up --build --abort-on-container-exit
} else {
    # Поднимаем тестовый контейнер без пересборки образа
    Write-Host "`n[2] Использую имеющийся тестовый контейнер, запускаю тесты..." -ForegroundColor Green
    docker compose -p test -f docker-compose.test.yml up --abort-on-container-exit
}