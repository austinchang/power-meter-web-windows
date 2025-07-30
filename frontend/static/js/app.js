/**
 * Power Meter GUI Professional - Web Edition
 * Global Application JavaScript
 */

class PowerMeterApp {
    constructor() {
        this.socket = null;
        this.theme = 'light';
        this.isConnected = false;
        this.updateInterval = null;
        this.updateIntervalSeconds = 30; // 預設更新間隔
        this.meterData = new Map();
        
        this.init();
    }
    
    init() {
        console.log('Initializing Power Meter Web Edition...');
        
        try {
            this.initSocketIO();
            console.log('Socket.IO initialized');
            
            this.initThemeSystem();
            console.log('Theme system initialized');
            
            this.initEventListeners();
            console.log('Event listeners initialized');
            
            // 延遲啟動自動更新，讓頁面先完全載入
            setTimeout(() => {
                this.loadUpdateInterval().then(() => {
                    this.startAutoUpdate();
                    console.log('Auto update started with interval:', this.updateIntervalSeconds);
                });
            }, 1000);
            
            console.log('Power Meter Web Edition initialized successfully');
        } catch (error) {
            console.error('Initialization error:', error);
            this.showNotification('應用程式初始化失敗', 'error');
        }
    }
    
    /**
     * Initialize Socket.IO connection with improved error handling
     */
    initSocketIO() {
        try {
            console.log('Initializing Socket.IO connection...');
            
            this.socket = io({
                transports: ['polling', 'websocket'],
                timeout: 20000,
                reconnection: true,
                reconnectionAttempts: 5,
                reconnectionDelay: 1000,
                reconnectionDelayMax: 5000,
                maxReconnectionAttempts: 5,
                randomizationFactor: 0.5
            });
            
            this.socket.on('connect', () => {
                console.log('Connected to server');
                this.isConnected = true;
                this.updateConnectionStatus(true);
                this.showNotification('已連接到服務器', 'success');
            });
            
            this.socket.on('disconnect', (reason) => {
                console.log('Disconnected from server:', reason);
                this.isConnected = false;
                this.updateConnectionStatus(false);
                this.showNotification('與服務器連接中斷: ' + reason, 'error');
            });
            
            this.socket.on('connect_error', (error) => {
                console.error('Socket connection error:', error);
                this.isConnected = false;
                this.updateConnectionStatus(false);
                this.showNotification('連接服務器失敗: ' + error.message, 'error');
            });
            
            this.socket.on('reconnect', (attemptNumber) => {
                console.log('Reconnected after', attemptNumber, 'attempts');
                this.isConnected = true;
                this.updateConnectionStatus(true);
                this.showNotification('重新連接成功', 'success');
            });
            
            this.socket.on('reconnect_error', (error) => {
                console.error('Reconnection failed:', error);
                this.showNotification('重新連接失敗', 'error');
            });
            
            this.socket.on('reconnect_failed', () => {
                console.error('Failed to reconnect after max attempts');
                this.showNotification('連接失敗，已超過最大重試次數', 'error');
            });
            
            this.socket.on('status', (data) => {
                console.log('Status update:', data);
            });
            
            this.socket.on('meter_data', (data) => {
                this.handleMeterDataUpdate(data);
            });
            
            this.socket.on('meter_data_response', (data) => {
                console.log('Received meter data response:', data);
                if (data.success && data.data) {
                    data.data.forEach(meterData => {
                        this.handleMeterDataUpdate(meterData);
                    });
                }
            });
            
            this.socket.on('config_updated', (data) => {
                this.showNotification(data.message, 'success');
            });
            
            // 監聽供電時段變更廣播
            this.socket.on('power_schedule_changed', (data) => {
                console.log('Power schedule changed:', data);
                this.showNotification(data.message, 'info');
                
                // 延遲一點時間讓後端處理完成，然後刷新數據
                setTimeout(() => {
                    this.refreshAllData();
                    console.log('Data refreshed due to power schedule change');
                }, 500);
            });
            
            this.socket.on('error', (error) => {
                console.error('Socket error:', error);
                this.showNotification('通訊錯誤: ' + error, 'error');
            });
            
            console.log('Socket.IO initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize Socket.IO:', error);
            this.showNotification('無法初始化 Socket.IO 連接', 'error');
        }
    }
    
    /**
     * Initialize theme system
     */
    initThemeSystem() {
        // Load saved theme (without API call during initialization)
        const savedTheme = localStorage.getItem('power-meter-theme') || 'light';
        this.setTheme(savedTheme, false); // false = don't send API request during init
        
        // Theme selector event listeners
        document.querySelectorAll('[data-theme]').forEach(element => {
            element.addEventListener('click', (e) => {
                e.preventDefault();
                const theme = e.currentTarget.dataset.theme;
                this.setTheme(theme, true); // true = send API request when user changes theme
            });
        });
    }
    
    /**
     * Set application theme
     */
    setTheme(themeName, sendApiRequest = true) {
        this.theme = themeName;
        document.body.setAttribute('data-theme', themeName);
        localStorage.setItem('power-meter-theme', themeName);
        
        // Only send API request if explicitly requested (not during initialization)
        if (sendApiRequest) {
            this.apiRequest('/api/config/themes/' + themeName, 'PUT')
                .then(response => {
                    if (response.success) {
                        console.log('Theme updated to:', themeName);
                    }
                })
                .catch(error => {
                    console.error('Failed to update theme:', error);
                });
        } else {
            console.log('Theme set to:', themeName, '(initialization, no API call)');
        }
    }
    
    /**
     * Initialize global event listeners
     */
    initEventListeners() {
        // Handle page visibility change
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseAutoUpdate();
            } else {
                this.resumeAutoUpdate();
            }
        });
        
        // Handle window beforeunload
        window.addEventListener('beforeunload', () => {
            if (this.socket) {
                this.socket.disconnect();
            }
        });
        
        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl+R: Refresh data
            if (e.ctrlKey && e.key === 'r') {
                e.preventDefault();
                this.refreshAllData();
            }
            
            // Ctrl+T: Toggle theme
            if (e.ctrlKey && e.key === 't') {
                e.preventDefault();
                this.toggleTheme();
            }
        });
    }
    
    /**
     * Update connection status indicator
     */
    updateConnectionStatus(connected) {
        const statusIcon = document.getElementById('connectionStatus');
        const statusText = document.getElementById('connectionText');
        
        if (statusIcon && statusText) {
            if (connected) {
                statusIcon.className = 'fas fa-circle status-online me-1';
                statusText.textContent = '在線';
            } else {
                statusIcon.className = 'fas fa-circle status-offline me-1';
                statusText.textContent = '離線';
            }
        }
    }
    
    /**
     * Show notification toast
     */
    showNotification(message, type = 'info') {
        const toast = document.getElementById('notificationToast');
        const toastBody = toast.querySelector('.toast-body');
        const toastIcon = toast.querySelector('.fas');
        
        // Set message
        toastBody.textContent = message;
        
        // Set icon based on type
        let iconClass = 'fas fa-info-circle';
        if (type === 'success') iconClass = 'fas fa-check-circle';
        else if (type === 'error') iconClass = 'fas fa-exclamation-circle';
        else if (type === 'warning') iconClass = 'fas fa-exclamation-triangle';
        
        toastIcon.className = iconClass + ' me-2';
        
        // Show toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }
    
    /**
     * Show/hide loading modal
     */
    showLoading(show = true) {
        try {
            const modal = document.getElementById('loadingModal');
            if (!modal) {
                console.warn('Loading modal not found');
                return;
            }
            
            if (show) {
                modal.style.display = 'block';
                modal.classList.add('show');
                document.body.classList.add('modal-open');
                console.log('Loading modal shown');
            } else {
                modal.style.display = 'none';
                modal.classList.remove('show');
                document.body.classList.remove('modal-open');
                console.log('Loading modal hidden');
            }
        } catch (error) {
            console.error('Error handling loading modal:', error);
        }
    }
    
    /**
     * Start auto update interval
     */
    startAutoUpdate() {
        this.updateInterval = setInterval(() => {
            if (this.isConnected) {
                this.requestMeterData();
            }
        }, this.updateIntervalSeconds * 1000); // Use configurable update interval
    }
    
    /**
     * Pause auto update
     */
    pauseAutoUpdate() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
    
    /**
     * Resume auto update
     */
    resumeAutoUpdate() {
        if (!this.updateInterval) {
            this.startAutoUpdate();
        }
    }
    
    /**
     * Update refresh interval and restart auto update
     */
    updateRefreshInterval(seconds) {
        // Validate interval range
        const minInterval = 5;  // Reduced from 30 to 5
        const maxInterval = 180;
        
        if (seconds < minInterval || seconds > maxInterval) {
            console.warn(`Invalid update interval: ${seconds}s. Must be between ${minInterval}-${maxInterval}s`);
            return false;
        }
        
        this.updateIntervalSeconds = seconds;
        
        // Restart auto update with new interval
        this.pauseAutoUpdate();
        this.startAutoUpdate();
        
        console.log(`Update interval changed to ${seconds} seconds`);
        return true;
    }
    
    /**
     * Get current update interval
     */
    getUpdateInterval() {
        return this.updateIntervalSeconds;
    }
    
    /**
     * Load update interval from API
     */
    async loadUpdateInterval() {
        try {
            console.log('Loading update interval from API...');
            const response = await this.apiRequest('/api/system/config');
            
            if (response.success && response.data.update_interval) {
                const interval = response.data.update_interval.current;
                this.updateIntervalSeconds = interval;
                console.log(`Update interval loaded from API: ${interval} seconds`);
            } else {
                console.log('Using default update interval:', this.updateIntervalSeconds);
            }
        } catch (error) {
            console.error('Failed to load update interval:', error);
            console.log('Using default update interval:', this.updateIntervalSeconds);
        }
    }
    
    /**
     * Request meter data via Socket.IO
     */
    requestMeterData() {
        if (this.socket && this.isConnected) {
            this.socket.emit('request_meter_data', {
                request_id: Date.now(),
                all_meters: true
            });
        }
    }
    
    /**
     * Handle meter data update
     */
    handleMeterDataUpdate(data) {
        if (data.meter_id) {
            this.meterData.set(data.meter_id, data);
        }
        
        // Update last update time
        const lastUpdateElement = document.getElementById('lastUpdateTime');
        if (lastUpdateElement) {
            lastUpdateElement.textContent = new Date().toLocaleTimeString('zh-TW');
        }
        
        // Trigger custom event for pages to handle
        const event = new CustomEvent('meterDataUpdate', { detail: data });
        document.dispatchEvent(event);
    }
    
    /**
     * Refresh all meter data
     */
    refreshAllData() {
        console.log('Refreshing all data...');
        this.showLoading(true);
        
        // 設置超時，確保載入狀態不會永遠停留
        const timeout = setTimeout(() => {
            console.warn('Data refresh timeout, hiding loading');
            this.showLoading(false);
        }, 5000);
        
        this.apiRequest('/api/meters')
            .then(response => {
                clearTimeout(timeout);
                console.log('API response received:', response);
                
                if (response.success) {
                    response.data.forEach(meterData => {
                        this.meterData.set(meterData.id, meterData);
                    });
                    
                    // Trigger refresh event
                    const event = new CustomEvent('dataRefresh', { detail: response.data });
                    document.dispatchEvent(event);
                    
                    this.showNotification('數據刷新成功', 'success');
                    console.log('Data refresh completed successfully');
                } else {
                    this.showNotification('數據刷新失敗: ' + response.error, 'error');
                    console.error('API returned error:', response.error);
                }
            })
            .catch(error => {
                clearTimeout(timeout);
                console.error('Failed to refresh data:', error);
                this.showNotification('網絡錯誤，請檢查連接', 'error');
            })
            .finally(() => {
                this.showLoading(false);
                console.log('Loading state cleared');
            });
    }
    
    /**
     * Toggle between light and dark theme
     */
    toggleTheme() {
        const themes = ['light', 'dark', 'industrial'];
        const currentIndex = themes.indexOf(this.theme);
        const nextIndex = (currentIndex + 1) % themes.length;
        this.setTheme(themes[nextIndex], true); // Send API request when toggling
    }
    
    /**
     * API request helper
     */
    async apiRequest(url, method = 'GET', data = null) {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        try {
            const response = await fetch(url, options);
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }
    
    /**
     * Format number with thousand separators
     */
    formatNumber(number, decimals = 2) {
        return new Intl.NumberFormat('zh-TW', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(number);
    }
    
    /**
     * Format currency
     */
    formatCurrency(amount) {
        return new Intl.NumberFormat('zh-TW', {
            style: 'currency',
            currency: 'TWD',
            minimumFractionDigits: 0
        }).format(amount);
    }
    
    /**
     * Format date/time
     */
    formatDateTime(dateString) {
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('zh-TW', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        }).format(date);
    }
    
    /**
     * Get meter data by ID
     */
    getMeterData(meterId) {
        return this.meterData.get(meterId);
    }
    
    /**
     * Get all meter data
     */
    getAllMeterData() {
        return Array.from(this.meterData.values());
    }
    
    /**
     * Control meter power
     */
    async controlMeterPower(meterId, powerOn) {
        try {
            const response = await this.apiRequest(`/api/meters/${meterId}/control`, 'POST', {
                power_on: powerOn
            });
            
            if (response.success) {
                this.showNotification(response.message, 'success');
                
                // Update local data
                const meterData = this.meterData.get(meterId);
                if (meterData) {
                    meterData.power_on = powerOn;
                }
                
                // Trigger update event
                const event = new CustomEvent('meterPowerUpdate', { 
                    detail: { meterId, powerOn, data: response.data }
                });
                document.dispatchEvent(event);
                
                return true;
            } else {
                this.showNotification('控制失敗: ' + response.error, 'error');
                return false;
            }
        } catch (error) {
            console.error('Power control failed:', error);
            this.showNotification('控制失敗，請檢查網絡連接', 'error');
            return false;
        }
    }
    
    /**
     * Batch control meters
     */
    async batchControlMeters(meterIds, powerOn) {
        this.showLoading(true);
        
        try {
            const response = await this.apiRequest('/api/meters/batch/control', 'POST', {
                meter_ids: meterIds,
                power_on: powerOn
            });
            
            if (response.success) {
                this.showNotification(response.message, 'success');
                
                // Update local data
                meterIds.forEach(meterId => {
                    const meterData = this.meterData.get(meterId);
                    if (meterData) {
                        meterData.power_on = powerOn;
                    }
                });
                
                // Trigger batch update event
                const event = new CustomEvent('batchPowerUpdate', { 
                    detail: { meterIds, powerOn, results: response.data.results }
                });
                document.dispatchEvent(event);
                
                return true;
            } else {
                this.showNotification('批量控制失敗: ' + response.error, 'error');
                return false;
            }
        } catch (error) {
            console.error('Batch control failed:', error);
            this.showNotification('批量控制失敗，請檢查網絡連接', 'error');
            return false;
        } finally {
            this.showLoading(false);
        }
    }
}

// Global app instance
let app;

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    app = new PowerMeterApp();
    
    // Make app globally accessible
    window.powerMeterApp = app;
    
    console.log('Power Meter Web Edition ready');
});

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PowerMeterApp;
}