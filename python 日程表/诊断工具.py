# -*- coding: utf-8 -*-
"""日程表 —— 配置诊断工具（独立 exe，双击即可运行）

为什么需要这个工具
------------------
终端用户反馈「改了透明度/文字大小，重启后又变回默认」，可能的原因有好几种：
配置根本没写到、写到别的目录了、写的时候被覆盖了、目录没权限、文件损坏……
光靠描述无法判断到底是哪一种。这个工具把该查的东西一次性全查清楚，
生成一份可以直接发给我们的文本报告。

它做什么
--------
1. 环境信息：Windows 版本、程序实际位置、是否以管理员运行、exe 是否被移动过
2. 配置定位：到底应该在哪个目录、那个目录能不能写、文件在不在
3. 配置内容：user_data.json 的**完整原文**（这是最关键的证据）
4. 读到的值：程序启动时会把哪些设置读进去（透明度/字号/框高等）
5. 错误日志：APPDATA\\日程表\\error.log 的内容（程序自己记的写盘失败）
6. 旧配置：exe 目录里是否还残留老版本配置（迁移没搬成功就是它）
7. Excel 数据：配置里记的数据文件在不在（找不到会导致「没有事件」）
8. 开机自启：注册表里有没有、指向的路径还在不在
9. 可写性实测：当场建一个临时文件再删掉，验证权限

用法
----
双击运行 → 自动生成「诊断报告_YYYYMMDD_HHMMSS.txt」在 exe 同目录 →
把这个 txt 发回来即可。不会修改你的任何设置。
"""

import os
import sys
import json
import time
import shutil
import platform
import tempfile

VERSION = "2026.10.02 诊断版"
USER_SETTINGS_FILE = "user_data.json"
DEFAULT_USER_SETTINGS = {
    'ai_enable': False,
    'event_length': 560,
    'window_opacity': 1.0,
    'icon_opacity': 1.0,
    'text_size': 14,
    'icon_size': 100,
    'auto_fit_box': True,
}
AUTOSTART_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_VALUE_NAME = "日程表_Win7"

OUT = []


def w(line=""):
    OUT.append(str(line))


def sec(title):
    w("")
    w("=" * 66)
    w("  " + title)
    w("=" * 66)


def app_dir():
    """exe 所在目录（与主程序 get_app_path 保持一致的思路）。"""
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
        internal = os.path.join(base, '_internal')
        if os.path.isdir(internal):
            return internal
        return base
    return os.getcwd()


def settings_dir():
    """配置目录：与主程序完全一致的规则（%APPDATA%\\日程表）。"""
    base = os.environ.get('APPDATA') or os.path.expanduser('~')
    return os.path.join(base, '日程表')


def is_admin():
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def test_writable(path):
    """实测目录能不能写：建临时文件 → 写内容 → 删掉，返回 (结果, 说明)。"""
    probe = os.path.join(path, "_诊断临时文件.tmp")
    try:
        with open(probe, 'w', encoding='utf-8') as f:
            f.write("ok")
        with open(probe, 'r', encoding='utf-8') as f:
            f.read()
        os.remove(probe)
        return True, "可以正常写入"
    except Exception as e:
        try:
            if os.path.exists(probe):
                os.remove(probe)
        except Exception:
            pass
        return False, "写入失败：%s" % e


def main():
    # 报告内容必须在每次运行时清空。OUT 是模块级列表，不清的话第二次调用
    # 会把上一次的报告整段接在后面（同一进程里重复运行时就会出现
    # 「明明配置正常，报告里却有一堆【严重】告警」这种假象）。
    del OUT[:]

    exe_dir = app_dir()
    cfg_dir = settings_dir()
    cfg_file = os.path.join(cfg_dir, USER_SETTINGS_FILE)
    log_file = os.path.join(cfg_dir, 'error.log')
    legacy_file = os.path.join(exe_dir, USER_SETTINGS_FILE)

    w("日程表 配置诊断报告")
    w("生成时间：%s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    w("工具版本：%s" % VERSION)
    w("")
    w("这份报告只读取信息，不会修改任何设置，可以放心发给技术支持。")

    # ---------------------------------------------------------------- 1 环境
    sec("1. 运行环境")
    w("Windows 版本      ：%s" % platform.platform())
    try:
        # win32_ver() 返回 (release, version, csd, ptype)，版本号在 [1]
        w("系统版本号        ：%s（内部版本 %s）" % (
            platform.win32_ver()[1], platform.win32_ver()[2] or "无 SP"))
    except Exception:
        w("系统版本号        ：(读取失败)")
    w("系统架构          ：%s" % (platform.architecture()[0]))
    w("当前登录用户      ：%s" % os.environ.get('USERNAME', '(未知)'))
    w("是否管理员运行    ：%s" % ("是" if is_admin() else "否（普通用户，程序会写到自己的 APPDATA）"))
    w("程序是否打包成 exe：%s" % ("是" if getattr(sys, 'frozen', False) else "否（开发模式）"))
    w("exe 实际路径      ：%s" % os.path.abspath(sys.executable))
    w("exe 所在目录      ：%s" % exe_dir)
    w("目录是否存在      ：%s" % ("是" if os.path.isdir(exe_dir) else "否 ← 异常！"))
    tmp_meipass = getattr(sys, '_MEIPASS', None)
    w("单文件解压临时目录：%s" % (tmp_meipass if tmp_meipass else "(非单文件模式)"))

    # ------------------------------------------------------------ 2 配置目录
    sec("2. 配置目录（设置应该存这里）")
    w("应使用的目录      ：%s" % cfg_dir)
    w("配置目录是否存在  ：%s" % ("是" if os.path.isdir(cfg_dir) else "否 ← 程序会自动创建，若一直是「否」说明创建失败"))
    ok, msg = test_writable(cfg_dir) if os.path.isdir(cfg_dir) else (False, "目录不存在，无法测试")
    w("目录可写性实测    ：%s（%s）" % ("通过" if ok else "失败", msg))
    w("APPDATA 环境变量  ：%s" % (os.environ.get('APPDATA') or "(空!)"))
    w("")
    w("说明：程序从这一版开始，配置固定存到上面这个目录（不再存 exe 目录），")
    w("      这样 exe 换位置、被重新解压、放在 Program Files 都丢不了设置。")

    # ------------------------------------------------------------ 3 配置内容
    sec("3. 配置文件内容（最关键的证据）")
    w("配置文件路径      ：%s" % cfg_file)
    w("文件是否存在      ：%s" % ("是" if os.path.exists(cfg_file) else "否 ← 从来没保存成功过！"))
    raw = None
    if os.path.exists(cfg_file):
        try:
            with open(cfg_file, 'r', encoding='utf-8') as f:
                raw = f.read()
            info = os.stat(cfg_file)
            w("文件大小          ：%d 字节" % info.st_size)
            w("最后修改时间      ：%s" % time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(info.st_mtime)))
            w("最后写入时间距今  ：%.1f 小时" % ((time.time() - info.st_mtime) / 3600.0))
        except Exception as e:
            w("读取失败          ：%s ← 文件可能已损坏" % e)
        w("")
        w("---- user_data.json 原文开始 ----")
        if raw is None:
            w("(读取失败，无内容)")
        else:
            w(raw)
        w("---- user_data.json 原文结束 ----")
    else:
        w("")
        w("（文件不存在 —— 这就是「改了设置重启就丢」的直接原因：")
        w("  程序根本没把设置写下来，或写到别的地方去了。）")

    # ------------------------------------------------------------ 4 读到的值
    sec("4. 程序启动时会读到的设置值")
    data = dict(DEFAULT_USER_SETTINGS)
    if raw:
        try:
            loaded = json.loads(raw)
            if isinstance(loaded, dict):
                data.update(loaded)
        except Exception as e:
            w("解析 JSON 失败    ：%s ← 配置格式坏了，程序会全部回落到默认值" % e)
    else:
        w("（无配置文件，以下都是程序内置默认值 —— 这就是你看到的「默认状态」）")
    w("")
    # 单项取值全部包起来：配置里某个字段是脏数据（比如透明度写成了
    # "abc"）时，诊断工具不能自己也跟着崩 —— 崩了就拿不到任何报告。
    # 这里不用 %-14s 做对齐：中文按字符计宽，固定宽度会排出错位的表格。
    def show(label, key, fmt):
        try:
            v = data.get(key)
        except Exception as e:
            v = "读取异常(%s)" % e
        try:
            w("  %s：%s" % (label, fmt(v)))
        except Exception as e:
            w("  %s：显示失败（值=%r，%s）" % (label, v, e))

    def pct(v):
        return "%.0f%%" % (float(v if v is not None else 1.0) * 100)

    show("桌面图标透明度  ", 'window_opacity', pct)
    show("最小化图标透明度", 'icon_opacity', pct)
    show("文字大小        ", 'text_size', lambda v: "%s px" % v)
    show("图标大小        ", 'icon_size', lambda v: "%s px" % v)
    show("事件框长度      ", 'event_length', lambda v: "%s px" % v)
    w("  白框自动加高    ：%s" % ("开（内容多会自动撑高）" if data.get('auto_fit_box', True) else "关（严格按你设的高度）"))

    # ------------------------------------------------------------ 5 错误日志
    sec("5. 程序自己记的错误（error.log）")
    w("日志路径          ：%s" % log_file)
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.read().strip().split('\n')
            w("共 %d 条记录（最后 30 条）：" % len(lines))
            for ln in lines[-30:]:
                w("  " + ln)
        except Exception as e:
            w("读取失败：%s" % e)
    else:
        w("没有错误日志 —— 说明程序没遇到过写盘失败。")
        w("（如果设置确实丢了但这里没记录，更可能是「写到了别处」或「被覆盖」）")

    # ------------------------------------------------------------ 6 旧配置
    sec("6. exe 目录里的旧配置（老版本残留）")
    w("旧配置路径        ：%s" % legacy_file)
    w("是否存在          ：%s" % ("是" if os.path.exists(legacy_file) else "否（正常）"))
    if os.path.exists(legacy_file):
        try:
            with open(legacy_file, 'r', encoding='utf-8') as f:
                legacy_raw = f.read()
            info = os.stat(legacy_file)
            w("最后修改时间      ：%s（%.1f 小时前）" % (
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info.st_mtime)),
                (time.time() - info.st_mtime) / 3600.0))
            w("")
            w("---- 旧配置原文开始 ----")
            w(legacy_raw)
            w("---- 旧配置原文结束 ----")
            w("")
            if os.path.exists(cfg_file):
                w("★ 注意：新旧两处都有配置。程序读的是上面【第 3 节】那个")
                w("  （APPDATA 里的新位置），这个旧的会被忽略 ——")
                w("  如果新位置的内容不是你想要的，说明之前保存被覆盖过。")
            else:
                w("★ 注意：新位置没有配置、只有这个旧的。正常情况下程序第一次")
                w("  启动就会把它搬过去；如果没有，请把本报告发回给我们。")
        except Exception as e:
            w("读取失败：%s" % e)

    # ------------------------------------------------------------ 7 Excel 数据
    sec("7. 事件数据文件（Excel）")
    user_data = data.get('user_data')
    if isinstance(user_data, str):
        user_data = [user_data]
    if not isinstance(user_data, (list, tuple)):
        # 脏数据（数字/嵌套字典等）：照实报出来，别让工具自己崩
        w("配置里的数据文件字段类型异常：%r" % (user_data,))
        w("这会让程序读不到事件。请在主窗口右键 → 打开日历 → 重新选择 Excel 文件。")
        user_data = []
    if not user_data:
        w("配置里没有记录数据文件 ← 程序找不到事件，界面会是空的")
        w("请在主窗口右键 → 打开日历 → 重新选择你的 Excel 文件")
    else:
        for p in user_data:
            ap = os.path.abspath(str(p))
            w("数据文件          ：%s" % ap)
            w("  是否存在        ：%s" % ("是" if os.path.exists(ap) else "否 ← 文件被移动/改名/删除了！"))
            if os.path.exists(ap):
                try:
                    info = os.stat(ap)
                    w("  大小/修改时间   ：%.1f KB / %s" % (
                        info.st_size / 1024.0,
                        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info.st_mtime))))
                except Exception:
                    pass

    # ------------------------------------------------------------ 8 开机自启
    sec("8. 开机自动启动")
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_REG_PATH, 0, winreg.KEY_READ) as key:
            try:
                value, _ = winreg.QueryValueEx(key, AUTOSTART_VALUE_NAME)
                w("已开启            ：是")
                w("注册表指向        ：%s" % value)
                target = str(value).strip('"').split('" "')[0].split('"')[0]
                w("指向的文件是否存在：%s" % ("是" if os.path.exists(target) else "否 ← 路径失效！"))
                if not os.path.exists(target):
                    w("★ 程序被移动过位置。开机自启还指着旧路径，开机后不会启动；")
                    w("  请重新勾选一次「开机自动启动」即可修正。")
            except FileNotFoundError:
                w("已开启            ：否")
    except Exception as e:
        w("读取注册表失败    ：%s" % e)

    # ------------------------------------------------------------ 9 结论提示
    sec("9. 初步结论（供参考，以第 3 节内容为准）")
    verdicts = []
    if not os.path.exists(cfg_file):
        verdicts.append("【严重】配置文件根本不存在 —— 设置从未成功保存。")
    else:
        # 解析必须放在 try 里：配置文件损坏恰恰是最需要诊断的场景，
        # 这里如果自己先崩了，用户就什么报告都拿不到了。
        parsed = None
        parse_err = None
        if raw and raw.strip():
            try:
                parsed = json.loads(raw)
            except Exception as e:
                parse_err = str(e)
        if parse_err is not None:
            verdicts.append("【严重】配置文件 JSON 解析失败：%s" % parse_err)
            verdicts.append("    程序会把全部设置回落到默认值 —— 这就是「重启就变默认」的原因。")
            verdicts.append("    修复办法：关闭程序后删除该文件，重新打开程序再设置一次即可。")
        elif not isinstance(parsed, dict):
            verdicts.append("【严重】配置文件格式不是有效的 JSON 对象，程序会全部用默认值。")
        elif not os.path.exists(log_file):
            verdicts.append("配置文件存在且格式正常，但内容不是你想要的值 ——")
            verdicts.append("    说明有别的程序/旧版本在覆盖它（历史上日历选文件时会整份覆盖）。")
    if ok is False:
        verdicts.append("【严重】配置目录不可写 —— 任何设置都存不下来。")
    if os.path.exists(legacy_file) and not os.path.exists(cfg_file):
        verdicts.append("旧配置在 exe 目录、新配置在 APPDATA，说明自动搬迁没生效。")
    if not verdicts:
        w("没有发现明显异常。如果设置仍然丢失，请把本报告完整发回，")
        w("我们会根据第 3 节的原文继续定位。")
    for v in verdicts:
        w(v)
    w("")
    w("=" * 66)
    w("  报告结束 —— 请把本文件发给技术支持")
    w("=" * 66)

    text = '\n'.join(OUT)
    # 报告写到 exe 同目录（用户最容易找到的地方）；失败则退回桌面
    stamp = time.strftime("%Y%m%d_%H%M%S")
    targets = [
        os.path.join(exe_dir, "诊断报告_%s.txt" % stamp),
        os.path.join(os.path.expanduser("~"), "Desktop", "诊断报告_%s.txt" % stamp),
        os.path.join(tempfile.gettempdir(), "诊断报告_%s.txt" % stamp),
    ]
    saved = None
    for t in targets:
        try:
            os.makedirs(os.path.dirname(t), exist_ok=True)
            with open(t, 'w', encoding='utf-8-sig') as f:
                f.write(text)
            saved = t
            break
        except Exception:
            continue
    return text, saved


if __name__ == '__main__':
    try:
        text, saved = main()
        print(text)
        print("")
        if saved:
            print("报告已保存到：%s" % saved)
        else:
            print("报告保存失败，请手动记录上面的内容。")
    except Exception as e:
        print("诊断工具运行出错：%s" % e)
        import traceback
        traceback.print_exc()
    # 双击运行时给用户留时间看结果
    if getattr(sys, 'frozen', False):
        try:
            input("\n按回车键关闭...")
        except Exception:
            time.sleep(20)
