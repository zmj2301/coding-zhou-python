# -*- coding: utf-8 -*-
"""验证「彻底退出」：

背景：主窗口不占任务栏后，退出不彻底会导致进程残留、exe 被占用删不掉。
本脚本模拟最坏情况——退出后有东西把进程卡死（死循环），验证：
  [1] 悬浮球菜单的「退出」已改走主窗口的彻底退出（button_quit）
  [2] button_quit 的看门狗能在 ~2 秒内强杀卡死的进程（本文件自身作为
      子进程跑，父进程计时并断言退出码）
"""
import os
import re
import subprocess
import sys
import time

os.chdir(os.path.dirname(os.path.abspath(__file__)))

FAIL = []


def check(name, cond, extra=""):
    print("  [%s] %s%s" % ("PASS" if cond else "FAIL", name, ("  " + extra) if extra else ""))
    if not cond:
        FAIL.append(name)


print("=" * 76)
print("[1] 悬浮球「退出」走彻底退出入口")
print("=" * 76)
with open("show_yourwindows.py", "r", encoding="utf-8") as f:
    src = f.read()
check("悬浮球菜单已改为 self.main_window.button_quit",
      "menu.addAction('退出', self.main_window.button_quit)" in src)
check("不再有裸 QApplication.quit 作退出入口",
      "menu.addAction('退出', QApplication.instance().quit)" not in src)
check("button_quit 含看门狗强杀 (os._exit)", "os._exit(0)" in src)

print("=" * 76)
print("[2] 看门狗强杀卡死的进程（子进程实测，应 ~2 秒退出、退出码 0）")
print("=" * 76)
CHILD = r'''
import os, sys, time
sys.path.insert(0, os.getcwd())
QT_QPA = os.environ.get("QT_QPA_PLATFORM", "")
import show_yourwindows as m
app = m.QApplication.instance() or m.QApplication(sys.argv)
w = m.MyWindow()
w.show()
app.processEvents()
# 模拟「退出后被卡死」：调 button_quit 后进程并不自行结束，而是死循环。
# 期望：button_quit 启动的看门狗线程在 ~2 秒后 os._exit(0) 强杀本进程。
w.button_quit()
t0 = time.time()
while True:
    time.sleep(0.05)
    if time.time() - t0 > 30:
        os._exit(9)  # 30 秒还没被杀 = 看门狗失效
'''
child = os.path.join(os.getcwd(), "_quit_flow_child.py")
with open(child, "w", encoding="utf-8") as f:
    f.write(CHILD)

env = dict(os.environ)
t0 = time.time()
proc = subprocess.run([sys.executable, "_quit_flow_child.py"],
                      env=env, capture_output=True, timeout=40)
elapsed = time.time() - t0
os.remove(child)
print("    子进程退出码=%s  耗时=%.1f 秒" % (proc.returncode, elapsed))
check("卡死的进程被看门狗杀掉（退出码 0）", proc.returncode == 0, str(proc.returncode))
check("在 ~6 秒内结束（看门狗 2 秒 + 子进程启动余量）", elapsed < 6.0, "%.1fs" % elapsed)

print("=" * 76)
print("汇总:", "全部通过 ✅" if not FAIL else "失败项 %s" % FAIL)
print("=" * 76)
sys.exit(1 if FAIL else 0)
