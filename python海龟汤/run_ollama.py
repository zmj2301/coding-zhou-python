import subprocess
import os
import sys

def 检查是否打开ollama服务():
    """
    检查ollama服务是否已启动
    """
    try:
        # 尝试执行ollama list，检查是否有响应
        subprocess.check_output(
            "ollama list",
            shell=True,
            stderr=subprocess.PIPE,
            encoding="utf-8"
        )
        return True
    except subprocess.CalledProcessError:
        return False
def open_cmd_and_run_ollama(model_name="llama3"):
    """
    强制弹出CMD窗口并执行ollama run（Windows专用，确保窗口可见）
    """
    # 第一步：检查是否为Windows系统
    if sys.platform != "win32":
        print("❌ 此方案仅支持Windows系统！")
        return
    
    # 第二步：先验证ollama是否安装并配置环境变量
    try:
        # 静默执行ollama --version，验证命令是否可用
        subprocess.check_output(
            "ollama --version",
            shell=True,
            stderr=subprocess.PIPE,
            encoding="utf-8"
        )
    except subprocess.CalledProcessError:
        print("❌ 未找到ollama命令！请先：")
        print("  1. 安装ollama（官网：https://ollama.com/）")
        print("  2. 配置ollama到系统环境变量（或重启电脑让环境变量生效）")
        return
    
    # 第三步：构造强制弹出CMD的命令（修复核心）
    # start cmd 是Windows强制新建窗口的命令，优先级最高
    cmd = f'start cmd /k "ollama serve"'
    
    try:
        # 执行命令（无需额外flags，start已强制新建窗口）
        subprocess.Popen(
            cmd,
            shell=True,
            cwd=os.path.expanduser("~")  # 切换到用户主目录，避免路径问题
        )
        print(f"✅ 已弹出CMD窗口，执行命令：ollama serve")
    except Exception as e:
        print(f"⚠️ 执行失败：{str(e)}")

# 调用函数（替换为你的模型名）
if __name__ == "__main__":
    if not 检查是否打开ollama服务():
        from tkinter import messagebox
        if messagebox.askyesno("ollama服务未启动", "是否尝试启动ollama服务？"):
            print("ollama服务未启动，尝试启动...")
            open_cmd_and_run_ollama()
        else:
            print("用户选择不启动ollama服务")
