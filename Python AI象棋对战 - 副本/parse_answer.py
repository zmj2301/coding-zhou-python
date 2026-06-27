import json

def parse_answer_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    data = json.loads(content)
    if isinstance(data, str):
        data = json.loads(data)

    board = data.get('board', [])
    analysis = data.get('analysis', [])
    print(analysis)
    print(type(board))

if __name__ == "__main__":
    parse_answer_json("answer.json")