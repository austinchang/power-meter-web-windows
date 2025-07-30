"""
Power Meter Service - 數據持久化服務
Handles meter data persistence and energy calculation
"""

import logging
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError

from ..database import db, Meter, MeterHistory, BillingRecord, SystemConfig


class MeterDataService:
    """電表數據服務 - 處理數據持久化和累積計算"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.unit_price = 4.0  # 默認單價，稍後從配置獲取
    
    def _get_unit_price(self):
        """獲取當前電費單價"""
        try:
            return float(SystemConfig.get_value('unit_price', 4.0))
        except:
            return self.unit_price
    
    def get_or_create_meter(self, meter_id: int, name: str = None, parking: str = None) -> Meter:
        """獲取或創建電表記錄"""
        try:
            meter = Meter.query.filter_by(meter_id=meter_id).first()
            
            if not meter:
                # 創建新電表記錄
                meter = Meter(
                    meter_id=meter_id,
                    name=name or f'RTU電表{meter_id:02d}',
                    parking=parking or f'RTU-{meter_id:04d}',
                    total_energy=0.0,
                    daily_energy=0.0,
                    cost_today=0.0,
                    power_on=False
                )
                db.session.add(meter)
                db.session.commit()
                self.logger.info(f"創建新電表記錄: {meter_id}")
            
            return meter
            
        except SQLAlchemyError as e:
            self.logger.error(f"數據庫操作失敗 - get_or_create_meter({meter_id}): {e}")
            db.session.rollback()
            raise
    
    def save_meter_data(self, meter_data: Dict) -> bool:
        """保存電表數據並更新累積計算"""
        try:
            meter_id = meter_data.get('meter_id')
            if not meter_id:
                return False
            
            # 獲取電表記錄
            meter = self.get_or_create_meter(
                meter_id=meter_id,
                name=meter_data.get('name'),
                parking=meter_data.get('parking')
            )
            
            # 更新供電狀態
            new_power_status = meter_data.get('power_on', False)
            power_status_changed = meter.power_on != new_power_status
            
            if power_status_changed:
                meter.last_power_change = datetime.utcnow()
                self.logger.info(f"電表 {meter_id} 供電狀態變更: {meter.power_on} -> {new_power_status}")
            
            # 計算用電量累積
            current_energy = float(meter_data.get('energy', 0))
            if new_power_status and current_energy > meter.total_energy:
                # 只有在供電且有用電時才累積
                energy_diff = current_energy - meter.total_energy
                meter.daily_energy += energy_diff
                self.logger.debug(f"電表 {meter_id} 累積用電: +{energy_diff:.1f} kWh")
            
            # 更新電表數據
            meter.total_energy = current_energy
            meter.power_on = new_power_status
            meter.cost_today = meter.daily_energy * self._get_unit_price()
            meter.last_updated = datetime.utcnow()
            
            # 保存歷史記錄
            history = MeterHistory(
                meter_id=meter_id,
                voltage=float(meter_data.get('voltage', 0)),
                current=float(meter_data.get('current', 0)),
                power=float(meter_data.get('power', 0)),
                energy=current_energy,
                power_on=new_power_status,
                power_status=meter_data.get('power_status', 'unpowered'),
                recorded_at=datetime.utcnow()
            )
            
            db.session.add(history)
            db.session.commit()
            
            return True
            
        except SQLAlchemyError as e:
            self.logger.error(f"保存電表數據失敗 - meter_id={meter_id}: {e}")
            db.session.rollback()
            return False
        except Exception as e:
            self.logger.error(f"保存電表數據時發生未知錯誤 - meter_id={meter_id}: {e}")
            return False
    
    def batch_save_meters(self, meters_data: List[Dict]) -> int:
        """批量保存電表數據"""
        success_count = 0
        
        for meter_data in meters_data:
            if self.save_meter_data(meter_data):
                success_count += 1
        
        self.logger.info(f"批量保存電表數據完成: {success_count}/{len(meters_data)}")
        return success_count
    
    def get_meter_current_data(self, meter_id: int) -> Optional[Dict]:
        """獲取電表當前數據 - 根據供電時段實時判斷狀態"""
        try:
            meter = Meter.query.filter_by(meter_id=meter_id).first()
            if not meter:
                return None
            
            # 檢查當前供電時段狀態
            current_power_active = self.is_power_schedule_active('open_power')
            
            # 獲取最新歷史記錄
            latest_history = MeterHistory.query.filter_by(meter_id=meter_id).order_by(
                MeterHistory.recorded_at.desc()
            ).first()
            
            result = meter.to_dict()
            
            # 根據供電時段覆蓋電表的供電狀態
            result['power_on'] = current_power_active
            
            if latest_history:
                result.update({
                    'voltage': latest_history.voltage if current_power_active else 0.0,
                    'current': latest_history.current if current_power_active else 0.0,
                    'power': latest_history.power if current_power_active else 0.0,
                    'power_status': 'powered' if current_power_active else 'unpowered',
                    'timestamp': latest_history.recorded_at.isoformat()
                })
            else:
                # 如果沒有歷史記錄，根據供電狀態設置預設值
                result.update({
                    'voltage': 220.0 if current_power_active else 0.0,
                    'current': 10.0 if current_power_active else 0.0,
                    'power': 2200.0 if current_power_active else 0.0,
                    'power_status': 'powered' if current_power_active else 'unpowered',
                    'timestamp': datetime.now().isoformat()
                })
            
            return result
            
        except SQLAlchemyError as e:
            self.logger.error(f"獲取電表數據失敗 - meter_id={meter_id}: {e}")
            return None
    
    def get_all_meters_current_data(self) -> List[Dict]:
        """獲取所有電表當前數據"""
        try:
            meters = Meter.query.all()
            results = []
            
            for meter in meters:
                meter_data = self.get_meter_current_data(meter.meter_id)
                if meter_data:
                    results.append(meter_data)
            
            return results
            
        except SQLAlchemyError as e:
            self.logger.error(f"獲取所有電表數據失敗: {e}")
            return []
    
    def reset_daily_energy(self, meter_id: int = None) -> bool:
        """重置每日用電量 (可指定電表或全部)"""
        try:
            if meter_id:
                meter = Meter.query.filter_by(meter_id=meter_id).first()
                if meter:
                    meter.daily_energy = 0.0
                    meter.cost_today = 0.0
            else:
                # 重置所有電表
                Meter.query.update({
                    'daily_energy': 0.0,
                    'cost_today': 0.0
                })
            
            db.session.commit()
            
            # 更新重置日期
            SystemConfig.set_value('last_reset_date', datetime.now().date().isoformat())
            
            self.logger.info(f"每日用電量重置完成 - meter_id: {meter_id or 'ALL'}")
            return True
            
        except SQLAlchemyError as e:
            self.logger.error(f"重置每日用電量失敗 - meter_id={meter_id}: {e}")
            db.session.rollback()
            return False
    
    def check_and_auto_reset_daily(self) -> bool:
        """檢查並自動重置每日用電量 (如果是新的一天)"""
        try:
            last_reset_date_str = SystemConfig.get_value('last_reset_date')
            today = datetime.now().date()
            
            if last_reset_date_str:
                last_reset_date = datetime.fromisoformat(last_reset_date_str).date()
                if last_reset_date < today:
                    self.reset_daily_energy()
                    self.logger.info(f"自動重置每日用電量: {last_reset_date} -> {today}")
                    return True
            else:
                # 第一次運行，設置重置日期
                SystemConfig.set_value('last_reset_date', today.isoformat())
            
            return False
            
        except Exception as e:
            self.logger.error(f"檢查每日重置失敗: {e}")
            return False
    
    def create_billing_record(self, meter_id: int, energy_used: float, 
                            power_schedule_type: str = 'open_power') -> Optional[BillingRecord]:
        """創建計費記錄"""
        try:
            unit_price = self._get_unit_price()
            billing_record = BillingRecord(
                meter_id=meter_id,
                billing_date=datetime.now().date(),
                start_time=datetime.utcnow(),
                energy_used=energy_used,
                unit_price=unit_price,
                total_cost=energy_used * unit_price,
                power_schedule_type=power_schedule_type
            )
            
            db.session.add(billing_record)
            db.session.commit()
            
            return billing_record
            
        except SQLAlchemyError as e:
            self.logger.error(f"創建計費記錄失敗 - meter_id={meter_id}: {e}")
            db.session.rollback()
            return None
    
    def get_meter_history(self, meter_id: int, hours: int = 24) -> List[Dict]:
        """獲取電表歷史數據"""
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            
            history_records = MeterHistory.query.filter(
                MeterHistory.meter_id == meter_id,
                MeterHistory.recorded_at >= since
            ).order_by(MeterHistory.recorded_at.asc()).all()
            
            return [record.to_dict() for record in history_records]
            
        except SQLAlchemyError as e:
            self.logger.error(f"獲取電表歷史失敗 - meter_id={meter_id}: {e}")
            return []
    
    def is_power_schedule_active(self, schedule_type: str = 'open_power') -> bool:
        """檢查供電時段是否活躍 - 優先從資料庫讀取用戶設定"""
        try:
            from flask import current_app
            from ..database.models import SystemConfig
            import json
            
            # 優先從資料庫讀取用戶設定的時段
            try:
                schedule_json = SystemConfig.get_value('power_schedule')
                
                if schedule_json:
                    schedule = json.loads(schedule_json)
                    power_config = schedule.get(schedule_type, {})
                    self.logger.debug(f"從資料庫讀取供電時段設定: {schedule_type} = {power_config}")
                else:
                    # 如果資料庫沒有配置，使用預設配置
                    schedule = current_app.config.get('DEFAULT_POWER_SCHEDULE', {
                        'open_power': {'start': '06:00:00', 'end': '22:00:00'},
                        'close_power': {'start': '22:00:00', 'end': '06:00:00'}
                    })
                    power_config = schedule.get(schedule_type, {})
                    self.logger.debug(f"使用預設供電時段設定: {schedule_type} = {power_config}")
                
            except Exception as db_error:
                self.logger.warning(f"無法從資料庫讀取供電時段，使用預設配置: {db_error}")
                # 如果資料庫讀取失敗，回退到預設配置
                schedule = current_app.config.get('DEFAULT_POWER_SCHEDULE', {
                    'open_power': {'start': '06:00:00', 'end': '22:00:00'},
                    'close_power': {'start': '22:00:00', 'end': '06:00:00'}
                })
                power_config = schedule.get(schedule_type, {})
            
            if not power_config:
                self.logger.warning(f"找不到供電時段配置: {schedule_type}")
                return False
            
            start_time_str = power_config.get('start', '06:00:00')
            end_time_str = power_config.get('end', '22:00:00')
            
            start_time = time.fromisoformat(start_time_str)
            end_time = time.fromisoformat(end_time_str)
            current_time = datetime.now().time()
            
            self.logger.debug(f"供電時段檢查: {schedule_type} = {start_time_str}-{end_time_str}, 當前時間: {current_time}")
            
            if start_time <= end_time:
                # 同日內的時段
                is_active = start_time <= current_time <= end_time
            else:
                # 跨日的時段
                is_active = current_time >= start_time or current_time <= end_time
            
            self.logger.debug(f"供電時段 {schedule_type} 活躍狀態: {is_active}")
            return is_active
            
        except Exception as e:
            self.logger.error(f"檢查供電時段失敗: {e}")
            return False


# 全局服務實例
meter_service = MeterDataService()