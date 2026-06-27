import pyaudio
from vosk import Model, KaldiRecognizer
import wave
import json
import os
import sys
import platform

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

while True:
    # 从麦克风读取数据
    data = stream.read(4000)
    # 如果读取到数据，就进行识别。
    if rec.AcceptWaveform(data):
        result = rec.Result()
        result = json.loads(result)["text"].replace(" ", "")
        print(result)
