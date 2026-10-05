# -*- coding: utf-8 -*-
"""设置窗口样式预览（紧凑版）"""
import tkinter as tk
from tkinter import ttk


# ── 设计令牌 ──────────────────────────────────────────────
COLOR = {
    'window_bg':   '#eef1f6',
    'card_bg':     '#ffffff',
    'title':       '#1f2937',
    'accent':      '#4f6ef7',
    'accent_soft': '#eef0ff',
    'text':        '#374151',
    'text_dim':    '#8a94a6',
    'hint':        '#4f6ef7',
    'border':      '#e3e7ef',
    'track':       '#dbe1ec',
}

FONT = {
    'title':  ('Microsoft YaHei', 11, 'bold'),
    'label':  ('Microsoft YaHei', 9),
    'value':  ('Microsoft YaHei', 9, 'bold'),
    'btn':    ('Microsoft YaHei', 9, 'bold'),
}

# ── 紧凑间距令牌（改这一个块即可全局收紧）───────────────
SPACE = {
    'card_pad':      (12, 10),   # 卡片内边距 (x, y)
    'card_margin':   (12, 6),    # 卡片外边距 (x, y_top/bottom)
    'title_sep':     (0, 4),     # 卡片标题 → 分隔线间距
    'sep_first':     (0, 6),     # 分隔线 → 首行控件间距
    'row_pady':      2,          # 同行控件上下间距
    'slider_padx':   (8, 6),     # 滑块左右 padding
    'label_hint':    6,          # 标签到滑块的水平间距
    'header_pad':    (12, 10),   # 顶部标题栏
    'bottom_tip':    (0, 6),     # 底部提示
    'btn_pad':       (12, 5),    # 主按钮 padding
}


def apply_styles(style):
    style.theme_use("clam")

    style.configure(".",
                    background=COLOR['window_bg'],
                    foreground=COLOR['text'],
                    font=FONT['label'])

    style.configure("Card.TFrame",
                    background=COLOR['card_bg'],
                    relief="flat")

    style.configure("CardTitle.TLabel",
                    background=COLOR['card_bg'],
                    foreground=COLOR['title'],
                    font=FONT['title'])

    style.configure("CardSep.TFrame",
                    background=COLOR['border'],
                    height=1)

    style.configure("Setting.TLabel",
                    background=COLOR['card_bg'],
                    foreground=COLOR['text'],
                    font=FONT['label'])

    style.configure("Value.TLabel",
                    background=COLOR['card_bg'],
                    foreground=COLOR['hint'],
                    font=FONT['value'])

    style.configure("Horizontal.TScale",
                    background=COLOR['card_bg'],
                    troughcolor=COLOR['track'],
                    sliderthickness=14,
                    borderwidth=0)

    style.configure("TCheckbutton",
                    background=COLOR['card_bg'],
                    foreground=COLOR['text'],
                    font=FONT['label'])
    style.map("TCheckbutton",
              background=[("active", COLOR['card_bg'])])

    style.configure("Primary.TButton",
                    background=COLOR['accent'],
                    foreground='#ffffff',
                    font=FONT['btn'],
                    padding=SPACE['btn_pad'],
                    borderwidth=0)
    style.map("Primary.TButton",
              background=[("active", '#3d5be0'), ("pressed", '#2d4bcf')])


def make_card(parent, title_text, row):
    px, py = SPACE['card_pad']
    mx, my = SPACE['card_margin']
    card = ttk.Frame(parent, style="Card.TFrame", padding=(px, py))
    card.grid(row=row, column=0, padx=mx, pady=(my, my), sticky="ew")

    if title_text:
        ttk.Label(card, text=title_text, style="CardTitle.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w",
            pady=SPACE['title_sep'])
        sep = ttk.Frame(card, style="CardSep.TFrame", height=1)
        sep.grid(row=1, column=0, columnspan=3, sticky="ew",
                 pady=SPACE['sep_first'])
        start_row = 2
    else:
        start_row = 0

    return card, start_row


def slider_row(card, row, label_text, hint_var, **scale_kwargs):
    ttk.Label(card, text=label_text, style="Setting.TLabel").grid(
        row=row, column=0, sticky="w", pady=SPACE['row_pady'])

    padx_l, padx_r = SPACE['slider_padx']
    slider = ttk.Scale(card, orient=tk.HORIZONTAL, length=200,
                       style="Horizontal.TScale", **scale_kwargs)
    slider.grid(row=row, column=1,
                padx=(SPACE['label_hint'], padx_r),
                sticky="ew", pady=SPACE['row_pady'])

    ttk.Label(card, textvariable=hint_var, style="Value.TLabel").grid(
        row=row, column=2, sticky="e", pady=SPACE['row_pady'])

    card.columnconfigure(1, weight=1)
    return slider


def checkbox_row(card, row, text, bool_var, pady=(4, 0)):
    cb = ttk.Checkbutton(card, text=text, variable=bool_var)
    cb.grid(row=row, column=0, columnspan=3, sticky="w", pady=pady)
    return cb


def main():
    root = tk.Tk()
    root.title("设置 — 紧凑预览")
    root.configure(bg=COLOR['window_bg'])
    # 紧凑后窗口总高从 940 → ~720
    root.geometry("420x720+%d+%d" % (
        max(0, (root.winfo_screenwidth() - 420) // 2),
        max(0, (root.winfo_screenheight() - 720) // 4)))
    root.resizable(False, False)

    style = ttk.Style()
    apply_styles(style)

    # ── 顶部标题栏 ──
    hx, hy = SPACE['header_pad']
    header = tk.Frame(root, bg=COLOR['window_bg'])
    header.pack(fill="x", padx=hx, pady=(hy, 2))
    tk.Label(header, text="⚙  设置日程管理器",
             bg=COLOR['window_bg'], fg=COLOR['accent'],
             font=('Microsoft YaHei', 14, 'bold')).pack(side="left")

    # ── body ──
    body = tk.Frame(root, bg=COLOR['window_bg'])
    body.pack(fill="both", expand=True)
    body.columnconfigure(0, weight=1)

    # ── 状态变量 ──
    v_event_len = tk.IntVar(value=560)
    v_text = tk.IntVar(value=14)
    v_text_hint = tk.StringVar(value="14 px")
    v_opacity = tk.DoubleVar(value=100.0)
    v_opacity_hint = tk.StringVar(value="100%")
    v_icon_op = tk.DoubleVar(value=100.0)
    v_icon_op_hint = tk.StringVar(value="100%")
    v_icon_sz = tk.IntVar(value=100)
    v_icon_sz_hint = tk.StringVar(value="100 px")
    v_auto_fit = tk.BooleanVar(value=True)
    v_autostart = tk.BooleanVar(value=False)

    def _bind_hint(intvar, strvar, suffix=""):
        def _upd(*_):
            try:
                strvar.set("%d%s" % (int(round(float(intvar.get()))), suffix))
            except Exception:
                pass
        intvar.trace_add("write", _upd)

    _bind_hint(v_text, v_text_hint, " px")
    _bind_hint(v_opacity, v_opacity_hint, "%")
    _bind_hint(v_icon_op, v_icon_op_hint, "%")
    _bind_hint(v_icon_sz, v_icon_sz_hint, " px")

    # ══ 卡片 1：外观尺寸 ══
    card1, r1 = make_card(body, "外观尺寸", 0)
    slider_row(card1, r1, "事件框长度",
               tk.StringVar(value="560 px"),
               from_=100, to=1200, variable=v_event_len)
    checkbox_row(card1, r1 + 1, "内容多时自动加高白框（推荐）", v_auto_fit)

    # ══ 卡片 2：文字与图标 ══
    card2, r2 = make_card(body, "文字与图标", 1)
    slider_row(card2, r2, "文字大小", v_text_hint,
               from_=9, to=28, variable=v_text)
    slider_row(card2, r2 + 1, "图标大小", v_icon_sz_hint,
               from_=48, to=200, variable=v_icon_sz)

    # ══ 卡片 3：透明度 ══
    card3, r3 = make_card(body, "透明度", 2)
    slider_row(card3, r3, "底色透明度", v_opacity_hint,
               from_=0, to=100, variable=v_opacity)
    slider_row(card3, r3 + 1, "图标透明度", v_icon_op_hint,
               from_=0, to=100, variable=v_icon_op)

    # ══ 卡片 4：启动行为 ══
    card4, r4 = make_card(body, "启动行为", 3)
    checkbox_row(card4, r4, "开机自动启动", v_autostart)

    ttk.Label(card4, text="开机自启位置",
              style="Setting.TLabel").grid(
        row=r4 + 1, column=0, columnspan=3, sticky="w", pady=(6, 2))

    ttk.Button(card4, text="📍 保存当前位置为开机自启位置",
               style="Primary.TButton").grid(
        row=r4 + 2, column=0, columnspan=3, sticky="ew", pady=(2, 0))

    # ── 底部提示 ──
    tip = tk.Label(root,
                   text="提示：拖主窗口右下角蓝色小块也能调事件框高度",
                   bg=COLOR['window_bg'], fg=COLOR['text_dim'],
                   font=('Microsoft YaHei', 8))
    tip.pack(side="bottom", pady=SPACE['bottom_tip'])

    root.mainloop()


if __name__ == "__main__":
    main()
