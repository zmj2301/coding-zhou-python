# 导入声音模块
import pyttsx3

# 创建语音引擎实例
engine = pyttsx3.init()

def speak(text):
    """
    将文本转换为语音并播放
    参数：
        text: 要转换为语音的文本
    """
    try:
        # 设置语音属性
        rate = engine.getProperty('rate')  # 获取当前语速
        engine.setProperty('rate', 140)    # 设置语速（150字/分钟）
        
        volume = engine.getProperty('volume')  # 获取当前音量
        engine.setProperty('volume', 0.8)     # 设置音量（0.0-1.0）
        
        # 选择语音（如果有多个）
        voices = engine.getProperty('voices')
        # 遍历所有可用语音，选择第一个中文语音
        for voice in voices:
            if 'en' in voice.id or 'english' in voice.id.lower():
                engine.setProperty('voice', voice.id)
                break
        print(voice.id)
        
        # 将文本转换为语音并播放
        engine.say(text)
        engine.runAndWait()
        print(f"已播放语音：{text}")
        return True
    except Exception as e:
        print(f"播放语音时出错：{str(e)}")
        return False

# 测试代码
if __name__ == "__main__":
    test_text = "一百零八星宿，之，天魁星，呼保义，宋江"
    print(f"正在播放：{test_text}")
    speak(test_text)

