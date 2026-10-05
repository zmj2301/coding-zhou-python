# -*- coding: utf-8 -*-
"""验证：过期事件现在也能在主窗口看到（用户要求）。

构造一组混合事件：今天 / 未来 / 已过期，调用主窗口的刷新逻辑，
断言：① 主窗口正文包含已过期的那一条；② 带有「已过期」标注；
③ 今天和未来事件照常显示；④ 数据层不自动删除（见 verify_expiry.py）。
"""
import os
import sys
import time
from datetime import date, timedelta

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

try:
    from PySide6.QtCore import QTimer
except ImportError:
    from PySide2.QtCore import QTimer

import show_yourwindows as m

app = m.QApplication.instance() or m.QApplication(sys.argv)
w = m.MyWindow()
w.show()
app.processEvents()
for t in w.findChildren(QTimer):
    t.stop()
app.processEvents()

FAIL = []


def check(name, cond, extra=""):
    print("  [%s] %s%s" % ("PASS" if cond else "FAIL", name, ("  " + extra) if extra else ""))
    if not cond:
        FAIL.append(name)


today = date.today()
d_today = (today.month, today.day)
d_future = ((today + timedelta(days=5)).month, (today + timedelta(days=5)).day)
d_past = ((today - timedelta(days=2)).month, (today - timedelta(days=2)).day)

w.events = [
    {'month': "%02d" % d_today[0], 'day': "%02d" % d_today[1], 'things': "今天的例会"},
    {'month': "%02d" % d_future[0], 'day': "%02d" % d_future[1], 'things': "未来的考试"},
    {'month': "%02d" % d_past[0], 'day': "%02d" % d_past[1], 'things': "过期的缴费"},
]

print("=" * 76)
print("[1] 主窗口正文是否包含过期事件")
print("=" * 76)
w.update_countdown()
app.processEvents()
text = w.content_label.toPlainText()
print("    主窗口正文：")
for line in text.splitlines():
    print("      " + line)

check("正文包含今天事件", "今天的例会" in text)
check("正文包含未来事件", "未来的考试" in text)
check("正文包含过期事件", "过期的缴费" in text, "过期项是否出现")
check("有「已过期」标注", "已过期" in text)
check("标注提示手动清除", "手动清除" in text)

print("=" * 76)
print("[2] 过期事件不应被自动删除（数据层仍保留）")
print("=" * 76)
labels = [e['things'] for e in w.events]
check("过期事件仍在 self.events", "过期的缴费" in labels)

print("=" * 76)
print("汇总:", "全部通过" if not FAIL else "失败项 %s" % FAIL)
print("=" * 76)
w.close()
sys.exit(1 if FAIL else 0)
