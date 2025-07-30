#!/usr/bin/env python3
"""
RTU 相關 API 端點
專門處理 MODBUS RTU 連線管理和配置
"""

import glob
from datetime import datetime
from flask import request, jsonify, current_app
from . import api_bp
from ..services.power_meter_controller_minimal import get_power_meter_controller

@api_bp.route('/rtu/status', methods=['GET'])
def get_rtu_status():
    """
    獲取 RTU 連線狀態
    
    Returns:
        JSON: RTU 連線狀態信息
    """
    try:
        rtu_enabled = current_app.config.get('RTU_ENABLED', False)
        
        if not rtu_enabled:
            return jsonify({
                'success': True,
                'data': {
                    'enabled': False,
                    'message': 'RTU 功能未啟用'
                },
                'timestamp': datetime.now().isoformat()
            })
        
        # 獲取電表控制器實例
        port = current_app.config.get('RTU_PORT', 'COM1')
        slave_address = int(current_app.config.get('RTU_SLAVE_ADDRESS', '2'))
        controller = get_power_meter_controller(port, slave_address)
        status = controller.get_connection_status()
        
        return jsonify({
            'success': True,
            'data': {
                'enabled': True,
                'connected': status['connected'],
                'mode': status['mode'],
                'port': status['port'],
                'slave_address': status['slave_address'],
                'baudrate': status['baudrate'],
                'parity': status['parity'],
                'bytesize': status['bytesize'],
                'stopbits': status['stopbits'],
                'timeout': status['timeout'],
                'request_count': status['request_count'],
                'success_count': status['success_count'],
                'error_count': status['error_count'],
                'success_rate': status['success_rate'],
                'has_minimalmodbus': status['has_minimalmodbus'],
                'force_simulation': status['force_simulation']
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"獲取 RTU 狀態時發生錯誤: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/rtu/reconnect', methods=['POST'])
def reconnect_rtu():
    """
    重新連接 RTU 設備
    
    Returns:
        JSON: 連接結果
    """
    try:
        rtu_enabled = current_app.config.get('RTU_ENABLED', False)
        
        if not rtu_enabled:
            return jsonify({
                'success': False,
                'error': 'RTU 功能未啟用',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 獲取電表控制器實例
        port = current_app.config.get('RTU_PORT', 'COM1')
        slave_address = int(current_app.config.get('RTU_SLAVE_ADDRESS', '2'))
        controller = get_power_meter_controller(port, slave_address)
        
        # 測試連接狀態
        status = controller.get_connection_status()
        connected = status['connected']
        
        return jsonify({
            'success': True,
            'data': {
                'connected': connected,
                'message': 'RTU 控制器狀態已檢查',
                'mode': status['mode']
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"重新連接 RTU 時發生錯誤: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/rtu/cache/clear', methods=['POST'])
def clear_rtu_cache():
    """
    清除 RTU 數據快取
    
    Returns:
        JSON: 操作結果
    """
    try:
        rtu_enabled = current_app.config.get('RTU_ENABLED', False)
        
        if not rtu_enabled:
            return jsonify({
                'success': False,
                'error': 'RTU 功能未啟用',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # minimalmodbus 控制器沒有快取機制，返回成功狀態
        return jsonify({
            'success': True,
            'data': {
                'message': 'minimalmodbus 控制器無需清除快取'
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"清除 RTU 快取時發生錯誤: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/meters/config', methods=['GET'])
def get_meters_config():
    """
    獲取電表配置信息
    
    Returns:
        JSON: 電表配置數據
    """
    try:
        config_data = {
            'meter_count': current_app.config.get('METER_COUNT', 50),
            'rtu_enabled': current_app.config.get('RTU_ENABLED', False),
            'rtu_port': current_app.config.get('RTU_PORT', '/dev/ttyUSB0'),
            'rtu_baudrate': current_app.config.get('RTU_BAUDRATE', 9600),
            'unit_price': current_app.config.get('DEFAULT_UNIT_PRICE', 3.5),
            'cache_expiry': current_app.config.get('RTU_CACHE_EXPIRY', 5),
            'available_ports': _get_available_serial_ports(),
            'rtu_config': {
                'bytesize': current_app.config.get('RTU_BYTESIZE', 8),
                'parity': current_app.config.get('RTU_PARITY', 'N'),
                'stopbits': current_app.config.get('RTU_STOPBITS', 1),
                'timeout': current_app.config.get('RTU_TIMEOUT', 1.0)
            }
        }
        
        return jsonify({
            'success': True,
            'data': config_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"獲取電表配置時發生錯誤: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/meters/config', methods=['PUT'])
def update_meters_config():
    """
    更新電表配置
    
    Returns:
        JSON: 更新結果
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 可更新的配置項
        updatable_configs = {
            'RTU_ENABLED': 'rtu_enabled',
            'RTU_PORT': 'rtu_port',
            'RTU_BAUDRATE': 'rtu_baudrate',
            'DEFAULT_UNIT_PRICE': 'unit_price',
            'RTU_CACHE_EXPIRY': 'cache_expiry',
            'RTU_BYTESIZE': 'rtu_bytesize',
            'RTU_PARITY': 'rtu_parity',
            'RTU_STOPBITS': 'rtu_stopbits',
            'RTU_TIMEOUT': 'rtu_timeout'
        }
        
        updates = {}
        for config_key, data_key in updatable_configs.items():
            if data_key in data:
                updates[config_key] = data[data_key]
                current_app.config[config_key] = data[data_key]
        
        if not updates:
            return jsonify({
                'success': False,
                'error': 'No valid configuration updates provided',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 如果更新了 RTU 配置，需要重新初始化客戶端
        rtu_config_keys = ['RTU_PORT', 'RTU_BAUDRATE', 'RTU_BYTESIZE', 'RTU_PARITY', 'RTU_STOPBITS', 'RTU_TIMEOUT']
        if any(key in updates for key in rtu_config_keys):
            global _rtu_client
            from .meters import _rtu_client
            if _rtu_client:
                _rtu_client.disconnect()
                _rtu_client = None  # 強制重新創建
        
        current_app.logger.info(f"更新電表配置: {updates}")
        
        return jsonify({
            'success': True,
            'data': {
                'updates': updates,
                'message': '配置更新成功'
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"更新電表配置時發生錯誤: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


def _get_available_serial_ports():
    """獲取可用的串列埠清單"""
    ports = []
    
    # Linux/Unix 系統的常見串列埠
    for port_pattern in ['/dev/ttyUSB*', '/dev/ttyACM*', '/dev/ttyS*']:
        ports.extend(glob.glob(port_pattern))
    
    # Windows 系統的串列埠 (如果需要)
    try:
        import serial.tools.list_ports
        available_ports = [port.device for port in serial.tools.list_ports.comports()]
        ports.extend(available_ports)
    except ImportError:
        pass
    
    return sorted(list(set(ports)))