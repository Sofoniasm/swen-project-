# PowerShell helper to run simulator
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $root
Set-Location ..
. .\.venv\Scripts\Activate.ps1
python -m ai_engine.simulator --mode http --interval 5 --backend http://127.0.0.1:8000
