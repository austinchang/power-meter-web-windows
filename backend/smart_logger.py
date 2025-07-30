#!/usr/bin/env python3
"""
Universal Smart Logging System
通用智能記錄系統 - 可被任何專案導入使用

Version: 2.0.0
Author: Claude Code
License: MIT
"""

import sys
import re
import os
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class UniversalSmartLogger:
    """通用智能記錄器 - 可配置用於任何專案"""
    
    def __init__(self, project_name: str = None, config: Dict = None):
        """
        初始化智能記錄器
        
        Args:
            project_name: 專案名稱 (用於自動偵測配置)
            config: 自定義配置
        """
        self.project_name = project_name or self._detect_project_name()
        self.config = self._load_config(config)
        self.trigger_patterns = self._build_trigger_patterns()
        
    def _detect_project_name(self) -> str:
        """自動偵測專案名稱"""
        cwd = Path.cwd()
        if 'multi-terminal-tester' in str(cwd):
            return 'multi-terminal-tester'
        elif 'gomoku' in str(cwd):
            return 'gomoku-game'
        else:
            return cwd.name
    
    def _load_config(self, custom_config: Dict = None) -> Dict:
        """載入配置"""
        default_config = {
            'release_notes_file': 'docs/RELEASE_NOTES.md',
            'backup_on_edit': True,
            'auto_keywords': True,
            'project_specific': {
                'multi-terminal-tester': {
                    'keywords_chinese': ['終端', 'SSH', '連線', '輸入', '游標', '超時'],
                    'keywords_english': ['terminal', 'ssh', 'connection', 'input', 'timeout'],
                    'default_files': ['src/main_enhanced.py', 'src/terminal_widget.py']
                },
                'gomoku-game': {
                    'keywords_chinese': ['五子棋', 'AI', '遊戲', '介面', '演算法'],
                    'keywords_english': ['gomoku', 'ai', 'game', 'gui', 'algorithm'],
                    'default_files': ['src/gomoku.py', 'src/simple_ai.py']
                }
            }
        }
        
        if custom_config:
            default_config.update(custom_config)
        
        return default_config
    
    def _build_trigger_patterns(self) -> List[str]:
        """建立觸發詞模式"""
        return [
            # 通用中文觸發詞
            r'記錄這個問題[:：]\s*(.+)',
            r'問題已解決[:：]\s*(.+)',
            r'修復了[:：]\s*(.+)',
            r'解決方案[:：]\s*(.+)',
            
            # 通用英文觸發詞
            r'LOG_ISSUE[:：]\s*(.+)',
            r'FIXED[:：]\s*(.+)',
            r'SOLUTION[:：]\s*(.+)',
            r'RESOLVED[:：]\s*(.+)',
            
            # 完整格式
            r'問題[:：](.+?)解決方案[:：](.+?)檔案[:：](.+)',
            r'ISSUE[:：](.+?)FIX[:：](.+?)FILE[:：](.+)',
            
            # 專案特定觸發詞
            f'記錄{self.project_name}問題[:：](.+)',
            f'LOG_{self.project_name.upper().replace("-", "_")}_ISSUE[:：](.+)',
        ]
    
    def parse_message(self, message: str) -> Optional[Dict]:
        """解析訊息，提取問題、解決方案和檔案"""
        for pattern in self.trigger_patterns:
            match = re.search(pattern, message, re.IGNORECASE | re.DOTALL)
            if match:
                groups = match.groups()
                
                if len(groups) == 1:
                    return self._parse_simple_format(groups[0])
                elif len(groups) == 3:
                    return {
                        'question': groups[0].strip(),
                        'solution': groups[1].strip(),
                        'files': groups[2].strip()
                    }
        
        return None
    
    def _parse_simple_format(self, text: str) -> Dict:
        """解析簡單格式的文字"""
        separators = ['解決方案', '修復', 'solution', 'fix', 'resolved', '→', '->', '=>']
        
        for sep in separators:
            if sep in text.lower():
                parts = re.split(sep, text, 1, re.IGNORECASE)
                if len(parts) == 2:
                    return {
                        'question': parts[0].strip(),
                        'solution': parts[1].strip(),
                        'files': self._suggest_files(parts[0] + parts[1])
                    }
        
        return {
            'question': text.strip(),
            'solution': '請提供解決方案',
            'files': self._suggest_files(text)
        }
    
    def _suggest_files(self, text: str) -> str:
        """根據內容建議檔案位置"""
        project_config = self.config['project_specific'].get(self.project_name, {})
        default_files = project_config.get('default_files', ['待定'])
        
        # 簡單的檔案建議邏輯
        text_lower = text.lower()
        if 'gui' in text_lower or '介面' in text_lower:
            return default_files[0] if default_files else '待定'
        elif 'ai' in text_lower or '演算法' in text_lower:
            return default_files[-1] if default_files else '待定'
        else:
            return '待定'
    
    def log_user_question(self, question: str, solution: str, files: str) -> bool:
        """記錄使用者問題到 RELEASE_NOTES.md"""
        release_notes_path = Path(self.config['release_notes_file'])
        
        if not release_notes_path.exists():
            self._create_release_notes_template(release_notes_path)
        
        # 備份檔案
        if self.config['backup_on_edit']:
            backup_path = release_notes_path.with_suffix('.backup.md')
            if release_notes_path.exists():
                backup_path.write_text(release_notes_path.read_text(encoding='utf-8'))
        
        # 讀取現有內容
        try:
            with open(release_notes_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            content = self._get_release_notes_template()
        
        # 準備新增的內容
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S CST")
        
        # 更新內容
        updated_content = self._update_release_notes_content(
            content, question, solution, files, timestamp
        )
        
        # 寫回檔案
        with open(release_notes_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"✅ 已成功記錄 {self.project_name} 問題到 RELEASE_NOTES.md")
        print(f"   問題: {question}")
        print(f"   解決方案: {solution}")
        print(f"   修改檔案: {files}")
        print(f"   時間: {timestamp}")
        
        # 自動提取關鍵字
        if self.config['auto_keywords']:
            chinese_kw, english_kw = self.extract_keywords(question, solution)
            if chinese_kw or english_kw:
                print(f"\n📋 建議的關鍵字:")
                if chinese_kw:
                    print(f"   中文: {', '.join(chinese_kw)}")
                if english_kw:
                    print(f"   英文: {', '.join(english_kw)}")
        
        return True
    
    def _create_release_notes_template(self, path: Path):
        """創建 RELEASE_NOTES.md 模板"""
        template = self._get_release_notes_template()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(template, encoding='utf-8')
    
    def _get_release_notes_template(self) -> str:
        """取得 RELEASE_NOTES.md 模板"""
        return f"""# {self.project_name} - Release Notes

## Version 1.0.0 - Initial Release with Smart Logging
**Release Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S CST')}

### 🗣️ User Issues & System Responses

#### User Request Keywords & Solutions:
- **"範例問題"** → 範例解決方案 ✅

#### System Modification Keywords:
```
🔍 Search Terms: 專案相關關鍵字

🐛 Bug Fixes: 修復相關關鍵字

🔧 Technical: 技術相關關鍵字

🎨 UI/UX: 介面相關關鍵字
```

### 🐛 Problem → Solution Quick Reference
```
❌ "範例問題" → 範例解決方案 (檔案位置)
```

### 🔍 Keyword Index & Search Guide

### 🗣️ User Request Keywords (中文)
```
{', '.join(self.config['project_specific'].get(self.project_name, {}).get('keywords_chinese', []))}
```

### 🔧 Technical Keywords (English)
```
{', '.join(self.config['project_specific'].get(self.project_name, {}).get('keywords_english', []))}
```

---

*Last Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S CST')}*
*Maintainer: {self.project_name} Development Team*
*Smart Logging System: Universal v2.0.0*
"""
    
    def _update_release_notes_content(self, content: str, question: str, 
                                    solution: str, files: str, timestamp: str) -> str:
        """更新 RELEASE_NOTES.md 內容"""
        lines = content.split('\n')
        
        # 尋找並更新 User Request Keywords & Solutions 區段
        user_solutions_marker = "#### User Request Keywords & Solutions:"
        for i, line in enumerate(lines):
            if user_solutions_marker in line:
                # 找到插入位置
                for j in range(i + 1, len(lines)):
                    if lines[j].strip() == "" or lines[j].startswith("#### "):
                        new_entry = f'- **"{question}"** → {solution} ✅ ({timestamp})'
                        lines.insert(j, new_entry)
                        break
                break
        
        # 更新 Problem → Solution Quick Reference 區段
        quick_ref_marker = "### 🐛 Problem → Solution Quick Reference"
        for i, line in enumerate(lines):
            if quick_ref_marker in line:
                for j in range(i + 1, len(lines)):
                    if lines[j].strip() == "```" and j > i + 2:
                        new_quick_ref = f'❌ "{question}" → {solution} ({files})'
                        lines.insert(j, new_quick_ref)
                        break
                break
        
        return '\n'.join(lines)
    
    def extract_keywords(self, question: str, solution: str) -> Tuple[List[str], List[str]]:
        """從問題和解決方案中提取關鍵字"""
        project_config = self.config['project_specific'].get(self.project_name, {})
        
        chinese_keywords = []
        english_keywords = []
        
        # 專案特定關鍵字
        project_chinese = project_config.get('keywords_chinese', [])
        project_english = project_config.get('keywords_english', [])
        
        text = (question + ' ' + solution).lower()
        
        for keyword in project_chinese:
            if keyword in question or keyword in solution:
                chinese_keywords.append(keyword)
        
        for keyword in project_english:
            if keyword in text:
                english_keywords.append(keyword)
        
        # 通用關鍵字檢測
        common_chinese = ["無法", "不能", "沒有", "問題", "錯誤", "卡住", "修復", "改善"]
        common_english = ["error", "fix", "bug", "issue", "problem", "solution", "improve"]
        
        for keyword in common_chinese:
            if keyword in question or keyword in solution:
                if keyword not in chinese_keywords:
                    chinese_keywords.append(keyword)
        
        for keyword in common_english:
            if keyword in text:
                if keyword not in english_keywords:
                    english_keywords.append(keyword)
        
        return chinese_keywords, english_keywords
    
    def auto_log_from_text(self, text: str) -> bool:
        """從文字中自動記錄問題"""
        parsed = self.parse_message(text)
        if parsed:
            return self.log_user_question(
                parsed['question'],
                parsed['solution'], 
                parsed['files']
            )
        return False

def main():
    """命令列介面"""
    if len(sys.argv) < 2:
        print("Universal Smart Logger - 通用智能記錄器")
        print("")
        print("使用方法:")
        print("1. 直接記錄:")
        print("   python3 smart_logger.py \"記錄這個問題：問題描述 解決方案：解決方法\"")
        print("")
        print("2. 指定專案:")
        print("   python3 smart_logger.py --project gomoku-game \"LOG_ISSUE：AI太弱 FIX：改善演算法\"")
        print("")
        print("3. 從檔案記錄:")
        print("   python3 smart_logger.py --file conversation.txt")
        return
    
    # 解析參數
    project_name = None
    text = None
    file_path = None
    
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--project" and i + 1 < len(args):
            project_name = args[i + 1]
            i += 2
        elif args[i] == "--file" and i + 1 < len(args):
            file_path = args[i + 1]
            i += 2
        else:
            text = " ".join(args[i:])
            break
    
    # 初始化記錄器
    logger = UniversalSmartLogger(project_name)
    
    # 執行記錄
    if file_path:
        if not os.path.exists(file_path):
            print(f"檔案不存在: {file_path}")
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        success = logger.auto_log_from_text(content)
        if not success:
            print("在檔案中沒有找到可記錄的問題格式")
    
    elif text:
        success = logger.auto_log_from_text(text)
        if not success:
            print("沒有找到可記錄的問題格式")
            print("請使用支援的觸發詞格式")
    
    else:
        print("請提供要記錄的文字或檔案路徑")

if __name__ == "__main__":
    main()