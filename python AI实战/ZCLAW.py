from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os
import re
import sys

# 导入技能执行器
from skill_executor import execute_command, extract_contact_name, build_video_call_command, build_face_detection_command

# 导入语音识别API（如果加载失败则跳过语音功能，仅保留记录功能）
try:
    from speech_api import speech_bp
except Exception as e:
    print(f"语音识别模块加载失败，将跳过语音功能: {e}")
    speech_bp = None

app = Flask(__name__)
CORS(app)

# 注册语音识别蓝图（仅在加载成功时注册）
if speech_bp is not None:
    app.register_blueprint(speech_bp)

# 获取资源路径的辅助函数，兼容开发环境和 Nuitka/PyInstaller 打包环境
def resource_path(relative_path):
    """获取资源的绝对路径，兼容开发环境和打包环境"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包环境
        return os.path.join(sys._MEIPASS, relative_path)
    elif hasattr(sys, 'frozen'):
        # Nuitka 打包环境
        return os.path.join(os.path.dirname(sys.executable), relative_path)
    else:
        # 开发环境
        return os.path.join(os.path.dirname(__file__), relative_path)

# 直接用 OpenAI 格式调用智谱 AI
client = OpenAI(
    api_key=os.environ.get('ZHIPUAI_API_KEY', ''),  # 去 https://open.bigmodel.cn 申请
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)

# 读取SKILL.md文件
skillmd = ""
try:
    skill_path = resource_path("SKILL.md")
    skillmd = open(skill_path, 'r', encoding='utf-8').read()
except FileNotFoundError:
    # 只在非重载器进程中显示错误弹窗，避免重复显示
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true' and not getattr(sys, '_called_from_test', False):
        from tkinter import messagebox
        messagebox.showerror("错误", "未找到SKILL.md文件，请确保文件存在于正确位置")
    skillmd = ""

# 存储对话历史的字典，键为会话ID
sessions = {}

# 危险指令列表
dangerous_commands = [
    r'rm\s+-rf', 
    r'del\s+/s\s+/q',
    r'format',
    r'regedit',
    r'shutdown',
    r'reboot',
    r'mkdir\s+/dev',
    r':(){:|:&};:',
    r'chmod\s+777',
    r'wget.*sh',
    r'curl.*sh',
    r'powershell.*-ExecutionPolicy.*Bypass',
    r'dd\s+if=',
    r'mv\s+/\S+',
]

# 检测危险指令
def is_dangerous_command(command):
    for pattern in dangerous_commands:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message')
    session_id = data.get('session_id', 'default')
    authorize = data.get('authorize', False)
    
    # 初始化会话
    if session_id not in sessions:
        sessions[session_id] = {
            'messages': [{
                "role": "system", 
                "content": """你是一个AI助手，必须优先使用工具执行任务。回答格式：
                1.需要执行命令时：输出'命令:XXX'，XXX为标准Windows cmd命令
                2.不需要执行命令时：输出'完成:XXX'，XXX为总结信息
                规则：
                - 每次只生成一个命令
                - 对于获取新闻、下载视频、安装工具等任务，必须使用对应技能命令
                - 不要让用户自己执行命令，由你通过工具执行
                - 当用户要求创建文件时，使用echo命令创建文件，例如：echo 内容 > 文件名.txt""" + skillmd
            }],
            'pending_command': None
        }
    
    # 检查是否有待授权的命令
    if sessions[session_id]['pending_command']:
        pending_cmd = sessions[session_id]['pending_command']
        if authorize:
            # 用户已授权，执行命令
            project_dir = os.path.dirname(os.path.abspath(__file__))
            command_result = execute_command(pending_cmd, project_dir)
            # 检查是否有错误信息
            if "系统找不到指定的文件" in command_result or "error" in command_result.lower() or "找不到" in command_result:
                # 命令执行失败，明确标记错误
                content = f"执行失败 {command_result}。请分析错误原因并决定是否重新执行或采取其他措施。"
            else:
                # 命令执行成功，返回结果
                content = f"执行完毕 {command_result}"
            sessions[session_id]['messages'].append({"role": "user", "content": content})
            
            # 再次调用AI获取最终回复
            response = client.chat.completions.create(
                model="GLM-4-Flash",
                messages=sessions[session_id]['messages']
            )
            
            final_reply = response.choices[0].message.content
            sessions[session_id]['messages'].append({"role": "assistant", "content": final_reply})
            sessions[session_id]['pending_command'] = None
            
            return jsonify({
                "type": "command_executed",
                "command": pending_cmd,
                "result": command_result,
                "final_reply": final_reply
            })
        else:
            # 用户未授权，结束任务
            sessions[session_id]['pending_command'] = None
            return jsonify({
                "type": "complete",
                "content": "已取消命令执行，任务结束。"
            })
    
    # 添加用户消息
    sessions[session_id]['messages'].append({"role": "user", "content": user_input})
    
    # 第一次调用AI，获取初始回复
    response = client.chat.completions.create(
        model="GLM-4-Flash",
        messages=sessions[session_id]['messages']
    )
    
    reply = response.choices[0].message.content
    sessions[session_id]['messages'].append({"role": "assistant", "content": reply})
    
    # 检查是否需要执行命令
    if reply.strip().startswith("完成:"):
        return jsonify({
            "type": "thinking",
            "step": 1,
            "content": "已分析用户请求，不需要执行命令，任务完成。",
            "ai_reply": reply.strip().split("完成:")[1].strip()
        })
    elif "命令:" in reply:
        # 提取命令
        try:
            command = reply.strip().split("命令:")[1].strip()
            
            # 检测是否为危险命令
            is_dangerous = is_dangerous_command(command)
            
            if is_dangerous:
                # 危险命令，需要授权
                sessions[session_id]['pending_command'] = command
                return jsonify({
                    "type": "authorization_required",
                    "step": 2,
                    "content": "检测到危险命令，需要您的授权才能执行。",
                    "command": command,
                    "ai_reply": reply
                })
            else:
                # 安全命令，直接执行
                project_dir = os.path.dirname(os.path.abspath(__file__))
                command_result = execute_command(command, project_dir)
                # 检查是否有错误信息
                if "系统找不到指定的文件" in command_result or "error" in command_result.lower() or "找不到" in command_result:
                    # 命令执行失败，明确标记错误
                    content = f"执行失败 {command_result}。请分析错误原因并决定是否重新执行或采取其他措施。"
                else:
                    # 命令执行成功
                    content = f"执行完毕 {command_result}"
                sessions[session_id]['messages'].append({"role": "user", "content": content})
                
                # 再次调用AI获取最终回复
                response = client.chat.completions.create(
                    model="GLM-4-Flash",
                    messages=sessions[session_id]['messages']
                )
                
                final_reply = response.choices[0].message.content
                sessions[session_id]['messages'].append({"role": "assistant", "content": final_reply})
                
                return jsonify({
                    "type": "command_executed",
                    "step": 3,
                    "content": "安全命令已执行，正在生成最终回复。",
                    "command": command,
                    "result": command_result,
                    "final_reply": final_reply
                })
        except Exception as e:
            # 处理命令提取错误
            return jsonify({
                "type": "complete",
                "content": f"命令执行失败：{str(e)}"
            })
    else:
        # AI回复格式不正确，重新请求正确格式
        correction_message = "你的回复格式不正确，请使用正确的格式：\n1.需要执行命令时：输出'命令:XXX'，XXX为标准Windows cmd命令\n2.不需要执行命令时：输出'完成:XXX'，XXX为总结信息\n请重新回复。"
        sessions[session_id]['messages'].append({"role": "user", "content": correction_message})
        
        # 再次调用AI获取正确格式的回复
        response = client.chat.completions.create(
            model="GLM-4-Flash",
            messages=sessions[session_id]['messages']
        )
        
        corrected_reply = response.choices[0].message.content
        sessions[session_id]['messages'].append({"role": "assistant", "content": corrected_reply})
        # 将AI所有回答的标点符号统一为英文
        corrected_reply = corrected_reply.replace("：", ":")

        # 再次检查格式
        if corrected_reply.strip().startswith("完成:"):
            return jsonify({
                "type": "thinking",
                "step": 1,
                "content": "已分析用户请求，不需要执行命令，任务完成。",
                "ai_reply": corrected_reply.strip().split("完成:")[1].strip()
            })
        elif "命令:" in corrected_reply:
            try:
                command = corrected_reply.strip().split("命令:")[1].strip()
                
                # 检测是否为危险命令
                is_dangerous = is_dangerous_command(command)
                
                if is_dangerous:
                    # 危险命令，需要授权
                    sessions[session_id]['pending_command'] = command
                    return jsonify({
                        "type": "authorization_required",
                        "step": 2,
                        "content": "检测到危险命令，需要您的授权才能执行。",
                        "command": command,
                        "ai_reply": corrected_reply
                    })
                else:
                    # 安全命令，直接执行
                    command_result = os.popen(command).read()
                    content = f"执行完毕 {command_result}"
                    sessions[session_id]['messages'].append({"role": "user", "content": content})
                    
                    # 再次调用AI获取最终回复
                    response = client.chat.completions.create(
                        model="GLM-4-Flash",
                        messages=sessions[session_id]['messages']
                    )
                    
                    final_reply = response.choices[0].message.content
                    sessions[session_id]['messages'].append({"role": "assistant", "content": final_reply})
                    
                    return jsonify({
                        "type": "command_executed",
                        "step": 3,
                        "content": "安全命令已执行，正在生成最终回复。",
                        "command": command,
                        "result": command_result,
                        "final_reply": final_reply
                    })
            except Exception as e:
                # 处理命令提取错误
                return jsonify({
                    "type": "complete",
                    "content": f"命令执行失败：{str(e)}"
                })
        else:
            # 仍然格式不正确
            return jsonify({
                "type": "complete",
                "content": f"抱歉，我无法理解您的请求，请尝试重新表述。{corrected_reply}"
            })

@app.route('/api/clear', methods=['POST'])
def clear():
    data = request.json
    session_id = data.get('session_id', 'default')
    if session_id in sessions:
        del sessions[session_id]
    return jsonify({"status": "success"})

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    user_input = data.get('message')
    session_id = 'default'
    
    # 初始化会话
    if session_id not in sessions:
        sessions[session_id] = {
            'messages': [{
                "role": "system", 
                "content": """你是一个AI助手，必须优先使用工具执行任务。回答格式：
                1.需要执行命令时：输出'命令:XXX'，XXX为标准Windows cmd命令
                2.不需要执行命令时：输出'完成:XXX'，XXX为总结信息
                规则：
                - 每次只生成一个命令
                - 对于获取新闻、下载视频、安装工具等任务，必须使用对应技能命令
                - 不要让用户自己执行命令，由你通过工具执行
                - 当用户要求创建文件时，使用echo命令创建文件，例如：echo 内容 > 文件名.txt""" + skillmd
            }],
            'pending_command': None
        }
    
    # 添加用户消息
    sessions[session_id]['messages'].append({"role": "user", "content": user_input})
    
    # 调用AI获取回复
    response = client.chat.completions.create(
        model="GLM-4-Flash",
        messages=sessions[session_id]['messages']
    )
    
    reply = response.choices[0].message.content
    sessions[session_id]['messages'].append({"role": "assistant", "content": reply})
    
    # 检查是否需要执行命令
    if reply.strip().startswith("完成:"):
        return jsonify({"response": reply.strip().split("完成:")[1].strip()})
    elif "命令:" in reply:
        # 提取命令
        try:
            command = reply.strip().split("命令:")[1].strip()
            
            # 检测是否为危险命令
            is_dangerous = is_dangerous_command(command)
            
            if is_dangerous:
                # 危险命令，返回需要授权
                return jsonify({"response": "检测到危险命令，需要授权才能执行"})
            else:
                # 安全命令，直接执行
                project_dir = os.path.dirname(os.path.abspath(__file__))
                command_result = execute_command(command, project_dir)
                # 检查是否有错误信息
                if "系统找不到指定的文件" in command_result or "error" in command_result.lower() or "找不到" in command_result:
                    # 命令执行失败，明确标记错误
                    content = f"执行失败 {command_result}。请分析错误原因并决定是否重新执行或采取其他措施。"
                else:
                    # 命令执行成功
                    content = f"执行完毕 {command_result}"
                sessions[session_id]['messages'].append({"role": "user", "content": content})
                
                # 再次调用AI获取最终回复
                response = client.chat.completions.create(
                    model="GLM-4-Flash",
                    messages=sessions[session_id]['messages']
                )
                
                final_reply = response.choices[0].message.content
                sessions[session_id]['messages'].append({"role": "assistant", "content": final_reply})
                
                return jsonify({"response": final_reply})
        except Exception as e:
            return jsonify({"response": f"命令执行失败：{str(e)}"})
    else:
        return jsonify({"response": reply})

# 提供前端文件
@app.route('/')
def serve_index():
    # 直接读取并返回index.html内容
    index_path = os.path.join(os.path.dirname(__file__), 'front-end', 'index.html')
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/<path:path>')
def serve_static(path):
    # 处理静态文件请求
    static_path = os.path.join(os.path.dirname(__file__), 'front-end', path)
    try:
        with open(static_path, 'rb') as f:
            content = f.read()
        # 根据文件扩展名设置Content-Type
        if path.endswith('.js'):
            return content, 200, {'Content-Type': 'application/javascript'}
        elif path.endswith('.css'):
            return content, 200, {'Content-Type': 'text/css'}
        elif path.endswith('.png'):
            return content, 200, {'Content-Type': 'image/png'}
        elif path.endswith('.jpg') or path.endswith('.jpeg'):
            return content, 200, {'Content-Type': 'image/jpeg'}
        elif path.endswith('.gif'):
            return content, 200, {'Content-Type': 'image/gif'}
        elif path.endswith('.ico'):
            return content, 200, {'Content-Type': 'image/x-icon'}
        else:
            return content, 200, {'Content-Type': 'application/octet-stream'}
    except Exception as e:
        return f"Error: {e}", 404

if __name__ == '__main__':
    import webbrowser
    import threading
    import time
    import os
    
    port = 5003
    url = f'http://127.0.0.1:{port}/'
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    # 只在非重载器进程中打开浏览器，避免启动两次
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        def open_browser():
            time.sleep(1.5)
            webbrowser.open(url)
        
        threading.Thread(target=open_browser).start()
    
    app.run(debug=True, host='0.0.0.0', port=port)
