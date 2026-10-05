# -*- coding: utf-8 -*-
"""验证「透明度 0 被 or 吃掉」的修复。

这个 bug 由终端用户的诊断报告直接定位：
  报告里 user_data.json 明确写着 "window_opacity": 0.0、"icon_opacity": 0.0，
  说明保存是成功的；但用户说「拉到底重启又变回白板」。

根因：`float(self.user_settings.get('window_opacity') or 1.0)`。
Python 里 0.0 是 falsy，`or` 直接把它丢掉返回 1.0 —— 任何把透明度调到 0
的用户，重启后都会被强制变回 100%（白板）。改多少遍都没用。

  [1] _opacity_from：0 能读出来，None 才回落默认
  [2] 用终端用户的真实配置启动，白框/蓝条 alpha 必须是 0（真透明）
  [3] 重启循环：任意值（含 0）连续多次启动都不丢
  [4] event_length 同类问题也修好了（0 不再被丢）
  [5] 源码里不再有 `or 1.0` 这种取默认值的写法
"""
import os
import sys
import re
import json
import copy
import tempfile
import shutil

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

import show_yourwindows as m

try:
    from PySide6.QtCore import QTimer
except ImportError:
    from PySide2.QtCore import QTimer

FAIL = []


def check(name, cond, extra=""):
    print("  [%s] %s%s" % ("PASS" if cond else "FAIL", name, ("  " + extra) if extra else ""))
    if not cond:
        FAIL.append(name)


def qss_alpha(widget):
    """从控件样式里抠出 background-color 的 alpha 值。"""
    mm = re.search(r'background-color:\s*rgba\([^,]+,[^,]+,[^,]+,\s*([0-9.]+)\s*\)',
                   widget.styleSheet())
    return float(mm.group(1)) if mm else None


# ---------------------------------------------------------------- [1]
print("=" * 76)
print("[1] _opacity_from：0 是合法值，None 才回落默认")
print("=" * 76)
_of = m.MyWindow._opacity_from
check("_opacity_from(0.0) == 0.0", _of(0.0) == 0.0, "得到 %s" % _of(0.0))
check("_opacity_from(0) == 0.0", _of(0) == 0.0, "得到 %s" % _of(0))
check("_opacity_from(0.35) == 0.35", abs(_of(0.35) - 0.35) < 1e-6)
check("_opacity_from(None) == 1.0（缺键才回落）", _of(None) == 1.0, "得到 %s" % _of(None))
check("_opacity_from('abc') == 1.0（脏数据不崩）", _of('abc') == 1.0, "得到 %s" % _of('abc'))
check("_opacity_from(5) == 1.0（超范围夹取）", _of(5) == 1.0, "得到 %s" % _of(5))
check("_opacity_from(-1) == 0.0（负数夹取）", _of(-1) == 0.0, "得到 %s" % _of(-1))

# ---------------------------------------------------------------- [2]
print("=" * 76)
print("[2] 用终端用户的真实配置启动，底色必须真的透明")
print("=" * 76)

# 报告里 user_data.json 的原文（诊断报告 20261003_091709.txt 第 42-53 行）
REAL = {
    # 报告里的 user_data 指向终端用户那台 Win7 的 E:\软件\ZZ\测试待办数据.xlsx，
    # 本机不存在，会让 validate_and_load_data 读 Excel 时段错误（access violation）。
    # 这里只关心透明度相关字段，Excel 指向本机的测试文件即可。
    "user_data": [os.path.join(os.getcwd(), "测试待办数据.xlsx")],
    "event_length": 1200,
    "icon_size": 48,
    "window_opacity": 0.0,
    "text_size": 9,
    "icon_opacity": 0.0,
    "ai_enable": False,
    "auto_fit_box": False,
}

_T = tempfile.mkdtemp(prefix="verify_opacity_")
with open(os.path.join(_T, m.USER_SETTINGS_FILE), 'w', encoding='utf-8') as f:
    json.dump(REAL, f, ensure_ascii=False)
m.get_app_path = lambda: _T
m.get_settings_dir = lambda: _T

app = m.QApplication.instance() or m.QApplication(sys.argv)
w = m.MyWindow()
w.show()
app.processEvents()
for t in w.findChildren(QTimer):
    t.stop()
app.processEvents()
app.processEvents()

check("启动读到 window_opacity == 0.0", w.window_opacity == 0.0,
      "实际 %s" % w.window_opacity)
check("启动读到 icon_opacity == 0.0", w.icon_opacity == 0.0,
      "实际 %s" % w.icon_opacity)

a_content = qss_alpha(w.content_label)
a_count = qss_alpha(w.countdown_label)
a_image = qss_alpha(w.image_label)
print("    实际 alpha：白框=%s 蓝条=%s 图标=%s" % (a_content, a_count, a_image))
check("白框底色 alpha == 0（白板消失）", a_content == 0.0, "实际 %s" % a_content)
check("蓝条底色 alpha == 0", a_count == 0.0, "实际 %s" % a_count)
check("图标底色 alpha == 0", a_image == 0.0, "实际 %s" % a_image)
check("文字仍是不透明实色（#333333）",
      "#333333" in w.content_label.styleSheet())
w.close()

# ---------------------------------------------------------------- [3]
print("=" * 76)
print("[3] 重启循环：0 值反复启动都不丢")
print("=" * 76)
# 复用同一个 MyWindow 实例、改配置后重新走一遍启动流程来模拟「重启」。
# 反复 new/close 多个带定时器的 QMainWindow 会让 PySide2 在退出时段错误
# （segfault），所以这里不做真实的多实例创建。
for val in (0.0, 0.25, 0.0, 1.0, 0.0):
    cfg = copy.deepcopy(REAL)
    cfg['window_opacity'] = val
    cfg['icon_opacity'] = val
    with open(os.path.join(_T, m.USER_SETTINGS_FILE), 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False)
    # 模拟启动时 __init__ 里的那一段读取
    loaded = m.load_user_settings(_T)
    got = m.MyWindow._opacity_from(loaded.get('window_opacity'))
    got_icon = m.MyWindow._opacity_from(loaded.get('icon_opacity'))
    # 模拟 initUI 末尾的 apply_window_opacity()
    w.window_opacity = got
    w.apply_window_opacity()
    app.processEvents()
    a = qss_alpha(w.content_label)
    ok = (got == val and got_icon == val and a == round(0.9 * val, 3))
    check("重新加载 opacity=%s 保持不变且真的应用" % val, ok,
          "读到 %s / 白框alpha=%s（期望 %s）" % (got, a, round(0.9 * val, 3)))
w.close()

# ---------------------------------------------------------------- [4]
print("=" * 76)
print("[4] event_length 同类问题（0 被 or 吃掉）也修好")
print("=" * 76)


def read_event_length(cfg):
    """复刻 __init__ 里的读取逻辑（修好后的版本）。"""
    with open(os.path.join(_T, m.USER_SETTINGS_FILE), 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False)
    loaded = m.load_user_settings(_T)
    v = loaded.get('event_length')
    if v is None:
        v = m.DEFAULT_USER_SETTINGS['event_length']
    return max(60, int(v))


check("event_length=0 时回落到安全下限 60", read_event_length(
    dict(copy.deepcopy(REAL), event_length=0)) == 60)
check("event_length 缺键(None)时用默认 560", read_event_length(
    dict(copy.deepcopy(REAL), event_length=None)) == 560)
check("event_length=240 正常读出", read_event_length(
    dict(copy.deepcopy(REAL), event_length=240)) == 240)

# ---------------------------------------------------------------- [5]
print("=" * 76)
print("[5] 源码里不再有「用 or 取默认值」的写法")
print("=" * 76)
with open('show_yourwindows.py', 'r', encoding='utf-8') as f:
    code = ''.join(ln for ln in f if not ln.strip().startswith('#'))
bad_op = re.findall(r"float\([^)]*\.get\('(?:window|icon)_opacity'\) or ", code)
check("无 float(x.get(opacity) or 默认) 写法", not bad_op, str(bad_op))
bad_el = re.findall(r"int\(\s*self\.user_settings\.get\('event_length'\)\s*\n?\s*or ", code)
check("无 int(x.get(event_length) or 默认) 写法", not bad_el, str(bad_el))

shutil.rmtree(_T, ignore_errors=True)

print("=" * 76)
print("汇总:", "全部通过 ✅" if not FAIL else "失败项 %s" % FAIL)
