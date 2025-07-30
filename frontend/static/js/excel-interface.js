/**
 * Excel Interface JavaScript
 * Excel 風格界面專用 JavaScript
 */

class ExcelInterface {
    constructor() {
        this.meterGroups = [
            { start: 1, end: 10, name: '分錶群組 1-10' },
            { start: 11, end: 20, name: '分錶群組 11-20' },
            { start: 21, end: 30, name: '分錶群組 21-30' },
            { start: 31, end: 40, name: '分錶群組 31-40' },
            { start: 41, end: 50, name: '分錶群組 41-50' }
        ];
        
        this.currentUnitPrice = 4;
        this.selectedMeterId = null;
        this.scheduleUpdateInterval = null;  // For dynamic interval updates
        this.currentSchedule = null;
        this.scheduleFormChanged = false;
        
        // 編輯狀態追蹤 - 防止數據更新覆蓋用戶編輯
        this.editingInputs = new Set(); // 追蹤正在編輯的輸入框
        this.editingTimeouts = new Map(); // 編輯保護超時
        
        this.init();
        
        // Make this instance globally accessible for function calls
        window.excelInterface = this;
    }
    
    init() {
        console.log('Initializing Excel Interface...');
        
        try {
            console.log('Generating meter tables...');
            this.generateMeterTables();
            
            console.log('Setting up event listeners...');
            this.initEventListeners();
            
            console.log('Setting up schedule form change detection...');
            this.setupScheduleFormMonitoring();
            
            console.log('Starting data updates...');
            this.startDataUpdate();
            
            // Load system config after PowerMeterApp is ready
            this.waitForPowerMeterApp().then(() => {
                console.log('Loading system config...');
                // Add a small delay to ensure DOM is fully ready
                setTimeout(() => {
                    this.loadSystemConfig();
                }, 500);
                
                // Also setup periodic display updates
                setTimeout(() => {
                    this.setupPeriodicDisplayUpdates();
                }, 2000);
            });
            
            console.log('Excel Interface initialized successfully');
            
            // Add a final safety check to ensure inputs are populated
            setTimeout(() => {
                this.finalInputCheck();
            }, 3000);
            
        } catch (error) {
            console.error('Excel Interface initialization error:', error);
        }
    }
    
    /**
     * Generate meter tables for all groups
     */
    generateMeterTables() {
        const container = document.getElementById('additionalMeterGroups');
        
        // Generate additional groups (2-5)
        for (let i = 1; i < this.meterGroups.length; i++) {
            const group = this.meterGroups[i];
            const tableHtml = this.generateGroupTable(group, i + 1);
            container.innerHTML += tableHtml;
        }
    }
    
    /**
     * Generate HTML for a meter group table
     */
    generateGroupTable(group, groupIndex) {
        const meterIds = [];
        const headerCells = [];
        const idCells = [];
        const householdCells = [];
        const powerStatusCells = [];
        const parkingCells = [];
        const usageCells = [];
        const amountCells = [];
        
        for (let id = group.start; id <= group.end; id++) {
            meterIds.push(id);
            headerCells.push(`<th>${id}</th>`);
            idCells.push(`<td class="meter-id-cell"><input type="text" class="meter-input" data-meter="${id}" data-field="meter_id" value="${id}"></td>`);
            
            const householdName = `A${id}`;
            householdCells.push(`<td class="household-cell"><input type="text" class="meter-input" data-meter="${id}" data-field="household" value="${householdName}"></td>`);
            
            powerStatusCells.push(`<td class="power-status-cell power-on" data-meter="${id}" onclick="togglePowerStatus(${id})"><i class="fas fa-power-off me-1"></i>ON</td>`);
            
            parkingCells.push(`<td class="parking-cell"><input type="text" class="meter-input" data-meter="${id}" data-field="parking" value="ABC-${id.toString().padStart(4, '0')}"></td>`);
            usageCells.push(`<td class="usage-cell" data-meter="${id}">0.0</td>`);
            amountCells.push(`<td class="amount-cell" data-meter="${id}">0</td>`);
        }
        
        return `
            <div class="group-header">${group.name}</div>
            <table class="meter-table" id="meterTable${groupIndex}">
                <thead>
                    <tr>
                        <th class="row-header">項目</th>
                        ${headerCells.join('')}
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td class="row-header">分錶ID</td>
                        ${idCells.join('')}
                    </tr>
                    <tr>
                        <td class="row-header">戶別</td>
                        ${householdCells.join('')}
                    </tr>
                    <tr>
                        <td class="row-header">供電狀態</td>
                        ${powerStatusCells.join('')}
                    </tr>
                    <tr>
                        <td class="row-header">車位號</td>
                        ${parkingCells.join('')}
                    </tr>
                    <tr>
                        <td class="row-header">用電量 (度)</td>
                        ${usageCells.join('')}
                    </tr>
                    <tr>
                        <td class="row-header">金額 (元)</td>
                        ${amountCells.join('')}
                    </tr>
                </tbody>
            </table>
        `;
    }
    
    /**
     * Initialize event listeners
     */
    initEventListeners() {
        // Remove old household cell click events (now handled by power status cells)
        // Household cells are now for editing only
        
        // Input field double-click events (detail modal)
        document.addEventListener('dblclick', (e) => {
            if (e.target.classList.contains('meter-input') && e.target.dataset.field === 'household') {
                const meterId = parseInt(e.target.dataset.meter);
                this.showMeterDetail(meterId);
            }
        });
        
        // Meter input focus events (開始編輯保護)
        document.addEventListener('focus', (e) => {
            if (e.target.classList.contains('meter-input')) {
                const inputKey = this.getInputKey(e.target);
                this.startEditingProtection(inputKey);
                console.log(`Started editing protection for: ${inputKey}`);
            }
        }, true);
        
        // Meter input blur events (結束編輯保護，延遲一段時間)
        document.addEventListener('blur', (e) => {
            if (e.target.classList.contains('meter-input')) {
                const inputKey = this.getInputKey(e.target);
                this.endEditingProtection(inputKey);
                console.log(`Ended editing protection for: ${inputKey}`);
            }
        }, true);
        
        // Meter input change events
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('meter-input')) {
                const meterId = parseInt(e.target.dataset.meter);
                const field = e.target.dataset.field;
                const value = e.target.value;
                
                if (field === 'parking') {
                    this.updateMeterParking(meterId, value);
                } else if (field === 'household') {
                    this.updateMeterField(meterId, 'household', value);
                } else if (field === 'meter_id') {
                    this.updateMeterField(meterId, 'meter_id', value);
                }
            }
        });
        
        // Global data update event
        document.addEventListener('meterDataUpdate', (e) => {
            this.handleMeterDataUpdate(e.detail);
        });
        
        document.addEventListener('dataRefresh', (e) => {
            this.handleDataRefresh(e.detail);
        });
        
        document.addEventListener('meterPowerUpdate', (e) => {
            this.handlePowerUpdate(e.detail);
        });
        
        document.addEventListener('batchPowerUpdate', (e) => {
            this.handleBatchPowerUpdate(e.detail);
        });
        
        // Listen for power schedule changes from other pages
        this.setupPowerScheduleListener();
    }
    
    /**
     * Wait for PowerMeterApp to be ready
     */
    waitForPowerMeterApp(maxAttempts = 50) {
        return new Promise((resolve) => {
            let attempts = 0;
            const checkInterval = setInterval(() => {
                attempts++;
                console.log(`Waiting for PowerMeterApp... attempt ${attempts}`);
                
                if (window.powerMeterApp && window.powerMeterApp.apiRequest) {
                    console.log('PowerMeterApp is ready');
                    clearInterval(checkInterval);
                    resolve();
                } else if (attempts >= maxAttempts) {
                    console.warn('PowerMeterApp not ready after maximum attempts');
                    clearInterval(checkInterval);
                    resolve(); // 仍然繼續，但可能功能受限
                }
            }, 100); // 檢查間隔100ms
        });
    }
    
    /**
     * Setup power schedule change listener
     */
    setupPowerScheduleListener() {
        // Wait for PowerMeterApp to be ready
        const checkAndSetup = () => {
            if (window.powerMeterApp && window.powerMeterApp.socket) {
                console.log('Excel Interface: Setting up power schedule listener');
                window.powerMeterApp.socket.on('power_schedule_changed', (data) => {
                    console.log('Excel Interface: Power schedule changed', data);
                    this.handlePowerScheduleChange(data);
                });
            } else {
                console.log('Excel Interface: PowerMeterApp not ready, retrying in 500ms');
                setTimeout(checkAndSetup, 500);
            }
        };
        
        checkAndSetup();
    }
    
    /**
     * 獲取輸入框的唯一鍵值
     */
    getInputKey(input) {
        const meterId = input.dataset.meter;
        const field = input.dataset.field;
        return `${meterId}-${field}`;
    }
    
    /**
     * 開始編輯保護
     */
    startEditingProtection(inputKey) {
        this.editingInputs.add(inputKey);
        
        // 清除之前的超時
        if (this.editingTimeouts.has(inputKey)) {
            clearTimeout(this.editingTimeouts.get(inputKey));
        }
    }
    
    /**
     * 結束編輯保護（延遲執行）
     */
    endEditingProtection(inputKey) {
        // 延遲3秒後移除保護，讓用戶有時間完成編輯
        const timeoutId = setTimeout(() => {
            this.editingInputs.delete(inputKey);
            this.editingTimeouts.delete(inputKey);
            console.log(`Removed editing protection for: ${inputKey}`);
        }, 3000);
        
        this.editingTimeouts.set(inputKey, timeoutId);
    }
    
    /**
     * 檢查輸入框是否受編輯保護
     */
    isInputProtected(meterId, field) {
        const inputKey = `${meterId}-${field}`;
        return this.editingInputs.has(inputKey);
    }
    
    /**
     * Update schedule controls with retry mechanism
     */
    updateScheduleControlsWithRetry(schedule, retryCount = 0) {
        const maxRetries = 10;
        const retryDelay = 300;
        
        console.log(`🔄 Attempting to update schedule controls (retry ${retryCount})`);
        console.log(`📋 Schedule data:`, schedule);
        
        // Try to find all required elements
        const openStartEl = document.getElementById('openStartTime');
        const openEndEl = document.getElementById('openEndTime');
        const closeStartEl = document.getElementById('closeStartTime');
        const closeEndEl = document.getElementById('closeEndTime');
        
        const elementsFound = {
            openStartEl: !!openStartEl,
            openEndEl: !!openEndEl,
            closeStartEl: !!closeStartEl,
            closeEndEl: !!closeEndEl
        };
        
        console.log('🔍 Schedule control elements found:', elementsFound);
        
        // Check if all elements are found
        const allElementsFound = Object.values(elementsFound).every(found => found);
        
        if (!allElementsFound && retryCount < maxRetries) {
            console.log(`⏳ Not all elements found, retrying in ${retryDelay}ms...`);
            setTimeout(() => {
                this.updateScheduleControlsWithRetry(schedule, retryCount + 1);
            }, retryDelay);
            return;
        }
        
        if (!allElementsFound) {
            console.error('❌ Could not find all schedule control elements after max retries');
            return;
        }
        
        // Update elements with proper format conversion
        const formatTime = (timeStr) => {
            // Convert "HH:MM:SS" to "HH:MM" for time input
            return timeStr.includes(':') ? timeStr.substring(0, 5) : timeStr;
        };
        
        try {
            // Check if user has made unsaved changes
            const hasUnsavedChanges = this.checkForUnsavedChanges(schedule);
            
            if (hasUnsavedChanges) {
                console.log('⚠️ 檢測到未保存的修改，顯示提醒訊息');
                this.showUnsavedChangesWarning();
                return; // Don't overwrite user's changes
            }
            
            if (openStartEl) {
                const formattedTime = this.format24HourTime(schedule.open_power.start);
                console.log(`🔍 Setting openStartTime: raw="${schedule.open_power.start}", formatted="${formattedTime}"`);
                openStartEl.value = formattedTime;
                console.log(`✅ Updated openStartTime: input.value="${openStartEl.value}"`);
                
                // Verify the value was set correctly
                if (openStartEl.value !== formattedTime) {
                    console.error(`❌ Value mismatch! Expected "${formattedTime}", got "${openStartEl.value}"`);
                }
                
                // Trigger change event to ensure the input is properly updated
                openStartEl.dispatchEvent(new Event('change', { bubbles: true }));
            }
            
            if (openEndEl) {
                const formattedTime = this.format24HourTime(schedule.open_power.end);
                console.log(`🔍 Setting openEndTime: raw="${schedule.open_power.end}", formatted="${formattedTime}"`);
                
                // Special handling for the problematic field
                if (schedule.open_power.end === '11:00:00' && formattedTime === '11:00') {
                    console.log('🎯 Special case: Setting 11:00 time');
                }
                
                openEndEl.value = formattedTime;
                console.log(`✅ Updated openEndTime: input.value="${openEndEl.value}"`);
                
                // Verify the value was set correctly
                if (openEndEl.value !== formattedTime) {
                    console.error(`❌ Value mismatch! Expected "${formattedTime}", got "${openEndEl.value}"`);
                    console.error('   This is the timezone conversion bug!');
                    
                    // Try alternative setting methods
                    console.log('🔧 Trying alternative setting method...');
                    openEndEl.setAttribute('value', formattedTime);
                    console.log(`   After setAttribute: ${openEndEl.value}`);
                }
                
                openEndEl.dispatchEvent(new Event('change', { bubbles: true }));
            }
            
            if (closeStartEl) {
                const formattedTime = this.format24HourTime(schedule.close_power.start);
                console.log(`🔍 Setting closeStartTime: raw="${schedule.close_power.start}", formatted="${formattedTime}"`);
                closeStartEl.value = formattedTime;
                console.log(`✅ Updated closeStartTime: input.value="${closeStartEl.value}"`);
                closeStartEl.dispatchEvent(new Event('change', { bubbles: true }));
            }
            
            if (closeEndEl) {
                const formattedTime = this.format24HourTime(schedule.close_power.end);
                console.log(`🔍 Setting closeEndTime: raw="${schedule.close_power.end}", formatted="${formattedTime}"`);
                closeEndEl.value = formattedTime;
                console.log(`✅ Updated closeEndTime: input.value="${closeEndEl.value}"`);
                closeEndEl.dispatchEvent(new Event('change', { bubbles: true }));
            }
            
            // Update schedule display range
            this.updateScheduleStatusDisplay(schedule);
            
            console.log('✅ Schedule controls updated successfully');
            
        } catch (error) {
            console.error('❌ Error updating schedule controls:', error);
        }
    }
    
    /**
     * Check if user has made unsaved changes to the schedule form
     */
    checkForUnsavedChanges(serverSchedule) {
        const openStartEl = document.getElementById('openStartTime');
        const openEndEl = document.getElementById('openEndTime');
        const closeStartEl = document.getElementById('closeStartTime');
        const closeEndEl = document.getElementById('closeEndTime');
        
        if (!openStartEl || !openEndEl || !closeStartEl || !closeEndEl) {
            return false; // Can't check if elements don't exist
        }
        
        const formatTime = (timeStr) => {
            return timeStr.includes(':') ? timeStr.substring(0, 5) : timeStr;
        };
        
        const currentFormValues = {
            openStart: openStartEl.value,
            openEnd: openEndEl.value,
            closeStart: closeStartEl.value,
            closeEnd: closeEndEl.value
        };
        
        const serverValues = {
            openStart: formatTime(serverSchedule.open_power.start),
            openEnd: formatTime(serverSchedule.open_power.end),
            closeStart: formatTime(serverSchedule.close_power.start),
            closeEnd: formatTime(serverSchedule.close_power.end)
        };
        
        // Check if any value is different
        const hasChanges = (
            currentFormValues.openStart !== serverValues.openStart ||
            currentFormValues.openEnd !== serverValues.openEnd ||
            currentFormValues.closeStart !== serverValues.closeStart ||
            currentFormValues.closeEnd !== serverValues.closeEnd
        );
        
        if (hasChanges) {
            console.log('🔍 檢測到表單變更:', {
                current: currentFormValues,
                server: serverValues
            });
        }
        
        return hasChanges;
    }
    
    /**
     * Show warning about unsaved changes
     */
    showUnsavedChangesWarning() {
        // Add visual indicator to the form
        const updateButton = document.querySelector('button[onclick="updatePowerSchedule()"]');
        if (updateButton) {
            updateButton.classList.add('btn-warning');
            updateButton.classList.remove('btn-primary');
            updateButton.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>有未保存的修改';
            
            // Add pulsing effect
            updateButton.style.animation = 'pulse 2s infinite';
        }
        
        // Show notification
        if (window.powerMeterApp && window.powerMeterApp.showNotification) {
            window.powerMeterApp.showNotification('檢測到未保存的時段設定修改，請點擊「更新時段」保存', 'warning');
        }
        
        // Add CSS for pulse animation if not exists
        if (!document.getElementById('unsavedChangesStyle')) {
            const style = document.createElement('style');
            style.id = 'unsavedChangesStyle';
            style.textContent = `
                @keyframes pulse {
                    0% { transform: scale(1); }
                    50% { transform: scale(1.05); }
                    100% { transform: scale(1); }
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    /**
     * Setup form change monitoring for schedule inputs
     */
    setupScheduleFormMonitoring() {
        // Delay setup to ensure DOM is ready
        setTimeout(() => {
            const inputIds = ['openStartTime', 'openEndTime', 'closeStartTime', 'closeEndTime'];
            
            inputIds.forEach(id => {
                const element = document.getElementById(id);
                if (element) {
                    // Monitor focus event
                    element.addEventListener('focus', (e) => {
                        console.log(`🎯 Focus on ${id}, current value: "${element.value}"`);
                    });
                    
                    element.addEventListener('input', (e) => {
                        console.log(`📝 Schedule input changed: ${id} = "${element.value}"`);
                        console.log(`   Input event details:`, {
                            type: e.type,
                            value: e.target.value,
                            inputType: e.inputType
                        });
                        this.markFormAsChanged();
                    });
                    
                    element.addEventListener('change', (e) => {
                        console.log(`📝 Schedule input confirmed: ${id} = "${element.value}"`);
                        console.log(`   Change event details:`, {
                            type: e.type,
                            value: e.target.value,
                            rawValue: element.value
                        });
                        
                        // Special check for the problematic field
                        if (id === 'openEndTime' && element.value === '23:00') {
                            console.error(`❌ PROBLEM DETECTED: openEndTime is 23:00!`);
                            console.error(`   This should be 11:00 if user entered 11:00`);
                            console.error(`   Checking element properties:`, {
                                value: element.value,
                                defaultValue: element.defaultValue,
                                min: element.min,
                                max: element.max,
                                step: element.step
                            });
                        }
                        
                        this.markFormAsChanged();
                    });
                    
                    // Monitor blur event
                    element.addEventListener('blur', (e) => {
                        console.log(`👁️ Blur from ${id}, final value: "${element.value}"`);
                    });
                    
                    console.log(`✅ Added enhanced listeners to ${id}`);
                } else {
                    console.log(`⚠️ Schedule input element not found: ${id}`);
                }
            });
        }, 1000);
    }
    
    /**
     * Mark form as having unsaved changes
     */
    markFormAsChanged() {
        const updateButton = document.querySelector('button[onclick="updatePowerSchedule()"]');
        if (updateButton && !updateButton.classList.contains('btn-warning')) {
            updateButton.classList.add('btn-warning');
            updateButton.classList.remove('btn-primary');
            updateButton.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>有未保存的修改';
            updateButton.style.animation = 'pulse 2s infinite';
            
            // Add CSS for pulse animation if not exists
            if (!document.getElementById('unsavedChangesStyle')) {
                const style = document.createElement('style');
                style.id = 'unsavedChangesStyle';
                style.textContent = `
                    @keyframes pulse {
                        0% { transform: scale(1); }
                        50% { transform: scale(1.05); }
                        100% { transform: scale(1); }
                    }
                `;
                document.head.appendChild(style);
            }
            
            console.log('⚠️ 標記表單為已修改狀態');
        }
    }
    
    /**
     * Setup periodic display updates to ensure schedule status is always current
     */
    setupPeriodicDisplayUpdates() {
        console.log('🔄 Setting up periodic schedule display updates');
        
        // Initial update after delay
        setTimeout(() => {
            if (this.currentSchedule) {
                console.log('📊 Initial schedule display update');
                this.updateScheduleStatusDisplay(this.currentSchedule);
                
                // Also force update the input controls
                console.log('🔄 Force updating input controls');
                this.forceUpdateInputControls();
            } else {
                console.log('⚠️ No current schedule for initial display update, loading from API');
                this.loadScheduleFromAPI();
            }
        }, 1000);
        
        // Update every 30 seconds to reflect time changes
        setInterval(() => {
            if (this.currentSchedule) {
                console.log('🕐 Periodic schedule display update');
                this.updateScheduleStatusDisplay(this.currentSchedule);
            }
        }, 30000);
    }
    
    /**
     * Force update input controls with current schedule
     */
    async forceUpdateInputControls() {
        try {
            if (!this.currentSchedule) {
                console.log('🔄 No current schedule, loading from API first');
                await this.loadScheduleFromAPI();
            }
            
            if (this.currentSchedule) {
                console.log('🔄 Force updating input controls with schedule:', this.currentSchedule);
                
                const openStartEl = document.getElementById('openStartTime');
                const openEndEl = document.getElementById('openEndTime');
                const closeStartEl = document.getElementById('closeStartTime');
                const closeEndEl = document.getElementById('closeEndTime');
                
                if (openStartEl && openEndEl && closeStartEl && closeEndEl) {
                    // Ensure 24-hour format (HH:MM)
                    openStartEl.value = this.format24HourTime(this.currentSchedule.open_power.start);
                    openEndEl.value = this.format24HourTime(this.currentSchedule.open_power.end);
                    closeStartEl.value = this.format24HourTime(this.currentSchedule.close_power.start);
                    closeEndEl.value = this.format24HourTime(this.currentSchedule.close_power.end);
                    
                    console.log('✅ Force updated all input controls:', {
                        openStart: openStartEl.value,
                        openEnd: openEndEl.value,
                        closeStart: closeStartEl.value,
                        closeEnd: closeEndEl.value
                    });
                } else {
                    console.error('❌ Some input elements not found:', {
                        openStartEl: !!openStartEl,
                        openEndEl: !!openEndEl,
                        closeStartEl: !!closeStartEl,
                        closeEndEl: !!closeEndEl
                    });
                }
            }
        } catch (error) {
            console.error('❌ Error in forceUpdateInputControls:', error);
        }
    }
    
    /**
     * Load schedule directly from API
     */
    async loadScheduleFromAPI() {
        try {
            console.log('🔄 Loading schedule directly from API');
            
            if (!window.powerMeterApp || !window.powerMeterApp.apiRequest) {
                console.error('❌ PowerMeterApp not available for API request');
                return;
            }
            
            const response = await window.powerMeterApp.apiRequest('/api/system/power-schedule');
            if (response.success && response.data) {
                console.log('✅ Loaded schedule from API:', response.data);
                this.currentSchedule = response.data;
                
                // Update both display and controls
                this.updateScheduleStatusDisplay(this.currentSchedule);
                this.updateScheduleControlsWithRetry(this.currentSchedule, 0);
            } else {
                console.error('❌ Failed to load schedule from API:', response);
            }
        } catch (error) {
            console.error('❌ Error loading schedule from API:', error);
        }
    }
    
    /**
     * Final check to ensure all inputs are populated
     */
    async finalInputCheck() {
        console.log('🔍 Final input check - ensuring all time inputs are populated');
        
        const openStartEl = document.getElementById('openStartTime');
        const openEndEl = document.getElementById('openEndTime');
        const closeStartEl = document.getElementById('closeStartTime');
        const closeEndEl = document.getElementById('closeEndTime');
        
        const allElementsExist = openStartEl && openEndEl && closeStartEl && closeEndEl;
        
        if (!allElementsExist) {
            console.warn('❌ Some input elements still not found in final check:', {
                openStartEl: !!openStartEl,
                openEndEl: !!openEndEl,
                closeStartEl: !!closeStartEl,
                closeEndEl: !!closeEndEl
            });
            return;
        }
        
        const allInputsEmpty = (
            !openStartEl.value && 
            !openEndEl.value && 
            !closeStartEl.value && 
            !closeEndEl.value
        );
        
        console.log('🔍 Current input values:', {
            openStart: openStartEl.value,
            openEnd: openEndEl.value,
            closeStart: closeStartEl.value,
            closeEnd: closeEndEl.value,
            allEmpty: allInputsEmpty
        });
        
        if (allInputsEmpty) {
            console.log('⚠️ All inputs are empty, forcing reload from API');
            await this.loadScheduleFromAPI();
            
            // Double check after loading
            setTimeout(() => {
                if (!openStartEl.value && !openEndEl.value && !closeStartEl.value && !closeEndEl.value) {
                    console.error('❌ Inputs still empty after API reload, trying force update');
                    this.forceUpdateInputControls();
                }
            }, 500);
        } else {
            console.log('✅ Inputs are populated, no action needed');
        }
    }
    
    /**
     * Load system configuration
     */
    async loadSystemConfig(retryCount = 0) {
        const maxRetries = 3;
        
        // Wait for PowerMeterApp to be ready
        if (!window.powerMeterApp || !window.powerMeterApp.apiRequest) {
            if (retryCount < maxRetries) {
                console.log(`PowerMeterApp not ready, retrying in 1 second... (${retryCount + 1}/${maxRetries})`);
                setTimeout(() => this.loadSystemConfig(retryCount + 1), 1000);
                return;
            } else {
                console.error('PowerMeterApp not available after maximum retries');
                return;
            }
        }
        
        try {
            console.log('Loading system config from API...');
            const response = await window.powerMeterApp.apiRequest('/api/system/config');
            if (response.success) {
                const config = response.data;
                console.log('System config loaded:', config);
                
                // Update unit price
                this.currentUnitPrice = config.defaults.unit_price;
                const unitPriceEl = document.getElementById('unitPrice');
                if (unitPriceEl) {
                    // 使用新的選單設定函數
                    if (typeof resetUnitPriceSelector === 'function') {
                        resetUnitPriceSelector();
                    } else {
                        // 後備方案：直接設定值（適用於舊版輸入框）
                        unitPriceEl.value = this.currentUnitPrice;
                    }
                }
                
                // Update power schedule
                if (config.power_schedule) {
                    const schedule = config.power_schedule;
                    console.log('✅ Updating power schedule display:', schedule);
                    
                    // Store schedule for periodic updates first
                    this.currentSchedule = schedule;
                    
                    // Use delayed update to ensure DOM is ready
                    setTimeout(() => {
                        this.updateScheduleControlsWithRetry(schedule, 0);
                    }, 500);
                    
                    // Update schedule status display with delay
                    console.log('Calling updateScheduleStatusDisplay with schedule:', schedule);
                    setTimeout(() => {
                        this.updateScheduleStatusDisplay(schedule);
                    }, 800);
                    
                    console.log('✅ Power schedule display updated successfully');
                } else {
                    console.warn('⚠️ No power_schedule found in config, attempting direct API call...');
                    
                    // Fallback: try to load schedule directly from API
                    setTimeout(async () => {
                        try {
                            const scheduleResponse = await window.powerMeterApp.apiRequest('/api/system/power-schedule');
                            if (scheduleResponse.success && scheduleResponse.data) {
                                console.log('✅ Loaded schedule from direct API call:', scheduleResponse.data);
                                this.currentSchedule = scheduleResponse.data;
                                this.updateScheduleControlsWithRetry(scheduleResponse.data, 0);
                                setTimeout(() => {
                                    this.updateScheduleStatusDisplay(scheduleResponse.data);
                                }, 1000);
                            }
                        } catch (error) {
                            console.error('❌ Failed to load schedule from direct API:', error);
                        }
                    }, 800);
                }
                
                // Update interval settings
                if (config.update_interval) {
                    const updateInterval = config.update_interval;
                    console.log('Updating interval settings:', updateInterval);
                    
                    const intervalSlider = document.getElementById('updateInterval');
                    const intervalValue = document.getElementById('intervalValue');
                    
                    if (intervalSlider) intervalSlider.value = updateInterval.current;
                    if (intervalValue) intervalValue.textContent = updateInterval.current;
                    
                    // Apply to PowerMeterApp
                    if (window.powerMeterApp) {
                        window.powerMeterApp.updateRefreshInterval(updateInterval.current);
                    }
                }
            } else {
                console.error('API returned error:', response);
                if (retryCount < maxRetries) {
                    console.log(`Retrying loadSystemConfig... (${retryCount + 1}/${maxRetries})`);
                    setTimeout(() => this.loadSystemConfig(retryCount + 1), 2000);
                }
            }
        } catch (error) {
            console.error('Failed to load system config:', error);
            if (retryCount < maxRetries) {
                console.log(`Retrying loadSystemConfig after error... (${retryCount + 1}/${maxRetries})`);
                setTimeout(() => this.loadSystemConfig(retryCount + 1), 2000);
            }
        }
    }
    
    /**
     * Start periodic data updates
     */
    startDataUpdate() {
        console.log('Starting Excel interface data updates...');
        
        // 立即載入初始數據（已包含系統配置和時段判斷）
        console.log('Loading initial meter data with schedule state...');
        this.loadInitialMeterData();
        
        // 也在短延遲後再次載入以確保數據正確
        setTimeout(() => {
            console.log('Secondary meter data load...');
            this.refreshMeterData();
        }, 500);
        
        // Update statistics every 10 seconds
        setInterval(() => {
            this.updateStatistics();
        }, 10000);
        
        // Update schedule display based on current interval setting
        this.scheduleUpdateInterval = setInterval(() => {
            this.updateScheduleDisplayStatus();
        }, 30000);  // Will be updated dynamically
        
        // Force reload configuration every 60 seconds to ensure consistency
        setInterval(() => {
            console.log('Force reloading system config for consistency...');
            this.loadSystemConfig();
        }, 60000);
        
        // Initialize update interval controls
        this.initializeUpdateIntervalControls();
    }
    
    /**
     * Toggle meter power status
     */
    async toggleMeterPower(cell) {
        const meterId = parseInt(cell.dataset.meter);
        const currentlyOn = cell.classList.contains('power-on');
        const newState = !currentlyOn;
        
        // Optimistic UI update
        this.updateCellPowerState(cell, newState);
        
        // API call
        const success = await window.powerMeterApp.controlMeterPower(meterId, newState);
        
        if (!success) {
            // Revert on failure
            this.updateCellPowerState(cell, currentlyOn);
        }
    }
    
    /**
     * Update cell power state
     */
    updateCellPowerState(cell, powerOn) {
        if (powerOn) {
            cell.classList.remove('power-off');
            cell.classList.add('power-on');
        } else {
            cell.classList.remove('power-on');
            cell.classList.add('power-off');
        }
        
        // 如果是戶別單元格，也要更新相關的用電量和金額顯示
        if (cell.classList.contains('household-cell')) {
            const meterId = cell.dataset.meter;
            if (meterId) {
                const usageCell = document.querySelector(`.usage-cell[data-meter="${meterId}"]`);
                const amountCell = document.querySelector(`.amount-cell[data-meter="${meterId}"]`);
                
                if (!powerOn) {
                    // 停止供電時清空用電量和金額
                    if (usageCell) usageCell.textContent = '0.0';
                    if (amountCell) amountCell.textContent = '0.00';
                    
                    // 獲取電表名稱 - 先嘗試從現有顯示中提取，否則從數據獲取
                    this.updateMeterDisplayState(parseInt(meterId), false);
                } else {
                    // 供電中時更新戶別顯示並重新載入數據
                    this.updateMeterDisplayState(parseInt(meterId), true);
                }
            }
        }
    }
    
    /**
     * Update meter display state with correct name
     */
    async updateMeterDisplayState(meterId, powerOn) {
        try {
            const householdCell = document.querySelector(`.household-cell[data-meter="${meterId}"]`);
            if (!householdCell) return;
            
            // 先從 API 獲取電表名稱
            const response = await fetch(`/api/meters/${meterId}`);
            const result = await response.json();
            
            let meterName = `RTU電表${meterId.toString().padStart(2, '0')}`;
            if (result.success && result.data && result.data.name) {
                meterName = result.data.name;
            }
            
            if (!powerOn) {
                // 斷電狀態：顯示紅色"停止供電"
                householdCell.innerHTML = `
                    <div class="text-danger fw-bold">${meterName}</div>
                    <small class="text-danger">停止供電</small>
                `;
            } else {
                // 供電狀態：顯示綠色"供電中"
                householdCell.innerHTML = `
                    <div class="text-success fw-bold">${meterName}</div>
                    <small class="text-success">供電中</small>
                `;
                
                // 重新載入電表數據
                this.refreshSingleMeterDisplay(meterId);
            }
        } catch (error) {
            console.error(`❌ Error updating meter ${meterId} display state:`, error);
            
            // 使用後備方案
            const householdCell = document.querySelector(`.household-cell[data-meter="${meterId}"]`);
            if (householdCell) {
                const meterName = `RTU電表${meterId.toString().padStart(2, '0')}`;
                if (!powerOn) {
                    householdCell.innerHTML = `
                        <div class="text-danger fw-bold">${meterName}</div>
                        <small class="text-danger">停止供電</small>
                    `;
                } else {
                    householdCell.innerHTML = `
                        <div class="text-success fw-bold">${meterName}</div>
                        <small class="text-success">供電中</small>
                    `;
                    this.refreshSingleMeterDisplay(meterId);
                }
            }
        }
    }
    
    /**
     * Refresh single meter display data
     */
    async refreshSingleMeterDisplay(meterId) {
        try {
            console.log(`🔄 Refreshing data for meter ${meterId}...`);
            
            const response = await fetch(`/api/meters/${meterId}`);
            const result = await response.json();
            
            if (result.success && result.data) {
                const meterData = result.data;
                console.log(`📊 Got meter ${meterId} data:`, meterData);
                
                // Update usage cell
                const usageCell = document.querySelector(`.usage-cell[data-meter="${meterId}"]`);
                if (usageCell && meterData.daily_energy !== undefined) {
                    usageCell.textContent = window.powerMeterApp.formatNumber(meterData.daily_energy, 1);
                }
                
                // Update amount cell
                const amountCell = document.querySelector(`.amount-cell[data-meter="${meterId}"]`);
                if (amountCell) {
                    const cost = meterData.cost_today !== undefined ? meterData.cost_today : 
                                 (meterData.daily_energy !== undefined ? meterData.daily_energy * this.currentUnitPrice : 0);
                    amountCell.textContent = window.powerMeterApp.formatNumber(cost, 2);
                }
                
                console.log(`✅ Refreshed meter ${meterId} display`);
            } else {
                console.error(`❌ Failed to get meter ${meterId} data:`, result);
            }
        } catch (error) {
            console.error(`❌ Error refreshing meter ${meterId} data:`, error);
        }
    }
    
    /**
     * Show meter detail modal
     */
    showMeterDetail(meterId) {
        this.selectedMeterId = meterId;
        
        // Get meter data
        const meterData = window.powerMeterApp.getMeterData(meterId) || {
            id: meterId,
            name: meterId <= 42 ? `A${meterId}` : `備${meterId - 42}`,
            parking: `ABC-${meterId.toString().padStart(4, '0')}`,
            power_on: true,
            voltage: 220.0,
            current: 15.0,
            power: 3300.0,
            energy: meterId * 50.5,
            daily_energy: meterId * 12.5,
            cost_today: (meterId * 12.5) * this.currentUnitPrice
        };
        
        // Update modal content
        document.getElementById('modalMeterName').textContent = meterData.name;
        document.getElementById('modalMeterId').textContent = meterId;
        document.getElementById('modalHouseholdName').value = meterData.name;
        document.getElementById('modalParkingNumber').value = meterData.parking;
        document.getElementById('modalPowerStatus').checked = meterData.power_on;
        document.getElementById('modalVoltage').textContent = window.powerMeterApp.formatNumber(meterData.voltage, 1);
        document.getElementById('modalCurrent').textContent = window.powerMeterApp.formatNumber(meterData.current, 2);
        document.getElementById('modalPower').textContent = window.powerMeterApp.formatNumber(meterData.power, 0);
        document.getElementById('modalEnergy').textContent = window.powerMeterApp.formatNumber(meterData.energy, 2);
        document.getElementById('modalCost').textContent = window.powerMeterApp.formatNumber(meterData.cost_today, 0);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('meterDetailModal'));
        modal.show();
    }
    
    /**
     * Save meter details from modal
     */
    saveMeterDetails() {
        if (!this.selectedMeterId) return;
        
        const householdName = document.getElementById('modalHouseholdName').value;
        const parkingNumber = document.getElementById('modalParkingNumber').value;
        const powerStatus = document.getElementById('modalPowerStatus').checked;
        
        // Update household input
        const householdInput = document.querySelector(`input[data-meter="${this.selectedMeterId}"][data-field="household"]`);
        if (householdInput) {
            householdInput.value = householdName;
        }
        
        // Update parking input
        const parkingInput = document.querySelector(`input[data-meter="${this.selectedMeterId}"][data-field="parking"]`);
        if (parkingInput) {
            parkingInput.value = parkingNumber;
        }
        
        // API call to save changes
        window.powerMeterApp.apiRequest(`/api/meters/${this.selectedMeterId}/update`, 'PUT', {
            name: householdName,
            parking: parkingNumber
        }).then(response => {
            if (response.success) {
                window.powerMeterApp.showNotification('電表資訊更新成功', 'success');
            } else {
                window.powerMeterApp.showNotification('更新失敗: ' + response.error, 'error');
            }
        });
        
        // Update power status if changed
        const currentMeterData = window.powerMeterApp.getMeterData(this.selectedMeterId);
        if (currentMeterData && currentMeterData.power_on !== powerStatus) {
            window.powerMeterApp.controlMeterPower(this.selectedMeterId, powerStatus);
        }
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('meterDetailModal'));
        modal.hide();
    }
    
    /**
     * Update meter parking number
     */
    updateMeterParking(meterId, parking) {
        this.updateMeterField(meterId, 'parking', parking);
    }
    
    /**
     * Update meter field (generic function)
     */
    updateMeterField(meterId, field, value) {
        const updateData = {};
        updateData[field] = value;
        
        window.powerMeterApp.apiRequest(`/api/meters/${meterId}/update`, 'PUT', updateData).then(response => {
            if (response.success) {
                console.log(`${field} updated for meter ${meterId}: ${value}`);
                window.powerMeterApp.showNotification(
                    `電表 ${meterId} ${field === 'parking' ? '車位號' : field === 'household' ? '戶別' : '分錶ID'}更新成功`, 
                    'success'
                );
            } else {
                window.powerMeterApp.showNotification(
                    `更新失敗: ${response.error}`, 
                    'error'
                );
            }
        }).catch(error => {
            console.error(`Failed to update ${field}:`, error);
            window.powerMeterApp.showNotification(
                `更新${field === 'parking' ? '車位號' : field === 'household' ? '戶別' : '分錶ID'}失敗`, 
                'error'
            );
        });
    }
    
    /**
     * Handle meter data update
     */
    handleMeterDataUpdate(data) {
        if (!data.meter_id) return;
        
        const meterId = data.meter_id;
        
        // Update usage cell - 使用真實的每日用電量
        const usageCell = document.querySelector(`.usage-cell[data-meter="${meterId}"]`);
        if (usageCell) {
            const dailyEnergy = data.daily_energy !== undefined ? data.daily_energy : data.energy;
            usageCell.textContent = window.powerMeterApp.formatNumber(dailyEnergy, 1);
        }
        
        // Update amount cell - 使用真實的今日費用
        const amountCell = document.querySelector(`.amount-cell[data-meter="${meterId}"]`);
        if (amountCell) {
            const cost = data.cost_today !== undefined ? data.cost_today : 
                         (data.daily_energy !== undefined ? data.daily_energy * this.currentUnitPrice : data.energy * this.currentUnitPrice);
            amountCell.textContent = window.powerMeterApp.formatNumber(cost, 2);
        }
        
        // Update power status separately from household display
        const isPowered = data.power_on !== undefined ? data.power_on : 
                         (data.status === 'online' && data.power_status !== 'unpowered');
        
        // 更新供電狀態按鈕
        const powerStatusCells = document.querySelectorAll(`.power-status-cell[data-meter="${meterId}"]`);
        powerStatusCells.forEach(cell => {
            if (isPowered) {
                cell.className = 'power-status-cell power-on';
                cell.innerHTML = '<i class="fas fa-power-off me-1"></i>ON';
            } else {
                cell.className = 'power-status-cell power-off';
                cell.innerHTML = '<i class="fas fa-power-off me-1"></i>OFF';
            }
            // 重新綁定點擊事件
            cell.onclick = () => window.togglePowerStatus(meterId);
        });
        
        // 更新戶別輸入框的值（使用編輯保護機制）
        if (!this.isInputProtected(meterId, 'household')) {
            const householdInputs = document.querySelectorAll(`input[data-meter="${meterId}"][data-field="household"]`);
            householdInputs.forEach(input => {
                // 雙重檢查：既檢查保護狀態，也檢查焦點狀態
                if (document.activeElement === input) {
                    console.log(`Skipping update for meter ${meterId} household - user has focus`);
                    return;
                }
                
                // 只有在值確實不同且不為空時才更新
                if (data.name && data.name.trim() !== '' && input.value !== data.name) {
                    console.log(`Updating household for meter ${meterId}: ${input.value} -> ${data.name}`);
                    input.value = data.name;
                }
            });
        } else {
            console.log(`Skipping household update for meter ${meterId} - protected by editing state`);
        }
        
        // 更新車位號輸入框的值（使用編輯保護機制）
        if (!this.isInputProtected(meterId, 'parking')) {
            const parkingInputs = document.querySelectorAll(`input[data-meter="${meterId}"][data-field="parking"]`);
            parkingInputs.forEach(input => {
                // 雙重檢查：既檢查保護狀態，也檢查焦點狀態
                if (document.activeElement === input) {
                    console.log(`Skipping update for meter ${meterId} parking - user has focus`);
                    return;
                }
                
                // 只有在值確實不同且從API返回了新值時才更新
                if (data.parking && data.parking.trim() !== '' && input.value !== data.parking) {
                    console.log(`Updating parking for meter ${meterId}: ${input.value} -> ${data.parking}`);
                    input.value = data.parking;
                }
            });
        } else {
            console.log(`Skipping parking update for meter ${meterId} - protected by editing state`);
        }
        
        // 更新分錶ID輸入框的值（使用編輯保護機制）
        if (!this.isInputProtected(meterId, 'meter_id')) {
            const meterIdInputs = document.querySelectorAll(`input[data-meter="${meterId}"][data-field="meter_id"]`);
            meterIdInputs.forEach(input => {
                // 雙重檢查：既檢查保護狀態，也檢查焦點狀態
                if (document.activeElement === input) {
                    console.log(`Skipping update for meter ${meterId} meter_id - user has focus`);
                    return;
                }
                
                // 分錶ID一般不會從服務器更新，但保持一致性
                if (data.meter_id && input.value !== data.meter_id.toString()) {
                    console.log(`Updating meter_id for meter ${meterId}: ${input.value} -> ${data.meter_id}`);
                    input.value = data.meter_id.toString();
                }
            });
        } else {
            console.log(`Skipping meter_id update for meter ${meterId} - protected by editing state`);
        }
        
        // 更新狀態指示器
        const statusIndicators = document.querySelectorAll(`.status-indicator[data-meter="${meterId}"]`);
        statusIndicators.forEach(indicator => {
            const isOnline = data.status === 'online' && data.power_on;
            indicator.className = `status-indicator ${isOnline ? 'status-online' : 'status-offline'}`;
        });
    }
    
    /**
     * Handle data refresh
     */
    handleDataRefresh(allMeterData) {
        allMeterData.forEach(meterData => {
            this.handleMeterDataUpdate(meterData);
        });
        
        this.updateStatistics();
    }
    
    /**
     * Handle power update
     */
    handlePowerUpdate(data) {
        const { meterId, powerOn } = data;
        // 使用新的供電狀態更新函數
        if (window.updatePowerStatusUI) {
            window.updatePowerStatusUI(meterId, powerOn);
        }
    }
    
    /**
     * Handle batch power update
     */
    handleBatchPowerUpdate(data) {
        const { meterIds, powerOn } = data;
        
        // 使用新的供電狀態更新函數
        meterIds.forEach(meterId => {
            if (window.updatePowerStatusUI) {
                window.updatePowerStatusUI(meterId, powerOn);
            }
        });
    }
    
    /**
     * Handle power schedule change broadcast
     */
    handlePowerScheduleChange(data) {
        console.log('Excel Interface: Handling power schedule change', data);
        
        // Update time display elements if they exist
        if (data.schedule) {
            const schedule = data.schedule;
            
            // Store schedule for periodic updates first
            this.currentSchedule = schedule;
            
            // Update schedule display elements with retry mechanism
            console.log('Broadcast: Updating schedule controls via retry mechanism');
            this.updateScheduleControlsWithRetry(schedule, 0);
            
            // Update schedule status display
            this.updateScheduleStatusDisplay(schedule);
        }
        
        // Show notification
        if (window.powerMeterApp && window.powerMeterApp.showNotification) {
            window.powerMeterApp.showNotification(data.message || '供電時段已更新', 'info');
        }
        
        // Optimized refresh - reduce delays for faster updates
        setTimeout(() => {
            console.log('Excel Interface: Force refreshing all data due to schedule change');
            
            // Method 1: Refresh via API
            if (window.powerMeterApp && window.powerMeterApp.refreshAllData) {
                window.powerMeterApp.refreshAllData();
            }
            
            // Method 2: Update each meter cell directly with shorter delay
            setTimeout(() => {
                console.log('Excel Interface: Updating all meter cells');
                // Force update all household cells to reflect new power states
                const allHouseholdCells = document.querySelectorAll('.household-cell');
                allHouseholdCells.forEach(cell => {
                    const meterId = parseInt(cell.dataset.meter);
                    const meterData = window.powerMeterApp.getMeterData(meterId);
                    if (meterData) {
                        this.handleMeterDataUpdate(meterData);
                    }
                });
                
                // Update statistics and schedule display
                this.updateStatistics();
                this.updateScheduleDisplay();
            }, 200); // Further reduced from 500ms to 200ms
            
        }, 100); // Further reduced from 300ms to 100ms
    }
    
    /**
     * Load initial meter data immediately
     */
    async loadInitialMeterData() {
        try {
            console.log('🔄 Fetching initial meter data and applying current schedule...');
            
            // 同時獲取電表數據和系統配置
            const [metersResponse, configResponse] = await Promise.all([
                fetch('/api/meters'),
                fetch('/api/system/config')
            ]);
            
            const metersData = await metersResponse.json();
            const configData = await configResponse.json();
            
            if (metersData.success && metersData.data) {
                console.log('Initial meter data loaded:', metersData.data.length, 'meters');
                
                // 檢查當前供電時段狀態
                let shouldPowerOn = false;
                if (configData.success && configData.data && configData.data.power_schedule) {
                    const schedule = configData.data.power_schedule;
                    shouldPowerOn = this.isInOpenPowerPeriod(schedule);
                    console.log(`⚡ Current time should be: ${shouldPowerOn ? 'ON' : 'OFF'} based on schedule`);
                    
                    // 儲存時段配置
                    this.currentSchedule = schedule;
                }
                
                // 根據時段狀態更新每個電表的顯示
                metersData.data.forEach(meterData => {
                    // 決定電表的供電狀態：基於時段判斷而不是API返回的狀態
                    const actualPowerState = shouldPowerOn;
                    
                    this.handleMeterDataUpdate({
                        meter_id: meterData.id,
                        name: meterData.name,
                        power_on: actualPowerState,
                        voltage: actualPowerState ? meterData.voltage : 0,
                        current: actualPowerState ? meterData.current : 0,
                        power: actualPowerState ? meterData.power : 0,
                        energy: meterData.energy,
                        daily_energy: actualPowerState ? (meterData.daily_energy || meterData.energy) : 0,
                        cost_today: actualPowerState ? (meterData.cost_today || 0) : 0,
                        status: meterData.status || 'online'
                    });
                });
                
                // 立即更新統計
                this.updateStatistics();
                
                console.log('✅ Initial meter data display updated with correct schedule state');
            } else {
                console.error('Failed to load initial meter data:', metersData);
            }
        } catch (error) {
            console.error('Error loading initial meter data:', error);
        }
    }
    
    /**
     * Refresh all meter data
     */
    refreshMeterData() {
        window.powerMeterApp.refreshAllData();
    }
    
    /**
     * Update statistics
     */
    updateStatistics() {
        const allMeterData = window.powerMeterApp.getAllMeterData();
        
        // Calculate statistics
        let totalPower = 0;
        let totalCost = 0;
        let onlineCount = 0;
        let poweredCount = 0;  // 新增：供電中的電表數量
        
        allMeterData.forEach(meter => {
            // 統計在線電表 - 檢查兩種格式
            const isOnline = meter.status === 'online' || meter.online === true;
            if (isOnline) {
                onlineCount++;
            }
            
            // 統計供電中的電表 - 檢查power_on狀態
            const isPowered = meter.power_on === true || 
                              (meter.is_powered === true && meter.power_status === 'powered');
            
            if (isPowered && isOnline) {
                poweredCount++;
                
                // 只統計供電中電表的功率和費用
                if (meter.power) {
                    totalPower += meter.power; // 保持kW單位
                }
                
                if (meter.cost_today !== undefined) {
                    totalCost += meter.cost_today;
                } else if (meter.daily_energy !== undefined) {
                    totalCost += meter.daily_energy * this.currentUnitPrice; // 使用動態單價
                } else if (meter.energy) {
                    totalCost += meter.energy * this.currentUnitPrice; // 使用動態單價
                }
            }
        });
        
        // Calculate offline meters
        const offlineCount = allMeterData.length - onlineCount;
        
        // Update UI
        const totalMetersElement = document.getElementById('totalMeters');
        const onlineMetersElement = document.getElementById('onlineMeters');
        const offlineMetersElement = document.getElementById('offlineMeters');
        const totalPowerElement = document.getElementById('totalPower');
        const totalCostElement = document.getElementById('totalCost');
        const currentUnitPriceElement = document.getElementById('currentUnitPrice');
        
        if (totalMetersElement) totalMetersElement.textContent = allMeterData.length.toString();
        if (onlineMetersElement) {
            // 顯示格式：在線數/供電數
            onlineMetersElement.textContent = `${onlineCount}/${poweredCount}`;
            onlineMetersElement.title = `在線: ${onlineCount}, 供電中: ${poweredCount}`;
        }
        if (offlineMetersElement) {
            offlineMetersElement.textContent = offlineCount.toString();
            offlineMetersElement.title = `離線電表數量: ${offlineCount}`;
        }
        if (totalPowerElement) totalPowerElement.textContent = window.powerMeterApp.formatNumber(totalPower, 1);
        if (totalCostElement) totalCostElement.textContent = window.powerMeterApp.formatNumber(totalCost, 0);
        if (currentUnitPriceElement) {
            currentUnitPriceElement.textContent = this.currentUnitPrice.toFixed(1);
            currentUnitPriceElement.title = `當前電費單價: ${this.currentUnitPrice} 元/kWh`;
        }
    }
    
    /**
     * Update schedule display status
     */
    updateScheduleDisplay() {
        // Reload system config to get latest schedule
        console.log('Updating schedule display...');
        this.loadSystemConfig();
    }
    
    /**
     * Update schedule status display card
     */
    updateScheduleStatusDisplay(schedule, retryCount = 0) {
        console.log('updateScheduleStatusDisplay called with:', schedule, 'retry:', retryCount);
        
        const statusCard = document.querySelector('.schedule-status-card');
        const statusElement = document.getElementById('scheduleStatus');
        const timeRangeElement = document.getElementById('scheduleTimeRange');
        
        console.log('Status display elements found:', {
            statusCard: !!statusCard,
            statusElement: !!statusElement,
            timeRangeElement: !!timeRangeElement,
            schedule: !!schedule
        });
        
        // Retry if elements are not found
        if ((!statusElement || !timeRangeElement) && retryCount < 5) {
            console.log(`⏳ Status display elements not found, retrying in 500ms... (${retryCount + 1}/5)`);
            setTimeout(() => {
                this.updateScheduleStatusDisplay(schedule, retryCount + 1);
            }, 500);
            return;
        }
        
        if (!statusElement || !timeRangeElement || !schedule) {
            console.error('❌ Missing elements or schedule for status display after max retries:', {
                statusElement: !!statusElement,
                timeRangeElement: !!timeRangeElement,
                schedule: !!schedule
            });
            return;
        }
        
        const now = new Date();
        const currentTime = now.getHours() * 60 + now.getMinutes(); // minutes since midnight
        
        // Parse schedule times
        const openStart = this.parseTimeToMinutes(schedule.open_power.start);
        const openEnd = this.parseTimeToMinutes(schedule.open_power.end);
        
        console.log('Time analysis:', {
            currentTime: currentTime,
            currentTimeHM: `${now.getHours()}:${now.getMinutes().toString().padStart(2, '0')}`,
            openStart: openStart,
            openEnd: openEnd,
            openStartHM: schedule.open_power.start.substring(0, 5),
            openEndHM: schedule.open_power.end.substring(0, 5)
        });
        
        let isPowerOn = false;
        let timeRange = '';
        
        // Special case: if openEnd is 00:00 (midnight), treat it as 24:00 for comparison
        let effectiveOpenEnd = openEnd;
        if (openEnd === 0 && openStart > 0) {
            effectiveOpenEnd = 24 * 60; // 24:00 in minutes
        }
        
        // Handle normal time range (not crossing midnight)
        if (openStart < effectiveOpenEnd) {
            // Check if current time is within the open power period
            if (effectiveOpenEnd === 24 * 60) {
                // Special case: open until midnight (00:00)
                isPowerOn = currentTime >= openStart;
            } else {
                isPowerOn = currentTime >= openStart && currentTime < effectiveOpenEnd;
            }
            
            const endTimeDisplay = effectiveOpenEnd === 24 * 60 ? '00:00' : schedule.open_power.end.substring(0, 5);
            timeRange = `${schedule.open_power.start.substring(0, 5)} - ${endTimeDisplay}`;
            console.log('Normal time range - isPowerOn:', isPowerOn);
        } 
        // Handle time range crossing midnight (e.g., 22:00 - 06:00)
        else {
            isPowerOn = currentTime >= openStart || currentTime < openEnd;
            timeRange = `${schedule.open_power.start.substring(0, 5)} - ${schedule.open_power.end.substring(0, 5)} (跨日)`;
            console.log('Midnight crossing time range - isPowerOn:', isPowerOn);
        }
        
        // Update UI with enhanced error handling
        try {
            if (isPowerOn) {
                statusElement.innerHTML = '<i class="fas fa-bolt me-1"></i>供電中';
                timeRangeElement.textContent = `供電時段: ${timeRange}`;
                if (statusCard) statusCard.classList.remove('power-off');
            } else {
                statusElement.innerHTML = '<i class="fas fa-power-off me-1"></i>停止供電';
                timeRangeElement.textContent = `供電時段: ${timeRange}`;
                if (statusCard) statusCard.classList.add('power-off');
            }
            
            console.log(`✅ Schedule status updated: ${isPowerOn ? '供電中' : '停止供電'}, Range: ${timeRange}`);
            console.log('✅ DOM elements updated successfully:', {
                statusElement: statusElement.innerHTML,
                timeRangeElement: timeRangeElement.textContent
            });
        } catch (error) {
            console.error('❌ Error updating UI elements:', error);
            
            // Force retry with direct element selection
            setTimeout(() => {
                try {
                    const forceStatusElement = document.getElementById('scheduleStatus');
                    const forceTimeRangeElement = document.getElementById('scheduleTimeRange');
                    
                    if (forceStatusElement && forceTimeRangeElement) {
                        console.log('🔄 Force retry: updating DOM elements directly');
                        if (isPowerOn) {
                            forceStatusElement.innerHTML = '<i class="fas fa-bolt me-1"></i>供電中';
                            forceTimeRangeElement.textContent = `供電時段: ${timeRange}`;
                        } else {
                            forceStatusElement.innerHTML = '<i class="fas fa-power-off me-1"></i>停止供電';
                            forceTimeRangeElement.textContent = `供電時段: ${timeRange}`;
                        }
                        console.log('✅ Force retry successful');
                    }
                } catch (retryError) {
                    console.error('❌ Force retry also failed:', retryError);
                }
            }, 200);
        }
    }
    
    /**
     * Parse time string to minutes since midnight
     */
    parseTimeToMinutes(timeString) {
        const [hours, minutes] = timeString.split(':').map(Number);
        return hours * 60 + minutes;
    }
    
    /**
     * Update schedule display status periodically (for time-based changes)
     */
    updateScheduleDisplayStatus() {
        // Get current schedule from stored configuration
        if (this.currentSchedule) {
            this.updateScheduleStatusDisplay(this.currentSchedule);
        }
    }
    
    /**
     * Format time string to 24-hour format (HH:MM)
     */
    format24HourTime(timeStr) {
        if (!timeStr) return '';
        
        try {
            // Extract HH:MM from HH:MM:SS format
            const parts = timeStr.split(':');
            if (parts.length >= 2) {
                const hours = parts[0].padStart(2, '0');
                const minutes = parts[1].padStart(2, '0');
                return `${hours}:${minutes}`;
            }
            return timeStr;
        } catch (error) {
            console.error('Error formatting time:', error);
            return timeStr;
        }
    }

    /**
     * Determine if current time is in open power period
     */
    isInOpenPowerPeriod(schedule) {
        if (!schedule || !schedule.open_power) {
            return false;
        }

        const now = new Date();
        const currentTime = now.getHours() * 60 + now.getMinutes();
        
        const openStart = this.parseTimeToMinutes(schedule.open_power.start);
        const openEnd = this.parseTimeToMinutes(schedule.open_power.end);
        
        // Handle cases where period crosses midnight
        if (openStart <= openEnd) {
            // Normal case: 08:00 - 17:00
            return currentTime >= openStart && currentTime < openEnd;
        } else {
            // Cross midnight case: 22:00 - 06:00
            return currentTime >= openStart || currentTime < openEnd;
        }
    }

    /**
     * Parse time string to minutes since midnight
     */
    parseTimeToMinutes(timeStr) {
        if (!timeStr) return 0;
        
        const parts = timeStr.split(':');
        const hours = parseInt(parts[0] || 0);
        const minutes = parseInt(parts[1] || 0);
        
        return hours * 60 + minutes;
    }

    /**
     * Apply schedule to all meters immediately
     */
    applyScheduleToAllMeters(schedule) {
        console.log('🔄 Applying new schedule to all meters...');
        
        if (!schedule || !schedule.open_power) {
            console.error('❌ Invalid schedule provided');
            return;
        }
        
        const shouldPowerOn = this.isInOpenPowerPeriod(schedule);
        console.log(`⚡ Current time should be: ${shouldPowerOn ? 'ON' : 'OFF'}`);
        
        // Find all household cells (戶別單元格)
        const householdCells = document.querySelectorAll('.household-cell[data-meter]');
        console.log(`📋 Found ${householdCells.length} household cells to update`);
        
        householdCells.forEach(cell => {
            const meterId = parseInt(cell.dataset.meter);
            if (meterId) {
                // Update visual state immediately
                this.updateCellPowerState(cell, shouldPowerOn);
                console.log(`🔄 Updated meter ${meterId} visual state to ${shouldPowerOn ? 'ON' : 'OFF'}`);
                
                // Send API request to update actual meter state
                if (window.powerMeterApp && window.powerMeterApp.controlMeterPower) {
                    window.powerMeterApp.controlMeterPower(meterId, shouldPowerOn)
                        .then(success => {
                            if (success) {
                                console.log(`✅ Meter ${meterId} API update successful`);
                            } else {
                                console.error(`❌ Meter ${meterId} API update failed`);
                                // Revert visual state on API failure
                                this.updateCellPowerState(cell, !shouldPowerOn);
                            }
                        })
                        .catch(error => {
                            console.error(`❌ Meter ${meterId} API error:`, error);
                            // Revert visual state on API error
                            this.updateCellPowerState(cell, !shouldPowerOn);
                        });
                }
            }
        });
        
        // Show notification about the mass update
        if (window.powerMeterApp && window.powerMeterApp.showNotification) {
            const action = shouldPowerOn ? '開啟' : '關閉';
            window.powerMeterApp.showNotification(
                `正在根據新時段設定${action}所有分錶...`, 
                'info'
            );
        }
        
        // 延遲強制刷新所有電表顯示，確保狀態一致
        setTimeout(() => {
            console.log('🔄 Force refreshing all meter displays for consistency...');
            this.forceRefreshAllMeterDisplays();
        }, 2000);
    }
    
    /**
     * Force refresh all meter displays to ensure consistency
     */
    async forceRefreshAllMeterDisplays() {
        try {
            console.log('🔄 Starting force refresh of all meter displays...');
            
            // 獲取所有電表數據
            const response = await fetch('/api/meters');
            const result = await response.json();
            
            if (result.success && result.data) {
                console.log(`📊 Got ${result.data.length} meters data for force refresh`);
                
                result.data.forEach(meterData => {
                    this.updateMeterData(meterData.meter_id, meterData);
                });
                
                // 也更新統計顯示
                this.updateStatistics();
                
                console.log('✅ Force refresh of all meter displays completed');
            } else {
                console.error('❌ Failed to get meters data for force refresh:', result);
            }
        } catch (error) {
            console.error('❌ Error in force refresh of meter displays:', error);
        }
    }

    /**
     * Update schedule display interval dynamically
     */
    updateScheduleDisplayInterval(newInterval) {
        console.log(`🔄 Updating schedule display interval to ${newInterval} seconds`);
        
        // Clear existing interval
        if (this.scheduleUpdateInterval) {
            clearInterval(this.scheduleUpdateInterval);
        }
        
        // Set new interval (convert to milliseconds)
        this.scheduleUpdateInterval = setInterval(() => {
            this.updateScheduleDisplayStatus();
        }, newInterval * 1000);
        
        console.log(`✅ Schedule display now updates every ${newInterval} seconds`);
    }

    /**
     * Initialize update interval controls with current value
     */
    initializeUpdateIntervalControls() {
        console.log('🔧 Initializing update interval controls...');
        
        // Load current interval from API
        if (window.powerMeterApp && window.powerMeterApp.apiRequest) {
            window.powerMeterApp.apiRequest('/api/system/config', 'GET')
                .then(response => {
                    if (response.success && response.data.update_interval) {
                        const currentInterval = response.data.update_interval.current;
                        console.log(`📊 Current interval from server: ${currentInterval}s`);
                        
                        // Update slider value
                        const slider = document.getElementById('updateInterval');
                        if (slider) {
                            slider.value = currentInterval;
                            console.log(`🎚️ Set slider value to: ${currentInterval}`);
                        }
                        
                        // Update displays
                        this.updateIntervalDisplays(currentInterval);
                    }
                })
                .catch(error => {
                    console.error('❌ Failed to load current interval:', error);
                    // Fallback to default
                    this.updateIntervalDisplays(30);
                });
        } else {
            console.warn('⚠️ PowerMeterApp not available, using default interval');
            this.updateIntervalDisplays(30);
        }
    }

    /**
     * Update all interval-related displays
     */
    updateIntervalDisplays(interval) {
        console.log(`🔄 Updating interval displays to: ${interval}s`);
        
        // Update slider display value
        const valueDisplay = document.getElementById('intervalValue');
        if (valueDisplay) {
            valueDisplay.textContent = interval;
            // Update color based on interval
            if (interval <= 10) {
                valueDisplay.className = 'text-danger fw-bold';
            } else if (interval <= 30) {
                valueDisplay.className = 'text-warning fw-bold';
            } else {
                valueDisplay.className = 'text-success fw-bold';
            }
        }
        
        // Update current interval display
        const currentIntervalDisplay = document.getElementById('currentInterval');
        if (currentIntervalDisplay) {
            currentIntervalDisplay.textContent = `${interval}秒`;
            // Update color based on interval
            if (interval <= 10) {
                currentIntervalDisplay.className = 'fw-bold text-danger';
            } else if (interval <= 30) {
                currentIntervalDisplay.className = 'fw-bold text-warning';
            } else {
                currentIntervalDisplay.className = 'fw-bold text-success';
            }
        }
        
        console.log(`✅ Interval displays updated to ${interval}s`);
    }
}

// Global functions for button handlers
window.updatePowerSchedule = function() {
    console.log('🚀 updatePowerSchedule function called');
    
    try {
        // Get form elements
        const openStartEl = document.getElementById('openStartTime');
        const openEndEl = document.getElementById('openEndTime');
        const closeStartEl = document.getElementById('closeStartTime');
        const closeEndEl = document.getElementById('closeEndTime');
        
        // Check if elements exist
        if (!openStartEl || !openEndEl || !closeStartEl || !closeEndEl) {
            console.error('❌ Some schedule input elements not found:', {
                openStartEl: !!openStartEl,
                openEndEl: !!openEndEl,
                closeStartEl: !!closeStartEl,
                closeEndEl: !!closeEndEl
            });
            window.powerMeterApp.showNotification('表單元素缺失，請重新載入頁面', 'error');
            return;
        }
        
        // Get values and validate
        const openStart = openStartEl.value;
        const openEnd = openEndEl.value;
        const closeStart = closeStartEl.value;
        const closeEnd = closeEndEl.value;
        
        console.log('📋 Form values:', { openStart, openEnd, closeStart, closeEnd });
        console.log('📋 Detailed form inspection:', {
            openStartEl_value: openStartEl.value,
            openStartEl_type: typeof openStartEl.value,
            openEndEl_value: openEndEl.value,
            openEndEl_type: typeof openEndEl.value,
            closeStartEl_value: closeStartEl.value,
            closeStartEl_type: typeof closeStartEl.value,
            closeEndEl_value: closeEndEl.value,
            closeEndEl_type: typeof closeEndEl.value
        });
        
        if (!openStart || !openEnd || !closeStart || !closeEnd) {
            console.error('❌ Some time values are empty');
            window.powerMeterApp.showNotification('請填寫完整的時間設定', 'error');
            return;
        }
        
        const schedule = {
            open_power: {
                start: openStart + ':00',
                end: openEnd + ':00'
            },
            close_power: {
                start: closeStart + ':00',
                end: closeEnd + ':00'
            }
        };
        
        console.log('📤 Sending schedule update:', schedule);
        console.log('🔍 Critical time verification:');
        console.log('  User set openEnd to:', openEnd);
        console.log('  Will send to server:', openEnd + ':00');
        console.log('  Expected in database: 11:00:00');
        console.log('  Current problematic value in DB: 23:00:00');
        
        // Add manual verification
        if (openEnd === '11:00') {
            console.log('✅ openEnd value is correct (11:00)');
        } else {
            console.log('❌ openEnd value is WRONG, expected 11:00, got:', openEnd);
        }
        
        // Check if powerMeterApp is available
        if (!window.powerMeterApp || !window.powerMeterApp.apiRequest) {
            console.error('❌ PowerMeterApp not available');
            alert('系統未初始化，請重新載入頁面');
            return;
        }
        
        // Show loading state
        if (window.powerMeterApp.showLoading) {
            window.powerMeterApp.showLoading(true);
        }
        
        window.powerMeterApp.apiRequest('/api/system/power-schedule', 'PUT', schedule)
            .then(response => {
                console.log('📥 Schedule update response:', response);
                
                if (response.success) {
                    window.powerMeterApp.showNotification('供電時段更新成功', 'success');
                    
                    // Reset button state after successful update
                    const updateButton = document.querySelector('button[onclick="updatePowerSchedule()"]');
                    if (updateButton) {
                        updateButton.classList.remove('btn-warning');
                        updateButton.classList.add('btn-primary');
                        updateButton.innerHTML = '<i class="fas fa-save me-1"></i>更新時段';
                        updateButton.style.animation = '';
                    }
                    
                    // Update the stored schedule with new values
                    if (window.excelInterface) {
                        window.excelInterface.currentSchedule = schedule;
                        
                        // Immediately update the display with multiple attempts
                        console.log('🔄 Force updating schedule display after save...');
                        window.excelInterface.updateScheduleStatusDisplay(schedule);
                        
                        // Immediately update all meter power states based on new schedule
                        console.log('⚡ Applying new schedule to all meters...');
                        window.excelInterface.applyScheduleToAllMeters(schedule);
                        
                        // Also try with delays to ensure DOM is ready
                        setTimeout(() => {
                            console.log('🔄 Second attempt to update schedule display...');
                            window.excelInterface.updateScheduleStatusDisplay(schedule);
                        }, 100);
                        
                        setTimeout(() => {
                            console.log('🔄 Third attempt to update schedule display...');
                            window.excelInterface.updateScheduleStatusDisplay(schedule);
                        }, 500);
                        
                        // Force reload schedule from API to ensure consistency
                        setTimeout(() => {
                            console.log('🔄 Force reloading schedule from API to verify consistency...');
                            window.excelInterface.loadScheduleFromAPI();
                        }, 1000);
                    }
                    
                    // Trigger data refresh to update meter displays
                    if (window.powerMeterApp.refreshAllData) {
                        setTimeout(() => {
                            window.powerMeterApp.refreshAllData();
                        }, 500);
                    }
                } else {
                    console.error('❌ Schedule update failed:', response.error);
                    window.powerMeterApp.showNotification('更新失敗: ' + (response.error || '未知錯誤'), 'error');
                }
            })
            .catch(error => {
                console.error('❌ Network error during schedule update:', error);
                window.powerMeterApp.showNotification('網絡錯誤，請檢查連接', 'error');
            })
            .finally(() => {
                // Hide loading state
                if (window.powerMeterApp.showLoading) {
                    window.powerMeterApp.showLoading(false);
                }
            });
            
    } catch (error) {
        console.error('❌ Unexpected error in updatePowerSchedule:', error);
        alert('更新時段時發生錯誤: ' + error.message);
    }
};

window.reloadScheduleInputs = function() {
    console.log('🔄 Manual reload of schedule inputs triggered');
    
    if (window.excelInterface) {
        // Show loading state
        const reloadBtn = document.querySelector('button[onclick="reloadScheduleInputs()"]');
        if (reloadBtn) {
            const originalContent = reloadBtn.innerHTML;
            reloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            reloadBtn.disabled = true;
            
            // Restore button after operation
            setTimeout(() => {
                reloadBtn.innerHTML = originalContent;
                reloadBtn.disabled = false;
            }, 2000);
        }
        
        // Force reload from API
        window.excelInterface.loadScheduleFromAPI();
        
        if (window.powerMeterApp && window.powerMeterApp.showNotification) {
            window.powerMeterApp.showNotification('正在重新載入時段設定...', 'info');
        }
    } else {
        console.error('❌ ExcelInterface not available');
        alert('系統未準備好，請稍後再試');
    }
};

window.updateBillingPeriod = function() {
    const unitPrice = parseFloat(getCurrentSelectedUnitPrice());
    
    // Check if price changed and requires password
    if (unitPrice !== window.excelInterface.currentUnitPrice) {
        const password = prompt('修改電費單價需要管理員密碼:');
        if (password !== 'admin123') {
            window.powerMeterApp.showNotification('密碼錯誤，無法修改電費單價', 'error');
            resetUnitPriceSelector();
            return;
        }
    }
    
    const billingData = {
        start_date: document.getElementById('billingStartDate').value,
        end_date: document.getElementById('billingEndDate').value,
        unit_price: unitPrice
    };
    
    window.powerMeterApp.apiRequest('/api/system/billing-period', 'PUT', billingData)
        .then(response => {
            if (response.success) {
                window.excelInterface.currentUnitPrice = unitPrice;
                window.powerMeterApp.showNotification('計費週期設定更新成功', 'success');
                
                // Update statistics display to show new unit price
                window.excelInterface.updateStatistics();
                
                // Refresh usage and amount calculations
                window.excelInterface.refreshMeterData();
            } else {
                window.powerMeterApp.showNotification('更新失敗: ' + response.error, 'error');
            }
        })
        .catch(error => {
            console.error('Failed to update billing period:', error);
            window.powerMeterApp.showNotification('網絡錯誤', 'error');
        });
};

window.batchPowerControl = function(powerOn) {
    const meterIds = Array.from({length: 48}, (_, i) => i + 1);
    const action = powerOn ? '供電' : '斷電';
    
    if (confirm(`確定要對所有電表執行${action}操作嗎？`)) {
        window.powerMeterApp.batchControlMeters(meterIds, powerOn);
    }
};

window.refreshAllData = function() {
    window.excelInterface.refreshMeterData();
};

window.exportData = function() {
    window.powerMeterApp.showNotification('數據導出功能開發中...', 'info');
};

window.saveMeterDetails = function() {
    window.excelInterface.saveMeterDetails();
};

// Update interval control functions
window.updateIntervalDisplay = function() {
    const slider = document.getElementById('updateInterval');
    const valueDisplay = document.getElementById('intervalValue');
    if (slider && valueDisplay) {
        const value = parseInt(slider.value);
        valueDisplay.textContent = value;
        
        // Update color based on interval
        if (value <= 10) {
            valueDisplay.className = 'text-danger fw-bold';
        } else if (value <= 30) {
            valueDisplay.className = 'text-warning fw-bold';
        } else {
            valueDisplay.className = 'text-success fw-bold';
        }
        
        console.log(`🎚️ Slider updated to: ${value}s`);
    }
};

window.applyUpdateInterval = function() {
    const slider = document.getElementById('updateInterval');
    const currentIntervalDisplay = document.getElementById('currentInterval');
    if (!slider) return;
    
    const interval = parseInt(slider.value);
    
    // Validate interval range
    if (interval < 5 || interval > 180) {
        window.powerMeterApp.showNotification('更新間隔必須在 5-180 秒之間', 'error');
        return;
    }
    
    // Show loading state
    const button = document.querySelector('button[onclick="applyUpdateInterval()"]');
    const originalContent = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>套用中...';
    button.disabled = true;
    
    // Update via API
    window.powerMeterApp.apiRequest('/api/system/update-interval', 'PUT', {
        interval: interval
    }).then(response => {
        if (response.success) {
            // Apply to PowerMeterApp
            if (window.powerMeterApp.updateRefreshInterval(interval)) {
                // Update current interval display
                if (currentIntervalDisplay) {
                    currentIntervalDisplay.textContent = `${interval}秒`;
                    // Update color based on interval
                    if (interval <= 10) {
                        currentIntervalDisplay.className = 'fw-bold text-danger';
                    } else if (interval <= 30) {
                        currentIntervalDisplay.className = 'fw-bold text-warning';
                    } else {
                        currentIntervalDisplay.className = 'fw-bold text-success';
                    }
                }
                
                // Update schedule display interval if ExcelInterface exists
                if (window.excelInterface && window.excelInterface.updateScheduleDisplayInterval) {
                    window.excelInterface.updateScheduleDisplayInterval(interval);
                }
                
                // Also update the slider value to reflect current setting
                const slider = document.getElementById('updateInterval');
                if (slider) {
                    slider.value = interval;
                    console.log(`🔄 Synchronized slider to: ${interval}s`);
                }
                
                // Show appropriate message based on interval
                let message = `更新間隔已設為 ${interval} 秒`;
                let type = 'success';
                
                if (interval <= 10) {
                    message += ' (高頻更新，可能影響性能)';
                    type = 'warning';
                } else if (interval >= 120) {
                    message += ' (低頻更新，節省資源)';
                }
                
                window.powerMeterApp.showNotification(message, type);
            } else {
                window.powerMeterApp.showNotification('更新間隔範圍錯誤', 'error');
            }
        } else {
            window.powerMeterApp.showNotification('設定失敗: ' + response.error, 'error');
        }
    }).catch(error => {
        console.error('Failed to update interval:', error);
        window.powerMeterApp.showNotification('網絡錯誤', 'error');
    }).finally(() => {
        // Restore button state
        button.innerHTML = originalContent;
        button.disabled = false;
    });
};

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('Excel interface DOM loaded');
    
    // Initialize immediately and retry if needed
    const initExcel = () => {
        try {
            console.log('Initializing Excel interface...');
            window.excelInterface = new ExcelInterface();
            console.log('Excel interface initialized successfully');
        } catch (error) {
            console.error('Excel interface initialization failed:', error);
            
            // Fallback: basic event handlers
            console.log('Setting up fallback event handlers...');
            setupFallbackHandlers();
        }
    };
    
    // Enhanced fallback handlers with better event delegation
    const setupFallbackHandlers = () => {
        console.log('Setting up fallback event handlers...');
        
        // Use event delegation for better performance and reliability
        // Only add this listener if we're on the Excel interface page
        if (document.querySelector('.household-cell') || document.querySelector('.excel-container')) {
            document.addEventListener('click', function(e) {
                // Handle household cells
                if (e.target.classList.contains('household-cell')) {
                    console.log('Household cell clicked:', e.target.textContent);
                    
                    // Toggle power state
                    if (e.target.classList.contains('power-on')) {
                        e.target.classList.remove('power-on');
                        e.target.classList.add('power-off');
                        console.log('Switched to power off');
                    } else {
                        e.target.classList.remove('power-off');
                        e.target.classList.add('power-on');
                        console.log('Switched to power on');
                    }
                    
                    // Visual feedback
                    e.target.style.transform = 'scale(0.95)';
                    setTimeout(() => {
                        e.target.style.transform = 'scale(1)';
                    }, 100);
                }
                
                // Handle buttons (only on Excel page)
                if (e.target.tagName === 'BUTTON') {
                    console.log('Button clicked:', e.target.textContent);
                    
                    // Handle specific button actions
                    const buttonText = e.target.textContent;
                    if (buttonText.includes('刷新')) {
                        console.log('Refresh button clicked');
                        location.reload();
                    } else if (buttonText.includes('全部供電')) {
                        console.log('Power on all button clicked');
                        document.querySelectorAll('.household-cell').forEach(cell => {
                            cell.classList.remove('power-off');
                            cell.classList.add('power-on');
                        });
                    } else if (buttonText.includes('全部斷電')) {
                        console.log('Power off all button clicked');
                        document.querySelectorAll('.household-cell').forEach(cell => {
                            cell.classList.remove('power-on');
                            cell.classList.add('power-off');
                        });
                    }
                }
            });
        }
        
        // Add visual feedback for all clickable elements
        document.addEventListener('mousedown', function(e) {
            if (e.target.classList.contains('household-cell') || e.target.tagName === 'BUTTON') {
                e.target.style.opacity = '0.7';
            }
        });
        
        document.addEventListener('mouseup', function(e) {
            if (e.target.classList.contains('household-cell') || e.target.tagName === 'BUTTON') {
                e.target.style.opacity = '1';
            }
        });
        
        console.log('Fallback handlers set up successfully');
    };
    
    // Wait for app to be ready with improved timeout handling
    const waitForApp = (attempts = 0) => {
        console.log(`Waiting for PowerMeterApp... attempt ${attempts + 1}`);
        
        if (window.powerMeterApp) {
            console.log('PowerMeterApp found, initializing Excel interface');
            initExcel();
        } else if (attempts < 30) { // Wait up to 3 seconds
            setTimeout(() => waitForApp(attempts + 1), 100);
        } else {
            console.warn('PowerMeterApp not found after 3 seconds, using fallback');
            setupFallbackHandlers();
        }
    };
    
    waitForApp();
});