from ollama import chat
import sys

print("脚本开始执行...", flush=True)
print(f"Python 版本：{sys.version}", flush=True)

try:
    print("正在调用 deepseek-r1:1.5b 模型...", flush=True)
    response = chat(
        model='qwen',
        messages=[{'role': 'user', 'content': '今天日期'}],
    )
    print("AI 回复:", flush=True)
    print(response.message.content, flush=True)
except Exception as e:
    print(f"发生错误：{type(e).__name__}: {e}", flush=True)
    print("请确保 ollama 服务正在运行", flush=True)
    import traceback
    traceback.print_exc()