import edge_tts
import asyncio
import os
import time
from datetime import datetime

async def edge_tts_demo(text, save_path="edge_tts.mp3"):
    # 选择音色（zh-CN-XiaoyiNeural 是中文女声，可换其他音色）
    communicate = edge_tts.Communicate(text, "zh-CN-XiaoyiNeural")
    # 保存音频文件
    await communicate.save(save_path)
    print(f"音频已保存到：{save_path}")

def calculate_remaining_minutes(target_hour=22):
    """计算距离目标时间还有多少分钟"""
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    
    # 计算距离目标时间（默认晚上10点=22点）的分钟数
    remaining_minutes = (target_hour - current_hour) * 60 - current_minute
    
    # 如果已经过了目标时间，计算到明天目标时间的剩余分钟
    if remaining_minutes <= 0:
        remaining_minutes += 24 * 60  # 加上24小时的分钟数
    
    return remaining_minutes

def close_audio_player():
    """尝试关闭音频播放器"""
    try:
        # Windows下关闭可能占用文件的进程
        os.system("taskkill /f /im wmplayer.exe 2>nul")
        os.system("taskkill /f /im Media.Player.exe 2>nul")
        time.sleep(1)  # 等待进程关闭
    except:
        pass

if __name__ == "__main__":
    try:
        # 计算距离晚上10点还有多少分钟
        remaining_minutes = calculate_remaining_minutes(22)  # 22点 = 晚上10点
        
        # 关闭可能占用音频文件的播放器
        close_audio_player()
        
        # 生成音频文件
        asyncio.run(edge_tts_demo(f"晚上10点已到"))
        print("音频文件已播放")
        
        # 播放音频文件
        file_path = "edge_tts.mp3"
        os.system(f"start {file_path}")
        time.sleep(3)
        
        close_audio_player()
        
        # 等待一段时间再进行下一次循环
        time.sleep(57)  # 每分钟更新一次
        
    except PermissionError:
        print("音频文件正在被使用，等待后重试...")
        time.sleep(5)
    except Exception as e:
        print(f"发生错误: {e}")
        time.sleep(10)
