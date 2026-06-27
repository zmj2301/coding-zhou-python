from zai import ZhipuAiClient
import os

client = ZhipuAiClient(api_key=os.environ.get('ZHIPUAI_API_KEY', ''))  # 请填写您自己的 API Key

response = client.chat.completions.create(
    model="glm-4.7-flash",
    messages=[
        {"role": "user", "content": "作为一名生活专家"},
        {"role": "assistant", "content": "人为什么要吃饭"},
        {"role": "user", "content": "我想知道一些关于我的生活的信息"},
        ],
    thinking={
        "type": "enabled",    # 启用深度思考模式
    },
    stream=True,              # 启用流式输出
    max_tokens=65536,          # 最大输出tokens
    temperature=1.0           # 控制输出的随机性
)

# 流式获取回复
for chunk in response:
    if chunk.choices[0].delta.reasoning_content:
        print(chunk.choices[0].delta.reasoning_content, end='', flush=True)

    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end='', flush=True)