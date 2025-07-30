// Edge 瀏覽器時間輸入修復
(function() {
    'use strict';
    
    console.log('🔧 Edge 時間輸入修復載入中...');
    
    // 檢測是否為 Edge
    const isEdge = navigator.userAgent.includes('Edg/');
    
    if (!isEdge) {
        console.log('✅ 非 Edge 瀏覽器，不需要修復');
        return;
    }
    
    console.log('🌐 檢測到 Edge 瀏覽器，啟用修復');
    
    // 創建自定義時間選擇器
    function createCustomTimePicker(originalInput) {
        const wrapper = document.createElement('div');
        wrapper.className = 'custom-time-picker';
        wrapper.style.display = 'inline-block';
        wrapper.style.position = 'relative';
        
        // 創建小時選擇
        const hourSelect = document.createElement('select');
        hourSelect.className = 'form-select form-select-sm d-inline-block';
        hourSelect.style.width = '70px';
        hourSelect.style.marginRight = '5px';
        
        for (let i = 0; i < 24; i++) {
            const option = document.createElement('option');
            option.value = i.toString().padStart(2, '0');
            option.textContent = i.toString().padStart(2, '0');
            hourSelect.appendChild(option);
        }
        
        // 創建分隔符
        const separator = document.createElement('span');
        separator.textContent = ':';
        separator.style.margin = '0 5px';
        
        // 創建分鐘選擇
        const minuteSelect = document.createElement('select');
        minuteSelect.className = 'form-select form-select-sm d-inline-block';
        minuteSelect.style.width = '70px';
        
        // 提供 00 和 30 分鐘選項（半小時機制）
        const minuteOptions = ['00', '30'];
        minuteOptions.forEach(minute => {
            const option = document.createElement('option');
            option.value = minute;
            option.textContent = minute;
            minuteSelect.appendChild(option);
        });
        
        // 組合元素
        wrapper.appendChild(hourSelect);
        wrapper.appendChild(separator);
        wrapper.appendChild(minuteSelect);
        
        // 隱藏原始輸入框
        originalInput.style.display = 'none';
        
        // 設定初始值
        const currentValue = originalInput.value || '00:00';
        const [hours, minutes] = currentValue.split(':');
        hourSelect.value = hours || '00';
        // 設定分鐘，自動取最接近的 00 或 30
        const min = parseInt(minutes || '0');
        minuteSelect.value = min >= 30 ? '30' : '00';
        
        // 同步值到原始輸入框
        function updateValue() {
            const newValue = `${hourSelect.value}:${minuteSelect.value}`;
            originalInput.value = newValue;
            
            // 觸發 change 事件
            const event = new Event('change', { bubbles: true });
            originalInput.dispatchEvent(event);
            
            // 觸發 input 事件
            const inputEvent = new Event('input', { bubbles: true });
            originalInput.dispatchEvent(inputEvent);
            
            console.log(`📝 更新 ${originalInput.id}: ${newValue}`);
        }
        
        hourSelect.addEventListener('change', updateValue);
        minuteSelect.addEventListener('change', updateValue);
        
        // 插入到原始輸入框之後
        originalInput.parentNode.insertBefore(wrapper, originalInput.nextSibling);
        
        // 返回控制器
        return {
            setValue: function(value) {
                const [h, m] = value.split(':');
                hourSelect.value = h || '00';
                // 設定分鐘，自動取最接近的 00 或 30
                const min = parseInt(m || '0');
                minuteSelect.value = min >= 30 ? '30' : '00';
                updateValue();
            },
            getValue: function() {
                return `${hourSelect.value}:${minuteSelect.value}`;
            }
        };
    }
    
    // 修復所有時間輸入框
    function fixAllTimeInputs() {
        const timeInputs = document.querySelectorAll('input[type="time"]');
        const customPickers = {};
        
        timeInputs.forEach(input => {
            if (input.id && !input.dataset.customPicker) {
                console.log(`🔧 修復時間輸入: ${input.id}`);
                const picker = createCustomTimePicker(input);
                customPickers[input.id] = picker;
                input.dataset.customPicker = 'true';
            }
        });
        
        // 修正 excel-interface.js 中的方法
        if (window.excelInterface) {
            const originalUpdateControls = window.excelInterface.updateScheduleControlsWithRetry;
            
            window.excelInterface.updateScheduleControlsWithRetry = function(schedule, retryCount = 0) {
                // 呼叫原始方法
                originalUpdateControls.call(this, schedule, retryCount);
                
                // 使用自定義選擇器設定值
                if (schedule && customPickers) {
                    setTimeout(() => {
                        if (schedule.open_power) {
                            if (customPickers.openStartTime) {
                                customPickers.openStartTime.setValue(
                                    this.format24HourTime(schedule.open_power.start)
                                );
                            }
                            if (customPickers.openEndTime) {
                                customPickers.openEndTime.setValue(
                                    this.format24HourTime(schedule.open_power.end)
                                );
                            }
                        }
                        
                        if (schedule.close_power) {
                            if (customPickers.closeStartTime) {
                                customPickers.closeStartTime.setValue(
                                    this.format24HourTime(schedule.close_power.start)
                                );
                            }
                            if (customPickers.closeEndTime) {
                                customPickers.closeEndTime.setValue(
                                    this.format24HourTime(schedule.close_power.end)
                                );
                            }
                        }
                        
                        console.log('✅ Edge 修復: 時間值已更新');
                    }, 100);
                }
            };
        }
        
        console.log('✅ Edge 時間輸入修復完成');
    }
    
    // 等待 DOM 載入完成
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', fixAllTimeInputs);
    } else {
        // DOM 已載入，延遲執行以確保其他腳本已初始化
        setTimeout(fixAllTimeInputs, 100);
    }
})();