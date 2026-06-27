# PyInstaller 打包计划

## 目标
使用 PyInstaller 将 ZCLAW.py 脚本打包为独立的可执行文件（.exe），包含图标和相关资源文件。

## 文件结构

### 主文件
- **入口脚本**: `E:\coding-zhou\Python\python AI实战\ZCLAW.py`
- **图标文件**: `E:\coding-zhou\Python\python AI实战\256x256 (1).ico`

### 需要包含的资源目录
1. `E:\coding-zhou\Python\python AI实战\` - 主目录（包含Python脚本）
2. `back-end/` - 后端代码
3. `front-end/` - 前端文件
4. `sever/` - 服务器相关文件

## 打包命令

```powershell
D:\python.exe -m PyInstaller `
    --noconfirm `
    --onefile `
    --windowed `
    --icon "E:\coding-zhou\Python\python AI实战\256x256 (1).ico" `
    --add-data "E:\coding-zhou\Python\python AI实战\back-end;back-end" `
    --add-data "E:\coding-zhou\Python\python AI实战\front-end;front-end" `
    --add-data "E:\coding-zhou\Python\python AI实战\sever;sever" `
    --add-data "E:\coding-zhou\Python\python AI实战\Agent_zp.py;." `
    --add-data "E:\coding-zhou\Python\python AI实战\LLM.py;." `
    --add-data "E:\coding-zhou\Python\python AI实战\SKILL.md;." `
    --add-data "E:\coding-zhou\Python\python AI实战\deepseek.py;." `
    --add-data "E:\coding-zhou\Python\python AI实战\create_tunnel.py;." `
    "E:\coding-zhou\Python\python AI实战\ZCLAW.py"
```

## 实施步骤

1. **检查 PyInstaller 安装**
   - 确认 D:\python.exe 存在且 PyInstaller 已安装
   - 如未安装，执行 `D:\python.exe -m pip install pyinstaller`

2. **执行打包命令**
   - 在 PowerShell 中运行上述完整命令
   - 等待打包完成

3. **验证输出**
   - 检查 `dist/ZCLAW.exe` 是否生成
   - 测试可执行文件是否能正常运行

4. **路径处理说明**
   - Windows 使用分号 `;` 作为 --add-data 的分隔符
   - 图标路径使用 --icon 参数指定
   - 所有资源文件使用 --add-data 包含

## 预期输出
- 位置: `E:\coding-zhou\Python\python AI实战\dist\ZCLAW.exe`
- 类型: 单文件可执行程序（--onefile）
- 模式: 窗口模式（--windowed，无控制台窗口）
