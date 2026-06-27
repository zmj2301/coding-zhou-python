import os
import sys
import subprocess
import threading

def execute_command(command, project_dir=None):
    """
    执行命令，特殊处理 GUI 程序和需要替换占位符的命令
    
    :param command: 要执行的命令
    :param project_dir: 项目目录路径，用于替换 {项目路径} 占位符
    :return: 执行结果
    """
    if project_dir is None:
        project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 替换占位符
    command = command.replace("{项目路径}", project_dir)
    
    # 检测是否是 GUI 程序（视频通话、人脸检测等）
    is_gui_program = any(keyword in command.lower() for keyword in [
        "video_call", "test_env", "cv2", "tkinter", "pyaudio"
    ])
    
    try:
        if is_gui_program:
            # GUI 程序在新线程中执行，避免阻塞
            def run_gui():
                try:
                    # 使用 subprocess 启动独立进程
                    subprocess.Popen(
                        command,
                        shell=True,
                        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
                    )
                except Exception as e:
                    print(f"GUI程序执行失败: {e}")
            
            threading.Thread(target=run_gui, daemon=True).start()
            return "正在启动视频通话/人脸检测功能，请稍候..."
        else:
            # 普通命令同步执行
            result = os.popen(command).read()
            return result
    except Exception as e:
        return f"命令执行失败: {str(e)}"


def extract_contact_name(user_input):
    """
    从用户输入中提取联系人姓名
    
    :param user_input: 用户输入
    :return: 联系人姓名
    """
    keywords = ["打电话给", "呼叫", "打给", "和", "跟"]
    for keyword in keywords:
        if keyword in user_input:
            name = user_input.split(keyword)[-1].strip()
            # 清理标点符号和多余内容
            name = name.rstrip("。！？.,!?")
            # 移除可能带有的"视频通话"、"电话"等后缀
            for suffix in ["视频通话", "电话", "通话", "聊天"]:
                if name.endswith(suffix):
                    name = name[:-len(suffix)].strip()
            if name:
                return name
    return "联系人"


def build_video_call_command(contact_name, project_dir=None):
    """
    构建视频通话命令
    
    :param contact_name: 联系人姓名
    :param project_dir: 项目目录
    :return: 完整命令
    """
    if project_dir is None:
        project_dir = os.path.dirname(os.path.abspath(__file__))
    
    video_call_path = os.path.join(project_dir, "video_call.py")
    python_path = sys.executable
    
    # 创建一个简单的包装脚本，直接调用 make_call 函数
    wrapper_code = f'''
import sys
import os

# 添加项目路径
sys.path.insert(0, r"{project_dir}")

from video_call import make_call

if __name__ == "__main__":
    contact_name = sys.argv[1] if len(sys.argv) > 1 else "联系人"
    make_call(contact_name)
'''
    
    wrapper_path = os.path.join(project_dir, "temp_call_wrapper.py")
    with open(wrapper_path, "w", encoding="utf-8") as f:
        f.write(wrapper_code)
    
    # 构建命令
    command = f'"{python_path}" "{wrapper_path}" "{contact_name}"'
    return command


def build_face_detection_command(project_dir=None):
    """
    构建人脸检测命令
    
    :param project_dir: 项目目录
    :return: 完整命令
    """
    if project_dir is None:
        project_dir = os.path.dirname(os.path.abspath(__file__))
    
    test_env_path = os.path.join(project_dir, "test_env.py")
    python_path = sys.executable
    
    command = f'"{python_path}" "{test_env_path}"'
    return command
