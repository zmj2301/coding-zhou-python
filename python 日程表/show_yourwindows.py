import sys
from typing import Any

# ---------------------------------------------------------------------------
# Qt 绑定兼容层
#
# 程序需要同时支持两种运行环境：
#   * PySide6 / Qt6 —— 需要 Python 3.9+，且【不支持 Windows 7】（Qt6 官方要求 Win10 1809+）
#   * PySide2 / Qt5 —— 配 Python 3.8，可以在 Windows 7 上运行（Win7 分发版走这条路）
#
# 两者的 API 差异极小，只有「鼠标事件全局坐标」和「exec 命名」两处，
# 所以这里按可用性自动选择绑定，其余代码保持一份。
# ---------------------------------------------------------------------------
try:
    from PySide6.QtWidgets import (QApplication, QMainWindow, QMenu, QVBoxLayout, QHBoxLayout,
                                   QWidget, QTextEdit, QLabel, QScrollArea, QFrame, QPushButton,
                                   QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QMessageBox, QSizePolicy,
                                   QSizeGrip, QLayout, QDialog)
    from PySide6.QtCore import (QSize, Qt, QPoint, QRectF, QTimer, QDateTime,
                                Signal, QPropertyAnimation, QEasingCurve, QEvent)
    from PySide6.QtGui import QIcon, QPixmap, QFont, QPainter, QColor, QPen, QLinearGradient, QTextDocument
    QT_BINDING = "PySide6"
except ImportError:  # pragma: no cover - 取决于打包/运行环境
    from PySide2.QtWidgets import (QApplication, QMainWindow, QMenu, QVBoxLayout, QHBoxLayout,
                                   QWidget, QTextEdit, QLabel, QScrollArea, QFrame, QPushButton,
                                   QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QMessageBox, QSizePolicy,
                                   QSizeGrip, QLayout, QDialog)
    from PySide2.QtCore import (QSize, Qt, QPoint, QRectF, QTimer, QDateTime,
                                Signal, QPropertyAnimation, QEasingCurve, QEvent)
    from PySide2.QtGui import QIcon, QPixmap, QFont, QPainter, QColor, QPen, QLinearGradient, QTextDocument
    QT_BINDING = "PySide2"

import os
import random
import time
import traceback
import tkinter as tk
import json
import urllib.request
import urllib.error
import ssl
from tkinter import ttk
from tkinter import messagebox


def _global_pos(event):
    """取鼠标事件的屏幕坐标。

    Qt6: event.globalPosition() 返回 QPointF，需要 .toPoint()
    Qt5: event.globalPos() 直接返回 QPoint
    """
    getter = getattr(event, "globalPosition", None)
    if getter is not None:
        try:
            return getter().toPoint()
        except AttributeError:
            return getter()
    return event.globalPos()


def _exec_menu(menu, pos):
    """QMenu 弹出：Qt6 叫 exec()，Qt5 叫 exec_()。"""
    fn = getattr(menu, "exec", None) or getattr(menu, "exec_", None)
    return fn(pos)


def get_app_path():
    if getattr(sys, 'frozen', False):
        # 单文件模式或单目录模式
        base_path = os.path.dirname(sys.executable)
        # 检查是否是单目录模式（如果存在_internal目录，则使用_internal目录）
        internal_path = os.path.join(base_path, '_internal')
        if os.path.exists(internal_path) and os.path.isdir(internal_path):
            return internal_path
        return base_path
    # 开发模式
    return os.getcwd()


def get_assets_path():
    """只读资源（如 img 图标）目录：
    单文件模式在临时解压目录 sys._MEIPASS，单目录模式在 _internal，开发模式为当前目录。"""
    if getattr(sys, 'frozen', False):
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            return meipass
    return get_app_path()


def get_settings_dir():
    """配置文件（user_data.json / error.log）的目录：固定用 %APPDATA%\\日程表。

    原来配置存在 exe 所在目录，实际场景下会丢，终端用户反馈
    「每次开机都要重新调透明度/文字大小」就是这个原因：
      * exe 放在 C:\\Program Files 等目录时没有管理员权限，写不进去（且是静默失败）；
      * exe 换个目录 / 重新解压再运行，配置就"跟丢"，表现为全部回到默认；
      * 部分安全软件会盯着 exe 目录写文件。
    改成固定在当前用户的 APPDATA 下：一定可写、与 exe 位置无关，
    重装 / 挪动 exe 都不会丢配置。"""
    base = os.environ.get('APPDATA') or os.path.expanduser('~')
    d = os.path.join(base, '日程表')
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        d = get_app_path()
    return d


def migrate_legacy_settings(legacy_dir):
    """老版本把 user_data.json 存在 exe 目录；若新目录还没有配置而旧目录有，
    自动把旧配置搬过来 —— 老用户已调好的透明度/字号等设置不丢。"""
    try:
        new_path = os.path.join(get_settings_dir(), USER_SETTINGS_FILE)
        old_path = os.path.join(legacy_dir, USER_SETTINGS_FILE)
        if os.path.exists(new_path) or not os.path.exists(old_path):
            return
        with open(old_path, 'rb') as f:
            data = f.read()
        with open(new_path, 'wb') as f:
            f.write(data)
        print("已迁移旧配置:", old_path, "->", new_path)
    except Exception as e:
        print("迁移旧配置失败:", e)
        _log_error("迁移旧配置失败: %s" % e)


def _log_error(msg):
    """把错误追加到 APPDATA 下的 error.log —— 打包成无窗口 exe 后
    print 是看不见的，配置/迁移写失败时必须留下可排查的痕迹。"""
    try:
        with open(os.path.join(get_settings_dir(), 'error.log'), 'a', encoding='utf-8') as f:
            f.write(time.strftime('%Y-%m-%d %H:%M:%S ') + str(msg) + '\n')
    except Exception:
        pass


def ensure_tk_error_hook():
    """让 Tkinter 回调里的异常可见。

    Tkinter 默认把按钮回调里抛出的异常交给 root.report_callback_exception，
    而它只往 stderr 打印。程序打包成 GUI（console=False）后 stderr 无处可见，
    于是回调里的任何 bug 都表现为「点了按钮没反应」——极难排查。
    这里接管它：弹窗提示 + 追加写入 error.log。
    """
    try:
        root = getattr(tk, "_default_root", None)
        if root is None or getattr(root, "_schedule_err_hook", False):
            return

        def _report(exc, val, tb):
            detail = "".join(traceback.format_exception(exc, val, tb))
            print(detail)
            try:
                with open(os.path.join(get_settings_dir(), "error.log"), "a", encoding="utf-8") as f:
                    f.write("[%s] %s\n%s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), val, detail))
            except Exception:
                pass
            try:
                messagebox.showerror("操作未完成", "程序内部出错：%s\n\n详细信息已写入 error.log" % val)
            except Exception:
                pass

        root.report_callback_exception = _report
        root._schedule_err_hook = True
    except Exception:
        pass


# ------------------------------------------------------------- Qt / Tk 事件泵
# 本程序有两套事件循环：Qt 的 app.exec() 是主循环，而 Tk 的 cal_window.mainloop()
# 是在 Qt 回调里「嵌套」启动的（点开日历窗口时）。嵌套期间 Qt 的事件循环被完全
# 阻塞，所以从 Tk 回调里调用 Qt 的 setWindowOpacity / setGraphicsEffect 之后，
# 窗口不会立刻重绘，用户看到的是「拖了滑块没反应」。
# 下面这个函数在处理完这类调用后手动泵一次 Qt 事件队列，使改动立即可见。
_pumping_qt = False


def _pump_qt_events():
    global _pumping_qt
    if _pumping_qt:
        return
    _pumping_qt = True
    try:
        app = QApplication.instance()
        if app is not None:
            app.processEvents()
    except Exception:
        pass
    finally:
        _pumping_qt = False


# ---------------------------------------------------------------- 开机自启动
# 用 HKCU\...\Run 注册表项实现：不需要管理员权限，也不会像启动文件夹那样
# 因为快捷方式被移动/改名而失效。

AUTOSTART_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_VALUE_NAME = "ScheduleMate"


def _startup_command():
    """写入 Run 项的命令行：打包后直接指向 exe，开发模式则带上脚本路径。"""
    exe = os.path.abspath(sys.executable)
    if getattr(sys, 'frozen', False):
        return '"%s"' % exe
    return '"%s" "%s"' % (exe, os.path.abspath(__file__))


def is_autostart_enabled():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_REG_PATH, 0, winreg.KEY_READ) as key:
            try:
                value, _ = winreg.QueryValueEx(key, AUTOSTART_VALUE_NAME)
                return bool(value)
            except FileNotFoundError:
                return False
    except Exception as e:
        print("读取开机自启动设置失败:", e)
        return False


def set_autostart(enable):
    """开启/关闭开机自动启动。返回 (是否成功, 错误信息)。

    **写完必须读回验证**。实测有些环境（安全软件 / 沙箱）下 SetValueEx
    既不抛异常也不报错 —— 函数返回「成功」，但注册表里根本没有那个值。
    直接返回成功会让用户以为勾上了，开机时却什么都没发生。
    """
    try:
        import winreg
        # 只申请「查询 + 写入」这两项权限，不用 KEY_ALL_ACCESS：
        # 权限给得越大越容易被安全软件的启动项防护判定为可疑而拒绝。
        access = winreg.KEY_QUERY_VALUE | winreg.KEY_SET_VALUE
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_REG_PATH, 0, access) as key:
            if enable:
                want = _startup_command()
                winreg.SetValueEx(key, AUTOSTART_VALUE_NAME, 0, winreg.REG_SZ, want)
                # 读回确认真的写进去了（关键：不能只信 SetValueEx 的返回值 ——
                # 实测有些环境里它会静默丢弃写入，既不报错也不生效）
                try:
                    got, _ = winreg.QueryValueEx(key, AUTOSTART_VALUE_NAME)
                except FileNotFoundError:
                    return False, ("写入没有生效（写入后读回找不到该值）——"
                                   "通常是安全软件的启动项防护拦下了，"
                                   "请到安全软件里允许本程序后重试")
                if str(got).strip() != str(want).strip():
                    return False, "写入内容与预期不符，请重试"
            else:
                try:
                    winreg.DeleteValue(key, AUTOSTART_VALUE_NAME)
                except FileNotFoundError:
                    pass
        return True, ""
    except Exception as e:
        print("设置开机自启动失败:", e)
        return False, str(e)


# ---------------------------------------------------------------- 用户设置读写

USER_SETTINGS_FILE = "user_data.json"

DEFAULT_USER_SETTINGS = {
    # AI 解析已从 Win7 版移除：打包环境(C:\py38)没有 zai 模块，
    # 调用会直接抛 ImportError。这里固定为 False，相关代码不再执行。
    'ai_enable': False,
    # 默认 560，与 initUI 原本写死的值一致，保证首次使用的观感不变
    'event_length': 560,
    'window_opacity': 1.0,   # 桌面图标（主窗口整体）透明度
    'icon_opacity': 1.0,     # 最小化图标（窗口内那张图）透明度
    'text_size': 14,         # 主窗口文字大小（今日事件正文；倒计时在此基础上 +4）
    'icon_size': 100,        # 主窗口里那张图标的边长（px）。原为写死 150，偏大占地方
    # 白框是否随内容自动加高（True=事件多时自动撑高到全部显示，不用滚动）。
    # 用户手动拖小蓝块/拖滑块调小框高后，会自动切成 False（手动优先），
    # 避免「刚调小、正文一变（倒计时每秒变）框又自己弹高到显示全部」。
    'auto_fit_box': True,
    # 开机自启位置（屏幕相对坐标，0.0 ~ 1.0）。None 表示没保存过 —— 启动时
    # Qt 会用默认位置；保存后下次启动按此相对位置恢复（跨分辨率仍可按比例定位）。
    'pos_rel_x': None,
    'pos_rel_y': None,
}

# 文字大小的允许区间，防止滑块拖到极端值导致界面不可用
TEXT_SIZE_MIN, TEXT_SIZE_MAX = 9, 28

# 图标大小的允许区间
ICON_SIZE_MIN, ICON_SIZE_MAX = 48, 200

# ── 设置窗口样式令牌（紧凑卡片版）────────────────────────────
# 颜色（统一一套，改一处全局生效）
_SET_COLOR = {
    'window_bg':   '#eef1f6',   # 窗口底色（浅灰蓝）
    'card_bg':     '#ffffff',   # 卡片底色（纯白）
    'title':       '#1f2937',   # 卡片标题（深灰黑）
    'accent':      '#4f6ef7',   # 主色（蓝紫）
    'accent_active': '#3d5be0', # 主色 hover
    'text':        '#374151',   # 正文（深灰）
    'text_dim':    '#8a94a6',   # 次要文字（浅灰）
    'hint':        '#4f6ef7',   # 值提示（滑块右边的数值）
    'border':      '#e3e7ef',   # 卡片分隔线
    'track':       '#dbe1ec',   # 滑块轨道底色
}
# 字体
_SET_FONT = {
    'header': ('Microsoft YaHei', 14, 'bold'),   # 窗口顶部标题
    'title':  ('Microsoft YaHei', 11, 'bold'),   # 卡片标题
    'label':  ('Microsoft YaHei', 9),            # 卡片内标签
    'value':  ('Microsoft YaHei', 9, 'bold'),     # 数值提示
    'btn':    ('Microsoft YaHei', 9, 'bold'),     # 按钮
}
# 紧凑间距（改这些值就能全局松/紧）
_SET_SPACE = {
    'card_pad':    (12, 10),   # 卡片内边距 (x, y)
    'card_margin': (12, 6),    # 卡片外边距 (x, y)
    'title_sep':   (0, 4),     # 卡片标题 → 分隔线
    'sep_first':   (0, 6),     # 分隔线 → 首行控件
    'row_pady':    2,          # 每行控件上下间距
    'slider_gap':  6,          # 标签到滑块的水平间距
    'header_pad':  (12, 10),   # 窗口顶部标题栏
    'btn_pad':     (12, 5),    # 主按钮 padding
}


def _apply_settings_styles(style):
    """给设置窗口用的 ttk.Style 一次性配置。

    只给 ttk 组件配样式，Tk 组件（如 Canvas/Frame）仍用 bg 参数直接设色。
    不影响日历窗口自己的样式配置（它在 set_calendar 里会单独 apply）。
    """
    c = _SET_COLOR
    f = _SET_FONT
    s = _SET_SPACE

    style.theme_use("clam")

    # 全局默认
    style.configure(".",
                    background=c['window_bg'],
                    foreground=c['text'],
                    font=f['label'])

    # 卡片容器
    style.configure("Card.TFrame",
                    background=c['card_bg'], relief="flat")

    # 卡片标题（深灰大号）
    style.configure("CardTitle.TLabel",
                    background=c['card_bg'],
                    foreground=c['title'],
                    font=f['title'])

    # 卡片内分隔线
    style.configure("CardSep.TFrame",
                    background=c['border'], height=1)

    # 设置项标签（卡片内，普通深灰）
    style.configure("Setting.TLabel",
                    background=c['card_bg'],
                    foreground=c['text'],
                    font=f['label'])

    # 值提示（滑块右边的 "100%" / "14 px"）
    style.configure("Value.TLabel",
                    background=c['card_bg'],
                    foreground=c['hint'],
                    font=f['value'])

    # 滑块（轨道底色 + 白色圆柄）
    style.configure("Horizontal.TScale",
                    background=c['card_bg'],
                    troughcolor=c['track'],
                    sliderthickness=14,
                    borderwidth=0)

    # 勾选框
    style.configure("TCheckbutton",
                    background=c['card_bg'],
                    foreground=c['text'],
                    font=f['label'])
    style.map("TCheckbutton",
              background=[("active", c['card_bg'])])

    # 主按钮（蓝底白字）
    style.configure("Primary.TButton",
                    background=c['accent'],
                    foreground='#ffffff',
                    font=f['btn'],
                    padding=s['btn_pad'],
                    borderwidth=0)
    style.map("Primary.TButton",
              background=[("active", c['accent_active']),
                          ("pressed", '#2d4bcf')])


def _clamp_text_size(value):
    """把文字大小限制在允许区间内，非法值（None/字符串/超范围）一律回落默认值。"""
    try:
        size = int(value)
    except (TypeError, ValueError):
        return DEFAULT_USER_SETTINGS['text_size']
    return max(TEXT_SIZE_MIN, min(TEXT_SIZE_MAX, size))


def _clamp_icon_size(value):
    """把图标边长限制在允许区间内，非法值一律回落默认值。"""
    try:
        size = int(value)
    except (TypeError, ValueError):
        return DEFAULT_USER_SETTINGS['icon_size']
    return max(ICON_SIZE_MIN, min(ICON_SIZE_MAX, size))


# ── 日历窗口样式令牌（和设置窗口同色系，整个应用统一）─────────
_CAL_COLOR = {
    'window_bg':      '#eef1f6',
    'card_bg':        '#ffffff',
    'card_border':    '#e3e7ef',
    'title':          '#1f2937',
    'accent':         '#4f6ef7',
    'accent_active':   '#3d5be0',
    'accent_soft':    '#eef0ff',
    'text':           '#374151',
    'text_dim':       '#8a94a6',
    'today_bg':       '#4f6ef7',
    'today_fg':       '#ffffff',
    'has_event_bg':   '#fef3c7',
    'has_event_fg':   '#92400e',
    'weekday_bg':     '#f8fafc',
    'weekday_fg':     '#8a94a6',
}
_CAL_FONT = {
    'win_title':  ('Microsoft YaHei', 13, 'bold'),
    'card_title': ('Microsoft YaHei', 11, 'bold'),
    'label':      ('Microsoft YaHei', 9),
    'btn':        ('Microsoft YaHei', 9, 'bold'),
    'date_num':   ('Microsoft YaHei', 11, 'bold'),
    'event':      ('Microsoft YaHei', 10),
}
_CAL_SPACE = {
    'card_pad':    (12, 10),
    'card_margin': 10,
    'header_pad':  (14, 10),
    'control_gap': 4,
    'date_pad':    6,     # 日期格子上下内边距
}


def _apply_calendar_styles(style):
    """日历主窗口用的 ttk.Style 配置。

    和 _apply_settings_styles 分开，避免互相覆盖 —— 不同窗口有不同用途。
    """
    c = _CAL_COLOR
    f = _CAL_FONT
    s = _CAL_SPACE

    style.theme_use("clam")

    style.configure(".",
                    background=c['window_bg'],
                    foreground=c['text'],
                    font=f['label'])

    # 卡片容器
    style.configure("Card.TFrame",
                    background=c['card_bg'], relief="flat")

    # 卡片标题（深灰大号）
    style.configure("CardTitle.TLabel",
                    background=c['card_bg'],
                    foreground=c['title'],
                    font=f['card_title'])

    # 窗口顶部大标题
    style.configure("WinTitle.TLabel",
                    background=c['window_bg'],
                    foreground=c['accent'],
                    font=f['win_title'])

    # 主按钮（蓝底白字）
    style.configure("Primary.TButton",
                    background=c['accent'],
                    foreground='#ffffff',
                    font=f['btn'],
                    padding=(12, 5),
                    borderwidth=0)
    style.map("Primary.TButton",
              background=[("active", c['accent_active']),
                          ("pressed", '#2d4bcf')])

    # 次按钮（白底蓝描边）
    style.configure("Secondary.TButton",
                    background=c['card_bg'],
                    foreground=c['accent'],
                    font=f['btn'],
                    padding=(10, 4),
                    borderwidth=1)
    style.map("Secondary.TButton",
              background=[("active", c['accent_soft'])])

    # 输入框
    style.configure("Field.TEntry",
                    font=f['label'],
                    padding=(6, 3),
                    background=c['card_bg'],
                    foreground=c['text'],
                    borderwidth=1,
                    relief="solid")

    # 下拉框
    style.configure("Field.TCombobox",
                    font=f['label'],
                    padding=(6, 3),
                    background=c['card_bg'],
                    foreground=c['text'],
                    borderwidth=1,
                    relief="solid")
    style.map("Field.TCombobox",
              fieldbackground=[("readonly", c['card_bg'])])

    # ── 兼容旧样式名（嵌套对话框 add_event / find_line 里还在用）──
    # 把它们映射到新样式的同款配置，避免每个对话框都要重写一遍
    style.configure("Title.TLabel",
                    font=f['card_title'],
                    foreground=c['accent'],
                    background=c['window_bg'],
                    padding=(4, 4))
    style.configure("Modern.TLabel",
                    font=f['label'],
                    foreground=c['text'],
                    background=c['window_bg'])
    style.configure("Modern.TButton",
                    background=c['accent'],
                    foreground='#ffffff',
                    font=f['btn'],
                    padding=(10, 5),
                    borderwidth=0)
    style.map("Modern.TButton",
              background=[("active", c['accent_active']),
                          ("pressed", '#2d4bcf')])
    style.configure("Modern.TEntry",
                    font=f['label'],
                    padding=(6, 3),
                    background=c['card_bg'],
                    foreground=c['text'],
                    borderwidth=1,
                    relief="solid")
    style.configure("Modern.TCombobox",
                    font=f['label'],
                    padding=(6, 3),
                    background=c['card_bg'],
                    foreground=c['text'],
                    borderwidth=1,
                    relief="solid")


def load_user_settings(dir_path):
    """读取 user_data.json；缺失或损坏时回落到默认值，保证启动不崩。"""
    data = dict(DEFAULT_USER_SETTINGS)
    path = os.path.join(dir_path, USER_SETTINGS_FILE)
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                data.update(loaded)
        except Exception as e:
            print("读取 user_data.json 失败:", e)
            _log_error("读取 user_data.json 失败(%s): %s" % (path, e))
    return data


def save_user_settings(dir_path, settings):
    """写回 user_data.json，保留文件里已有的其它键（例如 user_data 的 Excel 路径）。

    写失败不再静默：打包成无窗口 exe 后 print 看不见，写不进配置却毫无
    痕迹正是终端用户「每次开机配置都重置」排查困难的原因。失败会追加到
    APPDATA 下的 error.log。返回是否成功。"""
    path = os.path.join(dir_path, USER_SETTINGS_FILE)
    merged = {}
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                old = json.load(f)
            if isinstance(old, dict):
                merged.update(old)
    except Exception as e:
        print("合并旧设置失败（将直接覆盖）:", e)
    merged.update(settings or {})
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(merged, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print("写入 user_data.json 失败(%s):" % path, e)
        _log_error("写入 user_data.json 失败(%s): %s" % (path, e))
        return False


def sync_events_to_excel(self, on_error=None):
    """把 self.events 写回 Excel，让事件在文件中持久化。

    背景：原来新增 / 修改 / 删除事件后只更新内存 self.events，Excel 没改；
    一旦用户点「数据刷新」或重启，analysis_excel 从文件重读 → 内存先
    clear() → 刚加的事件就丢了。根因就是内存和文件两个数据源不同步。

    统一在所有"事件内容变更"的地方调用本函数，让 Excel 始终是唯一真相。
    格式：time 列用字符串如 "4.10"、"12.31" —— 避免 check_exit 原来用
    float(...) 写 "4.10 → 4.1" 再被 str() 读回成 "4.1" 解析成 4月1日 的 bug。

    参数:
        self: 主窗口对象（需要 self.events / self.dir_path）
        on_error: 可选回调 (err_msg)，用于在 Tk 回调里弹 messagebox 通知。
                  不传则只打印日志。
    返回: True 成功, False 失败
    """
    import pandas as pd

    # 1. 取 Excel 路径（与启动校验 / analysis_excel 同一来源）
    try:
        cfg = load_user_settings(get_settings_dir())
        paths = cfg.get('user_data', []) if isinstance(cfg, dict) else []
        file_path = paths[0] if paths else None
    except Exception:
        file_path = None

    if not file_path:
        # 用户还没选过 Excel 文件 —— 不写，直接成功（用户本来也没文件可写）
        return True

    if not os.path.isabs(file_path):
        file_path = os.path.abspath(os.path.join(
            getattr(self, 'dir_path', os.getcwd()), file_path))

    if not os.path.exists(file_path):
        msg = f"Excel 文件不存在：{file_path}，无法同步事件"
        print(msg); _log_error(msg)
        if callable(on_error):
            on_error(msg)
        return False

    # 2. 构造 DataFrame —— 统一用字符串 time，不再用 float 格式
    export_data = []
    for ev in getattr(self, 'events', []) or []:
        if not isinstance(ev, dict):
            continue
        try:
            m = int(str(ev.get('month', '')).strip())
            d = int(str(ev.get('day', '')).strip())
            things = str(ev.get('things', '')).strip()
        except (ValueError, TypeError):
            continue
        export_data.append({
            # 字符串拼接保留前导零：4月10日 → "4.10"，不会被 pandas 变成 4.1
            'time': f"{m}.{d}",
            'things': things,
        })

    # 3. 写回
    try:
        df = pd.DataFrame(export_data)
        df.to_excel(file_path, index=False)
        print(f"已同步 {len(export_data)} 条事件到 Excel: {file_path}")
        return True
    except Exception as e:
        msg = f"写入 Excel 失败：{e}\n请检查文件是否正被 Excel 打开"
        print(msg); _log_error(msg)
        if callable(on_error):
            on_error(msg)
        return False


# ============================================================================
# 版本检查 —— 从 Codingzhou.top Windows 专区 /api/windows/list 读取 manifest.json
# ============================================================================
# 本地版本号：格式 YYYY.MM.DD（打包日期），改这里即可
APP_VERSION = "2026.10.5"  # 测试用旧版本

# Worker 代理的 Windows 专区 manifest（已部署好的端点，读 zmj2301/windows-zone 仓库）
# 返回格式见仓库 manifest.json：files[].version = "20261005_0919", latest = true
REMOTE_VERSION_URL = "https://codingzhou.top/api/windows/list"

# 下载端点模板 —— Worker 流式代理 GitHub raw 文件
# 用法：REMOTE_DOWNLOAD_BASE + file 名字（files[].file 字段）
REMOTE_DOWNLOAD_BASE = "https://codingzhou.top/api/windows/download?file="


def check_update_available(timeout=8):
    """请求 /api/windows/list 并对比本地版本。

    返回 (is_newer: bool, remote_version: str, info: dict | None, error: str | None)

    manifest.json 格式：
      { "files": [ { "version": "20261005_0919", "date": "2026-10-05",
                     "file": "日程表_Win7_20261005_0919.zip", "latest": true } ] }

    版本比较：
      本地 APP_VERSION = "2026.10.5"  # 测试用旧版本 → 拆成 [2026, 10, 5]
      manifest.version = "20261005_0919" → 拆成 [2026, 10, 5, 9, 19]
      逐项比数字，多出来的段补 0。
    """
    import re as _re

    # 1. 请求 Worker 端点 —— 加时间戳绕过 CDN/边缘缓存
    ctx = ssl.create_default_context()
    _cache_buster = "&_t=%d" % int(time.time())
    _url = REMOTE_VERSION_URL + _cache_buster
    try:
        req = urllib.request.Request(
            _url,
            headers={"User-Agent": "ScheduleMateWin7/" + APP_VERSION,
                     "Cache-Control": "no-cache"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.URLError as e:
        return False, "", None, "网络连接失败: %s" % e.reason
    except urllib.error.HTTPError as e:
        return False, "", None, "服务器返回 %d: %s" % (e.code, e.reason)
    except Exception as e:
        return False, "", None, "请求异常: %s" % e

    # 2. 解析 manifest.json
    try:
        manifest = json.loads(body)
    except Exception as e:
        return False, "", None, "manifest 不是合法 JSON: %s" % e

    files = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(files, list) or not files:
        return False, "", None, "manifest 里没有 files 列表"

    # 3. 找最新版本 —— 优先 latest=true，否则按 version 字符串排序取最大
    latest = None
    for f in files:
        if isinstance(f, dict) and f.get("latest") is True:
            latest = f
            break
    if latest is None:
        try:
            latest = max(
                (f for f in files if isinstance(f, dict)),
                key=lambda f: str(f.get("version", "")))
        except Exception:
            return False, "", None, "无法确定 manifest 里的最新版本"

    remote_ver_raw = str(latest.get("version", "")).strip()
    if not remote_ver_raw:
        return False, "", None, "最新版本条目缺 version 字段"

    # 4. 版本比较 —— 统一转成整数数组
    def _parse(v):
        """把任意版本字符串转成整数数组。

        支持格式：
          "2026.10.5"       → [2026, 10, 5, 0, 0]
          "20261005_0919"   → [2026, 10, 5, 9, 19]
          "20261005"        → [2026, 10, 5, 0, 0]

        紧凑 YYYYMMDD_HHMM 先拆成空格分隔再提取数字。
        """
        s = str(v)
        # 先把 YYYYMMDD_HHMM 紧凑格式拆成 YYYY MM DD HH MM
        s = _re.sub(r'^(\d{4})(\d{2})(\d{2})(?:_(\d{2})(\d{2}))?$',
                    r'\1 \2 \3 \4 \5', s)
        parts = _re.findall(r"\d+", s)
        out = []
        for p in parts[:5]:  # 最多 5 段：年 月 日 时 分
            try:
                out.append(int(p))
            except ValueError:
                out.append(0)
        return out + [0] * (5 - len(out))

    local_parts = _parse(APP_VERSION)
    remote_parts = _parse(remote_ver_raw)
    is_newer = remote_parts > local_parts

    # 5. 组装 info dict —— UpdateDialog 要用
    remote_ver_pretty = remote_ver_raw.replace("_", " ")
    info = {
        "version": remote_ver_raw,
        "release_date": latest.get("date", ""),
        "download_url": REMOTE_DOWNLOAD_BASE + latest.get("file", ""),
        "file_name": latest.get("file", ""),
        "file_size": latest.get("size", 0),
        "sha256": latest.get("sha256", ""),
        "desc": latest.get("desc", ""),
        # notes 没有 —— manifest.json 里没这个字段，保持空列表
        "notes": [],
    }
    return is_newer, remote_ver_pretty, info, None


class UpdateDialog(QDialog):
    """漂亮的"发现新版本"弹窗（Qt 原生，走 PySide2/PySide6 双兼容）。

    视觉风格对齐主窗口：
      · 圆角 20px 卡片式浮层 + 阴影
      · 微软雅黑字体 / 白色文字 / 半透明蓝强调
      · 更新按钮带悬停态（颜色变亮 + 微微放大）
      · 标题带小图标（emoji 兜底，无外部资源依赖）
    """

    def __init__(self, parent=None, *, local_ver, remote_ver, info, is_newer, error=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(520, 420)
        self._build_ui(local_ver, remote_ver, info, is_newer, error)

    # ── UI 组装 ────────────────────────────────────────────────────────────
    def _build_ui(self, local_ver, remote_ver, info, is_newer, error):
        # 卡片壳：圆角 + 阴影 + 深蓝渐变
        card = QFrame(self)
        card.setGeometry(0, 0, 520, 420)
        card.setStyleSheet("""
            QFrame#card {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #1e293b, stop:1 #0f172a);
                border-radius: 20px;
            }
        """)
        card.setObjectName("card")
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 140))
        card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(36, 32, 36, 28)
        layout.setSpacing(14)

        # 顶部图标 + 标题
        if error:
            self._add_header(layout, "⚠️", "检查失败", "#fbbf24",
                             subtitle="网络或服务器错误，无法获取最新版本")
        elif is_newer:
            self._add_header(layout, "✨", "发现新版本！", "#38bdf8",
                             subtitle="有新功能等你体验")
        else:
            self._add_header(layout, "✅", "已经是最新版", "#34d399",
                             subtitle="感谢使用，暂无新版本发布")

        # 版本对比卡片
        self._add_version_band(layout, local_ver, remote_ver, is_newer, error)

        # 更新日志
        notes = []
        if isinstance(info, dict) and info.get("notes"):
            notes = [str(x) for x in info["notes"]]
        if notes and is_newer:
            self._add_notes(layout, notes)
        elif not is_newer and not error:
            self._add_notes(layout, [
                "当前没有可更新的版本。",
                "可在 Codingzhou.top 关注后续动态。"])
        elif error:
            self._add_notes(layout, [f"错误详情：{error[:160]}"])

        layout.addStretch(1)

        # 按钮行
        row = QHBoxLayout()
        row.setSpacing(12)
        row.addStretch(1)

        if is_newer and isinstance(info, dict) and info.get("download_url"):
            self.btn_later = QPushButton("稍后")
            self.btn_later.setFixedHeight(40)
            self.btn_later.setCursor(Qt.PointingHandCursor)
            self.btn_later.setStyleSheet("""
                QPushButton {
                    color: #cbd5e1;
                    background: transparent;
                    border: 1px solid #475569;
                    border-radius: 10px;
                    padding: 0 22px;
                    font-family: "Microsoft YaHei";
                    font-size: 14px;
                }
                QPushButton:hover { color: #f1f5f9; border-color: #64748b; }
                QPushButton:pressed { color: #94a3b8; }
            """)
            self.btn_later.clicked.connect(self.reject)
            row.addWidget(self.btn_later)

            self.btn_update = QPushButton("⬇  立即更新")
            self.btn_update.setFixedSize(168, 40)
            self.btn_update.setCursor(Qt.PointingHandCursor)
            self.btn_update.setStyleSheet("""
                QPushButton {
                    color: #ffffff;
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #3b82f6, stop:1 #6366f1);
                    border: none;
                    border-radius: 10px;
                    padding: 0 22px;
                    font-family: "Microsoft YaHei";
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #60a5fa, stop:1 #818cf8);
                }
                QPushButton:pressed { padding: 0 21px; }
            """)
            self.btn_update.clicked.connect(
                lambda: self._open(info.get("download_url")))
            row.addWidget(self.btn_update)
        else:
            self.btn_close = QPushButton("知道了")
            self.btn_close.setFixedSize(120, 40)
            self.btn_close.setCursor(Qt.PointingHandCursor)
            self.btn_close.setStyleSheet("""
                QPushButton {
                    color: #ffffff;
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #3b82f6, stop:1 #6366f1);
                    border: none;
                    border-radius: 10px;
                    padding: 0 22px;
                    font-family: "Microsoft YaHei";
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #60a5fa, stop:1 #818cf8);
                }
            """)
            self.btn_close.clicked.connect(self.reject)
            row.addWidget(self.btn_close)

        layout.addLayout(row)

        # 底部小字
        foot = QLabel("© Codingzhou.top  ·  日程表  ·  仅检查版本不自动下载")
        foot.setStyleSheet(
            "color: #475569; font-family: 'Microsoft YaHei'; font-size: 11px;")
        foot.setAlignment(Qt.AlignCenter)
        layout.addWidget(foot)

    # ── 子部件组装 ──────────────────────────────────────────────────────────
    def _add_header(self, layout, emoji, title, color, subtitle=""):
        row = QHBoxLayout()
        row.setSpacing(14)
        icon = QLabel(emoji)
        icon.setFont(QFont("Segoe UI Emoji", 28))
        icon.setStyleSheet(f"color: {color}; background: transparent;")
        icon.setFixedWidth(54)
        row.addWidget(icon)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        t = QLabel(title)
        t.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        t.setStyleSheet("color: #f1f5f9; background: transparent;")
        title_col.addWidget(t)
        if subtitle:
            s = QLabel(subtitle)
            s.setFont(QFont("Microsoft YaHei", 10))
            s.setStyleSheet("color: #94a3b8; background: transparent;")
            title_col.addWidget(s)
        row.addLayout(title_col)
        row.addStretch(1)
        layout.addLayout(row)

    def _add_version_band(self, layout, local_ver, remote_ver, is_newer, error):
        if error:
            local_band = QFrame()
            local_band.setStyleSheet("""
                QFrame { background: #1e293b; border-radius: 10px; }""")
            h = QHBoxLayout(local_band)
            h.setContentsMargins(18, 14, 18, 14)
            h.addWidget(QLabel(
                '<span style="color:#fbbf24">网络请求失败</span>'
                '<span style="color:#64748b">  —— </span>'
                '<span style="color:#e2e8f0">可稍后在设置里再次检查</span>'))
            layout.addWidget(local_band)
            return

        # 本地 / 最新 两个对比 pill
        pill_row = QHBoxLayout()
        pill_row.setSpacing(10)

        local = QLabel(f"  当前版本：{local_ver}  ")
        local.setStyleSheet("""
            QLabel {
                color: #cbd5e1;
                background: #1e293b;
                border-radius: 10px;
                padding: 8px 16px;
                font-family: "Microsoft YaHei";
                font-size: 13px;
            }
        """)
        pill_row.addWidget(local)

        arrow = QLabel("→")
        arrow.setFont(QFont("Segoe UI Emoji", 14, QFont.Bold))
        arrow.setStyleSheet(
            "color: %s; background: transparent;"
            % ("#38bdf8" if is_newer else "#475569"))
        pill_row.addWidget(arrow)

        latest = QLabel(
            f"  最新：{remote_ver}  "
            + (" ✨" if is_newer else " ✓"))
        latest.setStyleSheet("""
            QLabel {
                color: %s;
                background: %s;
                border-radius: 10px;
                padding: 8px 16px;
                font-family: "Microsoft YaHei";
                font-size: 13px;
                font-weight: bold;
            }
        """ % ("#ffffff",
               "qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #3b82f6,stop:1 #6366f1)"
               if is_newer else "#0f3d2e"))
        pill_row.addWidget(latest)
        pill_row.addStretch(1)
        layout.addLayout(pill_row)

    def _add_notes(self, layout, items):
        box = QFrame()
        box.setStyleSheet("""
            QFrame { background: #0f172a; border-radius: 12px; }""")
        v = QVBoxLayout(box)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(6)
        title = QLabel("📝  更新内容")
        title.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        title.setStyleSheet("color: #94a3b8; background: transparent;")
        v.addWidget(title)
        for item in items[:6]:  # 最多 6 条，避免弹窗过长
            row = QHBoxLayout()
            dot = QLabel("•")
            dot.setStyleSheet("color: #38bdf8; font-size: 16px; background: transparent;")
            dot.setFixedWidth(14)
            txt = QLabel(item)
            txt.setWordWrap(True)
            txt.setStyleSheet(
                "color: #cbd5e1; font-family: 'Microsoft YaHei'; "
                "font-size: 12px; background: transparent;")
            row.addWidget(dot)
            row.addWidget(txt)
            row.addStretch(1)
            v.addLayout(row)
        layout.addWidget(box)

    # ── 点击更新 ───────────────────────────────────────────────────────────
    def _open(self, url):
        import webbrowser
        if url:
            try:
                webbrowser.open(url, new=2)
            except Exception:
                pass
        self.accept()

    # ── 无边框拖动 ─────────────────────────────────────────────────────────
    def mousePressEvent(self, ev):
        self._drag_pos = ev.globalPos() - self.frameGeometry().topLeft()
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        if hasattr(self, "_drag_pos") and ev.buttons() & Qt.LeftButton:
            self.move(ev.globalPos() - self._drag_pos)
        super().mouseMoveEvent(ev)


class MyWindow(QMainWindow):
    # 检查更新完成的信号 —— 在工作线程里 emit，自动回到主线程执行槽函数
    # 参数: (is_newer: bool, remote_ver: str, info: str, error: str)
    # info / error 用 str 传递（info 是 JSON 字符串），避免跨线程序列化 dict 的坑
    _update_checked = Signal(bool, str, str, str)

    @staticmethod
    def _opacity_from(value, default=1.0):
        """从配置里读透明度：0 是合法值（表示底色全透明），只有 None 才回落默认。

        不能写 float(value or default) —— 0.0 在 Python 里是 falsy，
        会被 `or` 当成「没填」而丢掉默认值，用户拉到底反而变回 100%。
        """
        if value is None:
            return float(default)
        try:
            v = float(value)
        except (TypeError, ValueError):
            return float(default)
        return max(0.0, min(1.0, v))

    def __init__(self):
        super().__init__()
        self.dir_path = get_app_path()
        # 确保能找到img目录
        self.icon_path = os.path.join(get_assets_path(), 'img', 'icon.png')

        # 用户设置（透明度等），initUI 里应用
        # 设置读写统一走固定配置目录（%APPDATA%\日程表），与 exe 位置解耦：
        # exe 换目录 / 放 Program Files / 重新解压，配置都不会丢；
        # 老版本存在 exe 目录的 user_data.json 会自动迁移过来。
        migrate_legacy_settings(self.dir_path)
        self.user_settings = load_user_settings(get_settings_dir())
        # AI 解析功能已移除（原来这里没初始化，开设置前调用 AI 会 AttributeError）
        self.ai_enable = False
        # 透明度必须用「是否为 None」判断，不能用 `or`。
        #
        # 致命坑：用户把「桌面图标透明度」拉到 0% 期望白框完全透明，但
        # `float(0.0 or 1.0)` 里 0.0 是 falsy，`or` 直接把它丢掉、返回
        # 1.0 —— 保存确实写进文件了（终端用户诊断报告实测文件里就是
        # window_opacity: 0.0），但启动时读出来变成 100%，白板又回来了。
        # 表现就是「拉到底了，重启又变回白的」，改多少遍都没用。
        # 只有 None（键不存在）才该用默认值，0 是合法值。
        self.window_opacity = self._opacity_from(self.user_settings.get('window_opacity'))
        self.icon_opacity = self._opacity_from(self.user_settings.get('icon_opacity'))
        # 事件框长度：initUI 里会用到，必须先在这里初始化
        # （原来只在「设置」窗口里才赋值，initUI 一读就会 AttributeError）
        # 同样不用 `or`（0 是 falsy 会被丢掉），用显式 None 判断。
        _el = self.user_settings.get('event_length')
        if _el is None:
            _el = DEFAULT_USER_SETTINGS['event_length']
        self.event_length = max(60, int(_el))
        self.text_size = _clamp_text_size(self.user_settings.get('text_size'))
        # 主窗口图标边长（原来写死 150，用户反馈偏大）
        self.icon_size = _clamp_icon_size(self.user_settings.get('icon_size'))
        # 白框是否随内容自动加高。手动调小框高后会切成 False（手动优先），
        # 这样「刚调小就被内容变化顶回去」的循环才断得掉。
        self.auto_fit_box = bool(self.user_settings.get('auto_fit_box', True))

        # 初始化事件数据
        self.events = []
        
        # 初始化AI回答缓存
        self.ai_awswers = {}
        self.answers_json = {}
        
        # 初始化定时器，用于实时更新倒计时
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)  # 每秒更新一次
        import time
        # 定义变量
        self.time_day = int(time.strftime("%d", time.localtime()))
        self.time_month = int(time.strftime("%m", time.localtime()))
        self.time_year = int(time.strftime("%Y", time.localtime()))
        self.time_hour = int(time.strftime("%H", time.localtime()))
        self.time_minute = int(time.strftime("%M", time.localtime()))
        self.time_second = int(time.strftime("%S", time.localtime()))

        self.delete_events = {}

        self.ai_awswers = {}

        self.good_morning = [
            "早安，愿你今天顺心顺意。",
            "新的一天，平安喜乐。",
            "早安，愿阳光满路。",
            "清晨安好，万事皆甜。",
            "早安，保持好心情。",
            "新的一天，元气满满。",
            "早安，愿你被温柔以待。",
            "清晨愉快，事事顺利。",
            "早安，今天也要加油。",
            "愿你晨起有微笑，所遇皆美好。",
            "早安，开启美好一天。",
            "清晨安康，喜乐常伴。",
            "早安，愿好运常相随。",
            "新的一天，平安顺遂。",
            "早安，生活温柔有趣。",
            "清晨安好，心向阳光。",
            "早安，愿你轻松自在。",
            "新的一天，万事可期。",
            "早安，愿烦恼都消散。",
            "清晨愉快，幸福常在。",
            "早安，愿你眼里有光。",
            "新的一天，温暖相伴。",
            "早安，保持热爱生活。",
            "清晨安康，笑意盈盈。",
            "早安，愿一切刚刚好。",
            "新的一天，不负时光。",
            "早安，愿你平安无忧。",
            "清晨安好，顺心如意。",
            "早安，愿快乐不缺席。",
            "新的一天，勇敢向前。",
            "早安，愿生活多惊喜。",
            "清晨愉快，万事顺心。",
            "早安，愿你温暖如初。",
            "新的一天，努力发光。",
            "早安，愿好运找上门。",
            "清晨安康，平安喜乐。",
            "早安，愿心情常晴朗。",
            "新的一天，温柔前行。",
            "早安，愿日子清欢无忧。",
            "清晨安好，幸福相伴。",
            "早安，愿你事事都顺心。",
            "新的一天，健康常伴。",
            "早安，愿生活充满甜。",
            "清晨愉快，笑意常在。",
            "早安，愿你被世界温柔以待。",
            "新的一天，从容不迫。",
            "早安，愿所有美好如约而至。",
            "清晨安康，万事顺意。",
            "早安，愿你心中有光。",
            "新的一天，快乐出发。",
            "早安，清晨的第一声问候。",
            "清晨安好，愿你轻松快乐。",
            "早安，愿今天顺顺利利。",
            "新的一天，愿你不负自己。",
            "早安，愿生活温柔又明亮。",
            "清晨愉快，平安健康。",
            "早安，愿好运一路相伴。",
            "新的一天，愿你笑容常在。",
            "早安，愿烦恼远离你。",
            "清晨安康，愿你事事称心。",
            "早安，愿你每天都开心。",
            "新的一天，愿你温暖向阳。",
            "早安，愿一切美好降临。",
            "清晨安好，愿你轻松度过。",
            "早安，愿你今天超顺利。",
            "新的一天，愿你喜乐安宁。",
            "早安，愿生活善待你。",
            "清晨愉快，愿你万事胜意。",
            "早安，愿你元气十足。",
            "新的一天，愿你平安幸福。",
            "早安，愿你心中常欢喜。",
            "清晨安康，愿你事事顺利。",
            "早安，愿你今天超开心。",
            "新的一天，愿你温柔又强大。",
            "早安，愿阳光照亮你。",
            "清晨安好，愿你幸福满满。",
            "早安，愿你每天都顺利。",
            "新的一天，愿你所盼皆如愿。",
            "早安，愿你生活有甜。",
            "清晨愉快，愿你平安顺遂。",
            "早安，愿你今天好心情。",
            "新的一天，愿你轻松前行。",
            "早安，愿你被幸福包围。",
            "清晨安康，愿你笑口常开。",
            "早安，愿你万事都如意。",
            "新的一天，愿你温暖又快乐。",
            "早安，愿你今天顺顺当当。",
            "清晨安好，愿你健康平安。",
            "早安，愿你日子甜滋滋。",
            "新的一天，愿你好运连连。",
            "早安，愿你心中无烦恼。",
            "清晨愉快，愿你事事圆满。",
            "早安，愿你每天都精彩。",
            "新的一天，愿你从容自在。",
            "早安，愿你被温柔拥抱。",
            "清晨安康，愿你天天开心。",
            "早安，愿一切顺顺利利。",
            "新的一天，愿你遇见美好。",
            "早安，愿你幸福常相伴。",
            "清晨安好，愿你今天超棒。",

            "早安，晨光温柔，岁月静好。",
            "清晨有风，有光，有你，真好。",
            "早安，愿你在平凡日子里闪闪发光。",
            "新的一天，愿你温柔且坚定。",
            "早安，清晨的风，吹走所有疲惫。",
            "愿你晨起有光，心中有爱。",
            "早安，生活简单，内心丰盈。",
            "清晨的阳光，是最好的安慰。",
            "早安，愿你眼里有星辰，心中有山海。",
            "新的一天，愿你不慌不忙，向阳生长。",
            "早安，愿时光温柔，你我平安。",
            "清晨安好，愿你被世界温柔以待。",
            "早安，愿你走过的路都开满鲜花。",
            "新的一天，愿你心中有暖，无惧风霜。",
            "早安，愿每一个清晨都带来希望。",
            "清晨安康，愿日子清净，抬头皆是温柔。",
            "早安，愿你把日子过成自己喜欢的样子。",
            "新的一天，愿所有努力都不被辜负。",
            "早安，愿你心中有盼，脚下有路。",
            "清晨愉快，愿你被爱包围，温暖常存。",
            "早安，愿你晨起有微笑，梦里有惊喜。",
            "新的一天，愿你平安健康，万事顺遂。",
            "早安，愿你的世界永远阳光明媚。",
            "清晨安好，愿你事事顺心，无忧无虑。",
            "早安，愿你眼里的光，永远不会熄灭。",
            "新的一天，愿你遇见更好的自己。",
            "早安，愿生活给你惊喜，不给你烦恼。",
            "清晨安康，愿你笑容真诚，内心坦荡。",
            "早安，愿你一路繁花，一路向阳。",
            "新的一天，愿你从容自在，无忧无虑。",
            "早安，愿清晨的阳光治愈你所有不开心。",
            "清晨愉快，愿你所念皆如愿，所行皆坦途。",
            "早安，愿你每天都有小确幸。",
            "新的一天，愿你被温柔和好运点亮。",
            "早安，愿你心中有爱，眼里有光。",
            "清晨安好，愿你生活明朗，万物可爱。",
            "早安，愿你不负韶华，不负春秋。",
            "新的一天，愿你向光而行，向暖而生。",
            "早安，愿你日子有盼头，生活有甜头。",
            "清晨安康，愿你平安喜乐，万事胜意。",
            "早安，愿你晨起有希望，夜晚有归宿。",
            "新的一天，愿你所得皆所期，所失皆无碍。",
            "早安，愿你温柔半两，从容一生。",
            "清晨愉快，愿你心中有暖，岁月不寒。",
            "早安，愿你历经山河，觉得人间值得。",
            "新的一天，愿你保持热爱，奔赴山海。",
            "早安，愿你每天都光芒万丈。",
            "清晨安好，愿你自在如风，快乐如星。",
            "早安，愿你生活不拥挤，笑容不刻意。",
            "新的一天，愿你平安无恙，喜乐常安。",
            "早安，愿你前路浩浩荡荡，万事尽可期待。",
            "清晨安康，愿你以温柔待世界，以乐观待生活。",
            "早安，愿你每一天都值得被珍藏。",
            "新的一天，愿你心有暖阳，无惧风霜。",
            "早安，愿你所有美好，都如期而至。",
            "清晨愉快，愿你简单一点，快乐一点。",
            "早安，愿你被世界温柔以待。",
            "新的一天，愿你眼里有光，心中有爱。",
            "早安，愿你生活有糖，岁月有香。",
            "清晨安好，愿你不被生活为难。",
            "早安，愿你每天醒来，都是美好的开始。",
            "新的一天，愿你好运爆棚，笑容满分。",
            "早安，愿你温柔对待世界，也被世界温柔对待。",
            "清晨安康，愿你事事顺心，日日欢喜。",
            "早安，愿你所遇皆温柔，所行皆坦途。",
            "新的一天，愿你心中有光，眼里有笑。",
            "早安，愿清晨的微风，带给你一天的好心情。",
            "清晨愉快，愿你平安健康，快乐无忧。",
            "早安，愿你日子甜甜，好运连连。",
            "新的一天，愿你从容不迫，优雅前行。",
            "早安，愿你生活温暖，内心阳光。",
            "清晨安好，愿你万事顺心，天天开心。",
            "早安，愿你不负时光，不负自己。",
            "新的一天，愿你所有美好，不期而遇。",
            "早安，愿你心中有暖，脸上有笑，眼里有光。",
            "清晨安康，愿你每一天都闪闪发光。",
            "早安，愿你被爱包围，被好运照顾。",
            "新的一天，愿你向阳而生，逆风翻盘。",
            "早安，愿你生活明朗，人生可爱。",
            "清晨愉快，愿你平安喜乐，自在随心。",
            "早安，愿你所念皆所得，所愿皆成真。",
            "新的一天，愿你前路有光，身后有爱。",
            "早安，愿你晨起有清风，夜晚有星辰。",
            "清晨安好，愿你日子清净，喜乐无忧。",
            "早安，愿你生活有惊喜，梦想有回应。",
            "新的一天，愿你平安顺遂，无忧无虑。",
            "早安，愿你笑对生活，生活对你温柔。",
            "清晨安康，愿你事事顺利，步步生花。",
            "早安，愿你心向阳光，无惧悲伤。",
            "新的一天，愿你温柔有力，坚定有光。",
            "早安，愿你每一天都顺顺当当。",
            "清晨愉快，愿你被好运和温柔包围。",
            "早安，愿你努力有回报，付出有结果。",
            "新的一天，愿你幸福常伴，快乐不停。",
            "早安，愿你成为自己的太阳，无需借谁的光。",
            "清晨安好，愿你活得认真，笑得放肆。",
            "早安，愿你所行皆坦途，所待皆惊喜。",
            "新的一天，愿你心情像阳光一样灿烂。",
            "早安，愿你每天都有好心情。",

            "早安，新的一天，愿你万事顺心。",
            "清晨安康，愿你平安健康，幸福常在。",
            "早安，愿你今天比昨天更开心。",
            "新的一天，愿你好运不断，惊喜不停。",
            "早安，愿你被世界温柔以待。",
            "清晨愉快，愿你事事圆满，日日欢喜。",
            "早安，愿你眼里有光，心中有爱，生活有糖。",
            "新的一天，愿你不被生活为难，有事有方向。",
            "早安，愿你所遇皆美好，所行皆顺利。",
            "清晨安好，愿你每一天都充满希望。",
            "早安，愿你心中有暖，不惧路远。",
            "新的一天，愿你保持热爱，继续加油。",
            "早安，愿你笑容常在，烦恼不在。",
            "清晨安康，愿你生活甜甜，好运绵绵。",
            "早安，愿你今天元气满格，诸事顺利。",
            "新的一天，愿你从容自在，安静努力。",
            "早安，愿你不负晨光，不负自己。",
            "清晨愉快，愿你平安喜乐，万事顺心。",
            "早安，愿你日子有光，生活有香。",
            "新的一天，愿你所求皆如愿，所行皆坦途。",
            "早安，愿你晨起有微笑，一路有温暖。",
            "清晨安好，愿你万事胜意，平安无恙。",
            "早安，愿你生活温柔，心态阳光。",
            "新的一天，愿你努力向上，闪闪发光。",
            "早安，愿你每天都被温柔包围。",
            "清晨安康，愿你无忧无虑，自在欢喜。",
            "早安，愿你今天顺风顺水，顺心顺意。",
            "新的一天，愿你心中有光，步履不停。",
            "早安，愿你所有期待，都开花结果。",
            "清晨愉快，愿你万事顺利，平安健康。",
            "早安，愿你心情美好，事事如意。",
            "新的一天，愿你好运加持，万事可期。",
            "早安，愿你生活有甜，心里有暖。",
            "清晨安好，愿你每天都轻松又开心。",
            "早安，愿你今天一切顺利。",
            "新的一天，愿你不慌不忙，静静发光。",
            "早安，愿你被好运照顾，被快乐拥抱。",
            "清晨安康，愿你事事顺心，天天安康。",
            "早安，愿你生活明朗，心情晴朗。",
            "新的一天，愿你平安喜乐，笑容不断。",
            "早安，愿你每一天都值得期待。",
            "清晨愉快，愿你所念皆如愿，所得皆欢喜。",
            "早安，愿你眼里有星光，脚下有力量。",
            "新的一天，愿你向着阳光，野蛮生长。",
            "早安，愿你日子温柔，时光安然。",
            "清晨安好，愿你万事顺意，幸福安康。",
            "早安，愿你今天有收获，有快乐。",
            "新的一天，愿你心中有爱，遇事不慌。",
            "早安，愿你一路向阳，一路美好。",
            "清晨安康，愿你生活有甜，有光，有暖。",
            "早安，愿你每天都顺顺利利，开开心心。",
            "新的一天，愿你所有烦恼都随风吹散。",
            "早安，愿你被温柔点亮一整天。",
            "清晨愉快，愿你平安健康，万事顺心。",
            "早安，愿你今天超棒，超顺，超开心。",
            "新的一天，愿你笑容多一点，烦恼少一点。",
            "早安，愿你心中有暖，眼里有笑。",
            "清晨安好，愿你生活处处有惊喜。",
            "早安，愿你今天万事大吉，诸事顺利。",
            "新的一天，愿你向着美好出发。",
            "早安，愿你保持微笑，生活对你微笑。",
            "清晨安康，愿你每一天都平安喜乐。",
            "早安，愿你好运常在，快乐常伴。",
            "新的一天，愿你不辜负自己，不辜负生活。",
            "早安，愿你所行皆温暖，所遇皆温柔。",
            "清晨愉快，愿你事事都如意，天天都开心。",
            "早安，愿你生活有香气，心情有阳光。",
            "新的一天，愿你从容、温柔、有力量。",
            "早安，愿你今天被爱包围，被好运拥抱。",
            "清晨安好，愿你万事顺心，平安健康。",
            "早安，愿你的每一天都闪闪发光。",
            "新的一天，愿你所有美好如约绽放。",
            "早安，愿你晨起有希望，夜晚有安心。",
            "清晨安康，愿你日子甜甜，心情美美。",
            "早安，愿你顺顺利利，平平安安。",
            "新的一天，愿你心有暖阳，无惧迷茫。",
            "早安，愿你生活温柔以待，人生不负热爱。",
            "清晨愉快，愿你心中有爱，四季不寒。",
            "早安，愿你每天都元气满满。",
            "新的一天，愿你遇见温柔，遇见好运。",
            "早安，愿你今天轻松愉快，万事顺遂。",
            "清晨安好，愿你事事称心，日日安康。",
            "早安，愿你眼里有光，心中有暖。",
            "新的一天，愿你一路向前，一路生花。",
            "早安，愿你生活有甜，有爱，有惊喜。",
            "清晨安康，愿你平安顺遂，喜乐无忧。",
            "早安，愿你今天开心，今天顺利。",
            "新的一天，愿你保持温柔，保持热爱。",
            "早安，愿你所盼皆如愿，所得皆欢喜。",
            "清晨愉快，愿你万事顺意，笑容常在。",
            "早安，愿你每一天都温暖明亮。",
            "新的一天，愿你不负生活，不负自己。",
            "早安，愿你心中有光，生活有盼。",
            "清晨安好，愿你无忧无虑，笑容常在。",
            "早安，愿你今天顺顺当当，万事可期。",
            "新的一天，愿你被温柔以待，被好运照顾。",
            "早安，愿你生活明朗，万事可爱。",
            "清晨安康，愿你平安健康，幸福常伴。",
            "早安，愿你每天都有新的小开心。",

            "早安，愿清晨的第一缕阳光送给你好运。",
            "新的一天，愿你平安健康，万事顺心。",
            "早安，愿你今天心情好，运气好，状态好。",
            "清晨安好，愿你事事顺利，天天好心情。",
            "早安，愿你生活有惊喜，日子有温暖。",
            "新的一天，愿你不慌不忙，慢慢变好。",
            "早安，愿你被爱、被好运、被温柔包围。",
            "清晨愉快，愿你万事胜意，平安喜乐。",
            "早安，愿你眼里有笑，心中有暖，生活有光。",
            "新的一天，愿你所有努力都有回响。",
            "早安，愿你今天顺顺利利，开开心心。",
            "清晨安康，愿你生活甜甜，好运不断。",
            "早安，愿你从容生活，温柔处世。",
            "新的一天，愿你心中有光，向阳而生。",
            "早安，愿你晨起有微笑，所遇皆温柔。",
            "清晨安好，愿你万事顺遂，无忧无虑。",
            "早安，愿你今天比昨天更优秀、更快乐。",
            "新的一天，愿你平安无恙，喜乐常安。",
            "早安，愿你生活给你温暖，岁月给你惊喜。",
            "清晨愉快，愿你所念皆如愿，所行皆顺利。",
            "早安，愿你脸上有笑，心中有光，脚下有路。",
            "新的一天，愿你保持热爱，奔赴下一场美好。",
            "早安，愿你事事顺心，日日安康。",
            "清晨安康，愿你生活简单幸福，自在从容。",
            "早安，愿你所有烦恼消失，所有快乐到来。",
            "新的一天，愿你向暖而行，向光而往。",
            "早安，愿你今天好运爆棚，万事顺意。",
            "清晨安好，愿你平安健康，笑容常在。",
            "早安，愿你日子有盼，生活有甜。",
            "新的一天，愿你不负晨光，不负韶华。",
            "早安，愿你被世界温柔以待，被生活好好拥抱。",
            "清晨愉快，愿你事事圆满，心中常安。",
            "早安，愿你每一天都充满阳光和希望。",
            "新的一天，愿你所求皆所得，所愿皆成真。",
            "早安，愿你心有温柔，不惧风雨。",
            "清晨安康，愿你万事顺意，幸福常在。",
            "早安，愿你今天轻松、快乐、顺利。",
            "新的一天，愿你眼里有光，心中有爱。",
            "早安，愿你生活有香气，人生有底气。",
            "清晨安好，愿你所遇皆美好，所得皆欢喜。",
            "早安，愿你顺风顺水，顺心意。",
            "新的一天，愿你安静努力，悄悄发光。",
            "早安，愿你每天都被阳光和温柔唤醒。",
            "清晨安康，愿你平安喜乐，无忧无虑。",
            "早安，愿你心中有暖，岁月有光。",
            "新的一天，愿你所有美好如期而至。",
            "早安，愿你笑对人生，人生对你温柔。",
            "清晨愉快，愿你事事顺心，样样满意。",
            "早安，愿你生活有甜，有爱，有温暖。",
            "新的一天，愿你从容自在，平安喜乐。",
            "早安，愿你今天有好运，有惊喜，有笑容。",
            "清晨安好，愿你万事顺意，日日欢喜。",
            "早安，愿你心向阳光，一路芬芳。",
            "新的一天，愿你不辜负生活，不迷失方向。",
            "早安，愿你被温柔拥抱，被好运青睐。",
            "清晨安康，愿你平安健康，万事顺遂。",
            "早安，愿你每一天都闪闪发光、温暖明亮。",
            "新的一天，愿你保持微笑，保持热爱。",
            "早安，愿你所行皆坦途，所待皆惊喜。",
            "清晨愉快，愿你心中有光，眼里有笑。",
            "早安，愿你今天万事顺意，平安喜乐。",
            "新的一天，愿你生活明朗，心情灿烂。",
            "早安，愿你日子清净，温柔欢喜。",
            "清晨安好，愿你事事顺心，平安健康。",
            "早安，愿你心中有爱，生活有光。",
            "新的一天，愿你一路向阳，一路美好。",
            "早安，愿你今天开心多一点，烦恼少一点。",
            "清晨安康，愿你好运常伴，幸福常在。",
            "早安，愿你不负时光，向阳生长。",
            "新的一天，愿你所念皆如愿，所得皆温柔。",
            "早安，愿你生活有惊喜，每天有欢喜。",
            "清晨愉快，愿你万事顺意，喜乐常伴。",
            "早安，愿你眼里有星辰，心中有大海。",
            "新的一天，愿你温柔、坚定、勇敢。",
            "早安，愿你晨起有清风，归来有温暖。",
            "清晨安好，愿你生活无忧，心里有光。",
            "早安，愿你顺顺利利一整天天。",
            "新的一天，愿你心中有暖，不惧风霜。",
            "早安，愿你被好运、被温柔、被快乐包围。",
            "清晨安康，愿你万事顺心，平安喜乐。",
            "早安，愿你每一天都活得自在、开心、明亮。",
            "新的一天，愿你所有美好都不缺席。",
            "早安，愿你生活温柔，笑容坦荡。",
            "清晨愉快，愿你事事都圆满，日日都开心。",
            "早安，愿你心中有光，步履从容。",
            "新的一天，愿你向阳而行，温暖自在。",
            "早安，愿你今天顺顺当当，心情舒畅。",
            "清晨安好，愿你平安健康，万事顺意。",
            "早安，愿你生活有甜，心里有光，身边有爱。",
            "新的一天，愿你保持热爱，成为更好的自己。",
            "早安，愿你眼里有笑，心中有暖。",
            "清晨安康，愿你万事胜意，日日安康。",
            "早安，愿你每天醒来，都是温柔和希望。",
            "新的一天，愿你好运连连，惊喜不断。",
            "早安，愿你生活明朗，万事可期。",
            "清晨愉快，愿你平安喜乐，万事顺遂。",
            "早安，愿你所行皆温暖，所爱皆美好。",
            "新的一天，愿你从容、自在、开心。",
            "早安，愿你心中有暖，脸上有笑。",
            "清晨安好，愿你事事顺心，天天开心。",
            "早安，愿你今天一切都好。",

            "早安，愿清晨的阳光，温暖你的一整天。",
            "新的一天，愿你平安健康，喜乐无忧。",
            "早安，愿你事事顺心，心情舒畅。",
            "清晨安康，愿你生活温柔，岁月安然。",
            "早安，愿你被世界温柔以待，被好运时刻照顾。",
            "新的一天，愿你不慌不忙，自在生长。",
            "早安，愿你眼里有光，心中有爱，生活有甜。",
            "清晨愉快，愿你万事顺意，笑容常伴。",
            "早安，愿你今天顺风顺水，万事可期。",
            "新的一天，愿你心中有暖，不惧路远漫长。",
            "早安，愿你生活有惊喜，每天有小确幸。",
            "清晨安好，愿你无忧无虑，平安健康。",
            "早安，愿你保持热爱，继续向前。",
            "新的一天，愿你不负时光，不负自己。",
            "早安，愿你笑容常在，幸福常伴。",
            "清晨安康，愿你日子甜甜，心情暖暖。",
            "早安，愿你今天元气满满，诸事顺利。",
            "新的一天，愿你遇见美好，收获快乐。",
            "早安，愿你生活明朗，万物可爱，人间值得。",
            "清晨愉快，愿你所念皆如愿，所行皆坦途。",
            "早安，愿你心中有光，眼里有笑，生活有香。",
            "新的一天，愿你温柔且坚强，善良且有锋芒。",
            "早安，愿你平安无恙，喜乐常安。",
            "清晨安好，愿你万事顺心，日日欢喜。",
            "早安，愿你今天轻松自在，快乐无忧。",
            "新的一天，愿你努力有回报，付出有收获。",
            "早安，愿你所遇皆温柔，所得皆欢喜。",
            "清晨安康，愿你生活有暖，有心，有光。",
            "早安，愿你顺顺利利，开开心心过一天。",
            "新的一天，愿你心向阳光，一路生花。",
            "早安，愿你晨起有微笑，夜晚有安心。",
            "清晨愉快，愿你万事顺意，平安健康。",
            "早安，愿你生活有甜，有爱，有温暖，有惊喜。",
            "新的一天，愿你所有期待，都有回应。",
            "早安，愿你被温柔唤醒，被好运陪伴。",
            "清晨安好，愿你事事称心，平安喜乐。",
            "早安，愿你每一天都阳光灿烂。",
            "新的一天，愿你从容生活，认真热爱。",
            "早安，愿你心中有暖，眼里有光。",
            "清晨安康，愿你平安顺遂，笑容常在。",
            "早安，愿你今天好运爆棚，笑容满分。",
            "新的一天，愿你一路向阳，事事顺心。",
            "早安，愿你生活温柔以待，平安喜乐。",
            "清晨愉快，愿你万事胜意，心想事成。",
            "早安，愿你不被生活为难，一切都刚刚好。",
            "新的一天，愿你向着阳光，一路芬芳。",
            "早安，愿你日子清净，抬头皆是温柔。",
            "清晨安好，愿你健康、平安、开心、顺利。",
            "早安，愿你心中有爱，无惧风雨。",
            "新的一天，愿你所盼皆如愿，所爱皆美好。",
            "早安，愿你每天都顺顺当当、健健康康。",
            "清晨安康，愿你生活有香气，心情有阳光。",
            "早安，愿你被爱包围，被好运拥抱。",
            "新的一天，愿你不负光阴，不负自己。",
            "早安，愿你清晨有希望，夜晚有安心。",
            "清晨愉快，愿你万事顺遂，无忧无虑。",
            "早安，愿你生活处处是美好，时时有温柔。",
            "新的一天，愿你眼里有光，心中有暖。",
            "早安，愿你今天超顺利、超开心、超幸福。",
            "清晨安好，愿你平安健康，万事顺心。",
            "早安，愿你保持微笑，生活自然美好。",
            "新的一天，愿你所有美好，不期而遇。",
            "早安，愿你所行皆坦途，所爱皆温柔。",
            "清晨安康，愿你日子有甜，生活有光。",
            "早安，愿你每一天都活得热气腾腾。",
            "新的一天，愿你心有暖阳，无惧风霜。",
            "早安，愿你生活明朗，人生可爱，人间值得。",
            "清晨愉快，愿你平安喜乐，万事顺心。",
            "早安，愿你好运常来，幸福常在。",
            "新的一天，愿你温柔、勇敢、光芒万丈。",
            "早安，愿你晨起有清风，眼里有笑意。",
            "清晨安好，愿你事事顺利，步步生花。",
            "早安，愿你生活有惊喜，梦想有力量。",
            "新的一天，愿你不惧过去，不负将来。",
            "早安，愿你心中有暖，岁月安然。",
            "清晨安康，愿你平安顺遂，喜乐无忧。",
            "早安，愿你今天开开心心，万事大吉。",
            "新的一天，愿你保持热爱，继续奔赴。",
            "早安，愿你所念皆所得，所愿皆成真。",
            "清晨愉快，愿你事事顺心，天天安康。",
            "早安，愿你生活温柔，世界温暖。",
            "新的一天，愿你眼里有光，脚下有路。",
            "早安，愿你每一天都平安、健康、喜乐。",
            "清晨安好，愿你无忧无虑，自在生活。",
            "早安，愿你顺风顺水，顺顺利利。",
            "新的一天，愿你心中有光，生活有盼。",
            "早安，愿你被温柔、被好运、被快乐包围。",
            "清晨安康，愿你万事顺意，幸福常伴。",
            "早安，愿你今天所有美好都如约绽放。",
            "新的一天，愿你从容向前，向阳而生。",
            "早安，愿你晨起有微笑，笑里有幸福。",
            "清晨愉快，愿你平安健康，万事顺遂。",
            "早安，愿你生活有甜，有暖，有惊喜。",
            "新的一天，愿你不负生活，不负时光。",
            "早安，愿你心向阳光，无惧悲伤。",
            "清晨安好，愿你事事顺心，日日欢喜。",
            "早安，愿你平安喜乐，自在随心。",
            "新的一天，愿你所有努力，皆有回响。",
            "早安，愿你保持温柔，保持善良，保持热爱。",
            "清晨安康，愿你生活明朗，万事顺意。",
            "早安，愿你每一天都开心顺遂。",
            "新的一天，愿你被世界温柔以待。",
            "早安，愿你心中有暖，脸上有光，眼里有笑。",

            "早安，新的一天，愿你平安健康，万事顺心。",
            "清晨安康，愿你生活温柔，笑容常在。",
            "早安，愿你今天顺顺利利，开开心心。",
            "新的一天，愿你眼里有光，心中有爱。",
            "早安，愿你所遇皆美好，所行皆坦途。",
            "清晨愉快，愿你万事胜意，喜乐常安。",
            "早安，愿你心中有暖，不惧岁月风霜。",
            "新的一天，愿你保持热爱，奔赴山海。",
            "早安，愿你生活有惊喜，每天有欢喜。",
            "清晨安好，愿你无忧无虑，平安顺遂。",
            "早安，愿你不负时光，不负自己。",
            "新的一天，愿你好运连连，幸福绵绵。",
            "早安，愿你被温柔以待，被好运照顾。",
            "清晨安康，愿你事事顺心，平安健康。",
            "早安，愿你日子清净，内心温柔。",
            "新的一天，愿你向阳而生，温暖前行。",
            "早安，愿你晨起有微笑，一路有阳光。",
            "清晨愉快，愿你所念皆如愿，所得皆欢喜。",
            "早安，愿你生活有甜，心里有暖。",
            "新的一天，愿你不慌不忙，慢慢变好。",
            "早安，愿你眼里有星辰，心中有山海。",
            "清晨安好，愿你万事顺意，日日安康。",
            "早安，愿你今天元气满格，心情满格。",
            "新的一天，愿你所有美好如期而至。",
            "早安，愿你心中有光，眼里有笑。",
            "清晨安康，愿你平安喜乐，万事顺遂。",
            "早安，愿你生活明朗，万物可爱。",
            "新的一天，愿你从容自在，安静发光。",
            "早安，愿你一路繁花，一路向阳。",
            "清晨愉快，愿你事事圆满，心中常乐。",
            "早安，愿你今天轻松、愉快、顺利。",
            "新的一天，愿你心有暖阳，无惧迷茫。",
            "早安，愿你被爱包围，被快乐拥抱。",
            "清晨安好，愿你生活处处有温柔。",
            "早安，愿你所求皆如愿，所行皆顺利。",
            "新的一天，愿你不负韶华，不负自己。",
            "早安，愿你日子有盼头，生活有甜头。",
            "清晨安康，愿你平安无恙，喜乐常在。",
            "早安，愿你每一天都闪闪发光。",
            "新的一天，愿你温柔有力，坚定有光。",
            "早安，愿你清晨有希望，夜晚有安心。",
            "清晨愉快，愿你万事顺意，笑容常在。",
            "早安，愿你生活有香气，人生有底气。",
            "新的一天，愿你所行皆温暖，所待皆惊喜。",
            "早安，愿你心中有爱，四季不寒。",
            "清晨安好，愿你事事顺心，天天开心。",
            "早安，愿你顺风顺水，顺心意。",
            "新的一天，愿你向着美好，继续努力。",
            "早安，愿你笑对生活，生活对你温柔。",
            "清晨安康，愿你平安健康，万事顺心。",
            "早安，愿你今天超棒、超顺、超开心。",
            "新的一天，愿你生活有甜，有爱，有暖。",
            "早安，愿你心中有暖，眼里有光。",
            "清晨愉快，愿你万事顺遂，无忧无虑。",
            "早安，愿你每天醒来，都有阳光和温柔。",
            "新的一天，愿你一路向前，一路生花。",
            "早安，愿你保持微笑，保持善良。",
            "清晨安好，愿你生活有惊喜，梦想有回应。",
            "早安，愿你平安喜乐，万事胜意。",
            "新的一天，愿你不辜负生活，不迷失方向。",
            "早安，愿你眼里有笑，心中有暖，脚下有路。",
            "清晨安康，愿你事事顺利，平安健康。",
            "早安，愿你日子甜甜，心情美美。",
            "新的一天，愿你从容、温柔、快乐、自在。",
            "早安，愿你被好运点亮一整天。",
            "清晨愉快，愿你心中有光，生活有盼。",
            "早安，愿你所盼皆如愿，所爱皆美好。",
            "新的一天，愿你心向阳光，一路芬芳。",
            "早安，愿你生活温柔，心态阳光。",
            "清晨安好，愿你万事顺意，幸福常在。",
            "早安，愿你今天有收获，有快乐，有好运。",
            "新的一天，愿你所有努力都不被辜负。",
            "早安，愿你一路向阳，一路美好。",
            "清晨安康，愿你生活有光，有暖，有甜。",
            "早安，愿你无忧无虑，自在欢喜。",
            "新的一天，愿你成为自己的太阳。",
            "早安，愿你晨起有清风，归来有温暖。",
            "清晨愉快，愿你万事顺心，平安喜乐。",
            "早安，愿你日子温柔，时光安然。",
            "新的一天，愿你遇见更好的自己。",
            "早安，愿你生活处处是惊喜。",
            "清晨安好，愿你平安顺遂，喜乐无忧。",
            "早安，愿你心中有暖，不惧路远。",
            "新的一天，愿你保持热爱，继续加油。",
            "早安，愿你笑容常在，烦恼不在。",
            "清晨安康，愿你生活甜甜，好运绵绵。",
            "早安，愿你今天元气满格，诸事顺利。",
            "新的一天，愿你从容自在，安静努力。",
            "早安，愿你不负晨光，不负自己。",
            "清晨愉快，愿你平安喜乐，万事顺心。",
            "早安，愿你日子有光，生活有香。",
            "新的一天，愿你所求皆如愿，所行皆坦途。",
            "早安，愿你晨起有微笑，一路有温暖。",
            "清晨安好，愿你万事胜意，平安无恙。",
            "早安，愿你生活温柔，心态阳光。",
            "新的一天，愿你努力向上，闪闪发光。",
            "早安，愿你每天都被温柔包围。",
            "清晨安康，愿你无忧无虑，自在欢喜。",
            "早安，愿你今天顺风顺水，顺心顺意。",
            "新的一天，愿你心中有光，步履不停。",
            "早安，愿你所有期待，都开花结果。",

            "早安，愿清晨的阳光，治愈你所有不开心。",
            "新的一天，愿你平安健康，万事顺遂。",
            "早安，愿你事事顺心，心情愉悦。",
            "清晨安康，愿你生活温柔，岁月静好。",
            "早安，愿你被世界温柔以待。",
            "新的一天，愿你不慌不忙，向阳生长。",
            "早安，愿你眼里有光，心中有爱。",
            "清晨愉快，愿你万事顺意，笑容常伴。",
            "早安，愿你今天顺风顺水，万事可期。",
            "新的一天，愿你心中有暖，无惧风霜。",
            "早安，愿你生活有惊喜，每天有小确幸。",
            "清晨安好，愿你平安健康，无忧无虑。",
            "早安，愿你保持热爱，奔赴下一场山海。",
            "新的一天，愿你不负时光，不负自己。",
            "早安，愿你笑容常在，幸福常伴。",
            "清晨安康，愿你日子甜甜，心情暖暖。",
            "早安，愿你今天元气满满，诸事顺利。",
            "新的一天，愿你遇见美好，收获快乐。",
            "早安，愿你生活明朗，万物可爱。",
            "清晨愉快，愿你所念皆如愿，所行皆坦途。",
            "早安，愿你心中有光，眼里有笑，生活有香。",
            "新的一天，愿你温柔且坚强，善良且有锋芒。",
            "早安，愿你平安无恙，喜乐常安。",
            "清晨安好，愿你万事顺心，日日欢喜。",
            "早安，愿你今天轻松自在，快乐无忧。",
            "新的一天，愿你努力有回报，付出有收获。",
            "早安，愿你所遇皆温柔，所得皆欢喜。",
            "清晨安康，愿你生活有暖，有心，有光。",
            "早安，愿你顺顺利利，开开心心过一天。",
            "新的一天，愿你心向阳光，一路生花。",
            "早安，愿你晨起有微笑，夜晚有安心。",
            "清晨愉快，愿你万事顺意，平安健康。",
            "早安，愿你生活有甜，有爱，有温暖，有惊喜。",
            "新的一天，愿你所有期待，都有回应。",
            "早安，愿你被温柔唤醒，被好运陪伴。",
            "清晨安好，愿你事事称心，平安喜乐。",
            "早安，愿你每一天都阳光灿烂。",
            "新的一天，愿你从容生活，认真热爱。",
            "早安，愿你心中有暖，眼里有光。",
            "清晨安康，愿你平安顺遂，笑容常在。",
            "早安，愿你今天好运爆棚，笑容满分。",
            "新的一天，愿你一路向阳，事事顺心。",
            "早安，愿你生活温柔以待，平安喜乐。",
            "清晨愉快，愿你万事胜意，心想事成。",
            "早安，愿你不被生活为难，一切都刚刚好。",
            "新的一天，愿你向着阳光，一路芬芳。",
            "早安，愿你日子清净，抬头皆是温柔。",
            "清晨安好，愿你健康、平安、开心、顺利。",
            "早安，愿你心中有爱，无惧风雨。",
            "新的一天，愿你所盼皆如愿，所爱皆美好。",
            "早安，愿你每天都顺顺当当、健健康康。",
            "清晨安康，愿你生活有香气，心情有阳光。",
            "早安，愿你被爱包围，被好运拥抱。",
            "新的一天，愿你不负光阴，不负自己。",
            "早安，愿你清晨有希望，夜晚有安心。",
            "清晨愉快，愿你万事顺遂，无忧无虑。",
            "早安，愿你生活处处是美好，时时有温柔。",
            "新的一天，愿你眼里有光，心中有暖。",
            "早安，愿你今天超顺利、超开心、超幸福。",
            "清晨安好，愿你平安健康，万事顺心。",
            "早安，愿你保持微笑，生活自然美好。",
            "新的一天，愿你所有美好，不期而遇。",
            "早安，愿你所行皆坦途，所爱皆温柔。",
            "清晨安康，愿你日子有甜，生活有光。",
            "早安，愿你每一天都活得热气腾腾。",
            "新的一天，愿你心有暖阳，无惧风霜。",
            "早安，愿你生活明朗，人生可爱，人间值得。",
            "清晨愉快，愿你平安喜乐，万事顺心。",
            "早安，愿你好运常来，幸福常在。",
            "新的一天，愿你温柔、勇敢、光芒万丈。",
            "早安，愿你晨起有清风，眼里有笑意。",
            "清晨安好，愿你事事顺利，步步生花。",
            "早安，愿你生活有惊喜，梦想有力量。",
            "新的一天，愿你不惧过去，不负将来。",
            "早安，愿你心中有暖，岁月安然。",
            "清晨安康，愿你平安顺遂，喜乐无忧。",
            "早安，愿你今天开开心心，万事大吉。",
            "新的一天，愿你保持热爱，继续奔赴。",
            "早安，愿你所念皆所得，所愿皆成真。",
            "清晨愉快，愿你事事顺心，天天安康。",
            "早安，愿你生活温柔，世界温暖。",
            "新的一天，愿你眼里有光，脚下有路。",
            "早安，愿你每一天都平安、健康、喜乐。",
            "清晨安好，愿你无忧无虑，自在生活。",
            "早安，愿你顺风顺水，顺顺利利。",
            "新的一天，愿你心中有光，生活有盼。",
            "早安，愿你被温柔、被好运、被快乐包围。",
            "清晨安康，愿你万事顺意，幸福常伴。",
            "早安，愿你今天所有美好都如约绽放。",
            "新的一天，愿你从容向前，向阳而生。",
            "早安，愿你晨起有微笑，笑里有幸福。",
            "清晨愉快，愿你平安健康，万事顺遂。",
            "早安，愿你生活有甜，有暖，有惊喜。",
            "新的一天，愿你不负生活，不负时光。",
            "早安，愿你心向阳光，无惧悲伤。",
            "清晨安好，愿你事事顺心，日日欢喜。",
            "早安，愿你平安喜乐，自在随心。",
            "新的一天，愿你所有努力，皆有回响。",
            "早安，愿你保持温柔，保持善良，保持热爱。",
            "清晨安康，愿你生活明朗，万事顺意。",
            "早安，愿你每一天都开心顺遂。",
            "新的一天，愿你被世界温柔以待。",
            "早安，愿你心中有暖，脸上有光，眼里有笑。",

            "早安，愿你今天顺心顺意，平安喜乐。",
            "新的一天，愿你眼里有光，心中有爱。",
            "早安，愿生活温柔，愿你笑容坦荡。",
            "清晨安康，愿你万事顺意，无忧无虑。",
            "早安，愿你被温柔以待，被好运照顾。",
            "新的一天，愿你不慌不忙，静静发光。",
            "早安，愿你晨起有微笑，所遇皆美好。",
            "清晨愉快，愿你平安健康，万事顺遂。",
            "早安，愿你生活有甜，心里有暖。",
            "新的一天，愿你保持热爱，奔赴山海。",
            "早安，愿你日子清净，温柔欢喜。",
            "清晨安好，愿你事事顺心，天天开心。",
            "早安，愿你今天顺顺当当，心情舒畅。",
            "新的一天，愿你心中有光，步履从容。",
            "早安，愿你一路向阳，一路美好。",
            "清晨安康，愿你生活有光，有暖，有甜。",
            "早安，愿你不负时光，不负自己。",
            "新的一天，愿你好运连连，幸福不断。",
            "早安，愿你所念皆如愿，所行皆坦途。",
            "清晨愉快，愿你万事胜意，平安无恙。",
            "早安，愿你生活明朗，万物可爱。",
            "新的一天，愿你温柔有力，坚定有光。",
            "早安，愿你每天都被温柔包围。",
            "清晨安好，愿你平安喜乐，万事顺心。",
            "早安，愿你今天元气满满，万事大吉。",
            "新的一天，愿你心有暖阳，无惧风霜。",
            "早安，愿你眼里有星辰，心中有山海。",
            "清晨安康，愿你日子甜甜，好运连连。",
            "早安，愿你从容自在，安静努力。",
            "新的一天，愿你所有美好如期而至。",
            "早安，愿你生活有惊喜，每天有欢喜。",
            "清晨愉快，愿你心中有暖，脸上有笑。",
            "早安，愿你顺风顺水，顺心意。",
            "新的一天，愿你向着阳光，野蛮生长。",
            "早安，愿你成为自己的太阳，无需借谁的光。",
            "清晨安好，愿你平安健康，笑容常在。",
            "早安，愿你日子有盼头，生活有甜头。",
            "新的一天，愿你不负韶华，不负春秋。",
            "早安，愿你所行皆温暖，所爱皆美好。",
            "清晨安康，愿你万事顺意，日日安康。",
            "早安，愿你今天轻松愉快，万事顺遂。",
            "新的一天，愿你心中有爱，眼里有笑。",
            "早安，愿你生活温柔，心态阳光。",
            "清晨愉快，愿你事事圆满，日日欢喜。",
            "早安，愿你一路繁花，一路向阳。",
            "新的一天，愿你所盼皆如愿，所得皆欢喜。",
            "早安，愿你晨起有清风，夜晚有星辰。",
            "清晨安好，愿你生活处处有惊喜。",
            "早安，愿你平安无恙，喜乐常安。",
            "新的一天，愿你保持微笑，保持善良。",
            "早安，愿你心中有暖，岁月不寒。",
            "清晨安康，愿你万事顺心，平安健康。",
            "早安，愿你每天醒来，都是美好开始。",
            "新的一天，愿你温柔且坚定，勇敢且善良。",
            "早安，愿你生活有香气，心情有阳光。",
            "清晨愉快，愿你无忧无虑，自在随心。",
            "早安，愿你今天超棒、超顺、超幸福。",
            "新的一天，愿你眼里有光，脚下有路。",
            "早安，愿你历经山河，觉得人间值得。",
            "清晨安好，愿你平安顺遂，喜乐无忧。",
            "早安，愿你心中有光，生活有盼。",
            "新的一天，愿你不辜负生活，不迷失方向。",
            "早安，愿你被好运、温柔、快乐包围。",
            "清晨安康，愿你事事顺利，平安喜乐。",
            "早安，愿你每一天都闪闪发光。",
            "新的一天，愿你从容、自在、开心。",
            "早安，愿你生活明朗，万事可期。",
            "清晨愉快，愿你所念皆如愿，所愿皆成真。",
            "早安，愿你向光而行，向暖而生。",
            "新的一天，愿你努力有回报，付出有收获。",
            "早安，愿你日子温柔，时光安然。",
            "清晨安好，愿你健康平安，万事顺意。",
            "早安，愿你今天有收获，有快乐，有好运。",
            "新的一天，愿你心中有爱，遇事不慌。",
            "早安，愿你生活有甜，有爱，有惊喜。",
            "清晨安康，愿你平安喜乐，万事胜意。",
            "早安，愿你一路向前，一路生花。",
            "新的一天，愿你保持热爱，成为更好的自己。",
            "早安，愿你晨起有希望，夜晚有安心。",
            "清晨愉快，愿你万事顺遂，无忧无虑。",
            "早安，愿你所行皆坦途，所待皆惊喜。",
            "新的一天，愿你心向阳光，一路芬芳。",
            "早安，愿你生活温柔以待，人生不负热爱。",
            "清晨安好，愿你事事顺心，日日安康。",
            "早安，愿你每天都元气满满。",
            "新的一天，愿你遇见温柔，遇见好运。",
            "早安，愿你笑对生活，生活对你微笑。",
            "清晨安康，愿你平安健康，幸福常伴。",
            "早安，愿你所求皆所得，所爱皆美好。",
            "新的一天，愿你保持微笑，保持善良。",
            "早安，愿你今天有收获，有快乐，有好运。",
            "新的一天，愿你所求皆所得，所爱皆美好。",
        ]
        self.good_afternoon = [
            "下午好，愿你午后轻松惬意。",
            "午后时光，愿你平安顺心。",
            "下午安康，心情常晴朗。",
            "午后安好，万事皆温柔。",
            "下午愉快，烦恼都消散。",
            "午后阳光，温暖你一整天。",
            "下午好，保持好心情。",
            "午后时光，惬意又安心。",
            "下午安康，喜乐常相伴。",
            "午后安好，愿你事事顺心。",
            "下午好，愿好运常相随。",
            "午后时光，轻松又自在。",
            "下午愉快，生活有甜度。",
            "午后安好，所遇皆美好。",
            "下午好，愿你眼里有光。",
            "午后温柔，治愈所有疲惫。",
            "下午安康，愿你万事胜意。",
            "午后静好，岁月温柔以待。",
            "下午好，愿你从容不迫。",
            "午后微风，带来一整天好运。",
            "下午愉快，愿你笑容常在。",
            "午后安好，愿你无忧无虑。",
            "下午好，愿生活善待你。",
            "午后时光，安静且舒心。",
            "下午安康，万事皆可期。",
            "午后温暖，陪伴你每一刻。",
            "下午好，愿你平安喜乐。",
            "午后轻松，工作顺利不累。",
            "下午愉快，愿你心想事成。",
            "午后安好，愿你甜甜蜜蜜。",
            "下午好，愿你心态常阳光。",
            "午后时光，温柔且治愈。",
            "下午安康，愿你事事圆满。",
            "午后静好，愿你轻松自在。",
            "下午好，愿你好运连连。",
            "午后微风，吹散所有烦恼。",
            "下午愉快，愿你生活有光。",
            "午后安好，所盼皆能如愿。",
            "下午好，愿你温暖如初。",
            "午后时光，简单又快乐。",
            "下午安康，愿你健康常伴。",
            "午后温暖，治愈所有不开心。",
            "下午好，愿你一切顺利。",
            "午后轻松，日子清欢无忧。",
            "下午愉快，愿你万事顺心。",
            "午后安好，愿你幸福满满。",
            "下午好，愿你被温柔包围。",
            "午后时光，安静治愈一切。",
            "下午安康，愿你笑意盈盈。",
            "午后静好，愿你所遇皆甜。",
            "下午好，愿你平安无恙。",
            "午后微风，送来好运与安宁。",
            "下午愉快，愿你不负时光。",
            "午后安好，愿你从容前行。",
            "下午好，愿你生活有惊喜。",
            "午后时光，温暖且明亮。",
            "下午安康，愿你事事称心。",
            "午后温暖，让心情更舒畅。",
            "下午好，愿你轻松度过午后。",
            "午后轻松，烦恼通通走开。",
            "下午愉快，愿你每一天都甜。",
            "午后安好，愿你心中有暖。",
            "下午好，愿你眼里有笑意。",
            "午后时光，岁月安然静好。",
            "下午安康，愿你快乐不停歇。",
            "午后静好，愿你万事顺意。",
            "下午好，愿你好运常伴左右。",
            "午后微风，让心情更轻盈。",
            "下午愉快，愿你生活温柔有趣。",
            "午后安好，愿你努力有回报。",
            "下午好，愿你保持热爱生活。",
            "午后时光，安静又有力量。",
            "下午安康，愿你一切刚刚好。",
            "午后温暖，陪伴你一整个下午。",
            "下午好，愿你平安健康顺遂。",
            "午后轻松，工作顺心不疲惫。",
            "下午愉快，愿你所行皆坦途。",
            "午后安好，愿你日子有盼头。",
            "下午好，愿你心中有爱有光。",
            "午后时光，简单幸福就很好。",
            "下午安康，愿你笑容真诚坦荡。",
            "午后静好，愿你不被生活为难。",
            "下午好，愿你一路繁花向阳。",
            "午后微风，送来温柔与安心。",
            "下午愉快，愿你每一天都精彩。",
            "午后安好，愿你从容且自信。",
            "下午好，愿你生活有香有甜。",
            "午后时光，治愈你所有疲惫。",
            "下午安康，愿你事事顺利无忧。",
            "午后温暖，让下午更有温度。",
            "下午好，愿你轻松快乐每一天。",
            "午后轻松，愿你心态平和安稳。",
            "下午愉快，愿你生活处处美好。",
            "午后安好，愿你所求皆如愿。",
            "下午好，愿你不负自己不负岁月。",
            "午后时光，温柔治愈每一秒。",
            "下午安康，愿你喜乐安宁常在。",
            "午后静好，愿你每天都有小确幸。",
            "下午好，愿你被好运温柔照顾。",
            "午后微风，让心情慢慢变好。",
            "下午愉快，愿你生活明朗可爱。",
            "午后安好，愿你心中无烦恼牵挂。",
            "下午好，愿你元气满满过下午。",
            "午后时光，安静享受片刻温柔。",
            "下午安康，愿你万事顺心如意。",
            "午后温暖，带给你一整天力量。",
            "下午好，愿你平安顺遂常相伴。",
            "午后轻松，愿你下午顺顺当当。",
            "下午愉快，愿你生活甜甜美美。",
            "午后安好，愿你笑容永不缺席。",
            "下午好，愿你心态阳光一路芬芳。",
            "午后时光，岁月温柔善待你。",
            "下午安康，愿你事事圆满如意。",
            "午后静好，愿你轻松快乐无烦恼。",
            "下午好，愿你好运爆棚一整下午。",
            "午后微风，吹散压力与疲惫。",
            "下午愉快，愿你所遇皆温柔善意。",
            "午后安好，愿你生活有光有暖。",
            "下午好，愿你成为自己的小太阳。",
            "午后时光，简单安静也很美好。",
            "下午安康，愿你健康平安开心。",
            "午后温暖，让心情变得更柔软。",
            "下午好，愿你一切顺顺利利。",
            "午后轻松，愿你午后安稳惬意。",
            "下午愉快，愿你万事皆得所愿。",
            "午后安好，愿你生活有惊喜回应。",
            "下午好，愿你心中有暖不惧风霜。",
            "午后时光，安静积蓄前行力量。",
            "下午安康，愿你笑意常挂脸庞。",
            "午后静好，愿你日子清净温柔。",
            "下午好，愿你一路向阳一路美好。",
            "午后微风，带来安心与好消息。",
            "下午愉快，愿你生活温柔且明亮。",
            "午后安好，愿你所有期待开花结果。",
            "下午好，愿你轻松自在无忧无虑。",
            "午后时光，温暖治愈你的心。",
            "下午安康，愿你平安喜乐每一天。",
            "午后温暖，让下午时光更惬意。",
            "下午好，愿你事事顺心无烦恼。",
            "午后轻松，愿你工作顺利生活甜。",
            "下午愉快，愿你幸福常伴左右。",
            "午后安好，愿你生活有温度有光。",
            "下午好，愿你眼里有光心中有爱。",
            "午后时光，岁月安然万事顺心。",
            "下午安康，愿你快乐顺心不疲惫。",
            "午后静好，愿你温柔以待全世界。",
            "下午好，愿你好运常来福气常在。",
            "午后微风，让心情清爽又舒适。",
            "下午愉快，愿你生活有甜有盼有爱。",
            "午后安好，愿你从容优雅过下午。",
            "下午好，愿你每一天都闪闪发光。",
            "午后时光，安静享受温柔午后。",
            "下午安康，愿你万事顺意无忧愁。",
            "午后温暖，带给你安心与快乐。",
            "下午好，愿你平安健康心情好。",
            "午后轻松，愿你午后时光超舒服。",
            "下午愉快，愿你所念皆如愿所行皆坦途。",
            "午后安好，愿你生活处处充满阳光。",
            "下午好，愿你温柔坚定勇敢前行。",
            "午后时光，简单美好治愈人心。",
            "下午安康，愿你事事称心如意。",
            "午后静好，愿你日子有光有暖有甜。",
            "下午好，愿你被爱包围被温柔拥抱。",
            "午后微风，吹散所有不开心疲惫。",
            "下午愉快，愿你生活顺遂平安喜乐。",
            "午后安好，愿你心中有光眼里有笑。",
            "下午好，愿你不负时光不负自己。",
            "午后时光，温柔且有力量的午后。",
            "下午安康，愿你快乐安康万事顺。",
            "午后温暖，治愈内心所有不安。",
            "下午好，愿你轻松愉快过下午。",
            "午后轻松，愿你万事顺利心安宁。",
            "下午愉快，愿你生活有惊喜有温柔。",
            "午后安好，愿你每一天都顺顺当当。",
            "下午好，愿你心态平和心情愉悦。",
            "午后时光，岁月静好安稳舒心。",
            "下午安康，愿你万事可期好运来。",
            "午后静好，愿你生活自在随心常安。",
            "下午好，愿你好运不断惊喜不停。",
            "午后微风，送来温柔与好运气。",
            "下午愉快，愿你所遇皆美好所行皆顺利。",
            "午后安好，愿你心中有暖无惧远方。",
            "下午好，愿你保持微笑生活对你笑。",
            "午后时光，安静温柔治愈所有累。",
            "下午安康，愿你平安顺遂开心每一天。",
            "午后温暖，让下午充满阳光味道。",
            "下午好，愿你事事顺利万事大吉。",
            "午后轻松，愿你午后安稳轻松惬意。",
            "下午愉快，愿你生活甜甜好运连连。",
            "午后安好，愿你眼里有笑心中有暖。",
            "下午好，愿你向阳而生温暖前行。",
            "午后时光，简单快乐就是最幸福。",
            "下午安康，愿你笑意盈盈烦恼远离。",
            "午后静好，愿你生活温柔平安健康。",
            "下午好，愿你一路顺风事事顺心。",
            "午后微风，让心情轻盈没有压力。",
            "下午愉快，愿你生活有光有爱有甜。",
            "午后安好，愿你所有努力皆有回响。",
            "下午好，愿你生活不拥挤笑容不刻意。",
            "午后时光，岁月温柔治愈你的心。",
            "下午安康，愿你万事顺意喜乐常安。",
            "午后温暖，带给你一整个下午温暖。",
            "下午好，愿你平安健康万事皆顺意。",
            "午后轻松，愿你下午轻松没有烦恼。",
            "下午愉快，愿你所求皆所得所愿皆成真。",
            "午后安好，愿你生活明朗万物可爱。",
            "下午好，愿你心中有爱眼里有光笑容有甜。",
            "午后时光，安静享受这温柔的下午。",
            "下午安康，愿你事事顺心日日安康。",
            "午后静好，愿你生活有盼有喜有爱。",
            "下午好，愿你好运常伴福气满满。",
            "午后微风，吹散疲惫烦恼压力。",
            "下午愉快，愿你生活温柔有趣顺心。",
            "午后安好，愿你从容不迫安静努力。",
            "下午好，愿你不负晨光不负午后时光。",
            "午后时光，温暖治愈人心的午后。",
            "下午安康，愿你平安喜乐万事胜意。",
            "午后温暖，让心情温暖一整个下午。",
            "下午好，愿你事事圆满日日欢喜。",
            "午后轻松，愿你工作顺利生活安逸。",
            "下午愉快，愿你生活有香气心情有阳光。",
            "午后安好，愿你所念皆欢喜所得皆温柔。",
            "下午好，愿你一路繁花一路温暖。",
            "午后时光，岁月安然温柔以待。",
            "下午安康，愿你快乐常在烦恼不在。",
            "午后静好，愿你生活简单幸福自在。",
            "下午好，愿你好运加持万事顺利。",
            "午后微风，带来清爽好心情。",
            "下午愉快，愿你生活处处有小确幸。",
            "午后安好，愿你心中有光步履不停。",
            "下午好，愿你温暖向阳温柔生活。",
            "午后时光，安静温柔且有力量。",
            "下午安康，愿你平安无恙喜乐常伴。",
            "午后温暖，让下午变得更有意义。",
            "下午好，愿你一切顺心万事如意。",
            "午后轻松，愿你午后轻松快乐无忧。",
            "下午愉快，愿你生活有甜有暖有惊喜。",
            "午后安好，愿你眼里有星辰心中有大海。",
            "下午好，愿你温柔善良坚定有光。",
            "午后时光，岁月静好温柔相伴。",
            "下午安康，愿你事事称心天天开心。",
            "午后静好，愿你生活清净无忧喜乐安宁。",
            "下午好，愿你好运常在幸福常伴。",
            "午后微风，让心情放松没有负担。",
            "下午愉快，愿你所行皆温暖所爱皆美好。",
            "午后安好，愿你不辜负生活不迷失方向。",
            "下午好，愿你生活有光有暖有温柔。",
            "午后时光，安静享受这一刻治愈。",
            "下午安康，愿你平安顺遂万事皆可期。",
            "午后温暖，带给你安心温柔快乐。",
            "下午好，愿你事事顺利心情愉悦。",
            "午后轻松，愿你下午顺顺利利开开心心。",
            "下午愉快，愿你生活甜甜美美开开心心。",
            "午后安好，愿你心中有暖脸上有笑。",
            "下午好，愿你一路向阳万事皆顺。",
            "午后时光，温柔治愈的美好下午。",
            "下午安康，愿你健康平安喜乐无忧。",
            "午后静好，愿你生活温柔善待自己。",
            "下午好，愿你好运连连福气多多。",
            "午后微风，送来清凉舒适好心情。",
            "下午愉快，愿你所遇皆温柔事事皆圆满。",
            "午后安好，愿你生活有惊喜有期待有温暖。",
            "下午好，愿你保持热爱奔赴下一场美好。",
            "午后时光，岁月安然温暖相伴。",
            "下午安康，愿你笑意常在烦恼远离。",
            "午后温暖，让你的下午充满温柔。",
            "下午好，愿你平安健康顺心如意。",
            "午后轻松，愿你午后时光安稳又惬意。",
            "下午愉快，愿你生活明朗心情灿烂。",
            "午后安好，愿你心中有爱无惧风雨。",
            "下午好，愿你眼里有光脚下有路心中有暖。",
            "午后时光，安静温柔的美好时刻。",
            "下午安康，愿你万事顺意平安喜乐。",
            "午后静好，愿你生活自在开心无忧。",
            "下午好，愿你好运不断幸福绵绵。",
            "午后微风，吹散所有不安与疲惫。",
            "下午愉快，愿你生活有温度有情怀。",
            "午后安好，愿你所有美好如约而至。",
            "下午好，愿你从容生活温柔处世。",
            "午后时光，温暖治愈每一个瞬间。",
            "下午安康，愿你平安顺遂喜乐常在。",
            "午后温暖，让心情更柔软更安心。",
            "下午好，愿你事事顺心万事胜意。",
            "午后轻松，愿你下午轻松愉快没烦恼。",
            "下午愉快，愿你生活有甜有爱有温暖。",
            "午后安好，愿你所盼皆如愿所得皆欢喜。",
            "下午好，愿你生活温柔且坚定。",
            "午后时光，岁月静好安稳快乐。",
            "下午安康，愿你健康平安心情舒畅。",
            "午后静好，愿你生活清净温柔常安。",
            "下午好，愿你好运爆棚笑容满分。",
            "午后微风，带来好运温柔与安心。",
            "下午愉快，愿你所行皆坦途所待皆惊喜。",
            "午后安好，愿你心中有光眼里有笑。",
            "下午好，愿你不负时光不负温柔。",
            "午后时光，安静享受午后的小美好。",
            "下午安康，愿你万事顺利平安健康。",
            "午后温暖，带给你一整天的温暖。",
            "下午好，愿你事事圆满幸福安康。",
            "午后轻松，愿你午后安稳快乐轻松。",
            "下午愉快，愿你生活处处充满温柔。",
            "午后安好，愿你心中有暖岁月不寒。",
            "下午好，愿你向阳而行温暖向上。",
            "午后时光，温柔简单治愈的下午。",
            "下午安康，愿你喜乐安宁万事顺意。",
            "午后静好，愿你生活有光有暖有喜。",
            "下午好，愿你被温柔包围被好运照顾。",
            "午后微风，让心情清爽快乐无忧。",
            "下午愉快，愿你生活有趣有盼有爱。",
            "午后安好，愿你努力向上闪闪发光。",
            "下午好，愿你生活平安顺遂无忧愁。",
            "午后时光，岁月温柔善待每一个你。",
            "下午安康，愿你开心快乐顺顺利利。",
            "午后温暖，让下午时光更温暖。",
            "下午好，愿你事事顺心平安健康。",
            "午后轻松，愿你下午轻松惬意无压力。",
            "下午愉快，愿你所求皆如愿所行皆顺利。",
            "午后安好，愿你生活明朗万事可爱。",
            "下午好，愿你心中有爱笑容坦荡。",
            "午后时光，安静治愈所有不开心。",
            "下午安康，愿你万事顺意喜乐常伴。",
            "午后静好，愿你生活温柔平安顺遂。",
            "下午好，愿你好运常来幸福常在。",
            "午后微风，送来清凉好心情好消息。",
            "下午愉快，愿你所遇皆美好所盼皆成真。",
            "午后安好，愿你心中有暖不惧路远。",
            "下午好，愿你保持微笑生活自然美好。",
            "午后时光，温柔相伴美好常在。",
            "下午安康，愿你平安健康喜乐无忧。",
            "午后温暖，让你的心情更阳光。",
            "下午好，愿你事事顺利万事大吉。",
            "午后轻松，愿你午后轻松安稳又快乐。",
            "下午愉快，愿你生活甜甜好运多多。",
            "午后安好，愿你眼里有笑心中有光。",
            "下午好，愿你一路芬芳一路向阳。",
            "午后时光，岁月安然治愈人心。",
            "下午安康，愿你万事顺心日日欢喜。",
            "午后静好，愿你生活自在随心无忧无虑。",
            "下午好，愿你好运加持惊喜不断。",
            "午后微风，吹散所有烦恼与压力。",
            "下午愉快，愿你生活温柔有趣平安喜乐。",
            "午后安好，愿你心中有光步履从容。",
            "下午好，愿你不负自己不负生活时光。",
            "午后时光，安静温柔的午后时光。",
            "下午安康，愿你平安顺遂万事胜意。",
            "午后温暖，带给你安心快乐与温柔。",
            "下午好，愿你事事称心如意好心情。",
            "午后轻松，愿你下午顺顺当当轻松过。",
            "下午愉快，愿你生活有香气有阳光有温暖。",
            "午后安好，愿你所有美好不期而遇。",
            "下午好，愿你心中有暖眼里有光。",
            "午后时光，岁月静好温柔治愈一切。",
            "下午安康，愿你健康平安开心顺意。",
            "午后静好，愿你生活清净喜乐常安。",
            "下午好，愿你好运连连惊喜不停。",
            "午后微风，让心情轻盈快乐无忧。",
            "下午愉快，愿你所行皆温暖所念皆如愿。",
            "午后安好，愿你生活有惊喜有温柔有爱。",
            "下午好，愿你从容向上向阳而生。",
            "午后时光，安静享受这温柔时刻。",
            "下午安康，愿你万事顺意平安健康。",
            "午后温暖，让下午充满阳光与温柔。",
            "下午好，愿你事事顺利心情常好。",
            "午后轻松，愿你午后轻松愉快无烦恼。",
            "下午愉快，愿你生活美满幸福安康。",
            "午后安好，愿你心中有爱无惧风霜。",
            "下午好，愿你眼里有光心中有暖脚下有力。",
            "午后时光，岁月温柔相伴左右。",
            "下午安康，愿你喜乐常在烦恼走开。",
            "午后静好，愿你生活简单快乐安心。",
            "下午好，愿你好运常伴顺心顺意。",
            "午后微风，送来温柔好运好心情。",
            "下午愉快，愿你所遇皆善意所行皆美好。",
            "午后安好，愿你心中有盼生活有甜。",
            "下午好，愿你保持热爱生活闪闪发光。",
            "午后时光，温暖治愈的美好下午。",
            "下午安康，愿你平安顺遂开心常伴。",
            "午后温暖，让心情温暖柔软安心。",
            "下午好，愿你事事圆满万事顺意。",
            "午后轻松，愿你下午轻松愉快惬意。",
            "下午愉快，愿你生活有甜有暖有光有爱。",
            "午后安好，愿你所盼皆如愿所得皆温柔。",
            "下午好，愿你一路向阳一路温暖。",
            "午后时光，岁月安然静好如初。",
            "下午安康，愿你健康平安万事顺心。",
            "午后静好，愿你生活温柔善待自己。",
            "下午好，愿你好运爆棚福气满满。",
            "午后微风，让心情放松愉悦清爽。",
            "下午愉快，愿你生活明朗万事可期。",
            "午后安好，愿你心中有光有爱有暖。",
            "下午好，愿你不负时光不负温柔自己。",
            "午后时光，安静温柔治愈所有疲惫。",
            "下午安康，愿你万事顺意喜乐安康。",
            "午后温暖，带给你一整个下午好心情。",
            "下午好，愿你事事顺心平安喜乐。",
            "午后轻松，愿你午后安稳轻松快乐。",
            "下午愉快，愿你生活甜甜美美顺顺当当。",
            "午后安好，愿你眼里有笑脸上有光心中有暖。",
            "下午好，愿你温柔前行向阳而生。",
            "午后时光，岁月温柔治愈你的心。",
            "下午安康，愿你开心顺意万事大吉。",
            "午后静好，愿你生活清净无忧常安。",
            "下午好，愿你好运不断幸福常伴。",
            "午后微风，吹散疲惫不安与烦恼。",
            "下午愉快，愿你所行皆坦途所爱皆温暖。",
            "午后安好，愿你生活有惊喜期待与温柔。",
            "下午好，愿你心中有暖不惧任何远方。",
            "午后时光，安静享受美好午后时光。",
            "下午安康，愿你平安健康顺遂无忧。",
            "午后温暖，让下午充满温柔与阳光。",
            "下午好，愿你事事顺利万事胜意。",
            "午后轻松，愿你下午轻松愉快没压力。",
            "下午愉快，愿你生活有光有暖有甜有爱。",
            "午后安好，愿你所有努力都有美好回响。",
            "下午好，愿你生活温柔且坚强善良有锋芒。",
            "午后时光，岁月安然静好伴你左右。",
            "下午安康，愿你万事顺心喜乐常在。",
            "午后静好，愿你生活自在开心快乐无忧。",
            "下午好，愿你好运加持万事顺利如意。",
            "午后微风，送来清凉好运与好心情。",
            "下午愉快，愿你所遇皆美好所做皆顺利。",
            "午后安好，愿你心中有光眼里有笑脸上有暖。",
            "下午好，愿你不负生活不负自己不负时光。",
            "午后时光，温柔治愈安静美好的下午。",
            "下午安康，愿你平安顺遂喜乐安康无忧。",
            "午后温暖，让你的心情更阳光更温柔。",
            "下午好，愿你事事称心平安健康顺意。",
            "午后轻松，愿你午后轻松安稳惬意快乐。",
            "下午愉快，愿你生活有香气阳光与温暖。",
            "午后安好，愿你所盼皆成真所得皆欢喜。",
            "下午好，愿你一路繁花一路温暖一路向阳。",
            "午后时光，岁月温柔善待认真生活的你。",
            "下午安康，愿你万事顺意平安喜乐常在。",
            "午后静好，愿你生活清净温柔喜乐安宁。",
            "下午好，愿你好运常伴笑容常在幸福常来。",
            "午后微风，让心情轻盈放松没有负担。",
            "下午愉快，愿你生活温柔有趣简单幸福。",
            "午后安好，愿你心中有爱有光有暖有喜。",
            "下午好，愿你从容不迫安静努力闪闪发光。",
            "午后时光，安静享受这片刻温柔治愈。",
            "下午安康，愿你平安健康顺遂开心顺意。",
            "午后温暖，带给你安心快乐温柔与好运。",
            "下午好，愿你事事顺利万事圆满心情好。",
            "午后轻松，愿你下午顺顺当当轻松愉快。",
            "下午愉快，愿你生活甜甜好运连连幸福满满。",
            "午后安好，愿你眼里有笑心中有暖生活有光。",
            "下午好，愿你向阳而生温暖前行不负时光。",
            "午后时光，岁月安然治愈所有不开心。",
            "下午安康，愿你万事顺心日日安康喜乐无忧。",
            "午后静好，愿你生活自在随心温柔常安。",
            "下午好，愿你好运爆棚惊喜不断笑容满分。",
            "午后微风，送来清凉好消息好心情好运。",
            "下午愉快，愿你所行皆温暖所遇皆温柔所盼皆如愿。",
            "午后安好，愿你心中有暖不惧路远不畏风霜。",
            "下午好，愿你保持微笑生活对你温柔以待。",
            "午后时光，温柔相伴美好治愈的下午。",
            "下午安康，愿你平安健康喜乐顺意万事胜意。",
            "午后温暖，让下午充满阳光味道与温柔。",
            "下午好，愿你事事圆满万事顺意平安喜乐。",
            "午后轻松，愿你午后轻松惬意安稳快乐无忧。",
            "下午愉快，愿你生活明朗万物可爱人间值得。",
            "午后安好，愿你心中有光有爱有暖有盼有喜。",
            "下午好，愿你温柔坚定善良勇敢一路向前。",
            "午后时光，岁月静好温柔治愈一切疲惫。",
            "下午安康，愿你万事顺意平安健康开心常在。",
            "午后静好，愿你生活清净无忧喜乐安宁常伴。",
            "下午好，愿你好运连连福气满满幸福安康。",
            "午后微风，吹散所有压力疲惫烦恼不安。",
            "下午愉快，愿你生活有光有暖有甜有爱有盼。",
            "午后安好，愿你所有美好如期而至所有期待如愿。",
            "下午好，愿你不负时光不负自己不负生活温柔。",
            "午后时光，安静享受温柔治愈的美好下午。",
            "下午安康，愿你平安顺遂喜乐无忧万事顺心。",
            "午后温暖，带给你一整天好心情好运气。",
            "下午好，愿你事事顺利万事大吉平安喜乐。",
            "午后轻松，愿你下午轻松愉快顺顺当当。",
            "下午愉快，愿你生活甜甜美美开开心心顺遂。",
            "午后安好，愿你眼里有笑心中有暖脸上有光。",
            "下午好，愿你一路向阳一路芬芳一路美好。",
            "午后时光，岁月安然温柔相伴治愈人心。",
            "下午安康，愿你万事顺心日日欢喜喜乐常在。",
            "午后静好，愿你生活自在随心无忧无虑常安。",
            "下午好，愿你好运加持惊喜不断万事顺利。",
            "午后微风，送来清凉舒适好运好心情。",
            "下午愉快，愿你所遇皆美好所行皆顺利所盼皆如愿。",
            "午后安好，愿你心中有暖眼中有光笑里有幸福。",
            "下午好，愿你保持热爱奔赴山海忠于自己。",
            "午后时光，安静温柔治愈所有累与不开心。",
            "下午安康，愿你平安健康顺遂无忧万事胜意。",
            "午后温暖，让下午充满温柔阳光与好心情。",
            "下午好，愿你事事称心如意万事顺意安康。",
            "午后轻松，愿你午后轻松安稳快乐惬意无忧。",
            "下午愉快，愿你生活有香气有阳光有温暖有爱。",
            "午后安好，愿你所有努力皆有回报所有期待皆如愿。",
            "下午好，愿你温柔以待生活生活温柔待你。",
            "午后时光，岁月静好安稳快乐温柔相伴。",
            "下午安康，愿你万事顺意喜乐安康平安顺遂。",
            "午后静好，愿你生活清净温柔喜乐安宁无忧。",
            "下午好，愿你好运常伴笑容常在幸福常伴。",
            "午后微风，让心情轻盈放松愉悦清爽。",
            "下午愉快，愿你生活温柔有趣平安喜乐万事顺心。",
            "午后安好，愿你心中有光有爱有暖有盼有喜有笑。",
            "下午好，愿你从容生活温柔处世向阳而生。",
            "午后时光，安静享受这美好治愈的午后。",
            "下午安康，愿你平安健康开心顺意万事大吉。",
            "午后温暖，带给你安心快乐温柔好运阳光。",
            "下午好，愿你事事顺利圆满平安喜乐安康。",
            "午后轻松，愿你下午轻松愉快没烦恼没压力。",
            "下午愉快，愿你生活甜甜好运连连惊喜不断。",
            "午后安好，愿你眼里有笑心中有暖生活有光有爱。",
            "下午好，愿你一路繁花一路温暖一路向阳一路美好。",
            "午后时光，岁月温柔善待每一个认真生活的人。",
            "下午安康，愿你万事顺心喜乐常在平安健康顺遂。",
            "午后静好，愿你生活自在开心快乐无忧温柔常安。",
            "下午好，愿你好运爆棚福气满满惊喜不停笑容满分。",
            "午后微风，送来清凉好消息好心情好运气好温柔。",
            "下午愉快，愿你所行皆坦途所遇皆温柔所盼皆如愿所得皆欢喜。",
            "午后安好，愿你心中有暖不惧路远不畏风霜不惧迷茫。",
            "下午好，愿你不负时光不负自己不负生活不负温柔。",
            "午后时光，安静温柔治愈所有疲惫所有不开心。",
            "下午安康，愿你平安顺遂喜乐无忧万事顺意万事胜意。",
            "午后温暖，让下午充满阳光温柔好运与好心情。",
            "下午好，愿你事事顺利万事大吉平安喜乐健康顺遂。",
            "午后轻松，愿你午后轻松惬意安稳快乐轻松无忧。",
            "下午愉快，愿你生活明朗万物可爱人间值得温柔以待。",
            "午后安好，愿你心中有光有爱有暖有盼有喜有笑有力量。",
            "下午好，愿你温柔坚定善良勇敢积极向上向阳而生。",
            "午后时光，岁月静好温柔治愈一切烦恼一切疲惫。",
            "下午安康，愿你万事顺意平安健康开心常在喜乐无忧。",
            "午后静好，愿你生活清净无忧喜乐安宁常伴左右。",
            "下午好，愿你好运连连福气满满幸福安康万事顺利。",
            "午后微风，吹散所有压力疲惫烦恼不安迷茫。",
            "下午愉快，愿你生活有光有暖有甜有爱有盼有喜有笑。",
            "午后安好，愿你所有美好如期而至所有期待如愿以偿。",
            "下午好，愿你保持微笑保持热爱保持温柔保持善良。",
            "午后时光，安静享受这温柔治愈美好下午时光。",
            "下午安康，愿你平安顺遂喜乐安康万事顺心万事胜意。",
            "午后温暖，带给你一整天好心情好运气好温柔。",
            "下午好，愿你事事圆满万事顺意平安喜乐健康无忧。",
            "午后轻松，愿你下午轻松愉快顺顺当当没烦恼。",
            "下午愉快，愿你生活甜甜美美开开心心顺遂无忧。",
            "午后安好，愿你眼里有笑心中有暖脸上有光生活有甜。",
            "下午好，愿你一路向阳一路芬芳一路温暖一路美好。",
            "午后时光，岁月安然温柔相伴治愈所有不开心。",
            "下午安康，愿你万事顺心日日欢喜喜乐常在平安健康。",
            "午后静好，愿你生活自在随心无忧无虑常安常乐。",
            "下午好，愿你好运加持惊喜不断万事顺利笑容常在。",
            "午后微风，送来清凉舒适好运好心情温柔安心。",
            "下午愉快，愿你所遇皆美好所行皆顺利所盼皆如愿所得皆温柔。",
            "午后安好，愿你心中有暖眼中有光笑里有幸福生活有甜。",
            "下午好，愿你保持热爱奔赴山海忠于自己热爱生活。",
            "午后时光，安静温柔治愈所有累所有烦所有不开心。",
            "下午安康，愿你平安健康顺遂无忧万事顺意万事胜意喜乐。",
            "午后温暖，让下午充满温柔阳光安心快乐好运气。",
            "下午好，愿你事事称心如意万事顺意平安喜乐安康顺遂。",
            "午后轻松，愿你午后轻松安稳快乐惬意无忧无压力。",
            "下午愉快，愿你生活有香气有阳光有温暖有爱有盼有喜。",
            "午后安好，愿你所有努力皆有回报所有期待皆有回应。",
            "下午好，愿你温柔以待生活生活温柔以待你。",
            "午后时光，岁月静好安稳快乐温柔相伴治愈一切。",
            "下午安康，愿你万事顺意喜乐安康平安顺遂开心顺意。",
            "午后静好，愿你生活清净温柔喜乐安宁无忧常安。",
            "下午好，愿你好运常伴笑容常在幸福常伴万事顺利。",
            "午后微风，让心情轻盈放松愉悦清爽安心温柔。",
            "下午愉快，愿你生活温柔有趣平安喜乐万事顺心万事胜意。",
            "午后安好，愿你心中有光有爱有暖有盼有喜有笑有力量。",
            "下午好，愿你从容生活温柔处世积极向上向阳而生。",
            "午后时光，安静享受这美好治愈温柔的下午时光。"
        ]
        self.good_night = [
            "晚上好，愿你今夜安稳舒心。",
            "夜幕降临，愿烦恼都消散。",
            "夜晚安好，愿你轻松入眠。",
            "晚上好，愿一天疲惫都卸下。",
            "夜色温柔，愿你被温柔包围。",
            "晚上安康，愿你好梦相伴。",
            "夜晚愉快，愿心情慢慢变好。",
            "晚上好，愿你平安喜乐。",
            "夜色渐浓，愿你安心放松。",
            "夜晚安好，万事皆顺心。",
            "晚上好，愿你今夜无烦恼。",
            "夜幕温柔，愿你一夜好眠。",
            "晚上安康，愿你事事如意。",
            "夜晚宁静，愿你心安自在。",
            "晚上好，愿你卸下所有疲惫。",
            "夜色美好，愿你心情舒畅。",
            "夜晚安好，愿你甜梦入睡。",
            "晚上好，愿你今夜轻松惬意。",
            "夜幕降临，愿你安心休息。",
            "晚上安康，愿你幸福常在。",
            "夜晚好，愿月光温柔待你。",
            "晚上愉快，愿你一夜安宁。",
            "夜色温柔，治愈所有疲惫。",
            "晚上好，愿你今夜好梦连连。",
            "夜晚安好，愿你无忧无虑。",
            "晚上安康，愿你心中有暖。",
            "夜幕安静，愿你放松心情。",
            "晚上好，愿你今夜睡得香。",
            "夜色渐深，愿你平安健康。",
            "夜晚安好，愿你一切安好。",
            "晚上好，愿你被世界温柔以待。",
            "晚上安康，愿你烦恼清零。",
            "夜晚宁静，愿你心安如常。",
            "晚上好，愿你今夜不失眠。",
            "夜色温柔，愿你一夜好眠。",
            "夜晚安好，愿你笑容常在梦里。",
            "晚上好，愿你今夜安心入眠。",
            "晚上安康，愿你生活有甜。",
            "夜幕降临，愿你轻松自在。",
            "夜晚好，愿所有美好伴你左右。",
            "晚上愉快，愿你今夜安稳。",
            "夜色温柔，愿你心情柔软。",
            "晚上好，愿你今夜无扰无忧。",
            "夜晚安好，愿你平安顺遂。",
            "晚上安康，愿你喜乐安宁。",
            "夜幕渐深，愿你好好休息。",
            "晚上好，愿你今夜睡得安稳。",
            "夜色美好，愿你一夜好梦。",
            "夜晚安好，愿你心中无牵挂。",
            "晚上好，愿你今夜放松身心。",
            "晚上安康，愿你好运常伴。",
            "夜晚宁静，愿你心安事顺。",
            "晚上好，愿你今夜甜甜蜜蜜。",
            "夜色温柔，愿你一夜无梦到天亮。",
            "夜晚安好，愿你所有疲惫消失。",
            "晚上好，愿你今夜安心好梦。",
            "晚上安康，愿你事事顺心。",
            "夜幕降临，愿你休息愉快。",
            "夜晚好，愿你今夜睡得香甜。",
            "晚上愉快，愿你今夜好心情。",
            "夜色渐浓，愿你一夜安宁。",
            "晚上好，愿你今夜被温暖包围。",
            "夜晚安好，愿你平安健康。",
            "晚上安康，愿你幸福满满。",
            "夜幕安静，愿你卸下压力。",
            "晚上好，愿你今夜轻松好梦。",
            "夜色温柔，愿你今夜不疲惫。",
            "夜晚安好，愿你一切顺顺利利。",
            "晚上好，愿你今夜安稳入眠。",
            "晚上安康，愿你心中有光。",
            "夜晚宁静，愿你一夜好眠。",
            "晚上好，愿你今夜好梦成真。",
            "夜色美好，愿你心情常好。",
            "夜晚安好，愿你今夜无忧无虑。",
            "晚上好，愿你今夜温柔入眠。",
            "晚上安康，愿你生活温柔以待。",
            "夜幕降临，愿你今夜安心。",
            "夜晚好，愿你今夜轻松愉快。",
            "晚上愉快，愿你今夜万事顺心。",
            "夜色温柔，愿你今夜被爱包围。",
            "晚上好，愿你今夜睡得踏实。",
            "夜晚安好，愿你平安喜乐常在。",
            "晚上安康，愿你烦恼都走开。",
            "夜幕渐深，愿你今夜好好睡。",
            "晚上好，愿你今夜安宁无忧。",
            "夜色温柔，愿你今夜治愈自己。",
            "夜晚安好，愿你一夜好梦到天明。",
            "晚上好，愿你今夜轻松无压力。",
            "晚上安康，愿你事事皆圆满。",
            "夜晚宁静，愿你心安人安。",
            "晚上好，愿你今夜睡得舒服。",
            "夜色渐浓，愿你今夜无烦恼。",
            "夜晚安好，愿你今夜顺顺利利。",
            "晚上好，愿你今夜放松好心情。",
            "晚上安康，愿你今夜好运相伴。",
            "夜幕安静，愿你今夜好好休息。",
            "夜晚好，愿你今夜甜梦环绕。",
            "晚上愉快，愿你今夜心安自在。",
            "夜色温柔，愿你今夜睡得更香。",
            "晚上好，愿你今夜平安无恙。",
            "夜晚安好，愿你今夜幸福安康。",
            "晚上安康，愿你今夜一切安好。",
            "夜幕降临，愿你今夜轻松入睡。",
            "晚上好，愿你今夜无扰安心。",
            "夜色美好，愿你今夜心情美美。",
            "夜晚宁静，愿你今夜安稳入睡。",
            "晚上好，愿你今夜卸下所有累。",
            "晚上安康，愿你今夜喜乐常伴。",
            "夜晚安好，愿你今夜好梦不断。",
            "晚上好，愿你今夜温柔安心。",
            "夜色渐深，愿你今夜睡得安宁。",
            "晚上安康，愿你今夜万事大吉。",
            "夜晚好，愿你今夜无忧无虑过。",
            "晚上愉快，愿你今夜心情晴朗。",
            "夜色温柔，愿你今夜被温暖治愈。",
            "晚上好，愿你今夜平安顺心。",
            "夜晚安好，愿你今夜健康常伴。",
            "晚上安康，愿你今夜生活有甜。",
            "夜幕安静，愿你今夜好好放松。",
            "晚上好，愿你今夜安心好眠。",
            "夜色温柔，愿你今夜所有累消失。",
            "夜晚安好，愿你今夜万事顺意。",
            "晚上好，愿你今夜睡得安稳香甜。",
            "晚上安康，愿你今夜心中有暖。",
            "夜幕降临，愿你今夜轻松惬意。",
            "夜晚宁静，愿你今夜心安无忧。",
            "晚上好，愿你今夜好梦常伴。",
            "夜色渐浓，愿你今夜幸福常在。",
            "夜晚安好，愿你今夜不慌不忙。",
            "晚上好，愿你今夜放松安心。",
            "晚上安康，愿你今夜事事称心。",
            "夜晚好，愿你今夜温柔入睡。",
            "晚上愉快，愿你今夜平安健康。",
            "夜色温柔，愿你今夜治愈所有不开心。",
            "晚上好，愿你今夜安稳无忧。",
            "夜晚安好，愿你今夜笑容常在。",
            "晚上安康，愿你今夜好运连连。",
            "夜幕渐深，愿你今夜好好入眠。",
            "晚上好，愿你今夜心情舒畅。",
            "夜色温柔，愿你今夜一夜好眠。",
            "夜晚安好，愿你今夜一切刚刚好。",
            "晚上好，愿你今夜轻松安然入睡。",
            "晚上安康，愿你今夜万事可期。",
            "夜晚宁静，愿你今夜平安喜乐。",
            "晚上好，愿你今夜无烦恼不疲惫。",
            "夜色美好，愿你今夜幸福安康。",
            "夜晚安好，愿你今夜顺顺当当。",
            "晚上好，愿你今夜被温柔治愈。",
            "晚上安康，愿你今夜心安喜乐。",
            "夜幕降临，愿你今夜好好休息。",
            "夜晚好，愿你今夜轻松好梦。",
            "晚上愉快，愿你今夜万事如愿。",
            "夜色温柔，愿你今夜安心放松。",
            "晚上好，愿你今夜平安顺遂。",
            "夜晚安好，愿你今夜心中无愁。",
            "晚上安康，愿你今夜生活明朗。",
            "夜幕安静，愿你今夜睡得香甜。",
            "晚上好，愿你今夜无忧无虑好眠。",
            "夜色温柔，愿你今夜所有疲惫清零。",
            "夜晚安好，愿你今夜事事顺利。",
            "晚上好，愿你今夜安稳舒心入眠。",
            "晚上安康，愿你今夜好运常来。",
            "夜晚宁静，愿你今夜心安万事顺。",
            "晚上好，愿你今夜轻松自在休息。",
            "夜色渐浓，愿你今夜好梦成真。",
            "夜晚安好，愿你今夜健康平安。",
            "晚上好，愿你今夜温柔以待自己。",
            "晚上安康，愿你今夜幸福满满。",
            "夜幕渐深，愿你今夜安心入睡。",
            "夜晚好，愿你今夜不失眠不焦虑。",
            "晚上愉快，愿你今夜心情柔软。",
            "夜色温柔，愿你今夜被爱包围入睡。",
            "晚上好，愿你今夜平安无忧。",
            "夜晚安好，愿你今夜喜乐安宁。",
            "晚上安康，愿你今夜事事圆满。",
            "夜幕安静，愿你今夜放松身心。",
            "晚上好，愿你今夜一夜安睡。",
            "夜色温柔，愿你今夜治愈内心疲惫。",
            "夜晚安好，愿你今夜万事顺心如意。",
            "晚上好，愿你今夜睡得安稳又轻松。",
            "晚上安康，愿你今夜所盼皆如愿。",
            "夜幕降临，愿你今夜好好治愈自己。",
            "夜晚宁静，愿你今夜心安人安事事安。",
            "晚上好，愿你今夜好梦相伴到天亮。",
            "夜色美好，愿你今夜心情愉快。",
            "夜晚安好，愿你今夜无扰无烦。",
            "晚上好，愿你今夜轻松安然。",
            "晚上安康，愿你今夜生活有光。",
            "夜晚好，愿你今夜平安健康顺遂。",
            "晚上愉快，愿你今夜温柔安心好梦。",
            "夜色渐浓，愿你今夜幸福常伴左右。",
            "晚上好，愿你今夜卸下所有压力。",
            "夜晚安好，愿你今夜所有烦恼消散。",
            "晚上安康，愿你今夜好运加持。",
            "夜幕安静，愿你今夜睡得舒服安心。",
            "晚上好，愿你今夜无忧无虑好睡眠。",
            "夜色温柔，愿你今夜被温暖拥抱。",
            "夜晚安好，愿你今夜顺顺利利一整夜。",
            "晚上好，愿你今夜轻松放松好心情。",
            "晚上安康，愿你今夜万事胜意。",
            "夜晚宁静，愿你今夜心安喜乐常在。",
            "晚上好，愿你今夜甜梦一夜到天明。",
            "夜色渐深，愿你今夜平安无恙。",
            "夜晚安好，愿你今夜幸福安康常在。",
            "晚上好，愿你今夜好好照顾自己。",
            "晚上安康，愿你今夜事事称心如意。",
            "夜幕降临，愿你今夜轻松入睡无烦恼。",
            "夜晚好，愿你今夜温柔治愈疲惫。",
            "晚上愉快，愿你今夜心情舒畅安稳。",
            "夜色温柔，愿你今夜一夜好梦无忧。",
            "晚上好，愿你今夜平安喜乐顺心。",
            "夜晚安好，愿你今夜健康快乐常伴。",
            "晚上安康，愿你今夜生活温柔有趣。",
            "夜幕安静，愿你今夜安心好好休息。",
            "晚上好，愿你今夜睡得香睡得稳。",
            "夜色温柔，愿你今夜所有不开心都走。",
            "夜晚安好，愿你今夜万事顺利安康。",
            "晚上好，愿你今夜轻松惬意无压力。",
            "晚上安康，愿你今夜心中有光有暖。",
            "夜晚宁静，愿你今夜平安顺遂无忧。",
            "晚上好，愿你今夜好梦不断好眠不停。",
            "夜色美好，愿你今夜心情常晴。",
            "夜晚安好，愿你今夜不被烦恼打扰。",
            "晚上好，愿你今夜温柔安心入睡。",
            "晚上安康，愿你今夜幸福安康顺心。",
            "夜幕渐浓，愿你今夜放松好好休息。",
            "夜晚好，愿你今夜平安健康好眠。",
            "晚上愉快，愿你今夜万事顺心如愿。",
            "夜色温柔，愿你今夜被世界温柔以待。",
            "晚上好，愿你今夜安稳无忧入眠。",
            "夜晚安好，愿你今夜喜乐安宁常在。",
            "晚上安康，愿你今夜事事圆满如意。",
            "夜幕安静，愿你今夜身心放松舒适。",
            "晚上好，愿你今夜一夜安宁好眠。",
            "夜色温柔，愿你今夜治愈所有累与烦。",
            "夜晚安好，愿你今夜万事大吉大利。",
            "晚上好，愿你今夜轻松自在安心睡。",
            "晚上安康，愿你今夜好运连连不断。",
            "夜晚宁静，愿你今夜心安事顺人安。",
            "晚上好，愿你今夜睡得香甜无烦恼。",
            "夜色渐深，愿你今夜平安健康喜乐。",
            "夜晚安好，愿你今夜生活有甜有暖。",
            "晚上好，愿你今夜好好休息不熬夜。",
            "晚上安康，愿你今夜心中有爱有暖。",
            "夜幕降临，愿你今夜轻松愉快入睡。",
            "夜晚好，愿你今夜温柔好梦相伴。",
            "晚上愉快，愿你今夜心情柔软放松。",
            "夜色温柔，愿你今夜被温暖治愈好。",
            "晚上好，愿你今夜平安顺遂喜乐。",
            "夜晚安好，愿你今夜所有疲惫都卸下。",
            "晚上安康，愿你今夜万事顺意安康。",
            "夜幕安静，愿你今夜安心舒适入眠。",
            "晚上好，愿你今夜一夜好眠到天亮。",
            "夜色温柔，愿你今夜心情慢慢变好。",
            "夜晚安好，愿你今夜顺顺当当无忧。",
            "晚上好，愿你今夜轻松安然无烦恼。",
            "晚上安康，愿你今夜幸福常在身边。",
            "夜晚宁静，愿你今夜心安喜乐无忧。",
            "晚上好，愿你今夜好梦环绕身边。",
            "夜色美好，愿你今夜健康平安顺遂。",
            "夜晚安好，愿你今夜不焦虑不疲惫。",
            "晚上好，愿你今夜放松心情好好睡。",
            "晚上安康，愿你今夜事事顺心常安。",
            "夜幕渐浓，愿你今夜好运常伴左右。",
            "夜晚好，愿你今夜温柔安心好睡眠。",
            "晚上愉快，愿你今夜万事如愿以偿。",
            "夜色温柔，愿你今夜被爱包围治愈。",
            "晚上好，愿你今夜平安无忧喜乐。",
            "夜晚安好，愿你今夜生活明朗可爱。",
            "晚上安康，愿你今夜心中无愁无烦。",
            "夜幕安静，愿你今夜身心轻松安稳。",
            "晚上好，愿你今夜睡得安稳又香甜。",
            "夜色温柔，愿你今夜所有烦恼都消失。",
            "夜晚安好，愿你今夜万事顺利顺心。",
            "晚上好，愿你今夜轻松治愈自己。",
            "晚上安康，愿你今夜好运加持常在。",
            "夜晚宁静，愿你今夜平安喜乐安康。",
            "晚上好，愿你今夜无忧无虑安心睡。",
            "夜色渐深，愿你今夜幸福安康顺心。",
            "夜晚安好，愿你今夜健康平安无忧。",
            "晚上好，愿你今夜温柔对待自己。",
            "晚上安康，愿你今夜事事圆满称心。",
            "夜幕降临，愿你今夜好好休息放松。",
            "夜晚好，愿你今夜一夜好梦好眠。",
            "晚上愉快，愿你今夜心情舒畅愉悦。",
            "夜色温柔，愿你今夜被温暖拥抱入眠。",
            "晚上好，愿你今夜平安顺遂安稳。",
            "夜晚安好，愿你今夜喜乐安宁无忧。",
            "晚上安康，愿你今夜生活有光有暖有甜。",
            "夜幕安静，愿你今夜安心入睡无扰。",
            "晚上好，愿你今夜一夜安宁无烦恼。",
            "夜色温柔，愿你今夜治愈疲惫与不安。",
            "夜晚安好，愿你今夜万事顺意大吉。",
            "晚上好，愿你今夜轻松自在不疲惫。",
            "晚上安康，愿你今夜好运常来常伴。",
            "夜晚宁静，愿你今夜心安人安事事顺。",
            "晚上好，愿你今夜睡得香甜又安稳。",
            "夜色美好，愿你今夜平安健康喜乐。",
            "夜晚安好，愿你今夜幸福常伴无忧。",
            "晚上好，愿你今夜好好放松不焦虑。",
            "晚上安康，愿你今夜心中有光有爱。",
            "夜幕渐浓，愿你今夜轻松入眠无烦。",
            "夜晚好，愿你今夜温柔治愈好心情。",
            "晚上愉快，愿你今夜万事顺心如意。",
            "夜色温柔，愿你今夜被世界温柔治愈。",
            "晚上好，愿你今夜平安无恙喜乐。",
            "夜晚安好，愿你今夜所有累都消失。",
            "晚上安康，愿你今夜事事顺利圆满。",
            "夜幕安静，愿你今夜身心舒适放松。",
            "晚上好，愿你今夜一夜好眠无烦恼。",
            "夜色温柔，愿你今夜心情柔软安宁。",
            "夜晚安好，愿你今夜万事大吉顺遂。",
            "晚上好，愿你今夜轻松安然入睡。",
            "晚上安康，愿你今夜好运连连好梦。",
            "夜晚宁静，愿你今夜平安顺心无忧。",
            "晚上好，愿你今夜好梦成真相伴。",
            "夜色渐深，愿你今夜健康平安喜乐。",
            "夜晚安好，愿你今夜生活温柔以待。",
            "晚上好，愿你今夜好好照顾好自己。",
            "晚上安康，愿你今夜事事称心常安。",
            "夜幕降临，愿你今夜轻松愉快好眠。",
            "夜晚好，愿你今夜温柔安心入梦。",
            "晚上愉快，愿你今夜心情舒畅放松。",
            "夜色温柔，愿你今夜被温暖包围入眠。",
            "晚上好，愿你今夜平安顺遂无忧。",
            "夜晚安好，愿你今夜喜乐常在身边。",
            "晚上安康，愿你今夜万事顺意顺心。",
            "夜幕安静，愿你今夜安心休息无扰。",
            "晚上好，愿你今夜一夜安稳好睡眠。",
            "夜色温柔，愿你今夜治愈所有不开心。",
            "夜晚安好，愿你今夜顺顺利利一整夜。",
            "晚上好，愿你今夜轻松惬意好心情。",
            "晚上安康，愿你今夜幸福安康常在。",
            "夜晚宁静，愿你今夜心安万事顺遂。",
            "晚上好，愿你今夜睡得舒服又安心。",
            "夜色美好，愿你今夜平安健康顺心。",
            "夜晚安好，愿你今夜无烦恼无压力。",
            "晚上好，愿你今夜温柔安心好好睡。",
            "晚上安康，愿你今夜心中有暖有爱。",
            "夜幕渐浓，愿你今夜好运相伴左右。",
            "夜晚好，愿你今夜一夜好梦到天明。",
            "晚上愉快，愿你今夜万事如愿顺心。",
            "夜色温柔，愿你今夜被爱治愈入睡。",
            "晚上好，愿你今夜平安喜乐安稳。",
            "夜晚安好，愿你今夜生活明朗有光。",
            "晚上安康，愿你今夜事事圆满大吉。",
            "夜幕安静，愿你今夜身心轻松无忧。",
            "晚上好，愿你今夜一夜好眠无烦恼。",
            "夜色温柔，愿你今夜所有疲惫都清零。",
            "夜晚安好，愿你今夜万事顺利安康。",
            "晚上好，愿你今夜轻松自在安心入眠。",
            "晚上安康，愿你今夜好运不断连连。",
            "夜晚宁静，愿你今夜平安喜乐无忧。",
            "晚上好，愿你今夜睡得香甜安稳入梦。",
            "夜色渐深，愿你今夜健康平安顺遂。",
            "夜晚安好，愿你今夜幸福常在顺心。",
            "晚上好，愿你今夜好好休息不疲惫。",
            "晚上安康，愿你今夜心中有爱有光。",
            "夜幕降临，愿你今夜轻松治愈自己。",
            "夜晚好，愿你今夜温柔好梦好眠。",
            "晚上愉快，愿你今夜心情柔软舒适。",
            "夜色温柔，愿你今夜被温暖拥抱入睡。",
            "晚上好，愿你今夜平安无恙顺遂。",
            "夜晚安好，愿你今夜喜乐安宁常在。",
            "晚上安康，愿你今夜万事顺意圆满。",
            "夜幕安静，愿你今夜安心放松入眠。",
            "晚上好，愿你今夜一夜安宁好梦不停。",
            "夜色温柔，愿你今夜心情慢慢变柔软。",
            "夜晚安好，愿你今夜万事大吉大利。",
            "晚上好，愿你今夜轻松安然无烦恼。",
            "晚上安康，愿你今夜好运常伴好梦。",
            "夜晚宁静，愿你今夜心安事顺人安常。",
            "晚上好，愿你今夜睡得香甜无忧愁。",
            "夜色美好，愿你今夜平安健康喜乐常在。",
            "夜晚安好，愿你今夜生活有甜有暖有光。",
            "晚上好，愿你今夜放松心情好好休息。",
            "晚上安康，愿你今夜事事顺心如意常安。",
            "夜幕渐浓，愿你今夜轻松入眠无烦恼。",
            "夜晚好，愿你今夜温柔治愈所有疲惫。",
            "晚上愉快，愿你今夜万事顺心如愿以偿。",
            "夜色温柔，愿你今夜被世界温柔以待入睡。",
            "晚上好，愿你今夜平安喜乐顺遂无忧。",
            "夜晚安好，愿你今夜所有烦恼都随风散。",
            "晚上安康，愿你今夜事事顺利圆满称心。",
            "夜幕安静，愿你今夜身心舒适安稳入眠。",
            "晚上好，愿你今夜一夜好眠到天亮无忧。",
            "夜色温柔，愿你今夜治愈不安与疲惫。",
            "夜晚安好，愿你今夜万事顺意安康大吉。",
            "晚上好，愿你今夜轻松自在不熬夜好好睡。",
            "晚上安康，愿你今夜好运连连不断好梦。",
            "夜晚宁静，愿你今夜平安喜乐安康无忧。",
            "晚上好，愿你今夜无忧无虑安心好眠。",
            "夜色渐深，愿你今夜幸福安康顺心常在。",
            "夜晚安好，愿你今夜健康平安顺遂无忧。",
            "晚上好，愿你今夜温柔对待自己好好休息。",
            "晚上安康，愿你今夜事事圆满称心如意。",
            "夜幕降临，愿你今夜轻松愉快安心入眠。",
            "夜晚好，愿你今夜温柔安心好梦环绕。",
            "晚上愉快，愿你今夜心情舒畅愉悦放松。",
            "夜色温柔，愿你今夜被温暖包围治愈入睡。",
            "晚上好，愿你今夜平安顺遂喜乐无忧常在。",
            "夜晚安好，愿你今夜生活温柔有趣有光有暖。",
            "晚上安康，愿你今夜万事顺意顺心大吉大利。",
            "夜幕安静，愿你今夜安心舒适放松无烦恼。",
            "晚上好，愿你今夜一夜好眠安稳香甜无扰。",
            "夜色温柔，愿你今夜所有疲惫不安都消散。",
            "夜晚安好，愿你今夜万事顺利安康顺心如意。",
            "晚上好，愿你今夜轻松安然治愈自己好好睡。",
            "晚上安康，愿你今夜好运加持常伴好梦连连。",
            "夜晚宁静，愿你今夜平安喜乐心安事顺人安。",
            "晚上好，愿你今夜睡得香甜安稳无忧无愁。",
            "夜色美好，愿你今夜健康平安喜乐顺遂常在。",
            "夜晚安好，愿你今夜幸福安康顺心生活有光。",
            "晚上好，愿你今夜好好休息放松身心不疲惫。",
            "晚上安康，愿你今夜心中有爱有暖有光有笑。",
            "夜幕渐浓，愿你今夜轻松入眠无烦恼无压力。",
            "夜晚好，愿你今夜温柔治愈好心情好睡眠。",
            "晚上愉快，愿你今夜万事顺心如意如愿以偿。",
            "夜色温柔，愿你今夜被世界温柔以待被爱包围。",
            "晚上好，愿你今夜平安无恙喜乐安宁顺遂无忧。",
            "夜晚安好，愿你今夜所有累烦愁都消散不见。",
            "晚上安康，愿你今夜事事圆满大吉大利万事顺意。",
            "夜幕安静，愿你今夜身心轻松舒适安稳无忧入眠。",
            "晚上好，愿你今夜一夜好眠到天明好梦不停歇。"
        ]
        
        # 初始化问候语
        if self.time_hour < 12:
            # 早上
            self.current_time_period = "早上"
            self.current_time_period = random.choice(self.good_morning)
        elif 12 <= self.time_hour < 18:
            # 下午
            self.current_time_period = "下午"
            self.current_time_period = random.choice(self.good_afternoon)
        else:
            # 晚上  23:00
            self.current_time_period = "晚上"
            self.current_time_period = random.choice(self.good_night)
        # 检查如果大于70字，则将字符串每50字换行符
        if len(self.current_time_period) > 10:
            self.current_time_period = self.current_time_period[:10] + "\n" + self.current_time_period[10:]
        self.initUI()


    def initUI(self):
        # 设定窗口钉在画面上
        # Qt.Tool：不在 Windows 任务栏上显示图标（悬浮球/面板本来就是 Tool）。
        # 注意：Tool 窗口没有任务栏按钮，「最小化」后窗口将无处可点 —— 所以
        # 右键菜单里的「最小化」已改为收成桌面悬浮球（见 button_minimize）。
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # 创建主布局
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # 设置背景透明
        self.central_widget.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # 加载图片（边长取自设置，原为写死 150）
        self.pet_image_pixmap = QPixmap(self.icon_path)
        self.pet_image_pixmap = self.pet_image_pixmap.scaled(
            QSize(self.icon_size, self.icon_size), Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # 创建图片标签
        self.image_label = QLabel(self)
        self.image_label.setPixmap(self.pet_image_pixmap)
        self.image_label.setStyleSheet("border-radius: 10px; background-color: rgba(255, 255, 255, 0.1); padding: 5px;")
        
        # 创建倒计时标签
        self.countdown_label = QLabel(self)
        self.countdown_label.setText('倒计时应用程序')
        self.countdown_label.setFont(QFont('Microsoft YaHei', 18, QFont.Bold))
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet("color: #FFFFFF; background-color: rgba(64, 158, 255, 0.8); padding: 12px 20px; border-radius: 15px;")
        
        # 顶部水平布局：图标居左、倒计时框居右（右上角）。
        # 原来图标和倒计时垂直居中排列，用户反馈倒计时框在中间不好看，
        # 改到右上角后整体更紧凑、信息层级更清晰。
        self.top_layout = QHBoxLayout()
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        self.top_layout.addWidget(self.image_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.top_layout.addStretch(1)
        self.top_layout.addWidget(self.countdown_label, alignment=Qt.AlignRight | Qt.AlignTop)
        self.layout.addLayout(self.top_layout)
        
        # 创建内容信息显示
        self.content_label = QTextEdit(self)
        self.content_label.setReadOnly(True)
        self.content_label.setFont(QFont('Microsoft YaHei', 14))
        # 宽度跟随窗口自适应（不再固定 300）；高度随内容动态计算（见 _fit_content_height）
        self.content_label.setMinimumWidth(280)
        # 应用用户设置的事件框长度。
        # 原来这里写死 560，导致 user_data.json 里存的值根本没被读取 ——
        # 用户改完设置、文件里也确实存了，但重启后还是 560，表现为「保存不了」。
        self.content_label.setMaximumHeight(int(round(float(self.event_length))))

        # 水平方向设为 Ignored：字号变大时这两个控件的「理想宽度」也会变大，
        # 若不忽略，Qt 布局会把整个窗口一起撑宽 —— 那样改字号看起来就像
        # 在调分辨率、整体缩放。宽度改由可用空间决定，不反向影响窗口。
        self.content_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        # 倒计时框现在在水平布局里（右上角），水平方向不能用 Ignored ——
        # 否则水平布局算 sizeHint 时会忽略它的宽度，导致布局宽度计算错误。
        # 改用 Preferred + 设最大宽度，既参与布局计算，又不会被字号撑大窗口。
        self.countdown_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # 字号最大 28 → countdown 字号 32，一行"今天是 2026/10/4"
        # 约 15 个字符 × 32px ≈ 480px。给足空间让字号调大时不被截断。
        self.countdown_label.setMaximumWidth(340)
        self.content_label.setStyleSheet("color: #333333; background-color: rgba(255, 255, 255, 0.9); padding: 15px; border-radius: 15px; border: none;")
        self.layout.addWidget(self.content_label, 1)  # stretch=1：填满可用宽度

        # 右下角的「滑动组件」：主窗口是无边框的（FramelessWindowHint），
        # 用户拖不到窗口边缘来改大小，所以这里在窗口右下角放一个 QSizeGrip，
        # 让它可以直接拖拽调整白框/窗口高度 —— 解决「白框太矮被截断」的诉求。
        # 放在 central_widget（铺满整窗）的右下角，正好落在白框边角的外侧留白处，
        # 不会压住白框右侧的滚动条。
        self.size_grip = QSizeGrip(self.central_widget)
        self.size_grip.setFixedSize(22, 22)
        self.size_grip.setStyleSheet(
            "border-bottom-right-radius: 6px; background: rgba(64, 158, 255, 0.55);")
        self.size_grip.raise_()
        # 跟踪用户是否正在拖 grip（供 resizeEvent 区分「用户拖拽」和「被动 resize」）
        self._grip_dragging = False
        self.size_grip.installEventFilter(self)

        # 添加间距。
        # 15 → 6：用户反馈「上面蓝色倒计时条和下面白色事件框之间的间距太大」，
        # 调小作为默认布局（图标-蓝条、蓝条-白框三段一起收紧，观感更整体）。
        self.layout.setSpacing(6)
        self.layout.setContentsMargins(20, 20, 20, 20)
        # 解除布局对窗口最小尺寸的锁定：白框 setFixedHeight 之后，布局会把
        # 窗口最小高度锁在「其它控件+白框」，导致拖右下角 grip 只能拉大、
        # 永远拉不小（resize 被最小值静默钳住）。窗口尺寸完全交给
        # _fit_content_height / resizeEvent 自己管理。
        self.layout.setSizeConstraint(QLayout.SetNoConstraint)
        
        # 调整窗口大小：350 → 440，给放大字号的倒计时框 + 图标留够空间
        self.resize(440, 450)

        # 应用用户设置的透明度：
        # window_opacity -> 只让各框的「底色」透明（文字保持不透明实色）
        # icon_opacity   -> 仅窗口内那张图标图片
        #
        # 注意：底色透明到 0 时，透明区域在 Windows 上会「点击穿透」，
        # 窗口就拖不动了。这里给容器铺一层几乎看不见的底（alpha 0.01），
        # 视觉上完全无感，但保证整块区域仍能接收鼠标、可以拖动窗口。
        self.central_widget.setStyleSheet("background-color: rgba(255, 255, 255, 0.01);")
        self.apply_window_opacity()

        self.icon_opacity_effect = QGraphicsOpacityEffect(self.image_label)
        self.icon_opacity_effect.setOpacity(self.icon_opacity)
        self.image_label.setGraphicsEffect(self.icon_opacity_effect)

        # 应用用户设置的文字大小（initUI 里字号是写死的默认值，这里按设置覆盖）
        self.apply_text_size()

        self.drag_positon = QPoint()
        self.menu = QMenu(self)

        # 拖拽 grip 改大小时：防抖地把新的 event_length 写回 user_data.json
        self._el_save_timer = QTimer(self)
        self._el_save_timer.setSingleShot(True)
        self._el_save_timer.timeout.connect(
            lambda: self._persist_event_length(getattr(self, 'event_length', 560)))

        # 以「事件框长度」为基准建立初始窗口高度（白框 = event_length，
        # 窗口 = 其它控件高度 + event_length）。这样启动后白框就按用户设置
        # 的大小显示，而不是被旧的「只收不放」逻辑卡在很矮的状态。
        self._fit_content_height(allow_grow=True)

        # 程序启动时自动校验上次使用的 Excel 数据
        self.validate_and_load_data()

    def apply_text_size(self, size=None):
        """应用主窗口文字大小。

        text_size 控制的是「今日事件」正文；倒计时标签在正文基础上再大 4 号，
        保持它作为标题的视觉层级（原本就是 18 vs 14 的关系）。

        只改字号，绝不改变白框和窗口的尺寸 —— 否则拖字号滑块时框和窗口一起
        被撑大，看起来就像在调分辨率、整体缩放。
        """
        if size is not None:
            self.text_size = _clamp_text_size(size)

        base = self.text_size
        countdown_size = base + 4

        # 改字号会让 Qt 重算 sizeHint，但窗口不能被顶大：
        # 先在「不允许窗口变大」的前提下把字号换掉（_suppress_fit 只是避免
        # 换字号的瞬间触发一次多余的排版），随后统一交给 _fit_content_height，
        # 它会把白框限制在窗口剩余空间内，多出来的内容在框内滚动。
        self._suppress_fit = True
        try:
            if getattr(self, 'countdown_label', None) is not None:
                f = self.countdown_label.font()
                f.setPointSize(countdown_size)
                self.countdown_label.setFont(f)

            if getattr(self, 'content_label', None) is not None:
                f = self.content_label.font()
                f.setPointSize(base)
                self.content_label.setFont(f)
        finally:
            self._suppress_fit = False

        self._fit_content_height()

    def apply_icon_size(self, size=None):
        """应用主窗口图标大小（只改这张图，不动窗口和文字）。

        图标原来是写死的 150x150，用户反馈太大、占地方，默认已改为 100，
        并放进设置里可以自己拖。
        """
        if size is not None:
            self.icon_size = _clamp_icon_size(size)

        if getattr(self, 'image_label', None) is None:
            return

        pix = QPixmap(self.icon_path)
        if not pix.isNull():
            self.pet_image_pixmap = pix.scaled(
                QSize(self.icon_size, self.icon_size),
                Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(self.pet_image_pixmap)

        # 图标这一项和「文字大小」不一样：用户是嫌图标太大占地方，
        # 所以调图标时窗口要跟着一起收/放（图标调小 → 整块跟着变小），
        # 这里允许重新适配一次窗口高度；白框仍按内容取自然高度。
        self._fit_content_height(allow_grow=True)

    # 各控件「底色」的原始 alpha（滑块拉到 100% 时的值）
    BASE_BG_ALPHA = {
        'content': 0.9,     # 今日事件白框
        'countdown': 0.8,   # 倒计时蓝框
        'image': 0.1,       # 图标那张图的淡底
    }

    def apply_window_opacity(self, value=None):
        """「桌面图标透明度」：只让各框的**底色**变透明，文字与图标保持完全不透明。

        之前用的是 setWindowOpacity()，那是「整个窗口统一乘一个 alpha」，
        会把文字一起稀释 —— 用户反馈观感是「变暗/发虚」，而不是「底色消失」。
        这里改成只动底色 alpha，文字始终是不透明实色。
        """
        if value is not None:
            self.window_opacity = float(value)
        f = max(0.0, min(1.0, float(self.window_opacity)))

        # 窗口本身保持完全不透明，否则文字会被一起削弱
        self.setWindowOpacity(1.0)

        if getattr(self, 'content_label', None) is not None:
            a = self.BASE_BG_ALPHA['content'] * f
            self.content_label.setStyleSheet(
                "color: #333333; background-color: rgba(255, 255, 255, %.3f); "
                "padding: 15px; border-radius: 15px; border: none;" % a)
            # QTextEdit 的背景实际由 viewport 绘制，只设 QTextEdit 本身的
            # stylesheet 在某些环境（尤其 Win7 + PySide2）下 viewport 仍会
            # 透出默认白底 —— 这正是「配置已是 0 但白底还在」的真凶。
            # 必须同时把 viewport 的背景设成相同的 alpha，底色才会真正消失。
            self.content_label.viewport().setStyleSheet(
                "background-color: rgba(255, 255, 255, %.3f);" % a)

        if getattr(self, 'countdown_label', None) is not None:
            a = self.BASE_BG_ALPHA['countdown'] * f
            # 白字只有在足够深的底色上才看得清；底色淡下去就换成深色字，
            # 这样即使底色完全消失，在浅色桌面上依然清晰（且始终是不透明实色）
            text_color = "#FFFFFF" if a >= 0.45 else "#14487a"
            self.countdown_label.setStyleSheet(
                "color: %s; background-color: rgba(64, 158, 255, %.3f); "
                "padding: 12px 20px; border-radius: 15px;" % (text_color, a))

        if getattr(self, 'image_label', None) is not None:
            a = self.BASE_BG_ALPHA['image'] * f
            self.image_label.setStyleSheet(
                "border-radius: 10px; background-color: rgba(255, 255, 255, %.3f); "
                "padding: 5px;" % a)

    def _other_widgets_height(self):
        """主布局里除白框以外，其它控件 + 间距 + 边距一共占多少高度。

        现在的布局结构：
            [水平布局 top_layout]  图标(左) + 倒计时(右)
            [白框 content_label]

        水平布局里的图标和倒计时是「并排」关系，高度取两者的最大值
        （而不是累加），再加上水平布局自身的上下边距。
        """
        total = 0
        layout = self.layout
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item is None:
                continue
            w = item.widget()
            if w is self.content_label:
                continue
            if w is not None:
                total += w.sizeHint().height()
            else:
                # 子布局（目前是顶部的水平布局）：高度 = 内部控件最大高度
                sub = item.layout()
                if sub is not None:
                    max_h = 0
                    for j in range(sub.count()):
                        si = sub.itemAt(j)
                        if si is None:
                            continue
                        sw = si.widget()
                        if sw is not None:
                            max_h = max(max_h, sw.sizeHint().height())
                    total += max_h
                else:
                    total += item.sizeHint().height()
        total += layout.spacing() * max(layout.count() - 1, 0)
        m = layout.contentsMargins()
        total += m.top() + m.bottom()
        return total

    def _fit_content_height(self, allow_grow=False, fit_content=False):
        """按「基准窗口高度 self._fit_h」重排白框高度。

        关键约定（解决「白框太矮被截断/出滚动条」+「改字号像调分辨率」两件事）：
          * 白框高度 = self._fit_h - 其它控件占用高度
          * self._fit_h 由「事件框长度」(event_length) 决定：
                窗口基准 = 其它控件高度 + event_length
            也就是说，event_length 现在真正是白框的*目标高度*，而不再是
            可有可无的上限 —— 调滑块 / 拖 grip 改的就是这个基准。

        两种重算基准的时机（互斥使用）：
          * allow_grow=True：滑块 / 拖 grip 改了 event_length，
                窗口基准 = 其它控件 + event_length
          * fit_content=True：正文内容真的变了（update_countdown 检测到
                文字变化才传），窗口基准 = 其它控件 + max(event_length,
                内容自然高度)（不超过屏幕）—— 内容变多白框自动加高，
                装得下就不用滚动；内容变少则回落到 event_length。

        改字号、每秒刷新都*不会*动基准 —— 这是「改字号像调分辨率」的根治点。
        """
        if not hasattr(self, 'content_label'):
            return
        # 改字号/改图标换图的瞬间不参与排版，否则会把刚锁住的尺寸又撑开
        if getattr(self, '_suppress_fit', False):
            return
        edit = self.content_label
        others = self._other_widgets_height()

        if allow_grow:
            # 事件框长度（event_length）为目标高度：窗口基准 = 其它控件 + event_length
            # 先把白框目标高度算出来，再统一落到基准上。
            el = int(round(float(getattr(self, 'event_length', 560) or 560)))
            box = max(el, 60)
            # 屏幕夹取：无边框窗口不能超出屏幕，白框超出部分要被夹掉。
            # 注意夹的是**白框**（box），不是整个窗口 —— 早前把窗口高度
            # (others+el) 拿去和屏幕比，夹完再减 others 会二次缩水。
            screen = QApplication.primaryScreen()
            if screen is not None:
                cap_box = max(screen.availableGeometry().height() - 60 - others, 60)
                box = min(box, cap_box)
            # 基准必须精确等于「其它控件 + 白框」，因为后面所有排版都用
            # avail = self._fit_h - others 来算白框。这里绝对不能再套一层
            # 「窗口不小于 300」的下限 —— 那个下限是窗口级的，一旦混进基准，
            # 白框就会被撑大：实测 others=131、用户设 100 时 _fit_h 被抬到 300，
            # 白框拿到 169（用户设 100 永远得不到 100）。
            self._fit_h = others + box

        if fit_content and not getattr(self, 'auto_fit_box', True):
            # 手动优先：用户已明确把框调小（拖过小蓝块或滑块），就严格按他设
            # 的高度显示，内容多了在框内滚动。
            #
            # 这里是终端用户「框框调小后，鼠标一动又自己弹高显示全部」的根因：
            # 正文内容一变（倒计时每秒都在变）就走 fit_content 分支，把白框
            # 重算成 max(内容自然高度, event_length) —— 内容自然高度往往比
            # 用户设的高度大，于是刚调小的框立刻被顶回去。勾掉设置里的
            # 「内容多时自动加高白框」或手动调小后，就走不到这个分支。
            fit_content = False

        if fit_content:
            # 内容变了：白框 = max(event_length, 内容自然高度)，上限为屏幕高度。
            # 这样事件再多也能全部摆出来（装不下才滚动），内容变少时回落到
            # event_length，不会每秒乱跳 —— 因为只有文字真的变化才会走到这里。
            #
            # 注意：不能直接量 widget 里的 document —— QTextDocumentLayout 在
            # setText 之后是分块异步排版的，要过好几轮事件才稳定，中间量到的
            # 是半新半旧的高度（实测 12 条缩到 6 条时量到 514，真值约 382，
            # 白框因此不回落）。这里用一份「干净的探测文档」离线测量，它按需
            # 同步排版，结果永远准确。
            #
            # 先激活布局再量：setText 后 edit.width() 可能还是上一轮的旧值
            # （布局尚未重新分配），用旧宽度排版会得到偏小的内容高度，导致
            # 白框装不下全部内容。activate() 让 edit.width() 更新到当前
            # 布局分配的实际宽度，再据此排版才准确。
            self.layout.activate()
            probe = QTextDocument()
            probe.setDefaultFont(edit.font())
            probe.setDocumentMargin(edit.document().documentMargin())
            # 按无滚动条时的可用宽度排版（白框加高后滚动条会消失，文字换行会更少）。
            # 注意：不能直接用 edit.width() —— setText 后它可能还是上一轮的旧值，
            # 而本函数末尾会用 sizeHint 调整窗口尺寸，edit.width() 到那时才是
            # 最终值。用旧宽度排版会得到偏小的内容高度，白框装不下全部内容。
            # 改用 sizeHint().width() 推算最终可用宽度，排版结果才准确。
            _m = self.layout.contentsMargins()
            _target_w = self.sizeHint().width()
            vw = max(_target_w - _m.left() - _m.right() - 2 * edit.frameWidth(), 0)
            probe.setTextWidth(vw)
            probe.setPlainText(edit.toPlainText())
            natural = int(probe.size().height())
            m = edit.contentsMargins()
            natural = natural + m.top() + m.bottom() + 2
            el = int(round(float(getattr(self, 'event_length', 560) or 560)))
            target_box = max(natural, el)
            screen = QApplication.primaryScreen()
            if screen is not None:
                cap_box = max(screen.availableGeometry().height() - 60 - others, 60)
                target_box = min(target_box, cap_box)
            # 同 allow_grow 分支：基准必须精确，否则白框会被窗口下限撑大
            self._fit_h = others + max(target_box, 60)

        # 白框分到「基准窗口高度里除其它控件外的全部」
        base_h = getattr(self, '_fit_h', None) or self.height()
        avail = max(base_h - others, 60)
        edit.setFixedHeight(avail)
        self.layout.activate()
        # activate() 会把窗口最小高度重新锁成「其它控件+白框」（实测 minH=540），
        # 导致拖右下角 grip 只能拉大、永远拉不小——resize 被最小值静默钳住。
        # 每次排版后解除，让 grip 两个方向都能拖；过小则由 resizeEvent 里
        # 白框 60px 下限自然托底。
        self.setMinimumSize(1, 1)

        # 让「滑动组件」(grip) 始终贴在白框/窗口右下角
        if getattr(self, 'size_grip', None) is not None:
            cw = self.central_widget
            self.size_grip.move(max(cw.width() - self.size_grip.width() - 2, 0),
                                max(cw.height() - self.size_grip.height() - 2, 0))

        if not self.isVisible():
            return
        # 窗口高度跟随基准（可增可减：icon 变小、event_length 变小都要收得回）
        target = self.sizeHint()
        if abs(target.height() - self.height()) > 1 or abs(target.width() - self.width()) > 1:
            self._resize_window(target.width(), target.height())
        # 注意：**不要**用 self.height() 覆盖 _fit_h。
        # _fit_h 是「其它控件 + 用户设定高度」的精确基准，而 self.height() 是
        # sizeHint 落地后的结果，两者会差出一截（实测设 150 拿到 169），
        # 一旦覆盖，下一轮排版就以偏差值为基准，误差会一直累积。
        # 窗口尺寸变化由上面的 _resize_window 负责跟进，基准保持精确值。

    def _resize_window(self, w, h):
        """程序内主动改窗口高度（会被 resizeEvent 识别，不算用户手动调整）。"""
        self.setMinimumHeight(0)
        self._programmatic_resize = True
        try:
            self.resize(w, h)
        finally:
            self._programmatic_resize = False

    def eventFilter(self, obj, ev):
        """跟踪用户是否正在拖右下角 grip。

        grip 的 mouseMove 会调用窗口 resize；resizeEvent 里用 _grip_dragging
        区分「用户拖拽」（要反推 event_length）和「启动/系统等被动 resize」
        （绝不能改写用户存的设置值）。用事件过滤器而不是查鼠标物理状态，
        真实拖拽和测试里的合成事件都能覆盖。"""
        if obj is getattr(self, 'size_grip', None):
            if ev.type() == QEvent.MouseButtonPress:
                self._grip_dragging = True
            elif ev.type() == QEvent.MouseButtonRelease:
                self._grip_dragging = False
        return super().eventFilter(obj, ev)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 只有用户拖右下角 grip 触发的 resize 才改排版基线（_fit_h）并反推
        # 「事件框长度」；show/窗口管理器等被动 resize 绝不能动 —— 实测 show
        # 时会把基线打回旧窗口高度（450），盖掉按 event_length 算好的基准，
        # 启动白框就矮一截。被动 resize 只重排，不改基准。
        if (not getattr(self, '_programmatic_resize', False)
                and getattr(self, '_grip_dragging', False)):
            new_h = event.size().height()
            self._fit_h = new_h
            others = self._other_widgets_height()
            new_el = max(new_h - others, 60)
            cur_el = int(round(float(getattr(self, 'event_length', 0) or 0)))
            if abs(new_el - cur_el) > 1:
                self.event_length = new_el
                # 手动调过就把「自动加高」让位给用户：只要用户拖过小蓝块，
                # 框高就以他为准，正文变化不再把它顶回去（否则刚拖小就弹高）。
                if getattr(self, 'auto_fit_box', True):
                    self.auto_fit_box = False
                if getattr(self, '_el_save_timer', None) is not None:
                    self._el_save_timer.start(400)
        # 窗口尺寸变化导致文字换行变化时，重新计算内容高度
        self._fit_content_height()

    def _persist_event_length(self, value):
        """把「事件框长度」写回 user_data.json。

        关键：只写 event_length 这一个键（save_user_settings 会自动合并文件里
        已有的其它键）。绝不能把 self.user_settings 整个写回去 —— 那是主窗口
        启动时读的旧快照，设置窗口里改完还没重启的其它设置会被旧值盖掉，
        表现就是「调完字体，其它设置又回到默认了」。
        """
        try:
            v = int(round(float(value)))
            # 连同「手动优先」标志一起存：手动调过框高之后，重启仍然按手动来，
            # 不会被自动加高顶回去（否则这个状态只在本次运行内有效）。
            save_user_settings(get_settings_dir(), {
                'event_length': v,
                'auto_fit_box': bool(getattr(self, 'auto_fit_box', True)),
            })
            print("已保存事件框长度 event_length =", v)
        except Exception as e:
            print("持久化 event_length 失败:", e)
            _log_error("持久化 event_length 失败: %s" % e)

    def save_window_position(self):
        """把当前窗口的左上角存成「屏幕相对坐标」(0~1)。

        用相对坐标而不是绝对像素 —— 跨分辨率（1920x1080 → 1366x768）
        或换显示器时，窗口会按比例出现在相同的「相对位置」上。
        """
        screen = QApplication.primaryScreen()
        if screen is None:
            return False
        geom = screen.availableGeometry()
        sw, sh = geom.width(), geom.height()
        if sw <= 0 or sh <= 0:
            return False
        pos = self.pos()
        rel_x = max(0.0, min(1.0, pos.x() / sw))
        rel_y = max(0.0, min(1.0, pos.y() / sh))
        ok = save_user_settings(get_settings_dir(), {
            'pos_rel_x': round(rel_x, 4),
            'pos_rel_y': round(rel_y, 4),
        })
        if ok:
            print("已保存开机位置 pos_rel=(%.3f, %.3f) → 绝对=(%d, %d) 屏幕=%dx%d" % (
                rel_x, rel_y, pos.x(), pos.y(), sw, sh))
        return ok

    def restore_window_position(self):
        """按 saved pos_rel_x/pos_rel_y 恢复窗口位置，并做屏幕可见性校验。

        校验通过才移动；校验失败（窗口完全落到屏幕外）则放弃恢复、
        让 Qt 保持默认初始位置 —— 多显示器插拔/分辨率变化时不会出现
        「窗口启动后消失在屏幕外」的幽灵问题。
        """
        cfg = load_user_settings(get_settings_dir())
        rx = cfg.get('pos_rel_x')
        ry = cfg.get('pos_rel_y')
        if rx is None or ry is None:
            return  # 从没保存过，用默认位置
        try:
            rx = float(rx)
            ry = float(ry)
        except (TypeError, ValueError):
            return
        if not (0.0 <= rx <= 1.0 and 0.0 <= ry <= 1.0):
            return

        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geom = screen.availableGeometry()
        sw, sh = geom.width(), geom.height()
        if sw <= 0 or sh <= 0:
            return
        target_x = int(round(rx * sw))
        target_y = int(round(ry * sh))

        # 等窗口 show() + _fit_content_height() 完成后 self.width()/height()
        # 才是最终值；现在先 move 到目标位置，让 Qt 布局完成后再做校验。
        self.move(target_x, target_y)

        # 用 singleShot 等布局稳定后再校验可见性：窗口宽度/高度此刻还没最终确定
        QTimer.singleShot(0, self._validate_position_visible)

    def _validate_position_visible(self):
        """恢复位置后检查窗口是否真的落在屏幕可见区域内。

        失败则放弃本次恢复（Qt 的默认位置总比屏幕外好），并清掉配置里的坏值 ——
        下次启动不会再被同一份坏数据坑一次。"""
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geom = screen.availableGeometry()
        rect = self.frameGeometry()
        # 窗口至少要有一个角落在屏幕内才算有效（无边框窗口允许轻微出界）
        if not rect.intersects(geom):
            print("恢复位置校验失败：窗口完全落在屏幕外，放弃恢复")
            # 清掉坏值，避免每次启动都被同一份数据坑
            save_user_settings(get_settings_dir(), {
                'pos_rel_x': None, 'pos_rel_y': None,
            })

    @staticmethod
    def _parse_event_date(time_str):
        """解析「月.日」类日期，规则与 analysis_excel 保持一致。
        返回 (month:int, day:int) 或 None。"""
        s = str(time_str).strip()
        if not s or s.lower() == 'nan':
            return None
        month = None
        day = None
        for sep in ('.', '/', '-'):
            if sep in s:
                parts = s.split(sep)
                if len(parts) >= 2:
                    month = parts[0].strip()
                    day = parts[1].strip()
                    break
        if month is None and s.isdigit() and len(s) in (3, 4):
            if len(s) == 3:
                month, day = s[0], s[1:]
            else:
                month, day = s[:2], s[2:]
        if month is not None and str(day).startswith('.'):
            day = str(day)[1:]
        try:
            int_month, int_day = int(month), int(day)
        except (TypeError, ValueError):
            return None
        if 1 <= int_month <= 12 and 1 <= int_day <= 31:
            return int_month, int_day
        return None

    def validate_and_load_data(self):
        """程序启动时自动校验上次使用的 Excel 数据：
        - 数据合法：直接加载到 self.events，不弹窗；
        - 存在问题：跳过坏行、加载其余数据，弹窗列出问题明细。"""
        import pandas as pd

        user_data_file = os.path.join(get_settings_dir(), 'user_data.json')
        if not os.path.exists(user_data_file):
            return  # 从未导入过，无需校验

        try:
            with open(user_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            paths = data.get('user_data', []) if isinstance(data, dict) else []
            if not paths:
                return
            file_path = paths[0]
        except Exception as e:
            QMessageBox.warning(self, '启动数据校验', f'读取 user_data.json 失败：\n{e}')
            return

        if not os.path.isabs(file_path):
            file_path = os.path.abspath(os.path.join(self.dir_path, file_path))
        if not os.path.exists(file_path):
            QMessageBox.warning(
                self, '启动数据校验',
                f'上次使用的 Excel 文件不存在：\n{file_path}\n\n请通过“打开日历”重新选择文件。')
            return

        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            QMessageBox.critical(
                self, '启动数据校验',
                f'Excel 文件读取失败：\n{e}\n\n请检查文件是否损坏或正被其他程序占用。')
            return

        # 列识别（与 analysis_excel 规则一致）
        time_column = None
        things_column = None
        for col in df.columns:
            cl = str(col).lower()
            if 'time' in cl or '日期' in str(col) or 'date' in cl:
                time_column = col
                break
        if 'things' in df.columns:
            things_column = 'things'
        else:
            for col in df.columns:
                cl = str(col).lower()
                if 'thing' in cl or '事件' in str(col) or 'content' in cl:
                    things_column = col
                    break

        if time_column is None or things_column is None:
            QMessageBox.critical(
                self, '启动数据校验',
                'Excel 缺少必要的列：需要包含 time 和 things 两列。\n'
                f'当前列名：{df.columns.tolist()}\n\n请通过“打开日历”修正文件。')
            return

        problems = []
        loaded = []
        times_list = df[time_column].astype(str).tolist()
        things_list = df[things_column].tolist()
        for row_no, (raw_time, raw_thing) in enumerate(zip(times_list, things_list), start=2):
            time_s = str(raw_time).strip()
            thing_empty = (bool(pd.isna(raw_thing))
                           or str(raw_thing).strip() == ''
                           or str(raw_thing).strip().lower() == 'nan')
            if (not time_s or time_s.lower() == 'nan') and thing_empty:
                continue  # 整行为空，跳过，不计为错误

            parsed = self._parse_event_date(raw_time)
            if parsed is None:
                problems.append(f'第 {row_no} 行：日期 “{time_s}” 无法识别（应为 月.日，如 9.26）')
                continue
            if thing_empty:
                problems.append(f'第 {row_no} 行：待办内容为空（日期 {parsed[0]}.{parsed[1]}）')
                continue

            month, day = parsed
            loaded.append({
                'month': f'{month:02d}',
                'day': f'{day:02d}',
                'things': str(raw_thing).strip()
            })

        def problem_text(probs):
            detail = '\n'.join(probs[:10])
            if len(probs) > 10:
                detail += f'\n…等共 {len(probs)} 个问题'
            return detail

        if not loaded:
            QMessageBox.critical(
                self, '启动数据校验',
                f'文件中没有可加载的有效待办数据，共发现 {len(problems)} 个问题：\n\n'
                + problem_text(problems))
            return

        # 加载有效数据，主窗口下一次倒计时刷新即会显示
        self.events = loaded
        print(f"启动数据校验：加载 {len(loaded)} 条待办，发现 {len(problems)} 个问题")

        if problems:
            QMessageBox.warning(
                self, '启动数据校验',
                f'已加载 {len(loaded)} 条有效待办；\n'
                f'同时发现 {len(problems)} 个问题，对应行已跳过：\n\n'
                + problem_text(problems))
    
    def check_update_from_menu(self):
        """右键菜单「检查更新…」：子线程请求远端 version.json，信号回主线程弹窗。

        跨版本（PySide2/PySide6）安全方案：
          工作线程 → emit Signal(bool, str, str, str) → Qt 自动排队 → 主线程槽函数弹窗
        完全避开"在非 Qt 线程调 QMessageBox"这种 UB。
        """
        import threading

        # 槽函数 —— 只在主线程被调（由 Signal 自动排队）
        def _on_result(is_newer, remote_ver, info_json, err):
            try:
                info = json.loads(info_json) if info_json else {}
            except Exception:
                info = {}

            # 用漂亮的自定义 UpdateDialog 代替 QMessageBox
            try:
                dlg = UpdateDialog(
                    parent=self,
                    local_ver=APP_VERSION,
                    remote_ver=remote_ver or "-",
                    info=info,
                    is_newer=is_newer,
                    error=err,
                )
                # 居中显示（相对主窗口，没父窗口就相对屏幕）
                if self.isVisible():
                    cp = self.frameGeometry().center()
                    dlg.move(cp.x() - dlg.width() // 2, cp.y() - dlg.height() // 2)
                else:
                    from PySide2.QtWidgets import QApplication as _QA
                    screen = _QA.primaryScreen().availableGeometry()
                    dlg.move(screen.center().x() - dlg.width() // 2,
                             screen.center().y() - dlg.height() // 2)
                dlg.exec_()
            except Exception as e:
                # 兜底：如果 UpdateDialog 构造失败（极少发生），降级到 QMessageBox
                if err:
                    QMessageBox.warning(self, "检查更新",
                        "检查新版本时出错：\n\n%s\n\n本地版本：%s" % (err, APP_VERSION))
                elif is_newer:
                    QMessageBox.information(self, "检查更新",
                        "有新版本！本地 %s → 最新 %s\n\n%s" % (
                            APP_VERSION, remote_ver,
                            (info.get("download_url", "") if isinstance(info, dict) else "")))
                else:
                    QMessageBox.information(self, "检查更新",
                        "当前已是最新版本 %s" % APP_VERSION)
                _log_error("UpdateDialog 构造失败: %s" % e)

        self._update_checked.connect(_on_result)

        def _worker():
            try:
                is_newer, remote_ver, info, err = check_update_available(timeout=8)
                info_json = json.dumps(info, ensure_ascii=False) if isinstance(info, dict) else ""
            except Exception as e:
                is_newer, remote_ver, info_json, err = False, "", "", str(e)
            # Signal.emit 跨线程安全：Qt 自动把调用投回主线程事件队列
            try:
                self._update_checked.emit(is_newer, remote_ver, info_json, err)
            except Exception:
                # 万一 emit 也有问题，兜底：直接在工作线程弹窗（PySide6 某些构造下可用）
                try:
                    _on_result(is_newer, remote_ver, info_json, err)
                except Exception:
                    pass

        threading.Thread(target=_worker, daemon=True).start()

    def button_quit(self, event=None):
        """彻底退出：关闭所有窗口并保证进程一定结束（exe 立刻解除占用）。

        背景：主窗口改成 Qt.Tool（不占任务栏）后，用户没法再从任务栏
        「右键 → 关闭窗口」；如果退出不彻底（比如日历/设置窗口的 Tk 主循环
        还卡着，或悬浮球面板没关），进程会残留 —— 删除或替换 exe 时就会
        提示「文件正在使用」。
        所以这里分三步：优雅关闭所有窗口 → 退出 Qt 事件循环 →
        2 秒后若进程仍未退出则强制结束（看门狗线程）。
        """
        self.menu.clear()
        try:
            app = QApplication.instance()
            if app is not None:
                # 关闭所有顶层窗口（主窗口、悬浮球、待办面板等）
                for w in app.topLevelWidgets():
                    try:
                        w.close()
                    except Exception:
                        pass
                app.quit()
        except Exception:
            pass

        # 兜底看门狗：正常退出路径下解释器先结束，这个守护线程随之消亡、
        # 不会触发（也不影响 PyInstaller 临时目录的正常清理）；
        # 一旦有 Tk mainloop 之类卡住退出，2 秒后强制结束进程。
        import threading

        def _force_exit():
            time.sleep(2.0)
            os._exit(0)

        try:
            threading.Thread(target=_force_exit, daemon=True).start()
        except Exception:
            pass
    
    def update_countdown(self):
        """更新倒计时显示"""
        # 实时更新时间变量

        import time
        old_hour = self.time_hour
        
        self.time_day = int(time.strftime("%d", time.localtime()))
        self.time_month = int(time.strftime("%m", time.localtime()))
        self.time_year = int(time.strftime("%Y", time.localtime()))
        self.time_hour = int(time.strftime("%H", time.localtime()))
        self.time_minute = int(time.strftime("%M", time.localtime()))
        self.time_second = int(time.strftime("%S", time.localtime()))
        
        # 只有在小时变化时才更新问候语
        if self.time_hour != old_hour:
            if self.time_hour < 12:
                self.current_time_period = "早上"
                self.current_time_period = random.choice(self.good_morning)
            elif 12 <= self.time_hour < 18:
                self.current_time_period = "下午"
                self.current_time_period = random.choice(self.good_afternoon)
            else:
                self.current_time_period = "晚上"
                self.current_time_period = random.choice(self.good_night)
            # 检查如果大于6行，则在第6行添加换行符
            if len(self.current_time_period) > 6:
                self.current_time_period = self.current_time_period[:6] + "\n" + self.current_time_period[6:]
        
        if not self.events:
            self.countdown_label.setText(f"{self.time_year}/{self.time_month}/{self.time_day}\n {self.time_hour}:{self.time_minute}:{self.time_second} \n\n{self.current_time_period}")
            self.content_label.setText("请从Excel文件中导入事件数据")
            self._fit_content_height()
            return
        
        # 获取当前时间
        current_time = QDateTime.currentDateTime()
        
        # 计算所有事件的时间差
        upcoming_events = []
        today_events = []
        expired_events = []
        for event in self.events:
            # 解析事件时间
            event_month = int(event['month'])
            event_day = int(event['day'])
            
            # 创建事件日期时间对象（假设是今年）
            event_time = QDateTime(current_time.date().year(), event_month, event_day, 0, 0, 0)
            
            # 检查是否是当天事件
            is_today = (event_month == current_time.date().month() and event_day == current_time.date().day())
            
            if is_today:
                # 当天事件
                today_events.append({
                    'event': event,
                    'seconds_diff': 0
                })
            else:
                # 计算时间差
                seconds_diff = current_time.secsTo(event_time)
                
                if seconds_diff > 0:
                    # 未来的事件
                    upcoming_events.append({
                        'event': event,
                        'seconds_diff': seconds_diff
                    })
                else:
                    # 已过期（日期在过去）。按用户要求：主窗口也要能看到，
                    # 只标注出来，删除仍由日历窗口的「标记为已完成」手动完成。
                    expired_events.append({
                        'event': event
                    })
        
        # 倒计时标题：优先今天，其次最近的未来事件，否则仅剩过期事件
        if today_events:
            countdown_text = f"今天是 {self.time_year}/{self.time_month}/{self.time_day}\n今天的事件:"
        elif upcoming_events:
            upcoming_events.sort(key=lambda x: x['seconds_diff'])
            nearest_event = upcoming_events[0]['event']
            min_seconds = upcoming_events[0]['seconds_diff']
            days = min_seconds // (24 * 3600)
            hours = (min_seconds % (24 * 3600)) // 3600
            minutes = (min_seconds % 3600) // 60
            seconds = min_seconds % 60
            countdown_text = f"距离 {nearest_event['month']}.{nearest_event['day']} 还有"
        else:
            countdown_text = f"当前时间\n{self.time_year}/{self.time_month}/{self.time_day}\n{self.time_hour}:{self.time_minute}:{self.time_second} \n\n{self.current_time_period}"
        self.countdown_label.setText(countdown_text)

        # 组装正文：今天的事件 / 未来事件 / 已过期事件 ——
        # 已过期事件始终在主窗口可见（用户要求），只标注出来，删除仍由
        # 日历窗口的「标记为已完成」手动完成。
        content = ""
        if today_events:
            today_events.sort(key=lambda x: x['event']['day'])
            for today_event in today_events:
                content += f"\n• {today_event['event']['things']}"

            if upcoming_events:
                upcoming_events.sort(key=lambda x: x['seconds_diff'])
                content += f"\n\n未来事件:"
                # 未来事件全部列出（原来只取前 3 条再拼一句「还有 N 个更多事件」，
                # 用户实测「框框拉长也只显示四五个、进度条拉不到最后一个」，
                # 根因就是这条硬编码截断 —— 框再长，第 4 条以后根本不在正文里。
                for future_event in upcoming_events:
                    event = future_event['event']
                    seconds_diff = future_event['seconds_diff']
                    days = seconds_diff // (24 * 3600)
                    hours = (seconds_diff % (24 * 3600)) // 3600
                    minutes = (seconds_diff % (24 * 3600)) // 60
                    seconds = seconds_diff % 60
                    if days > 0:
                        time_str = f"{days+1}天后"
                    elif hours > 0:
                        time_str = f"{hours}小时后"
                    elif minutes > 0:
                        time_str = f"{minutes}分钟后"
                    else:
                        time_str = f"{seconds}秒后"
                    # 日期不由程序添加（用户自己在事件文字里写日期，跟以前一样），
                    # 只保留「（X天后）」相对时间
                    content += f"\n• {event['things']}（{time_str}）"

        elif upcoming_events:
            upcoming_events.sort(key=lambda x: x['seconds_diff'])
            nearest_event = upcoming_events[0]['event']
            min_seconds = upcoming_events[0]['seconds_diff']
            days = min_seconds // (24 * 3600)
            hours = (min_seconds % (24 * 3600)) // 3600
            minutes = (min_seconds % 3600) // 60
            seconds = min_seconds % 60
            content = f"• {nearest_event['things']}\n\n倒计时：\n{days}天 {hours}时 {minutes}分 {seconds}秒"
            if len(upcoming_events) > 1:
                content += "\n\n后续事件："
                for i, future_event in enumerate(upcoming_events[1:], 1):
                    event = future_event['event']
                    seconds_diff = future_event['seconds_diff']
                    days_diff = seconds_diff // (24 * 3600)
                    hours_diff = (seconds_diff % (24 * 3600)) // 3600
                    minutes_diff = (seconds_diff % 3600) // 60
                    if days_diff > 0:
                        time_str = f"{days_diff+1}天后"
                    elif hours_diff > 0:
                        time_str = f"{hours_diff}小时后"
                    elif minutes_diff > 0:
                        time_str = f"{minutes_diff}分钟后"
                    else:
                        time_str = "即将开始"
                    content += f"\n• {event['things']}（{time_str}）"
        else:
            content = "请导入新的事件数据\n\n"

        if expired_events:
            expired_events.sort(key=lambda x: (int(x['event']['month']), int(x['event']['day'])))
            if content and not content.endswith("\n\n"):
                content += "\n\n"
            content += "已过期事件（需手动清除）:" + "".join(
                f"\n• {ev['event']['month']}.{ev['event']['day']} : {ev['event']['things']}"
                for ev in expired_events)

        # 正文只在内容真的变化时才刷新：
        # 原来每秒都 setText（会把滚动条打回去再恢复），用户正在拖滚动条时
        # 每秒被程序抢一次，表现为「进度条拉不到最后 / 点不到下面的东西」。
        # 文字没变就完全不动白框 —— 滚动条停在哪就是哪，排版零扰动。
        if content != self.content_label.toPlainText():
            # 保存当前滚动位置
            scroll_pos = self.content_label.verticalScrollBar().value()
            # 更新内容
            self.content_label.setText(content)
            # 恢复滚动位置
            self.content_label.verticalScrollBar().setValue(scroll_pos)
            self._last_content_text = content
            # 延迟到下一轮事件循环再排版：setText 后文档布局/滚动条状态要等
            # 一轮事件处理才稳定，立即测量会拿到旧布局的高度（实测从 12 条
            # 缩到 6 条时量到的还是旧高度，白框就不会回落）。
            QTimer.singleShot(0, lambda: self._fit_content_height(fit_content=True))
    
    def button_open_calendar(self):
            import tkinter as tk
            from tkinter import ttk
            import calendar
            from tkinter import filedialog
            from tkinter import messagebox
            import json
            
            def get_answer(question):
                # 调用AI模型获取回答
                try:
                    from zai._client import ZhipuAiClient
                    
                    client = ZhipuAiClient(api_key=os.environ.get('ZHIPUAI_API_KEY', ''))
                    response = client.chat.completions.create(
                        model="glm-4.7-flash",
                        messages=[
                            {"role": "user", "content": question},
                            {"role": "assistant", "content": "回答尽量简短100字，说说你对这个的看法，千万避免长时间思考"},
                            {"role": "user", "content": "帮我说说这个的好处,富有互动性"}
                            ],
                        thinking={
                            "type": "enabled",    # 启用深度思考模式
                        },
                        
                        max_tokens=1000,          # 最大输出tokens
                        temperature=5.0           # 控制输出的随机性
                    )

                    answer = response.choices[0].message.content
                    return f"\n\nAI回答: {answer}"
                except Exception as e:
                    return f"\n\nAI回答获取失败: {str(e)}"
            
            def mark_as_completed(day, month):
                # 检查事件是否存在
                # 查找匹配的事件
                event_found = None
                for event in self.events:
                    if int(event['month']) == month and int(event['day']) == day:
                        event_found = event
                        break
                
                if event_found:
                    if not messagebox.askokcancel("确认", f"确定将 {month}月{day}日 的事件标记为已完成吗？\n删除后不可恢复！！！"):
                        return

                    # 标记为已完成
                    event_found['completed'] = True
                    # 如果事件描述中包含*，替换为+
                    if '*' in event_found['things']:
                        event_found['things'] = event_found['things'].replace('*', '+')
                        self.delete_events[(day, month)] = event_found['things']
                    self.events.remove(event_found)
                    # ── 删除后立即写回 Excel，让刷新/重启不再复活 ──
                    def _on_del_err(msg):
                        messagebox.showerror("已删除但无法写入 Excel",
                            f"事件已从本窗口删除，但无法同步到 Excel：\n\n{msg}\n\n"
                            "最常见原因：Excel 文件正在被 Excel 程序打开。")
                    sync_events_to_excel(self, on_error=_on_del_err)
                    # 刷新日历显示，更新*标记
                    show_calendar()
                    # 刷新事件详情显示
                    refresh_text()
                else:
                    # 事件不存在
                    messagebox.showwarning("警告", f"日期 {month}月{day}日 不存在事件")
                    return

            def show_calendar(*args):
                def update_answer(question, month, day):
                    import time
                    import json
                    
                    # 解除锁定
                    self.text.config(state=tk.NORMAL)
                    
                    # 清空文本框
                    self.text.delete(1.0, tk.END)
                    
                    # 插入标题
                    self.text.insert(tk.END, f"{month}月{day}日的事件:\n", "header")
                    
                    # 显示用户的事情
                    if question:
                        self.text.insert(tk.END, f"• {question}\n\n", "event")
                    
                    data = str(month)+'.'+str(day)
                    
                    # 日期特征分析
                    def get_date_features(month, day):
                        features = []
                        
                        # 季节判断
                        if 3 <= month <= 5:
                            features.append("春季")
                        elif 6 <= month <= 8:
                            features.append("夏季")
                        elif 9 <= month <= 11:
                            features.append("秋季")
                        else:
                            features.append("冬季")
                        
                        # 节假日判断
                        holidays = {
                            (1, 1): "元旦",
                            (2, 14): "情人节",
                            (3, 8): "妇女节",
                            (4, 1): "愚人节",
                            (4, 4): "清明节",
                            (5, 1): "劳动节",
                            (6, 1): "儿童节",
                            (8, 1): "建军节",
                            (9, 10): "教师节",
                            (10, 1): "国庆节",
                            (12, 25): "圣诞节"
                        }
                        
                        if (month, day) in holidays:
                            features.append(f"{holidays[(month, day)]}节")
                        
                        # 特殊日期
                        if month == 12 and day >= 20:
                            features.append("年末")
                        elif month == 1 and day <= 10:
                            features.append("年初")
                        
                        return features
                    
                    # 直接调用get_answer获取新的AI回答
                    if self.ai_enable:
                        # 生成包含日期特征的提示词
                        date_features = get_date_features(month, day)
                        feature_text = "，".join(date_features)
                        enhanced_question = f"请对{month}月{day}日（{feature_text}）的事件进行评价：{question}"
                        
                        print(f"生成新的AI回答: {data}")
                        ai_answer = get_answer(enhanced_question)
                        
                        # 验证AI回答的格式与内容完整性
                        if not ai_answer or not isinstance(ai_answer, str) or len(ai_answer.strip()) == 0:
                            print("AI回答格式错误或内容为空")
                            ai_answer = "AI回答生成失败，请稍后重试"
                        else:
                            # 确保回答内容完整
                            ai_answer = ai_answer.strip()
                    else:
                        ai_answer = "AI解析已禁用"
                    
                    # 确保answers_json包含所有现有数据
                    if not hasattr(self, 'answers_json') or self.answers_json is None:
                        self.answers_json = {}
                    
                    # 更新AI回答文件
                    try:
                        # 准确定位到目标JSON文件的指定存储路径
                        ai_file_path = os.path.join(self.dir_path, 'ai_awswers.json')
                        print(f"更新AI回答文件路径: {ai_file_path}")
                        
                        # 加载现有数据，确保不影响其他数据的完整性
                        if os.path.exists(ai_file_path):
                            try:
                                with open(ai_file_path, 'r', encoding='utf-8') as f:
                                    file_content = f.read().strip()
                                    if file_content:
                                        try:
                                            existing_data = json.loads(file_content)
                                            # 确保existing_data是字典类型
                                            if isinstance(existing_data, dict):
                                                self.answers_json.update(existing_data)
                                                print(f"加载现有数据成功，共 {len(existing_data)} 条记录")
                                            else:
                                                print("现有数据格式错误，使用空数据")
                                        except json.JSONDecodeError as json_e:
                                            print(f"JSON解析失败: {json_e}")
                                            # 保留当前数据，不覆盖
                            except Exception as load_e:
                                print(f"加载现有数据失败: {load_e}")
                        
                        # 保存更新前的数据备份，以防写入失败
                        backup_data = self.answers_json.copy()
                        
                        # 更新数据
                        self.answers_json.update({data: ai_answer})
                        print(f"更新数据成功: {data} -> {ai_answer[:50]}...")
                        
                        # 执行文件写入操作并确认保存成功
                        try:
                            with open(ai_file_path, 'w', encoding='utf-8') as f:
                                f.write(json.dumps(self.answers_json, ensure_ascii=False, indent=4))
                            # 验证文件写入成功
                            if os.path.exists(ai_file_path):
                                file_size = os.path.getsize(ai_file_path)
                                print(f"文件写入成功，大小: {file_size} 字节")
                            else:
                                print("文件写入失败，文件不存在")
                                # 回退到备份数据
                                self.answers_json = backup_data
                        except Exception as write_e:
                            print(f"文件写入失败: {write_e}")
                            # 回退到备份数据
                            self.answers_json = backup_data
                    except Exception as e:
                        print(f"更新AI回答文件失败: {e}")
                        # 回退到内存缓存
                        if not hasattr(self, 'ai_awswers'):
                            self.ai_awswers = {}
                        self.ai_awswers[data] = ai_answer
                        print(f"回退到内存缓存: {data}")
                        # 以具体日期为索引文件中保存AI回答
                    
                    # 插入AI回答
                    self.text.insert(tk.END, ai_answer, "ai_answer")
                    
                    # 锁定文本框
                    self.text.config(state=tk.DISABLED)
                    
                    # 提供操作成功的反馈信息
                    messagebox.showinfo("成功", f"{month}月{day}日的AI回答更新成功！")
                    
                # 获取年份和月份值，处理空值情况
                year_str = year_var.get().strip()
                month_str = month_var.get().strip()
                
                # 如果值为空，不进行转换和显示
                if not year_str or not month_str:
                    return
                if '*' in month_str:
                    month_str = month_str.replace('*', '')

                try:
                    year = int(year_str)
                    month = int(month_str)
                except ValueError:
                    # 如果转换失败，不执行后续操作
                    return
                
                # 清空日期网格容器（只清日期格子，标题/星期/图例是静态的）
                for widget in grid_frame.winfo_children():
                    widget.destroy()

                # 用 calendar.Calendar 获取 7 列宽的月历（从周日开始）
                _cal = calendar.Calendar(firstweekday=6)  # 6=Sunday start
                weeks = _cal.monthdatescalendar(year, month)

                today_bd = (self.time_year, self.time_month, self.time_day)

                for r, week in enumerate(weeks):
                    for c, d in enumerate(week):
                        day = d.day
                        is_this_month = d.month == month

                        if not is_this_month:
                            # 上/下月灰字占位
                            cell = tk.Label(grid_frame, text=str(day),
                                            bg=_CAL_COLOR['card_bg'],
                                            fg='#d0d6e0',
                                            font=_CAL_FONT['date_num'],
                                            anchor="center",
                                            relief="flat", bd=0,
                                            padx=2, pady=_CAL_SPACE['date_pad'])
                        elif (d.year, d.month, d.day) == today_bd:
                            # 今天：主色圆底白字
                            cell = tk.Label(grid_frame, text=str(day),
                                            bg=_CAL_COLOR['today_bg'],
                                            fg=_CAL_COLOR['today_fg'],
                                            font=_CAL_FONT['date_num'],
                                            anchor="center",
                                            relief="flat", bd=0,
                                            padx=2, pady=_CAL_SPACE['date_pad'],
                                            cursor="hand2")
                        else:
                            # 普通天：白底，hover 主色淡
                            bg = _CAL_COLOR['card_bg']
                            fg = _CAL_COLOR['text']
                            # 查有没有事件
                            for ev in self.events:
                                if int(ev.get('month', 0)) == month and int(ev.get('day', 0)) == day:
                                    bg = _CAL_COLOR['has_event_bg']
                                    fg = _CAL_COLOR['has_event_fg']
                                    break
                            cell = tk.Label(grid_frame, text=str(day),
                                            bg=bg, fg=fg,
                                            font=_CAL_FONT['date_num'],
                                            anchor="center",
                                            relief="flat", bd=0,
                                            padx=2, pady=_CAL_SPACE['date_pad'],
                                            cursor="hand2")

                        cell.grid(row=r, column=c, sticky="nsew", padx=1, pady=1)

                        if is_this_month:
                            # hover 效果（今天不参与）
                            cell_orig_bg = cell['bg']
                            if cell_orig_bg != _CAL_COLOR['today_bg']:
                                def _enter(e, b=cell, orig=cell_orig_bg):
                                    b.configure(bg=_CAL_COLOR['accent_soft'])
                                def _leave(e, b=cell, orig=cell_orig_bg):
                                    b.configure(bg=orig)
                                cell.bind("<Enter>", _enter)
                                cell.bind("<Leave>", _leave)

                            # 点击 → 显示当天事件
                            cell.bind("<Button-1>",
                                      lambda e, dd=day, mm=month: show_events_for_date(mm, dd))
                            # 右键菜单
                            def _right(e, dd=day, mm=month):
                                ctx = tk.Menu(cal_window, tearoff=0)
                                ctx.add_command(label="√标记为已完成",
                                                command=lambda: mark_as_completed(dd, mm))
                                ctx.add_separator()
                                ctx.add_command(label="➕ 新建事件",
                                                command=lambda: add_event(
                                                    str(mm).zfill(2), str(dd).zfill(2)))
                                question_ = ""
                                for i in self.events:
                                    if int(i.get('day', 0)) == dd:
                                        question_ = i.get('things', '')
                                        break
                                if question_:
                                    ctx.add_command(label='更新AI回答',
                                                    command=lambda q=question_: update_answer(q, mm, dd))
                                ctx.post(e.x_root, e.y_root)
                            cell.bind("<Button-3>", _right)

            def show_events_for_date(month, day):
                
                """显示指定日期的事件"""
                import time
                
                # 解除锁定
                self.text.config(state=tk.NORMAL)
                
                # 清空文本框
                self.text.delete(1.0, tk.END)
                
                # 日期特征分析
                def get_date_features(month, day):
                    features = []
                    
                    # 季节判断
                    if 3 <= month <= 5:
                        features.append("春季")
                    elif 6 <= month <= 8:
                        features.append("夏季")
                    elif 9 <= month <= 11:
                        features.append("秋季")
                    else:
                        features.append("冬季")
                    
                    # 节假日判断
                    holidays = {
                        (1, 1): "元旦",
                        (1, 25): "小年（北方）",
                        (1, 29): "小年（南方）",
                        (2, 14): "情人节",
                        (2, 19): "雨水（节气）",
                        (3, 8): "妇女节",
                        (3, 12): "植树节",
                        (4, 1): "愚人节",
                        (4, 4): "清明节",
                        (4, 22): "地球日",
                        (5, 1): "劳动节",
                        (5, 4): "青年节",
                        (5, 12): "护士节",
                        (6, 1): "儿童节",
                        (6, 5): "环境日",
                        (6, 21): "夏至（节气）",
                        (7, 1): "建党节",
                        (8, 1): "建军节",
                        (8, 7): "立秋（节气）",
                        (9, 10): "教师节",
                        (9, 23): "秋分（节气）",
                        (10, 1): "国庆节",
                        (10, 31): "万圣节前夜",
                        (11, 11): "光棍节",
                        (12, 20): "大雪（节气）",
                        (12, 25): "圣诞节",
                        (12, 13): "国家公祭日"
                    }
                    
                    if (month, day) in holidays:
                        features.append(f"{holidays[(month, day)]}节")
                    
                    # 特殊日期
                    if month == 12 and day >= 20:
                        features.append("年末")
                    elif month == 1 and day <= 10:
                        features.append("年初")
                    
                    return features
                
                # 查找匹配的事件
                found_events = []
                for event in self.events:
                    if int(event['month']) == month and int(event['day']) == day:
                        found_events.append(event)
                
                if found_events:
                    # 日期特征
                    date_features = get_date_features(month, day)
                    feature_text = "，".join(date_features)
                    
                    # 插入标题（包含日期特征）
                    self.text.insert(tk.END, f"{month}月{day}日（{feature_text}）的事件:\n", "header")
                    
                    question = ""
                    for event in found_events:
                        # 计算事件距离当前时间的时间差
                        event_month = int(event['month'])
                        event_day = int(event['day'])
                        
                        # 获取当前时间
                        import datetime
                        today = datetime.datetime.now()
                        event_date = datetime.datetime(today.year, event_month, event_day)
                        
                        # 计算时间差
                        time_diff = event_date - today
                        total_seconds = int(time_diff.total_seconds())
                        
                        # 格式化时间差
                        if total_seconds > 0:
                            if total_seconds < 3600:
                                time_str = f"{total_seconds // 60}分钟后"
                            elif total_seconds < 86400:
                                time_str = f"{total_seconds // 3600}小时后"
                            else:
                                time_str = f"{total_seconds // 86400}天后"
                        elif total_seconds < 0:
                            if abs(total_seconds) < 3600:
                                time_str = f"{abs(total_seconds) // 60}分钟前"
                            elif abs(total_seconds) < 86400:
                                time_str = f"{abs(total_seconds) // 3600}小时前"
                            else:
                                time_str = f"{abs(total_seconds) // 86400}天前"
                        else:
                            time_str = "今天"
                        
                        # 按照要求的格式显示事件
                        self.text.insert(tk.END, f"• {event['things']}（{time_str}）\n", "event")
                        question += f"{event['things']}"

                    # AI 解析功能已从 Win7 版移除（打包环境没有 zai 模块），直接返回
                    return
                    # 获取点击的日期
                    data = str(month)+'.'+str(day)
                    # 加载 AI 回答文件
                    self.answers_json = {}
                    ai_file_path = self.dir_path+'/ai_awswers.json'
                    if os.path.exists(ai_file_path):
                        try:
                            with open(ai_file_path, 'r', encoding='utf-8') as f:
                                file_content = f.read().strip()
                                if file_content:
                                    self.answers_json = json.loads(file_content)
                        except Exception as e:
                            print(f"读取AI回答文件失败: {e}")
                    
                    # 生成包含日期特征的提示词
                    enhanced_question = f"请对{month}月{day}日（{feature_text}）的事件进行评价：{question}"
                    
                    # 优先从内存缓存获取
                    if data in self.ai_awswers:
                        print(f"从内存缓存获取AI回答: {data}")
                        ai_answer = self.ai_awswers[data]
                    # 从文件缓存获取
                    elif data in self.answers_json:
                        print(f"从文件缓存获取AI回答: {data}")
                        ai_answer = self.answers_json[data]
                        # 同时更新到内存缓存
                        self.ai_awswers[data] = ai_answer
                    else:
                        ai_answer = get_answer(enhanced_question)
                        try:
                            # 更新数据
                            self.answers_json.update({data: ai_answer})
                            
                            # 写入文件
                            with open(self.dir_path+'/ai_awswers.json', 'w', encoding='utf-8') as f:
                                f.write(json.dumps(self.answers_json, ensure_ascii=False, indent=4))
                        except Exception as e:
                            print(f"更新AI回答文件失败: {e}")
                            # 回退到内存缓存
                            if not hasattr(self, 'ai_awswers'):
                                self.ai_awswers = {}
                            self.ai_awswers[data] = ai_answer
                        # 以具体日期为索引文件中保存AI回答
                    
                    # 插入分隔线
                    self.text.insert(tk.END, "\nAI评价：\n", "header")
                    # 插入AI回答
                    self.text.insert(tk.END, ai_answer, "ai_answer")
                    
                else:
                    # 日期特征
                    date_features = get_date_features(month, day)
                    feature_text = "，".join(date_features)
                    self.text.insert(tk.END, f"{month}月{day}日（{feature_text}）没有相关事件\n", "header")
                
                # 锁定文本框
                self.text.config(state=tk.DISABLED)
                
            def refresh_text():
                """重置text组件为原始显示模式"""
                # 解除锁定
                self.text.config(state=tk.NORMAL)
                
                # 清空文本框
                self.text.delete(1.0, tk.END)
                
                # 按照原始模式显示
                month_data = [event['month'] for event in self.events]
                day_data = [event['day'] for event in self.events]
                things = [event['things'] for event in self.events]
                # 对于时间和日期进行排序，且合并相同日期的事件，
                sorted_events = sorted(zip(month_data, day_data, things))
                # 合并相同日期的事件
                merged_events = {}
                for month, day, thing in sorted_events:
                    if (month, day) not in merged_events:
                        merged_events[(month, day)] = []
                    merged_events[(month, day)].append(thing)
                # 重新排序，确保按日期显示
                sorted_events = sorted(merged_events.items(), key=lambda x: (x[0][0], x[0][1]))
                # 打印排序后的事件
                print("排序后的事件:", sorted_events)
                
                for (month, day), event_list in sorted_events:
                    # 将同一日期的事件合并为一个字符串
                    events_text = "\n  ".join(event_list)
                    self.text.insert(tk.END, f"{month}.{day}:\n  {events_text}\n")
                
                # 锁定文本框
                self.text.config(state=tk.DISABLED)

            def analysis_excel(file_path):
                # 处理相对路径
                if not os.path.isabs(file_path):
                    file_path = os.path.join(self.dir_path, file_path)
                
                if not os.path.exists(file_path):
                    messagebox.showerror("错误", f"文件不存在: {file_path}")
                    return
                    
                import pandas as pd
                try:
                    df = pd.read_excel(file_path)
                    print("原始数据:", file_path)
                    print("列名:", df.columns.tolist())
                    print("数据行数:", len(df))
                    print("前5行数据:", df.head().to_string())
                    
                    # 只保留需要的列（time和things），避免其他列的NaN影响数据
                    required_columns = ['time', 'things']
                    # 检查所需列是否存在
                    existing_columns = [col for col in required_columns if col in df.columns]
                    df = df[existing_columns]
                    
                    # 添加详细的调试信息
                    print("\n=== 列数据详细信息 ===")
                    for col in df.columns:
                        print(f"列名: {col}")
                        print(f"数据类型: {df[col].dtype}")
                        print(f"非空值数量: {df[col].notna().sum()}")
                        print(f"空值数量: {df[col].isna().sum()}")
                        print(f"前10个值: {df[col].head(10).tolist()}")
                        # 检查是否包含空字符串
                        if df[col].dtype == 'object':
                            empty_str_count = (df[col] == '').sum()
                            print(f"空字符串数量: {empty_str_count}")
                            # 尝试将空字符串转换为NaN
                            df[col] = df[col].replace('', pd.NA)
                    
                    # 只删除time和things列都为空的行
                    print("\n=== 删除空行前 ===")
                    print(f"数据行数: {len(df)}")
                    df.dropna(subset=['time', 'things'], how='all', inplace=True)
                    print("=== 删除空行后 ===")
                    print(f"数据行数: {len(df)}")
                    
                    # 再次检查数据
                    print("\n=== 最终数据 ===")
                    print(f"前5行数据: {df.head().to_string()}")
                    
                    # 尝试获取time列，处理可能的列名差异
                    time_column = 'time'
                    things_column = 'things'
                    
                    # 检查列名是否存在
                    if time_column not in df.columns:
                        print(f"警告: 未找到'time'列，尝试查找其他可能的时间列名")
                        # 列出所有列名，让用户知道可用的列名
                        print(f"可用列名: {df.columns.tolist()}")
                        # 尝试寻找包含'time'或'日期'或'date'的列
                        for col in df.columns:
                            col_lower = col.lower()
                            if 'time' in col_lower or '日期' in col_lower or 'date' in col_lower:
                                time_column = col
                                print(f"自动选择时间列: {time_column}")
                                break
                                
                    if things_column not in df.columns:
                        print(f"警告: 未找到'things'列，尝试查找其他可能的事件列名")
                        # 尝试寻找包含'thing'或'事件'或'content'的列
                        for col in df.columns:
                            col_lower = col.lower()
                            if 'thing' in col_lower or '事件' in col_lower or 'content' in col_lower:
                                things_column = col
                                print(f"自动选择事件列: {things_column}")
                                break
                    
                    try:
                        # 获取time列和things列
                        # 强制转换为字符串类型，处理数值类型的日期
                        times = df[time_column].astype(str).tolist()
                        things = df[things_column].tolist()
                        print(f"使用列名: time={time_column}, things={things_column}")
                        print(f"times列表: {times}")
                        print(f"things列表: {things}")
                        print(f"times列表长度: {len(times)}")
                        print(f"things列表长度: {len(things)}")
                    except KeyError as e:
                        print(f"错误: 找不到指定的列 - {e}")
                        print("请确保Excel文件中包含'time'和'things'列")
                        times = []
                        things = []
                    
                    # 解析日期，支持多种格式（. / -）
                    month_data = []
                    day_data = []
                    
                    # 清空现有事件数据
                    self.events.clear()
                    
                    # 定义支持的日期分隔符
                    date_separators = ['.', '/', '-']
                    
                    print("\n=== 开始解析日期 ===")
                    for i, (time_str, thing) in enumerate(zip(times, things)):
                        print(f"\n第 {i+1} 条记录: time={time_str}, thing={thing}")

                        # 确保time_str是字符串类型
                        # ── float 直接转 str，不做任何小数位补零 ──
                        # 解析规则：小数点前=月份，小数点后=日期（直接当数字读）
                        #   9.3  → month='9', day='3'  → 后面补前导零 → 9月03号 ✅
                        #   12.31 → month='12', day='31' → 12月31号 ✅
                        #   3.05 → str(3.05)='3.05' → month='3', day='05' → 3月05号 ✅
                        if isinstance(time_str, float):
                            # 整数型 float（如 10.0）转 int str，避免 "10.0"
                            if time_str == int(time_str):
                                time_str = str(int(time_str))
                            else:
                                time_str = str(time_str)
                            print(f"  [float转str] {time_str!r}")

                        time_str = str(time_str).strip()
                        month = None
                        day = None
                        
                        # 跳过空的time_str
                        if not time_str or time_str == 'nan':
                            print(f"跳过空的time_str: {time_str}")
                            continue
                        
                        # 尝试不同的日期分隔符
                        for sep in date_separators:
                            if sep in time_str:
                                parts = time_str.split(sep)
                                if len(parts) >= 2:
                                    # 只取前两个部分（月和日）
                                    month = parts[0].strip()
                                    day = parts[1].strip()
                                    print(f"使用分隔符 '{sep}' 解析: 月={month}, 日={day}")
                                    break
                        
                        # 如果没有找到分隔符，尝试其他格式
                        if month is None and day is None:
                            # 尝试直接解析数字（如405表示4月5日）
                            if time_str.isdigit() and len(time_str) in [3, 4]:
                                if len(time_str) == 3:
                                    # 格式：MDD（如405表示4月5日）
                                    month = time_str[0]
                                    day = time_str[1:]
                                    print(f"直接解析3位数字: 月={month}, 日={day}")
                                elif len(time_str) == 4:
                                    # 格式：MMDD（如0405表示4月5日）
                                    month = time_str[:2]
                                    day = time_str[2:]
                                    print(f"直接解析4位数字: 月={month}, 日={day}")
                        
                        # 特殊处理: 如果day以'.'开头（例如：3..11）
                        if month is not None and day.startswith('.'):
                            day = day[1:]
                            print(f"处理特殊情况，移除day前的'.': {day}")
                        
                        # 如果成功解析出月和日
                        if month is not None and day is not None:
                            try:
                                # 转换为整数，确保是有效数字
                                int_month = int(month)
                                int_day = int(day)
                                
                                # 验证月份和日期的有效性
                                if 1 <= int_month <= 12 and 1 <= int_day <= 31:
                                    # 转换回字符串，保持两位数格式（可选）
                                    if len(str(int_month)) == 1:
                                        month = f"0{int_month}"
                                    else:
                                        month = str(int_month)
                                    if len(str(int_day)) == 1:
                                        day = f"0{int_day}"
                                    else:
                                        day = str(int_day)
                                    
                                    month_data.append(month)
                                    day_data.append(day)
                                    # 存储事件数据到self.events列表
                                    self.events.append({
                                        'month': month,
                                        'day': day,
                                        'things': thing
                                    })
                                    print(f"成功解析并添加事件: 月={month}, 日={day}, 事件={thing}")
                                else:
                                    print(f"警告: 无效的日期 {time_str} (月: {month}, 日: {day})")
                            except ValueError as e:
                                print(f"警告: 无法解析时间格式 {time_str} - {e}")
                        else:
                            print(f"警告: 无法解析时间格式 {time_str}，请使用 M.D、M/D、M-D 或 MMDD 格式")
                    
                    print(f"\n=== 解析结果 ===")
                    print(f"成功解析 {len(month_data)} 个事件")
                    print(f"月份列表: {month_data}")
                    print(f"日期列表: {day_data}")
                    print(f"事件列表: {[event['things'] for event in self.events]}")
                    
                    if len(month_data) != len(day_data):
                        messagebox.showwarning("警告", "月份和日期数量不匹配")
                        return
                    if len(things) != len(month_data):
                        messagebox.showwarning("警告", "事件数量不匹配")
                        return

                    print("原始时间:", times)
                    print("月份:", month_data)
                    print("日期:", day_data)
                    print("事件:", things)
                    print("解析后的事件数据:", self.events)
                    
                    # 调用刷新函数，重置为原始显示模式
                    refresh_text()
                    
                    # 重新显示日历，更新*标记
                    show_calendar()
                    
                    messagebox.showinfo("成功", "事件数据导入成功！")
                except Exception as e:
                    messagebox.showerror("错误", f"分析Excel文件失败: {e}")
                    print(f"分析Excel文件失败: {e}")
                    import traceback
                    traceback.print_exc()

            def select_file():
                from tkinter import filedialog
                import json
                # 设置默认路径为当前目录
                initial_dir = self.dir_path
                file_path = filedialog.askopenfilename(initialdir=initial_dir, filetypes=[("Excel files", "*.xlsx;*.xls")])
                if file_path:
                    # 使用绝对路径
                    absolute_path = os.path.abspath(file_path)
                    file_entry.delete(0, tk.END)
                    file_entry.insert(0, absolute_path)
                    # 记录 Excel 路径到 user_data.json。
                    # 【关键修复】原来用 'w' 模式把整个文件覆盖成只剩
                    # {"user_data": [路径]} —— 透明度、文字大小、图标大小等
                    # 其它设置全被冲掉！终端用户反馈「每次开机配置都重置」
                    # 的真因就是它：只要在日历里重新选过一次 Excel，配置即清空。
                    # 改走 save_user_settings 合并保存，只更新 user_data 键，
                    # 其余设置原样保留；失败也会写进 error.log。
                    save_user_settings(get_settings_dir(),
                                       {'user_data': [absolute_path]})
                else:
                    messagebox.showwarning("警告", "请选择一个Excel文件")

            def add_event(month_choice=None, day_choice=None, *args):
                def confirm_event_add(month, day, text):
                    if not month or not day or not text:
                        messagebox.showwarning("警告", "请输入月份、日期和事件内容")
                        return
                    # 检查合理性
                    if not month.isdigit() or not day.isdigit():
                        messagebox.showwarning("警告", "月份和日期必须是数字")
                        return
                    if not (1 <= int(month) <= 12 and 1 <= int(day) <= 31):
                        messagebox.showwarning("警告", "月份和日期必须是1-12和1-31之间的整数")
                        return
                    """self.events.append({
                        'month': month,
                        'day': day,
                        'things': text
                    })"""
                    # self.events 是列表（见 __init__ / Excel 导入），此处按「同日期覆盖、否则追加」处理。
                    # 注意：不能用 self.events[month+day] = {...}，列表不支持字符串下标，
                    # 那样会在回调里抛 TypeError 而界面毫无反应。
                    def _norm(v):
                        try:
                            return int(str(v).strip())
                        except Exception:
                            return None

                    _m, _d = _norm(month), _norm(day)
                    self.events = [
                        e for e in self.events
                        if not (isinstance(e, dict)
                                and _norm(e.get('month')) == _m
                                and _norm(e.get('day')) == _d)
                    ]
                    self.events.append({
                        'month': "%02d" % _m,
                        'day': "%02d" % _d,
                        'things': text
                    })

                    # ── 立即写回 Excel，让刷新/重启后新事件仍在 ──
                    # 原来只改内存，analysis_excel 一 clear() 就丢了。
                    # 这里同步失败不阻断界面显示——文件被 Excel 打开时用户能看到
                    # "添加成功" 但被 Excel 锁挡住，这时后面的弹窗会提示他先关掉 Excel。
                    def _on_write_err(msg):
                        messagebox.showerror("事件已添加但无法写入 Excel",
                            f"事件已在本窗口内显示，但无法同步到 Excel 文件：\n\n{msg}\n\n"
                            "最常见原因：Excel 文件正在被 Excel 程序打开。\n"
                            "请先关闭 Excel，再回来点「刷新」即可。")
                    synced = sync_events_to_excel(self, on_error=_on_write_err)

                    messagebox.showinfo("成功",
                        "事件添加成功！" + ("" if synced else "\n\n⚠️ 未能写入 Excel（请看下一条错误提示）"))
                    # 刷新文本显示
                    refresh_text()
                    # 重新显示日历，更新*标记
                    show_calendar()

                    add_root.destroy()


                add_root = tk.Toplevel()
                ensure_tk_error_hook()   # 让回调异常弹窗可见，避免「点了没反应」
                # 锁定窗口，防止用户调整大小
                add_root.resizable(False, False)
                add_root.title("新建事件")
                add_root.geometry("560x400")
                add_root.configure(bg="#f5f7fa")
                
                # 设置统一的间距
                padx = 5
                pady = 5
                
                # 创建主框架
                main_frame = ttk.Frame(add_root, padding=(20, 20, 20, 20))
                main_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
                
                # 设置标题
                title_label = ttk.Label(main_frame, text="创建一个事件，开始自律生活！", 
                                    style="Title.TLabel", foreground="#409eff")
                title_label.grid(row=0, column=0, columnspan=4, pady=(0, 20), sticky=tk.W)
                
                # 获取当前年份
                self.year = time.strftime("%Y", time.localtime())
                
                # 年份显示
                year_label = ttk.Label(main_frame, text=f"年份: {self.year}", 
                                    style="Modern.TLabel", foreground="#606266")
                year_label.grid(row=1, column=0, padx=padx, pady=pady, sticky=tk.E)
                
                # 月份输入
                month_label = ttk.Label(main_frame, text="月份:", style="Modern.TLabel")
                month_label.grid(row=1, column=1, padx=padx, pady=pady, sticky=tk.E)
                month_entry = ttk.Entry(main_frame, width=8, style="Modern.TEntry")
                month_entry.grid(row=1, column=2, padx=padx, pady=pady, sticky=tk.W)
                
                # 日期输入
                day_label = ttk.Label(main_frame, text="日期:", style="Modern.TLabel")
                day_label.grid(row=1, column=3, padx=padx, pady=pady, sticky=tk.E)
                day_entry = ttk.Entry(main_frame, width=8, style="Modern.TEntry")
                day_entry.grid(row=1, column=4, padx=padx, pady=pady, sticky=tk.W)
                
                # 事件内容输入框
                text = tk.Text(main_frame, width=45, height=6, 
                            font=("Microsoft YaHei", 10),
                            bg="#ffffff",
                            fg="#333333",
                            bd=1,
                            relief="solid",
                            highlightbackground="#dcdfe6",
                            highlightcolor="#409eff",
                            highlightthickness=1,
                            wrap=tk.WORD)
                text.grid(row=2, column=0, columnspan=5, padx=padx, pady=pady, sticky=(tk.N, tk.S, tk.E, tk.W))

                # ── Enter 保存 + Shift+Enter 换行（钉钉/飞书惯例）──
                # ⚠️ Tkinter Text 控件有个大坑：类级别默认绑了
                #    <Return> → tk::TextInsert %W \n
                #    实例绑定即使返回 "break" 也拦不住类绑定。
                #    解决办法：用更底层的 <KeyPress> 事件拦截，
                #    只对这一个 Text 生效，不影响程序里其他 Text。

                def _do_save(_evt=None):
                    confirm_event_add(month_entry.get(), day_entry.get(),
                                      text.get("1.0", tk.END).strip())
                    return "break"

                def _on_keypres(evt):
                    """拦截这一个 Text 的 Return，自己决定保存还是换行"""
                    if evt.keysym == "Return":
                        if evt.state & 0x1:   # Shift 按下 → 手动插入换行
                            text.insert(tk.INSERT, "\n")
                        else:                  # 纯 Enter → 保存
                            _do_save(evt)
                        return "break"          # 关键：阻止 Text 类默认换行
                    return None

                text.bind("<KeyPress>", _on_keypres)
                text.bind("<Control-s>", _do_save)
                text.bind("<Control-S>", _do_save)
                # 焦点不在 Text 时：Enter 也保存（比如月份/日期输入框里回车）
                add_root.bind("<Return>", _do_save)
                add_root.bind("<Control-s>", _do_save)
                add_root.bind("<Control-S>", _do_save)
                add_root.bind("<Escape>", lambda e: (add_root.destroy(), "break")[-1])
                
                # 查看events的指定日期中是否有事件
                # month_choice/day_choice 可能是 int 也可能是补零字符串（如 "09"），统一成数字再比较
                def _num(v):
                    try:
                        return int(str(v).strip())
                    except Exception:
                        return None

                if month_choice is not None and day_choice is not None:
                    for event in self.events:
                        if not isinstance(event, dict):
                            continue
                        if (_num(event.get('month')) == _num(month_choice)
                                and _num(event.get('day')) == _num(day_choice)):
                            text.insert(tk.END, event.get('things', ''))
                            break

                # 确认按钮 + 快捷键提示
                confirm_btn = ttk.Button(main_frame, text="💾 保存", style="Modern.TButton",
                                          command=lambda: confirm_event_add(
                                              month_entry.get(), day_entry.get(),
                                              text.get("1.0", tk.END).strip()))
                confirm_btn.grid(row=3, column=2, columnspan=2,
                                 padx=padx, pady=(pady+10, 0), sticky=(tk.E, tk.W))

                tk.Label(main_frame,
                         text="快捷键: Enter 保存  |  Shift+Enter 换行  |  Ctrl+S 保存  |  Esc 取消",
                         bg="#f5f7fa", fg="#8a94a6",
                         font=("Microsoft YaHei", 8)).grid(
                    row=3, column=0, columnspan=2, padx=padx,
                    pady=(pady+10, 0), sticky=tk.W)
                
                # 配置行和列的权重，使布局更灵活
                main_frame.columnconfigure(2, weight=1)
                main_frame.columnconfigure(3, weight=1)
                main_frame.rowconfigure(2, weight=1)
                
                # 设置输入框默认值
                # 如果输入时间参数，设置默认值为参数时间，否则设置系统默认时间
                print(month_choice,day_choice)
                if month_choice is not None and day_choice is not None:
                    month_entry.insert(0, month_choice)
                    day_entry.insert(0, day_choice)
                else:
                    month_entry.insert(0, time.strftime("%m", time.localtime()))
                    day_entry.insert(0, time.strftime("%d", time.localtime()))
                
                
                
                # 绑定回车键确认
                add_root.bind("<Return>", lambda e: confirm_btn.invoke())
                
                # 设置初始焦点
                month_entry.focus()
                
                # 居中窗口
                add_root.update_idletasks()
                width = add_root.winfo_width()
                height = add_root.winfo_height()
                x = (add_root.winfo_screenwidth() // 2) - (width // 2)
                y = (add_root.winfo_screenheight() // 2) - (height // 2)
                add_root.geometry(f"{width}x{height}+{x}+{y}")

            def find_line(text):
                """打开搜索对话框"""
                current_search_pos = 0
                all_matches = []
                
                def search_text():
                    """执行搜索"""
                    nonlocal current_search_pos, all_matches
                    
                    search_query = search_entry.get()
                    if not search_query:
                        return
                    
                    text.config(state=tk.NORMAL)
                    text.tag_remove("highlight", "1.0", tk.END)
                    text.tag_remove(tk.SEL, "1.0", tk.END)
                    
                    all_matches = []
                    pos = "1.0"
                    while True:
                        pos = text.search(search_query, pos, tk.END)
                        if not pos:
                            break
                        end_pos = f"{pos}+{len(search_query)}c"
                        all_matches.append((pos, end_pos))
                        text.tag_add("highlight", pos, end_pos)
                        pos = end_pos
                    
                    text.tag_configure("highlight", background="yellow", foreground="black")
                    
                    if all_matches:
                        current_search_pos = 0
                        highlight_current_match()
                    else:
                        status_label.config(text="未找到匹配项", foreground="#f56c6c")
                    
                    text.config(state=tk.DISABLED)
                
                def highlight_current_match():
                    """高亮显示当前匹配项"""
                    if not all_matches:
                        return
                    
                    pos, end_pos = all_matches[current_search_pos]
                    text.config(state=tk.NORMAL)
                    text.tag_remove(tk.SEL, "1.0", tk.END)
                    text.tag_add(tk.SEL, pos, end_pos)
                    text.mark_set(tk.INSERT, end_pos)
                    text.see(pos)
                    text.config(state=tk.DISABLED)
                    status_label.config(text=f"找到 {len(all_matches)} 个匹配项中的第 {current_search_pos + 1} 个", foreground="#67c23a")
                
                def find_next():
                    """查找下一个"""
                    nonlocal current_search_pos
                    if not all_matches:
                        search_text()
                        return
                    current_search_pos = (current_search_pos + 1) % len(all_matches)
                    highlight_current_match()
                
                def find_prev():
                    """查找上一个"""
                    nonlocal current_search_pos
                    if not all_matches:
                        search_text()
                        return
                    current_search_pos = (current_search_pos - 1) % len(all_matches)
                    highlight_current_match()
                
                def close_search():
                    """关闭搜索对话框，清除高亮"""
                    text.config(state=tk.NORMAL)
                    text.tag_remove("highlight", "1.0", tk.END)
                    text.tag_remove(tk.SEL, "1.0", tk.END)
                    text.config(state=tk.DISABLED)
                    search_window.destroy()
                
                search_window = tk.Toplevel()
                ensure_tk_error_hook()
                search_window.title("查找")
                search_window.geometry("500x150")
                search_window.configure(bg="#f5f7fa")
                search_window.resizable(False, False)
                
                main_frame = ttk.Frame(search_window, padding=(15, 15, 15, 15))
                main_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
                
                padx = 5
                pady = 5
                
                ttk.Label(main_frame, text="查找:", style="Modern.TLabel").grid(row=0, column=0, padx=padx, pady=pady, sticky=tk.E)
                
                search_entry = ttk.Entry(main_frame, width=30, style="Modern.TEntry")
                search_entry.grid(row=0, column=1, columnspan=2, padx=padx, pady=pady, sticky=(tk.W, tk.E))
                
                next_btn = ttk.Button(main_frame, text="查找下一个", style="Modern.TButton", command=find_next)
                next_btn.grid(row=1, column=0, padx=padx, pady=pady, sticky=tk.E)
                
                prev_btn = ttk.Button(main_frame, text="查找上一个", style="Modern.TButton", command=find_prev)
                prev_btn.grid(row=1, column=1, padx=padx, pady=pady, sticky=tk.E)
                
                close_btn = ttk.Button(main_frame, text="关闭", style="Modern.TButton", command=close_search)
                close_btn.grid(row=1, column=2, padx=padx, pady=pady, sticky=tk.E)
                
                status_label = ttk.Label(main_frame, text="", style="Modern.TLabel")
                status_label.grid(row=2, column=0, columnspan=3, padx=padx, pady=pady, sticky=tk.W)
                
                main_frame.columnconfigure(1, weight=1)
                
                def on_entry_change(*args):
                    """输入框内容改变时自动搜索"""
                    search_text()
                
                search_var = tk.StringVar()
                search_entry.config(textvariable=search_var)
                search_var.trace("w", on_entry_change)
                
                search_entry.bind("<Return>", lambda e: find_next())
                search_window.bind("<Escape>", lambda e: close_search())
                search_window.bind("<Return>", lambda e: find_next())
                
                search_entry.focus_set()

            # 定义退出检查函数
            def check_exit(check_file_path):
                """关闭日历窗口时的同步逻辑。

                原来：
                  1. 先 to_excel 覆盖 Excel（不等用户同意）
                  2. 用 float 写 time 导致 4月10日 → 4.1 读回成 4月1日
                  3. 覆盖完再弹窗问"要不要退出"——用户选"否"也已经覆盖了
                现在：每次新增/删除事件都已经同步过 Excel，这里只做兜底再退出。
                格式统一走 sync_events_to_excel（用字符串 time，修掉日期 bug）。
                """
                def _on_exit_err(msg):
                    # 退出时写盘失败不阻断退出（文件被 Excel 打开时），让用户看到提示
                    messagebox.showwarning("日历关闭提示",
                        f"未能同步到 Excel：\n\n{msg}\n\n"
                        "请先关闭 Excel，再点主窗口的「打开日历」并手动点刷新。")

                # sync_events_to_excel 内部自己找 Excel 路径；这里的 check_file_path
                # 参数保留函数签名兼容性但不再使用（更可靠的来源是 user_data.json）
                sync_events_to_excel(self, on_error=_on_exit_err)

                cal_window.destroy()
                
            def save_file():  # 改为接受 df 参数
                import pandas as pd
                from tkinter import filedialog
                save_file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("文本文件", "*.xlsx")])
                print("文件类型",self.events)
                
                if save_file_path:
                    try:
                        print("保存文件路径:", save_file_path)
                        # 将self.events转化成excel文件# 将self.events转化成excel文件
                        # 转换数据格式：将 month 和 day 合并为 time，并去掉前导零
                        export_data = []
                        for event in self.events:
                            export_data.append({
                                'time': f"{int(event['month'])}.{int(event['day'])}",  # 例如: '4.2'
                                'things': event['things']
                            })

                        df = pd.DataFrame(export_data)
                        df.to_excel(save_file_path, index=False)
                        print("保存成功！")
                    except Exception as e:
                        print(f"保存失败: {e}")

            def set_calendar():
                """设置日程管理器"""
                # 构建期间 update_e 一律不生效：ttk.Scale 的 .set() 会触发 command，
                # 不拦住的话，「把用户已存的值读进滑块」这个过程就会把某些项
                # （如写死的 560）先写盘/先应用，看起来就是其它设置被重置了。
                self._settings_init = True

                def update_e(type_name):
                    # 窗口还在构建时，ttk.Scale 的 .set() 也会触发 command，
                    # 此时一律忽略：否则「读入用户已有设置」这个过程本身就会
                    # 反复触发应用/写盘，把没轮到初始化的项打回默认值。
                    if getattr(self, '_settings_init', False):
                        return
                    # 注：原「启用AI解析」分支已随 AI 功能一起移除
                    if type_name == "event":
                        # 「事件框长度」现在真正是白框的*目标高度*：改滑块时让
                        # 主窗口白框跟着变高/变矮，并把新值持久化到 user_data.json。
                        # 注意：ttk.Scale.get() 返回 float，Qt 的 setMaximumHeight / 数学只收 int。
                        self.event_length = int(round(float(self.event_length_slider.get())))
                        self.content_label.setMaximumHeight(self.event_length)
                        # 手动调过滑块 = 手动优先：把「自动加高」让位给用户。
                        # 否则用户明明把框调小了，正文一变（倒计时每秒变）
                        # 框又自动撑高到内容全高，看起来像「调小没反应」。
                        # 想恢复自动，勾选下面的「内容多时自动加高白框」即可。
                        if getattr(self, 'auto_fit_box', True):
                            self.auto_fit_box = False
                            try:
                                self.bool_auto_fit.set(False)
                            except Exception:
                                pass
                        # allow_grow=True：以「其它控件 + event_length」为基准重排窗口
                        self._fit_content_height(allow_grow=True)
                        self._persist_event_length(self.event_length)
                        _pump_qt_events()
                    elif type_name == "window_opacity":
                        # 桌面图标透明度：只让各框「底色」透明（文字保持不透明实色），
                        # 效果上就是把白色/蓝色底板去掉、让内容嵌进桌面
                        val = self.window_opacity_slider.get() / 100.0
                        self.window_opacity = val
                        self.apply_window_opacity(val)
                        self.window_opacity_hint.set("%d%%" % round(val * 100))
                        # 改完立即存盘（只写这一个键），窗口被强杀也不丢
                        save_user_settings(get_settings_dir(), {'window_opacity': val})
                        _pump_qt_events()
                    elif type_name == "icon_opacity":
                        # 最小化图标透明度：只作用于窗口内那张图标图片
                        val = self.icon_opacity_slider.get() / 100.0
                        self.icon_opacity = val
                        if getattr(self, "icon_opacity_effect", None) is not None:
                            self.icon_opacity_effect.setOpacity(val)
                            # 让图片按新透明度重绘
                            self.image_label.update()
                        self.icon_opacity_hint.set("%d%%" % round(val * 100))
                        save_user_settings(get_settings_dir(), {'icon_opacity': val})
                        _pump_qt_events()
                    elif type_name == "auto_fit":
                        # 「内容多时自动加高白框」总开关。
                        # 勾上：事件多了白框自动撑高到全部显示（不用滚动）。
                        # 取消：白框严格按「事件框长度」/ 你拖出来的高度显示，
                        #       内容多了就在框内滚动 —— 手动设的框高不会被顶掉。
                        self.auto_fit_box = bool(self.bool_auto_fit.get())
                        save_user_settings(get_settings_dir(),
                                           {'auto_fit_box': self.auto_fit_box})
                        if self.auto_fit_box:
                            # 重新按「内容自然高度 vs 设定高度」算一次
                            self._fit_content_height(fit_content=True)
                        else:
                            self._fit_content_height()
                        _pump_qt_events()
                    elif type_name == "autostart":
                        want = bool(self.bool_get_autostart.get())
                        ok, err = set_autostart(want)
                        if ok:
                            messagebox.showinfo("提示", "已开启开机自动启动" if want else "已关闭开机自动启动")
                        else:
                            # 实测：360 等安全软件会拦截「把 python.exe 注册成启动项」，
                            # 表现就是 WinError 5 拒绝访问（与代码无关）。给出可操作的提示。
                            hint = ""
                            if "拒绝访问" in str(err) or "WinError 5" in str(err):
                                hint = ("\n\n多半是安全软件（如 360）的「启动项防护」拦下了这次写入。"
                                        "\n可以：① 在安全软件里允许本次修改后重试；"
                                        "\n② 或改用打包好的 exe 运行（启动项指向 exe 时通常不会被拦）。")
                            messagebox.showerror("设置失败", "无法修改开机自启动：%s%s" % (err, hint))
                            self.bool_get_autostart.set(is_autostart_enabled())
                    elif type_name == "text_size":
                        # 主窗口文字大小：正文用该值，倒计时在此基础上 +4
                        self.apply_text_size(self.text_size_slider.get())
                        self.text_size_hint.set("%d px" % self.text_size)
                        save_user_settings(get_settings_dir(), {'text_size': self.text_size})
                        _pump_qt_events()
                    elif type_name == "icon_size":
                        # 主窗口图标大小：只换这张图的边长，窗口/文字尺寸不动
                        self.apply_icon_size(self.icon_size_slider.get())
                        self.icon_size_hint.set("%d px" % self.icon_size)
                        save_user_settings(get_settings_dir(), {'icon_size': self.icon_size})
                        _pump_qt_events()
                    elif type_name == "exit":
                        # 关闭窗口时**绝不能**把 self.user 整个写回去。
                        #
                        # 原来这里是：
                        #     self.user['event_length'] = self.event_length
                        #     ... （逐个改 5 个键）
                        #     save_user_settings(get_settings_dir(), self.user)
                        # self.user 是「打开设置窗口那一刻」的旧快照。用户在
                        # 设置窗口开着的时候做的这些事，改的都是主窗口的属性、
                        # 早就各自存过盘了，而 self.user 里还是旧值：
                        #   · 拖主窗口右下角小蓝块（grip）改 event_length
                        #   · 在日历窗口里换了 Excel 文件（user_data 路径）
                        # 关闭设置窗口时这一写，就把刚存好的新值用旧快照盖回去
                        # —— 表现就是「改了设置、重启又变回原样」。
                        #
                        # 现在：每一项在改动时就已经单键存盘过了，关闭窗口
                        # 什么都不用写；只补存一次 auto_fit_box（勾选状态）
                        # 就够了。
                        save_user_settings(get_settings_dir(),
                                           {'auto_fit_box': bool(self.auto_fit_box)})
                        set_window.destroy()
                    elif type_name == "save_pos":
                        # 把主窗口当前位置存下来，下次启动自动恢复到同一相对位置。
                        # 注意：保存的是「屏幕相对坐标」(0~1)，不是绝对像素 ——
                        # 跨分辨率（1920x1080 → 1366x768）或换显示器时，
                        # 窗口会按比例出现在相同的相对位置上。
                        ok = self.save_window_position()
                        if ok:
                            messagebox.showinfo("保存成功",
                                "已保存当前窗口位置。\n下次启动将自动恢复到这里。")
                        else:
                            messagebox.showerror("保存失败",
                                "无法保存位置，请稍后重试。")

                    else:
                        messagebox.showerror("错误", "未知的设置类型")
                
                # 打开设置对话框，且只能打开一个窗口
                style = ttk.Style()
                _apply_settings_styles(style)

                set_window = tk.Toplevel()
                ensure_tk_error_hook()
                set_window.title("设置")
                W, H = 420, 720   # 紧凑卡片版
                set_window.geometry("%dx%d+%d+%d" % (
                    W, H,
                    max(0, (set_window.winfo_screenwidth() - W) // 2),
                    max(0, (set_window.winfo_screenheight() - H) // 3)))
                set_window.configure(bg=_SET_COLOR['window_bg'])
                set_window.resizable(False, False)

                # 绑定退出
                set_window.protocol("WM_DELETE_WINDOW", lambda: update_e("exit"))

                # 顶部标题栏（Tk Frame，直接用 bg）
                hx, hy = _SET_SPACE['header_pad']
                header = tk.Frame(set_window, bg=_SET_COLOR['window_bg'])
                header.pack(fill="x", padx=hx, pady=(hy, 2))
                tk.Label(header, text="⚙  设置日程管理器",
                         bg=_SET_COLOR['window_bg'],
                         fg=_SET_COLOR['accent'],
                         font=_SET_FONT['header']).pack(side="left")

                body = tk.Frame(set_window, bg=_SET_COLOR['window_bg'])
                body.pack(fill="both", expand=True)
                body.columnconfigure(0, weight=1)

                def _make_card(title_text, row):
                    """创建一张白底卡片容器。"""
                    px, py = _SET_SPACE['card_pad']
                    mx, my = _SET_SPACE['card_margin']
                    card = ttk.Frame(body, style="Card.TFrame", padding=(px, py))
                    card.grid(row=row, column=0, padx=mx, pady=(my, my), sticky="ew")
                    card.columnconfigure(1, weight=1)
                    if title_text:
                        ttk.Label(card, text=title_text, style="CardTitle.TLabel").grid(
                            row=0, column=0, columnspan=3, sticky="w",
                            pady=_SET_SPACE['title_sep'])
                        sep = ttk.Frame(card, style="CardSep.TFrame", height=1)
                        sep.grid(row=1, column=0, columnspan=3, sticky="ew",
                                 pady=_SET_SPACE['sep_first'])
                        return card, 2
                    return card, 0

                def _add_slider(card, row, label, hint_var, **scale_kwargs):
                    """一行「标签 + 滑块 + 值」。"""
                    rp = _SET_SPACE['row_pady']
                    ttk.Label(card, text=label, style="Setting.TLabel").grid(
                        row=row, column=0, sticky="w", pady=rp)
                    slider = ttk.Scale(card, orient=tk.HORIZONTAL, length=200,
                                       style="Horizontal.TScale", **scale_kwargs)
                    slider.grid(row=row, column=1,
                                padx=(_SET_SPACE['slider_gap'], 6),
                                sticky="ew", pady=rp)
                    ttk.Label(card, textvariable=hint_var, style="Value.TLabel").grid(
                        row=row, column=2, sticky="e", pady=rp)
                    return slider

                def _add_checkbox(card, row, text, bool_var, pady=(4, 0)):
                    cb = ttk.Checkbutton(card, text=text, variable=bool_var)
                    cb.grid(row=row, column=0, columnspan=3, sticky="w", pady=pady)
                    return cb

                # ══ 卡片 1：外观尺寸 ══
                card1, r1 = _make_card("外观尺寸", 0)

                self.event_length = tk.IntVar(value=DEFAULT_USER_SETTINGS['event_length'])
                self.event_length_slider = _add_slider(
                    card1, r1,
                    "事件框长度（也可拖主窗口右下角小蓝块）",
                    tk.StringVar(value="560 px"),
                    from_=100, to=1200, variable=self.event_length,
                    command=lambda e: update_e("event"))

                self.bool_auto_fit = tk.BooleanVar(value=True)
                self.auto_fit_check = _add_checkbox(
                    card1, r1 + 1,
                    "内容多时自动加高白框（推荐）", self.bool_auto_fit,
                    pady=(4, 0))

                # ══ 卡片 2：文字与图标 ══
                card2, r2 = _make_card("文字与图标", 1)

                self.text_size_var = tk.IntVar(value=DEFAULT_USER_SETTINGS['text_size'])
                self.text_size_hint = tk.StringVar(value="14 px")
                self.text_size_slider = _add_slider(
                    card2, r2, "文字大小", self.text_size_hint,
                    from_=TEXT_SIZE_MIN, to=TEXT_SIZE_MAX,
                    variable=self.text_size_var,
                    command=lambda e: update_e("text_size"))

                self.icon_size_var = tk.IntVar(value=DEFAULT_USER_SETTINGS['icon_size'])
                self.icon_size_hint = tk.StringVar(value="100 px")
                self.icon_size_slider = _add_slider(
                    card2, r2 + 1, "图标大小", self.icon_size_hint,
                    from_=ICON_SIZE_MIN, to=ICON_SIZE_MAX,
                    variable=self.icon_size_var,
                    command=lambda e: update_e("icon_size"))

                # ══ 卡片 3：透明度 ══
                card3, r3 = _make_card("透明度", 2)

                self.window_opacity_var = tk.DoubleVar(value=100.0)
                self.window_opacity_hint = tk.StringVar(value="100%")
                self.window_opacity_slider = _add_slider(
                    card3, r3, "底色透明度", self.window_opacity_hint,
                    from_=0, to=100, variable=self.window_opacity_var,
                    command=lambda e: update_e("window_opacity"))

                self.icon_opacity_var = tk.DoubleVar(value=100.0)
                self.icon_opacity_hint = tk.StringVar(value="100%")
                self.icon_opacity_slider = _add_slider(
                    card3, r3 + 1, "图标透明度", self.icon_opacity_hint,
                    from_=0, to=100, variable=self.icon_opacity_var,
                    command=lambda e: update_e("icon_opacity"))

                # ══ 卡片 4：启动行为 ══
                card4, r4 = _make_card("启动行为", 3)

                self.bool_get_autostart = tk.BooleanVar(value=False)
                self.autostart_check = _add_checkbox(
                    card4, r4, "开机自动启动", self.bool_get_autostart,
                    pady=(0, 0))
                # 勾选框点击：update_e("autostart") 走全局注册的回调，
                # 但 _add_checkbox 里没法传 command，这里手动绑上
                self.autostart_check.configure(
                    command=lambda: update_e("autostart"))

                ttk.Label(card4, text="开机自启位置",
                          style="Setting.TLabel").grid(
                    row=r4 + 1, column=0, columnspan=3, sticky="w", pady=(6, 2))

                self.save_pos_btn = ttk.Button(
                    card4, text="📍 保存当前位置为开机自启位置",
                    style="Primary.TButton",
                    command=lambda: update_e("save_pos"))
                self.save_pos_btn.grid(row=r4 + 2, column=0, columnspan=3,
                                       sticky="ew", pady=(2, 0))

                # ── 底部提示 ──
                tk.Label(set_window,
                         text="提示：拖主窗口右下角蓝色小块也能调事件框高度",
                         bg=_SET_COLOR['window_bg'],
                         fg=_SET_COLOR['text_dim'],
                         font=('Microsoft YaHei', 8)).pack(side="bottom", pady=(0, 6))

                # 读取用户设置（复用 load_user_settings：文件缺失/损坏时回落默认值，不会崩）
                self.user = load_user_settings(get_settings_dir())

                # AI 开关已移除（不再读取/写入 ai_enable）

                self.event_length = self.user.get("event_length", 560)
                self.event_length_slider.set(self.event_length)

                # 主窗口文字大小
                self.text_size = _clamp_text_size(self.user.get('text_size'))
                self.text_size_slider.set(self.text_size)
                self.text_size_hint.set("%d px" % self.text_size)

                # 主窗口图标大小
                self.icon_size = _clamp_icon_size(self.user.get('icon_size'))
                self.icon_size_slider.set(self.icon_size)
                self.icon_size_hint.set("%d px" % self.icon_size)

                # 桌面图标透明度（主窗口整体）
                # 同样不能用 `or 1.0`：用户保存的 0 会被当成「没填」而在
                # 这里被拉回 100%，然后再写回文件 —— 透明度 0 永远存不住。
                self.window_opacity = self._opacity_from(self.user.get('window_opacity'))
                self.window_opacity_slider.set(self.window_opacity * 100)
                self.window_opacity_hint.set("%d%%" % round(self.window_opacity * 100))

                # 最小化图标透明度（窗口内那张图片）
                self.icon_opacity = self._opacity_from(self.user.get('icon_opacity'))
                self.icon_opacity_slider.set(self.icon_opacity * 100)
                self.icon_opacity_hint.set("%d%%" % round(self.icon_opacity * 100))

                # 白框自动加高开关：以主窗口当前状态为准（主窗口启动时已从
                # 配置读过；期间用户拖过小蓝块/滑块也会同步过来）。
                self.auto_fit_box = bool(getattr(self, 'auto_fit_box', True))
                self.bool_auto_fit.set(self.auto_fit_box)
                # 手动优先时给一句提示，避免用户以为勾选项坏了
                if not self.auto_fit_box:
                    self.auto_fit_check.config(text="内容多时自动加高白框（当前按你设的高度显示）")

                # 开机自启动：以注册表实际状态为准，而不是本地 json
                self.bool_get_autostart.set(bool(is_autostart_enabled()))

                # 所有滑块都已读入用户已存的值：从现在起 update_e 恢复生效，
                # 之后用户拖动滑块才真正应用/写盘
                self._settings_init = False

                set_window.mainloop()

            def open_excel_file(file_path):
                import webbrowser
                webbrowser.open(file_path)
            
            def new_excel_file():
                from tkinter import filedialog
                file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("文本文件", "*.xlsx")])
                if file_path:
                    from openpyxl import Workbook
                    from openpyxl.utils.cell import get_column_letter
                    # 1. 准备数据
                    template_event = ["time", "things"]

                    # 2. 创建工作簿和工作表
                    wb = Workbook()
                    ws = wb.active  # 使用默认工作表（也可以用 wb.create_sheet("Sheet1") 新建）

                    # 3. 分别写入 A1 和 B1
                    ws["A1"] = template_event[0]  # A1 单元格写入 "time"
                    ws["B1"] = template_event[1]  # B1 单元格写入 "things"

                    # 4. 保存文件
                    wb.save(file_path)
                    messagebox.showinfo("提示", "新建文件成功")
                        
            # 创建主窗口
            cal_window = tk.Tk()
            ensure_tk_error_hook()
            cal_window.title("日历")
            # 1080×720 → 980×620：紧凑 20%，减少挡路面积
            cal_window.geometry("980x620+%d+%d" % (
                max(0, (cal_window.winfo_screenwidth() - 980) // 2),
                max(0, (cal_window.winfo_screenheight() - 620) // 3)))
            cal_window.minsize(840, 520)
            cal_window.configure(bg=_CAL_COLOR['window_bg'])

            # 应用新样式（统一的卡片区 + 主色）
            style = ttk.Style()
            _apply_calendar_styles(style)

            # ── 顶部标题栏（窗口级 Tk Frame）──
            header = tk.Frame(cal_window, bg=_CAL_COLOR['window_bg'])
            header.pack(fill="x", padx=14, pady=(12, 8))

            ttk.Label(header, text="📅  事件日历管理",
                      style="WinTitle.TLabel").pack(side="left")

            ttk.Button(header, text="⚙ 设置",
                       style="Secondary.TButton",
                       command=set_calendar).pack(side="right", padx=(6, 0))

            menu_bar = tk.Menu(cal_window, tearoff=False)
            menu_bar.add_command(label="分析数据",
                                 command=lambda: analysis_excel(file_entry.get()))
            menu_bar.add_command(label="刷新",
                                 command=lambda: show_calendar_and_refresh())
            menu_bar.add_command(label='另存为xlsx', command=save_file)
            menu_bar.add_command(label="新建事件",
                                 command=lambda: add_event(None, None))
            menu_bar.add_separator()
            menu_bar.add_command(label='打开xlsx文件',
                                 command=lambda: open_excel_file(file_entry.get()))
            menu_bar.add_command(label='新建xlsx文件', command=new_excel_file)

            file_btn = ttk.Button(header, text="📁 文件",
                                  style="Primary.TButton")
            file_btn.pack(side="right", padx=(6, 0))

            def _show_file_menu(event):
                menu_bar.post(file_btn.winfo_rootx(),
                              file_btn.winfo_rooty() + file_btn.winfo_height())
            file_btn.bind("<Enter>", _show_file_menu)

            ttk.Button(header, text="＋ 新建事件",
                       style="Primary.TButton",
                       command=lambda: add_event(None, None)).pack(side="right")

            # ── 控制卡（年份 / 月份 / Excel 路径 一行）──
            c = _CAL_COLOR; f = _CAL_FONT

            control_card = ttk.Frame(cal_window, style="Card.TFrame",
                                      padding=_CAL_SPACE['card_pad'])
            control_card.pack(fill="x", padx=12, pady=(0, 8))

            ttk.Label(control_card, text="年份:",
                      style="CardTitle.TLabel").grid(
                row=0, column=0, padx=(0, 4), sticky="e")

            year_var = tk.StringVar(value=str(self.time_year))
            year_entry = ttk.Entry(control_card, textvariable=year_var,
                                    width=6, style="Field.TEntry")
            year_entry.configure(state="readonly")
            year_entry.grid(row=0, column=1, padx=(0, 12), sticky="w")

            ttk.Label(control_card, text="月份:",
                      style="CardTitle.TLabel").grid(
                row=0, column=2, padx=(0, 4), sticky="e")

            month_var = tk.StringVar(value=str(self.time_month))
            month_var.trace("w", show_calendar)
            month_entry_values = [str(i) for i in range(1, 13)]
            month_entry_values[month_entry_values.index(str(self.time_month))] = f"{self.time_month}*"
            month_entry = ttk.Combobox(control_card, textvariable=month_var,
                                        values=month_entry_values, width=5,
                                        state="readonly", style="Field.TCombobox")
            month_entry.grid(row=0, column=3, padx=(0, 16), sticky="w")

            # 从 user_data.json 读取文件路径
            user_file_paths = []
            user_data_file = os.path.join(get_settings_dir(), 'user_data.json')
            if os.path.exists(user_data_file):
                try:
                    with open(user_data_file, 'r', encoding='utf-8') as fjson:
                        data = json.load(fjson)
                        if 'user_data' in data and isinstance(data['user_data'], list):
                            user_file_paths = data['user_data']
                except Exception as e:
                    print(f"读取user_data.json失败: {e}")

            ttk.Label(control_card, text="Excel:",
                      style="CardTitle.TLabel").grid(
                row=0, column=4, padx=(0, 4), sticky="e")

            file_entry = ttk.Entry(control_card, width=36,
                                    style="Field.TEntry")
            file_entry.grid(row=0, column=5, padx=(0, 6), sticky="we")
            if user_file_paths:
                file_path = user_file_paths[0]
                if not os.path.isabs(file_path):
                    file_path = os.path.abspath(
                        os.path.join(self.dir_path, file_path))
                if os.path.exists(file_path):
                    file_entry.insert(0, file_path)

            ttk.Button(control_card, text="选择…",
                       style="Secondary.TButton",
                       command=select_file).grid(row=0, column=6, padx=4)

            control_card.columnconfigure(5, weight=1)

            # 合并刷新功能（给 show_calendar 和右侧事件详情同时刷新用）
            def show_calendar_and_refresh():
                show_calendar()
                refresh_text()

            # ── 主区域：左日历卡 + 右事件详情卡 ──
            body = tk.Frame(cal_window, bg=_CAL_COLOR['window_bg'])
            body.pack(fill="both", expand=True, padx=12, pady=(0, 12))

            body.columnconfigure(0, weight=3, uniform="half")
            body.columnconfigure(1, weight=2, uniform="half")
            body.rowconfigure(0, weight=1)

            # ── 日历卡 ──
            calendar_frame = ttk.Frame(body, style="Card.TFrame",
                                        padding=(12, 10))
            calendar_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

            # 卡标题行（年月 + 今天小圆标签）
            cal_title_bar = tk.Frame(calendar_frame, bg=_CAL_COLOR['card_bg'])
            cal_title_bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))

            import calendar as _cal_module

            weekday_names = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
            first_wd = _cal_module.weekday(self.time_year, self.time_month, 1)  # 0=Mon
            # 转周日开始（Python calendar 默认周一开始，转一下）
            first_wd = (first_wd + 1) % 7
            today_weekday = _cal_module.weekday(self.time_year, self.time_month, self.time_day)
            today_weekday = (today_weekday + 1) % 7

            ttk.Label(cal_title_bar,
                      text=f"{self.time_year} 年 {self.time_month} 月",
                      style="CardTitle.TLabel").pack(side="left")
            tk.Label(cal_title_bar,
                     text=f"  ·  {weekday_names[today_weekday]}",
                     bg=_CAL_COLOR['card_bg'], fg=_CAL_COLOR['text_dim'],
                     font=_CAL_FONT['label']).pack(side="left")
            # 今天小圆标签
            tk.Label(cal_title_bar,
                     text=f"  今天 {self.time_month}/{self.time_day}  ",
                     bg=_CAL_COLOR['accent'], fg='#ffffff',
                     font=('Microsoft YaHei', 8, 'bold'),
                     padx=6, pady=1).pack(side="right")

            # 星期表头（一行淡灰底）
            wd_frame = tk.Frame(calendar_frame, bg=_CAL_COLOR['card_bg'])
            wd_frame.grid(row=1, column=0, sticky="ew", pady=(0, 2))
            for i, wd in enumerate(weekday_names):
                tk.Label(wd_frame, text=wd,
                         bg=_CAL_COLOR['weekday_bg'],
                         fg=_CAL_COLOR['weekday_fg'],
                         font=('Microsoft YaHei', 9, 'bold'),
                         anchor="center", padx=4, pady=4
                         ).grid(row=0, column=i, sticky="ew", padx=1)

            # 日期网格容器（7×6）
            grid_frame = tk.Frame(calendar_frame, bg=_CAL_COLOR['card_bg'])
            grid_frame.grid(row=2, column=0, sticky="nsew")
            for i in range(7):
                grid_frame.columnconfigure(i, weight=1, uniform="col")
            for i in range(6):
                grid_frame.rowconfigure(i, weight=1)

            # 图例
            legend = tk.Frame(calendar_frame, bg=_CAL_COLOR['card_bg'])
            legend.grid(row=3, column=0, sticky="ew", pady=(8, 0))
            tk.Label(legend, text="● 今天  ",
                     bg=_CAL_COLOR['today_bg'],
                     fg=_CAL_COLOR['today_fg'],
                     font=('Microsoft YaHei', 8, 'bold'),
                     padx=6, pady=2).pack(side="left")
            tk.Label(legend, text="● 有事件",
                     bg=_CAL_COLOR['has_event_bg'],
                     fg=_CAL_COLOR['has_event_fg'],
                     font=('Microsoft YaHei', 8, 'bold'),
                     padx=6, pady=2).pack(side="left", padx=(4, 0))
            tk.Label(legend,
                     text="（点击日期查看事件详情）",
                     bg=_CAL_COLOR['card_bg'],
                     fg=_CAL_COLOR['text_dim'],
                     font=('Microsoft YaHei', 8)).pack(side="right")

            calendar_frame.columnconfigure(0, weight=1)
            calendar_frame.rowconfigure(2, weight=1)

            # ── 事件详情卡 ──
            text_frame = ttk.Frame(body, style="Card.TFrame",
                                     padding=(12, 10))
            text_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

            # 卡标题（可点击触发搜索）
            text_title = ttk.Label(text_frame, text="📋 事件详情",
                                    style="CardTitle.TLabel")
            text_title.grid(row=0, column=0, sticky="w", pady=(0, 6))
            # 可点击触发搜索
            text_title.bind("<Button-1>",
                            lambda e: find_line(self.text))

            # 保持 tk.Text（refresh_text 依赖它写数据），只改样式
            self.text = tk.Text(text_frame,
                                state=tk.DISABLED,
                                font=("Microsoft YaHei", 10),
                                bg=_CAL_COLOR['card_bg'],
                                fg=_CAL_COLOR['text'],
                                bd=0, relief="flat",
                                padx=4, pady=4,
                                wrap=tk.WORD,
                                highlightthickness=0,
                                cursor="arrow")
            self.text.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))

            # 文本框滚动条（同样式）
            scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL,
                                       command=self.text.yview)
            scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S), padx=(2, 0))
            self.text.configure(yscrollcommand=scrollbar.set)

            # 标签配色（统一改主色 #4f6ef7）
            self.text.tag_configure("header",
                                    font=("Microsoft YaHei", 12, "bold"),
                                    foreground=_CAL_COLOR['accent'],
                                    spacing1=8, spacing3=4)
            self.text.tag_configure("event",
                                    font=("Microsoft YaHei", 10),
                                    foreground=_CAL_COLOR['text'],
                                    spacing3=4)
            self.text.tag_configure("ai_answer",
                                    font=("Microsoft YaHei", 9, "italic"),
                                    foreground="#10b981",
                                    spacing1=8, spacing3=4)

            # Ctrl+F 搜索快捷键
            def on_ctrl_f(event):
                find_line(self.text)
                return "break"
            self.text.bind("<Control-f>", on_ctrl_f)
            self.text.bind("<Control-F>", on_ctrl_f)
            cal_window.bind("<Control-f>", on_ctrl_f)
            cal_window.bind("<Control-F>", on_ctrl_f)

            text_frame.rowconfigure(1, weight=1)
            text_frame.columnconfigure(0, weight=1)

            # 解析 Excel 数据（有路径就解析，刷新事件列表）
            if user_file_paths:
                analysis_excel(file_entry.get())

            # 初始显示当前月份的日历
            show_calendar()

            cal_window.protocol("WM_DELETE_WINDOW",
                                lambda: check_exit(file_entry.get()))

            cal_window.mainloop()    
        

    def button_minimize(self, event=None):
        # 主窗口已改为 Qt.Tool（不占任务栏），showMinimized 之后窗口没有
        # 任务栏按钮可以点回来，等于凭空消失 —— 所以「最小化」统一收成
        # 桌面悬浮球：既不占地方，点悬浮球又能随时还原完整窗口。
        self.button_maximize_to_desktop()

    def button_maximize_to_desktop(self, event=None):
        # 保存当前窗口几何信息，恢复完整版时使用
        self._saved_geometry = self.saveGeometry()

        # 创建桌面悬浮球
        self.floating_ball = FloatingBall(self)

        # 初始位置取当前窗口的右上角，并保证在屏幕可用区域内
        screen = self.screen().availableGeometry()
        ball_x = self.frameGeometry().right() - FloatingBall.BALL_SIZE
        ball_y = self.frameGeometry().top()
        ball_x = min(max(ball_x, screen.left() + 2), screen.right() - FloatingBall.BALL_SIZE - 2)
        ball_y = min(max(ball_y, screen.top() + 2), screen.bottom() - FloatingBall.BALL_SIZE - 2)
        self.floating_ball.move(ball_x, ball_y)
        self.floating_ball.show()

        # 隐藏完整版主窗口
        self.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_positon = _global_pos(event) - self.frameGeometry().topLeft()
        if event.button() == Qt.RightButton:
            # 显示菜单（包括退出打开日历）
            self.menu = QMenu(self)
            self.menu.addAction('打开日历', self.button_open_calendar)

            # 绘制横杠
            self.menu.addSeparator()
            # 最小化
            self.menu.addAction('缩小为桌面悬浮球', self.button_maximize_to_desktop)
            self.menu.addAction('最小化', self.button_minimize)

            self.menu.addSeparator()
            self.menu.addAction('检查更新…', self.check_update_from_menu)

            self.menu.addSeparator()
            self.menu.addAction('退出', self.button_quit)
            
            _exec_menu(self.menu, _global_pos(event))
               
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.move(_global_pos(event) - self.drag_positon)


class FloatingPanel(QWidget):
    """悬浮球旁弹出的待办事项竖列面板"""

    restore_clicked = Signal()
    mouse_entered = Signal()
    mouse_left = Signal()

    PANEL_WIDTH = 268

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # 每行: {'event': dict, 'is_today': bool, 'sub_label': QLabel}
        self.rows = []

        # 外层布局，留出阴影空间
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)

        # 白色圆角容器
        self.container = QFrame()
        self.container.setObjectName('panel')
        self.container.setFixedWidth(self.PANEL_WIDTH - 24)
        outer.addWidget(self.container)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        # 顶部标题栏
        header = QHBoxLayout()
        header.setSpacing(6)
        title = QLabel('待办事项')
        title.setObjectName('title')
        title.setFont(QFont('Microsoft YaHei', 12, QFont.Bold))
        header.addWidget(title)
        header.addStretch()
        close_btn = QPushButton('×')
        close_btn.setObjectName('closeBtn')
        close_btn.setFixedSize(22, 22)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.hide)
        header.addWidget(close_btn)
        layout.addLayout(header)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet('background-color: #eef1f6;')
        layout.addWidget(line)

        # 待办滚动区域
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.content = QWidget()
        self.content.setObjectName('scrollContent')
        self.list_layout = QVBoxLayout(self.content)
        self.list_layout.setContentsMargins(2, 2, 6, 2)
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch()
        self.scroll.setWidget(self.content)
        layout.addWidget(self.scroll)

        # 底部：回到完整版按钮
        restore_btn = QPushButton('回到完整版')
        restore_btn.setObjectName('restoreBtn')
        restore_btn.setFixedHeight(40)
        restore_btn.setCursor(Qt.PointingHandCursor)
        restore_btn.clicked.connect(self.restore_clicked.emit)
        layout.addWidget(restore_btn)

        # 阴影效果
        shadow = QGraphicsDropShadowEffect(self.container)
        shadow.setBlurRadius(26)
        shadow.setColor(QColor(31, 45, 80, 70))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)

        self.container.setStyleSheet("""
            QFrame#panel { background: #ffffff; border-radius: 16px; }
            QLabel#title { color: #1f2a44; background: transparent; }
            QPushButton#closeBtn { color: #8a94a6; background: transparent;
                                   border: none; font-size: 16px; }
            QPushButton#closeBtn:hover { color: #1f2a44; }
            QFrame#todoRow { background: #f2f6fe; border-radius: 10px; }
            QFrame#todoRowToday { background: #fff3e2; border-radius: 10px; }
            QLabel#rowTitle { color: #1f2a44; background: transparent; }
            QLabel#rowTitleToday { color: #b25c09; background: transparent; }
            QLabel#rowSub { color: #7a8499; background: transparent; }
            QLabel#rowSubToday { color: #e08a1e; background: transparent; }
            QLabel#empty { color: #9aa3b5; background: transparent; }
            QLabel#moreLabel { color: #9aa3b5; background: transparent; }
            QScrollArea { background: transparent; border: none; }
            QScrollArea > QWidget > QWidget { background: transparent; }
            QScrollBar:vertical { background: transparent; width: 8px; margin: 2px; }
            QScrollBar::handle:vertical { background: #d3dbea; border-radius: 4px;
                                         min-height: 30px; }
            QScrollBar::handle:vertical:hover { background: #b9c5da; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
            QPushButton#restoreBtn {
                color: white; border: none; font-size: 13px; font-weight: 600;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #5596f7, stop:1 #2f6be0);
                border-radius: 10px;
            }
            QPushButton#restoreBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #69a5ff, stop:1 #3b7bf0);
            }
            QPushButton#restoreBtn:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #3b7ef0, stop:1 #2456c2);
            }
        """)

        # 面板可见时每秒刷新倒计时
        self.tick_timer = QTimer(self)
        self.tick_timer.setInterval(1000)
        self.tick_timer.timeout.connect(self.update_countdowns)

    @staticmethod
    def relative_text(seconds_diff):
        """与主窗口保持一致的相对时间描述"""
        days = seconds_diff // (24 * 3600)
        hours = (seconds_diff % (24 * 3600)) // 3600
        minutes = (seconds_diff % 3600) // 60
        seconds = seconds_diff % 60
        if days > 0:
            return f"{days + 1}天后"
        if hours > 0:
            return f"{hours}小时后"
        if minutes > 0:
            return f"{minutes}分钟后"
        return f"{seconds}秒后"

    def _collect_items(self):
        """返回 (今日事件列表, 未来事件列表[(event, diff)...])"""
        now = QDateTime.currentDateTime()
        year = now.date().year()
        today_items = []
        future_items = []
        for event in self.main_window.events:
            try:
                month = int(event['month'])
                day = int(event['day'])
            except (KeyError, TypeError, ValueError):
                continue
            event_dt = QDateTime(year, month, day, 0, 0, 0)
            if month == now.date().month() and day == now.date().day():
                today_items.append(event)
            else:
                diff = now.secsTo(event_dt)
                if diff > 0:
                    future_items.append((event, diff))
        today_items.sort(key=lambda e: str(e.get('things', '')))
        future_items.sort(key=lambda item: item[1])
        return today_items, future_items

    def refresh(self):
        """重新构建待办列表内容"""
        # 清空旧行（保留末尾的 stretch）
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self.rows = []

        today_items, future_items = self._collect_items()
        visible_future = future_items[:20]

        card_count = 0
        for event in today_items:
            self._add_row(event, is_today=True)
            card_count += 1
        for event, _diff in visible_future:
            self._add_row(event, is_today=False)
            card_count += 1

        has_more = len(future_items) > len(visible_future)

        if card_count == 0:
            empty = QLabel('暂无待办事项\n请先从 Excel 导入事件')
            empty.setObjectName('empty')
            empty.setAlignment(Qt.AlignCenter)
            empty.setFont(QFont('Microsoft YaHei', 11))
            empty.setWordWrap(True)
            self.list_layout.insertWidget(0, empty)
            content_h = 120
        else:
            if has_more:
                more = QLabel(f"还有 {len(future_items) - len(visible_future)} 个待办…")
                more.setObjectName('moreLabel')
                more.setAlignment(Qt.AlignCenter)
                more.setFont(QFont('Microsoft YaHei', 9))
                self.list_layout.insertWidget(self.list_layout.count() - 1, more)
            content_h = min(300, max(96, card_count * 56 + (24 if has_more else 0)))

        self.scroll.setFixedHeight(content_h)
        self.setFixedWidth(self.PANEL_WIDTH)
        self.adjustSize()
        self.update_countdowns()
        self.tick_timer.start()

    def _add_row(self, event, is_today):
        thing = str(event.get('things', '')).strip()
        if not thing or thing == 'nan':
            thing = '(未命名事项)'

        row = QFrame()
        row.setObjectName('todoRowToday' if is_today else 'todoRow')

        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(10, 8, 10, 8)
        row_layout.setSpacing(8)

        dot = QLabel()
        dot.setFixedSize(8, 8)
        if is_today:
            dot.setStyleSheet('background-color: #f59e0b; border-radius: 4px; margin-top: 5px;')
        else:
            dot.setStyleSheet('background-color: #3b82f6; border-radius: 4px; margin-top: 5px;')
        row_layout.addWidget(dot, alignment=Qt.AlignTop)

        v = QVBoxLayout()
        v.setSpacing(2)
        title = QLabel(thing)
        title.setObjectName('rowTitleToday' if is_today else 'rowTitle')
        title.setWordWrap(True)
        title.setFont(QFont('Microsoft YaHei', 10, QFont.Bold if is_today else QFont.Normal))
        sub = QLabel()
        sub.setObjectName('rowSubToday' if is_today else 'rowSub')
        sub.setFont(QFont('Microsoft YaHei', 9))
        v.addWidget(title)
        v.addWidget(sub)
        row_layout.addLayout(v, 1)

        self.list_layout.insertWidget(self.list_layout.count() - 1, row)
        self.rows.append({'event': event, 'is_today': is_today, 'sub_label': sub})

    def update_countdowns(self):
        """每秒更新每行的相对时间（不重建控件，避免闪烁）"""
        now = QDateTime.currentDateTime()
        year = now.date().year()
        for item in self.rows:
            event = item['event']
            try:
                month = int(event['month'])
                day = int(event['day'])
            except (KeyError, TypeError, ValueError):
                continue
            event_dt = QDateTime(year, month, day, 0, 0, 0)
            if item['is_today']:
                item['sub_label'].setText('今天')
            else:
                diff = now.secsTo(event_dt)
                if diff <= 0:
                    item['sub_label'].setText(f"{event['month']}.{event['day']} · 已过期")
                else:
                    item['sub_label'].setText(
                        f"{event['month']}.{event['day']} · {self.relative_text(diff)}")

    def hideEvent(self, event):
        self.tick_timer.stop()
        super().hideEvent(event)

    def enterEvent(self, event):
        self.mouse_entered.emit()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.mouse_left.emit()
        super().leaveEvent(event)


class FloatingBall(QWidget):
    """桌面悬浮球：可拖拽移动，鼠标悬停展开待办竖列"""

    BALL_SIZE = 48

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(self.BALL_SIZE, self.BALL_SIZE)

        icon_size = int(self.BALL_SIZE * 0.5)
        self.calendar_pixmap = QPixmap(main_window.icon_path).scaled(
            icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.panel = FloatingPanel(main_window)
        self.panel.restore_clicked.connect(self.restore_full)
        self.panel.mouse_entered.connect(self._cancel_hide)
        self.panel.mouse_left.connect(self._schedule_hide)

        # 离开悬浮球/面板后延迟收起，避免移动间隙误触
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.setInterval(260)
        self.hide_timer.timeout.connect(self.panel.hide)

        self._drag_offset = QPoint()
        self._pressed = False
        self._moved = False

        self.snap_anim = QPropertyAnimation(self, b'pos', self)
        self.snap_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.snap_anim.setDuration(200)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)

        w = self.width()
        h = self.height()
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor('#5aa0ff'))
        grad.setColorAt(1.0, QColor('#2e6be6'))
        p.setPen(Qt.NoPen)
        p.setBrush(grad)
        p.drawEllipse(QRectF(1, 1, w - 2, h - 2))

        # 白色圆底 + 日历图标（位置和大小均按球直径比例计算）
        white_margin = w * 0.18
        white_size = w - 2 * white_margin
        p.setBrush(QColor(255, 255, 255, 255))
        p.drawEllipse(QRectF(white_margin, white_margin, white_size, white_size))

        icon_margin = w * 0.25
        icon_rect_size = w - 2 * icon_margin
        target = QRectF(icon_margin, icon_margin, icon_rect_size, icon_rect_size)
        p.drawPixmap(target, self.calendar_pixmap,
                     QRectF(0, 0, self.calendar_pixmap.width(), self.calendar_pixmap.height()))

    # ---------- 悬停展开 / 收起 ----------
    def enterEvent(self, event):
        self._cancel_hide()
        self.show_panel()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._schedule_hide()
        super().leaveEvent(event)

    def _cancel_hide(self):
        self.hide_timer.stop()

    def _schedule_hide(self):
        self.hide_timer.start()

    def show_panel(self):
        self.panel.refresh()
        self.reposition_panel()
        self.panel.show()
        self.panel.raise_()

    def reposition_panel(self):
        """面板出现在悬浮球靠屏幕内侧，自动避开屏幕边缘"""
        screen = QApplication.screenAt(self.frameGeometry().center())
        if screen is None:
            screen = QApplication.primaryScreen()
        geo = screen.availableGeometry()
        ball = self.frameGeometry()

        pw = self.panel.width()
        ph = self.panel.height()
        if ball.center().x() < geo.center().x():
            x = ball.right() + 10
        else:
            x = ball.left() - 10 - pw
        x = min(max(x, geo.left() + 6), geo.right() - pw - 6)

        y = ball.center().y() - ph // 2
        y = min(max(y, geo.top() + 6), geo.bottom() - ph - 6)
        self.panel.move(x, y)

    # ---------- 拖拽 ----------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.snap_anim.stop()
            self._pressed = True
            self._moved = False
            self._drag_offset = _global_pos(event) - self.frameGeometry().topLeft()
        elif event.button() == Qt.RightButton:
            self._show_menu(_global_pos(event))

    def mouseMoveEvent(self, event):
        if self._pressed and event.buttons() & Qt.LeftButton:
            self._moved = True
            self.move(_global_pos(event) - self._drag_offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._pressed:
            self._pressed = False
            if not self._moved:
                # 单击（未拖动）切换面板
                if self.panel.isVisible():
                    self.panel.hide()
                else:
                    self.show_panel()
            else:
                self._snap_to_edge()

    def _snap_to_edge(self):
        """拖动结束后，靠近屏幕边缘时自动吸附（类似豆包悬浮球）"""
        screen = QApplication.screenAt(self.frameGeometry().center())
        if screen is None:
            screen = QApplication.primaryScreen()
        geo = screen.availableGeometry()
        center = self.frameGeometry().center()
        dist_left = center.x() - geo.left()
        dist_right = geo.right() - center.x()

        target = QPoint(self.pos())
        if min(dist_left, dist_right) <= 80:
            if dist_left < dist_right:
                target.setX(geo.left())
            else:
                target.setX(geo.right() - self.width())
        target.setY(min(max(target.y(), geo.top()), geo.bottom() - self.height()))

        if target != self.pos():
            self.snap_anim.stop()
            self.snap_anim.setStartValue(QPoint(self.pos()))
            self.snap_anim.setEndValue(target)
            self.snap_anim.start()

    def _show_menu(self, pos):
        menu = QMenu(self)
        menu.addAction('回到完整版', self.restore_full)
        menu.addSeparator()
        # 退出走主窗口的彻底退出（关全部窗口 + 看门狗强杀兜底），
        # 不能只用 QApplication.quit —— 那样残留 Tk 窗口时进程退不干净，
        # exe 会被占用删不掉。
        menu.addAction('退出', self.main_window.button_quit)
        _exec_menu(menu, pos)

    def restore_full(self):
        """收起悬浮球，回到完整版主窗口"""
        self.hide_timer.stop()
        self.panel.hide()
        main_window = self.main_window
        saved = getattr(main_window, '_saved_geometry', None)
        if saved is not None:
            main_window.restoreGeometry(saved)
        main_window.show()
        main_window.raise_()
        main_window.activateWindow()
        main_window.floating_ball = None
        self.panel.close()
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # 主窗口缩小为悬浮球后，关闭悬浮窗不应退出整个程序
    app.setQuitOnLastWindowClosed(False)
    window = MyWindow()
    window.show()
    # 等窗口 show() + _fit_content_height() 完成布局后再恢复位置：
    # 此时 self.pos() 还是 Qt 默认值，restore 会读配置里的相对坐标并 move 过去。
    # 如果没保存过位置，restore 直接 return，不影响默认行为。
    QTimer.singleShot(0, window.restore_window_position)
    # Qt6 是 app.exec()，Qt5 是 app.exec_()
    _app_exec = getattr(app, "exec", None) or getattr(app, "exec_", None)
    sys.exit(_app_exec())