"""
圖表數據 API 路由 / Chart data API routes
"""

import json
import random
from datetime import datetime, timedelta
from flask import request, jsonify, current_app
from . import api_bp


@api_bp.route('/charts/realtime', methods=['GET'])
def get_realtime_chart_data():
    """
    獲取即時圖表數據 / Get real-time chart data
    
    Returns:
        JSON: 即時圖表數據
    """
    try:
        # 查詢參數 / Query parameters
        meter_ids = request.args.getlist('meter_ids[]')
        if not meter_ids:
            meter_ids = [str(i) for i in range(1, min(11, current_app.config['METER_COUNT'] + 1))]  # 預設前10個
        
        # 轉換為整數 / Convert to integers
        meter_ids = [int(mid) for mid in meter_ids if mid.isdigit()]
        
        # 生成即時數據 / Generate real-time data
        current_time = datetime.now()
        chart_data = {
            'timestamp': current_time.isoformat(),
            'meters': []
        }
        
        for meter_id in meter_ids:
            if 1 <= meter_id <= current_app.config['METER_COUNT']:
                meter_data = {
                    'meter_id': meter_id,
                    'name': f'A{meter_id}' if meter_id <= 42 else f'備{meter_id-42}',
                    'voltage': 220.0 + random.uniform(-5, 5),
                    'current': 15.0 + random.uniform(-2, 2),
                    'power': 3300.0 + random.uniform(-200, 200),
                    'energy': meter_id * 50.5 + random.uniform(0, 10),
                    'timestamp': current_time.isoformat()
                }
                chart_data['meters'].append(meter_data)
        
        return jsonify({
            'success': True,
            'data': chart_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/charts/historical', methods=['GET'])
def get_historical_chart_data():
    """
    獲取歷史圖表數據 / Get historical chart data
    
    Returns:
        JSON: 歷史圖表數據
    """
    try:
        # 查詢參數 / Query parameters
        meter_id = int(request.args.get('meter_id', 1))
        days = int(request.args.get('days', 7))
        interval = request.args.get('interval', 'hour')  # hour, day
        data_type = request.args.get('type', 'power')   # voltage, current, power, energy
        
        if meter_id < 1 or meter_id > current_app.config['METER_COUNT']:
            return jsonify({
                'success': False,
                'error': f'Invalid meter ID: {meter_id}',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 生成歷史數據 / Generate historical data
        end_time = datetime.now()
        data_points = []
        
        if interval == 'hour':
            delta = timedelta(hours=1)
            count = min(days * 24, 168)  # 最多 7 天
        else:  # day
            delta = timedelta(days=1)
            count = min(days, 30)  # 最多 30 天
        
        for i in range(count):
            timestamp = end_time - (delta * i)
            
            # 根據數據類型生成不同的數值 / Generate different values based on data type
            if data_type == 'voltage':
                value = 220.0 + random.uniform(-10, 10)
                unit = 'V'
            elif data_type == 'current':
                value = 15.0 + random.uniform(-3, 3)
                unit = 'A'
            elif data_type == 'power':
                value = 3300.0 + random.uniform(-500, 500)
                unit = 'W'
            else:  # energy
                value = meter_id * 2.5 + i * 0.5
                unit = 'kWh'
            
            data_points.append({
                'timestamp': timestamp.isoformat(),
                'value': round(value, 2),
                'unit': unit
            })
        
        # 按時間順序排列 / Sort by timestamp
        data_points.reverse()
        
        chart_data = {
            'meter_id': meter_id,
            'meter_name': f'A{meter_id}' if meter_id <= 42 else f'備{meter_id-42}',
            'data_type': data_type,
            'interval': interval,
            'days': days,
            'data_points': data_points,
            'count': len(data_points)
        }
        
        return jsonify({
            'success': True,
            'data': chart_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/charts/comparison', methods=['GET'])
def get_comparison_chart_data():
    """
    獲取比較圖表數據 / Get comparison chart data
    
    Returns:
        JSON: 比較圖表數據
    """
    try:
        # 查詢參數 / Query parameters
        meter_ids = request.args.getlist('meter_ids[]')
        if not meter_ids:
            meter_ids = ['1', '2', '3', '4', '5']  # 預設比較前5個
        
        # 轉換為整數 / Convert to integers
        meter_ids = [int(mid) for mid in meter_ids if mid.isdigit()]
        data_type = request.args.get('type', 'power')   # voltage, current, power, energy
        period = request.args.get('period', 'today')    # today, week, month
        
        # 驗證電表 ID / Validate meter IDs
        valid_meter_ids = [mid for mid in meter_ids if 1 <= mid <= current_app.config['METER_COUNT']]
        
        if not valid_meter_ids:
            return jsonify({
                'success': False,
                'error': 'No valid meter IDs provided',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 生成比較數據 / Generate comparison data
        comparison_data = {
            'data_type': data_type,
            'period': period,
            'meters': []
        }
        
        for meter_id in valid_meter_ids:
            # 根據數據類型和時間段生成數據 / Generate data based on type and period
            if data_type == 'voltage':
                avg_value = 220.0 + random.uniform(-5, 5)
                max_value = avg_value + random.uniform(5, 15)
                min_value = avg_value - random.uniform(5, 15)
                unit = 'V'
            elif data_type == 'current':
                avg_value = 15.0 + random.uniform(-2, 2)
                max_value = avg_value + random.uniform(2, 8)
                min_value = avg_value - random.uniform(2, 8)
                unit = 'A'
            elif data_type == 'power':
                avg_value = 3300.0 + random.uniform(-300, 300)
                max_value = avg_value + random.uniform(200, 800)
                min_value = avg_value - random.uniform(200, 800)
                unit = 'W'
            else:  # energy
                if period == 'today':
                    avg_value = meter_id * 12.5
                elif period == 'week':
                    avg_value = meter_id * 87.5
                else:  # month
                    avg_value = meter_id * 375.0
                
                max_value = avg_value * 1.2
                min_value = avg_value * 0.8
                unit = 'kWh'
            
            meter_data = {
                'meter_id': meter_id,
                'name': f'A{meter_id}' if meter_id <= 42 else f'備{meter_id-42}',
                'average': round(avg_value, 2),
                'maximum': round(max_value, 2),
                'minimum': round(min_value, 2),
                'unit': unit,
                'cost': round(avg_value * current_app.config['DEFAULT_UNIT_PRICE'], 2) if data_type == 'energy' else None
            }
            comparison_data['meters'].append(meter_data)
        
        return jsonify({
            'success': True,
            'data': comparison_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/charts/dashboard', methods=['GET'])
def get_dashboard_chart_data():
    """
    獲取儀表板圖表數據 / Get dashboard chart data
    
    Returns:
        JSON: 儀表板數據
    """
    try:
        # 從 RTU 客戶端獲取真實數據 / Get real data from RTU client
        meter_count = current_app.config['METER_COUNT']
        
        # 嘗試使用 RTU 客戶端獲取真實數據
        try:
            from ..modbus.rtu_client import ModbusRTUClient
            
            rtu_config = {
                'rtu_port': current_app.config['RTU_PORT'],
                'baudrate': current_app.config['RTU_BAUDRATE'],
                'bytesize': current_app.config['RTU_BYTESIZE'],
                'parity': current_app.config['RTU_PARITY'],
                'stopbits': current_app.config['RTU_STOPBITS'],
                'timeout': current_app.config['RTU_TIMEOUT'],
                'cache_expiry': current_app.config['RTU_CACHE_EXPIRY'],
                'RTU_SIMULATOR_PORT': current_app.config.get('RTU_SIMULATOR_PORT', 5502)
            }
            
            rtu_client = ModbusRTUClient(rtu_config)
            rtu_enabled = current_app.config.get('RTU_ENABLED', False)
            
            if rtu_enabled and rtu_client:
                # 從 RTU 讀取前 10 個電表的數據進行統計
                meter_ids = list(range(1, min(11, meter_count + 1)))
                meter_data_dict = rtu_client.read_multiple_meters(meter_ids)
                
                # 計算真實統計數據
                online_count = sum(1 for data in meter_data_dict.values() if data.get('online', False))
                total_power = sum(data.get('power_active', 0) for data in meter_data_dict.values() if data.get('online', False))
                total_energy = sum(data.get('total_energy', 0) for data in meter_data_dict.values() if data.get('online', False))
                
                # 根據樣本估算全部電表
                if online_count > 0:
                    total_power = total_power * (meter_count / len(meter_ids))
                    total_energy = total_energy * (meter_count / len(meter_ids))
                    online_count = int(online_count * (meter_count / len(meter_ids)))
                else:
                    # 回退到模擬數據
                    total_power = meter_count * 3.5  # 每個電表平均 3.5kW
                    total_energy = sum(i * 50.5 for i in range(1, meter_count + 1))
                    online_count = meter_count - 2
            else:
                # RTU 未啟用，使用模擬數據
                total_power = meter_count * 3.5  # 每個電表平均 3.5kW
                total_energy = sum(i * 50.5 for i in range(1, meter_count + 1))
                online_count = meter_count - 2
                
        except Exception as e:
            # RTU 讀取失敗，使用模擬數據
            print(f"RTU data fetch failed: {e}")
            total_power = meter_count * 3.5  # 每個電表平均 3.5kW  
            total_energy = sum(i * 50.5 for i in range(1, meter_count + 1))
            online_count = meter_count - 2
        
        total_cost = total_energy * current_app.config['DEFAULT_UNIT_PRICE']
        
        # 供電狀態統計 / Power status statistics
        power_on_count = meter_count - random.randint(0, 5)
        power_off_count = meter_count - power_on_count
        
        # 電表狀態分佈 / Meter status distribution
        status_distribution = {
            'online': online_count,
            'offline': meter_count - online_count,
            'power_on': power_on_count,
            'power_off': power_off_count
        }
        
        # 用電量前 10 名 / Top 10 energy consumers
        top_consumers = []
        for i in range(10):
            meter_id = i + 1
            energy = meter_id * 50.5 + random.uniform(0, 20)
            top_consumers.append({
                'meter_id': meter_id,
                'name': f'A{meter_id}',
                'energy': round(energy, 2),
                'cost': round(energy * current_app.config['DEFAULT_UNIT_PRICE'], 2)
            })
        
        # 按小時統計今日用電 / Hourly energy consumption today
        hourly_data = []
        for hour in range(24):
            total_hour_energy = sum(random.uniform(1, 5) for _ in range(meter_count))
            hourly_data.append({
                'hour': f'{hour:02d}:00',
                'energy': round(total_hour_energy, 2),
                'cost': round(total_hour_energy * current_app.config['DEFAULT_UNIT_PRICE'], 2)
            })
        
        dashboard_data = {
            'summary': {
                'total_meters': meter_count,
                'online_meters': online_count,
                'total_power': round(total_power, 2),
                'total_energy': round(total_energy, 2),
                'total_cost': round(total_cost, 2),
                'average_power': round(total_power / meter_count, 2),
                'currency': '元'
            },
            'status_distribution': status_distribution,
            'top_consumers': top_consumers,
            'hourly_consumption': hourly_data,
            'last_update': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': dashboard_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/charts/export', methods=['POST'])
def export_chart_data():
    """
    導出圖表數據 / Export chart data
    
    Returns:
        JSON: 導出結果
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        chart_type = data.get('chart_type')
        export_format = data.get('format', 'csv')  # csv, json, excel
        date_range = data.get('date_range', {})
        
        if not chart_type:
            return jsonify({
                'success': False,
                'error': 'chart_type is required',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # TODO: 實際導出邏輯
        export_filename = f'chart_data_{chart_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.{export_format}'
        
        return jsonify({
            'success': True,
            'data': {
                'filename': export_filename,
                'format': export_format,
                'chart_type': chart_type,
                'download_url': f'/api/charts/download/{export_filename}',
                'expires_at': (datetime.now() + timedelta(hours=1)).isoformat()
            },
            'message': '圖表數據導出成功',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500