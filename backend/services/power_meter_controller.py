#!/usr/bin/env python3
"""
Web版電錶控制器 - 基於 MODBUS_NEW20.PY 架構
用於Web系統的單電表監控與繼電器控制
"""

import os
import serial
import struct
import time
import threading
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

# 配置模擬模式 (可通過環境變量覆蓋)
FORCE_SIMULATION = os.environ.get('FORCE_SIMULATION', 'True').lower() == 'true'

try:
    import minimalmodbus
    if FORCE_SIMULATION:
        logging.warning("強制使用模擬模式運行 monitor 功能")
        MINIMALMODBUS_AVAILABLE = False
    else:
        MINIMALMODBUS_AVAILABLE = True
except ImportError:
    logging.warning("minimalmodbus 庫未安裝，monitor功能將以模擬模式運行")
    MINIMALMODBUS_AVAILABLE = False

if not MINIMALMODBUS_AVAILABLE:
    # 創建模擬的minimalmodbus模組，集成供電時段邏輯
    import random
    
    def _get_power_schedule_status():
        """獲取當前供電時段狀態"""
        try:
            # 延遲導入避免循環依賴
            from .meter_service import meter_service
            is_power_on = meter_service.is_power_schedule_active('open_power')
            logging.debug(f"MockMinimalModbus: 供電時段狀態 = {is_power_on}")
            return is_power_on
        except Exception as e:
            logging.warning(f"MockMinimalModbus: 無法獲取供電時段狀態，使用預設值: {e}")
            # 如果無法獲取供電時段，預設為開啟（06:00-22:00）
            from datetime import datetime
            current_hour = datetime.now().hour
            return 6 <= current_hour < 22
    
    class MockSerial:
        def __init__(self):
            self.baudrate = 9600
            self.bytesize = 8
            self.parity = None
            self.stopbits = 1
            self.timeout = 1.0
    
    class MockMinimalModbus:
        MODE_RTU = 'rtu'
        class Instrument:
            def __init__(self, port, slave_address):
                self.serial = MockSerial()
                self.mode = 'rtu'
                self.slave_address = slave_address
                
            def read_float(self, address, functioncode=3):
                # 根據供電時段決定數值
                is_power_on = _get_power_schedule_status()
                
                if address == 0x0000:  # 電壓
                    if is_power_on:
                        return 220.0 + random.uniform(-5, 5)
                    else:
                        return 0.0  # 停電時無電壓
                elif address == 0x0006:  # 電流
                    if is_power_on:
                        return random.uniform(10, 30)
                    else:
                        return 0.0  # 停電時無電流
                elif address == 0x000C:  # 功率
                    if is_power_on:
                        return random.uniform(2200, 6600)
                    else:
                        return 0.0  # 停電時無功率
                elif address == 0x0156:  # kWh
                    # 累積電量不受供電狀態影響
                    return random.uniform(100, 1000)
                return 100.0 + random.uniform(-10, 10) if is_power_on else 0.0
                
            def read_registers(self, address, count, functioncode=3):
                # 根據供電時段決定暫存器值
                is_power_on = _get_power_schedule_status()
                if is_power_on:
                    return [0x4200, 0x0000]  # 模擬正常 FLOAT32 數據
                else:
                    return [0x0000, 0x0000]  # 停電時返回0值
                
            def read_bit(self, address, functioncode=1):
                # 模擬繼電器狀態 - 根據供電時段決定 ON/OFF
                is_power_on = _get_power_schedule_status()
                logging.debug(f"MockMinimalModbus: 電表 {self.slave_address} 繼電器狀態 = {'ON' if is_power_on else 'OFF'}")
                return is_power_on
                
            def write_register(self, address, value, functioncode=6):
                return True
                
            def write_bit(self, address, value, functioncode=5):
                # 模擬寫入繼電器狀態
                logging.info(f"MockMinimalModbus: 電表 {self.slave_address} 繼電器設定為 {'ON' if value else 'OFF'}")
                return True
    
    minimalmodbus = MockMinimalModbus()

class WebPowerMeterController:
    """
    Web版電錶控制器
    基於 MODBUS_NEW20.PY 的 PowerMeterController 類別
    """
    
    def __init__(self, port: str = 'COM1', slave_address: int = 1):
        """
        初始化 Modbus RTU 連接
        
        Args:
            port: 串口名稱 (Windows: COM1, Linux: /dev/ttyUSB0)
            slave_address: 電表的 Modbus 地址 (1-50)
        """
        try:
            self.slave_address = slave_address
            self.instrument = minimalmodbus.Instrument(port, slave_address)
            
            # 設定通訊參數 - 與原版完全一致
            self.instrument.serial.baudrate = 9600
            self.instrument.serial.bytesize = 8
            self.instrument.serial.parity = serial.PARITY_NONE
            self.instrument.serial.stopbits = 1
            self.instrument.serial.timeout = 1.0
            self.instrument.mode = minimalmodbus.MODE_RTU
            
            logging.info(f"✓ 成功連接到電表 {slave_address} (端口: {port})")
            logging.info(f"✓ 通訊參數: 9600-N-8-1")
            
        except Exception as e:
            logging.error(f"✗ 連接電表 {slave_address} 失敗: {e}")
            raise
    
    def read_float32_value(self, start_address: int, name: str = "數值") -> Tuple[Optional[float], Optional[list]]:
        """
        讀取任意地址的 FLOAT32 值 - 使用 ABCD Big-Endian
        與 MODBUS_NEW20.PY 完全一致的實現
        
        Args:
            start_address: 起始地址
            name: 數值名稱（用於錯誤日誌）
            
        Returns:
            Tuple[float, list]: (數值, 原始暫存器值)
        """
        try:
            # 讀取兩個連續暫存器
            registers = self.instrument.read_registers(start_address, 2, functioncode=3)
            
            if registers:
                # 使用 ABCD (Big-Endian) 組合 - 與原版一致
                value_32bit = (registers[0] << 16) | registers[1]
                bytes_data = struct.pack('>I', value_32bit)
                float_value = struct.unpack('>f', bytes_data)[0]
                
                return float_value, registers
            
            return None, None
            
        except Exception as e:
            logging.error(f"✗ 讀取{name}錯誤 (地址: 0x{start_address:04X}): {e}")
            return None, None
    
    def read_kwh(self) -> Tuple[Optional[float], Optional[list]]:
        """
        讀取總有效電能 (kWh) - 使用 ABCD Big-Endian
        與 MODBUS_NEW20.PY 完全一致
        
        Returns:
            Tuple[float, list]: (電能值, 原始暫存器值)
        """
        try:
            # 讀取地址 0x000C 和 0x000D (總有效電能)
            registers = self.instrument.read_registers(0x000C, 2, functioncode=3)
            
            if registers:
                # 使用 ABCD (Big-Endian) 組合
                value_32bit = (registers[0] << 16) | registers[1]
                bytes_data = struct.pack('>I', value_32bit)
                kwh = struct.unpack('>f', bytes_data)[0]
                
                return kwh, registers
            
            return None, None
            
        except Exception as e:
            logging.error(f"✗ 讀取電能錯誤: {e}")
            return None, None
    
    def read_all_parameters(self) -> Dict[str, Dict[str, Any]]:
        """
        讀取所有電力參數
        與 MODBUS_NEW20.PY 完全一致的地址映射
        
        Returns:
            Dict: 包含所有電力參數的字典
        """
        parameters = {
            '平均相電壓': {'address': 0x0000, 'unit': 'V'},
            '平均電流': {'address': 0x0004, 'unit': 'A'},
            '總有效功率': {'address': 0x0006, 'unit': 'W'},
            '總有效電能': {'address': 0x000C, 'unit': 'kWh'}
        }
        
        results = {}
        
        for name, info in parameters.items():
            value, registers = self.read_float32_value(info['address'], name)
            if value is not None:
                results[name] = {
                    'value': value,
                    'unit': info['unit'],
                    'registers': registers,
                    'address': info['address']
                }
        
        return results
    
    def read_relay_status(self) -> str:
        """
        讀取繼電器狀態
        與 MODBUS_NEW20.PY 完全一致
        
        Returns:
            str: "ON" 或 "OFF" 或 "未知"
        """
        try:
            # 讀取地址 0x0000 (功能碼 01h)
            status = self.instrument.read_bit(0x0000, functioncode=1)
            return "ON" if status else "OFF"
        except Exception as e:
            logging.error(f"✗ 讀取繼電器狀態錯誤: {e}")
            return "未知"
    
    def control_relay(self, action: str) -> bool:
        """
        控制繼電器 ON/OFF
        與 MODBUS_NEW20.PY 完全一致的實現
        
        Args:
            action: "ON" 或 "OFF"
            
        Returns:
            bool: 控制是否成功
        """
        try:
            # 地址 0x0000, 功能碼 05h
            # ON: 寫入 0xFF00 (True), OFF: 寫入 0x0000 (False)
            value = True if action.upper() == "ON" else False
            self.instrument.write_bit(0x0000, value, functioncode=5)
            
            # 等待一下讓繼電器動作
            time.sleep(0.5)
            
            # 確認狀態
            new_status = self.read_relay_status()
            success = (new_status == action.upper())
            
            if success:
                logging.info(f"✓ 電表 {self.slave_address} 繼電器已{action.upper()}")
            else:
                logging.error(f"✗ 電表 {self.slave_address} 繼電器控制失敗，當前狀態: {new_status}")
            
            return success
            
        except Exception as e:
            logging.error(f"✗ 控制電表 {self.slave_address} 繼電器錯誤: {e}")
            return False
    
    def get_monitoring_data(self) -> Dict[str, Any]:
        """
        獲取適合Web顯示的監控數據
        
        Returns:
            Dict: 格式化的監控數據
        """
        try:
            params = self.read_all_parameters()
            relay_status = self.read_relay_status()
            
            if params:
                # 提取各個值並格式化
                voltage = params.get('平均相電壓', {}).get('value', 0)
                current = params.get('平均電流', {}).get('value', 0)
                power = params.get('總有效功率', {}).get('value', 0)
                kwh = params.get('總有效電能', {}).get('value', 0)
                
                return {
                    'meter_id': self.slave_address,
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'voltage': round(voltage, 1),
                    'current': round(current, 2),
                    'power': round(power, 1),
                    'energy': round(kwh, 1),
                    'energy_raw': kwh,  # 原始精度用於計算變化
                    'relay_status': relay_status,
                    'success': True
                }
            else:
                return {
                    'meter_id': self.slave_address,
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'success': False,
                    'error': '讀取電表數據失敗'
                }
                
        except Exception as e:
            logging.error(f"✗ 獲取電表 {self.slave_address} 監控數據錯誤: {e}")
            return {
                'meter_id': self.slave_address,
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'success': False,
                'error': str(e)
            }
    
    def test_connection(self) -> bool:
        """
        測試與電表的連接
        
        Returns:
            bool: 連接是否正常
        """
        try:
            # 嘗試讀取一個簡單的值來測試連接
            voltage, _ = self.read_float32_value(0x0000, "測試連接")
            return voltage is not None
        except Exception as e:
            logging.error(f"✗ 電表 {self.slave_address} 連接測試失敗: {e}")
            return False


class MeterControllerManager:
    """
    電表控制器管理器
    管理多個電表的連接和操作
    """
    
    def __init__(self, port: str = 'COM1'):
        """
        初始化管理器
        
        Args:
            port: 串口名稱
        """
        self.port = port
        self.controllers: Dict[int, WebPowerMeterController] = {}
        self.active_connections: Dict[int, bool] = {}
    
    def get_controller(self, meter_id: int) -> Optional[WebPowerMeterController]:
        """
        獲取指定電表的控制器，如果不存在則創建
        
        Args:
            meter_id: 電表ID (1-50)
            
        Returns:
            WebPowerMeterController: 電表控制器
        """
        if meter_id not in self.controllers:
            try:
                controller = WebPowerMeterController(self.port, meter_id)
                if controller.test_connection():
                    self.controllers[meter_id] = controller
                    self.active_connections[meter_id] = True
                    logging.info(f"✓ 創建電表 {meter_id} 控制器成功")
                else:
                    logging.warning(f"⚠ 電表 {meter_id} 連接測試失敗")
                    return None
            except Exception as e:
                logging.error(f"✗ 創建電表 {meter_id} 控制器失敗: {e}")
                return None
        
        return self.controllers.get(meter_id)
    
    def control_meter_relay(self, meter_id: int, action: str) -> Dict[str, Any]:
        """
        控制指定電表的繼電器
        
        Args:
            meter_id: 電表ID
            action: "ON" 或 "OFF"
            
        Returns:
            Dict: 控制結果
        """
        controller = self.get_controller(meter_id)
        if not controller:
            return {
                'success': False,
                'error': f'無法連接到電表 {meter_id}',
                'meter_id': meter_id
            }
        
        success = controller.control_relay(action)
        new_status = controller.read_relay_status()
        
        return {
            'success': success,
            'meter_id': meter_id,
            'action': action,
            'current_status': new_status,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
    
    def get_meter_data(self, meter_id: int) -> Dict[str, Any]:
        """
        獲取指定電表的監控數據
        
        Args:
            meter_id: 電表ID
            
        Returns:
            Dict: 電表數據
        """
        controller = self.get_controller(meter_id)
        if not controller:
            return {
                'success': False,
                'error': f'無法連接到電表 {meter_id}',
                'meter_id': meter_id
            }
        
        return controller.get_monitoring_data()
    
    def cleanup(self):
        """清理所有連接"""
        for meter_id in list(self.controllers.keys()):
            try:
                # 這裡可以添加清理邏輯，如關閉串口連接等
                del self.controllers[meter_id]
                logging.info(f"✓ 清理電表 {meter_id} 控制器")
            except Exception as e:
                logging.error(f"✗ 清理電表 {meter_id} 控制器失敗: {e}")
        
        self.controllers.clear()
        self.active_connections.clear()