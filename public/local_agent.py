#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code Explorer 本地伴生程序
============================
在本地电脑上运行此程序，即可通过 Code Explorer 网站浏览并运行本地 Python 项目。

使用方法:
    python local_agent.py [--port PORT] [--projects-dir PATH]

    --port        监听端口 (默认: 18765)
    --projects-dir 项目根目录 (默认: 脚本所在目录)

示例:
    python local_agent.py
    python local_agent.py --port 9999
    python local_agent.py --projects-dir D:/my-python-projects
"""

import ast
import http.server
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import uuid
from pathlib import Path

# ==================== 配置 ====================

DEFAULT_PORT = 18765
DEFAULT_TIMEOUT = 120
MAX_TIMEOUT = 600
MAX_OUTPUT_SIZE = 4 * 1024 * 1024  # 4MB

# Python 标准库模块
STDLIB_MODULES = {
    'abc', 'argparse', 'array', 'ast', 'asyncio', 'base64', 'binascii',
    'bisect', 'builtins', 'bz2', 'calendar', 'cgi', 'cmath', 'cmd',
    'code', 'codecs', 'collections', 'colorsys', 'compileall',
    'concurrent', 'configparser', 'contextlib', 'copy', 'copyreg',
    'csv', 'ctypes', 'dataclasses', 'datetime', 'decimal', 'difflib',
    'dis', 'email', 'encodings', 'enum', 'errno', 'faulthandler',
    'filecmp', 'fileinput', 'fnmatch', 'fractions', 'ftplib', 'functools',
    'gc', 'getopt', 'getpass', 'gettext', 'glob', 'gzip', 'hashlib',
    'heapq', 'hmac', 'html', 'http', 'idlelib', 'imaplib', 'importlib',
    'inspect', 'io', 'ipaddress', 'itertools', 'json', 'keyword',
    'linecache', 'locale', 'logging', 'lzma', 'mailbox', 'marshal',
    'math', 'mimetypes', 'mmap', 'modulefinder', 'multiprocessing',
    'numbers', 'operator', 'optparse', 'os', 'pathlib', 'pdb', 'pickle',
    'pickletools', 'pipes', 'pkgutil', 'platform', 'plistlib', 'pprint',
    'profile', 'pstats', 'py_compile', 'pyclbr', 'pydoc', 'queue', 'random',
    're', 'readline', 'reprlib', 'rlcompleter', 'runpy', 'sched',
    'secrets', 'select', 'selectors', 'shlex', 'shutil', 'signal',
    'site', 'smtplib', 'socket', 'socketserver', 'sqlite3', 'ssl',
    'stat', 'statistics', 'string', 'struct', 'subprocess', 'symtable',
    'sys', 'sysconfig', 'tabnanny', 'tarfile', 'telnetlib', 'tempfile',
    'termios', 'test', 'textwrap', 'threading', 'time', 'timeit',
    'tkinter', 'token', 'tokenize', 'trace', 'traceback', 'tracemalloc',
    'tty', 'types', 'typing', 'unicodedata', 'unittest', 'urllib',
    'uuid', 'venv', 'warnings', 'wave', 'weakref', 'webbrowser',
    'xml', 'xmlrpc', 'zipapp', 'zipfile', 'zlib', '_thread',
    '__future__', 'pkg_resources', 'setuptools', 'pip',
}

IMPORT_TO_PIP = {
    'cv2': 'opencv-python',
    'PIL': 'Pillow',
    'yaml': 'pyyaml',
    'sklearn': 'scikit-learn',
    'bs4': 'beautifulsoup4',
    'numpy': 'numpy',
    'pandas': 'pandas',
    'matplotlib': 'matplotlib',
    'flask': 'flask',
    'django': 'django',
    'torch': 'torch',
    'tensorflow': 'tensorflow',
    'openai': 'openai',
    'requests': 'requests',
    'scipy': 'scipy',
    'seaborn': 'seaborn',
    'plotly': 'plotly',
    'rich': 'rich',
    'click': 'click',
    'tqdm': 'tqdm',
    'colorama': 'colorama',
    'termcolor': 'termcolor',
    'dotenv': 'python-dotenv',
    'jwt': 'pyjwt',
    'telegram': 'python-telegram-bot',
    'discord': 'discord.py',
    'skimage': 'scikit-image',
    'xgboost': 'xgboost',
    'lightgbm': 'lightgbm',
    'selenium': 'selenium',
    'playwright': 'playwright',
    'pygame': 'pygame',
    'pyautogui': 'pyautogui',
}

# ==================== 工具函数 ====================

def detect_imports(code):
    """分析代码中的第三方导入"""
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
            third_party.add(pip_name if pip_name else imp)
    return third_party


def scan_projects(root_dir):
    """扫描目录下的 Python 项目"""
    projects = []
    skip_names = {
        '.git', '__pycache__', '.venv', 'venv', 'node_modules',
        '.idea', '.vscode', 'dist', 'build', 'egg-info',
        'code-explorer', 'public',
    }
    try:
        root = Path(root_dir).resolve()
        if not root.exists():
            return projects
        for entry in sorted(root.iterdir()):
            if not entry.is_dir():
                # 单个 .py 文件也作为"项目"展示
                if entry.is_file() and entry.suffix == '.py':
                    projects.append({
                        'name': entry.stem,
                        'path': entry.name,
                        'type': 'single-file',
                        'label': '单文件',
                        'desc': f'单文件脚本',
                        'fileCount': 1,
                        'size': entry.stat().st_size,
                        'mainFile': entry.name,
                        'lastModified': int(entry.stat().st_mtime * 1000),
                    })
                continue
            if entry.name.startswith('.') or entry.name in skip_names:
                continue
            py_files = list(entry.rglob('*.py'))
            if not py_files:
                continue
            # 猜测主文件
            priorities = ['main.py', 'app.py', 'run.py', 'start.py', 'game.py',
                         'Chinese_chess.py', 'index.py', 'server.py']
            main_file = ''
            for p in priorities:
                if (entry / p).exists():
                    main_file = p
                    break
            if not main_file and py_files:
                main_file = py_files[0].name
            # 统计文件类型
            file_types = set()
            for f in entry.iterdir():
                if f.is_file() and f.suffix in ('.html', '.py', '.js', '.css', '.md'):
                    file_types.add(f.suffix)
            has_html = any(f.suffix == '.html' for f in entry.rglob('*'))
            has_py = any(f.suffix == '.py' for f in entry.rglob('*'))
            if has_html and has_py:
                proj_type = 'web-app'
                label = 'Web 应用'
            elif has_py:
                proj_type = 'python'
                label = 'Python'
            else:
                proj_type = 'other'
                label = '其他'
            projects.append({
                'name': entry.name,
                'path': str(entry.relative_to(root)).replace('\\', '/'),
                'type': proj_type,
                'label': label,
                'desc': f'{len(py_files)} 个 Python 文件',
                'fileCount': len(list(entry.rglob('*'))),
                'pyFileCount': len(py_files),
                'mainFile': main_file,
                'hasHTML': has_html,
                'lastModified': int(entry.stat().st_mtime * 1000),
            })
    except PermissionError:
        pass
    except Exception as e:
        print(f"[WARN] 扫描项目时出错: {e}", file=sys.stderr)
    return projects


def scan_files(project_dir, max_depth=3):
    """扫描项目目录的文件树"""
    result = []
    root = Path(project_dir).resolve()
    if not root.exists() or not root.is_dir():
        return result

    skip_names = {'__pycache__', '.git', '.venv', 'venv', 'node_modules',
                  '.idea', '.vscode', 'dist', 'build', 'egg-info'}

    def scan_dir(d, depth):
        if depth > max_depth:
            return
        try:
            entries = sorted(d.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
        except PermissionError:
            return
        for entry in entries:
            if entry.name.startswith('.') or entry.name in skip_names:
                continue
            rel = str(entry.relative_to(root)).replace('\\', '/')
            if entry.is_dir():
                result.append({
                    'name': entry.name,
                    'type': 'directory',
                    'path': rel,
                    'lastModified': int(entry.stat().st_mtime * 1000),
                })
                scan_dir(entry, depth + 1)
            elif entry.is_file():
                ext = entry.suffix.lower()
                result.append({
                    'name': entry.name,
                    'type': 'file',
                    'path': rel,
                    'ext': ext,
                    'size': entry.stat().st_size,
                    'lastModified': int(entry.stat().st_mtime * 1000),
                })

    scan_dir(root, 0)
    return result


def read_file_content(file_path, max_size=512 * 1024):
    """读取文件内容"""
    path = Path(file_path).resolve()
    if not path.exists() or not path.is_file():
        return None
    if path.stat().st_size > max_size:
        return None
    try:
        return path.read_text(encoding='utf-8', errors='replace')
    except Exception:
        try:
            return path.read_text(encoding='gbk', errors='replace')
        except Exception:
            return None


def run_code_in_dir(project_dir, code, timeout=DEFAULT_TIMEOUT, main_file='', extra_files=None):
    """在指定目录中运行 Python 代码，通过 generator 流式输出"""
    if extra_files is None:
        extra_files = {}

    # 创建临时目录（用于单文件运行或文件覆盖）
    temp_dir = Path(tempfile.mkdtemp(prefix='local-run-'))
    try:
        # 如果有项目目录，复制项目文件
        if project_dir and Path(project_dir).exists():
            src = Path(project_dir).resolve()
            skip_dirs = {'__pycache__', '.git', '.venv', 'venv', 'node_modules',
                         '.idea', '.vscode', 'dist', 'build', 'egg-info'}
            for item in src.rglob('*'):
                if any(part in skip_dirs for part in item.relative_to(src).parts):
                    continue
                rel = item.relative_to(src)
                dest = temp_dir / rel
                if item.is_dir():
                    dest.mkdir(exist_ok=True)
                elif item.is_file():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(item), str(dest))
        # 写入主代码
        entry = main_file or 'script.py'
        if not entry.endswith('.py'):
            entry += '.py'
        (temp_dir / entry).write_text(code, encoding='utf-8')
        # 写入额外文件
        for fname, fcode in extra_files.items():
            fpath = temp_dir / fname
            fpath.parent.mkdir(parents=True, exist_ok=True)
            fpath.write_text(fcode, encoding='utf-8')

        python_bin = sys.executable
        cmd = [python_bin, '-u', entry]

        proc = subprocess.Popen(
            cmd,
            cwd=str(temp_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env={**os.environ, 'PYTHONUNBUFFERED': '1'},
        )

        start_time = time.time()
        output_buffer = []
        total_size = 0

        # 读取输出
        def read_output(stream, is_stdout=True):
            nonlocal total_size
            try:
                for line in iter(stream.readline, ''):
                    if not line:
                        break
                    line_str = line if isinstance(line, str) else line.decode('utf-8', errors='replace')
                    total_size += len(line_str.encode('utf-8'))
                    if total_size > MAX_OUTPUT_SIZE:
                        yield {'type': 'output', 'data': '... (输出已截断，超过4MB)'}
                        return
                    yield {'type': 'output', 'data': line_str.rstrip('\n')}
            except Exception as e:
                yield {'type': 'error', 'data': str(e)}

        # 用线程读取输出
        stdout_queue = queue.Queue()
        def collect_output():
            try:
                for item in read_output(proc.stdout):
                    stdout_queue.put(item)
            except Exception as e:
                stdout_queue.put({'type': 'error', 'data': f'读取输出出错: {e}'})

        reader_thread = threading.Thread(target=collect_output, daemon=True)
        reader_thread.start()

        yield {'type': 'status', 'data': {'phase': 'running', 'message': '开始执行...'}}

        while proc.poll() is None:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                proc.kill()
                yield {'type': 'error', 'data': f'执行超时 ({timeout}秒)'}
                return
            try:
                item = stdout_queue.get(timeout=0.5)
                yield item
            except queue.Empty:
                continue

        # 读取剩余输出
        reader_thread.join(timeout=2)
        while not stdout_queue.empty():
            try:
                item = stdout_queue.get_nowait()
                yield item
            except queue.Empty:
                break

        exit_code = proc.returncode
        elapsed = time.time() - start_time
        yield {'type': 'status', 'data': {
            'phase': 'done',
            'exitCode': exit_code,
            'elapsed': round(elapsed, 2),
            'message': f'执行完成 (耗时 {elapsed:.1f}s, 退出码 {exit_code})'
        }}

    finally:
        # 清理临时目录（延迟清理）
        def cleanup():
            time.sleep(5)
            try:
                shutil.rmtree(str(temp_dir), ignore_errors=True)
            except Exception:
                pass
        threading.Thread(target=cleanup, daemon=True).start()


# ==================== HTTP 服务器 ====================

class LocalAgentHandler(http.server.BaseHTTPRequestHandler):
    """本地伴生程序的 HTTP 请求处理器"""

    server_version = "CodeExplorerLocalAgent/1.0"

    # 允许的来源（Code Explorer 域名 + localhost）
    ALLOWED_ORIGINS = [
        'https://codingzhou.dpdns.org',
        'http://localhost',
        'http://127.0.0.1',
        'https://localhost',
        'https://127.0.0.1',
    ]

    def log_message(self, format, *args):
        pass  # 静默日志

    def _set_cors_headers(self):
        """设置 CORS 响应头"""
        origin = self.headers.get('Origin', '')
        if any(origin.startswith(o) for o in self.ALLOWED_ORIGINS):
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Access-Control-Allow-Credentials', 'true')
        else:
            self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def _send_error(self, message, status=400):
        self._send_json({'error': message}, status)

    def do_OPTIONS(self):
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path == '/api/status':
            return self._send_json({
                'status': 'connected',
                'pythonVersion': sys.version.split()[0],
                'pythonPath': sys.executable,
                'projectDir': str(self.server.projects_dir),
                'port': self.server.server_address[1],
            })

        if path == '/api/projects':
            projects = scan_projects(self.server.projects_dir)
            return self._send_json({
                'projects': projects,
                'total': len(projects),
                'projectDir': str(self.server.projects_dir),
            })

        if path == '/api/files':
            project = params.get('project', [''])[0]
            if not project:
                return self._send_error('缺少 project 参数')
            project_dir = Path(self.server.projects_dir) / project
            # 安全检查
            try:
                resolved = project_dir.resolve()
                base_resolved = Path(self.server.projects_dir).resolve()
                if not str(resolved).startswith(str(base_resolved)):
                    return self._send_error('访问被拒绝', 403)
            except Exception:
                return self._send_error('访问被拒绝', 403)
            depth = int(params.get('depth', ['3'])[0])
            files = scan_files(str(project_dir), max_depth=depth)
            return self._send_json({'files': files})

        if path == '/api/file-content':
            project = params.get('project', [''])[0]
            file_path = params.get('path', [''])[0]
            if not project or not file_path:
                return self._send_error('缺少参数')
            full_path = Path(self.server.projects_dir) / project / file_path
            # 安全检查
            try:
                resolved = full_path.resolve()
                base_resolved = (Path(self.server.projects_dir) / project).resolve()
                if not str(resolved).startswith(str(base_resolved)):
                    return self._send_error('访问被拒绝', 403)
            except Exception:
                return self._send_error('访问被拒绝', 403)
            content = read_file_content(str(full_path))
            if content is None:
                return self._send_error('无法读取文件（过大或不存在）', 404)
            return self._send_json({
                'path': file_path,
                'content': content,
                'size': len(content),
            })

        return self._send_error('未找到路由', 404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            return self._send_error('无效的 JSON 数据')

        if path == '/api/run':
            return self._handle_run(data)

        if path == '/api/scan':
            # 重新扫描项目
            projects = scan_projects(self.server.projects_dir)
            return self._send_json({
                'projects': projects,
                'total': len(projects),
            })

        return self._send_error('未找到路由', 404)

    def _handle_run(self, data):
        """处理代码运行请求，使用 SSE 流式返回"""
        project = data.get('project', '')
        code = data.get('code', '')
        main_file = data.get('mainFile', '')
        extra_files = data.get('files', {})
        timeout = min(int(data.get('timeout', DEFAULT_TIMEOUT)), MAX_TIMEOUT)
        run_id = uuid.uuid4().hex[:12]

        if not code:
            return self._send_error('代码为空')

        # 确定项目目录
        if project:
            project_dir = str(Path(self.server.projects_dir) / project)
            # 安全检查
            try:
                resolved = Path(project_dir).resolve()
                base_resolved = Path(self.server.projects_dir).resolve()
                if not str(resolved).startswith(str(base_resolved)):
                    return self._send_error('访问被拒绝', 403)
            except Exception:
                return self._send_error('项目路径无效', 403)
            if not Path(project_dir).exists():
                return self._send_error('项目不存在', 404)
        else:
            project_dir = None

        # 分析依赖
        imports = detect_imports(code)

        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
        self.send_header('Cache-Control', 'no-cache, no-transform')
        self.send_header('Connection', 'keep-alive')
        self._set_cors_headers()
        self.end_headers()

        def emit(event, data):
            payload = f'event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n'
            self.wfile.write(payload.encode('utf-8'))
            self.wfile.flush()

        def stream_run():
            try:
                emit('status', {'phase': 'preparing', 'runId': run_id,
                                'message': f'准备执行环境... (Python {sys.version.split()[0]})'})
                if imports:
                    emit('status', {'phase': 'analyzing',
                                    'message': f'检测到 {len(imports)} 个第三方依赖: {", ".join(sorted(imports))}'})

                emit('status', {'phase': 'running', 'message': '开始执行...'})

                last_heartbeat = 0
                for chunk in run_code_in_dir(project_dir, code, timeout, main_file, extra_files):
                    now = time.time()
                    if now - last_heartbeat > 15:
                        emit('heartbeat', {'time': int(now)})
                        last_heartbeat = now

                    if chunk['type'] == 'output':
                        emit('output', {'text': chunk['data']})
                    elif chunk['type'] == 'error':
                        emit('error', {'message': chunk['data']})
                    elif chunk['type'] == 'status':
                        emit('status', chunk['data'])

                emit('done', {'runId': run_id})

            except Exception as e:
                import traceback
                emit('error', {'message': f'执行出错: {str(e)}'})
                emit('done', {'runId': run_id})

        # 在新线程中运行（避免阻塞连接）
        thread = threading.Thread(target=stream_run, daemon=True)
        thread.start()


class LocalAgentServer:
    """本地伴生程序服务器"""

    def __init__(self, host='127.0.0.1', port=DEFAULT_PORT, projects_dir=None):
        self.host = host
        self.port = port
        self.projects_dir = Path(projects_dir or Path(__file__).resolve().parent)
        self.httpd = None

    def start(self):
        """启动服务器"""
        self.httpd = http.server.HTTPServer((self.host, self.port), LocalAgentHandler)
        self.httpd.projects_dir = self.projects_dir

        print(f"""
╔══════════════════════════════════════════════════╗
║  Code Explorer 本地伴生程序                      ║
╠══════════════════════════════════════════════════╣
║  状态:  ● 运行中                                 ║
║  地址:  http://{self.host}:{self.port}                 ║
║  项目目录: {self.projects_dir}
║  Python:  {sys.version.split()[0]}
║  浏览器访问: https://codingzhou.dpdns.org/run/local
╠══════════════════════════════════════════════════╣
║  按 Ctrl+C 停止                                  ║
╚══════════════════════════════════════════════════╝
""")
        try:
            self.httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n正在停止...")
            self.httpd.shutdown()
            print("已停止。")

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Code Explorer 本地伴生程序 - 在 Code Explorer 网站上运行本地 Python 项目'
    )
    parser.add_argument('--port', type=int, default=DEFAULT_PORT,
                        help=f'监听端口 (默认: {DEFAULT_PORT})')
    parser.add_argument('--projects-dir', type=str, default=None,
                        help='项目根目录 (默认: 脚本所在目录)')
    parser.add_argument('--no-browser', action='store_true',
                        help='启动后不自动打开浏览器')
    args = parser.parse_args()

    # 验证项目目录
    projects_dir = Path(args.projects_dir or Path(__file__).resolve().parent)
    if not projects_dir.exists():
        print(f"[ERROR] 项目目录不存在: {projects_dir}")
        sys.exit(1)

    server = LocalAgentServer(
        host='127.0.0.1',
        port=args.port,
        projects_dir=projects_dir,
    )

    # 尝试打开浏览器
    if not args.no_browser:
        import webbrowser
        time.sleep(0.5)
        webbrowser.open('https://codingzhou.dpdns.org/run/local')

    server.start()


if __name__ == '__main__':
    main()