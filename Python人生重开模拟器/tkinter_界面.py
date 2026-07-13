import tkinter as tk
from tkinter import messagebox
import random
import os
import json
import re

# ==================== 颜色配置 ====================
BG_COLOR = "#1a1a2e"       # 深蓝黑背景
CARD_COLOR = "#16213e"     # 卡片背景
ACCENT_COLOR = "#0f3460"   # 强调色
TEXT_COLOR = "#e0e0e0"     # 主文字色
LABEL_COLOR = "#a8d8ea"    # 标签色
BTN_BG = "#e94560"         # 按钮背景
BTN_FG = "#ffffff"         # 按钮文字
ENTRY_BG = "#0f3460"       # 输入框背景
ARROW_BG = "#533483"       # 箭头按钮背景
TEXT_BG = "#0d1b2a"        # Text组件背景
SCROLL_BG = "#1b2838"      # 滚动条背景

# ==================== 游戏数据加载 ====================
events_dict = {}
age_events = {}
event_file = os.path.abspath("events.json")
age_event_file = os.path.abspath("age.json")

def get_all_events():
    if os.path.isfile(event_file):
        with open(event_file, "r", encoding="utf-8") as f:
            temp = json.load(f)
            for k in temp.keys():
                events_dict[int(k)] = temp[k]
        return events_dict
    else:
        messagebox.showinfo("提示", "事件文件不存在")
        exit()

def get_age_events():
    if os.path.isfile(age_event_file):
        with open(age_event_file, "r", encoding="utf-8") as f:
            temp = json.load(f)
            for k in temp.keys():
                event_list = temp[k]['event']
                filtered = []
                for item in event_list:
                    item_str = str(item)
                    eid = int(item_str.split('*')[0])
                    if eid in events:
                        filtered.append(item)
                age_events[int(k)] = filtered
        return age_events
    else:
        messagebox.showinfo("提示", "年龄事件文件不存在")
        exit()

def weight_choice(age_list):
    weight_event = {}
    for item in age_list:
        if '*' in str(item):
            _list = str(item).split('*')
            weight_event[int(_list[0])] = float(_list[1])
        else:
            weight_event[int(item)] = 1
    rnd = random.random() * sum(weight_event.values())
    cumulative = 0
    for key, value in weight_event.items():
        cumulative += value
        if rnd <= cumulative:
            return key

def check_condition(condition, stats, past_events):
    if not condition:
        return True
    condition = condition.strip()
    while '(' in condition:
        start = condition.rfind('(')
        end = condition.find(')', start)
        if start == -1 or end == -1:
            break
        inner = condition[start+1:end]
        result = check_condition(inner, stats, past_events)
        condition = condition[:start] + str(result) + condition[end+1:]
    if '|' in condition:
        parts = condition.split('|')
        return any(check_condition(p.strip(), stats, past_events) for p in parts)
    if '&' in condition:
        parts = condition.split('&')
        return all(check_condition(p.strip(), stats, past_events) for p in parts)
    if 'EVT?' in condition:
        match = re.search(r'EVT?\[([^\]]+)\]', condition)
        if match:
            event_ids = [int(x.strip()) for x in match.group(1).split(',')]
            return any(eid in past_events for eid in event_ids)
        return False
    if 'TLT?' in condition:
        return False
    match = re.match(r'(CHR|STR|INT|MNY|SPR|LIF)(>=|<=|>|<|==|!=)(\d+)', condition)
    if match:
        stat = match.group(1)
        op = match.group(2)
        value = int(match.group(3))
        current_value = stats.get(stat, 0)
        if op == '>': return current_value > value
        elif op == '<': return current_value < value
        elif op == '>=': return current_value >= value
        elif op == '<=': return current_value <= value
        elif op == '==': return current_value == value
        elif op == '!=': return current_value != value
    if condition == 'True': return True
    if condition == 'False': return False
    return False

def filter_events_by_conditions(age_list, stats, past_events):
    valid_events = []
    for item in age_list:
        event_id = int(str(item).split('*')[0])
        event_data = events.get(event_id)
        if not event_data:
            continue
        include_cond = event_data.get('include')
        if include_cond and not check_condition(include_cond, stats, past_events):
            continue
        exclude_cond = event_data.get('exclude')
        if exclude_cond and check_condition(exclude_cond, stats, past_events):
            continue
        valid_events.append(item)
    return valid_events

def apply_effect(effect, stats):
    if not effect:
        return
    for stat, change in effect.items():
        if stat in stats:
            stats[stat] += change

def process_branch(branch, stats, past_events):
    if not branch:
        return None
    for cond in branch:
        parts = cond.split(':')
        if len(parts) == 2:
            condition, event_id = parts
            if check_condition(condition, stats, past_events):
                return int(event_id)
    return None

# 加载游戏数据
events = get_all_events()
age_event_list = get_age_events()

# ==================== 游戏状态 ====================
current_stats = {}
past = {}
age = 0
game_over = False
auto_running = False
auto_timer_id = None

# ==================== UI 组件 ====================
all_widgets = []
text_widget = None  # 全局引用，用于逐行追加文本

def validate_input(value):
    if value == "":
        return True
    try:
        num = int(value)
        return 0 <= num <= 10
    except ValueError:
        return False

def increment(entry):
    try:
        current = int(entry.get())
        if current < 10:
            entry.delete(0, tk.END)
            entry.insert(0, str(current + 1))
    except ValueError:
        entry.delete(0, tk.END)
        entry.insert(0, "0")

def decrement(entry):
    try:
        current = int(entry.get())
        if current > 0:
            entry.delete(0, tk.END)
            entry.insert(0, str(current - 1))
    except ValueError:
        entry.delete(0, tk.END)
        entry.insert(0, "0")

def create_input_row(parent, label_text, default_value=5):
    frame = tk.Frame(parent, bg=BG_COLOR)
    frame.pack(pady=8, padx=30, fill=tk.X)
    all_widgets.append(frame)

    label = tk.Label(frame, text=label_text, width=12, anchor='w',
                     font=("微软雅黑", 12), fg=LABEL_COLOR, bg=BG_COLOR)
    label.pack(side=tk.LEFT, padx=5)

    vcmd = (root.register(validate_input), '%P')
    entry = tk.Entry(frame, width=5, validate='key', validatecommand=vcmd,
                     justify='center', font=("微软雅黑", 12, "bold"),
                     bg=ENTRY_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR,
                     relief=tk.FLAT, bd=2)
    entry.insert(0, str(default_value))
    entry.pack(side=tk.LEFT, padx=5)

    # 右侧箭头按钮容器（上下垂直排列）
    arrow_frame = tk.Frame(frame, bg=BG_COLOR)
    arrow_frame.pack(side=tk.LEFT, padx=5)

    up_btn = tk.Button(arrow_frame, text="▲", width=3, font=("微软雅黑", 9),
                       fg=BTN_FG, bg=ARROW_BG, activebackground="#7c5cbf",
                       bd=0, cursor="hand2", command=lambda: increment(entry))
    up_btn.pack()

    down_btn = tk.Button(arrow_frame, text="▼", width=3, font=("微软雅黑", 9),
                         fg=BTN_FG, bg=ARROW_BG, activebackground="#7c5cbf",
                         bd=0, cursor="hand2", command=lambda: decrement(entry))
    down_btn.pack()

    return entry

def submit():
    """提交属性，进入游戏页面"""
    global age, past, game_over, text_widget, auto_running, auto_timer_id
    auto_running = False
    auto_timer_id = None

    # 收集输入值
    values = []
    for entry in entries:
        try:
            val = int(entry.get())
        except ValueError:
            val = 0
        values.append(val)

    total = sum(values)
    if total != 20:
        messagebox.showwarning("提示", f"属性总和必须为20，当前总和为{total}，请重新分配！")
        return

    # 初始化游戏状态
    current_stats['CHR'] = values[1]
    current_stats['STR'] = values[0]
    current_stats['INT'] = values[2]
    current_stats['MNY'] = values[3]
    current_stats['SPR'] = 5
    current_stats['LIF'] = 100
    past = {}
    age = 0
    game_over = False

    # 禁用验证后清空组件
    for entry in entries:
        try:
            entry.config(validate='none')
        except tk.TclError:
            pass
    for widget in all_widgets:
        try:
            widget.destroy()
        except tk.TclError:
            pass
    all_widgets.clear()

    # 创建 Text 组件（可滚动，锁定不可编辑）
    text_frame = tk.Frame(root, bg=BG_COLOR)
    text_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
    all_widgets.append(text_frame)

    scrollbar = tk.Scrollbar(text_frame, bg=SCROLL_BG, troughcolor=BG_COLOR)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    text_widget = tk.Text(text_frame, width=50, height=25, wrap=tk.WORD,
                          yscrollcommand=scrollbar.set, font=("微软雅黑", 11),
                          bg=TEXT_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR,
                          relief=tk.FLAT, bd=2, padx=10, pady=10,
                          state=tk.DISABLED)
    text_widget.pack(fill=tk.BOTH, expand=True)
    scrollbar.config(command=text_widget.yview)

    # 显示初始属性（需要临时解锁）
    text_widget.config(state=tk.NORMAL)
    text_widget.insert(tk.END, "══════════════════════════\n")
    text_widget.insert(tk.END, "  《人生重开模拟器》\n")
    text_widget.insert(tk.END, "══════════════════════════\n\n")
    text_widget.insert(tk.END, f"体质(STR): {values[0]}\n")
    text_widget.insert(tk.END, f"颜值(CHR): {values[1]}\n")
    text_widget.insert(tk.END, f"智力(INT): {values[2]}\n")
    text_widget.insert(tk.END, f"家境(MNY): {values[3]}\n\n")
    text_widget.insert(tk.END, "──────────────────────────\n\n")
    text_widget.config(state=tk.DISABLED)

    # 按钮容器（水平排列）
    btn_frame = tk.Frame(root, bg=BG_COLOR)
    btn_frame.pack(pady=10)
    all_widgets.append(btn_frame)

    next_btn = tk.Button(btn_frame, text="下一个", width=10, font=("微软雅黑", 12, "bold"),
                         fg=BTN_FG, bg=BTN_BG, activebackground="#ff6b81",
                         bd=0, padx=15, pady=8, cursor="hand2",
                         command=next_action)
    next_btn.pack(side=tk.LEFT, padx=5)
    all_widgets.append(next_btn)

    auto_btn = tk.Button(btn_frame, text="自动播放", width=10, font=("微软雅黑", 12, "bold"),
                         fg=BTN_FG, bg=ARROW_BG, activebackground="#7c5cbf",
                         bd=0, padx=15, pady=8, cursor="hand2",
                         command=toggle_auto)
    auto_btn.pack(side=tk.LEFT, padx=5)
    all_widgets.append(auto_btn)

def toggle_auto():
    """切换自动播放状态"""
    global auto_running, auto_timer_id
    if auto_running:
        # 停止自动播放
        auto_running = False
        if auto_timer_id:
            root.after_cancel(auto_timer_id)
            auto_timer_id = None
        # 恢复按钮文字
        for widget in all_widgets:
            try:
                if isinstance(widget, tk.Button) and widget.cget("text") == "停止":
                    widget.config(text="自动播放", bg=ARROW_BG)
            except tk.TclError:
                pass
    else:
        if game_over:
            return
        auto_running = True
        # 更改按钮文字
        for widget in all_widgets:
            try:
                if isinstance(widget, tk.Button) and widget.cget("text") == "自动播放":
                    widget.config(text="停止", bg=BTN_BG)
            except tk.TclError:
                pass
        auto_next()

def auto_next():
    """自动推进一岁，1秒后再次调用"""
    global auto_running, auto_timer_id
    if not auto_running or game_over:
        auto_running = False
        return
    next_action()
    if auto_running and not game_over:
        auto_timer_id = root.after(1000, auto_next)

def next_action():
    """点击"下一个"推进一岁"""
    global age, game_over

    if game_over:
        return

    # 临时解锁 Text 组件以写入内容
    text_widget.config(state=tk.NORMAL)

    # 推进到下一岁
    while age < 100 and current_stats['LIF'] > 0:
        age_list = age_event_list.get(age, [])

        valid_events = filter_events_by_conditions(age_list, current_stats, past)

        if not valid_events:
            age += 1
            continue

        remaining = [item for item in valid_events if int(str(item).split('*')[0]) not in past]

        if not remaining:
            past.clear()
            remaining = valid_events

        event_id = weight_choice(remaining)

        if event_id is None or event_id not in events:
            age += 1
            continue

        past[event_id] = age
        event_data = events[event_id]

        text_widget.insert(tk.END, f"{age}岁：{event_data['event']}\n")

        branch = event_data.get('branch')
        if branch:
            branch_event_id = process_branch(branch, current_stats, past)
            if branch_event_id and branch_event_id in events:
                branch_event = events[branch_event_id]
                text_widget.insert(tk.END, f"  → {branch_event['event']}\n")
                past[branch_event_id] = age
                apply_effect(branch_event.get('effect'), current_stats)

        apply_effect(event_data.get('effect'), current_stats)

        age += 1
        break

    # 检查游戏是否结束
    if age >= 100 or current_stats['LIF'] <= 0:
        game_over = True
        auto_running = False
        if auto_timer_id:
            root.after_cancel(auto_timer_id)
            auto_timer_id = None
        if current_stats['LIF'] <= 0:
            text_widget.insert(tk.END, f"\n你在{age}岁时去世了。\n")
        else:
            text_widget.insert(tk.END, f"\n你活到了100岁！\n")
        text_widget.insert(tk.END, "\n══════════════════════════\n")
        text_widget.insert(tk.END, "最终属性：\n")
        for stat, val in current_stats.items():
            text_widget.insert(tk.END, f"  {stat}: {val}\n")
        text_widget.insert(tk.END, "══════════════════════════\n")

        # 锁定 Text 组件
        text_widget.config(state=tk.DISABLED)
        text_widget.see(tk.END)

        # 将按钮改为"重新开始"
        for widget in all_widgets:
            try:
                widget.destroy()
            except tk.TclError:
                pass
        all_widgets.clear()

        restart_btn = tk.Button(root, text="重新开始", width=12, font=("微软雅黑", 12, "bold"),
                                fg=BTN_FG, bg=BTN_BG, activebackground="#ff6b81",
                                bd=0, padx=20, pady=8, cursor="hand2",
                                command=restart_game)
        restart_btn.pack(pady=15)
        all_widgets.append(restart_btn)
        return

    # 锁定 Text 组件
    text_widget.config(state=tk.DISABLED)
    text_widget.see(tk.END)

def restart_game():
    """重新开始游戏"""
    global age, past, game_over, text_widget

    for widget in all_widgets:
        try:
            widget.destroy()
        except tk.TclError:
            pass
    all_widgets.clear()

    title_label = tk.Label(root, text="人生重开模拟器", font=("微软雅黑", 22, "bold"),
                           fg=BTN_BG, bg=BG_COLOR)
    title_label.pack(pady=30)
    all_widgets.append(title_label)

    subtitle = tk.Label(root, text="请分配你的初始属性（总和=20）",
                        font=("微软雅黑", 11), fg=LABEL_COLOR, bg=BG_COLOR)
    subtitle.pack(pady=5)
    all_widgets.append(subtitle)

    entries.clear()
    entries.append(create_input_row(root, "体质(STR)", 5))
    entries.append(create_input_row(root, "颜值(CHR)", 5))
    entries.append(create_input_row(root, "智力(INT)", 5))
    entries.append(create_input_row(root, "家境(MNY)", 5))

    submit_btn = tk.Button(root, text="提  交", width=12, font=("微软雅黑", 12, "bold"),
                           fg=BTN_FG, bg=BTN_BG, activebackground="#ff6b81",
                           bd=0, padx=20, pady=8, cursor="hand2",
                           command=submit)
    submit_btn.pack(pady=30)
    all_widgets.append(submit_btn)

# ==================== 主窗口 ====================
root = tk.Tk()
root.title("生命模拟器")
root.geometry("520x650")
root.configure(bg=BG_COLOR)

title_label = tk.Label(root, text="人生重开模拟器", font=("微软雅黑", 22, "bold"),
                       fg=BTN_BG, bg=BG_COLOR)
title_label.pack(pady=30)
all_widgets.append(title_label)

subtitle = tk.Label(root, text="请分配你的初始属性（总和=20）",
                    font=("微软雅黑", 11), fg=LABEL_COLOR, bg=BG_COLOR)
subtitle.pack(pady=5)
all_widgets.append(subtitle)

entries = []
entries.append(create_input_row(root, "体质(STR)", 5))
entries.append(create_input_row(root, "颜值(CHR)", 5))
entries.append(create_input_row(root, "智力(INT)", 5))
entries.append(create_input_row(root, "家境(MNY)", 5))

submit_btn = tk.Button(root, text="提  交", width=12, font=("微软雅黑", 12, "bold"),
                       fg=BTN_FG, bg=BTN_BG, activebackground="#ff6b81",
                       bd=0, padx=20, pady=8, cursor="hand2",
                       command=submit)
submit_btn.pack(pady=30)
all_widgets.append(submit_btn)

root.mainloop()
