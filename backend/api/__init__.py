"""
Backend API module
後端 API 模組
"""

from flask import Blueprint

# 創建 API 藍圖 / Create API blueprint
api_bp = Blueprint('api', __name__)

# 導入路由模組 / Import route modules
from . import meters, system, charts, config, history, config_sync