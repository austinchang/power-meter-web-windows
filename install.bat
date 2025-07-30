@echo off
chcp 65001 >nul
color 0A
title Power Meter Web Edition - 安裝程式

echo ================================================
echo   Power Meter Web Edition - Windows 安裝程式
echo   專業電表監控系統 MODBUS RTU 版本
echo ================================================
echo.

REM 檢查管理員權限
net session >nul 2>&1
if not %errorLevel% == 0 (
    echo [警告] 建議以管理員身分執行此安裝程式
    echo.
)

REM 檢查 Python 安裝
echo [檢查] 檢查 Python 安裝...
python --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 請先安裝 Python 3.8 或以上版本！
    echo.
    echo 請從以下網址下載並安裝 Python:
    echo https://www.python.org/downloads/
    echo.
    echo 安裝時請記得勾選 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

REM 顯示 Python 版本
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [成功] 發現 Python %PYTHON_VERSION%

REM 檢查 pip
echo [檢查] 檢查 pip 安裝...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] pip 未正確安裝！
    pause
    exit /b 1
)
echo [成功] pip 已安裝

echo.
echo [1/7] 建立虛擬環境...
if exist venv (
    echo [資訊] 虛擬環境已存在，跳過建立
) else (
    python -m venv venv
    if errorlevel 1 (
        echo [錯誤] 建立虛擬環境失敗！
        pause
        exit /b 1
    )
    echo [成功] 虛擬環境建立完成
)

echo.
echo [2/7] 啟動虛擬環境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [錯誤] 啟動虛擬環境失敗！
    pause
    exit /b 1
)
echo [成功] 虛擬環境已啟動

echo.
echo [3/7] 升級 pip...
python -m pip install --upgrade pip --quiet
echo [成功] pip 已升級至最新版本

echo.
echo [4/7] 安裝必要套件...
echo [資訊] 正在安裝套件，請稍候...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [錯誤] 套件安裝失敗！
    echo [建議] 請檢查網路連線或使用國內映像站：
    echo pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
    pause
    exit /b 1
)
echo [成功] 所有套件安裝完成

echo.
echo [5/7] 建立必要目錄...
mkdir data\database 2>nul
mkdir data\logs 2>nul
mkdir data\uploads 2>nul
mkdir data\config 2>nul
echo [成功] 目錄結構建立完成

echo.
echo [6/7] 複製設定檔案...
if exist config\config_windows.py (
    copy config\config_windows.py config.py >nul 2>&1
    echo [成功] Windows 配置檔已複製
) else (
    echo [警告] Windows 配置檔不存在，將使用預設配置
)

if exist config\modbus_config.json (
    copy config\modbus_config.json data\config\ >nul 2>&1
    echo [成功] MODBUS 配置檔已複製
)

echo.
echo [7/7] 初始化資料庫...
python scripts\setup_database.py >nul 2>&1
if errorlevel 1 (
    echo [警告] 資料庫初始化可能有問題，首次啟動時會自動建立
) else (
    echo [成功] 資料庫初始化完成
)

echo.
echo ================================================
echo   🎉 安裝完成！
echo ================================================
echo.
echo 接下來的步驟：
echo 1. 連接您的 MODBUS RTU 電表到 COM port
echo 2. 編輯 config\modbus_config.json 設定您的設備
echo 3. 執行 scripts\test_modbus.py 測試連接
echo 4. 執行 start.bat 啟動系統
echo 5. 開啟瀏覽器訪問 http://localhost:5001
echo.
echo 系統預設設定：
echo - COM Port: COM1
echo - MODBUS Address: 2 (對應 Web Meter ID 1)
echo - Baudrate: 9600-N-8-1
echo.
echo ================================================
echo   需要協助？請查看 docs\INSTALL_GUIDE_CN.md
echo ================================================
echo.
pause