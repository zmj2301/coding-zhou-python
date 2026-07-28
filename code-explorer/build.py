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

BASE_DIR = Path(__file__).resolve().parent        # code-explorer/
PROJECT_ROOT = BASE_DIR.parent                      # E:\coding-zhou\Python
PUBLIC_DIR = BASE_DIR / 'public'                    # code-explorer/public/
WEB_GAMES_DIR = PROJECT_ROOT / 'web-games'          # 项目根/web-games
FATHERS_DAY_DIR = PROJECT_ROOT / 'fathers-day'      # 项目根/fathers-day
INDEX_HTML_SRC = PROJECT_ROOT / 'index.html'        # 项目根/index.html


def copy_file(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f'  复制: {src} -> {dst}')


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
    print('  构建 Code Explorer 项目')
    print('=' * 50)
    print()

    # 保留 ai-assistant.html、changelog.json 和 images 目录（如果已存在）
    preserved_files = {}
    for fname in ['ai-assistant.html', 'changelog.json']:
        fpath = PUBLIC_DIR / fname
        if fpath.exists():
            preserved_files[fname] = fpath.read_bytes()
            print(f'  保留: {fname}')

    # 保留 images 目录（封面图）
    preserved_images = None
    images_src = PUBLIC_DIR / 'images'
    if images_src.exists():
        import tempfile
        preserved_images = tempfile.mkdtemp()
        preserved_images_path = Path(preserved_images)
        copy_dir(images_src, preserved_images_path / 'images')
        print(f'  保留: images/ 目录 ({len(list(images_src.rglob(\"*\")))} 个文件)')

    if PUBLIC_DIR.exists():
        print(f'清理旧的 public 目录...')
        shutil.rmtree(PUBLIC_DIR)

    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    # 恢复保留的文件
    for fname, content in preserved_files.items():
        (PUBLIC_DIR / fname).write_bytes(content)
        print(f'  恢复: {fname}')

    # 恢复 images 目录
    if preserved_images:
        preserved_images_path = Path(preserved_images)
        copy_dir(preserved_images_path / 'images', PUBLIC_DIR / 'images')
        import shutil as shutil2
        shutil2.rmtree(preserved_images_path, ignore_errors=True)
        print('  恢复: images/ 目录')

    print()
    print('步骤 1: 生成文件树和项目列表 JSON...')
    sys.path.insert(0, str(BASE_DIR))
    import generate_filetree
    generate_filetree.main()

    print()
    print('步骤 2: 复制首页 index.html...')
    if INDEX_HTML_SRC.exists():
        copy_file(INDEX_HTML_SRC, PUBLIC_DIR / 'index.html')
    else:
        print(f'  跳过: index.html 不存在 ({INDEX_HTML_SRC})')

    print()
    print('步骤 2.5: 确保 changelog.json 存在...')
    changelog_src = PROJECT_ROOT / 'changelog.json'
    changelog_dst = PUBLIC_DIR / 'changelog.json'
    if changelog_src.exists() and changelog_src.resolve() != changelog_dst.resolve():
        copy_file(changelog_src, changelog_dst)
    elif changelog_dst.exists():
        print(f'  changelog.json 已在 public 目录中')
    else:
        print('  跳过: changelog.json 不存在')

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
