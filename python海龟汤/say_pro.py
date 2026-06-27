import edge_tts
import asyncio
import os
import time
from datetime import datetime

async def edge_tts_demo(text, save_path="edge_tts.mp3"):
    # 选择音色和设置音量（zh-CN-XiaoyiNeural 是中文女声，可换其他音色）
    # 音量范围：0.0到2.0，默认1.0
    communicate = edge_tts.Communicate(
        text, 
        "zh-CN-XiaoyiNeural",
        rate="+0%",  # 语速，+0%表示正常语速
        volume="+0%"  # 音量，+0%表示正常音量，+50%表示放大50%，-50%表示缩小50%
    )
    # 保存音频文件
    await communicate.save(save_path)
    print(f"音频已保存到：{save_path}")

def close_audio_player():
    """尝试关闭音频播放器"""
    try:
        # Windows下关闭可能占用文件的进程
        os.system("taskkill /f /im wmplayer.exe 2>nul")
        os.system("taskkill /f /im Media.Player.exe 2>nul")
    except:
        pass

if __name__ == "__main__":
    try:
        
        # 关闭可能占用音频文件的播放器
        close_audio_player()
        
        # 生成音频文件
        asyncio.run(edge_tts_demo(f"一百零八星宿，之，天魁星，呼保义，宋江"))
        print("音频文件已播放")
        
        # 播放音频文件
        file_path = "edge_tts.mp3"
        os.system(f"start {file_path}")

        os.remove(file_path)
    
        
    except PermissionError:
        print("音频文件正在被使用，等待后重试...")
    except Exception as e:
        print(f"发生错误: {e}")
