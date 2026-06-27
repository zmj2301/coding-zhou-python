# Please install OpenAI SDK first: `pip3 install openai`
import os
from openai import OpenAI
import webbrowser

client = OpenAI(
    # 从环境变量中获取API密钥
    api_key=os.environ.get('DEEPSEEK_API_KEY', ''),
    base_url="https://api.deepseek.com")

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "你好"},
    ],
    stream=False
)

print(response.choices[0].message.content)
webbrowser.open("https://platform.deepseek.com/usage")