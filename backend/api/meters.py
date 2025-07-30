"""
電表 API 路由 / Meter API routes
整合 MODBUS RTU 通訊支援
"""

import json
import time
from datetime import datetime, timedelta
from flask import request, jsonify, current_app
from . import api_bp
from ..modbus.rtu_client import ModbusRTUClient

# 全局 RTU 客戶端實例
_rtu_client = None

def get_rtu_client():
    """獲取 RTU 客戶端實例"""
    global _rtu_client
    if _rtu_client is None:
        rtu_config = {
            'rtu_port': current_app.config.get('RTU_PORT', '/dev/ttyUSB0'),
            'baudrate': current_app.config.get('RTU_BAUDRATE', 9600),
            'bytesize': current_app.config.get('RTU_BYTESIZE', 8),
            'parity': current_app.config.get('RTU_PARITY', 'N'),
            'stopbits': current_app.config.get('RTU_STOPBITS', 1),
            'timeout': current_app.config.get('RTU_TIMEOUT', 1.0),
            'cache_expiry': current_app.config.get('RTU_CACHE_EXPIRY', 5)
        }
        _rtu_client = ModbusRTUClient(rtu_config)
    return _rtu_client


@api_bp.route('/meters', methods=['GET'])
def get_all_meters():
    """
    獲取所有電表信息 / Get all meter information
    支援 MODBUS RTU 實際數據讀取
    
    Query Parameters:
        use_cache (bool): 是否使用快取數據 (預設: true)
        meter_range (str): 電表範圍，如 "1-10" (預設: 全部)
    
    Returns:
        JSON: 所有電表的數據
    """
    try:
        # 解析查詢參數
        use_cache = request.args.get('use_cache', 'true').lower() == 'true'
        meter_range = request.args.get('meter_range', None)
        
        meter_count = current_app.config.get('METER_COUNT', 50)
        rtu_enabled = current_app.config.get('RTU_ENABLED', False)
        
        # 確定要讀取的電表 ID 範圍
        if meter_range:
            try:
                start, end = map(int, meter_range.split('-'))
                meter_ids = list(range(max(1, start), min(meter_count + 1, end + 1)))
            except:
                meter_ids = list(range(1, meter_count + 1))
        else:
            meter_ids = list(range(1, meter_count + 1))
        
        meters = []
        
        if rtu_enabled:
            # 使用 MODBUS RTU 讀取實際數據
            rtu_client = get_rtu_client()
            
            if not use_cache:
                rtu_client.clear_cache()
            
            # 批量讀取電表數據
            meter_data_dict = rtu_client.read_multiple_meters(meter_ids[:10])  # 限制前10個避免超時
            
            for meter_id in meter_ids:
                if meter_id in meter_data_dict:
                    raw_data = meter_data_dict[meter_id]
                    
                    # 從數據庫獲取電表配置信息
                    from ..database.models import Meter
                    db_meter = Meter.query.filter_by(meter_id=meter_id).first()
                    
                    # 轉換為標準格式
                    meter_data = {
                        'id': meter_id,
                        'name': db_meter.name if db_meter else f'RTU電表{meter_id:02d}',
                        'parking': db_meter.parking if db_meter else f'RTU-{meter_id:04d}',
                        'status': 'online' if raw_data.get('online', False) else 'offline',
                        'power_on': raw_data.get('online', False),
                        'voltage': round(raw_data.get('voltage_avg', 0), 2),
                        'voltage_l1': round(raw_data.get('voltage_l1', 0), 2),
                        'voltage_l2': round(raw_data.get('voltage_l2', 0), 2),
                        'voltage_l3': round(raw_data.get('voltage_l3', 0), 2),
                        'current': round(raw_data.get('current_total', 0), 2),
                        'current_l1': round(raw_data.get('current_l1', 0), 2),
                        'current_l2': round(raw_data.get('current_l2', 0), 2),
                        'current_l3': round(raw_data.get('current_l3', 0), 2),
                        'power': round(raw_data.get('power_active', 0), 2),
                        'power_apparent': round(raw_data.get('power_apparent', 0), 2),
                        'energy': round(raw_data.get('total_energy', 0), 2),
                        'frequency': round(raw_data.get('frequency', 0), 2),
                        'power_factor': round(raw_data.get('power_factor', 0), 3),
                        'last_update': raw_data.get('timestamp'),
                        'error_message': raw_data.get('error_message')
                    }
                else:
                    # 電表離線或無法讀取
                    meter_data = _get_fallback_meter_data(meter_id)
                
                meters.append(meter_data)
        else:
            # 使用模擬數據 (原始行為)
            for meter_id in meter_ids:
                meters.append(_get_simulated_meter_data(meter_id))
        
        # 獲取連線狀態
        connection_status = {}
        if rtu_enabled:
            connection_status = get_rtu_client().get_connection_status()
        
        return jsonify({
            'success': True,
            'data': meters,
            'count': len(meters),
            'rtu_enabled': rtu_enabled,
            'connection_status': connection_status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"獲取電表數據時發生錯誤: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


def _get_simulated_meter_data(meter_id: int) -> dict:
    """獲取模擬電表數據 - 考慮時段控制"""
    from ..services.meter_service import meter_service
    
    # 從數據庫獲取電表配置信息
    try:
        from ..database.models import Meter
        
        meter = Meter.query.filter_by(meter_id=meter_id).first()
        
        # 始終根據當前供電時段決定狀態，確保一致性
        is_power_on = meter_service.is_power_schedule_active('open_power')
        
        if meter:
            name = meter.name
            parking = meter.parking
        else:
            # 如果數據庫中沒有記錄，使用預設名稱
            name = f'RTU電表{meter_id:02d}'
            parking = f'RTU-{meter_id:04d}'
    except:
        # 如果查詢失敗，回退到時段控制和預設值
        is_power_on = meter_service.is_power_schedule_active('open_power')
        name = f'RTU電表{meter_id:02d}'
        parking = f'RTU-{meter_id:04d}'
    
    return {
        'id': meter_id,
        'name': name,
        'parking': parking,
        'status': 'online',
        'power_on': is_power_on,  # 優先使用數據庫狀態，否則根據時段控制設定
        'voltage': 220.0 + (meter_id % 10) if is_power_on else 0.0,
        'current': 15.0 + (meter_id % 5) if is_power_on else 0.0,
        'power': 3300.0 + (meter_id * 10) if is_power_on else 0.0,
        'energy': meter_id * 50.5,
        'last_update': datetime.now().isoformat()
    }


def _get_fallback_meter_data(meter_id: int) -> dict:
    """獲取備用電表數據 (當 RTU 讀取失敗時使用) - 考慮時段控制"""
    from ..services.meter_service import meter_service
    
    # 從數據庫獲取電表配置信息
    try:
        from ..database.models import Meter
        
        meter = Meter.query.filter_by(meter_id=meter_id).first()
        
        # 始終根據當前供電時段決定狀態，確保一致性
        is_power_on = meter_service.is_power_schedule_active('open_power')
        
        if meter:
            name = meter.name
            parking = meter.parking
        else:
            # 如果數據庫中沒有記錄，使用預設名稱
            name = f'RTU電表{meter_id:02d}'
            parking = f'RTU-{meter_id:04d}'
    except:
        # 如果查詢失敗，回退到時段控制和預設值
        is_power_on = meter_service.is_power_schedule_active('open_power')
        name = f'RTU電表{meter_id:02d}'
        parking = f'RTU-{meter_id:04d}'
    
    return {
        'id': meter_id,
        'name': name,
        'parking': parking,
        'status': 'offline',
        'power_on': is_power_on,  # 優先使用數據庫狀態，否則根據時段控制設定
        'voltage': 220.0 + (meter_id % 10) if is_power_on else 0.0,
        'voltage_l1': 220.0 + (meter_id % 10) if is_power_on else 0.0,
        'voltage_l2': 220.0 + (meter_id % 10) if is_power_on else 0.0,
        'voltage_l3': 220.0 + (meter_id % 10) if is_power_on else 0.0,
        'current': 15.0 + (meter_id % 5) if is_power_on else 0.0,
        'current_l1': 15.0 + (meter_id % 5) if is_power_on else 0.0,
        'current_l2': 15.0 + (meter_id % 5) if is_power_on else 0.0,
        'current_l3': 15.0 + (meter_id % 5) if is_power_on else 0.0,
        'power': 3300.0 + (meter_id * 10) if is_power_on else 0.0,
        'power_apparent': 3300.0 + (meter_id * 10) if is_power_on else 0.0,
        'energy': meter_id * 50.5,  # 累積用電量不受供電狀態影響
        'frequency': 50.0 if is_power_on else 0.0,
        'power_factor': 0.95 if is_power_on else 0.0,
        'last_update': datetime.now().isoformat(),
        'error_message': 'RTU 通訊失敗'
    }


@api_bp.route('/meters/<int:meter_id>', methods=['GET'])
def get_meter(meter_id):
    """
    獲取特定電表信息 / Get specific meter information
    支援 MODBUS RTU 實際數據讀取
    
    Args:
        meter_id (int): 電表 ID
        
    Query Parameters:
        use_cache (bool): 是否使用快取數據 (預設: true)
        
    Returns:
        JSON: 電表數據
    """
    try:
        meter_count = current_app.config.get('METER_COUNT', 50)
        if meter_id < 1 or meter_id > meter_count:
            return jsonify({
                'success': False,
                'error': f'Invalid meter ID: {meter_id}. Valid range: 1-{meter_count}',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 解析查詢參數
        use_cache = request.args.get('use_cache', 'true').lower() == 'true'
        rtu_enabled = current_app.config.get('RTU_ENABLED', False)
        
        if rtu_enabled:
            # 使用 MODBUS RTU 讀取實際數據
            rtu_client = get_rtu_client()
            
            if not use_cache:
                rtu_client.clear_cache()
            
            raw_data = rtu_client.read_meter_data(meter_id)
            
            if raw_data.get('online', False):
                # 從數據庫獲取電表配置信息
                from ..database.models import Meter
                db_meter = Meter.query.filter_by(meter_id=meter_id).first()
                
                # 轉換為標準格式並添加計費信息
                meter_data = {
                    'id': meter_id,
                    'name': db_meter.name if db_meter else f'RTU電表{meter_id:02d}',
                    'parking': db_meter.parking if db_meter else f'RTU-{meter_id:04d}',
                    'status': 'online',
                    'power_on': True,
                    'voltage': round(raw_data.get('voltage_avg', 0), 2),
                    'voltage_l1': round(raw_data.get('voltage_l1', 0), 2),
                    'voltage_l2': round(raw_data.get('voltage_l2', 0), 2),
                    'voltage_l3': round(raw_data.get('voltage_l3', 0), 2),
                    'current': round(raw_data.get('current_total', 0), 2),
                    'current_l1': round(raw_data.get('current_l1', 0), 2),
                    'current_l2': round(raw_data.get('current_l2', 0), 2),
                    'current_l3': round(raw_data.get('current_l3', 0), 2),
                    'power': round(raw_data.get('power_active', 0), 2),
                    'power_apparent': round(raw_data.get('power_apparent', 0), 2),
                    'energy': round(raw_data.get('total_energy', 0), 2),
                    'frequency': round(raw_data.get('frequency', 0), 2),
                    'power_factor': round(raw_data.get('power_factor', 0), 3),
                    'last_update': raw_data.get('timestamp'),
                }
                
                # 計算計費信息 (基於累積電能的估算)
                total_energy = meter_data['energy']
                daily_energy = total_energy * 0.025  # 假設每日消耗 2.5%
                monthly_energy = daily_energy * 30
                unit_price = current_app.config.get('DEFAULT_UNIT_PRICE', 3.5)
                
                meter_data.update({
                    'daily_energy': round(daily_energy, 2),
                    'monthly_energy': round(monthly_energy, 2),
                    'cost_today': round(daily_energy * unit_price, 2),
                    'cost_month': round(monthly_energy * unit_price, 2)
                })
            else:
                # 電表離線
                meter_data = _get_fallback_meter_data(meter_id)
                meter_data.update({
                    'daily_energy': 0.0,
                    'monthly_energy': 0.0,
                    'cost_today': 0.0,
                    'cost_month': 0.0
                })
        else:
            # 使用模擬數據
            meter_data = _get_simulated_meter_data(meter_id)
            unit_price = current_app.config.get('DEFAULT_UNIT_PRICE', 3.5)
            daily_energy = meter_id * 12.5
            monthly_energy = meter_id * 375.0
            
            meter_data.update({
                'daily_energy': daily_energy,
                'monthly_energy': monthly_energy,
                'cost_today': daily_energy * unit_price,
                'cost_month': monthly_energy * unit_price
            })
        
        return jsonify({
            'success': True,
            'data': meter_data,
            'rtu_enabled': rtu_enabled,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"獲取電表 {meter_id} 數據時發生錯誤: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/meters/<int:meter_id>/control', methods=['POST'])
def control_meter(meter_id):
    """
    控制電表供電狀態 / Control meter power status
    
    Args:
        meter_id (int): 電表 ID
        
    Returns:
        JSON: 控制結果
    """
    try:
        if meter_id < 1 or meter_id > current_app.config['METER_COUNT']:
            return jsonify({
                'success': False,
                'error': f'Invalid meter ID: {meter_id}',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        power_on = data.get('power_on')
        if power_on is None:
            return jsonify({
                'success': False,
                'error': 'power_on field is required',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        rtu_enabled = current_app.config.get('RTU_ENABLED', False)
        action = "供電" if power_on else "斷電"
        success = True
        error_message = None
        
        if rtu_enabled:
            # 實際控制 MODBUS RELAY
            try:
                rtu_client = get_rtu_client()
                result = rtu_client.write_relay_control(meter_id, power_on)
                if not result:
                    success = False
                    error_message = "MODBUS RELAY控制失敗"
                    current_app.logger.error(f'電表 {meter_id} RELAY控制失敗')
                else:
                    current_app.logger.info(f'電表 {meter_id} RELAY {action}成功')
            except Exception as e:
                success = False
                error_message = f"RELAY控制異常: {str(e)}"
                current_app.logger.error(f'電表 {meter_id} RELAY控制異常: {e}')
        
        # 更新數據庫中的供電狀態
        if success:
            try:
                from ..database.models import Meter, db
                
                meter = Meter.query.filter_by(meter_id=meter_id).first()
                if not meter:
                    meter = Meter(
                        meter_id=meter_id,
                        name=f'RTU電表{meter_id:02d}',
                        parking=f'RTU-{meter_id:04d}',
                        total_energy=0.0,
                        daily_energy=0.0,
                        cost_today=0.0,
                        power_on=power_on
                    )
                    db.session.add(meter)
                else:
                    meter.power_on = power_on
                
                db.session.commit()
                current_app.logger.info(f'電表 {meter_id} 供電狀態已更新到數據庫: {power_on}')
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f'更新電表 {meter_id} 供電狀態失敗: {str(e)}')
                success = False
                error_message = f'數據庫更新失敗: {str(e)}'
        
        if success:
            current_app.logger.info(f'控制電表 {meter_id}: {action}')
            return jsonify({
                'success': True,
                'data': {
                    'meter_id': meter_id,
                    'power_on': power_on,
                    'action': action,
                    'timestamp': datetime.now().isoformat()
                },
                'message': f'電表 {meter_id} {action}成功',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': error_message or f'電表 {meter_id} {action}失敗',
                'timestamp': datetime.now().isoformat()
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/meters/<int:meter_id>/update', methods=['PUT'])
def update_meter(meter_id):
    """
    更新電表配置 / Update meter configuration
    
    Args:
        meter_id (int): 電表 ID
        
    Returns:
        JSON: 更新結果
    """
    try:
        if meter_id < 1 or meter_id > current_app.config['METER_COUNT']:
            return jsonify({
                'success': False,
                'error': f'Invalid meter ID: {meter_id}',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 驗證更新字段 / Validate update fields
        allowed_fields = ['name', 'parking', 'voltage_range', 'current_range', 'power_range', 'household']
        updates = {k: v for k, v in data.items() if k in allowed_fields}
        
        # 處理字段映射：household -> name
        if 'household' in updates:
            updates['name'] = updates.pop('household')
        
        if not updates:
            return jsonify({
                'success': False,
                'error': f'No valid update fields provided. Allowed: {allowed_fields}',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 實際更新數據庫
        try:
            from ..database.models import Meter, db
            
            meter = Meter.query.filter_by(meter_id=meter_id).first()
            if not meter:
                # 如果電表不存在，創建新的
                meter = Meter(
                    meter_id=meter_id,
                    name=f'RTU電表{meter_id:02d}',
                    parking=f'RTU-{meter_id:04d}',
                    total_energy=0.0,
                    daily_energy=0.0,
                    cost_today=0.0,
                    power_on=False
                )
                db.session.add(meter)
            
            # 更新允許的字段
            for field, value in updates.items():
                if hasattr(meter, field):
                    setattr(meter, field, value)
            
            db.session.commit()
            current_app.logger.info(f'電表 {meter_id} 配置已更新到數據庫: {updates}')
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'更新電表 {meter_id} 失敗: {str(e)}')
            return jsonify({
                'success': False,
                'error': f'Database update failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        return jsonify({
            'success': True,
            'data': {
                'meter_id': meter_id,
                'updates': updates,
                'timestamp': datetime.now().isoformat()
            },
            'message': f'電表 {meter_id} 配置更新成功',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/meters/<int:meter_id>/history', methods=['GET'])
def get_meter_history_data(meter_id):
    """
    獲取電表歷史數據 / Get meter historical data
    
    Args:
        meter_id (int): 電表 ID
        
    Returns:
        JSON: 歷史數據
    """
    try:
        if meter_id < 1 or meter_id > current_app.config['METER_COUNT']:
            return jsonify({
                'success': False,
                'error': f'Invalid meter ID: {meter_id}',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 查詢參數 / Query parameters
        days = int(request.args.get('days', 7))  # 預設 7 天
        interval = request.args.get('interval', 'hour')  # hour, day, week
        
        # 生成模擬歷史數據 / Generate mock historical data
        history_data = []
        end_time = datetime.now()
        
        if interval == 'hour':
            delta = timedelta(hours=1)
            count = min(days * 24, 168)  # 最多 7 天的小時數據
        elif interval == 'day':
            delta = timedelta(days=1)
            count = min(days, 30)  # 最多 30 天的日數據
        else:  # week
            delta = timedelta(weeks=1)
            count = min(days // 7, 12)  # 最多 12 週的數據
        
        for i in range(count):
            timestamp = end_time - (delta * i)
            history_data.append({
                'timestamp': timestamp.isoformat(),
                'voltage': 220.0 + (i % 10),
                'current': 15.0 + (i % 5),
                'power': 3300.0 + (i * 5),
                'energy': meter_id * 2.5 + i,
                'cost': (meter_id * 2.5 + i) * current_app.config['DEFAULT_UNIT_PRICE']
            })
        
        # 按時間順序排列 / Sort by timestamp
        history_data.reverse()
        
        return jsonify({
            'success': True,
            'data': {
                'meter_id': meter_id,
                'interval': interval,
                'days': days,
                'records': history_data,
                'count': len(history_data)
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/meters/batch/control', methods=['POST'])
def batch_control_meters():
    """
    批量控制電表 / Batch control meters
    
    Returns:
        JSON: 批量控制結果
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        meter_ids = data.get('meter_ids', [])
        power_on = data.get('power_on')
        
        if not meter_ids:
            return jsonify({
                'success': False,
                'error': 'meter_ids list is required',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        if power_on is None:
            return jsonify({
                'success': False,
                'error': 'power_on field is required',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 驗證電表 ID / Validate meter IDs
        invalid_ids = [mid for mid in meter_ids if mid < 1 or mid > current_app.config['METER_COUNT']]
        if invalid_ids:
            return jsonify({
                'success': False,
                'error': f'Invalid meter IDs: {invalid_ids}',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # TODO: 實際批量控制 MODBUS 設備
        action = "供電" if power_on else "斷電"
        results = []
        
        for meter_id in meter_ids:
            results.append({
                'meter_id': meter_id,
                'success': True,
                'action': action,
                'timestamp': datetime.now().isoformat()
            })
            current_app.logger.info(f'批量控制電表 {meter_id}: {action}')
        
        return jsonify({
            'success': True,
            'data': {
                'total_count': len(meter_ids),
                'success_count': len(results),
                'failed_count': 0,
                'results': results
            },
            'message': f'批量{action} {len(meter_ids)} 個電表成功',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500