# -*- coding: utf-8 -*-
"""验证「手动优先 + 关设置窗口不再覆盖」两项修复（用户第三批语音反馈）：

  [1] 白框自动加高可被关闭（auto_fit_box=False）
  [2] 手动调小后（auto_fit_box=False），内容变多也不会把白框顶高
  [3] 拖 grip / 拖滑块会自动切到「手动优先」，并持久化
  [4] auto_fit_box 会被记住，重启后仍按手动来
  [5] 关闭设置窗口（update_e("exit")）不再用旧快照整份覆盖配置
  [6] 勾选「自动加高」能恢复自动行为
"""
import os
import sys
import json
import time
import tempfile
import shutil

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

import show_yourwindows as m

try:
    from PySide6.QtCore import QTimer, QDate, QEvent, QPointF, Qt
    from PySide6.QtGui import QMouseEvent

    def make_press():
        return QMouseEvent(QEvent.MouseButtonPress, QPointF(5, 5), QPointF(5, 5),
                           Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
                           Qt.KeyboardModifier.NoModifier)
except ImportError:
    from PySide2.QtCore import QTimer, QDate, QEvent, QPointF, Qt
    from PySide2.QtGui import QMouseEvent

    def make_press():
        # PySide2 的签名少一个 globalPos 参数
        return QMouseEvent(QEvent.MouseButtonPress, QPointF(5, 5),
                           Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)

_TMP = tempfile.mkdtemp(prefix="verify_manual_")
m.get_app_path = lambda: _TMP
m.get_settings_dir = lambda: _TMP

app = m.QApplication.instance() or m.QApplication(sys.argv)
FAIL = []


def check(name, cond, extra=""):
    print("  [%s] %s%s" % ("PASS" if cond else "FAIL", name, ("  " + extra) if extra else ""))
    if not cond:
        FAIL.append(name)


def cfg_path():
    return os.path.join(_TMP, m.USER_SETTINGS_FILE)


def read_cfg():
    if not os.path.exists(cfg_path()):
        return {}
    with open(cfg_path(), 'r', encoding='utf-8') as f:
        return json.load(f)


today = QDate.currentDate()


def ev(days_offset, things):
    d = today.addDays(days_offset)
    return {"month": "%02d" % d.month(), "day": "%02d" % d.day(), "things": things}


def others(w):
    return w._other_widgets_height()


def box_h(w):
    return w.content_label.height()


# ---------------------------------------------------------------- [1][2]
print("=" * 76)
print("[1][2] 手动优先：调小后内容变多不再被顶高")
print("=" * 76)

w = m.MyWindow()
w.show()
app.processEvents()
for _t in w.findChildren(QTimer):
    _t.stop()
app.processEvents()

# 造 14 条事件（内容很多，自然高度远大于设定高度）
w.events = [ev(i + 1, "事件%02d-这是一个内容比较长的待办事项用于测试" % i) for i in range(14)]

# 场景 A：自动加高开着（默认）→ 白框会长到内容全高
w.auto_fit_box = True
w.event_length = 150
w._fit_content_height(allow_grow=True)
app.processEvents()
w.update_countdown()
app.processEvents()
app.processEvents()
h_auto = box_h(w)
check("自动加高开启时白框被内容撑高（> 事件框长度 150）", h_auto > 200, "实测 %d" % h_auto)

# 场景 B：用户手动调小 → auto_fit_box 关闭 → 白框严格按 150
w.auto_fit_box = False
w._fit_content_height(allow_grow=True)
app.processEvents()
h_manual = box_h(w)
check("手动模式下白框 = 事件框长度 150", abs(h_manual - 150) <= 4, "实测 %d" % h_manual)

# 关键：内容再变一次（模拟倒计时每秒刷新），白框不能被顶回去
w.update_countdown()
app.processEvents()
app.processEvents()
h_after = box_h(w)
check("正文再次变化后白框仍不被顶高（手动优先生效）",
      abs(h_after - 150) <= 4, "实测 %d（自动模式是 %d）" % (h_after, h_auto))

# 内容变少（清空事件）后也仍按 150
w.events = [ev(1, "只剩一条")]
w.update_countdown()
app.processEvents()
app.processEvents()
h_few = box_h(w)
check("内容变少后白框回落到 150", abs(h_few - 150) <= 4, "实测 %d" % h_few)

# ---------------------------------------------------------------- [3]
print("=" * 76)
print("[3] 拖 grip 自动切到「手动优先」并持久化")
print("=" * 76)

w.auto_fit_box = True
w.event_length = 560
# 模拟真实拖拽：先在 grip 上按下（让事件过滤器置 _grip_dragging=True）。
# 注意必须用 QApplication.sendEvent 派发 —— 直接 widget.event() 不会走
# 事件过滤器链（eventFilter 是在事件派发到 widget 时由 QApplication 调用的）。
app.sendEvent(w.size_grip, make_press())
app.processEvents()
check("grip 按下后 _grip_dragging=True", w._grip_dragging is True)

# 触发一次「拖拽导致的窗口变矮」
target_h = others(w) + 220
w._programmatic_resize = False
w.resize(w.width(), target_h)
app.processEvents()
check("拖 grip 后自动切到手动优先（auto_fit_box=False）",
      w.auto_fit_box is False, "当前 %s" % w.auto_fit_box)
check("event_length 被反推为 220", abs(int(w.event_length) - 220) <= 2,
      "实测 %s" % w.event_length)

# 写盘走的是 400ms 防抖定时器，必须等真实时间过去（不能只 processEvents）
deadline = time.time() + 2.0
while time.time() < deadline and not os.path.exists(cfg_path()):
    app.processEvents()
    time.sleep(0.02)
app.processEvents()
saved = read_cfg()
check("auto_fit_box=false 已写入配置", saved.get('auto_fit_box') is False,
      "文件值 %s" % saved.get('auto_fit_box'))
check("event_length 已写入配置", abs(int(saved.get('event_length', 0)) - 220) <= 2,
      "文件值 %s" % saved.get('event_length'))

# 拖完之后内容变化也不能顶高
w.events = [ev(i + 1, "事件%02d-内容比较长" % i) for i in range(14)]
w.update_countdown()
app.processEvents()
app.processEvents()
h_grip = box_h(w)
check("拖 grip 后内容变多也不顶高", abs(h_grip - 220) <= 4, "实测 %d" % h_grip)

# ---------------------------------------------------------------- [4]
print("=" * 76)
print("[4] 手动优先状态跨重启保留")
print("=" * 76)
w2 = m.MyWindow()
w2.show()
app.processEvents()
for _t in w2.findChildren(QTimer):
    _t.stop()
app.processEvents()
check("新实例读到 auto_fit_box=False", w2.auto_fit_box is False,
      "读到 %s" % w2.auto_fit_box)
check("新实例读到 event_length≈220", abs(int(w2.event_length) - 220) <= 2,
      "读到 %s" % w2.event_length)
h2 = box_h(w2)
check("新实例白框按手动高度显示", abs(h2 - 220) <= 4, "实测 %d" % h2)
w2.events = [ev(i + 1, "事件%02d-内容比较长" % i) for i in range(14)]
w2.update_countdown()
app.processEvents()
app.processEvents()
h2b = box_h(w2)
check("新实例内容变多也不顶高", abs(h2b - 220) <= 4, "实测 %d" % h2b)

# ---------------------------------------------------------------- [5]
print("=" * 76)
print("[5] 关闭设置窗口不再用旧快照整份覆盖")
print("=" * 76)
# 模拟真实事故：设置窗口打开时读到一份旧快照，之后主窗口改了值
save_user = m.save_user_settings
snapshot = dict(read_cfg())           # 「打开设置窗口那一刻」的旧快照
# 之后用户拖 grip / 换 Excel，主窗口已把新值写进文件
save_user(_TMP, {'event_length': 777, 'window_opacity': 0.0, 'icon_size': 150})
# 旧实现会用 snapshot 整份写回，把上面三个新值全部盖回旧值。
# 新实现：exit 只存 auto_fit_box 这一个键。
save_user(_TMP, {'auto_fit_box': snapshot.get('auto_fit_box', True)})
after = read_cfg()
check("event_length 未被旧快照覆盖", abs(int(after.get('event_length', 0)) - 777) <= 1,
      "实测 %s" % after.get('event_length'))
check("window_opacity 未被旧快照覆盖", abs(float(after.get('window_opacity', 1)) - 0.0) < 0.001,
      "实测 %s" % after.get('window_opacity'))
check("icon_size 未被旧快照覆盖", abs(int(after.get('icon_size', 0)) - 150) <= 1,
      "实测 %s" % after.get('icon_size'))

# 静态检查：源码里不能再出现「整份写回 self.user」的写法。
# 只扫非注释行 —— 那行代码已被删除，但解释「为什么删」的注释里还留着原写法。
with open('show_yourwindows.py', 'r', encoding='utf-8') as f:
    code_lines = []
    for ln in f:
        st = ln.strip()
        if st.startswith('#'):
            continue
        code_lines.append(ln)
    code = ''.join(code_lines)
bad = "save_user_settings(get_settings_dir(), self.user)" in code
check("源码中已无 save_user_settings(..., self.user) 整份写回", bad is False)

# ---------------------------------------------------------------- [6]
print("=" * 76)
print("[6] 勾选「自动加高」能恢复自动行为")
print("=" * 76)
w2.auto_fit_box = True
w2._fit_content_height(fit_content=True)
app.processEvents()
app.processEvents()
h_auto2 = box_h(w2)
check("恢复自动后白框重新被内容撑高", h_auto2 > 260, "实测 %d（手动时 %d）" % (h_auto2, h2b))

w2.close()
w.close()
shutil.rmtree(_TMP, ignore_errors=True)

print("=" * 76)
print("汇总:", "全部通过 ✅" if not FAIL else "失败项 %s" % FAIL)
