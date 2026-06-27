import os
import requests
import json

# 智谱AI API配置
API_KEY = os.environ.get('ZHIPUAI_API_KEY', '')  # 填写您自己的 APIKey
BASE_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

# 请求头
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# 请求体
payload = {
    "model": "glm-4v",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "请帮我分析图片中的人物表情，判断人物是否开心、悲伤、愤怒等。"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://cloudcovert-1305175928.cos.ap-guangzhou.myqcloud.com/%E5%9B%BE%E7%89%87grounding.PNG"
                    }
                }
            ]
        }
    ],
    "temperature": 0.5,
    "max_tokens": 1000
}

# 发送请求
try:
    response = requests.post(
        BASE_URL,
        headers=headers,
        json=payload,
        timeout=60
    )
    response.raise_for_status()  # 抛出HTTP异常
    result = response.json()
    
    # 输出结果
    print("分析结果:")
    print(result["choices"][0]["message"]["content"])
    
except Exception as e:
    print(f"调用失败: {str(e)}")
    if response:
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
