"""将 pvz 的 .psd->.png 结果同步到 public/ 和 code-explorer/ 副本目录"""
import shutil, os

src = 'e:\\coding-zhou\\Python\\web-games\\pvz_tmp\\game\\images\\interface'
dests = [
    'e:\\coding-zhou\\Python\\public\\web-games\\pvz_tmp\\game\\images\\interface',
    'e:\\coding-zhou\\Python\\code-explorer\\public\\web-games\\pvz_tmp\\game\\images\\interface',
]

for d in dests:
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(src):
        if f.endswith('.png'):
            shutil.copy(os.path.join(src, f), os.path.join(d, f))
            print(f'Copied {f} -> {d}')

print('Done')
