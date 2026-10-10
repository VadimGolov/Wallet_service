# Функция для запуска и проверки
function Inspect {
    param(
        [Parameter(Mandatory)][scriptblock]$Command,
        [Parameter(Mandatory)][string]$Message
    )
    & $Command
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n$Message (код $LASTEXITCODE)" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

# Проверяем наличие Docker
$docker = Get-Command docker -ErrorAction SilentlyContinue
if (-not $docker) {
    Write-Host "`nУстановите Docker Desktop или добавьте docker в переменную среды PATH." -ForegroundColor Red
    exit 1
}

Write-Host "`n--------------------------------------------------" -ForegroundColor Cyan
Write-Host "Запуск Режима Тестирования..." -ForegroundColor Cyan
Write-Host "--------------------------------------------------" -ForegroundColor Cyan

$seq_num = 1
$composeFile = "docker-compose.test.yml"

# 1. Проверяем контейнеры
$containers = docker compose -f $composeFile ps -q -a
if (-not $containers) {
    Write-Host "`n[$seq_num] Тестовые контейнеры не найдены" -ForegroundColor Yellow
    $rebuild = 'Y'
} else {
    Write-Host "`n[$seq_num] Тестовые контейнеры найдены" -ForegroundColor Green
    Write-Host "`nВы хотитите пересобрать тестовые контейнеры? (Y/N) " -NoNewline -ForegroundColor Yellow
    $rebuild = (Read-Host).Trim().ToUpper()
}

# 2. Пересборка
if ($rebuild -eq 'Y') {
    if ($containers) {
        $seq_num += 1
        Write-Host "`n[$seq_num] Удаляю старые контейнеры и volume..." -ForegroundColor Green
        Inspect -Command { docker compose -f $composeFile down -v --remove-orphans } `
                -Message "Ошибка при docker compose down"
    }
    $seq_num += 1
    Write-Host "`n[$seq_num] Собираю новые контейнеры..." -ForegroundColor Green
    Inspect -Command { docker compose -f $composeFile build } `
            -Message "Ошибка сборки контейнеров"
} else {
    $seq_num += 1
    Write-Host "`n[$seq_num] Использую существующие контейнеры..." -ForegroundColor Green
}

# 3. Поднимаем БД
$seq_num += 1
Write-Host "`n[$seq_num] Запускаю db_test..." -ForegroundColor Green
Inspect -Command { docker compose -f $composeFile up -d --wait db_test } `
        -Message "Не удалось запустить db_test"

# 4. Тесты
$seq_num += 1
Write-Host "`n--------------------------------------------------" -ForegroundColor Green
Write-Host "[$seq_num] Запускаю тесты" -ForegroundColor Green
Write-Host "--------------------------------------------------" -ForegroundColor Green
docker compose -f $composeFile run --rm test
$test_output = $LASTEXITCODE

docker compose -f $composeFile down

Write-Host "`n--------------------------------------------------" -ForegroundColor Cyan
if ($test_output -eq 0) {
    Write-Host "Все тесты успешно пройдены" -ForegroundColor Green
} else {
    Write-Host "Есть проваленные тесты!" -ForegroundColor Red
}
Write-Host "--------------------------------------------------" -ForegroundColor Cyan

exit $test_output