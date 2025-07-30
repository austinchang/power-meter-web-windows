"""
Power Meter Web Edition - 數據庫模型
Database Models for Power Meter Data Persistence
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Meter(db.Model):
    """電表基本信息表 / Meter Basic Information"""
    __tablename__ = 'meters'
    
    id = db.Column(db.Integer, primary_key=True)
    meter_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    parking = db.Column(db.String(50), nullable=False)
    
    # 累積數據 / Accumulated Data
    total_energy = db.Column(db.Float, default=0.0)          # 總累積用電量 kWh
    daily_energy = db.Column(db.Float, default=0.0)         # 當日用電量 kWh
    cost_today = db.Column(db.Float, default=0.0)           # 當日費用 元
    
    # 供電狀態 / Power Status
    power_on = db.Column(db.Boolean, default=False)         # 是否供電
    last_power_change = db.Column(db.DateTime, default=datetime.utcnow)  # 最後供電狀態變更時間
    
    # 最後更新時間
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 關聯關係
    history_records = db.relationship('MeterHistory', backref='meter', lazy='dynamic')
    billing_records = db.relationship('BillingRecord', backref='meter', lazy='dynamic')
    
    def __repr__(self):
        return f'<Meter {self.meter_id}: {self.name}>'
    
    def to_dict(self):
        """轉換為字典格式"""
        return {
            'id': self.id,
            'meter_id': self.meter_id,
            'name': self.name,
            'parking': self.parking,
            'total_energy': round(self.total_energy, 1),
            'daily_energy': round(self.daily_energy, 1),
            'cost_today': round(self.cost_today, 2),
            'power_on': self.power_on,
            'last_power_change': self.last_power_change.isoformat() if self.last_power_change else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class MeterHistory(db.Model):
    """電表歷史數據表 / Meter Historical Data"""
    __tablename__ = 'meter_history'
    
    id = db.Column(db.Integer, primary_key=True)
    meter_id = db.Column(db.Integer, db.ForeignKey('meters.meter_id'), nullable=False, index=True)
    
    # 即時數據快照 / Real-time Data Snapshot
    voltage = db.Column(db.Float, default=0.0)              # 電壓 V
    current = db.Column(db.Float, default=0.0)              # 電流 A
    power = db.Column(db.Float, default=0.0)                # 功率 W
    energy = db.Column(db.Float, default=0.0)               # 累積電能 kWh
    
    # 供電狀態 / Power Status
    power_on = db.Column(db.Boolean, default=False)
    power_status = db.Column(db.String(20), default='unpowered')
    
    # 記錄時間
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<MeterHistory Meter{self.meter_id} at {self.recorded_at}>'
    
    def to_dict(self):
        """轉換為字典格式"""
        return {
            'id': self.id,
            'meter_id': self.meter_id,
            'voltage': round(self.voltage, 1),
            'current': round(self.current, 1),
            'power': round(self.power, 1),
            'energy': round(self.energy, 1),
            'power_on': self.power_on,
            'power_status': self.power_status,
            'recorded_at': self.recorded_at.isoformat()
        }


class BillingRecord(db.Model):
    """計費記錄表 / Billing Records"""
    __tablename__ = 'billing_records'
    
    id = db.Column(db.Integer, primary_key=True)
    meter_id = db.Column(db.Integer, db.ForeignKey('meters.meter_id'), nullable=False, index=True)
    
    # 計費時段 / Billing Period
    billing_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    
    # 用電數據 / Energy Data
    start_energy = db.Column(db.Float, default=0.0)         # 開始電量
    end_energy = db.Column(db.Float, default=0.0)           # 結束電量
    energy_used = db.Column(db.Float, default=0.0)          # 用電量 kWh
    
    # 計費數據 / Billing Data
    unit_price = db.Column(db.Float, default=4.0)           # 單價 元/度
    total_cost = db.Column(db.Float, default=0.0)           # 總費用 元
    
    # 供電狀態 / Power Status
    power_schedule_type = db.Column(db.String(20), default='open_power')  # open_power / close_power
    
    # 記錄時間
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<BillingRecord Meter{self.meter_id} {self.billing_date}>'
    
    def to_dict(self):
        """轉換為字典格式"""
        return {
            'id': self.id,
            'meter_id': self.meter_id,
            'billing_date': self.billing_date.isoformat(),
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'start_energy': round(self.start_energy, 1),
            'end_energy': round(self.end_energy, 1),
            'energy_used': round(self.energy_used, 1),
            'unit_price': round(self.unit_price, 2),
            'total_cost': round(self.total_cost, 2),
            'power_schedule_type': self.power_schedule_type
        }


class SystemConfig(db.Model):
    """系統配置表 / System Configuration"""
    __tablename__ = 'system_config'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(200))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemConfig {self.key}: {self.value}>'
    
    @staticmethod
    def get_value(key, default=None):
        """獲取配置值"""
        config = SystemConfig.query.filter_by(key=key).first()
        return config.value if config else default
    
    @staticmethod
    def set_value(key, value, description=None):
        """設置配置值"""
        config = SystemConfig.query.filter_by(key=key).first()
        if config:
            config.value = str(value)
            if description:
                config.description = description
            config.updated_at = datetime.utcnow()
        else:
            config = SystemConfig(
                key=key,
                value=str(value),
                description=description or f'Auto-created config for {key}'
            )
            db.session.add(config)
        
        db.session.commit()
        return config


def init_database(app):
    """初始化數據庫"""
    with app.app_context():
        # 創建所有表
        db.create_all()
        
        # 初始化基本配置
        SystemConfig.set_value('unit_price', '4.0', '電費單價 (元/度)')
        SystemConfig.set_value('last_reset_date', datetime.now().date().isoformat(), '最後重置日期')
        
        # 初始化電表數據 (如果沒有的話)
        if Meter.query.count() == 0:
            print("初始化電表數據...")
            for i in range(1, 51):  # 50個電表
                meter = Meter(
                    meter_id=i,
                    name=f'RTU電表{i:02d}',
                    parking=f'RTU-{i:04d}',
                    total_energy=i * 100.0,  # 初始累積電量
                    daily_energy=0.0,
                    cost_today=0.0,
                    power_on=False
                )
                db.session.add(meter)
            
            db.session.commit()
            print("電表數據初始化完成")
        
        print("數據庫初始化完成")