"""
Power Meter GUI Professional - Web Edition 主應用程式
Main application for Web Edition with Flask + Socket.IO
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS

from config import get_config, APP_INFO
from backend.database import db, init_database
from backend.services import meter_service


def create_app(config_name=None):
    """
    創建 Flask 應用程式 / Create Flask application
    
    Args:
        config_name (str): Configuration name
        
    Returns:
        Flask: Flask application instance
    """
    app = Flask(__name__, 
                template_folder='frontend/templates',
                static_folder='frontend/static')
    
    # 載入配置 / Load configuration
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    
    # 設置日誌 / Setup logging
    setup_logging(app)
    
    # 初始化擴展 / Initialize extensions
    db.init_app(app)
    socketio = SocketIO(
        app,
        cors_allowed_origins=app.config['SOCKETIO_CORS_ALLOWED_ORIGINS'],
        async_mode=app.config['SOCKETIO_ASYNC_MODE'],
        logger=app.config['SOCKETIO_LOGGER'],
        engineio_logger=app.config['SOCKETIO_ENGINEIO_LOGGER']
    )
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # 初始化數據庫 / Initialize database
    init_database(app)
    
    # 註冊藍圖 / Register blueprints
    register_blueprints(app)
    
    # 註冊 Socket.IO 事件 / Register Socket.IO events
    register_socket_events(socketio)
    
    # 添加模板全局變量 / Add template global variables
    register_template_globals(app)
    
    # 註冊錯誤處理器 / Register error handlers
    register_error_handlers(app)
    
    return app, socketio


def setup_logging(app):
    """設置日誌系統 / Setup logging system"""
    if not app.debug:
        # 生產環境日誌設定 / Production logging setup
        file_handler = logging.FileHandler(app.config['LOG_FILE'])
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Power Meter Web Edition startup')


def register_blueprints(app):
    """註冊藍圖 / Register blueprints"""
    from backend.api import api_bp
    from backend.socket_handlers import socket_bp
    from backend.routes.monitor import monitor_bp
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(socket_bp)
    app.register_blueprint(monitor_bp)


def register_socket_events(socketio):
    """註冊 Socket.IO 事件 / Register Socket.IO events"""
    
    @socketio.on('connect')
    def handle_connect():
        """客戶端連接事件 / Client connect event"""
        print(f'Client connected: {request.sid}')
        emit('status', {'message': 'Connected to Power Meter Web Edition'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """客戶端斷開事件 / Client disconnect event"""
        print(f'Client disconnected: {request.sid}')
    
    @socketio.on('join_room')
    def handle_join_room(data):
        """加入房間事件 / Join room event"""
        room = data.get('room', 'default')
        join_room(room)
        emit('status', {'message': f'Joined room: {room}'})
    
    @socketio.on('leave_room')
    def handle_leave_room(data):
        """離開房間事件 / Leave room event"""
        room = data.get('room', 'default')
        leave_room(room)
        emit('status', {'message': f'Left room: {room}'})
    
    @socketio.on('request_meter_data')
    def handle_meter_data_request(data):
        """請求電表數據事件 / Request meter data event"""
        print(f"Handling meter data request: {data}")
        
        request_id = data.get('request_id')
        all_meters = data.get('all_meters', False)
        meter_id = data.get('meter_id')
        
        # 檢查並自動重置每日用電量
        meter_service.check_and_auto_reset_daily()
        
        # 使用 RTU 客戶端獲取真實數據
        try:
            from backend.modbus.rtu_client import ModbusRTUClient
            
            # 創建 RTU 客戶端 (支援 TCP)
            rtu_config = {
                'rtu_port': app.config['RTU_PORT'],
                'baudrate': app.config['RTU_BAUDRATE'],
                'bytesize': app.config['RTU_BYTESIZE'],
                'parity': app.config['RTU_PARITY'],
                'stopbits': app.config['RTU_STOPBITS'],
                'timeout': app.config['RTU_TIMEOUT'],
                'cache_expiry': app.config['RTU_CACHE_EXPIRY'],
                'RTU_SIMULATOR_PORT': app.config.get('RTU_SIMULATOR_PORT', 5502)
            }
            
            rtu_client = ModbusRTUClient(rtu_config)
            rtu_enabled = app.config.get('RTU_ENABLED', False)
            
        except ImportError:
            print("Warning: RTU client not available, using mock data")
            rtu_client = None
            rtu_enabled = False
        
        if all_meters:
            # 返回所有電表數據
            all_meter_data = []
            meter_count = app.config.get('METER_COUNT', 50)
            meters_to_save = []  # 用於批量保存到數據庫
            
            # 檢查當前供電時段
            current_power_active = meter_service.is_power_schedule_active('open_power')
            
            if rtu_enabled and rtu_client:
                # 使用 RTU 客戶端批量讀取
                meter_ids = list(range(1, meter_count + 1))
                meter_data_dict = rtu_client.read_multiple_meters(meter_ids)
                
                for i in range(1, meter_count + 1):
                    if i in meter_data_dict and meter_data_dict[i].get('online', False):
                        raw_data = meter_data_dict[i]
                        
                        # 從數據庫獲取持久化數據
                        db_meter = meter_service.get_meter_current_data(i)
                        
                        # 根據供電時段決定實際供電狀態
                        actual_power_on = current_power_active and raw_data.get('is_powered', True)
                        actual_power_status = 'powered' if actual_power_on else 'unpowered'
                        actual_status = 'online' if actual_power_on else 'powered_off'
                        
                        # 準備保存到數據庫的數據
                        save_data = {
                            'meter_id': i,
                            'name': f'RTU電表{i:02d}',
                            'parking': f'RTU-{i:04d}',
                            'voltage': round(raw_data.get('voltage_avg', 0), 1) if actual_power_on else 0.0,
                            'current': round(raw_data.get('current_total', 0), 1) if actual_power_on else 0.0,
                            'power': round(raw_data.get('instant_power', raw_data.get('power_active', 0)), 1) if actual_power_on else 0.0,
                            'energy': round(raw_data.get('total_energy', 0), 1),
                            'power_on': actual_power_on,
                            'power_status': actual_power_status
                        }
                        meters_to_save.append(save_data)
                        
                        # 準備返回給前端的數據 (使用數據庫的累積數據)
                        meter_data = {
                            'id': i,
                            'meter_id': i,
                            'name': f'RTU電表{i:02d}',
                            'parking': f'RTU-{i:04d}',
                            'status': actual_status,
                            'power_on': actual_power_on,
                            'voltage': round(raw_data.get('voltage_avg', 0), 1) if actual_power_on else 0.0,
                            'current': round(raw_data.get('current_total', 0), 1) if actual_power_on else 0.0,
                            'power': round(raw_data.get('instant_power', raw_data.get('power_active', 0)), 1) if actual_power_on else 0.0,
                            'energy': round(raw_data.get('total_energy', 0), 1),
                            'daily_energy': db_meter['daily_energy'] if db_meter else 0.0,
                            'cost_today': db_meter['cost_today'] if db_meter else 0.0,
                            'power_status': actual_power_status,
                            'timestamp': raw_data.get('timestamp', datetime.now().isoformat())
                        }
                    else:
                        # 電表離線，從數據庫獲取最後已知狀態
                        db_meter = meter_service.get_meter_current_data(i)
                        
                        # 離線時按供電時段決定狀態顯示
                        offline_power_status = 'powered' if current_power_active else 'unpowered'
                        offline_status = 'offline'
                        
                        if db_meter:
                            meter_data = db_meter.copy()
                            meter_data.update({
                                'status': offline_status,
                                'power_on': current_power_active,
                                'voltage': 0.0,  # 離線時無電壓
                                'current': 0.0,  # 離線時無電流
                                'power': 0.0,    # 離線時無功率
                                'power_status': offline_power_status
                            })
                        else:
                            # 創建默認離線數據
                            meter_data = {
                                'id': i,
                                'meter_id': i,
                                'name': f'RTU電表{i:02d}',
                                'parking': f'RTU-{i:04d}',
                                'status': offline_status,
                                'power_on': current_power_active,
                                'voltage': 0.0,
                                'current': 0.0,
                                'power': 0.0,
                                'energy': 0.0,
                                'daily_energy': 0.0,
                                'cost_today': 0.0,
                                'power_status': offline_power_status,
                                'timestamp': datetime.now().isoformat()
                            }
                    
                    all_meter_data.append(meter_data)
            else:
                # 模擬模式：從數據庫獲取持久化數據，如果沒有則使用模擬數據
                for i in range(1, meter_count + 1):
                    db_meter = meter_service.get_meter_current_data(i)
                    
                    # 模擬模式也要按供電時段決定狀態
                    simulated_power_status = 'powered' if current_power_active else 'unpowered'
                    simulated_status = 'simulated'
                    
                    if db_meter:
                        # 使用數據庫中的持久化數據
                        meter_data = db_meter.copy()
                        meter_data.update({
                            'status': simulated_status,
                            'power_on': current_power_active,
                            'voltage': (220.0 + (i % 10)) if current_power_active else 0.0,
                            'current': (15.0 + (i % 5)) if current_power_active else 0.0,
                            'power': (3300.0 + (i * 10)) if current_power_active else 0.0,
                            'power_status': simulated_power_status
                        })
                    else:
                        # 創建模擬數據並保存到數據庫
                        meter_data = {
                            'id': i,
                            'meter_id': i,
                            'name': f'RTU電表{i:02d}',
                            'parking': f'RTU-{i:04d}',
                            'status': simulated_status,
                            'power_on': current_power_active,
                            'voltage': (220.0 + (i % 10)) if current_power_active else 0.0,
                            'current': (15.0 + (i % 5)) if current_power_active else 0.0,
                            'power': (3300.0 + (i * 10)) if current_power_active else 0.0,
                            'energy': i * 50.5,
                            'daily_energy': 0.0,
                            'cost_today': 0.0,
                            'power_status': simulated_power_status,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        # 保存到數據庫
                        meter_service.save_meter_data(meter_data)
                    
                    all_meter_data.append(meter_data)
            
            # 批量保存 RTU 數據到數據庫
            if meters_to_save:
                meter_service.batch_save_meters(meters_to_save)
            
            emit('meter_data_response', {
                'request_id': request_id,
                'success': True,
                'data': all_meter_data,
                'rtu_enabled': rtu_enabled,
                'connection_status': rtu_client.get_connection_status() if rtu_client else {},
                'timestamp': datetime.now().isoformat()
            })
            print(f"Sent all meter data response for request {request_id}")
        
        elif meter_id:
            # 返回單個電表數據
            if rtu_enabled and rtu_client:
                raw_data = rtu_client.read_meter_data(meter_id)
                
                if raw_data.get('online', False):
                    # 計算金額：每日用電量 × 電價（3.5元/kWh）
                    daily_energy = round(raw_data.get('daily_energy_usage', 0), 1)
                    cost_today = round(daily_energy * 3.5, 2)
                    
                    meter_data = {
                        'id': meter_id,
                        'meter_id': meter_id,
                        'name': f'RTU電表{meter_id:02d}',
                        'parking': f'RTU-{meter_id:04d}',
                        'status': 'online' if raw_data.get('is_powered', True) else 'powered_off',
                        'power_on': raw_data.get('is_powered', True),
                        'voltage': round(raw_data.get('voltage_avg', 0), 1),
                        'current': round(raw_data.get('current_total', 0), 1),
                        'power': round(raw_data.get('instant_power', raw_data.get('power_active', 0)), 1),
                        'energy': round(raw_data.get('total_energy', 0), 1),
                        'daily_energy': daily_energy,  # RTU模擬器提供的真實每日用電量
                        'cost_today': cost_today,      # Web介面計算的金額
                        'power_status': raw_data.get('power_status', 'powered'),
                        'timestamp': raw_data.get('timestamp')
                    }
                else:
                    meter_data = {
                        'id': meter_id,
                        'meter_id': meter_id,
                        'name': f'RTU電表{meter_id:02d}',
                        'parking': f'RTU-{meter_id:04d}',
                        'status': 'offline',
                        'power_on': False,
                        'voltage': 0.0,
                        'current': 0.0,
                        'power': 0.0,
                        'energy': 0.0,
                        'daily_energy': 0.0,
                        'cost_today': 0.0,
                        'timestamp': datetime.now().isoformat()
                    }
            else:
                # 使用模擬數據
                meter_data = {
                    'id': meter_id,
                    'meter_id': meter_id,
                    'name': f'A{meter_id}' if meter_id <= 42 else f'備{meter_id-42}',
                    'parking': f'ABC-{meter_id:04d}',
                    'status': 'simulated',
                    'power_on': True,
                    'voltage': 220.0 + (meter_id % 10),
                    'current': 15.0 + (meter_id % 5),
                    'power': 3300.0 + (meter_id * 10),
                    'energy': meter_id * 50.5,
                    'daily_energy': meter_id * 12.5,
                    'cost_today': (meter_id * 12.5) * 4,
                    'timestamp': datetime.now().isoformat()
                }
            
            emit('meter_data', meter_data)
            print(f"Sent single meter data for meter {meter_id}")
    
    @socketio.on('update_meter_config')
    def handle_meter_config_update(data):
        """更新電表配置事件 / Update meter config event"""
        meter_id = data.get('meter_id')
        config = data.get('config', {})
        
        # TODO: 實際更新電表配置
        print(f'Updating meter {meter_id} config: {config}')
        emit('config_updated', {
            'meter_id': meter_id,
            'status': 'success',
            'message': 'Configuration updated successfully'
        })
    
    @socketio.on('rtu_connect')
    def handle_rtu_connect(data):
        """RTU 連接事件 / RTU connect event"""
        try:
            from backend.modbus.rtu_client import ModbusRTUClient
            
            # 創建或重新連接 RTU 客戶端
            rtu_config = {
                'rtu_port': app.config['RTU_PORT'],
                'baudrate': app.config['RTU_BAUDRATE'],
                'bytesize': app.config['RTU_BYTESIZE'],
                'parity': app.config['RTU_PARITY'],
                'stopbits': app.config['RTU_STOPBITS'],
                'timeout': app.config['RTU_TIMEOUT'],
                'cache_expiry': app.config['RTU_CACHE_EXPIRY']
            }
            
            rtu_client = ModbusRTUClient(rtu_config)
            success = rtu_client.connect()
            
            status = rtu_client.get_connection_status()
            
            emit('rtu_connection_status', {
                'connected': success,
                'status': status,
                'message': '連接成功' if success else '連接失敗',
                'timestamp': datetime.now().isoformat()
            })
            
            print(f"RTU connection attempt: {'success' if success else 'failed'}")
            
        except Exception as e:
            emit('rtu_connection_status', {
                'connected': False,
                'error': str(e),
                'message': f'連接錯誤: {e}',
                'timestamp': datetime.now().isoformat()
            })
            print(f"RTU connection error: {e}")
    
    @socketio.on('rtu_disconnect')
    def handle_rtu_disconnect(data):
        """RTU 斷開事件 / RTU disconnect event"""
        try:
            from backend.modbus.rtu_client import ModbusRTUClient
            
            # 創建客戶端並斷開連接
            rtu_config = {
                'rtu_port': app.config['RTU_PORT'],
                'baudrate': app.config['RTU_BAUDRATE']
            }
            
            rtu_client = ModbusRTUClient(rtu_config)
            rtu_client.disconnect()
            
            emit('rtu_connection_status', {
                'connected': False,
                'message': 'RTU 連接已斷開',
                'timestamp': datetime.now().isoformat()
            })
            
            print("RTU disconnected")
            
        except Exception as e:
            emit('rtu_connection_status', {
                'connected': False,
                'error': str(e),
                'message': f'斷開錯誤: {e}',
                'timestamp': datetime.now().isoformat()
            })
            print(f"RTU disconnect error: {e}")
    
    @socketio.on('rtu_status')
    def handle_rtu_status(data):
        """獲取 RTU 狀態事件 / Get RTU status event"""
        try:
            from backend.modbus.rtu_client import ModbusRTUClient
            
            rtu_config = {
                'rtu_port': app.config['RTU_PORT'],
                'baudrate': app.config['RTU_BAUDRATE'],
                'timeout': app.config['RTU_TIMEOUT']
            }
            
            rtu_client = ModbusRTUClient(rtu_config)
            status = rtu_client.get_connection_status()
            
            emit('rtu_status_response', {
                'success': True,
                'status': status,
                'config': {
                    'rtu_enabled': app.config.get('RTU_ENABLED', False),
                    'rtu_port': app.config['RTU_PORT'],
                    'baudrate': app.config['RTU_BAUDRATE'],
                    'timeout': app.config['RTU_TIMEOUT']
                },
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            emit('rtu_status_response', {
                'success': False,
                'error': str(e),
                'message': f'獲取狀態失敗: {e}',
                'timestamp': datetime.now().isoformat()
            })
            print(f"RTU status error: {e}")
    
    @socketio.on('update_power_schedule')
    def handle_update_power_schedule(data):
        """更新供電時段配置 / Update power schedule configuration"""
        try:
            schedule = data.get('schedule', {})
            
            # 驗證時段格式
            required_keys = ['open_power', 'close_power']
            for key in required_keys:
                if key not in schedule:
                    emit('power_schedule_response', {
                        'success': False,
                        'error': f'缺少必要的時段配置: {key}',
                        'timestamp': datetime.now().isoformat()
                    })
                    return
                
                if 'start' not in schedule[key] or 'end' not in schedule[key]:
                    emit('power_schedule_response', {
                        'success': False,
                        'error': f'{key} 時段缺少 start 或 end 時間',
                        'timestamp': datetime.now().isoformat()
                    })
                    return
            
            # 通過RTU客戶端更新供電時段（需要在RTU客戶端添加相應方法）
            from backend.modbus.rtu_client import ModbusRTUClient
            
            rtu_config = {
                'rtu_port': app.config['RTU_PORT'],
                'baudrate': app.config['RTU_BAUDRATE'],
                'timeout': app.config['RTU_TIMEOUT'],
                'RTU_SIMULATOR_PORT': app.config.get('RTU_SIMULATOR_PORT', 5502)
            }
            
            rtu_client = ModbusRTUClient(rtu_config)
            
            # 使用RTU客戶端更新供電時段
            success = rtu_client.update_power_schedule(schedule)
            
            if success:
                # 回應給請求的客戶端
                emit('power_schedule_response', {
                    'success': True,
                    'schedule': schedule,
                    'message': '供電時段配置已更新',
                    'timestamp': datetime.now().isoformat()
                })
                
                # 廣播給所有客戶端，通知供電時段已變更
                socketio.emit('power_schedule_changed', {
                    'schedule': schedule,
                    'message': '供電時段已更新，正在同步電表狀態...',
                    'timestamp': datetime.now().isoformat()
                }, broadcast=True)
                
                print(f"Power schedule updated and broadcasted: {schedule}")
            else:
                emit('power_schedule_response', {
                    'success': False,
                    'schedule': schedule,
                    'message': '供電時段配置更新失敗',
                    'timestamp': datetime.now().isoformat()
                })
            
        except Exception as e:
            emit('power_schedule_response', {
                'success': False,
                'error': str(e),
                'message': f'更新供電時段時發生錯誤: {e}',
                'timestamp': datetime.now().isoformat()
            })
            print(f"Power schedule update error: {e}")
    
    @socketio.on('get_power_schedule')
    def handle_get_power_schedule(data):
        """獲取當前供電時段配置 / Get current power schedule configuration"""
        try:
            from backend.modbus.rtu_client import ModbusRTUClient
            
            rtu_config = {
                'rtu_port': app.config['RTU_PORT'],
                'baudrate': app.config['RTU_BAUDRATE'],
                'timeout': app.config['RTU_TIMEOUT'],
                'RTU_SIMULATOR_PORT': app.config.get('RTU_SIMULATOR_PORT', 5502)
            }
            
            rtu_client = ModbusRTUClient(rtu_config)
            schedule = rtu_client.get_power_schedule()
            
            emit('power_schedule_response', {
                'success': True,
                'schedule': schedule,
                'message': '供電時段配置獲取成功',
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            emit('power_schedule_response', {
                'success': False,
                'error': str(e),
                'message': f'獲取供電時段配置時發生錯誤: {e}',
                'timestamp': datetime.now().isoformat()
            })
    
    @socketio.on('get_power_status')
    def handle_get_power_status(data):
        """獲取當前供電狀態 / Get current power status"""
        try:
            from backend.modbus.rtu_client import ModbusRTUClient
            
            rtu_config = {
                'rtu_port': app.config['RTU_PORT'],
                'baudrate': app.config['RTU_BAUDRATE'],
                'timeout': app.config['RTU_TIMEOUT'],
                'RTU_SIMULATOR_PORT': app.config.get('RTU_SIMULATOR_PORT', 5502)
            }
            
            rtu_client = ModbusRTUClient(rtu_config)
            
            # 獲取供電狀態摘要
            status_summary = rtu_client.get_power_status_summary()
            
            if status_summary.get('success', False):
                emit('power_status_response', {
                    'success': True,
                    'overall_status': status_summary['overall_status'],
                    'powered_meters': status_summary['powered_meters'],
                    'unpowered_meters': status_summary['unpowered_meters'],
                    'sample_size': status_summary['sample_size'],
                    'message': f'當前系統狀態: {"供電中" if status_summary["overall_status"] == "powered" else "已斷電"}',
                    'timestamp': datetime.now().isoformat()
                })
            else:
                emit('power_status_response', {
                    'success': False,
                    'error': status_summary.get('error', '獲取狀態失敗'),
                    'message': f'獲取供電狀態失敗: {status_summary.get("error", "未知錯誤")}',
                    'timestamp': datetime.now().isoformat()
                })
            
        except Exception as e:
            emit('power_status_response', {
                'success': False,
                'error': str(e),
                'message': f'獲取供電狀態時發生錯誤: {e}',
                'timestamp': datetime.now().isoformat()
            })
    
    @socketio.on('rtu_test_meters')
    def handle_rtu_test_meters(data):
        """測試 RTU 電表連接 / Test RTU meters connection"""
        meter_count = data.get('meter_count', 50)  # 預設測試 50 個電表
        
        try:
            from backend.modbus.rtu_client import ModbusRTUClient
            
            rtu_config = {
                'rtu_port': app.config['RTU_PORT'],
                'baudrate': app.config['RTU_BAUDRATE'],
                'timeout': app.config['RTU_TIMEOUT'],
                'RTU_SIMULATOR_PORT': app.config.get('RTU_SIMULATOR_PORT', 5502)
            }
            
            rtu_client = ModbusRTUClient(rtu_config)
            
            # 測試指定數量的電表 (移除 10 個限制)
            test_results = []
            for meter_id in range(1, meter_count + 1):
                try:
                    meter_data = rtu_client.read_meter_data(meter_id)
                    test_results.append({
                        'meter_id': meter_id,
                        'online': meter_data.get('online', False),
                        'energy': meter_data.get('total_energy', 0),
                        'voltage': meter_data.get('voltage_avg', 0),
                        'status': 'success'
                    })
                except Exception as e:
                    test_results.append({
                        'meter_id': meter_id,
                        'online': False,
                        'error': str(e),
                        'status': 'failed'
                    })
            
            online_count = sum(1 for result in test_results if result.get('online', False))
            
            emit('rtu_test_results', {
                'success': True,
                'tested_meters': meter_count,
                'online_meters': online_count,
                'results': test_results,
                'message': f'測試完成：{online_count}/{meter_count} 電表在線',
                'timestamp': datetime.now().isoformat()
            })
            
            print(f"RTU test completed: {online_count}/{meter_count} meters online")
            
        except Exception as e:
            emit('rtu_test_results', {
                'success': False,
                'error': str(e),
                'message': f'測試失敗: {e}',
                'timestamp': datetime.now().isoformat()
            })
            print(f"RTU test error: {e}")


def register_template_globals(app):
    """註冊模板全局變量 / Register template global variables"""
    
    @app.template_global()
    def app_info():
        """應用程式信息 / Application information"""
        return APP_INFO
    
    @app.template_global()
    def current_year():
        """當前年份 / Current year"""
        return datetime.now().year
    
    @app.template_global()
    def url_for_safe(endpoint, **values):
        """安全的 URL 生成，處理不存在的端點"""
        try:
            from flask import url_for
            return url_for(endpoint, **values)
        except:
            return '#'  # 返回空連結而不是錯誤


def register_error_handlers(app):
    """註冊錯誤處理器 / Register error handlers"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        """404 錯誤處理 / 404 error handler"""
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """500 錯誤處理 / 500 error handler"""
        return render_template('errors/500.html'), 500


# 創建應用程式實例 / Create application instance
app, socketio = create_app()


# 主頁路由 / Main page routes
@app.route('/')
def index():
    """主頁 / Main page"""
    return render_template('index.html')


@app.route('/excel')
def excel_interface():
    """Excel 風格界面 / Excel-style interface"""
    return render_template('excel_interface.html')

@app.route('/monitor')
def monitor_interface():
    """電表即時監控界面 / Real-time meter monitoring interface"""
    return render_template('monitor.html')


@app.route('/monitoring')
def monitoring():
    """監控界面 / Monitoring interface"""
    return render_template('monitoring.html')


@app.route('/charts')
def charts():
    """圖表界面 / Charts interface"""
    return render_template('charts.html')


@app.route('/settings')
def settings():
    """設定界面 / Settings interface"""
    return render_template('settings.html')


@app.route('/rtu')
def rtu_management():
    """RTU 連接管理界面 / RTU connection management interface"""
    return render_template('rtu_management.html')


@app.route('/power_schedule')
def power_schedule_management():
    """供電時段管理界面 / Power schedule management interface"""
    return render_template('power_schedule.html')


@app.route('/history')
def history_data():
    """歷史數據查詢界面 / History data query interface"""
    return render_template('history.html')


@app.route('/test')
def test_page():
    """測試頁面 / Test page"""
    from flask import send_from_directory
    return send_from_directory('.', 'test_excel.html')


@app.route('/test_socket')
def test_socket_page():
    """Socket.IO 測試頁面 / Socket.IO test page"""
    from flask import send_from_directory
    return send_from_directory('.', 'test_socket.html')


@app.route('/test_urls')
def test_urls_page():
    """URL 測試頁面 / URL test page"""
    from flask import send_from_directory
    return send_from_directory('.', 'test_urls.html')


@app.route('/api/system/info')
def system_info():
    """系統信息 API / System information API"""
    return jsonify({
        'app_info': APP_INFO,
        'config': {
            'meter_count': app.config['METER_COUNT'],
            'themes': app.config['AVAILABLE_THEMES'],
            'default_theme': app.config['DEFAULT_THEME'],
            'update_intervals': {
                'real_time': app.config['REAL_TIME_UPDATE_INTERVAL'],
                'database': app.config['DATABASE_SAVE_INTERVAL'],
                'chart': app.config['CHART_UPDATE_INTERVAL']
            }
        },
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/system/status')
def system_status():
    """系統狀態 API / System status API"""
    import psutil
    
    return jsonify({
        'success': True,
        'data': {
            'app_info': APP_INFO,
            'system': {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory': {
                    'percent': psutil.virtual_memory().percent,
                    'used': psutil.virtual_memory().used,
                    'total': psutil.virtual_memory().total
                },
                'disk': {
                    'percent': psutil.disk_usage('/').percent,
                    'used': psutil.disk_usage('/').used,
                    'total': psutil.disk_usage('/').total
                }
            },
            'config': {
                'environment': 'development' if app.debug else 'production',
                'debug_mode': app.debug,
                'meter_count': app.config['METER_COUNT']
            },
            'timestamp': datetime.now().isoformat()
        }
    })


if __name__ == '__main__':
    """應用程式入口點 / Application entry point"""
    
    # 檢查環境變量 / Check environment variables
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5001))
    
    print("=" * 60)
    print(f"🌐 {APP_INFO['name']}")
    print(f"📝 Version: {APP_INFO['version']}")
    print(f"🚀 Starting server at http://{host}:{port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"📊 Excel interface: http://{host}:{port}/excel")
    print("=" * 60)
    
    # 啟動 Socket.IO 服務器 / Start Socket.IO server
    socketio.run(
        app,
        debug=debug,
        host=host,
        port=port,
        use_reloader=debug,
        log_output=debug,
        allow_unsafe_werkzeug=True
    )
