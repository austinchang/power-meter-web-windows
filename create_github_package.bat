@echo off
chcp 65001 >nul
cls
color 0E
title Power Meter Web Edition - GitHub 打包工具

echo ====================================================
echo   Power Meter Web Edition - GitHub 打包工具
echo   準備上傳到 GitHub 的完整專案包
echo ====================================================
echo.

REM 檢查必要檔案
echo [檢查] 驗證專案檔案完整性...
set "missing_files="

if not exist "README.md" set "missing_files=%missing_files% README.md"
if not exist "requirements.txt" set "missing_files=%missing_files% requirements.txt"
if not exist "install.bat" set "missing_files=%missing_files% install.bat"
if not exist "start.bat" set "missing_files=%missing_files% start.bat"
if not exist "run_windows.py" set "missing_files=%missing_files% run_windows.py"
if not exist "LICENSE" set "missing_files=%missing_files% LICENSE"
if not exist "backend\" set "missing_files=%missing_files% backend/"
if not exist "frontend\" set "missing_files=%missing_files% frontend/"
if not exist "config\" set "missing_files=%missing_files% config/"
if not exist "scripts\" set "missing_files=%missing_files% scripts/"

if not "%missing_files%"=="" (
    echo [錯誤] 缺少必要檔案：%missing_files%
    echo [解決] 請確認專案檔案完整
    pause
    exit /b 1
)

echo [成功] 所有必要檔案存在
echo.

REM 建立 .gitignore 檔案
echo [建立] 建立 .gitignore 檔案...
(
echo # Power Meter Web Edition - .gitignore
echo.
echo # Python
echo __pycache__/
echo *.py[cod]
echo *$py.class
echo *.so
echo.
echo # Distribution / packaging
echo .Python
echo build/
echo develop-eggs/
echo dist/
echo downloads/
echo eggs/
echo .eggs/
echo lib/
echo lib64/
echo parts/
echo sdist/
echo var/
echo wheels/
echo *.egg-info/
echo .installed.cfg
echo *.egg
echo.
echo # Virtual environments
echo venv/
echo env/
echo ENV/
echo.
echo # Database
echo *.db
echo *.sqlite3
echo data/database/
echo.
echo # Logs
echo *.log
echo data/logs/
echo.
echo # Runtime config
echo data/config/
echo.
echo # Windows
echo Thumbs.db
echo ehthumbs.db
echo Desktop.ini
echo.
echo # IDE
echo .vscode/
echo .idea/
echo *.swp
echo *.swo
echo.
echo # Temporary files
echo *.tmp
echo *.temp
echo.
echo # System files
echo .DS_Store
echo .DS_Store?
echo ._*
echo .Spotlight-V100
echo .Trashes
) > .gitignore

echo [成功] .gitignore 檔案已建立
echo.

REM 建立 GitHub 工作流程
echo [建立] 建立 GitHub Actions 工作流程...
mkdir .github\workflows 2>nul
(
echo name: Power Meter Web Edition CI
echo.
echo on:
echo   push:
echo     branches: [ main ]
echo   pull_request:
echo     branches: [ main ]
echo.
echo jobs:
echo   test:
echo     runs-on: windows-latest
echo     
echo     steps:
echo     - uses: actions/checkout@v3
echo     
echo     - name: Set up Python
echo       uses: actions/setup-python@v3
echo       with:
echo         python-version: '3.8'
echo     
echo     - name: Install dependencies
echo       run: |
echo         python -m pip install --upgrade pip
echo         pip install -r requirements.txt
echo     
echo     - name: Test installation
echo       run: |
echo         python -c "import flask, socketio, minimalmodbus; print('All dependencies OK')"
echo     
echo     - name: Check database setup
echo       run: |
echo         python scripts/setup_database.py test
) > .github\workflows\ci.yml

echo [成功] GitHub Actions 工作流程已建立
echo.

REM 建立專案統計
echo [統計] 計算專案檔案統計...
set "file_count=0"
set "dir_count=0"

for /f %%i in ('dir /s /b *.py ^| find /c /v ""') do set "py_files=%%i"
for /f %%i in ('dir /s /b *.html ^| find /c /v ""') do set "html_files=%%i"
for /f %%i in ('dir /s /b *.js ^| find /c /v ""') do set "js_files=%%i"
for /f %%i in ('dir /s /b *.css ^| find /c /v ""') do set "css_files=%%i"
for /f %%i in ('dir /s /b *.bat ^| find /c /v ""') do set "bat_files=%%i"

echo.
echo ====================================================
echo   專案統計
echo ====================================================
echo Python 檔案: %py_files% 個
echo HTML 模板: %html_files% 個  
echo JavaScript: %js_files% 個
echo CSS 樣式: %css_files% 個
echo 批次檔案: %bat_files% 個
echo.

REM 建立版本資訊檔案
echo [建立] 建立版本資訊檔案...
(
echo {
echo   "name": "power-meter-web-windows",
echo   "version": "1.0.0",
echo   "description": "專業電表監控系統 Windows 版 - 支援 MODBUS RTU 通訊",
echo   "main": "run_windows.py",
echo   "scripts": {
echo     "start": "python run_windows.py",
echo     "install": "install.bat",
echo     "test": "python scripts/test_modbus.py"
echo   },
echo   "repository": {
echo     "type": "git",
echo     "url": "https://github.com/[your-username]/power-meter-web-windows.git"
echo   },
echo   "keywords": [
echo     "power-meter",
echo     "modbus-rtu", 
echo     "energy-monitoring",
echo     "windows",
echo     "flask",
echo     "socketio"
echo   ],
echo   "author": "Claude Code Assistant",
echo   "license": "MIT",
echo   "python_requires": ">=3.8",
echo   "os": "Windows 10/11"
echo }
) > package.json

echo [成功] package.json 已建立
echo.

REM 顯示 Git 指令
echo ====================================================
echo   🚀 GitHub 上傳指令
echo ====================================================
echo.
echo 1. 在 GitHub 建立新專案： power-meter-web-windows
echo.
echo 2. 在此目錄執行以下指令：
echo.
echo    git init
echo    git add .
echo    git commit -m "🚀 初始版本：Power Meter Web Edition Windows 版本"
echo    git branch -M main  
echo    git remote add origin https://github.com/[your-username]/power-meter-web-windows.git
echo    git push -u origin main
echo.
echo 3. 建立 Release：
echo    - 前往 GitHub 專案頁面
echo    - 點擊 "Releases" ^> "Create a new release"
echo    - Tag: v1.0.0-windows
echo    - Title: Power Meter Web Edition v1.0.0 - Windows 首發版
echo.
echo ====================================================
echo   📥 使用者下載方式
echo ====================================================
echo.
echo ZIP 下載：
echo https://github.com/[your-username]/power-meter-web-windows/archive/refs/heads/main.zip
echo.
echo Git Clone：
echo git clone https://github.com/[your-username]/power-meter-web-windows.git
echo.
echo ====================================================
echo   📋 安裝 SOP
echo ====================================================
echo.
echo 1. 下載並解壓到 C:\PowerMeterWeb\
echo 2. 雙擊 install.bat ^(管理員身分^)
echo 3. 設定 config\modbus_config.json
echo 4. 執行 python scripts\test_modbus.py 測試
echo 5. 雙擊 start.bat 啟動系統
echo 6. 開啟瀏覽器訪問 http://localhost:5001
echo.
echo ====================================================

echo.
echo [完成] GitHub 打包準備完成！
echo.
echo 💡 下一步：
echo 1. 複製上述 Git 指令到命令列執行
echo 2. 上傳到 GitHub
echo 3. 建立 Release 版本
echo 4. 提供下載連結給使用者
echo.
echo 📖 完整 SOP 請參考：GITHUB_DEPLOYMENT_SOP.md
echo.
pause