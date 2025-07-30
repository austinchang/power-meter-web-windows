"""
Power Meter GUI Professional - Web Edition 配置
Configuration for Web Edition
"""

import os
from datetime import timedelta
from pathlib import Path

# 專案根目錄 / Project root directory
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_DIR = DATA_DIR / "database"
CONFIG_DIR = DATA_DIR / "config"

# 創建必要目錄 / Create necessary directories
for directory in [DATA_DIR, DATABASE_DIR, CONFIG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


class Config:
    """基礎配置類 / Base configuration class"""
    
    # Flask 應用設定 / Flask application settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'power-meter-web-edition-secret-key-2025'
    
    # 數據庫設定 / Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{DATABASE_DIR}/power_meter_web.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Socket.IO 設定 / Socket.IO settings
    SOCKETIO_ASYNC_MODE = 'threading'
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
    SOCKETIO_LOGGER = True
    SOCKETIO_ENGINEIO_LOGGER = True
    
    # CORS 設定 / CORS settings
    CORS_ORIGINS = ["http://localhost:5000", "http://127.0.0.1:5000"]
    
    # JWT 設定 / JWT settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-for-power-meter'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # 電表通訊設定 / Meter communication settings
    MODBUS_PORT = os.environ.get('MODBUS_PORT', '/dev/ttyUSB0')
    MODBUS_BAUDRATE = int(os.environ.get('MODBUS_BAUDRATE', 9600))
    MODBUS_TIMEOUT = float(os.environ.get('MODBUS_TIMEOUT', 3.0))
    MODBUS_RETRY_COUNT = int(os.environ.get('MODBUS_RETRY_COUNT', 3))
    
    # 電表範圍設定 / Meter range settings
    METER_START_ID = 1
    METER_END_ID = 50
    METER_COUNT = METER_END_ID - METER_START_ID + 1
    
    # RTU 模擬器連接設定 / RTU Simulator connection settings (支援 Windows COM)
    RTU_ENABLED = True
    RTU_PORT = os.environ.get('RTU_PORT', 'COM1' if os.name == 'nt' else '/dev/ttyUSB0')
    RTU_BAUDRATE = int(os.environ.get('RTU_BAUDRATE', 9600))
    RTU_BYTESIZE = int(os.environ.get('RTU_BYTESIZE', 8))
    RTU_PARITY = os.environ.get('RTU_PARITY', 'N')
    RTU_STOPBITS = int(os.environ.get('RTU_STOPBITS', 1))
    RTU_TIMEOUT = float(os.environ.get('RTU_TIMEOUT', 1.0))
    RTU_CACHE_EXPIRY = int(os.environ.get('RTU_CACHE_EXPIRY', 5))
    
    # RTU 模擬器地址設定 (TCP 模式)
    RTU_SIMULATOR_HOST = os.environ.get('RTU_SIMULATOR_HOST', '127.0.0.1')
    RTU_SIMULATOR_PORT = int(os.environ.get('RTU_SIMULATOR_PORT', 5502))
    
    # 啟用 TCP 模式
    MODBUS_MODE = os.environ.get('MODBUS_MODE', 'TCP')
    
    # 數據更新間隔 / Data update intervals (seconds)
    REAL_TIME_UPDATE_INTERVAL = 1.0
    DATABASE_SAVE_INTERVAL = 60.0
    CHART_UPDATE_INTERVAL = 2.0
    
    # 系統預設值 / System defaults
    DEFAULT_VOLTAGE_RANGE = (0, 300)     # V
    DEFAULT_CURRENT_RANGE = (0, 50)      # A  
    DEFAULT_POWER_RANGE = (0, 15000)     # W
    DEFAULT_UNIT_PRICE = 4               # 元/度
    
    # 供電時段預設值 / Default power schedule
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
    
    # 模擬模式配置 / Simulation mode configuration
    USE_POWER_SCHEDULE_IN_SIMULATION = True  # 模擬模式是否遵循供電時段
    FORCE_SIMULATION = os.environ.get('FORCE_SIMULATION', 'True').lower() == 'true'
    
    # 電表數據更新週期設定 / Meter data update interval settings
    DEFAULT_UPDATE_INTERVAL = 30  # 預設更新間隔 (秒)
    MIN_UPDATE_INTERVAL = 5       # 最小更新間隔 (秒) - 從30改為5
    MAX_UPDATE_INTERVAL = 180     # 最大更新間隔 (秒)
    
    # 主題設定 / Theme settings
    AVAILABLE_THEMES = ['light', 'dark', 'industrial']
    DEFAULT_THEME = 'light'
    
    # 日誌設定 / Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = DATA_DIR / 'logs' / 'power_meter_web.log'
    
    # 創建日誌目錄 / Create log directory
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # 文件上傳設定 / File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = DATA_DIR / 'uploads'
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    
    # API 設定 / API settings
    API_TITLE = 'Power Meter Web API'
    API_VERSION = 'v1'
    API_DESCRIPTION = 'Power Meter Professional Web Edition REST API'
    
    # 安全設定 / Security settings
    SESSION_COOKIE_SECURE = False  # 開發環境設為 False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # 性能設定 / Performance settings
    THREADED = True
    PROCESSES = 1


class DevelopmentConfig(Config):
    """開發環境配置 / Development configuration"""
    DEBUG = True
    TESTING = False
    
    # 開發環境特定設定
    SQLALCHEMY_ECHO = True  # 顯示 SQL 查詢
    SOCKETIO_LOGGER = True
    SOCKETIO_ENGINEIO_LOGGER = True
    
    # RTU 模擬器連接設定 (開發環境) - 支援 Windows COM
    RTU_ENABLED = True
    RTU_PORT = 'COM1' if os.name == 'nt' else '/dev/ttyUSB0'
    METER_COUNT = 50  # 支援 50 個電表
    
    # 開發用模擬數據 / Development mock data
    USE_MOCK_MODBUS = False  # 停用模擬數據，使用真實 RTU
    MOCK_DATA_ENABLED = False


class ProductionConfig(Config):
    """生產環境配置 / Production configuration"""
    DEBUG = False
    TESTING = False
    
    # 生產環境安全設定 / Production security settings
    SESSION_COOKIE_SECURE = True
    SQLALCHEMY_ECHO = False
    SOCKETIO_LOGGER = False
    SOCKETIO_ENGINEIO_LOGGER = False
    
    # 生產環境 CORS 設定
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',')
    
    # 生產環境數據庫優化
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 20,
        'max_overflow': 30
    }


class TestingConfig(Config):
    """測試環境配置 / Testing configuration"""
    DEBUG = True
    TESTING = True
    
    # 測試用內存數據庫 / In-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # 測試環境特定設定
    WTF_CSRF_ENABLED = False
    USE_MOCK_MODBUS = True
    MOCK_DATA_ENABLED = True
    
    # 加速測試的更新間隔
    REAL_TIME_UPDATE_INTERVAL = 0.1
    DATABASE_SAVE_INTERVAL = 1.0


# 配置字典 / Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """
    獲取配置對象 / Get configuration object
    
    Args:
        config_name (str): Configuration name
        
    Returns:
        Config: Configuration class
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    return config.get(config_name, DevelopmentConfig)


# 應用程式信息 / Application information
APP_INFO = {
    'name': 'Power Meter GUI Professional - Web Edition',
    'version': '1.0.0-web-beta',
    'description': 'Professional power meter monitoring system with Excel-style web interface',
    'author': 'Claude Code Plan Mode',
    'license': 'MIT',
    'python_requires': '>=3.8',
    'homepage': 'https://github.com/austinchang/power_meter_gui_web_edition'
}