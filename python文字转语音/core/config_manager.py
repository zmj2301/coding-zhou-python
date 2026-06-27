import json
import os
from pathlib import Path


class ConfigManager:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.config_path = self.data_dir / "config.json"
        
        self.default_config = {
            "api_key": "",
            "api_provider": "openai",
            "engine": "pyttsx3",
            "quality": "standard",
            "speed": 1.0,
            "voice_type": "female",
            "output_format": "mp3",
            "output_dir": str(self.base_dir / "output"),
            "first_run": True
        }
        
        self.config = self.load_config()
    
    def load_config(self):
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                return {**self.default_config, **config}
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return self.default_config.copy()
        else:
            return self.default_config.copy()
    
    def save_config(self):
        try:
            if not self.data_dir.exists():
                self.data_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value
    
    def is_first_run(self):
        return self.config.get("first_run", True)
    
    def set_first_run_done(self):
        self.config["first_run"] = False
        self.save_config()
