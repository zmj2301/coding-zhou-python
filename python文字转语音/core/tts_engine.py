import pyttsx3
from gtts import gTTS
import tempfile
import os
from pathlib import Path
import threading
import sys


class TTSEngine:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.engine_pyttsx3 = None
        self.is_playing = False
        self.current_audio_path = None
        self.stop_requested = False
        self.engine_busy = False
    
    def init_pyttsx3(self):
        try:
            if self.engine_pyttsx3:
                try:
                    self.engine_pyttsx3.stop()
                except:
                    pass
            
            self.engine_pyttsx3 = pyttsx3.init()
            return self.engine_pyttsx3
        except Exception as e:
            print(f"pyttsx3初始化失败: {e}")
            return None
    
    def get_available_voices(self, engine_type="pyttsx3"):
        voices = []
        if engine_type == "pyttsx3":
            engine = self.init_pyttsx3()
            if engine:
                try:
                    for voice in engine.getProperty('voices'):
                        voices.append({
                            'id': voice.id,
                            'name': voice.name,
                            'lang': voice.languages[0] if voice.languages else 'unknown'
                        })
                except Exception as e:
                    print(f"获取语音列表失败: {e}")
        return voices
    
    def synthesize_with_pyttsx3(self, text, output_path, speed=1.0, voice_type="female", quality="standard"):
        try:
            engine = self.init_pyttsx3()
            if not engine:
                return False
            
            rate = int(200 * speed)
            engine.setProperty('rate', rate)
            
            voices = engine.getProperty('voices')
            selected_voice = None
            
            for voice in voices:
                voice_name = voice.name.lower()
                if voice_type == "male" and "male" in voice_name:
                    selected_voice = voice.id
                    break
                elif voice_type == "female" and ("female" in voice_name or "zira" in voice_name):
                    selected_voice = voice.id
                    break
            
            if selected_voice:
                engine.setProperty('voice', selected_voice)
            
            engine.save_to_file(text, output_path)
            engine.runAndWait()
            
            if Path(output_path).exists() and Path(output_path).stat().st_size > 0:
                return True
            return False
        except Exception as e:
            print(f"pyttsx3合成失败: {e}")
            return False
    
    def speak_with_pyttsx3(self, text, speed=1.0, voice_type="female"):
        try:
            engine = self.init_pyttsx3()
            if not engine:
                return False
            
            rate = int(200 * speed)
            engine.setProperty('rate', rate)
            
            voices = engine.getProperty('voices')
            selected_voice = None
            
            for voice in voices:
                voice_name = voice.name.lower()
                if voice_type == "male" and "male" in voice_name:
                    selected_voice = voice.id
                    break
                elif voice_type == "female" and ("female" in voice_name or "zira" in voice_name):
                    selected_voice = voice.id
                    break
            
            if selected_voice:
                engine.setProperty('voice', selected_voice)
            
            engine.say(text)
            engine.runAndWait()
            
            try:
                engine.stop()
            except:
                pass
            
            return True
        except Exception as e:
            print(f"pyttsx3播放失败: {e}")
            return False
    
    def synthesize_with_gtts(self, text, output_path, speed=1.0, voice_type="female", quality="standard"):
        try:
            if not text.strip():
                return False
            
            lang = 'zh'
            slow = False
            if quality == "low":
                slow = True
            
            tts = gTTS(text=text, lang=lang, slow=slow)
            tts.save(output_path)
            
            if Path(output_path).exists() and Path(output_path).stat().st_size > 0:
                return True
            return False
        except Exception as e:
            print(f"gTTS合成失败: {e}")
            return False
    
    def synthesize(self, text, output_path=None, engine_type=None, speed=None, voice_type=None, quality=None):
        try:
            if not text or not text.strip():
                return False, None
            
            if engine_type is None:
                engine_type = self.config_manager.get("engine", "pyttsx3")
            if speed is None:
                speed = self.config_manager.get("speed", 1.0)
            if voice_type is None:
                voice_type = self.config_manager.get("voice_type", "female")
            if quality is None:
                quality = self.config_manager.get("quality", "standard")
            
            if output_path is None:
                temp_dir = tempfile.gettempdir()
                output_path = os.path.join(temp_dir, "tts_output.mp3")
            
            success = False
            if engine_type == "pyttsx3":
                success = self.synthesize_with_pyttsx3(text, output_path, speed, voice_type, quality)
            else:
                success = self.synthesize_with_gtts(text, output_path, speed, voice_type, quality)
            
            if success:
                self.current_audio_path = output_path
            
            return success, output_path
        except Exception as e:
            print(f"合成失败: {e}")
            return False, None
    
    def play_audio(self, audio_path):
        try:
            if not audio_path or not Path(audio_path).exists():
                print("音频文件不存在")
                return False
            
            self.is_playing = True
            self.stop_requested = False
            
            try:
                import platform
                import subprocess
                
                if platform.system() == "Windows":
                    os.startfile(audio_path)
                elif platform.system() == "Darwin":
                    subprocess.call(["open", audio_path])
                else:
                    subprocess.call(["xdg-open", audio_path])
                
                return True
            except Exception as e:
                print(f"系统播放失败: {e}")
            
            try:
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy() and not self.stop_requested:
                    pygame.time.Clock().tick(10)
                
                pygame.mixer.music.stop()
                pygame.mixer.quit()
                return True
            except Exception as e:
                print(f"pygame播放失败: {e}")
            
            return False
        except Exception as e:
            print(f"播放音频失败: {e}")
            return False
        finally:
            self.is_playing = False
    
    def stop_playback(self):
        try:
            self.stop_requested = True
            
            if self.engine_pyttsx3:
                try:
                    self.engine_pyttsx3.stop()
                except:
                    pass
            
            try:
                import pygame
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
                    pygame.mixer.quit()
            except:
                pass
            
            self.is_playing = False
            self.engine_busy = False
            return True
        except Exception as e:
            print(f"停止播放失败: {e}")
            return False
