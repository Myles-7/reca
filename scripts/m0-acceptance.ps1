[CmdletBinding()]
param()

$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
$root = Split-Path -Parent $PSScriptRoot
$project = "reca_m0_acceptance"
$evidenceRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("reca-m0-acceptance-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
$envFile = Join-Path $evidenceRoot "acceptance.env"
$minioProbe = Join-Path $evidenceRoot "minio-private-probe.py"
$results = [System.Collections.Generic.List[object]]::new()
$apiPort = 18000
$frontendPort = 15173

New-Item -ItemType Directory -Path $evidenceRoot -Force | Out-Null

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

$secretBytes = New-Object byte[] 48
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($secretBytes)
$rng.Dispose()
$secret = [Convert]::ToBase64String($secretBytes)
$postgresPassword = "pg_" + [guid]::NewGuid().ToString("N")
$minioPassword = "minio_" + [guid]::NewGuid().ToString("N")
$adminPassword = "admin_" + [guid]::NewGuid().ToString("N")
$configLines = @(
"PROJECT_NAME=RECA"
"ENVIRONMENT=test"
"DEMO_MODE=false"
"SECRET_KEY=$secret"
"FIRST_SUPERUSER=acceptance@example.invalid"
"FIRST_SUPERUSER_PASSWORD=$adminPassword"
"POSTGRES_DB=reca_acceptance"
"POSTGRES_USER=reca_acceptance"
"POSTGRES_PASSWORD=$postgresPassword"
"MINIO_ROOT_USER=reca-acceptance"
"MINIO_ROOT_PASSWORD=$minioPassword"
"MINIO_BUCKET=reca-acceptance"
"MODEL_API_KEY="
"OPENALEX_API_KEY="
"API_PORT=$apiPort"
"FRONTEND_PORT=$frontendPort"
"VITE_API_URL=http://127.0.0.1:$apiPort"
"VITE_APP_ENV=test"
"VITE_DEMO_MODE=false"
)
$configLines | Set-Content -LiteralPath $envFile -Encoding utf8

@'
import datetime as dt
import hashlib
import hmac
import os
import urllib.request

endpoint = os.environ["MINIO_ENDPOINT"].rstrip("/")
access_key = os.environ["MINIO_ROOT_USER"]
secret_key = os.environ["MINIO_ROOT_PASSWORD"]
bucket = os.environ["MINIO_BUCKET"]
region = "us-east-1"

def request(method: str, path: str, body: bytes = b"") -> bytes:
    now = dt.datetime.now(dt.timezone.utc)
    stamp, day = now.strftime("%Y%m%dT%H%M%SZ"), now.strftime("%Y%m%d")
    payload_hash = hashlib.sha256(body).hexdigest()
    host = endpoint.removeprefix("http://").removeprefix("https://")
    headers = {"host": host, "x-amz-content-sha256": payload_hash, "x-amz-date": stamp}
    signed_headers = ";".join(headers)
    canonical_headers = "".join(f"{key}:{headers[key]}\\n" for key in headers)
    canonical_request = f"{method}\\n{path}\\n\\n{canonical_headers}\\n{signed_headers}\\n{payload_hash}"
    scope = f"{day}/{region}/s3/aws4_request"
    signing_key = hmac.new(("AWS4" + secret_key).encode(), day.encode(), hashlib.sha256).digest()
    for component in (region, "s3", "aws4_request"):
        signing_key = hmac.new(signing_key, component.encode(), hashlib.sha256).digest()
    signature = hmac.new(signing_key, f"AWS4-HMAC-SHA256\\n{stamp}\\n{scope}\\n{hashlib.sha256(canonical_request.encode()).hexdigest()}".encode(), hashlib.sha256).hexdigest()
    headers["Authorization"] = f"AWS4-HMAC-SHA256 Credential={access_key}/{scope}, SignedHeaders={signed_headers}, Signature={signature}"
    with urllib.request.urlopen(urllib.request.Request(endpoint + path, data=body or None, method=method, headers=headers), timeout=10) as response:
        return response.read()

request("PUT", f"/{bucket}")
payload = b"reca-m0-acceptance-private-object"
request("PUT", f"/{bucket}/m0-acceptance.txt", payload)
assert request("GET", f"/{bucket}/m0-acceptance.txt") == payload
'@ | Set-Content -LiteralPath $minioProbe -Encoding utf8

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
        Invoke-Step "start-services" { docker @compose up -d postgres valkey minio grobid api worker frontend }
        Invoke-Step "container-status" { docker @compose ps }
        Invoke-Step "migrate-empty-database" { docker @compose exec -T api alembic upgrade head }
        Invoke-Step "migrate-idempotently" { docker @compose exec -T api alembic upgrade head }
        Invoke-Step "pgvector" { docker @compose exec -T api python -c "from sqlalchemy import text; from app.core.db import engine; assert engine.connect().execute(text(\"SELECT 1 FROM pg_extension WHERE extname = 'vector'\")).scalar_one() == 1" }
        foreach ($endpoint in @("live", "ready", "dependencies")) { Invoke-Step "health-$endpoint" { Invoke-WebRequest -UseBasicParsing -TimeoutSec 10 "http://127.0.0.1:$apiPort/api/v1/health/$endpoint" | Select-Object -ExpandProperty Content } }
        Invoke-Step "request-id" { $response = Invoke-WebRequest -UseBasicParsing -TimeoutSec 10 -Headers @{ "X-Request-ID" = "m0-acceptance-001" } "http://127.0.0.1:$apiPort/api/v1/health/live"; if ($response.Headers["X-Request-ID"] -ne "m0-acceptance-001") { throw "Request ID was not propagated" } }
        Invoke-Step "worker-ping" { docker @compose exec -T worker celery -A app.core.celery:celery_app inspect ping }
        Invoke-Step "worker-health-ping" { docker @compose exec -T api python -c "from app.workers.health import health_ping; result = health_ping.delay().get(timeout=15); assert result == {'status':'ok','service':'reca-worker'}" }
        Invoke-Step "minio-private-write-read" { Get-Content -Raw -LiteralPath $minioProbe | & docker @compose exec -T api python - }
        Invoke-Step "frontend-home" { Invoke-WebRequest -UseBasicParsing -TimeoutSec 10 "http://127.0.0.1:$frontendPort/" | Select-Object -ExpandProperty StatusCode }
        Invoke-Step "frontend-system-status" { Invoke-WebRequest -UseBasicParsing -TimeoutSec 10 "http://127.0.0.1:$frontendPort/system-status" | Select-Object -ExpandProperty StatusCode }
        Invoke-Step "restart-services" { docker @compose restart; Start-Sleep -Seconds 10; docker @compose ps }
        Invoke-Step "persistence" { docker @compose exec -T api alembic current; docker @compose exec -T api python -c "from sqlalchemy import text; from app.core.db import engine; assert engine.connect().execute(text('SELECT 1')).scalar_one() == 1" }
        Invoke-Step "container-log-secret-scan" { $matches = docker @compose logs --no-color | Select-String -Pattern "(postgresql\+psycopg://[^\s]+:|Authorization: Bearer|BEGIN PRIVATE KEY)"; if ($matches) { throw "Sensitive log pattern detected" } }
    }
    else {
        foreach ($name in @("start-services", "container-status", "migrate-empty-database", "migrate-idempotently", "pgvector", "health-live", "health-ready", "health-dependencies", "request-id", "worker-ping", "worker-health-ping", "minio-private-write-read", "frontend-home", "frontend-system-status", "restart-services", "persistence", "container-log-secret-scan")) { Add-NotRun $name "Blocked because isolated image build failed; see build-images.log." }
    }
    Invoke-Step "backend-tests" { python -m uv run pytest backend/tests -m no_database }
    Invoke-Step "frontend-tests" { bun run --cwd frontend format:check; bun run --cwd frontend lint; bun run --cwd frontend build }
    Invoke-Step "playwright-shell" { Push-Location frontend; try { bunx playwright test -c playwright.shell.config.ts --reporter=list } finally { Pop-Location } }
    Invoke-Step "repository-secret-scan" { $secretMatches = git grep -n -E "BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|AKIA[0-9A-Z]{16}" -- . ":(exclude).env.example"; if ($LASTEXITCODE -gt 1) { throw "Secret scan could not run" }; if ($secretMatches) { throw "Secret pattern detected" }; $global:LASTEXITCODE = 0 }
    Invoke-Step "python-security-audit" { python -m uv run pip-audit }
    Invoke-Step "node-security-audit" { bun audit }
}
finally {
    & docker @compose down -v --remove-orphans *>$null
    Remove-Item -LiteralPath $envFile -Force -ErrorAction SilentlyContinue
    Pop-Location
}

$results | Format-Table -AutoSize
$failed = @($results | Where-Object { $_.Status -eq "FAIL" }).Count
if ($failed -gt 0) { exit 1 }
