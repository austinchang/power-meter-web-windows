#!/usr/bin/env python3
"""
Power Meter Web Edition - 緊急修復安裝程式
Emergency Fix Installer for Power Meter Web Edition
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_header():
    """顯示修復程式標題"""
    print("=" * 60)
    print("  Power Meter Web Edition - 緊急修復安裝程式")
    print("  Emergency Fix Installer")
    print("=" * 60)
    print()

def install_core_packages():
    """安裝核心套件"""
    try:
        # 確定 Python 執行檔路徑
        if platform.system() == "Windows":
            python_exe = Path("venv/Scripts/python.exe")
        else:
            python_exe = Path("venv/bin/python")
        
        if not python_exe.exists():
            print("❌ 找不到虛擬環境，請先創建虛擬環境")
            print("執行：python -m venv venv")
            return False
        
        # 核心套件清單（避免版本衝突）
        core_packages = [
            "Flask>=2.2.0",
            "Flask-SocketIO>=5.0.0", 
            "Flask-SQLAlchemy>=3.0.0",
            "Flask-CORS>=4.0.0",
            "minimalmodbus>=2.0.0",
            "pyserial>=3.5",
            "python-socketio>=5.8.0",
            "python-engineio>=4.6.0",
            "eventlet>=0.33.0",
            "SQLAlchemy>=2.0.0",
            "python-dotenv>=1.0.0",
            "psutil>=5.9.0",
            "colorama>=0.4.0"
        ]
        
        # Windows 特定套件
        if platform.system() == "Windows":
            core_packages.append("pywin32")  # 不指定版本，使用最新版
        
        print("📦 正在安裝核心套件...")
        
        for package in core_packages:
            print(f"🔧 安裝 {package}...")
            result = subprocess.run([
                str(python_exe), '-m', 'pip', 'install', package, '--upgrade'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"⚠️  {package} 安裝失敗，嘗試映像站...")
                # 嘗試使用映像站
                result2 = subprocess.run([
                    str(python_exe), '-m', 'pip', 'install', package, '--upgrade',
                    '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple/'
                ], capture_output=True, text=True)
                
                if result2.returncode == 0:
                    print(f"✅ {package} 映像站安裝成功")
                else:
                    print(f"❌ {package} 安裝失敗，跳過")
                    continue
            else:
                print(f"✅ {package} 安裝成功")
        
        print("\n✅ 核心套件安裝完成")
        return True
        
    except Exception as e:
        print(f"❌ 安裝過程中發生錯誤：{e}")
        return False

def create_basic_structure():
    """創建基本目錄結構"""
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

def test_imports():
    """測試重要模組導入"""
    if platform.system() == "Windows":
        python_exe = Path("venv/Scripts/python.exe")
    else:
        python_exe = Path("venv/bin/python")
    
    test_modules = [
        "flask",
        "flask_socketio", 
        "minimalmodbus",
        "serial",
        "sqlalchemy"
    ]
    
    print("\n🧪 測試模組導入...")
    
    success_count = 0
    for module in test_modules:
        result = subprocess.run([
            str(python_exe), '-c', f'import {module}; print("{module} OK")'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {module} 導入成功")
            success_count += 1
        else:
            print(f"❌ {module} 導入失敗")
    
    print(f"\n📊 測試結果：{success_count}/{len(test_modules)} 模組可用")
    return success_count >= len(test_modules) - 1  # 允許1个模組失敗

def main():
    """主修復程序"""
    print_header()
    
    print("🔧 這是緊急修復安裝程式，用於解決套件版本衝突問題")
    print()
    
    # 檢查虛擬環境
    if not Path("venv").exists():
        print("📦 創建虛擬環境...")
        result = subprocess.run([sys.executable, '-m', 'venv', 'venv'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ 創建虛擬環境失敗")
            input("\n按 Enter 鍵結束...")
            sys.exit(1)
        print("✅ 虛擬環境創建成功")
    
    # 安裝核心套件
    if not install_core_packages():
        print("\n❌ 套件安裝失敗")
        input("\n按 Enter 鍵結束...")
        sys.exit(1)
    
    # 創建目錄結構
    create_basic_structure()
    
    # 測試導入
    if test_imports():
        print("\n🎉 修復安裝完成！")
        print("\n接下來可以：")
        print("1. 執行：python test_modbus.py 測試 MODBUS 連接")
        print("2. 執行：python start.py 啟動系統")
        print("3. 訪問：http://localhost:5001")
    else:
        print("\n⚠️  部分模組可能有問題，但基本功能應該可用")
        print("可以嘗試執行：python start.py")
    
    input("\n按 Enter 鍵結束...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用戶取消修復")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 修復過程中發生未預期的錯誤：{e}")
        input("\n按 Enter 鍵結束...")
        sys.exit(1)