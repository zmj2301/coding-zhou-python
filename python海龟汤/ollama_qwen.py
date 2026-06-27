from ollama import chat
import json



def get_answer(quesion,player,model):
    models = ["qwen3:0.6b","minimax-m2.1:cloud","kimi-k2.5:cloud"]
    response = chat(
        model=models[model],
        messages=[{'role': f'{player}', 'content': quesion}],
    )
    return response.message.content

anwer = get_answer('请出100个历史名人，列表格式输出','user',2)

print(anwer)