# Power Meter Web Edition - GitHub 部署完整 SOP

## 📋 目錄
1. [GitHub 專案創建](#github-專案創建)
2. [使用者下載與安裝](#使用者下載與安裝)
3. [故障排除](#故障排除)
4. [技術支援](#技術支援)

---

## 🚀 GitHub 專案創建

### 第一步：建立 GitHub Repository
1. 登入 GitHub 帳號
2. 點擊右上角 "+" → "New repository"
3. 設定專案資訊：
   - **Repository name**: `power-meter-web-windows`
   - **Description**: `專業電表監控系統 Windows 版 - 支援 MODBUS RTU 通訊`
   - **Public** 或 **Private** (根據需求選擇)
   - ✅ Add a README file
   - ✅ Add .gitignore (選擇 Python)
   - ✅ Choose a license (MIT License)

### 第二步：上傳專案檔案
```bash
# 在 windows_package 目錄下執行
git init
git add .
git commit -m "🚀 初始版本：Power Meter Web Edition Windows 版本

✨ 功能特色：
- 支援 MODBUS RTU (9600-N-8-1) 
- 50 電表同時監控
- Excel 風格介面
- 供電時段智能管理
- 一鍵安裝部署

🔧 技術特色：
- Flask + Socket.IO 即時監控
- SQLite 數據持久化  
- Windows 10/11 原生支援
- COM port 自動偵測

🎯 適用場景：
- 工廠電力監控
- 大樓用電管理
- 設備能耗分析"

git branch -M main
git remote add origin https://github.com/[your-username]/power-meter-web-windows.git
git push -u origin main
```

### 第三步：設定 GitHub Releases
1. 在 GitHub 專案頁面點擊 "Releases"
2. 點擊 "Create a new release"
3. 設定版本標籤：`v1.0.0-windows`
4. 釋出標題：`Power Meter Web Edition v1.0.0 - Windows 首發版`
5. 釋出說明：
```markdown
## 🎉 Power Meter Web Edition Windows 版本首發！

### ✨ 主要功能
- **MODBUS RTU 支援**: 原生支援 9600-N-8-1 通訊協定
- **50 電表監控**: 同時監控多達 50 個電表設備
- **Excel 風格介面**: 熟悉的表格操作體驗
- **供電時段管理**: 智能供電時段控制 (預設 06:00-22:00)
- **即時數據更新**: Socket.IO 無需重新整理的即時監控

### 🚀 快速開始
1. 下載 ZIP 檔案並解壓
2. 雙擊 `install.bat` 自動安裝
3. 設定 MODBUS 連接參數
4. 雙擊 `start.bat` 啟動系統
5. 開啟瀏覽器訪問 http://localhost:5001

### 📋 系統需求
- Windows 10/11 (64-bit)
- Python 3.8+
- 可用的 COM port
- 支援 MODBUS RTU 的電表設備

### 🔧 MODBUS 設定
- **COM Port**: COM1 (可自訂)
- **Baudrate**: 9600
- **Data bits**: 8
- **Parity**: None
- **Stop bits**: 1
- **MODBUS Address**: 2 (電表 ID)

完整安裝和使用說明請參考 [README.md](README.md)
```

---

## 📥 使用者下載與安裝

### 方法一：ZIP 檔案下載 (推薦)
```
🔗 下載連結：https://github.com/[your-username]/power-meter-web-windows/archive/refs/heads/main.zip

📁 解壓位置：建議解壓到 C:\PowerMeterWeb\
```

### 方法二：Git Clone
```bash
git clone https://github.com/[your-username]/power-meter-web-windows.git
cd power-meter-web-windows
```

---

## 🛠️ 完整安裝 SOP

### 第一步：環境準備
```
✅ 確認 Windows 10/11 系統
✅ 確認有可用的 COM port
✅ 準備 MODBUS RTU 電表（地址設為 2）
✅ 確認網路連線（用於下載套件）
```

### 第二步：Python 環境檢查
```batch
# 開啟命令提示字元，檢查 Python 版本
python --version

# 如果沒有 Python，請至 https://python.org 下載安裝 Python 3.8+
# 安裝時勾選 "Add Python to PATH"
```

### 第三步：專案安裝
```batch
# 1. 下載並解壓專案到 C:\PowerMeterWeb\

# 2. 進入專案目錄
cd C:\PowerMeterWeb

# 3. 執行一鍵安裝（管理員身分執行）
install.bat
```

### 第四步：MODBUS 設定
```batch
# 編輯 config\modbus_config.json
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

### 第五步：連接測試
```batch
# 執行 MODBUS 測試工具
python scripts\test_modbus.py

# 或直接雙擊 scripts\test_modbus.py
```

### 第六步：啟動系統
```batch
# 雙擊 start.bat 或執行
start.bat
```

### 第七步：訪問系統
```
🌐 開啟瀏覽器訪問：
- 本機：http://localhost:5001
- 區網：http://[電腦IP]:5001

📱 主要功能頁面：
- 首頁：/
- Excel 介面：/excel  
- 即時監控：/monitor
- 歷史查詢：/history
- 供電管理：/power_schedule
- RTU 管理：/rtu
```

---

## ⚙️ 進階設定

### 環境變數設定
```batch
# 在 start.bat 中修改或設定系統環境變數
set RTU_PORT=COM2           # 更改 COM port
set RTU_BAUDRATE=19200     # 更改 Baudrate  
set FORCE_SIMULATION=true  # 啟用模擬模式
set METER_COUNT=25         # 設定電表數量
```

### 防火牆設定
```batch
# 開放 5001 port 供區域網路存取
netsh advfirewall firewall add rule name="Power Meter Web" dir=in action=allow protocol=TCP localport=5001
```

### Windows 服務安裝
```batch
# 使用 NSSM 設定為 Windows 服務
# 1. 下載 NSSM：https://nssm.cc/download
# 2. 安裝服務
nssm install PowerMeterWeb "C:\PowerMeterWeb\venv\Scripts\python.exe" "C:\PowerMeterWeb\run_windows.py"
nssm set PowerMeterWeb AppDirectory "C:\PowerMeterWeb"
nssm start PowerMeterWeb
```

---

## 🔧 故障排除

### 常見問題與解決方案

#### ❌ 問題：無法連接到 COM port
```
🔍 診斷步驟：
1. 裝置管理員確認 COM port 存在
2. 檢查是否被其他程式佔用
3. 確認 USB 轉 RS485 驅動已安裝

💡 解決方案：
- 更換 COM port 號碼
- 重新插拔 USB 轉換器
- 重新安裝驅動程式
```

#### ❌ 問題：讀取電表數據失敗
```
🔍 診斷步驟：
1. 執行 scripts\test_modbus.py 測試
2. 確認電表 MODBUS Address = 2
3. 檢查通訊參數 (9600-N-8-1)
4. 確認線路連接正確

💡 解決方案：
- 調整 MODBUS Address
- 檢查實體線路
- 確認電表電源開啟
```

#### ❌ 問題：網頁無法存取
```
🔍 診斷步驟：
1. 確認 start.bat 執行成功
2. 檢查 5001 port 是否被佔用
3. 檢查防火牆設定

💡 解決方案：
- 更改 port 號碼
- 關閉防火牆測試
- 重新啟動服務
```

#### ❌ 問題：Python 套件安裝失敗
```
🔍 診斷步驟：
1. 檢查網路連線
2. 確認 Python 版本 >= 3.8
3. 檢查磁碟空間

💡 解決方案：
- 使用管理員身分執行 install.bat
- 使用國內映像站：
  pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

---

## 📞 技術支援

### 聯絡方式
- **GitHub Issues**: [提交問題](https://github.com/[your-username]/power-meter-web-windows/issues)
- **Email**: support@powermeter.com
- **文件**: 查看專案 `docs/` 目錄

### 回報問題時請提供
1. **系統資訊**: Windows 版本、Python 版本
2. **錯誤訊息**: 完整的錯誤日誌
3. **設定檔案**: modbus_config.json 內容
4. **硬體資訊**: COM port、電表型號
5. **操作步驟**: 重現問題的步驟

### 日誌檔案位置
```
📁 重要日誌檔案：
- 應用程式日誌：data\logs\power_meter_web.log
- 資料庫檔案：data\database\power_meter_web.db
- 設定檔案：config\modbus_config.json
```

---

## 🎯 快速檢查清單

### 下載前確認
- [ ] Windows 10/11 系統
- [ ] 有穩定的網路連線
- [ ] 至少 500MB 可用磁碟空間

### 安裝前確認  
- [ ] Python 3.8+ 已安裝
- [ ] 以管理員身分執行安裝
- [ ] 防毒軟體不會阻擋安裝

### 使用前確認
- [ ] COM port 可正常使用
- [ ] MODBUS 電表地址設為 2
- [ ] 通訊參數為 9600-N-8-1
- [ ] 實體線路連接正確

### 啟動前確認
- [ ] install.bat 執行成功
- [ ] test_modbus.py 測試通過
- [ ] 5001 port 未被占用
- [ ] 防火牆已正確設定

---

**⚡ Power Meter Web Edition - 讓電力監控變得簡單高效！**

📝 最後更新：2025-01-01  
🔖 版本：v1.0.0-windows  
💻 平台：Windows 10/11 (64-bit)