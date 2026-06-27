def get_answer(persona, content):
    import os
    from openai import OpenAI
    # 打开网页，查看api_key
    import webbrowser
    webbrowser.open("https://platform.deepseek.com/usage")

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

answer = get_answer("你是一个打跑得快的高手，回答只有牌面值（“2,2表示出对二”）", "1+1等于几")
print(answer)
