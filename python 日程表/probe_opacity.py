# -*- coding: utf-8 -*-
"""取证：拖动「桌面图标透明度」时，被削弱的到底是「底色」还是「文字」。

判据很硬：今日事件的文字色是 #333333（灰度 51）且完全不透明。
· 真正的「透明」= 只让底色消失，文字像素应恒为 ~51，不受影响
· 现在的「整体半透明」= 文字被一起稀释，像素值会朝桌面色漂移

做法：先在不透明状态下锁定一批「文字像素坐标」，之后每次都在
同一批坐标上采样，看它们的灰度怎么变。
"""
import os
import sys
import time

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

import show_yourwindows as m

app = m.QApplication.instance() or m.QApplication(sys.argv)
w = m.MyWindow()
w.move(150, 150)
w.show()
app.processEvents()
time.sleep(2.0)

TEXT_GRAY = 51.0  # #333333 的灰度


def grab():
    w.repaint()
    app.processEvents()
    time.sleep(0.6)
    r = w.content_label.rect()
    p = w.content_label.mapToGlobal(r.topLeft())
    return app.primaryScreen().grabWindow(
        0, p.x() + 12, p.y() + 12, r.width() - 24, r.height() - 24).toImage()


def gray_at(img, x, y):
    c = img.pixelColor(x, y)
    return 0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()


# ---------- 基准：不透明状态，锁定文字像素坐标 ----------
base = grab()
text_pts, bg_pts = [], []
for y in range(0, base.height(), 1):
    for x in range(0, base.width(), 1):
        g = gray_at(base, x, y)
        if g < 110:          # 深色 = 文字笔画
            text_pts.append((x, y))
        elif g > 215:        # 接近白 = 白框底色
            bg_pts.append((x, y))
print("锁定文字像素 %d 个、底色像素 %d 个" % (len(text_pts), len(bg_pts)))
if not text_pts:
    print("!! 没抓到文字像素，可能白框内无内容"); sys.exit(1)


def sample(img):
    t = sum(gray_at(img, x, y) for x, y in text_pts) / len(text_pts)
    b = sum(gray_at(img, x, y) for x, y in bg_pts) / len(bg_pts) if bg_pts else 0
    return t, b


def report(tag, img):
    t, b = sample(img)
    drift = abs(t - TEXT_GRAY)
    print("  %-36s 文字 %6.1f (偏离本色 %5.1f)   底色 %6.1f" % (tag, t, drift, b))
    return t, b


print()
print("=" * 84)
print("修复后｜apply_window_opacity：只降底色 alpha，文字保持不透明")
print("=" * 84)
report("透明度 = 1.00", base)
w.apply_window_opacity(0.6)
report("透明度 = 0.60", grab())
w.apply_window_opacity(0.3)
t30, b30 = report("透明度 = 0.30", grab())
w.apply_window_opacity(0.0)
t0, b0 = report("透明度 = 0.00（底色全去掉）", grab())

print("=" * 84)
print("对照｜旧实现 setWindowOpacity（整体半透明）")
print("=" * 84)
w.apply_window_opacity(1.0)
w.setWindowOpacity(0.3)
told, _ = report("旧实现 0.30", grab())

print("=" * 84)
print("文字本色 #333333 灰度 = %.0f" % TEXT_GRAY)
print("  · 修复后 0.00：文字 %.1f（偏离 %.1f），底色 %.1f" % (t0, abs(t0 - TEXT_GRAY), b0))
print("  · 旧实现 0.30：文字 %.1f（偏离 %.1f）" % (told, abs(told - TEXT_GRAY)))
print("  · 判定：修复后文字偏离 %.1f，旧实现偏离 %.1f" % (abs(t0 - TEXT_GRAY), abs(told - TEXT_GRAY)))
print("=" * 84)
w.close()
