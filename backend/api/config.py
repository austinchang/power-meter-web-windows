"""
配置管理 API 路由 / Configuration management API routes
"""

import json
from datetime import datetime
from flask import request, jsonify, current_app
from . import api_bp


@api_bp.route('/config/themes', methods=['GET'])
def get_themes():
    """
    獲取可用主題列表 / Get available themes list
    
    Returns:
        JSON: 主題列表
    """
    try:
        themes_data = {
            'available_themes': current_app.config.get('AVAILABLE_THEMES', []),
            'default_theme': current_app.config.get('DEFAULT_THEME', 'light'),
            'themes_info': {
                'light': {
                    'name': 'Light Theme',
                    'description': '明亮主題，適合日間使用',
                    'primary_color': '#2196F3',
                    'background_color': '#FFFFFF'
                },
                'dark': {
                    'name': 'Dark Theme', 
                    'description': '暗黑主題，適合夜間使用',
                    'primary_color': '#64B5F6',
                    'background_color': '#1E1E1E'
                },
                'industrial': {
                    'name': 'Industrial Theme',
                    'description': '工業主題，專業監控風格',
                    'primary_color': '#FF6B35',
                    'background_color': '#263238'
                }
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': themes_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/config/themes/<theme_name>', methods=['PUT'])
def set_theme(theme_name):
    """
    設置當前主題 / Set current theme
    
    Args:
        theme_name (str): 主題名稱
        
    Returns:
        JSON: 設置結果
    """
    try:
        available_themes = current_app.config.get('AVAILABLE_THEMES', [])
        
        if theme_name not in available_themes:
            return jsonify({
                'success': False,
                'error': f'Invalid theme name. Available themes: {available_themes}',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # TODO: 實際保存主題設置到數據庫或配置文件
        current_app.logger.info(f'設置主題為: {theme_name}')
        
        return jsonify({
            'success': True,
            'data': {
                'theme_name': theme_name,
                'applied_at': datetime.now().isoformat()
            },
            'message': f'主題已設置為 {theme_name}',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/config/user-preferences', methods=['GET'])
def get_user_preferences():
    """
    獲取用戶偏好設置 / Get user preferences
    
    Returns:
        JSON: 用戶偏好設置
    """
    try:
        # TODO: 從數據庫讀取實際用戶偏好
        preferences_data = {
            'display': {
                'theme': current_app.config.get('DEFAULT_THEME', 'light'),
                'language': 'zh-TW',
                'timezone': 'Asia/Taipei',
                'date_format': 'YYYY-MM-DD',
                'time_format': '24h'
            },
            'notifications': {
                'email_alerts': True,
                'sound_alerts': False,
                'desktop_notifications': True,
                'alert_thresholds': {
                    'voltage_high': 250,
                    'voltage_low': 200,
                    'current_high': 40,
                    'power_high': 12000
                }
            },
            'dashboard': {
                'auto_refresh': True,
                'refresh_interval': 5,  # seconds
                'default_chart_type': 'line',
                'show_grid': True,
                'animation_enabled': True
            },
            'excel_interface': {
                'show_meter_groups': True,
                'highlight_power_status': True,
                'auto_save_changes': True,
                'confirm_power_control': True
            },
            'data': {
                'historical_data_retention': 365,  # days
                'export_default_format': 'csv',
                'backup_frequency': 'daily'
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': preferences_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/config/user-preferences', methods=['PUT'])
def update_user_preferences():
    """
    更新用戶偏好設置 / Update user preferences
    
    Returns:
        JSON: 更新結果
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 驗證設置項目 / Validate settings
        valid_categories = ['display', 'notifications', 'dashboard', 'excel_interface', 'data']
        updates = {}
        
        for category, settings in data.items():
            if category in valid_categories and isinstance(settings, dict):
                updates[category] = settings
        
        if not updates:
            return jsonify({
                'success': False,
                'error': f'No valid preferences provided. Valid categories: {valid_categories}',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # TODO: 實際保存到數據庫
        current_app.logger.info(f'更新用戶偏好設置: {updates}')
        
        return jsonify({
            'success': True,
            'data': {
                'updates': updates,
                'updated_at': datetime.now().isoformat()
            },
            'message': f'用戶偏好設置更新成功，已更新 {len(updates)} 個類別',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/config/meter-groups', methods=['GET'])
def get_meter_groups():
    """
    獲取電表分組配置 / Get meter groups configuration
    
    Returns:
        JSON: 電表分組配置
    """
    try:
        # 標準的電表分組配置 / Standard meter groups configuration
        groups_data = [
            {
                'group_id': 1,
                'name': '分錶群組 1-10',
                'start_id': 1,
                'end_id': 10,
                'count': 10,
                'description': '主要用電區域 A'
            },
            {
                'group_id': 2,
                'name': '分錶群組 11-20',
                'start_id': 11,
                'end_id': 20,
                'count': 10,
                'description': '主要用電區域 B'
            },
            {
                'group_id': 3,
                'name': '分錶群組 21-30',
                'start_id': 21,
                'end_id': 30,
                'count': 10,
                'description': '主要用電區域 C'
            },
            {
                'group_id': 4,
                'name': '分錶群組 31-40',
                'start_id': 31,
                'end_id': 40,
                'count': 10,
                'description': '主要用電區域 D'
            },
            {
                'group_id': 5,
                'name': '分錶群組 41-48',
                'start_id': 41,
                'end_id': 48,
                'count': 8,
                'description': '備用電表區域'
            }
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'groups': groups_data,
                'total_groups': len(groups_data),
                'total_meters': sum(group['count'] for group in groups_data)
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/config/meter-groups/<int:group_id>', methods=['PUT'])
def update_meter_group(group_id):
    """
    更新電表分組配置 / Update meter group configuration
    
    Args:
        group_id (int): 分組 ID
        
    Returns:
        JSON: 更新結果
    """
    try:
        if group_id < 1 or group_id > 5:
            return jsonify({
                'success': False,
                'error': 'Invalid group ID. Valid range: 1-5',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 允許更新的字段 / Allowed update fields
        allowed_fields = ['name', 'description']
        updates = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not updates:
            return jsonify({
                'success': False,
                'error': f'No valid update fields provided. Allowed: {allowed_fields}',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # TODO: 實際更新數據庫
        current_app.logger.info(f'更新電表分組 {group_id}: {updates}')
        
        return jsonify({
            'success': True,
            'data': {
                'group_id': group_id,
                'updates': updates,
                'updated_at': datetime.now().isoformat()
            },
            'message': f'電表分組 {group_id} 配置更新成功',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/config/export-settings', methods=['GET'])
def export_config_settings():
    """
    導出配置設置 / Export configuration settings
    
    Returns:
        JSON: 配置導出結果
    """
    try:
        # 收集所有配置數據 / Collect all configuration data
        config_export = {
            'app_info': {
                'name': 'Power Meter GUI Professional - Web Edition',
                'version': '1.0.0-web-beta',
                'exported_at': datetime.now().isoformat()
            },
            'system_config': {
                'meter_count': current_app.config.get('METER_COUNT'),
                'update_intervals': {
                    'real_time': current_app.config.get('REAL_TIME_UPDATE_INTERVAL'),
                    'database': current_app.config.get('DATABASE_SAVE_INTERVAL'),
                    'chart': current_app.config.get('CHART_UPDATE_INTERVAL')
                },
                'default_values': {
                    'voltage_range': current_app.config.get('DEFAULT_VOLTAGE_RANGE'),
                    'current_range': current_app.config.get('DEFAULT_CURRENT_RANGE'),
                    'power_range': current_app.config.get('DEFAULT_POWER_RANGE'),
                    'unit_price': current_app.config.get('DEFAULT_UNIT_PRICE')
                }
            },
            'power_schedule': current_app.config.get('DEFAULT_POWER_SCHEDULE'),
            'themes': {
                'available': current_app.config.get('AVAILABLE_THEMES'),
                'default': current_app.config.get('DEFAULT_THEME')
            }
        }
        
        # 生成導出文件名 / Generate export filename
        export_filename = f'power_meter_config_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        return jsonify({
            'success': True,
            'data': {
                'config': config_export,
                'filename': export_filename,
                'format': 'json',
                'size': len(json.dumps(config_export)),
                'exported_at': datetime.now().isoformat()
            },
            'message': '配置導出成功',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@api_bp.route('/config/import-settings', methods=['POST'])
def import_config_settings():
    """
    導入配置設置 / Import configuration settings
    
    Returns:
        JSON: 配置導入結果
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        config_data = data.get('config')
        if not config_data:
            return jsonify({
                'success': False,
                'error': 'Configuration data is required',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 驗證配置格式 / Validate configuration format
        required_sections = ['system_config', 'power_schedule', 'themes']
        missing_sections = [section for section in required_sections if section not in config_data]
        
        if missing_sections:
            return jsonify({
                'success': False,
                'error': f'Missing required configuration sections: {missing_sections}',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # TODO: 實際導入配置到數據庫
        imported_sections = []
        for section in required_sections:
            if section in config_data:
                imported_sections.append(section)
                current_app.logger.info(f'導入配置段落: {section}')
        
        return jsonify({
            'success': True,
            'data': {
                'imported_sections': imported_sections,
                'total_sections': len(imported_sections),
                'imported_at': datetime.now().isoformat()
            },
            'message': f'配置導入成功，已導入 {len(imported_sections)} 個段落',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500