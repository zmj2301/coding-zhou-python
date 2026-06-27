from typing import Optional, Any
from PySide6.QtCore import Qt, QRect, QPoint, Signal, QTimer, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QMouseEvent, QPainter, QColor, QBrush, QPen, QFont, QCursor, QGuiApplication, QLinearGradient, QRadialGradient
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton


_RESIZE_MARGIN: int = 8


class CountdownWidget(QWidget):
    """倒计时组件 - 美化版"""
    
    settings_clicked = Signal()
    start_clicked = Signal()
    pause_clicked = Signal()
    stop_clicked = Signal()
    position_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化倒计时组件
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self._drag_pos: Optional[QPoint] = None
        self._resize_edge: int = 0
        self._remaining: int = 0
        self._is_work: bool = True
        self._is_running: bool = False
        self._state_text: str = "待机"
        self._pulse_phase: float = 0
        self._glow_phase: float = 0
        self._bg_opacity: float = 220
        
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(180, 100)
        self.resize(300, 200)
        
        self._init_ui()
        self._position_bottom_right()
        
        self._pulse_timer: QTimer = QTimer(self)
        self._pulse_timer.timeout.connect(self._pulse_animation)
        self._pulse_timer.start(50)
        
        self._glow_timer: QTimer = QTimer(self)
        self._glow_timer.timeout.connect(self._glow_animation)
        self._glow_timer.start(40)

    def get_bg_opacity(self) -> float:
        return self._bg_opacity
    
    def set_bg_opacity(self, opacity: float) -> None:
        self._bg_opacity = opacity
        self.update()
    
    bg_opacity = Property(float, get_bg_opacity, set_bg_opacity)

    def _position_bottom_right(self) -> None:
        """定位到屏幕右下角"""
        screen = QGuiApplication.primaryScreen().geometry()
        size = self.frameGeometry()
        pos_x = screen.right() - self.width() - 20
        pos_y = screen.bottom() - self.height() - 20
        self.move(pos_x, pos_y)

    def _init_ui(self) -> None:
        """初始化UI组件"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 14)
        layout.setSpacing(8)

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)

        self._status_label = QLabel(self._state_text)
        self._status_label.setStyleSheet("""
            color: rgba(255,255,255,200); 
            font-size: 14px; 
            font-weight: 500;
        """)
        top_bar.addWidget(self._status_label)

        top_bar.addStretch()

        self._settings_btn = QPushButton('⚙️')
        self._settings_btn.setFixedSize(32, 32)
        self._settings_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(80, 80, 90, 160);
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(100, 100, 110, 200);
            }
            QPushButton:pressed {
                background-color: rgba(60, 60, 70, 180);
            }
        """)
        self._settings_btn.setCursor(QCursor(Qt.ArrowCursor))
        self._settings_btn.clicked.connect(self.settings_clicked.emit)
        top_bar.addWidget(self._settings_btn)

        close_btn = QPushButton('✕')
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(232, 17, 35, 140);
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(232, 17, 35, 200);
            }
            QPushButton:pressed {
                background-color: rgba(180, 10, 20, 180);
            }
        """)
        close_btn.setCursor(QCursor(Qt.ArrowCursor))
        close_btn.clicked.connect(self.hide)
        top_bar.addWidget(close_btn)

        layout.addLayout(top_bar)

        self._time_label = QLabel("20:00")
        self._time_label.setAlignment(Qt.AlignCenter)
        self._time_label.setStyleSheet("""
            color: #ffffff; 
            font-size: 52px; 
            font-weight: bold;
            font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
        """)
        layout.addWidget(self._time_label)

        self._progress_label = QLabel("")
        self._progress_label.setAlignment(Qt.AlignCenter)
        self._progress_label.setStyleSheet("""
            color: rgba(255,255,255,140); 
            font-size: 12px;
            font-weight: 500;
        """)
        layout.addWidget(self._progress_label)

        control_bar = QHBoxLayout()
        control_bar.setContentsMargins(0, 0, 0, 0)
        control_bar.setSpacing(10)

        self._start_btn = QPushButton("开始")
        self._start_btn.setFixedHeight(36)
        self._start_btn.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0078d4, stop:1 #00bcf2);
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0086e5, stop:1 #00ccff);
            }
            QPushButton:pressed {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #006ac0, stop:1 #0099cc);
            }
        """)
        self._start_btn.setCursor(QCursor(Qt.ArrowCursor))
        self._start_btn.clicked.connect(self._on_start_pause_click)
        control_bar.addWidget(self._start_btn)

        self._stop_btn = QPushButton("停止")
        self._stop_btn.setFixedHeight(36)
        self._stop_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(80, 80, 90, 160);
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(100, 100, 110, 200);
            }
            QPushButton:pressed {
                background-color: rgba(60, 60, 70, 180);
            }
        """)
        self._stop_btn.setCursor(QCursor(Qt.ArrowCursor))
        self._stop_btn.clicked.connect(self.stop_clicked.emit)
        control_bar.addWidget(self._stop_btn)

        layout.addLayout(control_bar)

    def _pulse_animation(self) -> None:
        """脉冲动画"""
        self._pulse_phase = (self._pulse_phase + 1) % 100
        self.update()

    def _glow_animation(self) -> None:
        """光晕动画"""
        self._glow_phase = (self._glow_phase + 1) % 80

    def _on_start_pause_click(self) -> None:
        """开始/暂停按钮点击事件"""
        if self._is_running:
            self.pause_clicked.emit()
        else:
            self.start_clicked.emit()

    def set_running_state(self, is_running: bool) -> None:
        """
        设置运行状态
        
        Args:
            is_running: 是否正在运行
        """
        self._is_running = is_running
        if is_running:
            self._start_btn.setText("暂停")
            self._status_label.setText(self._state_text + " (运行中)")
            
            animation = QPropertyAnimation(self, b"bg_opacity")
            animation.setDuration(200)
            animation.setStartValue(self._bg_opacity)
            animation.setEndValue(240)
            animation.setEasingCurve(QEasingCurve.OutCubic)
            animation.start()
        else:
            self._start_btn.setText("开始")
            if self._state_text == "休息倒计时":
                self._status_label.setText("休息中")
            elif self._state_text == "工作倒计时":
                self._status_label.setText("工作中")
            else:
                self._status_label.setText(self._state_text)
            
            animation = QPropertyAnimation(self, b"bg_opacity")
            animation.setDuration(200)
            animation.setStartValue(self._bg_opacity)
            animation.setEndValue(220)
            animation.setEasingCurve(QEasingCurve.OutCubic)
            animation.start()

    def update_time(self, remaining_seconds: int, total_seconds: int, is_work: bool) -> None:
        """
        更新时间显示
        
        Args:
            remaining_seconds: 剩余秒数
            total_seconds: 总秒数
            is_work: 是否是工作时间
        """
        self._remaining = remaining_seconds
        self._is_work = is_work
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        self._time_label.setText(f"{minutes:02d}:{seconds:02d}")

        if remaining_seconds <= 60 and remaining_seconds > 0:
            self._time_label.setStyleSheet("""
                color: #ff4747; 
                font-size: 52px; 
                font-weight: bold;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            """)
        else:
            self._time_label.setStyleSheet("""
                color: #ffffff; 
                font-size: 52px; 
                font-weight: bold;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            """)

        if is_work:
            self._state_text = "工作倒计时"
            progress = (total_seconds - remaining_seconds) / total_seconds * 100 if total_seconds > 0 else 0
            self._progress_label.setText(f"已工作 {int(progress)}%")
        else:
            self._state_text = "休息倒计时"
            progress = (total_seconds - remaining_seconds) / total_seconds * 100 if total_seconds > 0 else 0
            self._progress_label.setText(f"已休息 {int(progress)}%")

        if self._is_running:
            self._status_label.setText(self._state_text + " (运行中)")
        else:
            self._status_label.setText(self._state_text)

        self.update()

    def set_idle_state(self) -> None:
        """设置为待机状态"""
        self._state_text = "待机"
        self._remaining = 0
        self._time_label.setText("20:00")
        self._progress_label.setText("")
        self._status_label.setText(self._state_text)
        self._start_btn.setText("开始")

    def paintEvent(self, event: Any) -> None:
        """绘制美化背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        rect = self.rect().adjusted(2, 2, -2, -2)
        
        glow_intensity = 0.3 + 0.2 * (self._glow_phase / 80.0)
        if self._glow_phase > 40:
            glow_intensity = 0.5 - 0.2 * ((self._glow_phase - 40) / 40.0)
        
        outer_glow = QRadialGradient(rect.center(), rect.width() / 2)
        outer_glow.setColorAt(0, QColor(0, 120, 212, int(glow_intensity * 100)))
        outer_glow.setColorAt(0.5, QColor(0, 120, 212, int(glow_intensity * 50)))
        outer_glow.setColorAt(1, QColor(0, 120, 212, 0))
        painter.setBrush(QBrush(outer_glow))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())
        
        bg_gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        if self._is_work:
            bg_gradient.setColorAt(0, QColor(35, 35, 45, int(self._bg_opacity)))
            bg_gradient.setColorAt(1, QColor(20, 20, 30, int(self._bg_opacity)))
        else:
            bg_gradient.setColorAt(0, QColor(45, 30, 50, int(self._bg_opacity)))
            bg_gradient.setColorAt(1, QColor(25, 15, 30, int(self._bg_opacity)))
        
        painter.setBrush(QBrush(bg_gradient))
        painter.setPen(QPen(QColor(100, 100, 130, 150), 2))
        painter.drawRoundedRect(rect, 20, 20)
        
        if self._is_running:
            border_glow = 0.5 + 0.5 * (self._pulse_phase / 100.0)
            if self._pulse_phase > 50:
                border_glow = 1.0 - 0.5 * ((self._pulse_phase - 50) / 50.0)
            
            glow_color = QColor(0, 188, 242, int(border_glow * 200)) if self._is_work else QColor(180, 100, 220, int(border_glow * 200))
            painter.setPen(QPen(glow_color, 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 20, 20)

    def _get_resize_edge(self, pos: QPoint) -> int:
        """
        获取调整大小的边缘（仅顶部边缘可缩放）
        
        Args:
            pos: 鼠标位置
            
        Returns:
            边缘标识
        """
        edge = 0
        r = self.rect()
        # 仅允许从顶部边缘缩放
        if pos.y() < _RESIZE_MARGIN:
            edge |= Qt.TopEdge
        return edge

    def _update_cursor(self, edge: int) -> None:
        """
        更新鼠标光标
        
        Args:
            edge: 边缘标识
        """
        if edge == Qt.TopEdge:
            self.setCursor(QCursor(Qt.SizeVerCursor))
        else:
            self.setCursor(QCursor(Qt.OpenHandCursor))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            edge = self._get_resize_edge(event.position().toPoint())
            if edge:
                self._resize_edge = edge
                self._drag_pos = event.position().toPoint()
                self.setCursor(QCursor(Qt.ClosedHandCursor))
            else:
                self._resize_edge = 0
                self._drag_pos = event.position().toPoint()
                self.setCursor(QCursor(Qt.ClosedHandCursor))

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_pos is None:
            edge = self._get_resize_edge(event.position().toPoint())
            self._update_cursor(edge)
            return

        delta = event.position().toPoint() - self._drag_pos
        pos = self.pos()

        if self._resize_edge:
            new_rect = QRect(pos, self.size())
            if self._resize_edge & Qt.LeftEdge:
                new_rect.setLeft(new_rect.left() + delta.x())
            if self._resize_edge & Qt.RightEdge:
                new_rect.setRight(new_rect.right() + delta.x())
            if self._resize_edge & Qt.TopEdge:
                new_rect.setTop(new_rect.top() + delta.y())
            if self._resize_edge & Qt.BottomEdge:
                new_rect.setBottom(new_rect.bottom() + delta.y())

            if new_rect.width() >= self.minimumWidth() and new_rect.height() >= self.minimumHeight():
                self.setGeometry(new_rect)
                self._drag_pos = event.position().toPoint()
        else:
            self.move(pos + delta)
            self.position_changed.emit()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_pos = None
        self._resize_edge = 0
        self.setCursor(QCursor(Qt.OpenHandCursor))

    def closeEvent(self, event: Any) -> None:
        self.hide()
        event.ignore()
