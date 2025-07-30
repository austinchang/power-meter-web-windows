#!/usr/bin/env python3
"""
Power Meter Web Edition - MODBUS RTU 連接測試工具
MODBUS RTU Connection Test Tool for Windows
"""

import os
import sys
import json
import serial
import struct
import time
from datetime import datetime
from pathlib import Path

# 添加專案根目錄到 Python 路徑
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import minimalmodbus
    print("✅ minimalmodbus 套件已安裝")
except ImportError:
    print("❌ 錯誤：minimalmodbus 套件未安裝")
    print("請執行：pip install minimalmodbus")
    input("按 Enter 結束...")
    sys.exit(1)

try:
    import serial.tools.list_ports
    print("✅ pyserial 套件已安裝")
except ImportError:
    print("❌ 錯誤：pyserial 套件未安裝")
    print("請執行：pip install pyserial")
    input("按 Enter 結束...")
    sys.exit(1)


class ModbusRTUTester:
    """MODBUS RTU 測試器"""
    
    def __init__(self):
        self.instrument = None
        self.config = self.load_config()
        
    def load_config(self):
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
    
    def list_com_ports(self):
        """列出可用的 COM ports"""
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
    
    def connect_meter(self, com_port, modbus_address):
        """連接到電表"""
        try:
            print(f"\n🔗 正在連接到 {com_port}, MODBUS Address: {modbus_address}...")
            
            # 建立連接
            self.instrument = minimalmodbus.Instrument(com_port, modbus_address)
            
            # 設定通訊參數
            settings = self.config.get('default_settings', {})
            self.instrument.serial.baudrate = settings.get('baudrate', 9600)
            self.instrument.serial.bytesize = settings.get('databits', 8)
            
            # 設定 parity
            parity = settings.get('parity', 'N')
            if parity.upper() == 'N':
                self.instrument.serial.parity = serial.PARITY_NONE
            elif parity.upper() == 'E':
                self.instrument.serial.parity = serial.PARITY_EVEN
            elif parity.upper() == 'O':
                self.instrument.serial.parity = serial.PARITY_ODD
            
            self.instrument.serial.stopbits = settings.get('stopbits', 1)
            self.instrument.serial.timeout = settings.get('timeout', 1.0)
            self.instrument.mode = minimalmodbus.MODE_RTU
            
            print(f"✅ 連接成功！通訊參數：{self.instrument.serial.baudrate}-{parity}-{self.instrument.serial.bytesize}-{self.instrument.serial.stopbits}")
            return True
            
        except Exception as e:
            print(f"❌ 連接失敗：{e}")
            return False
    
    def read_float32_register(self, address, name="數值"):
        """讀取 FLOAT32 暫存器值"""
        try:
            # 讀取兩個連續暫存器
            registers = self.instrument.read_registers(address, 2, functioncode=3)
            
            if registers:
                # 使用 ABCD (Big-Endian) 組合
                value_32bit = (registers[0] << 16) | registers[1]
                bytes_data = struct.pack('>I', value_32bit)
                float_value = struct.unpack('>f', bytes_data)[0]
                
                return float_value, registers
            
            return None, None
            
        except Exception as e:
            print(f"❌ 讀取{name}失敗 (地址: 0x{address:04X}): {e}")
            return None, None
    
    def read_all_parameters(self):
        """讀取所有電力參數"""
        print("\n" + "="*50)
        print("📊 讀取電力參數...")
        print("="*50)
        
        parameters = {
            '平均相電壓': {'address': 0x0000, 'unit': 'V'},
            '平均電流': {'address': 0x0004, 'unit': 'A'},
            '總有效功率': {'address': 0x0006, 'unit': 'W'},
            '總有效電能': {'address': 0x000C, 'unit': 'kWh'}
        }
        
        results = {}
        all_success = True
        
        for name, info in parameters.items():
            value, registers = self.read_float32_register(info['address'], name)
            if value is not None:
                results[name] = {
                    'value': value,
                    'unit': info['unit'],
                    'registers': registers,
                    'address': info['address']
                }
                print(f"✅ {name}: {value:.3f} {info['unit']} (暫存器: [{registers[0]}, {registers[1]}])")
            else:
                all_success = False
        
        return results, all_success
    
    def read_relay_status(self):
        """讀取繼電器狀態"""
        try:
            print("\n🔌 讀取繼電器狀態...")
            # 讀取地址 0x0000 (功能碼 01h)
            status = self.instrument.read_bit(0x0000, functioncode=1)
            status_text = "ON" if status else "OFF"
            print(f"✅ 繼電器狀態: {status_text}")
            return status_text
        except Exception as e:
            print(f"❌ 讀取繼電器狀態失敗: {e}")
            return "未知"
    
    def test_relay_control(self):
        """測試繼電器控制"""
        print("\n" + "="*50)
        print("🎛️  測試繼電器控制...")
        print("="*50)
        
        # 讀取初始狀態
        initial_status = self.read_relay_status()
        print(f"初始狀態: {initial_status}")
        
        try:
            # 測試 OFF
            print("\n測試設定為 OFF...")
            self.instrument.write_bit(0x0000, False, functioncode=5)
            time.sleep(1)
            status = self.read_relay_status()
            
            # 測試 ON
            print("\n測試設定為 ON...")
            self.instrument.write_bit(0x0000, True, functioncode=5)
            time.sleep(1)
            status = self.read_relay_status()
            
            # 恢復初始狀態
            print(f"\n恢復初始狀態 ({initial_status})...")
            restore_value = True if initial_status == "ON" else False
            self.instrument.write_bit(0x0000, restore_value, functioncode=5)
            time.sleep(1)
            final_status = self.read_relay_status()
            
            print("✅ 繼電器控制測試完成")
            return True
            
        except Exception as e:
            print(f"❌ 繼電器控制測試失敗: {e}")
            return False
    
    def continuous_monitoring(self, interval=5):
        """連續監控模式"""
        print("\n" + "="*50)
        print("📈 連續監控模式 (按 Ctrl+C 停止)")
        print("="*50)
        
        print(f"{'時間':<10} {'電壓(V)':<10} {'電流(A)':<10} {'功率(W)':<12} {'電能(kWh)':<12} {'繼電器':<8}")
        print("-" * 70)
        
        try:
            while True:
                current_time = datetime.now().strftime('%H:%M:%S')
                
                # 讀取電力參數
                params, success = self.read_all_parameters()
                relay_status = self.read_relay_status()
                
                if success and params:
                    voltage = params.get('平均相電壓', {}).get('value', 0)
                    current = params.get('平均電流', {}).get('value', 0)
                    power = params.get('總有效功率', {}).get('value', 0)
                    energy = params.get('總有效電能', {}).get('value', 0)
                    
                    print(f"{current_time:<10} {voltage:<10.1f} {current:<10.3f} "
                          f"{power:<12.1f} {energy:<12.1f} {relay_status:<8}")
                else:
                    print(f"{current_time:<10} {'---':<10} {'---':<10} {'---':<12} {'---':<12} {'---':<8}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n監控已停止")
    
    def run_comprehensive_test(self):
        """執行綜合測試"""
        print("=" * 60)
        print("🧪 Power Meter Web Edition - MODBUS RTU 綜合測試")
        print("=" * 60)
        
        # 列出 COM ports
        available_ports = self.list_com_ports()
        
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
        
        # 連接測試
        if not self.connect_meter(com_port, modbus_address):
            return False
        
        # 讀取參數測試
        params, param_success = self.read_all_parameters()
        
        # 繼電器測試
        relay_success = False
        test_relay = input("\n是否測試繼電器控制？(y/N): ").strip().lower()
        if test_relay == 'y':
            relay_success = self.test_relay_control()
        
        # 連續監控選項
        continuous = input("\n是否啟動連續監控？(y/N): ").strip().lower()
        if continuous == 'y':
            interval = input("監控間隔(秒) [5]: ").strip()
            try:
                interval = int(interval) if interval else 5
            except ValueError:
                interval = 5
            self.continuous_monitoring(interval)
        
        # 測試結果總結
        print("\n" + "="*50)
        print("📋 測試結果總結")
        print("="*50)
        print(f"COM Port: {com_port}")
        print(f"MODBUS Address: {modbus_address}")
        print(f"參數讀取: {'✅ 成功' if param_success else '❌ 失敗'}")
        print(f"繼電器控制: {'✅ 成功' if relay_success else '⏭️  跳過' if test_relay != 'y' else '❌ 失敗'}")
        
        if param_success:
            print("\n✅ 電表連接正常，可以啟動 Web 系統")
            print("執行 start.bat 啟動 Power Meter Web Edition")
        else:
            print("\n❌ 電表連接有問題，請檢查：")
            print("1. COM port 是否正確")
            print("2. MODBUS Address 是否正確")
            print("3. 通訊參數是否匹配 (9600-N-8-1)")
            print("4. 線路連接是否正常")
            print("5. 電表電源是否開啟")
        
        return param_success


def main():
    """主程式"""
    try:
        os.system('title MODBUS RTU 測試工具')  # 設定視窗標題
        os.system('color 0F')  # 設定顏色
        
        tester = ModbusRTUTester()
        success = tester.run_comprehensive_test()
        
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