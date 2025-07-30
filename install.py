#!/usr/bin/env python3
"""
Power Meter Web Edition - Python 安裝程式
Python Installer for Power Meter Web Edition
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

def print_header():
    """顯示安裝程式標題"""
    print("=" * 60)
    print("  Power Meter Web Edition - Python 安裝程式")
    print("  Professional Power Meter Monitoring System")
    print("=" * 60)
    print()

def check_python():
    """檢查 Python 版本"""
    try:
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print("❌ 錯誤：需要 Python 3.8 或以上版本！")
            print("目前版本：Python {}.{}".format(version.major, version.minor))
            print("請從 https://www.python.org/downloads/ 下載最新版本")
            return False
        
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} 檢查通過")
        return True
    except Exception as e:
        print(f"❌ Python 檢查失敗：{e}")
        return False

def check_pip():
    """檢查 pip 是否可用"""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ pip 檢查通過")
            return True
        else:
            print("❌ pip 未正確安裝")
            return False
    except Exception as e:
        print(f"❌ pip 檢查失敗：{e}")
        return False

def create_venv():
    """創建虛擬環境"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("ℹ️  虛擬環境已存在，跳過創建")
        return True
    
    try:
        print("📦 正在創建虛擬環境...")
        result = subprocess.run([sys.executable, '-m', 'venv', 'venv'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 虛擬環境創建成功")
            return True
        else:
            print(f"❌ 虛擬環境創建失敗：{result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 創建虛擬環境時發生錯誤：{e}")
        return False

def install_packages():
    """安裝必要套件"""
    try:
        # 確定 Python 執行檔路徑
        if platform.system() == "Windows":
            python_exe = Path("venv/Scripts/python.exe")
            pip_exe = Path("venv/Scripts/pip.exe")
        else:
            python_exe = Path("venv/bin/python")
            pip_exe = Path("venv/bin/pip")
        
        if not python_exe.exists():
            print("❌ 找不到虛擬環境中的 Python")
            return False
        
        print("📦 升級 pip...")
        result = subprocess.run([str(python_exe), '-m', 'pip', 'install', '--upgrade', 'pip'], 
                              capture_output=True, text=True)
        
        print("📦 正在安裝套件，請稍候...")
        
        # 檢查 requirements.txt 是否存在
        if not Path("requirements.txt").exists():
            print("❌ 找不到 requirements.txt 檔案")
            return False
        
        # 安裝套件
        result = subprocess.run([str(python_exe), '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 所有套件安裝完成")
            return True
        else:
            print(f"❌ 套件安裝失敗：{result.stderr}")
            print("\n💡 建議嘗試使用國內映像站：")
            
            # 嘗試使用國內映像站
            print("🔄 正在嘗試使用清華大學映像站...")
            result2 = subprocess.run([
                str(python_exe), '-m', 'pip', 'install', '-r', 'requirements.txt',
                '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple/'
            ], capture_output=True, text=True)
            
            if result2.returncode == 0:
                print("✅ 使用映像站安裝成功")
                return True
            else:
                print(f"❌ 映像站安裝也失敗：{result2.stderr}")
                return False
                
    except Exception as e:
        print(f"❌ 安裝套件時發生錯誤：{e}")
        return False

def create_directories():
    """創建必要目錄"""
    directories = [
        "data/database",
        "data/logs", 
        "data/uploads",
        "data/config"
    ]
    
    try:
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        print("✅ 目錄結構創建完成")
        return True
    except Exception as e:
        print(f"❌ 創建目錄失敗：{e}")
        return False

def copy_config_files():
    """複製設定檔案"""
    try:
        # 複製 Windows 配置檔
        windows_config = Path("config/config_windows.py")
        main_config = Path("config.py")
        
        if windows_config.exists():
            shutil.copy2(windows_config, main_config)
            print("✅ Windows 配置檔已複製")
        else:
            print("⚠️  Windows 配置檔不存在，將使用預設配置")
        
        # 複製 MODBUS 配置檔
        modbus_config = Path("config/modbus_config.json")
        data_config = Path("data/config/modbus_config.json")
        
        if modbus_config.exists():
            shutil.copy2(modbus_config, data_config)
            print("✅ MODBUS 配置檔已複製")
        
        return True
    except Exception as e:
        print(f"❌ 複製配置檔失敗：{e}")
        return False

def setup_database():
    """初始化資料庫"""
    try:
        if platform.system() == "Windows":
            python_exe = Path("venv/Scripts/python.exe")
        else:
            python_exe = Path("venv/bin/python")
        
        setup_script = Path("scripts/setup_database.py")
        
        if not setup_script.exists():
            print("⚠️  資料庫設置腳本不存在，首次啟動時會自動建立")
            return True
        
        print("🗄️  正在初始化資料庫...")
        result = subprocess.run([str(python_exe), str(setup_script)], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 資料庫初始化完成")
            return True
        else:
            print("⚠️  資料庫初始化可能有問題，首次啟動時會自動建立")
            return True  # 不讓這個失敗阻止安裝
            
    except Exception as e:
        print(f"⚠️  資料庫初始化錯誤：{e}")
        return True  # 不讓這個失敗阻止安裝

def print_success_message():
    """顯示安裝成功訊息"""
    print()
    print("=" * 60)
    print("  🎉 安裝完成！")
    print("=" * 60)
    print()
    print("接下來的步驟：")
    print("1. 連接您的 MODBUS RTU 電表到 COM port")
    print("2. 編輯 config/modbus_config.json 設定您的設備")
    print("3. 執行測試：python scripts/test_modbus.py")
    print("4. 啟動系統：python run_windows.py")
    print("5. 開啟瀏覽器訪問 http://localhost:5001")
    print()
    print("系統預設設定：")
    print("- COM Port: COM1")
    print("- MODBUS Address: 2 (對應 Web Meter ID 1)")
    print("- Baudrate: 9600-N-8-1")
    print()
    print("=" * 60)
    print("  需要協助？請查看 README.md")
    print("=" * 60)

def main():
    """主安裝程序"""
    print_header()
    
    # 檢查作業系統
    if platform.system() != "Windows":
        print("⚠️  此安裝程式主要為 Windows 設計")
    
    # 檢查 Python 版本
    if not check_python():
        input("\n按 Enter 鍵結束...")
        sys.exit(1)
    
    # 檢查 pip
    if not check_pip():
        input("\n按 Enter 鍵結束...")
        sys.exit(1)
    
    # 安裝步驟
    steps = [
        ("創建虛擬環境", create_venv),
        ("安裝必要套件", install_packages),
        ("創建目錄結構", create_directories),
        ("複製設定檔案", copy_config_files),
        ("初始化資料庫", setup_database)
    ]
    
    for i, (step_name, step_func) in enumerate(steps, 1):
        print(f"\n[{i}/{len(steps)}] {step_name}...")
        if not step_func():
            print(f"\n❌ 安裝失敗於步驟：{step_name}")
            input("\n按 Enter 鍵結束...")
            sys.exit(1)
    
    print_success_message()
    input("\n按 Enter 鍵結束...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用戶取消安裝")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 安裝過程中發生未預期的錯誤：{e}")
        input("\n按 Enter 鍵結束...")
        sys.exit(1)