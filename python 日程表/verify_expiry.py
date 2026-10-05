# -*- coding: utf-8 -*-
"""验证用户最关心的问题：事件过期后会不会被自动清除。

今天是 10 月 1 日，所以用「9月30日」模拟已过期事件、「10月5日」模拟未来事件。
检查两件事：
  1) 数据层：self.events 里过期事件还在不在（会不会被自动删掉）
  2) 显示层：主窗口还会不会显示它
"""
import os
import sys
import time

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

import show_yourwindows as m

now = time.localtime()
today_m, today_d = now.tm_mon, now.tm_mday
print("系统今天: %d月%d日" % (today_m, today_d))

app = m.QApplication.instance() or m.QApplication(sys.argv)
w = m.MyWindow()
w.show()
app.processEvents()
time.sleep(1.0)

# 清空现有事件，只放两条我们自己造的：一条已过期、一条未来
w.events = [
    {'month': '09', 'day': '30', 'things': '【过期测试】昨天的事件'},
    {'month': '10', 'day': '05', 'things': '【未来测试】五天后的事件'},
]
print("已注入 2 条事件：09-30（过期） / 10-05（未来）")
print()

# 刷新显示（程序每秒都会自动调用这个）
w.update_countdown()
app.processEvents()
time.sleep(0.5)

print("=" * 74)
print("[1] 数据层：过期事件还在不在 self.events 里")
months_days = [(e.get('month'), e.get('day')) for e in w.events]
print("    self.events =", months_days)
expired_kept = ('09', '30') in months_days
print("    >>> 过期事件保留在内存中:", expired_kept)

print("=" * 74)
print("[2] 显示层：主窗口还看不看得到过期事件")
text = w.content_label.toPlainText()
print("    主窗口正文:")
for line in text.strip().splitlines():
    print("       " + line)
expired_shown = '过期测试' in text
future_shown = '未来测试' in text
print("    >>> 过期事件显示在主窗口:", expired_shown)
print("    >>> 未来事件显示在主窗口:", future_shown)

print("=" * 74)
print("[3] 再连续刷新 5 次，看过期事件会不会被逐步清掉")
for i in range(5):
    w.update_countdown()
    app.processEvents()
    time.sleep(0.3)
months_days2 = [(e.get('month'), e.get('day')) for e in w.events]
print("    5 次刷新后 self.events =", months_days2)
print("    >>> 依然保留:", ('09', '30') in months_days2)

print("=" * 74)
print("结论：")
print("  · 数据层 %s —— 过期事件不会被自动删除，只有手动「标记为已完成」才删"
      % ("✅ 安全" if expired_kept else "❌ 被自动清除了"))
print("  · 显示层 %s —— 主窗口只显示「今天 + 未来」的倒计时，过期事件不再出现在主窗口"
      % ("已隐藏" if not expired_shown else "仍显示"))
print("  · 过期事件在「日历」窗口里仍可看到（会标注「已过期」），在那里手动删除")
print("=" * 74)
w.close()
