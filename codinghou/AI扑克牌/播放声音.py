import edge_tts
import asyncio
import os
import time
from datetime import datetime
async def edge_tts_demo(text, save_path):  # 默认保存为{}.mp3，可自定义保存路径
    # 选择音色（zh-CN-XiaoyiNeural 是中文女声，可换其他音色）
    communicate = edge_tts.Communicate(text, "zh-CN-XiaoyiNeural")
    # 保存音频文件
    await communicate.save(save_path)
    print(f"音频已保存到：{save_path}")

def run_to_sounds():
    os.system("movie_player.exe")

if __name__ == "__main__":
    list = ["2", "3", "4", "5", "6", "7", "8", "9", "10","勾", "但", "k", "歼"]
    for i in list:
        text = f"一张{i}"
        # 生成音频文件
        asyncio.run(edge_tts_demo(text, f"{text}.mp3"))
