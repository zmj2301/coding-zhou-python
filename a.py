import requests

API_KEY = "sk-3baca8be787969a02fbe927968ce074379a17ff4df0eb1a0"
url = "https://codingzhou.dpdns.org/api/recommend"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
data = {
    "messages": [
        {"role": "user", "content": "推荐几个Python项目"}
    ]
}
resp = requests.post(url, json=data, headers=headers)
print(resp.json()["response"])