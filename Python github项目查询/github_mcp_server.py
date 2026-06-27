#!/usr/bin/env python3
"""
GitHub MCP Server - 简单的 GitHub 仓库查询 MCP 服务器
"""

import json
import sys
from typing import Any, Dict, List, Optional
import requests


class GitHubMCP:
    def __init__(self, token: Optional[str] = None):
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-MCP-Server/1.0"
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
    
    def search_repos(self, query: str, per_page: int = 10) -> Dict[str, Any]:
        """搜索 GitHub 仓库"""
        url = f"{self.base_url}/search/repositories"
        params = {
            "q": query,
            "per_page": per_page,
            "sort": "stars",
            "order": "desc"
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_repo_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """获取仓库详细信息"""
        url = f"{self.base_url}/repos/{owner}/{repo}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def list_user_repos(self, username: str, per_page: int = 10) -> List[Dict[str, Any]]:
        """获取用户的仓库列表"""
        url = f"{self.base_url}/users/{username}/repos"
        params = {
            "per_page": per_page,
            "sort": "updated"
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return [{"error": str(e)}]


def main():
    """简单的命令行交互"""
    import argparse
    
    parser = argparse.ArgumentParser(description="GitHub MCP Server")
    parser.add_argument("--token", help="GitHub Personal Access Token")
    
    args = parser.parse_args()
    
    mcp = GitHubMCP(args.token)
    
    print("GitHub MCP Server - 简单查询工具")
    print("=" * 50)
    
    while True:
        print("\n请选择操作:")
        print("1. 搜索仓库")
        print("2. 获取仓库信息")
        print("3. 获取用户仓库列表")
        print("4. 退出")
        
        choice = input("\n请输入选项 (1-4): ").strip()
        
        if choice == "1":
            query = input("请输入搜索关键词: ").strip()
            if query:
                result = mcp.search_repos(query)
                if "items" in result:
                    print(f"\n找到 {result['total_count']} 个仓库:")
                    for i, repo in enumerate(result["items"], 1):
                        print(f"\n{i}. {repo['name']}")
                        print(f"   Stars: {repo['stargazers_count']}")
                        print(f"   描述: {repo.get('description', '无')}")
                        print(f"   地址: {repo['html_url']}")
                else:
                    print(f"错误: {result.get('error', '未知错误')}")
        
        elif choice == "2":
            owner = input("请输入仓库所有者: ").strip()
            repo = input("请输入仓库名称: ").strip()
            if owner and repo:
                result = mcp.get_repo_info(owner, repo)
                if "error" not in result:
                    print(f"\n仓库信息:")
                    print(f"名称: {result['name']}")
                    print(f"Stars: {result['stargazers_count']}")
                    print(f"Forks: {result['forks_count']}")
                    print(f"语言: {result.get('language', '未知')}")
                    print(f"地址: {result['html_url']}")
                else:
                    print(f"错误: {result['error']}")
        
        elif choice == "3":
            username = input("请输入用户名: ").strip()
            if username:
                repos = mcp.list_user_repos(username)
                print(f"\n{username} 的仓库:")
                for i, repo in enumerate(repos, 1):
                    if "name" in repo:
                        print(f"{i}. {repo['name']} - {repo.get('description', '无')}")
        
        elif choice == "4":
            print("再见!")
            break
        
        else:
            print("无效选项，请重新输入!")


if __name__ == "__main__":
    main()
