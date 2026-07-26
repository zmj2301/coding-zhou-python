import tkinter as tk
import pyperclip
from PIL import ImageTk, Image, ImageDraw


HIGHLIGHT = "#07C160"
SIDEBAR_BG = "#F5F5F5"
SIDEBAR_W = 360


class OcrResultWindow:
    def __init__(self, pil_image, ocr_lines, on_done=None, parent_root=None):
        self.pil_image = pil_image
        self.ocr_lines = ocr_lines
        self.on_done = on_done
        self.parent_root = parent_root
        self.root = None
        self.line_widgets = []
        self.copy_timers = {}
        self.highlight_image = None
        self.tk_image = None
        self.image_label = None

    def show(self):
        self.root = tk.Toplevel(self.parent_root) if self.parent_root else tk.Tk()
        self.root.title("OCR 识别结果")
        self.root.configure(bg="white")
        self.root.attributes('-topmost', True)

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        w, h = min(1000, screen_w - 100), min(600, screen_h - 100)
        x = (screen_w - w) // 2
        y = (screen_h - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.minsize(700, 400)

        self.root.bind('<Escape>', lambda e: self._done())

        main = tk.Frame(self.root, bg="white")
        main.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(main, bg="white", padx=10, pady=10)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_image_panel(left)

        sep = tk.Frame(main, width=1, bg="#E0E0E0")
        sep.pack(side=tk.LEFT, fill=tk.Y)

        right = tk.Frame(main, bg=SIDEBAR_BG, width=SIDEBAR_W)
        right.pack(side=tk.RIGHT, fill=tk.Y)
        right.pack_propagate(False)

        self._build_sidebar(right)

        bottom = tk.Frame(self.root, bg="white", padx=15, pady=8)
        bottom.pack(fill=tk.X)

        tk.Button(bottom, text="完成", bg=HIGHLIGHT, fg="white",
                  font=("Microsoft YaHei", 10), bd=0, padx=20, pady=4,
                  activebackground="#06AD56", cursor="hand2",
                  command=self._done).pack(side=tk.RIGHT)

        self.root.protocol("WM_DELETE_WINDOW", self._done)

    def _build_image_panel(self, parent):
        img = self.pil_image.copy()
        draw = ImageDraw.Draw(img)
        for line in self.ocr_lines:
            x, y, w, h = line["x"], line["y"], line["w"], line["h"]
            draw.rectangle([x, y, x + w, y + h], outline=HIGHLIGHT, width=2)

        iw, ih = img.size
        pw = 520
        ratio = min(pw / iw, 1.0)
        dw, dh = int(iw * ratio), int(ih * ratio)
        img_display = img.resize((dw, dh), Image.LANCZOS)
        self.highlight_image = img
        self.tk_image = ImageTk.PhotoImage(img_display)

        self.image_label = tk.Label(parent, image=self.tk_image, bg="white")
        self.image_label.pack()

    def _build_sidebar(self, parent):
        header = tk.Frame(parent, bg=SIDEBAR_BG, padx=12, pady=10)
        header.pack(fill=tk.X)
        tk.Label(header, text="识别到的文字", bg=SIDEBAR_BG, fg="#333",
                 font=("Microsoft YaHei", 11, "bold")).pack(anchor=tk.W)
        tk.Label(header, text="点击 \U0001f4cb 复制文字", bg=SIDEBAR_BG, fg="#999",
                 font=("Microsoft YaHei", 8)).pack(anchor=tk.W)

        canvas = tk.Canvas(parent, bg=SIDEBAR_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=SIDEBAR_BG)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor=tk.NW, width=SIDEBAR_W - 16)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        for i, line in enumerate(self.ocr_lines):
            frame = self._create_line_frame(scroll_frame, i, line)
            frame.pack(fill=tk.X, padx=8, pady=2)
            self.line_widgets.append(frame)

    def _create_line_frame(self, parent, idx, line):
        text = line["text"]
        frame = tk.Frame(parent, bg="white", bd=0, padx=10, pady=6)

        num_label = tk.Label(frame, text=str(idx + 1), bg=HIGHLIGHT, fg="white",
                             font=("Microsoft YaHei", 8), width=2, height=1)
        num_label.pack(side=tk.LEFT, padx=(0, 8))

        copy_btn = tk.Label(frame, text="\U0001f4cb", bg="white", fg="#999",
                            font=("Arial", 10), cursor="hand2")
        copy_btn.pack(side=tk.RIGHT, padx=(5, 0))
        copy_btn.bind('<Button-1>', lambda e, i=idx, b=copy_btn: self._copy_line(i, b))

        text_label = tk.Label(frame, text=text, bg="white", fg="#333",
                              font=("Microsoft YaHei", 10), anchor=tk.W, justify=tk.LEFT,
                              wraplength=SIDEBAR_W - 80)
        text_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        return frame

    def _copy_line(self, idx, btn):
        pyperclip.copy(self.ocr_lines[idx]["text"])

        if idx in self.copy_timers and self.copy_timers[idx] is not None:
            try:
                self.root.after_cancel(self.copy_timers[idx])
            except Exception:
                pass

        btn.configure(text="\u2611")
        timer = self.root.after(1000, lambda b=btn: b.configure(text="\U0001f4cb"))
        self.copy_timers[idx] = timer

    def _done(self):
        for timer_id in self.copy_timers.values():
            if timer_id is not None:
                try:
                    self.root.after_cancel(timer_id)
                except Exception:
                    pass
        self.copy_timers.clear()

        if self.root:
            try:
                self.root.destroy()
            except Exception:
                pass
            self.root = None
        if self.on_done:
            self.on_done()
