#!/usr/bin/env python3
"""
測試 MODBUS RTU 整合功能
Test MODBUS RTU Integration
"""

import os
import sys
import time
from pathlib import Path

# 添加項目路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

def test_power_meter_controller():
    """測試電表控制器"""
    print("=" * 60)
    print("🔧 測試 Power Meter Controller (基於 minimalmodbus)")
    print("=" * 60)
    
    try:
        from backend.services.power_meter_controller_minimal import get_power_meter_controller
        
        # 設定測試參數
        port = os.environ.get('RTU_PORT', 'COM1')
        slave_address = int(os.environ.get('RTU_SLAVE_ADDRESS', '2'))
        
        print(f"📍 連接參數:")
        print(f"   - 端口: {port}")
        print(f"   - 從站地址: {slave_address}")
        print(f"   - 通訊參數: 9600-N-8-1")
        print()
        
        # 創建控制器實例
        controller = get_power_meter_controller(port, slave_address)
        
        # 測試連接狀態
        print("📊 連接狀態:")
        status = controller.get_connection_status()
        for key, value in status.items():
            print(f"   - {key}: {value}")
        print()
        
        # 測試讀取所有參數
        print("📋 讀取電力參數:")
        params = controller.read_all_parameters()
        for name, info in params.items():
            value = info.get('value', 'N/A')
            unit = info.get('unit', '')
            print(f"   - {name}: {value} {unit}")
        print()
        
        # 測試繼電器狀態
        print("🔌 繼電器狀態:")
        relay_status = controller.read_relay_status()
        print(f"   - 當前狀態: {relay_status}")
        print()
        
        # 測試獲取格式化數據
        print("🌐 Web 格式數據:")
        meter_data = controller.get_meter_data(slave_address)
        
        key_fields = [
            'id', 'online', 'voltage_avg', 'current_total', 
            'power_active', 'total_energy', 'is_powered', 'relay_status'
        ]
        
        for field in key_fields:
            value = meter_data.get(field, 'N/A')
            print(f"   - {field}: {value}")
        
        if meter_data.get('error_message'):
            print(f"   - 錯誤訊息: {meter_data['error_message']}")
        
        print()
        print("✅ Power Meter Controller 測試完成!")
        return True
        
    except Exception as e:
        print(f"❌ Power Meter Controller 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_integration():
    """測試 API 整合"""
    print("=" * 60)
    print("🌐 測試 API 整合")
    print("=" * 60)
    
    try:
        # 模擬 Flask app context
        import os
        from unittest.mock import MagicMock
        
        # 設定環境變數
        os.environ['RTU_ENABLED'] = 'true'
        os.environ['RTU_PORT'] = 'COM1'
        os.environ['RTU_SLAVE_ADDRESS'] = '2'
        os.environ['METER_COUNT'] = '50'
        
        # 創建模擬的 Flask app
        app = MagicMock()
        app.config = {
            'RTU_ENABLED': True,
            'RTU_PORT': 'COM1',
            'RTU_SLAVE_ADDRESS': 2,
            'METER_COUNT': 50,
            'DEFAULT_UNIT_PRICE': 4.0
        }
        
        # 測試電表控制器導入
        from backend.services.power_meter_controller_minimal import get_power_meter_controller
        
        controller = get_power_meter_controller('COM1', 2)
        print(f"✅ 控制器創建成功: {type(controller).__name__}")
        
        # 測試數據獲取
        meter_data = controller.get_meter_data(2)
        print(f"✅ 電表數據獲取成功: {len(meter_data)} 個字段")
        
        # 檢查關鍵字段
        required_fields = [
            'id', 'timestamp', 'online', 'voltage_avg', 'current_total',
            'power_active', 'total_energy', 'is_powered'
        ]
        
        missing_fields = [field for field in required_fields if field not in meter_data]
        if missing_fields:
            print(f"⚠️  缺少字段: {missing_fields}")
        else:
            print("✅ 所有必要字段都存在")
        
        print()
        print("✅ API 整合測試完成!")
        return True
        
    except Exception as e:
        print(f"❌ API 整合測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("🚀 MODBUS RTU 整合測試開始")
    print(f"📁 工作目錄: {Path.cwd()}")
    print(f"🐍 Python 版本: {sys.version}")
    print(f"📦 Python 路徑: {sys.path[:3]}...")
    print()
    
    results = []
    
    # 測試 1: Power Meter Controller
    results.append(("Power Meter Controller", test_power_meter_controller()))
    
    # 測試 2: API 整合
    results.append(("API Integration", test_api_integration()))
    
    # 顯示結果
    print("=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print()
    print(f"📈 通過率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有測試通過! MODBUS RTU 整合就緒!")
    else:
        print("⚠️  部分測試失敗，請檢查配置和連接")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)