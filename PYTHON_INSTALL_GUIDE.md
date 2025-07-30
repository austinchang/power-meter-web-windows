# Power Meter Web Edition - Python 安裝指南

## 🚨 批次檔問題解決方案

如果您遇到 `.bat` 檔案無法執行的問題（出現 'cho' 不是內部命令等錯誤），請使用以下 **Python 安裝方式**：

---

## ⚡ 快速安裝 (3 步驟)

### 第 1 步：下載專案
```
https://github.com/austinchang/power-meter-web-windows
點擊 "Code" → "Download ZIP" → 解壓到 D:\power-meter-web-windows\
```

### 第 2 步：Python 安裝
```bash
# 進入專案目錄
cd D:\power-meter-web-windows

# 執行 Python 安裝程式
python install.py
```

### 第 3 步：啟動系統
```bash
# 測試 MODBUS 連接（可選）
python test_modbus.py

# 啟動系統
python start.py
```

### 第 4 步：訪問系統
```
開啟瀏覽器訪問：http://localhost:5001
```

---

## 🔧 Python 腳本優點

### ✅ **install.py** - Python 安裝程式
- 跨平台相容性
- 詳細的錯誤檢查和提示
- 自動處理虛擬環境
- 智能套件安裝（支援國內映像站）
- 完整的安裝進度顯示

### ✅ **start.py** - Python 啟動程式  
- 環境變數自動設定
- 安裝狀態檢查
- 詳細的系統資訊顯示
- 優雅的錯誤處理

### ✅ **test_modbus.py** - MODBUS 測試工具
- COM port 自動偵測
- 互動式參數設定
- 完整的連接測試
- 詳細的故障診斷

---

## 📋 系統需求

### 必要需求
- **Python 3.8+** (必須安裝)
- **Windows 10/11** (64-bit)
- **可用的 COM port**
- **網路連線** (套件下載)

### 檢查 Python 安裝
```bash
# 檢查 Python 版本
python --version

# 如果顯示 Python 3.8+ 即可使用
# 如果出現錯誤，請到 https://python.org 下載安裝
```

---

## 🛠️ 詳細安裝步驟

### 步驟 1：環境檢查
```bash
# 檢查 Python（必須 3.8+）
python --version

# 檢查 pip
python -m pip --version
```

### 步驟 2：執行安裝
```bash
# 進入專案目錄
cd D:\power-meter-web-windows

# 執行 Python 安裝程式
python install.py
```

**安裝程式會自動：**
- ✅ 檢查 Python 版本
- ✅ 建立虛擬環境
- ✅ 安裝所有必要套件
- ✅ 創建資料庫和目錄
- ✅ 複製配置檔案

### 步驟 3：配置 MODBUS
```bash
# 編輯配置檔案
notepad config\modbus_config.json

# 設定您的電表參數：
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

### 步驟 4：測試連接
```bash
# 執行 MODBUS 測試
python test_modbus.py

# 按照提示輸入：
# - COM Port (預設 COM1)
# - MODBUS Address (預設 2)
```

### 步驟 5：啟動系統
```bash
# 啟動 Web 系統
python start.py

# 系統將在 http://localhost:5001 啟動
```

---

## 🔍 故障排除

### ❌ 問題：Python 未安裝
```
解決方案：
1. 下載 Python：https://python.org/downloads/
2. 安裝時勾選 "Add Python to PATH"
3. 重新開啟命令提示字元
```

### ❌ 問題：套件安裝失敗
```
解決方案：
1. 檢查網路連線
2. install.py 會自動嘗試國內映像站
3. 手動使用映像站：
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### ❌ 問題：無法找到 COM port
```
解決方案：
1. 檢查設備管理員中的 COM port
2. 確認 USB 轉 RS485 驅動已安裝
3. 執行 python test_modbus.py 查看可用 port
```

### ❌ 問題：MODBUS 連接失敗
```
解決方案：
1. 確認電表 MODBUS Address = 2
2. 檢查通訊參數 (9600-N-8-1)
3. 檢查實體線路連接
4. 確認電表電源開啟
```

---

## 📊 功能驗證

### 安裝成功後應該看到：
```
✅ Python 版本檢查通過
✅ 虛擬環境創建成功
✅ 所有套件安裝完成
✅ 目錄結構創建完成
✅ 配置檔案複製完成
✅ 資料庫初始化完成
```

### 啟動成功後應該看到：
```
🚀 Power Meter Web Edition - 啟動中...
🌐 網頁服務將啟動於:
   - 本機存取: http://localhost:5001
⚡ 系統準備就緒！按 Ctrl+C 停止服務
```

---

## 🎯 主要功能頁面

### 訪問 http://localhost:5001 後可使用：
- **首頁** (`/`) - 系統概覽
- **Excel 介面** (`/excel`) - 表格式電表監控
- **即時監控** (`/monitor`) - 即時電力參數
- **圖表分析** (`/charts`) - 視覺化數據分析  
- **歷史查詢** (`/history`) - 歷史數據查詢和匯出
- **供電管理** (`/power_schedule`) - 供電時段設定
- **RTU 管理** (`/rtu`) - MODBUS RTU 連接管理
- **系統設定** (`/settings`) - 系統參數設定

---

## 📞 技術支援

### 如果仍有問題：
1. **檢查日誌**：查看 `data/logs/` 目錄下的日誌檔案
2. **GitHub Issues**：https://github.com/austinchang/power-meter-web-windows/issues
3. **重新安裝**：刪除 `venv` 資料夾後重新執行 `python install.py`

---

**⚡ Power Meter Web Edition - 讓電力監控變得簡單高效！**

*使用 Python 安裝方式，避免批次檔相容性問題*