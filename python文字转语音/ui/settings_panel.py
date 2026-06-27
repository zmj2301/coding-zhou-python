import tkinter as tk
from tkinter import ttk


class SettingsPanel(ttk.LabelFrame):
    def __init__(self, parent, config_manager, on_change=None, *args, **kwargs):
        super().__init__(parent, text="音频设置", *args, **kwargs)
        self.parent = parent
        self.config_manager = config_manager
        self.on_change = on_change
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        engine_frame = ttk.Frame(main_frame)
        engine_frame.pack(fill=tk.X, pady=5)
        ttk.Label(engine_frame, text="TTS引擎:").pack(side=tk.LEFT)
        self.engine_var = tk.StringVar(value=self.config_manager.get("engine", "pyttsx3"))
        engine_combo = ttk.Combobox(engine_frame, textvariable=self.engine_var, values=["pyttsx3", "gTTS"], state="readonly", width=15)
        engine_combo.pack(side=tk.LEFT, padx=10)
        engine_combo.bind("<<ComboboxSelected>>", self._on_setting_change)
        
        quality_frame = ttk.Frame(main_frame)
        quality_frame.pack(fill=tk.X, pady=5)
        ttk.Label(quality_frame, text="音质:").pack(side=tk.LEFT)
        self.quality_var = tk.StringVar(value=self.config_manager.get("quality", "standard"))
        quality_combo = ttk.Combobox(quality_frame, textvariable=self.quality_var, values=["low", "standard", "high"], state="readonly", width=15)
        quality_combo.pack(side=tk.LEFT, padx=10)
        quality_combo.bind("<<ComboboxSelected>>", self._on_setting_change)
        
        speed_frame = ttk.Frame(main_frame)
        speed_frame.pack(fill=tk.X, pady=5)
        ttk.Label(speed_frame, text="语速:").pack(side=tk.LEFT)
        self.speed_var = tk.DoubleVar(value=self.config_manager.get("speed", 1.0))
        speed_scale = ttk.Scale(speed_frame, from_=0.5, to=2.0, variable=self.speed_var, orient=tk.HORIZONTAL, command=self._on_speed_change)
        speed_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        self.speed_label = ttk.Label(speed_frame, text=f"{self.speed_var.get():.1f}x", width=5)
        self.speed_label.pack(side=tk.LEFT)
        
        voice_frame = ttk.Frame(main_frame)
        voice_frame.pack(fill=tk.X, pady=5)
        ttk.Label(voice_frame, text="语音类型:").pack(side=tk.LEFT)
        self.voice_var = tk.StringVar(value=self.config_manager.get("voice_type", "female"))
        voice_combo = ttk.Combobox(voice_frame, textvariable=self.voice_var, values=["male", "female", "neutral"], state="readonly", width=15)
        voice_combo.pack(side=tk.LEFT, padx=10)
        voice_combo.bind("<<ComboboxSelected>>", self._on_setting_change)
        
        format_frame = ttk.Frame(main_frame)
        format_frame.pack(fill=tk.X, pady=5)
        ttk.Label(format_frame, text="输出格式:").pack(side=tk.LEFT)
        self.format_var = tk.StringVar(value=self.config_manager.get("output_format", "mp3"))
        format_combo = ttk.Combobox(format_frame, textvariable=self.format_var, values=["mp3", "wav"], state="readonly", width=15)
        format_combo.pack(side=tk.LEFT, padx=10)
        format_combo.bind("<<ComboboxSelected>>", self._on_setting_change)
    
    def _on_setting_change(self, event=None):
        self._save_settings()
        if self.on_change:
            self.on_change()
    
    def _on_speed_change(self, value):
        self.speed_label.config(text=f"{float(value):.1f}x")
        self._save_settings()
        if self.on_change:
            self.on_change()
    
    def _save_settings(self):
        self.config_manager.set("engine", self.engine_var.get())
        self.config_manager.set("quality", self.quality_var.get())
        self.config_manager.set("speed", float(self.speed_var.get()))
        self.config_manager.set("voice_type", self.voice_var.get())
        self.config_manager.set("output_format", self.format_var.get())
        self.config_manager.save_config()
    
    def get_settings(self):
        return {
            "engine": self.engine_var.get(),
            "quality": self.quality_var.get(),
            "speed": float(self.speed_var.get()),
            "voice_type": self.voice_var.get(),
            "output_format": self.format_var.get()
        }
