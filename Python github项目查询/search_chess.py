import requests

def search_xiangqi():
    url = "https://api.github.com/search/repositories"
    params = {
        "q": "chinese chess OR xiangqi OR 象棋",
        "per_page": 15,
        "sort": "stars",
        "order": "desc"
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        print(f"\n找到 {data['total_count']} 个相关项目\n")
        print("="*80)
        
        for i, repo in enumerate(data['items'], 1):
            print(f"\n{i}. 🌟 {repo['name']}")
            print(f"   👤 作者: {repo['owner']['login']}")
            print(f"   ⭐ Stars: {repo['stargazers_count']} | 🍴 Forks: {repo['forks_count']}")
            print(f"   💻 语言: {repo.get('language', '未知')}")
            print(f"   📝 描述: {repo.get('description', '暂无描述')}")
            print(f"   🔗 地址: {repo['html_url']}")
            print("-"*80)
            
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    search_xiangqi()
