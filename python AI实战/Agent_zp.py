from openai import OpenAI
import os
from tkinter import messagebox
import sys

# 在本地创建一个hello.txt文件内容为hello world

# 直接用 OpenAI 格式调用智谱 AI
client = OpenAI(
    api_key=os.environ.get('ZHIPUAI_API_KEY', ''),  # 去 https://open.bigmodel.cn 申请
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)

try:
    skillmd = open("SKILL.md",'r',encoding='utf-8').read()
except FileNotFoundError as e:
    messagebox.showerror("错误", f"未找到SKILL.md文件: {e}")
    skillmd = ""

messages = [{"role": "system", "content": """你的目标是完成用户的任务(执行命令，总结信息)，你必须选择下面的其中一种格式进行回答,请确保命令符合标准cmd命令：
            1.输出'命令:XXX',xxx为命令本身，不要用任何的格式，不要解释
            2.输出'完成:XXX',xxx为你总结的信息
            注意：
            - 这是Windows系统，不要使用Unix/Linux命令（如touch）
            - 在Windows中创建空文件可以使用：type nul > 文件名.txt
            - 在Windows中创建带内容的文件可以使用：echo 内容 > 文件名.txt
            """+skillmd}]

def ask():
    import pyaudio
    from vosk import Model, KaldiRecognizer
    import wave
    import json
    import os
    import sys
    import platform
    import time

    def get_model_path():
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller打包环境
            model_path = os.path.join(sys._MEIPASS, "vosk-model-small-cn-0.22")
        elif hasattr(sys, 'frozen'):
            # Nuitka打包环境
            model_path = os.path.join(os.path.dirname(sys.executable), "vosk-model-small-cn-0.22")
        else:
            # 开发环境 - 使用绝对路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(current_dir, "vosk-model-small-cn-0.22")
            
            # Windows系统下，如果路径包含非ASCII字符，尝试使用短路径名
            if platform.system() == 'Windows':
                try:
                    # 检查路径是否包含非ASCII字符
                    model_path.encode('ascii')
                except UnicodeEncodeError:
                    # 路径包含非ASCII字符，尝试获取短路径名
                    try:
                        import subprocess
                        result = subprocess.run(
                            ['powershell', '-Command', 
                            f'$shell = New-Object -ComObject Scripting.FileSystemObject; $shortPath = $shell.GetFolder("{current_dir}").ShortPath; Write-Output $shortPath'],
                            capture_output=True,
                            text=True,
                            check=True
                        )
                        short_dir = result.stdout.strip()
                        model_path = os.path.join(short_dir, "vosk-model-small-cn-0.22")
                    except Exception as e:
                        print(f"警告：无法获取短路径名: {e}")
                        print(f"使用原始路径: {model_path}")
        
        # 验证路径是否存在
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型路径不存在: {model_path}")
        
        return model_path


    model = Model(get_model_path())
    # 创建麦克风对象。
    p = pyaudio.PyAudio()
    stream = p.open(
        # 16位采样，单声道，16kHz采样率，输入模式
        format=pyaudio.paInt16, 
        channels=1, 
        rate=16000, 
        input=True, 
        frames_per_buffer=4000
    )
    rec = KaldiRecognizer(model, 16000)
    print("请说话...")
    
    result_text = ""
    silence_start_time = None
    max_silence_duration = 2.0  # 静音2秒后认为说话结束
    max_listen_time = 15.0  # 最长监听时间15秒
    start_time = time.time()
    has_spoken = False  # 是否已经检测到语音

    while True:
        # 从麦克风读取数据
        data = stream.read(4000)
        
        # 检查是否超时
        elapsed_time = time.time() - start_time
        if elapsed_time > max_listen_time:
            print(f"监听超时({max_listen_time}秒)")
            break
        
        # 如果读取到数据，就进行识别。
        if rec.AcceptWaveform(data):
            result = rec.Result()
            result = json.loads(result)["text"].strip()
            if result:
                result_text += result
                has_spoken = True
                silence_start_time = None  # 重置静音计时
                print(f"识别中: {result_text}")
        
        # 检测静音
        if has_spoken and silence_start_time is None:
            # 检查当前是否为静音（通过检测部分结果）
            partial_result = json.loads(rec.PartialResult())
            if not partial_result.get("partial", ""):
                silence_start_time = time.time()
        elif silence_start_time is not None:
            silence_duration = time.time() - silence_start_time
            if silence_duration >= max_silence_duration:
                print(f"检测到静音{max_silence_duration}秒，认为说话结束")
                break
    
    # 获取最终识别结果
    final_result = rec.FinalResult()
    final_result = json.loads(final_result)["text"].strip()
    if final_result:
        result_text += final_result
    
    # 清理资源
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # 如果没有识别到任何内容，提示用户重试
    if not result_text or result_text.strip() == "":
        print("未识别到有效语音，请重试...")
        return ask()  # 递归调用重新识别
    
    print(f"识别完成: {result_text}")
    return result_text


while True:
    user_input = ask()
    print(f"【User】{user_input}")
    messages.append({"role":"user","content": user_input})

    print("\n------------------- Agent 循环开始 -------------------")

    while True:
        try:
            response = client.chat.completions.create(
                model="GLM-4-Flash",  # 免费模型，速度快
                messages=messages
            )

            reply = response.choices[0].message.content
            messages.append({"role":"assistant","content": reply})

            print(f"【AI】{reply}")

            if reply.strip().startswith("完成:"):
                print("\n------------------- Agent 任务完成，退出程序 -------------------")
                print(f"【AI】{reply.strip().split('完成:')[1].strip()}")
                sys.exit(0)  # 完全退出程序

            command = reply.strip().split("命令:")[1].strip()
            print(f"执行命令: {command}")
            # 执行命令并等待完成
            command_result = os.popen(command).read()
            print(f"命令执行完成")

            content = f"执行完毕 {command_result}"
            print(f"【Agent】{content}")
            messages.append({"role":"user","content": content})
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("错误", f"发生错误: {e}")
            print(f"错误：运行 Zclaw 时发生错误: {e}")
            print("\n------------------- Agent 因错误退出 -------------------")
            sys.exit(1)  # 完全退出程序
                