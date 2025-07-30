#!/usr/bin/env python3
"""
Power Meter Web Edition - Windows 啟動程式
Windows Launcher for Power Meter Web Edition
"""

import os
import sys
import platform
from pathlib import Path

# 確保在 Windows 環境
if platform.system() != 'Windows':
    print("⚠️  警告：此版本專為 Windows 設計，在其他系統上可能無法正常運行")

# 設定專案根目錄
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 設定環境變數
os.environ['FLASK_ENV'] = 'production'
os.environ['PYTHON_PATH'] = str(PROJECT_ROOT)

# Windows 特定環境設定
if not os.environ.get('RTU_PORT'):
    os.environ['RTU_PORT'] = 'COM1'

if not os.environ.get('FORCE_SIMULATION'):
    os.environ['FORCE_SIMULATION'] = 'false'

# 匯入並啟動應用程式
if __name__ == '__main__':
    try:
        # 使用 Windows 專用配置
        os.environ['CONFIG_MODULE'] = 'config.config_windows'
        
        # 導入主應用程式
        from app import app, socketio
        
        print("=" * 60)
        print("🚀 Power Meter Web Edition - Windows 版本啟動中...")
        print("=" * 60)
        print(f"📁 專案路徑: {PROJECT_ROOT}")
        print(f"💻 系統平台: {platform.system()} {platform.release()}")
        print(f"🐍 Python 版本: {platform.python_version()}")
        print(f"🔌 COM Port: {os.environ.get('RTU_PORT', 'COM1')}")
        print(f"🎭 模擬模式: {'啟用' if os.environ.get('FORCE_SIMULATION', 'false').lower() == 'true' else '停用'}")
        print("=" * 60)
        print("🌐 網頁服務啟動於:")
        print("   - 本機存取: http://localhost:5001")
        print("   - 本機存取: http://127.0.0.1:5001")
        print(f"   - 區域網路: http://{os.environ.get('COMPUTERNAME', 'YOUR-PC')}:5001")
        print("=" * 60)
        print("📋 可用頁面:")
        print("   • 首頁: /")
        print("   • Excel 介面: /excel")
        print("   • 即時監控: /monitor")
        print("   • 圖表分析: /charts")
        print("   • 歷史查詢: /history")
        print("   • 供電管理: /power_schedule")
        print("   • RTU 管理: /rtu")
        print("   • 系統設定: /settings")
        print("=" * 60)
        print("⚡ 系統準備就緒！按 Ctrl+C 停止服務")
        print("=" * 60)
        
        # 啟動 Socket.IO 應用程式
        socketio.run(
            app,
            host='0.0.0.0',
            port=5001,
            debug=False,
            use_reloader=False,
            log_output=True
        )
        
    except ImportError as e:
        print(f"❌ 匯入錯誤：{e}")
        print("請確認是否正確執行了 install.bat 安裝所有必要套件")
        input("按 Enter 結束...")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\n🛑 使用者停止服務")
        
    except Exception as e:
        print(f"❌ 啟動失敗：{e}")
        print("請檢查配置檔案和系統設定")
        input("按 Enter 結束...")
        sys.exit(1)