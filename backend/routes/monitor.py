#!/usr/bin/env python3
"""
電表監控API路由
提供單電表監控和繼電器控制的Web API
"""

import logging
from flask import Blueprint, request, jsonify, current_app
from typing import Dict, Any

from backend.services.single_meter_monitor import get_monitor_instance

# 創建藍圖
monitor_bp = Blueprint('monitor', __name__, url_prefix='/api/monitor')

def get_com_port() -> str:
    """獲取配置的COM端口"""
    return current_app.config.get('RTU_PORT', 'COM1')

@monitor_bp.route('/meters', methods=['GET'])
def get_available_meters():
    """
    獲取可用的電表列表 (1-50)
    
    Returns:
        JSON: 電表列表
    """
    try:
        # 從配置中獲取電表範圍
        start_id = current_app.config.get('METER_START_ID', 1)
        end_id = current_app.config.get('METER_END_ID', 50)
        
        meters = []
        for meter_id in range(start_id, end_id + 1):
            meters.append({
                'id': meter_id,
                'name': f'RTU電表{meter_id:02d}',
                'display_name': f'電表{meter_id:02d} (RTU電表{meter_id:02d})'
            })
        
        return jsonify({
            'success': True,
            'data': meters,
            'total': len(meters)
        })
        
    except Exception as e:
        logging.error(f"✗ 獲取電表列表錯誤: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@monitor_bp.route('/start/<int:meter_id>', methods=['POST'])
def start_meter_monitoring(meter_id: int):
    """
    開始監控指定電表
    
    Args:
        meter_id: 電表ID (1-50)
        
    Body:
        {
            "interval": 5  // 監控間隔（秒），可選，預設5
        }
    
    Returns:
        JSON: 啟動結果
    """
    try:
        # 驗證電表ID範圍
        start_id = current_app.config.get('METER_START_ID', 1)
        end_id = current_app.config.get('METER_END_ID', 50)
        
        if not (start_id <= meter_id <= end_id):
            return jsonify({
                'success': False,
                'error': f'電表ID必須在 {start_id}-{end_id} 範圍內'
            }), 400
        
        # 獲取請求參數
        data = request.get_json() or {}
        interval = data.get('interval', 5)
        
        # 驗證間隔範圍
        if not (1 <= interval <= 60):
            return jsonify({
                'success': False,
                'error': '監控間隔必須在 1-60 秒之間'
            }), 400
        
        # 獲取監控器實例
        monitor = get_monitor_instance(get_com_port())
        
        # 開始監控
        result = monitor.start_monitoring(meter_id, interval)
        
        if result['success']:
            logging.info(f"✓ 開始監控電表 {meter_id}，間隔 {interval} 秒")
            return jsonify(result)
        else:
            logging.warning(f"⚠ 啟動電表 {meter_id} 監控失敗: {result.get('error')}")
            return jsonify(result), 400
            
    except Exception as e:
        logging.error(f"✗ 啟動監控錯誤: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@monitor_bp.route('/stop', methods=['POST'])
def stop_monitoring():
    """
    停止監控
    
    Returns:
        JSON: 停止結果
    """
    try:
        monitor = get_monitor_instance(get_com_port())
        result = monitor.stop_monitoring()
        
        if result['success']:
            logging.info("✓ 停止監控")
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logging.error(f"✗ 停止監控錯誤: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@monitor_bp.route('/status', methods=['GET'])
def get_monitoring_status():
    """
    獲取當前監控狀態
    
    Returns:
        JSON: 監控狀態
    """
    try:
        monitor = get_monitor_instance(get_com_port())
        status = monitor.get_current_status()
        
        return jsonify({
            'success': True,
            'data': status
        })
        
    except Exception as e:
        logging.error(f"✗ 獲取監控狀態錯誤: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@monitor_bp.route('/data/latest', methods=['GET'])
def get_latest_data():
    """
    獲取最新的監控數據
    
    Returns:
        JSON: 最新監控數據
    """
    try:
        monitor = get_monitor_instance(get_com_port())
        data = monitor.get_latest_data()
        
        if data:
            return jsonify({
                'success': True,
                'data': data
            })
        else:
            return jsonify({
                'success': False,
                'message': '暫無新數據'
            })
            
    except Exception as e:
        logging.error(f"✗ 獲取最新數據錯誤: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@monitor_bp.route('/relay/control', methods=['POST'])
def control_current_relay():
    """
    控制當前監控電表的繼電器
    
    Body:
        {
            "action": "ON" | "OFF"
        }
    
    Returns:
        JSON: 控制結果
    """
    try:
        data = request.get_json()
        if not data or 'action' not in data:
            return jsonify({
                'success': False,
                'error': '缺少 action 參數'
            }), 400
        
        action = data['action'].upper()
        if action not in ['ON', 'OFF']:
            return jsonify({
                'success': False,
                'error': 'action 必須是 ON 或 OFF'
            }), 400
        
        monitor = get_monitor_instance(get_com_port())
        result = monitor.control_relay(action)
        
        if result['success']:
            logging.info(f"✓ 繼電器控制成功: {action}")
            return jsonify(result)
        else:
            logging.warning(f"⚠ 繼電器控制失敗: {result.get('error')}")
            return jsonify(result), 400
            
    except Exception as e:
        logging.error(f"✗ 繼電器控制錯誤: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@monitor_bp.route('/relay/<int:meter_id>/<action>', methods=['POST'])
def control_meter_relay(meter_id: int, action: str):
    """
    控制指定電表的繼電器（直接控制，不需要先開始監控）
    
    Args:
        meter_id: 電表ID
        action: "ON" 或 "OFF"
    
    Returns:
        JSON: 控制結果
    """
    try:
        # 驗證電表ID範圍
        start_id = current_app.config.get('METER_START_ID', 1)
        end_id = current_app.config.get('METER_END_ID', 50)
        
        if not (start_id <= meter_id <= end_id):
            return jsonify({
                'success': False,
                'error': f'電表ID必須在 {start_id}-{end_id} 範圍內'
            }), 400
        
        action = action.upper()
        if action not in ['ON', 'OFF']:
            return jsonify({
                'success': False,
                'error': 'action 必須是 ON 或 OFF'
            }), 400
        
        monitor = get_monitor_instance(get_com_port())
        result = monitor.manager.control_meter_relay(meter_id, action)
        
        if result['success']:
            logging.info(f"✓ 電表 {meter_id} 繼電器控制成功: {action}")
            return jsonify(result)
        else:
            logging.warning(f"⚠ 電表 {meter_id} 繼電器控制失敗: {result.get('error')}")
            return jsonify(result), 400
            
    except Exception as e:
        logging.error(f"✗ 電表 {meter_id} 繼電器控制錯誤: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@monitor_bp.route('/data/<int:meter_id>', methods=['GET'])
def get_meter_data(meter_id: int):
    """
    獲取指定電表的即時數據（單次讀取）
    
    Args:
        meter_id: 電表ID
    
    Returns:
        JSON: 電表數據
    """
    try:
        # 驗證電表ID範圍
        start_id = current_app.config.get('METER_START_ID', 1)
        end_id = current_app.config.get('METER_END_ID', 50)
        
        if not (start_id <= meter_id <= end_id):
            return jsonify({
                'success': False,
                'error': f'電表ID必須在 {start_id}-{end_id} 範圍內'
            }), 400
        
        monitor = get_monitor_instance(get_com_port())
        data = monitor.manager.get_meter_data(meter_id)
        
        if data.get('success'):
            return jsonify({
                'success': True,
                'data': data
            })
        else:
            return jsonify({
                'success': False,
                'error': data.get('error', '讀取數據失敗')
            }), 400
            
    except Exception as e:
        logging.error(f"✗ 獲取電表 {meter_id} 數據錯誤: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@monitor_bp.route('/test/<int:meter_id>', methods=['POST'])
def test_meter_connection(meter_id: int):
    """
    測試與指定電表的連接
    
    Args:
        meter_id: 電表ID
    
    Returns:
        JSON: 測試結果
    """
    try:
        # 驗證電表ID範圍
        start_id = current_app.config.get('METER_START_ID', 1)
        end_id = current_app.config.get('METER_END_ID', 50)
        
        if not (start_id <= meter_id <= end_id):
            return jsonify({
                'success': False,
                'error': f'電表ID必須在 {start_id}-{end_id} 範圍內'
            }), 400
        
        monitor = get_monitor_instance(get_com_port())
        controller = monitor.manager.get_controller(meter_id)
        
        if controller:
            connection_ok = controller.test_connection()
            return jsonify({
                'success': True,
                'meter_id': meter_id,
                'connected': connection_ok,
                'message': f'電表 {meter_id} 連接{"正常" if connection_ok else "失敗"}'
            })
        else:
            return jsonify({
                'success': False,
                'meter_id': meter_id,
                'connected': False,
                'message': f'無法建立與電表 {meter_id} 的連接'
            })
            
    except Exception as e:
        logging.error(f"✗ 測試電表 {meter_id} 連接錯誤: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 錯誤處理
@monitor_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': '找不到請求的資源'
    }), 404

@monitor_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': '內部服務器錯誤'
    }), 500