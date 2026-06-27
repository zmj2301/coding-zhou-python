import requests
import json

def search_github_repos(query, per_page=10):
    """
    搜索GitHub仓库
    :param query: 搜索关键词
    :param per_page: 每页返回数量
    :return: 搜索结果
    """
    url = f"https://api.github.com/search/repositories"
    params = {
        "q": query,
        "per_page": per_page,
        "sort": "stars",
        "order": "desc"
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
        return None

def get_repo_info(owner, repo):
    """
    获取指定仓库的详细信息
    :param owner: 仓库所有者
    :param repo: 仓库名称
    :return: 仓库信息
    """
    url = f"https://api.github.com/repos/{owner}/{repo}"
    
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
        return None

def print_repo_info(repo):
    """
    打印仓库信息
    :param repo: 仓库数据
    """
    print(f"\n{'='*60}")
    print(f"项目名称: {repo['name']}")
    print(f"所有者: {repo['owner']['login']}")
    print(f"描述: {repo.get('description', '无描述')}")
    print(f"Stars: {repo['stargazers_count']}")
    print(f"Forks: {repo['forks_count']}")
    print(f"语言: {repo.get('language', '未知')}")
    print(f"仓库地址: {repo['html_url']}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    print("GitHub项目查询工具")
    print("1. 搜索项目")
    print("2. 查询指定项目详情")
    
    choice = input("\n请选择功能 (1/2): ").strip()
    
    if choice == "1":
        query = input("请输入搜索关键词: ").strip()
        if query:
            print(f"\n正在搜索 '{query}'...")
            result = search_github_repos(query)
            if result and 'items' in result:
                print(f"\n找到 {result['total_count']} 个项目，显示前10个:")
                for repo in result['items']:
                    print_repo_info(repo)
    elif choice == "2":
        owner = input("请输入仓库所有者: ").strip()
        repo = input("请输入仓库名称: ").strip()
        if owner and repo:
            print(f"\n正在查询 {owner}/{repo}...")
            repo_info = get_repo_info(owner, repo)
            if repo_info:
                print_repo_info(repo_info)
    else:
        print("无效的选择")
