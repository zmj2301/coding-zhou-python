"""
定时休息应用主模块
提供工作休息计时器、屏幕锁定等功能
"""

import sys
import os
import ctypes
import threading
import time
from typing import Optional
from PySide6.QtCore import Qt, QTimer, QSettings, QObject, Signal
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from core.logger import logger
from core.timer_manager import TimerManager, TimerState
from ui.countdown_widget import CountdownWidget
from ui.settings_dialog import SettingsDialog
from ui.agreement_dialog import AgreementDialog


_USER32 = ctypes.windll.user32
_WTSAPI32 = ctypes.windll.wtsapi32

WTS_CURRENT_SERVER_HANDLE = 0
WTS_CURRENT_SESSION = 0xFFFFFFFF

_LockWorkStation = _USER32.LockWorkStation

# 会话监控轮询间隔（秒）- 优化性能
_SESSION_MONITOR_INTERVAL = 0.2


def _check_desktop_locked_via_input_desktop() -> bool:
    """通过 OpenInputDesktop 检测锁屏：无法打开输入桌面即为锁定"""
    try:
        hdesk = _USER32.OpenInputDesktop(0, False, 0x0100)
        if not hdesk:
            return True
        _USER32.CloseDesktop(hdesk)
        return False
    except Exception:
        return True


def _check_desktop_locked_via_desktop_name() -> bool:
    """通过桌面名称检测锁屏：非 Default 即为锁定"""
    try:
        hdesk = _USER32.OpenInputDesktop(0, False, 0x0100)
        if not hdesk:
            return True
        name_length = ctypes.c_uint32()
        _USER32.GetUserObjectInformationW(hdesk, 0x02, None, 0, ctypes.byref(name_length))
        desktop_name = ""
        if name_length.value > 0:
            name_buffer = ctypes.create_unicode_buffer(name_length.value)
            success = _USER32.GetUserObjectInformationW(
                hdesk, 0x02, name_buffer, name_length.value, ctypes.byref(name_length)
            )
            if success:
                desktop_name = name_buffer.value
        _USER32.CloseDesktop(hdesk)
        return bool(desktop_name and desktop_name != "Default")
    except Exception:
        return True


def _check_locked_via_foreground_window() -> bool:
    """通过前台窗口类名检测锁屏界面"""
    try:
        hwnd = _USER32.GetForegroundWindow()
        if not hwnd:
            return False
        class_name = ctypes.create_unicode_buffer(256)
        _USER32.GetClassNameW(hwnd, class_name, 256)
        lock_classes = ["LockScreenBackstop", "WorkerW", "ApplicationFrameWindow"]
        return any(cls in class_name.value for cls in lock_classes)
    except Exception:
        return False


def _lock_screen() -> None:
    """锁定屏幕"""
    logger.info("调用Windows API锁定屏幕")
    _LockWorkStation()


class SessionMonitor(QObject):
    """会话监控器 - 检测屏幕解锁事件"""
    
    session_unlocked = Signal()

    def __init__(self):
        """初始化会话监控器"""
        super().__init__()
        self._running: bool = False
        self._last_locked: bool = False
        self._poll_thread: Optional[threading.Thread] = None

    def _is_desktop_locked(self) -> bool:
        """
        检测桌面是否已锁定 - 组合多种方法，任一判定为锁定即返回 True
        """
        # 方法1：输入桌面可访问性（最可靠）
        locked1 = _check_desktop_locked_via_input_desktop()
        
        # 方法2：桌面名称（辅助验证）
        locked2 = _check_desktop_locked_via_desktop_name()
        
        # 方法3：前台窗口类名（辅助验证）
        locked3 = _check_locked_via_foreground_window()
        
        # 综合判断：任一为 True 即视为锁定
        # 只有三者都为 False 才认为未锁定
        is_locked = locked1 or locked2 or locked3
        
        # 调试日志（可选，生产环境可注释）
        # logger.debug(f"锁屏检测: input_desktop={locked1}, desktop_name={locked2}, foreground={locked3} => {is_locked}")
        
        return is_locked

    def _check_loop(self) -> None:
        """检查循环 - 定期检测桌面状态"""
        while self._running:
            try:
                is_locked = self._is_desktop_locked()
                # 详细日志：记录每次检测结果（可选，调试用）
                # logger.debug(f"锁屏检测: locked={is_locked}, last_locked={self._last_locked}")
                if self._last_locked and not is_locked:
                    logger.warning(f"检测到桌面解锁事件 (last_locked={self._last_locked}, is_locked={is_locked})")
                    self.session_unlocked.emit()
                self._last_locked = is_locked
            except Exception as e:
                logger.warning(f"会话监控循环异常: {e}")
            finally:
                time.sleep(_SESSION_MONITOR_INTERVAL)

    def start(self) -> None:
        """启动会话监控"""
        if self._poll_thread is not None:
            return
        # 启动前先检测一次，建立基准
        self._last_locked = self._is_desktop_locked()
        logger.info(f"会话监控初始状态: {'锁定' if self._last_locked else '未锁定'}")
        self._poll_thread = threading.Thread(target=self._check_loop, daemon=True)
        self._poll_thread.start()
        logger.info(f"会话监控已启动 (轮询间隔: {_SESSION_MONITOR_INTERVAL}秒)")

    def stop(self) -> None:
        """停止会话监控"""
        self._running = False


class App(QApplication):
    """定时休息应用主类"""
    
    def __init__(self, argv):
        """
        初始化应用
        
        Args:
            argv: 命令行参数
        """
        super().__init__(argv)
        logger.info("初始化App...")
        self.setApplicationName("定时休息")
        self.setQuitOnLastWindowClosed(False)

        self._settings = QSettings("CodersLife", "定时休息")

        self._timer_mgr = TimerManager()
        self._read_settings()

        self._session_monitor = SessionMonitor()
        self._session_monitor.session_unlocked.connect(self._on_session_unlocked)

        self._countdown_widget = CountdownWidget()

        # 高频锁屏守护定时器：休息期间每 500ms 检测一次，防止用户解锁
        self._lock_guard_timer = QTimer(self)
        self._lock_guard_timer.setInterval(500)
        self._lock_guard_timer.timeout.connect(self._lock_guard_check)

        self._connect_signals()

        self._session_monitor.start()

        if not self._show_agreement():
            logger.info("用户未同意协议，退出应用")
            return

        logger.info("显示倒计时窗口")
        self._countdown_widget.show()
        self._countdown_widget.raise_()
        self._countdown_widget.activateWindow()
        work_min = self._timer_mgr.work_duration // 60
        self._countdown_widget.set_idle_state(work_min)

    def _show_agreement(self) -> bool:
        """
        显示用户协议对话框
        
        Returns:
            用户是否同意协议
        """
        logger.info("显示用户协议对话框")
        dlg = AgreementDialog()
        result = dlg.exec()
        if result == QDialog.DialogCode.Accepted:
            logger.info("用户已同意协议")
            return True
        else:
            logger.info("用户未同意协议")
            return False

    def _read_settings(self) -> None:
        """读取设置"""
        work = self._settings.value("work_minutes", 20, type=int)
        break_ = self._settings.value("break_minutes", 5, type=int)
        logger.info(f"读取设置: 工作={work}分钟, 休息={break_}分钟")
        self._timer_mgr.work_duration = work * 60
        self._timer_mgr.break_duration = break_ * 60

    def _save_settings(self, work_minutes: int, break_minutes: int) -> None:
        """
        保存设置
        
        Args:
            work_minutes: 工作时长（分钟）
            break_minutes: 休息时长（分钟）
        """
        logger.info(f"保存设置: 工作={work_minutes}分钟, 休息={break_minutes}分钟")
        self._settings.setValue("work_minutes", work_minutes)
        self._settings.setValue("break_minutes", break_minutes)

    def _connect_signals(self) -> None:
        """连接信号与槽"""
        logger.debug("连接信号...")
        self._timer_mgr.state_changed.connect(self._on_state_changed)
        self._timer_mgr.time_updated.connect(self._countdown_widget.update_time)
        self._timer_mgr.work_finished.connect(self._on_work_finished)
        self._timer_mgr.break_finished.connect(self._on_break_finished)

        self._countdown_widget.settings_clicked.connect(self._show_settings)
        self._countdown_widget.start_clicked.connect(self._on_start_clicked)
        self._countdown_widget.pause_clicked.connect(self._on_pause_clicked)
        self._countdown_widget.stop_clicked.connect(self._on_stop_clicked)

        logger.debug("信号连接完成")

    def _on_state_changed(self, state: TimerState) -> None:
        """
        状态变化事件
        
        Args:
            state: 新的计时器状态
        """
        logger.info(f"状态改变: {state}")
        if state == TimerState.WORKING:
            self._countdown_widget.set_running_state(True)
        elif state == TimerState.LOCKED:
            self._countdown_widget.set_running_state(True)
            self._countdown_widget.show()
        elif state == TimerState.IDLE:
            self._countdown_widget.set_running_state(False)
            work_min = self._timer_mgr.work_duration // 60
            self._countdown_widget.set_idle_state(work_min)

    def _on_start_clicked(self) -> None:
        """开始按钮点击事件"""
        logger.info("用户点击开始")
        state = self._timer_mgr.state
        if state == TimerState.IDLE:
            self._timer_mgr.start_work()
            self._countdown_widget.set_running_state(True)
        elif state == TimerState.BREAK_DONE:
            self._timer_mgr.start_work()
            self._countdown_widget.set_running_state(True)

    def _on_pause_clicked(self) -> None:
        """暂停按钮点击事件"""
        logger.info("用户点击暂停")
        self._timer_mgr.pause()
        self._countdown_widget.set_running_state(False)

    def _on_stop_clicked(self) -> None:
        """停止按钮点击事件"""
        logger.info("用户点击停止")
        self._timer_mgr.stop()
        self._countdown_widget.set_running_state(False)
        work_min = self._timer_mgr.work_duration // 60
        self._countdown_widget.set_idle_state(work_min)

    def _show_settings(self) -> None:
        """显示设置对话框"""
        logger.debug("显示设置对话框")
        work_min = self._timer_mgr.work_duration // 60
        break_min = self._timer_mgr.break_duration // 60
        dlg = SettingsDialog(work_min, break_min, self._countdown_widget)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            logger.debug("设置被用户接受")
            self._timer_mgr.work_duration = dlg.work_minutes * 60
            self._timer_mgr.break_duration = dlg.break_minutes * 60
            self._save_settings(dlg.work_minutes, dlg.break_minutes)
            
            # 同步保存到 config.json
            self._sync_to_config_json(dlg.work_minutes, dlg.break_minutes)
    
    def _sync_to_config_json(self, work_minutes: int, break_minutes: int) -> None:
        """
        将设置同步到 config.json
        
        Args:
            work_minutes: 工作时长（分钟）
            break_minutes: 休息时长（分钟）
        """
        try:
            import json
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                if 'timer' not in config:
                    config['timer'] = {}
                config['timer']['work_minutes'] = work_minutes
                config['timer']['break_minutes'] = break_minutes
                
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
                
                logger.debug(f"已同步配置到 config.json: 工作={work_minutes}分钟, 休息={break_minutes}分钟")
        except Exception as e:
            logger.warning(f"同步配置到 config.json 失败: {e}")

    def _on_work_finished(self) -> None:
        """工作结束事件"""
        logger.info("工作时间结束")
        self._countdown_widget.set_running_state(False)
        _lock_screen()
        QTimer.singleShot(2000, self._timer_mgr.start_break)

    def _on_break_finished(self) -> None:
        """休息结束事件 - 自动开始下一轮工作"""
        logger.info("休息时间结束，自动开始下一轮工作")
        self._countdown_widget.set_running_state(False)
        QTimer.singleShot(1000, self._auto_start_next_work)

    def _auto_start_next_work(self) -> None:
        """自动开始下一轮工作"""
        state = self._timer_mgr.state
        if state == TimerState.BREAK_DONE:
            logger.info("自动启动下一轮工作计时")
            self._timer_mgr.start_work()
            self._countdown_widget.set_running_state(True)

    @property
    def countdown_widget(self) -> CountdownWidget:
        """获取倒计时组件"""
        return self._countdown_widget

    def _on_session_unlocked(self) -> None:
        """会话解锁事件 - 在休息期间强制解锁会立即重新锁定"""
        state = self._timer_mgr.state
        logger.warning(f"检测到会话解锁事件，当前状态: {state}")
        if state == TimerState.LOCKED:
            logger.warning("休息期间强制解锁，立即重新锁屏！")
            _lock_screen()
            # 兜底：500ms后再次尝试锁屏
            QTimer.singleShot(500, _lock_screen)
            # 额外兜底：1秒后再次尝试
            QTimer.singleShot(1000, _lock_screen)



