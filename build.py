#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
构建脚本：生成文件树、复制静态文件到 public 目录
"""

import os
import shutil
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / 'public'
CODE_EXPLORER_DIR = BASE_DIR / 'code-explorer'
WEB_GAMES_DIR = BASE_DIR / 'web-games'
FATHERS_DAY_DIR = BASE_DIR / 'fathers-day'


def copy_file(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f'  复制: {src.relative_to(BASE_DIR)} -> {dst.relative_to(BASE_DIR)}')


def copy_dir(src: Path, dst: Path, exclude_dirs=None, exclude_exts=None):
    if exclude_dirs is None:
        exclude_dirs = set()
    if exclude_exts is None:
        exclude_exts = set()

    if not src.exists():
        return

    dst.mkdir(parents=True, exist_ok=True)

    for item in src.iterdir():
        if item.name.startswith('.'):
            continue
        if item.is_dir():
            if item.name in exclude_dirs:
                continue
            copy_dir(item, dst / item.name, exclude_dirs, exclude_exts)
        elif item.is_file():
            ext = item.suffix.lower()
            if ext in exclude_exts:
                continue
            copy_file(item, dst / item.name)


def main():
    print('=' * 50)
    print('  构建 Cloudflare Pages 项目')
    print('=' * 50)
    print()

    if PUBLIC_DIR.exists():
        print(f'清理旧的 public 目录...')
        shutil.rmtree(PUBLIC_DIR)

    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    print()
    print('步骤 1: 生成文件树 JSON...')
    sys.path.insert(0, str(CODE_EXPLORER_DIR))
    from generate_filetree import get_file_tree, BASE_DIR as SCAN_DIR, OUTPUT_FILE
    tree = get_file_tree(str(BASE_DIR))
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    output_file = PUBLIC_DIR / 'file-tree.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tree, f, ensure_ascii=False, indent=2)
    print(f'  文件树已生成: {output_file.relative_to(BASE_DIR)} ({len(tree)} 个顶层项目)')

    print()
    print('步骤 2: 复制首页 index.html...')
    copy_file(CODE_EXPLORER_DIR / 'index.html', PUBLIC_DIR / 'index.html')

    print()
    print('步骤 3: 复制 web-games 目录...')
    if WEB_GAMES_DIR.exists():
        copy_dir(WEB_GAMES_DIR, PUBLIC_DIR / 'web-games')
    else:
        print('  跳过: web-games 目录不存在')

    print()
    print('步骤 4: 复制 fathers-day 目录...')
    if FATHERS_DAY_DIR.exists():
        copy_dir(FATHERS_DAY_DIR, PUBLIC_DIR / 'fathers-day')
    else:
        print('  跳过: fathers-day 目录不存在')

    print()
    print('=' * 50)
    print('  构建完成！')
    print(f'  输出目录: {PUBLIC_DIR}')
    print('=' * 50)


if __name__ == '__main__':
    main()
