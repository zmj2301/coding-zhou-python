from ollama import chat
import sys

print("开始测试...", file=sys.stderr)
print("Python 版本:", sys.version, file=sys.stderr)

try:
    print("调用模型中...", file=sys.stderr)
    response = chat(
        model='deepseek-r1:1.5b',
        messages=[{'role': 'user', 'content': '你好！请简单介绍一下你自己。'}],
    )
    print("=" * 50, file=sys.stderr)
    print("AI 回复:")
    print(response.message.content)
    print("=" * 50, file=sys.stderr)
except Exception as e:
    print(f"错误：{type(e).__name__}: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
