#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI File Assistant Backend
用于处理文件操作和AI交互的Python后端服务
"""

import os
import json
import base64
import logging
import argparse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from datetime import datetime
from typing import Dict, List, Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ai_file_assistant.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AIFileAssistant")

class FileAssistant:
    """文件助手类，处理所有文件操作"""
    
    def __init__(self, base_dir: str = "./files"):
        """初始化文件助手
        
        Args:
            base_dir: 文件存储的基础目录
        """
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)
        logger.info(f"文件助手初始化，基础目录: {self.base_dir}")
        
        # 用户数据存储
        self.users_file = os.path.join(self.base_dir, "users.json")
        self.users = self._load_users()
        
        # 文件操作权限
        self.permissions = {
            "read": False,
            "write": False,
            "delete": False
        }
        
        # 允许访问的路径列表
        self.allowed_paths = [self.base_dir]
    
    def _load_users(self) -> Dict[str, Dict[str, str]]:
        """加载用户数据
        
        Returns:
            用户数据字典
        """
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error("用户数据文件格式错误，创建新文件")
                return {}
        return {}
    
    def _save_users(self) -> None:
        """保存用户数据"""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)
    
    def register_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """注册新用户
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            
        Returns:
            包含状态和消息的字典
        """
        if username in self.users:
            return {"status": "error", "message": "用户名已存在"}
        
        # 在实际应用中应该对密码进行哈希处理
        self.users[username] = {
            "email": email,
            "password": password,
            "created_at": datetime.now().isoformat()
        }
        
        self._save_users()
        logger.info(f"新用户注册: {username}")
        
        # 为新用户创建文件目录
        user_dir = os.path.join(self.base_dir, username)
        os.makedirs(user_dir, exist_ok=True)
        
        return {"status": "success", "message": "注册成功"}
    
    def login_user(self, username: str, password: str) -> Dict[str, Any]:
        """用户登录
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            包含状态、消息和用户信息的字典
        """
        if username not in self.users:
            return {"status": "error", "message": "用户名不存在"}
        
        if self.users[username]["password"] != password:
            return {"status": "error", "message": "密码错误"}
        
        logger.info(f"用户登录: {username}")
        
        return {
            "status": "success",
            "message": "登录成功",
            "user": {
                "username": username,
                "email": self.users[username]["email"]
            }
        }
    
    def set_permissions(self, read: bool = False, write: bool = False, delete: bool = False) -> None:
        """设置文件操作权限
        
        Args:
            read: 是否允许读取
            write: 是否允许写入
            delete: 是否允许删除
        """
        self.permissions = {
            "read": read,
            "write": write,
            "delete": delete
        }
        logger.info(f"权限更新: {self.permissions}")
    
    def add_allowed_path(self, path: str) -> bool:
        """添加允许访问的路径
        
        Args:
            path: 要添加的路径
            
        Returns:
            添加是否成功
        """
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path) and abs_path not in self.allowed_paths:
            self.allowed_paths.append(abs_path)
            logger.info(f"添加允许访问路径: {abs_path}")
            return True
        return False
    
    def is_path_allowed(self, path: str) -> bool:
        """检查路径是否允许访问
        
        Args:
            path: 要检查的路径
            
        Returns:
            是否允许访问
        """
        abs_path = os.path.abspath(path)
        for allowed_path in self.allowed_paths:
            if abs_path.startswith(allowed_path):
                return True
        return False
    
    def list_files(self, username: str, path: str = "") -> List[Dict[str, Any]]:
        """列出用户目录下的文件和文件夹
        
        Args:
            username: 用户名
            path: 相对路径
            
        Returns:
            文件和文件夹列表
        """
        if not self.permissions["read"]:
            logger.warning("读取权限未授权")
            return []
        
        user_dir = os.path.join(self.base_dir, username)
        target_dir = os.path.abspath(os.path.join(user_dir, path))
        
        # 安全检查：确保不会访问用户目录外的文件
        if not target_dir.startswith(user_dir):
            logger.warning(f"尝试访问未授权路径: {target_dir}")
            return []
        
        if not os.path.exists(target_dir):
            return []
        
        items = []
        try:
            for item in os.listdir(target_dir):
                item_path = os.path.join(target_dir, item)
                item_rel_path = os.path.relpath(item_path, user_dir)
                
                item_info = {
                    "name": item,
                    "path": item_rel_path.replace("\\", "/"),
                    "is_dir": os.path.isdir(item_path),
                    "size": os.path.getsize(item_path) if os.path.isfile(item_path) else 0,
                    "modified": datetime.fromtimestamp(os.path.getmtime(item_path)).isoformat()
                }
                items.append(item_info)
        except Exception as e:
            logger.error(f"列出文件失败: {e}")
        
        return items
    
    def create_folder(self, username: str, path: str) -> Dict[str, Any]:
        """创建新文件夹
        
        Args:
            username: 用户名
            path: 要创建的文件夹路径
            
        Returns:
            包含状态和消息的字典
        """
        if not self.permissions["write"]:
            return {"status": "error", "message": "写入权限未授权"}
        
        user_dir = os.path.join(self.base_dir, username)
        target_dir = os.path.abspath(os.path.join(user_dir, path))
        
        # 安全检查
        if not target_dir.startswith(user_dir):
            return {"status": "error", "message": "无权访问该路径"}
        
        try:
            os.makedirs(target_dir, exist_ok=True)
            logger.info(f"创建文件夹: {target_dir}")
            return {"status": "success", "message": "文件夹创建成功"}
        except Exception as e:
            logger.error(f"创建文件夹失败: {e}")
            return {"status": "error", "message": f"创建文件夹失败: {str(e)}"}
    
    def upload_file(self, username: str, file_name: str, content: bytes, path: str = "") -> Dict[str, Any]:
        """上传文件
        
        Args:
            username: 用户名
            file_name: 文件名
            content: 文件内容
            path: 上传路径
            
        Returns:
            包含状态和消息的字典
        """
        if not self.permissions["write"]:
            return {"status": "error", "message": "写入权限未授权"}
        
        user_dir = os.path.join(self.base_dir, username)
        target_path = os.path.abspath(os.path.join(user_dir, path, file_name))
        
        # 安全检查
        if not target_path.startswith(user_dir):
            return {"status": "error", "message": "无权访问该路径"}
        
        try:
            # 确保目标目录存在
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            with open(target_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"文件上传成功: {target_path}")
            return {
                "status": "success", 
                "message": "文件上传成功",
                "file": {
                    "name": file_name,
                    "path": os.path.relpath(target_path, user_dir).replace("\\", "/"),
                    "size": len(content)
                }
            }
        except Exception as e:
            logger.error(f"文件上传失败: {e}")
            return {"status": "error", "message": f"文件上传失败: {str(e)}"}
    
    def download_file(self, username: str, path: str) -> Optional[Dict[str, Any]]:
        """下载文件
        
        Args:
            username: 用户名
            path: 文件路径
            
        Returns:
            包含文件信息和内容的字典，如果失败则返回None
        """
        if not self.permissions["read"]:
            return {"status": "error", "message": "读取权限未授权"}
        
        user_dir = os.path.join(self.base_dir, username)
        target_path = os.path.abspath(os.path.join(user_dir, path))
        
        # 安全检查
        if not target_path.startswith(user_dir) or not os.path.exists(target_path):
            return {"status": "error", "message": "文件不存在或无权访问"}
        
        try:
            with open(target_path, 'rb') as f:
                content = f.read()
            
            return {
                "status": "success",
                "file": {
                    "name": os.path.basename(target_path),
                    "content": base64.b64encode(content).decode('utf-8'),
                    "size": os.path.getsize(target_path),
                    "modified": datetime.fromtimestamp(os.path.getmtime(target_path)).isoformat()
                }
            }
        except Exception as e:
            logger.error(f"文件下载失败: {e}")
            return {"status": "error", "message": f"文件下载失败: {str(e)}"}
    
    def delete_file(self, username: str, path: str) -> Dict[str, Any]:
        """删除文件或文件夹
        
        Args:
            username: 用户名
            path: 要删除的文件或文件夹路径
            
        Returns:
            包含状态和消息的字典
        """
        if not self.permissions["delete"]:
            return {"status": "error", "message": "删除权限未授权"}
        
        user_dir = os.path.join(self.base_dir, username)
        target_path = os.path.abspath(os.path.join(user_dir, path))
        
        # 安全检查
        if not target_path.startswith(user_dir) or not os.path.exists(target_path):
            return {"status": "error", "message": "文件或文件夹不存在或无权访问"}
        
        try:
            if os.path.isfile(target_path):
                os.remove(target_path)
                logger.info(f"删除文件: {target_path}")
            else:
                import shutil
                shutil.rmtree(target_path)
                logger.info(f"删除文件夹: {target_path}")
            
            return {"status": "success", "message": "删除成功"}
        except Exception as e:
            logger.error(f"删除失败: {e}")
            return {"status": "error", "message": f"删除失败: {str(e)}"}
    
    def analyze_file(self, username: str, path: str) -> Dict[str, Any]:
        """分析文件内容
        
        Args:
            username: 用户名
            path: 文件路径
            
        Returns:
            包含分析结果的字典
        """
        if not self.permissions["read"]:
            return {"status": "error", "message": "读取权限未授权"}
        
        user_dir = os.path.join(self.base_dir, username)
        target_path = os.path.abspath(os.path.join(user_dir, path))
        
        # 安全检查
        if not target_path.startswith(user_dir) or not os.path.exists(target_path):
            return {"status": "error", "message": "文件不存在或无权访问"}
        
        try:
            file_name = os.path.basename(target_path)
            file_ext = os.path.splitext(file_name)[1].lower()
            
            # 根据文件类型进行不同的分析
            if file_ext in ['.txt', '.md', '.csv', '.json']:
                with open(target_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # 简单的文本分析
                lines = content.split('\n')
                words = content.split()
                
                analysis = {
                    "file_type": "text",
                    "line_count": len(lines),
                    "word_count": len(words),
                    "char_count": len(content),
                    "preview": content[:500] + "..." if len(content) > 500 else content
                }
            
            elif file_ext in ['.xlsx', '.xls']:
                try:
                    import pandas as pd
                    df = pd.read_excel(target_path)
                    
                    analysis = {
                        "file_type": "spreadsheet",
                        "sheet_names": [df.name] if hasattr(df, 'name') else ["Sheet1"],
                        "rows": len(df),
                        "columns": len(df.columns),
                        "column_names": list(df.columns),
                        "preview": df.head(5).to_dict()
                    }
                except ImportError:
                    analysis = {
                        "file_type": "spreadsheet",
                        "message": "需要安装pandas库以分析Excel文件"
                    }
            
            elif file_ext in ['.docx']:
                try:
                    import docx
                    doc = docx.Document(target_path)
                    
                    paragraphs = [p.text for p in doc.paragraphs]
                    analysis = {
                        "file_type": "document",
                        "paragraph_count": len(paragraphs),
                        "preview": paragraphs[:3] if len(paragraphs) > 3 else paragraphs
                    }
                except ImportError:
                    analysis = {
                        "file_type": "document",
                        "message": "需要安装python-docx库以分析Word文件"
                    }
            
            else:
                analysis = {
                    "file_type": "unknown",
                    "message": f"不支持的文件类型: {file_ext}"
                }
            
            logger.info(f"文件分析完成: {target_path}")
            return {
                "status": "success",
                "analysis": analysis
            }
        
        except Exception as e:
            logger.error(f"文件分析失败: {e}")
            return {"status": "error", "message": f"文件分析失败: {str(e)}"}


class AIHandler:
    """AI处理类，用于模拟AI交互"""
    
    def __init__(self):
        """初始化AI处理器"""
        self.conversations = {}
        logger.info("AI处理器初始化")
    
    def create_conversation(self, user_id: str) -> str:
        """创建新的对话
        
        Args:
            user_id: 用户ID
            
        Returns:
            对话ID
        """
        conversation_id = f"{user_id}_{datetime.now().timestamp()}"
        self.conversations[conversation_id] = {
            "user_id": user_id,
            "messages": [],
            "created_at": datetime.now().isoformat()
        }
        logger.info(f"创建新对话: {conversation_id}")
        return conversation_id
    
    def add_message(self, conversation_id: str, role: str, content: str) -> bool:
        """添加消息到对话
        
        Args:
            conversation_id: 对话ID
            role: 角色 (user 或 assistant)
            content: 消息内容
            
        Returns:
            添加是否成功
        """
        if conversation_id not in self.conversations:
            return False
        
        self.conversations[conversation_id]["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        return True
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """获取对话
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            对话信息，如果不存在则返回None
        """
        return self.conversations.get(conversation_id)
    
    def generate_response(self, conversation_id: str, message: str, file_info: Optional[Dict[str, Any]] = None) -> str:
        """生成AI响应
        
        Args:
            conversation_id: 对话ID
            message: 用户消息
            file_info: 文件信息（如果有）
            
        Returns:
            AI响应
        """
        # 添加用户消息
        self.add_message(conversation_id, "user", message)
        
        # 模拟AI响应
        if file_info:
            # 如果有文件信息，生成与文件相关的响应
            response = self._generate_file_response(message, file_info)
        else:
            # 普通文本响应
            response = self._generate_text_response(message)
        
        # 添加AI响应
        self.add_message(conversation_id, "assistant", response)
        
        return response
    
    def _generate_text_response(self, message: str) -> str:
        """生成文本响应
        
        Args:
            message: 用户消息
            
        Returns:
            AI响应
        """
        # 简单的响应模板，实际应用中应该使用真实的AI模型
        message_lower = message.lower()
        
        if any(greeting in message_lower for greeting in ["你好", "hi", "hello", "嗨"]):
            return "你好！我是你的AI文件助手。我可以帮助你管理文件、分析内容，或者回答你的问题。请问有什么我可以帮你的吗？"
        
        elif any(question in message_lower for question in ["你是谁", "你是什么"]):
            return "我是一个AI文件助手，可以帮助你管理和分析文件，回答问题，以及执行各种文件相关的任务。"
        
        elif any(help in message_lower for help in ["帮助", "怎么用", "使用方法"]):
            return """我可以帮助你：
1. 管理文件：上传、下载、创建文件夹、删除文件等
2. 分析文件：查看文件内容、统计信息等
3. 回答问题：解答你的各种疑问

你可以直接告诉我你想做什么，比如"帮我上传一个文件"或"分析这个Excel文件中的数据"。"""
        
        elif "谢谢" in message_lower or "感谢" in message_lower:
            return "不客气！如果还有其他需要帮助的地方，请随时告诉我。"
        
        else:
            return f"我理解你想了解关于'{message}'的信息。这是一个很有趣的话题。在实际应用中，我会使用先进的AI模型来提供更详细和准确的回答。你还有其他问题吗？"
    
    def _generate_file_response(self, message: str, file_info: Dict[str, Any]) -> str:
        """生成文件相关的响应
        
        Args:
            message: 用户消息
            file_info: 文件信息
            
        Returns:
            AI响应
        """
        file_name = file_info.get("name", "文件")
        file_type = file_info.get("file_type", "unknown")
        
        if "分析" in message or "查看" in message:
            if file_type == "text":
                line_count = file_info.get("analysis", {}).get("line_count", 0)
                word_count = file_info.get("analysis", {}).get("word_count", 0)
                preview = file_info.get("analysis", {}).get("preview", "")

                return f"""我已分析了您的文件 "{file_name}"，以下是我的发现：
- 文件类型：文本文件
- 行数：{line_count}
- 单词数：{word_count}
- 文件预览：
{preview}

您需要我对文件内容进行更详细的分析吗？"""

            elif file_type == "spreadsheet":
                rows = file_info.get("analysis", {}).get("rows", 0)
                columns = file_info.get("analysis", {}).get("columns", 0)
                column_names = file_info.get("analysis", {}).get("column_names", [])

                return f"""我已分析了您的电子表格文件 "{file_name}"，以下是我的发现：
- 文件类型：电子表格
- 行数：{rows}
- 列数：{columns}
- 列名：{', '.join(column_names)}

数据显示这是一个包含{rows}行数据的表格，共有{columns}个字段。您希望我进一步分析这些数据的哪些方面？例如数据趋势、统计信息或异常值等。"""

            elif file_type == "document":
                paragraph_count = file_info.get("analysis", {}).get("paragraph_count", 0)

                return f"""我已分析了您的文档文件 "{file_name}"，以下是我的发现：
- 文件类型：文档
- 段落数：{paragraph_count}

这是一个包含{paragraph_count}个段落的文档。您希望我提取文档的主要内容或关键点吗？"""

            else:
                return f"不支持的文件类型: {file_type}"

        else:
            return f"我已收到您的文件 '{file_name}'。请问您希望我对这个文件做什么？例如分析内容、提取信息或进行其他操作。"


class RequestHandler(BaseHTTPRequestHandler):
    """HTTP请求处理器"""
    
    # 初始化文件助手和AI处理器
    file_assistant = FileAssistant()
    ai_handler = AIHandler()
    
    def _set_response(self, status_code: int = 200, content_type: str = "application/json") -> None:
        """设置HTTP响应头
        
        Args:
            status_code: HTTP状态码
            content_type: 内容类型
        """
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_OPTIONS(self) -> None:
        """处理OPTIONS请求"""
        self._set_response(204)
    
    def do_GET(self) -> None:
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)

        logger.info(f"GET请求: {path}")

        # 根路径处理 - 返回index.html
        if path == '/' or path == '/index.html':
            index_path = os.path.join(os.path.dirname(__file__), 'index.html')
            if os.path.exists(index_path):
                try:
                    with open(index_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self._set_response(200, 'text/html')
                    self.wfile.write(content.encode('utf-8'))
                    return
                except Exception as e:
                    logger.error(f"读取index.html失败: {e}")

        # 静态文件服务
        if path.startswith('/static/') or path.startswith('/public/'):
            static_file = os.path.join(os.path.dirname(__file__), path.lstrip('/'))
            if os.path.exists(static_file) and os.path.isfile(static_file):
                ext = os.path.splitext(static_file)[1].lower()
                content_types = {
                    '.html': 'text/html',
                    '.css': 'text/css',
                    '.js': 'application/javascript',
                    '.json': 'application/json',
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.gif': 'image/gif',
                    '.svg': 'image/svg+xml',
                    '.ico': 'image/x-icon'
                }
                content_type = content_types.get(ext, 'application/octet-stream')
                try:
                    with open(static_file, 'rb') as f:
                        content = f.read()
                    self._set_response(200, content_type)
                    self.wfile.write(content)
                    return
                except Exception as e:
                    logger.error(f"读取静态文件失败: {e}")

        # API路由处理
        if path == '/api/users/login':
            # 处理登录请求
            username = query_params.get('username', [''])[0]
            password = query_params.get('password', [''])[0]
            
            if not username or not password:
                self._set_response(400)
                self.wfile.write(json.dumps({"status": "error", "message": "用户名和密码不能为空"}).encode())
                return
            
            result = self.file_assistant.login_user(username, password)
            self._set_response(200 if result["status"] == "success" else 401)
            self.wfile.write(json.dumps(result).encode())
        
        elif path.startswith('/api/files/list'):
            # 处理文件列表请求
            username = query_params.get('username', [''])[0]
            path_param = query_params.get('path', [''])[0]
            
            if not username:
                self._set_response(400)
                self.wfile.write(json.dumps({"status": "error", "message": "用户名不能为空"}).encode())
                return
            
            files = self.file_assistant.list_files(username, path_param)
            self._set_response(200)
            self.wfile.write(json.dumps({"status": "success", "files": files}).encode())
        
        elif path.startswith('/api/files/download'):
            # 处理文件下载请求
            username = query_params.get('username', [''])[0]
            file_path = query_params.get('path', [''])[0]
            
            if not username or not file_path:
                self._set_response(400)
                self.wfile.write(json.dumps({"status": "error", "message": "用户名和文件路径不能为空"}).encode())
                return
            
            result = self.file_assistant.download_file(username, file_path)
            
            if result["status"] == "success":
                self._set_response(200)
                self.wfile.write(json.dumps(result).encode())
            else:
                self._set_response(404)
                self.wfile.write(json.dumps(result).encode())
        
        elif path.startswith('/api/ai/conversation'):
            # 获取对话
            conversation_id = query_params.get('id', [''])[0]
            
            if not conversation_id:
                self._set_response(400)
                self.wfile.write(json.dumps({"status": "error", "message": "对话ID不能为空"}).encode())
                return
            
            conversation = self.ai_handler.get_conversation(conversation_id)
            
            if conversation:
                self._set_response(200)
                self.wfile.write(json.dumps({"status": "success", "conversation": conversation}).encode())
            else:
                self._set_response(404)
                self.wfile.write(json.dumps({"status": "error", "message": "对话不存在"}).encode())
        
        else:
            # 未找到路由
            self._set_response(404)
            self.wfile.write(json.dumps({"status": "error", "message": "未找到该API端点"}).encode())
    
    def do_POST(self) -> None:
        """处理POST请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # 获取请求体长度
        content_length = int(self.headers['Content-Length'])
        # 读取请求体
        post_data = self.rfile.read(content_length)
        
        try:
            # 尝试解析JSON数据
            data = json.loads(post_data.decode('utf-8'))
        except json.JSONDecodeError:
            self._set_response(400)
            self.wfile.write(json.dumps({"status": "error", "message": "无效的JSON格式"}).encode())
            return
        
        logger.info(f"POST请求: {path}")
        
        # API路由处理
        if path == '/api/users/register':
            # 处理注册请求
            username = data.get('username', '')
            email = data.get('email', '')
            password = data.get('password', '')
            
            if not username or not email or not password:
                self._set_response(400)
                self.wfile.write(json.dumps({"status": "error", "message": "用户名、邮箱和密码不能为空"}).encode())
                return
            
            result = self.file_assistant.register_user(username, email, password)
            self._set_response(201 if result["status"] == "success" else 400)
            self.wfile.write(json.dumps(result).encode())
        
        elif path == '/api/permissions':
            # 设置权限
            read = data.get('read', False)
            write = data.get('write', False)
            delete = data.get('delete', False)
            
            self.file_assistant.set_permissions(read, write, delete)
            self._set_response(200)
            self.wfile.write(json.dumps({"status": "success", "message": "权限设置成功"}).encode())
        
        elif path == '/api/files/folder':
            # 创建文件夹
            username = data.get('username', '')
            folder_path = data.get('path', '')
            
            if not username or not folder_path:
                self._set_response(400)
                self.wfile.write(json.dumps({"status": "error", "message": "用户名和文件夹路径不能为空"}).encode())
                return
            
            result = self.file_assistant.create_folder(username, folder_path)
            self._set_response(201 if result["status"] == "success" else 400)
            self.wfile.write(json.dumps(result).encode())
        
        elif path == '/api/files/upload':
            # 上传文件
            username = data.get('username', '')
            file_name = data.get('name', '')
            file_content = data.get('content', '')
            file_path = data.get('path', '')
            
            if not username or not file_name or not file_content:
                self._set_response(400)
                self.wfile.write(json.dumps({"status": "error", "message": "用户名、文件名和文件内容不能为空"}).encode())
                return
            
            try:
                # 解码base64文件内容
                content_bytes = base64.b64decode(file_content)
            except Exception as e:
                self._set_response(400)
                self.wfile.write(json.dumps({"status": "error", "message": "文件内容解码失败"}).encode())
                return
            
            result = self.file_assistant.upload_file(username, file_name, content_bytes, file_path)
            self._set_response(201 if result["status"] == "success" else 400)
            self.wfile.write(json.dumps(result).encode())
        
        elif path == '/api/files/delete':
            # 删除文件或文件夹
            username = data.get('username', '')
            file_path = data.get('path', '')
            
            if not username or not file_path:
                self._set_response(400)
                self.wfile.write(json.dumps({"status": "error", "message": "用户名和文件路径不能为空"}).encode())
                return
            
            result = self.file_assistant.delete_file(username, file_path)
            self._set_response(200 if result["status"] == "success" else 400)
            self.wfile.write(json.dumps(result).encode())
        
        elif path == '/api/files/analyze':
            # 分析文件
            username = data.get('username', '')
            file_path = data.get('path', '')
            
            if not username or not file_path:
                self._set_response(400)
                self.wfile.write(json.dumps({"status": "error", "message": "用户名和文件路径不能为空"}).encode())
                return
            
            result = self.file_assistant.analyze_file(username, file_path)
            self._set_response(200 if result["status"] == "success" else 400)
            self.wfile.write(json.dumps(result).encode())
        
        elif path == '/api/ai/conversation':
            # 创建新对话
            user_id = data.get('user_id', '')
            
            if not user_id:
                self._set_response(400)
                self.wfile.write(json.dumps({"status": "error", "message": "用户ID不能为空"}).encode())
                return
            
            conversation_id = self.ai_handler.create_conversation(user_id)
            self._set_response(201)
            self.wfile.write(json.dumps({"status": "success", "conversation_id": conversation_id}).encode())
        
        elif path == '/api/ai/message':
            # 发送消息到AI
            conversation_id = data.get('conversation_id', '')
            message = data.get('message', '')
            file_info = data.get('file_info', None)
            
            if not conversation_id or not message:
                self._set_response(400)
                self.wfile.write(json.dumps({"status": "error", "message": "对话ID和消息不能为空"}).encode())
                return
            
            if not self.ai_handler.get_conversation(conversation_id):
                self._set_response(404)
                self.wfile.write(json.dumps({"status": "error", "message": "对话不存在"}).encode())
                return
            
            response = self.ai_handler.generate_response(conversation_id, message, file_info)
            self._set_response(200)
            self.wfile.write(json.dumps({"status": "success", "response": response}).encode())
        
        else:
            # 未找到路由
            self._set_response(404)
            self.wfile.write(json.dumps({"status": "error", "message": "未找到该API端点"}).encode())
    
    def log_message(self, format: str, *args) -> None:
        """重写日志方法，使用我们的logger"""
        logger.info(f"{self.client_address[0]} - {format % args}")


def run_server(host: str = 'localhost', port: int = 8000) -> None:
    """启动HTTP服务器
    
    Args:
        host: 主机地址
        port: 端口号
    """
    server_address = (host, port)
    httpd = HTTPServer(server_address, RequestHandler)
    logger.info(f"服务器启动在 http://{host}:{port}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("服务器关闭")
        httpd.server_close()


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='AI File Assistant Backend')
    parser.add_argument('--host', type=str, default='localhost', help='服务器主机地址')
    parser.add_argument('--port', type=int, default=8000, help='服务器端口号')
    parser.add_argument('--open-browser', action='store_true', help='自动打开浏览器')
    
    args = parser.parse_args()
    
    # 如果指定了打开浏览器，则在启动服务器后打开
    if args.open_browser:
        import threading
        import time
        
        def open_browser():
            time.sleep(1)  # 等待服务器启动
            webbrowser.open(f'http://{args.host}:{args.port}')
        
        threading.Thread(target=open_browser).start()
    
    # 启动服务器
    run_server(args.host, args.port)
    