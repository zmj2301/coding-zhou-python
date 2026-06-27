# 配置文件管理
import json
import os


class Config:
    """配置类"""
    
    # 默认配置
    DEFAULT_CONFIG = {
        'model': {
            'input_channels': 14,
            'num_filters': [64, 128, 256],
            'hidden_size': 512,
            'dropout': 0.5
        },
        'mcts': {
            'simulation_limit': 1000,
            'time_limit': 2.0,
            'c_param': 1.414
        },
        'training': {
            'batch_size': 32,
            'learning_rate': 0.001,
            'num_epochs': 50,
            'device': 'auto'  # 'auto', 'cpu', 'cuda'
        },
        'difficulty': {
            1: {'sim_limit': 200, 'time_limit': 0.5},
            2: {'sim_limit': 800, 'time_limit': 1.5},
            3: {'sim_limit': 2000, 'time_limit': 3.0}
        },
        'paths': {
            'models_dir': 'models',
            'data_dir': 'data',
            'games_dir': 'data/games',
            'reports_dir': 'data/reports'
        }
    }
    
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = self.DEFAULT_CONFIG.copy()
        
        if os.path.exists(config_file):
            self.load()
    
    def get(self, key_path, default=None):
        """获取配置"""
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path, value):
        """设置配置"""
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def save(self):
        """保存配置"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def load(self):
        """加载配置"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                self._update_dict(self.config, loaded)
    
    def _update_dict(self, d, u):
        """递归更新字典"""
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._update_dict(d[k], v)
            else:
                d[k] = v
    
    def get_device(self):
        """获取计算设备"""
        import torch
        device_str = self.get('training.device', 'auto')
        
        if device_str == 'auto':
            return 'cuda' if torch.cuda.is_available() else 'cpu'
        
        return device_str
