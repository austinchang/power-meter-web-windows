#!/usr/bin/env python3
"""
Power Meter Web Edition - 資料庫初始化腳本
Database Setup Script for Windows
"""

import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

# 添加專案根目錄到 Python 路徑
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def create_database_structure():
    """建立資料庫結構"""
    
    # 確保資料庫目錄存在
    db_dir = PROJECT_ROOT / 'data' / 'database'
    db_dir.mkdir(parents=True, exist_ok=True)
    
    db_path = db_dir / 'power_meter_web.db'
    
    try:
        print("🗄️  初始化資料庫...")
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 建立 meters 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meter_id INTEGER UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                parking VARCHAR(50) NOT NULL,
                total_energy REAL DEFAULT 0.0,
                daily_energy REAL DEFAULT 0.0,
                cost_today REAL DEFAULT 0.0,
                power_on BOOLEAN DEFAULT 0,
                last_power_change DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 建立 meter_history 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meter_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meter_id INTEGER NOT NULL,
                voltage REAL DEFAULT 0.0,
                current REAL DEFAULT 0.0,
                power REAL DEFAULT 0.0,
                energy REAL DEFAULT 0.0,
                power_on BOOLEAN DEFAULT 0,
                power_status VARCHAR(20) DEFAULT 'unpowered',
                recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (meter_id) REFERENCES meters (meter_id)
            )
        ''')
        
        # 建立 billing_records 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS billing_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meter_id INTEGER NOT NULL,
                billing_date DATE NOT NULL,
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                start_energy REAL DEFAULT 0.0,
                end_energy REAL DEFAULT 0.0,
                energy_used REAL DEFAULT 0.0,
                unit_price REAL DEFAULT 4.0,
                total_cost REAL DEFAULT 0.0,
                power_schedule_type VARCHAR(20) DEFAULT 'open_power',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (meter_id) REFERENCES meters (meter_id)
            )
        ''')
        
        # 建立 system_config 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key VARCHAR(100) UNIQUE NOT NULL,
                value TEXT NOT NULL,
                description VARCHAR(200),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 建立索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_meter_id ON meters(meter_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_meter_id ON meter_history(meter_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_recorded_at ON meter_history(recorded_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_billing_meter_id ON billing_records(meter_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_billing_date ON billing_records(billing_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_config_key ON system_config(key)')
        
        print("✅ 資料庫表格建立完成")
        
        # 初始化系統配置
        configs = [
            ('unit_price', '4.0', '電費單價 (元/度)'),
            ('last_reset_date', datetime.now().date().isoformat(), '最後重置日期'),
            ('system_version', '1.0.0-windows', '系統版本'),
            ('installation_date', datetime.now().isoformat(), '安裝日期')
        ]
        
        for key, value, description in configs:
            cursor.execute('''
                INSERT OR REPLACE INTO system_config (key, value, description)
                VALUES (?, ?, ?)
            ''', (key, value, description))
        
        print("✅ 系統配置初始化完成")
        
        # 初始化電表資料 (預設 50 個電表)
        cursor.execute('SELECT COUNT(*) FROM meters')
        meter_count = cursor.fetchone()[0]
        
        if meter_count == 0:
            print("🏭 初始化電表資料...")
            
            # 插入 50 個電表的基本資料
            for i in range(1, 51):
                # 計算區域 (A-E 區，每區 10 個)
                zone = chr(ord('A') + (i - 1) // 10)
                zone_number = ((i - 1) % 10) + 1
                
                cursor.execute('''
                    INSERT INTO meters (
                        meter_id, name, parking, total_energy, 
                        daily_energy, cost_today, power_on
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    i,
                    f'RTU電表{i:02d}',
                    f'{zone}{zone_number:02d}-{i:04d}',
                    i * 100.0,  # 初始累積電量
                    0.0,
                    0.0,
                    False
                ))
            
            print(f"✅ 已初始化 50 個電表資料")
        else:
            print(f"ℹ️  電表資料已存在 ({meter_count} 個電表)")
        
        conn.commit()
        conn.close()
        
        print(f"✅ 資料庫初始化完成：{db_path}")
        return True
        
    except Exception as e:
        print(f"❌ 資料庫初始化失敗: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def verify_database():
    """驗證資料庫結構"""
    db_path = PROJECT_ROOT / 'data' / 'database' / 'power_meter_web.db'
    
    if not db_path.exists():
        print("❌ 資料庫檔案不存在")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 檢查表格
        tables = ['meters', 'meter_history', 'billing_records', 'system_config']
        
        print("\n🔍 驗證資料庫結構...")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone()[0] == 1:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"✅ {table}: {count} 筆記錄")
            else:
                print(f"❌ {table}: 表格不存在")
                return False
        
        conn.close()
        print("✅ 資料庫結構驗證完成")
        return True
        
    except Exception as e:
        print(f"❌ 資料庫驗證失敗: {e}")
        return False

def main():
    """主程式"""
    print("=" * 50)
    print("🗄️  Power Meter Web Edition - 資料庫設置")
    print("=" * 50)
    
    # 建立資料庫
    if create_database_structure():
        # 驗證資料庫
        if verify_database():
            print("\n🎉 資料庫設置完成！")
            print("\n接下來可以：")
            print("1. 執行 scripts\\test_modbus.py 測試 MODBUS 連接")
            print("2. 執行 start.bat 啟動 Web 系統")
        else:
            print("\n⚠️  資料庫驗證失敗，請重新執行設置")
            return False
    else:
        print("\n❌ 資料庫設置失敗")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        
        # 如果是直接執行（不是被 install.bat 調用），則等待用戶按鍵
        if len(sys.argv) == 1:  # 沒有命令列參數
            input("\n按 Enter 結束...")
            
    except Exception as e:
        print(f"❌ 程式執行錯誤: {e}")
        input("\n按 Enter 結束...")