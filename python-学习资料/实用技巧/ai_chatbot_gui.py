#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI聊天机器人图形用户界面应用程序
使用Python的Tkinter库开发，实现完整的聊天功能

运行说明：
1. 直接运行此脚本，无需安装额外非标准库
2. 在输入框中输入消息，点击"发送"按钮或按Enter键发送
3. 按Shift+Enter实现换行输入
4. 点击"清除聊天"按钮清空聊天记录
"""

import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import messagebox
import time
import random
import threading
import json
import urllib.request

# 尝试导入OpenAI客户端库，用于DeepSeek API
has_openai = False
try:
    from openai import OpenAI
    has_openai = True
    print("检测到OpenAI客户端库，将支持DeepSeek API")
except ImportError as e:
    print(f"未安装OpenAI客户端库: {e}")

# 尝试使用Ollama API，这是一个本地运行的AI模型服务
def is_ollama_available():
    """检查Ollama服务是否可用"""
    try:
        # 检查Ollama API是否可访问
        url = "http://localhost:11434/api/tags"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=2) as response:
            if response.status == 200:
                return True
    except Exception as e:
        print(f"Ollama服务不可用: {e}")
    return False

has_ollama = is_ollama_available()

# 尝试导入transformers库，如果没有则使用基于规则的回复
has_transformers = False
try:
    import transformers
    print(f"检测到transformers库，版本: {transformers.__version__}")
    from transformers import pipeline
    import torch
    print(f"检测到torch库，版本: {torch.__version__}")
    has_transformers = True
except ImportError as e:
    print(f"未安装或无法导入transformers库: {e}")
    print("将尝试使用其他AI服务或基于规则的回复系统")
except Exception as e:
    print(f"导入库时发生意外错误: {e}")
    print("将尝试使用其他AI服务或基于规则的回复系统")

class AIChatBotGUI:
    """AI聊天机器人GUI类，封装所有界面组件和业务逻辑"""
    
    def __init__(self, root):
        """初始化聊天机器人GUI"""
        self.root = root
        self.root.title("AI聊天机器人")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # 设置主题色
        self.theme_colors = {
            "bg": "#f0f0f0",
            "user_msg_bg": "#0078d4",
            "ai_msg_bg": "#e0e0e0",
            "btn_bg": "#0078d4",
            "btn_hover_bg": "#106ebe",
            "text_color": "#333333"
        }
        
        # 初始化聊天历史
        self.chat_history = []
        
        # 初始化AI模型和客户端
        self.ai_model = None
        self.deepseek_client = None
        self.model_loaded = False
        self.model_loading = False
        self.has_deepseek = False
        
        # 创建界面组件
        self.create_widgets()
        
        # 绑定事件
        self.bind_events()
        
        # 显示欢迎消息
        self.display_ai_message("您好！我是AI聊天机器人，正在加载AI模型...")
        
        # 在后台线程加载AI模型
        self.load_ai_model()
    
    def load_ai_model(self):
        """在后台线程加载AI模型"""
        def load_model_thread():
            self.model_loading = True
            try:
                # 优先使用DeepSeek API（来自qingyunke_chat.py的配置）
                if has_openai:
                    try:
                        print("正在初始化DeepSeek API客户端...")
                        # 使用qingyunke_chat.py中的API配置
                        self.deepseek_client = OpenAI(
                            api_key=os.environ.get('DEEPSEEK_API_KEY', ''),
                            base_url="https://api.deepseek.com"
                        )
                        # 测试连接
                        test_response = self.deepseek_client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[{"role": "system", "content": "You are a helpful assistant"}, {"role": "user", "content": "Hello"}],
                            stream=False
                        )
                        print(f"DeepSeek API连接成功，测试回复: {test_response.choices[0].message.content[:20]}...")
                        self.has_deepseek = True
                        self.model_loaded = True
                        self.display_ai_message("DeepSeek AI服务连接成功！现在可以与我进行智能对话了。")
                        return
                    except Exception as e:
                        print(f"初始化DeepSeek API失败: {e}")
                
                # 其次使用Ollama API（本地运行的真实AI模型）
                if has_ollama:
                    # 使用Ollama API（本地运行的真实AI模型）
                    print("检测到Ollama服务，将使用真实AI模型！")
                    self.model_loaded = True
                    self.display_ai_message("Ollama AI服务连接成功！现在可以与我进行智能对话了。")
                    return
                
                # 再次使用Hugging Face的预训练模型
                elif has_transformers:
                    # 使用Hugging Face的预训练模型
                    print("正在加载预训练AI模型...")
                    # 使用中文对话模型
                    self.ai_model = pipeline("conversational", model="microsoft/DialoGPT-medium", framework="pt")
                    self.model_loaded = True
                    self.display_ai_message("AI模型加载完成！现在可以与我进行智能对话了。")
                    return
                
                # 最后使用基于规则的智能回复
                else:
                    self.display_ai_message("未检测到AI服务，将使用基于规则的智能回复系统。")
            except Exception as e:
                print(f"加载AI模型失败: {e}")
                self.display_ai_message(f"加载AI模型失败: {e}\n将使用基于规则的智能回复系统。")
            finally:
                self.model_loading = False
        
        # 启动后台加载线程
        threading.Thread(target=load_model_thread, daemon=True).start()
    
    def create_widgets(self):
        """创建所有界面组件"""
        # 设置全局字体
        default_font = ("Microsoft YaHei", 12)
        
        # 主容器
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 聊天历史显示区域
        self.chat_display = scrolledtext.ScrolledText(
            self.main_frame,
            wrap=tk.WORD,
            font=default_font,
            bg="white",
            fg=self.theme_colors["text_color"],
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.chat_display.configure(state=tk.DISABLED)  # 初始设置为只读
        
        # 分隔线
        ttk.Separator(self.main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 10))
        
        # 输入和按钮容器
        self.input_frame = ttk.Frame(self.main_frame)
        self.input_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 多行文本输入框
        self.input_text = tk.Text(
            self.input_frame,
            height=4,
            font=default_font,
            wrap=tk.WORD,
            bg="white",
            fg=self.theme_colors["text_color"],
            relief=tk.SOLID,
            bd=1
        )
        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # 按钮容器
        self.btn_frame = ttk.Frame(self.input_frame)
        self.btn_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 发送按钮
        self.send_btn = ttk.Button(
            self.btn_frame,
            text="发送",
            command=self.send_message,
            style="Accent.TButton"
        )
        self.send_btn.pack(fill=tk.X, pady=(0, 5))
        
        # 清除聊天按钮
        self.clear_btn = ttk.Button(
            self.btn_frame,
            text="清除聊天",
            command=self.clear_chat
        )
        self.clear_btn.pack(fill=tk.X)
        
        # 配置样式
        self.configure_styles()
    
    def configure_styles(self):
        """配置界面样式"""
        # 创建样式对象
        style = ttk.Style()
        
        # 配置按钮样式
        style.configure(
            "Accent.TButton",
            background=self.theme_colors["btn_bg"],
            foreground="white",
            font=("Microsoft YaHei", 11, "bold")
        )
        
        # 配置悬停效果
        style.map(
            "Accent.TButton",
            background=[("active", self.theme_colors["btn_hover_bg"])]
        )
    
    def bind_events(self):
        """绑定事件处理"""
        # 绑定Enter键发送消息，Shift+Enter换行
        self.input_text.bind("<Return>", self.on_enter_press)
        self.input_text.bind("<Shift-Return>", self.on_shift_enter_press)
    
    def on_enter_press(self, event):
        """处理Enter键按下事件"""
        self.send_message()
        return "break"  # 阻止默认换行行为
    
    def on_shift_enter_press(self, event):
        """处理Shift+Enter键按下事件，实现换行"""
        self.input_text.insert(tk.INSERT, "\n")
        return "break"  # 阻止默认行为
    
    def send_message(self):
        """发送消息处理"""
        # 获取用户输入
        user_input = self.input_text.get("1.0", tk.END).strip()
        
        # 验证输入不为空
        if not user_input:
            messagebox.showwarning("提示", "请输入消息内容后再发送！")
            return
        
        # 验证输入长度
        if len(user_input) > 500:
            messagebox.showwarning("提示", "输入内容过长，请控制在500字符以内！")
            return
        
        # 清空输入框
        self.input_text.delete("1.0", tk.END)
        
        # 显示用户消息
        self.display_user_message(user_input)
        
        # 模拟AI回复
        self.simulate_ai_response(user_input)
    
    def display_user_message(self, message):
        """显示用户消息"""
        self._display_message("用户", message, is_user=True)
    
    def display_ai_message(self, message):
        """显示AI消息"""
        self._display_message("AI", message, is_user=False)
    
    def _display_message(self, sender, message, is_user=False):
        """内部方法：显示消息"""
        # 获取当前时间
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 配置文本框为可编辑状态
        self.chat_display.configure(state=tk.NORMAL)
        
        # 插入消息内容
        if is_user:
            # 用户消息：右对齐，蓝色背景
            self.chat_display.tag_configure("user", foreground="white", background=self.theme_colors["user_msg_bg"], justify=tk.RIGHT)
            self.chat_display.tag_configure("user_sender", foreground=self.theme_colors["user_msg_bg"], font=("Microsoft YaHei", 10, "bold"))
            
            # 插入用户标签
            self.chat_display.insert(tk.END, f"{sender}  {timestamp}\n", "user_sender")
            # 插入消息内容
            self.chat_display.insert(tk.END, f"{message}\n\n", "user")
        else:
            # AI消息：左对齐，灰色背景
            self.chat_display.tag_configure("ai", foreground="black", background=self.theme_colors["ai_msg_bg"], justify=tk.LEFT)
            self.chat_display.tag_configure("ai_sender", foreground="#666666", font=("Microsoft YaHei", 10, "bold"))
            
            # 插入AI标签
            self.chat_display.insert(tk.END, f"{sender}  {timestamp}\n", "ai_sender")
            # 插入消息内容
            self.chat_display.insert(tk.END, f"{message}\n\n", "ai")
        
        # 配置文本框为只读状态
        self.chat_display.configure(state=tk.DISABLED)
        
        # 自动滚动到底部
        self.chat_display.see(tk.END)
    
    def simulate_ai_response(self, user_input):
        """模拟AI回复"""
        # 保存到聊天历史
        self.chat_history.append({"sender": "user", "message": user_input})
        
        # 模拟思考时间
        self.root.after(500, lambda: self._generate_ai_response(user_input))
    
    def _generate_ai_response(self, user_input):
        """生成AI回复，优先使用真实AI模型，回退到规则系统"""
        ai_response = ""
        
        # 优先使用DeepSeek API（来自qingyunke_chat.py的配置）
        if self.has_deepseek and self.deepseek_client:
            try:
                print(f"使用DeepSeek真实AI模型生成回复，用户输入: {user_input}")
                
                # 构建对话历史
                conversation_history = [{"role": "system", "content": "You are a helpful assistant"}]
                
                # 添加最近的聊天记录作为上下文
                for msg in self.chat_history[-5:]:  # 使用最近5条消息作为上下文
                    if msg["sender"] == "user":
                        conversation_history.append({"role": "user", "content": msg["message"]})
                    else:
                        conversation_history.append({"role": "assistant", "content": msg["message"]})
                
                # 添加当前用户输入
                conversation_history.append({"role": "user", "content": user_input})
                
                # 调用DeepSeek API
                response = self.deepseek_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=conversation_history,
                    stream=False
                )
                
                ai_response = response.choices[0].message.content.strip()
                print(f"DeepSeek API回复: {ai_response[:50]}...")
                
                if not ai_response:
                    ai_response = "抱歉，我暂时无法回答这个问题。"
                    
            except Exception as e:
                print(f"使用DeepSeek API失败: {e}")
                # 回退到其他AI服务
                ai_response = self._get_other_ai_response(user_input)
        else:
            # 尝试其他AI服务
            ai_response = self._get_other_ai_response(user_input)
        
        # 保存AI回复到聊天历史
        self.chat_history.append({"sender": "ai", "message": ai_response})
        
        # 显示AI回复
        self.display_ai_message(ai_response)
    
    def _get_other_ai_response(self, user_input):
        """获取其他AI服务的回复"""
        ai_response = ""
        
        # 优先使用Ollama API（本地真实AI模型）
        if has_ollama:
            try:
                print(f"使用Ollama真实AI模型生成回复，用户输入: {user_input}")
                
                # 构建对话历史
                conversation_history = []
                for msg in self.chat_history[-5:]:  # 使用最近5条消息作为上下文
                    if msg["sender"] == "user":
                        conversation_history.append({"role": "user", "content": msg["message"]})
                    else:
                        conversation_history.append({"role": "assistant", "content": msg["message"]})
                
                # 添加当前用户输入
                conversation_history.append({"role": "user", "content": user_input})
                
                # 调用Ollama API
                url = "http://localhost:11434/api/chat"
                headers = {"Content-Type": "application/json"}
                data = {
                    "model": "llama2",  # 使用默认模型
                    "messages": conversation_history,
                    "stream": False
                }
                
                req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)
                with urllib.request.urlopen(req, timeout=30) as response:
                    if response.status == 200:
                        result = json.loads(response.read().decode("utf-8"))
                        ai_response = result["message"]["content"].strip()
                    else:
                        ai_response = "抱歉，AI服务暂时不可用。"
                
                if not ai_response:
                    ai_response = "抱歉，我暂时无法回答这个问题。"
                    
            except Exception as e:
                print(f"使用Ollama API失败: {e}")
                # 回退到预训练AI模型
                ai_response = self._get_transformers_response(user_input)
        else:
            # 尝试使用预训练AI模型
            ai_response = self._get_transformers_response(user_input)
        
        return ai_response
    
    def _get_transformers_response(self, user_input):
        """获取transformers模型的回复"""
        ai_response = ""
        
        # 使用预训练AI模型
        if self.model_loaded and self.ai_model:
            try:
                print(f"使用预训练AI模型生成回复，用户输入: {user_input}")
                
                # 准备对话历史
                from transformers import Conversation
                
                # 构建对话历史
                conversation = Conversation()
                
                # 添加最近的聊天记录作为上下文
                if len(self.chat_history) > 0:
                    for msg in self.chat_history[-5:]:  # 使用最近5条消息作为上下文
                        if msg["sender"] == "user":
                            conversation.add_user_input(msg["message"])
                        else:
                            conversation.add_system_response(msg["message"])
                
                # 添加当前用户输入
                conversation.add_user_input(user_input)
                
                # 生成AI回复
                response = self.ai_model(conversation)
                ai_response = response.generated_responses[-1]
                
                # 处理模型生成的特殊字符
                ai_response = ai_response.replace("\n", " ").strip()
                
                if not ai_response:
                    ai_response = "抱歉，我暂时无法回答这个问题。"
                    
            except Exception as e:
                print(f"使用预训练AI模型失败: {e}")
                # 回退到基于规则的回复
                ai_response = self._get_fallback_response(user_input)
        else:
            # 回退到基于规则的回复
            ai_response = self._get_fallback_response(user_input)
        
        return ai_response
    
    def _get_fallback_response(self, user_input):
        """当AI模型不可用时的回退回复方法"""
        # 转换为小写以便匹配
        user_input_lower = user_input.lower()
        
        # 上下文理解：检查最近的聊天记录
        context = ""
        if len(self.chat_history) > 2:
            # 获取最近3条消息作为上下文
            recent_msgs = self.chat_history[-3:]
            context = " ".join([msg["message"] for msg in recent_msgs])
            context = context.lower()
        
        # 基于规则的回复生成
        return self._get_rule_based_response(user_input_lower, context)
    
    def _get_rule_based_response(self, user_input, context):
        """基于规则生成回复"""
        # 问候语处理
        greetings = ["你好", "您好", "hi", "hello", "早上好", "下午好", "晚上好"]
        if any(greet in user_input for greet in greetings):
            return "您好！很高兴为您服务。请问有什么可以帮助您的吗？"
        
        # 再见处理
        farewells = ["再见", "拜拜", "byebye", "goodbye", "下次见"]
        if any(farewell in user_input for farewell in farewells):
            return "再见！期待下次为您服务。"
        
        # 感谢处理
        thanks = ["谢谢", "谢谢你", "感谢", "thank you", "thanks"]
        if any(thank in user_input for thank in thanks):
            return "不客气！这是我应该做的。"
        
        # 自我介绍处理
        about_me = ["你是谁", "你是什么", "介绍一下你自己", "你的名字"]
        if any(about in user_input for about in about_me):
            return "我是一个AI聊天机器人，由Python和Tkinter开发，能够理解并回答您的问题。"
        
        # 天气相关
        weather = ["天气", "气温", "温度", "下雨", "晴天", "多云"]
        if any(w in user_input for w in weather):
            return "抱歉，我目前还没有实时天气查询功能。您可以尝试使用天气应用或网站获取最新天气信息。"
        
        # 时间相关
        time_related = ["现在几点", "几点了", "当前时间", "时间"]
        if any(t in user_input for t in time_related):
            current_time = time.strftime("%H:%M:%S")
            return f"当前时间是 {current_time}。"
        
        # 日期相关
        date_related = ["今天几号", "几号了", "日期", "今天是什么日子"]
        if any(d in user_input for d in date_related):
            current_date = time.strftime("%Y年%m月%d日")
            return f"今天是 {current_date}。"
        
        # 数学计算（简单）
        if any(op in user_input for op in ["+", "-", "*", "÷", "/", "="]):
            # 提取数字和运算符
            import re
            numbers = re.findall(r"\d+", user_input)
            if len(numbers) >= 2:
                try:
                    num1 = float(numbers[0])
                    num2 = float(numbers[1])
                    
                    if "+" in user_input:
                        result = num1 + num2
                        return f"{num1} + {num2} = {result}"
                    elif "-" in user_input:
                        result = num1 - num2
                        return f"{num1} - {num2} = {result}"
                    elif "*" in user_input or "×" in user_input:
                        result = num1 * num2
                        return f"{num1} × {num2} = {result}"
                    elif "/" in user_input or "÷" in user_input:
                        if num2 == 0:
                            return "除数不能为零。"
                        result = num1 / num2
                        return f"{num1} ÷ {num2} = {result}"
                except:
                    pass
            return "抱歉，我无法理解这个数学问题。请尝试更清晰的表达方式。"
        
        # 上下文关联：如果之前提到过某个话题，尝试跟进
        if "天气" in context:
            return "您刚才提到了天气，请问还有什么关于天气的问题吗？"
        elif "时间" in context:
            return "您刚才询问了时间，还有其他关于时间或日期的问题吗？"
        elif "数学" in context or "计算" in context:
            return "您刚才进行了数学计算，还需要计算其他问题吗？"
        
        # 询问帮助
        help_related = ["帮助", "怎么用", "功能", "能做什么"]
        if any(h in user_input for h in help_related):
            return "我可以为您提供以下帮助：\n1. 回答常见问题\n2. 进行简单的数学计算\n3. 提供时间和日期信息\n4. 进行多轮对话\n请问您需要什么帮助？"
        
        # 情绪表达
        if any(emotion in user_input for emotion in ["开心", "高兴", "快乐", "愉快"]):
            return "很高兴听到您心情这么好！保持愉快的心情对健康很重要。"
        elif any(emotion in user_input for emotion in ["难过", "伤心", "不开心", "郁闷"]):
            return "听到您不开心，我很抱歉。希望您能尽快好起来，有什么可以帮助您的吗？"
        
        # 默认回复：尝试理解用户意图
        return f"您刚才说：'{user_input}'，我正在努力理解。请问您能提供更多信息，或者换一种方式表达吗？"
    
    def clear_chat(self):
        """清除聊天记录"""
        # 确认清除操作
        if messagebox.askyesno("确认", "确定要清空所有聊天记录吗？"):
            # 配置文本框为可编辑状态
            self.chat_display.configure(state=tk.NORMAL)
            # 清空内容
            self.chat_display.delete("1.0", tk.END)
            # 配置文本框为只读状态
            self.chat_display.configure(state=tk.DISABLED)
            # 清空聊天历史
            self.chat_history.clear()
            # 显示欢迎消息
            self.display_ai_message("您好！我是AI聊天机器人，很高兴为您服务。")
            # 保存欢迎消息到聊天历史
            self.chat_history.append({"sender": "ai", "message": "您好！我是AI聊天机器人，很高兴为您服务。"})

if __name__ == "__main__":
    # 创建主窗口
    root = tk.Tk()
    
    # 设置窗口图标（可选）
    try:
        # 尝试设置图标，如果没有图标文件则忽略
        pass
    except Exception:
        pass
    
    # 创建聊天机器人GUI实例
    app = AIChatBotGUI(root)
    
    # 运行主循环
    root.mainloop()
