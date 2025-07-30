"""
Socket.IO handlers module
Socket.IO 處理器模組
"""

from flask import Blueprint

# 創建 Socket 藍圖 / Create Socket blueprint
socket_bp = Blueprint('socket_handlers', __name__)

# 導入處理器模組 / Import handler modules
from . import meter_events, system_events