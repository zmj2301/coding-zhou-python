"""
语音识别API模块
使用Vosk进行离线语音识别
"""
from flask import Blueprint, request, jsonify
import pyaudio
from vosk import Model, KaldiRecognizer
import json
import os
import sys
import platform
import threading
import time

speech_bp = Blueprint('speech', __name__)

# 全局变量
recognizer = None
is_recording = False
current_text = ""
last_text_time = 0
silence_timeout = 3.0  # 静音3秒后自动停止

def get_model_path():
    """获取Vosk模型路径"""
    if hasattr(sys, '_MEIPASS'):
        model_path = os.path.join(sys._MEIPASS, "vosk-model-small-cn-0.22")
    elif hasattr(sys, 'frozen'):
        model_path = os.path.join(os.path.dirname(sys.executable), "vosk-model-small-cn-0.22")
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, "vosk-model-small-cn-0.22")
        
        if platform.system() == 'Windows':
            try:
                model_path.encode('ascii')
            except UnicodeEncodeError:
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
    
    return model_path

def init_recognizer():
    """初始化语音识别器"""
    global recognizer
    try:
        model_path = get_model_path()
        if not os.path.exists(model_path):
            return False, "模型路径不存在"
        
        model = Model(model_path)
        recognizer = KaldiRecognizer(model, 16000)
        return True, "初始化成功"
    except Exception as e:
        return False, str(e)

def recognition_worker():
    """语音识别工作线程"""
    global current_text, is_recording, last_text_time
    
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=4000
    )
    
    while True:
        if is_recording and recognizer:
            data = stream.read(4000)
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip()
                if text:
                    current_text += text
                    last_text_time = time.time()
                    print(f"识别中: {current_text}")
            
            # 检查静音超时
            if last_text_time > 0 and (time.time() - last_text_time) > silence_timeout:
                print(f"静音超时({silence_timeout}秒)，自动停止录音")
                is_recording = False
        else:
            # 暂停时稍微休息一下
            time.sleep(0.1)
    
    stream.stop_stream()
    stream.close()
    p.terminate()

# 启动识别工作线程
try:
    success, msg = init_recognizer()
    if success:
        threading.Thread(target=recognition_worker, daemon=True).start()
        print("语音识别服务已启动")
    else:
        print(f"语音识别初始化失败: {msg}")
except Exception as e:
    print(f"启动语音识别服务失败: {e}")

@speech_bp.route('/api/speech/start', methods=['POST'])
def start_recognition():
    """开始语音识别"""
    global is_recording, current_text, last_text_time
    
    if not recognizer:
        return jsonify({"success": False, "message": "语音识别器未初始化"})
    
    current_text = ""
    last_text_time = 0
    is_recording = True
    
    return jsonify({
        "success": True,
        "message": "开始录音"
    })

@speech_bp.route('/api/speech/stop', methods=['POST'])
def stop_recognition():
    """停止语音识别"""
    global is_recording, current_text
    
    # 保存当前识别结果
    result_text = current_text
    
    # 重置状态
    is_recording = False
    current_text = ""
    
    return jsonify({
        "success": True,
        "text": result_text,
        "message": "录音结束"
    })

@speech_bp.route('/api/speech/status', methods=['GET'])
def get_status():
    """获取识别状态"""
    return jsonify({
        "is_recording": is_recording,
        "text": current_text,
        "recognizer_ready": recognizer is not None
    })

@speech_bp.route('/api/speech/init', methods=['POST'])
def init_api():
    """初始化语音识别器"""
    success, msg = init_recognizer()
    return jsonify({
        "success": success,
        "message": msg
    })
