"""
定时休息应用主模块
提供工作休息计时器、屏幕锁定等功能
"""

import sys
import os
import ctypes
import threading
import time
import winsound
from typing import Optional
from PySide6.QtCore import Qt, QTimer, QSettings, QObject, Signal
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from core.logger import logger
from core.timer_manager import TimerManager, TimerState
from ui.countdown_widget import CountdownWidget
from ui.settings_dialog import SettingsDialog
from ui.agreement_dialog import AgreementDialog
from ui.flip_clock_widget import FlipClockWidget


_USER32 = ctypes.windll.user32
_WTSAPI32 = ctypes.windll.wtsapi32
_SHELL32 = ctypes.windll.shell32

WTS_CURRENT_SERVER_HANDLE = 0
WTS_CURRENT_SESSION = 0xFFFFFFFF

_LockWorkStation = _USER32.LockWorkStation

# 会话监控轮询间隔（秒）- 优化性能
_SESSION_MONITOR_INTERVAL = 0.2

# Shell_NotifyIcon 常量
NIM_ADD = 0x00000000
NIM_MODIFY = 0x00000001
NIM_DELETE = 0x00000002
NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_INFO = 0x00000010
NIIF_INFO = 0x00000001
NIIF_WARNING = 0x00000002
NIIF_ERROR = 0x00000003

class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("hwnd", ctypes.c_void_p),
        ("uID", ctypes.c_uint),
        ("uFlags", ctypes.c_uint),
        ("uCallbackMessage", ctypes.c_uint),
        ("hIcon", ctypes.c_void_p),
        ("szTip", ctypes.c_wchar * 128),
        ("dwState", ctypes.c_ulong),
        ("dwStateMask", ctypes.c_ulong),
        ("szInfo", ctypes.c_wchar * 256),
        ("uTimeout", ctypes.c_uint),
        ("szInfoTitle", ctypes.c_wchar * 64),
        ("dwInfoFlags", ctypes.c_ulong),
        ("guidItem", ctypes.c_ulong * 4),
        ("hBalloonIcon", ctypes.c_void_p),
    ]

def _show_balloon_notification(title: str, message: str, icon_flag: int = NIIF_INFO) -> None:
    """使用 Windows Shell_NotifyIcon 显示气球通知"""
    try:
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hwnd = None
        nid.uID = 1
        nid.uFlags = NIF_INFO
        nid.szInfoTitle = title
        nid.szInfo = message
        nid.dwInfoFlags = icon_flag
        _SHELL32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid))
        _SHELL32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid))
    except Exception as e:
        logger.warning(f"气球通知失败: {e}")


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


def _is_desktop_locked() -> bool:
    """独立函数：检测桌面是否已锁定，组合三种方法"""
    return (_check_desktop_locked_via_input_desktop()
            or _check_desktop_locked_via_desktop_name()
            or _check_locked_via_foreground_window())


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

        # 翻页钟倒计时窗口（快捷版）
        self._flip_clock = FlipClockWidget()

        # 高频锁屏守护定时器：休息期间每 50ms 检测一次，防止用户解锁
        self._lock_guard_timer = QTimer(self)
        self._lock_guard_timer.setInterval(50)
        self._lock_guard_timer.timeout.connect(self._lock_guard_check)

        # 1分钟提醒标记：每个工作周期只提醒一次
        self._one_minute_warned = False

        # 休息结束且锁屏时，标记待自动开始下一轮（用户解锁后触发）
        self._pending_auto_start = False

        # 解锁兜底轮询定时器：休息结束锁屏时启动，每 1s 检测是否已解锁
        self._unlock_poll_timer = QTimer(self)
        self._unlock_poll_timer.setInterval(1000)
        self._unlock_poll_timer.timeout.connect(self._unlock_poll_check)

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
        self._timer_mgr.time_updated.connect(self._sync_flip_clock)
        self._timer_mgr.time_updated.connect(self._check_one_minute_warning)
        self._timer_mgr.work_finished.connect(self._on_work_finished)
        self._timer_mgr.break_finished.connect(self._on_break_finished)

        self._countdown_widget.settings_clicked.connect(self._show_settings)
        self._countdown_widget.start_clicked.connect(self._on_start_clicked)
        self._countdown_widget.pause_clicked.connect(self._on_pause_clicked)
        self._countdown_widget.stop_clicked.connect(self._on_stop_clicked)

        # 翻页钟关闭 → 显示回倒计时窗口
        self._flip_clock.close_btn_clicked = self._show_countdown_from_flip

        logger.debug("信号连接完成")

    def _sync_flip_clock(self, remaining: int, total: int, is_work: bool) -> None:
        """将倒计时同步到翻页钟"""
        self._flip_clock.set_remaining(remaining)

    def _check_one_minute_warning(self, remaining: int, total: int, is_work: bool) -> None:
        """工作时间剩余1分钟时弹出Windows气球通知"""
        if is_work and remaining == 60 and not self._one_minute_warned:
            self._one_minute_warned = True
            logger.info("工作时间剩余1分钟，弹出通知")
            _show_balloon_notification("定时休息", "当前剩余 1 分钟锁屏，请及时保存资料", NIIF_WARNING)
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)

    def _on_state_changed(self, state: TimerState) -> None:
        """
        状态变化事件
        
        Args:
            state: 新的计时器状态
        """
        logger.info(f"状态改变: {state}")
        if state == TimerState.WORKING:
            self._countdown_widget.set_running_state(True)
            self._flip_clock.pause()
            self._flip_clock.hide()
            self._stop_lock_guard()
        elif state == TimerState.LOCKED:
            self._countdown_widget.set_running_state(True)
            self._countdown_widget.show()
            # 锁屏期间同步翻页钟
            break_min = self._timer_mgr.break_duration // 60
            self._flip_clock.set_duration(break_min)
            self._flip_clock.start()
            self._start_lock_guard()
        elif state == TimerState.IDLE:
            self._countdown_widget.set_running_state(False)
            work_min = self._timer_mgr.work_duration // 60
            self._countdown_widget.set_idle_state(work_min)
            self._flip_clock.stop()
            self._flip_clock.hide()
            self._stop_lock_guard()
        elif state == TimerState.BREAK_DONE:
            self._flip_clock.stop()
            self._flip_clock.hide()
            self._stop_lock_guard()

    def _start_lock_guard(self) -> None:
        """启动高频锁屏守护：休息期间每 500ms 检测一次"""
        if not self._lock_guard_timer.isActive():
            logger.info("启动休息期锁屏守护 (500ms 间隔)")
            self._lock_guard_timer.start()

    def _stop_lock_guard(self) -> None:
        """停止高频锁屏守护"""
        if self._lock_guard_timer.isActive():
            logger.info("停止休息期锁屏守护")
            self._lock_guard_timer.stop()

    def _lock_guard_check(self) -> None:
        """锁屏守护检测：休息期间检测到解锁立即重新锁屏"""
        if self._timer_mgr.state != TimerState.LOCKED:
            self._stop_lock_guard()
            return
        
        # 组合检测：任一判定为未锁定即视为用户解锁
        locked1 = _check_desktop_locked_via_input_desktop()
        locked2 = _check_desktop_locked_via_desktop_name()
        locked3 = _check_locked_via_foreground_window()
        is_locked = locked1 or locked2 or locked3
        
        if not is_locked:
            logger.warning("锁屏守护检测到解锁，立即重新锁屏！")
            _lock_screen()

    def _on_start_clicked(self) -> None:
        """开始按钮点击事件"""
        logger.info("用户点击开始")
        state = self._timer_mgr.state
        if state == TimerState.IDLE:
            self._one_minute_warned = False
            self._timer_mgr.start_work()
            self._countdown_widget.set_running_state(True)
        elif state == TimerState.BREAK_DONE:
            self._one_minute_warned = False
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
        self._pending_auto_start = False
        self._unlock_poll_timer.stop()
        self._countdown_widget.set_running_state(False)
        work_min = self._timer_mgr.work_duration // 60
        self._countdown_widget.set_idle_state(work_min)

    def _show_countdown_from_flip(self) -> None:
        """从翻页钟返回显示倒计时窗口"""
        logger.debug("翻页钟关闭，显示倒计时窗口")
        self._flip_clock.hide()
        self._countdown_widget.show()
        self._countdown_widget.raise_()
        self._countdown_widget.activateWindow()

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
        """工作结束事件 - 强制锁屏并自动开始休息"""
        logger.info("工作时间结束")
        self._countdown_widget.set_running_state(False)
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        _lock_screen()
        QTimer.singleShot(2000, self._timer_mgr.start_break)

    def _on_break_finished(self) -> None:
        """休息结束事件 - 登录后自动开始下一轮工作"""
        logger.info("休息时间结束")
        self._countdown_widget.set_running_state(False)
        self._flip_clock.stop()
        self._flip_clock.hide()
        self._stop_lock_guard()
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)

        if _is_desktop_locked():
            # 用户不在电脑前：等待解锁后自动开始
            logger.info("屏幕已锁定，等待用户回来自动开始工作")
            self._pending_auto_start = True
            if hasattr(self, '_pet_window') and self._pet_window:
                self._pet_window.set_countdown_overlay_text("工作时间到！")
            work_min = self._timer_mgr.work_duration // 60
            self._countdown_widget.set_idle_state(work_min)
            # 启动解锁兜底轮询
            self._unlock_poll_timer.start()
        else:
            # 用户已在电脑前，直接开始下一轮工作
            logger.info("用户已在电脑前，自动开始下一轮工作")
            self._one_minute_warned = False
            self._timer_mgr.start_work()

    def _unlock_poll_check(self) -> None:
        """解锁兜底检测：休息结束锁屏时周期性检查是否已解锁"""
        if not self._pending_auto_start:
            self._unlock_poll_timer.stop()
            return
        if not _is_desktop_locked():
            logger.info("解锁兜底检测：检测到用户已解锁，自动开始下一轮工作")
            self._unlock_poll_timer.stop()
            self._pending_auto_start = False
            if hasattr(self, '_pet_window') and self._pet_window:
                self._pet_window.set_countdown_overlay_text("")
            self._one_minute_warned = False
            self._timer_mgr.start_work()

    @property
    def countdown_widget(self) -> CountdownWidget:
        """获取倒计时组件"""
        return self._countdown_widget

    def _on_session_unlocked(self) -> None:
        """会话解锁事件 - 用户回到电脑前"""
        state = self._timer_mgr.state
        logger.info(f"检测到会话解锁，当前状态: {state}")

        if state == TimerState.LOCKED:
            logger.warning("休息期间强制解锁，立即重新锁屏！")
            _lock_screen()
            self._start_lock_guard()
        elif state == TimerState.BREAK_DONE or self._pending_auto_start:
            # 用户回来，自动开始下一轮工作
            logger.info("用户解锁且处于休息结束状态，自动开始下一轮工作")
            self._pending_auto_start = False
            self._unlock_poll_timer.stop()
            if hasattr(self, '_pet_window') and self._pet_window:
                self._pet_window.set_countdown_overlay_text("")
            self._one_minute_warned = False
            self._timer_mgr.start_work()
        elif state == TimerState.IDLE:
            if hasattr(self, '_pet_window') and self._pet_window:
                self._pet_window.set_countdown_overlay_text("")



