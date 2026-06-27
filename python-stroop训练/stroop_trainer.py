import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import random
import time
import json
import os
import threading
import webbrowser
from datetime import datetime

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# 智谱 AI API Key（从 zai 示例中取得），可按需替换
ZHIPU_API_KEY = os.environ.get('ZHIPUAI_API_KEY', '')
ZHIPU_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

COLORS = [
    ("红色", "#ff0000"),
    ("蓝色", "#0000ff"),
    ("绿色", "#008000"),
    ("黄色", "#ffff00"),
    ("紫色", "#800080"),
    ("橙色", "#ff8c00"),
    ("粉色", "#ff69b4"),
    ("青色", "#00ffff"),
    ("棕色", "#8b4513"),
    ("灰色", "#808080"),
    ("黑色", "#000000"),
    ("白色", "#ffffff"),
]

TOTAL_QUESTIONS = 10
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stroop_records.json")


def text_fg_for_bg(bg_hex):
    bg = bg_hex.lstrip("#")
    r, g, b = int(bg[0:2], 16), int(bg[2:4], 16), int(bg[4:6], 16)
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    return "white" if brightness < 140 else "black"


class StroopTrainer:
    def __init__(self, root):
        self.root = root
        self.root.title("Stroop 训练")
        self.root.geometry("680x760")
        self.root.configure(bg="white")

        self.score = 0
        self.question_index = 0
        self.start_time = None
        self.current_color_name = None
        self.current_display_color = None
        self.timer_running = False
        self.history_window = None

        self._build_ui()
        self._show_start_screen()
        self.root.protocol("WM_DELETE_WINDOW", self._on_exit)

    def _build_ui(self):
        self.title_label = tk.Label(
            self.root,
            text="Stroop 训练",
            font=("Microsoft YaHei", 24, "bold"),
            fg="black",
            bg="white",
        )
        self.title_label.pack(pady=20)

        self.info_label = tk.Label(
            self.root,
            text="请点击文字显示的颜色，而不是文字内容！",
            font=("Microsoft YaHei", 12),
            fg="#333333",
            bg="white",
        )
        self.info_label.pack(pady=5)

        self.status_label = tk.Label(
            self.root,
            text="",
            font=("Microsoft YaHei", 14),
            fg="#0066cc",
            bg="white",
        )
        self.status_label.pack(pady=10)

        self.word_label = tk.Label(
            self.root,
            text="",
            font=("Microsoft YaHei", 56, "bold"),
            bg="white",
        )
        self.word_label.pack(pady=30)

        self.buttons_frame = tk.Frame(self.root, bg="white")
        self.buttons_frame.pack(pady=20)

        self.color_buttons = []
        cols = 4
        for i, (name, code) in enumerate(COLORS):
            btn = tk.Button(
                self.buttons_frame,
                text=name,
                font=("Microsoft YaHei", 12, "bold"),
                width=8,
                height=2,
                bg=code,
                fg=text_fg_for_bg(code),
                activebackground=code,
                activeforeground=text_fg_for_bg(code),
                command=lambda c=code, n=name: self._on_click(c, n),
                relief="raised",
                bd=3,
            )
            btn.grid(row=i // cols, column=i % cols, padx=6, pady=6)
            self.color_buttons.append(btn)

        self.time_label = tk.Label(
            self.root,
            text="用时: 0.00 秒",
            font=("Microsoft YaHei", 12),
            fg="#cc8800",
            bg="white",
        )
        self.time_label.pack(pady=10)

        bottom_frame = tk.Frame(self.root, bg="white")
        bottom_frame.pack(pady=5)

        self.action_button = tk.Button(
            bottom_frame,
            text="开始训练",
            font=("Microsoft YaHei", 14, "bold"),
            width=12,
            bg="#4caf50",
            fg="white",
            command=self._start_game,
        )
        self.action_button.grid(row=0, column=0, padx=10)

        self.history_button = tk.Button(
            bottom_frame,
            text="历史记录",
            font=("Microsoft YaHei", 14, "bold"),
            width=12,
            bg="#2196f3",
            fg="white",
            command=self._show_history,
        )
        self.history_button.grid(row=0, column=1, padx=10)

        tk.Button(
            bottom_frame,
            text="退出",
            font=("Microsoft YaHei", 14, "bold"),
            width=12,
            bg="#555555",
            fg="white",
            command=self._on_exit,
        ).grid(row=0, column=2, padx=10)

        self._set_buttons_state(tk.DISABLED)

    def _on_exit(self):
        if not messagebox.askyesno("退出确认", "确定要退出 Stroop 训练吗？"):
            return
        script_dir = os.path.dirname(os.path.abspath(__file__))
        template_name = "stroop_comparison.html"
        deleted_files = []
        try:
            filenames = os.listdir(script_dir)
        except OSError as e:
            messagebox.showerror("退出错误", f"无法扫描目录: {e}")
            self.root.destroy()
            return
        for name in filenames:
            if not name.endswith(".html"):
                continue
            if name == template_name:
                continue
            full_path = os.path.join(script_dir, name)
            try:
                if os.path.isfile(full_path):
                    os.remove(full_path)
                    deleted_files.append(name)
            except OSError:
                pass
        if deleted_files:
            file_list = "\n".join(f"  · {n}" for n in deleted_files)
            messagebox.showinfo(
                "已清理",
                f"已清理 {len(deleted_files)} 个临时报告文件:\n{file_list}"
            )
        self.root.destroy()
    def _show_start_screen(self):
        self.title_label.config(text="Stroop 训练")
        self.word_label.config(text="准备开始", fg="black")
        self.status_label.config(
            text=f"共 {TOTAL_QUESTIONS} 题，点击按钮选择文字显示的颜色"
        )

    def _set_buttons_state(self, state):
        for btn in self.color_buttons:
            btn.config(state=state)

    def _start_game(self):
        self.score = 0
        self.question_index = 0
        self.start_time = time.time()
        self.timer_running = True
        self.action_button.config(state=tk.DISABLED, text="训练中...")
        self._set_buttons_state(tk.NORMAL)
        self._next_question()
        self._update_timer()

    def _next_question(self):
        if self.question_index >= TOTAL_QUESTIONS:
            self._end_game()
            return

        word_info = random.choice(COLORS)
        color_info = random.choice(COLORS)
        while color_info[1] == word_info[1]:
            color_info = random.choice(COLORS)

        self.current_color_name = word_info[0]
        self.current_display_color = color_info[1]
        self.question_index += 1

        self.word_label.config(text=self.current_color_name, fg=self.current_display_color)
        self.status_label.config(
            text=f"第 {self.question_index} / {TOTAL_QUESTIONS} 题   得分: {self.score}"
        )

    def _on_click(self, color_code, color_name):
        if not self.timer_running:
            return

        if color_code == self.current_display_color:
            self.score += 1

        self._next_question()

    def _update_timer(self):
        if not self.timer_running:
            return
        elapsed = time.time() - self.start_time
        self.time_label.config(text=f"用时: {elapsed:.2f} 秒")
        self.root.after(50, self._update_timer)

    def _end_game(self):
        self.timer_running = False
        total_time = time.time() - self.start_time
        self._set_buttons_state(tk.DISABLED)

        self.word_label.config(text="训练结束", fg="black")
        self.status_label.config(
            text=f"完成！得分 {self.score} / {TOTAL_QUESTIONS}"
        )
        self.time_label.config(text=f"总用时: {total_time:.2f} 秒")

        self.action_button.config(state=tk.NORMAL, text="再来一次")

        self._save_record(total_time)

        messagebox.showinfo(
            "训练结果",
            f"完成 {TOTAL_QUESTIONS} 道题目！\n\n"
            f"正确数: {self.score}\n"
            f"总用时: {total_time:.2f} 秒\n"
            f"平均每题: {total_time / TOTAL_QUESTIONS:.2f} 秒\n"
            f"正确率: {self.score / TOTAL_QUESTIONS * 100:.1f}%\n\n"
            f"本次结果已保存到 stroop_records.json",
        )

    def _save_record(self, total_time):
        record = {
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "score": self.score,
            "total_questions": TOTAL_QUESTIONS,
            "accuracy": round(self.score / TOTAL_QUESTIONS * 100, 1),
            "total_time": round(total_time, 2),
            "avg_time_per_question": round(total_time / TOTAL_QUESTIONS, 2),
        }
        try:
            records = []
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    records = json.load(f)
            records.append(record)
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("保存失败", f"无法保存记录: {e}")

    def _open_comparison_report(self, record, seq_num):
        """
        基于 stroop_comparison.html 模板，填入真实测试数据，
        另存为临时 HTML 并用默认浏览器打开。
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(script_dir, "stroop_comparison.html")
        if not os.path.exists(template_path):
            messagebox.showerror(
                "打开失败",
                "未找到模板文件:\n{}".format(template_path),
            )
            return

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                template = f.read()
        except Exception as e:
            messagebox.showerror("打开失败", "读取模板失败: {}".format(e))
            return

        # 读取全部历史记录，用于"累计训练统计
        all_records = []
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, list):
                    all_records = loaded
        except Exception:
            all_records = []

        # 基本字段
        accuracy = float(record.get("accuracy", 0))
        avg_time = float(record.get("avg_time_per_question", 0))
        score = int(record.get("score", 0))
        total_questions = int(record.get("total_questions", 0))
        datetime_str = record.get("datetime", "")

        # 进度条百分比
        accuracy_pct = round(min(accuracy / 84.0 * 100, 100), 1)
        if avg_time <= 0:
            time_pct = 0.0
        else:
            raw = (2.5 - avg_time) / (2.5 - 0.8) * 100
            time_pct = round(max(0.0, min(raw, 100.0)), 1)

        percentile = round(min(accuracy * 1.05, 99), 1)

        # 基于正确率计算综合层级 1~6
        def calc_level(acc):
            if acc >= 95:
                return 6
            if acc >= 88:
                return 5
            if acc >= 80:
                return 4
            if acc >= 70:
                return 3
            if acc >= 55:
                return 2
            return 1

        level = calc_level(accuracy)
        level_desc_map = {
            1: "入门级，继续训练打好基础",
            2: "基础级，基本熟悉任务",
            3: "进阶级，认知控制能力中等",
            4: "熟练级，超过约 65% 的测试者，认知控制能力良好",
            5: "优秀级，超过约 85% 的测试者",
            6: "大师级，超过约 95% 的测试者，认知控制能力出色",
        }
        level_desc = level_desc_map.get(level, "")
        level_tag_map = {
            1: "待提升",
            2: "基础",
            3: "一般",
            4: "良好",
            5: "优秀",
            6: "大师",
        }
        level_tag = level_tag_map.get(level, "-")

        # 构造 6 层金字塔 HTML（保持原始风格：4列 + 右侧状态徽章）
        # 每层（你的正确率，标准正确率，你的用时，标准用时
        # 使用正确率层级名称 + (达到了吧? 由于我们只有总体正确率和平均用时作为每一层级都展示相同指标（因为原始测试记录没有分层数据）

        # 层级定义：标题、副标题、标准正确率、标准用时、达标线
        levels_meta = [
            (1, "基础识别", "颜色文字一致", 50, 1.00, 55),
            (2, "颜色干扰", "颜色文字不一致", 70, 1.30, 70),
            (3, "反向判断", "选择相反颜色", 80, 1.50, 80),
            (4, "混合模式", "随机切换模式", 88, 1.70, 88),
            (5, "加速挑战", "限时快速反应", 93, 1.90, 93),
            (6, "终极大师", "全模式高强度", 98, 2.20, 98),
        ]

        pyramid_blocks = []
        for lv, title, sub, target_acc, target_time, target_cut in levels_meta:
            # 你的正确率和用时统一使用真实测试数据，不做层级虚构调整
            your_acc = accuracy
            your_time = avg_time
            # 判定：真实正确率 >= 该层级达标线 则视为达标
            if your_acc >= target_cut:
                if lv == level:
                    status_html = '<span class="status-tag tag-current">⚡ 当前</span>'
                else:
                    status_html = '<span class="status-tag tag-pass">🟢 达标</span>'
            else:
                status_html = '<span class="status-tag tag-fail">⚠️ 待提升</span>'
            block = (
                '<div class="pyramid-card level-{lv}">'
                '  <div class="pc-header">'
                '    <div class="pc-num">{lv}</div>'
                '    <div class="pc-titles">'
                '      <div class="pc-title">{title}</div>'
                '      <div class="pc-sub">{sub}</div>'
                '    </div>'
                '  </div>'
                '  <div class="pc-body">'
                '    <div class="pc-row">'
                '      <span class="pc-label">你的正确率</span>'
                '      <span class="pc-value" style="color:#fbbf24">{your_acc}%</span>'
                '    </div>'
                '    <div class="pc-row">'
                '      <span class="pc-label">标准正确率</span>'
                '      <span class="pc-value" style="color:#93c5fd">{target_acc}%</span>'
                '    </div>'
                '    <div class="pc-row">'
                '      <span class="pc-label">你的用时</span>'
                '      <span class="pc-value" style="color:#fbbf24">{your_time}s</span>'
                '    </div>'
                '    <div class="pc-row">'
                '      <span class="pc-label">标准用时</span>'
                '      <span class="pc-value" style="color:#6ee7b7">{target_time}s</span>'
                '    </div>'
                '  </div>'
                '  <div class="pc-footer">'
                '    {status_html}'
                '  </div>'
                '</div>'
            ).format(
                lv=lv,
                title=title,
                sub=sub,
                your_acc=your_acc,
                target_acc=target_acc,
                your_time=your_time,
                target_time=target_time,
                status_html=status_html,
            )
            pyramid_blocks.append(block)
        pyramid_levels = "\n".join(pyramid_blocks)

        history_count = len(all_records)
        if history_count > 0:
            avg_accuracy = round(
                sum(float(r.get("accuracy", 0)) for r in all_records) / history_count,
                1,
            )
        else:
            avg_accuracy = accuracy

        # 数据替换（逐字替换占位符，避免 str.format 误解析 CSS 中的花括号）
        level_next = min(level + 1, 6)
        values = {
            "datetime": datetime_str,
            "score": score,
            "total_questions": total_questions,
            "accuracy": accuracy,
            "avg_time_per_question": avg_time,
            "accuracy_pct": accuracy_pct,
            "time_pct": time_pct,
            "percentile": percentile,
            "level": level,
            "level_desc": level_desc,
            "level_tag": level_tag,
            "level_next": level_next,
            "pyramid_levels": pyramid_levels,
            "history_count": history_count,
            "avg_accuracy": avg_accuracy,
        }
        rendered = template
        for k, v in values.items():
            rendered = rendered.replace("{" + k + "}", str(v))

        # 写到临时 HTML
        safe_dt = datetime_str.replace(":", "").replace("-", "").replace(" ", "_")
        out_name = "stroop_report_{}_{}.html".format(seq_num, safe_dt)
        out_path = os.path.join(script_dir, out_name)
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(rendered)
        except Exception as e:
            messagebox.showerror("保存失败", "无法写入报告文件:\n{}".format(e))
            return

        try:
            webbrowser.open("file://" + out_path)
        except Exception as e:
            messagebox.showerror(
                "打开失败",
                "已生成报告文件:\n{}\n\n但无法自动打开浏览器: {}".format(out_path, e),
            )



    def _show_history(self):
        if self.history_window is not None and tk.Toplevel.winfo_exists(self.history_window):
            self.history_window.lift()
            self.history_window.focus_force()
            return

        try:
            if not os.path.exists(DATA_FILE):
                messagebox.showinfo("历史记录", "暂无历史记录。完成一次训练后会自动保存。")
                return
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception as e:
            messagebox.showerror("读取失败", f"无法读取历史记录: {e}")
            return

        if not isinstance(records, list):
            records = []

        if not records:
            messagebox.showinfo("历史记录", "暂无历史记录。")
            return

        self.history_window = tk.Toplevel(self.root)
        self.history_window.title("历史记录")
        self.history_window.geometry("780x760")
        self.history_window.configure(bg="#2b2b2b")
        self.history_window.focus_force()

        header = tk.Label(
            self.history_window,
            text="",
            font=("Microsoft YaHei", 13, "bold"),
            fg="white",
            bg="#2b2b2b",
        )
        header.pack(pady=8)

        hint = tk.Label(
            self.history_window,
            text="先点击选中一条记录，再使用下方按钮操作。",
            font=("Microsoft YaHei", 10),
            fg="#aaccee",
            bg="#2b2b2b",
        )
        hint.pack(pady=0)

        list_frame = tk.Frame(self.history_window, bg="#2b2b2b")
        list_frame.pack(padx=10, pady=8, fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        record_listbox = tk.Listbox(
            list_frame,
            font=("Consolas", 12),
            bg="#1e1e1e",
            fg="#e0e0e0",
            selectbackground="#4a90e2",
            selectforeground="white",
            activestyle="dotbox",
            height=20,
            exportselection=False,
            yscrollcommand=scrollbar.set,
        )
        record_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=record_listbox.yview)

        # summary 必须在 refresh_listbox 之前创建，否则闭包无法捕获
        summary = tk.Label(
            self.history_window,
            text="",
            font=("Microsoft YaHei", 11),
            fg="#ffcc66",
            bg="#2b2b2b",
        )
        summary.pack(pady=5)

        HEADER_ROWS = 2

        def refresh_listbox(current_records):
            record_listbox.delete(0, "end")
            title_line = "{:<6}{:<22}{:<10}{:<12}{:<14}{:<10}".format(
                "序号", "时间", "得分", "正确率", "总用时(s)", "平均(s)"
            )
            record_listbox.insert("end", title_line)
            record_listbox.insert("end", "-" * 84)
            record_listbox.itemconfig(0, {"fg": "#88ccff"})
            record_listbox.itemconfig(1, {"fg": "#88ccff"})
            for idx, r in enumerate(current_records, 1):
                line = "{:<6}{:<22}{:<10}{:<12}{:<14}{:<10}".format(
                    idx,
                    r["datetime"],
                    str(r["score"]) + "/" + str(r["total_questions"]),
                    str(r["accuracy"]) + "%",
                    r["total_time"],
                    r["avg_time_per_question"],
                )
                record_listbox.insert("end", line)
            header.config(text="共 {} 次训练记录".format(len(current_records)))
            if current_records:
                best = max(current_records, key=lambda x: (x["accuracy"], -x["avg_time_per_question"]))
                summary.config(
                    text="最佳记录: {} - {}% 正确率, 平均每题 {}s".format(
                        best["datetime"], best["accuracy"], best["avg_time_per_question"]
                    )
                )
            else:
                summary.config(text="暂无历史记录")

        refresh_listbox(records)
        record_listbox.focus_set()
        if len(records) > 0:
            record_listbox.selection_set(HEADER_ROWS)
            record_listbox.activate(HEADER_ROWS)

        self._history_records_ref = records

        def safe_get_record_index():
            sel = record_listbox.curselection()
            if not sel:
                return None
            record_idx = sel[0] - HEADER_ROWS
            if 0 <= record_idx < len(self._history_records_ref):
                return record_idx
            return None

        def delete_selected():
            record_idx = safe_get_record_index()
            if record_idx is None:
                messagebox.showinfo("提示", "请先选中一条记录再操作。", parent=self.history_window)
                return
            target = self._history_records_ref[record_idx]
            ok = messagebox.askyesno(
                "确认删除",
                "确定删除第 {} 条记录吗？\n\n时间: {}\n得分: {}/{}\n正确率: {}%\n\n删除后将同步更新 JSON 文件。".format(
                    record_idx + 1,
                    target["datetime"],
                    target["score"],
                    target["total_questions"],
                    target["accuracy"],
                ),
                parent=self.history_window,
            )
            if not ok:
                return
            try:
                self._history_records_ref.pop(record_idx)
                with open(DATA_FILE, "w", encoding="utf-8") as f:
                    json.dump(self._history_records_ref, f, ensure_ascii=False, indent=2)
                refresh_listbox(self._history_records_ref)
                new_count = len(self._history_records_ref)
                if new_count > 0:
                    new_sel = min(record_idx + HEADER_ROWS, new_count - 1 + HEADER_ROWS)
                    record_listbox.selection_set(new_sel)
            except Exception as e:
                messagebox.showerror("删除失败", "无法保存变更: {}".format(e), parent=self.history_window)

        def ai_review_selected():
            record_idx = safe_get_record_index()
            if record_idx is None:
                messagebox.showinfo("提示", "请先选中一条记录再操作。", parent=self.history_window)
                return
            try:
                self._open_ai_review(self._history_records_ref[record_idx], record_idx + 1)
            except Exception as e:
                messagebox.showerror("AI 测评错误", "打开 AI 测评时出错: {}".format(e))
                import traceback
                traceback.print_exc()

        def report_selected():
            record_idx = safe_get_record_index()
            if record_idx is None:
                messagebox.showinfo("提示", "请先选中一条记录再操作。", parent=self.history_window)
                return
            self._open_comparison_report(
                self._history_records_ref[record_idx], record_idx + 1
            )

        btn_frame = tk.Frame(self.history_window, bg="#2b2b2b")
        btn_frame.pack(pady=8)

        tk.Button(
            btn_frame,
            text="查看报告（选中项）",
            font=("Microsoft YaHei", 12, "bold"),
            width=18,
            height=2,
            bg="#4caf50",
            fg="white",
            command=report_selected,
        ).grid(row=0, column=0, padx=10)

        tk.Button(
            btn_frame,
            text="AI 测评（选中项）",
            font=("Microsoft YaHei", 12, "bold"),
            width=18,
            height=2,
            bg="#2196f3",
            fg="white",
            command=ai_review_selected,
        ).grid(row=0, column=1, padx=10)

        tk.Button(
            btn_frame,
            text="删除选中项",
            font=("Microsoft YaHei", 12, "bold"),
            width=18,
            height=2,
            bg="#d9534f",
            fg="white",
            command=delete_selected,
        ).grid(row=0, column=2, padx=10)

        tk.Button(
            btn_frame,
            text="关闭",
            font=("Microsoft YaHei", 12, "bold"),
            width=10,
            height=2,
            bg="#555555",
            fg="white",
            command=self.history_window.destroy,
        ).grid(row=0, column=3, padx=10)

    def _open_ai_review(self, record, seq_num):
        if not REQUESTS_AVAILABLE:
            messagebox.showwarning(
                "AI 测评",
                "缺少 requests 库。\n请先运行: pip install requests\n然后重启程序。",
            )
            return

        if hasattr(self, '_ai_review_win') and self._ai_review_win is not None:
            try:
                if tk.Toplevel.winfo_exists(self._ai_review_win):
                    self._ai_review_win.lift()
                    self._ai_review_win.focus_force()
                    return
            except tk.TclError:
                pass
            self._ai_review_win = None

        review_win = tk.Toplevel(self.root)
        self._ai_review_win = review_win
        review_win.title(f"AI 测评 - 第 {seq_num} 条记录")
        review_win.geometry("720x600")
        review_win.configure(bg="#2b2b2b")

        header = tk.Label(
            review_win,
            text="第 {} 条: {}  得分 {}/{}  正确率 {}%  平均 {}s/题".format(
                seq_num,
                record["datetime"],
                record["score"],
                record["total_questions"],
                record["accuracy"],
                record["avg_time_per_question"],
            ),
            font=("Microsoft YaHei", 12, "bold"),
            fg="#88ccff",
            bg="#2b2b2b",
            wraplength=680,
            justify="left",
        )
        header.pack(pady=10, padx=10, anchor="w")

        thinking_label = tk.Label(
            review_win,
            text="【AI 思考中】",
            font=("Microsoft YaHei", 10, "italic"),
            fg="#a0a0a0",
            bg="#2b2b2b",
        )
        thinking_label.pack(padx=10, anchor="w")

        thinking_text = scrolledtext.ScrolledText(
            review_win,
            font=("Microsoft YaHei", 10, "italic"),
            bg="#2a2a3a",
            fg="#9090a0",
            height=6,
            wrap="word",
        )
        thinking_text.pack(padx=10, pady=2, fill="both", expand=False)
        thinking_text.insert("end", "（等待 AI 深度思考...）\n")
        thinking_text.config(state="disabled")

        # --- 保存 AI 测评按钮 ---
        def _save_ai_review():
            # 将 AI 测评结果保存为文本文件，文件名默认使用本次测试数据
            # 过滤 Windows 文件名中的非法字符：\ / : * ? " < > |
            def _sanitize(name):
                for ch in '\\/:*?"<>|':
                    name = name.replace(ch, "_")
                return name

            default_name = _sanitize(
                "Stroop_第{}条_{}_得分{}_{}%".format(
                    seq_num,
                    record["datetime"],
                    record["score"],
                    record["accuracy"],
                )
            )

            file_path = filedialog.asksaveasfilename(
                title="保存AI测评结果",
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt")],
                initialfile=default_name + ".txt",
            )
            if not file_path:
                return
            try:
                summary = header.cget("text") if "header" in locals() else ""
                content = answer_text.get("1.0", "end-1c")
                with open(file_path, "w", encoding="utf-8") as f:
                    if summary:
                        f.write(summary + "\n")
                        f.write("=" * 60 + "\n\n")
                    f.write(content)
                # 保存成功后短暂更新按钮文案反馈
                original_text = answer_save_btn.cget("text")
                answer_save_btn.configure(text="  ✔ 已保存 ", bg="#4caf50")

                def _restore_btn():
                    if not window_alive[0]:
                        return
                    try:
                        answer_save_btn.configure(text=original_text, bg="#2196f3")
                    except tk.TclError:
                        pass

                try:
                    review_win.after(1500, _restore_btn)
                except tk.TclError:
                    pass
            except OSError as err:
                messagebox.showerror("保存失败", "无法写入文件：\n{}".format(err))

        def _on_save_enter(event, btn):
            btn.configure(bg="#42a5f5")

        def _on_save_leave(event, btn):
            btn.configure(bg="#2196f3")

        def _on_save_press(event, btn):
            btn.configure(bg="#1976d2")

        def _on_save_release(event, btn):
            btn.configure(bg="#42a5f5")

        # 【AI 测评结果】标题 + 保存按钮放同一行，保证 y 坐标一致
        section_frame = tk.Frame(review_win, bg="#2b2b2b")
        section_frame.pack(padx=10, pady=(10, 2), fill="x")

        answer_label = tk.Label(
            section_frame,
            text="【AI 测评结果】",
            font=("Microsoft YaHei", 11, "bold"),
            fg="#ffcc66",
            bg="#2b2b2b",
        )
        answer_label.pack(side="left", anchor="w")

        answer_save_btn = tk.Button(
            section_frame,
            text=" 💾 保存 ",
            font=("Microsoft YaHei", 10, "bold"),
            width=10,
            height=1,
            bg="#2196f3",
            fg="white",
            activebackground="#1976d2",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=_save_ai_review,
        )
        answer_save_btn.pack(side="right", anchor="e")
        answer_save_btn.bind("<Enter>", lambda e, b=answer_save_btn: _on_save_enter(e, b))
        answer_save_btn.bind("<Leave>", lambda e, b=answer_save_btn: _on_save_leave(e, b))
        answer_save_btn.bind("<ButtonPress-1>", lambda e, b=answer_save_btn: _on_save_press(e, b))
        answer_save_btn.bind("<ButtonRelease-1>", lambda e, b=answer_save_btn: _on_save_release(e, b))

        answer_text = scrolledtext.ScrolledText(
            review_win,
            font=("Microsoft YaHei", 11),
            bg="#1e1e1e",
            fg="#e0e0e0",
            wrap="word",
        )
        answer_text.pack(padx=10, pady=2, fill="both", expand=True)
        answer_text.config(state="disabled")

        status_bar = tk.Label(
            review_win,
            text="正在调用智谱AI...",
            font=("Microsoft YaHei", 10),
            fg="#88ccff",
            bg="#2b2b2b",
            anchor="w",
        )
        status_bar.pack(padx=10, pady=5, fill="x")

        stop_event = threading.Event()
        window_alive = [True]
        resp_ref = [None]

        def append_text(widget, text):
            def do():
                if not window_alive[0]:
                    return
                try:
                    widget.config(state="normal")
                    widget.insert("end", text)
                    widget.see("end")
                    widget.config(state="disabled")
                except tk.TclError:
                    pass
            try:
                review_win.after(0, do)
            except Exception:
                pass

        def update_status(text):
            def do():
                if not window_alive[0]:
                    return
                try:
                    status_bar.config(text=text)
                except tk.TclError:
                    pass
            try:
                review_win.after(0, do)
            except Exception:
                pass

        def thinking_clear_initial():
            def do():
                if not window_alive[0]:
                    return
                try:
                    thinking_text.config(state="normal")
                    thinking_text.delete("1.0", "end")
                    thinking_text.config(state="disabled")
                except tk.TclError:
                    pass
            try:
                review_win.after(0, do)
            except tk.TclError:
                pass

        first_thinking = [True]
        first_answer = [True]

        prompt = (
            "你是一名专注于 Stroop 效应认知训练的心理学教练。"
            "用户刚完成一次 Stroop 训练，以下是本次训练数据：\n"
            "- 题号：第 {} 次训练\n"
            "- 训练时间：{}\n"
            "- 得分：{} / {}\n"
            "- 正确率：{}%\n"
            "- 总用时：{} 秒\n"
            "- 平均每题：{} 秒\n\n"
            "请按以下结构给出测评（用中文，条理清晰，语言亲切鼓励）：\n"
            "1. 综合评分（用 1~10 分，并说明理由，结合正确率和反应速度）\n"
            "2. 亮点分析（做得好的地方）\n"
            "3. 问题诊断（可能存在的认知干扰或注意力波动）\n"
            "4. 改进建议（给出 3~5 条具体、可操作的训练建议）\n"
            "5. 下次训练目标（给出一个具体的正确率或用时目标）"
        ).format(
            seq_num,
            record["datetime"],
            record["score"],
            record["total_questions"],
            record["accuracy"],
            record["total_time"],
            record["avg_time_per_question"],
        )

        def ai_worker():
            try:

                payload = {
                    "model": "glm-4.7-flash",
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": True,
                    "max_tokens": 65536,
                    "temperature": 1.0,
                    "thinking": {"type": "enabled"},
                }

                headers = {
                    "Authorization": "Bearer {}".format(ZHIPU_API_KEY),
                    "Content-Type": "application/json",
                }

                update_status("AI 正在流式输出...")

                resp = requests.post(
                    ZHIPU_API_URL,
                    headers=headers,
                    json=payload,
                    stream=True,
                    timeout=120,
                )
                resp_ref[0] = resp
                resp.raise_for_status()

                for raw_line in resp.iter_lines(decode_unicode=True):
                    if stop_event.is_set():
                        break
                    if not raw_line:
                        continue
                    line = raw_line.strip()
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if not data or data == "[DONE]":
                        continue
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    try:
                        choice = chunk["choices"][0]
                        delta = choice.get("delta", {})
                    except (KeyError, IndexError, TypeError):
                        continue

                    reasoning = delta.get("reasoning_content") or delta.get("thinking_content")
                    content = delta.get("content")

                    if reasoning:
                        if first_thinking[0]:
                            thinking_clear_initial()
                            first_thinking[0] = False
                        append_text(thinking_text, reasoning)

                    if content:
                        first_answer[0] = False
                        append_text(answer_text, content)

                update_status("测评完成 ✓")
            except requests.exceptions.RequestException as e:
                update_status("网络/API 出错: {}".format(e))
                append_text(
                    answer_text,
                    "\n\n[调用出错] {}\n请检查网络连接或 API Key 是否有效。\n\n"
                    "========== 发送给 AI 的提示词 ==========\n{}".format(e, prompt),
                )
                print("=" * 40)
                print("[AI 测评调用异常] {}".format(e))
                print("发送给 AI 的提示词:")
                print(prompt)
                print("=" * 40)
            except Exception as e:
                update_status("调用失败: {}".format(e))
                append_text(
                    answer_text,
                    "\n\n[调用出错] {}\n请检查网络连接或 API Key 是否有效。\n\n"
                    "========== 发送给 AI 的提示词 ==========\n{}".format(e, prompt),
                )
                print("=" * 40)
                print("[AI 测评调用异常] {}".format(e))
                print("发送给 AI 的提示词:")
                print(prompt)
                print("=" * 40)
            finally:
                if resp_ref[0] is not None:
                    try:
                        resp_ref[0].close()
                    except Exception:
                        pass

        def on_close():
            stop_event.set()
            window_alive[0] = False
            if resp_ref[0] is not None:
                try:
                    resp_ref[0].close()
                except Exception:
                    pass
            try:
                review_win.destroy()
            except Exception:
                pass
            self._ai_review_win = None

        review_win.protocol("WM_DELETE_WINDOW", on_close)

        thread = threading.Thread(target=ai_worker, daemon=True)
        thread.start()


def main():
    root = tk.Tk()
    StroopTrainer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
