"""
MODBUS TCP 客戶端
連接到 TCP 版本的電表模擬器
"""

from pymodbus.client import ModbusTcpClient
import struct
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ModbusTCPClient:
    """MODBUS TCP 客戶端"""
    
    def __init__(self, host='localhost', port=5502):
        self.host = host
        self.port = port
        self.client = None
        self.connected = False
        
    def connect(self) -> bool:
        """連接到 MODBUS TCP 伺服器"""
        try:
            self.client = ModbusTcpClient(self.host, port=self.port)
            self.connected = self.client.connect()
            
            if self.connected:
                logger.info(f"✅ 連接到 MODBUS TCP 伺服器 {self.host}:{self.port}")
            else:
                logger.error("❌ 無法連接到 MODBUS TCP 伺服器")
                
            return self.connected
            
        except Exception as e:
            logger.error(f"連接錯誤: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """斷開連接"""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("已斷開 MODBUS TCP 連接")
    
    def registers_to_float(self, reg1: int, reg2: int) -> float:
        """將兩個寄存器轉換為浮點數"""
        packed = struct.pack('>HH', reg1, reg2)
        return struct.unpack('>f', packed)[0]
    
    def read_meter_data(self, meter_id: int) -> Optional[Dict[str, Any]]:
        """讀取電表數據"""
        if not self.connected:
            if not self.connect():
                return None
        
        try:
            # 讀取累積電能 (地址 0x0046)
            result = self.client.read_holding_registers(
                address=0x0046,
                count=2,
                slave=meter_id
            )
            
            if result.isError():
                logger.error(f"讀取電表 {meter_id} 失敗")
                return None
            
            # 轉換電能數據
            total_energy = self.registers_to_float(result.registers[0], result.registers[1])
            
            # 讀取電壓 (地址 0x0000)
            voltage_result = self.client.read_holding_registers(
                address=0x0000,
                count=2,
                slave=meter_id
            )
            
            voltage_l1 = 220.0  # 預設值
            if not voltage_result.isError():
                voltage_l1 = self.registers_to_float(
                    voltage_result.registers[0], 
                    voltage_result.registers[1]
                )
            
            # 讀取功率 (地址 0x0050)
            power_result = self.client.read_holding_registers(
                address=0x0050,
                count=2,
                slave=meter_id
            )
            
            current_power = 3.3  # 預設值
            if not power_result.isError():
                current_power = self.registers_to_float(
                    power_result.registers[0],
                    power_result.registers[1]
                )
            
            # 返回數據
            data = {
                'id': meter_id,
                'total_energy': total_energy,
                'voltage_l1': voltage_l1,
                'voltage_l2': voltage_l1,
                'voltage_l3': voltage_l1,
                'current_l1': 5.0,
                'current_l2': 5.0,
                'current_l3': 5.0,
                'current_power': current_power,
                'power_factor': 0.95,
                'frequency': 50.0,
                'status': 'online',
                'last_update': datetime.now().isoformat()
            }
            
            return data
            
        except Exception as e:
            logger.error(f"讀取電表 {meter_id} 數據時發生錯誤: {e}")
            return None
    
    def test_connection(self) -> bool:
        """測試連接"""
        try:
            # 嘗試讀取電表 1
            data = self.read_meter_data(1)
            return data is not None
        except:
            return False

# 全局 TCP 客戶端實例
tcp_client = ModbusTCPClient()

def get_tcp_client():
    """獲取 TCP 客戶端實例"""
    return tcp_client