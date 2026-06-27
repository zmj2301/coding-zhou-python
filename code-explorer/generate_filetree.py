#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成文件树 JSON，用于 Cloudflare Pages 的静态文件树 API
同时生成轻量级项目列表和各项目独立文件树
"""

import os
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / 'public'
OUTPUT_FILE = OUTPUT_DIR / 'file-tree.json'
PROJECT_LIST_FILE = OUTPUT_DIR / 'project-list.json'
PROJECT_TREES_DIR = OUTPUT_DIR / 'project-trees'

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

PROJECT_TYPE_KEYWORDS = {
    'game': ['游戏', '射击', '塔防', '冰火', '羊了个羊', '口算战争', 'mc农场', '我的世界', 'minecraft',
             '扑克牌', '五子棋', '成语接龙', '海龟汤', '黑神话', '悟空', '植物大战僵尸', '象棋',
             '趣味小游戏', 'Game7', '3D射击', 'stroop', '水果忍者'],
    'ai': ['AI', '人工智能', '机器学习', '模型训练', '图像识别', '手写识别', '文字转语音', 'TTS',
           '语音', '识别', 'deepseek', 'ollama', 'LLM', '微信自动回复', 'zhipu', 'agent', '生成图片'],
    'tool': ['github项目查询', '公交车查询', '天气可视化', '日程表', '计算机', '逗神文化',
             '学习资料', '实践', '摄像头', '桌面宠物', 'github', '每日励志', '单词纠错', '学习']
}

PROJECT_LABELS = {
    'game': '游戏',
    'ai': 'AI',
    'tool': '工具',
    'web-game': '网页游戏',
    'popup-preview': '节日祝福',
    'other': '其他'
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


def count_files(node):
    count = 0
    def walk(n):
        nonlocal count
        if n['type'] == 'file':
            count += 1
        if n.get('children'):
            for c in n['children']:
                walk(c)
    walk(node)
    return count


def find_main_file(node):
    if node['type'] == 'file':
        return node['name']
    if node.get('children'):
        main_patterns = ['main.py', 'index.html', 'app.py', 'Main.py', 'run.py']
        for pattern in main_patterns:
            for child in node['children']:
                if child['name'].lower() == pattern.lower():
                    return child['name']
        py_files = [c['name'] for c in node['children'] if c.get('ext') == '.py']
        if py_files:
            return py_files[0]
        html_files = [c['name'] for c in node['children'] if c.get('ext') == '.html']
        if html_files:
            return html_files[0]
        for child in node['children']:
            if child['type'] == 'directory':
                result = find_main_file(child)
                if result:
                    return result
    return ''


def classify_project(name):
    name_lower = name.lower()
    for ptype, keywords in PROJECT_TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in name_lower:
                return ptype
    return 'other'


def get_project_desc(name):
    desc_map = {
        'Python AI象棋对战': 'AI对战中国象棋，体验智能博弈的乐趣',
        'Python射击游戏': '经典射击游戏，考验你的反应速度',
        'Python植物大战僵尸': '策略塔防游戏，保卫你的花园',
        'Python 塔防游戏': '建造防御塔，抵御敌人入侵',
        '口算战争': '快速口算练习，提升数学能力',
        'Python桌面宠物': '可爱的桌面宠物，陪伴你工作学习',
        'python 天气可视化': '天气数据可视化，直观了解气象信息',
        'Python 微信自动回复AI': 'AI自动回复微信消息',
        'Python图像识别': '图像识别功能，识别各种物体',
        'Python 手写识别': '手写数字识别，体验AI的魅力',
        'python 成语接龙': '成语接龙游戏，学习中华传统文化',
        'python海龟汤': '情景推理游戏，挑战你的逻辑思维',
        'Python mc农场': '我的世界风格农场经营游戏',
        'python 我的世界': '3D沙盒游戏，自由创造世界',
        'Python 公交车查询': '公交信息查询工具',
        'Python github项目查询': 'GitHub项目搜索查询工具',
        'Python文字转语音': '文字转语音，让文字开口说话',
        'Python实践': 'Python编程实践项目集合',
        'python 日程表': '日程管理工具，高效规划时间',
        'python 计算机': '实用计算器工具',
        'python-stroop训练': 'Stroop效应认知训练',
        'python-学习资料': 'Python学习资料汇总',
        'python ai生成图片': 'AI图像生成，创造艺术作品',
        '奇奇怪怪的AI功能': '各种有趣的AI小功能',
        'Python冰火两重天': '冰火人双人冒险游戏',
        'python黑神话悟空': '黑神话悟空主题游戏',
        'Python 3D射击': '3D射击游戏，沉浸式体验',
        'python AI实战': 'AI实战项目合集',
        '每日励志语句': '每日一句励志语，充满正能量',
        '趣味小游戏': '各种有趣的小游戏合集',
        'Python水果忍者': '水果忍者切切乐',
        'python 逗神文化管理': '逗神文化管理系统',
        'Python连接摄像头': '摄像头调用与图像处理',
        'Python 单词纠错': '英文单词拼写纠错工具',
        'Python文字转语音无AI版': '无需AI的文字转语音工具',
    }
    for key in desc_map:
        if key.lower() == name.lower() or name.lower().startswith(key.lower()):
            return desc_map[key]
    return ''


def build_project_list(tree):
    projects = []
    
    for node in tree:
        if node['type'] != 'directory':
            continue
            
        if node['name'] == 'codinghou' and node.get('children'):
            for child in node['children']:
                if child['type'] == 'directory':
                    full_name = 'codinghou/' + child['name']
                    ptype = classify_project(child['name'])
                    project = {
                        'name': full_name,
                        'path': child['path'],
                        'type': ptype,
                        'label': PROJECT_LABELS.get(ptype, '其他'),
                        'desc': get_project_desc(full_name),
                        'mainFile': find_main_file(child),
                        'fileCount': count_files(child),
                        'lastModified': child.get('lastModified', 0),
                        'themeColor': child.get('themeColor', 'hsl(210, 35%, 60%)'),
                        'hasSubProjects': False
                    }
                    projects.append(project)
                    
        elif node['name'] == 'web-games' and node.get('children'):
            for child in node['children']:
                if child['type'] == 'directory':
                    project = {
                        'name': child['name'],
                        'path': child['path'],
                        'type': 'web-game',
                        'label': '网页游戏',
                        'desc': get_project_desc(child['name']) or '在浏览器中直接运行的网页游戏，无需安装',
                        'mainFile': 'index.html',
                        'fileCount': count_files(child),
                        'lastModified': child.get('lastModified', 0),
                        'themeColor': child.get('themeColor', 'hsl(210, 35%, 60%)'),
                        'webGameUrl': '/web-games/' + child['name'] + '/',
                        'hasSubProjects': False
                    }
                    projects.append(project)
                    
        else:
            ptype = classify_project(node['name'])
            is_popup = node['name'] == 'fathers-day'
            project = {
                'name': node['name'],
                'path': node['path'],
                'type': 'popup-preview' if is_popup else ptype,
                'label': '节日祝福' if is_popup else PROJECT_LABELS.get(ptype, '其他'),
                'desc': get_project_desc(node['name']),
                'mainFile': '点击查看 →' if is_popup else find_main_file(node),
                'fileCount': count_files(node),
                'lastModified': node.get('lastModified', 0),
                'themeColor': node.get('themeColor', 'hsl(340, 60%, 60%)' if is_popup else 'hsl(210, 35%, 60%)'),
                'popupUrl': '/fathers-day/index.html' if is_popup else None,
                'hasSubProjects': False
            }
            projects.append(project)
    
    projects.sort(key=lambda p: (0 if p['type'] == 'popup-preview' else 1, p['name']))
    
    return projects


def save_project_trees(tree):
    PROJECT_TREES_DIR.mkdir(parents=True, exist_ok=True)
    
    def save_tree_node(node, base_path=''):
        if node['type'] != 'directory':
            return
            
        tree_data = node.get('children', [])
        safe_name = node['path'].replace('/', '__').replace('\\', '__')
        tree_file = PROJECT_TREES_DIR / f'{safe_name}.json'
        
        with open(tree_file, 'w', encoding='utf-8') as f:
            json.dump(tree_data, f, ensure_ascii=False, separators=(',', ':'))
    
    for node in tree:
        if node['type'] == 'directory':
            if node['name'] == 'codinghou' and node.get('children'):
                for child in node['children']:
                    if child['type'] == 'directory':
                        save_tree_node(child)
            elif node['name'] == 'web-games' and node.get('children'):
                for child in node['children']:
                    if child['type'] == 'directory':
                        save_tree_node(child)
            else:
                save_tree_node(node)


def main():
    print(f'扫描目录: {BASE_DIR}')
    tree = get_file_tree(str(BASE_DIR))
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(tree, f, ensure_ascii=False, indent=2)
    print(f'完整文件树已生成: {OUTPUT_FILE}')
    print(f'  - 顶层目录数: {len(tree)}')
    print(f'  - 文件大小: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB')
    
    project_list = build_project_list(tree)
    with open(PROJECT_LIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(project_list, f, ensure_ascii=False, separators=(',', ':'))
    print(f'轻量项目列表已生成: {PROJECT_LIST_FILE}')
    print(f'  - 项目数量: {len(project_list)}')
    print(f'  - 文件大小: {PROJECT_LIST_FILE.stat().st_size / 1024:.1f} KB')
    
    save_project_trees(tree)
    tree_count = len(list(PROJECT_TREES_DIR.glob('*.json')))
    print(f'项目文件树已生成: {PROJECT_TREES_DIR}')
    print(f'  - 项目树数量: {tree_count}')


if __name__ == '__main__':
    main()
