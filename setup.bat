@echo off
setlocal

echo Creating virtual environment...
py -m venv .venv

if errorlevel 1 (
    echo Failed to create the virtual environment.
    exit /b 1
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Updating pip...
python -m pip install --upgrade pip

if errorlevel 1 (
    echo Failed to update pip.
    exit /b 1
)

echo Installing Python dependencies...
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo Failed to install Python dependencies.
    exit /b 1
)

echo Installing Chromium for Playwright...
python -m playwright install chromium

if errorlevel 1 (
    echo Failed to install Chromium.
    exit /b 1
)

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo Created .env from .env.example.
)

echo.
echo Installation completed successfully.
echo Edit the .env file before running the monitor.
echo.

endlocal
pause
