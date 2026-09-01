# Ïîèñê ôàéëà .env
param([string]$EnvFile = ".env")

if (-not (Test-Path -Path $EnvFile -PathType Leaf)) {
    Write-Error "`nÔàéë ïåðåìåííûõ îêðóæåíèÿ ${EnvFile} íå íàéäåí"
    exit 1
}

Write-Host "`n--------------------------------------------------" -ForegroundColor Cyan
Write-Host "Çàïóñê Ðåæèìà Ðàçðàáîòêè (volume + reload)..." -ForegroundColor Cyan
Write-Host "--------------------------------------------------" -ForegroundColor Cyan

# ×èòàåì .env â ñëîâàðü
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

# Ðàñïàêîâêà ñëîâàðÿ â ïåðåìåííûå
$user = $EnvVars['POSTGRES_USER']
$dbName = $EnvVars['POSTGRES_DB']

# Øàã 1: Ñïðàøèâàåì ïðî ìèãðàöèè
Write-Host "`n[1] Âû õîòèòå óäàëèòü âñå ñóùåñòâóþùèå ìèãðàöèè è ñîçäàòü íîâûå? (Y/N): " -NoNewline -ForegroundColor Yellow
$delete = Read-Host

if ($delete -eq 'Y' -or $delete -eq 'y') {
    # Øàã 2: Î÷èñòêà ÁÄ (ïîêà êîíòåéíåðû ðàáîòàþò, åñëè îíè çàïóùåíû)
    Write-Host "`n[2] Î÷èñòêà áàçû äàííûõ" -ForegroundColor Green
    # Ïðîâåðÿåì, çàïóùåí ëè êîíòåéíåð c áàçîé äàííûõ
    $is_active = docker compose ps --filter "status=running" --services | Select-String "db"
    if ($is_active) {
        docker compose exec -T db psql -U ${user} -d ${dbName} -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" 2>$null
    } else {
        Write-Host "`nÊîíòåéíåð ñ áàçîé äàííûõ íå çàïóùåí, î÷èñòêà íåâîçìîæíà" -ForegroundColor Red
        exit 1
    }
}
# Óäàëåíèå ñòàðûõ êîíòåéíåðîâ

Write-Host "[3] Óäàëåíèå ñòàðûõ êîíòåéíåðîâ" -ForegroundColor Green
docker compose down

if ($delete -eq 'Y' -or $delete -eq 'y') {
    # Óäàëåíèå ôàéëîâ ìèãðàöèé
    Write-Host "`n[4] Óäàëåíèå âñåõ ôàéëîâ ìèãðàöèé" -ForegroundColor Green
    Remove-Item -Path "alembic/versions/*.py" -Force
} else {
    Write-Host "`n[5] Ôàéëû ìèãðàöèé ñîõðàíåíû" -ForegroundColor Cyan
}

# Ñîçäàíèå íîâûõ êîíòåéíåðîâ
Write-Host "`n[6] Ñîçäàíèå íîâûõ êîíòåéíåðîâ" -ForegroundColor Green
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

# Ïàóçà, ÷òîáû êîíòåéíåðû çàïóñòèëèñü
Start-Sleep -Seconds 3

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nÍå óäàëîñü èíèöèàëèçèðîâàòü áàçó äàííûõ, äëÿ èñïðàâëåíèÿ ïåðåçàïóñòèòå ñêðèïò`n" -ForegroundColor Red
    exit 1
}

# Ñîçäàíèå íîâîé ìèãðàöèè åñëè ñòàðûå óäàëåíû
if ($delete -eq 'Y' -or $delete -eq 'y') {
    Write-Host "`n[7]Ñîçäàíèå ïåðâîé ìèãðàöèè" -ForegroundColor Yellow
    docker compose exec web alembic revision --autogenerate -m "initial"
} else {
    $initial = Get-ChildItem -Path "alembic/versions" -Filter "*initial.py" -ErrorAction SilentlyContinue
    if ($initial.Count -gt 0) {
        Write-Host "[8] Íàéäåí ôàéë ïåðâîé ìèãðàöèè" -ForegroundColor Green
    } else {
        Write-Host "[8] Ìèãðàöèé íå íàéäåíî!" -ForegroundColor Red
        exit 1
    }
}

# Ïðèìåíèòü ìèãðàöèè
docker compose exec web alembic upgrade head
Write-Host "`n[9] Ìèãðàöèè ïðèìåíåíû" -ForegroundColor Green

# Ôèíàëüíûé âûâîä
Write-Host "`n--------------------------------------------------" -ForegroundColor Cyan
Write-Host "Swagger äîñòóïåí ïî àäðåñó: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Ëîãè: docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f" -ForegroundColor Cyan
Write-Host "Îñòàíîâêà: docker compose down" -ForegroundColor Cyan
Write-Host "--------------------------------------------------" -ForegroundColor Cyan
