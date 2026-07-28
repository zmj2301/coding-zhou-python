#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import http.server
import json
import os
import subprocess
import sys
import urllib.parse
import hashlib
import hmac
import time
import base64
import tempfile
import urllib.request
import re
from pathlib import Path
from http.cookies import SimpleCookie

PORT = int(os.environ.get('PORT', 8765))
HOST = '0.0.0.0'
BASE_DIR = Path(__file__).resolve().parent / 'public'
DATA_DIR = Path(__file__).resolve().parent / 'data'

# 点赞/评论数据文件实际存放路径（与 worker.ts 保持一致）
LIKES_FILE = Path(__file__).resolve().parent / 'likes.json'
COMMENTS_DIR = Path(__file__).resolve().parent / 'comments'

# 项目根目录探测：ECS 上项目目录可能在不同层级，优先使用 PROJECTS_ROOT 环境变量
# 否则从 BASE_DIR 向上递归查找包含 project-list.json 或实际项目目录的根目录
PROJECTS_ROOT = None
if os.environ.get('PROJECTS_ROOT'):
    _pr = Path(os.environ.get('PROJECTS_ROOT')).resolve()
    if _pr.exists():
        PROJECTS_ROOT = _pr

def _find_projects_root():
    """自动探测项目根目录：优先查找 BASE_DIR 同级/父级中是否存在项目文件夹"""
    global PROJECTS_ROOT
    if PROJECTS_ROOT is not None:
        return PROJECTS_ROOT
    # 候选路径：ECS 常见部署结构
    candidates = [
        BASE_DIR,                                # public 本身
        BASE_DIR.parent,                         # code-explorer/
        BASE_DIR.parent.parent,                  # repo 根目录
        Path('/home/code-explorer/public'),      # 常见 ECS 绝对路径
        Path('/home/code-explorer'),
        Path('/opt/code-explorer/public'),
        Path('/opt/code-explorer'),
        Path('/var/www/code-explorer/public'),
        Path('/var/www/code-explorer'),
        Path('/www/code-explorer/public'),
        Path('/www/code-explorer'),
        Path('/root/code-explorer/public'),
        Path('/root/code-explorer'),
    ]
    for c in candidates:
        try:
            c = c.resolve()
            if c.exists() and c.is_dir():
                # 如果包含 project-list.json 或 project-trees 目录，认为是项目根
                if (c / 'project-list.json').exists() or (c / 'project-trees').exists():
                    PROJECTS_ROOT = c
                    return c
                # 或者包含若干 Python 项目目录（以.py 文件为特征）
                for entry in c.iterdir():
                    if entry.is_dir() and any(entry.glob('*.py')):
                        PROJECTS_ROOT = c
                        return c
        except Exception:
            continue
    # 兜底：使用 BASE_DIR
    PROJECTS_ROOT = BASE_DIR
    return PROJECTS_ROOT

_find_projects_root()

USER_PASSWORD = os.environ.get('USER_PASSWORD', '')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')
JWT_SECRET = os.environ.get('JWT_SECRET', 'default-secret-change-me')
ZHIPU_API_KEY = os.environ.get('ZHIPU_API_KEY', '')
ZHIPU_API_URL = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
ZHIPU_MODEL = 'glm-4.7-flash'
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'
AGNES_AI_API_KEY = os.environ.get('AGNES_AI_API_KEY', '')
AGNES_AI_API_URL = 'https://apihub.agnes-ai.com/v1/images/generations'

DATA_DIR.mkdir(exist_ok=True)
COMMENTS_DIR.mkdir(exist_ok=True)

def hmac_sha256(key, msg):
    return hmac.new(key.encode(), msg.encode(), hashlib.sha256).digest()

def base64url_encode(data):
    if isinstance(data, str):
        data = data.encode()
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

def base64url_decode(s):
    s += '=' * (4 - len(s) % 4)
    return base64.urlsafe_b64decode(s)

def sign_jwt(payload, secret, expires_in=604800):
    header = {'alg': 'HS256', 'typ': 'JWT'}
    now = int(time.time())
    full_payload = {**payload, 'iat': now, 'exp': now + expires_in}
    header_b64 = base64url_encode(json.dumps(header))
    payload_b64 = base64url_encode(json.dumps(full_payload))
    signing_input = f'{header_b64}.{payload_b64}'
    sig = hmac_sha256(secret, signing_input)
    sig_b64 = base64url_encode(sig)
    return f'{header_b64}.{payload_b64}.{sig_b64}'

def verify_jwt(token, secret):
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        signing_input = f'{header_b64}.{payload_b64}'
        expected_sig = hmac_sha256(secret, signing_input)
        actual_sig = base64url_decode(sig_b64)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        payload = json.loads(base64url_decode(payload_b64))
        if payload.get('exp', 0) < time.time():
            return None
        return payload
    except Exception:
        return None

def parse_cookies(cookie_header):
    cookies = {}
    if not cookie_header:
        return cookies
    for item in cookie_header.split(';'):
        parts = item.strip().split('=', 1)
        if len(parts) == 2:
            cookies[parts[0].strip()] = parts[1].strip()
    return cookies

def get_token_from_request(handler):
    cookies = parse_cookies(handler.headers.get('Cookie'))
    return cookies.get('wg_token')

def check_auth(handler):
    if not USER_PASSWORD:
        return True
    token = get_token_from_request(handler)
    if not token:
        return False
    return verify_jwt(token, JWT_SECRET) is not None

def check_admin(handler):
    if not ADMIN_PASSWORD:
        return False
    token = get_token_from_request(handler)
    if not token:
        return False
    payload = verify_jwt(token, JWT_SECRET)
    return payload is not None and payload.get('is_admin') is True

def read_json_file(filepath):
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def write_json_file(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_data_path(name):
    return DATA_DIR / f'{name}.json'


def _safe_project_filename(project_name):
    """生成安全的项目文件名（与 worker.ts 的 safeProjectName 保持一致）"""
    return re.sub(r'[\\/:*?"<>|]', '_', project_name)


def _get_comments_file(project_name):
    return COMMENTS_DIR / f'{_safe_project_filename(project_name)}.json'


def _load_likes():
    data = read_json_file(LIKES_FILE)
    return data if isinstance(data, dict) else {}


def _load_comments(project_name):
    data = read_json_file(_get_comments_file(project_name))
    if isinstance(data, dict) and isinstance(data.get('comments'), list):
        return data
    return {'project': project_name, 'comments': []}


def _save_comments(project_name, data):
    write_json_file(_get_comments_file(project_name), data)


def _load_all_comment_counts():
    """扫描 comments 目录，返回每个项目的评论数"""
    counts = {}
    if not COMMENTS_DIR.exists():
        return counts
    for f in COMMENTS_DIR.glob('*.json'):
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
            if isinstance(data, dict) and isinstance(data.get('comments'), list):
                counts[data.get('project', f.stem)] = len(data['comments'])
        except Exception:
            continue
    return counts


def scan_directory(dir_path, base_path=''):
    """扫描目录，返回文件树结构（与 generate_filetree.py 一致）"""
    items = []
    try:
        for entry in sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            name = entry.name
            if name.startswith('.'):
                continue
            if entry.is_dir():
                if name in ('__pycache__', 'node_modules', '.git', '.venv', 'venv'):
                    continue
                children = scan_directory(entry, f"{base_path}/{name}" if base_path else name)
                if children:
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


def get_project_tree(project_path):
    """获取项目文件树：优先 JSON 文件，fallback 到文件系统扫描"""
    safe_name = project_path.replace('/', '__').replace('\\', '__')
    data = read_json_file(BASE_DIR / 'project-trees' / f'{safe_name}.json')
    if data is not None:
        return data

    # Fallback：尝试多种可能的文件系统路径（包括自动探测的项目根目录）
    root = _find_projects_root()
    candidates = [
        root / project_path,                         # 探测到的项目根目录
        BASE_DIR / project_path,                     # public/ 下的项目目录
        BASE_DIR.parent / project_path,              # code-explorer/ 下的项目目录
        BASE_DIR.parent.parent / project_path,       # repo 根目录下的项目目录
    ]
    for full_path in candidates:
        try:
            full_path = full_path.resolve()
            if full_path.exists() and full_path.is_dir():
                return scan_directory(full_path)
        except Exception:
            continue

    return []


class MyHandler(http.server.BaseHTTPRequestHandler):

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'max-age=0, must-revalidate, no-store')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message, status=400):
        self.send_json({'error': message}, status)

    def set_cookie(self, name, value, max_age=604800):
        self.send_header('Set-Cookie', f'{name}={value}; Path=/; Max-Age={max_age}; HttpOnly; SameSite=Lax')

    def clear_cookie(self, name):
        self.send_header('Set-Cookie', f'{name}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax')

    def read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        return self.rfile.read(length)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if path == '/api/auth-check':
            authenticated = check_auth(self)
            return self.send_json({'authenticated': authenticated, 'passwordSet': bool(USER_PASSWORD)})

        if path == '/api/projects/list':
            data = read_json_file(BASE_DIR / 'project-list.json')
            if data:
                likes_data = _load_likes()
                comment_counts = _load_all_comment_counts()
                for p in data:
                    p_path = p.get('path', '')
                    p['likes'] = likes_data.get(p_path, 0) if isinstance(likes_data, dict) else 0
                    p['comments'] = comment_counts.get(p_path, 0)
                return self.send_json(data)
            # fallback：从项目根目录实时扫描
            root = _find_projects_root()
            projects = []
            if root.exists():
                for entry in sorted(root.iterdir()):
                    if not entry.is_dir() or entry.name.startswith('.') or entry.name in ('code-explorer', 'public', '__pycache__', 'node_modules'):
                        continue
                    if any(entry.glob('*.py')):
                        projects.append({
                            'name': entry.name,
                            'path': entry.name,
                            'type': 'other',
                            'label': '其他',
                            'desc': '',
                            'mainFile': '',
                            'fileCount': len(list(entry.rglob('*.py'))),
                            'lastModified': int(entry.stat().st_mtime * 1000),
                            'themeColor': 'hsl(200, 40%, 60%)',
                            'popupUrl': None,
                        })
            return self.send_json(projects)

        if path == '/api/projects/tree':
            project_path = qs.get('path', [''])[0]
            if not project_path:
                return self.send_json([])
            data = get_project_tree(project_path)
            return self.send_json(data)

        if path == '/api/files/tree':
            project = qs.get('project', [''])[0]
            if project:
                data = get_project_tree(project)
                return self.send_json(data)
            return self.send_json([])

        if path == '/api/ai-quota':
            return self.send_json({'usage': 0, 'remaining': 10000, 'limit': 10000, 'neuronsPerRequest': 100})

        if path == '/api/comments':
            project = qs.get('project', [''])[0]
            if not project:
                return self.send_error_json('缺少 project 参数')
            project_data = _load_comments(project)
            return self.send_json(project_data)

        if path == '/api/comments/counts':
            counts = _load_all_comment_counts()
            return self.send_json(counts)

        if path == '/api/likes':
            likes_data = _load_likes()
            return self.send_json(likes_data)

        if path == '/api/admin/dashboard':
            if not check_admin(self):
                return self.send_error_json('管理员未登录', 401)
            comment_counts = _load_all_comment_counts()
            likes_data = _load_likes()
            return self.send_json({
                'server': {'uptime': 'ECS Python Server', 'uptime_seconds': 0, 'total_files': 0, 'base_dir': '/home/code-explorer/public', 'port': PORT},
                'auth': {'password_set': bool(USER_PASSWORD), 'admin_password_set': bool(ADMIN_PASSWORD)},
                'data': {
                    'likes_count': len(likes_data),
                    'total_likes': sum(likes_data.values()) if isinstance(likes_data, dict) else 0,
                    'comment_files': len(comment_counts),
                    'total_comments': sum(comment_counts.values()),
                    'uploaded_files_count': 0,
                }
            })

        if path == '/api/health':
            return self.send_json({'status': 'ok'})

        if path == '/api/files/content':
            file_path = qs.get('path', [''])[0]
            if not file_path:
                return self.send_error_json('缺少 path 参数')
            if '..' in file_path or file_path.startswith('/'):
                return self.send_error_json('访问被拒绝：路径越界', 403)
            try:
                root = _find_projects_root()
                search_paths = [
                    root / file_path,
                    BASE_DIR.parent.parent / file_path,
                    BASE_DIR.parent / file_path,
                    BASE_DIR / file_path,
                ]
                local_path = None
                for sp in search_paths:
                    if sp.exists() and sp.is_file():
                        local_path = sp
                        break
                if not local_path:
                    return self.send_error_json('文件不存在', 404)
                content = local_path.read_text(encoding='utf-8', errors='replace')
                ext = os.path.splitext(file_path)[1].lower()
                lang_map = {'.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.html': 'html', '.css': 'css', '.json': 'json', '.md': 'markdown', '.java': 'java', '.cpp': 'cpp', '.c': 'c', '.rs': 'rust', '.go': 'go'}
                return self.send_json({
                    'path': file_path,
                    'name': os.path.basename(file_path),
                    'content': content,
                    'language': lang_map.get(ext, 'plaintext'),
                    'size': len(content.encode('utf-8'))
                })
            except FileNotFoundError:
                return self.send_error_json('文件不存在', 404)
            except Exception as e:
                return self.send_error_json(f'读取文件失败: {e}', 500)

        if path == '/api/files/search':
            query = qs.get('q', [''])[0].lower()
            if not query:
                return self.send_json([])
            tree = read_json_file(BASE_DIR / 'file-tree.json') or []
            results = []
            def search_tree(items):
                for item in items:
                    if item.get('type') == 'file' and query in item.get('name', '').lower():
                        results.append({'name': item['name'], 'path': item['path'], 'ext': item.get('ext', '')})
                    elif item.get('type') == 'directory' and item.get('children'):
                        search_tree(item['children'])
            search_tree(tree)
            return self.send_json(results[:100])

        if path == '/api/files/preview':
            file_path = qs.get('path', [''])[0]
            if not file_path:
                return self.send_error_json('缺少 path 参数')
            if '..' in file_path or file_path.startswith('/'):
                return self.send_error_json('访问被拒绝：路径越界', 403)
            try:
                root = _find_projects_root()
                search_paths = [
                    root / file_path,
                    BASE_DIR.parent.parent / file_path,
                    BASE_DIR.parent / file_path,
                    BASE_DIR / file_path,
                ]
                local_path = None
                for sp in search_paths:
                    if sp.exists() and sp.is_file():
                        local_path = sp
                        break
                if not local_path:
                    return self.send_error_json('文件不存在', 404)
                body = local_path.read_bytes()
                ext = os.path.splitext(file_path)[1].lower()
                ct_map = {'.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml'}
                content_type = ct_map.get(ext, 'application/octet-stream')
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(body)
                return
            except Exception as e:
                return self.send_error_json(f'预览失败: {e}', 500)

        if path == '/api/files/download':
            file_path = qs.get('path', [''])[0]
            if not file_path:
                return self.send_error_json('缺少 path 参数')
            try:
                root = _find_projects_root()
                search_paths = [
                    root / file_path,
                    BASE_DIR.parent.parent / file_path,
                    BASE_DIR.parent / file_path,
                    BASE_DIR / file_path,
                ]
                local_path = None
                for sp in search_paths:
                    if sp.exists() and sp.is_file():
                        local_path = sp
                        break
                if not local_path:
                    return self.send_error_json('文件不存在', 404)
                body = local_path.read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'application/octet-stream')
                self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(file_path)}"')
                self.end_headers()
                self.wfile.write(body)
                return
            except Exception as e:
                return self.send_error_json(f'下载失败: {e}', 500)

        self.send_error(404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        try:
            length = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(length) if length > 0 else b''
            body = json.loads(raw) if raw else {}
        except Exception:
            body = {}

        if path == '/api/login':
            password = body.get('password', '')
            if not USER_PASSWORD:
                return self.send_error_json('服务器未设置密码', 500)
            if password != USER_PASSWORD:
                return self.send_error_json('密码错误', 401)
            token = sign_jwt({'sub': 'user', 'is_admin': False}, JWT_SECRET)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.set_cookie('wg_token', token)
            self.end_headers()
            self.wfile.write(json.dumps({'token': token}).encode('utf-8'))
            return

        if path == '/api/logout':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.clear_cookie('wg_token')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode('utf-8'))
            return

        if path == '/api/admin/login':
            password = body.get('password', '')
            if not ADMIN_PASSWORD:
                return self.send_error_json('服务器未设置管理员密码', 500)
            if password != ADMIN_PASSWORD:
                return self.send_error_json('管理员密码错误', 401)
            token = sign_jwt({'sub': 'admin', 'is_admin': True}, JWT_SECRET)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.set_cookie('wg_token', token)
            self.end_headers()
            self.wfile.write(json.dumps({'token': token}).encode('utf-8'))
            return

        if path == '/api/admin/dashboard':
            if not check_admin(self):
                return self.send_error_json('管理员未登录', 401)
            comments_data = read_json_file(get_data_path('comments')) or {}
            likes_data = read_json_file(get_data_path('likes')) or {}
            return self.send_json({
                'server': {'uptime': 'ECS Python Server', 'uptime_seconds': 0, 'total_files': 0, 'base_dir': '/home/code-explorer/public', 'port': PORT},
                'auth': {'password_set': bool(USER_PASSWORD), 'admin_password_set': bool(ADMIN_PASSWORD)},
                'data': {
                    'likes_count': len(likes_data),
                    'total_likes': sum(likes_data.values()) if isinstance(likes_data, dict) else 0,
                    'comment_files': len(comments_data),
                    'total_comments': sum(len(v.get('comments', [])) for v in comments_data.values() if isinstance(v, dict)),
                    'uploaded_files_count': 0,
                }
            })

        if path == '/api/comments' and self.command == 'POST':
            project = body.get('project', '')
            text = (body.get('text', '') or '').strip()
            if not project or not text:
                return self.send_error_json('缺少 project 或 text 参数')
            project_data = _load_comments(project)
            comment_id = hashlib.md5(f'{time.time()}{text}'.encode()).hexdigest()[:8]
            comment = {
                'id': comment_id, 'project': project, 'text': text,
                'timestamp': int(time.time() * 1000), 'image': None, 'likes': 0
            }
            project_data['comments'].append(comment)
            _save_comments(project, project_data)
            return self.send_json(comment, 201)

        if path == '/api/comments/like' and self.command == 'POST':
            project = body.get('project', '')
            comment_id = body.get('id', '')
            if not project or not comment_id:
                return self.send_error_json('缺少 project 或 id 参数')
            project_data = _load_comments(project)
            comments = project_data.get('comments', [])
            if not comments:
                return self.send_error_json('评论不存在', 404)
            found = False
            for c in comments:
                if c['id'] == comment_id:
                    c['likes'] = c.get('likes', 0) + 1
                    found = True
                    break
            if not found:
                return self.send_error_json('评论不存在', 404)
            _save_comments(project, project_data)
            return self.send_json({'success': True})

        if path == '/api/likes' and self.command == 'POST':
            project = body.get('project', '')
            if not project:
                return self.send_error_json('缺少 project 参数')
            likes_data = _load_likes()
            likes_data[project] = likes_data.get(project, 0) + 1
            write_json_file(LIKES_FILE, likes_data)
            return self.send_json({'project': project, 'likes': likes_data[project]})

        if path == '/api/admin/clear-cache' and self.command == 'POST':
            if not check_admin(self):
                return self.send_error_json('需要管理员权限', 401)
            return self.send_json({'success': True, 'message': '缓存已清除'})

        if path == '/api/recommend':
            messages = body.get('messages', [])
            model = body.get('model', 'glm-4.7-flash')
            if not messages:
                return self.send_error_json('请输入消息', 400)
            try:
                projects = read_json_file(BASE_DIR / 'project-list.json') or []
                project_list = '\n'.join([
                    f"- {p.get('name','')} (path: {p.get('path','')}, type: {p.get('type','unknown')}, desc: {p.get('description','none')})"
                    for p in projects
                ])
                system_prompt = f"""你是一个热情友好的编程助手，名叫"小码"。你可以和用户自然地聊天、解答编程问题，也可以推荐项目。

你的性格：
- 说话语气像朋友一样自然，不要太正式
- 推荐项目时要说明推荐理由，让人觉得有说服力
- 如果用户问了具体需求，就帮他匹配最合适的项目
- 如果只是聊天，就轻松愉快地聊，不用每次都推荐项目

可用的项目列表：
{project_list}

当用户表达兴趣或需求时，推荐 3-5 个最相关的项目。推荐时在回复末尾附上 JSON 格式：
---RECOMMEND---
[{{"path": "项目路径", "reason": "推荐理由", "name": "项目名称"}}]
---END---
没有推荐需求时正常聊天，不要强行推荐。"""

                is_openrouter = '/' in model and not model.startswith('glm')

                if is_openrouter:
                    if not OPENROUTER_API_KEY:
                        return self.send_error_json('AI 功能未配置 OPENROUTER_API_KEY', 503)
                    api_url = OPENROUTER_API_URL
                    api_key = OPENROUTER_API_KEY
                    payload = {
                        'model': model,
                        'messages': [{'role': 'system', 'content': system_prompt}, *messages],
                        'temperature': 0.7,
                        'max_tokens': 800,
                        'reasoning': {'enabled': True},
                    }
                else:
                    if not ZHIPU_API_KEY:
                        return self.send_error_json('AI 功能未配置 ZHIPU_API_KEY', 503)
                    api_url = ZHIPU_API_URL
                    api_key = ZHIPU_API_KEY
                    payload = {
                        'model': ZHIPU_MODEL,
                        'messages': [{'role': 'system', 'content': system_prompt}, *messages],
                        'temperature': 0.7,
                        'max_tokens': 800,
                    }

                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
                if is_openrouter:
                    headers['HTTP-Referer'] = 'https://codingzhou.dpdns.org'
                    headers['X-Title'] = 'Code Explorer'

                req = urllib.request.Request(api_url, data=json.dumps(payload).encode(), headers=headers)
                with urllib.request.urlopen(req, timeout=60) as resp:
                    result = json.loads(resp.read())
                    choice = result.get('choices', [{}])[0]
                    msg = choice.get('message', {})
                    text = msg.get('content', '') or ''
                    reasoning = msg.get('reasoning_content', '') or ''
                    recommendations = []
                    rec_match = re.search(r'---RECOMMEND---\s*([\s\S]*?)\s*---END---', text)
                    if rec_match:
                        try:
                            rec_list = json.loads(rec_match.group(1))
                            if isinstance(rec_list, list):
                                recommendations = [r for r in rec_list if r.get('path')][:5]
                        except Exception:
                            pass
                        text = re.sub(r'---RECOMMEND---[\s\S]*?---END---', '', text).strip()
                    if not text and recommendations:
                        text = '为你推荐以下项目：'
                    elif not text:
                        text = '抱歉，AI 暂时无法生成回复，请稍后再试。'
                    return self.send_json({'success': True, 'response': text, 'reasoning': reasoning, 'recommendations': recommendations})
            except Exception as e:
                import traceback
                print(f'AI Error: {traceback.format_exc()}', file=sys.stderr)
                return self.send_error_json(f'AI 请求失败: {e}', 500)

        if path == '/api/generate-image':
            prompt = body.get('prompt', '')
            size = body.get('size', '1024x768')
            if not prompt:
                return self.send_error_json('请输入图片描述', 400)
            if not AGNES_AI_API_KEY:
                return self.send_error_json('图像生成功能未配置 AGNES_AI_API_KEY', 503)
            try:
                payload = {
                    'model': 'agnes-image-2.0-flash',
                    'prompt': prompt,
                    'size': size,
                    'extra_body': {'response_format': 'url'}
                }
                headers = {
                    'Authorization': f'Bearer {AGNES_AI_API_KEY}',
                    'Content-Type': 'application/json'
                }
                req = urllib.request.Request(AGNES_AI_API_URL, data=json.dumps(payload).encode(), headers=headers)
                with urllib.request.urlopen(req, timeout=120) as resp:
                    result = json.loads(resp.read())
                    data = result.get('data', [])
                    if data and len(data) > 0:
                        url = data[0].get('url', '')
                        if url:
                            return self.send_json({'success': True, 'url': url})
                    return self.send_error_json('图片生成失败，未返回图片 URL', 500)
            except Exception as e:
                import traceback
                print(f'Image Gen Error: {traceback.format_exc()}', file=sys.stderr)
                return self.send_error_json(f'图像生成失败: {e}', 500)

        if path == '/api/run':
            code = body.get('code', '')
            result = self.run_python_code(code)
            return self.send_json(result)

        self.send_error(404)

    def run_python_code(self, code, timeout=30):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        try:
            result = subprocess.run(
                ['python3', temp_file],
                capture_output=True, text=True, timeout=timeout,
                cwd=str(BASE_DIR)
            )
            return {'success': result.returncode == 0, 'output': result.stdout, 'error': result.stderr}
        except subprocess.TimeoutExpired:
            return {'success': False, 'output': '', 'error': f'执行超时（超过{timeout}秒）'}
        except Exception as e:
            return {'success': False, 'output': '', 'error': str(e)}
        finally:
            os.unlink(temp_file)

    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    print(f'Code Explorer 服务器启动: http://{HOST}:{PORT}')
    print(f'BASE_DIR: {BASE_DIR}')
    print(f'PROJECTS_ROOT: {_find_projects_root()}')
    print(f'USER_PASSWORD: {"已设置" if USER_PASSWORD else "未设置"}')
    print(f'ADMIN_PASSWORD: {"已设置" if ADMIN_PASSWORD else "未设置"}')
    print(f'ZHIPU_API_KEY: {"已设置" if ZHIPU_API_KEY else "未设置"}')
    with http.server.HTTPServer((HOST, PORT), MyHandler) as httpd:
        httpd.serve_forever()
