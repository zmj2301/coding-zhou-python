# -*- coding: utf-8 -*-
"""进一步确认：
1) dist/codingzhou-日程表 这个 onedir 版本用的 Qt 绑定
2) ScheduleMate_Win7 那个 PySide2 包内嵌的主脚本，import 的到底是 PySide2 还是 PySide6
"""
import os
import re

from PyInstaller.archive.readers import CArchiveReader

root = os.path.dirname(os.path.abspath(__file__))

print("=" * 78)
print("[1] dist/codingzhou-日程表 目录内容（前 40 个含 Qt/PySide 的）")
onedir = os.path.join(root, "dist", "codingzhou-日程表")
if os.path.isdir(onedir):
    hits = [f for f in os.listdir(onedir) if re.match(r"^(Qt\d|PySide)", f, re.I)]
    print("    目录文件总数: %d" % len(os.listdir(onedir)))
    print("    Qt/PySide 相关: %d 个" % len(hits))
    for f in sorted(hits)[:40]:
        print("      " + f)
else:
    print("    [不存在]")

print("=" * 78)
print("[2] ScheduleMate_Win7\\日程表_Win7.exe 内嵌主脚本的 import")
exe = os.path.abspath(os.path.join(root, "..", "ScheduleMate_Win7", "日程表_Win7.exe"))
r = CArchiveReader(exe)
script_names = [str(n) for n in r.toc if "show_yourwindows" in str(n)]
print("    主脚本条目: %s" % script_names)
for name in script_names:
    try:
        blob = r.extract(name)
    except Exception as e:
        print("    提取失败 %s: %s" % (name, e))
        continue
    if isinstance(blob, tuple):
        # (code_object, is_package)
        blob = blob[0]
    data = blob if isinstance(blob, (bytes, bytearray)) else str(blob).encode("utf-8", "ignore")
    n6 = data.count(b"PySide6")
    n2 = data.count(b"PySide2")
    print("    条目 %-30s 大小 %8d B  PySide6 出现 %d 次 / PySide2 出现 %d 次"
          % (name, len(data), n6, n2))
    for mod in (b"PySide6", b"PySide2"):
        idx = data.find(mod)
        if idx >= 0:
            print("      %s 上下文: %r" % (mod.decode(), data[max(0, idx - 40):idx + 40]))
print("=" * 78)
