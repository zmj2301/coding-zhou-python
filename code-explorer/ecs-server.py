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
import urllib.error
import re
import threading
import collections
import uuid
import shutil
import ast
import signal
import queue
from pathlib import Path
import sqlite3
import datetime
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

def _count_python_project_dirs(d):
    """统计目录下包含 .py 文件的子目录数量（排除一些特殊目录）"""
    count = 0
    skip_names = {'public', '__pycache__', '.git', 'node_modules', '.venv', 'venv',
                  'data', 'comments', 'uploads', 'functions', 'images', 'project-trees'}
    try:
        for entry in d.iterdir():
            if not entry.is_dir():
                continue
            if entry.name.startswith('.') or entry.name in skip_names:
                continue
            if any(entry.glob('*.py')):
                count += 1
    except Exception:
        pass
    return count

def _find_projects_root():
    """自动探测项目根目录：查找包含实际 Python 项目子目录的根目录"""
    global PROJECTS_ROOT
    if PROJECTS_ROOT is not None:
        return PROJECTS_ROOT
    # 候选路径：ECS 常见部署结构（优先级：先父目录，再public）
    candidates = [
        BASE_DIR.parent,                         # code-explorer/ (实际项目所在)
        BASE_DIR.parent.parent,                  # repo 根目录
        Path('/home/code-explorer'),             # 常见 ECS 绝对路径（项目目录）
        Path('/opt/code-explorer'),
        Path('/var/www/code-explorer'),
        Path('/www/code-explorer'),
        Path('/root/code-explorer'),
        BASE_DIR,                                # public 本身（静态文件兜底）
        Path('/home/code-explorer/public'),
        Path('/opt/code-explorer/public'),
        Path('/var/www/code-explorer/public'),
        Path('/www/code-explorer/public'),
        Path('/root/code-explorer/public'),
    ]
    best = None
    best_score = -1
    for c in candidates:
        try:
            c = c.resolve()
            if not c.exists() or not c.is_dir():
                continue
            py_dir_count = _count_python_project_dirs(c)
            has_list = (c / 'project-list.json').exists()
            has_trees = (c / 'project-trees').exists()
            # 评分：Python项目目录数量权重最高
            score = py_dir_count * 10
            if has_list:
                score += 2
            if has_trees:
                score += 1
            # public 目录降权（即使有project-list.json，它也是静态资源目录）
            if c.name == 'public':
                score -= 5
            if score > best_score:
                best_score = score
                best = c
        except Exception:
            continue
    if best is not None:
        PROJECTS_ROOT = best
        return best
    # 兜底：使用 BASE_DIR
    PROJECTS_ROOT = BASE_DIR
    return PROJECTS_ROOT

_find_projects_root()

USER_PASSWORD = os.environ.get('USER_PASSWORD', '')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')
JWT_SECRET = os.environ.get('JWT_SECRET', 'default-secret-change-me')
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '').strip()
OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'

# Ollama 本地 AI 配置
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
USE_OLLAMA = os.environ.get('USE_OLLAMA', 'true').lower() in ('true', '1', 'yes')
OLLAMA_DAILY_LIMIT = int(os.environ.get('OLLAMA_DAILY_LIMIT', '9999'))

# 模型配置：根据服务器资源（2核2G）选择轻量级模型
OLLAMA_MODELS = {
    'text': {
        'model': os.environ.get('OLLAMA_TEXT_MODEL', 'qwen2.5:1.5b'),
        'name': '文本模型',
        'description': '轻量级文本优化模型，适合日常对话和代码分析',
        'type': 'text',
        'capabilities': ['text', 'chat', 'code']
    },
    'vision': {
        'model': os.environ.get('OLLAMA_VISION_MODEL', 'moondream'),
        'name': '视觉模型',
        'description': '轻量级图片识别模型，支持图片分析和描述',
        'type': 'vision',
        'capabilities': ['image', 'vision', 'ocr']
    }
}
OLLAMA_MODEL = OLLAMA_MODELS['text']['model']

# 模型内存管理：2GB服务器只能同时加载1个模型
_current_loaded_model = None
_model_last_used = 0
_model_lock = None

# 自动释放配置
MODEL_KEEP_ALIVE = int(os.environ.get('MODEL_KEEP_ALIVE', '300'))  # 模型在内存中保留秒数

# ========= 内存缓存系统（替代 Cloudflare KV） =========
class MemoryCache:
    """基于 OrderedDict 的线程安全内存缓存，支持 TTL 和 LRU 淘汰"""
    def __init__(self, max_size=1000, default_ttl=300):
        self._cache = collections.OrderedDict()
        self._timestamps = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0

    def get(self, key):
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            ts = self._timestamps.get(key, 0)
            if time.time() - ts > self._default_ttl:
                # Expired
                del self._cache[key]
                del self._timestamps[key]
                self._misses += 1
                return None
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]

    def set(self, key, value, ttl=None):
        with self._lock:
            if len(self._cache) >= self._max_size and key not in self._cache:
                # Remove oldest
                oldest = next(iter(self._cache))
                del self._cache[oldest]
                del self._timestamps[oldest]
            self._cache[key] = value
            self._timestamps[key] = time.time()
            self._cache.move_to_end(key)

    def delete(self, key):
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._timestamps[key]
                return True
            return False

    def clear(self):
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()

    def stats(self):
        with self._lock:
            total = self._hits + self._misses
            return {
                'size': len(self._cache),
                'max_size': self._max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': f"{(self._hits / total * 100):.1f}%" if total > 0 else "N/A",
            }

# 全局缓存实例
_memory_cache = MemoryCache(max_size=2000, default_ttl=300)  # 5分钟默认TTL
# AI 响应缓存（更长 TTL，减少重复计算）
_ai_cache = MemoryCache(max_size=500, default_ttl=600)  # 10分钟
# 项目列表缓存
_project_cache = MemoryCache(max_size=100, default_ttl=1800)  # 30分钟

def _get_model_lock():
    global _model_lock
    if _model_lock is None:
        import threading
        _model_lock = threading.Lock()
    return _model_lock

def _unload_current_model():
    """卸载当前加载的模型以释放内存"""
    global _current_loaded_model
    if not _current_loaded_model:
        return
    model_name = _current_loaded_model
    _current_loaded_model = None
    try:
        stop_req = urllib.request.Request(
            f'{OLLAMA_URL}/api/generate',
            data=json.dumps({
                'model': model_name,
                'prompt': '',
                'stream': False,
                'keep_alive': 0
            }).encode(),
            headers={'Content-Type': 'application/json'}
        )
        urllib.request.urlopen(stop_req, timeout=30).read()
        print(f'[Ollama] 已卸载模型: {model_name}')
        time.sleep(1)
    except Exception as e:
        print(f'[Ollama] 卸载模型异常: {e}')
        time.sleep(2)

def _ensure_model_loaded(model_name):
    """确保指定模型已加载，如果切换则卸载旧模型"""
    global _current_loaded_model, _model_last_used
    lock = _get_model_lock()
    with lock:
        now = time.time()
        if _current_loaded_model == model_name:
            _model_last_used = now
            return
        if _current_loaded_model:
            _unload_current_model()
        _current_loaded_model = model_name
        _model_last_used = now
        print(f'[Ollama] 加载模型: {model_name}')

def _cleanup_idle_model():
    """检查并释放闲置超时的模型"""
    global _current_loaded_model, _model_last_used
    if not _current_loaded_model:
        return
    if MODEL_KEEP_ALIVE <= 0:
        return
    if time.time() - _model_last_used > MODEL_KEEP_ALIVE:
        print(f'[Ollama] 模型闲置超时，自动卸载: {_current_loaded_model}')
        _unload_current_model()

def _start_model_cleanup_timer():
    """启动后台定时器，定期检查闲置模型"""
    def cleanup_loop():
        while True:
            time.sleep(60)
            try:
                _cleanup_idle_model()
            except Exception as e:
                print(f'[Ollama] 清理定时器异常: {e}')
    t = threading.Thread(target=cleanup_loop, daemon=True)
    t.start()

# 共享池配置：总可用 = CF 每日额度 + OpenRouter 每日额度 + Ollama 每日额度；池子上限 = 总可用 * ratio
CF_DAILY_LIMIT = 1000
OPENROUTER_DAILY_LIMIT = 50
AI_POOL_RATIO = 0.9
AI_POOL_TOTAL = int(os.environ.get('AI_POOL_DAILY_LIMIT', int((CF_DAILY_LIMIT + OPENROUTER_DAILY_LIMIT + (OLLAMA_DAILY_LIMIT if USE_OLLAMA else 0)) * AI_POOL_RATIO)))


def init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(DATA_DIR / 'users.db'))
    db.row_factory = sqlite3.Row
    db.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        created_at INTEGER NOT NULL,
        last_login INTEGER
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL DEFAULT '',
        messages TEXT NOT NULL DEFAULT '[]',
        created_at INTEGER NOT NULL,
        updated_at INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS bookmarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        project_path TEXT NOT NULL,
        project_name TEXT NOT NULL,
        project_icon TEXT DEFAULT '',
        created_at INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(user_id, project_path)
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS recent_visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        project_path TEXT NOT NULL,
        project_name TEXT NOT NULL,
        project_icon TEXT DEFAULT '',
        visited_at INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(user_id, project_path)
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        project_path TEXT NOT NULL,
        created_at INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(user_id, project_path)
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS ai_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        date TEXT NOT NULL,
        count INTEGER NOT NULL DEFAULT 0,
        last_active INTEGER,
        UNIQUE(user_id, date)
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        key TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL DEFAULT '',
        desc TEXT DEFAULT '',
        daily_limit INTEGER NOT NULL DEFAULT 0,
        expires_at INTEGER,
        created_at INTEGER NOT NULL,
        last_used_at INTEGER,
        is_active INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    # 迁移：旧表补新列
    try:
        cols = [r[1] for r in db.execute("PRAGMA table_info(api_keys)").fetchall()]
        if 'desc' not in cols:
            db.execute("ALTER TABLE api_keys ADD COLUMN desc TEXT DEFAULT ''")
        if 'daily_limit' not in cols:
            db.execute("ALTER TABLE api_keys ADD COLUMN daily_limit INTEGER NOT NULL DEFAULT 0")
        if 'expires_at' not in cols:
            db.execute("ALTER TABLE api_keys ADD COLUMN expires_at INTEGER")
        db.commit()
    except Exception as e:
        print(f'[init_db] api_keys 迁移跳过: {e}', file=sys.stderr)
    db.execute('''CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        user_id INTEGER,
        type TEXT NOT NULL DEFAULT 'other',
        content TEXT NOT NULL,
        rating INTEGER NOT NULL DEFAULT 0,
        project TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'new',
        created_at INTEGER NOT NULL,
        updated_at INTEGER NOT NULL DEFAULT 0
    )''')
    try:
        cols = [r[1] for r in db.execute("PRAGMA table_info(feedback)").fetchall()]
        if 'updated_at' not in cols:
            db.execute("ALTER TABLE feedback ADD COLUMN updated_at INTEGER NOT NULL DEFAULT 0")
        db.commit()
    except Exception as e:
        print(f'[init_db] feedback 迁移跳过: {e}', file=sys.stderr)
    db.execute('''CREATE TABLE IF NOT EXISTS feedback_replies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        feedback_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        user_id INTEGER,
        content TEXT NOT NULL,
        is_admin INTEGER NOT NULL DEFAULT 0,
        created_at INTEGER NOT NULL,
        FOREIGN KEY (feedback_id) REFERENCES feedback(id) ON DELETE CASCADE
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS scratch_projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        filename TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        created_at INTEGER NOT NULL,
        updated_at INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    db.commit()
    # 强制重置管理员密码（每次启动都生效）
    admin_id_row = db.execute("SELECT id FROM users WHERE username = ?", ('zmj2013',)).fetchone()
    h, s = hash_password('ZHOUmj32842510*')
    if admin_id_row:
        db.execute("UPDATE users SET password_hash=?, salt=? WHERE username=?", (h, s, 'zmj2013'))
        print(f'[init_db] 管理员密码已重置: zmj2013', file=sys.stderr)
    else:
        db.execute("INSERT INTO users (username, password_hash, salt, role, created_at) VALUES (?, ?, ?, 'admin', ?)",
                   ('zmj2013', h, s, int(time.time())))
        print(f'[init_db] 管理员账号已创建: zmj2013', file=sys.stderr)
    db.commit()
    db.close()


def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16).hex()
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return h, salt


def verify_password(password, password_hash, salt):
    h, _ = hash_password(password, salt)
    return h == password_hash


def get_db():
    db = sqlite3.connect(str(DATA_DIR / 'users.db'))
    db.row_factory = sqlite3.Row
    return db


def get_user_by_username(username):
    db = get_db()
    try:
        cur = db.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        db.close()


def get_user_by_id(user_id):
    db = get_db()
    try:
        cur = db.execute("SELECT id, username, role, created_at, last_login FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        db.close()


# 代码执行相关配置
RUNS_DIR = Path('/tmp/code-explorer-runs')
VENV_CACHE_DIR = Path('/tmp/code-explorer-venvs')
RUN_AS_USER = os.environ.get('RUN_AS_USER', '')
DEFAULT_TIMEOUT = 60
MAX_TIMEOUT = 300
MAX_CONCURRENT_RUNS = 10
MAX_OUTPUT_SIZE = 1024 * 1024  # 1MB

DATA_DIR.mkdir(exist_ok=True)
COMMENTS_DIR.mkdir(exist_ok=True)
RUNS_DIR.mkdir(exist_ok=True, parents=True)
VENV_CACHE_DIR.mkdir(exist_ok=True, parents=True)

# ==================== 代码执行：进程管理 ====================
active_processes = {}
processes_lock = threading.Lock()

# Python 标准库模块集合（3.8+常见）
STDLIB_MODULES = {
    'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio',
    'asyncore', 'atexit', 'audioop', 'base64', 'bdb', 'binascii',
    'binhex', 'bisect', 'builtins', 'bz2', 'calendar', 'cgi', 'cgitb',
    'chunk', 'cmath', 'cmd', 'code', 'codecs', 'codeop', 'collections',
    'colorsys', 'compileall', 'concurrent', 'configparser', 'contextlib',
    'contextvars', 'copy', 'copyreg', 'cProfile', 'crypt', 'csv',
    'ctypes', 'curses', 'dataclasses', 'datetime', 'dbm', 'decimal',
    'difflib', 'dis', 'distutils', 'doctest', 'email', 'encodings',
    'enum', 'errno', 'faulthandler', 'fcntl', 'filecmp', 'fileinput',
    'fnmatch', 'formatter', 'fractions', 'ftplib', 'functools', 'gc',
    'getopt', 'getpass', 'gettext', 'glob', 'grp', 'gzip', 'hashlib',
    'heapq', 'hmac', 'html', 'http', 'idlelib', 'imaplib', 'imghdr',
    'imp', 'importlib', 'inspect', 'io', 'ipaddress', 'itertools',
    'json', 'keyword', 'lib2to3', 'linecache', 'locale', 'logging',
    'lzma', 'mailbox', 'mailcap', 'marshal', 'math', 'mimetypes',
    'mmap', 'modulefinder', 'multiprocessing', 'netrc', 'nis', 'nntplib',
    'numbers', 'operator', 'optparse', 'os', 'ossaudiodev', 'parser',
    'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil',
    'platform', 'plistlib', 'poplib', 'posix', 'posixpath', 'pprint',
    'profile', 'pstats', 'pty', 'pwd', 'py_compile', 'pyclbr',
    'pydoc', 'queue', 'quopri', 'random', 're', 'readline', 'reprlib',
    'resource', 'rlcompleter', 'runpy', 'sched', 'secrets', 'select',
    'selectors', 'shelve', 'shlex', 'shutil', 'signal', 'site',
    'smtpd', 'smtplib', 'sndhdr', 'socket', 'socketserver', 'spwd',
    'sqlite3', 'sre_compile', 'sre_constants', 'sre_parse', 'ssl',
    'stat', 'statistics', 'string', 'stringprep', 'struct', 'subprocess',
    'sunau', 'symtable', 'sys', 'sysconfig', 'syslog', 'tabnanny',
    'tarfile', 'telnetlib', 'tempfile', 'termios', 'test', 'textwrap',
    'threading', 'time', 'timeit', 'tkinter', 'token', 'tokenize',
    'trace', 'traceback', 'tracemalloc', 'tty', 'turtle', 'turtledemo',
    'types', 'typing', 'unicodedata', 'unittest', 'urllib', 'uu',
    'uuid', 'venv', 'warnings', 'wave', 'weakref', 'webbrowser',
    'winreg', 'winsound', 'wsgiref', 'xdrlib', 'xml', 'xmlrpc',
    'zipapp', 'zipfile', 'zipimport', 'zlib', '_thread',
    '__future__', 'pkg_resources', 'setuptools', 'pip',
}

# 需要图形界面（显示器）的模块 - 在无头服务器上无法正常运行
GUI_MODULES = {
    'turtle', 'tkinter', 'turtledemo',  # 标准库 GUI
    'pygame', 'pyglet', 'arcade',  # 游戏/图形库
    'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'PyQt4', 'pyside',  # Qt GUI
    'wx', 'wxPython', 'wxasync',  # wxPython
    'kivy', 'tkinter',  # 其他 GUI 框架
    'gtk', 'gi',  # GTK
    'Tkinter',  # Python 2 风格
    'pygame',  # 游戏开发
    'pyautogui',  # GUI 自动化（需要显示器）
    'pynput',  # 输入监控（在无头环境可能失败）
    'pyscreeze', 'pygetwindow', 'PyRect', 'PyScreeze',  # pyautogui 依赖
    'mouse', 'keyboard',  # 输入模拟
    'matplotlib',  # 注意：matplotlib 可以使用 Agg 后端非交互式运行，只警告不阻止
}

# 在无头环境中完全无法运行的 GUI 模块（检测到直接提示无法运行）
GUI_MODULES_BLOCKING = {
    'turtle', 'tkinter', 'turtledemo', 'Tkinter',
    'pygame', 'pyglet', 'arcade',
    'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'PyQt4', 'pyside',
    'wx', 'wxPython', 'kivy',
    'pyautogui', 'pyscreeze', 'pygetwindow',
}

IMPORT_TO_PIP = {
    'cv2': 'opencv-python',
    'PIL': 'Pillow',
    'yaml': 'pyyaml',
    'sklearn': 'scikit-learn',
    'bs4': 'beautifulsoup4',
    'requests': 'requests',
    'numpy': 'numpy',
    'pandas': 'pandas',
    'matplotlib': 'matplotlib',
    'flask': 'flask',
    'django': 'django',
    'pygame': 'pygame',
    'torch': 'torch',
    'tensorflow': 'tensorflow',
    'openai': 'openai',
    'wx': 'wxPython',
    'win32api': 'pywin32',
    'win32con': 'pywin32',
    'win32gui': 'pywin32',
    'serial': 'pyserial',
    'dotenv': 'python-dotenv',
    'jwt': 'pyjwt',
    'bcrypt': 'bcrypt',
    'Crypto': 'pycryptodome',
    'telegram': 'python-telegram-bot',
    'discord': 'discord.py',
    'svgwrite': 'svgwrite',
    'cairosvg': 'cairosvg',
    'imageio': 'imageio',
    'scipy': 'scipy',
    'seaborn': 'seaborn',
    'plotly': 'plotly',
    'bokeh': 'bokeh',
    'alive_progress': 'alive-progress',
    'tqdm': 'tqdm',
    'colorama': 'colorama',
    'termcolor': 'termcolor',
    'rich': 'rich',
    'click': 'click',
    'typer': 'typer',
    'fastapi': 'fastapi',
    'uvicorn': 'uvicorn',
    'aiohttp': 'aiohttp',
    'httpx': 'httpx',
    'pymongo': 'pymongo',
    'redis': 'redis',
    'psycopg2': 'psycopg2-binary',
    'pymysql': 'pymysql',
    'sqlalchemy': 'sqlalchemy',
    'jinja2': 'jinja2',
    'markdown': 'markdown',
    'bleach': 'bleach',
    'feedparser': 'feedparser',
    'praw': 'praw',
    'twilio': 'twilio',
    'stripe': 'stripe',
    'paypalrestsdk': 'paypalrestsdk',
    'pdfplumber': 'pdfplumber',
    'PyPDF2': 'pypdf2',
    'fitz': 'pymupdf',
    'docx': 'python-docx',
    'openpyxl': 'openpyxl',
    'xlrd': 'xlrd',
    'xlwt': 'xlwt',
    'csv': None,  # 标准库
}


def detect_imports(code):
    imports = set()
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_level = alias.name.split('.')[0]
                    imports.add(top_level)
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.level == 0:
                    top_level = node.module.split('.')[0]
                    imports.add(top_level)
    except SyntaxError:
        pass
    third_party = set()
    for imp in imports:
        if imp not in STDLIB_MODULES and not imp.startswith('_'):
            pip_name = IMPORT_TO_PIP.get(imp)
            if pip_name is not None:
                third_party.add(pip_name)
            else:
                third_party.add(imp)
    return third_party


def get_all_imports(code):
    """获取代码中所有顶层导入的模块名（包括标准库和第三方）"""
    imports = set()
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_level = alias.name.split('.')[0]
                    imports.add(top_level)
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.level == 0:
                    top_level = node.module.split('.')[0]
                    imports.add(top_level)
    except SyntaxError:
        pass
    return imports


def detect_gui_modules(code):
    """检测代码中是否使用了需要图形界面的模块
    返回 (blocking_modules, warning_modules) 元组：
    - blocking_modules: 完全无法在无头环境运行的模块（如 turtle, tkinter）
    - warning_modules: 可以安装但可能无法显示图形的模块（如 pygame, matplotlib）
    """
    imports = get_all_imports(code)
    blocking = set()
    warning = set()
    for imp in imports:
        if imp in GUI_MODULES_BLOCKING:
            blocking.add(imp)
        elif imp in GUI_MODULES:
            warning.add(imp)
    return blocking, warning


def find_gui_import_locations(code, file_label='<unknown>'):
    """扫描代码，定位 GUI 模块的 import 语句所在行号
    返回 dict: {模块名: [(file_label, line_no, line_text), ...]}
    """
    locations = {}
    # 匹配 import xxx / from xxx import yyy
    import re
    # 形式1: import turtle / import turtle, tkinter
    pat1 = re.compile(r'^\s*import\s+([\w\.,\s]+?)(?:\s+as\s+\w+)?\s*(?:#.*)?$')
    # 形式2: from turtle import position
    pat2 = re.compile(r'^\s*from\s+([\w\.]+)\s+import\s+.*?(?:\s+as\s+\w+)?\s*(?:#.*)?$')

    all_gui = GUI_MODULES_BLOCKING | GUI_MODULES

    for lineno, raw_line in enumerate(code.splitlines(), start=1):
        line = raw_line
        # 检查 import xxx 形式
        m1 = pat1.match(line)
        if m1:
            names = [n.strip().split('.')[0] for n in m1.group(1).split(',')]
            for n in names:
                if n in all_gui:
                    locations.setdefault(n, []).append((file_label, lineno, raw_line.strip()))
        # 检查 from xxx import yyy 形式
        m2 = pat2.match(line)
        if m2:
            n = m2.group(1).strip().split('.')[0]
            if n in all_gui:
                locations.setdefault(n, []).append((file_label, lineno, raw_line.strip()))
    return locations


def format_gui_locations_report(gui_locations, file_count=0, total_files=0):
    """格式化 GUI 模块位置信息为可读的报告"""
    if not gui_locations:
        return ''
    lines = ['\n\n【具体位置】:']
    for mod, locs in sorted(gui_locations.items()):
        # 合并同一文件中的多行
        files_seen = set()
        for file_label, lineno, line_text in locs:
            unique = (file_label, lineno)
            if unique in files_seen:
                continue
            files_seen.add(unique)
            lines.append(f'  • {file_label} 第 {lineno} 行: {line_text}')
    if total_files > 1:
        lines.append(f'\n（共扫描了 {total_files} 个 .py 文件）')
    return '\n'.join(lines)


def check_stl_module_available(python_bin, module_name):
    """检查标准库模块是否可用（某些模块如 tkinter/turtle 在编译 Python 时可能未包含）"""
    try:
        result = subprocess.run(
            [str(python_bin), '-c', f'import {module_name}'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def _find_system_python_for_venv():
    """为新建 venv 寻找一个可用的系统 Python 解释器。

    优先级：
    1. /usr/local/bin/python3.{9..13} / python3.{9..13}（编译安装的新版）
    2. /usr/bin/python3.{9..13}
    3. 兜底：当前进程用的 Python（sys.executable），保证 ecs-server 仍能工作

    返回 (python_executable_str, version_tag)
    version_tag 是形如 'py310'/'py36' 的标识，用于把 venv 缓存按版本隔离
    """
    candidates = []
    # 优先看 /usr/local/bin（源码/altinstall 通常装这里），再 /usr/bin
    for base in ('/usr/local/bin', '/usr/bin'):
        for minor in (13, 12, 11, 10, 9):
            candidates.append(f'{base}/python3.{minor}')
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            try:
                r = subprocess.run(
                    [c, '-c', 'import sys; print("%d.%d" % sys.version_info[:2])'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    universal_newlines=True, timeout=5
                )
                if r.returncode == 0:
                    ver = r.stdout.strip()
                    major, minor = ver.split('.')
                    tag = f'py{major}{minor}'
                    return c, tag
            except Exception:
                continue
    # 兜底
    fallback = sys.executable
    try:
        r = subprocess.run(
            [fallback, '-c', 'import sys; print("%d.%d" % sys.version_info[:2])'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, timeout=5
        )
        ver = (r.stdout.strip() if r.returncode == 0 else '0.0')
    except Exception:
        ver = '0.0'
    try:
        major, minor = ver.split('.')
        tag = f'py{major}{minor}'
    except Exception:
        tag = 'pyXX'
    return fallback, tag


def get_venv_path(project_key):
    """生成 venv 目录路径。按 project_key + Python 版本 tag 隔离缓存。

    这样在服务器升级 Python（比如从 3.6 升到 3.10）后：
    - 旧 venv（用 3.6 创建的）继续存在，但不会被误用
    - 新 venv 用新 Python 创建，避免老 venv 里 pip/wheel 不兼容
    """
    venv_hash = hashlib.md5(project_key.encode()).hexdigest()[:12]
    return VENV_CACHE_DIR / f'venv-{venv_hash}'


def _find_python_bin(venv_path):
    """在虚拟环境中查找 Python 可执行文件，兼容不同系统"""
    if os.name == 'nt':
        candidates = [venv_path / 'Scripts' / 'python.exe', venv_path / 'python.exe']
    else:
        candidates = [
            venv_path / 'bin' / 'python3',
            venv_path / 'bin' / 'python',
        ]
    for c in candidates:
        if c.exists():
            return c
    # 兜底：返回最可能的路径
    return candidates[0]


def ensure_venv(project_key, sse_callback=None, heartbeat_callback=None):
    """为指定项目键创建（或复用）虚拟环境。

    关键变化：用更高版本的系统 Python（如 3.10）创建 venv，
    以支持 Python 3.9+ 的 PEP 585 内置泛型、3.10+ 的 TypeAlias 等新语法。
    """
    # 选 Python 时把版本 tag 混进 key，让不同 Python 版本的 venv 缓存隔离
    system_python, py_tag = _find_system_python_for_venv()
    scoped_key = f'{py_tag}::{project_key}'
    venv_path = get_venv_path(scoped_key)
    python_bin = _find_python_bin(venv_path)
    if python_bin.exists():
        if sse_callback:
            try:
                r = subprocess.run(
                    [str(python_bin), '-c', 'import sys; print("%d.%d" % sys.version_info[:2])'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    universal_newlines=True, timeout=5
                )
                ver = r.stdout.strip() if r.returncode == 0 else '?'
            except Exception:
                ver = '?'
            sse_callback('status', {'phase': 'venv', 'message': f'复用虚拟环境（Python {ver}）'})
        return python_bin
    if sse_callback:
        sse_callback('status', {'phase': 'venv', 'message': f'创建虚拟环境（Python {py_tag[2:]}.x）...'})
    if heartbeat_callback:
        heartbeat_callback()
    result = subprocess.run(
        [system_python, '-m', 'venv', str(venv_path)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=180
    )
    if result.returncode != 0:
        raise RuntimeError(f'创建虚拟环境失败: {result.stderr}')
    # 重新定位 python 可执行文件
    python_bin = _find_python_bin(venv_path)
    if sse_callback:
        sse_callback('status', {'phase': 'venv', 'message': '升级 pip...'})
    if heartbeat_callback:
        heartbeat_callback()
    # 流式升级pip，避免长时间无输出
    process = subprocess.Popen(
        [str(python_bin), '-m', 'pip', 'install', '--upgrade', 'pip'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        universal_newlines=True, bufsize=1
    )
    last_hb = time.time()
    while True:
        line = process.stdout.readline()
        if not line:
            if process.poll() is not None:
                break
            if heartbeat_callback and time.time() - last_hb > 5:
                heartbeat_callback()
                last_hb = time.time()
            time.sleep(0.1)
            continue
        if heartbeat_callback:
            heartbeat_callback()
    process.wait()
    return python_bin


# 已安装包缓存（每个venv缓存一次）
_installed_packages_cache = {}

def get_installed_packages(python_bin):
    """获取虚拟环境中已安装的包列表（使用pip list，更可靠）"""
    key = str(python_bin)
    if key in _installed_packages_cache:
        # 缓存5分钟
        cache_time, pkgs = _installed_packages_cache[key]
        if time.time() - cache_time < 300:
            return pkgs
    try:
        result = subprocess.run(
            [str(python_bin), '-m', 'pip', 'list', '--format=json'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=30
        )
        if result.returncode == 0:
            import json as _json
            try:
                pkg_list = _json.loads(result.stdout)
                # key 是包名的规范化形式（小写，下划线转横线）
                installed = set()
                for p in pkg_list:
                    name = p.get('name', '').lower().replace('_', '-')
                    installed.add(name)
                _installed_packages_cache[key] = (time.time(), installed)
                return installed
            except Exception:
                pass
    except Exception:
        pass
    _installed_packages_cache[key] = (time.time(), set())
    return set()


def _normalize_pkg_name(name):
    """规范化包名：pip 比较时忽略大小写和横线/下划线差异"""
    return name.lower().replace('_', '-')


def check_package_installed(python_bin, package_name):
    """检查包是否已安装（优先用pip list，import作为后备）"""
    installed = get_installed_packages(python_bin)
    norm_name = _normalize_pkg_name(package_name)
    if norm_name in installed:
        return True
    # 检查 IMPORT_TO_PIP 中的反向映射
    for imp, pip_name in IMPORT_TO_PIP.items():
        if pip_name and _normalize_pkg_name(pip_name) == norm_name:
            if _normalize_pkg_name(pip_name) in installed:
                return True
    # 后备：用 import 测试（处理 pip list 未列出但可导入的情况，如 editable install）
    import_name = package_name
    for imp, pip in IMPORT_TO_PIP.items():
        if pip == package_name:
            import_name = imp
            break
    try:
        result = subprocess.run(
            [str(python_bin), '-c', f'import {import_name}'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def install_dependencies(python_bin, packages, sse_callback=None, heartbeat_callback=None, total=0, installed_count=None):
    """安装依赖包，流式输出pip进度，单个包失败不中断执行"""
    if not packages:
        return 0, 0
    packages = list(packages)
    if installed_count is None:
        installed_count = [0]
    installed = []
    failed = []
    total_count = total if total else len(packages)

    for idx, pkg in enumerate(packages, 1):
        if heartbeat_callback:
            heartbeat_callback()
        if sse_callback:
            current = installed_count[0]
            sse_callback('deps', {
                'phase': 'installing_package',
                'package': pkg,
                'index': current + 1,
                'total': total_count,
                'message': f'[{current + 1}/{total_count}] 正在安装 {pkg}...'
            })
        try:
            # 优先尝试国内镜像（阿里云），加速 pip 下载
            pip_index = os.environ.get('PIP_INDEX_URL', '')
            if pip_index:
                pip_cmd = [str(python_bin), '-m', 'pip', 'install', pkg, '-i', pip_index, '--timeout', '30']
            else:
                # 默认使用阿里云镜像
                pip_cmd = [str(python_bin), '-m', 'pip', 'install', pkg, '-i', 'https://mirrors.aliyun.com/pypi/simple/', '--timeout', '30']
            process = subprocess.Popen(
                pip_cmd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True, bufsize=1
            )
            last_hb = time.time()
            while True:
                line = process.stdout.readline()
                if not line:
                    if process.poll() is not None:
                        break
                    if heartbeat_callback and time.time() - last_hb > 5:
                        heartbeat_callback()
                        last_hb = time.time()
                    time.sleep(0.1)
                    continue
                line = line.strip()
                if line:
                    if heartbeat_callback:
                        heartbeat_callback()
                    # 过滤pip的冗余输出，只显示关键信息
                    if any(key in line.lower() for key in ['error', 'successfully installed', 'already satisfied', 'collecting', 'downloading', 'installing', 'warning']):
                        if sse_callback:
                            sse_callback('deps', {
                                'phase': 'pip_output',
                                'package': pkg,
                                'line': line[:200]
                            })
            process.wait()
            if process.returncode == 0:
                installed.append(pkg)
                installed_count[0] += 1
                if sse_callback:
                    sse_callback('deps', {
                        'phase': 'package_installed',
                        'package': pkg,
                        'message': f'已安装: {pkg}'
                    })
            else:
                # 镜像源失败时，回退到 PyPI 官方源
                if not pip_index:
                    if sse_callback:
                        sse_callback('deps', {
                            'phase': 'retry_official',
                            'package': pkg,
                            'message': f'{pkg} 国内镜像失败，回退到 PyPI 官方源...'
                        })
                    retry_proc = subprocess.Popen(
                        [str(python_bin), '-m', 'pip', 'install', pkg, '--timeout', '60'],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        universal_newlines=True, bufsize=1
                    )
                    while True:
                        line = retry_proc.stdout.readline()
                        if not line:
                            if retry_proc.poll() is not None:
                                break
                            if heartbeat_callback:
                                heartbeat_callback()
                            time.sleep(0.1)
                            continue
                        line = line.strip()
                        if line and any(key in line.lower() for key in ['error', 'successfully installed', 'already satisfied']):
                            if sse_callback:
                                sse_callback('deps', {
                                    'phase': 'pip_output',
                                    'package': pkg,
                                    'line': line[:200]
                                })
                        if heartbeat_callback:
                            heartbeat_callback()
                    retry_proc.wait()
                    if retry_proc.returncode == 0:
                        installed.append(pkg)
                        installed_count[0] += 1
                        if sse_callback:
                            sse_callback('deps', {
                                'phase': 'package_installed',
                                'package': pkg,
                                'message': f'已安装: {pkg}（使用 PyPI 官方源）'
                            })
                        continue
                failed.append(pkg)
                if sse_callback:
                    sse_callback('deps', {
                        'phase': 'package_failed',
                        'package': pkg,
                        'message': f'跳过无法安装的包: {pkg}（可能是本地模块或不存在）'
                    })
        except subprocess.TimeoutExpired:
            failed.append(pkg)
            if process:
                try: process.kill()
                except: pass
            if sse_callback:
                sse_callback('deps', {
                    'phase': 'package_timeout',
                    'package': pkg,
                    'message': f'安装超时，跳过: {pkg}'
                })
        except Exception as e:
            failed.append(pkg)
            if sse_callback:
                sse_callback('deps', {
                    'phase': 'package_error',
                    'package': pkg,
                    'message': f'安装出错，跳过: {pkg}'
                })
    if sse_callback:
        msg = f'{len(installed)} 个依赖包安装完成'
        if failed:
            msg += f'，{len(failed)} 个已跳过'
        sse_callback('deps', {
            'phase': 'installed',
            'installed': installed,
            'failed': failed,
            'message': msg
        })
    # 清除已安装包缓存，下次重新获取
    _installed_packages_cache.pop(str(python_bin), None)
    return len(installed), len(failed)


def parse_requirements_file(req_path):
    """解析 requirements.txt，返回包名列表"""
    packages = []
    try:
        with open(req_path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('-') or line.startswith('--'):
                    continue
                # 去除版本限定符：package>=1.0 -> package
                pkg_name = re.split(r'[<>=!~;\[]', line)[0].strip()
                if pkg_name:
                    packages.append(pkg_name)
    except Exception:
        pass
    return packages


def install_deps_for_dir(python_bin, temp_dir, skip_dirs, emit, heartbeat):
    """分析目录中所有 .py 文件，收集并安装缺失的第三方依赖。

    返回 True 表示可以继续执行；返回 False 表示已发出错误，应中止。
    """
    req_file = temp_dir / 'requirements.txt'

    heartbeat()
    emit('status', {'phase': 'analyzing', 'message': '分析项目依赖...'})

    # 收集所有 .py 文件以分析 imports
    all_imports = set()
    py_file_count = 0
    for py_file in temp_dir.rglob('*.py'):
        try:
            code_content = py_file.read_text(encoding='utf-8', errors='replace')
            all_imports.update(detect_imports(code_content))
            py_file_count += 1
        except Exception:
            pass
    if py_file_count == 0:
        emit('error', {'message': '项目中没有找到任何 .py 文件'})
        return False

    # 收集本地模块名（排除这些不安装）
    # 更精确的检测：所有目录名（包）和所有 .py 文件名（顶层模块）
    local_modules = set()
    for py_file in temp_dir.rglob('*.py'):
        rel = py_file.relative_to(temp_dir)
        parts = rel.parts
        # 顶层 .py 文件是模块
        if len(parts) == 1:
            local_modules.add(py_file.stem)
        # 路径中的所有目录都是潜在的包
        for i in range(len(parts) - 1):
            local_modules.add(parts[i])
        # __init__.py 确认该目录是包
        if py_file.name == '__init__.py':
            local_modules.add(py_file.parent.name)
    # 额外：扫描所有目录作为包
    for d in temp_dir.rglob('*'):
        if d.is_dir() and not any(part in skip_dirs for part in d.relative_to(temp_dir).parts):
            rel = d.relative_to(temp_dir)
            for part in rel.parts:
                local_modules.add(part)

    # 过滤掉本地模块和标准库模块
    third_party_imports = set()
    for imp in all_imports:
        # 本地模块
        if imp in local_modules:
            continue
        # 标准库
        if imp in STDLIB_MODULES:
            continue
        # 以 _ 开头的内部模块
        if imp.startswith('_'):
            continue
        third_party_imports.add(imp)
    all_imports = third_party_imports

    # 合并 requirements.txt 和检测到的依赖
    req_packages = []
    if req_file.exists():
        req_packages = parse_requirements_file(req_file)
        emit('deps', {'phase': 'requirements_found', 'count': len(req_packages), 'message': f'发现 requirements.txt，包含 {len(req_packages)} 个依赖'})

    # 去重合并所有需要安装的包（用规范化名称去重）
    all_packages = {}
    for pkg in req_packages:
        all_packages[_normalize_pkg_name(pkg)] = pkg
    for pkg in all_imports:
        norm = _normalize_pkg_name(pkg)
        if norm not in all_packages:
            all_packages[norm] = pkg

    # 使用改进的 check_package_installed 检查哪些真正缺失
    missing = []
    for norm_name, pkg_name in all_packages.items():
        if not check_package_installed(python_bin, pkg_name):
            missing.append(pkg_name)
    # 去重（保留顺序）
    seen = set()
    missing_unique = []
    for p in missing:
        if p not in seen:
            seen.add(p)
            missing_unique.append(p)

    if missing_unique:
        emit('deps', {'phase': 'installing', 'count': len(missing_unique), 'message': f'需要安装 {len(missing_unique)} 个依赖包'})
        install_dependencies(python_bin, missing_unique, emit, heartbeat)
    else:
        emit('deps', {'phase': 'installed', 'message': '所有依赖已就绪'})
    return True


def cleanup_old_runs():
    while True:
        time.sleep(300)
        try:
            cutoff = time.time() - 3600
            if RUNS_DIR.exists():
                for d in RUNS_DIR.iterdir():
                    try:
                        if d.is_dir() and d.stat().st_mtime < cutoff:
                            shutil.rmtree(str(d), ignore_errors=True)
                    except Exception:
                        pass
            with processes_lock:
                for run_id, info in list(active_processes.items()):
                    if info['process'].poll() is not None:
                        active_processes.pop(run_id, None)
        except Exception:
            pass


threading.Thread(target=cleanup_old_runs, daemon=True).start()

def hmac_sha256(key, msg):
    return hmac.new(key.encode(), msg.encode(), hashlib.sha256).digest()

def base64url_encode(data):
    if isinstance(data, str):
        data = data.encode()
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

def base64url_decode(s):
    if len(s) % 4:
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
    # First check Authorization header (Bearer token)
    auth_header = handler.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:].strip()
        if token:
            return token
    # Fallback to Cookie
    cookies = parse_cookies(handler.headers.get('Cookie'))
    return cookies.get('wg_token')

def check_auth(handler):
    # Check for Worker-injected auth header
    wg_auth = handler.headers.get('X-WG-Auth')
    if wg_auth:
        try:
            auth_data = json.loads(wg_auth)
            if auth_data.get('username'):
                return True
        except Exception:
            pass
    # Fallback to JWT token
    token = get_token_from_request(handler)
    if not token:
        return False
    payload = verify_jwt(token, JWT_SECRET)
    return payload is not None

def check_admin(handler):
    # Check for Worker-injected auth header
    wg_auth = handler.headers.get('X-WG-Auth')
    if wg_auth:
        try:
            auth_data = json.loads(wg_auth)
            if auth_data.get('is_admin') or auth_data.get('role') == 'admin':
                return True
        except Exception:
            pass
    # Fallback to JWT token
    token = get_token_from_request(handler)
    if not token:
        return False
    payload = verify_jwt(token, JWT_SECRET)
    if not payload:
        return False
    # 兼容新旧 JWT 格式
    is_admin = payload.get('role') == 'admin' or payload.get('is_admin') is True
    return is_admin

def get_current_user(handler):
    # First check for Worker-injected auth header (trusted since ECS is only accessed via Worker)
    wg_auth = handler.headers.get('X-WG-Auth')
    if wg_auth:
        try:
            auth_data = json.loads(wg_auth)
            username = auth_data.get('username', '')
            if username:
                user = get_user_by_username(username)
                if user:
                    # Merge DB user with Worker auth data (trust the Worker's role/is_admin)
                    user['role'] = auth_data.get('role', user.get('role', 'user'))
                    user['is_admin'] = auth_data.get('is_admin', user.get('is_admin', False))
                    return user
                # User might not exist in local DB yet; create a synthetic user
                return {
                    'id': 0,
                    'username': username,
                    'role': auth_data.get('role', 'user'),
                    'is_admin': auth_data.get('is_admin', False),
                    'password_hash': '',
                    'salt': ''
                }
        except Exception:
            pass
    # Fallback to JWT token verification
    token = get_token_from_request(handler)
    if not token:
        return None
    payload = verify_jwt(token, JWT_SECRET)
    if not payload:
        return None
    user_id = payload.get('user_id')
    if user_id:
        user = get_user_by_id(user_id)
        if user:
            return user
    # Handle tokens from Worker (no user_id, use sub/username)
    username = payload.get('sub') or payload.get('username')
    if username:
        user = get_user_by_username(username)
        if user:
            return user
        # Synthetic user for Worker-issued tokens
        return {
            'id': 0,
            'username': username,
            'role': payload.get('role', 'admin' if payload.get('is_admin') else 'user'),
            'is_admin': payload.get('is_admin', payload.get('role') == 'admin'),
            'password_hash': '',
            'salt': ''
        }
    return None


def get_api_key_from_request(handler):
    """从 Authorization: Bearer sk-xxx 或请求体 api_key 提取 API Key"""
    auth = handler.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        return auth[7:].strip()
    try:
        length = int(handler.headers.get('Content-Length', 0))
        if length > 0 and length < 10000:
            raw = handler.rfile.read(length)
            handler.rfile.seek(0)
            body = json.loads(raw) if raw else {}
            return body.get('api_key', '')
    except Exception:
        pass
    return ''


def get_user_by_api_key(api_key):
    """通过 API Key 查找用户，返回 (user_dict, api_key_row) 或 (None, None)"""
    if not api_key or not api_key.startswith('sk-'):
        return None, None
    db = get_db()
    try:
        cur = db.execute(
            "SELECT * FROM api_keys WHERE key = ? AND is_active = 1",
            (api_key,)
        )
        row = cur.fetchone()
        if not row:
            return None, None
        user = get_user_by_id(row['user_id'])
        if not user:
            return None, None
        # 更新 last_used_at
        db.execute("UPDATE api_keys SET last_used_at = ? WHERE id = ?",
                   (int(time.time()), row['id']))
        db.commit()
        return user, dict(row)
    finally:
        db.close()


def generate_api_key():
    """生成 sk- 前缀的随机 API Key"""
    return 'sk-' + os.urandom(24).hex()


# AI 安全配置
AI_DAILY_USER_LIMIT = int(os.environ.get('AI_DAILY_USER_LIMIT', '200'))  # 每用户每日 AI 调用上限
AI_RATE_LIMIT_SECONDS = int(os.environ.get('AI_RATE_LIMIT_SECONDS', '3'))  # 同一用户最短请求间隔（秒）
AI_IP_RATE_LIMIT = int(os.environ.get('AI_IP_RATE_LIMIT', '5'))  # 同一 IP 每分钟上限

# 敏感词过滤（用于 AI 输入安全检查）
SENSITIVE_WORDS = [
    # 政治敏感
    '习近平', '李克强', '江泽民', '胡锦涛', '政治局', '中央委员会',
    '台独', '藏独', '疆独', '港独', '法轮功', '六四', '天安门事件',
    '中国威胁论', '遏制中国',
    # 色情暴力
    '色情', '裸体', 'porn', 'sex', '暴力', '血腥', '杀人', '自杀',
    '毒品', '赌博', '卖淫', '嫖娼',
    # 恐怖极端
    '恐怖袭击', '人肉炸弹', '极端组织', 'ISIS',
    # 违法犯罪
    '洗钱', '诈骗', '传销', '赌博',
    # 其他敏感
    '翻墙', 'VPN', '科学上网',
]

# 请求频率记录（内存中，进程重启会清空）
_ip_request_log = {}  # {ip: [timestamp, ...]}
_user_request_log = {}  # {user_id: [timestamp, ...]}
_rate_lock = threading.Lock()


def check_sensitive_content(text):
    """检查文本是否包含敏感词，返回命中的敏感词列表"""
    if not text:
        return []
    text_lower = text.lower()
    hit = []
    for word in SENSITIVE_WORDS:
        if word.lower() in text_lower:
            hit.append(word)
    return hit


def check_rate_limit(user_id=None, ip=None):
    """检查请求频率是否超限，返回 (allowed, reason)"""
    now = time.time()
    ip = ip or 'unknown'

    with _rate_lock:
        # IP 频率限制：每分钟最多 N 次
        if ip not in _ip_request_log:
            _ip_request_log[ip] = []
        # 清理 1 分钟前的记录
        _ip_request_log[ip] = [t for t in _ip_request_log[ip] if now - t < 60]
        if len(_ip_request_log[ip]) >= AI_IP_RATE_LIMIT:
            return False, f'请求过于频繁，请稍后再试（每分钟最多 {AI_IP_RATE_LIMIT} 次）'
        _ip_request_log[ip].append(now)

        # 用户频率限制
        if user_id:
            if user_id not in _user_request_log:
                _user_request_log[user_id] = []
            _user_request_log[user_id] = [t for t in _user_request_log[user_id] if now - t < 3600]
            if _user_request_log[user_id] and (now - _user_request_log[user_id][-1]) < AI_RATE_LIMIT_SECONDS:
                return False, f'请求间隔过短，请等待 {AI_RATE_LIMIT_SECONDS} 秒'
            _user_request_log[user_id].append(now)

    return True, ''


def get_client_ip(handler):
    """获取客户端 IP"""
    xff = handler.headers.get('X-Forwarded-For', '')
    if xff:
        return xff.split(',')[0].strip()
    return handler.client_address[0] if handler.client_address else 'unknown'


def record_ai_usage(user_id, username):
    """记录某用户今日 AI 调用次数（UPSERT），user_id 可能为 None（未登录）"""
    if not user_id:
        return
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    db = get_db()
    try:
        db.execute('''INSERT INTO ai_usage (user_id, username, date, count, last_active)
                      VALUES (?, ?, ?, 1, ?)
                      ON CONFLICT(user_id, date) DO UPDATE SET
                          count = count + 1,
                          username = excluded.username,
                          last_active = excluded.last_active''',
                   (user_id, username, today, int(time.time())))
        db.commit()
    except Exception as e:
        print(f'AiUsage Error: {e}', file=sys.stderr)
    finally:
        db.close()

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


def has_messages_with_images(messages):
    """检查消息列表中是否包含图片"""
    for m in messages:
        content = m.get('content', '')
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get('type') in ('image_url', 'image', 'image_base64'):
                    return True
    return False


def extract_images_from_messages(messages):
    """从消息中提取图片，返回 base64 图片列表供 Ollama 使用"""
    images = []
    for m in messages:
        content = m.get('content', '')
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    img_url = None
                    if part.get('type') == 'image_url':
                        img_url = part.get('image_url', {}).get('url', '')
                    elif part.get('type') == 'image':
                        img_url = part.get('image', '')
                    elif part.get('type') == 'image_base64':
                        img_url = part.get('data', '')
                    if img_url:
                        # 如果是 URL 图片，需要下载并转换为 base64
                        if img_url.startswith('http://') or img_url.startswith('https://'):
                            try:
                                img_req = urllib.request.Request(img_url)
                                with urllib.request.urlopen(img_req, timeout=10) as resp:
                                    img_data = resp.read()
                                    img_b64 = base64.b64encode(img_data).decode('utf-8')
                                    images.append(img_b64)
                            except Exception:
                                pass
                        elif img_url.startswith('data:'):
                            # data URI，提取 base64 部分
                            try:
                                img_b64 = img_url.split(',', 1)[1] if ',' in img_url else ''
                                if img_b64:
                                    images.append(img_b64)
                            except Exception:
                                pass
                        else:
                            # 已是 base64
                            images.append(img_url)
    return images


def web_search(query, max_results=5):
    """使用 DuckDuckGo 免费搜索 API 进行联网搜索
    返回搜索结果列表 [{title, url, snippet}]"""
    try:
        # 使用 DuckDuckGo Instant Answer API
        encoded_query = urllib.parse.quote(query)
        # DuckDuckGo 没有直接的网页搜索 API，使用更简单的方式
        # 使用 searx 实例或其他免费方案
        search_url = f'https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1&no_redirect=1'
        req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        
        results = []
        # Abstract 部分
        if data.get('AbstractText'):
            results.append({
                'title': data.get('Heading', query),
                'url': data.get('AbstractURL', ''),
                'snippet': data['AbstractText']
            })
        # Related topics
        for topic in data.get('RelatedTopics', [])[:max_results]:
            if isinstance(topic, dict) and 'Text' in topic:
                results.append({
                    'title': topic.get('Text', '')[:80],
                    'url': topic.get('FirstURL', ''),
                    'snippet': topic.get('Text', '')[:200]
                })
        # Answer
        if data.get('Answer'):
            results.insert(0, {
                'title': query,
                'url': data.get('AnswerURL', ''),
                'snippet': data['Answer']
            })
        return results[:max_results]
    except Exception as e:
        print(f'[WebSearch] 搜索失败: {e}', file=sys.stderr)
        return []


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


def scan_directory(dir_path, base_path='', max_depth=0, current_depth=0):
    """扫描目录，返回文件树结构（与 generate_filetree.py 一致）
    max_depth=0 表示不限制深度，max_depth=1 表示只扫描第一层
    """
    items = []
    try:
        for entry in sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            name = entry.name
            if name.startswith('.'):
                continue
            if entry.is_dir():
                if name in ('__pycache__', 'node_modules', '.git', '.venv', 'venv'):
                    continue
                # 深度限制：达到最大深度时，目录标记为可展开但不递归
                if max_depth > 0 and current_depth + 1 >= max_depth:
                    items.append({
                        'name': name,
                        'type': 'directory',
                        'path': f"{base_path}/{name}" if base_path else name,
                        'children': [],
                        'hasChildren': True,
                    })
                else:
                    children = scan_directory(entry, f"{base_path}/{name}" if base_path else name, max_depth, current_depth + 1)
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


def get_project_tree(project_path, max_depth=0):
    """获取项目文件树：优先 JSON 文件，fallback 到文件系统扫描
    max_depth > 0 时只扫描指定深度（懒加载模式，跳过 JSON 缓存）
    """
    # 懒加载模式：直接扫描文件系统，不使用 JSON 缓存
    if max_depth <= 0:
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
                return scan_directory(full_path, max_depth=max_depth)
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

        # ========= Ollama 代理端点 (GET) =========
        if path.startswith('/api/ollama'):
            cu = get_current_user(self)
            if not cu:
                return self.send_error_json('请先登录', 401)
            ollama_path = path.replace('/api/ollama', '')
            if not ollama_path:
                ollama_path = '/api/tags'
            target_url = f"{OLLAMA_URL}{ollama_path}"
            try:
                req = urllib.request.Request(target_url, method='GET')
                with urllib.request.urlopen(req, timeout=60) as resp:
                    resp_data = resp.read()
                    self.send_response(resp.status)
                    self.send_header('Content-Type', resp.headers.get('Content-Type', 'application/json'))
                    self.send_header('Content-Length', len(resp_data))
                    self.end_headers()
                    self.wfile.write(resp_data)
            except urllib.error.HTTPError as e:
                err_body = e.read()
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(err_body)
            except Exception as e:
                self.send_error_json(f'Ollama 请求失败: {str(e)}', 500)
            return

        if path == '/api/auth-check':
            user = get_current_user(self)
            if user:
                return self.send_json({'authenticated': True, 'user': {'id': user['id'], 'username': user['username'], 'role': user['role']}})
            return self.send_json({'authenticated': False})

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
            # 支持深度参数：depth=1 只加载第一层目录，实现懒加载
            depth_str = qs.get('depth', ['0'])[0]
            try:
                depth = int(depth_str)
            except ValueError:
                depth = 0
            data = get_project_tree(project_path, max_depth=depth)
            return self.send_json(data)

        if path == '/api/files/subtree':
            # 懒加载：获取项目内某个子目录的子节点
            project_path = qs.get('project', [''])[0]
            dir_path = qs.get('dir', [''])[0]
            depth_str = qs.get('depth', ['1'])[0]
            if not project_path or not dir_path:
                return self.send_json([])
            try:
                depth = int(depth_str)
            except ValueError:
                depth = 1
            root = _find_projects_root()
            candidates = [
                root / project_path,
                BASE_DIR.parent.parent / project_path,
                BASE_DIR.parent / project_path,
                BASE_DIR / project_path,
            ]
            for full_path in candidates:
                try:
                    target = (full_path / dir_path).resolve()
                    # 安全检查：确保 target 在 project_path 下
                    project_full = full_path.resolve()
                    if str(target).startswith(str(project_full)) and target.exists() and target.is_dir():
                        children = scan_directory(target, dir_path, max_depth=depth)
                        return self.send_json(children)
                except Exception:
                    continue
            return self.send_json([])

        if path == '/api/files/tree':
            project = qs.get('project', [''])[0]
            if project:
                data = get_project_tree(project)
                return self.send_json(data)
            return self.send_json([])

        if path == '/api/ai-quota':
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            db = get_db()
            try:
                cur = db.execute("SELECT COALESCE(SUM(count), 0) AS cnt FROM ai_usage WHERE date = ?", (today,))
                row = cur.fetchone()
                used = row['cnt'] if row else 0
                # 单个非池子维度：保留原来的 neurons 视角
                return self.send_json({'usage': used, 'remaining': max(0, AI_POOL_TOTAL - used), 'limit': AI_POOL_TOTAL, 'neuronsPerRequest': 100})
            except Exception:
                return self.send_json({'usage': 0, 'remaining': AI_POOL_TOTAL, 'limit': AI_POOL_TOTAL, 'neuronsPerRequest': 100})
            finally:
                db.close()

        if path == '/api/cache-stats':
            stats = {
                'memory': _memory_cache.stats(),
                'ai': _ai_cache.stats(),
                'projects': _project_cache.stats(),
            }
            return self.send_json(stats)

        if path == '/api/cache-clear':
            _memory_cache.clear()
            _ai_cache.clear()
            _project_cache.clear()
            return self.send_json({'success': True, 'message': '所有缓存已清除'})

        if path == '/api/ollama-status':
            status = {
                'enabled': USE_OLLAMA,
                'url': OLLAMA_URL,
                'model': OLLAMA_MODEL,
                'dailyLimit': OLLAMA_DAILY_LIMIT,
                'available': False,
                'models': list(OLLAMA_MODELS.values()),
                'ollamaModels': []
            }
            if USE_OLLAMA:
                try:
                    ollama_req = urllib.request.Request(f'{OLLAMA_URL}/api/tags')
                    with urllib.request.urlopen(ollama_req, timeout=5) as resp:
                        ollama_data = json.loads(resp.read())
                        status['available'] = True
                        status['ollamaModels'] = [m.get('name', '') for m in ollama_data.get('models', [])]
                except Exception:
                    pass
            return self.send_json(status)

        if path == '/api/models':
            available_models = list(OLLAMA_MODELS.values())
            if USE_OLLAMA:
                try:
                    ollama_req = urllib.request.Request(f'{OLLAMA_URL}/api/tags')
                    with urllib.request.urlopen(ollama_req, timeout=5) as resp:
                        ollama_data = json.loads(resp.read())
                        ollama_model_names = {m.get('name', '').split(':')[0] for m in ollama_data.get('models', [])}
                        for m in available_models:
                            m['available'] = any(
                                om.startswith(m['model'].split(':')[0])
                                for om in ollama_model_names
                            )
                except Exception:
                    for m in available_models:
                        m['available'] = False
            else:
                for m in available_models:
                    m['available'] = False
            return self.send_json({
                'models': available_models,
                'defaultModel': OLLAMA_MODELS['text']['model'],
                'ollamaUrl': OLLAMA_URL,
                'enabled': USE_OLLAMA
            })

        if path == '/api/ai-pool':
            user = get_current_user(self)
            if not user:
                return self.send_error_json('请先登录', 401)
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            db = get_db()
            try:
                # 今日池子用量
                cur = db.execute("SELECT COALESCE(SUM(count), 0) AS total, COUNT(*) AS user_cnt FROM ai_usage WHERE date = ?", (today,))
                row = cur.fetchone()
                used = row['total'] if row else 0
                user_cnt = row['user_cnt'] if row else 0
                # 每用户用量（降序）
                cur = db.execute("SELECT user_id, username, count, last_active FROM ai_usage WHERE date = ? ORDER BY count DESC", (today,))
                users = []
                for r in cur.fetchall():
                    u = get_user_by_id(r['user_id'])
                    users.append({
                        'userId': r['user_id'],
                        'username': r['username'],
                        'role': u['role'] if u else 'user',
                        'used': r['count'],
                        'lastActive': r['last_active'],
                    })
                # 近7天趋势（含今天）
                days = 7
                try:
                    days = max(1, min(30, int(qs.get('days', ['7'])[0])))
                except ValueError:
                    days = 7
                trend = []
                for offset in range(days - 1, -1, -1):
                    d = (datetime.datetime.now() - datetime.timedelta(days=offset)).strftime('%Y-%m-%d')
                    cur = db.execute("SELECT COALESCE(SUM(count), 0) AS total FROM ai_usage WHERE date = ?", (d,))
                    trow = cur.fetchone()
                    trend.append({'date': d, 'used': trow['total'] if trow else 0})
                return self.send_json({
                    'pool': {
                        'total': AI_POOL_TOTAL,
                        'used': used,
                        'remaining': max(0, AI_POOL_TOTAL - used),
                        'cloudflareDaily': CF_DAILY_LIMIT,
                        'openrouterDaily': OPENROUTER_DAILY_LIMIT,
                        'ratio': AI_POOL_RATIO,
                        'date': today,
                    },
                    'users': users,
                    'trend': trend,
                })
            finally:
                db.close()

        if path == '/api/scratch/projects':
            user = get_current_user(self)
            if not user:
                return self.send_error_json('请先登录', 401)
            db = get_db()
            try:
                cur = db.execute("SELECT id, name, filename, file_size, created_at, updated_at FROM scratch_projects WHERE user_id = ? ORDER BY updated_at DESC", (user['id'],))
                projects = [dict(r) for r in cur.fetchall()]
                return self.send_json(projects)
            finally:
                db.close()

        if path.startswith('/api/scratch/projects/') and path.endswith('/download'):
            user = get_current_user(self)
            if not user:
                return self.send_error_json('请先登录', 401)
            try:
                project_id = int(path.split('/')[4])
            except (ValueError, IndexError):
                return self.send_error_json('无效的项目ID', 400)
            db = get_db()
            try:
                cur = db.execute("SELECT * FROM scratch_projects WHERE id = ? AND user_id = ?", (project_id, user['id']))
                project = cur.fetchone()
                if not project:
                    return self.send_error_json('项目不存在', 404)
                project = dict(project)
                file_path = BASE_DIR / 'scratch' / 'projects' / str(user['id']) / project['filename']
                if not file_path.exists():
                    return self.send_error_json('文件不存在', 404)
                body = file_path.read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'application/octet-stream')
                self.send_header('Content-Disposition', f'attachment; filename="{project["name"]}.sb3"')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            finally:
                db.close()

        if path == '/api/api-keys':
            user = get_current_user(self)
            if not user:
                return self.send_error_json('请先登录', 401)
            show_all = qs.get('all', [''])[0] == '1'
            db = get_db()
            try:
                if show_all:
                    if user.get('role') != 'admin':
                        return self.send_error_json('无权限查看全部 Key', 403)
                    cur = db.execute(
                        "SELECT id, user_id, username, key, name, desc, daily_limit, expires_at, created_at, last_used_at, is_active FROM api_keys ORDER BY created_at DESC"
                    )
                else:
                    cur = db.execute(
                        "SELECT id, user_id, username, key, name, desc, daily_limit, expires_at, created_at, last_used_at, is_active FROM api_keys WHERE user_id = ? ORDER BY created_at DESC",
                        (user['id'],)
                    )
                keys = [dict(r) for r in cur.fetchall()]
                return self.send_json({'keys': keys})
            finally:
                db.close()

        if path == '/api/api-keys/delete':
            user = get_current_user(self)
            if not user:
                return self.send_error_json('请先登录', 401)
            key_id = qs.get('id', [''])[0]
            if not key_id:
                return self.send_error_json('缺少 id 参数', 400)
            db = get_db()
            try:
                if user.get('role') == 'admin':
                    db.execute("DELETE FROM api_keys WHERE id = ?", (int(key_id),))
                else:
                    db.execute("DELETE FROM api_keys WHERE id = ? AND user_id = ?",
                               (int(key_id), user['id']))
                db.commit()
                return self.send_json({'success': True})
            finally:
                db.close()

        if path == '/api/api-keys/toggle':
            user = get_current_user(self)
            if not user:
                return self.send_error_json('请先登录', 401)
            key_id = qs.get('id', [''])[0]
            if not key_id:
                return self.send_error_json('缺少 id 参数', 400)
            db = get_db()
            try:
                if user.get('role') == 'admin':
                    db.execute("UPDATE api_keys SET is_active = 1 - is_active WHERE id = ?", (int(key_id),))
                else:
                    db.execute("UPDATE api_keys SET is_active = 1 - is_active WHERE id = ? AND user_id = ?",
                               (int(key_id), user['id']))
                db.commit()
                return self.send_json({'success': True})
            finally:
                db.close()

        if path == '/api/user/conversations':
            user = get_current_user(self)
            if not user:
                return self.send_error_json('请先登录', 401)
            db = get_db()
            try:
                cur = db.execute("SELECT id, title, messages, created_at, updated_at FROM conversations WHERE user_id = ? ORDER BY updated_at DESC", (user['id'],))
                convs = []
                for row in cur.fetchall():
                    c = dict(row)
                    c['messages'] = json.loads(c['messages'])
                    convs.append(c)
                return self.send_json({'conversations': convs})
            finally:
                db.close()

        if path == '/api/user/bookmarks':
            user = get_current_user(self)
            if not user:
                return self.send_error_json('请先登录', 401)
            db = get_db()
            try:
                cur = db.execute("SELECT project_path, project_name, project_icon, created_at FROM bookmarks WHERE user_id = ? ORDER BY created_at DESC", (user['id'],))
                bookmarks = [dict(row) for row in cur.fetchall()]
                return self.send_json({'bookmarks': bookmarks})
            finally:
                db.close()

        if path == '/api/user/recent':
            user = get_current_user(self)
            if not user:
                return self.send_error_json('请先登录', 401)
            db = get_db()
            try:
                cur = db.execute("SELECT project_path, project_name, project_icon, visited_at FROM recent_visits WHERE user_id = ? ORDER BY visited_at DESC LIMIT 10", (user['id'],))
                recent = [dict(row) for row in cur.fetchall()]
                return self.send_json({'recent': recent})
            finally:
                db.close()

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
            likes_data = _load_likes()  # 保持兼容旧数据
            # 同时从 SQLite 获取按用户去重的点赞数据
            user = get_current_user(self)
            user_liked = []
            if user:
                db = get_db()
                try:
                    cur = db.execute("SELECT project_path FROM likes WHERE user_id = ?", (user['id'],))
                    user_liked = [row['project_path'] for row in cur.fetchall()]
                finally:
                    db.close()
            return self.send_json({'likes': likes_data, 'userLiked': user_liked})

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

        if path == '/api/admin/users':
            if not check_admin(self):
                return self.send_error_json('需要管理员权限', 401)
            db = get_db()
            try:
                cur = db.execute("SELECT id, username, role, created_at, last_login FROM users ORDER BY id")
                users = [dict(row) for row in cur.fetchall()]
                return self.send_json({'users': users})
            finally:
                db.close()

        if path == '/api/feedback/list':
            is_admin = check_admin(self)
            user = get_current_user(self)
            db = get_db()
            try:
                if is_admin:
                    cur = db.execute("SELECT * FROM feedback ORDER BY created_at DESC")
                elif user:
                    cur = db.execute("SELECT * FROM feedback WHERE user_id = ? ORDER BY created_at DESC", (user['id'],))
                else:
                    return self.send_error_json('需要登录', 401)
                feedback = []
                for row in cur.fetchall():
                    item = dict(row)
                    reply_count = db.execute(
                        "SELECT COUNT(*) FROM feedback_replies WHERE feedback_id = ?", (item['id'],)
                    ).fetchone()[0]
                    item['reply_count'] = reply_count
                    feedback.append(item)
                return self.send_json({'feedback': feedback})
            finally:
                db.close()

        if path == '/api/feedback/detail':
            fid = qs.get('id', [''])[0]
            if not fid:
                return self.send_error_json('缺少反馈 ID', 400)
            try:
                fid = int(fid)
            except (TypeError, ValueError):
                return self.send_error_json('无效的反馈 ID', 400)
            user = get_current_user(self)
            is_admin = check_admin(self)
            if not user:
                return self.send_error_json('需要登录', 401)
            db = get_db()
            try:
                fb = db.execute("SELECT * FROM feedback WHERE id = ?", (fid,)).fetchone()
                if not fb:
                    return self.send_error_json('反馈不存在', 404)
                fb_item = dict(fb)
                if not is_admin and fb_item['user_id'] != user['id']:
                    return self.send_error_json('无权查看', 403)
                replies = db.execute(
                    "SELECT * FROM feedback_replies WHERE feedback_id = ? ORDER BY created_at ASC", (fid,)
                ).fetchall()
                fb_item['replies'] = [dict(r) for r in replies]
                return self.send_json(fb_item)
            finally:
                db.close()

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
            # 直接扫描文件系统搜索，不再依赖 24.5MB 的 file-tree.json
            results = []
            root = _find_projects_root()
            skip_dirs = {'__pycache__', '.git', 'node_modules', '.venv', 'venv', '.idea', '.vscode', '.code-explorer'}
            try:
                for entry in root.iterdir():
                    if not entry.is_dir() or entry.name.startswith('.') or entry.name in skip_dirs:
                        continue
                    for dirpath, dirnames, filenames in os.walk(str(entry)):
                        # 过滤不需要遍历的目录
                        dirnames[:] = [d for d in dirnames if d not in skip_dirs and not d.startswith('.')]
                        for fname in filenames:
                            if query in fname.lower():
                                full_path = os.path.relpath(os.path.join(dirpath, fname), str(root))
                                full_path = full_path.replace('\\', '/')
                                ext = os.path.splitext(fname)[1].lower()
                                results.append({'name': fname, 'path': full_path, 'ext': ext})
                                if len(results) >= 100:
                                    return self.send_json(results)
            except Exception:
                pass
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
                ct_map = {'.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.webp': 'image/webp', '.bmp': 'image/bmp', '.ico': 'image/x-icon', '.svg': 'image/svg+xml'}
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
                    root.parent / file_path,
                ]
                local_path = None
                is_dir = False
                for sp in search_paths:
                    if sp.exists():
                        if sp.is_dir():
                            local_path = sp
                            is_dir = True
                            break
                        elif sp.is_file():
                            local_path = sp
                            is_dir = False
                            break
                if not local_path:
                    return self.send_error_json('文件不存在', 404)

                if is_dir:
                    # 下载整个项目目录，打包为 ZIP
                    import io, zipfile
                    buf = io.BytesIO()
                    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                        project_name = local_path.name
                        for entry in local_path.rglob('*'):
                            if entry.is_file() and not entry.name.startswith('.'):
                                arcname = str(entry.relative_to(local_path))
                                zf.write(entry, arcname)
                    body = buf.getvalue()
                    filename = project_name + '.zip'
                else:
                    # 下载单个文件
                    body = local_path.read_bytes()
                    filename = os.path.basename(file_path)

                self.send_response(200)
                self.send_header('Content-Type', 'application/zip')
                encoded_fn = urllib.parse.quote(filename)
                self.send_header('Content-Disposition', f'attachment; filename="{encoded_fn}"; filename*=UTF-8\'\'{encoded_fn}')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            except Exception as e:
                return self.send_error_json(f'下载失败: {e}', 500)

        # ===== 静态页面路由 =====
        if path == '/run/local' or path == '/run/local/':
            local_path = BASE_DIR / 'run' / 'local.html'
            if local_path.exists():
                content = local_path.read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', len(content))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(content)
                return

        if path == '/feedback' or path == '/feedback/':
            # 重定向到反馈页面
            self.send_response(302)
            self.send_header('Location', '/feedback/index.html')
            self.end_headers()
            return

        # 尝试匹配静态文件
        if path == '/' or (path and not path.startswith('/api/')):
            clean_path = 'index.html' if path == '/' else path.lstrip('/').rstrip('/')
            if clean_path:
                candidates = [
                    BASE_DIR / clean_path,
                    BASE_DIR / (clean_path + '.html'),
                    BASE_DIR / clean_path / 'index.html',
                ]
                for candidate in candidates:
                    try:
                        if candidate.exists() and candidate.is_file():
                            content = candidate.read_bytes()
                            ext = candidate.suffix.lower()
                            content_types = {
                                '.html': 'text/html; charset=utf-8',
                                '.css': 'text/css; charset=utf-8',
                                '.js': 'application/javascript; charset=utf-8',
                                '.json': 'application/json; charset=utf-8',
                                '.png': 'image/png',
                                '.jpg': 'image/jpeg',
                                '.jpeg': 'image/jpeg',
                                '.gif': 'image/gif',
                                '.svg': 'image/svg+xml',
                                '.ico': 'image/x-icon',
                                '.webp': 'image/webp',
                                '.woff': 'font/woff',
                                '.woff2': 'font/woff2',
                            }
                            ctype = content_types.get(ext, 'application/octet-stream')
                            self.send_response(200)
                            self.send_header('Content-Type', ctype)
                            self.send_header('Content-Length', len(content))
                            self.send_header('Cache-Control', 'public, max-age=3600')
                            self.end_headers()
                            self.wfile.write(content)
                            return
                    except Exception:
                        continue

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
            username = body.get('username', '')
            password = body.get('password', '')
            if not username or not password:
                return self.send_error_json('请输入用户名和密码', 400)
            user = get_user_by_username(username)
            if not user:
                return self.send_error_json('用户名或密码错误', 401)
            if not verify_password(password, user['password_hash'], user['salt']):
                return self.send_error_json('用户名或密码错误', 401)
            # 更新 last_login
            db = get_db()
            try:
                db.execute("UPDATE users SET last_login = ? WHERE id = ?", (int(time.time()), user['id']))
                db.commit()
            finally:
                db.close()
            token = sign_jwt({'sub': user['username'], 'user_id': user['id'], 'username': user['username'], 'role': user['role']}, JWT_SECRET)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.set_cookie('wg_token', token)
            self.end_headers()
            self.wfile.write(json.dumps({'token': token, 'user': {'id': user['id'], 'username': user['username'], 'role': user['role']}}).encode('utf-8'))
            return

        if path == '/api/register':
            return self.send_error_json('注册功能已关闭，请联系管理员获取账号', 403)

        if path == '/api/logout':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.clear_cookie('wg_token')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode('utf-8'))
            return

        if path == '/api/admin/login':
            return self.send_error_json('管理员登录已废弃，请使用普通登录', 410)

        if path == '/api/user/profile':
            user = get_current_user(self)
            if not user:
                return self.send_error_json('请先登录', 401)
            return self.send_json({'user': user})

        if path == '/api/user/change-password':
            user = get_current_user(self)
            if not user:
                return self.send_error_json('请先登录', 401)
            old_password = body.get('old_password', '')
            new_password = body.get('new_password', '')
            if not old_password or not new_password:
                return self.send_error_json('请提供旧密码和新密码', 400)
            if len(new_password) < 6:
                return self.send_error_json('新密码长度至少6位', 400)
            # 验证旧密码
            db = get_db()
            try:
                cur = db.execute("SELECT password_hash, salt FROM users WHERE id = ?", (user['id'],))
                row = cur.fetchone()
                if not row or not verify_password(old_password, row['password_hash'], row['salt']):
                    return self.send_error_json('旧密码错误', 401)
                h, s = hash_password(new_password)
                db.execute("UPDATE users SET password_hash = ?, salt = ? WHERE id = ?", (h, s, user['id']))
                db.commit()
                return self.send_json({'success': True, 'message': '密码修改成功'})
            finally:
                db.close()

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

        if path == '/api/admin/users':
            if not check_admin(self):
                return self.send_error_json('需要管理员权限', 401)
            db = get_db()
            try:
                cur = db.execute("SELECT id, username, role, created_at, last_login FROM users ORDER BY id")
                users = [dict(row) for row in cur.fetchall()]
                return self.send_json({'users': users})
            finally:
                db.close()

        if path == '/api/admin/users/delete':
            if not check_admin(self):
                return self.send_error_json('需要管理员权限', 401)
            user_id = body.get('user_id')
            if not user_id:
                return self.send_error_json('缺少 user_id 参数', 400)
            db = get_db()
            try:
                cur = db.execute("SELECT role FROM users WHERE id = ?", (user_id,))
                row = cur.fetchone()
                if not row:
                    return self.send_error_json('用户不存在', 404)
                # 不能删除管理员
                if row['role'] == 'admin':
                    return self.send_error_json('不能删除管理员', 400)
                # 获取当前用户 ID
                token = get_token_from_request(self)
                payload = verify_jwt(token, JWT_SECRET)
                if payload and payload.get('user_id') == user_id:
                    return self.send_error_json('不能删除自己', 400)
                # 删除用户相关数据
                db.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
                db.execute("DELETE FROM bookmarks WHERE user_id = ?", (user_id,))
                db.execute("DELETE FROM recent_visits WHERE user_id = ?", (user_id,))
                db.execute("DELETE FROM likes WHERE user_id = ?", (user_id,))
                db.execute("DELETE FROM users WHERE id = ?", (user_id,))
                db.commit()
                return self.send_json({'success': True, 'message': '用户已删除'})
            finally:
                db.close()

        if path == '/api/feedback':
            user = get_current_user(self)
            if not user:
                return self.send_error_json('请先登录', 401)
            content = (body.get('content', '') or '').strip()
            ftype = body.get('type', 'other')
            if ftype not in ('bug', 'feature', 'suggestion', 'praise', 'other'):
                ftype = 'other'
            try:
                rating = int(body.get('rating', 0))
            except (TypeError, ValueError):
                rating = 0
            if not rating:
                return self.send_error_json('请选择评分', 400)
            rating = max(1, min(5, rating))
            project = (body.get('project', '') or '').strip()[:100]
            if not content:
                return self.send_error_json('请输入反馈内容', 400)
            if len(content) < 5:
                return self.send_error_json('反馈内容至少 5 个字', 400)
            now = int(time.time())
            db = get_db()
            try:
                cur = db.execute(
                    "INSERT INTO feedback (username, user_id, type, content, rating, project, status, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, 'new', ?, ?)",
                    (user['username'], user['id'], ftype, content[:2000], rating, project, now, now)
                )
                db.commit()
                feedback_id = cur.lastrowid
                return self.send_json({'success': True, 'id': feedback_id, 'message': '反馈提交成功'}, 201)
            finally:
                db.close()

        if path == '/api/feedback/reply':
            user = get_current_user(self)
            if not user:
                return self.send_error_json('请先登录', 401)
            if not check_admin(self):
                print(f"[WARN] Non-admin user '{user.get('username', 'unknown')}' (id={user.get('id')}) attempted to reply to feedback", file=sys.stderr)
                return self.send_error_json('需要管理员权限', 401)
            feedback_id = body.get('feedback_id')
            content = (body.get('content', '') or '').strip()
            if not feedback_id:
                return self.send_error_json('缺少反馈 ID', 400)
            if not content:
                return self.send_error_json('回复内容不能为空', 400)
            if len(content) < 2:
                return self.send_error_json('回复内容至少 2 个字', 400)
            db = get_db()
            try:
                fb = db.execute("SELECT id FROM feedback WHERE id = ?", (feedback_id,)).fetchone()
                if not fb:
                    return self.send_error_json('反馈不存在', 404)
                now = int(time.time())
                cur = db.execute(
                    "INSERT INTO feedback_replies (feedback_id, username, user_id, content, is_admin, created_at) "
                    "VALUES (?, ?, ?, ?, 1, ?)",
                    (feedback_id, user['username'], user['id'], content[:2000], now)
                )
                db.execute("UPDATE feedback SET updated_at = ? WHERE id = ?", (now, feedback_id))
                db.commit()
                return self.send_json({'success': True, 'reply_id': cur.lastrowid, 'message': '回复成功'})
            finally:
                db.close()

        if path == '/api/feedback/status':
            user = get_current_user(self)
            if not check_admin(self):
                if user:
                    print(f"[WARN] Non-admin user '{user.get('username', 'unknown')}' (id={user.get('id')}) attempted to change feedback status", file=sys.stderr)
                return self.send_error_json('需要管理员权限', 401)
            feedback_id = body.get('id')
            status = body.get('status', '')
            if not feedback_id:
                return self.send_error_json('缺少反馈 ID', 400)
            if status not in ('new', 'processing', 'resolved', 'closed'):
                return self.send_error_json('无效的状态', 400)
            db = get_db()
            try:
                fb = db.execute("SELECT id FROM feedback WHERE id = ?", (feedback_id,)).fetchone()
                if not fb:
                    return self.send_error_json('反馈不存在', 404)
                now = int(time.time())
                db.execute("UPDATE feedback SET status = ?, updated_at = ? WHERE id = ?", (status, now, feedback_id))
                db.commit()
                return self.send_json({'success': True})
            finally:
                db.close()

        if path == '/api/feedback/delete':
            user = get_current_user(self)
            if not user:
                return self.send_error_json('请先登录', 401)
            feedback_id = body.get('id')
            if not feedback_id:
                return self.send_error_json('缺少反馈 ID', 400)
            db = get_db()
            try:
                fb = db.execute("SELECT * FROM feedback WHERE id = ?", (feedback_id,)).fetchone()
                if not fb:
                    return self.send_error_json('反馈不存在', 404)
                is_admin = check_admin(self)
                if not is_admin and fb['user_id'] != user['id']:
                    return self.send_error_json('无权删除', 403)
                db.execute("DELETE FROM feedback_replies WHERE feedback_id = ?", (feedback_id,))
                db.execute("DELETE FROM feedback WHERE id = ?", (feedback_id,))
                db.commit()
                return self.send_json({'success': True})
            finally:
                db.close()

        if path == '/api/comments' and self.command == 'POST':
            project = body.get('project', '')
            text = (body.get('text', '') or '').strip()
            if not project or not text:
                return self.send_error_json('缺少 project 或 text 参数')
            project_data = _load_comments(project)
            comment_id = hashlib.md5(f'{time.time()}{text}'.encode()).hexdigest()[:8]
            user = get_current_user(self)
            comment = {
                'id': comment_id, 'project': project, 'text': text,
                'timestamp': int(time.time() * 1000), 'image': None, 'likes': 0,
                'user_id': user['id'] if user else None,
                'username': user['username'] if user else '匿名'
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
            user = get_current_user(self)
            if not user:
                return self.send_error_json('请先登录', 401)
            db = get_db()
            try:
                cur = db.execute("SELECT id FROM likes WHERE user_id = ? AND project_path = ?", (user['id'], project))
                existing = cur.fetchone()
                if existing:
                    # 取消点赞
                    db.execute("DELETE FROM likes WHERE id = ?", (existing['id'],))
                    db.commit()
                    # 更新全局计数
                    likes_data = _load_likes()
                    likes_data[project] = max(0, likes_data.get(project, 0) - 1)
                    write_json_file(LIKES_FILE, likes_data)
                    return self.send_json({'project': project, 'likes': likes_data.get(project, 0), 'liked': False})
                else:
                    # 点赞
                    db.execute("INSERT INTO likes (user_id, project_path, created_at) VALUES (?, ?, ?)",
                               (user['id'], project, int(time.time())))
                    db.commit()
                    likes_data = _load_likes()
                    likes_data[project] = likes_data.get(project, 0) + 1
                    write_json_file(LIKES_FILE, likes_data)
                    return self.send_json({'project': project, 'likes': likes_data.get(project, 0), 'liked': True})
            finally:
                db.close()

        if path == '/api/admin/clear-cache' and self.command == 'POST':
            if not check_admin(self):
                return self.send_error_json('需要管理员权限', 401)
            # 清理频率限制缓存
            with _rate_lock:
                _ip_request_log.clear()
                _user_request_log.clear()
            return self.send_json({'success': True, 'message': '缓存已清除'})

        if path == '/api/admin/ai-stats' and self.command == 'GET':
            if not check_admin(self):
                return self.send_error_json('需要管理员权限', 401)
            now = time.time()
            # 统计当前活跃的 IP 和用户
            active_ips = {ip: len([t for t in times if now - t < 60]) for ip, times in _ip_request_log.items()}
            active_users = {uid: len([t for t in times if now - t < 3600]) for uid, times in _user_request_log.items()}
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            db = get_db()
            try:
                cur = db.execute("SELECT username, SUM(count) as total FROM ai_usage WHERE date = ? GROUP BY username ORDER BY total DESC LIMIT 20", (today,))
                usage_stats = [{'username': r['username'], 'count': r['total']} for r in cur.fetchall()]
            finally:
                db.close()
            return self.send_json({
                'activeIPs': len(active_ips),
                'activeUsers': len(active_users),
                'todayUsage': usage_stats,
                'rateLimitConfig': {
                    'dailyUserLimit': AI_DAILY_USER_LIMIT,
                    'rateLimitSeconds': AI_RATE_LIMIT_SECONDS,
                    'ipRateLimit': AI_IP_RATE_LIMIT,
                }
            })

        if path == '/api/user/conversations':
            user = get_current_user(self)
            if not user:
                return self.send_error_json('请先登录', 401)
            conv_id = body.get('id')
            title = body.get('title', '')
            messages = body.get('messages', [])
            now = int(time.time())
            db = get_db()
            try:
                if conv_id:
                    db.execute("UPDATE conversations SET title = ?, messages = ?, updated_at = ? WHERE id = ? AND user_id = ?",
                               (title, json.dumps(messages, ensure_ascii=False), now, conv_id, user['id']))
                else:
                    cur = db.execute("INSERT INTO conversations (user_id, title, messages, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                                   (user['id'], title, json.dumps(messages, ensure_ascii=False), now, now))
                    conv_id = cur.lastrowid
                db.commit()
                return self.send_json({'success': True, 'id': conv_id})
            finally:
                db.close()

        if path == '/api/user/conversations/delete':
            user = get_current_user(self)
            if not user:
                return self.send_error_json('请先登录', 401)
            conv_id = body.get('id')
            if conv_id:
                db = get_db()
                try:
                    db.execute("DELETE FROM conversations WHERE id = ? AND user_id = ?", (conv_id, user['id']))
                    db.commit()
                finally:
                    db.close()
            return self.send_json({'success': True})

        if path == '/api/user/conversations/clear':
            user = get_current_user(self)
            if not user:
                return self.send_error_json('请先登录', 401)
            db = get_db()
            try:
                db.execute("DELETE FROM conversations WHERE user_id = ?", (user['id'],))
                db.commit()
            finally:
                db.close()
            return self.send_json({'success': True})

        if path == '/api/user/bookmarks':
            user = get_current_user(self)
            if not user:
                return self.send_error_json('请先登录', 401)
            project_path = body.get('project_path', '')
            project_name = body.get('project_name', '')
            project_icon = body.get('project_icon', '')
            if not project_path:
                return self.send_error_json('缺少 project_path 参数', 400)
            db = get_db()
            try:
                # Toggle 逻辑
                cur = db.execute("SELECT id FROM bookmarks WHERE user_id = ? AND project_path = ?", (user['id'], project_path))
                existing = cur.fetchone()
                if existing:
                    db.execute("DELETE FROM bookmarks WHERE id = ?", (existing['id'],))
                    db.commit()
                    return self.send_json({'bookmarked': False})
                else:
                    db.execute("INSERT INTO bookmarks (user_id, project_path, project_name, project_icon, created_at) VALUES (?, ?, ?, ?, ?)",
                               (user['id'], project_path, project_name, project_icon, int(time.time())))
                    db.commit()
                    return self.send_json({'bookmarked': True})
            finally:
                db.close()

        if path == '/api/user/recent':
            user = get_current_user(self)
            if not user:
                return self.send_error_json('请先登录', 401)
            project_path = body.get('project_path', '')
            project_name = body.get('project_name', '')
            project_icon = body.get('project_icon', '')
            if not project_path:
                return self.send_error_json('缺少 project_path 参数', 400)
            db = get_db()
            try:
                # 如果已存在，更新 visited_at
                cur = db.execute("SELECT id FROM recent_visits WHERE user_id = ? AND project_path = ?", (user['id'], project_path))
                existing = cur.fetchone()
                now = int(time.time())
                if existing:
                    db.execute("UPDATE recent_visits SET visited_at = ?, project_name = ?, project_icon = ? WHERE id = ?",
                               (now, project_name, project_icon, existing['id']))
                else:
                    # 检查数量，超过10条删除最旧的
                    cur = db.execute("SELECT COUNT(*) as cnt FROM recent_visits WHERE user_id = ?", (user['id'],))
                    count = cur.fetchone()['cnt']
                    if count >= 10:
                        db.execute("DELETE FROM recent_visits WHERE user_id = ? AND id NOT IN (SELECT id FROM recent_visits WHERE user_id = ? ORDER BY visited_at DESC LIMIT 9)",
                                   (user['id'], user['id']))
                    db.execute("INSERT INTO recent_visits (user_id, project_path, project_name, project_icon, visited_at) VALUES (?, ?, ?, ?, ?)",
                               (user['id'], project_path, project_name, project_icon, now))
                db.commit()
                return self.send_json({'success': True})
            finally:
                db.close()

        if path == '/api/api-keys':
            user = get_current_user(self)
            if not user:
                return self.send_error_json('请先登录', 401)
            name = body.get('name', '').strip() or f'Key-{int(time.time())}'
            desc = body.get('desc', '').strip()[:100]
            daily_limit = 0
            try:
                daily_limit = max(0, int(body.get('daily_limit') or 0))
            except (TypeError, ValueError):
                daily_limit = 0
            expires_at = body.get('expires_at') or 0
            try:
                expires_at = int(expires_at)
            except (TypeError, ValueError):
                expires_at = 0
            key = generate_api_key()
            db = get_db()
            try:
                db.execute(
                    "INSERT INTO api_keys (user_id, username, key, name, desc, daily_limit, expires_at, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (user['id'], user['username'], key, name, desc, daily_limit, expires_at, int(time.time()))
                )
                db.commit()
                return self.send_json({'success': True, 'key': key, 'name': name})
            finally:
                db.close()

        # ========= Ollama 代理端点 =========
        if path.startswith('/api/ollama'):
            # 代理到 Ollama 服务器
            cu = get_current_user(self)
            if not cu:
                return self.send_error_json('请先登录', 401)
            
            # 转发到 Ollama（使用已读取的 raw 数据，避免重复读取 rfile）
            ollama_path = path.replace('/api/ollama', '')
            if not ollama_path:
                ollama_path = '/api/tags'  # 默认列出模型
            
            target_url = f"{OLLAMA_URL}{ollama_path}"
            print(f'[Ollama Proxy] {path} -> {target_url}', file=sys.stderr)
            
            try:
                req = urllib.request.Request(
                    target_url,
                    data=raw if raw else None,
                    method=self.command,
                    headers={
                        'Content-Type': self.headers.get('Content-Type', 'application/json'),
                    }
                )
                with urllib.request.urlopen(req, timeout=180) as resp:
                    resp_data = resp.read()
                    self.send_response(resp.status)
                    self.send_header('Content-Type', resp.headers.get('Content-Type', 'application/json'))
                    self.send_header('Content-Length', len(resp_data))
                    self.end_headers()
                    self.wfile.write(resp_data)
            except urllib.error.HTTPError as e:
                err_body = e.read()
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(err_body)
            except Exception as e:
                self.send_error_json(f'Ollama 请求失败: {str(e)}', 500)
            return

        if path == '/api/recommend':
            cu = get_current_user(self)
            if not cu:
                api_key = get_api_key_from_request(self)
                if api_key:
                    cu, _ = get_user_by_api_key(api_key)
                if not cu:
                    return self.send_error_json('请先登录或提供有效的 API Key', 401)
            messages = body.get('messages', [])
            model = body.get('model', '')
            if not messages:
                return self.send_error_json('请输入消息', 400)

            # === 安全检查 1：频率限制 ===
            client_ip = get_client_ip(self)
            allowed, reason = check_rate_limit(
                user_id=cu['id'] if cu else None,
                ip=client_ip
            )
            if not allowed:
                return self.send_error_json(reason, 429)

            # === 安全检查 2：每日调用次数上限 ===
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            db = get_db()
            try:
                cur = db.execute("SELECT COALESCE(SUM(count), 0) AS cnt FROM ai_usage WHERE user_id = ? AND date = ?", (cu['id'], today))
                row = cur.fetchone()
                used = row['cnt'] if row else 0
                if used >= AI_DAILY_USER_LIMIT:
                    return self.send_error_json(f'今日 AI 调用次数已达上限（{AI_DAILY_USER_LIMIT} 次），请明天再来', 429)
            finally:
                db.close()

            # === 安全检查 3：敏感词过滤 ===
            user_messages = [m.get('content', '') for m in messages if m.get('role') == 'user']
            all_user_text = ' '.join(user_messages)
            sensitive_hits = check_sensitive_content(all_user_text)
            if sensitive_hits:
                print(f'[AI 安全] 用户 {cu["username"]} 提交敏感内容: {sensitive_hits}', file=sys.stderr)
                return self.send_error_json('抱歉，您的输入包含不适当内容，请重新输入', 400)

            try:
                # ========= 内存缓存检查 =========
                cache_key = hashlib.md5(
                    json.dumps(messages, sort_keys=True).encode()
                ).hexdigest()
                cached = _ai_cache.get(f"ai:{cache_key}")
                if cached:
                    # 缓存命中，直接返回
                    if cu:
                        record_ai_usage(cu['id'], cu['username'])
                    cached['cached'] = True
                    cached['serverCache'] = True
                    return self.send_json(cached)

                projects = read_json_file(BASE_DIR / 'project-list.json') or []
                # 限制项目数量到20个以控制prompt长度（Ollama小模型处理能力有限）
                max_projects = min(len(projects), 20)
                selected_projects = projects[:max_projects]
                project_list = '\n'.join([
                    f"- {p.get('name','')} (path: {p.get('path','')}, type: {p.get('type','unknown')})"
                    for p in selected_projects
                ])
                system_prompt = f"""你是编程助手"小码"。和用户自然聊天、解答编程问题、推荐项目。

可用项目（前{max_projects}个）：
{project_list}

推荐时用JSON格式附在回复末尾：
---RECOMMEND---
[{{"path":"项目路径","reason":"理由","name":"名称"}}]
---END---
用户: {messages[-1].get('content','')}
助手:"""

                # === 联网搜索：检测是否需要搜索并注入搜索结果 ===
                web_search_enabled = body.get('web_search', False)
                search_query = None
                if web_search_enabled or any(kw in all_user_text for kw in ['今天', '最新', '最近', '新闻', '天气', '股价', '实时', '现在', '目前', '搜索', 'search']):
                    # 提取最后一条用户消息作为搜索查询
                    for m in reversed(messages):
                        if m.get('role') == 'user':
                            content = m.get('content', '')
                            if isinstance(content, str):
                                search_query = content[:200]
                            elif isinstance(content, list):
                                search_query = ' '.join(
                                    p.get('text', '') or p.get('image_url', {}).get('url', '')
                                    for p in content if isinstance(p, dict)
                                )[:200]
                            if search_query:
                                break

                search_results_text = ''
                if search_query:
                    try:
                        search_results = web_search(search_query, max_results=3)
                        if search_results:
                            search_results_text = '\n\n【联网搜索结果】\n'
                            for i, r in enumerate(search_results, 1):
                                search_results_text += f"{i}. [{r['title']}]({r['url']})\n   {r['snippet'][:150]}\n"
                    except Exception:
                        pass

                if search_results_text:
                    system_prompt += search_results_text

                text = ''
                reasoning = ''
                ollama_ok = False

                if USE_OLLAMA:
                    # 模型选择逻辑：支持 ollama/text、ollama/vision 前缀，或直接指定模型名
                    ollama_model_name = None
                    if model and model.startswith('ollama/'):
                        model_key = model[len('ollama/'):]
                        if model_key in OLLAMA_MODELS:
                            ollama_model_name = OLLAMA_MODELS[model_key]['model']
                        else:
                            ollama_model_name = model_key
                    elif model and model in OLLAMA_MODELS:
                        ollama_model_name = OLLAMA_MODELS[model]['model']
                    else:
                        ollama_model_name = OLLAMA_MODEL

                    # 检查是否包含图片（vision 模型）
                    has_images = any(
                        isinstance(m.get('content'), list) and
                        any(p.get('type') == 'image_url' or p.get('type') == 'image' for p in m.get('content', []))
                        for m in messages
                    )

                    # 如果用户请求视觉模型或包含图片，自动切换到视觉模型
                    if has_images and ollama_model_name == OLLAMA_MODELS['text']['model']:
                        ollama_model_name = OLLAMA_MODELS['vision']['model']

                    # 内存管理：确保只加载当前需要的模型
                    _ensure_model_loaded(ollama_model_name)

                    # 构建 Ollama payload（keep_alive 设置为300秒，配合后台定时器）
                    ollama_payload = {
                        'model': ollama_model_name,
                        'messages': [{'role': 'system', 'content': system_prompt}, *messages],
                        'stream': False,
                        'keep_alive': f'{MODEL_KEEP_ALIVE}s',
                        'options': {'temperature': 0.7}
                    }

                    # 视觉模型支持：如果有图片，添加 images 字段
                    if has_messages_with_images(messages):
                        ollama_payload['images'] = extract_images_from_messages(messages)

                    ollama_req = urllib.request.Request(
                        f'{OLLAMA_URL}/api/chat',
                        data=json.dumps(ollama_payload).encode(),
                        headers={'Content-Type': 'application/json'}
                    )
                    try:
                        with urllib.request.urlopen(ollama_req, timeout=120) as resp:
                            ollama_result = json.loads(resp.read())
                            text = ollama_result.get('message', {}).get('content', '') or ''
                            ollama_ok = bool(text)
                    except urllib.error.URLError as ollama_err:
                        print(f'[Ollama] 连接失败: {ollama_err}', file=sys.stderr)
                    except Exception as ollama_err2:
                        print(f'[Ollama] 请求异常: {ollama_err2}', file=sys.stderr)

                    # 请求完成后更新最后使用时间，由后台定时器负责自动卸载
                    if ollama_ok:
                        global _model_last_used
                        _model_last_used = time.time()

                if not ollama_ok and OPENROUTER_API_KEY:
                    api_url = OPENROUTER_API_URL
                    api_key = OPENROUTER_API_KEY
                    actual_model = model if model and not model.startswith('ollama/') else 'openrouter/free'
                    payload = {
                        'model': actual_model,
                        'messages': [{'role': 'system', 'content': system_prompt}, *messages],
                        'temperature': 0.7,
                        'max_tokens': 800,
                        'reasoning': {'enabled': True},
                    }
                    headers = {
                        'Authorization': f'Bearer {api_key}',
                        'Content-Type': 'application/json',
                        'HTTP-Referer': 'https://codingzhou.dpdns.org',
                        'X-Title': 'Code Explorer',
                    }
                    req = urllib.request.Request(api_url, data=json.dumps(payload).encode(), headers=headers)
                    with urllib.request.urlopen(req, timeout=60) as resp:
                        result = json.loads(resp.read())
                        choice = result.get('choices', [{}])[0]
                        msg = choice.get('message', {})
                        text = msg.get('content', '') or ''
                        reasoning = msg.get('reasoning_content', '') or ''

                if not text and not OPENROUTER_API_KEY:
                    if USE_OLLAMA:
                        return self.send_error_json('AI 功能不可用：Ollama 未连接且未配置 OpenRouter 备用。请确认 Ollama 服务已启动。', 503)
                    return self.send_error_json('AI 功能不可用：未配置 AI 服务', 503)

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
                if cu:
                    record_ai_usage(cu['id'], cu['username'])
                # ========= 存储到内存缓存 =========
                result_data = {'success': True, 'response': text, 'reasoning': reasoning, 'recommendations': recommendations}
                _ai_cache.set(f"ai:{cache_key}", result_data, ttl=600)
                return self.send_json(result_data)
            except Exception as e:
                import traceback
                print(f'AI Error: {traceback.format_exc()}', file=sys.stderr)
                return self.send_error_json(f'AI 请求失败: {e}', 500)

        if path == '/api/run/start':
            if not check_auth(self):
                return self.send_error_json('请先登录', 401)
            self.handle_run_start(body)
            return

        if path == '/api/run/stop':
            if not check_auth(self):
                return self.send_error_json('请先登录', 401)
            self.handle_run_stop(body)
            return

        if path == '/api/scratch/upload':
            user = get_current_user(self)
            if not user:
                return self.send_error_json('请先登录', 401)
            name = body.get('name', '').strip()
            data = body.get('data', '')
            if not name or not data:
                return self.send_error_json('缺少项目名称或文件数据', 400)
            try:
                raw = base64.b64decode(data)
            except Exception:
                return self.send_error_json('文件数据格式错误', 400)
            # 确保存储目录存在
            projects_dir = BASE_DIR / 'scratch' / 'projects' / str(user['id'])
            projects_dir.mkdir(parents=True, exist_ok=True)
            filename = uuid.uuid4().hex + '.sb3'
            file_path = projects_dir / filename
            file_path.write_bytes(raw)
            now = int(time.time())
            db = get_db()
            try:
                cur = db.execute(
                    "INSERT INTO scratch_projects (user_id, name, filename, file_size, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (user['id'], name, filename, len(raw), now, now)
                )
                db.commit()
                project_id = cur.lastrowid
                return self.send_json({
                    'id': project_id,
                    'name': name,
                    'filename': filename,
                    'file_size': len(raw),
                    'created_at': now,
                    'updated_at': now,
                })
            finally:
                db.close()

        if path.startswith('/api/scratch/projects/') and path.endswith('/delete'):
            user = get_current_user(self)
            if not user:
                return self.send_error_json('请先登录', 401)
            try:
                project_id = int(path.split('/')[4])
            except (ValueError, IndexError):
                return self.send_error_json('无效的项目ID', 400)
            db = get_db()
            try:
                cur = db.execute("SELECT * FROM scratch_projects WHERE id = ? AND user_id = ?", (project_id, user['id']))
                project = cur.fetchone()
                if not project:
                    return self.send_error_json('项目不存在', 404)
                project = dict(project)
                file_path = BASE_DIR / 'scratch' / 'projects' / str(user['id']) / project['filename']
                if file_path.exists():
                    file_path.unlink()
                db.execute("DELETE FROM scratch_projects WHERE id = ?", (project_id,))
                db.commit()
                return self.send_json({'success': True})
            finally:
                db.close()

        self.send_error(404)

    class SSEStreamer:
        def __init__(self, handler):
            self.handler = handler
            self.started = False
            self.closed = False
            self._last_send = 0

        def start(self):
            if self.started:
                return
            self.handler.send_response(200)
            self.handler.send_header('Content-Type', 'text/event-stream; charset=utf-8')
            self.handler.send_header('Cache-Control', 'no-cache, no-transform')
            self.handler.send_header('Connection', 'keep-alive')
            self.handler.send_header('X-Accel-Buffering', 'no')
            self.handler.send_header('Access-Control-Allow-Origin', '*')
            self.handler.end_headers()
            self.started = True
            self._last_send = time.time()

        def send(self, event, data):
            if self.closed:
                return
            try:
                payload = f'event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n'
                self.handler.wfile.write(payload.encode('utf-8'))
                self.handler.wfile.flush()
                self._last_send = time.time()
            except (BrokenPipeError, ConnectionResetError):
                self.closed = True

        def heartbeat(self):
            """发送SSE注释心跳，保持连接活跃（防止代理超时）"""
            if self.closed:
                return
            now = time.time()
            if now - self._last_send < 10:
                return  # 10秒内有数据就不发送
            try:
                self.handler.wfile.write(b': heartbeat\n\n')
                self.handler.wfile.flush()
                self._last_send = now
            except (BrokenPipeError, ConnectionResetError):
                self.closed = True

        def close(self):
            self.closed = True

    def handle_run_start(self, body):
        mode = body.get('mode', 'single')
        timeout = min(int(body.get('timeout', DEFAULT_TIMEOUT)), MAX_TIMEOUT)
        run_id = uuid.uuid4().hex[:12]

        sse = self.SSEStreamer(self)
        sse.start()

        def emit(event, data):
            sse.send(event, data)

        def heartbeat():
            sse.heartbeat()

        temp_dir = None
        process = None

        try:
            with processes_lock:
                if len(active_processes) >= MAX_CONCURRENT_RUNS:
                    emit('error', {'message': '服务器繁忙，请稍后重试'})
                    return

            emit('status', {'phase': 'preparing', 'runId': run_id, 'message': '准备执行环境...'})

            temp_dir = Path(tempfile.mkdtemp(prefix=f'run-{run_id}-', dir=str(RUNS_DIR)))

            python_bin = None
            entry_file = 'main.py'

            if mode == 'single':
                code = body.get('code', '')
                if not code.strip():
                    emit('error', {'message': '代码为空'})
                    return

                imports = detect_imports(code)
                emit('status', {'phase': 'analyzing', 'message': f'检测到 {len(imports)} 个第三方依赖'})
                heartbeat()

                # 单文件使用与项目不同的虚拟环境 key（避免污染项目环境）
                file_name = body.get('fileName', 'script.py')
                venv_key = '__single_file__::' + (file_name or 'script.py')
                python_bin = ensure_venv(venv_key, emit, heartbeat)

                if imports:
                    # 使用 pip list 改进的检测方法
                    missing = []
                    for pkg in imports:
                        if not check_package_installed(python_bin, pkg):
                            missing.append(pkg)
                    if missing:
                        install_dependencies(python_bin, missing, emit, heartbeat)
                    else:
                        emit('deps', {'phase': 'installed', 'message': '所有依赖已就绪'})

                entry_file = 'script.py'
                (temp_dir / entry_file).write_text(code, encoding='utf-8')

            elif mode == 'project':
                project_path = body.get('projectPath', '')
                entry_file = body.get('entryFile', 'main.py')
                file_overrides = body.get('files', {})

                if not project_path:
                    emit('error', {'message': '缺少项目路径'})
                    return

                root = _find_projects_root()
                project_dir = None
                for sp in [root / project_path, BASE_DIR.parent.parent / project_path,
                           BASE_DIR.parent / project_path, BASE_DIR / project_path]:
                    try:
                        if sp.exists() and sp.is_dir():
                            project_dir = sp.resolve()
                            break
                    except Exception:
                        continue

                if not project_dir:
                    emit('error', {'message': f'项目不存在: {project_path}'})
                    return

                emit('status', {'phase': 'copying', 'message': '复制项目文件...'})
                heartbeat()

                skip_dirs = {'__pycache__', '.git', 'node_modules', '.venv', 'venv', '.idea', '.vscode'}
                file_count = 0
                for item in project_dir.rglob('*'):
                    if any(part in skip_dirs for part in item.parts):
                        continue
                    rel = item.relative_to(project_dir)
                    dest = temp_dir / rel
                    if item.is_dir():
                        dest.mkdir(exist_ok=True)
                    elif item.is_file():
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        rel_str = str(rel).replace('\\', '/')
                        if rel_str in file_overrides:
                            dest.write_text(file_overrides[rel_str], encoding='utf-8')
                        else:
                            shutil.copy2(str(item), str(dest))
                        file_count += 1
                        if file_count % 20 == 0:
                            heartbeat()

                for rel_path, content in file_overrides.items():
                    dest = temp_dir / rel_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(content, encoding='utf-8')

                emit('status', {'phase': 'venv', 'message': '准备项目虚拟环境...'})
                heartbeat()
                python_bin = ensure_venv(project_path, emit, heartbeat)

                if not install_deps_for_dir(python_bin, temp_dir, skip_dirs, emit, heartbeat):
                    return

            elif mode == 'multi':
                files = body.get('files', {})
                entry_file = body.get('entryFile', 'main.py')
                venv_key = body.get('venvKey', '')
                if not isinstance(files, dict) or not files:
                    emit('error', {'message': '缺少文件内容'})
                    return

                skip_dirs = {'__pycache__', '.git', 'node_modules', '.venv', 'venv', '.idea', '.vscode'}
                emit('status', {'phase': 'copying', 'message': '写入项目文件...'})
                heartbeat()

                file_count = 0
                for rel_path, content in files.items():
                    rel = rel_path.replace('\\', '/').lstrip('/')
                    if not rel or '..' in rel.split('/'):
                        emit('error', {'message': f'非法文件路径: {rel_path}'})
                        return
                    dest = temp_dir / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(content, encoding='utf-8')
                    file_count += 1
                    if file_count % 20 == 0:
                        heartbeat()

                if not venv_key:
                    venv_key = '__multi_file__'
                emit('status', {'phase': 'venv', 'message': '准备虚拟环境...'})
                heartbeat()
                python_bin = ensure_venv(venv_key, emit, heartbeat)

                if not install_deps_for_dir(python_bin, temp_dir, skip_dirs, emit, heartbeat):
                    return

            else:
                emit('error', {'message': f'不支持的模式: {mode}'})
                return

            if not (temp_dir / entry_file).exists():
                py_files = list(temp_dir.rglob('*.py'))
                if py_files:
                    entry_file = str(py_files[0].relative_to(temp_dir)).replace('\\', '/')
                    emit('status', {'phase': 'running', 'message': f'入口文件不存在，自动选择: {entry_file}'})
                else:
                    emit('error', {'message': f'入口文件不存在: {entry_file}'})
                    return

            # 检测 GUI 模块（在无头服务器环境中无法显示图形界面）
            all_gui_blocking = set()
            all_gui_warning = set()
            # 收集每个 GUI 模块的 import 位置（文件名 + 行号 + 代码行）
            gui_locations = {}  # {模块名: [(file_label, line_no, line_text), ...]}
            all_py_files_count = 0
            try:
                # 读取所有 Python 文件检测 GUI 模块
                for py_file in temp_dir.rglob('*.py'):
                    try:
                        all_py_files_count += 1
                        code_content = py_file.read_text(encoding='utf-8', errors='replace')
                        blocking, warning = detect_gui_modules(code_content)
                        all_gui_blocking.update(blocking)
                        all_gui_warning.update(warning)
                        # 定位 GUI import 的具体行号
                        rel_label = str(py_file.relative_to(temp_dir)).replace('\\', '/')
                        locs = find_gui_import_locations(code_content, rel_label)
                        for mod, loc_list in locs.items():
                            gui_locations.setdefault(mod, []).extend(loc_list)
                    except Exception:
                        pass

                # 额外检查：标准库 GUI 模块（如 turtle/tkinter）是否真的可用
                stl_gui_modules = {'turtle', 'tkinter', 'turtledemo', 'Tkinter'}
                for mod in list(all_gui_blocking):
                    if mod in stl_gui_modules:
                        if not check_stl_module_available(python_bin, mod):
                            # 标准库 GUI 模块不可用（Python 编译时未包含 Tk 支持）
                            loc_report = format_gui_locations_report(
                                {mod: gui_locations.get(mod, [])},
                                total_files=all_py_files_count
                            )
                            err_msg = (
                                '检测到使用了 ' + mod + ' 模块，但当前服务器环境不支持图形界面。\n\n'
                                '原因：服务器是无图形界面的 Linux 环境，Python 未包含 Tkinter 支持。\n'
                                'turtle、tkinter 等 GUI 程序需要在本地电脑上运行才能显示窗口。\n\n'
                                '建议：请在本地安装 Python 后运行此代码。'
                                + loc_report
                            )
                            emit('error', {
                                'message': err_msg
                            })
                            return
                        else:
                            # 模块可导入但仍无显示器，给出警告
                            all_gui_warning.add(mod)
                            all_gui_blocking.discard(mod)

                # 阻塞型 GUI 模块提示（即使能 import 也无法显示窗口）
                if all_gui_blocking:
                    modules_list = ', '.join(sorted(all_gui_blocking))
                    loc_report = format_gui_locations_report(
                        {m: gui_locations.get(m, []) for m in all_gui_blocking},
                        total_files=all_py_files_count
                    )
                    err_msg = (
                        '检测到使用了图形界面模块: ' + modules_list + '\n\n'
                        '当前服务器是无显示器的 Linux 环境，无法运行需要图形窗口的程序。\n'
                        '这类程序（如 pygame、PyQt、turtle 绘图等）需要在本地电脑上运行，\n'
                        '才能正常弹出窗口和显示画面。\n\n'
                        '非图形部分（如计算逻辑）仍可尝试执行，但图形界面功能将不可用。\n'
                        '如果程序不依赖图形界面显示结果，可以修改代码移除 GUI 相关 import 后重试。'
                        + loc_report
                    )
                    emit('error', {
                        'message': err_msg
                    })
                    return

                # 警告型 GUI 模块（可以运行但可能报错或不显示图形）
                if all_gui_warning:
                    modules_list = ', '.join(sorted(all_gui_warning))
                    loc_report = format_gui_locations_report(
                        {m: gui_locations.get(m, []) for m in all_gui_warning},
                        total_files=all_py_files_count
                    )
                    emit('stderr', {
                        'text': '[警告] 检测到图形相关模块: ' + modules_list + '。服务器无显示器，图形界面可能无法正常显示。'
                                + loc_report + '\n'
                    })
            except Exception as e:
                # GUI 检测失败不影响正常执行
                pass

            def set_resource_limits():
                try:
                    import resource
                    resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout))
                    mem_limit = 512 * 1024 * 1024
                    resource.setrlimit(resource.RLIMIT_AS, (mem_limit, mem_limit))
                    fsize_limit = 64 * 1024 * 1024
                    resource.setrlimit(resource.RLIMIT_FSIZE, (fsize_limit, fsize_limit))
                    resource.setrlimit(resource.RLIMIT_NPROC, (32, 32))
                except Exception:
                    pass

            preexec_fn = set_resource_limits
            if RUN_AS_USER and os.name != 'nt':
                try:
                    import pwd
                    pw = pwd.getpwnam(RUN_AS_USER)
                    run_uid, run_gid = pw.pw_uid, pw.pw_gid
                    def switch_user():
                        set_resource_limits()
                        os.setgid(run_gid)
                        os.setuid(run_uid)
                    preexec_fn = switch_user
                except Exception:
                    pass

            emit('status', {'phase': 'running', 'message': '开始执行...'})

            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            env['PYTHONIOENCODING'] = 'utf-8'
            venv_bin = python_bin.parent
            env['PATH'] = f'{venv_bin}:{env.get("PATH", "")}'
            env['VIRTUAL_ENV'] = str(python_bin.parent.parent)

            process = subprocess.Popen(
                [str(python_bin), '-u', entry_file],
                cwd=str(temp_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1,
                env=env,
                preexec_fn=preexec_fn if os.name != 'nt' else None,
            )

            with processes_lock:
                active_processes[run_id] = {
                    'process': process,
                    'temp_dir': temp_dir,
                    'start_time': time.time(),
                    'mode': mode
                }

            output_size = [0]
            timed_out = [False]
            start_time = time.time()

            def reader_thread(stream, event_type):
                try:
                    for line in iter(stream.readline, ''):
                        output_queue.put((event_type, line))
                        if process.poll() is not None:
                            remaining = output_queue.qsize()
                            for _ in range(remaining):
                                pass
                            break
                except Exception:
                    pass
                finally:
                    output_queue.put(('done', event_type))

            output_queue = queue.Queue()
            t_stdout = threading.Thread(target=reader_thread, args=(process.stdout, 'stdout'), daemon=True)
            t_stderr = threading.Thread(target=reader_thread, args=(process.stderr, 'stderr'), daemon=True)
            t_stdout.start()
            t_stderr.start()

            done_count = 0
            last_hb = time.time()
            while done_count < 2:
                elapsed = time.time() - start_time
                remaining = timeout - elapsed

                if remaining <= 0:
                    timed_out[0] = True
                    process.kill()
                    emit('stderr', {'text': f'\n[执行超时：超过{timeout}秒]\n'})
                    break

                try:
                    event_type, line = output_queue.get(timeout=min(remaining, 0.5))
                    if event_type == 'done':
                        done_count += 1
                        continue
                    output_size[0] += len(line)
                    if output_size[0] > MAX_OUTPUT_SIZE:
                        emit(event_type, {'text': '\n[输出被截断：超过最大限制]\n'})
                        process.kill()
                        break
                    emit(event_type, {'text': line})
                except queue.Empty:
                    if process.poll() is not None:
                        continue
                    # 定期发送心跳保持连接
                    if time.time() - last_hb > 5:
                        heartbeat()
                        last_hb = time.time()

            t_stdout.join(timeout=2)
            t_stderr.join(timeout=2)

            returncode = process.poll()
            if timed_out[0]:
                emit('exit', {'code': -1, 'timedOut': True, 'message': f'执行超时（{timeout}秒）'})
            else:
                msg = '执行完成' if returncode == 0 else f'执行出错（退出码: {returncode}）'
                emit('exit', {'code': returncode, 'timedOut': False, 'message': msg})

        except Exception as e:
            import traceback
            traceback.print_exc()
            emit('error', {'message': f'执行失败: {str(e)}'})

        finally:
            if process and process.poll() is None:
                try:
                    process.kill()
                    process.wait(timeout=3)
                except Exception:
                    pass

            with processes_lock:
                active_processes.pop(run_id, None)

            # 关闭 SSE 连接，防止客户端一直等待
            sse.close()
            try:
                self.wfile.flush()
            except Exception:
                pass
            self.close_connection = True

            if temp_dir:
                def cleanup_temp():
                    time.sleep(5)
                    try:
                        shutil.rmtree(str(temp_dir), ignore_errors=True)
                    except Exception:
                        pass
                threading.Thread(target=cleanup_temp, daemon=True).start()

    def handle_run_stop(self, body):
        run_id = body.get('runId', '')
        with processes_lock:
            proc_info = active_processes.get(run_id)

        if not proc_info:
            return self.send_json({'success': False, 'message': '未找到运行中的进程'}, 404)

        process = proc_info['process']
        try:
            if process.poll() is None:
                if os.name != 'nt':
                    try:
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                        time.sleep(1)
                        if process.poll() is None:
                            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    except Exception:
                        process.kill()
                else:
                    process.kill()
                process.wait(timeout=3)
            self.send_json({'success': True, 'message': '进程已终止'})
        except Exception as e:
            self.send_json({'success': False, 'message': f'终止失败: {e}'}, 500)

    def log_message(self, format, *args):
        pass


init_db()

if __name__ == '__main__':
    if USE_OLLAMA:
        os.environ.setdefault('OLLAMA_MAX_LOADED_MODELS', '1')
        _start_model_cleanup_timer()

    print(f'Code Explorer 服务器启动: http://{HOST}:{PORT}')
    print(f'BASE_DIR: {BASE_DIR}')
    print(f'PROJECTS_ROOT: {_find_projects_root()}')
    print(f'USER_PASSWORD: {"已设置" if USER_PASSWORD else "未设置"}')
    print(f'ADMIN_PASSWORD: {"已设置" if ADMIN_PASSWORD else "未设置"}')
    print(f'[Ollama] 本地AI: {"启用" if USE_OLLAMA else "禁用"} | 模型: {OLLAMA_MODEL} | URL: {OLLAMA_URL}')
    if USE_OLLAMA:
        print(f'[Ollama] 文本模型: {OLLAMA_MODELS["text"]["model"]} | 视觉模型: {OLLAMA_MODELS["vision"]["model"]}')
        print(f'[Ollama] 模型保留时间: {MODEL_KEEP_ALIVE}秒 | 最大加载数: 1')
    print(f'[OpenRouter] 备用AI: {"已设置" if OPENROUTER_API_KEY else "未设置"}')
    with http.server.HTTPServer((HOST, PORT), MyHandler) as httpd:
        httpd.serve_forever()
