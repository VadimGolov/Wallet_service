param([string]$EnvFile = "..\.testenv")

if (-not (Test-Path -Path $EnvFile -PathType Leaf)) {
    Write-Error "Файл переменных окружения ${EnvFile} не найден"
    exit 1
}

# Читаем .testenv в словарь
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

$user = $EnvVars['POSTGRES_USER']
$password = $EnvVars['POSTGRES_PASSWORD']
$dbName = $EnvVars['POSTGRES_DB']

Write-Host "=== Подготовка тестовой БД: ${dbName} ===" -ForegroundColor Cyan

# 1. Создать БД через суперпользователя postgres
Write-Host "[1/3] Создаём базу данных..." -ForegroundColor Yellow
docker compose exec db psql -U postgres -c "CREATE DATABASE ${dbName} OWNER ${user};"

if ($LASTEXITCODE -ne 0) {Write-Warning "База могла уже существовать — продолжаем."}

# 2. Применить миграции Alembic к тестовой БД
Write-Host "[2/3] Применяем миграции (alembic upgrade head)..." -ForegroundColor Yellow
$test_db = "postgresql+psycopg://${user}:${password}@db/${dbName}"
docker compose exec web env DATABASE_URL="${test_db}" alembic upgrade head

if ($LASTEXITCODE -ne 0) {throw "Миграции не применились. Проверьте логи."}

# 3. (Опционально) Копируем миграции np контейнера
Write-Host "[3/3] Копируем файлы миграций из контейнера..." -ForegroundColor Yellow

# Получаем список файлов .py в контейнере
$ContainerFiles = docker compose exec -T web ls /app/alembic/versions/*.py 2>$null

if ($ContainerFiles) {foreach ($File in $ContainerFiles) {
        # Извлекаем только имя файла (например, ca9c...py)
        $file_name = Split-Path $File -Leaf
        $dest_path = Join-Path $localVersionsPath $file_name

        # Копируем, если файла ещё нет локально или он отличается (простая проверка)
        if (-not (Test-Path $dest_path)) {
            Write-Host "  -> Копирую: ${file_name}" -ForegroundColor Green
            docker cp web:/app/alembic/versions/$fileName $dest_path
        } else {
            Write-Host "  -> Уже есть локально: ${file_name} (пропущено)" -ForegroundColor Gray
        }
    }
    Write-Host "Файлы миграций синхронизированы с проектом." -ForegroundColor Green
} else {
    Write-Warning "Не найдено файлов .py в /app/alembic/versions внутри контейнера."
}

Write-Host "=== Готово: БД создана, миграции применены, файлы скопированы в проект ===" -ForegroundColor Green























docker compose cp web:/app/alembic/versions/ca9c2db997c9_initial.py D:\Storage\Zerocoder\ZeroPro\wallet_service\alembic\versions\


Write-Host "=== Готово: тестовая БД '$dbName' создана и миграции применены ===" -ForegroundColor Green