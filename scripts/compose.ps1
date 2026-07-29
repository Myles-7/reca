param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("config", "build", "up", "ps", "logs", "restart", "down")]
    [string]$Action
)

$root = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $root ".env"
if (-not (Test-Path -LiteralPath $envFile)) {
    $envFile = Join-Path $root ".env.example"
}

$composeArgs = @("compose", "--env-file", $envFile)
switch ($Action) {
    "config"  { $composeArgs += "config" }
    "build"   { $composeArgs += @("build", "--pull") }
    "up"      { $composeArgs += @("up", "-d", "--build") }
    "ps"      { $composeArgs += "ps" }
    "logs"    { $composeArgs += @("logs", "--no-color", "--tail", "100") }
    "restart" { $composeArgs += "restart" }
    "down"    { $composeArgs += "down" }
}

Push-Location $root
try {
    & docker @composeArgs
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
