"""
歷史數據 API 路由 / History Data API routes
用於電表歷史數據查詢和統計
"""

from datetime import datetime
from flask import request, jsonify, current_app
from . import api_bp

# 導入智能日誌系統
try:
    from ..smart_logger import UniversalSmartLogger
    smart_logger = UniversalSmartLogger('power-meter-history')
except ImportError:
    smart_logger = None
    print("Warning: Smart Logger not available for history module")


@api_bp.route('/history/meter/<int:meter_id>', methods=['GET'])
def get_meter_history(meter_id):
    """
    獲取指定電表的歷史數據 / Get history data for specific meter
    
    Args:
        meter_id (int): 電表 ID
        
    Query Parameters:
        days (int): 查詢天數，預設 30 天
        
    Returns:
        JSON: 電表歷史數據
    """
    try:
        days = int(request.args.get('days', 30))
        
        # 驗證參數
        if meter_id < 1 or meter_id > 50:
            return jsonify({
                'success': False,
                'error': '電表 ID 必須在 1-50 範圍內',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        if days < 1 or days > 365:
            return jsonify({
                'success': False,
                'error': '查詢天數必須在 1-365 範圍內',
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
        history_data = rtu_client.get_meter_history(meter_id, days)
        
        if history_data.get('success', False):
            return jsonify({
                'success': True,
                'data': history_data,
                'query_params': {
                    'meter_id': meter_id,
                    'days': days
                },
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': history_data.get('error', '獲取歷史數據失敗'),
                'message': history_data.get('message', ''),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': '參數格式錯誤',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'獲取電表 {meter_id} 歷史數據時發生系統錯誤',
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/history/billing-summary', methods=['GET'])
def get_billing_summary():
    """
    獲取系統計費摘要 / Get system billing summary
    
    Returns:
        JSON: 計費摘要信息
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
        billing_data = rtu_client.get_system_billing_summary()
        
        if billing_data.get('success', False):
            return jsonify({
                'success': True,
                'data': billing_data,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': billing_data.get('error', '獲取計費摘要失敗'),
                'message': billing_data.get('message', ''),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '獲取計費摘要時發生系統錯誤',
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/history/statistics', methods=['GET'])
def get_history_statistics():
    """
    獲取歷史統計摘要 / Get history statistics summary
    
    Returns:
        JSON: 歷史統計信息
    """
    try:
        # 模擬歷史統計數據，實際應該從數據庫獲取
        current_date = datetime.now()
        
        return jsonify({
            'success': True,
            'data': {
                'database_status': 'active',
                'total_records': 12543,  # 模擬數據
                'daily_records': 365,
                'hourly_records': 8760,
                'power_status_logs': 2847,
                'billing_cycles': 12,
                'oldest_record': f"{current_date.year}-01-01T00:00:00",
                'newest_record': current_date.isoformat(),
                'database_size_mb': 15.7,
                'cleanup_schedule': '每90天自動清理',
                'last_cleanup': f"{current_date.year}-{current_date.month:02d}-01T02:00:00",
                'auto_backup': True,
                'last_backup': f"{current_date.year}-{current_date.month:02d}-{current_date.day:02d}T02:00:00"
            },
            'timestamp': current_date.isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '獲取歷史統計時發生錯誤',
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/history/power-events', methods=['GET'])
def get_power_events():
    """
    獲取供電事件記錄 / Get power event logs
    
    Query Parameters:
        hours (int): 查詢小時數，預設 24 小時
        meter_id (int): 特定電表 ID，可選
        
    Returns:
        JSON: 供電事件記錄
    """
    try:
        hours = int(request.args.get('hours', 24))
        meter_id = request.args.get('meter_id')
        
        # 驗證參數
        if hours < 1 or hours > 168:  # 最多 7 天
            return jsonify({
                'success': False,
                'error': '查詢小時數必須在 1-168 範圍內',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        if meter_id is not None:
            meter_id = int(meter_id)
            if meter_id < 1 or meter_id > 50:
                return jsonify({
                    'success': False,
                    'error': '電表 ID 必須在 1-50 範圍內',
                    'timestamp': datetime.now().isoformat()
                }), 400
        
        # 模擬供電事件數據
        current_time = datetime.now()
        events = []
        
        # 生成一些模擬事件
        for i in range(min(hours // 4, 20)):  # 每4小時一個事件，最多20個
            event_time = current_time.replace(
                hour=(current_time.hour - i * 4) % 24,
                minute=0,
                second=0,
                microsecond=0
            )
            
            events.append({
                'id': i + 1,
                'timestamp': event_time.isoformat(),
                'meter_id': meter_id or (i % 10 + 1),
                'event_type': 'power_on' if i % 2 == 0 else 'power_off',
                'reason': '時段調度' if i % 3 == 0 else '手動控制',
                'duration_minutes': 240 if i % 2 == 0 else 0,  # 供電事件持續時間
                'status': 'completed'
            })
        
        return jsonify({
            'success': True,
            'data': {
                'events': events,
                'count': len(events),
                'query_params': {
                    'hours': hours,
                    'meter_id': meter_id
                },
                'summary': {
                    'power_on_events': len([e for e in events if e['event_type'] == 'power_on']),
                    'power_off_events': len([e for e in events if e['event_type'] == 'power_off']),
                    'scheduled_events': len([e for e in events if e['reason'] == '時段調度']),
                    'manual_events': len([e for e in events if e['reason'] == '手動控制'])
                }
            },
            'timestamp': current_time.isoformat()
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': '參數格式錯誤',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '獲取供電事件記錄時發生錯誤',
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/history/daily-summary/<int:meter_id>', methods=['GET'])
def get_daily_summary(meter_id):
    """
    獲取電表每日統計摘要 / Get daily summary for specific meter
    
    Args:
        meter_id (int): 電表 ID
        
    Query Parameters:
        days (int): 查詢天數，預設 7 天
        
    Returns:
        JSON: 每日統計摘要
    """
    try:
        days = int(request.args.get('days', 7))
        
        # 驗證參數
        if meter_id < 1 or meter_id > 50:
            return jsonify({
                'success': False,
                'error': '電表 ID 必須在 1-50 範圍內',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        if days < 1 or days > 30:
            return jsonify({
                'success': False,
                'error': '查詢天數必須在 1-30 範圍內',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 模擬每日統計數據
        current_date = datetime.now()
        daily_stats = []
        
        for i in range(days):
            day = current_date.replace(
                day=max(1, current_date.day - i),
                hour=0,
                minute=0,
                second=0,
                microsecond=0
            )
            
            # 模擬每日數據
            base_usage = meter_id * 2.5 + (i * 0.3)  # 基本用電量變化
            daily_stats.append({
                'date': day.strftime('%Y-%m-%d'),
                'start_energy': round(1000 + (days - i - 1) * base_usage, 1),
                'end_energy': round(1000 + (days - i) * base_usage, 1),
                'daily_usage': round(base_usage, 1),
                'powered_hours': 22.5 - (i % 3 * 2),  # 模擬供電時間變化
                'unpowered_hours': 1.5 + (i % 3 * 2),
                'cost': round(base_usage * 3.5, 2),
                'avg_power': round(base_usage / 24 * 1000, 1),  # 平均功率 (W)
                'peak_power': round(base_usage / 24 * 1000 * 1.5, 1)
            })
        
        # 計算統計摘要
        total_usage = sum(stat['daily_usage'] for stat in daily_stats)
        total_cost = sum(stat['cost'] for stat in daily_stats)
        avg_daily_usage = total_usage / len(daily_stats) if daily_stats else 0
        
        return jsonify({
            'success': True,
            'data': {
                'meter_id': meter_id,
                'period': f"{daily_stats[-1]['date']} 至 {daily_stats[0]['date']}" if daily_stats else "",
                'daily_statistics': daily_stats,
                'summary': {
                    'total_usage_kwh': round(total_usage, 1),
                    'total_cost_yuan': round(total_cost, 2),
                    'avg_daily_usage_kwh': round(avg_daily_usage, 1),
                    'avg_daily_cost_yuan': round(total_cost / len(daily_stats) if daily_stats else 0, 2),
                    'max_daily_usage': max(stat['daily_usage'] for stat in daily_stats) if daily_stats else 0,
                    'min_daily_usage': min(stat['daily_usage'] for stat in daily_stats) if daily_stats else 0
                }
            },
            'timestamp': current_date.isoformat()
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': '參數格式錯誤',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'獲取電表 {meter_id} 每日統計時發生錯誤',
            'timestamp': datetime.now().isoformat()
        }), 500