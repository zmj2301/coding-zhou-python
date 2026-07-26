"""
翻页钟倒计时组件 - 基于 QWebEngineView 嵌入
提供机场翻牌板风格的倒计时显示
"""

import os
from typing import Optional, Callable
from PySide6.QtCore import Qt, Signal, Slot, QObject, QUrl
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel


class FlipClockBridge(QObject):
    """Python <-> JS 通信桥接"""

    tick = Signal(int, int)       # 剩余秒数, 总秒数
    finished = Signal()           # 倒计时结束

    def __init__(self, parent=None):
        super().__init__(parent)

    @Slot(int)
    def on_tick(self, remaining: int, total: int) -> None:
        self.tick.emit(remaining, total)

    @Slot()
    def on_finished(self) -> None:
        self.finished.emit()


class FlipClockWidget(QWidget):
    """翻页钟倒计时窗口"""

    time_updated = Signal(int, int)   # remaining, total
    countdown_finished = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(500, 220)

        # 外部回调：点击翻页钟关闭按钮时
        self._close_callback: Optional[Callable] = None

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 顶部栏：状态标签 + 关闭按钮
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(16, 8, 16, 0)

        self._status_label = QLabel("专注中")
        self._status_label.setStyleSheet(
            "color:rgba(255,255,255,0.5);font-size:12px;font-family:'Segoe UI','Microsoft YaHei',sans-serif;"
        )
        top_bar.addWidget(self._status_label)
        top_bar.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background:rgba(232,17,35,0.6);color:white;
                border:none;border-radius:14px;font-size:12px;font-weight:bold;
            }
            QPushButton:hover { background:rgba(232,17,35,0.9); }
        """)
        close_btn.clicked.connect(self._on_close_clicked)
        top_bar.addWidget(close_btn)

        main_layout.addLayout(top_bar)

        # WebEngine
        self._web = QWebEngineView(self)
        self._web.setStyleSheet("background:transparent;border:none;")
        main_layout.addWidget(self._web)

        # JS-Python 桥接
        self._bridge = FlipClockBridge(self)
        self._bridge.tick.connect(self._on_tick)
        self._bridge.finished.connect(self._on_finished)

        self._channel = QWebChannel()
        self._channel.registerObject("pyBridge", self._bridge)
        self._web.page().setWebChannel(self._channel)

        # 加载 HTML
        html_path = os.path.join(os.path.dirname(__file__), "flip_clock.html")
        self._web.load(QUrl.fromLocalFile(html_path))

    def _inject_channel_js(self) -> None:
        """注入 QWebChannel 初始化脚本"""
        inject = """
        <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
        <script>
        if (!window._bridgeReady) {
            window._bridgeReady = true;
            new QWebChannel(qt.webChannelTransport, function(ch) {
                window.pyBridge = ch.objects.pyBridge;
            });
        }
        </script>
        """
        script = f"document.head.insertAdjacentHTML('beforeend', `{inject}`);"
        self._web.page().runJavaScript(script, lambda result: None)

    def _on_tick(self, remaining: int, total: int) -> None:
        self.time_updated.emit(remaining, total)

    def _on_finished(self) -> None:
        self.countdown_finished.emit()

    def _on_close_clicked(self) -> None:
        """关闭翻页钟"""
        if self._close_callback:
            self._close_callback()

    @property
    def close_btn_clicked(self):
        return self._close_callback

    @close_btn_clicked.setter
    def close_btn_clicked(self, callback: Optional[Callable]) -> None:
        self._close_callback = callback

    # ========== 外部 API ==========

    def set_status(self, text: str) -> None:
        """设置状态标签文字"""
        self._status_label.setText(text)

    def set_duration(self, minutes: int) -> None:
        """设置倒计时时长（分钟）"""
        self._web.page().runJavaScript(f"setDuration({minutes})", lambda result: None)

    def start(self) -> None:
        """开始倒计时"""
        self._inject_channel_js()
        self._web.page().runJavaScript("startCountdown()", lambda result: None)

    def pause(self) -> None:
        """暂停"""
        self._web.page().runJavaScript("pauseCountdown()", lambda result: None)

    def stop(self) -> None:
        """停止并重置"""
        self._web.page().runJavaScript("stopCountdown()", lambda result: None)

    def set_remaining(self, seconds: int) -> None:
        """直接设置剩余秒数"""
        self._web.page().runJavaScript(f"setRemaining({seconds})", lambda result: None)