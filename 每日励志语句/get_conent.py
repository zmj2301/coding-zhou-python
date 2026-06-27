import requests

URL = "https://space.bilibili.com/480205745/dynamic"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
}

result = requests.get(URL, headers=headers)
if result.status_code != 200:
    print("请求失败", result.status_code)
    exit()
with open("dynamic.html", "w", encoding="utf-8") as f:
    f.write(result.text)
print(result.text)