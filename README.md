# Power Meter Web Edition for Windows

![Power Meter](https://img.shields.io/badge/Power%20Meter-Web%20Edition-blue.svg)
![Windows](https://img.shields.io/badge/Platform-Windows%2010%2F11-green.svg)
![MODBUS](https://img.shields.io/badge/Protocol-MODBUS%20RTU-orange.svg)
![Python](https://img.shields.io/badge/Python-3.8%2B-yellow.svg)

專業電表監控系統 Windows 版本，支援 MODBUS RTU 通訊，提供即時監控、歷史數據查詢、供電時段管理等功能。

## 🌟 功能特色

### 核心功能
- **即時電力監控** - 電壓、電流、功率、電能即時顯示
- **MODBUS RTU 支援** - 原生支援 MODBUS RTU 協定，9600-N-8-1
- **50 電表支援** - 可同時監控多達 50 個電表
- **繼電器控制** - 遠端控制電表繼電器開關
- **歷史數據查詢** - 完整的用電歷史記錄和統計
- **供電時段管理** - 智能供電時段控制 (預設 06:00-22:00)

### 介面特色
- **Excel 風格介面** - 熟悉的表格操作體驗
- **即時 Socket.IO** - 無需重新整理的即時數據更新
- **響應式設計** - 支援桌面和平板裝置
- **多主題支援** - 明亮、暗色、工業風主題

### 技術特色
- **Flask + Socket.IO** - 現代化 Web 框架
- **SQLite 資料庫** - 輕量級數據持久化
- **Windows 原生支援** - 完美適配 Windows 10/11
- **一鍵安裝部署** - 自動化安裝和配置

## 📋 系統需求

### 必要需求
- **作業系統**: Windows 10 (64-bit) 或 Windows 11
- **Python**: 3.8 或以上版本
- **記憶體**: 最少 2GB RAM
- **硬碟空間**: 最少 500MB 可用空間
- **網路**: 用於套件下載和區域網路存取

### 硬體需求
- **COM Port**: 可用的 COM port (COM1, COM2 等)
- **USB 轉 RS485**: 如使用 USB 轉換器
- **MODBUS RTU 電表**: 支援 9600-N-8-1 通訊的電表

## 🚀 快速開始

### 1. 下載專案

**方法 A: Git 下載**
```bash
git clone https://github.com/[your-username]/power-meter-web-windows.git
cd power-meter-web-windows
```

**方法 B: ZIP 下載**
1. 點擊 GitHub 頁面的 "Code" → "Download ZIP"
2. 解壓到 `C:\PowerMeterWeb` (或任意目錄)

### 2. 執行安裝

雙擊 `install.bat` 檔案，或在命令提示字元中執行：

```batch
install.bat
```

安裝程式會自動：
- ✅ 檢查 Python 環境
- ✅ 建立虛擬環境
- ✅ 安裝所有必要套件
- ✅ 初始化資料庫
- ✅ 設定預設配置

### 3. 設定 MODBUS 連接

編輯 `config\modbus_config.json` 檔案：

```json
{
  "meter_mapping": {
    "1": {
      "modbus_address": 2,
      "name": "電表 01",
      "com_port": "COM1"
    }
  }
}
```

### 4. 測試連接

執行 MODBUS 測試工具：

```batch
python scripts\test_modbus.py
```

或直接雙擊 `scripts\test_modbus.py`

### 5. 啟動系統

雙擊 `start.bat` 檔案，或執行：

```batch
start.bat
```

### 6. 存取系統

開啟瀏覽器訪問：
- **本機存取**: http://localhost:5001
- **區域網路**: http://[電腦IP]:5001

## 📊 使用說明

### 主要介面

1. **首頁** (`/`) - 系統概覽和快速存取
2. **Excel 介面** (`/excel`) - 表格式電表數據檢視
3. **即時監控** (`/monitor`) - 即時電力參數監控
4. **圖表分析** (`/charts`) - 視覺化數據分析
5. **歷史查詢** (`/history`) - 歷史數據查詢和匯出
6. **供電管理** (`/power_schedule`) - 供電時段設定
7. **RTU 管理** (`/rtu`) - MODBUS RTU 連接管理
8. **系統設定** (`/settings`) - 系統參數設定

### 電表配置

預設配置對應關係：
- **Web Meter ID 1** ↔ **MODBUS Address 2**
- **COM Port**: COM1
- **通訊參數**: 9600-N-8-1

### MODBUS 暫存器對應

| 參數 | MODBUS 地址 | 功能碼 | 資料型態 | 單位 |
|------|-------------|--------|----------|------|
| 電壓 | 0x0000 | 03 | Float32 | V |
| 電流 | 0x0004 | 03 | Float32 | A |
| 功率 | 0x0006 | 03 | Float32 | W |
| 電能 | 0x000C | 03 | Float32 | kWh |
| 繼電器狀態 | 0x0000 | 01 | Bit | - |
| 繼電器控制 | 0x0000 | 05 | Bit | - |

## 🔧 進階設定

### 環境變數設定

可透過設定環境變數來覆蓋預設配置：

```batch
set RTU_PORT=COM2
set RTU_BAUDRATE=19200
set FORCE_SIMULATION=false
set METER_COUNT=50
```

### 防火牆設定

如需區域網路存取，請開放防火牆：

```batch
netsh advfirewall firewall add rule name="Power Meter Web" dir=in action=allow protocol=TCP localport=5001
```

### Windows 服務設定

使用 NSSM 將系統設定為 Windows 服務：

1. 下載 [NSSM](https://nssm.cc/)
2. 執行以下命令：

```batch
nssm install PowerMeterWeb "C:\PowerMeterWeb\venv\Scripts\python.exe" "C:\PowerMeterWeb\app.py"
nssm set PowerMeterWeb AppDirectory "C:\PowerMeterWeb"
nssm set PowerMeterWeb DisplayName "Power Meter Web Service"
nssm start PowerMeterWeb
```

## 🛠️ 故障排除

### 常見問題

**Q: 無法連接到 COM port**
```
A: 1. 檢查 COM port 是否被其他程式使用
   2. 確認 USB 轉 RS485 驅動程式已安裝
   3. 檢查實體線路連接
```

**Q: 讀取電表數據失敗**
```
A: 1. 確認 MODBUS Address 設定正確 (預設是 2)
   2. 檢查通訊參數 (9600-N-8-1)
   3. 確認電表電源正常
   4. 執行 scripts\test_modbus.py 進行診斷
```

**Q: 網頁無法存取**
```
A: 1. 確認 start.bat 執行成功
   2. 檢查 5001 port 是否被佔用
   3. 檢查防火牆設定
```

**Q: Python 套件安裝失敗**
```
A: 1. 使用管理員身分執行 install.bat
   2. 嘗試使用國內映像站：
      pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 日誌檔案

系統日誌位於：
- **應用程式日誌**: `data\logs\power_meter_web.log`
- **資料庫檔案**: `data\database\power_meter_web.db`

### 重新安裝

如需重新安裝：

1. 刪除 `venv` 資料夾
2. 刪除 `data` 資料夾 (將清除所有數據)
3. 重新執行 `install.bat`

## 📁 檔案結構

```
C:\PowerMeterWeb\
├── install.bat              # 一鍵安裝腳本
├── start.bat               # 啟動腳本
├── requirements.txt        # Python 套件清單
├── app.py                  # 主應用程式
├── config.py              # 系統配置
├── config/
│   ├── config_windows.py  # Windows 專用配置
│   └── modbus_config.json # MODBUS 設定
├── backend/               # 後端程式碼
│   ├── api/              # REST API
│   ├── services/         # 業務邏輯
│   ├── database/         # 資料庫模型
│   └── modbus/           # MODBUS 通訊
├── frontend/             # 前端介面
│   ├── templates/        # HTML 模板
│   └── static/           # CSS, JS, 圖片
├── scripts/              # 工具腳本
│   ├── test_modbus.py    # MODBUS 測試工具
│   └── setup_database.py # 資料庫初始化
├── data/                 # 數據目錄
│   ├── database/         # SQLite 資料庫
│   ├── logs/             # 日誌檔案
│   └── config/           # 運行時配置
└── docs/                 # 文件
    ├── INSTALL_GUIDE_CN.md
    └── MODBUS_SETUP.md
```

## 🤝 技術支援

### 聯絡方式
- **GitHub Issues**: [提交問題](https://github.com/[your-username]/power-meter-web-windows/issues)
- **Email**: support@powermeter.com
- **文件**: 查看 `docs/` 目錄下的詳細文件

### 貢獻指南
歡迎提交 Pull Request 或回報 Issue！

### 授權條款
本專案採用 MIT 授權條款，詳見 [LICENSE](LICENSE) 檔案。

---

## 🎯 版本資訊

**目前版本**: 1.0.0-windows  
**發布日期**: 2025-01-01  
**支援平台**: Windows 10/11 (64-bit)  
**Python 版本**: 3.8+  

---

⚡ **Power Meter Web Edition** - 讓電力監控變得簡單高效！