# 修复 exe 打包后 combined.ico 路径问题

## 问题分析
- 错误：`TclError: bitmap "E:\coding-zhou\Python\python 日程表\dist/combined.ico" not defined`
- 原因：`self.dir_path = os.getcwd()` 获取的是当前工作目录，而不是 exe 所在目录
- 打包后，exe 运行时的工作目录可能不是 `dist` 目录

## 修复方案
使用 PyInstaller 的标准方法获取 exe 所在目录：

### 步骤 1：添加获取 exe 目录的函数
在代码开头添加：
```python
import sys
import os

def get_app_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.getcwd()
```

### 步骤 2：修改 iconbitmap 调用
将第 3243 行的：
```python
cal_window.iconbitmap(self.dir_path+'/combined.ico')
```
改为：
```python
icon_path = os.path.join(get_app_path(), 'combined.ico')
cal_window.iconbitmap(icon_path)
```

### 步骤 3：重新打包
运行 PyInstaller 重新打包 exe
