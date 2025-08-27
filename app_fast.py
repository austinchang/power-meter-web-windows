#!/usr/bin/env python3
"""
Power Meter GUI Professional - Web Edition Windows 快速啟動版本
Fast startup version for Windows with asynchronous meter initialization
遵循三大規定：RTU優先 -> 模擬器 -> 離線
"""

import os
import sys
import logging
import threading
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS

# 設定環境變量以使用真實電表（遵循三大規定）
os.environ['FORCE_SIMULATION'] = 'False'

from config import get_config, APP_INFO
from backend.database import db, init_database
from backend.services import meter_service


def create_app(config_name=None):
    """
    創建 Flask 應用程式 - Windows 快速啟動版本
    """
    app = Flask(__name__, 
                template_folder='frontend/templates',
                static_folder='frontend/static')
    
    # 載入配置
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    
    # 設置日誌
    setup_logging(app)
    
    # 初始化擴展
    db.init_app(app)
    socketio = SocketIO(
        app,
        cors_allowed_origins=app.config['SOCKETIO_CORS_ALLOWED_ORIGINS'],
        async_mode=app.config['SOCKETIO_ASYNC_MODE'],
        logger=app.config['SOCKETIO_LOGGER'],
        engineio_logger=app.config['SOCKETIO_ENGINEIO_LOGGER']
    )
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # 初始化數據庫
    init_database(app)
    
    # 註冊藍圖
    register_blueprints(app)
    
    # 註冊 Socket.IO 事件
    register_socket_events(socketio)
    
    # 添加模板全局變量
    register_template_globals(app)
    
    # 註冊錯誤處理器
    register_error_handlers(app)
    
    # 非同步初始化電表（不阻塞啟動）
    async_initialize_meters(app)
    
    return app, socketio


def async_initialize_meters(app):
    """
    非同步初始化電表 - 不阻塞主程式啟動
    遵循三大規定進行初始化
    """
    def init_meters():
        with app.app_context():
            try:
                logging.info("開始非同步初始化電表（遵循三大規定）...")
                
                # 快速創建電表記錄（不等待實際連接）
                start_id = app.config.get('METER_START_ID', 1)
                end_id = app.config.get('METER_END_ID', 50)
                
                for meter_id in range(start_id, min(end_id + 1, start_id + 10)):  # 先初始化前10個
                    try:
                        meter_service.get_or_create_meter(
                            meter_id=meter_id,
                            name=f'RTU電表{meter_id:02d}',
                            parking=f'RTU-{meter_id:04d}'
                        )
                    except Exception as e:
                        logging.warning(f"初始化電表 {meter_id} 失敗: {e}")
                
                logging.info("電表初始化完成（前10個）")
                
                # 背景繼續初始化其餘電表
                if end_id > start_id + 10:
                    for meter_id in range(start_id + 10, end_id + 1):
                        try:
                            time.sleep(0.1)  # 避免過度佔用資源
                            meter_service.get_or_create_meter(
                                meter_id=meter_id,
                                name=f'RTU電表{meter_id:02d}',
                                parking=f'RTU-{meter_id:04d}'
                            )
                        except Exception as e:
                            logging.warning(f"初始化電表 {meter_id} 失敗: {e}")
                            
            except Exception as e:
                logging.error(f"電表初始化錯誤: {e}")
    
    # 在背景執行緒中初始化
    init_thread = threading.Thread(target=init_meters, daemon=True)
    init_thread.start()


def setup_logging(app):
    """設置日誌系統"""
    if not app.debug:
        file_handler = logging.FileHandler(app.config['LOG_FILE'])
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Power Meter Web Edition (Windows Fast) startup')


def register_blueprints(app):
    """註冊藍圖"""
    from backend.api import api_bp
    from backend.socket_handlers import socket_bp
    from backend.routes.monitor import monitor_bp
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(socket_bp)
    app.register_blueprint(monitor_bp)


def register_socket_events(socketio):
    """註冊 Socket.IO 事件"""
    
    @socketio.on('connect')
    def handle_connect():
        """客戶端連接事件"""
        print(f'Client connected: {request.sid}')
        emit('status', {'message': 'Connected to Power Meter Web Edition (Windows Fast)'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """客戶端斷開事件"""
        print(f'Client disconnected: {request.sid}')
    
    @socketio.on('join')
    def handle_join(data):
        """加入房間事件"""
        room = data.get('room', 'default')
        join_room(room)
        print(f'Client {request.sid} joined room: {room}')
        emit('status', {'message': f'Joined room: {room}'}, room=room)
    
    @socketio.on('leave')
    def handle_leave(data):
        """離開房間事件"""
        room = data.get('room', 'default')
        leave_room(room)
        print(f'Client {request.sid} left room: {room}')
        emit('status', {'message': f'Left room: {room}'}, room=room)


def register_template_globals(app):
    """註冊模板全局變量"""
    @app.context_processor
    def inject_globals():
        return {
            'APP_INFO': APP_INFO,
            'now': datetime.now
        }


def register_error_handlers(app):
    """註冊錯誤處理器"""
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500


# 創建應用實例
app, socketio = create_app()


# 添加根路由
@app.route('/')
def index():
    """首頁"""
    return render_template('index.html')


@app.route('/excel')
def excel_page():
    """Excel 介面頁面"""
    return render_template('excel_interface.html')


@app.route('/monitor')
def monitor_page():
    """監控頁面"""
    return render_template('monitor.html')


@app.route('/api/system/info')
def system_info():
    """系統信息 API"""
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
            },
            'simulation_mode': os.environ.get('FORCE_SIMULATION', 'False'),
            'platform': 'Windows',
            'three_rules_compliant': True
        },
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/system/status')
def system_status():
    """系統狀態 API"""
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
                'platform': 'Windows'
            },
            'config': {
                'environment': 'development' if app.debug else 'production',
                'debug_mode': app.debug,
                'meter_count': app.config['METER_COUNT'],
                'simulation_mode': os.environ.get('FORCE_SIMULATION', 'False'),
                'three_rules_enabled': True
            },
            'timestamp': datetime.now().isoformat()
        }
    })


if __name__ == '__main__':
    """應用程式入口點 - Windows 快速啟動版本"""
    
    # 檢查環境變量
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5001))
    
    print("=" * 60)
    print(f"🚀 {APP_INFO['name']} - Windows 快速啟動版本")
    print(f"📝 Version: {APP_INFO['version']}")
    print(f"🌐 Starting server at http://{host}:{port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"⚡ 模擬模式: {os.environ.get('FORCE_SIMULATION', 'False')}")
    print(f"📊 Excel interface: http://{host}:{port}/excel")
    print(f"✅ 三大規定: RTU優先 -> 模擬器 -> 離線")
    print(f"✨ 使用非同步初始化 - 網頁立即可用！")
    print("=" * 60)
    
    # 啟動 Socket.IO 服務器
    socketio.run(
        app,
        debug=debug,
        host=host,
        port=port,
        use_reloader=debug,
        log_output=debug,
        allow_unsafe_werkzeug=True
    )