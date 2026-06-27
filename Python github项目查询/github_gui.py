import tkinter as tk
from tkinter import ttk
import os
import time
import re
import webbrowser
import requests
from openai import OpenAI

class AIAssistant:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('NVIDIA_API_KEY')
        if not self.api_key:
            raise ValueError("API密钥未设置，请设置NVIDIA_API_KEY环境变量")
        
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=self.api_key,
            timeout=60.0
        )
        self.max_retries = 3
        self.retry_delay = 2
    
    def chat(self, prompt, model, temperature=1, top_p=0.9, max_tokens=16384, thinking_budget=0, stream=False):
        extra_body = {"thinking_budget": thinking_budget} if thinking_budget else None
        
        for attempt in range(self.max_retries):
            try:
                completion = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    stream=stream,
                    extra_body=extra_body,
                    timeout=60.0
                )
                if stream:
                    return completion
                else:
                    return completion.choices[0].message.content
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"API连接失败，{self.retry_delay}秒后重试... ({attempt + 1}/{self.max_retries})")
                    time.sleep(self.retry_delay)
                else:
                    raise e

class github_gui:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub 助手")
        self.aiassistant = AIAssistant()
        self.create_widgets()
    
    def search_github_repos(self, query, per_page=5):
        url = "https://api.github.com/search/repositories"
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
            print(f"GitHub API 请求错误: {e}")
            return None
    
    def format_repo_data(self, repo_data):
        if not repo_data or 'items' not in repo_data:
            return ""
        
        formatted = "以下是从 GitHub 搜索到的相关仓库：\n\n"
        for idx, repo in enumerate(repo_data['items'], 1):
            formatted += f"{idx}. {repo['name']}\n"
            formatted += f"   所有者: {repo['owner']['login']}\n"
            formatted += f"   描述: {repo.get('description', '无描述')}\n"
            formatted += f"   Stars: {repo['stargazers_count']}\n"
            formatted += f"   Forks: {repo['forks_count']}\n"
            formatted += f"   语言: {repo.get('language', '未知')}\n"
            formatted += f"   地址: {repo['html_url']}\n\n"
        
        return formatted
    
    def extract_urls_from_repo_data(self, repo_data):
        urls = []
        if repo_data and 'items' in repo_data:
            for repo in repo_data['items']:
                if 'html_url' in repo:
                    urls.append(repo['html_url'])
        return urls
    
    def create_widgets(self):
        label = tk.Label(self.root, text="GitHub 助手", font=("Arial", 14))
        label.pack(pady=10)

        scrollbar = tk.Scrollbar(self.root)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_box = tk.Text(
            self.root,
            font=("Arial", 12),
            height=20,
            width=60,
            yscrollcommand=scrollbar.set
        )
        self.text_box.pack(padx=10, pady=10)
        self.text_box.config(state=tk.DISABLED)

        self.links_frame = tk.LabelFrame(self.root, text="快速链接", font=("Arial", 10))
        self.links_frame.pack(padx=10, pady=5, fill=tk.X)
        
        self.links_container = tk.Frame(self.links_frame)
        self.links_container.pack(padx=5, pady=5, fill=tk.X)

        input_frame = tk.Frame(self.root)
        input_frame.pack(pady=10, padx=10, fill=tk.X)

        self.entry = tk.Entry(input_frame, width=40)
        self.entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.entry.bind('<Return>', lambda e: self.send_message())

        self.model_var = tk.StringVar()
        self.model_var.set("stepfun-ai/step-3.5-flash")
        model_menu = ttk.OptionMenu(input_frame, self.model_var, "stepfun-ai/step-3.5-flash", 
                                     "stepfun-ai/step-3.5-flash", "deepseek/deepseek-3.2", 
                                     "qwen/qwen3-coder-480b-a35b-instruct")
        model_menu.pack(side=tk.LEFT, padx=5)

        button = tk.Button(input_frame, text="发送", command=self.send_message)
        button.pack(side=tk.LEFT, padx=5)

        scrollbar.config(command=self.text_box.yview)
    
    def extract_urls(self, text):
        url_pattern = r'https?://[^\s<>\]\)\"\']+'
        urls = re.findall(url_pattern, text)
        return list(set(urls))
    
    def open_url(self, url):
        webbrowser.open(url)
    
    def clear_link_buttons(self):
        for widget in self.links_container.winfo_children():
            widget.destroy()
    
    def create_link_buttons(self, urls):
        self.clear_link_buttons()
        
        if not urls:
            no_links_label = tk.Label(self.links_container, text="暂无链接", fg="gray")
            no_links_label.pack(pady=5)
            return
        
        for idx, url in enumerate(urls):
            repo_name = url.split('/')[-1] if '/' in url else url
            display_text = repo_name[:25] + "..." if len(repo_name) > 25 else repo_name
            btn = tk.Button(
                self.links_container,
                text=display_text,
                command=lambda u=url: self.open_url(u),
                fg="blue",
                cursor="hand2",
                relief=tk.RAISED,
                padx=10,
                pady=3
            )
            btn.grid(row=idx//2, column=idx%2, padx=5, pady=5, sticky="w")
    
    def send_message(self):
        question = self.entry.get().strip()
        if not question:
            return
        
        self.text_box.config(state=tk.NORMAL)
        self.text_box.insert(tk.END, f"用户: {question}\n\n")
        self.text_box.config(state=tk.DISABLED)
        self.entry.delete(0, tk.END)
        self.root.update()
        
        try:
            repo_data = self.search_github_repos(question)
            formatted_repos = self.format_repo_data(repo_data)
            
            prompt = f"""你是一个专业的 GitHub 助手，我已经为你集成了 GitHub API 功能。

## 可用的 GitHub API 功能：

1. **仓库搜索** - 已自动为你执行！系统会根据用户输入自动搜索 GitHub 上的相关仓库，按 Stars 数量排序，返回最热门的结果。

2. **搜索结果包含的信息**：
   - 仓库名称和所有者
   - 项目描述
   - Stars 数量（受欢迎程度）
   - Forks 数量
   - 主要编程语言
   - 仓库地址

3. **如何使用这些信息**：
   - 分析用户需求，找到最匹配的仓库
   - 推荐热门仓库并说明理由
   - 对比多个仓库的优缺点
   - 提供使用建议和学习资源

---

## 当前用户查询：
{question}

---

## 实时 GitHub 搜索结果：
{formatted_repos}

---

## 你的任务：
请根据以上信息，用中文友好、专业地回答用户问题。

如果搜索到相关仓库：
- 重点推荐最热门/最相关的 2-3 个仓库
- 说明每个仓库的特点和适用场景
- 提供学习和使用建议
- 确保包含仓库的完整 URL 链接

如果没有找到相关仓库：
- 给出通用的搜索建议
- 推荐该领域的知名项目
- 提供学习路径建议"""
            
            self.text_box.config(state=tk.NORMAL)
            self.text_box.insert(tk.END, "助手: ")
            self.text_box.config(state=tk.DISABLED)
            self.root.update()
            
            stream = self.aiassistant.chat(prompt, model=self.model_var.get(), stream=True)
            
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    self.text_box.config(state=tk.NORMAL)
                    self.text_box.insert(tk.END, content)
                    self.text_box.config(state=tk.DISABLED)
                    self.text_box.see(tk.END)
                    self.root.update()
            
            self.text_box.config(state=tk.NORMAL)
            self.text_box.insert(tk.END, "\n\n")
            self.text_box.config(state=tk.DISABLED)
            self.text_box.see(tk.END)
            
            ai_urls = self.extract_urls(full_response)
            repo_urls = self.extract_urls_from_repo_data(repo_data)
            all_urls = list(set(ai_urls + repo_urls))
            
            print(f"从 AI 回答提取的链接: {ai_urls}")
            print(f"从搜索结果提取的链接: {repo_urls}")
            print(f"所有链接: {all_urls}")
            
            self.create_link_buttons(all_urls)
            
        except Exception as e:
            self.text_box.config(state=tk.NORMAL)
            self.text_box.insert(tk.END, f"错误: {str(e)}\n\n")
            self.text_box.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = github_gui(root)
    root.mainloop()
