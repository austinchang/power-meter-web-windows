/**
 * Debug JavaScript for testing basic functionality
 */

console.log('Debug script loaded');

// Simple test functions
function testAlert() {
    alert('JavaScript 正常工作！');
}

function testConsole() {
    console.log('Console test - JavaScript 已載入');
}

// Check if jQuery/Bootstrap is available
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded');
    
    // Test Socket.IO
    if (typeof io !== 'undefined') {
        console.log('Socket.IO 可用');
        try {
            const socket = io();
            socket.on('connect', () => {
                console.log('Socket.IO 連接成功');
            });
        } catch (e) {
            console.error('Socket.IO 連接錯誤:', e);
        }
    } else {
        console.error('Socket.IO 不可用');
    }
    
    // Test Bootstrap
    if (typeof bootstrap !== 'undefined') {
        console.log('Bootstrap 可用');
    } else {
        console.error('Bootstrap 不可用');
    }
    
    // Debug: Log all button clicks and force navigation for links
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('btn')) {
            console.log('按鈕點擊:', e.target.textContent.trim());
            
            // 如果是連結按鈕，強制導航
            if (e.target.tagName === 'A' && e.target.href) {
                console.log('強制導航到:', e.target.href);
                // 強制導航，以防其他事件阻止了預設行為
                setTimeout(() => {
                    window.location.href = e.target.href;
                }, 100);
            }
        }
    });
});

// Global test functions
window.debugTest = function() {
    console.log('Debug test function called');
    alert('Debug 測試成功！');
};

window.testSocketIO = function() {
    if (window.powerMeterApp && window.powerMeterApp.socket) {
        console.log('Socket connection state:', window.powerMeterApp.isConnected);
        window.powerMeterApp.socket.emit('test', { message: 'Test from client' });
    } else {
        console.error('PowerMeterApp not initialized');
    }
};