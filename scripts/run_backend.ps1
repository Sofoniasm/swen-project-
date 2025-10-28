# PowerShell script to run the backend
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $root
Set-Location ..
if (-Not (Test-Path .venv)) {
    python -m venv .venv
}
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
if (Test-Path api\requirements.txt) {
    pip install -r api\requirements.txt
}
Write-Host "Starting backend on http://127.0.0.1:8000"
python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
