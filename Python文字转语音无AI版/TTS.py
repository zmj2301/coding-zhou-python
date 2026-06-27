import pyttsx3
import os

engine = pyttsx3.init()
with open('test.txt', 'r', encoding='utf-8') as f:
    text = f.read()

engine.say(text)
# 调整参数
engine.setProperty('rate', 300)
engine.setProperty('volume', 0.5)
engine.setProperty('voice', 'zh-CN-YunxiuNeural-A')
engine.runAndWait()
