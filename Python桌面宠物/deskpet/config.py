import json
import os
from typing import Dict, Any, List, Optional


class DeskPetConfig:
    """桌面宠物配置管理类"""
    
    DEFAULT_CONFIG: Dict[str, Any] = {
        "pet": {
            "size": 200,
            "x_offset": 50,
            "y_offset": 200,
            "bg_color": "white",
            "icon_path": "icon.png",
            "transparent": False
        },
        "timer": {
            "work_minutes": 20,
            "break_minutes": 5
        },
        "menus": {
            "cctv_channels": [
                {"name": "CCTV-1 综合", "url": "https://tv.cctv.com/cctv1/"},
                {"name": "CCTV-2 财经", "url": "https://tv.cctv.com/cctv2/"},
                {"name": "CCTV-3 综艺", "url": "https://tv.cctv.com/cctv3/"},
                {"name": "CCTV-4 中文国际", "url": "https://tv.cctv.com/cctv4/"},
                {"name": "CCTV-5 体育", "url": "https://tv.cctv.com/cctv5/"},
                {"name": "CCTV-5+ 体育赛事", "url": "https://tv.cctv.com/cctv5plus/"},
                {"name": "CCTV-6 电影", "url": "https://tv.cctv.com/cctv6/"},
                {"name": "CCTV-7 国防军事", "url": "https://tv.cctv.com/cctv7/"},
                {"name": "CCTV-8 电视剧", "url": "https://tv.cctv.com/cctv8/"},
                {"name": "CCTV-9 纪录", "url": "https://tv.cctv.com/cctv9/"},
                {"name": "CCTV-10 科教", "url": "https://tv.cctv.com/cctv10/"},
                {"name": "CCTV-11 戏曲", "url": "https://tv.cctv.com/cctv11/"},
                {"name": "CCTV-12 社会与法", "url": "https://tv.cctv.com/cctv12/"},
                {"name": "CCTV-13 新闻", "url": "https://tv.cctv.com/cctv13/"},
                {"name": "CCTV-14 少儿", "url": "https://tv.cctv.com/cctv14/"},
                {"name": "CCTV-15 音乐", "url": "https://tv.cctv.com/cctv15/"},
                {"name": "CCTV-16 奥林匹克", "url": "https://tv.cctv.com/cctv16/"},
                {"name": "CCTV-17 农业农村", "url": "https://tv.cctv.com/cctv17/"}
            ],
            "ai_models": [
                {"name": "DeepSeek 深度求索", "url": "https://chat.deepseek.com/"},
                {"name": "Qwen 通义千问", "url": "https://tongyi.aliyun.com/"},
                {"name": "ERNIE 文心一言", "url": "https://yiyan.baidu.com/"},
                {"name": "Kimi 月之暗面", "url": "https://kimi.moonshot.cn/"},
                {"name": "ChatGLM 智谱清言", "url": "https://chatglm.cn/"},
                {"name": "Doubao 豆包", "url": "https://www.doubao.com/"},
                {"name": "Yuanbao 腾讯元宝", "url": "https://yuanbao.tencent.com/"},
                {"name": "Spark 讯飞星火", "url": "https://xinghuo.xfyun.cn/"},
                {"name": "Metaso 秘塔搜索", "url": "https://metaso.cn/"},
                {"name": "NanoAI 360搜索", "url": "https://n.cn/"}
            ],
            "custom_links": []
        },
        "history": {
            "texts": []
        }
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为项目根目录下的 config.json
        """
        if config_path is None:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        self._config_path: str = config_path
        self._data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """加载配置文件，如不存在则使用默认配置"""
        existed = os.path.exists(self._config_path)
        if existed:
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, IOError, OSError):
                self._data = {}
        else:
            self._data = {}
        self._apply_defaults()
        if not existed:
            self.save()

    def save(self) -> None:
        """保存配置到文件"""
        try:
            os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=4, ensure_ascii=False)
        except (IOError, OSError) as e:
            print(f"保存配置失败: {e}")

    def _apply_defaults(self) -> None:
        """应用默认配置到现有数据中"""
        for section, defaults in self.DEFAULT_CONFIG.items():
            if section not in self._data:
                self._data[section] = {}
            if isinstance(defaults, dict):
                for key, val in defaults.items():
                    if key not in self._data[section]:
                        self._data[section][key] = val

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            section: 配置分区
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        return self._data.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value: Any) -> None:
        """
        设置配置值
        
        Args:
            section: 配置分区
            key: 配置键
            value: 配置值
        """
        if section not in self._data:
            self._data[section] = {}
        self._data[section][key] = value

    @property
    def pet_size(self) -> int:
        """宠物窗口大小"""
        return self.get("pet", "size", 200)

    @pet_size.setter
    def pet_size(self, value: int) -> None:
        self.set("pet", "size", int(value))

    @property
    def pet_x_offset(self) -> int:
        """宠物窗口X轴偏移"""
        return self.get("pet", "x_offset", 50)

    @pet_x_offset.setter
    def pet_x_offset(self, value: int) -> None:
        self.set("pet", "x_offset", int(value))

    @property
    def pet_y_offset(self) -> int:
        """宠物窗口Y轴偏移"""
        return self.get("pet", "y_offset", 200)

    @pet_y_offset.setter
    def pet_y_offset(self, value: int) -> None:
        self.set("pet", "y_offset", int(value))

    @property
    def pet_bg_color(self) -> str:
        """宠物窗口背景颜色"""
        return self.get("pet", "bg_color", "white")

    @pet_bg_color.setter
    def pet_bg_color(self, value: str) -> None:
        self.set("pet", "bg_color", str(value))

    @property
    def pet_icon_path(self) -> str:
        """宠物图标路径"""
        return self.get("pet", "icon_path", "icon.png")

    @pet_icon_path.setter
    def pet_icon_path(self, value: str) -> None:
        self.set("pet", "icon_path", str(value))

    @property
    def pet_transparent(self) -> bool:
        """是否透明背景"""
        return self.get("pet", "transparent", False)

    @pet_transparent.setter
    def pet_transparent(self, value: bool) -> None:
        self.set("pet", "transparent", bool(value))

    @property
    def work_minutes(self) -> int:
        """工作时长（分钟）"""
        return self.get("timer", "work_minutes", 20)

    @work_minutes.setter
    def work_minutes(self, value: int) -> None:
        self.set("timer", "work_minutes", int(value))

    @property
    def break_minutes(self) -> int:
        """休息时长（分钟）"""
        return self.get("timer", "break_minutes", 5)

    @break_minutes.setter
    def break_minutes(self, value: int) -> None:
        self.set("timer", "break_minutes", int(value))

    @property
    def cctv_channels(self) -> List[Dict[str, str]]:
        """CCTV频道列表"""
        return self.get("menus", "cctv_channels", [])

    @property
    def ai_models(self) -> List[Dict[str, str]]:
        """AI模型列表"""
        return self.get("menus", "ai_models", [])

    @property
    def custom_links(self) -> List[Dict[str, str]]:
        """自定义链接列表"""
        return self.get("menus", "custom_links", [])

    def add_history_text(self, text: str) -> None:
        """
        添加历史文本
        
        Args:
            text: 要添加的文本内容
        """
        texts = self.get("history", "texts", [])
        if text not in texts:
            texts.insert(0, text)
            if len(texts) > 20:
                texts = texts[:20]
            self.set("history", "texts", texts)

    @property
    def history_texts(self) -> List[str]:
        """历史文本列表"""
        return self.get("history", "texts", [])

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return dict(self._data)
