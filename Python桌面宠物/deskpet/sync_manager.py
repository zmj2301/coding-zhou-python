from typing import Optional
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QPoint


class PositionSyncManager:
    """位置同步管理器，用于同步多个窗口的位置"""
    
    def __init__(self, window_a: QWidget, window_b: QWidget):
        """
        初始化位置同步管理器
        
        Args:
            window_a: 第一个窗口（通常是宠物窗口）
            window_b: 第二个窗口（通常是倒计时窗口）
        """
        self._window_a: QWidget = window_a
        self._window_b: QWidget = window_b
        self._offset: Optional[QPoint] = None
        self._syncing: bool = False

    def init_offset(self) -> None:
        """初始化两个窗口之间的偏移量"""
        self._offset = self._window_b.pos() - self._window_a.pos()

    def sync_from_a(self) -> None:
        """从窗口A同步位置到窗口B"""
        if self._syncing or self._offset is None:
            return
        self._syncing = True
        new_pos = self._window_a.pos() + self._offset
        if self._within_screen(new_pos):
            self._window_b.move(new_pos)
        self._syncing = False

    def sync_from_b(self) -> None:
        """从窗口B同步位置到窗口A"""
        if self._syncing or self._offset is None:
            return
        self._syncing = True
        new_pos = self._window_b.pos() - self._offset
        if self._within_screen(new_pos):
            self._window_a.move(new_pos)
        self._syncing = False

    def _within_screen(self, pos: QPoint) -> bool:
        """
        检查位置是否在屏幕范围内
        
        Args:
            pos: 要检查的位置
            
        Returns:
            是否在屏幕范围内
        """
        for screen in QApplication.screens():
            if screen.geometry().contains(pos):
                return True
        return False
