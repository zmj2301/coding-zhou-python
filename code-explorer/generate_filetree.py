#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成文件树 JSON，用于 Cloudflare Pages 的静态文件树 API
"""

import os
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / 'public'
OUTPUT_FILE = OUTPUT_DIR / 'file-tree.json'

ALLOWED_EXTENSIONS = {
    '.py', '.cpp', '.c', '.h', '.java', '.js', '.ts', '.tsx', '.jsx',
    '.html', '.css', '.json', '.xml', '.yaml', '.yml', '.md', '.txt',
    '.csv', '.sql', '.sh', '.bat', '.ps1', '.ini', '.cfg', '.toml',
    '.rs', '.go', '.rb', '.php', '.swift', '.kt', '.scala', '.r',
    '.lua', '.pl', '.dart', '.vue', '.svelte', '.spec',
    '.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.ico'
}

EXCLUDED_DIRS = {
    '__pycache__', '.git', '.idea', 'node_modules', 'dist', 'build',
    '.venv', 'venv', 'env', '.env', '__pycache__',
    'garden', 'output', 'release',
    '项目封面图', 'comments', 'uploads',
    '.trae', '.vscode', 'public', 'functions'
}

_theme_cache = {}


def compute_folder_theme(name, children):
    global _theme_cache
    cache_key = name
    if cache_key in _theme_cache:
        return _theme_cache[cache_key]

    ext_hue_map = {
        '.py': 210, '.md': 35, '.json': 45, '.html': 340,
        '.css': 190, '.js': 55, '.txt': 150, '.png': 270,
        '.jpg': 270, '.ico': 180, '.wav': 320, '.mp3': 320,
        '.exe': 0, '.csv': 130, '.yaml': 160, '.yml': 160,
        '.xml': 25, '.sql': 110, '.sh': 60, '.bat': 40,
    }
    hue_sum = 0
    weight_sum = 0
    for child in children:
        if child['type'] == 'file':
            ext = child.get('ext', '').lower()
            weight = 3 if ext == '.py' else (2 if ext in ('.md', '.json', '.html') else 1)
            hue_sum += ext_hue_map.get(ext, 200) * weight
            weight_sum += weight
        else:
            hue_sum += 180
            weight_sum += 0.5
    base_hue = int(hue_sum / weight_sum) if weight_sum else 210
    name_hash = sum((i + 1) * ord(c) for i, c in enumerate(name))
    hue = (base_hue + (name_hash % 50) - 25) % 360
    sat = 30 + (name_hash % 15)
    light = 58 + (name_hash % 10)
    result = f'hsl({hue}, {sat}%, {light}%)'
    _theme_cache[cache_key] = result
    return result


def get_file_tree(directory, relative_path=''):
    items = []
    try:
        entries = sorted(os.scandir(directory), key=lambda e: (not e.is_dir(), e.name.lower()))
        for entry in entries:
            name = entry.name

            if name.startswith('.') or name in EXCLUDED_DIRS:
                continue

            rel_path = os.path.join(relative_path, name) if relative_path else name
            last_modified = int(entry.stat().st_mtime * 1000)

            if entry.is_dir():
                children = get_file_tree(entry.path, rel_path)
                if children:
                    theme = compute_folder_theme(name, children)
                    items.append({
                        'name': name,
                        'type': 'directory',
                        'path': rel_path.replace('\\', '/'),
                        'themeColor': theme,
                        'lastModified': last_modified,
                        'children': children
                    })
            elif entry.is_file():
                ext = os.path.splitext(name)[1].lower()
                if ext in ALLOWED_EXTENSIONS:
                    items.append({
                        'name': name,
                        'type': 'file',
                        'path': rel_path.replace('\\', '/'),
                        'ext': ext,
                        'lastModified': last_modified
                    })
    except PermissionError:
        pass

    return items


def main():
    print(f'扫描目录: {BASE_DIR}')
    tree = get_file_tree(str(BASE_DIR))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(tree, f, ensure_ascii=False, indent=2)
    print(f'文件树已生成: {OUTPUT_FILE}')
    print(f'顶层目录数: {len(tree)}')


if __name__ == '__main__':
    main()
