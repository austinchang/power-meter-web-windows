@echo off

echo Power Meter Web Edition - Quick Install
echo ========================================

echo Step 1: Creating virtual environment...
python -m venv venv

echo Step 2: Activating environment...
call venv\Scripts\activate.bat

echo Step 3: Installing packages...
pip install -r requirements.txt

echo Step 4: Creating directories...
mkdir data\database 2>nul
mkdir data\logs 2>nul

echo Step 5: Copying config...
copy config\config_windows.py config.py 2>nul

echo Step 6: Setting up database...
python scripts\setup_database.py

echo.
echo Installation complete!
echo Run: start.bat
echo Visit: http://localhost:5001
echo.
pause