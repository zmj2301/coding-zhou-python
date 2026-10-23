# -*- coding: utf-8 -*-
"""积分看板面板 —— 桌面宠物的积分/签到/预测可视化

数据来自 ECS 上的 /opt/credits 查询服务（127.0.0.1:8899），
本地通过 SSH 隧道访问，不在公网暴露任何凭据。

显示内容（每家一卡）：
  - 余额进度条 + 今日已用 / 预测用量
  - 今日签到状态（连续天数）
  - 今日用量建议（最大化但不超限）
  - 低余额告警（类似钉钉剩余提醒，分档变色）
  - 耗尽预测日期
  - 临近过期积分规划（含上学日/节假日考量）
底部：下次刷新倒计时 + 手动刷新按钮 + 最后更新时间。

只用标准库发 HTTP（urllib），不引入 requests 依赖。
"""
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QLinearGradient
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout,
)

# ---------------- 配置 ----------------
ECS_HOST = "39.107.96.165"
API_URL = "http://127.0.0.1:8899/api/credits"
TUNNEL_HOST = "127.0.0.1"
TUNNEL_PORT = 8899
REFRESH_SECONDS = 300          # 5 分钟，对齐用户要求
REQUEST_TIMEOUT = 12

PROVIDER_META = {
    "trae":      {"name": "TRAE",      "icon": "🛠", "color": "#2f6fd0"},
    "workbuddy": {"name": "WorkBuddy", "icon": "🐣", "color": "#7b5bd6"},
    "minimax":   {"name": "MiniMax",   "icon": "🤖", "color": "#0f9b7a"},
}

ALERT_COLORS = {
    "ok":      ("#1a7f37", "#e8f5ec", "状态良好"),
    "warning": ("#9a6700", "#fff4e5", "余额偏低"),
    "critical":("#b42318", "#fdecea", "即将耗尽"),
}

DAY_TYPE_LABEL = {"full": "可使用", "half": "半天", "off": "上学日"}


def _fmt(v, digits: int = 1) -> str:
    """积分格式化：None 显示 —，数值去掉无意义的 .0"""
    if v is None:
        return "—"
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    if abs(f - round(f)) < 0.05:
        return str(int(round(f)))
    return ("%." + str(digits) + "f") % f


# ---------------- 后台取数（不阻塞 UI）----------------
class FetchThread(QThread):
    done = Signal(dict)
    failed = Signal(str)

    def __init__(self, force: bool = False, parent=None):
        super().__init__(parent)
        self.force = force

    def run(self):
        url = API_URL + ("?refresh=1" if self.force else "")
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        try:
            # 绕过系统代理：本机设了 http_proxy，127.0.0.1 的请求也会被
            # 发给代理并返回 502，很容易被误判成 ECS 服务挂了。
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(req, timeout=REQUEST_TIMEOUT) as r:
                self.done.emit(json.loads(r.read().decode("utf-8")))
        except urllib.error.HTTPError as e:
            self.failed.emit("服务返回 %s" % e.code)
        except Exception as e:
            self.failed.emit(str(e))


def tunnel_alive() -> bool:
    """检查 SSH 隧道是否通。"""
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open("http://%s:%d/health" % (TUNNEL_HOST, TUNNEL_PORT),
                         timeout=4) as r:
            return json.loads(r.read().decode("utf-8")).get("ok", False)
    except Exception:
        return False


# ---------------- 进度条 ----------------
class BalanceBar(QWidget):
    """余额条：已用 / 总量。total 未知时退化为纯数值展示。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(10)
        self._pct = 0.0
        self._color = QColor("#2f6fd0")
        self._bg = QColor("#e6e8eb")
        self._unknown = False

    def set_value(self, remaining, total, color="#2f6fd0"):
        self._color = QColor(color)
        if total in (None, 0):
            self._unknown = True
            self._pct = 0.0
        else:
            self._unknown = False
            used = max(float(total) - float(remaining), 0.0)
            self._pct = max(min(used / float(total), 1.0), 0.0)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.height() / 2.0
        p.setPen(Qt.NoPen)
        p.setBrush(self._bg)
        p.drawRoundedRect(0, r - 4, self.width(), 8, 4, 4)
        if self._unknown:
            # 总量未知（MiniMax 只给余额）→ 用渐变示意
            g = QLinearGradient(0, 0, self.width(), 0)
            g.setColorAt(0.0, self._color)
            g.setColorAt(1.0, QColor("#ffffff"))
            p.setBrush(QBrush(g))
            p.drawRoundedRect(0, r - 4, max(self.width() * 0.35, 8), 8, 4, 4)
        elif self._pct > 0:
            p.setBrush(self._color)
            p.drawRoundedRect(0, r - 4, max(self.width() * self._pct, 6), 8, 4, 4)
        p.end()


# ---------------- 单家卡片 ----------------
class ProviderCard(QFrame):
    def __init__(self, key: str, parent=None):
        super().__init__(parent)
        self.key = key
        meta = PROVIDER_META.get(key, {})
        self.accent = meta.get("color", "#2f6fd0")
        self.setObjectName("card")
        self.setStyleSheet("""
            QFrame#card {
                background: #ffffff;
                border: 1px solid #e3e5e8;
                border-left: 4px solid %s;
                border-radius: 8px;
            }
        """ % self.accent)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(6)

        # 标题行：名称 + 签到状态
        top = QHBoxLayout()
        self.lbl_name = QLabel("%s %s" % (meta.get("icon", ""), meta.get("name", key)))
        self.lbl_name.setStyleSheet(
            "font-size:14px; font-weight:600; color:#1f2328; background:transparent;")
        top.addWidget(self.lbl_name)
        top.addStretch(1)
        self.lbl_checkin = QLabel("—")
        self.lbl_checkin.setStyleSheet(
            "font-size:12px; color:#57606a; background:transparent; padding:2px 8px;"
            "border-radius:9px; background:#f0f2f4;")
        top.addWidget(self.lbl_checkin)
        lay.addLayout(top)

        # 余额行
        self.lbl_balance = QLabel("余额 —")
        self.lbl_balance.setStyleSheet(
            "font-size:20px; font-weight:700; color:#1f2328; background:transparent;")
        lay.addWidget(self.lbl_balance)

        self.bar = BalanceBar()
        lay.addWidget(self.bar)

        # 明细网格
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(3)
        self.cells = {}
        for i, (label, _key) in enumerate([
            ("今日已用", "used"),
            ("预测用量", "pred"),
            ("今日目标", "target"),
            ("可用天数", "days"),
        ]):
            cap = QLabel(label)
            cap.setStyleSheet("font-size:11px; color:#8b949e; background:transparent;")
            val = QLabel("—")
            val.setStyleSheet("font-size:12px; font-weight:600; color:#24292f; background:transparent;")
            grid.addWidget(cap, i // 2, (i % 2) * 2)
            grid.addWidget(val, i // 2, (i % 2) * 2 + 1)
            self.cells[_key] = val
        lay.addLayout(grid)

        # 告警条
        self.lbl_alert = QLabel("")
        self.lbl_alert.setWordWrap(True)
        self.lbl_alert.setStyleSheet("font-size:11px; background:transparent; padding:4px 6px;"
                                     "border-radius:4px;")
        lay.addWidget(self.lbl_alert)

        # 耗尽预测
        self.lbl_runway = QLabel("")
        self.lbl_runway.setStyleSheet(
            "font-size:11px; color:#57606a; background:transparent;")
        lay.addWidget(self.lbl_runway)

        # 到期规划
        self.lbl_expiry = QLabel("")
        self.lbl_expiry.setWordWrap(True)
        self.lbl_expiry.setStyleSheet(
            "font-size:11px; color:#8b5e00; background:transparent;")
        lay.addWidget(self.lbl_expiry)

        self._empty("等待数据…")

    def _empty(self, msg):
        self.lbl_balance.setText("余额 —")
        self.lbl_checkin.setText("—")
        self.lbl_alert.setText(msg)
        self.lbl_runway.setText("")
        self.lbl_expiry.setText("")

    def update_data(self, d: Dict[str, Any]):
        if d.get("error"):
            self._empty("⚠ %s" % d["error"])
            return

        b = d.get("balance") or {}
        remain = b.get("remaining")
        total = b.get("total")
        self.lbl_balance.setText("余额 %s%s" % (
            _fmt(remain), (" / %s" % _fmt(total)) if total else ""))
        self.bar.set_value(remain, total, self.accent)

        ck = d.get("checkin") or {}
        if ck.get("done"):
            self.lbl_checkin.setText("✓ 已签到 %s天" % (ck.get("streak") or 0))
            self.lbl_checkin.setStyleSheet(
                "font-size:12px; color:#1a7f37; background:#e8f5ec; padding:2px 8px;"
                "border-radius:9px;")
        else:
            self.lbl_checkin.setText("✗ 未签到")
            self.lbl_checkin.setStyleSheet(
                "font-size:12px; color:#b42318; background:#fdecea; padding:2px 8px;"
                "border-radius:9px;")

        self.cells["used"].setText(_fmt(d.get("used_today")))
        self.cells["pred"].setText(_fmt(d.get("predicted_today")))

        ta = d.get("today_advice") or {}
        tgt = ta.get("target") or 0
        left = ta.get("suggest_remaining") or 0
        if left > 0:
            self.cells["target"].setText("%s（还可用 %s）" % (_fmt(tgt), _fmt(left)))
        else:
            self.cells["target"].setText(_fmt(tgt))

        rw = d.get("runway") or {}
        if rw.get("days") is not None:
            al = d.get("alert") or {}
            self.cells["days"].setText("%s 天" % rw.get("days"))
        else:
            self.cells["days"].setText("—")

        # 告警
        al = d.get("alert") or {}
        level = al.get("level", "ok")
        fg, bg, _ = ALERT_COLORS.get(level, ALERT_COLORS["ok"])
        day_t = DAY_TYPE_LABEL.get(d.get("day_type", ""), "")
        extra = " · 今日%s" % day_t if day_t else ""
        self.lbl_alert.setText("%s（%s）%s" % (al.get("message", ""),
                                              _fmt(al.get("percent")) + "%"
                                              if al.get("percent") is not None else "—",
                                              extra))
        self.lbl_alert.setStyleSheet(
            "font-size:11px; color:%s; background:%s; padding:4px 6px; border-radius:4px;"
            % (fg, bg))

        # 耗尽
        if rw.get("days") is not None:
            self.lbl_runway.setText("📉 预计 %s（%s）耗尽" % (rw.get("date"), rw.get("note", "")))
        else:
            self.lbl_runway.setText("📉 %s" % (rw.get("note") or ""))

        # 到期规划
        ep = (d.get("expiry_plan") or {})
        items = ep.get("items") or []
        if items:
            lines = ["⏰ 临近过期规划："]
            for it in items[:3]:
                lines.append("   %s 到期 %s 分，剩 %s 个可用日，需日用 %s（风险%s）" % (
                    it.get("expire_str"), _fmt(it.get("remaining")),
                    it.get("usable_days"), _fmt(it.get("per_day_need")), it.get("risk")))
            self.lbl_expiry.setText("\n".join(lines))
        else:
            self.lbl_expiry.setText("")


# ---------------- 主面板 ----------------
class CreditsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("积分看板")
        self.resize(460, 640)
        self.setStyleSheet("""
            QWidget { background:#f6f7f9; font-family:'Microsoft YaHei UI','Segoe UI',sans-serif; }
            QLabel#title { font-size:16px; font-weight:700; color:#1f2328; }
            QLabel#sub { font-size:11px; color:#8b949e; }
            QPushButton {
                background:#ffffff; border:1px solid #d0d7de; border-radius:6px;
                padding:5px 12px; font-size:12px; color:#24292f;
            }
            QPushButton:hover { background:#f3f4f6; border-color:#a8b0b8; }
            QPushButton:disabled { color:#a8b0b8; }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(10)

        # 标题行
        head = QHBoxLayout()
        tcol = QVBoxLayout()
        tcol.setSpacing(1)
        lbl_t = QLabel("积分看板")
        lbl_t.setObjectName("title")
        self.lbl_sub = QLabel("正在连接 ECS 查询服务…")
        self.lbl_sub.setObjectName("sub")
        tcol.addWidget(lbl_t)
        tcol.addWidget(self.lbl_sub)
        head.addLayout(tcol)
        head.addStretch(1)

        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.setFixedWidth(64)
        self.btn_refresh.clicked.connect(self._manual_refresh)
        head.addWidget(self.btn_refresh)
        root.addLayout(head)

        # 卡片区（可滚动）
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.inner = QWidget()
        self.inner.setStyleSheet("background:#f6f7f9;")
        self.card_layout = QVBoxLayout(self.inner)
        self.card_layout.setContentsMargins(0, 0, 0, 0)
        self.card_layout.setSpacing(9)
        self.scroll.setWidget(self.inner)
        root.addWidget(self.scroll, 1)

        self.cards = {}
        for key in ("trae", "workbuddy", "minimax"):
            c = ProviderCard(key)
            self.card_layout.addWidget(c)
            self.cards[key] = c
        self.card_layout.addStretch(1)

        # 底部状态条
        foot = QHBoxLayout()
        self.lbl_countdown = QLabel("—")
        self.lbl_countdown.setStyleSheet("font-size:11px; color:#57606a;")
        foot.addWidget(self.lbl_countdown)
        foot.addStretch(1)
        self.lbl_updated = QLabel("")
        self.lbl_updated.setStyleSheet("font-size:11px; color:#8b949e;")
        foot.addWidget(self.lbl_updated)
        root.addLayout(foot)

        self._data = None
        self._thread = None
        self._last_ok = 0.0

        # 1 秒心跳：驱动倒计时与超时重试
        self._tick = QTimer(self)
        self._tick.timeout.connect(self._on_tick)
        self._tick.start(1000)

        # 首次加载
        QTimer.singleShot(200, self.refresh)

    # ---------------- 取数 ----------------
    def refresh(self, force: bool = False):
        if self._thread and self._thread.isRunning():
            return
        self.btn_refresh.setEnabled(False)
        self.btn_refresh.setText("…")
        self._thread = FetchThread(force=force, parent=self)
        self._thread.done.connect(self._on_data)
        self._thread.failed.connect(self._on_error)
        self._thread.start()

    def _manual_refresh(self):
        self.refresh(force=True)

    def _on_data(self, data: dict):
        self._data = data
        self._last_ok = time.time()
        for key, card in self.cards.items():
            card.update_data((data.get("providers") or {}).get(key) or {})

        server_next = data.get("_next_refresh_in")
        self.lbl_sub.setText("开学模式已生效" if data.get("school_mode")
                             else "非开学模式（全部按可用日计算）")
        ts = data.get("updated_at")
        if ts:
            # 不用 fromisoformat（Python 3.7 才有），手工截取更保险
            try:
                dt = datetime.strptime(str(ts)[:19], "%Y-%m-%dT%H:%M:%S")
                self.lbl_updated.setText("数据时间 %s" % dt.strftime("%m-%d %H:%M"))
            except Exception:
                self.lbl_updated.setText("")
        # 优先用服务端给的节奏，本地 5 分钟为准
        self._interval = REFRESH_SECONDS
        self._btn_reset()
        self._countdown(force=0)

    def _on_error(self, msg: str):
        self.lbl_sub.setText("⚠ 查询失败：%s" % msg)
        for c in self.cards.values():
            c._empty("等待重试…")
        self._btn_reset()

    def _btn_reset(self):
        self.btn_refresh.setEnabled(True)
        self.btn_refresh.setText("刷新")

    # ---------------- 倒计时 ----------------
    def _on_tick(self):
        self._countdown()

    def _countdown(self, force: int = 0):
        interval = getattr(self, "_interval", REFRESH_SECONDS)
        elapsed = force or int(time.time() - self._last_ok)
        left = interval - elapsed
        if left <= 0:
            self.lbl_countdown.setText("正在刷新…")
            self.refresh()
            self._last_ok = time.time()   # 防抖，避免失败时疯狂重试
            return
        m, s = divmod(left, 60)
        self.lbl_countdown.setText("⏱ %d:%02d 后自动刷新" % (m, s))
