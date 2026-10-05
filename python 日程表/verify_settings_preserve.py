# -*- coding: utf-8 -*-
"""验证两个用户反馈的修复：

反馈一（截图1）：「调了下字体，其它设置又回复到默认状态了，需要一个个重新调整」
  根因：拖 grip / 调事件框长度时，_persist_event_length 把主窗口启动时的
  *旧设置快照*（self.user_settings）整个写回 user_data.json，把用户新改的
  其它设置盖回旧值；且打开设置窗口时每个滑块 .set() 都触发 update_e。
  验证：
    [1] 只写 event_length 单键 —— 其它键绝不被旧快照污染
    [2] ttk.Scale.set() 确实会触发 command（证明初始化保护是必要的）
    [3] 源码里有 _settings_init 初始化保护开关

反馈二（截图2）：「任务栏能不显示不」
    [4] 主窗口带 Qt.Tool 标志 —— 不再在任务栏显示
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
    from PySide6.QtCore import QTimer, Qt
except ImportError:
    from PySide2.QtCore import QTimer, Qt

# 用临时目录隔离 user_data.json，避免污染真实设置
_TMP = tempfile.mkdtemp(prefix="verify_settings_")
m.get_app_path = lambda: _TMP
m.get_settings_dir = lambda: _TMP

# 预置一份「用户精心调过的」设置
_PREFILL = {
    "event_length": 506,
    "text_size": 22,
    "icon_size": 88,
    "window_opacity": 0.4,
    "icon_opacity": 0.6,
}
with open(os.path.join(_TMP, m.USER_SETTINGS_FILE), "w", encoding="utf-8") as f:
    json.dump(_PREFILL, f, ensure_ascii=False)

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
print("[1] 拖 grip / 调事件框长度后，其它设置不被旧快照污染（单键写盘）")
print("=" * 76)
# 模拟「主窗口启动时的旧快照」：和文件里用户调过的值完全不同
w.user_settings.update({"text_size": 9, "icon_size": 48,
                        "window_opacity": 1.0, "icon_opacity": 1.0})
w._persist_event_length(300)
back = m.load_user_settings(_TMP)
print("    写盘后文件:", json.dumps(back, ensure_ascii=False))
check("event_length 已更新为 300", back.get("event_length") == 300, str(back.get("event_length")))
check("text_size 仍是用户调的 22（不被旧快照 9 覆盖）", back.get("text_size") == 22, str(back.get("text_size")))
check("icon_size 仍是用户调的 88（不被旧快照 48 覆盖）", back.get("icon_size") == 88, str(back.get("icon_size")))
check("window_opacity 仍是 0.4", abs(back.get("window_opacity", 0) - 0.4) < 1e-6, str(back.get("window_opacity")))
check("icon_opacity 仍是 0.6", abs(back.get("icon_opacity", 0) - 0.6) < 1e-6, str(back.get("icon_opacity")))

print("=" * 76)
print("[2] ttk.Scale.set() 会触发 command（初始化保护为什么必要）")
print("=" * 76)
import tkinter as tk
from tkinter import ttk
root = tk.Tk()
root.withdraw()
fired = []
s = ttk.Scale(root, from_=0, to=100, command=lambda v: fired.append(v))
s.set(30)
print("    创建后直接 .set(30)，command 触发次数 =", len(fired))
check(".set() 触发了 command（不保护就会误应用/误写盘）", len(fired) >= 1, str(fired))
root.destroy()

print("=" * 76)
print("[3] 源码含 _settings_init 初始化保护")
print("=" * 76)
with open("show_yourwindows.py", "r", encoding="utf-8") as f:
    src = f.read()
check("存在 _settings_init 开关", "_settings_init" in src)

print("=" * 76)
print("[4] 主窗口不占任务栏（Qt.Tool）")
print("=" * 76)
flags = w.windowFlags()
print("    flags =", hex(int(flags)), "| Qt.Tool 位 =", bool(flags & Qt.Tool))
check("主窗口带 Qt.Tool 标志", bool(flags & Qt.Tool))

print("=" * 76)
print("汇总:", "全部通过 ✅" if not FAIL else "失败项 %s" % FAIL)
print("=" * 76)

shutil.rmtree(_TMP, ignore_errors=True)
w.close()
sys.exit(1 if FAIL else 0)
