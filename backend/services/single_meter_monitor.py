#!/usr/bin/env python3
"""
單電表監控服務
提供對單個電表的即時監控功能
"""

import time
import threading
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from queue import Queue, Empty

from .power_meter_controller import MeterControllerManager


class SingleMeterMonitor:
    """
    單電表監控器
    支援選擇性監控和RELAY控制
    """
    
    def __init__(self, port: str = 'COM1'):
        """
        初始化監控器
        
        Args:
            port: 串口名稱
        """
        self.port = port
        self.manager = MeterControllerManager(port)
        
        # 監控狀態
        self.current_meter_id: Optional[int] = None
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.monitor_interval = 5  # 預設5秒
        
        # 數據追踪
        self.last_energy: Optional[float] = None
        self.start_energy: Optional[float] = None
        self.total_change = 0.0
        self.start_time: Optional[datetime] = None
        
        # 數據隊列和回調
        self.data_queue = Queue()
        self.data_callback: Optional[Callable] = None
        
        logging.info("✓ 單電表監控器初始化完成")
    
    def start_monitoring(self, meter_id: int, interval: int = 5, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        開始監控指定電表
        
        Args:
            meter_id: 電表ID (1-50)
            interval: 監控間隔（秒）
            callback: 數據回調函數
            
        Returns:
            Dict: 啟動結果
        """
        if self.is_monitoring:
            return {
                'success': False,
                'error': f'正在監控電表 {self.current_meter_id}，請先停止'
            }
        
        # 驗證電表連接
        controller = self.manager.get_controller(meter_id)
        if not controller:
            return {
                'success': False,
                'error': f'無法連接到電表 {meter_id}'
            }
        
        # 設定監控參數
        self.current_meter_id = meter_id
        self.monitor_interval = interval
        self.data_callback = callback
        self.is_monitoring = True
        
        # 重置數據追踪
        self.last_energy = None
        self.start_energy = None
        self.total_change = 0.0
        self.start_time = datetime.now()
        
        # 啟動監控線程
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name=f"MeterMonitor-{meter_id}"
        )
        self.monitor_thread.start()
        
        logging.info(f"✓ 開始監控電表 {meter_id}，間隔 {interval} 秒")
        
        return {
            'success': True,
            'meter_id': meter_id,
            'interval': interval,
            'message': f'開始監控電表 {meter_id}'
        }
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """
        停止監控
        
        Returns:
            Dict: 停止結果
        """
        if not self.is_monitoring:
            return {
                'success': False,
                'error': '目前沒有在監控任何電表'
            }
        
        meter_id = self.current_meter_id
        self.is_monitoring = False
        
        # 等待監控線程結束
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
        
        # 計算監控總結
        total_time = (datetime.now() - self.start_time).total_seconds() / 60 if self.start_time else 0
        
        logging.info(f"✓ 停止監控電表 {meter_id}")
        logging.info(f"  監控時長: {total_time:.1f} 分鐘")
        logging.info(f"  總計用電變化: {self.total_change:.3f} kWh")
        
        result = {
            'success': True,
            'meter_id': meter_id,
            'total_time_minutes': round(total_time, 1),
            'total_energy_change': round(self.total_change, 3),
            'message': f'監控電表 {meter_id} 已停止'
        }
        
        # 重置狀態
        self.current_meter_id = None
        self.monitor_thread = None
        
        return result
    
    def control_relay(self, action: str) -> Dict[str, Any]:
        """
        控制當前監控電表的繼電器
        
        Args:
            action: "ON" 或 "OFF"
            
        Returns:
            Dict: 控制結果
        """
        if not self.current_meter_id:
            return {
                'success': False,
                'error': '沒有正在監控的電表'
            }
        
        return self.manager.control_meter_relay(self.current_meter_id, action)
    
    def get_current_status(self) -> Dict[str, Any]:
        """
        獲取當前監控狀態
        
        Returns:
            Dict: 監控狀態
        """
        if not self.is_monitoring:
            return {
                'is_monitoring': False,
                'message': '目前沒有監控任何電表'
            }
        
        return {
            'is_monitoring': True,
            'meter_id': self.current_meter_id,
            'interval': self.monitor_interval,
            'start_time': self.start_time.strftime('%H:%M:%S') if self.start_time else None,
            'total_change': round(self.total_change, 3),
            'monitoring_duration': round((datetime.now() - self.start_time).total_seconds() / 60, 1) if self.start_time else 0
        }
    
    def get_latest_data(self) -> Optional[Dict[str, Any]]:
        """
        獲取最新的監控數據（非阻塞）
        
        Returns:
            Dict: 最新數據或None
        """
        try:
            return self.data_queue.get_nowait()
        except Empty:
            return None
    
    def _monitor_loop(self):
        """
        監控循環（在獨立線程中執行）
        """
        logging.info(f"📊 開始監控電表 {self.current_meter_id} 的數據循環")
        
        while self.is_monitoring:
            try:
                # 獲取電表數據
                data = self.manager.get_meter_data(self.current_meter_id)
                
                if data.get('success'):
                    # 處理數據並計算變化
                    processed_data = self._process_monitor_data(data)
                    
                    # 將數據加入隊列
                    if not self.data_queue.full():
                        self.data_queue.put(processed_data)
                    
                    # 執行回調函數
                    if self.data_callback:
                        try:
                            self.data_callback(processed_data)
                        except Exception as e:
                            logging.error(f"✗ 數據回調函數執行錯誤: {e}")
                    
                    logging.debug(f"📊 電表 {self.current_meter_id}: {processed_data['energy']} kWh, {processed_data['relay_status']}")
                
                else:
                    logging.error(f"✗ 讀取電表 {self.current_meter_id} 數據失敗: {data.get('error')}")
                
                # 等待下次監控
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                logging.error(f"✗ 監控循環錯誤: {e}")
                time.sleep(self.monitor_interval)
        
        logging.info(f"📊 電表 {self.current_meter_id} 監控循環結束")
    
    def _process_monitor_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理監控數據，計算變化量
        
        Args:
            data: 原始電表數據
            
        Returns:
            Dict: 處理後的數據
        """
        current_energy = data.get('energy_raw', 0)
        
        # 初始化起始值
        if self.start_energy is None:
            self.start_energy = current_energy
        
        # 計算變化量
        if self.last_energy is not None:
            change = current_energy - self.last_energy
            change_str = f"{change:+.3f}"
        else:
            change = 0
            change_str = "---"
        
        # 計算累計變化
        self.total_change = current_energy - self.start_energy
        
        # 更新追踪值
        self.last_energy = current_energy
        
        # 返回處理後的數據
        processed_data = {
            **data,  # 包含原始數據
            'change': change,
            'change_str': change_str,
            'total_change': self.total_change,
            'total_change_str': f"{self.total_change:+.3f}",
            'formatted_data': {
                'time': data.get('timestamp', ''),
                'voltage': f"{data.get('voltage', 0):.1f}",
                'current': f"{data.get('current', 0):.2f}",
                'power': f"{data.get('power', 0):.1f}",
                'energy': f"{data.get('energy', 0):.1f}",
                'change': change_str,
                'total_change': f"{self.total_change:+.3f}",
                'relay': data.get('relay_status', '未知')
            }
        }
        
        return processed_data
    
    def cleanup(self):
        """清理資源"""
        if self.is_monitoring:
            self.stop_monitoring()
        
        self.manager.cleanup()
        logging.info("✓ 單電表監控器清理完成")


# 全局監控器實例（單例模式）
_monitor_instance: Optional[SingleMeterMonitor] = None

def get_monitor_instance(port: str = 'COM1') -> SingleMeterMonitor:
    """
    獲取監控器實例（單例模式）
    
    Args:
        port: 串口名稱
        
    Returns:
        SingleMeterMonitor: 監控器實例
    """
    global _monitor_instance
    
    if _monitor_instance is None:
        _monitor_instance = SingleMeterMonitor(port)
    
    return _monitor_instance

def cleanup_monitor():
    """清理全局監控器實例"""
    global _monitor_instance
    
    if _monitor_instance:
        _monitor_instance.cleanup()
        _monitor_instance = None