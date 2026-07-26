import tkinter as tk
from PIL import ImageTk, Image
import pyautogui
import os
import threading
import sys

from ocr_engine import recognize
from ocr_result_window import OcrResultWindow


CANVAS_COLOR = "#2B2B2B"
SELECTION_BORDER = "#07C160"
SHADOW_ALPHA = "#40000000"
HANDLE_SIZE = 8
MIN_SELECTION = 20


class ScreenshotOverlay:
    def __init__(self, on_complete=None, on_cancel=None):
        self.on_complete = on_complete
        self.on_cancel = on_cancel
        self.screenshot = None
        self.tk_image = None
        self.root = None
        self.canvas = None

        self.sx = self.sy = self.ex = self.ey = 0
        self.start_x = self.start_y = 0
        self.selecting = False
        self.has_selection = False
        self.drag_mode = None
        self.drag_offset_x = self.drag_offset_y = 0
        self.toolbar = None

    def capture_and_show(self):
        screen = pyautogui.screenshot()
        self.screenshot = screen

        screen_w, screen_h = screen.size

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.geometry(f"{screen_w}x{screen_h}+0+0")
        self.root.attributes('-topmost', True)
        self.root.configure(bg=CANVAS_COLOR)
        self.root.focus_set()

        self.tk_image = ImageTk.PhotoImage(screen)

        self.canvas = tk.Canvas(self.root, width=screen_w, height=screen_h,
                                highlightthickness=0, cursor="crosshair")
        self.canvas.pack()

        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image, tags="bg")

        self.canvas.bind('<ButtonPress-1>', self._on_press)
        self.canvas.bind('<B1-Motion>', self._on_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_release)
        self.canvas.bind('<Motion>', self._on_motion)
        self.canvas.bind('<Double-Button-1>', self._on_double_click)
        self.root.bind('<Escape>', lambda e: self._cancel())

        self.root.mainloop()

    def _clear_overlays(self):
        self.canvas.delete("shadow")
        self.canvas.delete("border")
        self.canvas.delete("handles")
        self.canvas.delete("info")

    def _draw_selection(self):
        self._clear_overlays()
        if not self.has_selection and not self.selecting:
            return

        x1, y1, x2, y2 = self._norm_rect()
        sw = self.canvas.winfo_width()
        sh = self.canvas.winfo_height()

        self.canvas.create_rectangle(0, 0, sw, y1, fill="#000000",
                                     stipple="gray50", tags="shadow", outline="")
        self.canvas.create_rectangle(0, y2, sw, sh, fill="#000000",
                                     stipple="gray50", tags="shadow", outline="")
        self.canvas.create_rectangle(0, y1, x1, y2, fill="#000000",
                                     stipple="gray50", tags="shadow", outline="")
        self.canvas.create_rectangle(x2, y1, sw, y2, fill="#000000",
                                     stipple="gray50", tags="shadow", outline="")

        self.canvas.create_rectangle(x1, y1, x2, y2, outline=SELECTION_BORDER,
                                     width=2, tags="border")

        self._draw_handles(x1, y1, x2, y2)
        self._draw_info(x1, y1, x2, y2)

    def _draw_handles(self, x1, y1, x2, y2):
        s = HANDLE_SIZE
        handles = [
            (x1, y1, "nw"), (x2, y1, "ne"),
            (x1, y2, "sw"), (x2, y2, "se"),
            ((x1 + x2) // 2, y1, "n"), ((x1 + x2) // 2, y2, "s"),
            (x1, (y1 + y2) // 2, "w"), (x2, (y1 + y2) // 2, "e"),
        ]
        for hx, hy, tag in handles:
            self.canvas.create_rectangle(hx - s // 2, hy - s // 2,
                                         hx + s // 2, hy + s // 2,
                                         fill="white", outline=SELECTION_BORDER,
                                         width=1, tags=(f"handle_{tag}", "handles"))

    def _draw_info(self, x1, y1, x2, y2):
        w, h = x2 - x1, y2 - y1
        text = f"{w} × {h}"
        bx = x1
        by = y1 - 28 if y1 > 30 else y2 + 4
        self.canvas.create_rectangle(bx, by, bx + len(text) * 8 + 12, by + 22,
                                     fill=SELECTION_BORDER, outline="",
                                     tags="info")
        self.canvas.create_text(bx + 6, by + 11, text=text,
                                fill="white", anchor=tk.W, font=("Arial", 10),
                                tags="info")

    def _norm_rect(self):
        return (min(self.sx, self.ex), min(self.sy, self.ey),
                max(self.sx, self.ex), max(self.sy, self.ey))

    def _get_drag_mode(self, x, y):
        if not self.has_selection:
            return None
        x1, y1, x2, y2 = self._norm_rect()
        s = HANDLE_SIZE + 4
        zones = {
            "nw": (x1, y1, x1 + s, y1 + s),
            "ne": (x2 - s, y1, x2, y1 + s),
            "sw": (x1, y2 - s, x1 + s, y2),
            "se": (x2 - s, y2 - s, x2, y2),
            "n": (x1, y1, x2, y1 + s),
            "s": (x1, y2 - s, x2, y2),
            "w": (x1, y1, x1 + s, y2),
            "e": (x2 - s, y1, x2, y2),
        }
        for mode, (zx1, zy1, zx2, zy2) in zones.items():
            if zx1 <= x <= zx2 and zy1 <= y <= zy2:
                return mode
        return "move"

    def _on_press(self, event):
        if self.has_selection:
            mode = self._get_drag_mode(event.x, event.y)
            if mode == "move":
                self.drag_mode = "move"
                cx, cy = self._norm_rect()[:2]
                self.drag_offset_x = event.x - cx
                self.drag_offset_y = event.y - cy
                return
            elif mode:
                self.drag_mode = mode
                self._setup_drag_offsets(event.x, event.y)
                return
            else:
                self._cancel_selection()

        self.selecting = True
        self.has_selection = False
        self.start_x, self.start_y = event.x, event.y
        self.sx = self.ex = event.x
        self.sy = self.ey = event.y

    def _setup_drag_offsets(self, x, y):
        x1, y1, x2, y2 = self._norm_rect()
        mode = self.drag_mode
        if "n" in mode:
            self.drag_offset_y = y - y1
        if "s" in mode:
            self.drag_offset_y = y - y2
        if "w" in mode:
            self.drag_offset_x = x - x1
        if "e" in mode:
            self.drag_offset_x = x - x2

    def _on_drag(self, event):
        if self.selecting:
            self.ex, self.ey = event.x, event.y
            if abs(event.x - self.start_x) > 5 or abs(event.y - self.start_y) > 5:
                self.selecting = True
            self._draw_selection()
            return

        if self.drag_mode and self.has_selection:
            self._apply_drag(event.x, event.y)

    def _apply_drag(self, x, y):
        x1, y1, x2, y2 = self._norm_rect()
        w, h = x2 - x1, y2 - y1
        mode = self.drag_mode

        if mode == "move":
            nx = x - self.drag_offset_x
            ny = y - self.drag_offset_y
            self.sx, self.sy = nx, ny
            self.ex, self.ey = nx + w, ny + h
        elif "w" in mode:
            self.sx = x if "e" not in mode else x - self.drag_offset_x
        elif "e" in mode:
            self.ex = x - self.drag_offset_x
        if "n" in mode:
            self.sy = y if "s" not in mode else y - self.drag_offset_y
        elif "s" in mode:
            self.ey = y - self.drag_offset_y

        self._draw_selection()

    def _on_release(self, event):
        if self.selecting:
            self.selecting = False
            self.ex, self.ey = event.x, event.y
            x1, y1, x2, y2 = self._norm_rect()
            if x2 - x1 < MIN_SELECTION or y2 - y1 < MIN_SELECTION:
                self._cancel_selection()
                return
            self.has_selection = True
            self._draw_selection()
            self._show_toolbar(x2, y2)
            return

        self.drag_mode = None

    def _on_motion(self, event):
        if self.has_selection and not self.selecting:
            mode = self._get_drag_mode(event.x, event.y)
            cursors = {
                "nw": "size_nw_se", "ne": "size_ne_sw",
                "sw": "size_ne_sw", "se": "size_nw_se",
                "n": "sb_v_double_arrow", "s": "sb_v_double_arrow",
                "w": "sb_h_double_arrow", "e": "sb_h_double_arrow",
                "move": "fleur",
            }
            self.canvas.config(cursor=cursors.get(mode, "crosshair"))
        else:
            self.canvas.config(cursor="crosshair")

    def _on_double_click(self, event):
        if self.has_selection:
            self._confirm()

    def _show_toolbar(self, x, y):
        if self.toolbar:
            self.toolbar.destroy()
        self.toolbar = tk.Toplevel(self.root)
        self.toolbar.overrideredirect(True)
        self.toolbar.attributes('-topmost', True)
        self.toolbar.configure(bg="#2B2B2B")

        btn_style = {"bg": "#2B2B2B", "fg": "white", "bd": 0,
                     "font": ("Arial", 14), "padx": 8, "pady": 4,
                     "activebackground": "#3B3B3B", "activeforeground": "white",
                     "cursor": "hand2"}

        confirm = tk.Button(self.toolbar, text="✓", command=self._confirm, **btn_style)
        confirm.pack(side=tk.LEFT, padx=2)

        ocr_btn = tk.Button(self.toolbar, text="🔍", command=self._ocr_recognize, **btn_style)
        ocr_btn.pack(side=tk.LEFT, padx=2)

        cancel = tk.Button(self.toolbar, text="✕", command=self._cancel, **btn_style)
        cancel.pack(side=tk.LEFT, padx=2)

        save = tk.Button(self.toolbar, text="💾", command=self._save, **btn_style)
        save.pack(side=tk.LEFT, padx=2)

        self.toolbar.update_idletasks()
        tw, th = self.toolbar.winfo_reqwidth(), self.toolbar.winfo_reqheight()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()

        tx = min(x + 10, sw - tw - 10)
        ty = min(y + 10, sh - th - 10)
        self.toolbar.geometry(f"+{int(tx)}+{int(ty)}")

    def _confirm(self):
        area = self._norm_rect()
        cropped = self.screenshot.crop(area)

        if self.toolbar:
            self.toolbar.destroy()
            self.toolbar = None

        if self.on_complete:
            self.on_complete(cropped)

        self._close_all()

    def _ocr_recognize(self):
        area = self._norm_rect()
        cropped = self.screenshot.crop(area)

        if self.toolbar:
            self.toolbar.destroy()
            self.toolbar = None

        loading_label = tk.Label(
            self.canvas, text="识别中...", bg="#2B2B2B", fg="white",
            font=("微软雅黑", 16), padx=20, pady=10
        )
        loading_label.place(
            x=area[0] + (area[2] - area[0]) // 2,
            y=area[1] + (area[3] - area[1]) // 2,
            anchor="center"
        )

        if self.on_complete:
            self.on_complete(cropped)

        def run_ocr():
            try:
                lines = recognize(cropped)
                if lines:
                    self.root.after(0, lambda: self._show_ocr_result(cropped, lines))
                else:
                    self.root.after(0, self._close_all)
            except Exception as e:
                print(f"OCR error: {e}", file=sys.stderr)
                self.root.after(0, self._close_all)

        threading.Thread(target=run_ocr, daemon=True).start()

    def _show_ocr_result(self, cropped, lines):
        def on_ocr_done():
            self._close_all()

        ocr_win = OcrResultWindow(
            pil_image=cropped,
            ocr_lines=lines,
            on_done=on_ocr_done,
            parent_root=self.root
        )
        if hasattr(ocr_win, 'show'):
            ocr_win.show()

    def _cancel(self):
        if self.on_cancel:
            self.on_cancel()
        self._close_all()

    def _save(self):
        area = self._norm_rect()
        cropped = self.screenshot.crop(area)
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG 图片", "*.png"), ("所有文件", "*.*")]
        )
        if path:
            cropped.save(path)
        self._close_all()

    def _cancel_selection(self):
        self.has_selection = False
        self.selecting = False
        self._clear_overlays()
        if self.toolbar:
            self.toolbar.destroy()
            self.toolbar = None

    def _close_all(self):
        if self.toolbar:
            self.toolbar.destroy()
            self.toolbar = None
        if self.root:
            self.root.quit()
            self.root.destroy()
            self.root = None