@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Run INSTALL_WINDOWS.bat first.
  pause
  exit /b 1
)
set APP_DEBUG=1
start "Dreamy DoubleStack SRL Server" cmd /k ""%~dp0.venv\Scripts\python.exe" "%~dp0server.py""
echo Waiting for local app server...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ok=$false; for($i=0;$i -lt 40;$i++){try{$r=Invoke-WebRequest -UseBasicParsing http://127.0.0.1:5055/api/ping -TimeoutSec 1;if($r.StatusCode -eq 200){$ok=$true;break}}catch{};Start-Sleep -Milliseconds 500}; if(-not $ok){exit 1}"
if errorlevel 1 (
  echo The local app server did not start. Check the server window for the error.
  pause
  exit /b 1
)
start "" http://127.0.0.1:5055
exit
