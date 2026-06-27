import requests

data = requests.get("https://geekprank.com/hacker/")

with open('ht.html','w',encoding='utf-8') as f:
    f.write(data)