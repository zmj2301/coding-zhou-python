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

BASE_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = Path(__file__).resolve().parent / 'public'
CODE_EXPLORER_DIR = Path(__file__).resolve().parent
WEB_GAMES_DIR = CODE_EXPLORER_DIR / 'web-games'
FATHERS_DAY_DIR = CODE_EXPLORER_DIR / 'fathers-day'


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
    print('步骤 1: 生成文件树和项目列表 JSON...')
    sys.path.insert(0, str(CODE_EXPLORER_DIR / 'code-explorer'))
    import generate_filetree
    generate_filetree.main()

    print()
    print('步骤 2: 复制首页 index.html...')
    copy_file(CODE_EXPLORER_DIR / 'index.html', PUBLIC_DIR / 'index.html')

    print()
    print('步骤 2.1: 复制控制台 console.html...')
    console_src = CODE_EXPLORER_DIR / 'console.html'
    if console_src.exists():
        copy_file(console_src, PUBLIC_DIR / 'console.html')
    else:
        print('  跳过: console.html 不存在')

    print()
    print('步骤 2.3: 复制反馈页 feedback.html...')
    feedback_src = CODE_EXPLORER_DIR / 'feedback.html'
    if feedback_src.exists():
        copy_file(feedback_src, PUBLIC_DIR / 'feedback.html')
    else:
        print('  跳过: feedback.html 不存在')

    print()
    print('步骤 2.2: 复制 images 目录...')
    images_src = CODE_EXPLORER_DIR / 'code-explorer' / 'public' / 'images'
    if images_src.exists():
        copy_dir(images_src, PUBLIC_DIR / 'images')
    else:
        print('  跳过: images 目录不存在')

    print()
    print('步骤 2.5: 复制 changelog.json...')
    changelog_src = CODE_EXPLORER_DIR / 'changelog.json'
    if changelog_src.exists():
        copy_file(changelog_src, PUBLIC_DIR / 'changelog.json')
    else:
        print('  跳过: changelog.json 不存在')

    print()
    print('步骤 2.55: 复制 AGENTS.md 到 share 目录...')
    share_dir = PUBLIC_DIR / 'share'
    share_dir.mkdir(parents=True, exist_ok=True)
    agents_src = BASE_DIR / 'AGENTS.md'
    if agents_src.exists():
        copy_file(agents_src, share_dir / 'agents.md')
    else:
        print('  跳过: AGENTS.md 不存在')

    print()
    print('步骤 2.6: 复制 python 导航页...')
    python_src = CODE_EXPLORER_DIR / 'code-explorer' / 'python'
    if python_src.exists():
        copy_dir(python_src, PUBLIC_DIR / 'python')
    else:
        print('  跳过: python 目录不存在')

    print()
    print('步骤 2.7: 复制 project-list.json...')
    gen_src = CODE_EXPLORER_DIR / 'code-explorer' / 'public'
    project_list_src = gen_src / 'project-list.json'
    if project_list_src.exists():
        copy_file(project_list_src, PUBLIC_DIR / 'project-list.json')
    else:
        print('  跳过: project-list.json 不存在')

    print()
    print('步骤 2.7: 复制 project-trees 目录...')
    project_trees_src = gen_src / 'project-trees'
    if project_trees_src.exists():
        copy_dir(project_trees_src, PUBLIC_DIR / 'project-trees')
    else:
        print('  跳过: project-trees 目录不存在')

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
    print('步骤 5: 清理大文件（超过 5MB 的文件，Worker 不支持）...')
    for f in PUBLIC_DIR.rglob('*'):
        if not f.is_file():
            continue
        size = f.stat().st_size
        if size > 5 * 1024 * 1024:
            f.unlink()
            print(f'  删除: {f.relative_to(BASE_DIR)} ({size / 1024 / 1024:.1f} MB)')

    print()
    print('=' * 50)
    print('  构建完成！')
    print(f'  输出目录: {PUBLIC_DIR}')
    print('=' * 50)


if __name__ == '__main__':
    main()
