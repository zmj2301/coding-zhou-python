# http://github.com/pwxcoo/chinese-xinhua
import json
import time

with open('data/idiom.json','r',encoding='utf-8') as file:
    data = json.load(file)

with open('书列表.txt','w',encoding='utf-8') as file:
    idiom = '假如给我三天光明'
    file.write(idiom + '\n')
    idiom = '假如给我三天光明2'
    file.write(idiom + '\n')