import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import csv
import threading
import time
# 导入generate_maze模块，使用其字典存储功能
import generate_maze

class MazeManager:
    def __init__(self, root):
        self.root = root
        self.root.title("迷宫资源管理器")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # 迷宫数据存储
        self.mazes = []
        self.maze_files = {}
        
        # 创建主框架
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建主内容区域
        self.create_content_area()
        
        # 创建状态栏
        self.create_status_bar()
        
        # 加载默认迷宫数据
        self.load_default_mazes()
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = ttk.Frame(self.main_frame, relief=tk.RAISED, style='Toolbar.TFrame')
        toolbar.pack(fill=tk.X, pady=5)
        
        # 设置工具栏样式
        style = ttk.Style()
        style.configure('Toolbar.TFrame', background='#f0f0f0')
        
        # 启动游戏按钮
        self.play_btn = ttk.Button(toolbar, text="启动游戏", command=self.start_game, style='Play.TButton')
        self.play_btn.pack(side=tk.LEFT, padx=5)
        
        # 分隔线
        separator1 = ttk.Separator(toolbar, orient=tk.VERTICAL)
        separator1.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # 新建按钮
        self.new_btn = ttk.Button(toolbar, text="新建迷宫", command=self.new_maze)
        self.new_btn.pack(side=tk.LEFT, padx=5)
        
        # 导入按钮
        self.import_btn = ttk.Button(toolbar, text="导入迷宫", command=self.import_maze)
        self.import_btn.pack(side=tk.LEFT, padx=5)
        
        # 删除按钮
        self.delete_btn = ttk.Button(toolbar, text="删除选中", command=self.delete_selected, state=tk.DISABLED)
        self.delete_btn.pack(side=tk.LEFT, padx=5)
        
        # 分隔线
        separator2 = ttk.Separator(toolbar, orient=tk.VERTICAL)
        separator2.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # 刷新按钮
        self.refresh_btn = ttk.Button(toolbar, text="刷新", command=self.refresh_mazes)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
    
    def create_content_area(self):
        """创建主内容区域"""
        content_frame = ttk.Frame(self.main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 项目列表区域（占据整个宽度）
        self.maze_frame = ttk.LabelFrame(content_frame, text="迷宫项目")
        self.maze_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 项目列表容器，用于实现滚动
        self.maze_list = tk.Frame(self.maze_frame)
        self.maze_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 添加滚动条
        self.scrollbar = ttk.Scrollbar(self.maze_frame, orient=tk.VERTICAL, command=self.on_scroll)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 配置画布用于滚动
        self.canvas = tk.Canvas(self.maze_list, yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.canvas.yview)
        
        # 创建内部框架用于放置迷宫按钮
        self.maze_buttons_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.maze_buttons_frame, anchor=tk.NW)
        
        # 绑定滚动事件
        self.maze_buttons_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_var = tk.StringVar()
        if self.mazes:
            self.status_var.set("就绪")
        else:
            self.status_var.set("请先加载迷宫数据")
        
        status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
    
    def load_default_mazes(self):
        """加载默认迷宫数据"""
        # 清空本地迷宫列表
        self.mazes.clear()
        
        # 检查generate_maze模块中的字典是否有迷宫数据
        if not generate_maze.list_mazes():
            # 如果没有，生成一个默认迷宫
            generate_maze.generate_maze(20, "默认迷宫")
        
        # 从generate_maze模块的字典中获取所有迷宫
        for maze_name in generate_maze.list_mazes():
            maze = generate_maze.get_maze(maze_name)
            if maze:
                self.mazes.append({
                    'name': maze_name,
                    'size': f"{maze['size']}x{maze['size']}",
                    'date': time.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # 显示迷宫列表
        self.display_mazes()
        self.update_status(f"已加载 {len(self.mazes)} 个迷宫")
    
    def display_mazes(self):
        """显示迷宫列表"""
        # 清空现有按钮
        for widget in self.maze_buttons_frame.winfo_children():
            widget.destroy()
        
        # 创建迷宫按钮
        for i, maze in enumerate(self.mazes):
            # 计算位置
            row = i // 3
            col = i % 3
            
            # 创建迷宫按钮框架
            btn_frame = ttk.Frame(self.maze_buttons_frame, padding=5, relief=tk.RAISED, borderwidth=2)
            btn_frame.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            
            # 配置网格权重
            self.maze_buttons_frame.grid_columnconfigure(col, weight=1)
            self.maze_buttons_frame.grid_rowconfigure(row, weight=1)
            
            # 设置选中状态
            if hasattr(self, 'selected_maze') and self.selected_maze and self.selected_maze['name'] == maze['name']:
                btn_frame.configure(relief=tk.SUNKEN, borderwidth=3)
            else:
                btn_frame.configure(relief=tk.RAISED, borderwidth=2)
            
            # 创建迷宫按钮
            maze_btn = ttk.Button(
                btn_frame, 
                text=f"{maze['name']}\n{maze['size']}",
                style='Maze.TButton',
                command=lambda m=maze, bf=btn_frame: self.select_maze(m, bf)
            )
            maze_btn.pack(fill=tk.BOTH, expand=True, pady=5)
            
            # 创建按钮框架
            action_frame = ttk.Frame(btn_frame)
            action_frame.pack(fill=tk.X, side=tk.BOTTOM)
            
            # 添加重命名按钮
            rename_btn = ttk.Button(
                action_frame, 
                text="重命名",
                style='Rename.TButton',
                command=lambda m=maze: self.rename_maze(m)
            )
            rename_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
            
            # 添加删除按钮
            delete_btn = ttk.Button(
                action_frame, 
                text="删除",
                style='Delete.TButton',
                command=lambda m=maze: self.delete_maze(m)
            )
            delete_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=2)
            
            # 绑定事件
            maze_btn.bind("<Button-3>", lambda e, m=maze: self.show_context_menu(e, m))
            maze_btn.bind("<Double-1>", lambda e, m=maze: self.preview_maze(m))
            btn_frame.bind("<Double-1>", lambda e, m=maze: self.preview_maze(m))
        
        # 更新画布滚动区域
        self.on_frame_configure(None)
    
    def new_maze(self):
        """创建新的空白迷宫"""
        # 生成唯一的迷宫名称
        maze_count = len(self.mazes) + 1
        maze_name = f"新迷宫_{maze_count}"
        
        # 使用generate_maze模块生成新迷宫，直接保存到字典中
        generate_maze.generate_maze(20, maze_name)
        
        # 重新加载迷宫列表
        self.load_default_mazes()
        
        self.update_status(f"已创建新迷宫: {maze_name}")
        self.animate_add(len(self.mazes) - 1)
    
    def import_maze(self):
        """导入外部迷宫数据文件"""
        file_path = filedialog.askopenfilename(
            title="导入迷宫数据文件",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                # 解析迷宫数据
                with open(file_path, 'r') as f:
                    reader = csv.reader(f)
                    maze_data = [list(map(int, row)) for row in reader]
                
                # 检查迷宫数据格式
                if not maze_data or not all(len(row) == len(maze_data[0]) for row in maze_data):
                    messagebox.showerror("错误", "迷宫数据格式不正确")
                    return
                
                # 获取文件名作为迷宫名称
                maze_name = os.path.splitext(os.path.basename(file_path))[0]
                
                # 检查名称是否已存在，若存在则生成新名称
                counter = 1
                original_name = maze_name
                while maze_name in generate_maze.list_mazes():
                    maze_name = f"{original_name}_{counter}"
                    counter += 1
                
                # 直接将迷宫数据添加到generate_maze模块的字典中
                size = len(maze_data)
                # 查找起点和终点
                start = (2, 1)  # 默认起点
                end = (size-2, size-2)  # 默认终点
                
                # 在迷宫数据中查找实际的起点(0)和终点(3)
                for i in range(size):
                    for j in range(size):
                        if maze_data[i][j] == 3:
                            end = (i, j)
                            break
                    if end != (size-2, size-2):
                        break
                
                # 添加到generate_maze模块的字典中
                generate_maze.maze_dictionary[maze_name] = {
                    "data": maze_data,
                    "size": size,
                    "start": start,
                    "end": end
                }
                
                # 重新加载迷宫列表
                self.load_default_mazes()
                self.update_status(f"已导入迷宫: {maze_name}")
                self.animate_add(len(self.mazes) - 1)
            except Exception as e:
                messagebox.showerror("错误", f"导入失败: {str(e)}")
    
    def delete_maze(self, maze):
        """删除迷宫"""
        if messagebox.askyesno("确认删除", f"确定要删除迷宫 '{maze['name']}' 吗？\n删除后将无法恢复！"):
            # 使用generate_maze模块的delete_maze函数删除迷宫
            if generate_maze.delete_maze(maze['name']):
                # 重新加载迷宫列表
                self.load_default_mazes()
                self.update_status(f"已删除迷宫: {maze['name']}")
                # 构建迷宫文件路径
                maze_file_path = os.path.join('mazes', f"{maze['name']}.csv")
                # 只在文件存在时才删除
                if os.path.exists(maze_file_path):
                    os.remove(maze_file_path)
            else:
                messagebox.showerror("错误", "删除迷宫失败！")
    
    def delete_selected(self):
        """删除选中的迷宫"""
        if hasattr(self, 'selected_maze') and self.selected_maze:
            # 调用delete_maze函数删除选中的迷宫
            self.delete_maze(self.selected_maze)
            # 重置选中状态
            self.selected_maze = None
            # 禁用删除选中按钮
            self.delete_btn.config(state=tk.DISABLED)
        else:
            messagebox.showinfo("提示", "请先选择一个迷宫！")
    
    def select_maze(self, maze, btn_frame):
        """选择迷宫"""
        self.selected_maze = maze
        
        # 更新所有按钮框架的状态
        for widget in self.maze_buttons_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                widget.configure(relief=tk.RAISED, borderwidth=2)
        
        # 设置当前选中的按钮框架为凹陷状态
        btn_frame.configure(relief=tk.SUNKEN, borderwidth=3)
        
        self.update_status(f"已选择迷宫: {maze['name']}")
        
        # 启用删除选中按钮
        self.delete_btn.config(state=tk.NORMAL)
    
    def rename_maze(self, maze):
        """重命名迷宫"""
        # 创建重命名对话框
        rename_window = tk.Toplevel(self.root)
        rename_window.title("重命名迷宫")
        rename_window.geometry("300x150")
        rename_window.resizable(False, False)
        
        # 居中显示
        rename_window.transient(self.root)
        rename_window.grab_set()
        
        # 添加标签和输入框
        ttk.Label(rename_window, text="新名称:").pack(pady=20)
        
        name_var = tk.StringVar(value=maze['name'])
        name_entry = ttk.Entry(rename_window, textvariable=name_var, width=30)
        name_entry.pack(pady=5)
        name_entry.focus_set()
        name_entry.select_range(0, tk.END)
        
        def apply_rename():
            new_name = name_var.get().strip()
            if new_name:
                if new_name != maze['name']:
                    # 检查新名称是否已存在
                    if any(m['name'] == new_name for m in self.mazes if m != maze):
                        messagebox.showerror("错误", "迷宫名称已存在！")
                        return
                    
                    # 使用generate_maze模块的rename_maze函数重命名迷宫
                    old_name = maze['name']
                    if generate_maze.rename_maze(old_name, new_name):
                        # 重新加载迷宫列表
                        self.load_default_mazes()
                        self.update_status(f"已重命名迷宫: {old_name} → {new_name}")
                        # 关闭对话框
                        rename_window.destroy()
                    else:
                        messagebox.showerror("错误", "重命名迷宫失败！")
                else:
                    # 名称未改变
                    rename_window.destroy()
            else:
                messagebox.showerror("错误", "迷宫名称不能为空！")
        
        # 添加按钮
        button_frame = ttk.Frame(rename_window)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="确定", command=apply_rename).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=rename_window.destroy).pack(side=tk.RIGHT, padx=10)
        
        # 绑定回车键
        rename_window.bind('<Return>', lambda e: apply_rename())
    
    def preview_maze(self, maze):
        """预览迷宫"""
        # 创建预览窗口
        preview_window = tk.Toplevel(self.root)
        preview_window.title(f"迷宫预览: {maze['name']}")
        preview_window.geometry("400x400")
        
        # 居中显示
        preview_window.transient(self.root)
        preview_window.grab_set()
        
        # 添加迷宫信息
        info_frame = ttk.Frame(preview_window)
        info_frame.pack(fill=tk.X, pady=10, padx=10)
        
        ttk.Label(info_frame, text=f"名称: {maze['name']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"尺寸: {maze['size']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"类型: 内存字典存储").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"修改日期: {maze['date']}").pack(anchor=tk.W)
        
        # 添加预览画布
        canvas_frame = ttk.Frame(preview_window)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(canvas_frame, bg="white")
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # 从generate_maze模块的字典中获取迷宫数据
        try:
            # 获取迷宫数据
            maze_data = generate_maze.get_maze(maze['name'])['data']
            
            # 绘制迷宫
            def draw_maze(event=None):
                canvas.delete("all")
                
                # 计算缩放比例
                cell_size = min(canvas.winfo_width(), canvas.winfo_height()) // max(len(maze_data), len(maze_data[0]))
                cell_size = max(cell_size, 5)  # 最小5像素
                
                # 计算偏移量，使迷宫居中
                offset_x = (canvas.winfo_width() - len(maze_data[0]) * cell_size) // 2
                offset_y = (canvas.winfo_height() - len(maze_data) * cell_size) // 2
                
                for y, row in enumerate(maze_data):
                    for x, cell in enumerate(row):
                        if cell == 1:  # 墙
                            color = "black"
                        elif cell == 0:  # 可通行
                            color = "white"
                        elif cell == 3:  # 终点
                            color = "red"
                        else:  # 其他
                            color = "gray"
                        
                        canvas.create_rectangle(
                            offset_x + x * cell_size, offset_y + y * cell_size,
                            offset_x + (x + 1) * cell_size, offset_y + (y + 1) * cell_size,
                            fill=color, outline="#cccccc", width=1
                        )
            
            # 绘制迷宫
            draw_maze()
            
            # 绑定窗口大小变化事件
            canvas.bind("<Configure>", draw_maze)
            
            # 添加关闭按钮
            ttk.Button(preview_window, text="关闭", command=preview_window.destroy).pack(pady=10)
            
        except Exception as e:
            ttk.Label(canvas_frame, text=f"预览失败: {str(e)}", foreground="red").pack(pady=20)
            ttk.Button(preview_window, text="关闭", command=preview_window.destroy).pack(pady=10)
    
    def show_context_menu(self, event, maze):
        """显示右键菜单"""
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="预览", command=lambda: self.preview_maze(maze))
        context_menu.add_command(label="重命名", command=lambda: self.rename_maze(maze))
        context_menu.add_command(label="删除", command=lambda: self.delete_maze(maze), foreground="red")
        
        # 显示右键菜单
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def refresh_mazes(self):
        """刷新迷宫列表"""
        self.mazes.clear()
        self.load_default_mazes()
        self.update_status("迷宫列表已刷新")
    
    def animate_add(self, index):
        """添加动画效果"""
        # 这里可以实现平滑的添加动画
        pass
    
    def update_status(self, message):
        """更新状态栏消息"""
        self.status_var.set(message)
        # 5秒后恢复就绪状态
        self.root.after(5000, lambda: self.status_var.set("就绪"))
    
    def on_nav_select(self, event):
        """导航项选择事件"""
        selected_item = self.nav_tree.selection()[0]
        self.update_status(f"已选择导航项: {self.nav_tree.item(selected_item, 'text')}")
        # 可以根据选择的导航项过滤迷宫列表
    
    def on_scroll(self, *args):
        """滚动事件处理"""
        if args[0] == 'moveto':
            self.canvas.yview_moveto(args[1])
        else:
            self.canvas.yview_scroll(int(args[1]), args[2])
    
    def on_frame_configure(self, event):
        """更新画布滚动区域"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_mousewheel(self, event):
        """鼠标滚轮事件处理"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def start_game(self):
        """启动游戏"""
        try:
            # 检查是否有迷宫数据
            if not generate_maze.list_mazes():
                messagebox.showinfo("提示", "当前没有迷宫数据，正在生成默认迷宫...")
                # 生成默认迷宫
                generate_maze.generate_maze(20, "default")
                selected_maze_data = generate_maze.get_maze("default")
            else:
                # 使用选中的迷宫，如果没有选中则使用默认迷宫
                if hasattr(self, 'selected_maze') and self.selected_maze:
                    selected_maze_data = generate_maze.get_maze(self.selected_maze['name'])
                else:
                    selected_maze_data = generate_maze.get_maze("default")
            
            if selected_maze_data:
                # 保存到maze_data.csv文件
                with open('maze_data.csv', 'w', newline='') as f:
                    for row in selected_maze_data['data']:
                        f.write(','.join(map(str, row)) + '\n')
                
                maze_name = self.selected_maze['name'] if hasattr(self, 'selected_maze') and self.selected_maze else "default"
                self.update_status(f"正在启动游戏，使用迷宫: {maze_name}...")
                
                # 创建线程来启动游戏并监控错误
                def start_game_thread():
                    try:
                        import subprocess
                        # 使用run等待游戏进程结束，捕获输出
                        result = subprocess.run(
                            ["D:/python.exe", "go_maze.py"],
                            capture_output=True,
                            text=True,
                            cwd=os.getcwd()
                        )
                        
                        # 检查退出码
                        if result.returncode != 0:
                            # 有错误发生，通过UI线程显示错误信息
                            error_msg = f"游戏启动失败！\n错误码: {result.returncode}\n输出: {result.stdout}\n错误: {result.stderr}"
                            self.root.after(0, lambda: messagebox.showerror("游戏启动失败", error_msg))
                            self.root.after(0, lambda: self.update_status(f"游戏启动失败: {result.returncode}"))
                        else:
                            # 游戏正常退出
                            self.root.after(0, lambda: self.update_status(f"游戏已结束，使用迷宫: {maze_name}"))
                    except Exception as e:
                        error_msg = f"启动游戏线程失败: {str(e)}"
                        self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
                        self.root.after(0, lambda: self.update_status(f"启动游戏线程失败: {str(e)}"))
                        if messagebox.showerror("错误,迷宫数据错误", error_msg):
                            if messagebox.askokcancel("建议","建议删除当前迷宫数据，否则请检查数据是否正确"):
                                # 删除当前迷宫数据
                                generate_maze.delete_maze(maze_name)
                                self.update_status(f"已删除当前迷宫数据: {maze_name}")
                                self.refresh_mazes()
                        
                
                # 启动线程
                thread = threading.Thread(target=start_game_thread)
                thread.daemon = True  # 设置为守护线程，主线程退出时自动结束
                thread.start()
                
            else:
                messagebox.showerror("错误", "获取迷宫数据失败！")
        except Exception as e:
            messagebox.showerror("错误", f"启动游戏失败: {str(e)}")
            self.update_status(f"启动游戏失败: {str(e)}")
    
    def run(self):
        """运行应用"""
        # 设置样式
        style = ttk.Style()
        style.configure('Maze.TButton', font=('Arial', 10, 'bold'))
        style.configure('Delete.TButton', foreground='red')
        style.configure('Play.TButton', foreground='green', font=('Arial', 10, 'bold'))
        
        # 启动主循环
        self.root.mainloop()

# 主程序
if __name__ == "__main__":
    root = tk.Tk()
    app = MazeManager(root)
    app.run()