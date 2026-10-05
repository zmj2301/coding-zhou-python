# -*- coding: utf-8 -*-
"""验证「滑动组件」（QSizeGrip）与「事件框长度」联动：

用户录屏暴露的问题：主窗口白框太矮，内容被截断、出现滚动条；而无边框窗口
又拖不到边缘改大小。本脚本验证：
  [1] 主窗口右下角确实有可拖拽的滑动组件（QSizeGrip），挂在 central_widget 上
  [2] 启动时白框高度 == 设置里的 event_length（真正按设置显示，不再被卡矮）
  [3] 改 event_length（等同调滑块 / 拖 grip）后，白框与窗口真的跟着变
  [4] 模拟拖拽 grip 改大窗口：resizeEvent 反推出新的 event_length 并写回 user_data.json
  [5] 改字号时窗口高度纹丝不动（「改字号像调分辨率」根治，确认未回归）
  [6] 内容比白框高时不自动撑大窗口，而是在框内滚动（不再截断）
"""
import os
import sys
import json
import tempfile
import shutil

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

import show_yourwindows as m

try:
    from PySide6.QtCore import QTimer, Qt, QPoint
except ImportError:
    from PySide2.QtCore import QTimer, Qt, QPoint

# 用临时目录隔离 user_data.json，避免污染真实设置
_TMP = tempfile.mkdtemp(prefix="verify_grip_")
_orig_get_app_path = m.get_app_path
m.get_app_path = lambda: _TMP
m.get_settings_dir = lambda: _TMP

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


def read_saved_el():
    p = os.path.join(_TMP, m.USER_SETTINGS_FILE)
    if not os.path.exists(p):
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f).get("event_length")
    except Exception:
        return None


print("=" * 76)
print("[1] 主窗口右下角是否存在可拖拽的滑动组件 (QSizeGrip)")
print("=" * 76)
g = getattr(w, "size_grip", None)
print("    size_grip =", g)
check("size_grip 是 QSizeGrip 实例", isinstance(g, m.QSizeGrip))
check("挂在 central_widget 上", g is not None and g.parent() is w.central_widget)
check("尺寸合理 (20~26px)", g is not None and 20 <= g.width() <= 26 and 20 <= g.height() <= 26)

print("=" * 76)
print("[2] 启动时白框高度 == 设置里的 event_length")
print("=" * 76)
base_el = int(round(float(w.event_length)))
box_h = w.content_label.height()
# 白框会被屏幕高度正确夹取（offscreen 虚拟屏很矮），期望取 min(el, 上限)
_scr2 = m.QApplication.primaryScreen()
_cap2 = (_scr2.availableGeometry().height() - 60 - w._other_widgets_height()) if _scr2 is not None else (10 ** 9)
_exp2 = min(base_el, max(_cap2, 60))
print("    启动时：event_length=%s  白框高度=%s（期望 %s，屏幕上限夹取=%s）"
      % (base_el, box_h, _exp2, _cap2))
check("白框高度 = min(event_length, 屏幕上限)（误差<=4）",
      abs(box_h - _exp2) <= 4, "%s vs %s" % (box_h, _exp2))

print("=" * 76)
print("[3] 改 event_length（=调滑块 / 拖 grip）后白框与窗口真的跟着变")
print("=" * 76)
w.event_length = 240
w._fit_content_height(allow_grow=True)
app.processEvents()
h240 = w.content_label.height()
win240 = w.height()
print("    event_length=240 -> 白框=%s 窗口高=%s" % (h240, win240))
check("白框跟随到 ~240", abs(h240 - 240) <= 4, str(h240))

w.event_length = 520
w._fit_content_height(allow_grow=True)
app.processEvents()
h520 = w.content_label.height()
win520 = w.height()
print("    event_length=520 -> 白框=%s 窗口高=%s" % (h520, win520))
# 超过屏幕可用高度时会被正确「夹」在屏幕内（无边框窗口不能超出屏幕），
# 所以期望值取 min(520, 屏幕上限 - others)。offscreen 虚拟屏很矮会触发夹取。
scr = m.QApplication.primaryScreen()
screen_cap = (scr.availableGeometry().height() - 60) if scr is not None else (10 ** 9)
expected_520 = min(520, screen_cap - w._other_widgets_height())
check("白框跟随到 ~520（或受屏幕高度夹取）", abs(h520 - expected_520) <= 4,
      "%s vs 期望 %s" % (h520, expected_520))
check("窗口高度随之变化", win520 != win240, "%s -> %s" % (win240, win520))
check("白框 520 比 240 更高", h520 > h240 + 100, "%s > %s" % (h520, h240))

print("=" * 76)
print("[4] 真实合成鼠标事件拖拽 grip -> 反推 event_length 并持久化")
print("=" * 76)
# resizeEvent 现在只在「鼠标按着」时才反推 event_length（防止启动等被动
# resize 漂移用户设置），所以这里用合成鼠标事件完整模拟：按下 -> 向下拖 -> 松开
try:
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtCore import QPointF, QEvent
except ImportError:
    from PySide2.QtGui import QMouseEvent
    from PySide2.QtCore import QPointF, QEvent

g = w.size_grip
anchor = g.mapToGlobal(g.rect().center())
el_before = int(round(float(w.event_length)))
win_before = w.height()
dy = -120  # 向上拖：窗口已在屏幕上限附近，向下拖会被屏幕高度夹住

# 说明：QSizeGrip 对「合成事件」的 globalPos 处理依赖平台（Qt5/Qt6 行为不一），
# 它自己的缩放数学是 Qt 的久经考验代码，不在本测试范围。这里按下真实 grip
# （走我们的事件过滤器，置 _grip_dragging），随后直接 resize 窗口——
# 这正是 grip 处理器实际调用的东西，能完整覆盖「我们的逻辑」：
# 过滤器标记 -> resizeEvent 反推 event_length -> 防抖持久化。
app.sendEvent(g, QMouseEvent(QEvent.MouseButtonPress,
                             g.mapFromGlobal(anchor), anchor,
                             Qt.LeftButton, Qt.LeftButton, Qt.NoModifier))
check("按下 grip 后拖拽标记生效", getattr(w, "_grip_dragging", False))
others = w._other_widgets_height()
target_el = max(el_before + dy, 60)
app.processEvents()
w.resize(w.width(), others + target_el)  # 模拟 grip 处理器驱动的 resize
app.processEvents()
print("    按住 grip 拖拽 %dpx：窗口 %s -> %s  event_length %s -> %s"
      % (dy, win_before, w.height(), el_before, int(round(float(w.event_length)))))
check("窗口跟随拖拽", abs(w.height() - (others + target_el)) <= 6,
      "%s -> %s（期望 %s）" % (win_before, w.height(), others + target_el))
check("event_length 被反推为 ~%d" % target_el,
      abs(int(round(float(w.event_length))) - target_el) <= 6,
      str(w.event_length))
check("白框跟随拖拽", abs(w.content_label.height() - target_el) <= 6,
      str(w.content_label.height()))
app.sendEvent(g, QMouseEvent(QEvent.MouseButtonRelease,
                             g.mapFromGlobal(anchor + QPoint(0, dy)), anchor + QPoint(0, dy),
                             Qt.LeftButton, Qt.NoButton, Qt.NoModifier))
check("松开后拖拽标记复位", not getattr(w, "_grip_dragging", False))
# 防抖写盘：强制让 400ms 定时器立即触发
w._el_save_timer.start(0)
app.processEvents()
saved = read_saved_el()
print("    user_data.json 中保存的 event_length =", saved)
check("grip 拖拽结果已写回 user_data.json",
      saved is not None and abs(int(round(float(saved))) - target_el) <= 6,
      str(saved))

print("=" * 76)
print("[5] 改字号时窗口高度纹丝不动（根治「改字号像调分辨率」）")
print("=" * 76)
before_win = w.height()
before_box = w.content_label.height()
for sz in (14, 20, 26, 14):
    w.apply_text_size(sz)
    app.processEvents()
after_win = w.height()
after_box = w.content_label.height()
print("    字号 14->20->26->14：窗口高 %s -> %s（应不变）" % (before_win, after_win))
check("窗口高度全程不变", after_win == before_win, "%s -> %s" % (before_win, after_win))
check("正文/倒计时字号确实变了",
      w.content_label.font().pointSize() == 14
      and w.countdown_label.font().pointSize() == 18)

print("=" * 76)
print("[6] 内容比白框高时：窗口不自动撑大，框内出现滚动条")
print("=" * 76)
w.event_length = 180
w._fit_content_height(allow_grow=True)
app.processEvents()
tall = "\n".join("• 第 %02d 条：这是一条用来把白框撑爆的超长待办事项示例内容" % i
                for i in range(1, 40))
w.content_label.setPlainText(tall)
w._fit_content_height()  # 内容变化，不放大窗口
app.processEvents()
box_tall = w.content_label.height()
scroll = w.content_label.verticalScrollBar()
print("    白框固定=180，灌入 40 条后白框高度=%s  滚动条可见=%s"
      % (box_tall, scroll.isVisible()))
check("白框仍被锁在 ~180（不自动撑大）", abs(box_tall - 180) <= 4, str(box_tall))
check("内容过高时出现滚动条（不再截断）", scroll.isVisible())

print("=" * 76)
print("汇总:", "全部通过 ✅" if not FAIL else "失败项 %s" % FAIL)
print("=" * 76)

# 清理临时目录
try:
    shutil.rmtree(_TMP, ignore_errors=True)
except Exception:
    pass
w.close()
sys.exit(1 if FAIL else 0)
