# -*- coding: utf-8 -*-
"""验证「开机配置重置」两项根因修复：

终端用户反馈：每次开机都要重新调透明度/文字大小，配置全被改掉。

根因一（致命）：日历窗口选择 Excel 文件时用 'w' 模式把 user_data.json
  整个覆盖成只剩 {"user_data": [路径]}，其它设置全被冲掉。
根因二（位置）：配置存在 exe 所在目录 —— exe 换目录 / 放 Program Files
  无写权限 / 重新解压运行，配置跟丢或静默写失败。

验证：
  [1] 覆盖写已移除（源码不再有对 user_data.json 的 'w' 整写；改为合并保存）
  [2] 合并保存：只更新 user_data 键，其它设置原样保留
  [3] 迁移：老版本 exe 目录里的配置自动搬到新配置目录
  [4] 解耦：exe 换了目录，配置目录不变 → 设置不丢（不再每天重调）
  [5] 写失败不再静默（save_user_settings 失败会写 error.log）
"""
import os
import sys
import json
import shutil
import tempfile

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

import show_yourwindows as m

FAIL = []


def check(name, cond, extra=""):
    print("  [%s] %s%s" % ("PASS" if cond else "FAIL", name, ("  " + extra) if extra else ""))
    if not cond:
        FAIL.append(name)


print("=" * 76)
print("[1] 「选 Excel 整写 user_data.json」的覆盖代码已移除")
print("=" * 76)
with open("show_yourwindows.py", "r", encoding="utf-8") as f:
    src = f.read()
check("不再有覆盖写 user_data.json 的 'w' 模式",
      "json.dumps({\"user_data\": [absolute_path]}" not in src)
check("已改为合并保存 save_user_settings(get_settings_dir(), {'user_data': ...})",
      "save_user_settings(get_settings_dir(),\n                                       {'user_data': [absolute_path]})" in src)

print("=" * 76)
print("[2] 合并保存：Excel 路径与其它设置共存")
print("=" * 76)
TMP = tempfile.mkdtemp(prefix="verify_loc_")
m.get_settings_dir = lambda: TMP
m.save_user_settings(TMP, {"window_opacity": 0.4, "text_size": 22,
                           "icon_size": 88, "event_length": 432})
m.save_user_settings(TMP, {"user_data": ["D:/日程.xlsx"]})  # 模拟日历选 Excel
back = m.load_user_settings(TMP)
print("    保存 Excel 路径后:", json.dumps(back, ensure_ascii=False))
check("user_data 键已更新", back.get("user_data") == ["D:/日程.xlsx"])
check("透明度 0.4 保留", abs(back.get("window_opacity", 0) - 0.4) < 1e-6)
check("字号 22 保留", back.get("text_size") == 22)
check("图标 88 保留", back.get("icon_size") == 88)
check("事件框 432 保留", back.get("event_length") == 432)

print("=" * 76)
print("[3] 老版本配置自动迁移（exe 目录 -> 新配置目录）")
print("=" * 76)
TMP2 = tempfile.mkdtemp(prefix="verify_loc2_")
m.get_settings_dir = lambda: TMP2  # 新配置目录为空
m.save_user_settings(TMP2, {"__keep__": 1})  # 制造"目录已有文件"以关闭迁移？不：先清空
os.remove(os.path.join(TMP2, m.USER_SETTINGS_FILE))
# exe 目录里放一份老配置
with open(os.path.join(TMP, m.USER_SETTINGS_FILE), "w", encoding="utf-8") as f:
    json.dump({"window_opacity": 0.25, "text_size": 20}, f)
m.migrate_legacy_settings(TMP)
back2 = m.load_user_settings(TMP2)
print("    迁移后新目录内容:", json.dumps(back2, ensure_ascii=False))
check("旧配置已搬进新目录", abs(back2.get("window_opacity", 0) - 0.25) < 1e-6
      and back2.get("text_size") == 20)
check("已有配置时不覆盖（幂等）",
      m.migrate_legacy_settings(TMP) is None)

print("=" * 76)
print("[4] exe 换目录，配置不丢（不再每天重调）")
print("=" * 76)
TMP_APP_NEW = tempfile.mkdtemp(prefix="verify_loc_newapp_")
TMP_SET = tempfile.mkdtemp(prefix="verify_loc_set_")
m.get_settings_dir = lambda: TMP_SET
m.save_user_settings(TMP_SET, {"window_opacity": 0.3, "text_size": 24,
                               "icon_size": 66, "event_length": 400})
# 模拟换目录后的新 exe：get_app_path 指向全新目录（里面没有任何配置）
m.get_app_path = lambda: TMP_APP_NEW
try:
    from PySide6.QtCore import QTimer, Qt
except ImportError:
    from PySide2.QtCore import QTimer, Qt
app = m.QApplication.instance() or m.QApplication(sys.argv)
w = m.MyWindow()
w.show()
app.processEvents()
for _t in w.findChildren(QTimer):
    _t.stop()
app.processEvents()
print("    exe 目录=%s（空）  配置目录=%s" % (TMP_APP_NEW, TMP_SET))
print("    启动读到: 透明度=%s 字号=%s 图标=%s 事件框=%s"
      % (w.window_opacity, w.text_size, w.icon_size, w.event_length))
check("透明度 0.3 不丢", abs(w.window_opacity - 0.3) < 1e-6)
check("字号 24 不丢", w.text_size == 24)
check("图标 66 不丢", w.icon_size == 66)
check("事件框 400 不丢", abs(w.event_length - 400) <= 1)

print("=" * 76)
print("[5] 写失败不再静默（有 error.log 痕迹）")
print("=" * 76)
check("save_user_settings 失败走 _log_error", "_log_error(\"写入 user_data.json 失败" in src)
check("存在 _log_error 机制", "def _log_error(" in src)

for d in (TMP, TMP2, TMP_APP_NEW, TMP_SET):
    shutil.rmtree(d, ignore_errors=True)
print("=" * 76)
print("汇总:", "全部通过 ✅" if not FAIL else "失败项 %s" % FAIL)
print("=" * 76)
try:
    w.close()
except Exception:
    pass
sys.exit(1 if FAIL else 0)
