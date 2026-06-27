from vosk import Model, KaldiRecognizer
import wave
import json
import os
import sys
import platform

# 获取模型路径，处理中文路径编码问题
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

# 加载模型
model_path = get_model_path()
print(f"正在加载模型，路径: {model_path}")
model = Model(model_path)

# 获取音频文件路径
audio_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "录音.m4a")
if not os.path.exists(audio_file):
    raise FileNotFoundError(f"音频文件不存在: {audio_file}")

# 检查音频文件格式
audio_ext = os.path.splitext(audio_file)[1].lower()

if audio_ext == '.m4a':
    # M4A格式需要转换为WAV格式
    try:
        from pydub import AudioSegment
        
        print(f"正在转换M4A文件为WAV格式...")
        audio = AudioSegment.from_file(audio_file, format='m4a')
        
        # 转换为16kHz单声道WAV格式（Vosk要求）
        audio = audio.set_frame_rate(16000).set_channels(1)
        
        # 导出为临时WAV文件
        temp_wav = os.path.join(os.path.dirname(audio_file), "temp_recording.wav")
        audio.export(temp_wav, format='wav')
        
        # 打开转换后的WAV文件
        a2 = wave.open(temp_wav, "rb")
        print(f"音频转换完成，开始识别...")
        
    except ImportError:
        print("错误：需要安装pydub库来处理M4A文件")
        print("请运行: pip install pydub")
        print("并且需要安装ffmpeg: https://ffmpeg.org/download.html")
        sys.exit(1)
    except Exception as e:
        print(f"音频转换失败: {e}")
        sys.exit(1)
else:
    # 直接打开WAV文件
    a2 = wave.open(audio_file, "rb")

# 创建识别器
rec = KaldiRecognizer(model, 16000)

while True:
    data = a2.readframes(4000)
    if not data:
        break
    rec.AcceptWaveform(data)

a5 = json.loads(rec.FinalResult())
print(a5)
print(a5["text"])