# -*- coding: utf-8 -*-
"""从线上下载的文件剥离 Worker 注入，恢复本地源文件"""
import re, shutil, json
from pathlib import Path

TMP = Path(r'C:\Users\Administrator\AppData\Local\Temp')
ROOT = Path(r'E:\coding-zhou\Python')

def find_tmp(name):
    # git-bash /tmp 映射探测
    for cand in [TMP / name, Path(os.environ.get('TEMP', str(TMP))) / name]:
        if cand.exists():
            return cand
    raise FileNotFoundError(name)

import os
idx_tmp = find_tmp('rec_index.html')
py_tmp = find_tmp('rec_python.html')
cl_tmp = find_tmp('rec_changelog.json')

# 1) index.html: 线上文件已确认无赋值型注入（4 处均为页面自身消费代码），原样恢复
html = idx_tmp.read_text(encoding='utf-8')
assert 'enterPythonFolder' in html, '恢复的 index.html 缺少 enterPythonFolder!'

# 2) python 页同样原样恢复
pyh = py_tmp.read_text(encoding='utf-8')
assert 'projects/tree' in pyh, '恢复的 python/index.html 缺少 projects/tree!'

# 3) changelog 校验
cl = json.loads(cl_tmp.read_text(encoding='utf-8-sig'))
assert cl[0]['version'] == '2.6.7', f'changelog 首版本异常: {cl[0]["version"]}'
print(f'changelog 首版本: {cl[0]["version"]} ✓')

# 写回
(ROOT / 'index.html').write_text(html, encoding='utf-8', newline='')
(ROOT / 'code-explorer' / 'index.html').write_text(html, encoding='utf-8', newline='')
(ROOT / 'code-explorer' / 'python' / 'index.html').write_text(pyh, encoding='utf-8', newline='')
# changelog 保留原 BOM 习惯
cl_tmp_bytes = cl_tmp.read_bytes()
if not cl_tmp_bytes.startswith(b'\xef\xbb\xbf'):
    cl_tmp_bytes = b'\xef\xbb\xbf' + cl_tmp_bytes
(ROOT / 'changelog.json').write_bytes(cl_tmp_bytes)

print('写回完成:')
for p in ['index.html', 'code-explorer/index.html', 'code-explorer/python/index.html', 'changelog.json']:
    f = ROOT / p
    print(f'  {p}: {f.stat().st_size} 字节')
