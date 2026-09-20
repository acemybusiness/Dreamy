$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Test-Path ".venv\Scripts\python.exe")) {
  Write-Host "Run INSTALL_WINDOWS.bat first."
  exit 1
}
$env:APP_DEBUG="1"
Start-Process "http://127.0.0.1:5055"
& ".venv\Scripts\python.exe" "server.py"
