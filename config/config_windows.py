"""
Power Meter Web Edition - Windows 專用配置
Windows Specific Configuration for Power Meter Web Edition
"""

import os
import platform
from datetime import timedelta
from pathlib import Path

# 確認運行環境
IS_WINDOWS = platform.system() == 'Windows'
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_DIR = DATA_DIR / "database"
CONFIG_DIR = DATA_DIR / "config"
LOGS_DIR = DATA_DIR / "logs"

# 創建必要目錄
for directory in [DATA_DIR, DATABASE_DIR, CONFIG_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


class Config:
    """基礎配置類 - Windows 優化版本"""
    
    # Flask 應用設定
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'power-meter-web-windows-2025-key'
    
    # 數據庫設定 - Windows 路徑
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{DATABASE_DIR}/power_meter_web.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
    }
    
    # Socket.IO 設定 - Windows 相容性
    SOCKETIO_ASYNC_MODE = 'eventlet'  # Windows 推薦使用 eventlet
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
    SOCKETIO_LOGGER = True
    SOCKETIO_ENGINEIO_LOGGER = False  # 減少日誌輸出
    
    # CORS 設定
    CORS_ORIGINS = ["http://localhost:5001", "http://127.0.0.1:5001", "http://0.0.0.0:5001"]
    
    # JWT 設定
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-windows-power-meter-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # MODBUS RTU 設定 - Windows COM port
    RTU_ENABLED = os.environ.get('RTU_ENABLED', 'true').lower() == 'true'
    RTU_PORT = os.environ.get('RTU_PORT', 'COM1')  # Windows COM port
    RTU_SLAVE_ADDRESS = int(os.environ.get('RTU_SLAVE_ADDRESS', '2'))
    RTU_BAUDRATE = int(os.environ.get('RTU_BAUDRATE', 9600))
    RTU_BYTESIZE = int(os.environ.get('RTU_BYTESIZE', 8))
    RTU_PARITY = os.environ.get('RTU_PARITY', 'N')
    RTU_STOPBITS = int(os.environ.get('RTU_STOPBITS', 1))
    RTU_TIMEOUT = float(os.environ.get('RTU_TIMEOUT', 1.0))
    RTU_CACHE_EXPIRY = int(os.environ.get('RTU_CACHE_EXPIRY', 5))
    
    # 電表範圍設定
    METER_START_ID = 1
    METER_END_ID = 50
    METER_COUNT = METER_END_ID - METER_START_ID + 1
    
    # MODBUS 地址映射 - 重要：Web Meter ID 到實際 MODBUS Address 的映射
    MODBUS_ADDRESS_MAPPING = {
        1: 2,  # Web 介面顯示的 Meter ID 1 對應到實際的 MODBUS Address 2
        # 可以根據需要添加更多映射
        # 2: 3,  # Web Meter ID 2 → MODBUS Address 3
        # 3: 4,  # Web Meter ID 3 → MODBUS Address 4
    }
    
    # 數據更新間隔 (秒)
    REAL_TIME_UPDATE_INTERVAL = 2.0  # Windows 環境適中的更新頻率
    DATABASE_SAVE_INTERVAL = 60.0
    CHART_UPDATE_INTERVAL = 3.0
    
    # 系統預設值
    DEFAULT_VOLTAGE_RANGE = (0, 300)     # V
    DEFAULT_CURRENT_RANGE = (0, 50)      # A  
    DEFAULT_POWER_RANGE = (0, 15000)     # W
    DEFAULT_UNIT_PRICE = 4               # 元/度
    
    # 供電時段預設值
    DEFAULT_POWER_SCHEDULE = {
        'open_power': {
            'start': '06:00:00',
            'end': '22:00:00'
        },
        'close_power': {
            'start': '22:00:00', 
            'end': '06:00:00'
        }
    }
    
    # 模擬模式配置
    USE_POWER_SCHEDULE_IN_SIMULATION = True
    FORCE_SIMULATION = os.environ.get('FORCE_SIMULATION', 'False').lower() == 'true'
    
    # 電表數據更新週期設定
    DEFAULT_UPDATE_INTERVAL = 30
    MIN_UPDATE_INTERVAL = 5
    MAX_UPDATE_INTERVAL = 180
    
    # 主題設定
    AVAILABLE_THEMES = ['light', 'dark', 'industrial']
    DEFAULT_THEME = 'light'
    
    # 日誌設定 - Windows 路徑
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = LOGS_DIR / 'power_meter_web.log'
    
    # 文件上傳設定
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = DATA_DIR / 'uploads'
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    
    # API 設定
    API_TITLE = 'Power Meter Web API - Windows Edition'
    API_VERSION = 'v1.0-windows'
    API_DESCRIPTION = 'Professional Power Meter Web Edition for Windows with MODBUS RTU Support'
    
    # 安全設定
    SESSION_COOKIE_SECURE = False  # HTTP 環境
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Windows 特定設定
    WINDOWS_SERVICE_NAME = 'PowerMeterWeb'
    WINDOWS_SERVICE_DISPLAY_NAME = 'Power Meter Web Edition Service'
    
    # 性能設定 - Windows 優化
    THREADED = True
    PROCESSES = 1


class DevelopmentConfig(Config):
    """開發環境配置 - Windows 版本"""
    DEBUG = True
    TESTING = False
    
    # 開發環境特定設定
    SQLALCHEMY_ECHO = False  # Windows 控制台輸出較多，關閉 SQL 日誌
    SOCKETIO_LOGGER = True
    SOCKETIO_ENGINEIO_LOGGER = False
    
    # RTU 設定
    RTU_ENABLED = True
    RTU_PORT = os.environ.get('RTU_PORT', 'COM1')  # Windows COM port
    METER_COUNT = 50
    
    # Windows 開發環境設定
    FORCE_SIMULATION = os.environ.get('FORCE_SIMULATION', 'False').lower() == 'true'


class ProductionConfig(Config):
    """生產環境配置 - Windows 部署版本"""
    DEBUG = False
    TESTING = False
    
    # 生產環境安全設定
    SESSION_COOKIE_SECURE = False  # 如果使用 HTTPS 請設為 True
    SQLALCHEMY_ECHO = False
    SOCKETIO_LOGGER = False
    SOCKETIO_ENGINEIO_LOGGER = False
    
    # 生產環境 CORS 設定 - 可根據需要調整
    CORS_ORIGINS = [
        "http://localhost:5001",
        "http://127.0.0.1:5001",
        f"http://{os.environ.get('COMPUTERNAME', 'localhost')}:5001"
    ]
    
    # 生產環境數據庫優化
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20,
        'pool_timeout': 30
    }
    
    # 效能優化
    REAL_TIME_UPDATE_INTERVAL = 1.0
    DATABASE_SAVE_INTERVAL = 30.0


class TestingConfig(Config):
    """測試環境配置"""
    DEBUG = True
    TESTING = True
    
    # 測試用內存數據庫
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # 測試環境特定設定
    WTF_CSRF_ENABLED = False
    FORCE_SIMULATION = True  # 測試時使用模擬模式
    
    # 加速測試的更新間隔
    REAL_TIME_UPDATE_INTERVAL = 0.1
    DATABASE_SAVE_INTERVAL = 1.0


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': ProductionConfig  # Windows 版本預設使用生產配置
}


def get_config(config_name=None):
    """
    獲取配置對象
    
    Args:
        config_name (str): 配置名稱
        
    Returns:
        Config: 配置類
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'production')  # Windows 預設生產模式
    
    return config.get(config_name, ProductionConfig)


# 應用程式信息
APP_INFO = {
    'name': 'Power Meter Web Edition - Windows',
    'version': '1.0.0-windows',
    'description': 'Professional Power Meter Monitoring System for Windows with MODBUS RTU Support',
    'author': 'Claude Code Assistant',
    'license': 'MIT',
    'python_requires': '>=3.8',
    'platform': 'Windows 10/11',
    'modbus_support': 'MODBUS RTU over COM port',
    'homepage': 'https://github.com/power-meter-web-windows'
}


# MODBUS 設定驗證
def validate_modbus_config():
    """驗證 MODBUS 配置是否正確"""
    import json
    
    config_file = CONFIG_DIR / 'modbus_config.json'
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                modbus_config = json.load(f)
            return modbus_config
        except Exception as e:
            print(f"警告：無法讀取 MODBUS 配置檔案：{e}")
    
    # 返回預設配置
    return {
        "default_settings": {
            "baudrate": 9600,
            "parity": "N",
            "databits": 8,
            "stopbits": 1,
            "timeout": 1.0
        },
        "meter_mapping": {
            "1": {
                "modbus_address": 2,
                "name": "電表 01",
                "com_port": "COM1"
            }
        }
    }