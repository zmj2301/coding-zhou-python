# 测试AI调用功能
from ollama import chat

def test_ai_call():
    """
    测试AI调用功能是否正常
    """
    try:
        # 测试聊天模型调用
        messages = [
            {'role': 'system', 'content': '你是一个严格的游戏，只能回答"是"或不是，其他啥也不要说。'}, 
            {'role': 'user', 'content': '宋江是一百零八星宿之一吗？'}
        ]
        
        print("正在调用AI模型...")
        response = chat(
            model="qwen3:0.6b",
            options={
                "temperature": 0.1,
                "max_tokens": 500,
                "stream": False
            },
            messages=messages
        )
        
        answer = response.message.content.strip()
        print(f"AI回答：{answer}")
        return True
    except Exception as e:
        print(f"AI调用失败：{str(e)}")
        return False

if __name__ == "__main__":
    test_ai_call()