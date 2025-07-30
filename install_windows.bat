@echo off
chcp 65001 >nul
color 0A
title Power Meter Web Edition - Install

echo ================================================
echo   Power Meter Web Edition - Windows Install
echo   Professional Power Meter Monitoring System
echo ================================================
echo.

REM Check Administrator privileges
net session >nul 2>&1
if not %errorLevel% == 0 (
    echo [WARNING] Please run as Administrator for best results
    echo.
)

REM Check Python installation
echo [CHECK] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.8+ is required!
    echo.
    echo Please download and install Python from:
    echo https://www.python.org/downloads/
    echo.
    echo Remember to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

REM Display Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [SUCCESS] Found Python %PYTHON_VERSION%

REM Check pip
echo [CHECK] Checking pip installation...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is not properly installed!
    pause
    exit /b 1
)
echo [SUCCESS] pip is installed

echo.
echo [1/7] Creating virtual environment...
if exist venv (
    echo [INFO] Virtual environment already exists, skipping
) else (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created
)

echo.
echo [2/7] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment!
    pause
    exit /b 1
)
echo [SUCCESS] Virtual environment activated

echo.
echo [3/7] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo [SUCCESS] pip upgraded to latest version

echo.
echo [4/7] Installing required packages...
echo [INFO] Installing packages, please wait...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Package installation failed!
    echo [SUGGESTION] Check network connection or use China mirror:
    echo pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
    pause
    exit /b 1
)
echo [SUCCESS] All packages installed successfully

echo.
echo [5/7] Creating necessary directories...
mkdir data\database 2>nul
mkdir data\logs 2>nul
mkdir data\uploads 2>nul
mkdir data\config 2>nul
echo [SUCCESS] Directory structure created

echo.
echo [6/7] Copying configuration files...
if exist config\config_windows.py (
    copy config\config_windows.py config.py >nul 2>&1
    echo [SUCCESS] Windows configuration copied
) else (
    echo [WARNING] Windows config not found, using defaults
)

if exist config\modbus_config.json (
    copy config\modbus_config.json data\config\ >nul 2>&1
    echo [SUCCESS] MODBUS configuration copied
)

echo.
echo [7/7] Initializing database...
python scripts\setup_database.py >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Database initialization may have issues, will auto-create on first run
) else (
    echo [SUCCESS] Database initialized successfully
)

echo.
echo ================================================
echo   🎉 Installation Complete!
echo ================================================
echo.
echo Next steps:
echo 1. Connect your MODBUS RTU meter to COM port
echo 2. Edit config\modbus_config.json for your device
echo 3. Run scripts\test_modbus.py to test connection
echo 4. Run start.bat to start the system
echo 5. Open browser and visit http://localhost:5001
echo.
echo Default settings:
echo - COM Port: COM1
echo - MODBUS Address: 2 (maps to Web Meter ID 1)
echo - Baudrate: 9600-N-8-1
echo.
echo ================================================
echo   Need help? Check README.md for full guide
echo ================================================
echo.
pause