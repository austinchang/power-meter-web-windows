/**
 * 強制導航修復腳本
 * 用於解決連結按鈕不跳轉的問題
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Force navigation script loaded');
    
    // 找到所有的導航連結
    const navigationLinks = document.querySelectorAll('a.btn[href]');
    
    console.log(`Found ${navigationLinks.length} navigation links`);
    
    navigationLinks.forEach(link => {
        console.log(`Setting up navigation for: ${link.textContent.trim()} -> ${link.href}`);
        
        // 移除現有的事件監聽器（如果有的話）
        const newLink = link.cloneNode(true);
        link.parentNode.replaceChild(newLink, link);
        
        // 添加新的點擊事件
        newLink.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            console.log(`強制導航到: ${this.href}`);
            
            // 立即跳轉
            window.location.href = this.href;
        });
    });
});