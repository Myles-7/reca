[CmdletBinding()]
param(
    [string]$EvidenceDirectory,
    [switch]$FullBackendTests
)

$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
$root = Split-Path -Parent $PSScriptRoot
$project = "reca_m0_acceptance"
$evidenceRoot = if ($EvidenceDirectory) {
    $EvidenceDirectory
} else {
    Join-Path ([System.IO.Path]::GetTempPath()) ("reca-m0-acceptance-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
}
$envFile = Join-Path $evidenceRoot "acceptance.env"
$results = [System.Collections.Generic.List[object]]::new()
$apiPort = 18000
$frontendPort = 15173
$playwrightPort = 15174
$minioPort = 19000

New-Item -ItemType Directory -Path $evidenceRoot -Force | Out-Null
$env:UV_PROJECT_ENVIRONMENT = Join-Path $evidenceRoot "uv-environment"

function Add-Result([string]$Name, [string]$Status, [int]$ExitCode, [string]$Log) {
    $results.Add([PSCustomObject]@{ Name = $Name; Status = $Status; ExitCode = $ExitCode; Log = $Log })
}

function Invoke-Step([string]$Name, [scriptblock]$Action) {
    $log = Join-Path $evidenceRoot ("{0}.log" -f ($Name -replace "[^A-Za-z0-9_.-]", "_"))
    try {
        & $Action *>&1 | Out-File -LiteralPath $log -Encoding utf8
        $exitCode = if ($LASTEXITCODE -is [int]) { $LASTEXITCODE } else { 0 }
        if ($exitCode -eq 0) { Add-Result $Name "PASS" 0 $log } else { Add-Result $Name "FAIL" $exitCode $log }
    }
    catch {
        $_ | Out-File -LiteralPath $log -Encoding utf8 -Append
        Add-Result $Name "FAIL" 1 $log
    }
}

function Add-NotRun([string]$Name, [string]$Reason) {
    $log = Join-Path $evidenceRoot ("{0}.log" -f ($Name -replace "[^A-Za-z0-9_.-]", "_"))
    $Reason | Out-File -LiteralPath $log -Encoding utf8
    Add-Result $Name "NOT_RUN" 0 $log
}

function Invoke-NodeAudit {
    $log = Join-Path $evidenceRoot "node-security-audit.log"
    & bun audit *>&1 | Out-File -LiteralPath $log -Encoding utf8
    $output = Get-Content -Raw -LiteralPath $log
    if ($LASTEXITCODE -eq 0) { Add-Result "node-security-audit" "PASS" 0 $log; return }
    if ($output -match "[0-9]+ vulnerabilities \([0-9]+ low\)" -and $output -notmatch "(?im)\b(critical|high|moderate)\b") {
        Add-Result "node-security-audit" "PASS_WITH_LOW_ADVISORY" $LASTEXITCODE $log
        return
    }
    Add-Result "node-security-audit" "FAIL" $LASTEXITCODE $log
}

$secretBytes = New-Object byte[] 48
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($secretBytes)
$rng.Dispose()
$secret = [Convert]::ToBase64String($secretBytes)
$postgresPassword = "pg_" + [guid]::NewGuid().ToString("N")
$minioPassword = "minio_" + [guid]::NewGuid().ToString("N")
$adminPassword = "admin_" + [guid]::NewGuid().ToString("N")
$minioBucket = "reca-m0-acceptance-" + [guid]::NewGuid().ToString("N").Substring(0, 12)
$configLines = @(
"PROJECT_NAME=RECA"
"ENVIRONMENT=test"
"DEMO_MODE=false"
"SECRET_KEY=$secret"
"FIRST_SUPERUSER=acceptance@example.com"
"FIRST_SUPERUSER_PASSWORD=$adminPassword"
"POSTGRES_DB=reca_acceptance"
"POSTGRES_USER=reca_acceptance"
"POSTGRES_PASSWORD=$postgresPassword"
"MINIO_ROOT_USER=reca-acceptance"
"MINIO_ROOT_PASSWORD=$minioPassword"
"MINIO_BUCKET=reca-acceptance"
"MINIO_PORT=$minioPort"
"MINIO_PUBLIC_ENDPOINT=http://127.0.0.1:$minioPort"
"MODEL_API_KEY="
"OPENALEX_API_KEY="
"API_PORT=$apiPort"
"FRONTEND_PORT=$frontendPort"
"VITE_API_URL=http://127.0.0.1:$apiPort"
"VITE_APP_ENV=test"
"VITE_DEMO_MODE=false"
"FRONTEND_HOST=http://127.0.0.1:$frontendPort"
"BACKEND_CORS_ORIGINS=[`"http://127.0.0.1:$frontendPort`"]"
)
$configLines | Set-Content -LiteralPath $envFile -Encoding utf8

$compose = @("compose", "--project-name", $project, "--env-file", $envFile)
Push-Location $root
try {
    # This cleanup is intentionally scoped to the dedicated acceptance project.
    & docker @compose down -v --remove-orphans *>$null

    Invoke-Step "git-status" { git status --short }
    Invoke-Step "tool-versions" { docker --version; docker compose version; python --version; bun --version; python -m uv --version }
    Invoke-Step "locked-inputs" { Get-FileHash pyproject.toml, uv.lock, package.json, bun.lock -Algorithm SHA256 }
    Invoke-Step "source-and-image-policy" {
        if (-not (Test-Path THIRD_PARTY_NOTICES.md) -or -not (Test-Path vendor/licenses/full-stack-fastapi-template-LICENSE.txt)) { throw "Required source or license record is missing" }
        $trackedSecretFiles = git ls-files | Where-Object { $_ -ne ".env.example" -and $_ -match "(^|/)\.env($|\.)|\.pem$|\.key$" }
        if ($trackedSecretFiles) { throw "Tracked secret-like file detected" }
        $policyMatches = git grep -n -E "image:[[:space:]]*[^[:space:]]+:latest|upstream-lab" -- docker-compose.yml backend frontend
        if ($LASTEXITCODE -gt 1) { throw "Policy scan could not run" }
        if ($policyMatches) { throw "Forbidden image tag or upstream path detected" }
        $global:LASTEXITCODE = 0
    }
    Invoke-Step "compose-config" { docker @compose config -q }
    Invoke-Step "build-images" { docker @compose build api worker frontend }
    $build = $results | Where-Object Name -eq "build-images" | Select-Object -Last 1
    if ($build.Status -eq "PASS") {
        # Bring up the database dependencies before migration so the acceptance
        # environment does not compete with GROBID, Vite, and Playwright for RAM.
        Invoke-Step "start-core-services" { docker @compose up -d postgres valkey minio }
        Invoke-Step "core-container-status" { docker @compose ps postgres valkey minio }
        Invoke-Step "migrate-empty-database" { docker @compose run --rm api alembic upgrade head }
        Invoke-Step "migrate-idempotently" { docker @compose run --rm api alembic upgrade head }
        Invoke-Step "start-services" { docker @compose up -d grobid api worker frontend }
        Invoke-Step "container-status" { docker @compose ps }
        Invoke-Step "api-live" { python scripts/wait_for_http.py "http://127.0.0.1:$apiPort/api/v1/health/live" --timeout 90 }
        Invoke-Step "pgvector" { docker @compose exec -T api python -m app.cli.pgvector_smoke }
        Invoke-Step "api-ready" { python scripts/wait_for_http.py "http://127.0.0.1:$apiPort/api/v1/health/ready" --timeout 90 }
        foreach ($endpoint in @("live", "ready", "dependencies")) { Invoke-Step "health-$endpoint" { Invoke-WebRequest -UseBasicParsing -TimeoutSec 10 "http://127.0.0.1:$apiPort/api/v1/health/$endpoint" | Select-Object -ExpandProperty Content; $global:LASTEXITCODE = 0 } }
        Invoke-Step "request-id" { $response = Invoke-WebRequest -UseBasicParsing -TimeoutSec 10 -Headers @{ "X-Request-ID" = "m0-acceptance-001" } "http://127.0.0.1:$apiPort/api/v1/health/live"; if ($response.Headers["X-Request-ID"] -ne "m0-acceptance-001") { throw "Request ID was not propagated" }; $global:LASTEXITCODE = 0 }
        Start-Sleep -Seconds 10
        Invoke-Step "worker-ping" { docker @compose exec -T worker celery -A app.core.celery:celery_app inspect ping }
        Invoke-Step "worker-registered" { docker @compose exec -T worker celery -A app.core.celery:celery_app inspect registered }
        Invoke-Step "worker-health-ping" { docker @compose exec -T api python -c "from app.workers.health import health_ping; result = health_ping.delay().get(timeout=15); assert result == {'status':'ok','service':'reca-worker'}" }
        Invoke-Step "minio-private-write-read" { docker @compose exec -T api python -m app.cli.minio_smoke --bucket $minioBucket --verify-anonymous-denial }
        Invoke-Step "frontend-home" { Invoke-WebRequest -UseBasicParsing -TimeoutSec 10 "http://127.0.0.1:$frontendPort/" | Select-Object -ExpandProperty StatusCode }
        Invoke-Step "frontend-system-status" { Invoke-WebRequest -UseBasicParsing -TimeoutSec 10 "http://127.0.0.1:$frontendPort/system-status" | Select-Object -ExpandProperty StatusCode }
        Invoke-Step "restart-services" { docker @compose restart; docker @compose ps }
        Invoke-Step "api-restart-recovery-1" { python scripts/wait_for_http.py "http://127.0.0.1:$apiPort/api/v1/health/live" --timeout 90; python scripts/wait_for_http.py "http://127.0.0.1:$apiPort/api/v1/health/ready" --timeout 90 }
        Invoke-Step "api-restart-recovery-2" { docker @compose restart api; python scripts/wait_for_http.py "http://127.0.0.1:$apiPort/api/v1/health/live" --timeout 90; python scripts/wait_for_http.py "http://127.0.0.1:$apiPort/api/v1/health/ready" --timeout 90 }
        Invoke-Step "persistence" { docker @compose exec -T api alembic current; docker @compose exec -T api python -c "from sqlalchemy import text; from app.core.db import engine; assert engine.connect().execute(text('SELECT 1')).scalar_one() == 1"; docker @compose exec -T api python -m app.cli.minio_smoke --bucket $minioBucket --verify-persistence --verify-anonymous-denial --cleanup }
        Invoke-Step "container-log-secret-scan" { $matches = docker @compose logs --no-color | Select-String -Pattern "(postgresql\+psycopg://[^\s]+:|Authorization: Bearer|BEGIN PRIVATE KEY)"; if ($matches) { throw "Sensitive log pattern detected" } }
        if ($FullBackendTests) {
            Invoke-Step "backend-database-tests" {
                docker @compose run --rm `
                    --volume "${root}/backend/tests:/app/backend/tests:ro" `
                    --volume "${root}/frontend/src/shared/environment.ts:/app/frontend/src/shared/environment.ts:ro" `
                    --volume "${root}/.env.example:/app/.env.example:ro" `
                    api pytest -q
            }
        }
    }
    else {
        foreach ($name in @("start-services", "container-status", "migrate-empty-database", "migrate-idempotently", "pgvector", "health-live", "health-ready", "health-dependencies", "request-id", "worker-ping", "worker-health-ping", "minio-private-write-read", "frontend-home", "frontend-system-status", "restart-services", "persistence", "container-log-secret-scan")) { Add-NotRun $name "Blocked because isolated image build failed; see build-images.log." }
        if ($FullBackendTests) { Add-NotRun "backend-database-tests" "Blocked because isolated image build failed; see build-images.log." }
    }
    Invoke-Step "backend-tests" { python -m uv run pytest backend/tests -m no_database }
    Invoke-Step "frontend-dependencies" { bun install --frozen-lockfile }
    Invoke-Step "frontend-tests" { bun run --cwd frontend format:check; bun run --cwd frontend lint; bun run --cwd frontend build }
    Invoke-Step "playwright-shell" {
        Push-Location frontend
        $previousCI = $env:CI
        $previousPlaywrightPort = $env:RECA_PLAYWRIGHT_PORT
        try {
            $env:CI = "1"
            $env:RECA_PLAYWRIGHT_PORT = "$playwrightPort"
            bunx playwright test -c playwright.shell.config.ts --reporter=list
        }
        finally {
            $env:CI = $previousCI
            $env:RECA_PLAYWRIGHT_PORT = $previousPlaywrightPort
            Pop-Location
        }
    }
    Invoke-Step "repository-secret-scan" { $secretMatches = git grep -n -E "BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|AKIA[0-9A-Z]{16}" -- . ":(exclude).env.example" ":(exclude)scripts/m0-acceptance.ps1"; if ($LASTEXITCODE -gt 1) { throw "Secret scan could not run" }; if ($secretMatches) { throw "Secret pattern detected" }; $global:LASTEXITCODE = 0 }
    Invoke-Step "python-security-audit" { python -m uv run pip-audit }
    Invoke-NodeAudit
    Invoke-Step "post-run-git-status" { $changes = git status --porcelain --untracked-files=no; if ($LASTEXITCODE -ne 0) { throw "Git status could not run" }; if ($changes) { throw "Clean-room changed tracked files: $changes" } }
}
finally {
    & docker @compose down -v --remove-orphans *>$null
    Remove-Item -LiteralPath $envFile -Force -ErrorAction SilentlyContinue
    Pop-Location
}

$results | Format-Table -AutoSize
$failed = @($results | Where-Object { $_.Status -eq "FAIL" }).Count
$exitCode = if ($failed -gt 0) { 1 } else { 0 }
$results | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $evidenceRoot "summary.json") -Encoding utf8
$exitCode | Set-Content -LiteralPath (Join-Path $evidenceRoot "exit-code.txt") -Encoding ascii
exit $exitCode
