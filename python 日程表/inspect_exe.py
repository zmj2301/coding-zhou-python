# -*- coding: utf-8 -*-
"""解剖 PyInstaller onefile 包：确认内置的 Python / Qt 绑定 / API set DLL 情况。"""
import os
import re
import sys

from PyInstaller.archive.readers import CArchiveReader

TARGETS = [
    r"dist\日程表_Win7.exe",
    r"win7_dist\日程表_Win7.exe",
    r"..\ScheduleMate_Win7\日程表_Win7.exe",
]

PY_RE = re.compile(r"^python3\d*\.dll$", re.I)
QT_RE = re.compile(r"^Qt\d*Core\.dll$", re.I)
CORE_API_RE = re.compile(r"^api-ms-win-core-[\w.-]*\.dll$", re.I)
CRT_API_RE = re.compile(r"^api-ms-win-crt-[\w.-]*\.dll$", re.I)

for target in TARGETS:
    path = os.path.abspath(target)
    print("=" * 78)
    print(path)
    if not os.path.exists(path):
        print("  [不存在]")
        continue
    print("  大小: %.2f MB" % (os.path.getsize(path) / 1024.0 / 1024.0))
    try:
        r = CArchiveReader(path)
        names = [str(n) for n in r.toc]
    except Exception as e:
        print("  [读取失败] %s: %s" % (type(e).__name__, e))
        continue

    base = [os.path.basename(n) for n in names]
    pys = sorted({b for b in base if PY_RE.match(b)})
    qts = sorted({b for b in base if QT_RE.match(b)})
    core_api = sorted({b for b in base if CORE_API_RE.match(b)})
    crt_api = sorted({b for b in base if CRT_API_RE.match(b)})

    pyside6 = sum(1 for n in names if "PySide6" in n)
    pyside2 = sum(1 for n in names if "PySide2" in n)

    print("  条目总数        : %d" % len(names))
    print("  python 运行时   : %s" % (", ".join(pys) or "(无)"))
    print("  Qt 核心库       : %s" % (", ".join(qts) or "(无)"))
    print("  PySide6 条目    : %d" % pyside6)
    print("  PySide2 条目    : %d" % pyside2)
    print("  api-ms-win-core : %d 个 %s" % (len(core_api), core_api[:4]))
    print("  api-ms-win-crt  : %d 个" % len(crt_api))

    if pyside6 and not pyside2:
        verdict = "可用（PySide6 完整）"
    elif pyside2 and not pyside6:
        verdict = "不可用（源码需要 PySide6，包内只有 PySide2）"
    elif not pyside6 and not pyside2:
        verdict = "不可用（两种 Qt 绑定都没有）"
    else:
        verdict = "混杂，需人工确认"
    print("  >>> 判定: %s" % verdict)
print("=" * 78)
