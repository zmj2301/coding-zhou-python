#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code Explorer - 文件树生成器
扫描当前目录中的所有项目文件夹，生成 project-list.json、file-tree.json 和 project-trees/*.json
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime

# 根目录（脚本的父目录的父目录 = Python 根目录）
ROOT_DIR = Path(__file__).resolve().parent.parent
# 输出目录
OUTPUT_DIR = Path(__file__).resolve().parent / 'public'
OUTPUT_TREES_DIR = OUTPUT_DIR / 'project-trees'

# 需要跳过的目录和文件
SKIP_DIRS = {
    '.git', '.trae', '__pycache__', 'node_modules', '.venv', 'venv',
    'env', '.idea', '.vscode', '.github', 'code-explorer', 'public',
}
SKIP_FILES = {
    '.gitignore', '.replit', 'pyvenv.cfg', 'package-lock.json', 'package.json',
    'worker.ts', 'wrangler.toml', 'deploy.ps1', 'clear-cache.ps1',
    'build.py', 'download_covers.py', 'changelog.json', 'DEPLOY_CHECKLIST.md',
}

# 系统文件列表 - 这些项目没有封面图，用户不能访问
SYSTEM_DIRS = {
    'dist', 'functions', 'GitHub文件',
}

# 类型检测规则
TYPE_RULES = [
    ('web-game', lambda name, path: path.startswith('web-games/') or path.startswith('public/web-games/')),
    ('popup-preview', lambda name, path: name in ('fathers-day',)),
    ('ai', lambda name, path: 'AI' in name or 'ai' in name.lower()),
    ('game', lambda name, path: any(k in name for k in ('游戏', '象棋', '射击', '塔防', '忍者', '水果', '植物大战',
                                                         '冰火', '海龟汤', '成语接龙', '我的世界', '黑神话',
                                                         '3D', '扑克', '五子棋', '羊了个羊', '口算', '趣味',
                                                         'mc', 'MC', '僵尸', 'PVZ', 'pVz'))),
    ('tool', lambda name, path: any(k in name for k in ('工具', '查询', '识别', '纠错', '宠物', '日历', '日程',
                                                         '学习', '资料', '计算机', '连接', '摄像头', '价格',
                                                         '励志', '逗神', '管理', '公交', 'Stroop', 'stroop',
                                                         '实践', '文字转语音', '练习', '训练'))),
]

# 分类标签
CATEGORY_LABELS = {
    'game': '游戏',
    'ai': 'AI',
    'tool': '工具',
    'web-game': '网页游戏',
    'popup-preview': '弹出预览',
    'system-file': '系统文件',
    'other': '其他',
}

# 分类图标
CATEGORY_ICONS = {
    'game': '🕹️',
    'ai': '🤖',
    'tool': '🔧',
    'web-game': '🎮',
    'popup-preview': '🔗',
    'system-file': '📋',
    'other': '📁',
}

# 主题色生成
THEME_COLORS = [
    'hsl(173, 37%, 60%)', 'hsl(160, 40%, 63%)', 'hsl(170, 42%, 65%)',
    'hsl(157, 30%, 58%)', 'hsl(225, 33%, 66%)', 'hsl(220, 35%, 63%)',
    'hsl(241, 33%, 66%)', 'hsl(216, 40%, 63%)', 'hsl(183, 37%, 65%)',
    'hsl(193, 33%, 61%)', 'hsl(182, 32%, 60%)', 'hsl(200, 42%, 65%)',
    'hsl(189, 43%, 66%)', 'hsl(197, 42%, 60%)', 'hsl(245, 34%, 67%)',
    'hsl(189, 39%, 62%)', 'hsl(218, 37%, 65%)', 'hsl(268, 40%, 63%)',
    'hsl(234, 39%, 62%)', 'hsl(356, 31%, 59%)', 'hsl(352, 42%, 65%)',
    'hsl(196, 31%, 59%)', 'hsl(2, 42%, 65%)', 'hsl(322, 37%, 65%)',
    'hsl(334, 44%, 67%)', 'hsl(326, 36%, 59%)', 'hsl(105, 37%, 60%)',
    'hsl(194, 44%, 62%)', 'hsl(118, 36%, 64%)', 'hsl(181, 42%, 65%)',
    'hsl(266, 44%, 67%)', 'hsl(204, 30%, 63%)', 'hsl(154, 34%, 62%)',
    'hsl(224, 33%, 66%)', 'hsl(222, 42%, 65%)', 'hsl(196, 44%, 62%)',
    'hsl(22, 37%, 65%)', 'hsl(202, 42%, 65%)', 'hsl(226, 34%, 62%)',
    'hsl(201, 35%, 58%)', 'hsl(274, 41%, 64%)', 'hsl(210, 33%, 61%)',
    'hsl(199, 36%, 59%)', 'hsl(122, 30%, 63%)', 'hsl(236, 35%, 63%)',
    'hsl(144, 44%, 67%)', 'hsl(190, 44%, 67%)', 'hsl(211, 38%, 61%)',
    'hsl(213, 38%, 66%)', 'hsl(151, 32%, 65%)', 'hsl(309, 37%, 65%)',
    'hsl(258, 38%, 61%)', 'hsl(330, 30%, 63%)',
]


def get_project_type(name: str, path: str) -> str:
    """根据项目名称和路径判断类型"""
    if name in SYSTEM_DIRS:
        return 'system-file'
    for ptype, rule in TYPE_RULES:
        if rule(name, path):
            return ptype
    return 'other'


def get_main_file(files):
    """从文件列表中猜测主文件"""
    priorities = ['index.html', 'main.py', 'app.py', 'server.py', 'Chinese_chess.py',
                  'game.py', 'run.py', 'start.py', 'cli.py', 'GUI.py']
    for p in priorities:
        if p in files:
            return p
    py_files = [f for f in files if f.endswith('.py')]
    html_files = [f for f in files if f.endswith('.html')]
    if py_files:
        return py_files[0]
    if html_files:
        return html_files[0]
    return files[0] if files else ''


def scan_directory(dir_path: Path, base_path: str = ''):
    """扫描目录，返回文件树结构"""
    items = []
    try:
        for entry in sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            name = entry.name
            if name.startswith('.'):
                continue
            if entry.is_dir():
                children = scan_directory(entry, f"{base_path}/{name}" if base_path else name)
                if children:  # 只包含有文件的目录
                    items.append({
                        'name': name,
                        'type': 'directory',
                        'path': f"{base_path}/{name}" if base_path else name,
                        'children': children,
                    })
            elif entry.is_file():
                ext = os.path.splitext(name)[1].lower()
                items.append({
                    'name': name,
                    'type': 'file',
                    'path': f"{base_path}/{name}" if base_path else name,
                    'ext': ext,
                    'lastModified': int(entry.stat().st_mtime * 1000),
                })
    except PermissionError:
        pass
    return items


def flatten_tree(items, prefix=''):
    """将嵌套树展平为文件列表"""
    files = []
    for item in items:
        if item['type'] == 'file':
            files.append(item['path'])
        elif item['type'] == 'directory' and 'children' in item:
            files.extend(flatten_tree(item['children'], item['path']))
    return files


def update_project_list():
    """扫描所有项目文件夹，生成 project-list.json"""
    projects = []
    color_idx = 0

    # 扫描根目录中的项目文件夹
    for entry in sorted(ROOT_DIR.iterdir()):
        name = entry.name
        if not entry.is_dir():
            continue
        if name.startswith('.') or name in SKIP_DIRS:
            continue
        if name == 'code-explorer':
            continue

        rel_path = name
        # 检查是否是 web-games 下的子项目
        if name == 'web-games':
            for sub in sorted(entry.iterdir()):
                if sub.is_dir() and not sub.name.startswith('.') and sub.name not in ('shared', 'images'):
                    _add_project(sub.name, f"web-games/{sub.name}", projects, color_idx)
                    color_idx += 1
            continue

        _add_project(name, rel_path, projects, color_idx)
        color_idx += 1

    # 给 web-games/shared 和 web-games/images 也加回来（特殊处理）
    for sub_name in ('shared',):
        sub_path = ROOT_DIR / 'web-games' / sub_name
        if sub_path.is_dir():
            # 如果已经在列表中就跳过
            if any(p['path'] == f"web-games/{sub_name}" for p in projects):
                continue
            _add_project(sub_name, f"web-games/{sub_name}", projects, color_idx)
            color_idx += 1

    # 写入 project-list.json
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / 'project-list.json', 'w', encoding='utf-8') as f:
        json.dump(projects, f, ensure_ascii=False, indent=2)
    print(f"OK: 已生成 project-list.json ({len(projects)} 个项目)")


def _add_project(name, rel_path, projects, color_idx):
    """添加单个项目到列表"""
    ptype = get_project_type(name, rel_path)
    label = CATEGORY_LABELS.get(ptype, '其他')

    full_path = ROOT_DIR / rel_path
    if not full_path.exists():
        print(f"WARN: 项目路径不存在: {rel_path}")
        return

    # 扫描文件
    all_files = []
    for root, dirs, files in os.walk(full_path):
        # 跳过隐藏目录
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('__pycache__', 'node_modules')]
        for f in files:
            if f.startswith('.'):
                continue
            all_files.append(f)

    file_count = len(all_files)
    main_file = get_main_file(all_files)
    theme_color = THEME_COLORS[color_idx % len(THEME_COLORS)]

    # 获取最后修改时间
    try:
        last_modified = int(full_path.stat().st_mtime * 1000)
    except:
        last_modified = 0

    project = {
        'name': name,
        'path': rel_path,
        'type': ptype,
        'label': label,
        'desc': '',
        'mainFile': main_file,
        'fileCount': file_count,
        'lastModified': last_modified,
        'themeColor': theme_color,
    }

    # 针对不同类型的特殊字段
    if ptype == 'web-game':
        project['webGameUrl'] = f"/{rel_path}/"
    elif ptype == 'popup-preview':
        project['popupUrl'] = f"/{rel_path}/index.html"
    else:
        project['popupUrl'] = None

    # 如果子项目在同一个目录，设置标记
    if rel_path.count('/') > 0:
        project['hasSubProjects'] = False

    projects.append(project)


def update_project_trees():
    """为每个项目生成文件树"""
    # 读取项目列表
    project_list_path = OUTPUT_DIR / 'project-list.json'
    if not project_list_path.exists():
        print("FAIL: project-list.json 不存在，请先运行项目列表生成")
        return

    with open(project_list_path, 'r', encoding='utf-8') as f:
        projects = json.load(f)

    OUTPUT_TREES_DIR.mkdir(parents=True, exist_ok=True)

    # 清理不存在的项目的文件树缓存
    existing_paths = {p['path'] for p in projects}
    for tree_file in OUTPUT_TREES_DIR.glob('*.json'):
        if not tree_file.is_file():
            continue
        proj_name = tree_file.stem.replace('__', '/')
        # 检查这个项目是否还存在
        exists = False
        for p in projects:
            safe = p['path'].replace('/', '__').replace('\\', '__')
            if tree_file.stem == safe:
                exists = True
                break
        if not exists:
            tree_file.unlink()
            print(f"  删除: project-trees/{tree_file.name}")

    for project in projects:
        safe_name = project['path'].replace('/', '__').replace('\\', '__')
        tree_path = OUTPUT_TREES_DIR / f"{safe_name}.json"

        full_path = ROOT_DIR / project['path']
        if not full_path.exists():
            print(f"WARN: 项目路径不存在，跳过文件树: {project['path']}")
            if tree_path.exists():
                tree_path.unlink()
            continue

        tree = scan_directory(full_path)
        with open(tree_path, 'w', encoding='utf-8') as f:
            json.dump(tree, f, ensure_ascii=False, indent=2)

    print(f"OK: 已生成 {len(projects)} 个项目文件树")


def update_file_tree():
    """生成完整的文件树（用于搜索）"""
    all_items = []
    try:
        for entry in sorted(ROOT_DIR.iterdir()):
            name = entry.name
            if name.startswith('.'):
                continue
            if name in SKIP_DIRS:
                continue
            if entry.is_dir():
                children = scan_directory(entry, name)
                if children:
                    theme_color = 'hsl(173, 37%, 60%)'
                    try:
                        last_modified = int(entry.stat().st_mtime * 1000)
                    except:
                        last_modified = 0
                    all_items.append({
                        'name': name,
                        'type': 'directory',
                        'path': name,
                        'themeColor': theme_color,
                        'lastModified': last_modified,
                        'children': children,
                    })
    except PermissionError:
        pass

    with open(OUTPUT_DIR / 'file-tree.json', 'w', encoding='utf-8') as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)
    print(f"OK: 已生成 file-tree.json ({len(all_items)} 个顶级目录)")


def main():
    print("=== Code Explorer 文件树生成器 ===\n")
    print(f"根目录: {ROOT_DIR}")
    print(f"输出目录: {OUTPUT_DIR}\n")

    # 第一步：更新项目列表
    print("[1/3] 扫描项目文件夹...")
    update_project_list()

    # 第二步：更新项目文件树
    print("[2/3] 生成项目文件树...")
    update_project_trees()

    # 第三步：更新完整文件树
    print("[3/3] 生成完整文件树...")
    update_file_tree()

    print("\n=== 完成 ===")


if __name__ == '__main__':
    main()