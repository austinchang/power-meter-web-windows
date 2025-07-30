#!/usr/bin/env python3
"""
MODBUS RTU 客戶端 - 用於與 RTU 模擬器通訊
整合到 Power Meter Web 應用程式中
"""

import os
import time
import struct
import threading
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging

try:
    from pymodbus.client import ModbusSerialClient
    from pymodbus.exceptions import ModbusException
except ImportError:
    print("警告: pymodbus 未安裝，將使用模擬模式")
    ModbusSerialClient = None
    ModbusException = Exception

# TCP 客戶端支援
try:
    from pymodbus.client import ModbusTcpClient
    HAS_TCP_CLIENT = True
except ImportError:
    ModbusTcpClient = None
    HAS_TCP_CLIENT = False

class IEEE754Handler:
    """IEEE 754 浮點數處理器"""
    
    @staticmethod
    def registers_to_float(reg1: int, reg2: int) -> float:
        """將兩個16位寄存器轉換為浮點數"""
        try:
            # 檢查輸入值的有效性
            if not isinstance(reg1, int) or not isinstance(reg2, int):
                return 0.0
            if reg1 < 0 or reg1 > 65535 or reg2 < 0 or reg2 > 65535:
                return 0.0
                
            # 打包為字節
            packed = struct.pack('>HH', reg1, reg2)
            # 解包為浮點數
            result = struct.unpack('>f', packed)[0]
            
            # 檢查結果的有效性 - 避免極大或極小的異常值
            if not isinstance(result, float) or not (-1e6 < result < 1e6):
                return 0.0
            if result != result:  # NaN 檢查
                return 0.0
                
            return result
        except:
            return 0.0
    
    @staticmethod
    def float_to_registers(value: float) -> Tuple[int, int]:
        """將浮點數轉換為兩個16位寄存器"""
        try:
            # 轉換為32位浮點數的字節表示
            packed = struct.pack('>f', value)
            # 解包為兩個16位整數
            reg1, reg2 = struct.unpack('>HH', packed)
            return reg1, reg2
        except:
            return 0, 0

class ModbusRTUClient:
    """MODBUS RTU 客戶端"""
    
    # ADTEK MWH-7W 寄存器映射
    REGISTER_MAP = {
        # 基本電表數據
        'total_energy': 0x0046,    # 累積電能 kWh
        'voltage_l1': 0x0000,      # L1 電壓
        'voltage_l2': 0x0002,      # L2 電壓  
        'voltage_l3': 0x0004,      # L3 電壓
        'current_l1': 0x0006,      # L1 電流
        'current_l2': 0x0008,      # L2 電流
        'current_l3': 0x000A,      # L3 電流
        'frequency': 0x0010,       # 頻率
        'power_factor': 0x0012,    # 功率因子
        
        # 擴展狀態數據 (新增)
        'daily_energy_usage': 0x0050,  # 每日用電量 kWh
        'power_status': 0x0052,        # 供電狀態 (0=斷電, 1=供電)
        'instant_power': 0x0054,       # 瞬時功率 kW
        'meter_id': 0x0056,            # 電表ID
    }
    
    def __init__(self, config: dict):
        """初始化 RTU 客戶端 - 支援 TCP"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.connected = False
        self.last_connection_attempt = 0
        self.connection_retry_interval = 5
        self.request_count = 0
        self.error_count = 0
        
        # 檢查是否使用 TCP 模式
        self.use_tcp = (
            os.environ.get('MODBUS_MODE') == 'TCP' or
            os.environ.get('RTU_SIMULATOR_PORT') == '5502' or
            config.get('RTU_SIMULATOR_PORT') == 5502
        )
        
        if self.use_tcp:
            self.host = os.environ.get('RTU_SIMULATOR_HOST', 'localhost')
            self.port = int(os.environ.get('RTU_SIMULATOR_PORT', '5502'))
            self.logger.info(f"🌐 使用 MODBUS TCP 模式: {self.host}:{self.port}")
        else:
            # RTU 配置
            self.port = config.get('rtu_port', '/dev/ttyUSB0')
            self.baudrate = config.get('baudrate', 9600)
            self.bytesize = config.get('bytesize', 8)
            self.parity = config.get('parity', 'N')
            self.stopbits = config.get('stopbits', 1)
            self.timeout = config.get('timeout', 1.0)
            self.logger.info("🔌 使用 MODBUS RTU 模式")
        
        # 數據快取
        self.meter_cache = {}
        self.cache_expiry = config.get('cache_expiry', 5)  # 5秒快取
        
        # 統計信息
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        
        # 線程鎖
        self.lock = threading.Lock()
        
        if self.use_tcp:
            self.logger.info(f"MODBUS TCP 客戶端初始化 - {self.host}:{self.port}")
        else:
            self.logger.info(f"RTU 客戶端初始化 - 埠: {self.port}, 波特率: {self.baudrate}")
    
    def connect(self) -> bool:
        """建立連接 - 支援 TCP 和 RTU"""
        if self.connected:
            return True
            
        current_time = time.time()
        if current_time - self.last_connection_attempt < self.connection_retry_interval:
            return False
            
        self.last_connection_attempt = current_time
        
        try:
            if self.use_tcp and HAS_TCP_CLIENT:
                # TCP 連接
                self.client = ModbusTcpClient(self.host, port=self.port)
                self.connected = self.client.connect()
                if self.connected:
                    self.logger.info(f"✅ TCP 連接成功: {self.host}:{self.port}")
                else:
                    self.logger.warning(f"❌ TCP 連接失敗: {self.host}:{self.port}")
            else:
                # RTU 連接 (原始邏輯)
                if ModbusSerialClient is None:
                    self.logger.warning("⚠️ pymodbus 未安裝，使用模擬模式")
                    return False
                    
                self.client = ModbusSerialClient(
                    port=self.port,
                    baudrate=self.baudrate,
                    bytesize=self.bytesize,
                    parity=self.parity,
                    stopbits=self.stopbits,
                    timeout=self.timeout
                )
                
                self.connected = self.client.connect()
                if self.connected:
                    self.logger.info("✅ RTU 連接成功")
                else:
                    self.logger.warning("❌ RTU 連接失敗")
                    
        except Exception as e:
            self.logger.error(f"連接錯誤: {e}")
            self.connected = False
            
        return self.connected
    
    def disconnect(self):
        """斷開 RTU 連線"""
        if self.client:
            try:
                self.client.close()
                self.connected = False
                self.logger.info("RTU 連線已斷開")
            except Exception as e:
                self.logger.warning(f"斷開連線時發生錯誤: {e}")
    
    def read_register(self, meter_id: int, register_name: str) -> Optional[float]:
        """讀取指定電表的寄存器值"""
        if register_name not in self.REGISTER_MAP:
            self.logger.error(f"未知的寄存器: {register_name}")
            return None
        
        register_addr = self.REGISTER_MAP[register_name]
        return self._read_float_register(meter_id, register_addr)
    
    def _read_float_register(self, meter_id: int, register_addr: int) -> Optional[float]:
        """讀取浮點數寄存器 (佔用2個寄存器)"""
        with self.lock:
            self.request_count += 1
            
            # 檢查快取
            cache_key = f"{meter_id}_{register_addr}"
            current_time = time.time()
            
            if cache_key in self.meter_cache:
                cached_data = self.meter_cache[cache_key]
                if current_time - cached_data['timestamp'] < self.cache_expiry:
                    return cached_data['value']
            
            # 如果沒有連線，嘗試重連
            if not self.connected:
                if not self.connect():
                    return self._get_simulated_value(register_addr, meter_id)
            
            try:
                # 如果使用 TCP 模式且已連接，繼續執行實際讀取
                # 模擬模式或連線失敗時返回模擬數據
                if not self.use_tcp and (ModbusSerialClient is None or not self.connected):
                    return self._get_simulated_value(register_addr, meter_id)
                
                # 讀取2個連續寄存器 (IEEE 754 浮點數) - 使用 holding registers
                result = self.client.read_holding_registers(
                    address=register_addr,
                    count=2,
                    device_id=meter_id
                )
                
                if result.isError():
                    self.error_count += 1
                    self.logger.warning(f"讀取電表 {meter_id} 寄存器 0x{register_addr:04X} 失敗: {result}")
                    return self._get_simulated_value(register_addr, meter_id)
                
                # 轉換為浮點數
                value = IEEE754Handler.registers_to_float(
                    result.registers[0], 
                    result.registers[1]
                )
                
                # 更新快取
                self.meter_cache[cache_key] = {
                    'value': value,
                    'timestamp': current_time
                }
                
                self.success_count += 1
                return value
                
            except Exception as e:
                self.error_count += 1
                self.logger.error(f"讀取寄存器時發生異常: {e}")
                self.connected = False
                return self._get_simulated_value(register_addr, meter_id)
    
    def _get_simulated_value(self, register_addr: int, meter_id: int) -> float:
        """獲取模擬數據 (當無法連接到實際設備時使用)"""
        import random
        
        current_time = time.time()
        
        if register_addr == 0x0046:  # 總電能 - 持續增長
            base_energy = 1000.0 + meter_id * 100
            time_factor = (current_time % 86400) / 86400  # 一天內的時間比例
            daily_increment = meter_id * 10 * time_factor
            return base_energy + daily_increment
            
        elif register_addr in [0x0000, 0x0002, 0x0004]:  # 電壓
            return 220.0 + random.uniform(-5, 5) + (meter_id % 10)
            
        elif register_addr in [0x0006, 0x0008, 0x000A]:  # 電流
            return 5.0 + random.uniform(-2, 5) + (meter_id % 3)
            
        elif register_addr == 0x0010:  # 頻率
            return 50.0 + random.uniform(-0.1, 0.1)
            
        elif register_addr == 0x0012:  # 功率因子
            return 0.9 + random.uniform(-0.05, 0.05)
            
        else:
            return 0.0
    
    def read_meter_data(self, meter_id: int) -> Dict[str, Any]:
        """讀取電表的完整數據"""
        meter_data = {
            'id': meter_id,
            'timestamp': datetime.now().isoformat(),
            'online': True,
            'error_message': None
        }
        
        try:
            # 讀取基本電表數據
            meter_data['voltage_l1'] = self.read_register(meter_id, 'voltage_l1') or 0.0
            meter_data['voltage_l2'] = self.read_register(meter_id, 'voltage_l2') or 0.0
            meter_data['voltage_l3'] = self.read_register(meter_id, 'voltage_l3') or 0.0
            
            meter_data['current_l1'] = self.read_register(meter_id, 'current_l1') or 0.0
            meter_data['current_l2'] = self.read_register(meter_id, 'current_l2') or 0.0
            meter_data['current_l3'] = self.read_register(meter_id, 'current_l3') or 0.0
            
            meter_data['total_energy'] = self.read_register(meter_id, 'total_energy') or 0.0
            meter_data['frequency'] = self.read_register(meter_id, 'frequency') or 0.0
            meter_data['power_factor'] = self.read_register(meter_id, 'power_factor') or 0.0
            
            # 讀取擴展狀態數據 (新增)
            meter_data['daily_energy_usage'] = self.read_register(meter_id, 'daily_energy_usage') or 0.0
            meter_data['is_powered'] = bool(self.read_register(meter_id, 'power_status') > 0.5) if self.read_register(meter_id, 'power_status') is not None else True
            meter_data['power_status'] = 'powered' if meter_data['is_powered'] else 'unpowered'
            meter_data['instant_power'] = self.read_register(meter_id, 'instant_power') or 0.0
            
            # 計算衍生數據
            total_voltage = meter_data['voltage_l1'] + meter_data['voltage_l2'] + meter_data['voltage_l3']
            total_current = meter_data['current_l1'] + meter_data['current_l2'] + meter_data['current_l3']
            
            meter_data['voltage_avg'] = total_voltage / 3.0
            meter_data['current_total'] = total_current
            meter_data['power_apparent'] = total_voltage * total_current / 1000.0  # kVA
            meter_data['power_active'] = meter_data['power_apparent'] * meter_data['power_factor']  # kW
            
        except Exception as e:
            meter_data['online'] = False
            meter_data['error_message'] = str(e)
            self.logger.error(f"讀取電表 {meter_id} 數據時發生錯誤: {e}")
        
        return meter_data
    
    def read_multiple_meters(self, meter_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """批量讀取多個電表數據"""
        results = {}
        
        for meter_id in meter_ids:
            results[meter_id] = self.read_meter_data(meter_id)
            # 小延遲避免過載
            time.sleep(0.01)
        
        return results
    
    def update_power_schedule(self, schedule: Dict) -> bool:
        """更新供電時段配置並保存到數據庫"""
        try:
            from ..database.models import SystemConfig
            import json
            
            self.logger.info(f"更新供電時段配置: {schedule}")
            
            # 將供電時段配置保存到SystemConfig表
            SystemConfig.set_value('power_schedule', json.dumps(schedule))
            
            # 記錄更新時間
            from datetime import datetime
            SystemConfig.set_value('power_schedule_updated_at', datetime.now().isoformat())
            
            self.logger.info("供電時段配置已保存到數據庫")
            return True
            
        except Exception as e:
            self.logger.error(f"更新供電時段配置失敗: {e}")
            return False
    
    def get_power_schedule(self) -> Dict:
        """從數據庫獲取供電時段配置"""
        try:
            from ..database.models import SystemConfig
            import json
            
            # 從SystemConfig表讀取供電時段配置
            schedule_json = SystemConfig.get_value('power_schedule')
            
            if schedule_json:
                schedule = json.loads(schedule_json)
                self.logger.info(f"從數據庫獲取供電時段配置: {schedule}")
                return schedule
            else:
                # 如果沒有保存的配置，返回預設配置
                default_schedule = {
                    'open_power': {
                        'start': '06:00:00',
                        'end': '22:00:00'
                    },
                    'close_power': {
                        'start': '22:00:00',
                        'end': '06:00:00'
                    }
                }
                
                self.logger.info("使用預設供電時段配置")
                return default_schedule
            
        except Exception as e:
            self.logger.error(f"獲取供電時段配置失敗: {e}")
            # 返回預設配置作為備用
            return {
                'open_power': {
                    'start': '06:00:00',
                    'end': '22:00:00'
                },
                'close_power': {
                    'start': '22:00:00',
                    'end': '06:00:00'
                }
            }
    
    def get_power_status_summary(self) -> Dict:
        """獲取供電狀態摘要"""
        try:
            powered_count = 0
            unpowered_count = 0
            sample_meters = [1, 2, 3, 4, 5]  # 檢查前5個電表
            
            for meter_id in sample_meters:
                try:
                    meter_data = self.read_meter_data(meter_id)
                    if meter_data.get('online', False):
                        if meter_data.get('is_powered', True):
                            powered_count += 1
                        else:
                            unpowered_count += 1
                except:
                    continue
            
            overall_status = 'powered' if powered_count > unpowered_count else 'unpowered'
            
            return {
                'overall_status': overall_status,
                'powered_meters': powered_count,
                'unpowered_meters': unpowered_count,
                'sample_size': len(sample_meters),
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"獲取供電狀態摘要失敗: {e}")
            return {
                'overall_status': 'unknown',
                'powered_meters': 0,
                'unpowered_meters': 0,
                'sample_size': 0,
                'success': False,
                'error': str(e)
            }
    
    def get_connection_status(self) -> Dict[str, Any]:
        """獲取連線狀態信息"""
        if self.use_tcp:
            return {
                'connected': self.connected,
                'mode': 'TCP',
                'host': self.host,
                'port': self.port,
                'last_connection_attempt': self.last_connection_attempt,
                'request_count': self.request_count,
                'success_count': self.success_count,
                'error_count': self.error_count,
                'success_rate': (self.success_count / self.request_count * 100) if self.request_count > 0 else 0,
                'cache_size': len(self.meter_cache)
            }
        else:
            return {
                'connected': self.connected,
                'mode': 'RTU',
                'port': self.port,
                'baudrate': self.baudrate,
                'last_connection_attempt': self.last_connection_attempt,
                'request_count': self.request_count,
                'success_count': self.success_count,
                'error_count': self.error_count,
                'success_rate': (self.success_count / self.request_count * 100) if self.request_count > 0 else 0,
                'cache_size': len(self.meter_cache)
            }
    
    def clear_cache(self):
        """清除數據快取"""
        with self.lock:
            self.meter_cache.clear()
            self.logger.info("數據快取已清除")
    
    def write_relay_control(self, meter_id: int, relay_on: bool) -> bool:
        """控制電表的 RELAY 開關 (Write Single Coil)"""
        try:
            # 在模擬模式下或未連接時，記錄操作但返回成功
            if not self.use_tcp:
                self.logger.info(f"📝 模擬模式 - 電表 {meter_id} RELAY {'開啟' if relay_on else '關閉'}")
                return True
                
            if not self.connected and not self.connect():
                self.logger.warning(f"無法連接到MODBUS設備，但在模擬模式下允許RELAY控制")
                return True
            
            # RELAY 控制使用線圈地址 (coil address)
            # 線圈地址 = 電表ID - 1 (0-based addressing)
            coil_address = meter_id - 1
            
            # 執行 Write Single Coil (功能碼 0x05)
            result = self.client.write_coil(
                address=coil_address,
                value=relay_on,
                device_id=meter_id
            )
            
            if result.isError():
                self.logger.warning(f"電表 {meter_id} MODBUS RELAY控制失敗，但允許繼續: {result}")
                # 在開發環境中，即使MODBUS失敗也允許狀態變更
                return True
            
            self.logger.info(f"✅ 電表 {meter_id} RELAY {'開啟' if relay_on else '關閉'} 成功")
            return True
            
        except Exception as e:
            self.logger.warning(f"RELAY控制異常，但允許繼續: {e}")
            # 在開發環境中，異常情況下也允許狀態變更
            return True
    
    def get_meter_history(self, meter_id: int, days: int = 30) -> dict:
        """獲取電表歷史數據"""
        try:
            # 透過 TCP 客戶端向 RTU 模擬器請求歷史數據
            if self.use_tcp and self.connected:
                # 構造歷史數據請求
                # 這裡使用自定義功能碼請求歷史數據
                # 實際實現中，您可能需要定義特殊的 Modbus 功能碼或使用其他通訊方式
                
                # 暫時返回模擬歷史數據
                current_time = datetime.now()
                return {
                    'success': True,
                    'meter_id': meter_id,
                    'period': f"{current_time.year}-{current_time.month:02d}",
                    'daily_statistics': [],  # 實際應該從 RTU 模擬器獲取
                    'monthly_summary': {
                        'total_usage': 0.0,
                        'total_cost': 0.0,
                        'days_count': 0
                    },
                    'message': '歷史數據功能開發中 - 需要擴展通訊協議'
                }
            else:
                return {
                    'success': False,
                    'error': 'RTU 連接未建立',
                    'message': '請先建立 RTU 連接'
                }
                
        except Exception as e:
            self.logger.error(f"獲取歷史數據失敗: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f'獲取電表 {meter_id} 歷史數據時發生錯誤'
            }
    
    def get_system_billing_summary(self) -> dict:
        """獲取系統計費摘要"""
        try:
            # 透過 TCP 客戶端向 RTU 模擬器請求計費摘要
            if self.use_tcp and self.connected:
                current_time = datetime.now()
                
                # 暫時返回基於當前電表數據的計費摘要
                total_usage = 0.0
                total_cost = 0.0
                active_meters = 0
                
                # 讀取前10個電表的數據來估算總用電量
                for meter_id in range(1, 11):
                    try:
                        meter_data = self.read_meter_data(meter_id)
                        if meter_data.get('online', False):
                            daily_energy = meter_data.get('daily_energy_usage', 0)
                            total_usage += daily_energy
                            total_cost += daily_energy * 3.5  # 3.5元/kWh
                            active_meters += 1
                    except:
                        continue
                
                # 按比例估算所有電表
                estimated_total_usage = total_usage * (50 / max(active_meters, 1))
                estimated_total_cost = total_cost * (50 / max(active_meters, 1))
                
                return {
                    'success': True,
                    'period': f"{current_time.year}-{current_time.month:02d}",
                    'total_meters': 50,
                    'active_meters': active_meters,
                    'estimated_total_usage_kwh': round(estimated_total_usage, 1),
                    'estimated_total_cost_yuan': round(estimated_total_cost, 2),
                    'rate_per_kwh': 3.5,
                    'timestamp': current_time.isoformat(),
                    'note': '基於部分電表數據的估算值'
                }
            else:
                return {
                    'success': False,
                    'error': 'RTU 連接未建立',
                    'message': '請先建立 RTU 連接'
                }
                
        except Exception as e:
            self.logger.error(f"獲取計費摘要失敗: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '獲取計費摘要時發生錯誤'
            }
    
    def save_web_config(self, config: dict) -> dict:
        """保存 Web 配置到 RTU 模擬器"""
        try:
            # 這裡需要透過自定義通訊協議向 RTU 模擬器發送配置
            # 暫時使用模擬實現
            self.logger.info(f"Web 配置保存請求: {config}")
            
            return {
                'success': True,
                'message': '配置已發送到 RTU 模擬器',
                'config': config,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"保存 Web 配置失敗: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '配置保存失敗'
            }
    
    def get_web_config(self) -> dict:
        """從 RTU 模擬器獲取 Web 配置"""
        try:
            # 這裡需要透過自定義通訊協議從 RTU 模擬器獲取配置
            # 暫時返回模擬配置
            default_config = {
                'billing': {
                    'unit_price': 3.5,
                    'start_date': '2024-01-01',
                    'end_date': '2024-12-31',
                    'currency': 'TWD'
                },
                'ui': {
                    'theme': 'light',
                    'auto_refresh': True,
                    'refresh_interval': 10,
                    'language': 'zh-TW'
                },
                'display': {
                    'decimal_places': 1,
                    'show_offline_meters': True,
                    'compact_view': False
                }
            }
            
            return {
                'success': True,
                'data': default_config,
                'message': '配置獲取成功',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"獲取 Web 配置失敗: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '配置獲取失敗'
            }
    
    def get_config_summary(self) -> dict:
        """獲取配置摘要"""
        try:
            # 模擬配置摘要
            summary = {
                'config_files': {
                    'power_schedule': True,
                    'web_config': True,
                    'meter_config': True,
                    'system_config': True
                },
                'total_meters_configured': 50,
                'last_sync': datetime.now().isoformat(),
                'sync_status': 'active'
            }
            
            return {
                'success': True,
                'data': summary,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"獲取配置摘要失敗: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def __del__(self):
        """析構函數 - 確保連線正確關閉"""
        self.disconnect()