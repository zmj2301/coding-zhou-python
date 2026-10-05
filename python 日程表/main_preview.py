# -*- coding: utf-8 -*-
"""主窗口样式预览 —— 独立运行，不依赖项目代码。

python main_preview.py
"""
import sys
from PySide2.QtWidgets import (QApplication, QWidget, QLabel, QTextEdit,
                                 QHBoxLayout, QVBoxLayout, QSizeGrip)
from PySide2.QtCore import Qt, QSize
from PySide2.QtGui import QFont, QPixmap, QIcon

# ── 设计令牌（主窗口）──────────────────────────────────
# 这套配色和设置窗口的 _SET_COLOR 同源，保证整个应用视觉统一
C = {
    'window_bg':    '#eef1f6',   # 预览窗口背景
    'top_card_bg':  'rgba(255,255,255,0.78)',  # 顶部卡（图标+倒计时）
    'main_card_bg': 'rgba(255,255,255,0.78)',  # 事件白卡
    'border':       'rgba(0,0,0,0.06)',        # 细边框
    'accent':       '#4f6ef7',                 # 主色（蓝紫）
    'accent_soft':  '#eef0ff',                 # 主色淡
    'countdown_num': '#1f2937',                # 倒计时大数字（深灰黑）
    'countdown_lbl': '#4f6ef7',                # "倒计时"标签（主色）
    'event_title':   '#1f2937',                # 事件列表标题
    'event_text':    '#374151',                # 事件正文
    'event_dim':     '#8a94a6',                # 次要文字（时间/日期）
    'today_dot':     '#4f6ef7',                # 今天的圆点前导
    'grip':          'rgba(79,110,247,0.4)',   # 右下角 grip
}

S = {
    'radius':     12,   # 统一圆角（px）
    'margin':     16,   # 窗口外边距
    'gap':        8,    # 顶部卡 → 事件卡
    'card_pad':   14,   # 卡内边距
    'icon_size':  96,   # 图标边长
}


def build_style_sheet():
    """返回主窗口的 QSS 字符串。"""
    return """
    /* ── 顶部卡（图标 + 倒计时）── */
    #topCard {
        background-color: %s;
        border-radius: %dpx;
        border: 1px solid %s;
    }
    #imageLabel {
        background: transparent;
        border-radius: 10px;
    }
    /* 倒计时大数字 */
    #countdownNum {
        background: transparent;
        color: %s;
        font-size: 26px;
        font-weight: bold;
        font-family: "Microsoft YaHei";
        letter-spacing: 1px;
    }
    /* 倒计时上面的小标签 */
    #countdownLabel {
        background: transparent;
        color: %s;
        font-size: 11px;
        font-weight: bold;
        font-family: "Microsoft YaHei";
        letter-spacing: 0.5px;
    }
    /* ── 事件白卡 ── */
    #mainCard {
        background-color: %s;
        border-radius: %dpx;
        border: 1px solid %s;
    }
    QTextEdit#contentEdit {
        background-color: transparent;
        border: none;
        color: %s;
        font-size: 13px;
        font-family: "Microsoft YaHei";
    }
    /* viewport 也透明，否则会盖一层白 */
    QTextEdit#contentEdit::viewport {
        background-color: transparent;
        border: none;
    }
    /* 滚动条：细 + 主色 */
    QScrollBar:vertical {
        background: transparent;
        width: 6px;
        margin: 6px 2px 6px 0;
    }
    QScrollBar::handle:vertical {
        background: rgba(79,110,247,0.35);
        border-radius: 3px;
        min-height: 18px;
    }
    QScrollBar::handle:vertical:hover {
        background: rgba(79,110,247,0.6);
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
    }
    """ % (
        C['top_card_bg'], S['radius'], C['border'],
        C['countdown_num'], C['countdown_lbl'],
        C['main_card_bg'], S['radius'], C['border'],
        C['event_text'],
    )


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(build_style_sheet())

    # 预览窗口本身（模拟桌面背景 —— 深蓝紫渐变壁纸感）
    desktop_bg = QWidget()
    desktop_bg.setWindowTitle("主窗口样式预览")
    desktop_bg.setStyleSheet(
        "QWidget#desktop { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, "
        "stop:0 #2d3748, stop:0.5 #4a5568, stop:1 #1a202c); }")
    desktop_bg.setObjectName("desktop")
    desktop_bg.resize(900, 700)

    # ── 模拟主窗口（无边框 + 半透明）────
    window = QWidget(desktop_bg)
    window.setAttribute(Qt.WA_TranslucentBackground, True)
    window.setFixedSize(380, 520)
    window.move(260, 90)
    window_layout = QVBoxLayout(window)
    window_layout.setContentsMargins(S['margin'], S['margin'],
                                     S['margin'], S['margin'])
    window_layout.setSpacing(S['gap'])

    # ── 顶部卡：图标 + 倒计时 ──
    top_card = QWidget(window)
    top_card.setObjectName("topCard")
    top_layout = QHBoxLayout(top_card)
    top_layout.setContentsMargins(S['card_pad'], S['card_pad'],
                                  S['card_pad'], S['card_pad'])
    top_layout.setSpacing(12)

    # 图标（用一个占位 pixmap，实际会换成用户的日历图）
    icon_label = QLabel(top_card)
    icon_label.setObjectName("imageLabel")
    icon_label.setFixedSize(S['icon_size'], S['icon_size'])
    # 画一个占位图
    pm = QPixmap(S['icon_size'], S['icon_size'])
    pm.fill(Qt.transparent)
    from PySide2.QtGui import QPainter, QColor, QBrush, QPen
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(QColor(79, 110, 247, 200)))
    p.drawRoundedRect(0, 0, S['icon_size'], S['icon_size'], 12, 12)
    # 里面画个白色日历格
    p.setBrush(QBrush(QColor(255, 255, 255, 230)))
    p.drawRoundedRect(12, 20, S['icon_size'] - 24, S['icon_size'] - 32, 6, 6)
    p.setPen(QPen(QColor(79, 110, 247)))
    p.setFont(QFont('Microsoft YaHei', 18, QFont.Bold))
    p.drawText(pm.rect(), Qt.AlignCenter, "4")
    p.end()
    icon_label.setPixmap(pm)

    # 倒计时区域（垂直布局：小标签在上，大数字在下）
    countdown_col = QWidget(top_card)
    countdown_col.setStyleSheet("background: transparent;")
    col_layout = QVBoxLayout(countdown_col)
    col_layout.setContentsMargins(0, 0, 0, 0)
    col_layout.setSpacing(0)

    lbl_up = QLabel("距离考试还有", countdown_col)
    lbl_up.setObjectName("countdownLabel")
    lbl_up.setAlignment(Qt.AlignLeft | Qt.AlignBottom)

    num = QLabel("25 天", countdown_col)
    num.setObjectName("countdownNum")
    num.setAlignment(Qt.AlignLeft | Qt.AlignTop)

    col_layout.addWidget(lbl_up, 1)
    col_layout.addWidget(num, 2)

    top_layout.addWidget(icon_label, 0, Qt.AlignLeft | Qt.AlignVCenter)
    top_layout.addWidget(countdown_col, 1)

    window_layout.addWidget(top_card)

    # ── 事件白卡 ──
    main_card = QWidget(window)
    main_card.setObjectName("mainCard")
    main_layout = QVBoxLayout(main_card)
    main_layout.setContentsMargins(S['card_pad'], S['card_pad'],
                                   S['card_pad'], S['card_pad'])
    main_layout.setSpacing(6)

    # 卡内标题（小字）
    title = QLabel("📅 今日事件 · 2026/10/04 周六", main_card)
    title.setStyleSheet(
        "background: transparent; color: %s; font-size: 12px; "
        "font-weight: bold; font-family: 'Microsoft YaHei';" % C['event_title'])

    edit = QTextEdit(main_card)
    edit.setObjectName("contentEdit")
    edit.setReadOnly(True)
    events_html = (
        '<div style="line-height:1.7;">'
        '<div style="color:%s; font-size:12px; font-weight:bold; margin-bottom:6px;">'
        '⏰ 今天 · 10/04</div>'
        '<div style="padding:4px 0;"><span style="color:%s;">●</span>'
        '<span>09:00&nbsp;&nbsp;产品评审会议</span></div>'
        '<div style="padding:4px 0;"><span style="color:%s;">●</span>'
        '<span>14:30&nbsp;&nbsp;客户对接</span></div>'
        '<div style="padding:4px 0;"><span style="color:%s;">●</span>'
        '<span>20:00&nbsp;&nbsp;备考：线性代数</span></div>'
        '<div style="color:%s; font-size:12px; font-weight:bold; margin-top:12px; margin-bottom:6px;">'
        '📆 明天 · 10/05</div>'
        '<div style="padding:4px 0;"><span style="color:%s;">●</span>'
        '<span>10:00&nbsp;&nbsp;健身</span></div>'
        '<div style="padding:4px 0;"><span style="color:%s;">●</span>'
        '<span>15:00&nbsp;&nbsp;整理项目文档</span></div>'
        '<div style="color:%s; font-size:12px; font-weight:bold; margin-top:12px; margin-bottom:6px;">'
        '🌙 下周</div>'
        '<div style="padding:4px 0;"><span style="color:%s;">●</span>'
        '<span>10/07&nbsp;&nbsp;Release 包</span></div>'
        '<div style="padding:4px 0;"><span style="color:%s;">●</span>'
        '<span>10/09&nbsp;&nbsp;部门周会</span></div>'
        '</div>'
    ) % (
        C['event_title'],
        C['today_dot'],
        C['today_dot'],
        C['today_dot'],
        C['event_title'],
        C['accent'],
        C['accent'],
        C['event_title'],
        C['event_dim'],
        C['event_dim'],
    )
    edit.setHtml(events_html)
    edit.setMinimumHeight(340)

    main_layout.addWidget(title)
    main_layout.addWidget(edit)
    window_layout.addWidget(main_card, 1)

    # 右下 grip
    grip = QSizeGrip(window)
    grip.setFixedSize(18, 18)
    grip.setStyleSheet(
        "QSizeGrip { background: %s; border-radius: 4px; }" % C['grip'])
    grip.raise_()

    # 放到底部
    window_resize = lambda: grip.move(window.width() - 22, window.height() - 22)
    window.resizeEvent = lambda e: window_resize()
    window_resize()

    desktop_bg.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
