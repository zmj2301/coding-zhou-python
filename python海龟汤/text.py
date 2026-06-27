import pyttsx3
engine = pyttsx3.init()
voices = engine.getProperty('voices')
for voice in voices:
    print(f"ID: {voice.id}")
    print(f"名称: {voice.name}")
    print(f"语言: {voice.languages}")
    print(f"性别: {voice.gender}")
    print(f"年龄: {voice.age}")
    print("-" * 50)