#!/usr/bin/env python3
"""
Power Meter Web Edition - Python 啟動程式
Python Launcher for Power Meter Web Edition
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_installation():
    """檢查安裝狀態"""
    venv_path = Path("venv")
    
    if not venv_path.exists():
        print("❌ 虛擬環境不存在！")
        print("請先執行：python install.py")
        return False
    
    if platform.system() == "Windows":
        python_exe = venv_path / "Scripts" / "python.exe"
    else:
        python_exe = venv_path / "bin" / "python"
    
    if not python_exe.exists():
        print("❌ 找不到虛擬環境中的 Python 執行檔！")
        print("請重新執行：python install.py")
        return False
    
    return True

def set_environment_variables():
    """設定環境變數"""
    env_vars = {
        'FLASK_ENV': 'production',
        'PYTHONIOENCODING': 'utf-8',
        'FLASK_HOST': '0.0.0.0',
        'FLASK_PORT': '5001',
        'RTU_PORT': 'COM1',
        'RTU_BAUDRATE': '9600',
        'RTU_PARITY': 'N',
        'RTU_BYTESIZE': '8',
        'RTU_STOPBITS': '1',
        'RTU_TIMEOUT': '1.0',
        'FORCE_SIMULATION': 'false',
        'METER_COUNT': '50',
        'RTU_ENABLED': 'true'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value

def print_startup_info():
    """顯示啟動資訊"""
    print("=" * 60)
    print("🚀 Power Meter Web Edition - 啟動中...")
    print("=" * 60)
    print(f"📁 專案路徑: {Path.cwd()}")
    print(f"💻 系統平台: {platform.system()} {platform.release()}")
    print(f"🐍 Python 版本: {platform.python_version()}")
    print(f"🔌 COM Port: {os.environ.get('RTU_PORT', 'COM1')}")
    print(f"🎭 模擬模式: {'啟用' if os.environ.get('FORCE_SIMULATION', 'false').lower() == 'true' else '停用'}")
    print("=" * 60)
    print("🌐 網頁服務將啟動於:")
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

def main():
    """主啟動程序"""
    try:
        # 檢查安裝
        if not check_installation():
            input("\n按 Enter 鍵結束...")
            sys.exit(1)
        
        # 設定環境變數
        set_environment_variables()
        
        # 顯示啟動資訊
        print_startup_info()
        
        # 確定 Python 執行檔路徑
        if platform.system() == "Windows":
            python_exe = Path("venv/Scripts/python.exe")
        else:
            python_exe = Path("venv/bin/python")
        
        # 檢查主程式檔案
        main_app = Path("run_windows.py")
        if not main_app.exists():
            main_app = Path("app.py")
            if not main_app.exists():
                print("❌ 找不到主程式檔案 (run_windows.py 或 app.py)")
                input("\n按 Enter 鍵結束...")
                sys.exit(1)
        
        # 啟動應用程式
        print(f"\n🚀 正在啟動 {main_app}...")
        subprocess.run([str(python_exe), str(main_app)])
        
    except KeyboardInterrupt:
        print("\n\n🛑 使用者停止服務")
        
    except Exception as e:
        print(f"\n❌ 啟動失敗：{e}")
        print("請檢查配置檔案和系統設定")
        input("\n按 Enter 鍵結束...")
        sys.exit(1)

if __name__ == "__main__":
    main()