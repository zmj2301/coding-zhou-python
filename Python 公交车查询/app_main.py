#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""湘潭实时公交·最优乘车方案 —— Kivy 图形界面（v1.1.0）"""
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import StringProperty, ListProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from busapp import planner

APP_NAME = "湘潭实时公交"
APP_VERSION = planner.cl.APP_VERSION
BUILD_NO = "20261017"

BG = (0.96, 0.97, 0.99, 1)
CARD = (1, 1, 1, 1)
PRIMARY = (0.11, 0.45, 0.85, 1)
SUCCESS = (0.13, 0.65, 0.42, 1)
WARN = (0.92, 0.62, 0.13, 1)
TEXT = (0.13, 0.15, 0.19, 1)
SUBTLE = (0.42, 0.45, 0.51, 1)


def _register_fonts():
    """注册中文字体（须在 App.build 之后调用，避免过早初始化文本子系统）。

    Kivy 默认字体不含 CJK，中文会渲染成方框。
    """
    from kivy.core.text import LabelBase
    from kivy.logger import Logger

    candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyhbd.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/system/fonts/NotoSansCJK-Regular.ttc",
        "/system/fonts/DroidSansFallback.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                LabelBase.register(name="CN", fn_regular=path)
                Logger.info("BusApp: 已注册中文字体 %s" % path)
                return True
            except Exception as exc:
                Logger.warning("BusApp: 字体注册失败 %s (%s)" % (path, exc))
    Logger.warning("BusApp: 未找到中文字体，中文可能显示为方框")
    return False


FONT = "Roboto"
_HAS_CJK = False

_win = None
try:
    _win = Window
except Exception:
    pass
if _win is not None:
    try:
        Window.clearcolor = BG
    except Exception:
        pass


class RouteRow(BoxLayout):
    """单条行程分段。"""

    def __init__(self, kind, title, minutes, detail="", **kw):
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(52), **kw)
        self.add_widget(Label(
            font_name=FONT,
            text=u"%d\u5206" % round(minutes), size_hint_x=None, width=dp(62),
            color=PRIMARY if kind == "bus" else SUCCESS,
            font_size=dp(15), bold=True, halign="center", valign="middle"))
        self.add_widget(Label(font_name=FONT, text=title, color=TEXT, font_size=dp(14),
                              halign="left", valign="middle", shorten=True))
        if detail:
            self.add_widget(Label(
                font_name=FONT,
                text=detail, color=SUBTLE, font_size=dp(11),
                size_hint_x=None, width=dp(120), halign="right", valign="middle",
                shorten=True, shorten_from="right"))


class PlanCard(BoxLayout):
    """一个完整方案卡片：白底 + 左侧色条（绿=实时数据 / 橙=估算）。"""

    def __init__(self, index, plan, **kw):
        n = max(1, len(plan.legs))
        extra = dp(24) if plan.note else 0
        super().__init__(orientation="vertical", size_hint_y=None,
                         height=dp(56 + 50 * n) + extra,
                         padding=[dp(14), dp(10), dp(14), dp(10)],
                         spacing=dp(4), **kw)
        from kivy.graphics import Color, Rectangle

        accent = SUCCESS if plan.has_realtime else WARN
        with self.canvas.before:
            Color(*CARD)
            self._bg = Rectangle(pos=self.pos, size=self.size)
            Color(*accent)
            self._bar = Rectangle(pos=self.pos, size=(dp(4), self.size[1]))
        self.bind(pos=self._sync, size=self._sync)

        # 卡片头部：方案序号 + 总耗时 + 换乘/实时标记
        head_row = BoxLayout(size_hint_y=None, height=dp(30))
        head_row.add_widget(Label(
            font_name=FONT,
            text=u"方案 %d  ·  总计 %.0f 分钟" % (index, plan.total),
            color=TEXT, font_size=dp(16), bold=True,
            halign="left", valign="middle"))
        badges = u"换乘 %d 次" % plan.transfers
        if plan.has_realtime:
            badges += u"  ·  实时"
        else:
            badges += u"  ·  估算"
        head_row.add_widget(Label(
            font_name=FONT, text=badges,
            color=SUCCESS if plan.has_realtime else WARN,
            font_size=dp(12), size_hint_x=None, width=dp(120),
            halign="right", valign="middle"))
        self.add_widget(head_row)

        for leg in plan.legs:
            self.add_widget(RouteRow(leg.kind, leg.title, leg.minutes, leg.detail))

        if plan.note:
            self.add_widget(Label(
                font_name=FONT, text=u"⚠ " + plan.note, color=WARN,
                font_size=dp(11), size_hint_y=None, height=dp(22),
                halign="left", valign="middle"))

    def _sync(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._bar.pos = self.pos
        self._bar.size = (dp(4), self.size[1])



class BusApp(App):
    title = "%s v%s" % (APP_NAME, APP_VERSION)

    status = StringProperty("")
    busy = BooleanProperty(False)
    origin_text = StringProperty("\u672a\u6765\u7d20\u517b")
    dest_text = StringProperty("\u94ed\u9e3f\u7ff0\u6797\u5c45")

    def build(self):
        # 字体必须在窗口创建之后注册，否则文本子系统初始化顺序会出错
        global FONT, _HAS_CJK
        if _register_fonts():
            FONT = "CN"
            _HAS_CJK = True
        if Window is not None:
            try:
                Window.clearcolor = BG
                Window.bind(on_request_close=self._on_close)
            except Exception:
                pass
        root = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))

        # 顶部标题 + 版本号
        title_bar = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))
        titles = BoxLayout(orientation="vertical")
        titles.add_widget(Label(
            font_name=FONT,
            text=u"\U0001f68c %s" % APP_NAME, font_size=dp(22), bold=True,
            color=TEXT, halign="left", valign="bottom", size_hint_y=None, height=dp(30)))
        titles.add_widget(Label(
            font_name=FONT,
            text=u"\u7248\u672c v%s \u00b7 \u6784\u5efa%s \u00b7 %s" % (APP_VERSION, BUILD_NO, planner.cl.CITY_NAME),
            font_size=dp(11), color=SUBTLE, halign="left", valign="top",
            size_hint_y=None, height=dp(18)))
        title_bar.add_widget(titles)
        root.add_widget(title_bar)

        # 输入区
        card = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(150),
                         padding=dp(12), spacing=dp(6))
        card.add_widget(Label(font_name=FONT, text=u"\u8d77\u70b9\uff08\u652f\u6301\u5c0f\u533a/\u5b66\u6821/\u5730\u6807\uff09",
                              font_size=dp(12), color=SUBTLE, size_hint_y=None,
                              height=dp(18), halign="left", valign="middle"))
        self.origin_input = TextInput(
            text=self.origin_text, multiline=False, size_hint_y=None, height=dp(42),
            font_name=FONT, font_size=dp(15), padding=[dp(10), dp(10)])
        card.add_widget(self.origin_input)
        card.add_widget(Label(font_name=FONT, text=u"\u7ec8\u70b9\uff08\u652f\u6301\u7ad9\u540d/\u5730\u6807\uff09",
                              font_size=dp(12), color=SUBTLE, size_hint_y=None,
                              height=dp(18), halign="left", valign="middle"))
        self.dest_input = TextInput(
            text=self.dest_text, multiline=False, size_hint_y=None, height=dp(42),
            font_name=FONT, font_size=dp(15), padding=[dp(10), dp(10)])
        card.add_widget(self.dest_input)
        root.add_widget(card)

        # 查询按钮
        self.search_btn = Button(
            text=u"\u67e5\u8be2\u6700\u4f18\u65b9\u6848",
            size_hint_y=None, height=dp(50), size_hint_x=1,
            font_name=FONT, font_size=dp(17),
            background_normal="", background_color=PRIMARY,
            color=(1, 1, 1, 1))
        self.search_btn.bind(on_release=self._on_search)
        root.add_widget(self.search_btn)

        # 进度条
        self.progress = ProgressBar(max=1, value=0, size_hint_y=None, height=dp(4),
                                    opacity=0)
        root.add_widget(self.progress)

        # 状态栏
        self.status_label = Label(
            font_name=FONT,
            text=u"\u8f93\u5165\u8d77\u7ec8\u70b9\uff0c\u70b9\u300c\u67e5\u8be2\u6700\u4f18\u65b9\u6848\u300d",
            font_size=dp(13), color=SUBTLE, size_hint_y=None, height=dp(26),
            halign="left", valign="middle", shorten=True, shorten_from="right")
        root.add_widget(self.status_label)

        # 结果区
        self.results = BoxLayout(orientation="vertical", spacing=dp(10),
                                size_hint_y=None, height=dp(10))
        self.results.bind(minimum_height=lambda inst, val: setattr(inst, "height", val))
        self.scroll = ScrollView(do_scroll_x=False, bar_width=dp(3))
        self.scroll.add_widget(self.results)
        root.add_widget(self.scroll)
        return root

    def _set_status(self, text, color=None):
        self.status_label.text = text
        if color is not None:
            self.status_label.color = color

    def _on_search(self, *_):
        if self.busy:
            return
        o = self.origin_input.text.strip()
        d = self.dest_input.text.strip()
        if not o or not d:
            self._set_status(u"\u8bf7\u586b\u5199\u8d77\u70b9\u548c\u7ec8\u70b9", WARN)
            return
        self.busy = True
        self.search_btn.text = u"\u67e5\u8be2\u4e2d..."
        self.search_btn.disabled = True
        self.progress.opacity = 1
        self.progress.value = 0
        self._set_status(u"\u6b63\u5728\u62c9\u53d6\u5b9e\u65f6\u8f66\u8f86\u6570\u636e...")
        self.results.clear_widgets()
        Clock.schedule_interval(lambda dt: self._tick(dt), 0.05)
        threading.Thread(target=self._work, args=(o, d), daemon=True).start()

    def _tick(self, dt):
        self.progress.value = (self.progress.value + dt * 1.6) % 1
        return True

    def _work(self, origin, dest):
        try:
            o_stops, o_desc = planner.resolve_origin(origin)
            if not o_stops:
                Clock.schedule_once(lambda dt: self._fail(o_desc), 0)
                return
            d_stops, d_desc = planner.resolve_destination(dest)
            if not d_stops:
                Clock.schedule_once(lambda dt: self._fail(u"\u7ec8\u70b9\u672a\u627e\u5230\uff1a%s" % d_desc), 0)
                return
            plans = planner.plan_route(o_stops, d_stops)
            Clock.schedule_once(lambda dt: self._render(plans, o_desc, d_desc), 0)
        except Exception as exc:
            Clock.schedule_once(lambda dt: self._fail(u"\u67e5\u8be2\u5931\u8d25\uff1a%s" % exc), 0)

    def _fail(self, msg):
        self.busy = False
        self.search_btn.text = u"\u67e5\u8be2\u6700\u4f18\u65b9\u6848"
        self.search_btn.disabled = False
        self.progress.opacity = 0
        self._set_status(msg, WARN)

        content = Label(font_name=FONT, text=msg, font_size=dp(15), color=WARN, padding=dp(20))
        Popup(title=u"\u63d0\u793a", content=content, size_hint=(0.86, 0.32)).open()

    def _render(self, plans, o_desc, d_desc):
        self.busy = False
        self.search_btn.text = u"\u67e5\u8be2\u6700\u4f18\u65b9\u6848"
        self.search_btn.disabled = False
        self.progress.opacity = 0
        now = time.strftime("%H:%M:%S")
        self._set_status(u"\u8d77\u70b9 %s\uff5c\u7ec8\u70b9 %s\uff5c\u67e5\u8be2\u4e8e %s"
                         % (o_desc, d_desc, now), SUCCESS)
        for i, p in enumerate(plans, 1):
            card = PlanCard(i, p)
            self.results.add_widget(card)

    def _on_close(self, *_):
        self.stop()
        return True


if __name__ == "__main__":
    BusApp().run()