import os
from zhipuai import ZhipuAI


API_KEY = os.environ.get('ZHIPUAI_API_KEY', '')
MODEL = "glm-4.7-flash"


def build_messages():
    return [
        {"role": "user", "content": "作为一名营销专家，请为我的产品创作一个吸引人的口号"},
        {"role": "assistant", "content": "当然，要创作一个吸引人的口号，请告诉我一些关于您产品的信息"},
        {"role": "user", "content": "智谱开放平台"},
    ]


def stream_call(client):
    response = client.chat.completions.create(
        model=MODEL,
        messages=build_messages(),
        thinking={"type": "enabled"},
        stream=True,
        max_tokens=65536,
        temperature=1.0,
    )

    thinking_done = False
    for chunk in response:
        try:
            delta = chunk.choices[0].delta
        except (AttributeError, IndexError, TypeError):
            continue

        reasoning = getattr(delta, "reasoning_content", None) or getattr(
            delta, "thinking_content", None
        )
        content = getattr(delta, "content", None)

        if reasoning:
            if not thinking_done:
                print("\n=== AI 思考中 ===", flush=True)
                thinking_done = True
            print(reasoning, end="", flush=True)

        if content:
            if thinking_done:
                print("\n\n=== AI 回复 ===", flush=True)
                thinking_done = False
            print(content, end="", flush=True)

    print("\n", flush=True)


def main():
    client = ZhipuAI(api_key=API_KEY)
    try:
        stream_call(client)
    except Exception as exc:
        print(f"\n[调用异常] {exc}", flush=True)


if __name__ == "__main__":
    main()
