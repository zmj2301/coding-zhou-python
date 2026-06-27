"""
宠物图片尺寸设置对话框
"""
from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, 
    QPushButton, QSlider, QFrame
)


class SizeSettingsDialog(QDialog):
    """宠物尺寸设置对话框"""
    
    # 信号：尺寸已更改 (width, height)
    size_changed = Signal(int, int)
    
    def __init__(self, current_size: int, parent: Optional['QWidget'] = None):
        """
        初始化设置对话框
        
        Args:
            current_size: 当前的窗口尺寸（正方形边长）
            parent: 父窗口
        """
        super().__init__(parent)
        self._current_size = current_size
        self._temp_size = current_size
        
        self.setWindowTitle("调整宠物尺寸")
        self.setModal(True)
        self.setMinimumSize(300, 200)
        
        self._init_ui()
        
    def _init_ui(self) -> None:
        """初始化UI组件"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # 标题
        title_label = QLabel("设置宠物窗口大小")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #333;
            padding-bottom: 8px;
        """)
        layout.addWidget(title_label)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #e0e0e0;")
        layout.addWidget(line)
        
        # 尺寸显示和输入
        size_layout = QHBoxLayout()
        size_layout.setSpacing(12)
        
        size_label = QLabel("窗口尺寸:")
        size_label.setStyleSheet("""
            font-size: 14px;
            color: #555;
            font-weight: 500;
        """)
        size_layout.addWidget(size_label)
        
        self._size_spinbox = QSpinBox()
        self._size_spinbox.setRange(80, 600)
        self._size_spinbox.setSingleStep(20)
        self._size_spinbox.setValue(self._current_size)
        self._size_spinbox.setSuffix(" px")
        self._size_spinbox.setStyleSheet("""
            QSpinBox {
                font-size: 14px;
                padding: 6px 10px;
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
            }
            QSpinBox:hover {
                border-color: #0078d4;
            }
            QSpinBox:focus {
                border-color: #0078d4;
            }
        """)
        self._size_spinbox.valueChanged.connect(self._on_spinbox_changed)
        size_layout.addWidget(self._size_spinbox)
        
        size_layout.addStretch()
        layout.addLayout(size_layout)
        
        # 滑块
        slider_label = QLabel("拖动调整:")
        slider_label.setStyleSheet("""
            font-size: 14px;
            color: #555;
            font-weight: 500;
            padding-top: 8px;
        """)
        layout.addWidget(slider_label)
        
        self._size_slider = QSlider(Qt.Horizontal)
        self._size_slider.setRange(80, 600)
        self._size_slider.setValue(self._current_size)
        self._size_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #e0e0e0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                width: 24px;
                height: 24px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0078d4, stop:1 #00bcf2);
                border-radius: 12px;
                margin: -8px 0;
            }
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0086e5, stop:1 #00ccff);
            }
        """)
        self._size_slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self._size_slider)
        
        # 预设尺寸按钮
        preset_label = QLabel("快速选择:")
        preset_label.setStyleSheet("""
            font-size: 14px;
            color: #555;
            font-weight: 500;
            padding-top: 16px;
        """)
        layout.addWidget(preset_label)
        
        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(8)
        
        preset_sizes = [
            ("小", 100),
            ("中", 200),
            ("大", 300),
            ("超大", 400)
        ]
        
        for name, size in preset_sizes:
            btn = QPushButton(name)
            btn.setMinimumHeight(36)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f5f5f5;
                    color: #333;
                    border: none;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: 500;
                    padding: 0 16px;
                }
                QPushButton:hover {
                    background-color: #e8e8e8;
                }
                QPushButton:pressed {
                    background-color: #ddd;
                }
            """)
            btn.clicked.connect(lambda checked, s=size: self._set_preset_size(s))
            preset_layout.addWidget(btn)
        
        preset_layout.addStretch()
        layout.addLayout(preset_layout)
        
        layout.addStretch()
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setMinimumHeight(38)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                color: #333;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
            }
            QPushButton:pressed {
                background-color: #ddd;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("应用")
        apply_btn.setMinimumHeight(38)
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0078d4, stop:1 #00bcf2);
                color: white;
                border: none;
                border-radius: 8px;
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
        apply_btn.clicked.connect(self._on_apply)
        button_layout.addWidget(apply_btn)
        
        layout.addLayout(button_layout)
        
    def _on_spinbox_changed(self, value: int) -> None:
        """
        SpinBox值变化时更新滑块
        
        Args:
            value: 新的尺寸值
        """
        self._temp_size = value
        # 避免循环触发
        self._size_slider.blockSignals(True)
        self._size_slider.setValue(value)
        self._size_slider.blockSignals(False)
        
    def _on_slider_changed(self, value: int) -> None:
        """
        滑块值变化时更新SpinBox
        
        Args:
            value: 新的尺寸值
        """
        self._temp_size = value
        # 避免循环触发
        self._size_spinbox.blockSignals(True)
        self._size_spinbox.setValue(value)
        self._size_spinbox.blockSignals(False)
        
    def _set_preset_size(self, size: int) -> None:
        """
        设置预设尺寸
        
        Args:
            size: 预设的尺寸值
        """
        self._temp_size = size
        self._size_spinbox.setValue(size)
        self._size_slider.setValue(size)
        
    def _on_apply(self) -> None:
        """应用设置"""
        self.size_changed.emit(self._temp_size, self._temp_size)
        self.accept()
