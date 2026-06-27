import re
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 要监控的文件路径
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
TARGET_FILE = os.path.join(current_dir, "card_game_oop.py")
# 生成的思维导图文件路径
OUTPUT_FILE = os.path.join(current_dir, "card_game_mindmap_with_lines.txt")

run = True

class PythonParser:
    """解析Python文件，提取类和方法的定义及其行数"""
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.classes = []
        
    def parse(self):
        """解析Python文件，提取类和方法的定义"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        self.classes = []
        in_class = False
        in_method = False
        current_class = None
        current_method = None
        class_indent = 0
        method_indent = 0
        
        for line_num, raw_line in enumerate(lines, 1):
            line = raw_line.rstrip()
            stripped_line = line.strip()
            
            # 跳过空行和注释
            if not stripped_line or stripped_line.startswith('#'):
                continue
            
            # 计算缩进级别
            indent = len(line) - len(line.lstrip())
            
            # 提取类定义
            class_match = re.match(r'^class\s+(\w+)\s*(?:\(|:)\s*', stripped_line)
            if class_match:
                # 保存之前的类和方法
                if in_class:
                    if in_method:
                        current_method['line_end'] = line_num - 1
                        current_class['methods'].append(current_method)
                        in_method = False
                    current_class['line_end'] = line_num - 1
                    self.classes.append(current_class)
                
                # 开始新的类
                class_name = class_match.group(1)
                current_class = {
                    'name': class_name,
                    'line_start': line_num,
                    'line_end': None,
                    'methods': []
                }
                in_class = True
                in_method = False
                class_indent = indent
                continue
            
            # 提取方法定义
            method_match = re.match(r'^def\s+(\w+)\s*\(', stripped_line)
            if method_match and in_class:
                # 保存之前的方法
                if in_method:
                    current_method['line_end'] = line_num - 1
                    current_class['methods'].append(current_method)
                
                # 开始新的方法
                method_name = method_match.group(1)
                current_method = {
                    'name': method_name,
                    'line_start': line_num,
                    'line_end': None
                }
                in_method = True
                method_indent = indent
                continue
            
            # 处理类的结束
            if in_class and indent < class_indent:
                if in_method:
                    current_method['line_end'] = line_num - 1
                    current_class['methods'].append(current_method)
                    in_method = False
                current_class['line_end'] = line_num - 1
                self.classes.append(current_class)
                in_class = False
            
            # 处理方法的结束
            if in_method and indent < method_indent:
                current_method['line_end'] = line_num - 1
                current_class['methods'].append(current_method)
                in_method = False
        
        # 处理文件结尾的类和方法
        if in_class:
            if in_method:
                current_method['line_end'] = len(lines)
                current_class['methods'].append(current_method)
            current_class['line_end'] = len(lines)
            self.classes.append(current_class)
        
        return self.classes
    
    def generate_mindmap(self):
        """生成思维导图，包括每行的行号"""
        mindmap = ["# card_game_oo.py 代码作用思维导图（含行数信息）", ""]
        mindmap.append("┌─ card_game_oo.py")
        mindmap.append("│  ")
        
        for cls in self.classes:
            mindmap.append(f"├─ {cls['name']}类 - 行 {cls['line_start']}-{cls['line_end']}")
            
            for method in cls['methods']:
                mindmap.append(f"│  ├─ {method['name']}() - 行 {method['line_start']}-{method['line_end']}")
            
            mindmap.append("│  ")
        
        # 移除最后一个空行
        if mindmap[-1] == "│  ":
            mindmap.pop()
        
        return '\n'.join(mindmap)

class FileChangeHandler(FileSystemEventHandler):
    """监听文件变化的处理器"""
    
    def on_modified(self, event):
        """当文件被修改时触发"""
        if event.src_path.endswith(TARGET_FILE):
            print(f"检测到 {TARGET_FILE} 文件变化，更新思维导图...")
            update_mindmap()

def update_mindmap():
    """更新思维导图"""
    parser = PythonParser(TARGET_FILE)
    parser.parse()
    mindmap_content = parser.generate_mindmap()
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(mindmap_content)
    
    print(f"思维导图已更新到 {OUTPUT_FILE}")

def main():
    """主函数"""
    # 初始更新一次
    update_mindmap()
    
    # 监听文件变化
    event_handler = FileChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()
    
    print(f"正在监听 {TARGET_FILE} 文件变化...")
    print(f"按 Ctrl+C 停止监控")
    
    # 主循环
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("程序已停止")
        observer.stop()
    
    observer.join()

if __name__ == "__main__":
    main()
