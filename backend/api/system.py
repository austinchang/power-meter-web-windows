"""
系統 API 路由 / System API routes
"""

import json
import psutil
from datetime import datetime
from flask import request, jsonify, current_app
from . import api_bp
from ..database.models import SystemConfig

# 導入智能日誌系統
try:
    from ..smart_logger import UniversalSmartLogger
    smart_logger = UniversalSmartLogger('power-meter-web')
except ImportError:
    smart_logger = None
    print("Warning: Smart Logger not available")


def get_current_power_schedule():
    """
    從資料庫讀取當前供電時段設定
    Get current power schedule from database
    """
    try:
        # 從資料庫讀取供電時段設定
        schedule_json = SystemConfig.get_value('power_schedule')
        if schedule_json:
            return json.loads(schedule_json)
        else:
            # 如果資料庫中沒有設定，返回預設值
            return current_app.config.get('DEFAULT_POWER_SCHEDULE')
    except Exception as e:
        print(f"Error reading power schedule from database: {e}")
        # 發生錯誤時返回預設值
        return current_app.config.get('DEFAULT_POWER_SCHEDULE')


@api_bp.route('/system/status', methods=['GET'])
def get_system_status():
    """
    獲取系統狀態 / Get system status
    
    Returns:
        JSON: 系統狀態信息
    """
    try:
        # 系統資源信息 / System resource information
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 應用程式信息 / Application information
        from config import APP_INFO
        
        status_data = {
            'app_info': APP_INFO,
            'system': {
                'cpu_percent': cpu_percent,
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'disk': {
                    'total': disk.total,
                    'free': disk.free,
                    'used': disk.used,
                    'percent': (disk.used / disk.total) * 100
                }
            },
            'config': {
                'meter_count': current_app.config['METER_COUNT'],
                'debug_mode': current_app.debug,
                'environment': current_app.config.get('ENV', 'development')
            },
            'uptime': {
                'started': datetime.now().isoformat(),  # TODO: 實際記錄啟動時間
                'current': datetime.now().isoformat()
            },
            'status': 'running',
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': status_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/system/update-interval', methods=['PUT'])
def update_interval():
    """更新電表數據更新間隔"""
    try:
        data = request.get_json()
        if not data or 'interval' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing interval parameter'
            }), 400
        
        interval = int(data['interval'])
        min_interval = current_app.config.get('MIN_UPDATE_INTERVAL', 5)  # Changed from 30 to 5
        max_interval = current_app.config.get('MAX_UPDATE_INTERVAL', 180)
        
        if interval < min_interval or interval > max_interval:
            return jsonify({
                'success': False,
                'error': f'Interval must be between {min_interval}-{max_interval} seconds'
            }), 400
        
        # Save to database
        SystemConfig.set_value('update_interval', str(interval))
        
        return jsonify({
            'success': True,
            'data': {
                'interval': interval,
                'min_interval': min_interval,
                'max_interval': max_interval
            },
            'message': f'更新間隔已設為 {interval} 秒'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/system/config', methods=['GET'])
def get_system_config():
    """
    獲取系統配置 / Get system configuration
    
    Returns:
        JSON: 系統配置信息
    """
    try:
        config_data = {
            'modbus': {
                'port': current_app.config.get('MODBUS_PORT'),
                'baudrate': current_app.config.get('MODBUS_BAUDRATE'),
                'timeout': current_app.config.get('MODBUS_TIMEOUT'),
                'retry_count': current_app.config.get('MODBUS_RETRY_COUNT')
            },
            'meters': {
                'start_id': current_app.config.get('METER_START_ID'),
                'end_id': current_app.config.get('METER_END_ID'),
                'count': current_app.config.get('METER_COUNT')
            },
            'intervals': {
                'real_time_update': current_app.config.get('REAL_TIME_UPDATE_INTERVAL'),
                'database_save': current_app.config.get('DATABASE_SAVE_INTERVAL'),
                'chart_update': current_app.config.get('CHART_UPDATE_INTERVAL')
            },
            'update_interval': {
                'current': int(SystemConfig.get_value('update_interval') or current_app.config.get('DEFAULT_UPDATE_INTERVAL', 30)),
                'min': current_app.config.get('MIN_UPDATE_INTERVAL', 5),  # Changed from 30 to 5
                'max': current_app.config.get('MAX_UPDATE_INTERVAL', 180)
            },
            'defaults': {
                'voltage_range': current_app.config.get('DEFAULT_VOLTAGE_RANGE'),
                'current_range': current_app.config.get('DEFAULT_CURRENT_RANGE'),
                'power_range': current_app.config.get('DEFAULT_POWER_RANGE'),
                'unit_price': current_app.config.get('DEFAULT_UNIT_PRICE')
            },
            'power_schedule': get_current_power_schedule(),
            'themes': {
                'available': current_app.config.get('AVAILABLE_THEMES'),
                'default': current_app.config.get('DEFAULT_THEME')
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': config_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/system/config', methods=['PUT'])
def update_system_config():
    """
    更新系統配置 / Update system configuration
    
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
        
        # 允許更新的配置項 / Allowed configuration items
        allowed_updates = {
            'unit_price': 'DEFAULT_UNIT_PRICE',
            'real_time_update_interval': 'REAL_TIME_UPDATE_INTERVAL',
            'database_save_interval': 'DATABASE_SAVE_INTERVAL',
            'chart_update_interval': 'CHART_UPDATE_INTERVAL',
            'default_theme': 'DEFAULT_THEME'
        }
        
        updates = {}
        for key, value in data.items():
            if key in allowed_updates:
                config_key = allowed_updates[key]
                # TODO: 實際更新配置文件或數據庫
                current_app.logger.info(f'更新配置 {config_key}: {value}')
                updates[key] = value
        
        if not updates:
            return jsonify({
                'success': False,
                'error': f'No valid configuration updates provided. Allowed: {list(allowed_updates.keys())}',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        return jsonify({
            'success': True,
            'data': {
                'updates': updates,
                'timestamp': datetime.now().isoformat()
            },
            'message': f'系統配置更新成功，已更新 {len(updates)} 項設定',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/system/power-schedule', methods=['GET'])
def get_power_schedule():
    """
    獲取供電時段設定 / Get power schedule settings
    
    Returns:
        JSON: 供電時段設定
    """
    try:
        # 使用共享的獲取函數來讀取資料庫設定
        schedule_data = get_current_power_schedule()
        
        return jsonify({
            'success': True,
            'data': schedule_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/system/power-schedule', methods=['PUT'])
def update_power_schedule():
    """
    更新供電時段設定 / Update power schedule settings
    
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
        
        # 驗證數據格式 / Validate data format
        required_fields = ['open_power', 'close_power']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}',
                    'timestamp': datetime.now().isoformat()
                }), 400
            
            if 'start' not in data[field] or 'end' not in data[field]:
                return jsonify({
                    'success': False,
                    'error': f'Missing start/end time in {field}',
                    'timestamp': datetime.now().isoformat()
                }), 400
        
        # 保存到數據庫
        current_app.logger.info(f'更新供電時段設定: {data}')
        
        from ..database.models import SystemConfig
        import json
        
        # 將時段設定保存到資料庫
        SystemConfig.set_value('power_schedule', json.dumps(data))
        
        # 記錄更新時間
        from datetime import datetime
        SystemConfig.set_value('power_schedule_updated_at', datetime.now().isoformat())
        
        return jsonify({
            'success': True,
            'data': data,
            'message': '供電時段設定更新成功',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/system/billing-period', methods=['GET'])
def get_billing_period():
    """
    獲取計費週期設定 / Get billing period settings
    
    Returns:
        JSON: 計費週期設定
    """
    try:
        # TODO: 從數據庫讀取實際設定
        billing_data = {
            'start_date': '2023-01-01',
            'end_date': '2023-12-31',
            'unit_price': current_app.config.get('DEFAULT_UNIT_PRICE', 4),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': billing_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/system/billing-period', methods=['PUT'])
def update_billing_period():
    """
    更新計費週期設定 / Update billing period settings
    
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
        
        # 驗證必要字段 / Validate required fields
        required_fields = ['start_date', 'end_date', 'unit_price']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}',
                    'timestamp': datetime.now().isoformat()
                }), 400
        
        # 驗證日期格式 / Validate date format
        try:
            datetime.strptime(data['start_date'], '%Y-%m-%d')
            datetime.strptime(data['end_date'], '%Y-%m-%d')
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 驗證單價範圍 / Validate unit price range
        unit_price = data['unit_price']
        if not isinstance(unit_price, (int, float)) or unit_price <= 0:
            return jsonify({
                'success': False,
                'error': 'Unit price must be a positive number',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # TODO: 實際保存到數據庫
        current_app.logger.info(f'更新計費週期設定: {data}')
        
        return jsonify({
            'success': True,
            'data': data,
            'message': '計費週期設定更新成功',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/system/logs', methods=['GET'])
def get_system_logs():
    """
    獲取系統日誌 / Get system logs
    
    Returns:
        JSON: 系統日誌
    """
    try:
        # 查詢參數 / Query parameters
        limit = int(request.args.get('limit', 100))
        level = request.args.get('level', 'INFO').upper()
        
        # TODO: 從日誌文件讀取實際日誌
        # 這裡返回模擬日誌數據
        logs = []
        for i in range(min(limit, 50)):
            logs.append({
                'timestamp': datetime.now().isoformat(),
                'level': level,
                'message': f'System log message {i+1}',
                'module': 'system',
                'source': 'web_api'
            })
        
        return jsonify({
            'success': True,
            'data': {
                'logs': logs,
                'count': len(logs),
                'level_filter': level,
                'limit': limit
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500