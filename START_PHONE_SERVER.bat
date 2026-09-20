@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Run INSTALL_WINDOWS.bat first.
  pause
  exit /b 1
)

for /f "tokens=*" %%i in ('powershell -NoProfile -Command "$ip=(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -notlike '127.*' -and $_.PrefixOrigin -ne 'WellKnown'} | Sort-Object InterfaceMetric | Select-Object -First 1 -ExpandProperty IPAddress); Write-Output $ip"') do set LANIP=%%i

echo.
echo Dreamy SRL Phone Server
echo -----------------------
echo Keep this window open.
echo On your phone, while connected to the SAME Wi-Fi, open:
echo.
echo     http://%LANIP%:5055
echo.
echo If Windows asks about firewall access, allow Private networks.
echo.

set APP_DEBUG=0
.venv\Scripts\python.exe server.py
pause
