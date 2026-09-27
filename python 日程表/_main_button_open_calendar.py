    def button_open_calendar(self):
            import tkinter as tk
            from tkinter import ttk
            import calendar
            from tkinter import filedialog
            from tkinter import messagebox
            import json
            
            def get_answer(question):
                # 调用AI模型获取回答
                try:
                    from zai._client import ZhipuAiClient
                    
                    client = ZhipuAiClient(api_key=os.environ.get('ZHIPUAI_API_KEY', ''))
                    response = client.chat.completions.create(
                        model="glm-4.7-flash",
                        messages=[
                            {"role": "user", "content": question},
                            {"role": "assistant", "content": "回答尽量简短100字，说说你对这个的看法，千万避免长时间思考"},
                            {"role": "user", "content": "帮我说说这个的好处,富有互动性"}
                            ],
                        thinking={
                            "type": "enabled",    # 启用深度思考模式
                        },
                        
                        max_tokens=1000,          # 最大输出tokens
                        temperature=5.0           # 控制输出的随机性
                    )

                    answer = response.choices[0].message.content
                    return f"\n\nAI回答: {answer}"
                except Exception as e:
                    return f"\n\nAI回答获取失败: {str(e)}"
            
            def mark_as_completed(day, month):
                # 检查事件是否存在
                # 查找匹配的事件
                event_found = None
                for event in self.events:
                    if int(event['month']) == month and int(event['day']) == day:
                        event_found = event
                        break
                
                if event_found:
                    if not messagebox.askokcancel("确认", f"确定将 {month}月{day}日 的事件标记为已完成吗？\n删除后不可恢复！！！"):
                        return

                    # 标记为已完成
                    event_found['completed'] = True
                    # 如果事件描述中包含*，替换为+
                    if '*' in event_found['things']:
                        event_found['things'] = event_found['things'].replace('*', '+')
                        self.delete_events[(day, month)] = event_found['things']
                    self.events.remove(event_found)
                    # 刷新日历显示，更新*标记
                    show_calendar()
                    # 刷新事件详情显示
                    refresh_text()
                else:
                    # 事件不存在
                    messagebox.showwarning("警告", f"日期 {month}月{day}日 不存在事件")
                    return

            def show_calendar(*args):
                def update_answer(question, month, day):
                    import time
                    import json
                    
                    # 解除锁定
                    self.text.config(state=tk.NORMAL)
                    
                    # 清空文本框
                    self.text.delete(1.0, tk.END)
                    
                    # 插入标题
                    self.text.insert(tk.END, f"{month}月{day}日的事件:\n", "header")
                    
                    # 显示用户的事情
                    if question:
                        self.text.insert(tk.END, f"• {question}\n\n", "event")
                    
                    data = str(month)+'.'+str(day)
                    
                    # 日期特征分析
                    def get_date_features(month, day):
                        features = []
                        
                        # 季节判断
                        if 3 <= month <= 5:
                            features.append("春季")
                        elif 6 <= month <= 8:
                            features.append("夏季")
                        elif 9 <= month <= 11:
                            features.append("秋季")
                        else:
                            features.append("冬季")
                        
                        # 节假日判断
                        holidays = {
                            (1, 1): "元旦",
                            (2, 14): "情人节",
                            (3, 8): "妇女节",
                            (4, 1): "愚人节",
                            (4, 4): "清明节",
                            (5, 1): "劳动节",
                            (6, 1): "儿童节",
                            (8, 1): "建军节",
                            (9, 10): "教师节",
                            (10, 1): "国庆节",
                            (12, 25): "圣诞节"
                        }
                        
                        if (month, day) in holidays:
                            features.append(f"{holidays[(month, day)]}节")
                        
                        # 特殊日期
                        if month == 12 and day >= 20:
                            features.append("年末")
                        elif month == 1 and day <= 10:
                            features.append("年初")
                        
                        return features
                    
                    # 直接调用get_answer获取新的AI回答
                    if self.ai_enable:
                        # 生成包含日期特征的提示词
                        date_features = get_date_features(month, day)
                        feature_text = "，".join(date_features)
                        enhanced_question = f"请对{month}月{day}日（{feature_text}）的事件进行评价：{question}"
                        
                        print(f"生成新的AI回答: {data}")
                        ai_answer = get_answer(enhanced_question)
                        
                        # 验证AI回答的格式与内容完整性
                        if not ai_answer or not isinstance(ai_answer, str) or len(ai_answer.strip()) == 0:
                            print("AI回答格式错误或内容为空")
                            ai_answer = "AI回答生成失败，请稍后重试"
                        else:
                            # 确保回答内容完整
                            ai_answer = ai_answer.strip()
                    else:
                        ai_answer = "AI解析已禁用"
                    
                    # 确保answers_json包含所有现有数据
                    if not hasattr(self, 'answers_json') or self.answers_json is None:
                        self.answers_json = {}
                    
                    # 更新AI回答文件
                    try:
                        # 准确定位到目标JSON文件的指定存储路径
                        ai_file_path = os.path.join(self.dir_path, 'ai_awswers.json')
                        print(f"更新AI回答文件路径: {ai_file_path}")
                        
                        # 加载现有数据，确保不影响其他数据的完整性
                        if os.path.exists(ai_file_path):
                            try:
                                with open(ai_file_path, 'r', encoding='utf-8') as f:
                                    file_content = f.read().strip()
                                    if file_content:
                                        try:
                                            existing_data = json.loads(file_content)
                                            # 确保existing_data是字典类型
                                            if isinstance(existing_data, dict):
                                                self.answers_json.update(existing_data)
                                                print(f"加载现有数据成功，共 {len(existing_data)} 条记录")
                                            else:
                                                print("现有数据格式错误，使用空数据")
                                        except json.JSONDecodeError as json_e:
                                            print(f"JSON解析失败: {json_e}")
                                            # 保留当前数据，不覆盖
                            except Exception as load_e:
                                print(f"加载现有数据失败: {load_e}")
                        
                        # 保存更新前的数据备份，以防写入失败
                        backup_data = self.answers_json.copy()
                        
                        # 更新数据
                        self.answers_json.update({data: ai_answer})
                        print(f"更新数据成功: {data} -> {ai_answer[:50]}...")
                        
                        # 执行文件写入操作并确认保存成功
                        try:
                            with open(ai_file_path, 'w', encoding='utf-8') as f:
                                f.write(json.dumps(self.answers_json, ensure_ascii=False, indent=4))
                            # 验证文件写入成功
                            if os.path.exists(ai_file_path):
                                file_size = os.path.getsize(ai_file_path)
                                print(f"文件写入成功，大小: {file_size} 字节")
                            else:
                                print("文件写入失败，文件不存在")
                                # 回退到备份数据
                                self.answers_json = backup_data
                        except Exception as write_e:
                            print(f"文件写入失败: {write_e}")
                            # 回退到备份数据
                            self.answers_json = backup_data
                    except Exception as e:
                        print(f"更新AI回答文件失败: {e}")
                        # 回退到内存缓存
                        if not hasattr(self, 'ai_awswers'):
                            self.ai_awswers = {}
                        self.ai_awswers[data] = ai_answer
                        print(f"回退到内存缓存: {data}")
                        # 以具体日期为索引文件中保存AI回答
                    
                    # 插入AI回答
                    self.text.insert(tk.END, ai_answer, "ai_answer")
                    
                    # 锁定文本框
                    self.text.config(state=tk.DISABLED)
                    
                    # 提供操作成功的反馈信息
                    messagebox.showinfo("成功", f"{month}月{day}日的AI回答更新成功！")
                    
                # 获取年份和月份值，处理空值情况
                year_str = year_var.get().strip()
                month_str = month_var.get().strip()
                
                # 如果值为空，不进行转换和显示
                if not year_str or not month_str:
                    return
                if '*' in month_str:
                    month_str = month_str.replace('*', '')

                try:
                    year = int(year_str)
                    month = int(month_str)
                except ValueError:
                    # 如果转换失败，不执行后续操作
                    return
                
                # 清空日历框架
                for widget in calendar_frame.winfo_children():
                    widget.destroy()
                
                # 创建月份标题
                month_label = ttk.Label(calendar_frame, text=f"{year}年{month}月", 
                                    style="Title.TLabel", foreground="#409eff")
                month_label.grid(row=0, column=0, columnspan=7, pady=(0, 15))
                
                # 创建星期标题
                weekdays = ["一", "二", "三", "四", "五", "六","日"]
                for col, weekday in enumerate(weekdays):
                    # 设置周末为红色
                    if col == 5 or col == 6:
                        weekday_style = "Weekend.TLabel"
                        style.configure(weekday_style, foreground="#f56c6c")
                    else:
                        weekday_style = "Weekday.TLabel"
                        style.configure(weekday_style, foreground="#606266")
                    
                    ttk.Label(calendar_frame, text=weekday, 
                            style=weekday_style,
                            font=("Microsoft YaHei", 11, "bold")).grid(row=1, column=col, padx=8, pady=8)
                
                # 获取日历数据
                cal = calendar.monthcalendar(year, month)
                
                # 显示日历日期
                for row, week in enumerate(cal, start=2):
                    for col, day in enumerate(week):
                        if day != 0:
                            # 检查该日期是否有事件
                            has_event = False
                            for event in self.events:
                                if int(event['month']) == month and int(event['day']) == day:
                                    has_event = True
                                    break
                            
                            # 设置按钮文本，有事件则添加*标记
                            if has_event:
                                btn_text = f"{day}*"
                            else:
                                btn_text = str(day)
                            
                            # 设置周末按钮样式
                            if col == 5 or col == 6:
                                button_style = "Weekend.TButton"
                                style.configure(button_style, foreground="#f56c6c")
                            else:
                                button_style = "Calendar.TButton"
                            
                            # 创建可点击的日期按钮
                            btn = ttk.Button(calendar_frame, text=btn_text, 
                                        style=button_style,
                                        width=4)
                            # 绑定点击事件，显示当天的事件
                            btn.bind("<Button-1>", lambda e, d=day, m=month: show_events_for_date(m, d))
                            btn.grid(row=row, column=col, padx=8, pady=8)
                            
                            # 增加右键菜单功能
                            def show_context_menu(e, d=day, m=month):
                                # 创建右键菜单，使用cal_window作为父窗口
                                context_menu = tk.Menu(cal_window, tearoff=0)
                                # 添加"标记为已完成"选项
                                context_menu.add_command(label="√标记为已完成", 
                                                    command=lambda: mark_as_completed(d, m))
                                context_menu.add_separator()
                                month_str = str(m).zfill(2)
                                day_str = str(d).zfill(2)
                                context_menu.add_command(label=f"事件", 
                                                    command=lambda: add_event(month_str, day_str))
                                # 查找当天事件的第一个事项
                                question_ = ""
                                for i in self.events:
                                    if int(i['day']) == d:
                                        question_ = i['things']
                                        break
                                print("\n\n\n")
                                print(self.events)
                                print("\n\n\n")
                                print(d)
                                
                                # 只有当找到事件时才添加"更新AI回答"菜单项
                                if question_:
                                    context_menu.add_command(label='更新AI回答', 
                                                           command=lambda q=question_: update_answer(q, m, d))
                                
                                # 显示菜单
                                context_menu.post(e.x_root, e.y_root)
                            
                            # 绑定右键事件，显示上下文菜单
                            btn.bind("<Button-3>", show_context_menu)
                        else:
                            # 空单元格
                            ttk.Label(calendar_frame, text="", width=4).grid(row=row, column=col, padx=8, pady=8)

            def show_events_for_date(month, day):
                
                """显示指定日期的事件"""
                import time
                
                # 解除锁定
                self.text.config(state=tk.NORMAL)
                
                # 清空文本框
                self.text.delete(1.0, tk.END)
                
                # 日期特征分析
                def get_date_features(month, day):
                    features = []
                    
                    # 季节判断
                    if 3 <= month <= 5:
                        features.append("春季")
                    elif 6 <= month <= 8:
                        features.append("夏季")
                    elif 9 <= month <= 11:
                        features.append("秋季")
                    else:
                        features.append("冬季")
                    
                    # 节假日判断
                    holidays = {
                        (1, 1): "元旦",
                        (1, 25): "小年（北方）",
                        (1, 29): "小年（南方）",
                        (2, 14): "情人节",
                        (2, 19): "雨水（节气）",
                        (3, 8): "妇女节",
                        (3, 12): "植树节",
                        (4, 1): "愚人节",
                        (4, 4): "清明节",
                        (4, 22): "地球日",
                        (5, 1): "劳动节",
                        (5, 4): "青年节",
                        (5, 12): "护士节",
                        (6, 1): "儿童节",
                        (6, 5): "环境日",
                        (6, 21): "夏至（节气）",
                        (7, 1): "建党节",
                        (8, 1): "建军节",
                        (8, 7): "立秋（节气）",
                        (9, 10): "教师节",
                        (9, 23): "秋分（节气）",
                        (10, 1): "国庆节",
                        (10, 31): "万圣节前夜",
                        (11, 11): "光棍节",
                        (12, 20): "大雪（节气）",
                        (12, 25): "圣诞节",
                        (12, 13): "国家公祭日"
                    }
                    
                    if (month, day) in holidays:
                        features.append(f"{holidays[(month, day)]}节")
                    
                    # 特殊日期
                    if month == 12 and day >= 20:
                        features.append("年末")
                    elif month == 1 and day <= 10:
                        features.append("年初")
                    
                    return features
                
                # 查找匹配的事件
                found_events = []
                for event in self.events:
                    if int(event['month']) == month and int(event['day']) == day:
                        found_events.append(event)
                
                if found_events:
                    # 日期特征
                    date_features = get_date_features(month, day)
                    feature_text = "，".join(date_features)
                    
                    # 插入标题（包含日期特征）
                    self.text.insert(tk.END, f"{month}月{day}日（{feature_text}）的事件:\n", "header")
                    
                    question = ""
                    for event in found_events:
                        # 计算事件距离当前时间的时间差
                        event_month = int(event['month'])
                        event_day = int(event['day'])
                        
                        # 获取当前时间
                        import datetime
                        today = datetime.datetime.now()
                        event_date = datetime.datetime(today.year, event_month, event_day)
                        
                        # 计算时间差
                        time_diff = event_date - today
                        total_seconds = int(time_diff.total_seconds())
                        
                        # 格式化时间差
                        if total_seconds > 0:
                            if total_seconds < 3600:
                                time_str = f"{total_seconds // 60}分钟后"
                            elif total_seconds < 86400:
                                time_str = f"{total_seconds // 3600}小时后"
                            else:
                                time_str = f"{total_seconds // 86400}天后"
                        elif total_seconds < 0:
                            if abs(total_seconds) < 3600:
                                time_str = f"{abs(total_seconds) // 60}分钟前"
                            elif abs(total_seconds) < 86400:
                                time_str = f"{abs(total_seconds) // 3600}小时前"
                            else:
                                time_str = f"{abs(total_seconds) // 86400}天前"
                        else:
                            time_str = "今天"
                        
                        # 按照要求的格式显示事件
                        self.text.insert(tk.END, f"• {event['things']}（{time_str}）\n", "event")
                        question += f"{event['things']}"

                    # 检查是否有bool_get_ai_answer属性
                    if not hasattr(self, 'bool_get_ai_answer') or not self.bool_get_ai_answer.get():
                        return
                    # 获取点击的日期
                    data = str(month)+'.'+str(day)
                    # 加载 AI 回答文件
                    self.answers_json = {}
                    ai_file_path = self.dir_path+'/ai_awswers.json'
                    if os.path.exists(ai_file_path):
                        try:
                            with open(ai_file_path, 'r', encoding='utf-8') as f:
                                file_content = f.read().strip()
                                if file_content:
                                    self.answers_json = json.loads(file_content)
                        except Exception as e:
                            print(f"读取AI回答文件失败: {e}")
                    
                    # 生成包含日期特征的提示词
                    enhanced_question = f"请对{month}月{day}日（{feature_text}）的事件进行评价：{question}"
                    
                    # 优先从内存缓存获取
                    if data in self.ai_awswers:
                        print(f"从内存缓存获取AI回答: {data}")
                        ai_answer = self.ai_awswers[data]
                    # 从文件缓存获取
                    elif data in self.answers_json:
                        print(f"从文件缓存获取AI回答: {data}")
                        ai_answer = self.answers_json[data]
                        # 同时更新到内存缓存
                        self.ai_awswers[data] = ai_answer
                    else:
                        ai_answer = get_answer(enhanced_question)
                        try:
                            # 更新数据
                            self.answers_json.update({data: ai_answer})
                            
                            # 写入文件
                            with open(self.dir_path+'/ai_awswers.json', 'w', encoding='utf-8') as f:
                                f.write(json.dumps(self.answers_json, ensure_ascii=False, indent=4))
                        except Exception as e:
                            print(f"更新AI回答文件失败: {e}")
                            # 回退到内存缓存
                            if not hasattr(self, 'ai_awswers'):
                                self.ai_awswers = {}
                            self.ai_awswers[data] = ai_answer
                        # 以具体日期为索引文件中保存AI回答
                    
                    # 插入分隔线
                    self.text.insert(tk.END, "\nAI评价：\n", "header")
                    # 插入AI回答
                    self.text.insert(tk.END, ai_answer, "ai_answer")
                    
                else:
                    # 日期特征
                    date_features = get_date_features(month, day)
                    feature_text = "，".join(date_features)
                    self.text.insert(tk.END, f"{month}月{day}日（{feature_text}）没有相关事件\n", "header")
                
                # 锁定文本框
                self.text.config(state=tk.DISABLED)
                
            def refresh_text():
                """重置text组件为原始显示模式"""
                # 解除锁定
                self.text.config(state=tk.NORMAL)
                
                # 清空文本框
                self.text.delete(1.0, tk.END)
                
                # 按照原始模式显示
                month_data = [event['month'] for event in self.events]
                day_data = [event['day'] for event in self.events]
                things = [event['things'] for event in self.events]
                # 对于时间和日期进行排序，且合并相同日期的事件，
                sorted_events = sorted(zip(month_data, day_data, things))
                # 合并相同日期的事件
                merged_events = {}
                for month, day, thing in sorted_events:
                    if (month, day) not in merged_events:
                        merged_events[(month, day)] = []
                    merged_events[(month, day)].append(thing)
                # 重新排序，确保按日期显示
                sorted_events = sorted(merged_events.items(), key=lambda x: (x[0][0], x[0][1]))
                # 打印排序后的事件
                print("排序后的事件:", sorted_events)
                
                for (month, day), event_list in sorted_events:
                    # 将同一日期的事件合并为一个字符串
                    events_text = "\n  ".join(event_list)
                    self.text.insert(tk.END, f"{month}.{day}:\n  {events_text}\n")
                
                # 锁定文本框
                self.text.config(state=tk.DISABLED)

            def analysis_excel(file_path):
                # 处理相对路径
                if not os.path.isabs(file_path):
                    file_path = os.path.join(self.dir_path, file_path)
                
                if not os.path.exists(file_path):
                    messagebox.showerror("错误", f"文件不存在: {file_path}")
                    return
                    
                import pandas as pd
                try:
                    df = pd.read_excel(file_path)
                    print("原始数据:", file_path)
                    print("列名:", df.columns.tolist())
                    print("数据行数:", len(df))
                    print("前5行数据:", df.head().to_string())
                    
                    # 只保留需要的列（time和things），避免其他列的NaN影响数据
                    required_columns = ['time', 'things']
                    # 检查所需列是否存在
                    existing_columns = [col for col in required_columns if col in df.columns]
                    df = df[existing_columns]
                    
                    # 添加详细的调试信息
                    print("\n=== 列数据详细信息 ===")
                    for col in df.columns:
                        print(f"列名: {col}")
                        print(f"数据类型: {df[col].dtype}")
                        print(f"非空值数量: {df[col].notna().sum()}")
                        print(f"空值数量: {df[col].isna().sum()}")
                        print(f"前10个值: {df[col].head(10).tolist()}")
                        # 检查是否包含空字符串
                        if df[col].dtype == 'object':
                            empty_str_count = (df[col] == '').sum()
                            print(f"空字符串数量: {empty_str_count}")
                            # 尝试将空字符串转换为NaN
                            df[col] = df[col].replace('', pd.NA)
                    
                    # 只删除time和things列都为空的行
                    print("\n=== 删除空行前 ===")
                    print(f"数据行数: {len(df)}")
                    df.dropna(subset=['time', 'things'], how='all', inplace=True)
                    print("=== 删除空行后 ===")
                    print(f"数据行数: {len(df)}")
                    
                    # 再次检查数据
                    print("\n=== 最终数据 ===")
                    print(f"前5行数据: {df.head().to_string()}")
                    
                    # 尝试获取time列，处理可能的列名差异
                    time_column = 'time'
                    things_column = 'things'
                    
                    # 检查列名是否存在
                    if time_column not in df.columns:
                        print(f"警告: 未找到'time'列，尝试查找其他可能的时间列名")
                        # 列出所有列名，让用户知道可用的列名
                        print(f"可用列名: {df.columns.tolist()}")
                        # 尝试寻找包含'time'或'日期'或'date'的列
                        for col in df.columns:
                            col_lower = col.lower()
                            if 'time' in col_lower or '日期' in col_lower or 'date' in col_lower:
                                time_column = col
                                print(f"自动选择时间列: {time_column}")
                                break
                                
                    if things_column not in df.columns:
                        print(f"警告: 未找到'things'列，尝试查找其他可能的事件列名")
                        # 尝试寻找包含'thing'或'事件'或'content'的列
                        for col in df.columns:
                            col_lower = col.lower()
                            if 'thing' in col_lower or '事件' in col_lower or 'content' in col_lower:
                                things_column = col
                                print(f"自动选择事件列: {things_column}")
                                break
                    
                    try:
                        # 获取time列和things列
                        # 强制转换为字符串类型，处理数值类型的日期
                        times = df[time_column].astype(str).tolist()
                        things = df[things_column].tolist()
                        print(f"使用列名: time={time_column}, things={things_column}")
                        print(f"times列表: {times}")
                        print(f"things列表: {things}")
                        print(f"times列表长度: {len(times)}")
                        print(f"things列表长度: {len(things)}")
                    except KeyError as e:
                        print(f"错误: 找不到指定的列 - {e}")
                        print("请确保Excel文件中包含'time'和'things'列")
                        times = []
                        things = []
                    
                    # 解析日期，支持多种格式（. / -）
                    month_data = []
                    day_data = []
                    
                    # 清空现有事件数据
                    self.events.clear()
                    
                    # 定义支持的日期分隔符
                    date_separators = ['.', '/', '-']
                    
                    print("\n=== 开始解析日期 ===")
                    for i, (time_str, thing) in enumerate(zip(times, things)):
                        print(f"\n第 {i+1} 条记录: time={time_str}, thing={thing}")
                        # 确保time_str是字符串类型
                        time_str = str(time_str).strip()
                        month = None
                        day = None
                        
                        # 跳过空的time_str
                        if not time_str or time_str == 'nan':
                            print(f"跳过空的time_str: {time_str}")
                            continue
                        
                        # 尝试不同的日期分隔符
                        for sep in date_separators:
                            if sep in time_str:
                                parts = time_str.split(sep)
                                if len(parts) >= 2:
                                    # 只取前两个部分（月和日）
                                    month = parts[0].strip()
                                    day = parts[1].strip()
                                    print(f"使用分隔符 '{sep}' 解析: 月={month}, 日={day}")
                                    break
                        
                        # 如果没有找到分隔符，尝试其他格式
                        if month is None and day is None:
                            # 尝试直接解析数字（如405表示4月5日）
                            if time_str.isdigit() and len(time_str) in [3, 4]:
                                if len(time_str) == 3:
                                    # 格式：MDD（如405表示4月5日）
                                    month = time_str[0]
                                    day = time_str[1:]
                                    print(f"直接解析3位数字: 月={month}, 日={day}")
                                elif len(time_str) == 4:
                                    # 格式：MMDD（如0405表示4月5日）
                                    month = time_str[:2]
                                    day = time_str[2:]
                                    print(f"直接解析4位数字: 月={month}, 日={day}")
                        
                        # 特殊处理: 如果day以'.'开头（例如：3..11）
                        if month is not None and day.startswith('.'):
                            day = day[1:]
                            print(f"处理特殊情况，移除day前的'.': {day}")
                        
                        # 如果成功解析出月和日
                        if month is not None and day is not None:
                            try:
                                # 转换为整数，确保是有效数字
                                int_month = int(month)
                                int_day = int(day)
                                
                                # 验证月份和日期的有效性
                                if 1 <= int_month <= 12 and 1 <= int_day <= 31:
                                    # 转换回字符串，保持两位数格式（可选）
                                    if len(str(int_month)) == 1:
                                        month = f"0{int_month}"
                                    else:
                                        month = str(int_month)
                                    if len(str(int_day)) == 1:
                                        day = f"0{int_day}"
                                    else:
                                        day = str(int_day)
                                    
                                    month_data.append(month)
                                    day_data.append(day)
                                    # 存储事件数据到self.events列表
                                    self.events.append({
                                        'month': month,
                                        'day': day,
                                        'things': thing
                                    })
                                    print(f"成功解析并添加事件: 月={month}, 日={day}, 事件={thing}")
                                else:
                                    print(f"警告: 无效的日期 {time_str} (月: {month}, 日: {day})")
                            except ValueError as e:
                                print(f"警告: 无法解析时间格式 {time_str} - {e}")
                        else:
                            print(f"警告: 无法解析时间格式 {time_str}，请使用 M.D、M/D、M-D 或 MMDD 格式")
                    
                    print(f"\n=== 解析结果 ===")
                    print(f"成功解析 {len(month_data)} 个事件")
                    print(f"月份列表: {month_data}")
                    print(f"日期列表: {day_data}")
                    print(f"事件列表: {[event['things'] for event in self.events]}")
                    
                    if len(month_data) != len(day_data):
                        messagebox.showwarning("警告", "月份和日期数量不匹配")
                        return
                    if len(things) != len(month_data):
                        messagebox.showwarning("警告", "事件数量不匹配")
                        return

                    print("原始时间:", times)
                    print("月份:", month_data)
                    print("日期:", day_data)
                    print("事件:", things)
                    print("解析后的事件数据:", self.events)
                    
                    # 调用刷新函数，重置为原始显示模式
                    refresh_text()
                    
                    # 重新显示日历，更新*标记
                    show_calendar()
                    
                    messagebox.showinfo("成功", "事件数据导入成功！")
                except Exception as e:
                    messagebox.showerror("错误", f"分析Excel文件失败: {e}")
                    print(f"分析Excel文件失败: {e}")
                    import traceback
                    traceback.print_exc()

            def select_file():
                from tkinter import filedialog
                import json
                # 设置默认路径为当前目录
                initial_dir = self.dir_path
                file_path = filedialog.askopenfilename(initialdir=initial_dir, filetypes=[("Excel files", "*.xlsx;*.xls")])
                if file_path:
                    # 使用绝对路径
                    absolute_path = os.path.abspath(file_path)
                    file_entry.delete(0, tk.END)
                    file_entry.insert(0, absolute_path)
                    # 添加absolute_path到user_data.json文件格式为
                    """
                    {"user_data": [{absolute_path}]}
                    
                    """
                    with open(os.path.join(self.dir_path, 'user_data.json'), 'w', encoding='utf-8') as f:
                        f.write(json.dumps({"user_data": [absolute_path]}, ensure_ascii=False, indent=4))
                else:
                    messagebox.showwarning("警告", "请选择一个Excel文件")

            def add_event(month_choice=None, day_choice=None, *args):
                def confirm_event_add(month, day, text):
                    if not month or not day or not text:
                        messagebox.showwarning("警告", "请输入月份、日期和事件内容")
                        return
                    # 检查合理性
                    if not month.isdigit() or not day.isdigit():
                        messagebox.showwarning("警告", "月份和日期必须是数字")
                        return
                    if not (1 <= int(month) <= 12 and 1 <= int(day) <= 31):
                        messagebox.showwarning("警告", "月份和日期必须是1-12和1-31之间的整数")
                        return
                    """self.events.append({
                        'month': month,
                        'day': day,
                        'things': text
                    })"""
                    # 将原来的事件替换为新的事件
                    self.events[month+day] = {
                        'things': text
                    }
                    messagebox.showinfo("成功", "事件添加成功！")
                    # 刷新文本显示
                    refresh_text()
                    # 重新显示日历，更新*标记
                    show_calendar()

                    add_root.destroy()


                add_root = tk.Toplevel()
                # 锁定窗口，防止用户调整大小
                add_root.resizable(False, False)
                add_root.title("新建事件")
                add_root.geometry("560x400")
                add_root.configure(bg="#f5f7fa")
                
                # 设置统一的间距
                padx = 5
                pady = 5
                
                # 创建主框架
                main_frame = ttk.Frame(add_root, padding=(20, 20, 20, 20))
                main_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
                
                # 设置标题
                title_label = ttk.Label(main_frame, text="创建一个事件，开始自律生活！", 
                                    style="Title.TLabel", foreground="#409eff")
                title_label.grid(row=0, column=0, columnspan=4, pady=(0, 20), sticky=tk.W)
                
                # 获取当前年份
                self.year = time.strftime("%Y", time.localtime())
                
                # 年份显示
                year_label = ttk.Label(main_frame, text=f"年份: {self.year}", 
                                    style="Modern.TLabel", foreground="#606266")
                year_label.grid(row=1, column=0, padx=padx, pady=pady, sticky=tk.E)
                
                # 月份输入
                month_label = ttk.Label(main_frame, text="月份:", style="Modern.TLabel")
                month_label.grid(row=1, column=1, padx=padx, pady=pady, sticky=tk.E)
                month_entry = ttk.Entry(main_frame, width=8, style="Modern.TEntry")
                month_entry.grid(row=1, column=2, padx=padx, pady=pady, sticky=tk.W)
                
                # 日期输入
                day_label = ttk.Label(main_frame, text="日期:", style="Modern.TLabel")
                day_label.grid(row=1, column=3, padx=padx, pady=pady, sticky=tk.E)
                day_entry = ttk.Entry(main_frame, width=8, style="Modern.TEntry")
                day_entry.grid(row=1, column=4, padx=padx, pady=pady, sticky=tk.W)
                
                # 事件内容输入框
                text = tk.Text(main_frame, width=45, height=6, 
                            font=("Microsoft YaHei", 10),
                            bg="#ffffff",
                            fg="#333333",
                            bd=1,
                            relief="solid",
                            highlightbackground="#dcdfe6",
                            highlightcolor="#409eff",
                            highlightthickness=1,
                            wrap=tk.WORD)
                text.grid(row=2, column=0, columnspan=4, padx=padx, pady=pady, sticky=(tk.N, tk.S, tk.E, tk.W))
                
                # 查看events的指定日期中是否有事件
                for event in self.events:
                    if event['month'] == month_choice and event['day'] == day_choice:
                        text.insert(tk.END, event['things'])
                        break

                # 确认按钮
                confirm_btn = ttk.Button(main_frame, text="确认", style="Modern.TButton",command=lambda: confirm_event_add(month_entry.get(), day_entry.get(), text.get("1.0", tk.END).strip()))
                confirm_btn.grid(row=3, column=2, columnspan=2, padx=padx, pady=(pady+10, 0), sticky=(tk.E, tk.W))
                
                # 配置行和列的权重，使布局更灵活
                main_frame.columnconfigure(2, weight=1)
                main_frame.columnconfigure(3, weight=1)
                main_frame.rowconfigure(2, weight=1)
                
                # 设置输入框默认值
                # 如果输入时间参数，设置默认值为参数时间，否则设置系统默认时间
                print(month_choice,day_choice)
                if month_choice is not None and day_choice is not None:
                    month_entry.insert(0, month_choice)
                    day_entry.insert(0, day_choice)
                else:
                    month_entry.insert(0, time.strftime("%m", time.localtime()))
                    day_entry.insert(0, time.strftime("%d", time.localtime()))
                
                
                
                # 绑定回车键确认
                add_root.bind("<Return>", lambda e: confirm_btn.invoke())
                
                # 设置初始焦点
                month_entry.focus()
                
                # 居中窗口
                add_root.update_idletasks()
                width = add_root.winfo_width()
                height = add_root.winfo_height()
                x = (add_root.winfo_screenwidth() // 2) - (width // 2)
                y = (add_root.winfo_screenheight() // 2) - (height // 2)
                add_root.geometry(f"{width}x{height}+{x}+{y}")

            def find_line(text):
                """打开搜索对话框"""
                current_search_pos = 0
                all_matches = []
                
                def search_text():
                    """执行搜索"""
                    nonlocal current_search_pos, all_matches
                    
                    search_query = search_entry.get()
                    if not search_query:
                        return
                    
                    text.config(state=tk.NORMAL)
                    text.tag_remove("highlight", "1.0", tk.END)
                    text.tag_remove(tk.SEL, "1.0", tk.END)
                    
                    all_matches = []
                    pos = "1.0"
                    while True:
                        pos = text.search(search_query, pos, tk.END)
                        if not pos:
                            break
                        end_pos = f"{pos}+{len(search_query)}c"
                        all_matches.append((pos, end_pos))
                        text.tag_add("highlight", pos, end_pos)
                        pos = end_pos
                    
                    text.tag_configure("highlight", background="yellow", foreground="black")
                    
                    if all_matches:
                        current_search_pos = 0
                        highlight_current_match()
                    else:
                        status_label.config(text="未找到匹配项", foreground="#f56c6c")
                    
                    text.config(state=tk.DISABLED)
                
                def highlight_current_match():
                    """高亮显示当前匹配项"""
                    if not all_matches:
                        return
                    
                    pos, end_pos = all_matches[current_search_pos]
                    text.config(state=tk.NORMAL)
                    text.tag_remove(tk.SEL, "1.0", tk.END)
                    text.tag_add(tk.SEL, pos, end_pos)
                    text.mark_set(tk.INSERT, end_pos)
                    text.see(pos)
                    text.config(state=tk.DISABLED)
                    status_label.config(text=f"找到 {len(all_matches)} 个匹配项中的第 {current_search_pos + 1} 个", foreground="#67c23a")
                
                def find_next():
                    """查找下一个"""
                    nonlocal current_search_pos
                    if not all_matches:
                        search_text()
                        return
                    current_search_pos = (current_search_pos + 1) % len(all_matches)
                    highlight_current_match()
                
                def find_prev():
                    """查找上一个"""
                    nonlocal current_search_pos
                    if not all_matches:
                        search_text()
                        return
                    current_search_pos = (current_search_pos - 1) % len(all_matches)
                    highlight_current_match()
                
                def close_search():
                    """关闭搜索对话框，清除高亮"""
                    text.config(state=tk.NORMAL)
                    text.tag_remove("highlight", "1.0", tk.END)
                    text.tag_remove(tk.SEL, "1.0", tk.END)
                    text.config(state=tk.DISABLED)
                    search_window.destroy()
                
                search_window = tk.Toplevel()
                search_window.title("查找")
                search_window.geometry("500x150")
                search_window.configure(bg="#f5f7fa")
                search_window.resizable(False, False)
                
                main_frame = ttk.Frame(search_window, padding=(15, 15, 15, 15))
                main_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
                
                padx = 5
                pady = 5
                
                ttk.Label(main_frame, text="查找:", style="Modern.TLabel").grid(row=0, column=0, padx=padx, pady=pady, sticky=tk.E)
                
                search_entry = ttk.Entry(main_frame, width=30, style="Modern.TEntry")
                search_entry.grid(row=0, column=1, columnspan=2, padx=padx, pady=pady, sticky=(tk.W, tk.E))
                
                next_btn = ttk.Button(main_frame, text="查找下一个", style="Modern.TButton", command=find_next)
                next_btn.grid(row=1, column=0, padx=padx, pady=pady, sticky=tk.E)
                
                prev_btn = ttk.Button(main_frame, text="查找上一个", style="Modern.TButton", command=find_prev)
                prev_btn.grid(row=1, column=1, padx=padx, pady=pady, sticky=tk.E)
                
                close_btn = ttk.Button(main_frame, text="关闭", style="Modern.TButton", command=close_search)
                close_btn.grid(row=1, column=2, padx=padx, pady=pady, sticky=tk.E)
                
                status_label = ttk.Label(main_frame, text="", style="Modern.TLabel")
                status_label.grid(row=2, column=0, columnspan=3, padx=padx, pady=pady, sticky=tk.W)
                
                main_frame.columnconfigure(1, weight=1)
                
                def on_entry_change(*args):
                    """输入框内容改变时自动搜索"""
                    search_text()
                
                search_var = tk.StringVar()
                search_entry.config(textvariable=search_var)
                search_var.trace("w", on_entry_change)
                
                search_entry.bind("<Return>", lambda e: find_next())
                search_window.bind("<Escape>", lambda e: close_search())
                search_window.bind("<Return>", lambda e: find_next())
                
                search_entry.focus_set()

            # 定义退出检查函数
            def check_exit(check_file_path):
                
                # 获取文件数据
                import pandas as pd
                try:
                    df = pd.read_excel(check_file_path)
                except Exception as e:
                    messagebox.showerror("错误", f"读取文件失败: {e}")
                    return
                # 对比数据是否有差异
                
                self.events_compare = df.to_dict(orient='records')
                export_data = []
                for event in self.events:
                    export_data.append({
                        'time': float(f"{int(event['month'])}.{int(event['day'])}"),  # 例如: '4.2'
                        'things': event['things']
                    })
                try:
                    df = pd.DataFrame(export_data)
                    df.to_excel(check_file_path, index=False)
                    if not (self.events_compare == export_data):
                        if messagebox.askquestion("警告", f"文件数据与当前数据不一致，建议保存当前数据\n{self.events_compare}\n----------------------------------------------\n{export_data}\n是否继续退出？") == 'yes':
                            cal_window.destroy()
                    else:
                        cal_window.destroy()
                except Exception as e:
                    messagebox.showerror("错误", f"最常见的原因是文件在 Excel 中被打开。请先检查并关闭所有打开的 Excel 文件，然后重试。")
                
            def save_file():  # 改为接受 df 参数
                import pandas as pd
                from tkinter import filedialog
                save_file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("文本文件", "*.xlsx")])
                print("文件类型",self.events)
                
                if save_file_path:
                    try:
                        print("保存文件路径:", save_file_path)
                        # 将self.events转化成excel文件# 将self.events转化成excel文件
                        # 转换数据格式：将 month 和 day 合并为 time，并去掉前导零
                        export_data = []
                        for event in self.events:
                            export_data.append({
                                'time': f"{int(event['month'])}.{int(event['day'])}",  # 例如: '4.2'
                                'things': event['things']
                            })

                        df = pd.DataFrame(export_data)
                        df.to_excel(save_file_path, index=False)
                        print("保存成功！")
                    except Exception as e:
                        print(f"保存失败: {e}")

            def set_calendar():
                """设置日程管理器"""

                def update_e(type_name):
                    print(self.ai_enable)
                    """更新AI解析启用"""
                    if type_name == "ai":
                        if not self.bool_get_ai_answer.get():
                            if messagebox.askquestion("确认", "确定关闭AI解析吗？\n关闭后将无法使用AI回答功能") == 'yes':
                                self.ai_enable = False
                                self.bool_get_ai_answer.set(False)
                                messagebox.showinfo("提示", "AI解析已关闭")
                            else:
                                self.ai_enable = True
                                self.bool_get_ai_answer.set(True)
                        else:
                            self.ai_enable = True
                            self.bool_get_ai_answer.set(True)
                            messagebox.showinfo("提示", "AI解析已开启")
                    elif type_name == "event":
                        self.event_length = self.event_length_slider.get()
                        # 修改最大高度而不是固定高度，保持间距不变
                        # 使用Qt方法设置最大高度，保持间距不变
                        self.content_label.setMaximumHeight(self.event_length)
                    elif type_name == "exit":
                        # 保存设置
                        with open(self.dir_path+'/user_data.json', 'w', encoding='utf-8') as f:
                            self.user['ai_enable'] = self.ai_enable
                            self.user['event_length'] = self.event_length
                            json.dump(self.user, f, ensure_ascii=False, indent=4)
                        set_window.destroy()
                    
                    else:
                        messagebox.showerror("错误", "未知的设置类型")
                
                # 打开设置对话框，且只能打开一个窗口
                set_window = tk.Toplevel()
                set_window.title("设置")
                set_window.geometry("300x400+900+900")
                set_window.configure(bg="#f5f7fa")
                set_window.resizable(False, False)



                # 绑定退出
                set_window.protocol("WM_DELETE_WINDOW", lambda: update_e("exit"))

                self.bool_get_ai_answer = tk.BooleanVar(value=True)
                self.ai_enable = True

                ttk.Label(set_window, text="设置日程管理器", style="Title.TLabel", foreground="#409eff").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
                
                # 是否启用AI解析（滑块组件）
                self.ai_checkbutton = ttk.Checkbutton(set_window, text="启用AI解析", variable=self.bool_get_ai_answer, command=lambda: update_e("ai"))
                self.ai_checkbutton.grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
                # 调节事件框长度（100-700）

                ttk.Label(set_window, text="事件框长度", style="Title.TLabel").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
                self.event_length = tk.IntVar(value=100)
                self.event_length_slider = ttk.Scale(set_window, from_=100, to=700, orient=tk.HORIZONTAL, length=200, variable=self.event_length,command=lambda e: update_e("event"))
                self.event_length_slider.grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
                self.event_length_slider.set(200)
                
                # 读取用户设置
                self.user = {'ai_enable': True, 'event_length': 200}
                user_data_file = os.path.join(self.dir_path, 'user_data.json')
                if os.path.exists(user_data_file):
                    try:
                        with open(user_data_file, 'r', encoding='utf-8') as f:
                            self.user = json.load(f)
                            if 'ai_enable' in self.user and 'event_length' in self.user:
                                self.ai_enable = self.user['ai_enable']
                                self.event_length = self.user['event_length']
                                self.event_length_slider.set(self.event_length)
                    except Exception as e:
                        print(f"读取user_data.json失败: {e}")

                set_window.mainloop()

            def open_excel_file(file_path):
                import webbrowser
                webbrowser.open(file_path)
            
            def new_excel_file():
                from tkinter import filedialog
                file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("文本文件", "*.xlsx")])
                if file_path:
                    from openpyxl import Workbook
                    from openpyxl.utils.cell import get_column_letter
                    # 1. 准备数据
                    template_event = ["time", "things"]

                    # 2. 创建工作簿和工作表
                    wb = Workbook()
                    ws = wb.active  # 使用默认工作表（也可以用 wb.create_sheet("Sheet1") 新建）

                    # 3. 分别写入 A1 和 B1
                    ws["A1"] = template_event[0]  # A1 单元格写入 "time"
                    ws["B1"] = template_event[1]  # B1 单元格写入 "things"

                    # 4. 保存文件
                    wb.save(file_path)
                    messagebox.showinfo("提示", "新建文件成功")
                        
            # 创建主窗口
            cal_window = tk.Tk()
            cal_window.title("日历")
            cal_window.geometry("1080x720")
            cal_window.configure(bg="#f5f7fa")
            # 不尝试加载图标文件，避免程序崩溃

            # 尝试从user_data.json读取文件路径
            user_file_paths = []
            user_data_file = os.path.join(self.dir_path, 'user_data.json')
            if os.path.exists(user_data_file):
                try:
                    with open(user_data_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)  
                        if 'user_data' in data:
                            user_file_paths = data['user_data']
                except json.JSONDecodeError:
                    user_file_paths = []
                    messagebox.showerror("错误", "用户数据文件格式错误，请检查文件内容")
                except Exception as e:
                    print(f"读取user_data.json失败: {e}")
                    user_file_paths = []
    
            try:
                # 设置ttk样式
                style = ttk.Style()
                
                # 设置主题
                style.theme_use("clam")
                
                # 配置颜色方案
                style.configure(".", 
                            background="#f5f7fa",
                            foreground="#333333",
                            font=("Microsoft YaHei", 10))
                
                # 配置标题样式
                style.configure("Title.TLabel", 
                            font=("Microsoft YaHei", 14, "bold"),
                            foreground="#409eff",
                            padding=10)
                
                # 配置按钮样式
                style.configure("Modern.TButton",
                            font=("Microsoft YaHei", 10),
                            padding=8,
                            background="#409eff",
                            foreground="#ffffff")
                style.map("Modern.TButton",
                        background=[("active", "#66b1ff"), ("disabled", "#dcdfe6")],
                        foreground=[("disabled", "#a0a0a0")])
                
                # 配置日历按钮样式
                style.configure("Calendar.TButton",
                            font=("Microsoft YaHei", 11),
                            padding=5,
                            width=4,
                            background="#ffffff",
                            foreground="#333333")
                style.map("Calendar.TButton",
                        background=[("active", "#ecf5ff"), ("disabled", "#f5f7fa")])
                
                # 配置输入框样式
                style.configure("Modern.TEntry",
                            font=("Microsoft YaHei", 10),
                            padding=8,
                            background="#ffffff",
                            foreground="#333333",
                            borderwidth=1,
                            relief="solid")
                # 设置下拉框样式
                style.configure("Modern.TCombobox",
                            font=("Microsoft YaHei", 10),
                            padding=8,
                            background="#ffffff",
                            foreground="#333333",
                            borderwidth=1,
                            relief="solid")
            
            except Exception as e:
                messagebox.showerror("错误", f"样式设置错误: {e}")
            
            # 设置年份和月份选择
            control_frame = ttk.Frame(cal_window, padding="15")
            control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # 设置标题
            title_label = ttk.Label(control_frame, text="事件日历管理", style="Title.TLabel")
            title_label.grid(row=0, column=0, columnspan=6, pady=(0, 15))

            # 增加设置按钮
            set_btn = ttk.Button(control_frame, text="设置", style="Modern.TButton", command=set_calendar)
            set_btn.grid(row=0, column=5, padx=5, pady=10, sticky=tk.E)

            ttk.Label(control_frame, text="年份:").grid(row=1, column=0, padx=5, pady=10, sticky=tk.E)
            year_var = tk.StringVar(value=str(self.time_year))
            year_entry = ttk.Entry(control_frame, textvariable=year_var, width=8, style="Modern.TEntry")
            year_entry.grid(row=1, column=1, padx=5, pady=10, sticky=tk.W)
            year_entry.configure(state="readonly")
            
            ttk.Label(control_frame, text="月份:").grid(row=1, column=2, padx=5, pady=10, sticky=tk.E)
            month_var = tk.StringVar(value=str(self.time_month))
            month_var.trace("w", show_calendar)
            month_entry_values = [str(i) for i in range(1, 13)]
            month_entry_values[month_entry_values.index(str(self.time_month))] = f"{self.time_month}*"
            month_entry = ttk.Combobox(control_frame, textvariable=month_var, values=month_entry_values, width=8, style="Modern.TCombobox")
            month_entry.grid(row=1, column=3, padx=5, pady=10, sticky=tk.W)
            month_entry.configure(state="readonly")

            
            # 合并显示日历和刷新功能
            def show_calendar_and_refresh():
                show_calendar()
                refresh_text()
            
            # 尝试从user_data.json读取文件路径
            user_file_paths = []
            user_data_file = os.path.join(self.dir_path, 'user_data.json')
            if os.path.exists(user_data_file):
                try:
                    import json
                    with open(user_data_file, 'r', encoding='utf-8') as f:
                        user_data = json.load(f)
                        if 'user_data' in user_data and isinstance(user_data['user_data'], list):
                            user_file_paths = user_data['user_data']
                except Exception as e:
                    print(f"读取user_data.json失败: {e}")
            
            # 读取xlsx数据
            ttk.Label(control_frame, text="Excel文件:").grid(row=2, column=0, padx=5, pady=10, sticky=tk.E)
            file_entry = ttk.Entry(control_frame, width=40, style="Modern.TEntry")
            file_entry.grid(row=2, column=1, columnspan=2, padx=5, pady=10)
            file_entry.delete(0, tk.END)
            # 只有当user_file_paths不为空时，才尝试插入第一个文件路径
            if user_file_paths:
                # 确保使用绝对路径
                file_path = user_file_paths[0]
                if not os.path.isabs(file_path):
                    file_path = os.path.abspath(os.path.join(self.dir_path, file_path))
                # 检查文件是否存在
                if os.path.exists(file_path):
                    file_entry.insert(0, file_path)
                else:
                    # 如果文件不存在，清空路径
                    file_entry.delete(0, tk.END)
            # 默认解析文件
            
            ttk.Button(control_frame, text="选择文件", command=select_file, style="Modern.TButton").grid(row=2, column=3, padx=5, pady=10)
            # 合并为一个按钮为文件按钮，并用菜单触发分析数据、刷新、新建事件
            menu = tk.Menu(control_frame, tearoff=False)
            menu.add_command(label="分析数据", command=lambda: analysis_excel(file_entry.get()))
            menu.add_command(label="刷新", command=lambda: show_calendar_and_refresh())
            menu.add_command(label='另存为xlsx', command=lambda: save_file())
            menu.add_command(label="新建事件", command=lambda: add_event(None,None))
            menu.add_separator()
            menu.add_command(label='打开xlsx文件', command=lambda: open_excel_file(file_entry.get()))
            menu.add_command(label='新建xlsx文件', command=new_excel_file)
        
            add_btn = ttk.Button(control_frame, text="文件", style="Modern.TButton")
            add_btn.grid(row=2, column=4, padx=5, pady=10)
            
            # 当鼠标移到按钮上时显示菜单
            def show_menu(event):
                # 计算菜单显示位置，在按钮下方
                x = add_btn.winfo_rootx()
                y = add_btn.winfo_rooty() + add_btn.winfo_height()
                menu.post(x, y)
            
            # 绑定鼠标悬停事件
            add_btn.bind("<Enter>", show_menu)

            # 创建日历框架设置宽样式
            calendar_frame = ttk.Frame(cal_window, padding="15", relief="solid", borderwidth=1, width=10, height=500)
            calendar_frame.grid(row=1, column=0, padx=15, pady=15, sticky=(tk.N, tk.S, tk.W, tk.E))
            
            ## 增加长文本 标签，并放置在右侧
            text_frame = ttk.Frame(cal_window, padding="8", relief="solid", borderwidth=1,height=500)
            text_frame.grid(row=1, column=1, padx=15, pady=15, sticky=(tk.N, tk.S, tk.W, tk.E))
            
            # 文本框标题
            text_title = ttk.Button(text_frame, text="事件详情", style="Title.TLabel",command=lambda: find_line(self.text))
            text_title.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
            
            # 锁定文本框，防止用户直接编辑
            self.text = tk.Text(text_frame, 
                            width=40, 
                            height=25, 
                            state=tk.DISABLED,
                            font=("Microsoft YaHei", 10),
                            bg="#f5f7fa",
                            fg="#333333",
                            bd=0,
                            relief="flat",
                            padx=8,
                            pady=8,
                            wrap=tk.WORD,
                            highlightthickness=0)
            self.text.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))
            if user_file_paths:
                analysis_excel(file_entry.get())

            # 配置文本框滚动条
            scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text.yview)
            scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
            self.text.configure(yscrollcommand=scrollbar.set)
            
            # 配置文本框标签样式
            self.text.tag_configure("header", font=("Microsoft YaHei", 12, "bold"), foreground="#409eff", spacing1=10, spacing3=5)
            self.text.tag_configure("event", font=("Microsoft YaHei", 11), foreground="#606266", spacing3=5)
            self.text.tag_configure("ai_answer", font=("Microsoft YaHei", 10, "italic"), foreground="#67c23a", spacing1=10, spacing3=5)
            
            # 添加Ctrl+F快捷键打开搜索对话框
            def on_ctrl_f(event):
                find_line(self.text)
                return "break"
            
            self.text.bind("<Control-f>", on_ctrl_f)
            self.text.bind("<Control-F>", on_ctrl_f)
            cal_window.bind("<Control-f>", on_ctrl_f)
            cal_window.bind("<Control-F>", on_ctrl_f)
            
            # 配置行和列的权重
            text_frame.rowconfigure(1, weight=1)
            text_frame.columnconfigure(0, weight=1)
            cal_window.rowconfigure(1, weight=1)
            cal_window.columnconfigure(0, weight=1)
            cal_window.columnconfigure(1, weight=1)
            
            # 初始显示当前月份的日历
            show_calendar()

            cal_window.protocol("WM_DELETE_WINDOW", lambda: check_exit(file_entry.get()))

            cal_window.mainloop()    
        

