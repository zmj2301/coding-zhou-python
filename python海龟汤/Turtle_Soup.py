import requests
import json
import tkinter as tk
import os

URL = "https://api.siliconflow.cn/v1/chat/completions"
FONT = ("Arial", 16)

# 获取当前文件的绝对路径
current_file = os.path.abspath(__file__)
# 获取当前文件所在目录
current_dir = os.path.dirname(current_file)
# 组合目标文件路径（推荐）
target_path = os.path.join(current_dir, "users.json")
print(f"目标文件路径：{target_path}")

def get_answer(quesion,player,api):
    global text_box
    text_box.config(state=tk.NORMAL)
    text_box.insert(tk.END, f">>> 用户: {quesion}\n\n")
    text_box.see(tk.END)
    text_box.config(state=tk.DISABLED)
    entry.delete(0, tk.END)
    url = URL
    payload = {
        "model": "Qwen/QwQ-32B",
        "messages": [
            {
                "role": "system",
                "content":player
            },
            {
                "role": "user",
                "content": quesion
            }
        ]
    }
    headers = {
        "Authorization": "Bearer " + os.environ.get('DEEPSEEK_API_KEY', ''),
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, json=payload, headers=headers)

    print(json.loads(response.text)['choices'][0]['message']['content'])

    answer = json.loads(response.text)['choices'][0]['message']['content']
    text_box.config(state=tk.NORMAL)
    text_box.insert(tk.END, f">>> DeepSeek: {answer}\n\n")
    text_box.see(tk.END)
    text_box.config(state=tk.DISABLED)



# 创建主窗口
root = tk.Tk()
root.title("DeepSeek 聊天界面")

label = tk.Label(root, text="deepseek 聊天界面",font=FONT)
label.pack()


deepseek_key = "sk-vhtoequfzqqhvfvekgtgdytumvawxalzjmsgeoqkxosypteo"

# 创建滚动条
scrollbar = tk.Scrollbar(root)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# 创建多行文本框
text_box = tk.Text(
    root,
    height=30,
    width=50,
    yscrollcommand=scrollbar.set
)
text_box.pack(padx=10, pady=10)
text_box.config(state=tk.DISABLED)

button = tk.Button(root, text="发送", command=lambda: get_answer(entry.get(),'你现在是一个海龟汤游戏的出题者，玩家会向你提问，你只能用"是"或"不是"来回答。如果玩家输入"揭示谜底"或类似请求，你需要直接告诉玩家完整的故事真相。你已经掌握了一个离奇事件的完整故事。',deepseek_key))
button.pack(side='right')

entry = tk.Entry(root, width=45)
entry.pack(side='right')
entry.insert(tk.END,"请你作为海龟汤游戏的出题者，提出一个简短、离奇的情境谜面（汤面），只需要输出谜面内容，不要包含任何其他解释或标记。")

# 配置滚动条
scrollbar.config(command=text_box.yview)

# get_answer("请你作为海龟汤游戏的出题者，提出一个简短、离奇的情境谜面（汤面），只需要输出谜面内容，不要包含任何其他解释或标记。","出题者",deepseek_key)

# 运行主循环
root.mainloop()
