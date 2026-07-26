#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
下载项目封面图片到 code-explorer/public/images/covers/
"""

import os
import re
import requests
import hashlib
import time

OUTPUT_DIR = r"e:\coding-zhou\Python\code-explorer\public\images\covers"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 所有封面图片 URL 映射（英文文件名 -> URL）
image_urls = {
    # ===== 第一批：游戏类 25张 =====
    "codinghou": "https://aka.doubaocdn.com/s/dJgu1wyJBr",
    "python_ai_chess": "https://aka.doubaocdn.com/s/jZVJ1wyJBs",
    "python_pvz": "https://aka.doubaocdn.com/s/nIv61wyJBq",
    "python_tower_defense": "https://aka.doubaocdn.com/s/OPrm1wyJBr",
    "python_ice_fire": "https://aka.doubaocdn.com/s/MVB11wyJBt",
    "python_shooter": "https://aka.doubaocdn.com/s/mnM61wyJBs",
    "python_mc_farm": "https://aka.doubaocdn.com/s/wgTo1wyJBr",
    "python_black_myth": "https://aka.doubaocdn.com/s/EFUI1wyJBs",
    "python_minecraft": "https://aka.doubaocdn.com/s/gU671wyJDb",
    "math_war": "https://aka.doubaocdn.com/s/8vWp1wyJDZ",
    "ai扑克牌": "https://aka.doubaocdn.com/s/ejzL1wyJDa",
    "sheep_game": "https://aka.doubaocdn.com/s/pSDk1wyJDd",
    "python_gomoku": "https://aka.doubaocdn.com/s/oLKJ1wyJDZ",
    "python_3d_shooter": "https://aka.doubaocdn.com/s/mfUS1wyJDa",
    "python_idiom_chain": "https://aka.doubaocdn.com/s/RCSm1wyJDc",
    "web_games": "https://aka.doubaocdn.com/s/ppU31wyJDb",
    "fun_games": "https://aka.doubaocdn.com/s/O2fW1wyJDb",
    "python_fruit_ninja": "https://aka.doubaocdn.com/s/MXtn1wyJGl",
    "chinese_chess": "https://aka.doubaocdn.com/s/y8aw1wyJGk",
    "idiom_chain": "https://aka.doubaocdn.com/s/xAV41wyJGl",
    "math_war_web": "https://aka.doubaocdn.com/s/8deo1wyJGk",
    "my_world": "https://aka.doubaocdn.com/s/EK0H1wyJH9",
    "plane_war": "https://aka.doubaocdn.com/s/cyQl1wyJH7",
    "pvz_web": "https://aka.doubaocdn.com/s/HNZp1wyJH7",
    "stroop_training": "https://aka.doubaocdn.com/s/5ByM1wyJH9",

    # ===== 第二批：AI & 工具类 25张 =====
    "python_ai_practice": "https://aka.doubaocdn.com/s/Db0w1wyJ4G",
    "python_ai_image_gen": "https://aka.doubaocdn.com/s/PtB31wyJ4K",
    "python_wechat_ai": "https://aka.doubaocdn.com/s/fZ8N1wyJ4I",
    "weird_ai_tools": "https://aka.doubaocdn.com/s/N4GD1wyJ4I",
    "python_weather": "https://aka.doubaocdn.com/s/UyiL1wyJ4I",
    "python_schedule": "https://aka.doubaocdn.com/s/UPcW1wyJ4G",
    "python_bus_query": "https://aka.doubaocdn.com/s/JP1z1wyJ4H",
    "python_image_recognition": "https://aka.doubaocdn.com/s/dV551wyJ4H",
    "python_handwriting": "https://aka.doubaocdn.com/s/mKf31wyJ4v",
    "python_spell_check": "https://aka.doubaocdn.com/s/VVDP1wyJ4t",
    "python_tts_offline": "https://aka.doubaocdn.com/s/NfcW1wyJ4v",
    "python_tts_ai": "https://aka.doubaocdn.com/s/iJJI1wyJ4s",
    "python_github_query": "https://aka.doubaocdn.com/s/IdKI1wyJ4u",
    "python_calculator": "https://aka.doubaocdn.com/s/Vcet1wyJ4v",
    "python_camera": "https://aka.doubaocdn.com/s/8t7u1wyJ4s",
    "python_learning": "https://aka.doubaocdn.com/s/5pIl1wyJ4s",
    "python_community": "https://aka.doubaocdn.com/s/VgXL1wyJ4s",
    "python_practice": "https://aka.doubaocdn.com/s/8hj81wyJ5v",
    "daily_motivation": "https://aka.doubaocdn.com/s/kB7O1wyJ5y",
    "fathers_day": "https://aka.doubaocdn.com/s/iBWf1wyJ5v",
    "fathers_day_blessing": "https://aka.doubaocdn.com/s/wiO51wyJ5x",
    "code_explorer": "https://aka.doubaocdn.com/s/LvVU1wyJ6N",
    "portfolio": "https://aka.doubaocdn.com/s/Q7Bk1wyJ6N",
    "light_up_hometown": "https://aka.doubaocdn.com/s/tcgk1wyJ6c",
    "spell_check_supplement": "https://aka.doubaocdn.com/s/jsrU1wyJ6Z",
}

print(f"开始下载 {len(image_urls)} 张封面图片...")
print(f"保存目录: {OUTPUT_DIR}")
print()

success_count = 0
fail_count = 0

for name, url in image_urls.items():
    filepath = os.path.join(OUTPUT_DIR, f"{name}.jpg")
    
    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        print(f"  [跳过] {name} (已存在)")
        success_count += 1
        continue
    
    print(f"  [下载] {name} ...", end=" ")
    try:
        r = requests.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        r.raise_for_status()
        
        content_type = r.headers.get("content-type", "")
        ext = ".jpg"
        if "png" in content_type:
            ext = ".png"
        elif "webp" in content_type:
            ext = ".webp"
        
        if ext != ".jpg":
            filepath = os.path.join(OUTPUT_DIR, f"{name}{ext}")
        
        with open(filepath, "wb") as f:
            f.write(r.content)
        
        size_kb = len(r.content) / 1024
        print(f"OK ({size_kb:.1f} KB)")
        success_count += 1
    except Exception as e:
        print(f"失败: {e}")
        fail_count += 1
    
    time.sleep(0.3)  # 避免请求过快

print()
print(f"下载完成! 成功: {success_count}, 失败: {fail_count}")
print()

# 列出下载的文件
files = os.listdir(OUTPUT_DIR)
print(f"目录中的文件 ({len(files)}):")
for f in sorted(files):
    size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
    print(f"  {f} ({size/1024:.1f} KB)")
