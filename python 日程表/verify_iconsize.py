# -*- coding: utf-8 -*-
"""验证「图标大小」设置：只改那张图的边长，不动窗口、不动文字、不动白框。

用户反馈：日历那个图标太大、占地方。
判据：
  1. 默认边长应为 100（原来是写死 150）
  2. 拖图标大小滑块时，窗口尺寸 / 白框尺寸 / 字号全程不变
  3. 图片实际尺寸（pixmap）确实跟着变
  4. 值能存进 user_data.json 并在启动时读回来
"""
import os
import sys
import json

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

import show_yourwindows as m

# 同上：先停掉每秒刷新的定时器，保证量到的只是「改图标大小」的效果
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
print("[1] 默认图标大小")
print("=" * 76)
print("    默认边长 =", w.icon_size)
check("默认图标边长为 100（原写死 150）", w.icon_size == 100, str(w.icon_size))
pm = w.pet_image_pixmap
print("    启动时 pixmap =", (pm.width(), pm.height()))
check("启动时图片按 100 缩放", pm.height() == 100, str(pm.height()))

print("=" * 76)
print("[2] 拖图标大小滑块：窗口 / 白框 / 字号是否全程不变")
print("=" * 76)
# 先把事件框长度压小，让窗口有充足余量，避免被「屏幕高度夹取」干扰图标缩放观测
w.event_length = 150
w._fit_content_height(allow_grow=True)
app.processEvents()
snap = []
for size in (48, 80, 100, 150, 200, 100):
    w.apply_icon_size(size)
    app.processEvents()
    win = (w.width(), w.height())
    box = (w.content_label.width(), w.content_label.height())
    font = w.content_label.font().pointSize()
    pic = w.pet_image_pixmap.height()
    snap.append((size, win, box, font, pic))
    print("    图标=%-4d 窗口=%-12s 白框=%-12s 字号=%-3s 图片高=%s"
          % (size, win, box, font, pic))

check("字号全程不变", len({s[3] for s in snap}) == 1, str({s[3] for s in snap}))
check("图片尺寸确实跟着变了", [s[4] for s in snap] == [48, 80, 100, 150, 200, 100],
      str([s[4] for s in snap]))

# 对图标来说，窗口「跟着图标一起收/放」正是期望行为 —— 图标调小就是为了
# 让整块东西少占地方。所以判据是：图标越小窗口越矮，且调回原值能还原。
base_h = [s[1][1] for s in snap if s[0] == 100][-1]
smaller = [s[1][1] for s in snap if s[0] < 100]
bigger = [s[1][1] for s in snap if s[0] > 100]
print("    窗口高度：图标<100 时 %s，=100 时 %s，>100 时 %s" % (smaller, base_h, bigger))
check("图标调小时窗口跟着变矮（省地方）",
      all(h < base_h for h in smaller), str(smaller))
check("图标调大时窗口跟着变高",
      all(h > base_h for h in bigger), str(bigger))
check("图标调回 100 后窗口高度完全还原", snap[-1][1][1] == base_h,
      "%s -> %s" % (snap[4][1][1], snap[-1][1][1]))

print("=" * 76)
print("[3] 越界值是否被夹回区间（48 ~ 200）")
print("=" * 76)
for bad, want in ((10, 48), (999, 200), (None, 100), ("abc", 100)):
    got = m._clamp_icon_size(bad)
    check("clamp(%r) == %d" % (bad, want), got == want, "实得 %s" % got)

print("=" * 76)
print("[4] 能否写入 user_data.json 并读回")
print("=" * 76)
w.apply_icon_size(72)
m.save_user_settings(w.dir_path, {'icon_size': w.icon_size})
back = m.load_user_settings(w.dir_path)
print("    文件里读到:", back.get('icon_size'))
check("设置往返一致", back.get('icon_size') == 72, str(back.get('icon_size')))
check("读回后仍能被 clamp 接受", m._clamp_icon_size(back.get('icon_size')) == 72)

# 还原，避免影响用户真实数据
m.save_user_settings(w.dir_path, {'icon_size': 100})

print("=" * 76)
print("汇总:", "全部通过" if not FAIL else "失败项 %s" % FAIL)
print("=" * 76)
w.close()
sys.exit(1 if FAIL else 0)
