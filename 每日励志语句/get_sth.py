import requests

res = requests.get("http://open.iciba.com/dsapi/").json()
print(f"英文：{res['content']}")
print(f"中文：{res['note']}")