[CmdletBinding()]
param(
    [string]$EvidenceDirectory
)

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$root = Split-Path -Parent $PSScriptRoot
$project = "reca_m7_real_gate"
$evidenceRoot = if ($EvidenceDirectory) {
    $EvidenceDirectory
} else {
    Join-Path ([System.IO.Path]::GetTempPath()) ("reca-m7-real-browser-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
}
$envFile = Join-Path $evidenceRoot "acceptance.env"
$logFile = Join-Path $evidenceRoot "playwright.log"
$composeLogFile = Join-Path $evidenceRoot "compose.log"
$apiPort = 18050
$frontendPort = 15180
$minioPort = 19000

New-Item -ItemType Directory -Path $evidenceRoot -Force | Out-Null

$secretBytes = New-Object byte[] 48
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($secretBytes)
$rng.Dispose()
$secret = [Convert]::ToBase64String($secretBytes)
$postgresPassword = "pg_" + [guid]::NewGuid().ToString("N")
$minioPassword = "minio_" + [guid]::NewGuid().ToString("N")
$adminPassword = "admin_" + [guid]::NewGuid().ToString("N")
$adminEmail = "m7-real-gate@example.com"

@(
    "PROJECT_NAME=RECA"
    "ENVIRONMENT=test"
    "DEMO_MODE=false"
    "SECRET_KEY=$secret"
    "FIRST_SUPERUSER=$adminEmail"
    "FIRST_SUPERUSER_PASSWORD=$adminPassword"
    "POSTGRES_DB=reca_m7_real_gate"
    "POSTGRES_USER=reca_m7_real_gate"
    "POSTGRES_PASSWORD=$postgresPassword"
    "MINIO_ROOT_USER=reca-m7-real-gate"
    "MINIO_ROOT_PASSWORD=$minioPassword"
    "MINIO_BUCKET=reca-m7-real-gate"
    "MINIO_PORT=$minioPort"
    "MINIO_PUBLIC_ENDPOINT=http://127.0.0.1:$minioPort"
    "API_PORT=$apiPort"
    "FRONTEND_PORT=$frontendPort"
    "VITE_API_URL=http://127.0.0.1:$apiPort"
    "VITE_APP_ENV=test"
    "VITE_DEMO_MODE=false"
    "FRONTEND_HOST=http://127.0.0.1:$frontendPort"
    "BACKEND_CORS_ORIGINS=[`"http://127.0.0.1:$frontendPort`"]"
    "MODEL_API_KEY="
    "OPENALEX_API_KEY="
) | Set-Content -LiteralPath $envFile -Encoding utf8

$compose = @("compose", "--project-name", $project, "--env-file", $envFile)

function Wait-Http([string]$Url, [int]$TimeoutSeconds = 120) {
    & python scripts/wait_for_http.py $Url --timeout $TimeoutSeconds
    if ($LASTEXITCODE -ne 0) { throw "Timed out waiting for $Url" }
}

function Remove-AcceptanceProject {
    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        & docker @compose down -v --remove-orphans *> $null
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
}

Push-Location $root
try {
    # Cleanup is intentionally limited to this dedicated acceptance project.
    Remove-AcceptanceProject
    & docker @compose config -q
    & docker @compose build api worker frontend
    & docker @compose up -d postgres valkey minio
    & docker @compose ps postgres valkey minio
    Wait-Http "http://127.0.0.1:$minioPort/minio/health/live" 20
    & docker @compose run --rm api alembic upgrade head
    & docker @compose run --rm `
        --volume "${root}/backend/tests:/app/backend/tests:ro" `
        --volume "${root}/tests/golden:/app/tests/golden:ro" `
        api pytest -q tests/exports/test_service.py::test_readiness_persists_uuid_issue_references_as_json_values
    & docker @compose run --rm api python app/initial_data.py
    & docker @compose up -d api worker frontend
    Wait-Http "http://127.0.0.1:$apiPort/api/v1/health/live"
    Wait-Http "http://127.0.0.1:$frontendPort/"
    Wait-Http "http://127.0.0.1:$minioPort/minio/health/live"
    & docker @compose ps | Out-File -LiteralPath (Join-Path $evidenceRoot "compose-ps.log") -Encoding utf8

    $login = Invoke-RestMethod `
        -Method Post `
        -Uri "http://127.0.0.1:$apiPort/api/v1/login/access-token" `
        -ContentType "application/x-www-form-urlencoded" `
        -Body @{ username = $adminEmail; password = $adminPassword }
    $token = $login.access_token
    if (-not $token) { throw "The isolated login did not return an access token." }
    $headers = @{
        Authorization = "Bearer $token"
        "Idempotency-Key" = [guid]::NewGuid().ToString()
    }
    $projectEnvelope = Invoke-RestMethod `
        -Method Post `
        -Uri "http://127.0.0.1:$apiPort/api/v1/projects" `
        -Headers $headers `
        -ContentType "application/json" `
        -Body (@{
            name = "M7 real browser acceptance"
            project_type = "RESEARCH"
            current_stage = "MANUSCRIPT"
        } | ConvertTo-Json)
    $projectId = $projectEnvelope.data.id
    if (-not $projectId) { throw "The isolated Project API did not return an ID." }

    $seedScript = @'
import hashlib
import os
import uuid

from sqlmodel import Session, select

from app.core.db import engine
from app.models import (
    AuditActorType,
    Claim,
    ClaimConfidence,
    ClaimStatus,
    ClaimType,
    User,
)

project_id = uuid.UUID(os.environ["RECA_SEED_PROJECT_ID"])
claim_text = "The isolated M7 export path remains traceable to an authoritative Claim."
source_id = uuid.uuid4()
with Session(engine) as session:
    actor = session.exec(select(User).where(User.email == os.environ["FIRST_SUPERUSER"])).one()
    claim = Claim(
        project_id=project_id,
        claim_type=ClaimType.MANUSCRIPT_STATEMENT,
        claim_text=claim_text,
        normalized_claim=claim_text,
        scope_statement="Stage-5 isolated real API browser acceptance.",
        source_object_type="manuscript_version",
        source_object_id=source_id,
        source_location={"section": "acceptance"},
        source_hash=hashlib.sha256(str(source_id).encode()).hexdigest(),
        text_hash=hashlib.sha256(claim_text.encode()).hexdigest(),
        status=ClaimStatus.NEEDS_EVIDENCE,
        confidence=ClaimConfidence.UNKNOWN,
        created_by_actor_type=AuditActorType.USER,
        created_by_actor_id=str(actor.id),
    )
    session.add(claim)
    session.commit()
    session.refresh(claim)
    print(claim.id)
'@
    $claimId = $seedScript | docker @compose exec -T -e "RECA_SEED_PROJECT_ID=$projectId" api python -
    if ($LASTEXITCODE -ne 0 -or -not $claimId) { throw "The isolated Claim seed failed." }
    $claimId = $claimId.Trim()

    Push-Location frontend
    try {
        $env:RECA_M7_REAL_FRONTEND_URL = "http://127.0.0.1:$frontendPort"
        $env:RECA_M7_REAL_API_URL = "http://127.0.0.1:$apiPort"
        $env:RECA_M7_REAL_PROJECT_ID = $projectId
        $env:RECA_M7_REAL_CLAIM_ID = $claimId
        $env:RECA_M7_REAL_ACCESS_TOKEN = $token
        $env:CI = "1"
        & bunx playwright test -c playwright.m7-real.config.ts --reporter=list *>&1 |
            Tee-Object -FilePath $logFile
        if ($LASTEXITCODE -ne 0) { throw "Real M7 browser acceptance failed; see $logFile" }
    }
    finally {
        Remove-Item Env:RECA_M7_REAL_FRONTEND_URL -ErrorAction SilentlyContinue
        Remove-Item Env:RECA_M7_REAL_API_URL -ErrorAction SilentlyContinue
        Remove-Item Env:RECA_M7_REAL_PROJECT_ID -ErrorAction SilentlyContinue
        Remove-Item Env:RECA_M7_REAL_CLAIM_ID -ErrorAction SilentlyContinue
        Remove-Item Env:RECA_M7_REAL_ACCESS_TOKEN -ErrorAction SilentlyContinue
        Pop-Location
    }

    Write-Output "M7_REAL_BROWSER_ACCEPTANCE=PASS"
    Write-Output "EVIDENCE_DIRECTORY=$evidenceRoot"
}
finally {
    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        & docker @compose logs --no-color *> $composeLogFile
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    Remove-AcceptanceProject
    Remove-Item -LiteralPath $envFile -Force -ErrorAction SilentlyContinue
    Pop-Location
}
