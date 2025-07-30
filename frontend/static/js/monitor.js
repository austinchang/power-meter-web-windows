/*!
 * 電表即時監控系統 JavaScript
 * 支援任意電表選擇監控與繼電器控制
 */

class MeterMonitor {
    constructor() {
        console.log('🏗️ MeterMonitor 構造函數開始執行');
        this.currentMeterId = null;
        this.isMonitoring = false;
        this.monitorInterval = null;
        this.startTime = null;
        this.totalRows = 0;
        this.maxRows = 100; // 最大顯示行數
        
        console.log('🔧 初始化 UI...');
        this.initializeUI();
        console.log('🔧 載入電表列表...');
        this.loadAvailableMeters();
        console.log('🔧 綁定事件...');
        this.bindEvents();
        console.log('✅ MeterMonitor 構造函數執行完成');
    }

    /**
     * 初始化 UI 狀態
     */
    initializeUI() {
        // 初始按鈕狀態
        this.updateButtonStates(false);
        
        // 設置預設監控間隔
        const intervalInput = document.getElementById('intervalInput');
        if (intervalInput) {
            intervalInput.value = 5;
        }
        
        // 清空數據表格
        this.clearDataTable();
        
        console.log('✓ Monitor UI 初始化完成');
    }

    /**
     * 載入可用電表列表
     */
    async loadAvailableMeters() {
        try {
            const response = await fetch('/api/monitor/meters');
            const result = await response.json();
            
            if (result.success) {
                console.log(`🔧 正在填充 ${result.data.length} 個電表選項...`);
                this.populateMeterSelect(result.data);
                // 更新按鈕狀態（初始時沒有選擇電表）
                this.updateButtonStates(false);
                console.log(`✓ 載入 ${result.total} 個電表`);
            } else {
                console.error(`❌ 載入電表列表失敗: ${result.error}`);
                this.showAlert('danger', `載入電表列表失敗: ${result.error}`);
            }
        } catch (error) {
            console.error('載入電表列表錯誤:', error);
            this.showAlert('danger', `載入電表列表錯誤: ${error.message}`);
        }
    }

    /**
     * 填充電表選擇下拉選單
     */
    populateMeterSelect(meters) {
        const select = document.getElementById('meterSelect');
        if (!select) {
            console.error('❌ 找不到電表選擇器元素');
            return;
        }

        console.log(`🔧 開始填充 ${meters.length} 個電表選項`);
        
        // 清空現有選項（保留預設選項）
        select.innerHTML = '<option value="">請選擇電表...</option>';

        // 添加電表選項
        meters.forEach(meter => {
            const option = document.createElement('option');
            option.value = meter.id;
            option.textContent = meter.display_name;
            select.appendChild(option);
        });
        
        console.log(`✅ 電表選項填充完成，共 ${select.options.length - 1} 個電表`);
    }

    /**
     * 綁定事件處理器
     */
    bindEvents() {
        // 電表選擇變更
        const meterSelect = document.getElementById('meterSelect');
        if (meterSelect) {
            meterSelect.addEventListener('change', (e) => {
                const selected = e.target.value;
                this.currentMeterId = selected ? parseInt(selected) : null;
                this.updateButtonStates(false);
                this.updateCurrentMeterDisplay();
            });
        }

        // 監控控制按鈕
        const startBtn = document.getElementById('startMonitor');
        const stopBtn = document.getElementById('stopMonitor');
        
        if (startBtn) {
            console.log('🔧 綁定開始監控按鈕事件');
            startBtn.addEventListener('click', () => {
                console.log('🔘 開始監控按鈕被點擊');
                this.startMonitoring();
            });
        } else {
            console.error('❌ 找不到開始監控按鈕');
        }
        
        if (stopBtn) {
            console.log('🔧 綁定停止監控按鈕事件');
            stopBtn.addEventListener('click', () => {
                console.log('🔘 停止監控按鈕被點擊');
                this.stopMonitoring();
            });
        } else {
            console.error('❌ 找不到停止監控按鈕');
        }

        // 繼電器控制按鈕
        const relayOnBtn = document.getElementById('relayOn');
        const relayOffBtn = document.getElementById('relayOff');
        
        if (relayOnBtn) {
            relayOnBtn.addEventListener('click', () => this.controlRelay('ON'));
        }
        
        if (relayOffBtn) {
            relayOffBtn.addEventListener('click', () => this.controlRelay('OFF'));
        }

        // 測試連接按鈕
        const testBtn = document.getElementById('testConnection');
        if (testBtn) {
            testBtn.addEventListener('click', () => this.testConnection());
        }

        // 清除數據按鈕
        const clearBtn = document.getElementById('clearData');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearData());
        }

        // 監控間隔輸入
        const intervalInput = document.getElementById('intervalInput');
        if (intervalInput) {
            intervalInput.addEventListener('change', (e) => {
                const value = parseInt(e.target.value);
                if (value < 1 || value > 60) {
                    e.target.value = Math.max(1, Math.min(60, value));
                    this.showAlert('warning', '監控間隔必須在 1-60 秒之間');
                }
            });
        }
    }

    /**
     * 開始監控
     */
    async startMonitoring() {
        if (!this.currentMeterId) {
            this.showAlert('warning', '請先選擇要監控的電表');
            return;
        }

        const intervalInput = document.getElementById('intervalInput');
        const interval = parseInt(intervalInput?.value || 5);

        try {
            this.showLoadingState('startMonitor', true);
            
            const response = await fetch(`/api/monitor/start/${this.currentMeterId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ interval })
            });

            const result = await response.json();

            if (result.success) {
                this.isMonitoring = true;
                this.startTime = new Date();
                this.updateButtonStates(true);
                this.updateMonitorStats();
                this.startDataPolling();
                
                this.showAlert('success', `開始監控電表 ${this.currentMeterId}，間隔 ${interval} 秒`);
                console.log(`✓ 開始監控電表 ${this.currentMeterId}`);
            } else {
                this.showAlert('danger', `啟動監控失敗: ${result.error}`);
            }
        } catch (error) {
            console.error('啟動監控錯誤:', error);
            this.showAlert('danger', `啟動監控錯誤: ${error.message}`);
        } finally {
            this.showLoadingState('startMonitor', false);
        }
    }

    /**
     * 停止監控
     */
    async stopMonitoring() {
        try {
            this.showLoadingState('stopMonitor', true);
            
            const response = await fetch('/api/monitor/stop', {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                this.isMonitoring = false;
                this.stopDataPolling();
                this.updateButtonStates(false);
                
                // 顯示監控總結
                if (result.total_time_minutes !== undefined) {
                    this.showAlert('info', 
                        `監控已停止。總時長: ${result.total_time_minutes} 分鐘，` +
                        `總電能變化: ${result.total_energy_change} kWh`
                    );
                } else {
                    this.showAlert('success', '監控已停止');
                }
                
                console.log('✓ 監控已停止');
            } else {
                this.showAlert('danger', `停止監控失敗: ${result.error}`);
            }
        } catch (error) {
            console.error('停止監控錯誤:', error);
            this.showAlert('danger', `停止監控錯誤: ${error.message}`);
        } finally {
            this.showLoadingState('stopMonitor', false);
        }
    }

    /**
     * 控制繼電器
     */
    async controlRelay(action) {
        if (!this.currentMeterId) {
            this.showAlert('warning', '請先選擇電表');
            return;
        }

        try {
            const btnId = action === 'ON' ? 'relayOn' : 'relayOff';
            this.showLoadingState(btnId, true);

            const response = await fetch('/api/monitor/relay/control', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ action })
            });

            const result = await response.json();

            if (result.success) {
                this.updateRelayStatus(result.current_status);
                this.showAlert('success', `繼電器已${action}`);
                console.log(`✓ 繼電器控制成功: ${action}`);
            } else {
                this.showAlert('danger', `繼電器控制失敗: ${result.error}`);
            }
        } catch (error) {
            console.error('繼電器控制錯誤:', error);
            this.showAlert('danger', `繼電器控制錯誤: ${error.message}`);
        } finally {
            const btnId = action === 'ON' ? 'relayOn' : 'relayOff';
            this.showLoadingState(btnId, false);
        }
    }

    /**
     * 測試電表連接
     */
    async testConnection() {
        if (!this.currentMeterId) {
            this.showAlert('warning', '請先選擇電表');
            return;
        }

        try {
            this.showLoadingState('testConnection', true);

            const response = await fetch(`/api/monitor/test/${this.currentMeterId}`, {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                const status = result.connected ? 'success' : 'danger';
                this.showAlert(status, result.message);
            } else {
                this.showAlert('danger', `連接測試失敗: ${result.error}`);
            }
        } catch (error) {
            console.error('測試連接錯誤:', error);
            this.showAlert('danger', `測試連接錯誤: ${error.message}`);
        } finally {
            this.showLoadingState('testConnection', false);
        }
    }

    /**
     * 開始數據輪詢
     */
    startDataPolling() {
        // 清除現有輪詢
        this.stopDataPolling();

        // 立即獲取一次數據
        this.fetchLatestData();

        // 設置定期輪詢
        this.monitorInterval = setInterval(() => {
            this.fetchLatestData();
        }, 1000); // 每秒檢查一次新數據
    }

    /**
     * 停止數據輪詢
     */
    stopDataPolling() {
        if (this.monitorInterval) {
            clearInterval(this.monitorInterval);
            this.monitorInterval = null;
        }
    }

    /**
     * 獲取最新監控數據
     */
    async fetchLatestData() {
        try {
            const response = await fetch('/api/monitor/data/latest');
            const result = await response.json();

            if (result.success && result.data) {
                this.addDataRow(result.data);
                this.updateRelayStatus(result.data.relay_status);
                this.updateMonitorStats(result.data);
            }
        } catch (error) {
            console.error('獲取監控數據錯誤:', error);
        }
    }

    /**
     * 添加數據行到表格
     */
    addDataRow(data) {
        const tbody = document.getElementById('monitorData');
        if (!tbody) return;

        // 如果是第一行數據，清除提示信息
        if (tbody.children.length === 1 && tbody.children[0].cells.length === 1) {
            tbody.innerHTML = '';
        }

        // 創建新行
        const row = document.createElement('tr');
        
        // 格式化數據
        const formatted = data.formatted_data || {};
        
        row.innerHTML = `
            <td class="data-cell">${formatted.time || data.timestamp || '--'}</td>
            <td class="data-cell">${formatted.voltage || '--'}</td>
            <td class="data-cell">${formatted.current || '--'}</td>
            <td class="data-cell">${formatted.power || '--'}</td>
            <td class="data-cell">${formatted.energy || '--'}</td>
            <td class="data-cell ${this.getChangeClass(data.change)}">${formatted.change || '--'}</td>
            <td class="data-cell ${this.getChangeClass(data.total_change)}">${formatted.total_change || '--'}</td>
            <td class="relay-status ${this.getRelayClass(data.relay_status)}">${formatted.relay || data.relay_status || '未知'}</td>
        `;

        // 插入到表格頂部
        tbody.insertBefore(row, tbody.firstChild);

        // 限制最大行數
        this.totalRows++;
        if (this.totalRows > this.maxRows) {
            const lastRow = tbody.lastElementChild;
            if (lastRow) {
                tbody.removeChild(lastRow);
            }
        }
    }

    /**
     * 獲取變化值的 CSS 類別
     */
    getChangeClass(change) {
        if (typeof change === 'number') {
            return change > 0 ? 'change-positive' : change < 0 ? 'change-negative' : '';
        }
        return '';
    }

    /**
     * 獲取繼電器狀態的 CSS 類別
     */
    getRelayClass(status) {
        switch (status) {
            case 'ON': return 'relay-on';
            case 'OFF': return 'relay-off';
            default: return 'relay-unknown';
        }
    }

    /**
     * 更新按鈕狀態
     */
    updateButtonStates(monitoring) {
        const elements = {
            startMonitor: document.getElementById('startMonitor'),
            stopMonitor: document.getElementById('stopMonitor'),
            relayOn: document.getElementById('relayOn'),
            relayOff: document.getElementById('relayOff'),
            testConnection: document.getElementById('testConnection'),
            meterSelect: document.getElementById('meterSelect')
        };

        const hasSelection = this.currentMeterId !== null;
        console.log(`🔧 更新按鈕狀態: hasSelection=${hasSelection}, monitoring=${monitoring}, currentMeterId=${this.currentMeterId}`);

        if (elements.startMonitor) {
            elements.startMonitor.disabled = !hasSelection || monitoring;
            console.log(`開始監控按鈕 disabled: ${elements.startMonitor.disabled}`);
        }
        
        if (elements.stopMonitor) {
            elements.stopMonitor.disabled = !monitoring;
        }
        
        if (elements.relayOn) {
            elements.relayOn.disabled = !hasSelection;
        }
        
        if (elements.relayOff) {
            elements.relayOff.disabled = !hasSelection;
        }
        
        if (elements.testConnection) {
            elements.testConnection.disabled = !hasSelection;
        }
        
        if (elements.meterSelect) {
            elements.meterSelect.disabled = monitoring;
        }
    }

    /**
     * 更新當前電表顯示
     */
    updateCurrentMeterDisplay() {
        const currentMeterElement = document.getElementById('currentMeter');
        if (currentMeterElement) {
            currentMeterElement.textContent = this.currentMeterId ? 
                `電表${this.currentMeterId.toString().padStart(2, '0')}` : '--';
        }
    }

    /**
     * 更新監控統計
     */
    updateMonitorStats(data = null) {
        // 監控狀態
        const statusElement = document.getElementById('monitorStatus');
        if (statusElement) {
            statusElement.textContent = this.isMonitoring ? '監控中' : '未監控';
            statusElement.className = this.isMonitoring ? 'stat-value text-success' : 'stat-value';
        }

        // 監控時長
        const durationElement = document.getElementById('monitorDuration');
        if (durationElement && this.startTime) {
            const duration = Math.floor((new Date() - this.startTime) / 1000);
            const minutes = Math.floor(duration / 60);
            const seconds = duration % 60;
            durationElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }

        // 總變化
        if (data && data.total_change !== undefined) {
            const totalChangeElement = document.getElementById('totalChange');
            if (totalChangeElement) {
                totalChangeElement.textContent = (data.total_change >= 0 ? '+' : '') + data.total_change.toFixed(3);
                totalChangeElement.className = `stat-value ${this.getChangeClass(data.total_change)}`;
            }
        }
    }

    /**
     * 更新繼電器狀態顯示
     */
    updateRelayStatus(status) {
        const relayStatusElement = document.getElementById('relayStatus');
        if (relayStatusElement) {
            relayStatusElement.textContent = status || '未知';
            relayStatusElement.className = `badge ${this.getRelayBadgeClass(status)} relay-status`;
        }
    }

    /**
     * 獲取繼電器狀態徽章類別
     */
    getRelayBadgeClass(status) {
        switch (status) {
            case 'ON': return 'bg-success';
            case 'OFF': return 'bg-secondary';
            default: return 'bg-warning';
        }
    }

    /**
     * 清除數據
     */
    clearData() {
        this.clearDataTable();
        this.totalRows = 0;
        
        // 重置統計
        const totalChangeElement = document.getElementById('totalChange');
        if (totalChangeElement) {
            totalChangeElement.textContent = '--';
            totalChangeElement.className = 'stat-value';
        }
        
        this.showAlert('info', '數據已清除');
    }

    /**
     * 清空數據表格
     */
    clearDataTable() {
        const tbody = document.getElementById('monitorData');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center text-muted py-4">
                        <i class="fas fa-info-circle me-2"></i>
                        請選擇電表並開始監控以查看即時數據
                    </td>
                </tr>
            `;
        }
    }

    /**
     * 顯示載入狀態
     */
    showLoadingState(buttonId, loading) {
        const button = document.getElementById(buttonId);
        if (!button) return;

        if (loading) {
            button.disabled = true;
            const originalText = button.innerHTML;
            button.setAttribute('data-original-text', originalText);
            button.innerHTML = '<span class="loading-spinner me-1"></span>處理中...';
        } else {
            button.disabled = false;
            const originalText = button.getAttribute('data-original-text');
            if (originalText) {
                button.innerHTML = originalText;
                button.removeAttribute('data-original-text');
            }
        }
    }

    /**
     * 顯示警告消息
     */
    showAlert(type, message) {
        const container = document.getElementById('alertContainer');
        if (!container) return;

        const alertId = `alert-${Date.now()}`;
        const alertHtml = `
            <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
                <i class="fas fa-${this.getAlertIcon(type)} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;

        container.insertAdjacentHTML('beforeend', alertHtml);

        // 自動移除警告（除了錯誤警告）
        if (type !== 'danger') {
            setTimeout(() => {
                const alert = document.getElementById(alertId);
                if (alert) {
                    alert.remove();
                }
            }, 5000);
        }
    }

    /**
     * 獲取警告圖標
     */
    getAlertIcon(type) {
        const icons = {
            'success': 'check-circle',
            'danger': 'exclamation-triangle',
            'warning': 'exclamation-circle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
}

// 頁面載入完成後初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 初始化電表監控系統');
    window.meterMonitor = new MeterMonitor();
    console.log('✅ MeterMonitor 實例已創建並分配給 window.meterMonitor');
});