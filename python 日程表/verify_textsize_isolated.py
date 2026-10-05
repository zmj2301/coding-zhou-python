# -*- coding: utf-8 -*-
"""验证：改「文字大小」时，只改字号，不动白框、不动窗口。

用户反馈「一调就把显示框全部调整了，感觉像调分辨率」。
判据：改字号前后，窗口尺寸和白框尺寸都应保持不变，只有字号变。
"""
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

import show_yourwindows as m

# 主窗口有每秒刷新倒计时的定时器，会在测量途中改内容、改排版，导致结果抖动。
# 测试几何尺寸时必须先把它停掉，否则测出来的不是「改字号」的效果。
try:
    from PySide6.QtCore import QTimer
except ImportError:
    from PySide2.QtCore import QTimer

app = m.QApplication.instance() or m.QApplication(sys.argv)
w = m.MyWindow()
w.show()
app.processEvents()
for _t in w.findChildren(QTimer):
    _t.stop()
app.processEvents()

FAIL = []


def check(name, cond, extra=""):
    print("  [%s] %s%s" % ("PASS" if cond else "FAIL", name, ("  " + extra) if extra else ""))
    if not cond:
        FAIL.append(name)


print("=" * 76)
print("[1] 改字号时窗口 / 白框尺寸是否保持不变")
print("=" * 76)

# 灌入一份「有内容」的正文，模拟真实使用（否则白框一到底就测不出差异）
w.content_label.setPlainText("\n".join(
    "• 10.%02d 测试事件第 %d 条：这是一条用来撑高白框的示例待办" % (i, i)
    for i in range(1, 13)))
w._fit_content_height(allow_grow=True)
app.processEvents()
print("    初始：窗口=%s 白框=%s（已灌入 12 条示例事件）"
      % ((w.width(), w.height()), (w.content_label.width(), w.content_label.height())))

sizes = []
for size in (14, 18, 22, 28, 14):
    w.apply_text_size(size)
    app.processEvents()
    win = (w.width(), w.height())
    box = (w.content_label.width(), w.content_label.height())
    font = w.content_label.font().pointSize()
    sizes.append((size, win, box, font))
    print("    字号=%-3d 窗口=%-12s 白框=%-12s 实际字号=%s"
          % (size, win, box, font))

# 所有尺寸快照应完全一致（只比较窗口和白框）
win_set = {s[1] for s in sizes}
box_set = {s[2] for s in sizes}
check("窗口尺寸全程不变", len(win_set) == 1, str(win_set))
check("字号确实跟着变了",
      [s[3] for s in sizes] == [14, 18, 22, 28, 14],
      str([s[3] for s in sizes]))
# 白框会给「变高的倒计时标题」让出一点高度（倒计时 = 正文 +4，字号变大它必然变高），
# 但：① 幅度必须很小；② 字号调回原值时必须完全还原。窗口则全程不动。
first_box_h = sizes[0][2][1]
last_box_h = sizes[-1][2][1]
shrink = first_box_h - min(s[2][1] for s in sizes)
check("白框变化幅度很小（<=15%）", shrink <= first_box_h * 0.15,
      "让出 %d px / 原高 %d px" % (shrink, first_box_h))
check("字号调回 14 后白框完全还原", last_box_h == first_box_h,
      "%s -> %s" % (first_box_h, last_box_h))

print("=" * 76)
print("[2] 倒计时 = 正文 +4 的关系是否保持")
print("=" * 76)
w.apply_text_size(20)
check("正文 20 / 倒计时 24",
      w.content_label.font().pointSize() == 20
      and w.countdown_label.font().pointSize() == 24,
      "正文=%s 倒计时=%s" % (w.content_label.font().pointSize(),
                            w.countdown_label.font().pointSize()))

print("=" * 76)
print("[3] 「事件框长度」现在真正是白框的*目标高度*（改它就真的改白框）")
print("=" * 76)
w.event_length = 200
# event_length 是目标高度，必须 allow_grow=True（等同拖 grip / 调滑块）才生效
w._fit_content_height(allow_grow=True)
app.processEvents()
h_small = w.content_label.height()
print("    event_length=200 时白框高度:", h_small)
check("白框高度 ≈ 200", abs(h_small - 200) <= 4, str(h_small))

w.event_length = 560
w._fit_content_height(allow_grow=True)
app.processEvents()
h_big = w.content_label.height()
print("    event_length=560 时白框高度:", h_big)
check("放大后白框可以更高", h_big >= h_small + 100, "%s >= %s" % (h_big, h_small))
# 超过屏幕可用高度时会被正确「夹」在屏幕内（无边框窗口不能超出屏幕），
# 期望值取 min(560, 屏幕上限 - 其它控件高度)。offscreen 虚拟屏很矮会触发夹取。
_scr = m.QApplication.primaryScreen()
_scap = (_scr.availableGeometry().height() - 60) if _scr is not None else (10 ** 9)
_exp560 = min(560, _scap - w._other_widgets_height())
check("白框高度 ≈ 560（或受屏幕高度夹取）", abs(h_big - _exp560) <= 4,
      "%s vs 期望 %s" % (h_big, _exp560))

print("=" * 76)
print("汇总:", "全部通过" if not FAIL else "失败项 %s" % FAIL)
print("=" * 76)
w.close()
sys.exit(1 if FAIL else 0)
