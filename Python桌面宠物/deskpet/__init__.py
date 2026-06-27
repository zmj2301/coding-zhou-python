"""
桌面宠物主模块
提供桌面宠物窗口和定时休息功能的集成
"""

import sys
import os
import logging
from typing import Optional

from PySide6.QtWidgets import QApplication

from .config import DeskPetConfig
from .pet_window import PetWindow
from .sync_manager import PositionSyncManager

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'relax_exe'))


def _setup_logger() -> None:
    """配置日志系统"""
    logging.basicConfig(
        filename='main_log.log',
        filemode='w',
        encoding='utf-8',
        level=logging.DEBUG,
        format='%(levelname)s %(asctime)s : %(message)s (line %(lineno)d) [%(filename)s]'
    )
    logging.debug("应用启动")


class DeskPet:
    """桌面宠物主类 - 管理宠物窗口和倒计时功能"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化桌面宠物
        
        Args:
            config_path: 配置文件路径，默认为项目根目录下的 config.json
        """
        _setup_logger()
        self._config = DeskPetConfig(config_path)
        self._app: Optional[QApplication] = None
        self._pet_window: Optional[PetWindow] = None
        self._sync_manager: Optional[PositionSyncManager] = None
        self._countdown_widget = None

    @property
    def config(self) -> DeskPetConfig:
        """获取配置对象"""
        return self._config

    def run(self) -> None:
        """启动桌面宠物应用"""
        from relax_exe.app import App

        self._app = App(sys.argv)
        self._countdown_widget = self._app.countdown_widget
        
        # 统一配置 - 将倒计时应用的配置与 config.json 同步
        self._sync_app_config()

        self._pet_window = PetWindow(self._config, countdown_widget=self._countdown_widget)
        self._pet_window.show()
        self._pet_window.position_to_bottom_right()

        if self._countdown_widget and self._countdown_widget.isVisible():
            QApplication.processEvents()
            self._sync_manager = PositionSyncManager(self._pet_window, self._countdown_widget)
            self._sync_manager.init_offset()
            self._countdown_widget.position_changed.connect(self._sync_manager.sync_from_b)
            self._pet_window._sync_manager = self._sync_manager
            logging.debug("位置同步已建立")

        sys.exit(self._app.exec())
    
    def _sync_app_config(self) -> None:
        """同步配置到倒计时应用"""
        if hasattr(self._app, '_timer_mgr'):
            # 将 config.json 中的配置应用到 TimerManager
            work_seconds = self._config.work_minutes * 60
            break_seconds = self._config.break_minutes * 60
            self._app._timer_mgr.work_duration = work_seconds
            self._app._timer_mgr.break_duration = break_seconds
            logging.debug(f"配置已同步: 工作={self._config.work_minutes}分钟, 休息={self._config.break_minutes}分钟")

    def reload_config(self) -> None:
        """重新加载配置文件"""
        self._config.load()
        if self._pet_window:
            self._pet_window.reload_icon()
        self._sync_app_config()
        logging.debug("配置已重新加载")
