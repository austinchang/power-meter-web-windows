/**
 * 供電狀態切換功能
 * Power Status Toggle Functions
 */

/**
 * 切換電表供電狀態
 * @param {number} meterId - 電表ID
 */
function togglePowerStatus(meterId) {
    if (!window.powerMeterApp) {
        console.error('PowerMeterApp not ready');
        return;
    }
    
    // 獲取當前供電狀態
    const currentMeterData = window.powerMeterApp.getMeterData(meterId);
    if (!currentMeterData) {
        console.error(`Meter data not found for ID: ${meterId}`);
        return;
    }
    
    const currentPowerStatus = currentMeterData.power_on;
    const newPowerStatus = !currentPowerStatus;
    
    console.log(`Toggling power for meter ${meterId}: ${currentPowerStatus} -> ${newPowerStatus}`);
    
    // 立即更新UI
    updatePowerStatusUI(meterId, newPowerStatus);
    
    // 發送API請求
    window.powerMeterApp.apiRequest(`/api/meters/${meterId}/control`, 'POST', {
        power_on: newPowerStatus
    }).then(response => {
        if (response.success) {
            console.log(`Power status updated for meter ${meterId}: ${newPowerStatus}`);
            window.powerMeterApp.showNotification(
                `電表 ${meterId} ${newPowerStatus ? '供電' : '斷電'}成功`, 
                'success'
            );
        } else {
            // API失敗，恢復原狀態
            console.error(`Power control failed for meter ${meterId}:`, response);
            updatePowerStatusUI(meterId, currentPowerStatus);
            window.powerMeterApp.showNotification(
                `電表 ${meterId} 控制失敗: ${response.error || '未知錯誤'}`, 
                'error'
            );
        }
    }).catch(error => {
        // 網路錯誤，恢復原狀態
        updatePowerStatusUI(meterId, currentPowerStatus);
        console.error('Power control API error:', error);
        window.powerMeterApp.showNotification(
            `電表 ${meterId} 控制異常`, 
            'error'
        );
    });
}

/**
 * 更新供電狀態UI
 * @param {number} meterId - 電表ID
 * @param {boolean} powerOn - 供電狀態
 */
function updatePowerStatusUI(meterId, powerOn) {
    console.log(`Updating power status UI for meter ${meterId}: ${powerOn}`);
    
    // 更新所有群組中的對應電表
    const powerStatusCells = document.querySelectorAll(`.power-status-cell[data-meter="${meterId}"]`);
    
    console.log(`Found ${powerStatusCells.length} power status cells for meter ${meterId}`);
    
    powerStatusCells.forEach(cell => {
        if (powerOn) {
            cell.className = 'power-status-cell power-on';
            cell.innerHTML = '<i class="fas fa-power-off me-1"></i>ON';
        } else {
            cell.className = 'power-status-cell power-off';
            cell.innerHTML = '<i class="fas fa-power-off me-1"></i>OFF';
        }
        
        // 重新綁定點擊事件
        cell.onclick = () => togglePowerStatus(meterId);
        console.log(`Updated power status cell for meter ${meterId} to ${powerOn ? 'ON' : 'OFF'}`);
    });
    
    // 更新 PowerMeterApp 中的數據
    if (window.powerMeterApp && window.powerMeterApp.updateMeterPowerStatus) {
        window.powerMeterApp.updateMeterPowerStatus(meterId, powerOn);
    }
}

/**
 * 批量供電控制
 * @param {boolean} powerOn - 供電狀態
 */
function batchPowerControl(powerOn) {
    if (!window.powerMeterApp) {
        console.error('PowerMeterApp not ready');
        return;
    }
    
    const meterCount = 50; // 總電表數
    const meterIds = Array.from({length: meterCount}, (_, i) => i + 1);
    
    console.log(`Batch power control: ${powerOn ? 'ON' : 'OFF'} for ${meterCount} meters`);
    
    // 立即更新所有UI
    meterIds.forEach(meterId => {
        updatePowerStatusUI(meterId, powerOn);
    });
    
    // 發送批量API請求
    window.powerMeterApp.apiRequest('/api/meters/batch/control', 'POST', {
        meter_ids: meterIds,
        power_on: powerOn
    }).then(response => {
        if (response.success) {
            console.log(`Batch power control successful: ${response.data.success_count} meters`);
            window.powerMeterApp.showNotification(
                `批量${powerOn ? '供電' : '斷電'}成功: ${response.data.success_count}個電表`, 
                'success'
            );
        } else {
            window.powerMeterApp.showNotification(
                `批量控制失敗: ${response.error}`, 
                'error'
            );
        }
    }).catch(error => {
        console.error('Batch power control API error:', error);
        window.powerMeterApp.showNotification(
            '批量控制異常', 
            'error'
        );
    });
}

// 確保函數在全局範圍內可用
window.togglePowerStatus = togglePowerStatus;
window.updatePowerStatusUI = updatePowerStatusUI;
window.batchPowerControl = batchPowerControl;