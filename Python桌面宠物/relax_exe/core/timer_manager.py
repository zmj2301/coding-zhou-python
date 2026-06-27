"""
计时器管理器模块
提供工作休息计时器功能
"""

from enum import Enum, auto
from typing import Optional
from PySide6.QtCore import QObject, QTimer, Signal, QElapsedTimer


class TimerState(Enum):
    """计时器状态枚举"""
    IDLE = auto()
    WORKING = auto()
    LOCKED = auto()
    BREAK_DONE = auto()


class TimerManager(QObject):
    """计时器管理器 - 管理工作和休息计时器"""
    
    state_changed = Signal(TimerState)
    time_updated = Signal(int, int, bool)
    work_finished = Signal()
    break_finished = Signal()

    def __init__(self, parent: Optional[QObject] = None):
        """
        初始化计时器管理器
        
        Args:
            parent: 父对象
        """
        super().__init__(parent)
        self._work_duration: int = 20 * 60
        self._break_duration: int = 5 * 60
        self._state: TimerState = TimerState.IDLE
        self._remaining: int = 0
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_tick)
        self._elapsed_timer = QElapsedTimer()

    @property
    def state(self) -> TimerState:
        """获取当前计时器状态"""
        return self._state

    @property
    def work_duration(self) -> int:
        """获取工作时长（秒）"""
        return self._work_duration

    @work_duration.setter
    def work_duration(self, seconds: int) -> None:
        """
        设置工作时长
        
        Args:
            seconds: 工作时长（秒）
        """
        self._work_duration = max(1, seconds)

    @property
    def break_duration(self) -> int:
        """获取休息时长（秒）"""
        return self._break_duration

    @break_duration.setter
    def break_duration(self, seconds: int) -> None:
        """
        设置休息时长
        
        Args:
            seconds: 休息时长（秒）
        """
        self._break_duration = max(1, seconds)

    @property
    def remaining(self) -> int:
        """获取剩余秒数"""
        return self._remaining

    def start_work(self) -> None:
        """开始工作计时"""
        if self._state == TimerState.IDLE:
            self._remaining = self._work_duration
            self._set_state(TimerState.WORKING)
            self._timer.start()
            self._emit_time()

    def stop(self) -> None:
        """停止计时"""
        if self._state != TimerState.IDLE:
            self._timer.stop()
            self._set_state(TimerState.IDLE)
            self._remaining = 0
            self._emit_time()

    def pause(self) -> None:
        """暂停计时"""
        if self._state == TimerState.WORKING:
            self._timer.stop()
            self._set_state(TimerState.IDLE)

    def start_break(self) -> None:
        """开始休息计时"""
        self._remaining = self._break_duration
        self._set_state(TimerState.LOCKED)
        self._timer.start()
        self._emit_time()

    def _on_tick(self) -> None:
        """计时器滴答事件 - 每秒更新"""
        if self._state == TimerState.WORKING:
            self._remaining -= 1
            self._emit_time()
            if self._remaining <= 0:
                self._timer.stop()
                self._remaining = 0
                self._emit_time()
                self.work_finished.emit()

        elif self._state == TimerState.LOCKED:
            self._remaining -= 1
            self._emit_time()
            if self._remaining <= 0:
                self._timer.stop()
                self._remaining = 0
                self._emit_time()
                self._set_state(TimerState.BREAK_DONE)
                self.break_finished.emit()

    def _set_state(self, state: TimerState) -> None:
        """
        设置计时器状态
        
        Args:
            state: 新状态
        """
        self._state = state
        self.state_changed.emit(state)

    def _emit_time(self) -> None:
        """发射时间更新信号"""
        if self._state == TimerState.WORKING:
            self.time_updated.emit(self._remaining, self._work_duration, True)
        elif self._state == TimerState.LOCKED:
            self.time_updated.emit(self._remaining, self._break_duration, False)
        else:
            self.time_updated.emit(0, 0, True)
