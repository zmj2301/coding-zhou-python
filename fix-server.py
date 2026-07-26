#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复服务器上的目录名和文件问题"""
import os
import json
import shutil

BASE = '/home/code-explorer'
PUBLIC = os.path.join(BASE, 'public')
PROJECTS_FILE = os.path.join(PUBLIC, 'project-list.json')

# 读取 project-list.json
with open(PROJECTS_FILE, encoding='utf-8') as f:
    projects = json.load(f)

# 获取服务器上实际存在的目录
actual_dirs = {}
for d in os.listdir(BASE):
    full = os.path.join(BASE, d)
    if os.path.isdir(full) and not os.path.islink(full):
        actual_dirs[d] = full

# 检查每个 project 的 path 是否有对应目录
missing = []
for p in projects:
    path = p['path'].split('/')[0]
    if path not in actual_dirs:
        missing.append(path)

print(f"缺失的目录: {missing}")

# 对于缺失的目录，创建空目录
for name in missing:
    if name in ('dist', '项目封面图'):
        # 这些不重要，跳过
        print(f"  跳过不重要目录: {name}")
        continue
    # 尝试模糊匹配
    import difflib
    matches = difflib.get_close_matches(name, list(actual_dirs.keys()), n=1, cutoff=0.4)
    if matches:
        # 创建符号链接
        src = os.path.join(BASE, matches[0])
        dst = os.path.join(BASE, name)
        if not os.path.exists(dst):
            os.symlink(src, dst)
            print(f"  链接: {name} -> {matches[0]}")
    else:
        # 创建空目录
        dst = os.path.join(BASE, name)
        os.makedirs(dst, exist_ok=True)
        print(f"  创建空目录: {name}")

# 确保 comments 和 uploads 目录存在
os.makedirs(os.path.join(BASE, 'comments'), exist_ok=True)
os.makedirs(os.path.join(BASE, 'uploads'), exist_ok=True)

# 清理不存在的项目（从 project-list.json 中移除）
valid_projects = []
for p in projects:
    path = p['path'].split('/')[0]
    full_path = os.path.join(BASE, path)
    if os.path.exists(full_path):
        valid_projects.append(p)
    else:
        print(f"  移除不存在的项目: {p['name']} ({path})")

if len(valid_projects) < len(projects):
    with open(PROJECTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(valid_projects, f, ensure_ascii=False, indent=2)
    print(f"更新 project-list.json: {len(projects)} -> {len(valid_projects)} 个项目")

# 列出最终的目录
print("\n最终目录列表:")
for d in sorted(os.listdir(BASE)):
    full = os.path.join(BASE, d)
    if os.path.isdir(full):
        print(f"  {d}/")

print("\n修复完成!")
