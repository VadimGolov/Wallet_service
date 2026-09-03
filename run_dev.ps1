# Поиск файла .env
param([string]$EnvFile = ".env")

if (-not (Test-Path -Path $EnvFile -PathType Leaf)) {
    Write-Error "`nФайл переменных окружения ${EnvFile} не найден"
    exit 1
}

Write-Host "`n--------------------------------------------------" -ForegroundColor Cyan
Write-Host "Запуск Режима Разработки (volume + reload)..." -ForegroundColor Cyan
Write-Host "--------------------------------------------------" -ForegroundColor Cyan

# Читаем .env в словарь
$EnvVars = @{}
Get-Content $EnvFile | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith("#")) {
        $parts = $line -split "=", 2
        if ($parts.Count -eq 2) {
            $EnvVars[$parts[0]] = $parts[1]
        }
    }
}

# Распаковка словаря в переменные
$user = $EnvVars['POSTGRES_USER']
$dbName = $EnvVars['POSTGRES_DB']

# Шаг 1: Спрашиваем про миграции
Write-Host "`n[1] Вы хотите удалить все существующие миграции и создать новые? (Y/N): " -NoNewline -ForegroundColor Yellow
$delete = Read-Host

if ($delete -eq 'Y' -or $delete -eq 'y') {
    # Шаг 2: Очистка БД (пока контейнеры работают, если они запущены)
    Write-Host "`n[2] Очистка базы данных... " -NoNewline -ForegroundColor Green
    # Проверяем, запущен ли контейнер c базой данных
    $db_active = docker compose ps --filter "status=running" --services | Select-String "db"
    if ($db_active) {
        docker compose exec -T db psql -U ${user} -d ${dbName} -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" 2>&1 | Out-Null
        Write-Host "успешно завершена" -ForegroundColor Green
    } else {
        Write-Host
        Write-Host "    Контейнер с базой данных не запущен, очистка невозможна" -ForegroundColor Red
        Write-Host "    Все миграции будут сохранены" -ForegroundColor Red
        $delete = 'N'
    }
}

# Удаление старых контейнеров
Write-Host "`n[3] Удаление старых контейнеров" -ForegroundColor Green
docker compose down

if ($delete -eq 'Y' -or $delete -eq 'y') {
    # Удаление файлов миграций
    Write-Host "`n[4] Удаление всех файлов миграций... " -NoNewline -ForegroundColor Green
    Remove-Item -Path "alembic/versions/*.py" -Force
    Write-Host "успешно удалены" -ForegroundColor Green
} else {
    Write-Host "`n[4] Файлы миграций сохранены" -ForegroundColor Cyan
}

# Создание новых контейнеров
Write-Host "`n[5] Создание новых контейнеров" -ForegroundColor Green
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

# Пауза, чтобы контейнеры запустились
Start-Sleep -Seconds 3

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nНе удалось инициализировать базу данных, для исправления перезапустите скрипт`n" -ForegroundColor Red
    exit 1
}

# Создание новой миграции если старые удалены
if ($delete -eq 'Y' -or $delete -eq 'y') {
    Write-Host "`n[6]Создание первой миграции" -ForegroundColor Yellow
    docker compose exec web alembic revision --autogenerate -m "initial"
} else {
    $initial = Get-ChildItem -Path "alembic/versions" -Filter "*initial.py" -ErrorAction SilentlyContinue
    if ($initial.Count -gt 0) {
        Write-Host "`n[7] Найден файл первой миграции" -ForegroundColor Green
    } else {
        Write-Host "`n[7] Миграций не найдено!" -ForegroundColor Red
        exit 1
    }
}

# Применить миграции
docker compose exec web alembic upgrade head
Write-Host "`n[8] Миграции применены" -ForegroundColor Green

# Финальный вывод
Write-Host "`n--------------------------------------------------" -ForegroundColor Cyan
Write-Host "Swagger доступен по адресу: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Логи: docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f" -ForegroundColor Cyan
Write-Host "Остановка: docker compose down" -ForegroundColor Cyan
Write-Host "--------------------------------------------------" -ForegroundColor Cyan