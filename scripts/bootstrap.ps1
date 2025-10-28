# PowerShell bootstrap for Windows
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $root

if (-Not (Test-Path .venv)) {
    python -m venv .venv
}
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
if (Test-Path api\requirements.txt) {
    pip install -r api\requirements.txt
}

if (Test-Path frontend\package.json) {
    Push-Location frontend
    npm ci
    npm run build
    Pop-Location
}

docker-compose build --pull
docker-compose up -d
Write-Host "Bootstrap complete. Backend: http://localhost:8000 healthz, Frontend: http://localhost:8080"
