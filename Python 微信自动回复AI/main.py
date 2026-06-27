import requests
import json
import tkinter as tk
import os
from wxauto import WeChat
import time
from tkinter import messagebox as mg
import edge_tts
import asyncio

from wxauto.wxauto import TimeMessage

name = '小伊伊'
try:
    wx = WeChat()
    wx.ChatWith(who=name)
except:
    mg.showerror("错误", "请先打开微信")
    exit()

URL = "https://api.siliconflow.cn/v1/chat/completions"
FONT = ("Arial", 16)

persona = {
    '小伊伊': '请你扮演成小伊伊的哥哥，你的任务是回答用户的问题。注意小伊伊很喜欢欺负你，请小心回答，并带有反击的一点点幽默高情商语气,必须与提问的问题相结合，与用户语气相同,',
}

# 获取当前文件的绝对路径
current_file = os.path.abspath(__file__)
# 获取当前文件所在目录
current_dir = os.path.dirname(current_file)
# 组合目标文件路径（推荐）
target_path = os.path.join(current_dir, "users.json")
print(f"目标文件路径：{target_path}")
mouth = time.localtime().tm_mon
day = time.localtime().tm_mday

def get_answer(persona, content):
    import os
    from openai import OpenAI

    client = OpenAI(
        api_key=os.environ.get('DEEPSEEK_API_KEY', ''),
        base_url="https://api.deepseek.com")

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": persona},
            {"role": "user", "content": content},
        ],
        stream=False
    )

    return response.choices[0].message.content

def check_answer_past(msgs):
    msgs_ = []
    for m in msgs:
        if m.type == 'friend' or m.type == 'Self':
            msgs_.append(m)
    return msgs_

async def edge_tts_demo(text, save_path="edge_tts.mp3"):
    # 选择音色（zh-CN-XiaoyiNeural 是中文女声，可换其他音色）
    communicate = edge_tts.Communicate(text, "zh-CN-XiaoyiNeural")
    # 保存音频文件
    await communicate.save(save_path)
    # print(f"音频已保存到：{save_path}")

start_time = time.time()
running = True
# 增加调用次数
count = 0
# 添加已处理消息ID跟踪，避免重复处理
processed_messages = set()
# 添加循环延迟时间（秒）
loop_delay = 2

while running:
    t = time.time()
    
    # 增加循环延迟，避免高频调用
    time.sleep(loop_delay)
    
    print(int(t-start_time))
    
    # Check if there are any messages
    if count >= 5 or int(t-start_time) >= 400:
        wx.SendMsg('已调用5次API，今日额度已用完，正在转人工，下次再见！',who=name)
        running = False
        continue

    try:
        msgs = wx.GetAllMessage()
        
        if msgs:
            latest_msg = msgs[-1]
            
            # 生成消息唯一标识符（使用内容和发送者组合）
            msg_id = f"{latest_msg.type}_{latest_msg.content}_{latest_msg.time if hasattr(latest_msg, 'time') else 'notime'}"
            
            if latest_msg.content == '转人工' and latest_msg.type == 'friend':
                wx.SendMsg('好的，正在转人工，下次再见！',who=name)
                running = False
            elif latest_msg.type == 'friend' and msg_id not in processed_messages:
                # 标记消息为已处理
                processed_messages.add(msg_id)
                
                last_msgs = latest_msg.content
                if len(last_msgs) > 100:
                    last_msgs = last_msgs[:100]
                    
                m = check_answer_past(msgs)
                answer = get_answer(f"{str(last_msgs)},以下是聊天记录{m}",f'{persona[name]},作为一名兼具日常科普和会话专业知识的双重角色专家。作为日常科普专家，使用清晰且简短的语言和相关的例子，对与日常生活相关的科学概念提供准确、易懂的解释。(若用户没有提科学问题，请直接回答用户的问题)作为一名聊天专家，用简短的话语回答，一般不超过20字，语气平和以匹配受众的知识水平和兴趣。,并结合聊天记录回复最贴切的答案，已回答问题为主，聊天记录辅助回答，使回答内容更加完美，并以吸引人的方式呈现，鼓励好奇心和进一步讨论。',None)
                # print(answer)
                # 删除'/n'字符
                answer = ''.join(filter(None, answer.splitlines()))
                new_answer = ''.join(answer)
                # print(new_answer)
                try:
                    text = new_answer
                    save_path = "edge_tts.mp3"  # 定义音频保存路径
                    if text.strip():
                        asyncio.run(edge_tts_demo(text, save_path)) # 运行异步函数
                        # 播放音频文件
                        os.system(f"start {save_path}")
                        # 等待音频播放完成（给足够的时间）
                        time.sleep(3)  # 根据实际情况调整
                except edge_tts.exceptions.NoAudioReceived:
                    print("没有收到音频数据，可能是文本为空或参数错误")
                except Exception as e:
                    print(f"音频合成出错: {e}")
                
                # 增加发送消息前的延迟
                time.sleep(1)
                wx.SendMsg(new_answer,who=name)
                count += 1
                print(f"已调用{count}次API")
    except Exception as e:
        print(f"处理消息时出错: {e}")
        # 出错时增加额外延迟
        time.sleep(3)