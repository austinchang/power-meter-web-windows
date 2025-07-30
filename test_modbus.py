#!/usr/bin/env python3
"""
Power Meter Web Edition - MODBUS RTU 測試工具 (純 Python 版本)
MODBUS RTU Connection Test Tool - Pure Python Version
"""

import os
import sys
import json
import time
from pathlib import Path

# 添加專案根目錄到 Python 路徑
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def check_dependencies():
    """檢查必要套件是否已安裝"""
    missing_packages = []
    
    try:
        import serial
        print("✅ pyserial 套件已安裝")
    except ImportError:
        missing_packages.append("pyserial")
    
    try:
        import minimalmodbus
        print("✅ minimalmodbus 套件已安裝")
    except ImportError:
        missing_packages.append("minimalmodbus")
    
    if missing_packages:
        print("❌ 缺少必要套件：", ", ".join(missing_packages))
        print("請先執行：python install.py")
        return False
    
    return True

def load_config():
    """載入 MODBUS 配置"""
    config_file = PROJECT_ROOT / 'config' / 'modbus_config.json'
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  警告：無法載入配置檔案：{e}")
        return {
            "default_settings": {
                "baudrate": 9600,
                "parity": "N",
                "databits": 8,
                "stopbits": 1,
                "timeout": 1.0
            }
        }

def list_com_ports():
    """列出可用的 COM ports"""
    try:
        import serial.tools.list_ports
        
        print("\n" + "="*50)
        print("🔍 搜尋可用的 COM ports...")
        print("="*50)
        
        ports = serial.tools.list_ports.comports()
        if not ports:
            print("❌ 沒有找到可用的 COM ports")
            return []
        
        available_ports = []
        for port in ports:
            available_ports.append(port.device)
            print(f"✅ {port.device}: {port.description}")
            if hasattr(port, 'manufacturer') and port.manufacturer:
                print(f"   製造商: {port.manufacturer}")
            if hasattr(port, 'serial_number') and port.serial_number:
                print(f"   序號: {port.serial_number}")
            print()
        
        return available_ports
        
    except ImportError:
        print("❌ 無法導入 serial.tools.list_ports")
        return []

def test_modbus_connection(com_port="COM1", modbus_address=2):
    """測試 MODBUS 連接"""
    try:
        import minimalmodbus
        import serial
        
        print(f"\n🔗 正在連接到 {com_port}, MODBUS Address: {modbus_address}...")
        
        # 建立連接
        instrument = minimalmodbus.Instrument(com_port, modbus_address)
        
        # 設定通訊參數
        config = load_config()
        settings = config.get('default_settings', {})
        
        instrument.serial.baudrate = settings.get('baudrate', 9600)
        instrument.serial.bytesize = settings.get('databits', 8)
        
        # 設定 parity
        parity = settings.get('parity', 'N')
        if parity.upper() == 'N':
            instrument.serial.parity = serial.PARITY_NONE
        elif parity.upper() == 'E':
            instrument.serial.parity = serial.PARITY_EVEN
        elif parity.upper() == 'O':
            instrument.serial.parity = serial.PARITY_ODD
        
        instrument.serial.stopbits = settings.get('stopbits', 1)
        instrument.serial.timeout = settings.get('timeout', 1.0)
        instrument.mode = minimalmodbus.MODE_RTU
        
        print(f"✅ 連接成功！通訊參數：{instrument.serial.baudrate}-{parity}-{instrument.serial.bytesize}-{instrument.serial.stopbits}")
        
        # 測試讀取暫存器
        print("\n📊 測試讀取電表參數...")
        
        test_addresses = [
            (0x0000, "平均相電壓", "V"),
            (0x0004, "平均電流", "A"),
            (0x0006, "總有效功率", "W"),
            (0x000C, "總有效電能", "kWh")
        ]
        
        success_count = 0
        for address, name, unit in test_addresses:
            try:
                # 讀取兩個連續暫存器 (FLOAT32)
                registers = instrument.read_registers(address, 2, functioncode=3)
                if registers:
                    # 簡單顯示暫存器值
                    print(f"✅ {name}: 暫存器值 [{registers[0]}, {registers[1]}] {unit}")
                    success_count += 1
                else:
                    print(f"❌ {name}: 讀取失敗")
            except Exception as e:
                print(f"❌ {name}: 讀取錯誤 - {e}")
        
        # 測試繼電器狀態
        try:
            print("\n🔌 測試繼電器狀態...")
            status = instrument.read_bit(0x0000, functioncode=1)
            status_text = "ON" if status else "OFF"
            print(f"✅ 繼電器狀態: {status_text}")
            success_count += 1
        except Exception as e:
            print(f"❌ 繼電器狀態讀取失敗: {e}")
        
        print(f"\n📋 測試結果：{success_count}/5 項目成功")
        
        if success_count >= 3:
            print("✅ MODBUS 連接測試通過！")
            return True
        else:
            print("⚠️  MODBUS 連接可能有問題")
            return False
            
    except ImportError as e:
        print(f"❌ 缺少必要套件：{e}")
        return False
    except Exception as e:
        print(f"❌ 連接測試失敗：{e}")
        return False

def interactive_test():
    """互動式測試"""
    print("=" * 60)
    print("🧪 Power Meter Web Edition - MODBUS RTU 測試工具")
    print("=" * 60)
    
    # 檢查依賴套件
    if not check_dependencies():
        return False
    
    # 列出可用的 COM ports
    available_ports = list_com_ports()
    
    if not available_ports:
        print("❌ 沒有可用的 COM ports，請檢查硬體連接")
        return False
    
    # 取得使用者輸入
    print("\n請輸入測試參數:")
    
    # COM Port 選擇
    default_port = "COM1"
    if available_ports and "COM1" not in available_ports:
        default_port = available_ports[0]
    
    com_port = input(f"COM Port [{default_port}]: ").strip()
    if not com_port:
        com_port = default_port
    
    # MODBUS Address
    modbus_address = input("MODBUS Address [2]: ").strip()
    if not modbus_address:
        modbus_address = 2
    else:
        try:
            modbus_address = int(modbus_address)
        except ValueError:
            print("❌ 無效的 MODBUS Address，使用預設值 2")
            modbus_address = 2
    
    # 執行測試
    success = test_modbus_connection(com_port, modbus_address)
    
    # 顯示結果
    print("\n" + "="*50)
    print("📋 測試結果總結")
    print("="*50)
    print(f"COM Port: {com_port}")
    print(f"MODBUS Address: {modbus_address}")
    
    if success:
        print("✅ 電表連接正常，可以啟動 Web 系統")
        print("執行：python start.py 啟動 Power Meter Web Edition")
    else:
        print("❌ 電表連接有問題，請檢查：")
        print("1. COM port 是否正確")
        print("2. MODBUS Address 是否正確")
        print("3. 通訊參數是否匹配 (9600-N-8-1)")
        print("4. 線路連接是否正常")
        print("5. 電表電源是否開啟")
    
    return success

def main():
    """主程式"""
    try:
        success = interactive_test()
        
        print("\n" + "="*50)
        if success:
            print("🎉 測試完成！系統準備就緒。")
        else:
            print("⚠️  測試發現問題，請參考上述建議進行排除。")
        print("="*50)
        
    except KeyboardInterrupt:
        print("\n\n用戶中斷測試")
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤：{e}")
    
    finally:
        input("\n按 Enter 結束...")

if __name__ == "__main__":
    main()