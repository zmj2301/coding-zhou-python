# -*- coding: utf-8 -*-
"""日历主窗口样式预览 —— 独立运行。

python calendar_preview.py
"""
import calendar
import tkinter as tk
from tkinter import ttk, messagebox

# ── 设计令牌（和设置窗口同色，整个应用视觉统一）───────────────
C = {
    'window_bg':   '#eef1f6',   # 窗口底色（浅灰蓝）
    'card_bg':     '#ffffff',   # 卡片白
    'card_border': '#e3e7ef',   # 细边框
    'title':       '#1f2937',   # 深灰黑
    'accent':      '#4f6ef7',   # 主色蓝紫（统一替换旧 #409eff）
    'accent_soft': '#eef0ff',   # 主色淡
    'text':        '#374151',   # 正文深灰
    'text_dim':    '#8a94a6',   # 次要文字
    'today_bg':    '#4f6ef7',   # 今天的日期格子
    'today_fg':    '#ffffff',
    'has_event_bg': '#fef3c7',  # 有事件的日期格子（淡黄）
    'has_event_fg': '#92400e',
    'weekday_bg':   '#f8fafc',  # 星期表头
    'weekday_fg':   '#8a94a6',
}

F = {
    'window_title': ('Microsoft YaHei', 13, 'bold'),
    'card_title':   ('Microsoft YaHei', 11, 'bold'),
    'label':        ('Microsoft YaHei', 9),
    'btn':          ('Microsoft YaHei', 9, 'bold'),
    'date_num':     ('Microsoft YaHei', 11, 'bold'),
    'event':        ('Microsoft YaHei', 10),
}

# 紧凑令牌
S = {
    'card_pad':    (12, 10),   # 卡片内边距
    'card_margin': 10,         # 卡片外边距
    'row_pad':     6,          # 控件行间距
    'control_gap': 4,          # 控件之间
    'window_size': (1000, 640),  # 比原来 1080x720 稍小
}


def apply_styles(style):
    """一次性配置所有 ttk 组件。"""
    c = C; f = F
    style.theme_use("clam")

    # 全局
    style.configure(".", background=c['window_bg'], foreground=c['text'], font=f['label'])

    # 卡片
    style.configure("Card.TFrame", background=c['card_bg'], relief="flat")

    # 卡片标题
    style.configure("CardTitle.TLabel",
                    background=c['card_bg'], foreground=c['title'], font=f['card_title'])

    # 窗口顶部大标题
    style.configure("WinTitle.TLabel",
                    background=c['window_bg'], foreground=c['accent'], font=f['window_title'])

    # 主按钮（蓝底白字）
    style.configure("Primary.TButton",
                    background=c['accent'], foreground='#ffffff', font=f['btn'],
                    padding=(12, 5), borderwidth=0)
    style.map("Primary.TButton",
              background=[("active", '#3d5be0'), ("pressed", '#2d4bcf')])

    # 次按钮（白底蓝描边）
    style.configure("Secondary.TButton",
                    background=c['card_bg'], foreground=c['accent'], font=f['btn'],
                    padding=(10, 4), borderwidth=1)
    style.map("Secondary.TButton",
              background=[("active", c['accent_soft'])])

    # 输入框 / 下拉框
    style.configure("Field.TEntry",
                    font=f['label'], padding=(8, 4),
                    background=c['card_bg'], foreground=c['text'],
                    borderwidth=1, relief="solid")
    style.configure("Field.TCombobox",
                    font=f['label'], padding=(6, 3),
                    background=c['card_bg'], foreground=c['text'],
                    borderwidth=1, relief="solid")
    style.map("Field.TCombobox",
              fieldbackground=[("readonly", c['card_bg'])])


def build_date_buttons(parent, style, year, month, today_day=4):
    """构建 7x6 日历网格（按钮）。"""
    c = C; f = F
    cal = calendar.Calendar(firstweekday=0)  # 周日开始
    weeks = cal.monthdatescalendar(year, month)

    for row_idx, week in enumerate(weeks):
        for col_idx, date in enumerate(week):
            day = date.day
            is_this_month = date.month == month

            if not is_this_month:
                # 上月/下月的灰字
                btn = tk.Label(parent, text=str(day),
                               bg=c['card_bg'], fg='#d0d6e0',
                               font=('Microsoft YaHei', 10),
                               anchor="center",
                               relief="flat", bd=0,
                               padx=2, pady=6)
            elif day == today_day and date.month == month:
                # 今天：主色圆底
                btn = tk.Label(parent, text=str(day),
                               bg=c['today_bg'], fg=c['today_fg'],
                               font=F['date_num'],
                               anchor="center",
                               relief="flat", bd=0,
                               padx=2, pady=6)
            else:
                # 普通天：白色背景（以后替换成按钮以支持点击事件）
                btn = tk.Label(parent, text=str(day),
                               bg=c['card_bg'], fg=c['text'],
                               font=F['date_num'],
                               anchor="center",
                               relief="flat", bd=0,
                               padx=2, pady=6, cursor="hand2")
                # 模拟有事件的天（4号、7号、15号、20号）
                if day in (7, 15, 20) and date.month == month:
                    btn.configure(bg=c['has_event_bg'], fg=c['has_event_fg'])

            btn.grid(row=row_idx, column=col_idx, padx=1, pady=1, sticky="nsew")
            # hover 效果
            def _hover(e, b=btn, orig_bg=btn['bg']):
                b.configure(bg=c['accent_soft'])
            def _leave(e, b=btn, orig_bg=btn['bg']):
                # 有事件的保留淡黄底
                if b.cget('fg') == c['has_event_fg']:
                    b.configure(bg=c['has_event_bg'])
                elif b.cget('bg') != c['today_bg']:
                    b.configure(bg=c['card_bg'])
            btn.bind("<Enter>", _hover)
            btn.bind("<Leave>", _leave)


def main():
    root = tk.Tk()
    root.title("事件日历管理")
    W, H = S['window_size']
    root.geometry("%dx%d+%d+%d" % (
        W, H,
        max(0, (root.winfo_screenwidth() - W) // 2),
        max(0, (root.winfo_screenheight() - H) // 3)))
    root.configure(bg=C['window_bg'])
    root.minsize(900, 560)

    style = ttk.Style()
    apply_styles(style)

    current_year = 2026
    current_month = 10

    # ══════════════════════════════════════════════════
    # 顶部标题栏
    # ══════════════════════════════════════════════════
    header = tk.Frame(root, bg=C['window_bg'])
    header.pack(fill="x", padx=16, pady=(14, 8))

    ttk.Label(header, text="📅  事件日历管理",
              style="WinTitle.TLabel").pack(side="left")

    ttk.Button(header, text="⚙ 设置",
               style="Secondary.TButton").pack(side="right", padx=(6, 0))
    ttk.Button(header, text="📁 文件",
               style="Primary.TButton").pack(side="right", padx=(6, 0))
    ttk.Button(header, text="＋ 新建事件",
               style="Primary.TButton").pack(side="right")

    # ══════════════════════════════════════════════════
    # 年份月份选择（紧凑一行）
    # ══════════════════════════════════════════════════
    control_card = ttk.Frame(root, style="Card.TFrame", padding=(12, 10))
    control_card.pack(fill="x", padx=14, pady=(0, 10))

    ttk.Label(control_card, text="年份:", style="CardTitle.TLabel").grid(
        row=0, column=0, padx=(0, 4), sticky="e")
    year_var = tk.StringVar(value=str(current_year))
    year_entry = ttk.Entry(control_card, textvariable=year_var, width=6,
                            font=F['label'], state="readonly",
                            style="Field.TEntry")
    year_entry.grid(row=0, column=1, padx=(0, 12), pady=0, sticky="w")

    ttk.Label(control_card, text="月份:", style="CardTitle.TLabel").grid(
        row=0, column=2, padx=(0, 4), sticky="e")
    month_var = tk.StringVar(value=str(current_month))
    month_combo = ttk.Combobox(control_card, textvariable=month_var,
                               values=[str(i) for i in range(1, 13)],
                               width=5, state="readonly",
                               style="Field.TCombobox")
    month_combo.grid(row=0, column=3, padx=(0, 16), sticky="w")

    ttk.Label(control_card, text="Excel:", style="CardTitle.TLabel").grid(
        row=0, column=4, padx=(0, 4), sticky="e")
    file_entry = ttk.Entry(control_card, width=42, style="Field.TEntry",
                            font=F['label'])
    file_entry.insert(0, r"C:\Users\me\Documents\我的日程.xlsx")
    file_entry.grid(row=0, column=5, padx=(0, 6), sticky="we")

    ttk.Button(control_card, text="选择…",
               style="Secondary.TButton").grid(row=0, column=6, padx=4)
    ttk.Button(control_card, text="刷新",
               style="Secondary.TButton").grid(row=0, column=7, padx=4)

    control_card.columnconfigure(5, weight=1)

    # ══════════════════════════════════════════════════
    # 主区域：左日历 + 右事件详情（各占一半）
    # ══════════════════════════════════════════════════
    body = tk.Frame(root, bg=C['window_bg'])
    body.pack(fill="both", expand=True, padx=14, pady=(0, 14))

    body.columnconfigure(0, weight=3, uniform="half")  # 日历稍宽
    body.columnconfigure(1, weight=2, uniform="half")
    body.rowconfigure(0, weight=1)

    # ── 左侧：日历卡片 ──
    cal_card = ttk.Frame(body, style="Card.TFrame", padding=(14, 12))
    cal_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

    # 卡标题：2026 年 10 月 + 今天
    cal_title_bar = tk.Frame(cal_card, bg=C['card_bg'])
    cal_title_bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
    ttk.Label(cal_title_bar, text="2026 年 10 月",
              style="CardTitle.TLabel").pack(side="left")
    tk.Label(cal_title_bar, text="  ·  周六",
             bg=C['card_bg'], fg=C['text_dim'],
             font=F['label']).pack(side="left")
    # 今天小圆标签
    today_tag = tk.Label(cal_title_bar, text="  今天 10/4  ",
                         bg=C['accent'], fg='#ffffff',
                         font=('Microsoft YaHei', 9, 'bold'),
                         padx=6, pady=1,
                         relief="flat")
    today_tag.pack(side="right")

    # 星期表头（一行）
    weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
    wd_frame = tk.Frame(cal_card, bg=C['card_bg'])
    wd_frame.grid(row=1, column=0, sticky="ew", pady=(0, 2))
    for i, wd in enumerate(weekdays):
        lbl = tk.Label(wd_frame, text=wd,
                       bg=C['weekday_bg'], fg=C['weekday_fg'],
                       font=('Microsoft YaHei', 9, 'bold'),
                       anchor="center", padx=4, pady=4)
        lbl.grid(row=0, column=i, sticky="ew", padx=1)

    # 日期网格容器（放 7x6 的日期按钮）
    grid_frame = tk.Frame(cal_card, bg=C['card_bg'])
    grid_frame.grid(row=2, column=0, sticky="nsew")
    for i in range(7):
        grid_frame.columnconfigure(i, weight=1, uniform="col")
    for i in range(6):
        grid_frame.rowconfigure(i, weight=1)

    build_date_buttons(grid_frame, style, current_year, current_month)

    cal_card.columnconfigure(0, weight=1)
    cal_card.rowconfigure(2, weight=1)

    # 图例
    legend = tk.Frame(cal_card, bg=C['card_bg'])
    legend.grid(row=3, column=0, sticky="ew", pady=(8, 0))

    tk.Label(legend, text="● 今天  ",
             bg=C['today_bg'], fg=C['today_fg'],
             font=('Microsoft YaHei', 8, 'bold'),
             padx=6, pady=2).pack(side="left")
    tk.Label(legend, text="● 有事件  ",
             bg=C['has_event_bg'], fg=C['has_event_fg'],
             font=('Microsoft YaHei', 8, 'bold'),
             padx=6, pady=2).pack(side="left", padx=(4, 0))
    tk.Label(legend, text="（点击日期查看事件详情）",
             bg=C['card_bg'], fg=C['text_dim'],
             font=('Microsoft YaHei', 8)).pack(side="right")

    # ── 右侧：事件详情卡片 ──
    evt_card = ttk.Frame(body, style="Card.TFrame", padding=(14, 12))
    evt_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

    # 卡标题
    evt_title_bar = tk.Frame(evt_card, bg=C['card_bg'])
    evt_title_bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))

    ttk.Label(evt_title_bar, text="📋 事件详情",
              style="CardTitle.TLabel").pack(side="left")
    ttk.Label(evt_title_bar, text="  10/04 周六",
              background=C['card_bg'], foreground=C['text_dim'],
              font=F['label']).pack(side="left")

    ttk.Button(evt_title_bar, text="🔍 搜索",
               style="Secondary.TButton").pack(side="right", padx=(4, 0))

    # 事件列表（用 Canvas + 自定义事件项，不用 Text 更灵活）
    evt_canvas = tk.Canvas(evt_card, bg=C['card_bg'], highlightthickness=0,
                            borderwidth=0)
    evt_scroll = ttk.Scrollbar(evt_card, orient="vertical", command=evt_canvas.yview)
    evt_inner = tk.Frame(evt_canvas, bg=C['card_bg'])

    evt_inner.bind("<Configure>",
                   lambda e: evt_canvas.configure(scrollregion=evt_canvas.bbox("all")))
    evt_canvas.create_window((0, 0), window=evt_inner, anchor="nw", tags=("body",))
    evt_canvas.bind("<Configure>",
                    lambda e: evt_canvas.itemconfigure("body", width=e.width))

    evt_canvas.configure(yscrollcommand=evt_scroll.set)

    evt_canvas.grid(row=1, column=0, sticky="nsew")
    evt_scroll.grid(row=1, column=1, sticky="ns")

    # 渲染模拟事件
    mock_events = [
        ("⏰", "今天 · 10/04", [
            ("09:00", "产品评审会议（第三季度复盘）", C['accent']),
            ("14:30", "客户A对接合同细节", C['accent']),
            ("20:00", "备考：线性代数 第5章", C['accent']),
        ]),
        ("📆", "明天 · 10/05", [
            ("10:00", "健身（胸+三头）", C['text_dim']),
            ("15:00", "整理项目文档 → push GitHub", C['text_dim']),
        ]),
        ("🌙", "下周", [
            ("10/07", "提交 Release 包 v2.3.0", C['text_dim']),
            ("10/09", "部门周会 + OKR 同步", C['text_dim']),
            ("10/11", "带家人复查（上午）", C['text_dim']),
            ("10/13", "技术分享（主题待定）", C['text_dim']),
        ]),
    ]

    row = 0
    for emoji, date_header, items in mock_events:
        tk.Label(evt_inner,
                 text=f"{emoji}  {date_header}",
                 bg=C['card_bg'], fg=C['title'],
                 font=('Microsoft YaHei', 10, 'bold')).grid(
            row=row, column=0, sticky="w", pady=(10 if row > 0 else 0, 4))
        row += 1
        for time_str, event_text, dot_color in items:
            item_frame = tk.Frame(evt_inner, bg=C['card_bg'])
            item_frame.grid(row=row, column=0, sticky="ew", pady=1)
            # 圆点
            tk.Label(item_frame, text="●",
                     bg=C['card_bg'], fg=dot_color,
                     font=('Microsoft YaHei', 8)).pack(side="left", padx=(0, 6))
            # 时间
            tk.Label(item_frame, text=time_str,
                     bg=C['card_bg'], fg=dot_color,
                     font=('Microsoft YaHei', 9, 'bold')).pack(side="left")
            # 事件
            tk.Label(item_frame, text=event_text,
                     bg=C['card_bg'], fg=C['text'],
                     font=F['event'], wraplength=340,
                     anchor="w", justify="left").pack(side="left", fill="x", expand=True, padx=(4, 0))
            row += 1

    evt_card.columnconfigure(0, weight=1)
    evt_card.rowconfigure(1, weight=1)
    evt_inner.columnconfigure(0, weight=1)

    root.mainloop()


if __name__ == "__main__":
    main()
