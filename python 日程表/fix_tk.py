# -*- coding: utf-8 -*-
"""从用户已验证可用的包里，原样提取 Tk 8.6.9 脚本数据，修复 C:\\py38 的 Tk 版本冲突。

背景：C:\\py38 的 Tcl 运行时是 8.6.9，但之前会话从 D:\\Python39 拷进来的 tk 脚本是
8.6.12，运行时报 `version conflict for package "Tk": have 8.6.9, need exactly 8.6.12`。
这里从 ScheduleMate_Win7\\日程表_Win7.exe（用户实际在用、日历窗口正常）里提取配套的
8.6.9 tk 数据。
"""
import os

from PyInstaller.archive.readers import CArchiveReader

EXE = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   "..", "ScheduleMate_Win7", "日程表_Win7.exe"))
DEST = r"C:\py38\tcl\tk8.6"

reader = CArchiveReader(EXE)
names = [str(n) for n in reader.toc]

extracted, skipped = 0, []
for name in names:
    norm = name.replace("/", "\\")
    if not (norm.lower().startswith("tk\\") or norm.lower() == "tk"):
        continue
    rel = norm[3:] if len(norm) > 3 else ""
    if not rel:
        continue
    try:
        data = reader.extract(name)
    except Exception as e:
        skipped.append((name, "提取失败 %s" % e))
        continue
    if isinstance(data, tuple):
        data = data[0]
    if not isinstance(data, (bytes, bytearray)):
        skipped.append((name, "非字节类型 %s" % type(data)))
        continue

    out = os.path.join(DEST, rel.replace("\\", os.sep))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        f.write(data)
    extracted += 1

print("从 %s" % EXE)
print("提取 %d 个文件 -> %s" % (extracted, DEST))
if skipped:
    print("跳过 %d 个:" % len(skipped))
    for n, why in skipped[:10]:
        print("   ", n, why)

# 校验关键文件
key = os.path.join(DEST, "tk.tcl")
with open(key, "rb") as f:
    head = f.read(600)
import re
m = re.search(rb'package require -exact Tk\s+([0-9.]+)', head)
print("tk.tcl 要求 Tk 版本:", m.group(1).decode() if m else "?")
print("ttk 目录存在:", os.path.isdir(os.path.join(DEST, "ttk")))
