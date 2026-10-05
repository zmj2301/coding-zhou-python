# -*- coding: utf-8 -*-
"""验证「事件显示」四项修改（用户第二批语音反馈）：

  [1] 未来事件不再截断：全部列出，没有「还有 N 个更多事件」
  [2] 日期不由程序添加：未来事件行只有「• 事件文字（X天后）」
  [3] 白框自动加高：内容变多时白框长到装下全部（不超过屏幕）；
      内容变少时回落到「事件框长度」设置值
  [4] 滚动条不被每秒刷新打扰：文字没变时滚动位置原样保留
  [5] 已过期事件区保留日期（用户确认）
"""
import os
import sys
import tempfile
import shutil
import re

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

import show_yourwindows as m

try:
    from PySide6.QtCore import QTimer, QDate
except ImportError:
    from PySide2.QtCore import QTimer, QDate

_TMP = tempfile.mkdtemp(prefix="verify_events_")
m.get_app_path = lambda: _TMP
m.get_settings_dir = lambda: _TMP

app = m.QApplication.instance() or m.QApplication(sys.argv)
w = m.MyWindow()
w.show()
app.processEvents()
for _t in w.findChildren(QTimer):
    _t.stop()
app.processEvents()

FAIL = []


def check(name, cond, extra=""):
    print("  [%s] %s%s" % ("PASS" if cond else "FAIL", name, ("  " + extra) if extra else ""))
    if not cond:
        FAIL.append(name)


today = QDate.currentDate()


def ev(days_offset, things):
    d = today.addDays(days_offset)
    return {"month": "%02d" % d.month(), "day": "%02d" % d.day(), "things": things}


print("=" * 76)
print("[1][2] 未来事件全部显示 + 日期不由程序添加")
print("=" * 76)
things_list = ["事件%02d-这是一个用来测试的待办事项" % i for i in range(1, 13)]
w.event_length = 150
w.events = [ev(i + 1, t) for i, t in enumerate(things_list)]  # 未来 1~12 天
w.update_countdown()
app.processEvents()
content = w.content_label.toPlainText()
missing = [t for t in things_list if t not in content]
print("    正文行数=%d  缺失条目=%s" % (content.count("\n•"), missing))
check("12 条未来事件全部出现在正文", not missing, str(missing[:3]))
check("没有「还有 N 个更多事件」截断语", "更多事件" not in content)
# 未来 1~12 天的日期形如 10.03，不应以「月.日 (」前缀出现在未来事件行
date_prefixed = re.findall(r"\d{1,2}\.\d{1,2}\s*[(:：]", content)
print("    带日期前缀的行:", date_prefixed)
check("未来事件行没有程序添加的日期前缀", not date_prefixed, str(date_prefixed))
check("保留了相对时间（天后）", "天后" in content)

print("=" * 76)
print("[3] 白框自动加高：= min(内容自然高度, 屏幕上限)，且不低于 event_length")
print("=" * 76)


def probe_natural():
    """复现程序内的探测文档测高：干净文档离线排版，永远准确。"""
    edit = w.content_label
    p = m.QTextDocument()
    p.setDefaultFont(edit.font())
    p.setDocumentMargin(edit.document().documentMargin())
    p.setTextWidth(max(edit.width() - 2 * edit.frameWidth(), 0))
    p.setPlainText(edit.toPlainText())
    mm = edit.contentsMargins()
    return int(p.size().height()) + mm.top() + mm.bottom() + 2


scr = m.QApplication.primaryScreen()
screen_cap = (scr.availableGeometry().height() - 60) if scr is not None else (10 ** 9)
others = w._other_widgets_height()
cap_box = max(screen_cap - others, 60)


def expect_box():
    el = int(round(float(w.event_length)))
    return min(max(probe_natural(), el), cap_box)


# offscreen 虚拟屏只有 ~600px 高，条目多时白框会被正确夹到屏幕上限（真机更高）
w.events = [ev(i + 1, t) for i, t in enumerate(things_list)]
w.update_countdown()
app.processEvents()
box12 = w.content_label.height()
print("    12 条 -> 白框=%s 期望=%s（内容高%s 被屏幕%s 夹取）"
      % (box12, expect_box(), probe_natural(), cap_box))
check("12 条：白框 = min(内容自然高度, 屏幕上限)", abs(box12 - expect_box()) <= 4, str(box12))

w.events = [ev(i + 1, t) for i, t in enumerate(things_list[:6])]
w.update_countdown()
app.processEvents()
box6 = w.content_label.height()
print("    6 条 -> 白框=%s 期望=%s" % (box6, expect_box()))
check("6 条：白框 = min(内容自然高度, 屏幕上限)", abs(box6 - expect_box()) <= 4, str(box6))

# 3 条：内容较矮，应真正装得下（滚动条余量≈0），且不低于 event_length
w.events = [ev(i + 1, t) for i, t in enumerate(things_list[:3])]
w.update_countdown()
app.processEvents()
box3 = w.content_label.height()
sb3 = w.content_label.verticalScrollBar().maximum()
print("    3 条 -> 白框=%s 期望=%s 滚动条余量=%s" % (box3, expect_box(), sb3))
check("3 条：白框 = min(内容自然高度, 屏幕上限)", abs(box3 - expect_box()) <= 4, str(box3))
check("3 条：内容全部可见（余量≈0）", sb3 <= 4, str(sb3))
check("白框不低于 event_length(150)", box3 >= 146, str(box3))

# 内容变少 -> 回落：白框 = max(event_length, 内容自然高度)
w.events = [ev(1, "只剩一条")]
w.update_countdown()
app.processEvents()
box2 = w.content_label.height()
sb2 = w.content_label.verticalScrollBar().maximum()
print("    只剩 1 条 -> 白框=%s（>=150 且装得下）" % box2)
check("内容变少后不低于 event_length", box2 >= 146, str(box2))
check("内容变少后仍装得下（余量≈0）", sb2 <= 4, str(sb2))

win_h = w.height()
check("窗口高度 = 其它控件 + 白框", abs(win_h - others - box2) <= 2,
      "%d vs %d" % (win_h, others + box2))

print("=" * 76)
print("[4] 滚动条不被每秒刷新打扰")
print("=" * 76)
# 让内容超出白框（把 event_length 调小且文字不变），手动滚到中间再跑一秒刷新
w.events = [ev(i + 1, t) for i, t in enumerate(things_list)]
w.update_countdown()
w.event_length = 120
w._fit_content_height(allow_grow=True)
app.processEvents()
sb = w.content_label.verticalScrollBar()
sb.setValue(sb.maximum() // 2)
mid = sb.value()
w.update_countdown()  # 文字未变，不应动滚动条
w.update_countdown()
app.processEvents()
print("    拖到 %s，两次每秒刷新后 = %s" % (mid, sb.value()))
check("滚动位置保持不动（不被打回）", sb.value() == mid, "%s -> %s" % (mid, sb.value()))

print("=" * 76)
print("[5] 已过期事件区保留日期（用户确认）")
print("=" * 76)
expired = ev(-3, "过期的缴费")
w.events = [ev(1, "未来的一条"), expired]
w.update_countdown()
app.processEvents()
content = w.content_label.toPlainText()
seg = content.split("已过期事件")[-1]
print("    过期区内容:", seg.strip().replace("\n", " | "))
check("过期区保留 月.日 日期", re.search(r"\d{1,2}\.\d{1,2}", seg) is not None, seg[:40])
check("过期事件文字在列", "过期的缴费" in content)

print("=" * 76)
print("[6] 今天事件 + 未来事件混合：未来行同样不加日期")
print("=" * 76)
w.events = [ev(0, "今天的事"), ev(2, "后天的事")]
w.update_countdown()
app.processEvents()
content = w.content_label.toPlainText()
print("    正文:", content.strip().replace("\n", " | "))
check("今天的行 = 纯文字", "• 今天的事" in content)
# 天数取整约定是 days+1（不满一天按一天算），所以用正则断言相对时间格式
check("未来行 = 文字（相对时间）",
      re.search(r"后天的事（\d+天后）", content) is not None,
      content.strip().replace("\n", " | "))
check("未来行无 月.日 前缀", not re.search(r"\d{1,2}\.\d{1,2}\s*[(:：]", content))

print("=" * 76)
print("汇总:", "全部通过 ✅" if not FAIL else "失败项 %s" % FAIL)
print("=" * 76)

shutil.rmtree(_TMP, ignore_errors=True)
w.close()
sys.exit(1 if FAIL else 0)
