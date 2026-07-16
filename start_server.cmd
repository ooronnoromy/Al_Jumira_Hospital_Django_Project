@echo off
setlocal
cd /d "%~dp0"

set "PROJECT_PYTHON=%CD%\.venv\Scripts\python.exe"

rem Find the active adapter's IPv4 address so Django accepts requests from
rem other devices even if the router assigns this computer a new address.
set "LAN_IP="
for /f "tokens=4" %%I in ('route print -4 ^| findstr /R /C:"^[ ]*0.0.0.0[ ]*0.0.0.0"') do if not defined LAN_IP set "LAN_IP=%%I"

if not defined LAN_IP (
    echo WARNING: Could not detect an active local network address.
    echo The server will start, but only the local address is guaranteed.
    set "LAN_IP=127.0.0.1"
)

set "DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,%LAN_IP%"

if not exist "%PROJECT_PYTHON%" (
    echo ERROR: The project virtual environment was not found.
    echo Create it with: python -m venv .venv
    echo Then install dependencies with: .venv\Scripts\python.exe -m pip install -r requirements.txt
    exit /b 1
)

echo Checking Django and the local PostgreSQL connection...
"%PROJECT_PYTHON%" manage.py check --database default
if errorlevel 1 goto database_error

echo Applying pending database migrations...
"%PROJECT_PYTHON%" manage.py migrate --noinput
if errorlevel 1 goto database_error

netstat -ano | findstr /R /C:":8000 .*LISTENING" >nul
if not errorlevel 1 (
    echo.
    echo ERROR: Another server is already using port 8000.
    echo Stop the existing server with Ctrl+C before starting another copy.
    exit /b 1
)

echo Starting Hospital Management System...
echo.
echo On this computer: http://127.0.0.1:8000/
echo On phones and other Wi-Fi devices: http://%LAN_IP%:8000/
echo.
echo Keep this window open while using the system.
"%PROJECT_PYTHON%" manage.py runserver 0.0.0.0:8000
exit /b %errorlevel%

:database_error
echo.
echo ERROR: Django could not connect to or prepare PostgreSQL.
echo Check POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER,
echo and POSTGRES_PASSWORD in the .env file, then try again.
exit /b 1
