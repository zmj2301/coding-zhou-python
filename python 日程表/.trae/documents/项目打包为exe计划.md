# 项目打包为 exe 计划

## 目标
将 `show_yourwindows.py` 成功打包为独立的 exe 文件

## 当前状态分析

### 已有的配置文件
1. `build_exe.py` - PyInstaller 构建脚本
2. `show_yourwindows.spec` - PyInstaller 规范文件

### 依赖的库（从代码分析）
- PySide6 (Qt 库)
- tkinter (标准库)
- json (标准库)
- 其他标准库：os, random, time, typing

## 打包步骤

### 步骤 1：检查并修复 spec 文件
由于程序使用了 PySide6（Qt）和 tkinter，需要在 spec 文件中添加必要的配置：
- 添加 `hiddenimports` 包含所有依赖的库
- 确保 `datas` 包含程序需要的资源文件（如 img 目录）

### 步骤 2：检查资源文件路径
程序中使用的资源：
- `img/icon.png` - 图标文件
- `img/window_icon.png` - 窗口图标
- `456.xlsx` - 数据文件
- `user_data.json` - 用户数据
- `ai_awswers.json` - AI 回答缓存
- `user.json` - 用户配置

### 步骤 3：更新 spec 文件
需要修改 `show_yourwindows.spec`：
```python
a = Analysis(
    ['show_yourwindows.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('img', 'img'),
        ('*.xlsx', '.'),
        ('*.json', '.'),
    ],
    hiddenimports=[
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'json',
    ],
    ...
)
```

### 步骤 4：执行打包
运行 PyInstaller 打包命令：
```bash
D:\python.exe -m PyInstaller show_yourwindows.spec --clean
```

### 步骤 5：验证输出
检查生成的 exe 文件是否在当前目录下

## 注意事项
1. 由于有 `tensorflow` 等大型库的依赖，打包可能会花较长时间
2. 如果打包失败，需要根据错误信息添加缺失的 hidden imports
3. 某些库可能需要手动添加数据文件
