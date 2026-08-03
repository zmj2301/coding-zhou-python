#!/usr/bin/env python3
"""
扫描 public/resource/ 目录，生成 resources.json 资源列表。
由 Worker 在部署前运行，或手动运行后提交。
"""
import json
import os
from pathlib import Path

RESOURCE_DIR = Path(__file__).parent / 'public' / 'resource'
OUTPUT_FILE = RESOURCE_DIR / 'resources.json'

# 分类映射：根据文件夹名自动分类
CATEGORY_MAP = {
    'python': 'Python项目',
    'game': '游戏',
    'tool': '工具',
    'web': '网页',
    'learn': '学习资料',
    'other': '其他',
}

def get_file_size_str(size_bytes: int) -> str:
    """将字节数转换为可读字符串"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def get_icon(name: str) -> str:
    """根据资源名返回 emoji 图标"""
    name_lower = name.lower()
    icon_map = {
        'python': '🐍', 'py': '🐍',
        'game': '🎮', '游戏': '🎮',
        'tool': '🔧', '工具': '🔧',
        'web': '🌐', '网页': '🌐',
        'learn': '📚', '学习': '📚',
        'data': '📊', '数据': '📊',
        'image': '🖼️', '图片': '🖼️',
        'video': '🎬', '视频': '🎬',
        'audio': '🎵', '音乐': '🎵',
        'zip': '📦', '压缩': '📦',
        'pdf': '📄', '文档': '📄',
        'ai': '🤖', '智能': '🤖',
        'chat': '💬', '聊天': '💬',
        'code': '💻', '代码': '💻',
        'paint': '🎨', '画': '🎨',
        'photo': '📷', '相机': '📷',
        'weather': '🌤️', '天气': '🌤️',
        'clock': '⏰', '闹钟': '⏰',
        'piano': '🎹', '钢琴': '🎹',
        'chess': '♟️', '象棋': '♟️',
        'tree': '🌲', '植物': '🌲',
        'zombie': '🧟', '僵尸': '🧟',
        'fruit': '🍎', '水果': '🍎',
        'sheep': '🐑', '羊': '🐑',
        'shoot': '🔫', '射击': '🔫',
        'card': '🃏', '卡牌': '🃏',
        'puzzle': '🧩', '拼图': '🧩',
        'pet': '🐾', '宠物': '🐾',
        'music': '🎵',
        'calculator': '🧮', '计算': '🧮',
        'camera': '📷',
        'desktop': '🖥️', '桌面': '🖥️',
        'write': '✍️', '手写': '✍️',
        'voice': '🗣️', '语音': '🗣️',
        'recognize': '🔍', '识别': '🔍',
        'mc': '⛏️', 'minecraft': '⛏️', '我的世界': '⛏️',
        'blackmyth': '🐉', '黑神话': '🐉',
        'wukong': '🐉', '悟空': '🐉',
    }
    for key, icon in icon_map.items():
        if key in name_lower:
            return icon
    return '📦'

def get_tags(name: str, size_str: str, is_dir: bool) -> list:
    """根据资源信息生成标签"""
    tags = []
    name_lower = name.lower()
    if is_dir:
        tags.append('文件夹')
    else:
        ext = name.rsplit('.', 1)[-1].upper() if '.' in name else ''
        if ext in ('ZIP', 'RAR', '7Z', 'TAR', 'GZ'):
            tags.append('压缩包')
        elif ext in ('EXE', 'MSI', 'DMG', 'APP'):
            tags.append('可执行')
        elif ext in ('PDF', 'DOC', 'DOCX'):
            tags.append('文档')
        elif ext in ('MP4', 'AVI', 'MKV'):
            tags.append('视频')
        elif ext in ('MP3', 'WAV', 'OGG'):
            tags.append('音频')
        elif ext in ('PNG', 'JPG', 'JPEG', 'GIF', 'SVG'):
            tags.append('图片')
        else:
            tags.append(ext if ext else '文件')
    tags.append(size_str)
    return tags

def scan_resource_dir() -> list:
    """扫描资源目录，返回资源列表"""
    resources = []
    if not RESOURCE_DIR.exists():
        return resources

    for item in sorted(RESOURCE_DIR.iterdir()):
        if item.name.startswith('.') or item.name == 'resources.json':
            continue
        if item.name == 'index.html':
            continue

        name = item.name
        is_dir = item.is_dir()

        # 计算大小
        if is_dir:
            total_size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
            file_count = sum(1 for f in item.rglob('*') if f.is_file())
            desc = f"包含 {file_count} 个文件"
        else:
            total_size = item.stat().st_size
            desc = ""

        size_str = get_file_size_str(total_size)
        icon = get_icon(name)
        tags = get_tags(name, size_str, is_dir)

        # 自动分类
        category = '其他'
        for key, cat in CATEGORY_MAP.items():
            if key in name.lower():
                category = cat
                break

        resources.append({
            'name': name,
            'displayName': name,
            'icon': icon,
            'description': desc,
            'tags': tags,
            'category': category,
            'size': total_size,
            'sizeStr': size_str,
            'isDir': is_dir,
            'fileCount': file_count if is_dir else 1,
            'path': f'/resource/{name}',
            'downloadUrl': f'/api/resources/download?path={name}',
        })

    return resources

def main():
    resources = scan_resource_dir()
    OUTPUT_FILE.write_text(json.dumps(resources, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Generated {len(resources)} resources -> {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
