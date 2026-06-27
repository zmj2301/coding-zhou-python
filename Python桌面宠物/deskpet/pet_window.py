import logging
import webbrowser
import os
from typing import Optional, Callable, Any
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, Property
from PySide6.QtGui import QCursor, QPixmap, QAction, QPainter, QColor, QBrush, QPen, QFont, QRadialGradient
from PySide6.QtWidgets import QLabel, QMenu, QWidget, QApplication, QInputDialog, QMessageBox

from . import auto_start
from .size_settings_dialog import SizeSettingsDialog


class AnimatedLabel(QLabel):
    """带动画效果的标签"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._scale: float = 1.0
        self._hover_scale: float = 1.05
        self._breathe_timer: QTimer = QTimer(self)
        self._breathe_timer.timeout.connect(self._breathe)
        self._breathe_phase: int = 0
        self._breathe_timer.start(50)
        
    def get_scale(self) -> float:
        return self._scale
    
    def set_scale(self, scale: float) -> None:
        self._scale = scale
        self.update()
    
    scale = Property(float, get_scale, set_scale)
    
    def _breathe(self) -> None:
        """轻微的呼吸动画"""
        self._breathe_phase = (self._breathe_phase + 1) % 100
        breathe_scale = 1.0 + 0.01 * (self._breathe_phase / 100.0)
        if self._breathe_phase > 50:
            breathe_scale = 1.0 + 0.01 * (1 - self._breathe_phase / 100.0)
        self._scale = breathe_scale
        self.update()
    
    def paintEvent(self, event: Any) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        if self.pixmap() and not self.pixmap().isNull():
            w = int(self.width() * self._scale)
            h = int(self.height() * self._scale)
            x = (self.width() - w) // 2
            y = (self.height() - h) // 2
            painter.drawPixmap(x, y, w, h, self.pixmap())
        else:
            super().paintEvent(event)


class PetWindow(QWidget):
    """桌面宠物窗口"""
    
    def __init__(self, config: Any, sync_manager: Any = None, countdown_widget: Any = None):
        """
        初始化桌面宠物窗口
        
        Args:
            config: 配置对象
            sync_manager: 位置同步管理器
            countdown_widget: 倒计时组件
        """
        super().__init__()
        self._config = config
        self._sync_manager = sync_manager
        self._countdown_widget = countdown_widget
        self._drag_pos: Optional[QPoint] = None
        self._hovering: bool = False
        self._rotation_angle: float = 0
        
        self._init_window()
        self.label = AnimatedLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setScaledContents(True)
        self.label.setGeometry(0, 0, self._config.pet_size, self._config.pet_size)
        
        self._load_icon()
        
        self._float_timer: QTimer = QTimer(self)
        self._float_timer.timeout.connect(self._float_animation)
        self._float_offset: float = 0
        self._float_timer.start(30)
        
        self._shine_timer: QTimer = QTimer(self)
        self._shine_timer.timeout.connect(self.update)
        self._shine_phase: float = 0
        self._shine_timer.start(50)

    def _init_window(self) -> None:
        """初始化窗口设置"""
        size = self._config.pet_size
        bg_color = self._config.pet_bg_color
        
        self.setWindowTitle('DesktopPet')
        flags = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        self.setWindowFlags(flags)
        if self._config.pet_transparent:
            self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(size, size)
        self.setCursor(QCursor(Qt.OpenHandCursor))
        
        self._create_hover_animation()

    def _create_hover_animation(self) -> None:
        """创建悬停动画"""
        self._hover_animation = QPropertyAnimation(self, b"rotation_angle")
        self._hover_animation.setDuration(200)
        self._hover_animation.setEasingCurve(QEasingCurve.OutBack)

    def get_rotation_angle(self) -> float:
        return self._rotation_angle
    
    def set_rotation_angle(self, angle: float) -> None:
        self._rotation_angle = angle
        self.update()
    
    rotation_angle = Property(float, get_rotation_angle, set_rotation_angle)

    def _load_icon(self) -> None:
        """加载宠物图标"""
        try:
            pixmap = QPixmap(self._config.pet_icon_path)
            if not pixmap.isNull():
                self.label.setPixmap(pixmap)
            else:
                self.label.setText('🐾')
                self.label.setStyleSheet("font-size: 80px; color: #FFD700;")
        except Exception:
            self.label.setText('🐾')
            self.label.setStyleSheet("font-size: 80px; color: #FFD700;")

    def reload_icon(self) -> None:
        """重新加载图标"""
        self._load_icon()

    def _float_animation(self) -> None:
        """浮动动画"""
        self._float_offset += 0.05
        self.update()

    def mousePressEvent(self, event: Any) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.setCursor(QCursor(Qt.ClosedHandCursor))
            
            self._shake_animation()

    def _shake_animation(self) -> None:
        """点击时的轻微晃动效果"""
        self._shake_timer = QTimer(self)
        self._shake_count = 0
        self._shake_timer.timeout.connect(self._do_shake)
        self._shake_timer.start(30)
    
    def _do_shake(self) -> None:
        if self._shake_count < 6:
            offset = 3 if self._shake_count % 2 == 0 else -3
            self.move(self.x() + offset, self.y())
            self._shake_count += 1
        else:
            self._shake_timer.stop()

    def mouseMoveEvent(self, event: Any) -> None:
        if self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            if self._sync_manager:
                self._sync_manager.sync_from_a()

    def mouseReleaseEvent(self, event: Any) -> None:
        self._drag_pos = None
        self.setCursor(QCursor(Qt.OpenHandCursor))

    def enterEvent(self, event: Any) -> None:
        """鼠标进入窗口时的动画"""
        self._hovering = True
        self._hover_animation.setStartValue(self._rotation_angle)
        self._hover_animation.setEndValue(5)
        self._hover_animation.start()

    def leaveEvent(self, event: Any) -> None:
        """鼠标离开窗口时的动画"""
        self._hovering = False
        self._hover_animation.setStartValue(self._rotation_angle)
        self._hover_animation.setEndValue(0)
        self._hover_animation.start()

    def paintEvent(self, event: Any) -> None:
        """绘制带光晕背景的窗口"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self._config.pet_transparent:
            self._paint_transparent_background(painter)
        else:
            self._paint_solid_background(painter)

    def _paint_solid_background(self, painter: QPainter) -> None:
        """绘制纯色背景"""
        center_x = self.width() // 2
        center_y = self.height() // 2 + int(5 * (self._float_offset % 1.0))
        
        gradient = QRadialGradient(center_x, center_y, self.width() // 2)
        gradient.setColorAt(0, QColor(255, 255, 255, 255))
        gradient.setColorAt(0.7, QColor(240, 240, 255, 240))
        gradient.setColorAt(1, QColor(200, 200, 220, 200))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(5, 5, self.width() - 10, self.height() - 10)

    def _paint_transparent_background(self, painter: QPainter) -> None:
        """绘制透明背景（带光晕）"""
        self._shine_phase = (self._shine_phase + 1) % 100
        shine_opacity = 0.3 + 0.2 * (self._shine_phase / 100.0)
        if self._shine_phase > 50:
            shine_opacity = 0.5 - 0.2 * ((self._shine_phase - 50) / 50.0)
        
        center_x = self.width() // 2
        center_y = self.height() // 2 + int(5 * (self._float_offset % 1.0))
        
        gradient = QRadialGradient(center_x, center_y, self.width() // 2)
        gradient.setColorAt(0, QColor(255, 215, 0, int(shine_opacity * 255)))
        gradient.setColorAt(0.6, QColor(255, 165, 0, int(shine_opacity * 128)))
        gradient.setColorAt(1, QColor(255, 140, 0, 0))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, self.width(), self.height())

    def contextMenuEvent(self, event: Any) -> None:
        """右键菜单"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d30;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 24px;
                border-radius: 4px;
                color: #ffffff;
            }
            QMenu::item:selected {
                background-color: #0078d4;
            }
            QMenu::separator {
                height: 1px;
                background: #404040;
                margin: 4px 8px;
            }
            QMenu::item:checked {
                background-color: #0078d4;
            }
        """)

        # 自启动选项
        is_enabled = auto_start.is_auto_start_enabled()
        auto_start_action = QAction('🚀 开机自启动', self)
        auto_start_action.setCheckable(True)
        auto_start_action.setChecked(is_enabled)
        auto_start_action.triggered.connect(self._toggle_auto_start)
        menu.addAction(auto_start_action)

        menu.addSeparator()

        cctv_menu = QMenu('📺 CCTV频道', self)
        cctv_menu.setStyleSheet(menu.styleSheet())
        for channel in self._config.cctv_channels:
            action = QAction(channel["name"], self)
            action.triggered.connect(self._make_url_handler(channel["url"]))
            cctv_menu.addAction(action)
        menu.addMenu(cctv_menu)

        ai_menu = QMenu('🤖 AI模型', self)
        ai_menu.setStyleSheet(menu.styleSheet())
        for model in self._config.ai_models:
            action = QAction(model["name"], self)
            action.triggered.connect(self._make_url_handler(model["url"]))
            ai_menu.addAction(action)
        menu.addMenu(ai_menu)

        custom_menu = QMenu('🔗 自定义链接', self)
        custom_menu.setStyleSheet(menu.styleSheet())
        if self._config.custom_links:
            for link in self._config.custom_links:
                action = QAction(link["name"], self)
                action.triggered.connect(self._make_url_handler(link["url"]))
                custom_menu.addAction(action)
        else:
            action = QAction('暂无自定义链接', self)
            action.setEnabled(False)
            custom_menu.addAction(action)
        menu.addMenu(custom_menu)

        text_menu = QMenu('💬 显示文本', self)
        text_menu.setStyleSheet(menu.styleSheet())
        if self._config.history_texts:
            for text in self._config.history_texts[:10]:
                action = QAction(text[:30] + ('...' if len(text) > 30 else ''), self)
                action.triggered.connect(self._make_text_handler(text))
                text_menu.addAction(action)
            text_menu.addSeparator()

        input_action = QAction('✏️ 输入新文本...', self)
        input_action.triggered.connect(self._show_text)
        text_menu.addAction(input_action)
        menu.addMenu(text_menu)

        menu.addSeparator()
        show_countdown_action = QAction('⏱️ 显示倒计时', self)
        show_countdown_action.triggered.connect(self._show_countdown)
        menu.addAction(show_countdown_action)

        restore_action = QAction('🖼️ 恢复图片', self)
        restore_action.triggered.connect(self._restore_icon)
        menu.addAction(restore_action)
        
        resize_action = QAction('📏 调整尺寸', self)
        resize_action.triggered.connect(self._show_size_settings)
        menu.addAction(resize_action)

        menu.addSeparator()
        open_config_action = QAction('⚙️ 打开设置', self)
        open_config_action.triggered.connect(self._open_config)
        menu.addAction(open_config_action)

        quit_action = QAction('❌ 退出', self)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)

        menu.exec(event.globalPos())

    def _toggle_auto_start(self) -> None:
        """切换开机自启动状态"""
        try:
            new_state = auto_start.toggle_auto_start()
            if new_state:
                QMessageBox.information(
                    self,
                    "设置成功",
                    "已启用开机自启动！下次开机时将自动运行桌面宠物。"
                )
            else:
                QMessageBox.information(
                    self,
                    "设置成功",
                    "已禁用开机自启动。"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "设置失败",
                f"修改开机自启动设置失败：\n{str(e)}"
            )

    def _show_text(self) -> None:
        """显示输入文本对话框"""
        text, ok = QInputDialog.getText(self, '输入文本', '请输入要显示的文本内容：')
        if ok and text:
            self.label.setText(text)
            self._config.add_history_text(text)
            self._config.save()

    def _restore_icon(self) -> None:
        """恢复宠物图标"""
        self._load_icon()
    
    def _show_size_settings(self) -> None:
        """显示尺寸设置对话框"""
        dialog = SizeSettingsDialog(self._config.pet_size, self)
        dialog.size_changed.connect(self._on_size_changed)
        dialog.exec()
    
    def _on_size_changed(self, width: int, height: int) -> None:
        """
        尺寸变化处理
        
        Args:
            width: 新的宽度
            height: 新的高度
        """
        new_size = max(width, height)
        self._config.pet_size = new_size
        self._config.save()
        self._update_window_size(new_size)
    
    def _update_window_size(self, size: int) -> None:
        """
        更新窗口尺寸
        
        Args:
            size: 新的窗口尺寸
        """
        self.setFixedSize(size, size)
        self.label.setGeometry(0, 0, size, size)
        self.update()

    def _show_countdown(self) -> None:
        """显示倒计时窗口"""
        if self._countdown_widget:
            self._countdown_widget.show()
            self._countdown_widget.raise_()
            self._countdown_widget.activateWindow()

    def _make_url_handler(self, url: str) -> Callable[[], None]:
        """创建URL处理函数"""
        return lambda: self._open_url(url)

    def _make_text_handler(self, text: str) -> Callable[[], None]:
        """创建文本处理函数"""
        return lambda: self.label.setText(text)

    def _open_url(self, url: str) -> None:
        """打开URL"""
        logging.info(f'打开 URL-{url}')
        webbrowser.open(url)

    def _open_config(self) -> None:
        """打开配置文件"""
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        webbrowser.open(config_path)

    def position_to_bottom_right(self) -> None:
        """定位到屏幕右下角"""
        screen_geo = QApplication.primaryScreen().geometry()
        x = screen_geo.width() - self.width() - self._config.pet_x_offset
        y = screen_geo.height() - self.height() - self._config.pet_y_offset
        self.move(x, y)
