#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
代码浏览与执行平台 - 后端服务器
使用 Python 内置库实现，无需额外安装依赖
"""

import http.server
import json
import os
import subprocess
import sys
import urllib.parse
import mimetypes
import threading
import time
import socketserver
import socket
from pathlib import Path
import zipfile
import io
import re
import uuid
import base64
import hashlib
import secrets

# 编码设置：仅在非控制台输出时强制 UTF-8（如管道/重定向），
# 控制台输出使用系统默认编码（Windows 下为 GBK），避免中文乱码
# HTTP 响应通过 wfile.write 显式编码为 UTF-8，不受此影响
if sys.platform == 'win32':
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
if not sys.stdout.isatty():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if not sys.stderr.isatty():
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 配置
PORT = 8765
# 代码目录优先级：1) 同目录下的 code/ 文件夹 2) server.py 上级目录
# 把你的 Python 项目放到 code/ 文件夹里，或者直接把整个目录发给别人
_code_dir = Path(__file__).resolve().parent / 'code'
_parent_dir = Path(__file__).resolve().parent.parent
if _code_dir.exists() and any(_code_dir.iterdir()):
    BASE_DIR = _code_dir
elif _parent_dir.exists() and any(str(p) for p in _parent_dir.iterdir() if p.name != 'code-explorer' and not p.name.startswith('.')):
    BASE_DIR = _parent_dir
else:
    BASE_DIR = Path(__file__).resolve().parent
HOST = '0.0.0.0'

# HTML 预览时的资源路径重写
def rewrite_html_resource_paths(html_content, html_file_path):
    """
    将 HTML 中的相对路径资源引用（如 style.css、app.js、images/logo.png）
    重写为通过 /api/files/preview 加载的绝对路径，解决 iframe 预览时的资源加载问题。
    """
    try:
        text = html_content.decode('utf-8', errors='replace')
    except Exception:
        return html_content
    
    html_dir = html_file_path.parent
    
    def make_preview_url(original):
        if not original or original.startswith('/') or original.startswith('http://') or original.startswith('https://') or original.startswith('data:') or original.startswith('#') or original.startswith('mailto:'):
            return None
        try:
            full_path = (html_dir / original).resolve()
            if not str(full_path).startswith(str(BASE_DIR.resolve())):
                return None
            rel_path = str(full_path.relative_to(BASE_DIR)).replace('\\', '/')
            return '/api/files/preview?path=' + urllib.parse.quote(rel_path)
        except Exception:
            return None
    
    def replace_attr(match):
        before = match.group(1)
        quote = match.group(2)
        value = match.group(3)
        new_url = make_preview_url(value)
        if new_url:
            return f'{before}={quote}{new_url}{quote}'
        return match.group(0)
    
    text = re.sub(r'(src|href|srcset|data-src|poster|action)\s*=\s*([\'"])([^\'">]+?)\2', replace_attr, text, flags=re.IGNORECASE)
    
    def replace_style_url(match):
        value = match.group(1).strip('\'"')
        new_url = make_preview_url(value)
        if new_url:
            return f'url({new_url})'
        return match.group(0)
    
    text = re.sub(r'url\(\s*([\'"]?)([^)\'"]+?)\1\s*\)', replace_style_url, text)
    
    return text.encode('utf-8', errors='replace')

# 允许读取的文件扩展名
ALLOWED_EXTENSIONS = {
    '.py', '.cpp', '.c', '.h', '.java', '.js', '.ts', '.tsx', '.jsx',
    '.html', '.css', '.json', '.xml', '.yaml', '.yml', '.md', '.txt',
    '.csv', '.sql', '.sh', '.bat', '.ps1', '.ini', '.cfg', '.toml',
    '.rs', '.go', '.rb', '.php', '.swift', '.kt', '.scala', '.r',
    '.lua', '.pl', '.dart', '.vue', '.svelte', '.spec',
    '.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.ico'
}

# 评论功能配置 - 每个项目的评论保存在独立的 JSON 文件中
COMMENTS_DIR = Path(__file__).parent / 'comments'
UPLOADS_DIR = Path(__file__).parent / 'uploads'
LIKES_FILE = Path(__file__).parent / 'likes.json'
os.makedirs(str(COMMENTS_DIR), exist_ok=True)
os.makedirs(str(UPLOADS_DIR), exist_ok=True)
_comments_lock = threading.Lock()  # 防止多线程并发读写评论文件
_likes_lock = threading.Lock()     # 防止多线程并发读写点赞文件

# 登录认证配置
WEB_GAMES_PASSWORD = os.environ.get('CODE_EXPLORER_KEY', '')
ADMIN_PASSWORD = os.environ.get('CODE_EXPLORER_ADMINISTRATOR', '')
_sessions = {}          # token -> {'expiry': timestamp, 'is_admin': bool}
_sessions_lock = threading.Lock()
SESSION_TIMEOUT = 3600 * 24  # 24小时过期
SERVER_START_TIME = time.time()


def load_likes():
    """加载所有项目的点赞数据"""
    with _likes_lock:
        if LIKES_FILE.exists():
            try:
                return json.loads(LIKES_FILE.read_text(encoding='utf-8'))
            except Exception:
                return {}
        return {}


def save_likes(data):
    """保存点赞数据"""
    with _likes_lock:
        LIKES_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def _safe_project_filename(project_name):
    """将项目名称转为安全的文件名（替换路径分隔符和特殊字符）"""
    return project_name.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')


def _get_project_comments_file(project_name):
    """获取指定项目的评论文件路径"""
    safe_name = _safe_project_filename(project_name)
    return COMMENTS_DIR / f'{safe_name}.json'


def load_comments(project_name):
    """加载指定项目的评论，返回包含 project 和 comments 的字典"""
    file_path = _get_project_comments_file(project_name)
    with _comments_lock:
        if file_path.exists():
            try:
                data = json.loads(file_path.read_text(encoding='utf-8'))
                if isinstance(data, dict) and 'comments' in data:
                    return data
            except Exception:
                pass
    return {'project': project_name, 'comments': []}


def save_comments(project_name, data):
    """将评论数据以字典形式保存到指定项目的 JSON 文件"""
    file_path = _get_project_comments_file(project_name)
    with _comments_lock:
        file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def _get_cookie_token(headers):
    """从 Cookie 中提取 wg_token"""
    cookie_header = headers.get('Cookie', '')
    for cookie in cookie_header.split(';'):
        cookie = cookie.strip()
        if cookie.startswith('wg_token='):
            return cookie.split('=', 1)[1]
    return None


def _check_auth(headers):
    """检查请求是否携带有效 token"""
    if not WEB_GAMES_PASSWORD:
        return True  # 未设置密码，允许所有访问
    token = _get_cookie_token(headers)
    if not token:
        return False
    with _sessions_lock:
        if token in _sessions and _sessions[token]['expiry'] > time.time():
            return True
    return False


def _check_admin(headers):
    """检查请求是否携带有效管理员 token"""
    if not ADMIN_PASSWORD:
        return False  # 未设置管理员密码，不允许访问
    token = _get_cookie_token(headers)
    if not token:
        return False
    with _sessions_lock:
        if token in _sessions and _sessions[token]['expiry'] > time.time() and _sessions[token].get('is_admin'):
            return True
    return False


def _create_session(is_admin=False):
    """创建新会话，返回 token"""
    token = secrets.token_hex(32)
    with _sessions_lock:
        _sessions[token] = {'expiry': time.time() + SESSION_TIMEOUT, 'is_admin': is_admin}
        # 清理过期会话
        expired = [t for t, s in _sessions.items() if s['expiry'] <= time.time()]
        for t in expired:
            del _sessions[t]
    return token


def _destroy_session(token):
    """销毁会话"""
    with _sessions_lock:
        _sessions.pop(token, None)


def _require_auth(headers):
    """检查认证，未登录时直接发 401 并返回 True（表示已处理）"""
    if not WEB_GAMES_PASSWORD:
        return False  # 未设置密码，不需要认证
    if not _check_auth(headers):
        return True   # 需要返回 401
    return False       # 认证通过

# 排除的目录
EXCLUDED_DIRS = {
    '__pycache__', '.git', '.idea', 'node_modules', 'dist', 'build',
    '.venv', 'venv', 'env', '.env', '__pycache__',
    'garden', 'output', 'release',
    '项目封面图', 'comments', 'uploads'
}

# Python 解释器路径 - 使用 py 启动器指定 Python 3.12（有完整模块）
PYTHON_EXECUTABLE = 'py'
PYTHON_VERSION = '-3.12'


_theme_cache = {}
_file_tree_cache = None
_cache_time = 0

def compute_folder_theme(name, children):
    """根据文件夹内容计算柔和主题色 (HSL)，饱和度与亮度保持低调柔和"""
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
    """递归获取目录树结构，只显示代码/文本文件"""
    items = []
    try:
        for entry in sorted(os.scandir(directory), key=lambda e: (not e.is_dir(), e.name.lower())):
            name = entry.name
            
            # 跳过隐藏文件和排除目录
            if name.startswith('.') or name in EXCLUDED_DIRS:
                continue
            
            rel_path = os.path.join(relative_path, name) if relative_path else name
            last_modified = int(entry.stat().st_mtime * 1000)
            
            if entry.is_dir():
                children = get_file_tree(entry.path, rel_path)
                if children:  # 只添加包含文件的目录
                    theme = compute_folder_theme(name, children)
                    items.append({
                        'name': name,
                        'type': 'directory',
                        'path': rel_path,
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
                        'path': rel_path,
                        'ext': ext,
                        'lastModified': last_modified
                    })
    except PermissionError:
        pass
    
    return items


def get_language(ext):
    """根据扩展名返回语言标识"""
    lang_map = {
        '.py': 'python',
        '.cpp': 'cpp', '.c': 'c', '.h': 'c',
        '.java': 'java',
        '.js': 'javascript', '.jsx': 'javascript',
        '.ts': 'typescript', '.tsx': 'typescript',
        '.html': 'html',
        '.css': 'css',
        '.json': 'json',
        '.xml': 'xml',
        '.yaml': 'yaml', '.yml': 'yaml',
        '.md': 'markdown',
        '.sql': 'sql',
        '.sh': 'bash', '.bat': 'bash',
        '.rs': 'rust', '.go': 'go',
        '.rb': 'ruby', '.php': 'php',
        '.swift': 'swift', '.kt': 'kotlin',
        '.scala': 'scala', '.r': 'r',
        '.lua': 'lua', '.dart': 'dart',
        '.vue': 'html', '.svelte': 'html',
        '.toml': 'ini', '.ini': 'ini', '.cfg': 'ini',
        '.csv': 'plaintext', '.txt': 'plaintext',
        '.spec': 'plaintext',
    }
    return lang_map.get(ext, 'plaintext')


class CodeExplorerHandler(http.server.BaseHTTPRequestHandler):
    """HTTP 请求处理器"""

    def handle(self):
        """静默处理客户端断开连接的错误"""
        try:
            super().handle()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError, OSError):
            pass

    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{time.strftime('%H:%M:%S')}] {args[0]}")

    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def send_error_json(self, message, status=400):
        self.send_json({'error': message}, status)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip('/')  # 规范化：去掉末尾斜杠
        params = urllib.parse.parse_qs(parsed.query)
        print(f"[DEBUG] GET path='{path}'")
        
        # API 路由
        if path == '/api/files/tree':
            if _require_auth(self.headers):
                self.send_error_json('请先登录', 401)
                return
            global _file_tree_cache, _cache_time
            now = time.time()
            if _file_tree_cache is None or now - _cache_time > 300:
                _file_tree_cache = get_file_tree(str(BASE_DIR))
                _cache_time = now
            self.send_json(_file_tree_cache)
            return
        elif path == '/api/files/content':
            if _require_auth(self.headers):
                self.send_error_json('请先登录', 401)
                return
            file_path = params.get('path', [None])[0]
            if not file_path:
                self.send_error_json('缺少 path 参数')
                return
            
            full_path = BASE_DIR / file_path
            full_path = full_path.resolve()
            
            # 安全检查：确保文件在 BASE_DIR 内
            if not str(full_path).startswith(str(BASE_DIR.resolve())):
                self.send_error_json('访问被拒绝：路径越界', 403)
                return
            
            if not full_path.exists() or not full_path.is_file():
                self.send_error_json('文件不存在', 404)
                return
            
            try:
                content = full_path.read_text(encoding='utf-8', errors='replace')
                ext = os.path.splitext(file_path)[1].lower()
                self.send_json({
                    'path': file_path,
                    'name': os.path.basename(file_path),
                    'content': content,
                    'language': get_language(ext),
                    'size': full_path.stat().st_size
                })
            except Exception as e:
                self.send_error_json(f'读取文件失败: {str(e)}', 500)
            return
        elif path == '/api/files/preview':
            # 预览接口：以正确的 Content-Type 返回文件内容，供 iframe 直接渲染
            if _require_auth(self.headers):
                self.send_error_json('请先登录', 401)
                return
            file_path = params.get('path', [None])[0]
            if not file_path:
                self.send_error_json('缺少 path 参数')
                return
            full_path = BASE_DIR / file_path
            full_path = full_path.resolve()
            if not str(full_path).startswith(str(BASE_DIR.resolve())):
                self.send_error_json('访问被拒绝：路径越界', 403)
                return
            if not full_path.exists() or not full_path.is_file():
                self.send_error_json('文件不存在', 404)
                return
            ext = full_path.suffix.lower()
            content_type_map = {
                '.html': 'text/html; charset=utf-8',
                '.htm': 'text/html; charset=utf-8',
                '.svg': 'image/svg+xml',
                '.css': 'text/css; charset=utf-8',
                '.js': 'application/javascript; charset=utf-8',
                '.json': 'application/json; charset=utf-8',
                '.md': 'text/markdown; charset=utf-8',
                '.txt': 'text/plain; charset=utf-8',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.webp': 'image/webp',
                '.ico': 'image/x-icon',
            }
            ctype = content_type_map.get(ext, 'application/octet-stream')
            try:
                data = full_path.read_bytes()
            except Exception as e:
                self.send_error_json(f'读取文件失败: {str(e)}', 500)
                return
            # 对 HTML 文件进行资源路径重写，解决 iframe 预览时相对路径资源加载问题
            if ext in ('.html', '.htm'):
                data = rewrite_html_resource_paths(data, full_path)
            self.send_response(200)
            self.send_header('Content-Type', ctype)
            self.send_header('Content-Length', len(data))
            self.send_header('Cache-Control', 'no-store')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(data)
            return
        elif path == '/api/comments':
            if _require_auth(self.headers):
                self.send_error_json('请先登录', 401)
                return
            project = params.get('project', [None])[0]
            if not project:
                self.send_error_json('缺少 project 参数')
                return
            try:
                data = load_comments(project)
                self.send_json(data)
            except Exception as e:
                self.send_error_json(f'加载评论失败: {str(e)}', 500)
            return
        elif path == '/api/comments/counts':
            # 返回所有项目的评论数量
            if _require_auth(self.headers):
                self.send_error_json('请先登录', 401)
                return
            try:
                counts = {}
                if COMMENTS_DIR.exists():
                    for f in COMMENTS_DIR.glob('*.json'):
                        try:
                            data = json.loads(f.read_text(encoding='utf-8'))
                            if isinstance(data, dict) and 'project' in data and 'comments' in data:
                                counts[data['project']] = len(data['comments'])
                        except Exception:
                            pass
                self.send_json(counts)
            except Exception as e:
                self.send_error_json(f'加载评论数失败: {str(e)}', 500)
            return
        elif path == '/api/likes':
            if _require_auth(self.headers):
                self.send_error_json('请先登录', 401)
                return
            try:
                self.send_json(load_likes())
            except Exception as e:
                self.send_error_json(f'加载点赞数据失败: {str(e)}', 500)
            return
        elif path == '/api/files/search':
            if _require_auth(self.headers):
                self.send_error_json('请先登录', 401)
                return
            query = params.get('q', [''])[0].lower()
            if not query:
                self.send_json([])
                return
            
            results = []
            for root, dirs, files in os.walk(str(BASE_DIR)):
                # 过滤目录
                dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith('.')]
                
                for file in files:
                    if file.startswith('.'):
                        continue
                    ext = os.path.splitext(file)[1].lower()
                    if ext not in ALLOWED_EXTENSIONS:
                        continue
                    
                    if query in file.lower():
                        rel_path = os.path.relpath(os.path.join(root, file), str(BASE_DIR))
                        results.append({
                            'name': file,
                            'path': rel_path.replace('\\', '/'),
                            'ext': ext
                        })
            
            # 限制返回数量
            self.send_json(results[:100])
            return
        elif path == '/api/files/download':
            if _require_auth(self.headers):
                self.send_error_json('请先登录', 401)
                return
            file_path = params.get('path', [None])[0]
            if not file_path:
                self.send_error_json('缺少 path 参数')
                return

            full_path = BASE_DIR / file_path
            full_path = full_path.resolve()

            # 安全检查
            if not str(full_path).startswith(str(BASE_DIR.resolve())):
                self.send_error_json('访问被拒绝：路径越界', 403)
                return

            if not full_path.exists() or not full_path.is_dir():
                self.send_error_json('目录不存在', 404)
                return

            MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB 单文件
            MAX_TOTAL_SIZE = 200 * 1024 * 1024  # 200MB 总大小

            try:
                # 收集要打包的文件（只包含代码/文本文件）
                file_list = []
                total_size = 0
                for root, dirs, files in os.walk(str(full_path)):
                    dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith('.')]

                    for file in files:
                        if file.startswith('.'):
                            continue
                        ext = os.path.splitext(file)[1].lower()
                        if ext not in ALLOWED_EXTENSIONS:
                            continue

                        file_full = os.path.join(root, file)
                        try:
                            size = os.path.getsize(file_full)
                        except OSError:
                            continue
                        if size > MAX_FILE_SIZE:
                            continue
                        if total_size + size > MAX_TOTAL_SIZE:
                            break

                        arcname = os.path.relpath(file_full, str(full_path.parent))
                        file_list.append((file_full, arcname))
                        total_size += size

                if not file_list:
                    self.send_error_json('项目中没有可下载的代码文件', 404)
                    return

                # 创建 zip
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for file_full, arcname in file_list:
                        try:
                            zf.write(file_full, arcname)
                        except Exception as sub_e:
                            # 单个文件打包失败就跳过
                            print(f'  [warn] skip {file_full}: {sub_e}', flush=True)

                zip_data = zip_buffer.getvalue()
            except Exception as e:
                self.send_error_json(f'打包失败: {e}')
                return

            # 返回下载响应
            dir_name = full_path.name
            encoded_name = urllib.parse.quote(dir_name)
            self.send_response(200)
            self.send_header('Content-Type', 'application/zip')
            self.send_header('Content-Disposition',
                             f'attachment; filename="{encoded_name}.zip"; '
                             f'filename*=UTF-8\'\'{encoded_name}.zip')
            self.send_header('Content-Length', str(len(zip_data)))
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(zip_data)
            return
        elif path == '/api/auth-check':
            authenticated = _check_auth(self.headers)
            self.send_json({'authenticated': authenticated, 'passwordSet': bool(WEB_GAMES_PASSWORD)})
            return
        elif path == '/api/admin/dashboard':
            if not _check_admin(self.headers):
                self.send_error_json('管理员未登录', 401)
                return
            # 采集监控数据
            with _sessions_lock:
                active_sessions = sum(1 for s in _sessions.values() if s['expiry'] > time.time())
                admin_sessions = sum(1 for s in _sessions.values() if s['expiry'] > time.time() and s.get('is_admin'))
            uploaded_files = []
            if UPLOADS_DIR.exists():
                for f in UPLOADS_DIR.iterdir():
                    if f.is_file():
                        uploaded_files.append({'name': f.name, 'size': f.stat().st_size})
            comment_files = []
            if COMMENTS_DIR.exists():
                for f in COMMENTS_DIR.glob('*.json'):
                    comment_files.append({'name': f.name, 'size': f.stat().st_size})
            likes_data = {}
            if LIKES_FILE.exists():
                try:
                    likes_data = json.loads(LIKES_FILE.read_text(encoding='utf-8'))
                except:
                    likes_data = {'error': '读取失败'}
            total_files = 0
            try:
                for root, dirs, files in os.walk(str(BASE_DIR)):
                    total_files += len(files)
            except:
                pass
            uptime_seconds = int(time.time() - SERVER_START_TIME)
            uptime_str = ''
            d = uptime_seconds // 86400
            h = (uptime_seconds % 86400) // 3600
            m = (uptime_seconds % 3600) // 60
            if d: uptime_str += f'{d}天'
            if h: uptime_str += f'{h}小时'
            uptime_str += f'{m}分钟'
            self.send_json({
                'server': {
                    'uptime': uptime_str,
                    'uptime_seconds': uptime_seconds,
                    'base_dir': str(BASE_DIR),
                    'port': PORT,
                    'total_files': total_files,
                },
                'auth': {
                    'active_sessions': active_sessions,
                    'admin_sessions': admin_sessions,
                    'password_set': bool(WEB_GAMES_PASSWORD),
                    'admin_password_set': bool(ADMIN_PASSWORD),
                },
                'data': {
                    'likes_file': str(LIKES_FILE),
                    'likes_count': len(likes_data),
                    'comments_dir': str(COMMENTS_DIR),
                    'comment_files': comment_files,
                    'uploads_dir': str(UPLOADS_DIR),
                    'uploaded_files_count': len(uploaded_files),
                },
            })
            return
        else:
            # 静态文件服务
            if path == '/' or path == '':
                file_path = Path(__file__).parent / 'index.html'
            elif path.startswith('/web-games'):
                # web-games 目录在 code-explorer 的上级目录中
                safe_path = path[len('/web-games'):].lstrip('/')
                web_games_dir = (Path(__file__).parent.parent / 'web-games').resolve()
                file_path = (web_games_dir / safe_path).resolve()
                if not str(file_path).startswith(str(web_games_dir)):
                    self.send_error_json('访问被拒绝', 403)
                    return
                # 认证检查：设置密码后，非 index.html 的请求需要登录
                if safe_path and safe_path != 'index.html' and not _check_auth(self.headers):
                    # 浏览器页面访问跳转到登录页，API/图片资源请求返回 401
                    accept = self.headers.get('Accept', '')
                    if 'text/html' in accept:
                        self.send_response(302)
                        self.send_header('Location', '/web-games/')
                        self.send_cors_headers()
                        self.end_headers()
                        return
                    self.send_error_json('请先登录', 401)
                    return
            elif path.startswith('/fathers-day'):
                # fathers-day 目录在 code-explorer 的上级目录中
                safe_path = path[len('/fathers-day'):].lstrip('/')
                fd_dir = (Path(__file__).parent.parent / 'fathers-day').resolve()
                file_path = (fd_dir / safe_path).resolve()
                if not str(file_path).startswith(str(fd_dir)):
                    self.send_error_json('访问被拒绝', 403)
                    return
                # 认证检查
                if not _check_auth(self.headers):
                    accept = self.headers.get('Accept', '')
                    if 'text/html' in accept and 'application/json' not in accept:
                        self.send_response(302)
                        self.send_header('Location', '/')
                        self.send_cors_headers()
                        self.end_headers()
                        return
                    self.send_error_json('请先登录', 401)
                    return
            else:
                # 安全检查
                safe_path = path.lstrip('/')
                file_path = (Path(__file__).parent / safe_path).resolve()
                
                if not str(file_path).startswith(str(Path(__file__).parent.resolve())):
                    self.send_error_json('访问被拒绝', 403)
                    return
            
            # 如果路径是目录，尝试查找 index.html
            if file_path.exists() and file_path.is_dir():
                index_file = file_path / 'index.html'
                if index_file.exists():
                    file_path = index_file
                else:
                    self.send_error_json(f'页面未找到: {path}', 404)
                    return
            
            if file_path.exists() and file_path.is_file():
                content_type, _ = mimetypes.guess_type(str(file_path))
                if content_type is None:
                    content_type = 'application/octet-stream'
                
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_cors_headers()
                self.end_headers()
                
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                print(f"[DEBUG] 路径 '{path}' 未匹配任何路由，回退到静态文件")
                self.send_error_json(f'页面未找到: {path}', 404)
    
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip('/')  # 规范化：去掉末尾斜杠
        print(f"[DEBUG] POST path='{path}'")
        
        if path == '/api/comments':
            if _require_auth(self.headers):
                self.send_error_json('请先登录', 401)
                return
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self.send_error_json('无效的 JSON 数据')
                return

            project = data.get('project', '')
            text = data.get('text', '').strip()
            if not project or not text:
                self.send_error_json('缺少 project 或 text 参数')
                return

            comment = {
                'id': str(uuid.uuid4())[:8],
                'project': project,
                'text': text,
                'timestamp': int(time.time() * 1000),
                'image': None,
                'likes': 0
            }

            image_data = data.get('image', None)
            if image_data and isinstance(image_data, str) and ',' in image_data:
                try:
                    img_format, img_encoded = image_data.split(',', 1)
                    ext = 'png'
                    if '/jpeg' in img_format or '/jpg' in img_format:
                        ext = 'jpg'
                    elif '/gif' in img_format:
                        ext = 'gif'
                    elif '/webp' in img_format:
                        ext = 'webp'

                    os.makedirs(str(UPLOADS_DIR), exist_ok=True)
                    img_name = f"{comment['id']}_{uuid.uuid4().hex[:8]}.{ext}"
                    img_path = UPLOADS_DIR / img_name

                    with open(str(img_path), 'wb') as f:
                        f.write(base64.b64decode(img_encoded))

                    comment['image'] = f'uploads/{img_name}'
                except Exception:
                    comment['image'] = None

            # 加载项目评论数据，追加新评论，以字典形式保存
            project_data = load_comments(project)
            project_data['comments'].append(comment)
            save_comments(project, project_data)
            self.send_json(comment, 201)
            return
        elif path == '/api/comments/like':
            if _require_auth(self.headers):
                self.send_error_json('请先登录', 401)
                return
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self.send_error_json('无效的 JSON 数据')
                return

            project = data.get('project', '')
            comment_id = data.get('id', '')
            if not project or not comment_id:
                self.send_error_json('缺少 project 或 id 参数')
                return

            try:
                project_data = load_comments(project)
                found = False
                for c in project_data['comments']:
                    if c['id'] == comment_id:
                        c['likes'] = c.get('likes', 0) + 1
                        found = True
                        break
                if not found:
                    self.send_error_json('评论不存在', 404)
                    return
                save_comments(project, project_data)
                self.send_json({'success': True})
            except Exception as e:
                self.send_error_json(f'点赞失败: {str(e)}', 500)
            return
        elif path == '/api/likes':
            if _require_auth(self.headers):
                self.send_error_json('请先登录', 401)
                return
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self.send_error_json('无效的 JSON 数据')
                return
            project = data.get('project', '')
            if not project:
                self.send_error_json('缺少 project 参数')
                return
            try:
                likes = load_likes()
                likes[project] = likes.get(project, 0) + 1
                save_likes(likes)
                self.send_json({'project': project, 'likes': likes[project]})
            except Exception as e:
                self.send_error_json(f'点赞失败: {str(e)}', 500)
            return
        elif path == '/api/login':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self.send_error_json('无效的 JSON 数据')
                return
            password = data.get('password', '')
            if not WEB_GAMES_PASSWORD:
                self.send_error_json('服务器未设置密码', 500)
                return
            if password != WEB_GAMES_PASSWORD:
                self.send_error_json('密码错误', 401)
                return
            token = _create_session()
            self.send_json({'token': token})
            return
        elif path == '/api/logout':
            token = _get_cookie_token(self.headers)
            if token:
                _destroy_session(token)
            self.send_json({'success': True})
            return
        elif path == '/api/admin/login':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self.send_error_json('无效的 JSON 数据')
                return
            password = data.get('password', '')
            print(f'[ADMIN LOGIN] received="{password}" expected="{ADMIN_PASSWORD}" match={password == ADMIN_PASSWORD}', flush=True)
            if not ADMIN_PASSWORD:
                self.send_error_json('服务器未设置管理员密码', 500)
                return
            if password != ADMIN_PASSWORD:
                self.send_error_json('管理员密码错误', 401)
                return
            token = _create_session(is_admin=True)
            self.send_json({'token': token})
            return
        else:
            self.send_error_json('未找到接口', 404)


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """多线程 HTTP 服务器"""
    daemon_threads = True
    allow_reuse_address = True


def main():
    global _file_tree_cache, _cache_time
    print('=' * 55)
    print('  代码浏览与执行平台 - Code Explorer')
    print('=' * 55)
    print(f'  监听地址: http://localhost:{PORT}')
    print(f'  代码目录: {BASE_DIR}')
    print('=' * 55)
    print()
    print('  正在预加载项目列表...')
    _file_tree_cache = get_file_tree(str(BASE_DIR))
    _cache_time = time.time()
    print('  项目列表加载完成。')
    print()
    print('  在浏览器中打开上述地址即可使用。')
    print('  按 Ctrl+C 停止服务器。')
    print()
    
    print(f'  启动服务器: {HOST}:{PORT}')
    server = ThreadedHTTPServer((HOST, PORT), CodeExplorerHandler)
    print('  服务器启动成功，开始监听...')
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n服务器已停止。')
        server.shutdown()
    except Exception as e:
        print(f'  服务器异常: {type(e).__name__}: {e}')


if __name__ == '__main__':
    main()