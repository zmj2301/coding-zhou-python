import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
from datetime import datetime
import os

from .text_input_panel import TextInputPanel
from .control_panel import ControlPanel
from .settings_panel import SettingsPanel
from .ai_panel import AIPanel
from .status_panel import StatusPanel


class MainWindow(tk.Tk):
    def __init__(self, config_manager, tts_engine, audio_handler, ai_enhancer, history_manager):
        super().__init__()
        self.config_manager = config_manager
        self.tts_engine = tts_engine
        self.audio_handler = audio_handler
        self.ai_enhancer = ai_enhancer
        self.history_manager = history_manager
        
        self.current_audio_path = None
        self.is_processing = False
        self.is_playing = False
        
        self.title("文字转语音工具")
        self.geometry("900x700")
        self.minsize(800, 600)
        
        self.create_widgets()
        self.check_first_run()
    
    def create_widgets(self):
        left_frame = ttk.Frame(self)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        right_frame = ttk.Frame(self)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        self.text_panel = TextInputPanel(left_frame)
        self.text_panel.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.control_panel = ControlPanel(left_frame, 
                                        on_convert=self.on_convert, 
                                        on_stop=self.on_stop,
                                        on_save=self.on_save)
        self.control_panel.pack(fill=tk.X, pady=5)
        
        self.settings_panel = SettingsPanel(left_frame, self.config_manager)
        self.settings_panel.pack(fill=tk.X, pady=5)
        
        self.ai_panel = AIPanel(right_frame, self.config_manager, self.ai_enhancer, 
                               on_optimize=self.on_optimize_text)
        self.ai_panel.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.status_panel = StatusPanel(right_frame)
        self.status_panel.pack(fill=tk.X, pady=5)
        
        self.control_panel.set_status("就绪", "green")
        self.status_panel.set_progress(0)
    
    def check_first_run(self):
        if self.config_manager.is_first_run():
            messagebox.showinfo("欢迎使用", "这是您第一次使用本工具！\n推荐使用pyttsx3引擎，无需网络，直接播放。")
            self.config_manager.set_first_run_done()
    
    def on_convert(self):
        text = self.text_panel.get_text()
        if not text or not text.strip():
            messagebox.showwarning("提示", "请先输入要转换的文本")
            return
        
        if self.is_processing:
            messagebox.showinfo("提示", "正在处理中，请稍候...")
            return
        
        self.is_processing = True
        self.control_panel.set_buttons_state(True)
        self.control_panel.set_status("正在转换...", "blue")
        self.status_panel.set_info("正在进行语音合成...")
        self.status_panel.set_progress(0)
        
        thread = threading.Thread(target=self._convert_thread, args=(text,))
        thread.daemon = True
        thread.start()
    
    def _convert_thread(self, text):
        try:
            settings = self.settings_panel.get_settings()
            
            self.after(0, lambda: self.status_panel.set_progress(20))
            
            output_dir = Path(self.config_manager.get("output_dir", "./output"))
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_path = output_dir / f"tts_{timestamp}.{settings['output_format']}"
            
            self.after(0, lambda: self.status_panel.set_progress(50))
            
            if settings['engine'] == 'pyttsx3':
                try:
                    self.after(0, lambda: self.status_panel.set_progress(80))
                    self.after(0, lambda: self.control_panel.set_status("正在播放...", "green"))
                    
                    success = self.tts_engine.speak_with_pyttsx3(
                        text, 
                        settings['speed'], 
                        settings['voice_type']
                    )
                    
                    if success:
                        self.after(0, lambda: self.status_panel.set_progress(90))
                        
                        try:
                            file_success = self.tts_engine.synthesize_with_pyttsx3(
                                text, 
                                str(temp_path), 
                                settings['speed'], 
                                settings['voice_type'], 
                                settings['quality']
                            )
                            if file_success and Path(temp_path).exists():
                                self.current_audio_path = str(temp_path)
                                self.history_manager.add_record(text, str(temp_path), settings)
                        except Exception as e:
                            print(f"生成文件时出错（不影响播放）: {e}")
                        
                        self.after(0, lambda: self.status_panel.set_progress(100))
                        self.after(0, lambda: self.control_panel.set_status("播放完成", "green"))
                        self.after(0, lambda: self.status_panel.set_info("语音播放完成"))
                    else:
                        raise Exception("pyttsx3播放失败")
                    
                    self.is_processing = False
                    self.after(0, lambda: self.control_panel.set_buttons_state(False))
                    return
                    
                except Exception as e:
                    print(f"直接播放失败，尝试文件方式: {e}")
                    self.after(0, lambda: self.status_panel.set_info("尝试备用方式..."))
            
            success, audio_path = self.tts_engine.synthesize(
                text, 
                str(temp_path),
                settings['engine'],
                settings['speed'],
                settings['voice_type'],
                settings['quality']
            )
            
            self.after(0, lambda: self.status_panel.set_progress(80))
            
            if success:
                self.current_audio_path = audio_path
                self.history_manager.add_record(text, audio_path, settings)
                
                self.after(0, lambda: self.status_panel.set_progress(100))
                self.after(0, lambda: self.control_panel.set_status("转换完成", "green"))
                self.after(0, lambda: self.status_panel.set_info("语音合成完成"))
                
                play_thread = threading.Thread(target=self._play_thread, args=(audio_path,))
                play_thread.daemon = True
                play_thread.start()
            else:
                self.after(0, lambda: self.control_panel.set_status("转换失败", "red"))
                self.after(0, lambda: self.status_panel.set_info("语音合成失败，请尝试使用pyttsx3引擎"))
                self.after(0, lambda: messagebox.showerror("错误", "语音合成失败！\n请确保使用pyttsx3引擎（推荐），\ngTTS需要网络连接。"))
        
        except Exception as e:
            print(f"处理异常: {e}")
            self.after(0, lambda: self.control_panel.set_status("转换失败", "red"))
            self.after(0, lambda: self.status_panel.set_info(f"错误: {str(e)}"))
            self.after(0, lambda: messagebox.showerror("错误", f"发生错误: {str(e)}"))
        
        finally:
            self.is_processing = False
            self.after(0, lambda: self.control_panel.set_buttons_state(False))
    
    def _play_thread(self, audio_path):
        self.is_playing = True
        self.after(0, lambda: self.control_panel.set_status("正在播放...", "blue"))
        self.after(0, lambda: self.status_panel.set_info("正在播放音频..."))
        
        success = self.tts_engine.play_audio(audio_path)
        
        self.is_playing = False
        if success:
            self.after(0, lambda: self.control_panel.set_status("播放完成", "green"))
            self.after(0, lambda: self.status_panel.set_info("音频播放完成"))
        else:
            self.after(0, lambda: self.control_panel.set_status("播放完成", "orange"))
            self.after(0, lambda: self.status_panel.set_info("已尝试播放，请检查音频文件"))
    
    def on_stop(self):
        self.tts_engine.stop_playback()
        self.is_playing = False
        self.is_processing = False
        self.control_panel.set_status("已停止", "orange")
        self.control_panel.set_buttons_state(False)
        self.status_panel.set_info("播放已停止")
    
    def on_save(self):
        if not self.current_audio_path or not Path(self.current_audio_path).exists():
            messagebox.showwarning("提示", "请先进行语音转换并成功生成音频")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=f".{self.settings_panel.get_settings()['output_format']}",
            filetypes=[
                ("MP3 files", "*.mp3"),
                ("WAV files", "*.wav"),
                ("All files", "*.*")
            ],
            initialfile="tts_output"
        )
        
        if file_path:
            try:
                import shutil
                shutil.copy2(self.current_audio_path, file_path)
                messagebox.showinfo("成功", f"音频已保存到:\n{file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")
    
    def on_optimize_text(self):
        text = self.text_panel.get_text()
        if not text or not text.strip():
            messagebox.showwarning("提示", "请先输入要优化的文本")
            return None
        
        success, message, optimized_text = self.ai_enhancer.optimize_text(text)
        
        if success:
            self.text_panel.set_text(optimized_text)
        
        return success, message
