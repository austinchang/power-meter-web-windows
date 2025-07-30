@echo off
chcp 65001 >nul
cls
color 0B
title Power Meter Web Edition - 運行中

echo ================================================
echo   Power Meter Web Edition 啟動中...
echo   專業電表監控系統 MODBUS RTU 版本
echo ================================================
echo.

REM 檢查虛擬環境
if not exist venv\Scripts\activate.bat (
    echo [錯誤] 虛擬環境不存在！
    echo [解決] 請先執行 install.bat 進行安裝
    echo.
    pause
    exit /b 1
)

REM 設定環境變數
echo [設定] 設定系統環境變數...
set FLASK_ENV=production
set PYTHONIOENCODING=utf-8
set FLASK_HOST=0.0.0.0
set FLASK_PORT=5001

REM MODBUS RTU 設定
set RTU_PORT=COM1
set RTU_BAUDRATE=9600
set RTU_PARITY=N
set RTU_BYTESIZE=8
set RTU_STOPBITS=1
set RTU_TIMEOUT=1.0
set FORCE_SIMULATION=false

REM 進階設定
set METER_COUNT=50
set RTU_ENABLED=true

echo [設定] 啟動虛擬環境...
call venv\Scripts\activate.bat

REM 檢查設定檔
if not exist config.py (
    echo [警告] 設定檔不存在，複製預設設定...
    if exist config\config_windows.py (
        copy config\config_windows.py config.py >nul
    )
)

echo.
echo ================================================
echo   系統設定資訊
echo ================================================
echo 網路設定:
echo   - 本機存取: http://localhost:5001
echo   - 區網存取: http://%COMPUTERNAME%:5001
echo   - 所有介面: http://0.0.0.0:5001
echo.
echo MODBUS RTU 設定:
echo   - COM Port: %RTU_PORT%
echo   - Baudrate: %RTU_BAUDRATE%
echo   - 參數: %RTU_BYTESIZE%-%RTU_PARITY%-%RTU_STOPBITS%
echo   - 超時: %RTU_TIMEOUT% 秒
echo   - 模擬模式: %FORCE_SIMULATION%
echo.
echo 系統設定:
echo   - 電表數量: %METER_COUNT%
echo   - RTU 啟用: %RTU_ENABLED%
echo   - 執行模式: %FLASK_ENV%
echo.
echo ================================================
echo   🚀 正在啟動伺服器...
echo   
echo   按 Ctrl+C 停止伺服器
echo ================================================
echo.

REM 啟動伺服器
python run_windows.py

REM 如果程式意外結束
echo.
echo ================================================
echo   伺服器已停止
echo ================================================
echo.
echo 如果是意外結束，可能的原因：
echo 1. COM port 被其他程式佔用
echo 2. MODBUS 設定錯誤
echo 3. Python 套件有問題
echo.
echo 解決方法：
echo 1. 檢查 COM port 是否正確
echo 2. 執行 scripts\test_modbus.py 測試連接
echo 3. 查看錯誤訊息或聯絡技術支援
echo.
pause