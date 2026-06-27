#!/usr/bin/env python3
"""
简单的 MCP 服务器实现 - 遵循 MCP 协议
支持 stdio 传输
"""

import sys
import json
from typing import Any, Dict, Optional
import requests


class SimpleMCPServer:
    def __init__(self):
        self.tools = {
            "search_github_repos": self.search_github_repos,
            "get_repo_info": self.get_repo_info,
            "list_user_repos": self.list_user_repos
        }
        self.github_api = "https://api.github.com"
    
    def send_jsonrpc(self, message: Dict[str, Any]):
        """发送 JSON-RPC 消息"""
        print(json.dumps(message, ensure_ascii=False))
        sys.stdout.flush()
    
    def search_github_repos(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """搜索 GitHub 仓库"""
        query = arguments.get("query", "")
        per_page = arguments.get("per_page", 10)
        
        url = f"{self.github_api}/search/repositories"
        params = {
            "q": query,
            "per_page": per_page,
            "sort": "stars",
            "order": "desc"
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            items = []
            for repo in data.get("items", []):
                items.append({
                    "name": repo["name"],
                    "owner": repo["owner"]["login"],
                    "description": repo.get("description", ""),
                    "stars": repo["stargazers_count"],
                    "forks": repo["forks_count"],
                    "language": repo.get("language", ""),
                    "url": repo["html_url"]
                })
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(items, ensure_ascii=False, indent=2)
                    }
                ]
            }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"错误: {str(e)}"
                    }
                ],
                "isError": True
            }
    
    def get_repo_info(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """获取仓库详细信息"""
        owner = arguments.get("owner", "")
        repo = arguments.get("repo", "")
        
        if not owner or not repo:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "错误: 请提供 owner 和 repo 参数"
                    }
                ],
                "isError": True
            }
        
        url = f"{self.github_api}/repos/{owner}/{repo}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            repo_data = response.json()
            
            result = {
                "name": repo_data["name"],
                "owner": repo_data["owner"]["login"],
                "description": repo_data.get("description", ""),
                "stars": repo_data["stargazers_count"],
                "forks": repo_data["forks_count"],
                "watchers": repo_data["watchers_count"],
                "language": repo_data.get("language", ""),
                "open_issues": repo_data["open_issues_count"],
                "license": repo_data.get("license", {}).get("name", "") if repo_data.get("license") else "",
                "url": repo_data["html_url"],
                "created_at": repo_data["created_at"],
                "updated_at": repo_data["updated_at"]
            }
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False, indent=2)
                    }
                ]
            }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"错误: {str(e)}"
                    }
                ],
                "isError": True
            }
    
    def list_user_repos(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """获取用户的仓库列表"""
        username = arguments.get("username", "")
        per_page = arguments.get("per_page", 10)
        
        if not username:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "错误: 请提供 username 参数"
                    }
                ],
                "isError": True
            }
        
        url = f"{self.github_api}/users/{username}/repos"
        params = {"per_page": per_page, "sort": "updated"}
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            repos = response.json()
            
            items = []
            for repo in repos:
                items.append({
                    "name": repo["name"],
                    "description": repo.get("description", ""),
                    "stars": repo["stargazers_count"],
                    "language": repo.get("language", ""),
                    "url": repo["html_url"]
                })
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(items, ensure_ascii=False, indent=2)
                    }
                ]
            }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"错误: {str(e)}"
                    }
                ],
                "isError": True
            }
    
    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理 MCP 请求"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "GitHub MCP Server",
                        "version": "1.0.0"
                    }
                }
            }
        
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": "search_github_repos",
                            "description": "搜索 GitHub 仓库",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "搜索关键词"
                                    },
                                    "per_page": {
                                        "type": "integer",
                                        "description": "返回结果数量",
                                        "default": 10
                                    }
                                },
                                "required": ["query"]
                            }
                        },
                        {
                            "name": "get_repo_info",
                            "description": "获取仓库详细信息",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "owner": {
                                        "type": "string",
                                        "description": "仓库所有者"
                                    },
                                    "repo": {
                                        "type": "string",
                                        "description": "仓库名称"
                                    }
                                },
                                "required": ["owner", "repo"]
                            }
                        },
                        {
                            "name": "list_user_repos",
                            "description": "获取用户的仓库列表",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "username": {
                                        "type": "string",
                                        "description": "GitHub 用户名"
                                    },
                                    "per_page": {
                                        "type": "integer",
                                        "description": "返回结果数量",
                                        "default": 10
                                    }
                                },
                                "required": ["username"]
                            }
                        }
                    ]
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            if tool_name in self.tools:
                result = self.tools[tool_name](tool_args)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: {tool_name}"
                    }
                }
        
        elif method == "shutdown":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {}
            }
        
        elif method == "notifications/initialized":
            return None
        
        return None
    
    def run(self):
        """运行 MCP 服务器"""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            
            try:
                request = json.loads(line)
                response = self.handle_request(request)
                if response:
                    self.send_jsonrpc(response)
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)


if __name__ == "__main__":
    server = SimpleMCPServer()
    server.run()
