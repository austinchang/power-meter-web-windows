/**
 * Power Meter Web Edition Diagnostic Tool
 * 診斷工具 - 用於檢查 Web 應用程式的各個組件是否正常運作
 */

window.diagnosticTool = {
    /**
     * 執行完整的診斷檢查
     */
    runFullDiagnostic: function() {
        console.log('=== Power Meter Web Edition Diagnostic ===');
        const results = {};
        
        // 1. 檢查基本 JavaScript 環境
        results.javascript = this.checkJavaScript();
        console.log('1. JavaScript:', results.javascript ? 'OK' : 'FAILED');
        
        // 2. 檢查必要的庫
        results.libraries = this.checkLibraries();
        console.log('2. Libraries:', results.libraries.all ? 'OK' : 'PARTIAL');
        
        // 3. 檢查 Socket.IO
        results.socketIO = this.checkSocketIO();
        console.log('3. Socket.IO:', results.socketIO ? 'OK' : 'FAILED');
        
        // 4. 檢查主應用程式
        results.mainApp = this.checkMainApp();
        console.log('4. PowerMeterApp:', results.mainApp ? 'OK' : 'FAILED');
        
        // 5. 檢查 Excel 界面
        results.excelInterface = this.checkExcelInterface();
        console.log('5. ExcelInterface:', results.excelInterface ? 'OK' : 'FAILED');
        
        // 6. 檢查 DOM 元素
        results.domElements = this.checkDOMElements();
        console.log('6. Critical DOM Elements:', results.domElements.all ? 'OK' : 'PARTIAL');
        
        // 7. 檢查事件監聽器
        results.eventListeners = this.checkEventListeners();
        console.log('7. Event Listeners:', results.eventListeners ? 'OK' : 'FAILED');
        
        // 8. 測試 API 連接
        this.testAPI().then(apiResult => {
            results.api = apiResult;
            console.log('8. API Test:', apiResult ? 'OK' : 'FAILED');
            
            // 顯示總結
            this.showDiagnosticSummary(results);
        });
        
        return results;
    },
    
    /**
     * 檢查 JavaScript 基本功能
     */
    checkJavaScript: function() {
        try {
            // 測試基本 JavaScript 功能
            const testArray = [1, 2, 3];
            const testObject = { test: 'value' };
            return testArray.length === 3 && testObject.test === 'value';
        } catch (error) {
            console.error('JavaScript check failed:', error);
            return false;
        }
    },
    
    /**
     * 檢查必要的庫
     */
    checkLibraries: function() {
        const libraries = {
            bootstrap: typeof bootstrap !== 'undefined',
            socketio: typeof io !== 'undefined'
        };
        
        // 可選庫 (不會影響 all 狀態)
        const optionalLibraries = {
            jquery: typeof $ !== 'undefined',
            chartjs: typeof Chart !== 'undefined'
        };
        
        libraries.all = Object.values(libraries).every(lib => lib);
        
        // 記錄缺失的必要庫
        Object.keys(libraries).forEach(lib => {
            if (!libraries[lib] && lib !== 'all') {
                console.warn(`Missing required library: ${lib}`);
            }
        });
        
        // 記錄可選庫狀態
        Object.keys(optionalLibraries).forEach(lib => {
            if (!optionalLibraries[lib]) {
                console.info(`Optional library not found: ${lib}`);
            } else {
                console.info(`Optional library found: ${lib}`);
            }
        });
        
        return Object.assign(libraries, optionalLibraries);
    },
    
    /**
     * 檢查 Socket.IO 連接
     */
    checkSocketIO: function() {
        try {
            return typeof io !== 'undefined' && window.powerMeterApp && window.powerMeterApp.socket;
        } catch (error) {
            console.error('Socket.IO check failed:', error);
            return false;
        }
    },
    
    /**
     * 檢查主應用程式
     */
    checkMainApp: function() {
        try {
            return window.powerMeterApp && 
                   typeof window.powerMeterApp.init === 'function' &&
                   typeof window.powerMeterApp.isConnected !== 'undefined';
        } catch (error) {
            console.error('Main app check failed:', error);
            return false;
        }
    },
    
    /**
     * 檢查 Excel 界面
     */
    checkExcelInterface: function() {
        try {
            return window.excelInterface && 
                   typeof window.excelInterface.init === 'function';
        } catch (error) {
            console.error('Excel interface check failed:', error);
            return false;
        }
    },
    
    /**
     * 檢查關鍵 DOM 元素
     */
    checkDOMElements: function() {
        const criticalElements = [
            'connectionStatus',
            'connectionText',
            'notificationToast'
        ];
        
        const elements = {};
        criticalElements.forEach(id => {
            elements[id] = !!document.getElementById(id);
            if (!elements[id]) {
                console.warn(`Missing DOM element: ${id}`);
            }
        });
        
        elements.all = Object.values(elements).every(element => element);
        
        // 檢查 household cells
        const householdCells = document.querySelectorAll('.household-cell');
        elements.householdCells = householdCells.length;
        console.log(`Found ${householdCells.length} household cells`);
        
        return elements;
    },
    
    /**
     * 檢查事件監聽器
     */
    checkEventListeners: function() {
        try {
            // 檢查是否有點擊事件監聽器
            const householdCells = document.querySelectorAll('.household-cell');
            const buttons = document.querySelectorAll('button');
            
            console.log(`Checking event listeners on ${householdCells.length} household cells and ${buttons.length} buttons`);
            
            return householdCells.length > 0 || buttons.length > 0;
        } catch (error) {
            console.error('Event listener check failed:', error);
            return false;
        }
    },
    
    /**
     * 測試 API 連接
     */
    testAPI: async function() {
        try {
            const response = await fetch('/api/system/status');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            console.log('API Test Response:', data);
            return data.success === true;
        } catch (error) {
            console.error('API test failed:', error);
            return false;
        }
    },
    
    /**
     * 顯示診斷總結
     */
    showDiagnosticSummary: function(results) {
        console.log('=== Diagnostic Summary ===');
        
        const issues = [];
        
        if (!results.javascript) issues.push('JavaScript 環境異常');
        if (!results.libraries.all) issues.push('缺少必要的庫文件');
        if (!results.socketIO) issues.push('Socket.IO 連接失敗');
        if (!results.mainApp) issues.push('主應用程式初始化失敗');
        if (!results.excelInterface) issues.push('Excel 界面初始化失敗');
        if (!results.domElements.all) issues.push('缺少關鍵 DOM 元素');
        if (!results.eventListeners) issues.push('事件監聽器設置失敗');
        if (!results.api) issues.push('API 連接失敗');
        
        if (issues.length === 0) {
            console.log('✅ 所有組件檢查通過');
            this.showNotification('診斷完成：所有組件正常', 'success');
        } else {
            console.log('❌ 發現以下問題：');
            issues.forEach(issue => console.log(`  - ${issue}`));
            this.showNotification(`診斷完成：發現 ${issues.length} 個問題`, 'warning');
        }
        
        console.log('=== Diagnostic Complete ===');
        
        return issues;
    },
    
    /**
     * 顯示通知
     */
    showNotification: function(message, type) {
        if (window.powerMeterApp && window.powerMeterApp.showNotification) {
            window.powerMeterApp.showNotification(message, type);
        } else {
            // 後備通知方法
            console.log(`Notification (${type}): ${message}`);
            
            // 嘗試使用 Bootstrap Toast
            try {
                const toast = document.getElementById('notificationToast');
                if (toast) {
                    const toastBody = toast.querySelector('.toast-body');
                    if (toastBody) {
                        toastBody.textContent = message;
                        const bsToast = new bootstrap.Toast(toast);
                        bsToast.show();
                    }
                }
            } catch (error) {
                console.error('Toast notification failed:', error);
            }
            
            // 簡單的 alert 作為最後的後備
            if (type === 'error') {
                alert(`錯誤: ${message}`);
            }
        }
    },
    
    /**
     * 快速診斷 - 只檢查基本功能
     */
    quickDiagnostic: function() {
        console.log('=== Quick Diagnostic ===');
        
        const checks = [
            { name: 'JavaScript', test: () => this.checkJavaScript() },
            { name: 'Socket.IO', test: () => typeof io !== 'undefined' },
            { name: 'Main App', test: () => !!window.powerMeterApp },
            { name: 'Excel Interface', test: () => !!window.excelInterface },
            { name: 'DOM Ready', test: () => document.readyState === 'complete' }
        ];
        
        checks.forEach(check => {
            try {
                const result = check.test();
                console.log(`${check.name}: ${result ? '✅' : '❌'}`);
            } catch (error) {
                console.log(`${check.name}: ❌ (${error.message})`);
            }
        });
        
        console.log('=== Quick Diagnostic Complete ===');
    }
};

// 自動診斷（頁面載入後執行）
document.addEventListener('DOMContentLoaded', function() {
    // 延遲執行以確保所有組件都已載入
    setTimeout(() => {
        console.log('🔧 執行自動診斷...');
        window.diagnosticTool.quickDiagnostic();
    }, 3000);
});

// 全域快捷鍵：Ctrl+Shift+D 執行完整診斷
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.shiftKey && e.key === 'D') {
        e.preventDefault();
        window.diagnosticTool.runFullDiagnostic();
    }
});

// 暴露給全域使用
window.runDiagnostic = () => {
    console.log('🔧 Running diagnostic...');
    return window.diagnosticTool.runFullDiagnostic();
};
window.quickDiagnostic = () => {
    console.log('⚡ Running quick diagnostic...');
    return window.diagnosticTool.quickDiagnostic();
};

// 測試診斷工具是否正常載入
console.log('✅ Diagnostic tool loaded successfully');