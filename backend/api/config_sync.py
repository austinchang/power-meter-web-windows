"""
配置同步 API 路由 / Configuration Sync API routes
用於跨頁面配置持久化和狀態同步
"""

from datetime import datetime
from flask import request, jsonify, current_app
from . import api_bp

# 導入智能日誌系統
try:
    from ..smart_logger import UniversalSmartLogger
    smart_logger = UniversalSmartLogger('power-meter-config')
except ImportError:
    smart_logger = None
    print("Warning: Smart Logger not available for config module")


@api_bp.route('/config/web', methods=['GET'])
def get_web_config():
    """
    獲取 Web 介面配置 / Get web interface configuration
    
    Returns:
        JSON: Web 介面配置數據
    """
    try:
        from ..modbus.rtu_client import ModbusRTUClient
        
        # 創建 RTU 客戶端
        rtu_config = {
            'rtu_port': current_app.config['RTU_PORT'],
            'baudrate': current_app.config['RTU_BAUDRATE'],
            'timeout': current_app.config['RTU_TIMEOUT'],
            'RTU_SIMULATOR_PORT': current_app.config.get('RTU_SIMULATOR_PORT', 5502)
        }
        
        rtu_client = ModbusRTUClient(rtu_config)
        config_data = rtu_client.get_web_config()
        
        if config_data.get('success', False):
            return jsonify({
                'success': True,
                'data': config_data['data'],
                'message': '配置獲取成功',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': config_data.get('error', '配置獲取失敗'),
                'message': config_data.get('message', ''),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '獲取 Web 配置時發生系統錯誤',
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/config/web', methods=['POST', 'PUT'])
def save_web_config():
    """
    保存 Web 介面配置 / Save web interface configuration
    
    Request Body:
        {
            "billing": {
                "unit_price": 3.5,
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            },
            "ui": {
                "theme": "light",
                "auto_refresh": true,
                "refresh_interval": 10
            },
            "display": {
                "decimal_places": 1,
                "show_offline_meters": true
            }
        }
        
    Returns:
        JSON: 保存結果
    """
    try:
        config_data = request.get_json()
        
        if not config_data:
            return jsonify({
                'success': False,
                'error': '請提供配置數據',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 驗證必要的配置項
        required_sections = ['billing', 'ui', 'display']
        for section in required_sections:
            if section not in config_data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必要的配置區段: {section}',
                    'timestamp': datetime.now().isoformat()
                }), 400
        
        from ..modbus.rtu_client import ModbusRTUClient
        
        # 創建 RTU 客戶端
        rtu_config = {
            'rtu_port': current_app.config['RTU_PORT'],
            'baudrate': current_app.config['RTU_BAUDRATE'],
            'timeout': current_app.config['RTU_TIMEOUT'],
            'RTU_SIMULATOR_PORT': current_app.config.get('RTU_SIMULATOR_PORT', 5502)
        }
        
        rtu_client = ModbusRTUClient(rtu_config)
        save_result = rtu_client.save_web_config(config_data)
        
        if save_result.get('success', False):
            return jsonify({
                'success': True,
                'data': save_result['config'],
                'message': '配置保存成功',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': save_result.get('error', '配置保存失敗'),
                'message': save_result.get('message', ''),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '保存 Web 配置時發生系統錯誤',
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/config/power-schedule', methods=['GET'])
def get_power_schedule_config():
    """
    獲取供電時段配置 / Get power schedule configuration
    
    Returns:
        JSON: 供電時段配置
    """
    try:
        from ..modbus.rtu_client import ModbusRTUClient
        
        # 創建 RTU 客戶端
        rtu_config = {
            'rtu_port': current_app.config['RTU_PORT'],
            'baudrate': current_app.config['RTU_BAUDRATE'],
            'timeout': current_app.config['RTU_TIMEOUT'],
            'RTU_SIMULATOR_PORT': current_app.config.get('RTU_SIMULATOR_PORT', 5502)
        }
        
        rtu_client = ModbusRTUClient(rtu_config)
        schedule = rtu_client.get_power_schedule()
        
        return jsonify({
            'success': True,
            'data': {
                'schedule': schedule,
                'enabled': True,
                'timezone': 'Asia/Taipei'
            },
            'message': '供電時段配置獲取成功',
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '獲取供電時段配置時發生錯誤',
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/config/power-schedule', methods=['POST', 'PUT'])
def save_power_schedule_config():
    """
    保存供電時段配置 / Save power schedule configuration
    
    Request Body:
        {
            "open_power": {
                "start": "00:05:00",
                "end": "22:05:00"
            },
            "close_power": {
                "start": "15:56:00",
                "end": "21:55:00"
            }
        }
        
    Returns:
        JSON: 保存結果
    """
    try:
        schedule_data = request.get_json()
        
        if not schedule_data:
            return jsonify({
                'success': False,
                'error': '請提供供電時段配置數據',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 驗證必要的配置項
        required_keys = ['open_power', 'close_power']
        for key in required_keys:
            if key not in schedule_data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必要的時段配置: {key}',
                    'timestamp': datetime.now().isoformat()
                }), 400
            
            if 'start' not in schedule_data[key] or 'end' not in schedule_data[key]:
                return jsonify({
                    'success': False,
                    'error': f'{key} 時段缺少 start 或 end 時間',
                    'timestamp': datetime.now().isoformat()
                }), 400
        
        from ..modbus.rtu_client import ModbusRTUClient
        
        # 創建 RTU 客戶端
        rtu_config = {
            'rtu_port': current_app.config['RTU_PORT'],
            'baudrate': current_app.config['RTU_BAUDRATE'],
            'timeout': current_app.config['RTU_TIMEOUT'],
            'RTU_SIMULATOR_PORT': current_app.config.get('RTU_SIMULATOR_PORT', 5502)
        }
        
        rtu_client = ModbusRTUClient(rtu_config)
        success = rtu_client.update_power_schedule(schedule_data)
        
        if success:
            return jsonify({
                'success': True,
                'data': {
                    'schedule': schedule_data,
                    'enabled': True
                },
                'message': '供電時段配置保存成功',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': '供電時段配置保存失敗',
                'message': '無法更新 RTU 模擬器配置',
                'timestamp': datetime.now().isoformat()
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '保存供電時段配置時發生系統錯誤',
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/config/summary', methods=['GET'])
def get_config_summary():
    """
    獲取配置摘要 / Get configuration summary
    
    Returns:
        JSON: 配置摘要信息
    """
    try:
        from ..modbus.rtu_client import ModbusRTUClient
        
        # 創建 RTU 客戶端
        rtu_config = {
            'rtu_port': current_app.config['RTU_PORT'],
            'baudrate': current_app.config['RTU_BAUDRATE'],
            'timeout': current_app.config['RTU_TIMEOUT'],
            'RTU_SIMULATOR_PORT': current_app.config.get('RTU_SIMULATOR_PORT', 5502)
        }
        
        rtu_client = ModbusRTUClient(rtu_config)
        summary_data = rtu_client.get_config_summary()
        
        if summary_data.get('success', False):
            return jsonify({
                'success': True,
                'data': summary_data['data'],
                'message': '配置摘要獲取成功',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': summary_data.get('error', '配置摘要獲取失敗'),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '獲取配置摘要時發生系統錯誤',
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/config/sync-status', methods=['GET'])
def get_sync_status():
    """
    獲取配置同步狀態 / Get configuration sync status
    
    Returns:
        JSON: 同步狀態信息
    """
    try:
        # 模擬同步狀態數據
        current_time = datetime.now()
        
        sync_status = {
            'last_sync': current_time.isoformat(),
            'sync_enabled': True,
            'auto_sync_interval': 30,  # 秒
            'pending_changes': 0,
            'sync_errors': 0,
            'components': {
                'power_schedule': {
                    'last_sync': current_time.isoformat(),
                    'status': 'synced',
                    'changes': 0
                },
                'web_config': {
                    'last_sync': current_time.isoformat(),
                    'status': 'synced',
                    'changes': 0
                },
                'meter_config': {
                    'last_sync': current_time.isoformat(),
                    'status': 'synced',
                    'changes': 0
                }
            }
        }
        
        return jsonify({
            'success': True,
            'data': sync_status,
            'message': '同步狀態獲取成功',
            'timestamp': current_time.isoformat()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '獲取同步狀態時發生錯誤',
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/config/export', methods=['GET'])
def export_config():
    """
    導出所有配置 / Export all configurations
    
    Returns:
        JSON: 所有配置數據
    """
    try:
        from ..modbus.rtu_client import ModbusRTUClient
        
        # 創建 RTU 客戶端
        rtu_config = {
            'rtu_port': current_app.config['RTU_PORT'],
            'baudrate': current_app.config['RTU_BAUDRATE'],
            'timeout': current_app.config['RTU_TIMEOUT'],
            'RTU_SIMULATOR_PORT': current_app.config.get('RTU_SIMULATOR_PORT', 5502)
        }
        
        rtu_client = ModbusRTUClient(rtu_config)
        
        # 獲取各種配置
        web_config = rtu_client.get_web_config()
        power_schedule = rtu_client.get_power_schedule()
        
        export_data = {
            'export_info': {
                'version': '1.0.0',
                'export_time': datetime.now().isoformat(),
                'source': 'Power Meter Web Edition'
            },
            'web_config': web_config.get('data', {}) if web_config.get('success') else {},
            'power_schedule': {
                'schedule': power_schedule,
                'enabled': True,
                'timezone': 'Asia/Taipei'
            },
            'system_info': {
                'meter_count': current_app.config.get('METER_COUNT', 50),
                'rtu_enabled': current_app.config.get('RTU_ENABLED', False),
                'tcp_port': current_app.config.get('RTU_SIMULATOR_PORT', 5502)
            }
        }
        
        return jsonify({
            'success': True,
            'data': export_data,
            'message': '配置導出成功',
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '配置導出時發生錯誤',
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/config/import', methods=['POST'])
def import_config():
    """
    導入配置 / Import configurations
    
    Request Body:
        {
            "web_config": {...},
            "power_schedule": {...},
            "system_info": {...}
        }
        
    Returns:
        JSON: 導入結果
    """
    try:
        import_data = request.get_json()
        
        if not import_data:
            return jsonify({
                'success': False,
                'error': '請提供要導入的配置數據',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        from ..modbus.rtu_client import ModbusRTUClient
        
        # 創建 RTU 客戶端
        rtu_config = {
            'rtu_port': current_app.config['RTU_PORT'],
            'baudrate': current_app.config['RTU_BAUDRATE'],
            'timeout': current_app.config['RTU_TIMEOUT'],
            'RTU_SIMULATOR_PORT': current_app.config.get('RTU_SIMULATOR_PORT', 5502)
        }
        
        rtu_client = ModbusRTUClient(rtu_config)
        
        import_results = []
        success_count = 0
        
        # 導入 Web 配置
        if 'web_config' in import_data:
            web_result = rtu_client.save_web_config(import_data['web_config'])
            import_results.append({
                'type': 'web_config',
                'success': web_result.get('success', False),
                'message': web_result.get('message', '')
            })
            if web_result.get('success', False):
                success_count += 1
        
        # 導入供電時段配置  
        if 'power_schedule' in import_data and 'schedule' in import_data['power_schedule']:
            power_result = rtu_client.update_power_schedule(import_data['power_schedule']['schedule'])
            import_results.append({
                'type': 'power_schedule',
                'success': power_result,
                'message': '供電時段配置導入' + ('成功' if power_result else '失敗')
            })
            if power_result:
                success_count += 1
        
        return jsonify({
            'success': success_count > 0,
            'data': {
                'total_imported': success_count,
                'results': import_results
            },
            'message': f'配置導入完成，成功導入 {success_count} 項配置',
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '配置導入時發生系統錯誤',
            'timestamp': datetime.now().isoformat()
        }), 500